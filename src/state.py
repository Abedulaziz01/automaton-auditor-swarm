"""
Production-grade state management with Pydantic models
Enhanced for Phase 2 detective evidence
"""

from typing import List, Dict, Any, Optional, TypedDict, Annotated, Literal
from pydantic import BaseModel, Field, ConfigDict
import operator
from datetime import datetime

class Evidence(BaseModel):
    """Core evidence model - what each detective finds"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    dimension_id: str = Field(description="Which rubric dimension this evidence relates to")
    findings: List[str] = Field(description="List of specific findings")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    source: str = Field(description="Source file or location")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    verified: bool = Field(default=False, description="Whether evidence has been verified")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class JudicialOpinion(BaseModel):
    """Judicial opinion model - what judges decide"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    dimension_id: str = Field(description="Which rubric dimension this opinion covers")
    verdict: Literal["PASS", "FAIL", "REVIEW"] = Field(description="Final verdict")
    reasoning: str = Field(description="Detailed reasoning")
    evidence_used: List[str] = Field(description="Evidence IDs used")
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_remediation: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class AgentState(TypedDict):
    """Main agent state with reducers"""
    rubric: Dict[str, Any]  # Loaded rubric
    evidences: Annotated[List[Evidence], operator.add]  # Evidence accumulator
    opinions: Annotated[List[JudicialOpinion], operator.add]  # Judicial opinions
    errors: Annotated[List[str], operator.add]  # Error accumulator
    current_step: str  # Current step in workflow
    metadata: Dict[str, Any]  # Additional metadata
    investigation_targets: Dict[str, str]  # repo_path, pdf_path etc.

class DetectiveOutput(BaseModel):
    """Structured output for detectives"""
    evidences: List[Evidence]
    errors: List[str]
    metadata: Dict[str, Any]