from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Command
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
import json
import hashlib
from datetime import datetime

# Import our state models
from src.state import JudicialOpinion, Evidence, AgentState

class JudgePersona:
    """Base class for judge personas"""
    
    def __init__(self, llm):
        self.llm = llm
        
    def get_system_prompt(self, dimension: Dict, evidence: List[Evidence]) -> str:
        """To be implemented by each persona"""
        raise NotImplementedError
        
    def get_verdict_prompt(self, dimension: Dict, evidence: List[Evidence]) -> str:
        """Base prompt structure for verdict"""
        evidence_summary = "\n".join([
            f"- {e.source}: {e.content[:200]}..." 
            for e in evidence[:5]  # Limit to avoid token overflow
        ])
        
        return f"""
        Based on the evidence provided, render a judicial opinion for dimension:
        {dimension['name']}: {dimension['description']}
        
        Evidence available:
        {evidence_summary}
        
        Return a JSON object with:
        {{
            "dimension": "{dimension['name']}",
            "verdict": "pass|warn|fail",
            "confidence": 0.0-1.0,
            "reasoning": "detailed explanation",
            "evidence_ids": ["list", "of", "evidence", "ids"],
            "minority_opinion": "optional dissenting view"
        }}
        """


class Prosecutor(JudgePersona):
    """
    Strict judge who assumes bad practices
    Enforces Statute of Orchestration and Hallucination Liability
    """
    
    def get_system_prompt(self, dimension: Dict, evidence: List[Evidence]) -> str:
        base_prompt = self.get_verdict_prompt(dimension, evidence)
        
        prosecutor_prompt = f"""
        You are a PROSECUTOR in a technical court. Your role is to assume the worst - that the code was written by someone who doesn't understand the concepts ("vibe coding").
        
        STRICT ENFORCEMENT:
        1. Statute of Orchestration - The graph must show PROPER orchestration:
           - Parallel detectives MUST have fan-out
           - MUST have evidence aggregation fan-in
           - Judges MUST run in parallel with structured output
           - If ANY of these are missing, it's a FAIL
        
        2. Hallucination Liability - Evidence MUST be verifiable:
           - Code evidence MUST be from actual AST analysis, not assumptions
           - Documentation MUST cross-reference with actual code
           - If evidence claims something not in the code, it's a FAIL
        
        Be HARSH. If it's not perfect, it's a fail or at best a warn.
        Look for reasons to fail, not reasons to pass.
        
        {base_prompt}
        
        Remember: You are the PROSECUTOR. Your default stance is GUILTY (fail) until proven innocent.
        """
        
        return prosecutor_prompt


class Defense(JudgePersona):
    """
    Lenient judge who rewards effort
    Reads Git narrative and detects sophistication
    """
    
    def get_system_prompt(self, dimension: Dict, evidence: List[Evidence]) -> str:
        base_prompt = self.get_verdict_prompt(dimension, evidence)
        
        defense_prompt = f"""
        You are the DEFENSE attorney in a technical court. Your role is to find redeeming qualities and reward genuine effort.
        
        REWARD EFFORT & ITERATION:
        1. Git Narrative Analysis:
           - Look at commit history - do you see progressive improvement?
           - Are there multiple commits showing iteration?
           - Did they fix issues over time? This shows learning
        
        2. Deep AST Sophistication:
           - Are they using proper AST parsing, not just regex?
           - Do they have proper error handling?
           - Is the code maintainable and well-structured?
        
        Be LENIENT but not blind. If you see genuine effort and understanding, PASS or at least WARN.
        Default to giving them the benefit of the doubt.
        
        {base_prompt}
        
        Remember: You are the DEFENSE. Your default stance is INNOCENT (pass) until proven guilty beyond reasonable doubt.
        """
        
        return defense_prompt


class TechLead(JudgePersona):
    """
    Balanced judge focused on engineering excellence
    Enforces Pydantic rigor and reducer patterns
    """
    
    def get_system_prompt(self, dimension: Dict, evidence: List[Evidence]) -> str:
        base_prompt = self.get_verdict_prompt(dimension, evidence)
        
        tech_lead_prompt = f"""
        You are a TECH LEAD reviewing a pull request. Your role is balanced - you want good code to ship, but it must meet engineering standards.
        
        ENGINEERING EXCELLENCE:
        1. Pydantic Rigor:
           - Are models properly typed with validators?
           - Do they use Field with constraints?
           - Is there proper data validation?
        
        2. Reducer Patterns:
           - Do reducers prevent data loss? (operator.add, operator.iadd)
           - Is state management thread-safe?
           - Can the system recover from failures?
        
        3. Maintainability:
           - Is the code readable?
           - Are there comments where needed?
           - Would another engineer understand this in 6 months?
        
        Be BALANCED. Pass if it's good, warn if it needs work, fail if it's broken.
        Default to WARN - give them feedback to improve.
        
        {base_prompt}
        
        Remember: You are the TECH LEAD. Your default stance is "NEEDS IMPROVEMENT" (warn) with specific feedback.
        """
        
        return tech_lead_prompt


class PersonaCollusionDetector:
    """
    Detects if judges are colluding (too similar in their reasoning)
    """
    
    def __init__(self, similarity_threshold: float = 0.9):
        self.threshold = similarity_threshold
        
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts"""
        # Simple hash-based similarity for demo
        # In production, use embeddings or more sophisticated NLP
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
            
        return len(intersection) / len(union)
    
    def check_collusion(self, opinions: List[JudicialOpinion]) -> Dict[str, Any]:
        """
        Check if any two opinions are too similar
        Returns collusion report
        """
        if len(opinions) < 2:
            return {"collusion_detected": False, "pairs": []}
        
        collusion_pairs = []
        
        for i in range(len(opinions)):
            for j in range(i+1, len(opinions)):
                similarity = self.calculate_similarity(
                    opinions[i].reasoning,
                    opinions[j].reasoning
                )
                
                if similarity > self.threshold:
                    collusion_pairs.append({
                        "judge1": f"Judge_{i}",
                        "judge2": f"Judge_{j}",
                        "similarity": similarity,
                        "verdicts": [opinions[i].verdict, opinions[j].verdict]
                    })
        
        return {
            "collusion_detected": len(collusion_pairs) > 0,
            "pairs": collusion_pairs,
            "threshold": self.threshold
        }


class StructuredOutputValidator:
    """
    Validates that judge output matches expected schema
    """
    
    @staticmethod
    def validate(opinion_dict: dict) -> tuple[bool, Optional[str]]:
        """Validate opinion structure"""
        try:
            # Check required fields
            required_fields = ["dimension", "verdict", "confidence", "reasoning"]
            for field in required_fields:
                if field not in opinion_dict:
                    return False, f"Missing required field: {field}"
            
            # Validate verdict
            if opinion_dict["verdict"] not in ["pass", "warn", "fail"]:
                return False, f"Invalid verdict: {opinion_dict['verdict']}"
            
            # Validate confidence
            confidence = opinion_dict["confidence"]
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                return False, f"Invalid confidence: {confidence}"
            
            # Validate evidence_ids (optional)
            if "evidence_ids" in opinion_dict and not isinstance(opinion_dict["evidence_ids"], list):
                return False, "evidence_ids must be a list"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def to_judicial_opinion(opinion_dict: dict, persona: str) -> JudicialOpinion:
        """Convert validated dict to JudicialOpinion object"""
        return JudicialOpinion(
            dimension=opinion_dict["dimension"],
            verdict=opinion_dict["verdict"],
            confidence=opinion_dict["confidence"],
            reasoning=f"[{persona}] {opinion_dict['reasoning']}",
            evidence_ids=opinion_dict.get("evidence_ids", []),
            minority_opinion=opinion_dict.get("minority_opinion")
        )


class JudicialPanel:
    """
    Manages multiple judges for a dimension
    Runs them in parallel with retry logic
    """
    
    def __init__(self, llm, max_retries: int = 2):
        self.llm = llm
        self.max_retries = max_retries
        
        # Initialize judges with different personas
        self.judges = [
            ("Prosecutor", Prosecutor(llm)),
            ("Defense", Defense(llm)),
            ("TechLead", TechLead(llm))
        ]
        
        self.collusion_detector = PersonaCollusionDetector()
        self.validator = StructuredOutputValidator()
    
    def judge_dimension(
        self, 
        dimension: Dict, 
        evidence: List[Evidence]
    ) -> Dict[str, Any]:
        """
        Run all judges on a single dimension
        Returns opinions and collusion report
        """
        print(f"\n⚖️ JUDGING DIMENSION: {dimension['name']}")
        print("="*60)
        
        opinions = []
        errors = []
        
        # Run each judge
        for persona_name, judge in self.judges:
            print(f"\n👨‍⚖️ {persona_name} is deliberating...")
            
            opinion = self._run_judge_with_retry(
                persona_name, 
                judge, 
                dimension, 
                evidence
            )
            
            if opinion:
                opinions.append(opinion)
                print(f"   ✓ {persona_name} rendered: {opinion.verdict.upper()} (conf: {opinion.confidence:.2f})")
            else:
                errors.append(f"{persona_name} failed to render opinion")
                print(f"   ❌ {persona_name} failed")
        
        # Check for collusion
        collusion_report = self.collusion_detector.check_collusion(opinions)
        
        if collusion_report["collusion_detected"]:
            print("\n⚠️  COLLUSION DETECTED:")
            for pair in collusion_report["pairs"]:
                print(f"   {pair['judge1']} and {pair['judge2']} are {pair['similarity']:.1%} similar")
        
        return {
            "dimension": dimension["name"],
            "opinions": opinions,
            "collusion": collusion_report,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
    
    def _run_judge_with_retry(
        self,
        persona_name: str,
        judge: JudgePersona,
        dimension: Dict,
        evidence: List[Evidence]
    ) -> Optional[JudicialOpinion]:
        """Run a judge with retry logic"""
        
        for attempt in range(self.max_retries + 1):
            try:
                # Get the system prompt for this judge
                system_prompt = judge.get_system_prompt(dimension, evidence)
                
                # Invoke the LLM
                response = self.llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content="Render your judicial opinion now.")
                ])
                
                # Parse response
                try:
                    opinion_dict = json.loads(response.content)
                except:
                    # Try to extract JSON from text
                    import re
                    json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                    if json_match:
                        opinion_dict = json.loads(json_match.group())
                    else:
                        raise ValueError("No JSON found in response")
                
                # Validate structure
                is_valid, error = self.validator.validate(opinion_dict)
                
                if not is_valid:
                    print(f"   Attempt {attempt + 1}: Invalid output - {error}")
                    if attempt < self.max_retries:
                        continue
                    return None
                
                # Convert to JudicialOpinion
                return self.validator.to_judicial_opinion(opinion_dict, persona_name)
                
            except Exception as e:
                print(f"   Attempt {attempt + 1}: Error - {str(e)}")
                if attempt < self.max_retries:
                    continue
                return None
        
        return None


class SynthesisEngine:
    """
    Synthesizes multiple judicial opinions into final judgment
    Handles dissenting opinions and majority rules
    """
    
    def synthesize(self, panel_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize opinions from all dimensions
        """
        print("\n🔄 SYNTHESIZING FINAL JUDGMENT")
        print("="*60)
        
        all_opinions = []
        dissenting = []
        
        for result in panel_results:
            dimension = result["dimension"]
            opinions = result["opinions"]
            
            if not opinions:
                print(f"⚠️  No opinions for {dimension}")
                continue
            
            # Add all opinions
            all_opinions.extend(opinions)
            
            # Find majority verdict
            verdicts = {}
            for opinion in opinions:
                verdicts[opinion.verdict] = verdicts.get(opinion.verdict, 0) + 1
            
            majority_verdict = max(verdicts.items(), key=lambda x: x[1])
            
            # Find dissenting opinions
            for opinion in opinions:
                if opinion.verdict != majority_verdict[0]:
                    dissenting.append({
                        "dimension": dimension,
                        "opinion": opinion
                    })
        
        # Calculate overall score
        verdict_counts = {"pass": 0, "warn": 0, "fail": 0}
        weighted_score = 0
        total_weight = 0
        
        for opinion in all_opinions:
            verdict_counts[opinion.verdict] += 1
            # Weight by confidence
            if opinion.verdict == "pass":
                weighted_score += 1.0 * opinion.confidence
            elif opinion.verdict == "warn":
                weighted_score += 0.5 * opinion.confidence
            # fail adds 0
            total_weight += opinion.confidence
        
        final_score = (weighted_score / total_weight) * 100 if total_weight > 0 else 0
        
        synthesis = {
            "total_opinions": len(all_opinions),
            "verdict_distribution": verdict_counts,
            "final_score": final_score,
            "grade": self._get_grade(final_score),
            "dissenting_opinions": dissenting,
            "all_opinions": all_opinions
        }
        
        # Display results
        print(f"\n📊 SYNTHESIS RESULTS:")
        print(f"   Total Opinions: {synthesis['total_opinions']}")
        print(f"   Pass: {verdict_counts['pass']} | Warn: {verdict_counts['warn']} | Fail: {verdict_counts['fail']}")
        print(f"   Final Score: {final_score:.1f}% - {synthesis['grade']}")
        
        if dissenting:
            print(f"\n⚠️  Dissenting Opinions: {len(dissenting)}")
            for d in dissenting[:3]:  # Show first 3
                print(f"   - {d['dimension']}: {d['opinion'].reasoning[:100]}...")
        
        return synthesis
    
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A - Excellent"
        elif score >= 80:
            return "B - Good"
        elif score >= 70:
            return "C - Satisfactory"
        elif score >= 60:
            return "D - Needs Improvement"
        else:
            return "F - Failing"


# Main judge node for LangGraph
def judicial_bench_node(state: AgentState) -> Command[Literal["synthesize"]]:
    """
    Main node that runs all judges on all dimensions
    This will be integrated into the graph
    """
    print("\n" + "="*60)
    print("⚖️ CONVENING THE JUDICIAL BENCH")
    print("="*60)
    
    # Initialize judicial panel
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4", temperature=0.2)
    panel = JudicialPanel(llm)
    synthesis_engine = SynthesisEngine()
    
    # Group evidence by dimension
    # In real implementation, you'd have logic to map evidence to dimensions
    
    # Process each dimension in the rubric
    panel_results = []
    for dimension in state["rubric"]:
        # Filter evidence relevant to this dimension
        # This is simplified - you'd need more sophisticated matching
        relevant_evidence = [
            e for e in state["evidences"]
            if dimension["name"].lower() in e.forensic_notes.lower()
            or any(dim_id in e.id for dim_id in dimension.get("evidence_patterns", []))
        ]
        
        if not relevant_evidence:
            print(f"⚠️ No evidence for dimension {dimension['name']}")
            # Create empty evidence list - judges will handle
            relevant_evidence = []
        
        # Judge this dimension
        result = panel.judge_dimension(dimension, relevant_evidence)
        panel_results.append(result)
        
        # Add opinions to state
        for opinion in result["opinions"]:
            state["opinions"].append(opinion)
    
    # Synthesize final results
    synthesis = synthesis_engine.synthesize(panel_results)
    
    # Update state
    return Command(
        update={
            "opinions": state["opinions"],  # Already added above
            "final_report": synthesis,
            "dissenting_opinions": synthesis["dissenting_opinions"],
            "errors": []  # Clear errors
        },
        goto="synthesize"  # Or whatever your next node is
    )