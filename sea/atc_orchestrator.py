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
        use_config: bool = True,
        pattern_model: str = None,
        ideator_model: str = None,
        codegen_model: str = None
    ):
        """
        Initialize ATC orchestrator.

        Args:
            project_name: Weave project name for trace fetching
            use_config: Whether to use config.yaml for model selection (default: True)
            pattern_model: Optional model override for pattern recognition
            ideator_model: Optional model override for tool ideation
            codegen_model: Optional model override for code generation
        """
        self.project_name = project_name
        self.trace_fetcher = WeaveTraceFetcher(project_name)
        self.pattern_recognizer = PatternRecognizer(model=pattern_model, use_config=use_config)
        self.tool_ideator = ToolIdeator(model=ideator_model, use_config=use_config)
        self.tool_generator = ToolGenerator(model=codegen_model, use_config=use_config)
        self.daytona_manager = None  # Lazy initialization

    @weave.op()
    def run_atc_cycle(
        self,
        num_traces: int = 10,
        min_frequency: int = 3,
        generate_specifications: bool = True,
        generate_code: bool = False,
        test_in_sandbox: bool = False,
        save_to_agent: str = None,
        max_test_attempts: int = 3,
        op_name_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run complete ATC cycle: traces → patterns → specifications → code → testing.

        Args:
            num_traces: Number of traces to analyze (default: 10)
            min_frequency: Minimum pattern occurrences (default: 3)
            generate_specifications: Whether to generate detailed specs
            generate_code: Whether to generate Python code from specs
            test_in_sandbox: If True, tests code in sandbox before saving (strict quality gate)
            save_to_agent: Agent name to save tools to (e.g., "math_solver")
            max_test_attempts: Maximum regeneration attempts if sandbox tests fail
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

        # Step 4: Generate code with integrated testing (optional)
        if generate_code and results["tool_specifications"]:
            print(f"\n💻 STEP 4: Generating Python code")
            if test_in_sandbox:
                print(f"   🔒 Strict mode: Tools will be tested before saving")

            # Initialize DaytonaManager if testing enabled
            if test_in_sandbox and not self.daytona_manager:
                try:
                    print(f"   Initializing Daytona sandbox manager...")
                    self.daytona_manager = DaytonaManager()
                except Exception as e:
                    error_msg = f"Failed to initialize DaytonaManager: {str(e)}"
                    print(f"❌ {error_msg}")
                    results["errors"].append(error_msg)
                    # Disable testing if manager fails
                    test_in_sandbox = False

            try:
                generated_tools = []

                for spec in results["tool_specifications"]:
                    tool_name = spec.get('name', 'unknown')
                    print(f"\n  Generating {tool_name}...")

                    try:
                        # Generate code with optional testing
                        code_result = self.tool_generator.generate_code(
                            specification=spec,
                            save_to_agent=save_to_agent,
                            test_before_save=test_in_sandbox,
                            daytona_manager=self.daytona_manager if test_in_sandbox else None,
                            max_test_attempts=max_test_attempts
                        )

                        generated_tools.append(code_result)

                        # Report status
                        if code_result.get('save_status') == 'saved':
                            test_info = ""
                            if test_in_sandbox and code_result.get('test_attempts'):
                                attempts = code_result['test_attempts']
                                test_info = f" (tested, {attempts} attempt{'s' if attempts > 1 else ''})"
                            print(f"  ✓ {tool_name}: Saved successfully{test_info}")
                        elif code_result.get('save_status') == 'test_failed':
                            attempts = code_result.get('test_attempts', 0)
                            print(f"  ✗ {tool_name}: Tests failed after {attempts} attempts - NOT saved")
                        elif code_result.get('save_status') == 'validation_failed':
                            print(f"  ✗ {tool_name}: Validation failed - NOT saved")
                        elif not code_result.get('tool_code'):
                            print(f"  ✗ {tool_name}: Code generation failed")
                        else:
                            print(f"  ℹ️  {tool_name}: Generated but not saved")

                    except Exception as e:
                        error_msg = f"Error generating {tool_name}: {str(e)}"
                        print(f"  ❌ {error_msg}")
                        generated_tools.append({
                            "error": str(e),
                            "specification": spec,
                            "tool_name": tool_name,
                            "tool_code": None
                        })

                results["generated_tools"] = generated_tools

                # Summary statistics
                total_tools = len(generated_tools)
                successful_gen = sum(1 for tool in generated_tools if tool.get("tool_code"))
                saved_tools = sum(1 for tool in generated_tools if tool.get("save_status") == "saved")
                test_failed = sum(1 for tool in generated_tools if tool.get("save_status") == "test_failed")

                print(f"\n✓ Code generation complete:")
                print(f"  - Generated: {successful_gen}/{total_tools}")
                print(f"  - Saved: {saved_tools}/{total_tools}")
                if test_in_sandbox:
                    print(f"  - Test failures: {test_failed}/{total_tools}")

            except Exception as e:
                error_msg = f"Code generation failed: {str(e)}"
                print(f"❌ {error_msg}")
                results["errors"].append(error_msg)

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

        # Tools saved summary
        saved_count = sum(1 for t in results['generated_tools'] if t.get('save_status') == 'saved')
        print(f"Tools saved: {saved_count}/{len(results['generated_tools'])}")

        # Test summary (if testing was enabled)
        if test_in_sandbox and results['generated_tools']:
            test_failed_count = sum(1 for t in results['generated_tools'] if t.get('save_status') == 'test_failed')
            print(f"Test failures: {test_failed_count}/{len(results['generated_tools'])}")

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
