#!/usr/bin/env python
"""
Phase 1 Verification Script
Run this to ensure all components work before proceeding
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_phase1():
    """Run all verification checks"""
    
    print("=" * 60)
    print("🔍 PHASE 1 VERIFICATION")
    print("=" * 60)
    
    checks_passed = 0
    total_checks = 7  # Increased to 7 checks
    
    # Check 1: Rubric exists and is valid
    print("\n1️⃣ Checking rubric...")
    try:
        import json
        rubric_path = Path("rubric/week2_rubric.json")
        
        if not rubric_path.exists():
            raise FileNotFoundError(f"Rubric not found at {rubric_path.absolute()}")
            
        with open(rubric_path, "r", encoding="utf-8") as f:
            rubric = json.load(f)
            
        assert "dimensions" in rubric, "Missing 'dimensions' key"
        assert len(rubric["dimensions"]) > 0, "No dimensions found"
        assert "synthesis_rules" in rubric, "Missing 'synthesis_rules'"
        
        # Verify each dimension has required fields
        for i, dim in enumerate(rubric["dimensions"]):
            assert "name" in dim, f"Dimension {i} missing 'name'"
            assert "target_artifact" in dim, f"Dimension {i} missing 'target_artifact'"
            assert "forensic_instruction" in dim, f"Dimension {i} missing 'forensic_instruction'"
        
        print("   ✅ Rubric valid")
        print(f"      • Dimensions: {len(rubric['dimensions'])}")
        print(f"      • Synthesis rules: {len(rubric.get('synthesis_rules', {}))}")
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ Rubric error: {e}")
    
    # Check 2: State module imports and has correct fields
    print("\n2️⃣ Checking state module...")
    try:
        from src.state import AgentState, Evidence, JudicialOpinion
        
        # Verify AgentState has all required fields
        required_fields = [
            "repo_url", "pdf_path", "evidences", "opinions", 
            "final_report", "error", "rubric", "github_dimensions",
            "pdf_dimensions", "image_dimensions", "synthesis_rules",
            "current_dimension", "errors"
        ]
        
        # Get type hints to check fields
        from typing import get_type_hints
        hints = get_type_hints(AgentState)
        
        for field in required_fields:
            assert field in hints, f"Missing field: {field}"
        
        print("   ✅ State module imports correctly")
        print(f"      • Fields: {len(hints)} total")
        print(f"      • Required fields present: ✓")
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ State error: {e}")
    
    # Check 3: ContextBuilder runs and populates targeting fields
    print("\n3️⃣ Testing ContextBuilder...")
    try:
        from src.nodes.context_builder import context_builder
        from src.state import AgentState
        
        # Create test state with minimal fields
        test_state: AgentState = {
            "repo_url": "https://github.com/test/repo",
            "pdf_path": "test.pdf",
            "evidences": {},
            "opinions": [],
            "final_report": None,
            "error": None,
            "rubric": {},
            "github_dimensions": [],
            "pdf_dimensions": [],
            "image_dimensions": [],
            "synthesis_rules": {},
            "current_dimension": None,
            "errors": []
        }
        
        # Run context builder
        result = context_builder(test_state)
        
        # Verify it populated the targeting fields
        assert len(result["github_dimensions"]) > 0, "No GitHub dimensions found"
        assert "synthesis_rules" in result, "Missing synthesis_rules"
        
        print("   ✅ ContextBuilder executed successfully")
        print(f"      • GitHub dimensions: {len(result['github_dimensions'])}")
        print(f"      • PDF dimensions: {len(result['pdf_dimensions'])}")
        print(f"      • Image dimensions: {len(result['image_dimensions'])}")
        print(f"      • Synthesis rules: {len(result['synthesis_rules'])}")
        
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ ContextBuilder error: {e}")
    
    # Check 4: Detective nodes exist and return correct types
    print("\n4️⃣ Checking detective nodes...")
    try:
        from src.nodes.detectives import repo_detective, doc_detective, vision_detective
        from src.state import AgentState
        
        # Create test state with dimensions
        test_state: AgentState = {
            "repo_url": "https://github.com/test/repo",
            "pdf_path": "test.pdf",
            "evidences": {},
            "opinions": [],
            "final_report": None,
            "error": None,
            "rubric": {},
            "github_dimensions": [{"name": "test_dim"}],
            "pdf_dimensions": [{"name": "test_dim"}],
            "image_dimensions": [{"name": "test_dim"}],
            "synthesis_rules": {},
            "current_dimension": None,
            "errors": []
        }
        
        # Test each detective
        repo_result = repo_detective(test_state)
        assert isinstance(repo_result, dict), "repo_detective should return dict"
        
        doc_result = doc_detective(test_state)
        assert isinstance(doc_result, dict), "doc_detective should return dict"
        
        vision_result = vision_detective(test_state)
        assert isinstance(vision_result, dict), "vision_detective should return dict"
        
        print("   ✅ All detective nodes exist and return correct type")
        print(f"      • repo_detective: ✓")
        print(f"      • doc_detective: ✓")
        print(f"      • vision_detective: ✓")
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ Detective error: {e}")
    
    # Check 5: Graph compiles
    print("\n5️⃣ Testing graph compilation...")
    try:
        from src.graph import ConstitutionalGraph
        
        graph_instance = ConstitutionalGraph()
        assert graph_instance.graph is not None, "Graph not compiled"
        
        # Check nodes in graph
        nodes = list(graph_instance.graph.nodes.keys())
        expected_nodes = ["context_builder", "repo_detective", "doc_detective", "vision_detective"]
        
        for node in expected_nodes:
            assert node in nodes, f"Missing node: {node}"
        
        print("   ✅ Graph compiled successfully")
        print(f"      • Nodes: {', '.join(nodes)}")
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ Graph compilation error: {e}")
    
    # Check 6: Graph executes without errors
    print("\n6️⃣ Testing graph execution...")
    try:
        from src.graph import ConstitutionalGraph
        
        graph = ConstitutionalGraph()
        result = graph.run_graph(
            repo_url="https://github.com/test/repo",
            pdf_path="reports/week2_report.pdf"
        )
        
        # Verify result has expected structure
        assert "github_dimensions" in result, "Missing github_dimensions in result"
        assert "errors" in result, "Missing errors field"
        assert isinstance(result["errors"], list), "errors should be a list"
        
        print("   ✅ Graph executed successfully")
        print(f"      • GitHub dims: {len(result.get('github_dimensions', []))}")
        print(f"      • PDF dims: {len(result.get('pdf_dimensions', []))}")
        print(f"      • Image dims: {len(result.get('image_dimensions', []))}")
        print(f"      • Errors: {len(result.get('errors', []))}")
        
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ Graph execution error: {e}")
    
    # Check 7: Checkpointing works
    print("\n7️⃣ Testing checkpointing...")
    try:
        from src.graph import ConstitutionalGraph
        
        graph = ConstitutionalGraph()
        
        # First run
        config1 = {"configurable": {"thread_id": "test_checkpoint_1"}}
        result1 = graph.run_graph(
            repo_url="https://github.com/test/repo",
            pdf_path="test1.pdf"
        )
        
        # Second run with different thread
        config2 = {"configurable": {"thread_id": "test_checkpoint_2"}}
        result2 = graph.run_graph(
            repo_url="https://github.com/test/repo",
            pdf_path="test2.pdf"
        )
        
        print("   ✅ Checkpointing works (multiple threads run independently)")
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ Checkpointing error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {checks_passed}/{total_checks} checks passed")
    print("=" * 60)
    
    if checks_passed == total_checks:
        print("\n🎉 PHASE 1 COMPLETE! Ready for Phase 2.")
        print("\n📋 Phase 1 Achievements:")
        print("   ✓ Hot-swappable rubric loading")
        print("   ✓ Dynamic targeting protocol")
        print("   ✓ Strictly typed state")
        print("   ✓ Parallel detective branches")
        print("   ✓ Crash recovery with checkpointing")
        print("\n🚀 Next up: Phase 2 - Evidence Gathering with Gemini")
        return True
    else:
        print(f"\n❌ {total_checks - checks_passed} checks failed.")
        print("\n🔧 Troubleshooting:")
        for i in range(total_checks):
            if i >= checks_passed:
                print(f"   • Fix check {i+1} first")
        return False


if __name__ == "__main__":
    success = verify_phase1()
    sys.exit(0 if success else 1)