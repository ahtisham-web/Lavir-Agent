from typing import Dict, Any, List, Tuple, Optional
from .base_agent import BaseAgent
from ..schemas.models import AgentRole, AgentStep, StepStatus, ToolCall, ToolResult, ConfirmationRequest
from ..tools.gcal_tools import gcal_tools
from ..tools.safety_guard import safety_guard

class CalendarAgent(BaseAgent):
    """Specialized Agent for Checking Free/Busy Slots, Scheduling Events, and Resolving Conflicts."""
    def __init__(self):
        super().__init__(
            role=AgentRole.CALENDAR,
            name="Calendar Agent",
            description="Manages calendar schedules, checks availability, creates events, and handles cancellations."
        )

    def execute_subtask(self, action_type: str, params: Dict[str, Any], use_mock: bool = True) -> Tuple[AgentStep, Optional[ConfirmationRequest]]:
        """Executes a calendar tool action with safety guard check."""
        step = self.create_step(
            title=f"Calendar Action: {action_type}",
            thought=f"Calendar Agent inspecting schedule for '{action_type}' with parameters {params}.",
            action=action_type
        )
        
        # Check Safety Guard for sensitive operations (create / cancel event)
        is_safe, confirmation_req = safety_guard.evaluate_action(
            action_type=action_type,
            details=params,
            agent_role=self.role
        )

        if not is_safe and confirmation_req:
            step.status = StepStatus.REQUIRES_CONFIRMATION
            step.thought += " Action requires explicit user approval before calendar modification."
            return step, confirmation_req

        # Execute Tool
        tool_call = ToolCall(tool_name=action_type, arguments=params, agent_role=self.role)
        step.tool_call = tool_call

        if action_type == "get_calendar_events":
            res = gcal_tools.get_calendar_events(query_date=params.get("date"), use_mock=use_mock)
        elif action_type == "check_availability":
            res = gcal_tools.check_availability(
                start_time=params.get("start_time", ""),
                end_time=params.get("end_time", ""),
                use_mock=use_mock
            )
        elif action_type == "create_calendar_event":
            res = gcal_tools.create_calendar_event(
                title=params.get("title", "Meeting"),
                start_time=params.get("start_time", ""),
                end_time=params.get("end_time", ""),
                description=params.get("description", ""),
                attendees=params.get("attendees", []),
                location=params.get("location", ""),
                use_mock=use_mock
            )
        elif action_type == "cancel_calendar_event":
            res = gcal_tools.cancel_calendar_event(
                event_id=params.get("event_id", ""),
                use_mock=use_mock
            )
        else:
            res = ToolResult(tool_name=action_type, success=False, error=f"Unknown calendar tool: {action_type}")

        step.tool_result = res
        step.status = StepStatus.COMPLETED if res.success else StepStatus.FAILED
        return step, None

calendar_agent = CalendarAgent()
