# tests/test_rubric.py
import json
from pathlib import Path

def test_step2():
    print("\n🔬 TESTING STEP 2: Rubric JSON")
    print("=" * 50)
    
    rubric_path = Path("rubric/week2_rubric.json")
    
    # Test 1: File exists
    if not rubric_path.exists():
        print(f"❌ Test 2.1: Rubric file not found at {rubric_path}")
        return
    
    print("✅ Test 2.1: Rubric file exists")
    
    # Test 2: Valid JSON
    try:
        with open(rubric_path, 'r') as f:
            rubric = json.load(f)
        print("✅ Test 2.2: Valid JSON format")
    except json.JSONDecodeError as e:
        print(f"❌ Test 2.2: Invalid JSON: {e}")
        return
    
    # Test 3: Required fields
    required_fields = ['version', 'name', 'dimensions']
    missing = [f for f in required_fields if f not in rubric]
    if missing:
        print(f"❌ Test 2.3: Missing fields: {missing}")
    else:
        print("✅ Test 2.3: All required fields present")
    
    # Test 4: Dimension structure
    valid_dimensions = True
    for i, dim in enumerate(rubric['dimensions']):
        dim_required = ['id', 'name', 'target_artifact', 'forensic_instruction', 'judicial_logic']
        dim_missing = [f for f in dim_required if f not in dim]
        if dim_missing:
            print(f"❌ Test 2.4: Dimension {i} missing: {dim_missing}")
            valid_dimensions = False
    
    if valid_dimensions:
        print(f"✅ Test 2.4: All {len(rubric['dimensions'])} dimensions have required fields")
    
    # Test 5: Target artifacts
    artifacts = set(dim['target_artifact'] for dim in rubric['dimensions'])
    print(f"✅ Test 2.5: Target artifacts found: {', '.join(artifacts)}")

if __name__ == "__main__":
    test_step2()