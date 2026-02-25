"""
Constitutional LangGraph with Targeting Protocol
START → ContextBuilder → Detectives (Parallel) → END
"""

# ===== PATH FIX - ADD THIS FIRST =====
import sys
from pathlib import Path
# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
# =====================================

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.state import AgentState
from src.nodes.context_builder import context_builder
from src.nodes.detectives import repo_detective, doc_detective, vision_detective
import time


class ConstitutionalGraph:
    """Main graph orchestrator with constitutional routing"""
    
    def __init__(self):
        self.graph = None
        self.build_graph()
    
    def build_graph(self):
        """Build the LangGraph with:
        - ContextBuilder (constitutional loader)
        - Parallel detectives (targeting protocol)
        - Checkpointer for crash recovery
        """
        builder = StateGraph(AgentState)
        
        # ===== ADD NODES =====
        print("🔨 Building Constitutional Graph...")
        
        # Constitution Engine
        builder.add_node("context_builder", context_builder)
        print("  ├─ Added ContextBuilder node")
        
        # Parallel Detectives (Targeting Protocol)
        builder.add_node("repo_detective", self.repo_detective_wrapper)
        builder.add_node("doc_detective", self.doc_detective_wrapper)
        builder.add_node("vision_detective", self.vision_detective_wrapper)
        print("  ├─ Added Detective nodes (Repo, Doc, Vision)")
        
        # ===== DEFINE EDGES =====
        # START → ContextBuilder
        builder.add_edge(START, "context_builder")
        print("  ├─ Edge: START → ContextBuilder")
        
        # ContextBuilder → ALL Detectives (Parallel Fan-out)
        builder.add_edge("context_builder", "repo_detective")
        builder.add_edge("context_builder", "doc_detective")
        builder.add_edge("context_builder", "vision_detective")
        print("  ├─ Edge: ContextBuilder → Detectives (PARALLEL)")
        
        # All Detectives → END (Parallel Fan-in)
        builder.add_edge("repo_detective", END)
        builder.add_edge("doc_detective", END)
        builder.add_edge("vision_detective", END)
        print("  └─ Edge: Detectives → END")
        
        # ===== ADD CHECKPOINTER =====
        memory = MemorySaver()
        self.graph = builder.compile(checkpointer=memory)
        print("✅ Graph compiled with checkpointer")
        
        return self.graph
    
    # ===== WRAPPER METHODS =====
    def repo_detective_wrapper(self, state: AgentState):
        """Wrapper for repo_detective with timing"""
        print("\n🕵️  Repo Detective starting...")
        start = time.time()
        
        new_state = repo_detective(state)
        
        elapsed = time.time() - start
        dim_count = len(new_state.get("github_dimensions", []))
        print(f"✅ Repo Detective complete ({elapsed:.2f}s) - {dim_count} dimensions assigned")
        
        return new_state
    
    def doc_detective_wrapper(self, state: AgentState):
        """Wrapper for doc_detective with timing"""
        print("\n📄 Doc Detective starting...")
        start = time.time()
        
        new_state = doc_detective(state)
        
        elapsed = time.time() - start
        dim_count = len(new_state.get("pdf_dimensions", []))
        print(f"✅ Doc Detective complete ({elapsed:.2f}s) - {dim_count} dimensions assigned")
        
        return new_state
    
    def vision_detective_wrapper(self, state: AgentState):
        """Wrapper for vision_detective with timing"""
        print("\n👁️  Vision Detective starting...")
        start = time.time()
        
        new_state = vision_detective(state)
        
        elapsed = time.time() - start
        dim_count = len(new_state.get("image_dimensions", []))
        print(f"✅ Vision Detective complete ({elapsed:.2f}s) - {dim_count} dimensions assigned")
        
        return new_state
    
    def run_graph(self, repo_url: str, pdf_path: str):
        """Execute the constitutional graph"""
        
        # Initial state with all required fields
        initial_state: AgentState = {
            # Original fields
            "repo_url": repo_url,
            "pdf_path": pdf_path,
            "evidences": {},
            "opinions": [],
            "final_report": None,
            "error": None,
            
            # New Phase 1 fields
            "rubric": {},
            "github_dimensions": [],
            "pdf_dimensions": [],
            "image_dimensions": [],
            "synthesis_rules": {},
            "current_dimension": None,
            "errors": []
        }
        
        # Configuration for checkpointing
        config = {
            "configurable": {
                "thread_id": f"audit_{int(time.time())}"
            }
        }
        
        print("\n" + "="*60)
        print("🎬 STARTING CONSTITUTIONAL GRAPH EXECUTION")
        print("="*60)
        print(f"📂 Repo: {repo_url}")
        print(f"📄 PDF: {pdf_path}")
        print(f"🆔 Thread: {config['configurable']['thread_id']}")
        print("="*60)
        
        # Run graph
        final_state = self.graph.invoke(initial_state, config)
        
        print("\n" + "="*60)
        print("✅ GRAPH EXECUTION COMPLETE")
        print("="*60)
        
        # Print summary
        self._print_summary(final_state)
        
        return final_state
    
    def _print_summary(self, state: AgentState):
        """Print execution summary"""
        print("\n📊 EXECUTION SUMMARY:")
        print(f"  • GitHub dimensions: {len(state.get('github_dimensions', []))}")
        print(f"  • PDF dimensions: {len(state.get('pdf_dimensions', []))}")
        print(f"  • Image dimensions: {len(state.get('image_dimensions', []))}")
        print(f"  • Synthesis rules: {len(state.get('synthesis_rules', {}))}")
        
        if state.get("errors"):
            print(f"\n⚠️  ERRORS: {len(state['errors'])}")
            for i, err in enumerate(state["errors"][:3]):
                print(f"     {i+1}. {err}")
        else:
            print(f"\n✅ No errors")
        
        print(f"\n📌 State keys: {list(state.keys())}")


if __name__ == "__main__":
    # Create and run graph
    graph = ConstitutionalGraph()
    result = graph.run_graph(
        repo_url="https://github.com/test/repo",
        pdf_path="reports/week2_report.pdf"
    )