"""
Holds the per-session conversation state that Larvi uses for context
management: message history (in Anthropic Messages API format) plus any
tool call that is currently waiting on user confirmation.
"""
import json
from typing import Any, Dict, List, Optional


class ConversationState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict[str, Any]] = []
        # {"tool_use_id": str, "tool_name": str, "tool_input": dict, "agent": "email"|"calendar"}
        self.pending_confirmation: Optional[Dict[str, Any]] = None

    def add_user_message(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})

    def add_assistant_message(self, content_blocks: List[Any]) -> None:
        serializable = []
        for block in content_blocks:
            if hasattr(block, "model_dump"):
                serializable.append(block.model_dump())
            else:
                serializable.append(block)
        self.messages.append({"role": "assistant", "content": serializable})

    def add_tool_result(self, tool_use_id: str, result: Dict[str, Any]) -> None:
        self.messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": json.dumps(result),
            }],
        })

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages
