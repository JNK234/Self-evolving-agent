# ABOUTME: Complete SEA pipeline with unified self-improvement cycles
# ABOUTME: Solver uses W&B Inference, critic/updater/tools use configured models

import os
import json
import weave
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sea.unified_orchestrator import create_unified_orchestrator
from src.llm.llm_factory import get_llm, get_config
from src.agents.tools.langchain_calculator import calculator_tool

load_dotenv()


def solve_with_wb_inference(question: str, prompt_obj: weave.StringPrompt) -> str:
    """
    Solve problem using W&B Inference with ReAct agent.

    Uses the solver model from config.yaml (default: W&B Inference).
    """
    from src.llm.inference import run_react_agent

    # Get solver LLM from config - will be W&B Inference client
    solver_llm = get_llm("solver")

    # Note: run_react_agent expects a LangChain-compatible model
    # For W&B Inference, we need a different approach
    # Let's use a wrapper that uses the WBInference client
    from src.llm.wb_inference import WBInference

    if isinstance(solver_llm, WBInference):
        # Use W&B Inference directly with simple prompting
        system_prompt = prompt_obj.content
        full_prompt = f"{system_prompt}\n\nQuestion: {question}\n\nThink step by step and use the calculator tool if needed. Format your answer clearly."

        response = solver_llm.run_inference(
            prompt=full_prompt,
            metadata={"task": "math_solving", "question": question}
        )
        return response
    else:
        # Use LangChain ReAct agent for other providers
        return run_react_agent(
            question=question,
            tools=[calculator_tool],
            system_message=prompt_obj.content,
            temperature=0
        )


def save_prompt_version(prompt: str, version: int, changes: str, experiment_id: str = None):
    """Save prompt version to file."""
    os.makedirs("prompts", exist_ok=True

)
    prefix = f"{experiment_id}_" if experiment_id else ""
    filename = f"prompts/{prefix}prompt_v{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w') as f:
        f.write(f"# Version {version}\n")
        if experiment_id:
            f.write(f"# Experiment: {experiment_id}\n")
        f.write(f"# Changes: {changes}\n")
        f.write(f"# Timestamp: {datetime.now().isoformat()}\n\n")
        f.write(prompt)
    return filename


def main(
    problems_per_cycle: int = 10,
    num_cycles: int = 3,
    trigger_every_n: int = None,  # From config if not specified
    initial_prompt_file: str = "prompt_templates/agents/math_solver/advanced.txt",
    prompt_name: str = "math_solver_prompt",
    experiment_id: str = None,
    agent_name: str = "math_solver"
):
    """
    Run complete SEA pipeline with unified self-improvement.

    Args:
        problems_per_cycle: Problems per evaluation cycle
        num_cycles: Total evolution cycles
        trigger_every_n: Run self-improvement every N problems (from config if None)
        initial_prompt_file: Path to initial solver prompt
        prompt_name: Weave prompt name
        experiment_id: Unique experiment ID
        agent_name: Agent to save generated tools to
    """
    print("="*70)
    print("FULL SEA PIPELINE - Unified Self-Improvement System")
    print("="*70)

    # Load configuration
    config = get_config()
    si_config = config.get("self_improvement", {})
    trigger_every_n = trigger_every_n or si_config.get("trigger_every_n_runs", 10)

    print(f"\nConfiguration:")
    print(f"  Solver: {config['llm_config']['solver']['provider']} - {config['llm_config']['solver']['model_name']}")
    print(f"  Critic: {config['llm_config']['critic']['provider']} - {config['llm_config']['critic']['model_name']}")
    print(f"  Updater: {config['llm_config']['updater']['provider']} - {config['llm_config']['updater']['model_name']}")
    print(f"  Tool Generator: {config['llm_config']['tool_generator']['provider']} - {config['llm_config']['tool_generator']['model_name']}")
    print(f"  Self-Improvement Trigger: Every {trigger_every_n} problems")
    print(f"  Critic-Tuner: {'Enabled' if si_config.get('critic_tuner', {}).get('enabled', True) else 'Disabled'}")
    print(f"  ATC: {'Enabled' if si_config.get('automatic_tool_creation', {}).get('enabled', True) else 'Disabled'}")

    # Initialize Weave
    weave_project = os.getenv("WEAVE_PROJECT_NAME", "sea-full-pipeline")
    weave.init(weave_project)
    print(f"\n✓ Weave initialized: {weave_project}")

    # Load initial prompt
    with open(initial_prompt_file, 'r') as f:
        initial_prompt_text = f.read()

    # Determine final prompt name
    final_prompt_name = f"{prompt_name}_{experiment_id}" if experiment_id else prompt_name

    # Create Weave StringPrompt object
    current_prompt_obj = weave.StringPrompt(initial_prompt_text)
    weave.publish(current_prompt_obj, name=final_prompt_name)
    print(f"✓ Initial prompt published to Weave as '{final_prompt_name}:v0'")

    # Initialize unified orchestrator
    orchestrator = create_unified_orchestrator(
        weave_project=weave_project,
        config_path="config.yaml"
    )
    print("✓ Unified orchestrator initialized")

    # Load GSM8K problems
    dataset = pd.read_csv("data/train.csv")
    all_problems = [
        {"question": row['question'], "answer": row['answer']}
        for _, row in dataset.iterrows()
    ]
    print(f"✓ Loaded {len(all_problems)} GSM8K problems\n")

    # Save initial prompt
    prompt_version = 0
    save_prompt_version(current_prompt_obj.content, prompt_version, "Initial prompt", experiment_id)

    # Evolution tracking
    cycle_history = []
    total_problems_processed = 0
    total_tools_created = 0

    # Run evolution cycles
    for cycle in range(num_cycles):
        print("\n" + "="*70)
        print(f"EVOLUTION CYCLE {cycle + 1}/{num_cycles}")
        print("="*70)

        # Get problems for this cycle
        start_idx = cycle * problems_per_cycle
        end_idx = start_idx + problems_per_cycle
        cycle_problems = all_problems[start_idx:end_idx]

        print(f"Processing problems {start_idx+1}-{end_idx}...")

        # Check if self-improvement should trigger
        total_problems_processed += len(cycle_problems)
        should_improve = (total_problems_processed % trigger_every_n == 0) or (cycle == 0)

        if should_improve:
            print(f"\n🔄 Self-improvement triggered (processed {total_problems_processed} problems)")

            # Run unified self-improvement cycle
            results = orchestrator.run_self_improvement_cycle(
                problems=cycle_problems,
                solver_func=solve_with_wb_inference,
                current_prompt_obj=current_prompt_obj,
                num_recent_traces=10,
                op_name_filter="run_react_agent",
                save_tools_to_agent=agent_name
            )

            # Update prompt if changed
            if results["final_prompt"] != current_prompt_obj.content:
                prompt_version += 1
                new_prompt_text = results["final_prompt"]
                current_prompt_obj = weave.StringPrompt(new_prompt_text)

                # Publish to Weave
                weave.publish(current_prompt_obj, name=final_prompt_name)
                print(f"✓ Prompt updated to v{prompt_version}")

                # Save backup
                changes = results.get("cycle_summary", "Self-improvement cycle")
                prompt_file = save_prompt_version(
                    new_prompt_text,
                    prompt_version,
                    changes,
                    experiment_id
                )
                print(f"✓ Backup saved → {prompt_file}")

            # Track tools created
            tools_created = len(results.get("tools_saved", []))
            total_tools_created += tools_created
            if tools_created > 0:
                print(f"✓ New tools: {', '.join(results['tools_saved'])}")

            # Record cycle stats
            ct_results = results.get("critic_tuner_results", {})
            cycle_history.append({
                'cycle': cycle + 1,
                'problems_processed': total_problems_processed,
                'avg_score': ct_results.get('avg_score', None),
                'prompt_updated': ct_results.get('updated', False),
                'prompt_version': prompt_version,
                'tools_created': tools_created,
                'total_tools': total_tools_created,
                'summary': results.get("cycle_summary", "")
            })
        else:
            print(f"\n⏭️  Self-improvement skipped (will trigger at {trigger_every_n} problems)")

            # Just evaluate without improvement
            # (In production, you'd still solve problems but skip the improvement cycle)
            cycle_history.append({
                'cycle': cycle + 1,
                'problems_processed': total_problems_processed,
                'avg_score': None,
                'prompt_updated': False,
                'prompt_version': prompt_version,
                'tools_created': 0,
                'total_tools': total_tools_created,
                'summary': "Evaluation only (no self-improvement)"
            })

    # Final summary
    print("\n" + "="*70)
    print("EVOLUTION COMPLETE")
    print("="*70)
    print(f"Final Prompt Version: v{prompt_version}")
    print(f"Total Problems Processed: {total_problems_processed}")
    print(f"Total Tools Created: {total_tools_created}")
    print(f"Total Prompt Updates: {sum(1 for h in cycle_history if h.get('prompt_updated'))}")

    print("\n📊 Evolution History:")
    for h in cycle_history:
        score_str = f"Score: {h['avg_score']:.3f}" if h['avg_score'] is not None else "No eval"
        tools_str = f"+{h['tools_created']} tools" if h['tools_created'] > 0 else ""
        status = "→ UPDATED" if h.get('prompt_updated') else ""
        print(f"  Cycle {h['cycle']}: {score_str} | v{h['prompt_version']} {tools_str} {status}")

    print(f"\n✓ Check Weave UI for full traces: {weave_project}")
    print(f"✓ Prompts saved in prompts/ directory")
    if total_tools_created > 0:
        print(f"✓ Generated tools in src/agents/{agent_name}/tools/generated/")
    print("="*70)

    # Save evolution history
    history_file = f"prompts/{experiment_id}_" if experiment_id else "prompts/"
    history_file += "evolution_history.json"
    with open(history_file, 'w') as f:
        json.dump(cycle_history, f, indent=2)
    print(f"✓ Evolution history saved: {history_file}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run full SEA pipeline with unified self-improvement")
    parser.add_argument("--problems", type=int, default=10, help="Problems per cycle")
    parser.add_argument("--cycles", type=int, default=3, help="Number of cycles")
    parser.add_argument("--trigger-every", type=int, default=None, help="Self-improve every N problems (from config if not set)")
    parser.add_argument("--prompt", type=str, default="prompt_templates/agents/math_solver/advanced.txt", help="Initial prompt file")
    parser.add_argument("--name", type=str, default="math_solver_prompt", help="Weave prompt name")
    parser.add_argument("--experiment-id", type=str, default=None, help="Experiment ID (e.g., 'exp_001')")
    parser.add_argument("--agent", type=str, default="math_solver", help="Agent name for tool saving")

    args = parser.parse_args()

    main(
        problems_per_cycle=args.problems,
        num_cycles=args.cycles,
        trigger_every_n=args.trigger_every,
        initial_prompt_file=args.prompt,
        prompt_name=args.name,
        experiment_id=args.experiment_id,
        agent_name=args.agent
    )
