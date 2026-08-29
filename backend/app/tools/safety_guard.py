from typing import Tuple, Dict, Any, Optional
import uuid
from ..schemas.models import ConfirmationRequest, AgentRole
from ..core.config import settings

class SafetyGuard:
    """Human-in-the-Loop (HITL) Safety Guard for High-Stakes Agent Actions."""

    HIGH_STAKES_ACTIONS = {
        "send_email": {
            "description": "Send an outbound email to external or internal recipients.",
            "requires_approval": settings.REQUIRES_APPROVAL_FOR_SENDING_EMAIL,
            "role": AgentRole.EMAIL
        },
        "create_calendar_event": {
            "description": "Schedule a new event on Google Calendar.",
            "requires_approval": settings.REQUIRES_APPROVAL_FOR_CREATING_EVENT,
            "role": AgentRole.CALENDAR
        },
        "cancel_calendar_event": {
            "description": "Cancel or delete an existing Google Calendar event.",
            "requires_approval": settings.REQUIRES_APPROVAL_FOR_CANCELING_EVENT,
            "role": AgentRole.CALENDAR
        }
    }

    @classmethod
    def evaluate_action(cls, action_type: str, details: Dict[str, Any], agent_role: AgentRole) -> Tuple[bool, Optional[ConfirmationRequest]]:
        """
        Evaluates whether an action can proceed automatically or requires user confirmation.
        Returns: (is_safe_to_proceed, Optional[ConfirmationRequest])
        """
        rule = cls.HIGH_STAKES_ACTIONS.get(action_type)
        if not rule or not rule.get("requires_approval", True):
            return True, None

        confirmation_id = f"conf-{uuid.uuid4().hex[:8]}"
        req = ConfirmationRequest(
            confirmation_id=confirmation_id,
            action_type=action_type,
            description=rule["description"],
            details=details,
            agent_role=agent_role
        )
        return False, req

safety_guard = SafetyGuard()
