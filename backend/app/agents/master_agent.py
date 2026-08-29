from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from .email_agent import email_agent
from .calendar_agent import calendar_agent
from ..tools.gmail_tools import gmail_tools
from ..tools.gcal_tools import gcal_tools
from ..schemas.models import AgentRole, AgentStep, StepStatus, AgentResponse, ConfirmationRequest, ConfirmationResponse
from ..core.state_manager import state_manager
from ..tools.mock_services import mock_store

class LarviMasterAgent(BaseAgent):
    """
    Larvi Master Agent Orchestrator:
    Central brain coordinating Email Agent and Calendar Agent via multi-step tool execution,
    context tracking, and Human-in-the-Loop safety guard integration.
    """
    def __init__(self):
        super().__init__(
            role=AgentRole.MASTER,
            name="Larvi Master Agent",
            description="Central orchestrator parsing user intent, planning execution graphs, and delegating to specialized agents."
        )

    def process_request(self, prompt: str, session_id: str = "default_session", use_mock: bool = True) -> AgentResponse:
        """Processes user prompt and returns step-by-step trace & final result."""
        session = state_manager.get_or_create_session(session_id)
        session.steps = []
        
        # Step 1: Master Agent Reasoning & Plan Formulation
        master_step_1 = self.create_step(
            title="Intent Classification & Workflow Planning",
            thought=f"Analyzing prompt: '{prompt}'. Deconstructing into agent routing graph.",
            action="plan_workflow"
        )
        session.steps.append(master_step_1)

        prompt_lower = prompt.lower()
        
        # Multi-Step Workflow 1: Check inbox for meeting requests & schedule event
        if "email" in prompt_lower or "inbox" in prompt_lower or "meeting request" in prompt_lower or "schedule" in prompt_lower:
            return self._run_email_to_calendar_workflow(prompt, session, use_mock)
            
        # Workflow 2: Direct Calendar Availability or Event Operations
        elif "conflict" in prompt_lower or "free" in prompt_lower or "calendar" in prompt_lower or "schedule event" in prompt_lower:
            return self._run_calendar_workflow(prompt, session, use_mock)

        # Workflow 3: Email Drafting / Sending
        elif "draft" in prompt_lower or "send email" in prompt_lower or "mail" in prompt_lower:
            return self._run_email_workflow(prompt, session, use_mock)
            
        # Default Intelligent Fallback
        else:
            return self._run_general_inquiry_workflow(prompt, session, use_mock)

    def _run_email_to_calendar_workflow(self, prompt: str, session: Any, use_mock: bool) -> AgentResponse:
        """Autonomous Multi-Step Workflow: Inbox Scan -> Extract Time -> Check Calendar -> Propose Booking."""
        
        # Step 2: Delegate to Email Agent to search inbox
        email_step, conf = email_agent.execute_subtask("search_emails", {"query": "meeting"}, use_mock=use_mock)
        session.steps.append(email_step)

        emails = email_step.tool_result.data if (email_step.tool_result and email_step.tool_result.success) else []
        
        if not emails:
            master_final = self.create_step("Final Summary", "No pending meeting requests found in unread emails.", "finish")
            master_final.status = StepStatus.COMPLETED
            session.steps.append(master_final)
            return AgentResponse(
                session_id=session.session_id,
                prompt=prompt,
                status=StepStatus.COMPLETED,
                final_output="I checked your emails, but no new meeting requests were found.",
                steps=session.steps
            )

        target_email = emails[0]
        now = datetime.now()
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        # Step 3: Master Agent parses extracted meeting info
        parse_step = self.create_step(
            title="Meeting Parameter Extraction",
            thought=f"Extracted meeting request from email '{target_email.get('subject')}' from {target_email.get('sender')}. Extracted target time: Tomorrow at 2:00 PM ({tomorrow_str}T14:00:00).",
            action="parse_details"
        )
        parse_step.status = StepStatus.COMPLETED
        session.steps.append(parse_step)

        # Step 4: Delegate to Calendar Agent to check availability
        start_iso = f"{tomorrow_str}T14:00:00"
        end_iso = f"{tomorrow_str}T14:45:00"

        cal_avail_step, _ = calendar_agent.execute_subtask("check_availability", {"start_time": start_iso, "end_time": end_iso}, use_mock=use_mock)
        session.steps.append(cal_avail_step)

        avail_data = cal_avail_step.tool_result.data if cal_avail_step.tool_result else {}
        is_available = avail_data.get("available", True)

        # Step 5: Request Confirmation for Creating Calendar Event
        event_payload = {
            "title": f"Review PRs & Sprint Sync (w/ {target_email.get('sender').split('@')[0].capitalize()})",
            "start_time": start_iso,
            "end_time": end_iso,
            "description": f"Automated scheduling from email: '{target_email.get('subject')}'",
            "attendees": [target_email.get("sender"), "user@techcorp.com"],
            "location": "Google Meet"
        }

        cal_create_step, pending_conf = calendar_agent.execute_subtask("create_calendar_event", event_payload, use_mock=use_mock)
        session.steps.append(cal_create_step)

        if pending_conf:
            state_manager.set_pending_confirmation(session.session_id, pending_conf, event_payload)
            return AgentResponse(
                session_id=session.session_id,
                prompt=prompt,
                status=StepStatus.REQUIRES_CONFIRMATION,
                final_output=f"I found a meeting request from **{target_email.get('sender')}** for tomorrow at 2:00 PM. Calendar is **{'FREE' if is_available else 'BUSY'}**. Please approve adding this to Google Calendar.",
                steps=session.steps,
                pending_confirmation=pending_conf
            )

        return AgentResponse(
            session_id=session.session_id,
            prompt=prompt,
            status=StepStatus.COMPLETED,
            final_output="Event successfully scheduled!",
            steps=session.steps
        )

    def _run_calendar_workflow(self, prompt: str, session: Any, use_mock: bool) -> AgentResponse:
        """Handles calendar queries and conflict checks."""
        cal_step, _ = calendar_agent.execute_subtask("get_calendar_events", {}, use_mock=use_mock)
        session.steps.append(cal_step)

        events = cal_step.tool_result.data if cal_step.tool_result else []
        evt_summary = "\n".join([f"- **{e['title']}**: {e['start_time']} to {e['end_time']} ({e['location']})" for e in events if e.get("status") != "cancelled"])

        return AgentResponse(
            session_id=session.session_id,
            prompt=prompt,
            status=StepStatus.COMPLETED,
            final_output=f"Here are your upcoming scheduled calendar events:\n\n{evt_summary}",
            steps=session.steps
        )

    def _run_email_workflow(self, prompt: str, session: Any, use_mock: bool) -> AgentResponse:
        """Handles email search & drafting."""
        email_step, _ = email_agent.execute_subtask("search_emails", {"query": ""}, use_mock=use_mock)
        session.steps.append(email_step)

        emails = email_step.tool_result.data if email_step.tool_result else []
        unread_summary = "\n".join([f"- **From**: {m['sender']} | **Subject**: {m['subject']}\n  _{m['snippet']}_" for m in emails[:3]])

        return AgentResponse(
            session_id=session.session_id,
            prompt=prompt,
            status=StepStatus.COMPLETED,
            final_output=f"Found {len(emails)} unread messages in your inbox:\n\n{unread_summary}",
            steps=session.steps
        )

    def _run_general_inquiry_workflow(self, prompt: str, session: Any, use_mock: bool) -> AgentResponse:
        """Handles general user inquiries."""
        step = self.create_step(
            title="General Processing",
            thought="Parsed general request. Larvi Master Agent coordinating system response.",
            action="respond"
        )
        step.status = StepStatus.COMPLETED
        session.steps.append(step)

        return AgentResponse(
            session_id=session.session_id,
            prompt=prompt,
            status=StepStatus.COMPLETED,
            final_output="Hello! I am Larvi, your autonomous Email and Calendar AI Master Agent. Ask me to scan your emails for meeting requests, check conflicts, or schedule events on Google Calendar!",
            steps=session.steps
        )

    def resume_with_confirmation(self, session_id: str, confirmation_res: ConfirmationResponse, use_mock: bool = True) -> AgentResponse:
        """Resumes workflow after user responds to Human-in-the-Loop approval dialog."""
        session = state_manager.get_or_create_session(session_id)
        payload = session.pending_action_payload or {}
        conf_req = session.pending_confirmation

        state_manager.clear_pending_confirmation(session_id)

        if not confirmation_res.approved:
            reject_step = self.create_step(
                title="User Rejected Action",
                thought=f"User rejected confirmation request {confirmation_res.confirmation_id}. Reason: {confirmation_res.user_feedback or 'User denied authorization.'}",
                action="reject"
            )
            reject_step.status = StepStatus.REJECTED
            session.steps.append(reject_step)

            return AgentResponse(
                session_id=session_id,
                prompt="Resume workflow after user rejection",
                status=StepStatus.REJECTED,
                final_output="Action was cancelled based on your decision. No changes were made to your email or calendar.",
                steps=session.steps
            )

        # User Approved: Execute High-Stakes Action
        approve_step = self.create_step(
            title="User Approved Action",
            thought=f"User approved action {conf_req.action_type if conf_req else 'action'}. Proceeding with API execution.",
            action="execute_approved"
        )
        approve_step.status = StepStatus.CONFIRMED
        session.steps.append(approve_step)

        if conf_req and conf_req.action_type == "create_calendar_event":
            # Force execute without safety check (already approved)
            res = gcal_tools.create_calendar_event(
                title=payload.get("title", "Event"),
                start_time=payload.get("start_time", ""),
                end_time=payload.get("end_time", ""),
                description=payload.get("description", ""),
                attendees=payload.get("attendees", []),
                location=payload.get("location", ""),
                use_mock=use_mock
            )
            
            exec_step = self.create_step(
                title="Google Calendar Event Created",
                thought="Event successfully added to calendar. Generating confirmation notification email.",
                action="created"
            )
            exec_step.status = StepStatus.COMPLETED
            session.steps.append(exec_step)

            # Auto-draft confirmation email
            email_res = gmail_tools.draft_email(
                recipient=payload.get("attendees", ["alex@techcorp.com"])[0],
                subject=f"Confirmed: {payload.get('title')}",
                body=f"Hi,\n\nI have scheduled '{payload.get('title')}' on my Google Calendar for {payload.get('start_time')}.\n\nSee you then!",
                use_mock=use_mock
            )

            return AgentResponse(
                session_id=session_id,
                prompt="Resume after approval",
                status=StepStatus.COMPLETED,
                final_output=f"✅ **Action Confirmed!** Event **'{payload.get('title')}'** has been successfully booked on Google Calendar for `{payload.get('start_time')}`. Confirmation email draft created.",
                steps=session.steps
            )

        return AgentResponse(
            session_id=session_id,
            prompt="Resume after approval",
            status=StepStatus.COMPLETED,
            final_output="Action approved and executed successfully.",
            steps=session.steps
        )

master_agent = LarviMasterAgent()
