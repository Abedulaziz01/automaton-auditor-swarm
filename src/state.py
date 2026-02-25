"""
Typed State Definition for Automaton Auditor
Constitutional State with Targeting Protocol Fields
"""

from typing import List, Dict, Optional, Literal, Any
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
    """Main state flowing through the LangGraph
    Now includes targeting protocol fields for constitutional routing
    """
    
    # ===== ORIGINAL FIELDS (Keep these) =====
    # Inputs
    repo_url: str
    pdf_path: str
    
    # Collections with reducers
    evidences: Annotated[Dict[str, Evidence], operator.ior]
    opinions: Annotated[List[JudicialOpinion], operator.add]
    
    # Outputs
    final_report: Optional[str]
    error: Optional[str]
    
    # ===== NEW FIELDS for Phase 1 Constitution Engine =====
    # Full rubric loaded from JSON
    rubric: Dict[str, Any]
    
    # Targeting Protocol Fields (populated by ContextBuilder)
    github_dimensions: List[Dict[str, Any]]  # Dimensions targeting github_repo
    pdf_dimensions: List[Dict[str, Any]]     # Dimensions targeting pdf_report
    image_dimensions: List[Dict[str, Any]]    # Dimensions targeting extracted_images
    synthesis_rules: Dict[str, Any]            # Rules for Chief Justice
    
    # Runtime tracking
    current_dimension: Optional[str]           # Currently processing dimension
    errors: List[str]                           # Collect errors instead of single error


# Quick validation test
if __name__ == "__main__":
    # Test creating a state with all required fields
    test_state: AgentState = {
        # Original fields
        "repo_url": "https://github.com/test/repo",
        "pdf_path": "/path/to/report.pdf",
        "evidences": {},
        "opinions": [],
        "final_report": None,
        "error": None,
        
        # New fields
        "rubric": {},
        "github_dimensions": [],
        "pdf_dimensions": [],
        "image_dimensions": [],
        "synthesis_rules": {},
        "current_dimension": None,
        "errors": []
    }
    
    print("✅ AgentState updated successfully with targeting protocol fields")
    print(f"   Total fields: {len(test_state)}")