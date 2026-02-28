#!/bin/bash

echo "========================================="
echo "📊 PHASE 5: EXECUTIVE AUDIT REPORT"
echo "========================================="

# Step 1: Check for required files
echo -e "\n📂 Checking for audit data..."

if [ ! -d "audit" ]; then
    echo "⚠️  No audit directory found. Creating sample data..."
    python generate_sample_reports.py
fi

# Step 2: Generate peer review report
echo -e "\n📝 Generating PEER REVIEW report..."
python src/report_generator.py --type peer

# Step 3: Generate self-assessment report
echo -e "\n📝 Generating SELF-ASSESSMENT report..."
python src/report_generator.py --type self

# Step 4: Show generated files
echo -e "\n📁 Generated Reports:"
ls -la audit/report_*/governance_*.md 2>/dev/null || echo "No reports found"

# Step 5: Preview peer review report
echo -e "\n📋 Preview of Peer Review Report:"
echo "========================================="
PEER_REPORT=$(ls audit/report_peer*/governance_*.md 2>/dev/null | head -1)
if [ -f "$PEER_REPORT" ]; then
    cat "$PEER_REPORT" | head -30
    echo -e "\n... (truncated, see full report for complete audit)"
else
    echo "No peer report found"
fi

echo -e "\n========================================="
echo "✅ PHASE 5 COMPLETE"
echo "========================================="
echo -e "\n📊 Reports saved to:"
echo "   - audit/report_peergenerated/"
echo "   - audit/report_selfgenerated/"
echo -e "\n🔍 Review the Markdown files for complete governance audit"