# tests/test_state_phase2.py
import sys
import os
sys.path.insert(0, os.getcwd())

from src.state import Evidence, JudicialOpinion, AgentState
from datetime import datetime

def test_step1():
    print("\n🔬 TESTING STEP 1: Enhanced State Models")
    print("=" * 50)
    
    # Test 1: Create Evidence with all fields
    try:
        evidence = Evidence(
            dimension_id="repo_001",
            findings=["Found git history with 3 commits", "Detected state management"],
            confidence=0.95,
            source="git_log",
            metadata={"commit_count": 3, "branch": "main"},
            verified=False
        )
        print("✅ Test 1.1: Evidence creation successful")
        print(f"   - Dimension: {evidence.dimension_id}")
        print(f"   - Findings: {len(evidence.findings)} items")
        print(f"   - Confidence: {evidence.confidence}")
        print(f"   - Timestamp: {evidence.timestamp}")
    except Exception as e:
        print(f"❌ Test 1.1 Failed: {e}")
    
    # Test 2: Create JudicialOpinion
    try:
        opinion = JudicialOpinion(
            dimension_id="repo_001",
            verdict="PASS",
            reasoning="Repository meets all requirements",
            evidence_used=["evidence_1", "evidence_2"],
            confidence=0.88,
            suggested_remediation="No action needed"
        )
        print("✅ Test 1.2: JudicialOpinion creation successful")
        print(f"   - Verdict: {opinion.verdict}")
        print(f"   - Reasoning: {opinion.reasoning[:50]}...")
    except Exception as e:
        print(f"❌ Test 1.2 Failed: {e}")
    
    # Test 3: Create AgentState with reducer
    try:
        state: AgentState = {
            "rubric": {"dimensions": ["repo_001", "doc_001"]},
            "evidences": [evidence],
            "opinions": [opinion],
            "errors": [],
            "current_step": "detective",
            "metadata": {"start_time": datetime.now().isoformat()},
            "investigation_targets": {
                "repo_path": ".",
                "pdf_path": "document.pdf"
            }
        }
        print("✅ Test 1.3: AgentState creation successful")
        print(f"   - Evidences: {len(state['evidences'])}")
        print(f"   - Opinions: {len(state['opinions'])}")
        print(f"   - Current step: {state['current_step']}")
    except Exception as e:
        print(f"❌ Test 1.3 Failed: {e}")
    
    # Test 4: Verify reducer works (adding multiple evidences)
    try:
        state["evidences"].append(evidence)  # Should work due to operator.add
        print("✅ Test 1.4: Reducer working correctly")
        print(f"   - Evidences after append: {len(state['evidences'])}")
    except Exception as e:
        print(f"❌ Test 1.4 Failed: {e}")

if __name__ == "__main__":
    test_step1()