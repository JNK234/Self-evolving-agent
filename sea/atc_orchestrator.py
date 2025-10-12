# ABOUTME: ATCOrchestrator coordinates the Automatic Tool Creation data pipeline
# ABOUTME: Manages flow from Weave traces through pattern recognition to tool specifications

import weave
from typing import Dict, Any, List, Optional
from datetime import datetime
from sea.weave_trace_fetcher import WeaveTraceFetcher
from sea.pattern_recognizer import PatternRecognizer
from sea.tool_ideator import ToolIdeator
from sea.tool_generator import ToolGenerator
from sea.daytona_manager import DaytonaManager


class ATCOrchestrator:
    """Orchestrates the ATC pipeline: fetch traces → identify patterns → generate specifications."""

    def __init__(
        self,
        project_name: str,
        pattern_model: str = "gemini-2.0-flash",
        ideator_model: str = "gemini-2.0-flash",
        codegen_model: str = "gemini-2.0-flash"
    ):
        """
        Initialize ATC orchestrator.

        Args:
            project_name: Weave project name for trace fetching
            pattern_model: Model for pattern recognition
            ideator_model: Model for tool ideation
            codegen_model: Model for code generation
        """
        self.project_name = project_name
        self.trace_fetcher = WeaveTraceFetcher(project_name)
        self.pattern_recognizer = PatternRecognizer(model=pattern_model)
        self.tool_ideator = ToolIdeator(model=ideator_model)
        self.tool_generator = ToolGenerator(model=codegen_model)
        self.daytona_manager = None  # Lazy initialization

    @weave.op()
    def run_atc_cycle(
        self,
        num_traces: int = 20,
        agent_domain: str = "math",
        min_frequency: int = 3,
        generate_specifications: bool = True,
        generate_code: bool = False,
        test_in_sandbox: bool = False,
        op_name_filter: Optional[str] = "run_react_agent"
    ) -> Dict[str, Any]:
        """
        Run complete ATC cycle: traces → patterns → specifications → code → testing.

        Args:
            num_traces: Number of traces to analyze
            agent_domain: Domain context for pattern recognition
            min_frequency: Minimum pattern occurrences
            generate_specifications: Whether to generate detailed specs
            generate_code: Whether to generate Python code from specs
            test_in_sandbox: Whether to test generated code in Daytona sandbox
            op_name_filter: Filter for specific operation names

        Returns:
            Dictionary with cycle results and metadata
        """
        print("\n" + "="*60)
        print("ATC CYCLE STARTED")
        print("="*60)

        cycle_start = datetime.now()
        results = {
            "cycle_metadata": {
                "start_time": cycle_start.isoformat(),
                "project_name": self.project_name,
                "num_traces_requested": num_traces,
                "agent_domain": agent_domain,
                "min_frequency": min_frequency
            },
            "patterns_identified": [],
            "tool_proposals": [],
            "tool_specifications": [],
            "generated_tools": [],
            "test_results": [],
            "errors": []
        }

        # Step 1: Fetch traces from Weave
        print(f"\n📊 STEP 1: Fetching traces from Weave")
        try:
            traces = self.trace_fetcher.fetch_recent_traces(
                num_traces=num_traces,
                op_name_filter=op_name_filter,
                trace_roots_only=True
            )
            results["cycle_metadata"]["traces_fetched"] = len(traces)
            print(f"✓ Successfully fetched {len(traces)} traces")

            if not traces:
                error_msg = "No traces found - cannot proceed with pattern analysis"
                print(f"❌ {error_msg}")
                results["errors"].append(error_msg)
                return results

        except Exception as e:
            error_msg = f"Failed to fetch traces: {str(e)}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            return results

        # Step 2: Identify patterns
        print(f"\n🔍 STEP 2: Analyzing patterns")
        try:
            pattern_analysis = self.pattern_recognizer.identify_patterns(
                traces=traces,
                agent_domain=agent_domain,
                min_frequency=min_frequency
            )

            results["patterns_identified"] = pattern_analysis.get("patterns_identified", [])
            results["tool_proposals"] = pattern_analysis.get("tool_proposals", [])
            results["meta_analysis"] = pattern_analysis.get("meta_analysis", {})

            num_patterns = len(results["patterns_identified"])
            num_proposals = len(results["tool_proposals"])

            print(f"✓ Pattern analysis complete")
            print(f"  - Patterns identified: {num_patterns}")
            print(f"  - Tool proposals: {num_proposals}")

            if num_patterns == 0:
                print("⚠️  No patterns found (may need more traces or lower frequency threshold)")

        except Exception as e:
            error_msg = f"Pattern recognition failed: {str(e)}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            return results

        # Step 3: Generate specifications (optional)
        if generate_specifications and results["patterns_identified"]:
            print(f"\n🛠️  STEP 3: Generating tool specifications")
            try:
                specifications = self.tool_ideator.generate_specifications_batch(
                    results["patterns_identified"]
                )
                results["tool_specifications"] = specifications
                print(f"✓ Generated {len(specifications)} specifications")

            except Exception as e:
                error_msg = f"Specification generation failed: {str(e)}"
                print(f"❌ {error_msg}")
                results["errors"].append(error_msg)

        # Step 4: Generate code (optional)
        if generate_code and results["tool_specifications"]:
            print(f"\n💻 STEP 4: Generating Python code")
            try:
                generated_tools = self.tool_generator.generate_code_batch(
                    results["tool_specifications"]
                )
                results["generated_tools"] = generated_tools

                successful_gen = sum(1 for tool in generated_tools if tool.get("tool_code"))
                print(f"✓ Generated code for {successful_gen}/{len(generated_tools)} tools")

            except Exception as e:
                error_msg = f"Code generation failed: {str(e)}"
                print(f"❌ {error_msg}")
                results["errors"].append(error_msg)

        # Step 5: Test in sandbox (optional)
        if test_in_sandbox and results["generated_tools"]:
            print(f"\n🧪 STEP 5: Testing code in Daytona sandboxes")

            # Lazy initialize DaytonaManager
            if not self.daytona_manager:
                try:
                    self.daytona_manager = DaytonaManager()
                except Exception as e:
                    error_msg = f"Failed to initialize DaytonaManager: {str(e)}"
                    print(f"❌ {error_msg}")
                    results["errors"].append(error_msg)
                    results["test_results"] = []

            if self.daytona_manager:
                test_results = []

                for tool in results["generated_tools"]:
                    if not tool.get("tool_code"):
                        print(f"  ⏭️  Skipping {tool.get('tool_name', 'unknown')} - no code generated")
                        continue

                    try:
                        print(f"  Testing {tool.get('tool_name', 'unknown')}...")
                        test_result = self.daytona_manager.run_code_with_tests(
                            tool_code=tool["tool_code"],
                            dependencies=tool.get("dependencies", ["pytest"])
                        )

                        test_results.append({
                            "tool_name": tool.get("tool_name", "unknown"),
                            "success": test_result["success"],
                            "exit_code": test_result["exit_code"],
                            "execution_time": test_result["execution_time"],
                            "output": test_result["output"],
                            "error": test_result.get("error")
                        })

                        status = "✓ PASS" if test_result["success"] else "✗ FAIL"
                        print(f"    {status} ({test_result['execution_time']:.2f}s)")

                    except Exception as e:
                        error_msg = f"Testing failed for {tool.get('tool_name', 'unknown')}: {str(e)}"
                        print(f"    ❌ {error_msg}")
                        test_results.append({
                            "tool_name": tool.get("tool_name", "unknown"),
                            "success": False,
                            "error": error_msg
                        })

                results["test_results"] = test_results
                passed = sum(1 for r in test_results if r["success"])
                print(f"✓ Testing complete: {passed}/{len(test_results)} passed")

        # Cycle summary
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()
        results["cycle_metadata"]["end_time"] = cycle_end.isoformat()
        results["cycle_metadata"]["duration_seconds"] = duration

        print(f"\n{'='*60}")
        print("ATC CYCLE COMPLETE")
        print(f"{'='*60}")
        print(f"Duration: {duration:.2f}s")
        print(f"Traces analyzed: {results['cycle_metadata']['traces_fetched']}")
        print(f"Patterns found: {len(results['patterns_identified'])}")
        print(f"Tool proposals: {len(results['tool_proposals'])}")
        print(f"Specifications: {len(results['tool_specifications'])}")
        print(f"Code generated: {len(results['generated_tools'])}")
        print(f"Tests passed: {sum(1 for r in results['test_results'] if r['success'])}/{len(results['test_results'])}")
        print(f"Errors: {len(results['errors'])}")
        print("="*60 + "\n")

        return results

    def print_cycle_summary(self, results: Dict[str, Any]):
        """
        Print human-readable summary of ATC cycle results.

        Args:
            results: Results dictionary from run_atc_cycle
        """
        print(f"\n{'='*60}")
        print("ATC CYCLE SUMMARY")
        print(f"{'='*60}\n")

        # Metadata
        meta = results.get("cycle_metadata", {})
        print(f"Project: {meta.get('project_name', 'N/A')}")
        print(f"Duration: {meta.get('duration_seconds', 0):.2f}s")
        print(f"Traces: {meta.get('traces_fetched', 0)}")
        print()

        # Patterns
        patterns = results.get("patterns_identified", [])
        if patterns:
            print(f"📋 PATTERNS IDENTIFIED: {len(patterns)}")
            for i, pattern in enumerate(patterns, 1):
                print(f"\n{i}. {pattern.get('pattern_name', 'Unknown')}")
                print(f"   Type: {pattern.get('pattern_type', 'N/A')}")
                print(f"   Frequency: {pattern.get('frequency', 0)} occurrences")
                print(f"   Abstraction: {pattern.get('abstraction_potential', 0):.2f}")
        else:
            print("📋 PATTERNS: None found")

        # Tool Proposals
        proposals = results.get("tool_proposals", [])
        if proposals:
            print(f"\n\n🔧 TOOL PROPOSALS: {len(proposals)}")
            for i, proposal in enumerate(proposals, 1):
                print(f"\n{i}. {proposal.get('tool_name', 'Unknown')}")
                print(f"   Category: {proposal.get('category', 'N/A')}")
                print(f"   Priority: {proposal.get('priority', 'N/A').upper()}")
                print(f"   Description: {proposal.get('description', 'N/A')[:100]}...")
        else:
            print("\n\n🔧 TOOL PROPOSALS: None generated")

        # Specifications
        specs = results.get("tool_specifications", [])
        if specs:
            print(f"\n\n📝 SPECIFICATIONS: {len(specs)}")
            for i, spec in enumerate(specs, 1):
                print(f"\n{i}. {spec.get('name', 'Unknown')}")
                print(f"   Deterministic: {spec.get('deterministic_validated', False)}")
                print(f"   Complexity: {spec.get('implementation_complexity', 'N/A')}")
        else:
            print(f"\n\n📝 SPECIFICATIONS: None generated")

        # Errors
        errors = results.get("errors", [])
        if errors:
            print(f"\n\n⚠️  ERRORS: {len(errors)}")
            for error in errors:
                print(f"  - {error}")

        print(f"\n{'='*60}\n")
