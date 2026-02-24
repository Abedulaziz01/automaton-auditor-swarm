"""
Basic LangGraph with Checkpointer for crash recovery
This is your orchestration layer
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.state import AgentState
import time


class AuditorGraph:
    """Main graph orchestrator with crash recovery"""
    
    def __init__(self):
        self.graph = None
        self.build_graph()
    
    def build_graph(self):
        """Build the LangGraph with checkpointer"""
        
        # Initialize graph with our typed state
        builder = StateGraph(AgentState)
        
        # Add dummy nodes (we'll replace these later)
        builder.add_node("detective_node", self.detective_node)
        builder.add_node("judge_node", self.judge_node)
        builder.add_node("justice_node", self.justice_node)
        
        # Set entry point
        builder.set_entry_point("detective_node")
        
        # Add edges
        builder.add_edge("detective_node", "judge_node")
        builder.add_edge("judge_node", "justice_node")
        builder.add_edge("justice_node", END)
        
        # Add checkpointer for crash recovery (PRODUCTION REQUIREMENT)
        memory = MemorySaver()
        
        # Compile with checkpointer
        self.graph = builder.compile(checkpointer=memory)
        print("✅ Graph compiled with checkpointer")
        
        return self.graph
    
    # Dummy node implementations
    def detective_node(self, state: AgentState):
        """Dummy detective - will be replaced"""
        print("🔍 Detective node running...")
        # Simulate work
        time.sleep(1)
        print("✅ Detective node complete")
        return state
    
    def judge_node(self, state: AgentState):
        """Dummy judge - will be replaced"""
        print("⚖️ Judge node running...")
        time.sleep(1)
        print("✅ Judge node complete")
        return state
    
    def justice_node(self, state: AgentState):
        """Dummy justice - will be replaced"""
        print("👨‍⚖️ Justice node running...")
        time.sleep(1)
        print("✅ Justice node complete")
        return state
    
    def run_graph(self, repo_url: str, pdf_path: str):
        """Run the graph with checkpointing"""
        
        # Initial state
        initial_state = {
            "repo_url": repo_url,
            "pdf_path": pdf_path,
            "evidences": {},
            "opinions": [],
            "final_report": None,
            "error": None
        }
        
        # Thread ID enables checkpoint recovery
        config = {
            "configurable": {
                "thread_id": "audit_session_1"
            }
        }
        
        print("\n🎬 Starting graph execution...")
        final_state = self.graph.invoke(initial_state, config)
        print("✅ Graph execution complete")
        
        return final_state


# Simple test
if __name__ == "__main__":
    # Create and run graph
    auditor = AuditorGraph()
    result = auditor.run_graph("https://github.com/test/repo", "test.pdf")
    print("\n📊 Final state:", result.keys())