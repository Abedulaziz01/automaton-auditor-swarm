from typing import List, Dict, Any, Optional
from langgraph.types import Command
from datetime import datetime
import json
import numpy as np

from src.state import AgentState, JudicialOpinion, Evidence
from .synthesis_models import FinalVerdict, DimensionScore, RemediationAction
from .security_override import SecurityOverride
from .fact_supremacy import FactSupremacy
from .variance_detector import VarianceDetector

class ChiefJustice:
    """
    Supreme Court - Deterministic synthesis engine
    Applies hardcoded constitutional rules
    """
    
    def __init__(self):
        self.security = SecurityOverride()
        self.fact_supremacy = FactSupremacy()
        self.variance = VarianceDetector(variance_threshold=2.0)
        self.re_evaluation_count = 0
        self.max_re_evaluations = 3
        
    def __call__(self, state: AgentState) -> Command:
        """
        Main entry point for Chief Justice
        Applies all deterministic rules and produces final verdict
        """
        print("\n" + "="*70)
        print("⚖️ SUPREME COURT - CONVENING FINAL JUDGMENT")
        print("="*70)
        
        # Step 1: Extract opinions and evidence
        opinions = state.get("opinions", [])
        evidence = state.get("evidences", [])
        rubric = state.get("rubric", [])
        
        print(f"\n📋 Case Summary:")
        print(f"   Opinions: {len(opinions)}")
        print(f"   Evidence: {len(evidence)}")
        print(f"   Dimensions: {len(rubric)}")
        
        # Step 2: Convert opinions to initial scores
        initial_scores = self._calculate_initial_scores(opinions, rubric)
        
        print("\n📊 Initial Scores:")
        for score in initial_scores:
            print(f"   {score['dimension']}: {score['score']}/5 (conf: {score['confidence']:.2f})")
        
        # Step 3: Apply Security Override
        security_result = self.security.analyze_security(evidence)
        scores_after_security = self.security.apply_override(initial_scores, security_result)
        
        # Step 4: Apply Fact Supremacy
        fact_result = self.fact_supremacy.analyze_factual_basis(opinions, evidence)
        scores_after_facts = self.fact_supremacy.apply_supremacy(
            scores_after_security, 
            fact_result, 
            opinions
        )
        
        # Step 5: Detect Variance
        variance_result = self.variance.analyze_variance(opinions)
        scores_after_variance = self.variance.apply_variance_adjustment(
            scores_after_facts,
            variance_result
        )
        
        # Step 6: Handle Re-evaluation if needed
        if variance_result['trigger_re_evaluation'] and self.re_evaluation_count < self.max_re_evaluations:
            print("\n🔄 TRIGGERING RE-EVALUATION SUB-CHAIN")
            self.re_evaluation_count += 1
            
            # In a real implementation, this would trigger a sub-graph
            # For now, we'll note it in the final verdict
            re_evaluation_note = f"Re-evaluation triggered for: {variance_result['high_variance_dimensions']}"
        else:
            re_evaluation_note = "No re-evaluation needed"
        
        # Step 7: Calculate Overall Score
        overall_score = self._calculate_overall_score(scores_after_variance, rubric)
        
        # Step 8: Generate Dissent Summary
        dissent_summary = self._generate_dissent_summary(opinions, scores_after_variance)
        
        # Step 9: Generate Remediation Plan
        remediation_plan = self._generate_remediation_plan(
            scores_after_variance,
            security_result,
            fact_result,
            evidence
        )
        
        # Step 10: Extract synthesis rules from rubric
        synthesis_rules = self._extract_synthesis_rules(rubric)
        
        # Step 11: Create Dimension Score objects
        dimension_scores = [
            DimensionScore(
                dimension=s['dimension'],
                score=s['score'],
                confidence=s['confidence'],
                security_override_applied=s.get('security_override_applied', False),
                fact_supremacy_applied=s.get('fact_supremacy_applied', False),
                variance_detected=s.get('variance_detected', False),
                reasoning=s.get('reasoning', '')
            )
            for s in scores_after_variance
        ]
        
        # Step 12: Create Final Verdict
        verdict = FinalVerdict(
            case_id=f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            security_findings=security_result.get('findings', []),
            security_override_triggered=security_result.get('apply_cap', False),
            security_cap_applied=security_result.get('cap_score'),
            factual_discrepancies=fact_result.get('discrepancies', []),
            fact_supremacy_applied=fact_result.get('dimensions_affected', []),
            high_variance_dimensions=variance_result.get('high_variance_dimensions', []),
            re_evaluations_triggered=self.re_evaluation_count,
            dissent_summary=dissent_summary,
            remediation_plan=remediation_plan,
            synthesis_rules_applied=synthesis_rules
        )
        
        # Print Final Summary
        self._print_final_verdict(verdict)
        
        # Update state and move to next node
        return Command(
            update={
                "final_report": verdict.dict(),
                "dissenting_opinions": state.get("dissenting_opinions", []),
                "errors": []
            },
            goto="__end__"  # Or next node in your graph
        )
    
    def _calculate_initial_scores(self, opinions: List[JudicialOpinion], rubric: List[Dict]) -> List[Dict]:
        """Convert opinions to numeric scores (1-5 scale)"""
        scores_by_dim = {}
        
        for opinion in opinions:
            dim = opinion.dimension
            
            if dim not in scores_by_dim:
                scores_by_dim[dim] = []
            
            # Convert verdict to score
            if opinion.verdict == "pass":
                score = 5.0 * opinion.confidence
            elif opinion.verdict == "warn":
                score = 3.0 * opinion.confidence
            else:  # fail
                score = 1.0 * opinion.confidence
            
            scores_by_dim[dim].append({
                "score": score,
                "confidence": opinion.confidence,
                "reasoning": opinion.reasoning
            })
        
        # Average scores per dimension
        initial_scores = []
        for dim, dim_scores in scores_by_dim.items():
            avg_score = np.mean([s["score"] for s in dim_scores])
            avg_confidence = np.mean([s["confidence"] for s in dim_scores])
            
            # Round to nearest 0.5 for 1-5 scale
            rounded_score = round(avg_score * 2) / 2
            rounded_score = max(1, min(5, rounded_score))
            
            initial_scores.append({
                "dimension": dim,
                "score": rounded_score,
                "confidence": avg_confidence,
                "reasoning": f"Average of {len(dim_scores)} opinions"
            })
        
        return initial_scores
    
    def _calculate_overall_score(self, scores: List[Dict], rubric: List[Dict]) -> float:
        """Calculate weighted overall score"""
        total_weight = 0
        weighted_sum = 0
        
        # Create weight map from rubric
        weight_map = {d['name']: d.get('weight', 1.0) for d in rubric}
        
        for score in scores:
            dim = score['dimension']
            weight = weight_map.get(dim, 1.0)
            weighted_sum += score['score'] * weight
            total_weight += weight
        
        overall = weighted_sum / total_weight if total_weight > 0 else 0
        return round(overall, 2)
    
    def _generate_dissent_summary(self, opinions: List[JudicialOpinion], final_scores: List[Dict]) -> str:
        """Generate summary of dissenting opinions"""
        dissents = []
        
        # Find opinions that differ significantly from final scores
        score_map = {s['dimension']: s['score'] for s in final_scores}
        
        for opinion in opinions:
            final_score = score_map.get(opinion.dimension, 3)
            
            # Convert opinion to numeric for comparison
            if opinion.verdict == "pass":
                opinion_score = 5
            elif opinion.verdict == "warn":
                opinion_score = 3
            else:
                opinion_score = 1
            
            # If difference > 2, it's a significant dissent
            if abs(opinion_score - final_score) > 2:
                dissents.append(f"{opinion.dimension}: {opinion.reasoning[:100]}...")
        
        if dissents:
            summary = "Significant dissenting opinions:\n" + "\n".join(dissents[:3])
        else:
            summary = "No significant dissenting opinions"
        
        return summary
    
    def _generate_remediation_plan(
        self,
        scores: List[Dict],
        security_result: Dict,
        fact_result: Dict,
        evidence: List[Evidence]
    ) -> List[RemediationAction]:
        """Generate concrete remediation actions"""
        remediations = []
        
        # Add security remediations
        remediations.extend(security_result.get('remediations', []))
        
        # Add fact-based remediations
        for discrepancy in fact_result.get('discrepancies', [])[:3]:
            remediations.append(RemediationAction(
                priority="MEDIUM",
                action=f"Address factual discrepancy in {discrepancy.dimension}",
                reasoning=discrepancy.resolution
            ))
        
        # Add low score remediations
        for score in scores:
            if score['score'] <= 2:
                remediations.append(RemediationAction(
                    priority="HIGH",
                    action=f"Improve {score['dimension']} - current score {score['score']}/5",
                    reasoning=score.get('reasoning', 'Low score requires attention')
                ))
        
        return remediations
    
    def _extract_synthesis_rules(self, rubric: List[Dict]) -> List[str]:
        """Extract synthesis rules from rubric"""
        rules = []
        for dim in rubric:
            if 'synthesis_rules' in dim:
                rules.append(f"{dim['name']}: {dim['synthesis_rules']}")
        return rules
    
    def _print_final_verdict(self, verdict: FinalVerdict):
        """Print beautiful final verdict"""
        print("\n" + "="*70)
        print("🏛️  FINAL VERDICT - SUPREME COURT RULING")
        print("="*70)
        
        # Overall score with visual indicator
        print(f"\n📊 OVERALL SCORE: {verdict.overall_score}/5.0")
        
        # Score bar
        bar_length = 50
        filled = int((verdict.overall_score / 5.0) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"   [{bar}]")
        
        # Grade
        if verdict.overall_score >= 4.5:
            grade = "A - EXCELLENT"
        elif verdict.overall_score >= 3.5:
            grade = "B - GOOD"
        elif verdict.overall_score >= 2.5:
            grade = "C - SATISFACTORY"
        elif verdict.overall_score >= 1.5:
            grade = "D - NEEDS IMPROVEMENT"
        else:
            grade = "F - FAILING"
        
        print(f"   GRADE: {grade}")
        
        # Dimension scores
        print("\n📋 DIMENSION SCORES:")
        for ds in verdict.dimension_scores:
            flags = []
            if ds.security_override_applied:
                flags.append("🔒")
            if ds.fact_supremacy_applied:
                flags.append("⚖️")
            if ds.variance_detected:
                flags.append("📊")
            
            flag_str = " ".join(flags)
            print(f"   {ds.dimension:20} {ds.score}/5.0 {flag_str}")
        
        # Security findings
        if verdict.security_findings:
            print("\n🔒 SECURITY FINDINGS:")
            for f in verdict.security_findings[:3]:
                print(f"   ⚠️  {f.finding} ({f.risk_level})")
        
        # High variance dimensions
        if verdict.high_variance_dimensions:
            print("\n📊 HIGH VARIANCE DIMENSIONS:")
            for dim in verdict.high_variance_dimensions:
                print(f"   ⚠️  {dim} - needs re-evaluation")
        
        # Dissent summary
        print("\n🗣️  DISSENT SUMMARY:")
        print(f"   {verdict.dissent_summary[:200]}...")
        
        # Remediation plan
        if verdict.remediation_plan:
            print("\n🔧 REMEDIATION PLAN:")
            for i, action in enumerate(verdict.remediation_plan[:3], 1):
                print(f"   {i}. [{action.priority}] {action.action}")
        
        print("\n" + "="*70)
        print("✅ SUPREME COURT ADJOURNED")
        print("="*70)


# Node function for LangGraph
def chief_justice_node(state: AgentState) -> Command:
    """LangGraph node for Chief Justice"""
    chief = ChiefJustice()
    return chief(state)