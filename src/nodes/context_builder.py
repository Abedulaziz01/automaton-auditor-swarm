"""
ContextBuilder Node - Implements the Constitution Engine
Loads rubric, filters by target artifact, dispatches to specialized agents
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from src.state import AgentState


def context_builder(state: AgentState) -> AgentState:
    """
    Constitutional node that:
    1. Loads rubric from JSON
    2. Filters dimensions by target_artifact
    3. Dispatches instructions to specialized agents
    4. Returns enriched state with targeting protocol fields
    
    This makes the rubric HOT-SWAPPABLE - change JSON without code changes!
    """
    print("🔷 ContextBuilder: Loading constitution...")
    
    # 1. Load rubric
    rubric_path = Path("rubric/week2_rubric.json")
    
    try:
        with open(rubric_path, "r", encoding="utf-8") as f:
            rubric = json.load(f)
        print(f"   ✅ Loaded rubric: {rubric.get('name', 'Unknown')}")
    except FileNotFoundError:
        error_msg = f"Rubric not found at {rubric_path.absolute()}"
        print(f"   ❌ {error_msg}")
        state["errors"] = state.get("errors", []) + [error_msg]
        return state
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in rubric: {e}"
        print(f"   ❌ {error_msg}")
        state["errors"] = state.get("errors", []) + [error_msg]
        return state
    
    # 2. Store full rubric
    state["rubric"] = rubric
    
    # 3. Extract dimensions and synthesis rules
    dimensions = rubric.get("dimensions", [])
    synthesis_rules = rubric.get("synthesis_rules", {})
    
    # 4. TARGETING PROTOCOL - Filter by artifact type
    github_dimensions = []
    pdf_dimensions = []
    image_dimensions = []
    
    for dim in dimensions:
        target = dim.get("target_artifact")
        
        if target == "github_repo":
            github_dimensions.append(dim)
            print(f"   📦 GitHub dimension: {dim.get('name')}")
        
        elif target == "pdf_report":
            pdf_dimensions.append(dim)
            print(f"   📄 PDF dimension: {dim.get('name')}")
        
        elif target == "extracted_images":
            image_dimensions.append(dim)
            print(f"   🖼️  Image dimension: {dim.get('name')}")
    
    # 5. Update state with filtered dimensions
    state["github_dimensions"] = github_dimensions
    state["pdf_dimensions"] = pdf_dimensions
    state["image_dimensions"] = image_dimensions
    state["synthesis_rules"] = synthesis_rules
    
    # 6. Summary
    print(f"\n   📊 Targeting Protocol Summary:")
    print(f"      • Repo Detective: {len(github_dimensions)} dimensions")
    print(f"      • Doc Analyst: {len(pdf_dimensions)} dimensions")
    print(f"      • Vision Inspector: {len(image_dimensions)} dimensions")
    print(f"      • Chief Justice: {len(synthesis_rules)} rules")
    
    return state


# Quick test
if __name__ == "__main__":
    from src.state import AgentState
    
    test_state: AgentState = {
        "evidences": [],
        "opinions": [],
        "github_dimensions": [],
        "pdf_dimensions": [],
        "image_dimensions": [],
        "synthesis_rules": {},
        "rubric": {},
        "final_report": None,
        "errors": []
    }
    
    result = context_builder(test_state)
    print(f"\n✅ ContextBuilder executed successfully")
    print(f"   GitHub dimensions: {len(result['github_dimensions'])}")