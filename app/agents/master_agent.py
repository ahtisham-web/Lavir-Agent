"""
Larvi Master Agent.

Central controller: takes a natural-language message, uses Claude's
tool-use to decide intent + which tool(s) to call, dispatches to the
Email or Calendar sub-agent, feeds results back to Claude, and repeats
until Claude has a final answer for the user.

Design notes
------------
- One tool call per turn is assumed (the system prompt asks Claude to
  work step by step). This keeps the confirmation safety-net below
  simple and deterministic instead of relying purely on prompting.
- SENSITIVE_TOOLS lists actions that must never fire without an explicit
  user confirmation, enforced in code (not just prompted) - the pending
  action is stored on ConversationState and only executed once the
  *next* user message reads as a confirmation.
- Tool results are only ever reported as successful if the underlying
  service returned status == "success"; Larvi is instructed never to
  claim success otherwise.
"""
import json
from typing import Tuple

from anthropic import Anthropic

from app.config import settings
from app.agents.email_agent import EmailAgent
from app.agents.calendar_agent import CalendarAgent
from app.tools.email_tools import EMAIL_TOOL_SCHEMAS
from app.tools.calendar_tools import CALENDAR_TOOL_SCHEMAS
from app.state.conversation import ConversationState

SENSITIVE_TOOLS = {"send_email", "reply_email", "update_event", "reschedule_event", "cancel_event"}

SYSTEM_PROMPT = """You are Larvi, an AI assistant that manages a user's email and calendar.

You have two specialised toolsets available to you:
- Email tools (search, read, draft, send, reply)
- Calendar tools (view, search, check availability, create, update, reschedule, cancel)

Rules you must always follow:
1. Work step by step. Call at most one tool per turn, look at its result, then decide the next step.
2. Never claim an action succeeded unless the tool result you received has "status": "success".
   If a tool returns "status": "error", explain the problem to the user in plain language instead
   of pretending it worked.
3. Some tools are IMPORTANT ACTIONS (sending an email, replying to an email, updating/rescheduling/
   cancelling a calendar event). For these, first tell the user exactly what you are about to do
   and ask them to confirm - do not call the tool yet. Only call it after the user clearly confirms
   in a later message.
4. Use the conversation history to resolve references like "it", "that meeting", or "that email" to
   the specific item you previously found.
5. For multi-step requests (e.g. "find the email about the meeting and add it to my calendar"),
   break the work into the necessary sequence of tool calls yourself - search/read the email first,
   extract the details, then check availability and create the event.
6. If required information is missing (e.g. no date/time, no recipient), ask the user instead of
   guessing.
7. When you have enough information and no more tool calls are needed, give a clear, concise final
   answer summarizing exactly what was found or done.
"""

CONFIRM_WORDS = {"yes", "y", "yeah", "yep", "confirm", "confirmed", "go ahead", "do it", "proceed", "ok", "okay", "sure"}
DECLINE_WORDS = {"no", "n", "nope", "cancel", "don't", "dont", "stop", "nevermind", "never mind"}


def _looks_like_confirmation(text: str) -> bool:
    t = text.strip().lower().rstrip(".!")
    return t in CONFIRM_WORDS or any(t.startswith(w + " ") for w in CONFIRM_WORDS)


def _looks_like_decline(text: str) -> bool:
    t = text.strip().lower().rstrip(".!")
    return t in DECLINE_WORDS or any(t.startswith(w + " ") for w in DECLINE_WORDS)


class MasterAgent:
    def __init__(self, email_agent: EmailAgent = None, calendar_agent: CalendarAgent = None, client: Anthropic = None):
        self.client = client or Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.email_agent = email_agent or EmailAgent()
        self.calendar_agent = calendar_agent or CalendarAgent()
        self.tools = EMAIL_TOOL_SCHEMAS + CALENDAR_TOOL_SCHEMAS

    # ---- tool dispatch ----------------------------------------------

    def _dispatch(self, tool_name: str, tool_input: dict) -> Tuple[dict, str]:
        if tool_name in EmailAgent.TOOL_NAMES:
            return self.email_agent.run_tool(tool_name, tool_input), "email"
        if tool_name in CalendarAgent.TOOL_NAMES:
            return self.calendar_agent.run_tool(tool_name, tool_input), "calendar"
        return {"status": "error", "error": f"Unknown tool '{tool_name}'"}, "unknown"

    # ---- public entry point ------------------------------------------

    def handle_message(self, conversation: ConversationState, user_message: str) -> str:
        # 1. Resolve any pending confirmation before doing anything else.
        if conversation.pending_confirmation:
            pending = conversation.pending_confirmation
            if _looks_like_confirmation(user_message):
                conversation.pending_confirmation = None
                result, _agent = self._dispatch(pending["tool_name"], pending["tool_input"])
                conversation.add_user_message(user_message)
                conversation.add_tool_result(pending["tool_use_id"], result)
                return self._run_loop(conversation)
            elif _looks_like_decline(user_message):
                conversation.pending_confirmation = None
                conversation.add_user_message(user_message)
                conversation.add_tool_result(
                    pending["tool_use_id"], {"status": "cancelled", "message": "User declined this action."}
                )
                return self._run_loop(conversation)
            else:
                # Treat the message as a new instruction; drop the stale pending action
                # by telling Claude it was cancelled, then continue normally.
                conversation.pending_confirmation = None
                conversation.add_tool_result(
                    pending["tool_use_id"], {"status": "cancelled", "message": "Superseded by a new user message."}
                )

        # 2. Normal turn.
        conversation.add_user_message(user_message)
        return self._run_loop(conversation)

    # ---- agentic loop -------------------------------------------------

    def _run_loop(self, conversation: ConversationState) -> str:
        for _ in range(settings.MAX_AGENT_LOOP_STEPS):
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=self.tools,
                messages=conversation.get_messages(),
            )

            conversation.add_assistant_message(response.content)

            if response.stop_reason != "tool_use":
                return "".join(b.text for b in response.content if getattr(b, "type", None) == "text")

            tool_block = next((b for b in response.content if b.type == "tool_use"), None)
            if tool_block is None:
                return "".join(b.text for b in response.content if getattr(b, "type", None) == "text")

            tool_name, tool_input, tool_use_id = tool_block.name, tool_block.input, tool_block.id

            if tool_name in SENSITIVE_TOOLS:
                conversation.pending_confirmation = {
                    "tool_use_id": tool_use_id,
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                }
                return (
                    f"Before I do that: I'm about to call '{tool_name}' with {json.dumps(tool_input)}. "
                    "Reply 'confirm' to proceed or 'cancel' to stop."
                )

            result, _agent = self._dispatch(tool_name, tool_input)
            conversation.add_tool_result(tool_use_id, result)

        return "I've taken several steps but couldn't finish this within my step limit. Could you clarify what you'd like next?"
