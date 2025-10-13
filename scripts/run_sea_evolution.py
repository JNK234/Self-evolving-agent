# ABOUTME: Main entry point for Self-Evolving Agent system
# ABOUTME: Runs multi-cycle evolution with Solver → Critic → Updater loop

import os
import json
import weave
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sea.critic import Critic
from sea.updater import Updater
from sea.orchestrator import CriticTunerOrchestrator
from src.llm.inference import run_react_agent
from src.agents.tools.langchain_calculator import calculator_tool

load_dotenv()


def solve_with_prompt(question: str, prompt_obj: weave.StringPrompt) -> str:
    """Solve problem using current prompt object."""
    return run_react_agent(
        question=question,
        tools=[calculator_tool],
        system_message=prompt_obj.content,  # Extract content from weave prompt
        temperature=0
    )


def save_prompt_version(prompt: str, version: int, changes: str):
    """Save prompt version to file."""
    os.makedirs("prompts", exist_ok=True)
    filename = f"prompts/prompt_v{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w') as f:
        f.write(f"# Version {version}\n")
        f.write(f"# Changes: {changes}\n")
        f.write(f"# Timestamp: {datetime.now().isoformat()}\n\n")
        f.write(prompt)
    return filename


def main(
    problems_per_cycle: int = 10,
    num_cycles: int = 3,
    threshold: float = 0.85,
    initial_prompt_file: str = "prompt_templates/agents/math_solver/advanced.txt",
    prompt_name: str = "math_solver_prompt",
    experiment_id: str = None
):
    """
    Run multi-cycle SEA evolution.

    Args:
        problems_per_cycle: Number of problems to evaluate per cycle
        num_cycles: Total number of evolution cycles
        threshold: Score threshold for triggering updates
        initial_prompt_file: Path to initial solver prompt
        prompt_name: Name to use when publishing prompts to Weave (default: "math_solver_prompt")
        experiment_id: Optional unique ID for this experiment (e.g., "exp_001", "baseline_v2")
                       If provided, prompt name becomes "{prompt_name}_{experiment_id}"
    """
    print("="*60)
    print("Self-Evolving Agent - Critic-Tuner System")
    print("="*60)

    # Initialize Weave
    weave_project = os.getenv("WEAVE_PROJECT_NAME", "sea-evolution")
    weave.init(weave_project)
    print(f"✓ Weave initialized: {weave_project}")

    # Load initial prompt and wrap in Weave StringPrompt
    with open(initial_prompt_file, 'r') as f:
        initial_prompt_text = f.read()

    # Determine final prompt name
    if experiment_id:
        final_prompt_name = f"{prompt_name}_{experiment_id}"
    else:
        final_prompt_name = prompt_name

    # Create Weave StringPrompt object
    current_prompt_obj = weave.StringPrompt(initial_prompt_text)

    # Publish initial prompt to Weave (creates version v0)
    weave.publish(current_prompt_obj, name=final_prompt_name)
    print(f"✓ Initial prompt loaded from {initial_prompt_file}")
    print(f"✓ Initial prompt published to Weave as '{final_prompt_name}:v0'")

    # Initialize components
    critic = Critic()
    updater = Updater(max_suggestions=2)
    orchestrator = CriticTunerOrchestrator(
        critic=critic,
        updater=updater,
        threshold=threshold
    )
    print("✓ Critic-Tuner orchestrator initialized")

    # Load GSM8K problems
    dataset = pd.read_csv("data/train.csv")
    all_problems = [
        {"question": row['question'], "answer": row['answer']}
        for _, row in dataset.iterrows()
    ]
    print(f"✓ Loaded {len(all_problems)} GSM8K problems")

    # Save initial prompt to local file as backup (optional)
    prompt_version = 0  # Weave starts at v0
    save_prompt_version(current_prompt_obj.content, prompt_version, "Initial prompt")
    print()

    # Run cycles
    cycle_history = []

    for cycle in range(num_cycles):
        print("="*60)
        print(f"CYCLE {cycle + 1}/{num_cycles}")
        print("="*60)

        # Get problems for this cycle
        start_idx = cycle * problems_per_cycle
        end_idx = start_idx + problems_per_cycle
        cycle_problems = all_problems[start_idx:end_idx]

        print(f"Processing problems {start_idx+1}-{end_idx}...")

        # Run cycle
        stats = orchestrator.run_cycle(
            problems=cycle_problems,
            solver_func=solve_with_prompt,
            current_prompt_obj=current_prompt_obj
        )

        # Update prompt if changed
        if stats['updated']:
            prompt_version += 1

            # Get new prompt text and wrap in Weave StringPrompt
            new_prompt_text = stats['new_prompt']
            current_prompt_obj = weave.StringPrompt(new_prompt_text)

            # Publish new version to Weave (auto-increments version)
            weave.publish(current_prompt_obj, name=final_prompt_name)
            print(f"✓ Prompt published to Weave as '{final_prompt_name}:v{prompt_version}'")

            # Save to local file as backup (optional)
            prompt_file = save_prompt_version(
                new_prompt_text,
                prompt_version,
                stats['changes_summary']
            )
            print(f"✓ Prompt backup saved → {prompt_file}")

        # Print cycle summary
        print(f"\nCycle Results:")
        print(f"  Average Score: {stats['avg_score']:.3f}")
        print(f"  Criterion Scores:")
        for criterion_id, score in stats['criterion_scores'].items():
            print(f"    - {criterion_id}: {score:.3f}")
        print(f"  Prompt Updated: {stats['updated']}")
        print(f"  Changes: {stats['changes_summary']}")
        print(f"  Current Version: v{prompt_version}")
        print()

        # Track history
        cycle_history.append({
            'cycle': cycle + 1,
            'avg_score': stats['avg_score'],
            'criterion_scores': stats['criterion_scores'],
            'updated': stats['updated'],
            'version': prompt_version
        })

    # Final summary
    print("="*60)
    print("EVOLUTION COMPLETE")
    print("="*60)
    print(f"Final Prompt Version: v{prompt_version}")
    print(f"Total Updates: {sum(1 for h in cycle_history if h['updated'])}")
    print("\nScore Evolution:")
    for h in cycle_history:
        status = "→ UPDATED" if h['updated'] else ""
        print(f"  Cycle {h['cycle']}: {h['avg_score']:.3f} (v{h['version']}) {status}")

    print(f"\n✓ Check Weave UI for full evolution traces!")
    print(f"✓ Prompt versions saved in prompts/ directory")
    print("="*60)

    # Save history
    with open("prompts/evolution_history.json", 'w') as f:
        json.dump(cycle_history, f, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Self-Evolving Agent cycles")
    parser.add_argument("--problems", type=int, default=10, help="Problems per cycle")
    parser.add_argument("--cycles", type=int, default=3, help="Number of cycles")
    parser.add_argument("--threshold", type=float, default=0.85, help="Update threshold")
    parser.add_argument("--prompt", type=str, default="prompt_templates/agents/math_solver/advanced.txt",
                       help="Initial prompt file")
    parser.add_argument("--name", type=str, default="math_solver_prompt",
                       help="Base name for prompt in Weave")
    parser.add_argument("--experiment-id", type=str, default=None,
                       help="Unique experiment ID (e.g., 'baseline_v1', 'exp_001')")

    args = parser.parse_args()

    main(
        problems_per_cycle=args.problems,
        num_cycles=args.cycles,
        threshold=args.threshold,
        initial_prompt_file=args.prompt,
        prompt_name=args.name,
        experiment_id=args.experiment_id
    )
