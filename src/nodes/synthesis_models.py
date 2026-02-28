from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime

class SecurityRiskLevel(Enum):
    NONE = "none"
    LOW = "low" 
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityFinding(BaseModel):
    """Security issues found during investigation"""
    finding: str
    risk_level: SecurityRiskLevel
    evidence_id: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    
class FactualDiscrepancy(BaseModel):
    """Discrepancy between evidence and opinion"""
    dimension: str
    evidence_fact: str
    opinion_claim: str
    opinion_source: str  # Which judge made the claim
    resolution: str = "pending"

class DimensionScore(BaseModel):
    """Final score for a single dimension (1-5 scale)"""
    dimension: str
    score: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0.0, le=1.0)
    security_override_applied: bool = False
    fact_supremacy_applied: bool = False
    variance_detected: bool = False
    reasoning: str
    
    @validator('score')
    def validate_score(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Score must be between 1 and 5')
        return v

class RemediationAction(BaseModel):
    """Concrete remediation recommendation"""
    priority: str  # HIGH, MEDIUM, LOW
    action: str
    file_path: Optional[str] = None
    code_example: Optional[str] = None
    reasoning: str

class FinalVerdict(BaseModel):
    """Complete Supreme Court verdict"""
    case_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Overall scores
    overall_score: float = Field(ge=1.0, le=5.0)
    dimension_scores: List[DimensionScore]
    
    # Security findings
    security_findings: List[SecurityFinding] = []
    security_override_triggered: bool = False
    security_cap_applied: Optional[int] = None
    
    # Factual findings
    factual_discrepancies: List[FactualDiscrepancy] = []
    fact_supremacy_applied: List[str] = []  # Dimensions where facts overruled opinions
    
    # Variance findings
    high_variance_dimensions: List[str] = []
    re_evaluations_triggered: int = 0
    
    # Final outputs
    dissent_summary: str
    remediation_plan: List[RemediationAction]
    
    # Reference to rubric
    synthesis_rules_applied: List[str] = []

class RemediationPriority(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM" 
    LOW = "LOW"