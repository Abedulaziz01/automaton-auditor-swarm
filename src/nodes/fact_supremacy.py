from typing import List, Dict, Any, Optional
from .synthesis_models import FactualDiscrepancy

class FactSupremacy:
    """
    Applies fact supremacy rules:
    - Forensic evidence overrules opinions
    - Detects when judges ignore evidence
    """
    
    def __init__(self):
        self.fact_keywords = [
            "found", "detected", "observed", "measured",
            "line", "file", "commit", "hash", "timestamp",
            "ast", "parser", "graph", "edge", "node"
        ]
        
        self.opinion_keywords = [
            "think", "believe", "feel", "seems", "appears",
            "probably", "maybe", "perhaps", "might", "could"
        ]
    
    def analyze_factual_basis(self, opinions: List[Any], evidence: List[Any]) -> Dict[str, Any]:
        """
        Analyze if opinions are supported by facts
        """
        print("\n📊 FACT SUPREMACY ANALYSIS")
        print("="*60)
        
        discrepancies = []
        dimensions_affected = set()
        
        # Group evidence by dimension
        evidence_by_dim = {}
        for ev in evidence:
            # Extract dimension from evidence notes
            dim = self._extract_dimension(ev.forensic_notes)
            if dim:
                if dim not in evidence_by_dim:
                    evidence_by_dim[dim] = []
                evidence_by_dim[dim].append(ev)
        
        # Check each opinion against evidence
        for opinion in opinions:
            dim = opinion.dimension
            ev_list = evidence_by_dim.get(dim, [])
            
            # Skip if no evidence for this dimension
            if not ev_list:
                continue
            
            # Check if opinion references actual evidence
            evidence_refs = opinion.evidence_ids if hasattr(opinion, 'evidence_ids') else []
            
            if not evidence_refs:
                # Opinion doesn't reference any evidence
                discrepancy = FactualDiscrepancy(
                    dimension=dim,
                    evidence_fact=f"Evidence exists but not referenced: {[e.id for e in ev_list[:3]]}",
                    opinion_claim=opinion.reasoning[:100],
                    opinion_source=opinion.reasoning.split(']')[0].replace('[', '') if ']' in opinion.reasoning else 'Unknown',
                    resolution="Opinion lacks factual basis"
                )
                discrepancies.append(discrepancy)
                dimensions_affected.add(dim)
                continue
            
            # Check if referenced evidence actually exists
            valid_refs = []
            invalid_refs = []
            
            for ref in evidence_refs:
                if any(ref == e.id for e in ev_list):
                    valid_refs.append(ref)
                else:
                    invalid_refs.append(ref)
            
            if invalid_refs:
                discrepancy = FactualDiscrepancy(
                    dimension=dim,
                    evidence_fact=f"Evidence IDs exist: {[e.id for e in ev_list[:3]]}",
                    opinion_claim=f"References invalid IDs: {invalid_refs}",
                    opinion_source=opinion.reasoning.split(']')[0].replace('[', '') if ']' in opinion.reasoning else 'Unknown',
                    resolution="Opinion references non-existent evidence"
                )
                discrepancies.append(discrepancy)
                dimensions_affected.add(dim)
        
        # Count factual vs opinion-based statements
        factual_count = 0
        opinion_count = 0
        
        for opinion in opinions:
            reasoning = opinion.reasoning.lower()
            
            # Count fact keywords
            for kw in self.fact_keywords:
                if kw in reasoning:
                    factual_count += 1
                    break
            
            # Count opinion keywords
            for kw in self.opinion_keywords:
                if kw in reasoning:
                    opinion_count += 1
                    break
        
        result = {
            "discrepancies": discrepancies,
            "dimensions_affected": list(dimensions_affected),
            "total_discrepancies": len(discrepancies),
            "factual_statements": factual_count,
            "opinion_statements": opinion_count,
            "fact_to_opinion_ratio": factual_count / max(opinion_count, 1),
            "apply_fact_supremacy": len(discrepancies) > 0
        }
        
        # Print summary
        print(f"\nFactual Statements: {factual_count}")
        print(f"Opinion Statements: {opinion_count}")
        print(f"Fact/Opinion Ratio: {result['fact_to_opinion_ratio']:.2f}")
        print(f"Discrepancies Found: {len(discrepancies)}")
        print(f"Dimensions Affected: {result['dimensions_affected']}")
        
        if discrepancies:
            print("\n⚠️ Factual Discrepancies:")
            for d in discrepancies[:3]:
                print(f"  - {d.dimension}: {d.resolution}")
        
        return result
    
    def _extract_dimension(self, forensic_notes: str) -> Optional[str]:
        """Extract dimension name from forensic notes"""
        if not forensic_notes:
            return None
        
        # Simple extraction - look for common patterns
        notes_lower = forensic_notes.lower()
        
        dimension_keywords = [
            "orchestration", "state", "documentation", "security",
            "parallel", "graph", "model", "tool", "test"
        ]
        
        for kw in dimension_keywords:
            if kw in notes_lower:
                return kw
        
        return None
    
    def apply_supremacy(self, scores: List[Dict], fact_result: Dict, opinions: List[Any]) -> List[Dict]:
        """
        Apply fact supremacy to scores
        Opinions without factual basis are downgraded
        """
        if not fact_result['apply_fact_supremacy']:
            return scores
        
        print("\n⚖️ APPLYING FACT SUPREMACY - Opinions overruled by facts")
        
        adjusted_scores = []
        affected_dims = fact_result['dimensions_affected']
        
        for score_dict in scores:
            if score_dict['dimension'] in affected_dims:
                original = score_dict['score']
                # Reduce score by 1 if based on unsupported opinions
                score_dict['score'] = max(1, original - 1)
                score_dict['fact_supremacy_applied'] = True
                score_dict['reasoning'] += f" [FACT SUPREMACY: Score reduced from {original} to {score_dict['score']} due to unsupported opinions]"
                print(f"   {score_dict['dimension']}: {original} → {score_dict['score']} (fact overruled)")
            
            adjusted_scores.append(score_dict)
        
        return adjusted_scores