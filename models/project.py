from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

class ProjectStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    CONFIRMED = "confirmed"
    STRATEGY_GENERATED = "strategy_generated"

class ExtractedData(BaseModel):
    target: str
    timeline: str
    budget: str
    goal: str
    confidence: float  # 0-1 score from OpenAI
    raw_text: Optional[str] = None

class StrategyRecommendation(BaseModel):
    title: str
    rationale: list[Dict[str, Any]]
    candidates: list[str]
    confidence: float
    alternatives: Optional[list[Dict[str, Any]]] = None

class Project(BaseModel):
    id: str
    filename: str
    status: ProjectStatus
    extracted_data: Optional[ExtractedData] = None
    strategy: Optional[StrategyRecommendation] = None
    created_at: str