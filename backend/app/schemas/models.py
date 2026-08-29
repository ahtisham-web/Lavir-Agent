from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class AgentRole(str, Enum):
    MASTER = "Master Agent (Larvi)"
    EMAIL = "Email Agent"
    CALENDAR = "Calendar Agent"
    SYSTEM = "System / Guard"

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"

class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EmailMessage(BaseModel):
    id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    snippet: str
    body: str
    timestamp: str
    unread: bool = True
    labels: List[str] = Field(default_factory=list)

class CalendarEvent(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    start_time: str
    end_time: str
    location: Optional[str] = ""
    attendees: List[str] = Field(default_factory=list)
    status: str = "confirmed" # confirmed, tentative, cancelled
    creator: str = "user@example.com"

class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    agent_role: AgentRole

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    requires_confirmation: bool = False
    confirmation_payload: Optional[Dict[str, Any]] = None

class ConfirmationRequest(BaseModel):
    confirmation_id: str
    action_type: str # e.g. "send_email", "delete_event", "create_event"
    description: str
    details: Dict[str, Any]
    agent_role: AgentRole
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class ConfirmationResponse(BaseModel):
    confirmation_id: str
    approved: bool
    user_feedback: Optional[str] = None

class AgentStep(BaseModel):
    step_id: str
    agent_role: AgentRole
    title: str
    thought: str
    action: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[ToolResult] = None
    status: StepStatus = StepStatus.PENDING
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class UserRequest(BaseModel):
    prompt: str
    session_id: str = "default_session"
    use_mock: bool = True

class AgentResponse(BaseModel):
    session_id: str
    prompt: str
    status: StepStatus
    final_output: str
    steps: List[AgentStep]
    pending_confirmation: Optional[ConfirmationRequest] = None
