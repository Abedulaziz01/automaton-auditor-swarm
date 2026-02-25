"""
Basic LangGraph with Checkpointer for crash recovery
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
        builder = StateGraph(AgentState)
        
        # Add dummy nodes
        builder.add_node("detective_node", self.detective_node)
        builder.add_node("judge_node", self.judge_node)
        builder.add_node("justice_node", self.justice_node)
        
        # Set entry point and edges
        builder.set_entry_point("detective_node")
        builder.add_edge("detective_node", "judge_node")
        builder.add_edge("judge_node", "justice_node")
        builder.add_edge("justice_node", END)
        
        # Add checkpointer
        memory = MemorySaver()
        self.graph = builder.compile(checkpointer=memory)
        print("✅ Graph compiled with checkpointer")
        return self.graph
    
    def detective_node(self, state: AgentState):
        print("🔍 Detective node running...")
        time.sleep(1)
        print("✅ Detective node complete")
        return state
    
    def judge_node(self, state: AgentState):
        print("⚖️ Judge node running...")
        time.sleep(1)
        print("✅ Judge node complete")
        return state
    
    def justice_node(self, state: AgentState):
        print("👨‍⚖️ Justice node running...")
        time.sleep(1)
        print("✅ Justice node complete")
        return state
    
    def run_graph(self, repo_url: str, pdf_path: str):
        initial_state = {
            "repo_url": repo_url,
            "pdf_path": pdf_path,
            "evidences": {},
            "opinions": [],
            "final_report": None,
            "error": None
        }
        
        config = {"configurable": {"thread_id": "audit_session_1"}}
        
        print("\n🎬 Starting graph execution...")
        final_state = self.graph.invoke(initial_state, config)
        print("✅ Graph execution complete")
        return final_state


if __name__ == "__main__":
    auditor = AuditorGraph()
    result = auditor.run_graph("https://github.com/test/repo", "test.pdf")
    print("\n📊 Final state:", result.keys())