#!/usr/bin/env python3
"""
Executive Audit Report Generator
Produces professional governance-grade Markdown reports
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import os

class AuditReportGenerator:
    """
    Generates professional Markdown audit reports from all investigation phases
    """
    
    def __init__(self, audit_type: str = "peer"):
        """
        Initialize report generator
        
        Args:
            audit_type: "peer" for peer review, "self" for self-assessment
        """
        self.audit_type = audit_type
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.report_date = datetime.now().strftime("%Y-%m-%d")
        
        # Load all evidence files
        self.repo_evidence = self._load_json("audit/repo_evidence.json")
        self.doc_analysis = self._load_json("audit/doc_analysis.json")
        self.vision_inspection = self._load_json("audit/vision_inspection.json")
        self.judicial_opinions = self._load_json("audit/judicial_opinions.json")
        self.final_verdict = self._load_json("audit/final_verdict.json")
        
        # If no final verdict, create from opinions
        if not self.final_verdict and self.judicial_opinions:
            self.final_verdict = self._synthesize_from_opinions()
    
    def _load_json(self, path: str) -> Optional[Dict]:
        """Load JSON file if it exists"""
        if Path(path).exists():
            with open(path, 'r') as f:
                return json.load(f)
        return None
    
    def _synthesize_from_opinions(self) -> Dict:
        """Create synthetic verdict if final_verdict missing"""
        if not self.judicial_opinions:
            return {}
        
        opinions = []
        for result in self.judicial_opinions.get('panel_results', []):
            for op in result.get('opinions', []):
                opinions.append(op)
        
        # Count verdicts
        verdict_counts = {"pass": 0, "warn": 0, "fail": 0}
        for op in opinions:
            verdict_counts[op.get('verdict', 'warn')] += 1
        
        # Calculate score
        total = sum(verdict_counts.values())
        if total > 0:
            score = (verdict_counts['pass'] * 5 + verdict_counts['warn'] * 3) / total
        else:
            score = 0
        
        return {
            "overall_score": score,
            "dimension_scores": [],
            "security_override_triggered": False,
            "high_variance_dimensions": [],
            "remediation_plan": [],
            "dissent_summary": "No dissenting opinions recorded"
        }
    
    def generate_report(self) -> str:
        """
        Generate complete audit report
        """
        report = []
        
        # Header
        report.append(self._generate_header())
        
        # Executive Summary
        report.append(self._generate_executive_summary())
        
        # Security Flags
        report.append(self._generate_security_flags())
        
        # Criterion Breakdown
        report.append(self._generate_criterion_breakdown())
        
        # Architectural Risk Assessment
        report.append(self._generate_risk_assessment())
        
        # Governance Readiness
        report.append(self._generate_governance_readiness())
        
        # Footer
        report.append(self._generate_footer())
        
        return "\n\n".join(report)
    
    def _generate_header(self) -> str:
        """Generate report header with metadata"""
        audit_type_display = "PEER REVIEW" if self.audit_type == "peer" else "SELF-ASSESSMENT"
        
        return f"""# 🏛️ GOVERNANCE AUDIT REPORT: {audit_type_display}

**Report ID:** `AUDIT-{self.report_date.replace('-', '')}-{self.audit_type.upper()}`
**Date:** {self.report_date}
**Generated:** {self.timestamp}
**Audit Type:** {audit_type_display}
**Status:** Final

---

"""
    
    def _generate_executive_summary(self) -> str:
        """Generate executive summary section"""
        score = self.final_verdict.get('overall_score', 0) if self.final_verdict else 0
        security_issues = len(self.final_verdict.get('security_findings', [])) if self.final_verdict else 0
        dimensions = len(self.final_verdict.get('dimension_scores', [])) if self.final_verdict else 0
        remediations = len(self.final_verdict.get('remediation_plan', [])) if self.final_verdict else 0
        
        # Determine readiness level
        if score >= 4.0:
            readiness = "✅ READY FOR PRODUCTION"
            readiness_desc = "The system demonstrates excellent governance practices and is ready for deployment."
        elif score >= 3.0:
            readiness = "⚠️ CONDITIONALLY READY"
            readiness_desc = "The system meets minimum governance standards but requires remediation of identified issues."
        else:
            readiness = "❌ NOT READY"
            readiness_desc = "Critical governance gaps identified. Deployment not recommended until remediation is complete."
        
        return f"""## 📊 Executive Summary

This audit assesses the governance readiness of the autonomous agent system. The evaluation combines forensic evidence analysis, multi-perspective judicial review, and deterministic rule application to produce a comprehensive governance score.

### Key Findings

| Metric | Value |
|--------|-------|
| **Overall Governance Score** | {score:.1f}/5.0 |
| **Security Findings** | {security_issues} |
| **Dimensions Analyzed** | {dimensions} |
| **Remediation Items** | {remediations} |
| **Audit Confidence** | {self._calculate_confidence()}% |

### Readiness Assessment

**{readiness}**
{readiness_desc}

### Critical Highlights

{self._get_critical_highlights()}
"""
    
    def _calculate_confidence(self) -> int:
        """Calculate overall confidence score"""
        if not self.judicial_opinions:
            return 0
        
        opinions = []
        for result in self.judicial_opinions.get('panel_results', []):
            for op in result.get('opinions', []):
                opinions.append(op)
        
        if not opinions:
            return 0
        
        avg_confidence = sum(op.get('confidence', 0) for op in opinions) / len(opinions)
        return int(avg_confidence * 100)
    
    def _get_critical_highlights(self) -> str:
        """Extract critical findings for executive summary"""
        highlights = []
        
        # Security issues
        if self.final_verdict and self.final_verdict.get('security_override_triggered'):
            highlights.append("- 🔒 **Security Override Applied:** Critical security issues detected, scores capped at 3")
        
        # High variance dimensions
        high_var = self.final_verdict.get('high_variance_dimensions', []) if self.final_verdict else []
        if high_var:
            highlights.append(f"- 📊 **High Variance Detected:** {', '.join(high_var)} require re-evaluation")
        
        # Top remediation
        remediations = self.final_verdict.get('remediation_plan', []) if self.final_verdict else []
        if remediations:
            highlights.append(f"- 🔧 **Top Priority:** {remediations[0].get('action', 'Remediation required')}")
        
        if not highlights:
            highlights.append("- ✅ No critical issues detected")
        
        return "\n".join(highlights)
    
    def _generate_security_flags(self) -> str:
        """Generate security flags section"""
        security_findings = self.final_verdict.get('security_findings', []) if self.final_verdict else []
        
        if not security_findings:
            return """## 🔒 Security Flags

✅ **No security issues detected.** The codebase demonstrates secure coding practices.

| Risk Level | Count |
|------------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 0 |

"""
        
        # Count by risk level
        risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in security_findings:
            risk = finding.get('risk_level', '').lower()
            if risk in risk_counts:
                risk_counts[risk] += 1
        
        table = f"""## 🔒 Security Flags

⚠️ **Security issues detected that impact governance readiness.**

### Risk Summary

| Risk Level | Count |
|------------|-------|
| Critical | {risk_counts['critical']} |
| High | {risk_counts['high']} |
| Medium | {risk_counts['medium']} |
| Low | {risk_counts['low']} |

### Detailed Findings

"""
        
        for finding in security_findings:
            table += f"""#### {finding.get('finding', 'Security Issue')}
- **Risk Level:** {finding.get('risk_level', 'UNKNOWN').upper()}
- **Location:** `{finding.get('file_path', 'Unknown')}`
- **Evidence ID:** `{finding.get('evidence_id', 'N/A')}`
- **Impact:** This vulnerability could lead to {self._get_impact_description(finding.get('risk_level', ''))}

"""
        
        return table
    
    def _get_impact_description(self, risk_level: str) -> str:
        """Get impact description based on risk level"""
        impacts = {
            "critical": "remote code execution or complete system compromise",
            "high": "unauthorized access or data breach",
            "medium": "partial system compromise or data exposure",
            "low": "minor information disclosure or best practice violation"
        }
        return impacts.get(risk_level.lower(), "security degradation")
    
    def _generate_criterion_breakdown(self) -> str:
        """Generate detailed breakdown by criterion"""
        if not self.judicial_opinions:
            return "## 📋 Criterion Breakdown\n\nNo criterion data available."
        
        sections = ["## 📋 Criterion Breakdown\n"]
        
        # Group opinions by dimension
        dimensions = {}
        for result in self.judicial_opinions.get('panel_results', []):
            dim_name = result.get('dimension', 'Unknown')
            dimensions[dim_name] = {
                'opinions': result.get('opinions', []),
                'collusion': result.get('collusion', {})
            }
        
        for dim_name, data in dimensions.items():
            sections.append(self._generate_dimension_section(dim_name, data))
        
        return "\n".join(sections)
    
    def _generate_dimension_section(self, dim_name: str, data: Dict) -> str:
        """Generate section for a single dimension"""
        opinions = data['opinions']
        
        # Separate opinions by persona
        prosecutor = next((o for o in opinions if 'Prosecutor' in o.get('reasoning', '')), None)
        defense = next((o for o in opinions if 'Defense' in o.get('reasoning', '')), None)
        tech_lead = next((o for o in opinions if 'TechLead' in o.get('reasoning', '')), None)
        
        # Get final verdict for this dimension
        final_score = None
        if self.final_verdict:
            for ds in self.final_verdict.get('dimension_scores', []):
                if ds.get('dimension') == dim_name:
                    final_score = ds
                    break
        
        # Get evidence summary
        evidence_summary = self._get_evidence_for_dimension(dim_name)
        
        # Get remediation for this dimension
        remediation = self._get_remediation_for_dimension(dim_name)
        
        # Get dissent
        dissent = self._get_dissent_for_dimension(dim_name)
        
        # Build section
        section = f"""
### 🔍 {dim_name.replace('_', ' ').title()}

**Rubric Dimension ID:** `dimension.{dim_name}`

#### Evidence Summary
{evidence_summary}

#### Judicial Opinions

"""
        if prosecutor:
            verdict = prosecutor.get('verdict', 'unknown').upper()
            confidence = prosecutor.get('confidence', 0) * 100
            reasoning = prosecutor.get('reasoning', '').split(']')[-1].strip()
            section += f"""**Prosecutor Opinion** (Verdict: {verdict} | Confidence: {confidence:.0f}%)
> {reasoning}

"""
        
        if defense:
            verdict = defense.get('verdict', 'unknown').upper()
            confidence = defense.get('confidence', 0) * 100
            reasoning = defense.get('reasoning', '').split(']')[-1].strip()
            section += f"""**Defense Opinion** (Verdict: {verdict} | Confidence: {confidence:.0f}%)
> {reasoning}

"""
        
        if tech_lead:
            verdict = tech_lead.get('verdict', 'unknown').upper()
            confidence = tech_lead.get('confidence', 0) * 100
            reasoning = tech_lead.get('reasoning', '').split(']')[-1].strip()
            section += f"""**Tech Lead Opinion** (Verdict: {verdict} | Confidence: {confidence:.0f}%)
> {reasoning}

"""
        
        # Final Verdict
        if final_score:
            score = final_score.get('score', 0)
            flags = []
            if final_score.get('security_override_applied'):
                flags.append("Security Override Applied")
            if final_score.get('fact_supremacy_applied'):
                flags.append("Fact Supremacy Applied")
            if final_score.get('variance_detected'):
                flags.append("High Variance Detected")
            
            flag_text = f" ({', '.join(flags)})" if flags else ""
            
            section += f"""#### Final Verdict
**Score:** {score}/5.0{flag_text}
**Reasoning:** {final_score.get('reasoning', 'No reasoning provided')}

"""
        
        # Dissent Summary
        if dissent:
            section += f"""#### Dissent Summary
{dissent}

"""
        
        # Remediation Plan
        if remediation:
            section += f"""#### Remediation Plan
{remediation}

"""
        
        return section
    
    def _get_evidence_for_dimension(self, dim_name: str) -> str:
        """Get evidence summary for a dimension"""
        evidence_items = []
        
        # Check repo evidence
        if self.repo_evidence:
            for key, value in self.repo_evidence.items():
                if dim_name.lower() in key.lower() or any(dim_name.lower() in str(v).lower() for v in value.values() if isinstance(v, dict)):
                    evidence_items.append(f"- `{key}`: Repository structure analysis")
        
        # Check doc analysis
        if self.doc_analysis:
            depth = self.doc_analysis.get('theoretical_depth', {})
            if depth.get(dim_name):
                evidence_items.append(f"- Documentation analysis shows {depth[dim_name]}")
        
        # Check vision
        if self.vision_inspection and 'diagram_details' in self.vision_inspection:
            for diagram in self.vision_inspection['diagram_details']:
                if dim_name.lower() in str(diagram).lower():
                    evidence_items.append(f"- Page {diagram.get('page', '?')}: Architecture diagram analyzed")
        
        if not evidence_items:
            return "No direct evidence found for this dimension.\n"
        
        return "\n".join(evidence_items) + "\n"
    
    def _get_remediation_for_dimension(self, dim_name: str) -> str:
        """Get remediation actions for a dimension"""
        if not self.final_verdict:
            return "No remediation plan available."
        
        remediations = []
        for action in self.final_verdict.get('remediation_plan', []):
            if dim_name.lower() in action.get('action', '').lower() or dim_name.lower() in action.get('reasoning', '').lower():
                priority = action.get('priority', 'MEDIUM')
                action_text = action.get('action', 'No action specified')
                reasoning = action.get('reasoning', '')
                
                remediations.append(f"""**Priority:** {priority}
**Action:** {action_text}
**Why:** {reasoning}
""")
        
        if not remediations:
            return "No specific remediation required for this dimension."
        
        return "\n".join(remediations)
    
    def _get_dissent_for_dimension(self, dim_name: str) -> str:
        """Get dissenting opinions for a dimension"""
        if not self.final_verdict:
            return "No dissenting opinions recorded."
        
        dissent_summary = self.final_verdict.get('dissent_summary', '')
        if dim_name.lower() in dissent_summary.lower():
            return dissent_summary
        
        return "No significant dissent for this dimension."
    
    def _generate_risk_assessment(self) -> str:
        """Generate architectural risk assessment"""
        # Calculate risks based on findings
        security_risk = "HIGH" if self.final_verdict and self.final_verdict.get('security_override_triggered') else "LOW"
        
        variance_risk = "HIGH" if self.final_verdict and len(self.final_verdict.get('high_variance_dimensions', [])) > 0 else "LOW"
        
        # Get architectural issues from vision inspection
        arch_issues = []
        if self.vision_inspection:
            missing_patterns = self.vision_inspection.get('missing_patterns', [])
            if missing_patterns:
                arch_issues = missing_patterns
        
        overall_risk = "HIGH" if security_risk == "HIGH" or variance_risk == "HIGH" else "MEDIUM" if arch_issues else "LOW"
        
        return f"""## 🏗️ Architectural Risk Assessment

### Risk Matrix

| Risk Category | Level | Impact |
|---------------|-------|--------|
| Security Risk | {security_risk} | {'Critical system vulnerability' if security_risk == 'HIGH' else 'Minor security concerns'} |
| Architectural Consistency | {variance_risk} | {'Inconsistent implementation across components' if variance_risk == 'HIGH' else 'Good architectural alignment'} |
| Documentation Completeness | {self._get_doc_risk()} | Based on theoretical depth analysis |
| **Overall Risk** | **{overall_risk}** | {self._get_overall_risk_description(overall_risk)} |

### Key Architectural Findings

{self._get_architectural_findings()}

### Risk Mitigation Priorities

1. **Address security findings** - {security_risk} priority
2. **Resolve high variance dimensions** - {variance_risk} priority
3. **Implement remediation plan** - {len(self.final_verdict.get('remediation_plan', []))} items to address
"""
    
    def _get_doc_risk(self) -> str:
        """Calculate documentation risk"""
        if not self.doc_analysis:
            return "UNKNOWN"
        
        depth = self.doc_analysis.get('theoretical_depth', {})
        summary = depth.get('summary', {})
        depth_score = summary.get('depth_score', 0)
        
        if depth_score >= 0.7:
            return "LOW"
        elif depth_score >= 0.4:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _get_overall_risk_description(self, risk: str) -> str:
        """Get description for overall risk level"""
        descriptions = {
            "HIGH": "Immediate attention required before production deployment",
            "MEDIUM": "Address identified issues within next sprint",
            "LOW": "Acceptable risk level, monitor during normal operations"
        }
        return descriptions.get(risk, "Risk level undetermined")
    
    def _get_architectural_findings(self) -> str:
        """Get architectural findings from vision inspection"""
        if not self.vision_inspection:
            return "- No architectural diagrams analyzed\n"
        
        findings = []
        
        # Check for parallel patterns
        if self.vision_inspection.get('parallel_detectives_verified'):
            findings.append("- ✅ Parallel detective pattern verified in diagrams")
        else:
            findings.append("- ❌ Parallel detective pattern not documented")
        
        if self.vision_inspection.get('evidence_aggregation_verified'):
            findings.append("- ✅ Evidence aggregation pattern verified")
        else:
            findings.append("- ❌ Evidence aggregation not shown")
        
        if self.vision_inspection.get('parallel_judges_verified'):
            findings.append("- ✅ Parallel judge pattern verified")
        else:
            findings.append("- ❌ Parallel judge pattern not documented")
        
        if self.vision_inspection.get('chief_justice_verified'):
            findings.append("- ✅ Chief Justice pattern verified")
        else:
            findings.append("- ❌ Chief Justice not shown in diagrams")
        
        arch_score = self.vision_inspection.get('architecture_score', 0)
        findings.append(f"- Architecture documentation score: {arch_score}/100")
        
        return "\n".join(findings)
    
    def _generate_governance_readiness(self) -> str:
        """Generate governance readiness assessment"""
        score = self.final_verdict.get('overall_score', 0) if self.final_verdict else 0
        
        if score >= 4.5:
            readiness = "PRODUCTION READY"
            criteria = "✅ All governance criteria met or exceeded"
            recommendation = "Approve for production deployment"
        elif score >= 3.5:
            readiness = "CONDITIONALLY READY"
            criteria = "⚠️ Most criteria met, minor issues identified"
            recommendation = "Approve with conditions - must address remediation items within 30 days"
        elif score >= 2.5:
            readiness = "DEVELOPMENT STAGE"
            criteria = "⚠️ Significant gaps in governance"
            recommendation = "Hold deployment - requires major remediation"
        else:
            readiness = "NOT READY"
            criteria = "❌ Critical governance failures"
            recommendation = "Reject - requires complete rework"
        
        return f"""## ✅ Governance Readiness

### Readiness Level: {readiness}

{criteria}

### Governance Scorecard

| Governance Dimension | Score | Status |
|---------------------|-------|--------|
| Security & Compliance | {self._get_dimension_score('security')}/5 | {self._get_status_icon('security')} |
| Code Quality | {self._get_dimension_score('orchestration')}/5 | {self._get_status_icon('orchestration')} |
| Documentation | {self._get_dimension_score('documentation')}/5 | {self._get_status_icon('documentation')} |
| Architecture | {self._get_dimension_score('architecture')}/5 | {self._get_status_icon('architecture')} |

### Final Recommendation

**{recommendation}**

### Required Actions Before Approval

{self._get_required_actions()}
"""
    
    def _get_dimension_score(self, dim_name: str) -> float:
        """Get score for a specific dimension"""
        if not self.final_verdict:
            return 0.0
        
        for ds in self.final_verdict.get('dimension_scores', []):
            if dim_name in ds.get('dimension', ''):
                return ds.get('score', 0)
        return 0.0
    
    def _get_status_icon(self, dim_name: str) -> str:
        """Get status icon for dimension"""
        score = self._get_dimension_score(dim_name)
        if score >= 4:
            return "✅"
        elif score >= 3:
            return "⚠️"
        else:
            return "❌"
    
    def _get_required_actions(self) -> str:
        """Get list of required actions before approval"""
        if not self.final_verdict:
            return "No actions specified."
        
        actions = []
        remediations = self.final_verdict.get('remediation_plan', [])
        
        for i, action in enumerate(remediations[:5], 1):
            priority = action.get('priority', 'MEDIUM')
            action_text = action.get('action', 'No action specified')
            actions.append(f"{i}. **[Priority: {priority}]** {action_text}")
        
        if not actions:
            actions.append("No remediation required - ready for approval")
        
        return "\n".join(actions)
    
    def _generate_footer(self) -> str:
        """Generate report footer"""
        return f"""---
*This audit report was generated automatically by the Autonomous Governance System.*
*Report ID: `AUDIT-{self.report_date.replace('-', '')}-{self.audit_type.upper()}`*
*For questions about this report, contact the governance committee.*

**END OF REPORT**
"""

    def save_report(self, output_dir: str = None):
        """
        Save report to file
        """
        if not output_dir:
            output_dir = f"audit/report_{self.audit_type}generated"
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        filename = f"governance_audit_{self.audit_type}_{self.report_date}.md"
        output_path = Path(output_dir) / filename
        
        report_content = self.generate_report()
        
        with open(output_path, 'w') as f:
            f.write(report_content)
        
        print(f"✅ Report saved to: {output_path}")
        return output_path


# Command-line interface
def main():
    """Main entry point for report generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate governance audit report')
    parser.add_argument('--type', choices=['peer', 'self'], default='peer',
                       help='Audit type (peer review or self-assessment)')
    parser.add_argument('--output', help='Output directory (optional)')
    
    args = parser.parse_args()
    
    print("="*60)
    print(f"📊 Generating {args.type.upper()} Audit Report")
    print("="*60)
    
    generator = AuditReportGenerator(audit_type=args.type)
    output_path = generator.save_report(args.output)
    
    print(f"\n✅ Report generated successfully!")
    print(f"📁 Location: {output_path}")
    
    # Show preview
    print("\n📋 Report Preview (first 500 chars):")
    print("-"*40)
    with open(output_path, 'r') as f:
        print(f.read()[:500] + "...")

if __name__ == "__main__":
    main()