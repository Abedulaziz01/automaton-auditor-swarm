"""
Test LangSmith tracing with Gemini - FIXED VERSION
"""

import os
import time
from dotenv import load_dotenv
from src.graph import AuditorGraph
from langsmith import Client

# Load environment variables
load_dotenv(override=True)  # Force reload of env vars

print("🔍 Testing LangSmith connection...")
print(f"LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
print(f"LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT')}")
print(f"GOOGLE_API_KEY exists: {bool(os.getenv('GOOGLE_API_KEY'))}")
print(f"LANGSMITH_API_KEY exists: {bool(os.getenv('LANGSMITH_API_KEY'))}")

# Also check LangSmith endpoint (sometimes needed)
print(f"LANGSMITH_ENDPOINT: {os.getenv('LANGSMITH_ENDPOINT', 'not set')}")

# Initialize client to verify connection
try:
    client = Client()
    print("✅ LangSmith client initialized successfully")
except Exception as e:
    print(f"❌ LangSmith client failed: {e}")

# Run a test graph
auditor = AuditorGraph()
result = auditor.run_graph("test_repo", "test.pdf")

# CRITICAL: Wait for traces to upload
print("\n⏳ Waiting for traces to upload to LangSmith...")
time.sleep(5)  # Give it 5 seconds

# Force flush all pending traces
try:
    client.wait_for_all_tracers()  # This waits for all async traces
    print("✅ Traces flushed successfully")
except Exception as e:
    print(f"⚠️ Warning during flush: {e}")

# Check if the trace was actually created
try:
    # Look for recent runs in your project
    recent_runs = list(client.list_runs(
        project_name=os.getenv('LANGCHAIN_PROJECT'),
        execution_order=1,
        limit=5
    ))
    
    if recent_runs:
        print(f"\n📊 Found {len(recent_runs)} recent traces:")
        for i, run in enumerate(recent_runs):
            print(f"\n  Trace {i+1}:")
            print(f"    ID: {run.id}")
            print(f"    Name: {run.name}")
            print(f"    Start time: {run.start_time}")
            print(f"    URL: https://smith.langchain.com/runs/{run.id}")
    else:
        print("\n❌ No traces found yet. They might still be processing.")
        print("   Check the LangSmith dashboard in 1-2 minutes.")
        
except Exception as e:
    print(f"\n❌ Could not verify traces: {e}")

print("\n✅ Test complete. Please check the LangSmith dashboard!")
print("If traces still don't appear, run the diagnostic script below.")