from typing import Optional, List, Dict, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import operator


class Evidence(BaseModel):
    found: bool = Field(..., description="Whether the artifact was found")
    content: Optional[str] = Field(
        None, description="Extracted content or snippet"
    )
    location: str = Field(..., description="File path or logical location")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score between 0 and 1"
    )


class JudicialOpinion(BaseModel):
    judge: Literal["Prosecutor", "Defense", "TechLead"]
    score: int = Field(..., ge=0, le=5)
    argument: str
    cited_evidence: List[str]


class AgentState(TypedDict):
    evidences: Dict[str, Evidence]
    opinions: List[JudicialOpinion]


reducers = {
    "evidences": operator.ior,
    "opinions": operator.add
}