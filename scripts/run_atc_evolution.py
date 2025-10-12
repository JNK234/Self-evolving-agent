# ABOUTME: Standalone script for Automatic Tool Creation pattern recognition testing
# ABOUTME: Analyzes solver traces and generates tool proposals independently of main SEA loop

import os
import json
import weave
import argparse
from datetime import datetime
from dotenv import load_dotenv
from sea.atc_orchestrator import ATCOrchestrator
from sea.weave_trace_fetcher import WeaveTraceFetcher

load_dotenv()


def fetch_traces_from_weave(project_name: str, num_traces: int = 20, op_name_filter: str = "run_react_agent") -> list:
    """
    Fetch recent traces from Weave project.

    Args:
        project_name: Weave project name
        num_traces: Number of recent traces to fetch
        op_name_filter: Filter for operation names

    Returns:
        List of trace dictionaries

    Raises:
        ValueError: If project_name is not configured
        Exception: If trace fetching fails
    """
    if not project_name:
        raise ValueError(
            "Weave project name not configured. "
            "Set WEAVE_PROJECT_NAME env var or use --weave-project"
        )

    print(f"📊 Fetching traces from Weave project: {project_name}")

    try:
        fetcher = WeaveTraceFetcher(project_name)
        traces = fetcher.fetch_recent_traces(
            num_traces=num_traces,
            op_name_filter=op_name_filter,
            trace_roots_only=True
        )

        if not traces:
            print("⚠️  No traces found. Possible reasons:")
            print("   - No solver runs in the project yet")
            print(f"   - No traces match filter '{op_name_filter}'")
            print("   - Try running gsm8k_eval_with_calculator.py first")

        return traces

    except Exception as e:
        print(f"❌ Failed to fetch traces: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check WEAVE_PROJECT_NAME or --weave-project is correct")
        print("  2. Verify WANDB_API_KEY is set in environment")
        print("  3. Ensure the project exists and has traces")
        raise


def save_results(output_file: str, results: dict):
    """Save analysis results to JSON file."""
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Results saved to {output_file}")


def print_pattern_summary(patterns: list):
    """Print human-readable summary of identified patterns."""
    if not patterns:
        print("\n❌ No patterns identified")
        return

    print(f"\n{'='*60}")
    print(f"PATTERNS IDENTIFIED: {len(patterns)}")
    print(f"{'='*60}\n")

    for i, pattern in enumerate(patterns, 1):
        print(f"{i}. {pattern.get('pattern_name', 'Unknown')}")
        print(f"   Type: {pattern.get('pattern_type', 'N/A')}")
        print(f"   Frequency: {pattern.get('frequency', 0)} occurrences")
        print(f"   Abstraction Potential: {pattern.get('abstraction_potential', 0):.2f}")
        print(f"   Description: {pattern.get('description', 'N/A')}")
        print()


def print_tool_proposals(proposals: list):
    """Print human-readable summary of tool proposals."""
    if not proposals:
        print("\n❌ No tool proposals generated")
        return

    print(f"\n{'='*60}")
    print(f"TOOL PROPOSALS: {len(proposals)}")
    print(f"{'='*60}\n")

    for i, proposal in enumerate(proposals, 1):
        print(f"{i}. {proposal.get('tool_name', 'Unknown')}")
        print(f"   Category: {proposal.get('category', 'N/A')}")
        print(f"   Priority: {proposal.get('priority', 'N/A').upper()}")
        print(f"   Description: {proposal.get('description', 'N/A')}")
        print(f"   Generalization: {proposal.get('generalization_scope', 'N/A')}")
        print()


def print_specifications(specifications: list):
    """Print human-readable summary of tool specifications."""
    if not specifications:
        print("\n❌ No specifications generated")
        return

    print(f"\n{'='*60}")
    print(f"TOOL SPECIFICATIONS: {len(specifications)}")
    print(f"{'='*60}\n")

    for i, spec in enumerate(specifications, 1):
        print(f"{i}. {spec.get('name', 'Unknown')}")
        print(f"   Description: {spec.get('description', 'N/A')}")
        print(f"   Category: {spec.get('category', 'N/A')}")
        print(f"   Deterministic: {spec.get('deterministic_validated', spec.get('deterministic', False))}")
        print(f"   Complexity: {spec.get('implementation_complexity', 'N/A')}")

        if 'algorithm_sketch' in spec:
            print(f"   Algorithm Sketch:")
            for line in spec['algorithm_sketch'].split('\n')[:5]:  # First 5 lines
                print(f"     {line}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Run Automatic Tool Creation pattern recognition and tool ideation"
    )
    parser.add_argument(
        "--traces",
        type=int,
        default=20,
        help="Number of recent traces to analyze (default: 20)"
    )
    parser.add_argument(
        "--min-frequency",
        type=int,
        default=3,
        help="Minimum pattern occurrences for detection (default: 3)"
    )
    parser.add_argument(
        "--weave-project",
        type=str,
        default=None,
        help="Weave project name (defaults to WEAVE_PROJECT_NAME env var)"
    )
    parser.add_argument(
        "--agent-domain",
        type=str,
        default="general",
        help="Agent domain for context: math, code, data, general (default: general)"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="atc_results/tool_proposals.json",
        help="Output file for results (default: atc_results/tool_proposals.json)"
    )
    parser.add_argument(
        "--generate-specs",
        action="store_true",
        help="Generate detailed specifications for tool proposals"
    )
    parser.add_argument(
        "--op-name-filter",
        type=str,
        default="run_react_agent",
        help="Filter traces by operation name (default: run_react_agent)"
    )
    parser.add_argument(
        "--generate-code",
        action="store_true",
        help="Generate Python code from specifications (requires --generate-specs)"
    )
    parser.add_argument(
        "--test-in-sandbox",
        action="store_true",
        help="Test generated code in Daytona sandbox (requires --generate-code and DAYTONA_API_KEY)"
    )
    parser.add_argument(
        "--test-daytona",
        action="store_true",
        help="Test Daytona connection only and exit"
    )

    args = parser.parse_args()

    # Handle Daytona connection test
    if args.test_daytona:
        print("="*60)
        print("Testing Daytona Connection")
        print("="*60)
        try:
            from sea.daytona_manager import DaytonaManager
            manager = DaytonaManager()
            result = manager.test_connection()

            if result["success"]:
                print("\n✓ Daytona connection test PASSED")
                print(f"  Execution time: {result['execution_time']:.2f}s")
                return
            else:
                print("\n✗ Daytona connection test FAILED")
                print(f"  Error: {result.get('error', 'Unknown error')}")
                return
        except Exception as e:
            print(f"\n✗ Daytona connection test FAILED with exception:")
            print(f"  {str(e)}")
            return

    print("="*60)
    print("Automatic Tool Creation - Full Pipeline")
    print("="*60)

    # Validate Weave project configuration
    weave_project = args.weave_project or os.getenv("WEAVE_PROJECT_NAME")
    if not weave_project:
        print("\n❌ ERROR: Weave project not configured")
        print("\nPlease set WEAVE_PROJECT_NAME environment variable or use --weave-project")
        print("Example: export WEAVE_PROJECT_NAME='your-entity/your-project'")
        return

    # Initialize Weave
    try:
        weave.init(weave_project)
        print(f"✓ Weave initialized: {weave_project}")
    except Exception as e:
        print(f"\n❌ Failed to initialize Weave: {str(e)}")
        print("Check your WANDB_API_KEY and project name")
        return

    # Initialize orchestrator
    orchestrator = ATCOrchestrator(project_name=weave_project)
    print("✓ ATCOrchestrator initialized")

    # Validate flags
    if args.test_in_sandbox and not args.generate_code:
        print("\n⚠️  WARNING: --test-in-sandbox requires --generate-code")
        print("Enabling code generation automatically")
        args.generate_code = True

    if args.generate_code and not args.generate_specs:
        print("\n⚠️  WARNING: --generate-code requires --generate-specs")
        print("Enabling specification generation automatically")
        args.generate_specs = True

    # Run ATC cycle
    results = orchestrator.run_atc_cycle(
        num_traces=args.traces,
        agent_domain=args.agent_domain,
        min_frequency=args.min_frequency,
        generate_specifications=args.generate_specs,
        generate_code=args.generate_code,
        test_in_sandbox=args.test_in_sandbox,
        op_name_filter=args.op_name_filter
    )

    # Print detailed summaries
    print_pattern_summary(results.get('patterns_identified', []))
    print_tool_proposals(results.get('tool_proposals', []))

    if args.generate_specs:
        print_specifications(results.get('tool_specifications', []))

    # Print code generation results
    if args.generate_code:
        generated_tools = results.get('generated_tools', [])
        print(f"\n{'='*60}")
        print(f"CODE GENERATION RESULTS: {len(generated_tools)}")
        print(f"{'='*60}\n")

        for i, tool in enumerate(generated_tools, 1):
            tool_name = tool.get('tool_name', 'Unknown')
            has_code = bool(tool.get('tool_code'))
            code_valid = tool.get('code_valid', False)

            status = "✓" if has_code else "✗"
            validity = "(valid)" if code_valid else "(invalid)" if has_code else ""

            print(f"{i}. {status} {tool_name} {validity}")
            if has_code:
                print(f"   Dependencies: {', '.join(tool.get('dependencies', []))}")

    # Print test results
    if args.test_in_sandbox:
        test_results = results.get('test_results', [])
        print(f"\n{'='*60}")
        print(f"SANDBOX TEST RESULTS: {len(test_results)}")
        print(f"{'='*60}\n")

        passed = 0
        for result in test_results:
            if result['success']:
                passed += 1
                print(f"✓ {result['tool_name']} - PASSED ({result.get('execution_time', 0):.2f}s)")
            else:
                print(f"✗ {result['tool_name']} - FAILED")
                if result.get('error'):
                    print(f"   Error: {result['error'][:100]}")

        print(f"\nTotal: {passed}/{len(test_results)} tests passed")

    # Save results
    save_results(args.output_file, results)

    # Final summary
    print(f"\n{'='*60}")
    print("ATC CYCLE COMPLETE")
    print(f"{'='*60}")
    print(f"✓ Patterns identified: {len(results.get('patterns_identified', []))}")
    print(f"✓ Tool proposals: {len(results.get('tool_proposals', []))}")
    print(f"✓ Specifications: {len(results.get('tool_specifications', []))}")
    print(f"✓ Code generated: {len(results.get('generated_tools', []))}")
    print(f"✓ Tests passed: {sum(1 for r in results.get('test_results', []) if r['success'])}/{len(results.get('test_results', []))}")
    print(f"✓ Results saved to: {args.output_file}")
    print(f"✓ Check Weave UI for detailed traces!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
