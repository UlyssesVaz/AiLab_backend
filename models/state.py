# models/state.py
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

class AgentRole(str, Enum):
    PI = "Principal Investigator"
    IMMUNOLOGIST = "Immunologist"  
    ML_SPECIALIST = "ML Specialist"
    COMP_BIOLOGIST = "Computational Biologist"

class AgentInput(BaseModel):
    agent: AgentRole
    analysis: str
    recommendation: str  # "Modify Existing" or "De Novo Design"
    confidence: float
    reasoning: List[str]

class ProjectState(BaseModel):
    # Input
    text: str
    
    # Agent inputs (populated during workflow)
    agent_inputs: List[AgentInput] = []
    
    # Final outputs (API response format)
    extracted_data: Dict[str, Any] = {}
    strategy: Dict[str, Any] = {}
    status: str = "started"
    error: str = ""
    
    # Internal workflow tracking
    current_agent: Optional[AgentRole] = None

class EventType(Enum):
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete" 
    AGENT_THINKING = "agent_thinking"
    TOOL_USAGE = "tool_usage"
    DECISION_MADE = "decision_made"
    ERROR = "error"

class ProgressEvent(BaseModel):
    event_type: EventType
    timestamp: datetime
    step_name: str
    agent: Optional[AgentRole] = None
    details: Optional[Dict[str, Any]] = None
    progress: Optional[float] = None  # 0.0 to 1.0