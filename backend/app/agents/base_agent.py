from typing import List, Dict, Any, Optional
import uuid
from ..schemas.models import AgentRole, AgentStep, StepStatus, ToolCall, ToolResult

class BaseAgent:
    """Base Class for specialized agents in Larvi Architecture."""
    def __init__(self, role: AgentRole, name: str, description: str):
        self.role = role
        self.name = name
        self.description = description

    def create_step(self, title: str, thought: str, action: Optional[str] = None) -> AgentStep:
        return AgentStep(
            step_id=f"step-{uuid.uuid4().hex[:6]}",
            agent_role=self.role,
            title=title,
            thought=thought,
            action=action,
            status=StepStatus.RUNNING
        )
