#!/usr/bin/env python3
"""
Test script for DocAnalyst with Gemini
Run this to analyze your PDF documentation
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.tools.doc_tools import analyze_documentation
import json

def main():
    print("📄 DocAnalyst Test - PDF Documentation Analyzer (Gemini)")
    print("="*60)
    
    # Ask for PDF path
    pdf_path = input("\nEnter path to PDF file: ").strip()
    
    if not pdf_path or not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    # Ask for repo evidence (optional)
    repo_evidence_path = None
    use_repo = input("\nDo you have repo evidence from RepoInvestigator? (y/n): ").strip().lower()
    if use_repo == 'y':
        default_path = "audit/repo_evidence.json"
        repo_evidence_path = input(f"Enter path to repo_evidence.json [{default_path}]: ").strip()
        if not repo_evidence_path:
            repo_evidence_path = default_path
        
        if not Path(repo_evidence_path).exists():
            print(f"⚠️  Repo evidence not found at {repo_evidence_path}")
            print("   Continuing without cross-checking...")
            repo_evidence_path = None
    
    # Run analysis
    try:
        print("\n" + "="*60)
        print("🚀 Starting PDF Analysis with Gemini...")
        print("="*60)
        
        results = analyze_documentation(pdf_path, repo_evidence_path)
        
        # Save results
        output_dir = Path("audit")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "doc_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📝 Analysis saved to: {output_file}")
        
        # Show summary
        if "error" in results:
            print(f"\n❌ Error: {results['error']}")
            return
        
        print("\n📊 FINAL SUMMARY")
        print("="*60)
        
        # Theoretical depth summary
        depth = results.get('theoretical_depth', {})
        summary = depth.get('summary', {})
        print(f"\n📚 Theoretical Depth:")
        print(f"   - Real explanations: {summary.get('real_explanations', 0)}/{summary.get('total_concepts', 0)}")
        print(f"   - Buzzword only: {summary.get('buzzword_only', 0)}")
        print(f"   - Depth score: {summary.get('depth_score', 0):.2%}")
        
        # Path verification summary
        paths = results.get('path_verification', {})
        print(f"\n🔍 Path Verification:")
        print(f"   - Total paths: {paths.get('total_paths', 0)}")
        print(f"   - Verified: {len(paths.get('verified_paths', []))}")
        print(f"   - Hallucinated: {len(paths.get('hallucinated_paths', []))}")
        print(f"   - Verification rate: {paths.get('verification_rate', 0):.1%}")
        
        # Quality assessment
        print(f"\n⭐ QUALITY ASSESSMENT:")
        depth_score = summary.get('depth_score', 0)
        verification_rate = paths.get('verification_rate', 0)
        
        if depth_score > 0.6 and verification_rate > 0.7:
            print("   ✅ HIGH QUALITY - Good theoretical depth and accurate paths")
        elif depth_score > 0.4 or verification_rate > 0.5:
            print("   ⚠️  MEDIUM QUALITY - Some good content but needs improvement")
        else:
            print("   ❌ LOW QUALITY - Mostly buzzwords or missing content")
        
        # Model info
        print(f"\n🤖 Model used: {results.get('model_used', 'gemini')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()