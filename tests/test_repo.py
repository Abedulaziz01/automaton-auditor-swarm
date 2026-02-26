#!/usr/bin/env python3
# tests/test_step1_1.py - Test Git Forensics only

import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.tools.repo_tools import RepoInvestigator

def main():
    print("\n" + "🎯"*20)
    print("TESTING STEP 1.1: GIT FORENSICS")
    print("🎯"*20)
    
    # Ask for repo
    repo_path = input("\nEnter repo path (local or GitHub URL): ").strip()
    
    if not repo_path:
        print("❌ No repo provided")
        return
    
    # Create investigator and test git analysis
    investigator = RepoInvestigator(repo_path)
    
    try:
        investigator.setup()
        results = investigator.analyze_git_history()
        
        # Save results
        output_file = Path('step1_1_results.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Results saved to {output_file}")
        
        # Verification checklist
        print("\n" + "✓"*40)
        print("VERIFICATION CHECKLIST:")
        print("✓"*40)
        print("☐ Can you see commit messages and timestamps?")
        print("☐ Does it detect if there are at least 3 commits?")
        print("☐ Does it flag monolithic first commits?")
        print("☐ Is output structured as JSON?")
        
        # Show a preview of the results
        print("\n📋 Results preview:")
        print(json.dumps(results, indent=2, default=str)[:500] + "...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        investigator.cleanup()

if __name__ == "__main__":
    main()