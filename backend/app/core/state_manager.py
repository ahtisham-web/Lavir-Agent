from typing import Dict, Any, Optional, List
from ..schemas.models import AgentResponse, AgentStep, ConfirmationRequest, ConfirmationResponse, StepStatus

class SessionState:
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.history: List[Dict[str, Any]] = []
        self.steps: List[AgentStep] = []
        self.pending_confirmation: Optional[ConfirmationRequest] = None
        self.pending_action_payload: Optional[Dict[str, Any]] = None
        self.status: StepStatus = StepStatus.PENDING

class StateManager:
    """Central Session and Workflow State Manager for Larvi Agents."""
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}

    def get_or_create_session(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(session_id)
        return self.sessions[session_id]

    def set_pending_confirmation(self, session_id: str, confirmation_req: ConfirmationRequest, payload: Dict[str, Any]):
        session = self.get_or_create_session(session_id)
        session.pending_confirmation = confirmation_req
        session.pending_action_payload = payload
        session.status = StepStatus.REQUIRES_CONFIRMATION

    def clear_pending_confirmation(self, session_id: str):
        session = self.get_or_create_session(session_id)
        session.pending_confirmation = None
        session.pending_action_payload = None

state_manager = StateManager()
