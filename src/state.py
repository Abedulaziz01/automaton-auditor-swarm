"""
Typed State Definition for Automaton Auditor
"""

from typing import List, Dict, Optional, Literal
from typing_extensions import TypedDict, Annotated
from pydantic import BaseModel, Field
import operator


class Evidence(BaseModel):
    """Forensic evidence collected by detectives"""
    found: bool = Field(..., description="Whether the evidence was found")
    content: Optional[str] = Field(None, description="The actual content found")
    location: str = Field(..., description="File path where evidence was found")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Additional context")


class JudicialOpinion(BaseModel):
    """Opinion from a judge persona"""
    judge: Literal["Prosecutor", "Defense", "TechLead"] = Field(..., description="Which judge spoke")
    criterion_id: str = Field(..., description="Which rubric criterion this addresses")
    score: int = Field(..., ge=1, le=5, description="Score from 1-5")
    argument: str = Field(..., description="Detailed reasoning")
    cited_evidence: List[str] = Field(..., description="Evidence IDs that support this opinion")
    dissent: Optional[str] = Field(None, description="What this judge disagrees with")


class AgentState(TypedDict):
    """Main state flowing through the LangGraph"""
    # Inputs
    repo_url: str
    pdf_path: str
    
    # Collections with reducers
    evidences: Annotated[Dict[str, Evidence], operator.ior]
    opinions: Annotated[List[JudicialOpinion], operator.add]
    
    # Outputs
    final_report: Optional[str]
    error: Optional[str]