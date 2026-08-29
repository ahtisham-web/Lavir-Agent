from typing import Dict, Any, List, Tuple, Optional
from .base_agent import BaseAgent
from ..schemas.models import AgentRole, AgentStep, StepStatus, ToolCall, ToolResult, ConfirmationRequest
from ..tools.gmail_tools import gmail_tools
from ..tools.safety_guard import safety_guard

class EmailAgent(BaseAgent):
    """Specialized Agent for Email Understanding, Thread Extraction, and Drafting/Sending."""
    def __init__(self):
        super().__init__(
            role=AgentRole.EMAIL,
            name="Email Agent",
            description="Extracts meeting requests, parses email threads, and drafts or sends emails."
        )

    def execute_subtask(self, action_type: str, params: Dict[str, Any], use_mock: bool = True) -> Tuple[AgentStep, Optional[ConfirmationRequest]]:
        """Executes an email tool action with safety guard check."""
        step = self.create_step(
            title=f"Email Action: {action_type}",
            thought=f"Email Agent analyzing request '{action_type}' with parameters {params}.",
            action=action_type
        )
        
        # Check Safety Guard for high-stakes actions (e.g. send_email)
        is_safe, confirmation_req = safety_guard.evaluate_action(
            action_type=action_type,
            details=params,
            agent_role=self.role
        )

        if not is_safe and confirmation_req:
            step.status = StepStatus.REQUIRES_CONFIRMATION
            step.thought += " Action requires human confirmation before outbound transmission."
            return step, confirmation_req

        # Execute Tool
        tool_call = ToolCall(tool_name=action_type, arguments=params, agent_role=self.role)
        step.tool_call = tool_call

        if action_type == "search_emails":
            res = gmail_tools.search_emails(query=params.get("query", ""), use_mock=use_mock)
        elif action_type == "read_email_thread":
            res = gmail_tools.read_email_thread(thread_id=params.get("thread_id", ""), use_mock=use_mock)
        elif action_type == "draft_email":
            res = gmail_tools.draft_email(
                recipient=params.get("recipient", ""),
                subject=params.get("subject", ""),
                body=params.get("body", ""),
                use_mock=use_mock
            )
        elif action_type == "send_email":
            res = gmail_tools.send_email(
                recipient=params.get("recipient", ""),
                subject=params.get("subject", ""),
                body=params.get("body", ""),
                use_mock=use_mock
            )
        else:
            res = ToolResult(tool_name=action_type, success=False, error=f"Unknown email tool: {action_type}")

        step.tool_result = res
        step.status = StepStatus.COMPLETED if res.success else StepStatus.FAILED
        return step, None

email_agent = EmailAgent()
