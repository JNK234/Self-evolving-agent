# ABOUTME: Unified SEA training with wandb metrics + Phase 4 ATC/config architecture
# ABOUTME: Combines sea_agent.py training loop with advanced orchestration from run_full_sea_pipeline.py

import os
import json
import weave
import wandb
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

from sea.unified_orchestrator import create_unified_orchestrator
from sea.critic import Critic
from sea.updater import Updater
from sea.orchestrator import CriticTunerOrchestrator
from sea.weave_trace_fetcher import WeaveTraceFetcher
from src.llm.llm_factory import get_config, get_llm
from src.llm.inference import run_react_agent
from src.agents.shared.tool_loader import load_agent_tools
from datasets import load_dataset

load_dotenv()


def extract_answer(text: str) -> str:
    """Extract numerical answer from text."""
    import re
    match = re.search(r'####\s*([0-9\.]+)', text)
    if match:
        return match.group(1)
    numbers = re.findall(r'[0-9\.]+', text)
    return numbers[-1] if numbers else None


def evaluate_with_llm(question: str, expected_answer: str, model_response: str) -> Dict[str, Any]:
    """LLM-based evaluation of model response."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import PromptTemplate

    with open("prompt_templates/eval_p.txt", 'r') as file:
        eval_prompt = file.read()

    prompt_template = PromptTemplate.from_template(eval_prompt)
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    chain = prompt_template | llm
    response = chain.invoke({
        "question": question,
        "expected_answer": expected_answer,
        "model_response": model_response
    })

    eval_text = response.content
    result = {"raw_evaluation": eval_text, "correct": None, "reasoning": None}

    lines = eval_text.split('\n')
    for line in lines:
        if line.startswith('CORRECT:'):
            correct_str = line.split(':', 1)[1].strip()
            result["correct"] = correct_str.lower() == 'true'
        elif line.startswith('REASONING:'):
            result["reasoning"] = line.split(':', 1)[1].strip()

    return result


def log_to_wandb(model_name: str, total: int, correct: int, accuracy: float,
                 responses: list, run_name: str, model_type: str = "SEA_Agent", dataset: str = "GSM8K"):
    """Log evaluation results to Weights & Biases with visualization."""
    wb_project = os.getenv("WB_INFERENCE_PROJECT")
    if not wb_project:
        raise ValueError("WB_INFERENCE_PROJECT must be set in .env file")

    wandb.init(
        project=wb_project,
        name=run_name,
        config={
            "model_name": model_name,
            "model_type": model_type,
            "dataset": dataset,
            "total_examples": total,
        }
    )

    # Log metrics
    wandb.log({
        "accuracy": accuracy,
        "correct": correct,
        "incorrect": total - correct,
        "total": total
    })

    # Log prompt versions as artifacts
    if hasattr(log_to_wandb, '_prompt_versions'):
        for pv in log_to_wandb._prompt_versions:
            wandb.log({
                f"prompt_v{pv['version']}": wandb.Html(f"<pre>{pv['prompt']}</pre>"),
                f"prompt_v{pv['version']}_accuracy": pv['accuracy']
            })

    # Create sample table
    if responses:
        table_data = []
        for i, resp in enumerate(responses[:10]):
            expected = resp.get('expected_answer', 'N/A')
            predicted = resp.get('predicted_answer', 'N/A')
            question = resp.get('question', 'N/A')
            is_correct = resp.get('is_correct', False)

            table_data.append([
                i + 1,
                question[:100] + "..." if len(question) > 100 else question,
                str(expected),
                str(predicted),
                "✓ Correct" if is_correct else "✗ Incorrect"
            ])

        table = wandb.Table(
            columns=["Example", "Question", "Expected", "Predicted", "Result"],
            data=table_data
        )
        wandb.log({"evaluation_samples": table})

    wandb.finish()
    print(f"✓ Results logged to Weights & Biases: {run_name}")


def save_eval_results(model_name: str, total: int, correct: int, incorrect: int,
                      accuracy: float, responses: list, run_name: str):
    """Save evaluation results to text file."""
    os.makedirs("eval_results", exist_ok=True)
    filename = f"eval_results/{run_name}_{model_name}.txt"

    with open(filename, 'w') as f:
        f.write(f"Evaluation Results - {run_name}\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Total: {total}\n")
        f.write(f"Correct: {correct}\n")
        f.write(f"Incorrect: {incorrect}\n")
        f.write(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)\n\n")
        f.write(f"Sample Results (first 10):\n")
        f.write(f"{'-'*60}\n")

        for i, resp in enumerate(responses[:10]):
            f.write(f"\n{i+1}. Question: {resp.get('question', 'N/A')[:100]}...\n")
            f.write(f"   Expected: {resp.get('expected_answer', 'N/A')}\n")
            f.write(f"   Predicted: {resp.get('predicted_answer', 'N/A')}\n")
            f.write(f"   Status: {'✓ Correct' if resp.get('is_correct') else '✗ Incorrect'}\n")

    print(f"✓ Results saved to: {filename}")


@weave.op()
def solve_problem(query: str, prompt_obj: weave.StringPrompt, agent_name: str = "math_solver") -> str:
    """
    Solve problem using W&B Inference or LangChain ReAct agent.

    Uses the solver model from config.yaml. If W&B Inference is configured,
    uses direct prompting. Otherwise, uses LangChain ReAct with dynamic tools.
    """
    # Get solver LLM from config - may be W&B Inference client
    solver_llm = get_llm("solver")

    # Check if using W&B Inference
    from src.llm.wb_inference import WBInference

    if isinstance(solver_llm, WBInference):
        # Use W&B Inference directly with simple prompting
        system_prompt = prompt_obj.content
        full_prompt = f"{system_prompt}\n\nQuestion: {query}\n\nThink step by step and use the calculator tool if needed. Format your answer clearly."

        response = solver_llm.run_inference(
            prompt=full_prompt,
            metadata={"task": "math_solving", "question": query}
        )
        return response
    else:
        # Use LangChain ReAct agent with dynamic tool loading
        tools = load_agent_tools(agent_name, include_generated=True)

        response = run_react_agent(
            question=query,
            tools=tools,
            system_message=prompt_obj.content,
            temperature=0
        )
        return response


def run_sea_training(
    total_problems: int = 50,
    use_llm_eval: bool = True,
    enable_atc: bool = True,
    experiment_id: str = None,
    agent_name: str = "math_solver",
    dataset_name: str = "gsm8k",
    initial_prompt_file: str = "prompt_templates/agents/math_solver/advanced.txt",
    prompt_name: str = "math_solver_prompt"
) -> Dict[str, Any]:
    """
    Run SEA training with unified orchestration and wandb tracking.

    Args:
        total_problems: Total number of problems to solve
        use_llm_eval: Use LLM-based evaluation (vs simple extraction) - Default: True
        enable_atc: Enable Automatic Tool Creation during training - Default: True
        experiment_id: Unique experiment identifier (used in run names and file prefixes)
        agent_name: Agent name for tool saving (from config.yaml)
        dataset_name: Dataset to use - "gsm8k" or "math500" - Default: "gsm8k"
        initial_prompt_file: Path to initial solver prompt file
        prompt_name: Name to use when publishing prompts to Weave (e.g., "math_solver_prompt")

    Returns:
        Dictionary with training results and metrics
    """
    print("="*70)
    print("SEA TRAINING - Unified Self-Improving Agent")
    print("="*70)

    # Load configuration
    config = get_config()
    si_config = config.get("self_improvement", {})

    # Get update frequency from config
    update_frequency = si_config.get("trigger_every_n_runs", 10)

    print(f"\nConfiguration:")
    print(f"  Solver: {config['llm_config']['solver']['provider']} - {config['llm_config']['solver']['model_name']}")
    print(f"  Critic: {config['llm_config']['critic']['provider']} - {config['llm_config']['critic']['model_name']}")
    print(f"  Updater: {config['llm_config']['updater']['provider']} - {config['llm_config']['updater']['model_name']}")
    print(f"  Tool Generator: {config['llm_config']['tool_generator']['provider']} - {config['llm_config']['tool_generator']['model_name']}")
    print(f"  Update Frequency: Every {update_frequency} problems")
    print(f"  LLM Evaluation: {'Enabled' if use_llm_eval else 'Disabled'}")
    print(f"  Critic-Tuner: {'Enabled' if si_config.get('critic_tuner', {}).get('enabled', True) else 'Disabled'}")
    print(f"  ATC: {'Enabled' if si_config.get('automatic_tool_creation', {}).get('enabled', True) else 'Disabled'}")
    if experiment_id:
        print(f"  Experiment ID: {experiment_id}")

    # Initialize Weave
    weave_project = os.getenv("WEAVE_PROJECT_NAME")
    if not weave_project:
        raise ValueError("WEAVE_PROJECT_NAME must be set in .env file")
    weave.init(weave_project)
    print(f"\n✓ Weave initialized: {weave_project}")

    # Load dataset
    if dataset_name.lower() == "math500":
        ds = load_dataset("HuggingFaceH4/MATH-500")
        dataset = ds['test'][13:total_problems]
    else:
        ds = load_dataset("openai/gsm8k", "main")
        dataset = ds['train'][:total_problems]

    # Initialize tracking
    all_responses = []
    prompt_versions = []
    accuracy_history = []

    # Load initial prompt
    with open(initial_prompt_file, "r") as f:
        initial_prompt_text = f.read()

    # Determine final prompt name (with experiment ID if provided)
    final_prompt_name = f"{prompt_name}_{experiment_id}" if experiment_id else prompt_name

    # Create and publish Weave StringPrompt object (v0)
    current_prompt_obj = weave.StringPrompt(initial_prompt_text)
    weave.publish(current_prompt_obj, name=final_prompt_name)
    current_prompt = initial_prompt_text  # Keep text version for tracking
    prompt_version = 0

    print(f"✓ Loaded initial prompt from: {initial_prompt_file}")
    print(f"✓ Initial prompt published to Weave as '{final_prompt_name}:v{prompt_version}'")
    dataset_display = "MATH-500" if dataset_name.lower() == "math500" else "GSM8K"
    print(f"✓ Loaded {total_problems} {dataset_display} problems\n")

    # Initialize SEA components (Phase 4 advanced versions)
    critic = Critic(use_config=True)
    updater = Updater(use_config=True)

    # Initialize orchestrator if ATC enabled
    orchestrator = None
    if enable_atc:
        orchestrator = create_unified_orchestrator(
            weave_project=weave_project,
            config_path="config.yaml"
        )
        print("✓ ATC Orchestrator initialized\n")

    # Training loop
    correct_count = 0
    total_processed = 0
    tools_created = 0

    print(f"Starting training on {total_problems} problems...")
    print(f"Prompt will be updated every {update_frequency} problems\n")

    # Handle different dataset formats
    if dataset_name.lower() == "math500":
        questions = dataset['problem']
        answers = dataset['answer']
    else:
        questions = dataset['question']
        answers = dataset['answer']

    for i, (query, answer) in enumerate(zip(questions, answers)):
        print(f"\n{'='*70}")
        print(f"Problem {i+1}/{total_problems} | Prompt v{len(prompt_versions)}")
        print(f"{'='*70}")

        # Solve problem with current prompt
        current_prompt_obj = weave.StringPrompt(current_prompt)
        response = solve_problem(query, current_prompt_obj, agent_name)

        # Evaluate
        if use_llm_eval:
            eval_result = evaluate_with_llm(query, answer, response)
            is_correct = eval_result.get("correct", False)
        else:
            predicted = extract_answer(response)
            expected = extract_answer(answer)
            is_correct = (predicted == expected) if predicted and expected else False

        if is_correct:
            correct_count += 1
            print("✓ CORRECT")
        else:
            print("✗ INCORRECT")
            print(f"  Expected: {answer}")
            print(f"  Got: {response[:200]}...")

        # Store results
        all_responses.append({
            "problem_id": i + 1,
            "question": query,
            "expected_answer": answer,
            "predicted_answer": response,
            "is_correct": is_correct,
            "prompt_version": len(prompt_versions)
        })

        total_processed += 1
        current_accuracy = correct_count / total_processed
        accuracy_history.append(current_accuracy)
        print(f"  Accuracy: {current_accuracy:.3f} ({correct_count}/{total_processed})")

        # Self-improvement trigger
        if (i + 1) % update_frequency == 0 and i > 0:
            print(f"\n{'🔄 '*35}")
            print("SELF-IMPROVEMENT CYCLE TRIGGERED")
            print(f"{'🔄 '*35}\n")

            # Check if improvement needed
            recent_problems = all_responses[-update_frequency:]
            recent_incorrect = [p for p in recent_problems if not p["is_correct"]]

            if recent_incorrect:
                print(f"Found {len(recent_incorrect)} incorrect in last {update_frequency} problems")

                if enable_atc and orchestrator:
                    # Use full unified orchestration (Critic-Tuner + ATC)
                    print("\n→ Running Unified Orchestration (Critic-Tuner + ATC)...")

                    cycle_problems = [
                        {"question": p["question"], "answer": p["expected_answer"]}
                        for p in recent_problems
                    ]

                    # Create Weave prompt object
                    current_prompt_obj = weave.StringPrompt(current_prompt)

                    results = orchestrator.run_self_improvement_cycle(
                        problems=cycle_problems,
                        solver_func=lambda question, prompt_obj: solve_problem(question, prompt_obj, agent_name),
                        current_prompt_obj=current_prompt_obj,
                        num_recent_traces=10,
                        save_tools_to_agent=agent_name
                    )

                    new_prompt = results["final_prompt"]
                    tools_created += len(results.get("tools_saved", []))

                    if results.get("tools_saved"):
                        print(f"  ✓ Created tools: {', '.join(results['tools_saved'])}")

                else:
                    # Use Critic-Tuner framework (like run_sea_evolution.py)
                    print("\n→ Running Critic-Tuner cycle...")

                    # Create Weave prompt object
                    current_prompt_obj = weave.StringPrompt(current_prompt)

                    # Prepare problems in orchestrator format
                    cycle_problems = [
                        {"question": p["question"], "answer": p["expected_answer"]}
                        for p in recent_problems
                    ]

                    # Initialize Critic-Tuner orchestrator
                    ct_orchestrator = CriticTunerOrchestrator(
                        critic=critic,
                        updater=updater,
                        threshold=0.85
                    )

                    # Run cycle using proper framework
                    stats = ct_orchestrator.run_cycle(
                        problems=cycle_problems,
                        solver_func=lambda question, prompt_obj: solve_problem(question, prompt_obj, agent_name),
                        current_prompt_obj=current_prompt_obj
                    )

                    # Get new prompt
                    new_prompt = stats["new_prompt"]
                    if stats["updated"]:
                        print(f"  ✓ Prompt updated (score: {stats['avg_score']:.3f})")
                        print(f"  Changes: {stats['changes_summary']}")
                    else:
                        print(f"  → Prompt unchanged (score: {stats['avg_score']:.3f} >= threshold)")

                # Update prompt if changed
                if new_prompt != current_prompt:
                    # Save old version
                    prompt_versions.append({
                        "version": len(prompt_versions),
                        "prompt": current_prompt,
                        "accuracy": current_accuracy,
                        "problems_processed": total_processed
                    })

                    # Update to new prompt
                    prompt_version += 1
                    current_prompt = new_prompt

                    # Publish new version to Weave
                    current_prompt_obj = weave.StringPrompt(new_prompt)
                    weave.publish(current_prompt_obj, name=final_prompt_name)
                    print(f"\n  ✓ Prompt updated to v{prompt_version}")
                    print(f"  ✓ Published to Weave as '{final_prompt_name}:v{prompt_version}'")

                    # Save to file backup
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    exp_prefix = f"{experiment_id}_" if experiment_id else ""
                    filename = f"prompt_templates/{exp_prefix}evolved_v{prompt_version}_{timestamp}.txt"
                    os.makedirs("prompt_templates", exist_ok=True)
                    with open(filename, 'w') as f:
                        f.write(current_prompt)
                    print(f"  ✓ Backup saved to: {filename}\n")
                else:
                    print("  → Prompt unchanged\n")
            else:
                print("✓ All recent problems correct, keeping current prompt\n")

    # Final results
    final_accuracy = correct_count / total_problems

    # Save final prompt
    prompt_versions.append({
        "version": len(prompt_versions),
        "prompt": current_prompt,
        "accuracy": final_accuracy,
        "problems_processed": total_processed
    })

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_prefix = f"{experiment_id}_" if experiment_id else ""
    final_filename = f"prompt_templates/{exp_prefix}final_{timestamp}.txt"
    with open(final_filename, 'w') as f:
        f.write(current_prompt)

    results = {
        "total_problems": total_problems,
        "correct": correct_count,
        "incorrect": total_problems - correct_count,
        "final_accuracy": final_accuracy,
        "accuracy_history": accuracy_history,
        "responses": all_responses,
        "prompt_versions": prompt_versions,
        "final_prompt": current_prompt,
        "tools_created": tools_created
    }

    # Log to wandb
    run_name = f"{exp_prefix}SEA_Training_{timestamp}"
    log_to_wandb._prompt_versions = prompt_versions  # Pass prompt versions
    log_to_wandb(
        "SEA_Agent_Phase4",
        total_problems,
        correct_count,
        final_accuracy,
        all_responses,
        run_name,
        "SEA_Agent",
        dataset_display
    )

    # Save results to file
    save_eval_results(
        "SEA_Agent_Phase4",
        total_problems,
        correct_count,
        total_problems - correct_count,
        final_accuracy,
        all_responses,
        run_name
    )

    # Print summary
    print(f"\n{'='*70}")
    print("TRAINING COMPLETE")
    print(f"{'='*70}")
    print(f"Total Problems: {total_problems}")
    print(f"Correct: {correct_count}")
    print(f"Final Accuracy: {final_accuracy:.4f} ({final_accuracy*100:.2f}%)")
    print(f"Final Prompt Version: v{prompt_version}")
    print(f"Total Prompt Updates: {prompt_version}")
    if enable_atc:
        print(f"Tools Created: {tools_created}")
    print(f"\n✓ Final prompt published to Weave: '{final_prompt_name}:v{prompt_version}'")
    print(f"✓ Final prompt backup: {final_filename}")
    print(f"✓ Results logged to wandb: {run_name}")
    print(f"✓ Check Weave UI: {weave_project}")
    print(f"{'='*70}\n")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run SEA training with unified architecture")
    parser.add_argument("--problems", type=int, default=50, help="Total problems to solve")
    parser.add_argument("--llm-eval", action="store_true", help="Use LLM-based evaluation")
    parser.add_argument("--enable-atc", action="store_true", help="Enable Automatic Tool Creation")
    parser.add_argument("--experiment-id", type=str, default=None,
                       help="Experiment ID (prefixes all saved files and run names)")
    parser.add_argument("--agent", type=str, default="math_solver",
                       help="Agent name from config.yaml")
    parser.add_argument("--dataset", type=str, default="gsm8k",
                       choices=["gsm8k", "math500"],
                       help="Dataset to use: gsm8k or math500")
    parser.add_argument("--prompt", type=str, default="prompt_templates/agents/math_solver/advanced.txt",
                       help="Initial prompt file path")
    parser.add_argument("--prompt-name", type=str, default="math_solver_prompt",
                       help="Name for tracking prompts in Weave (e.g., 'math_solver_prompt')")

    args = parser.parse_args()

    run_sea_training(
        total_problems=args.problems,
        use_llm_eval=args.llm_eval,
        enable_atc=args.enable_atc,
        experiment_id=args.experiment_id,
        agent_name=args.agent,
        dataset_name=args.dataset,
        initial_prompt_file=args.prompt,
        prompt_name=args.prompt_name
    )
