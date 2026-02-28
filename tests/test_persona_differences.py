#!/usr/bin/env python3
"""
Test that judge personas are truly different
"""

from src.nodes.judges import Prosecutor, Defense, TechLead
from langchain_openai import ChatOpenAI

def test_persona_distinctness():
    """Test that each persona gives different responses to same input"""
    
    llm = ChatOpenAI(model="gpt-4", temperature=0.2)
    
    # Create judges
    prosecutor = Prosecutor(llm)
    defense = Defense(llm)
    tech_lead = TechLead(llm)
    
    # Test dimension
    dimension = {
        "name": "code_quality",
        "description": "Overall code quality and maintainability"
    }
    
    # Simple evidence
    evidence = []
    
    # Get prompts
    prompts = {
        "Prosecutor": prosecutor.get_system_prompt(dimension, evidence),
        "Defense": defense.get_system_prompt(dimension, evidence),
        "TechLead": tech_lead.get_system_prompt(dimension, evidence)
    }
    
    # Check distinctness
    print("🔍 Testing Persona Distinctness")
    print("="*60)
    
    for name, prompt in prompts.items():
        print(f"\n{name} prompt sample:")
        print(f"   {prompt[:200]}...")
    
    # Calculate similarity between first two
    from src.nodes.judges import PersonaCollusionDetector
    detector = PersonaCollusionDetector()
    
    sim_pd = detector.calculate_similarity(prompts["Prosecutor"], prompts["Defense"])
    sim_pt = detector.calculate_similarity(prompts["Prosecutor"], prompts["TechLead"])
    sim_dt = detector.calculate_similarity(prompts["Defense"], prompts["TechLead"])
    
    print("\n📊 Similarity Scores:")
    print(f"   Prosecutor vs Defense: {sim_pd:.2%}")
    print(f"   Prosecutor vs TechLead: {sim_pt:.2%}")
    print(f"   Defense vs TechLead: {sim_dt:.2%}")
    
    if max(sim_pd, sim_pt, sim_dt) < 0.7:
        print("\n✅ Personas are sufficiently distinct!")
    else:
        print("\n⚠️  Personas may be too similar - consider adjusting prompts")

if __name__ == "__main__":
    test_persona_distinctness()