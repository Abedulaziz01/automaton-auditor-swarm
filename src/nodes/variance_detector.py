from typing import List, Dict, Any, Optional
import numpy as np

class VarianceDetector:
    """
    Detects high variance in judge opinions
    Triggers re-evaluation if variance > 2.0
    """
    
    def __init__(self, variance_threshold: float = 2.0):
        self.threshold = variance_threshold
        
    def analyze_variance(self, opinions: List[Any]) -> Dict[str, Any]:
        """
        Analyze variance in opinions for each dimension
        """
        print("\n📊 VARIANCE DETECTION ANALYSIS")
        print("="*60)
        
        # Group opinions by dimension
        opinions_by_dim = {}
        for opinion in opinions:
            dim = opinion.dimension
            if dim not in opinions_by_dim:
                opinions_by_dim[dim] = []
            opinions_by_dim[dim].append(opinion)
        
        variance_results = []
        high_variance_dims = []
        
        for dim, dim_opinions in opinions_by_dim.items():
            if len(dim_opinions) < 2:
                continue
            
            # Convert verdicts to numeric scores
            verdict_scores = []
            for op in dim_opinions:
                if op.verdict == "pass":
                    verdict_scores.append(5.0 * op.confidence)
                elif op.verdict == "warn":
                    verdict_scores.append(3.0 * op.confidence)
                else:  # fail
                    verdict_scores.append(1.0 * op.confidence)
            
            # Calculate variance
            if len(verdict_scores) > 1:
                variance = float(np.var(verdict_scores))
                std_dev = float(np.std(verdict_scores))
                
                result = {
                    "dimension": dim,
                    "variance": variance,
                    "std_dev": std_dev,
                    "scores": verdict_scores,
                    "verdicts": [op.verdict for op in dim_opinions],
                    "high_variance": variance > self.threshold
                }
                
                variance_results.append(result)
                
                if variance > self.threshold:
                    high_variance_dims.append(dim)
                    
                # Print summary
                verdict_str = '/'.join([v.verdict for v in dim_opinions])
                status = "⚠️ HIGH VARIANCE" if variance > self.threshold else "✅ OK"
                print(f"\n{dim}:")
                print(f"   Verdicts: {verdict_str}")
                print(f"   Scores: {[round(s, 1) for s in verdict_scores]}")
                print(f"   Variance: {variance:.2f} ({status})")
        
        result = {
            "dimensions_analyzed": len(variance_results),
            "high_variance_dimensions": high_variance_dims,
            "variance_details": variance_results,
            "trigger_re_evaluation": len(high_variance_dims) > 0,
            "re_evaluation_count": len(high_variance_dims)
        }
        
        print(f"\n📊 Summary:")
        print(f"   High Variance Dimensions: {len(high_variance_dims)}")
        print(f"   Trigger Re-evaluation: {'⚠️ YES' if result['trigger_re_evaluation'] else '✅ NO'}")
        
        return result
    
    def apply_variance_adjustment(self, scores: List[Dict], variance_result: Dict) -> List[Dict]:
        """
        Apply variance detection to scores
        Marks dimensions that need re-evaluation
        """
        if not variance_result['trigger_re_evaluation']:
            return scores
        
        print("\n🔄 MARKING HIGH VARIANCE DIMENSIONS FOR RE-EVALUATION")
        
        adjusted_scores = []
        high_variance_dims = variance_result['high_variance_dimensions']
        
        for score_dict in scores:
            if score_dict['dimension'] in high_variance_dims:
                score_dict['variance_detected'] = True
                score_dict['reasoning'] += f" [HIGH VARIANCE: Needs re-evaluation]"
                print(f"   {score_dict['dimension']}: marked for re-evaluation")
            
            adjusted_scores.append(score_dict)
        
        return adjusted_scores