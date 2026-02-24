"""
STEP 11 — Export Trace Logs (FIXED VERSION)
Save trace to: audit/langsmith_logs/trace_run_01.json
Handles UUID and datetime serialization properly
"""

from langsmith import Client
import json
from pathlib import Path
from dotenv import load_dotenv
from uuid import UUID
from datetime import datetime
import os

# Custom JSON encoder to handle UUID and datetime objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)  # Convert UUID to string
        if isinstance(obj, datetime):
            return obj.isoformat()  # Convert datetime to ISO format
        if hasattr(obj, 'model_dump'):  # Handle Pydantic v2 models
            return obj.model_dump()
        if hasattr(obj, 'dict'):  # Handle Pydantic v1 models
            return obj.dict()
        # Let the base class default method raise the TypeError
        return super().default(obj)

# Load your API key from .env
load_dotenv()

# Verify API key is loaded
if not os.getenv('LANGSMITH_API_KEY'):
    print("❌ LANGSMITH_API_KEY not found in .env file!")
    print("Please check your .env file contains: LANGSMITH_API_KEY=lsv2_pt_your_key_here")
    exit(1)

# Your trace ID from LangSmith
trace_id = "019c8efd-9ac1-7980-9b08-683b4a35ab99"

# Create directory if it doesn't exist (using lowercase for consistency)
log_dir = Path("audit/langsmith_logs")
log_dir.mkdir(parents=True, exist_ok=True)
file_path = log_dir / "trace_run_01.json"

print("🔍 Exporting trace from LangSmith...")
print(f"📁 Saving to: {file_path}")
print(f"🆔 Trace ID: {trace_id}")
print(f"🔑 API Key found: {os.getenv('LANGSMITH_API_KEY')[:10]}...")  # Show first 10 chars

try:
    # Initialize LangSmith client
    client = Client()
    
    # Fetch the trace
    print("📡 Fetching trace data...")
    run = client.read_run(trace_id)
    
    # Convert the run to a dictionary
    # First check if it has model_dump (Pydantic v2) or dict (Pydantic v1)
    if hasattr(run, 'model_dump'):
        print("📦 Using model_dump() (Pydantic v2)")
        run_dict = run.model_dump()
    elif hasattr(run, 'dict'):
        print("📦 Using dict() (Pydantic v1)")
        run_dict = run.dict()
    else:
        # If it's already a dict, use it directly
        print("📦 Run is already a dictionary")
        run_dict = run
    
    # Save as JSON with custom encoder
    print("💾 Saving to file...")
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(run_dict, f, indent=2, cls=CustomJSONEncoder)
    
    # Verify file was created
    if file_path.exists():
        file_size = file_path.stat().st_size
        print("\n✅ SUCCESS! Trace exported successfully!")
        print(f"📍 Location: {file_path.absolute()}")
        print(f"📊 File size: {file_size:,} bytes")
        
        # Show preview
        print("\n📋 Preview (first 500 chars):")
        with open(file_path, 'r', encoding='utf-8') as f:
            preview = f.read(500)
            print(preview + "...")
            
        # Show full path for easy copying
        print(f"\n📁 Full path: {file_path.absolute()}")
    else:
        print("❌ Failed to create file")
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure required packages are installed:")
    print("pip install langsmith python-dotenv")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    print("\nTroubleshooting:")
    print("1. Check your LANGSMITH_API_KEY in .env")
    print("2. Verify the trace ID is correct")
    print("3. Make sure you're connected to the internet")
    print("4. Try running: pip install --upgrade langsmith")