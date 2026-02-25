from src.state import AgentState, Evidence

def repo_detective(state: AgentState) -> dict:
    """GitHub Repository Detective - Returns ONLY updates"""
    print("   🔍 Repo detective analyzing...")
    
    updates = {}
    
    # Example: Add evidence if found
    # if some_condition:
    #     evidence = Evidence(...)
    #     # Use the state's evidence ID or create a new one
    #     evidence_id = f"repo_ev_{len(state.get('evidences', {}))}"
    #     updates["evidences"] = {evidence_id: evidence}
    
    # Example: Add an error if something went wrong
    # if some_error:
    #     updates["errors"] = ["Repo detective: something went wrong"]
    
    # ⭐ IMPORTANT: Do NOT include 'repo_url', 'pdf_path', etc. in the return dict
    return updates

def doc_detective(state: AgentState) -> dict:
    """PDF Document Detective - Returns ONLY updates"""
    print("   📄 Doc detective analyzing...")
    # Return only the fields this node should change
    return {}  # Empty dict means no updates

def vision_detective(state: AgentState) -> dict:
    """Vision Detective - Returns ONLY updates"""
    print("   👁️ Vision detective analyzing...")
    # Return only the fields this node should change
    return {}  # Empty dict means no updates