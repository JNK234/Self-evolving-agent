# ABOUTME: UnifiedOrchestrator coordinates sequential self-improvement cycles
# ABOUTME: Runs Critic-Tuner → ATC in sequence for complete agent evolution

import weave
from typing import Dict, Any, List
from sea.orchestrator import CriticTunerOrchestrator
from sea.atc_orchestrator import ATCOrchestrator
from src.llm.llm_factory import get_config


class UnifiedOrchestrator:
    """Coordinates sequential self-improvement: Critic-Tuner → Automatic Tool Creation."""

    def __init__(
        self,
        critic_tuner_orchestrator: CriticTunerOrchestrator,
        atc_orchestrator: ATCOrchestrator,
        config_path: str = "config.yaml"
    ):
        """
        Initialize unified orchestrator.

        Args:
            critic_tuner_orchestrator: Initialized Critic-Tuner orchestrator
            atc_orchestrator: Initialized ATC orchestrator
            config_path: Path to configuration file
        """
        self.critic_tuner = critic_tuner_orchestrator
        self.atc = atc_orchestrator

        # Load self-improvement configuration
        self.config = get_config("self_improvement", config_path)
        self.ct_enabled = self.config.get("critic_tuner", {}).get("enabled", True)
        self.atc_enabled = self.config.get("automatic_tool_creation", {}).get("enabled", True)
        self.min_pattern_frequency = self.config.get("automatic_tool_creation", {}).get("min_pattern_frequency", 3)
        self.test_in_sandbox = self.config.get("automatic_tool_creation", {}).get("test_in_sandbox", True)
        self.max_test_attempts = self.config.get("automatic_tool_creation", {}).get("max_test_attempts", 3)

    @weave.op()
    def run_self_improvement_cycle(
        self,
        problems: List[Dict[str, Any]],
        solver_func,
        current_prompt_obj: weave.StringPrompt,
        num_recent_traces: int = 10,
        op_name_filter: str = None,
        save_tools_to_agent: str = None
    ) -> Dict[str, Any]:
        """
        Run complete self-improvement cycle: Critic-Tuner → ATC.

        Args:
            problems: List of problems for Critic-Tuner evaluation
            solver_func: Solver function for Critic-Tuner
            current_prompt_obj: Current solver prompt (weave.StringPrompt)
            num_recent_traces: Number of recent traces for ATC (default: 10)
            op_name_filter: Filter for trace retrieval
            save_tools_to_agent: Agent name to save generated tools to

        Returns:
            Dictionary with results from both stages:
            {
                "critic_tuner_results": {...},
                "atc_results": {...},
                "final_prompt": str,  # Updated prompt text
                "tools_created": int,  # Number of new tools
                "tools_saved": List[str],  # Names of saved tools
                "cycle_summary": str
            }
        """
        print("\n" + "="*70)
        print("UNIFIED SELF-IMPROVEMENT CYCLE")
        print("="*70)

        results = {
            "critic_tuner_results": None,
            "atc_results": None,
            "final_prompt": current_prompt_obj.content,
            "tools_created": 0,
            "tools_saved": [],
            "cycle_summary": ""
        }

        # Stage 1: Critic-Tuner Cycle
        if self.ct_enabled:
            print("\n📊 STAGE 1: Critic-Tuner Cycle")
            print("-" * 70)

            try:
                ct_results = self.critic_tuner.run_cycle(
                    problems=problems,
                    solver_func=solver_func,
                    current_prompt_obj=current_prompt_obj
                )

                results["critic_tuner_results"] = ct_results

                # Update prompt if changed
                if ct_results.get("updated"):
                    results["final_prompt"] = ct_results["new_prompt"]
                    current_prompt_obj = weave.StringPrompt(ct_results["new_prompt"])
                    print(f"\n✓ Prompt updated (score: {ct_results['avg_score']:.3f})")
                    print(f"  Changes: {ct_results['changes_summary']}")
                else:
                    print(f"\n✓ Prompt unchanged (score: {ct_results['avg_score']:.3f} >= threshold)")

            except Exception as e:
                print(f"\n❌ Critic-Tuner cycle failed: {e}")
                results["cycle_summary"] += f"Critic-Tuner error: {str(e)}. "
        else:
            print("\n⚠️  STAGE 1: Critic-Tuner disabled in config")

        # Stage 2: Automatic Tool Creation
        if self.atc_enabled:
            print("\n\n🔧 STAGE 2: Automatic Tool Creation")
            print("-" * 70)

            try:
                atc_results = self.atc.run_atc_cycle(
                    num_traces=num_recent_traces,
                    min_frequency=self.min_pattern_frequency,
                    generate_specifications=True,
                    generate_code=True,
                    test_in_sandbox=self.test_in_sandbox,
                    save_to_agent=save_tools_to_agent,
                    max_test_attempts=self.max_test_attempts,
                    op_name_filter=op_name_filter
                )

                results["atc_results"] = atc_results

                # Extract tool creation stats
                generated_tools = atc_results.get("generated_tools", [])
                results["tools_created"] = len(generated_tools)

                saved_tools = [
                    t.get("tool_name") for t in generated_tools
                    if t.get("save_status") == "saved"
                ]
                results["tools_saved"] = saved_tools

                if saved_tools:
                    print(f"\n✓ Tools created and saved: {', '.join(saved_tools)}")

                    # TODO: Update prompt to include instructions for new tools
                    # This would require the Updater to be called with tool usage instructions
                    print(f"   Note: Consider updating prompt to include tool usage instructions")
                else:
                    print(f"\n✓ Pattern analysis complete - no new tools created")

            except Exception as e:
                print(f"\n❌ ATC cycle failed: {e}")
                results["cycle_summary"] += f"ATC error: {str(e)}. "
        else:
            print("\n\n⚠️  STAGE 2: ATC disabled in config")

        # Generate cycle summary
        summary_parts = []
        if self.ct_enabled and results["critic_tuner_results"]:
            ct = results["critic_tuner_results"]
            summary_parts.append(
                f"Prompt: {'updated' if ct.get('updated') else 'unchanged'} "
                f"(score: {ct.get('avg_score', 0):.3f})"
            )

        if self.atc_enabled and results["atc_results"]:
            summary_parts.append(
                f"Tools: {len(results['tools_saved'])} created/saved"
            )

        results["cycle_summary"] = " | ".join(summary_parts) if summary_parts else "No changes"

        print("\n" + "="*70)
        print("CYCLE COMPLETE")
        print("="*70)
        print(f"Summary: {results['cycle_summary']}")
        print("="*70 + "\n")

        return results


def create_unified_orchestrator(
    weave_project: str,
    rubric_path: str = "src/agents/math_solver/rubric.json",
    config_path: str = "config.yaml"
) -> UnifiedOrchestrator:
    """
    Factory function to create a configured UnifiedOrchestrator.

    Args:
        weave_project: Weave project name for trace fetching
        rubric_path: Path to evaluation rubric
        config_path: Path to configuration file

    Returns:
        Configured UnifiedOrchestrator instance

    Example:
        >>> orchestrator = create_unified_orchestrator("my-project")
        >>> results = orchestrator.run_self_improvement_cycle(
        ...     problems=problems,
        ...     solver_func=solve_with_prompt,
        ...     current_prompt_obj=prompt_obj,
        ...     save_tools_to_agent="math_solver"
        ... )
    """
    from sea.critic import Critic
    from sea.updater import Updater

    # Load config for initialization
    config = get_config("self_improvement", config_path)
    ct_config = config.get("critic_tuner", {})

    # Initialize Critic-Tuner components (will use config internally)
    critic = Critic(rubric_path=rubric_path, use_config=True)
    updater = Updater(
        max_suggestions=ct_config.get("max_suggestions", 3),
        use_config=True
    )
    ct_orchestrator = CriticTunerOrchestrator(
        critic=critic,
        updater=updater,
        threshold=ct_config.get("score_threshold", 0.85)
    )

    # Initialize ATC orchestrator (will use config internally)
    atc_orchestrator = ATCOrchestrator(
        project_name=weave_project,
        use_config=True
    )

    return UnifiedOrchestrator(
        critic_tuner_orchestrator=ct_orchestrator,
        atc_orchestrator=atc_orchestrator,
        config_path=config_path
    )
