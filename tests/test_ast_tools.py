# tests/test_ast_tools.py
import sys
import os
sys.path.insert(0, os.getcwd())

from pathlib import Path
from src.tools.ast_tools import ASTAnalyzer
from src.tools.repo_tools import GitAnalyzer

def test_step3():
    print("\n🔬 TESTING STEP 3: AST and Git Tools")
    print("=" * 50)
    
    # Test 1: AST Parser
    print("\n📊 Test 3.1: AST Parser")
    
    # Create a test Python file
    test_file = Path("test_temp.py")
    with open(test_file, 'w') as f:
        f.write("""
from pydantic import BaseModel

class TestModel(BaseModel):
    name: str
    value: int

def test_function():
    return TestModel(name="test", value=123)
""")
    
    tree = ASTAnalyzer.parse_python_file(test_file)
    if tree:
        print("✅ AST Parser working")
        
        # Test class finding
        classes = ASTAnalyzer.find_class_definitions(tree, 'BaseModel')
        print(f"   Found {len(classes)} BaseModel classes")
        
        # Test function calls
        calls = ASTAnalyzer.find_function_calls(tree, 'TestModel')
        print(f"   Found {len(calls)} TestModel calls")
        
        # Test graph detection
        graph = ASTAnalyzer.detect_graph_structure(tree)
        print(f"   Graph detection: has_stategraph={graph['has_stategraph']}")
        
        # Test safety checks
        safety = ASTAnalyzer.check_tool_safety(tree)
        print(f"   Safety checks: {len(safety)} issues found")
    else:
        print("❌ AST Parser failed")
    
    test_file.unlink()  # Clean up
    
    # Test 2: Git Tools (if in git repo)
    print("\n📊 Test 3.2: Git Tools")
    git = GitAnalyzer(Path("."))
    
    commits = git.get_commit_history(max_count=3)
    if commits:
        print(f"✅ Git tools working")
        print(f"   Found {len(commits)} commits")
        for i, c in enumerate(commits):
            print(f"   Commit {i+1}: {c['hash'][:8]} - {c['subject'][:50]}")
        
        # Test monolithic detection
        mono = git.detect_monolithic_init()
        print(f"   Monolithic init: {mono['is_monolithic']}")
        
        # Test progression
        prog = git.get_commit_progression()
        print(f"   Has progression: {prog.get('has_progression', False)}")
    else:
        print("ℹ️ Not in a git repository or no commits found")

if __name__ == "__main__":
    test_step3()