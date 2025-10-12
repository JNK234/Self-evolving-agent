# ABOUTME: End-to-end integration test for ATC pipeline with real Weave data
# ABOUTME: Validates trace fetching, pattern recognition, and tool ideation flow

import os
import weave
from dotenv import load_dotenv
from sea.atc_orchestrator import ATCOrchestrator

load_dotenv()


def main():
    """Test complete ATC pipeline with real Weave traces."""
    print("="*60)
    print("ATC Weave Integration Test")
    print("="*60)

    # Get Weave project from environment
    project_name = os.getenv("WEAVE_PROJECT_NAME")
    if not project_name:
        print("\n❌ WEAVE_PROJECT_NAME not set in environment")
        print("Please set: export WEAVE_PROJECT_NAME='entity/project'")
        return 1

    print(f"\nProject: {project_name}")

    # Initialize Weave
    try:
        weave.init(project_name)
        print("✓ Weave initialized")
    except Exception as e:
        print(f"❌ Weave initialization failed: {e}")
        return 1

    # Initialize ATC orchestrator
    try:
        orchestrator = ATCOrchestrator(
            project_name=project_name,
            pattern_model="gemini-2.0-flash",
            ideator_model="gemini-2.0-flash"
        )
        print("✓ ATCOrchestrator initialized")
    except Exception as e:
        print(f"❌ Orchestrator initialization failed: {e}")
        return 1

    # Run ATC cycle
    print(f"\n{'='*60}")
    print("Running ATC Cycle")
    print(f"{'='*60}\n")

    try:
        results = orchestrator.run_atc_cycle(
            num_traces=10,
            agent_domain="math",
            min_frequency=2,
            generate_specifications=True,
            op_name_filter="run_react_agent"
        )

        # Print summary
        orchestrator.print_cycle_summary(results)

        # Check for errors
        if results.get("errors"):
            print("\n⚠️  Cycle completed with errors")
            return 1

        # Validate results
        traces_fetched = results["cycle_metadata"].get("traces_fetched", 0)
        patterns_found = len(results.get("patterns_identified", []))

        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        print(f"✓ Traces fetched: {traces_fetched}")
        print(f"✓ Patterns identified: {patterns_found}")
        print(f"✓ Tool proposals: {len(results.get('tool_proposals', []))}")
        print(f"✓ Specifications: {len(results.get('tool_specifications', []))}")

        if traces_fetched == 0:
            print("\n⚠️  No traces found - run gsm8k_eval_with_calculator.py first")
            return 1

        print("\n✅ Integration test PASSED")
        return 0

    except Exception as e:
        print(f"\n❌ ATC cycle failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
