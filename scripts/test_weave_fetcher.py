# ABOUTME: Test script for WeaveTraceFetcher to verify trace retrieval
# ABOUTME: Quick validation that we can fetch and format real Weave traces

import sys
sys.path.insert(0, '.')

from sea.weave_trace_fetcher import WeaveTraceFetcher
import json

def main():
    print("="*60)
    print("Testing WeaveTraceFetcher")
    print("="*60)

    # Initialize fetcher with project from environment
    project_name = "vishnu-narasimha/sea-project"
    print(f"\n📊 Initializing WeaveTraceFetcher for project: {project_name}")

    fetcher = WeaveTraceFetcher(project_name)

    # Fetch recent traces
    print(f"\n🔍 Fetching recent traces...")
    traces = fetcher.fetch_recent_traces(
        num_traces=5,
        op_name_filter="run_react_agent",
        trace_roots_only=True
    )

    print(f"\n{'='*60}")
    print(f"RESULTS: Retrieved {len(traces)} traces")
    print(f"{'='*60}\n")

    # Display summary of each trace
    for i, trace in enumerate(traces, 1):
        print(f"\nTrace {i}:")
        print(f"  ID: {trace['trace_id']}")
        print(f"  Problem: {trace['problem'][:100]}...")
        print(f"  Solution length: {len(str(trace['solution']))} chars")
        print(f"  Tools invoked: {trace['tools_invoked']}")
        print(f"  Metadata: {trace['metadata']}")

    # Save first trace as example
    if traces:
        output_file = "atc_results/example_trace.json"
        print(f"\n💾 Saving first trace to {output_file}")
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(traces[0], f, indent=2, default=str)

        print(f"✓ Example trace saved")

    print(f"\n{'='*60}")
    print("Test Complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
