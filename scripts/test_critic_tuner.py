# ABOUTME: Quick test script to verify Critic-Tuner components work
# ABOUTME: Tests rubric loading, critic evaluation, and updater functionality

import json
from sea.critic import Critic
from sea.updater import Updater

# Test sample
test_problem = "Janet has 16 eggs. She uses 3 for breakfast and 4 for muffins. How many eggs does she have left?"
test_solution = """Let me solve this step by step.

Step 1: Calculate total eggs used
I'll use the calculator: 3 + 4 = 7

Step 2: Calculate remaining eggs
16 - 7 = 9

#### 9"""


def test_rubric_loading():
    """Test that rubric loads correctly."""
    print("Testing rubric loading...")
    with open("src/agents/math_solver/rubric.json", 'r') as f:
        rubric = json.load(f)
    print(f"✓ Rubric loaded with {len(rubric['criteria'])} criteria")
    for criterion in rubric['criteria']:
        print(f"  - {criterion['id']}: weight={criterion['weight']}")
    return rubric


def test_critic():
    """Test critic evaluation."""
    print("\nTesting Critic...")
    critic = Critic()

    evaluation = critic.evaluate_solution(
        problem=test_problem,
        solution=test_solution
    )

    print(f"✓ Critic evaluation complete")
    print(f"  Overall Score: {evaluation.get('overall_score', 'N/A')}")
    print(f"  Suggestions: {len(evaluation.get('suggestions', []))}")

    return evaluation


def test_updater():
    """Test updater with sample suggestions."""
    print("\nTesting Updater...")

    sample_suggestions = [
        {
            "suggestion_type": "ADD_CONSTRAINT",
            "details": "Always show calculator tool usage explicitly",
            "reasoning": "Makes tool usage more visible"
        }
    ]

    sample_prompt = "You are a math solver. Use tools to solve problems."

    updater = Updater(max_suggestions=2)
    result = updater.apply_suggestions(
        current_prompt=sample_prompt,
        suggestions=sample_suggestions
    )

    print(f"✓ Updater complete")
    print(f"  Changes: {result['changes_summary']}")
    print(f"  New prompt length: {len(result['new_prompt'])} chars")

    return result


def main():
    """Run all tests."""
    print("="*60)
    print("Testing Critic-Tuner Components")
    print("="*60)

    try:
        rubric = test_rubric_loading()
        evaluation = test_critic()
        update_result = test_updater()

        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60)
        print("\nYou can now run the full evolution:")
        print("  python scripts/run_sea_evolution.py --problems 5 --cycles 2")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
