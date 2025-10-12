import os
import weave
from datasets import load_dataset
from typing import Dict, Any, List, Tuple
from sea.solver import solver
from sea.critic import critic
from sea.updater import updater
from utils.evals_utils import extract_boolean, extract_answer, log_to_wandb, save_eval_results, evaluate_with_llm
from datetime import datetime

# Initialize Weave for automatic tracing
WEAVE_PROJECT = os.getenv("WEAVE_PROJECT_NAME", "self-evolving-agent")
weave.init(WEAVE_PROJECT)

@weave.op()
def solve_problem(query: str, current_prompt: str) -> Tuple[str, str]:
    """Solve a problem using the current prompt"""
    response, _ = solver(query, current_prompt)
    return response, current_prompt

@weave.op()
def critic_response_batch(problems_data: List[Dict]) -> str:
    """Evaluate a batch of responses using the critic"""
    critic_feedback = critic(problems_data)
    return critic_feedback

@weave.op()
def update_prompt(query: str, response: str, critic_feedback: str, current_prompt: str) -> str:
    """Update the prompt based on critic feedback"""
    updater_response = updater(query, response, critic_feedback, current_prompt)
    return updater_response

def run_sea_agent(total_problems: int = 100, update_frequency: int = 5) -> Dict[str, Any]:
    """
    Run the Self-Evolving Agent system with iterative prompt improvement
    
    Args:
        total_problems: Total number of problems to solve
        update_frequency: How often to update the prompt (every n problems)
    
    Returns:
        Dictionary with evaluation results
    """
    # Load MATH-500 dataset
    ds = load_dataset("HuggingFaceH4/MATH-500")
    dataset = ds['test'][:total_problems]
    
    # Initialize tracking variables
    current_prompt = None
    all_responses = []
    prompt_versions = []
    accuracy_history = []
    
    # Load initial prompt
    with open("prompt_templates/sea_solver_p.txt", "r") as f:
        current_prompt = f.read()
    
    correct_count = 0
    total_processed = 0
    
    print(f"Starting SEA Agent evaluation on {total_problems} problems...")
    print(f"Prompt will be updated every {update_frequency} problems")
    
    for i, (problem, solution, answer) in enumerate(zip(dataset['problem'], dataset['solution'], dataset['answer'])):
        print(f"\n--- Problem {i+1}/{total_problems} ---")
        print(f"Current prompt version: {len(prompt_versions) + 1}")
        
        # Solve the problem with current prompt
        response, _ = solve_problem(problem, current_prompt)
        
        # Use evaluate_with_llm instead of exact matching
        eval_result = evaluate_with_llm(problem, answer, response)
        is_correct = eval_result.get("correct", False)
        
        if is_correct:
            correct_count += 1
            print("✓ CORRECT")
        else:
            print("✗ INCORRECT")
            print(f"Expected: {answer[:100]}...")
            print(f"Got: {response[:100]}...")
        
        # Store results
        all_responses.append({
            "problem_id": i + 1,
            "question": problem,
            "expected_answer": answer,
            "predicted_answer": response,
            "response": response,
            "is_correct": is_correct,
            "prompt_version": len(prompt_versions) + 1
        })
        
        total_processed += 1
        
        # Update prompt every n problems
        if (i + 1) % update_frequency == 0 and i > 0:
            print(f"\n🔄 Running critic on {update_frequency} problems...")
            
            # Get the recent problems for critic evaluation
            recent_problems = all_responses[-update_frequency:]
            
            # Run critic on the batch of recent problems
            critic_feedback = critic_response_batch(recent_problems)
            print(f"Critic feedback: {critic_feedback[:200]}...")
            
            # Check if we need to update (if there were incorrect responses)
            recent_incorrect = any(not resp["is_correct"] for resp in recent_problems)
            
            if recent_incorrect:
                print(f"\n🔄 Updating prompt after {update_frequency} problems...")
                
                # Use the first incorrect problem for prompt update
                incorrect_problems = [p for p in recent_problems if not p["is_correct"]]
                
                if incorrect_problems:
                    update_problem = incorrect_problems[0]
                    new_prompt = update_prompt(
                        update_problem["question"],
                        update_problem["response"],
                        critic_feedback,
                        current_prompt
                    )
                    print(f"NEW PROMPT: {new_prompt[:200]}...")
                    
                    # Store old prompt version
                    prompt_versions.append({
                        "version": len(prompt_versions) + 1,
                        "prompt": current_prompt,
                        "problems_used": update_frequency,
                        "accuracy": correct_count / total_processed,
                        "critic_feedback": critic_feedback
                    })
                    
                    # Update current prompt
                    current_prompt = new_prompt
                    print(f"✅ Prompt updated to version {len(prompt_versions) + 1}")
                else:
                    print("No incorrect problems found, keeping current prompt")
            else:
                print("All recent problems correct, keeping current prompt")
        
        # Calculate and log current accuracy
        current_accuracy = correct_count / total_processed
        accuracy_history.append(current_accuracy)
        print(f"Current accuracy: {current_accuracy:.3f} ({correct_count}/{total_processed})")
    
    # Final results
    final_accuracy = correct_count / total_problems
    
    # Store final prompt version
    prompt_versions.append({
        "version": len(prompt_versions) + 1,
        "prompt": current_prompt,
        "problems_used": total_problems,
        "accuracy": final_accuracy
    })
    
    # Save the final evolved prompt to a file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_prompt_filename = f"prompt_templates/sea_solver_evolved_{timestamp}.txt"
    
    with open(final_prompt_filename, "w") as f:
        f.write(current_prompt)
    
    print(f"💾 Final evolved prompt saved to: {final_prompt_filename}")

    results = {
        "total_problems": total_problems,
        "correct": correct_count,
        "incorrect": total_problems - correct_count,
        "final_accuracy": final_accuracy,
        "accuracy_history": accuracy_history,
        "responses": all_responses,
        "prompt_versions": prompt_versions,
        "final_prompt": current_prompt,
        "final_prompt_file": final_prompt_filename
    }
    
    # Log to wandb
    run_name = f"SEA_Agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_to_wandb(
        "SEA_Agent", 
        total_problems, 
        correct_count, 
        final_accuracy, 
        all_responses, 
        run_name, 
        "SEA_Agent"
    )
    
    # Save results
    save_eval_results("SEA_Agent", total_problems, correct_count, 
                     total_problems - correct_count, final_accuracy, all_responses, run_name)
    
    print(f"\n🎯 Final Results:")
    print(f"Total problems: {total_problems}")
    print(f"Correct: {correct_count}")
    print(f"Final accuracy: {final_accuracy:.4f} ({final_accuracy*100:.2f}%)")
    print(f"Prompt updated {len(prompt_versions)-1} times")
    
    return results

@weave.op()
def test_final_solver(test_problems: int = 10, prompt_file: str = None) -> Dict[str, Any]:
    """
    Test the final evolved solver on new problems
    """
    print(f"\n🧪 Testing final solver on {test_problems} new problems...")
    
    # Load the final prompt
    if prompt_file is None:
        import glob
        prompt_files = glob.glob("prompt_templates/sea_solver_evolved_*.txt")
        if not prompt_files:
            print("No evolved prompt files found. Please run run_sea_agent() first.")
            return None
        
        # Get the most recent file
        prompt_file = max(prompt_files, key=os.path.getctime)
        print(f"📁 Using evolved prompt: {prompt_file}")

    # Load the final evolved prompt
    try:
        with open(prompt_file, "r") as f:
            final_prompt = f.read()
    except FileNotFoundError:
        print(f"❌ Prompt file not found: {prompt_file}")
        return None

    # Load test dataset (use different problems from MATH-500)
    ds = load_dataset("HuggingFaceH4/MATH-500")
    dataset = ds['test'][100:100+test_problems]  # Use different problems for testing
    
    correct = 0
    test_responses = []
    
    for i, (problem, solution, answer) in enumerate(zip(dataset['problem'], dataset['solution'], dataset['answer'])):
        print(f"\nTest Problem {i+1}:")
        response, _ = solve_problem(problem, final_prompt)
        
        # Use evaluate_with_llm for evaluation
        eval_result = evaluate_with_llm(problem, answer, response)
        is_correct = eval_result.get("correct", False)
        
        # Store test results
        test_responses.append({
            "problem_id": i + 1,
            "question": problem,
            "expected_answer": answer,
            "predicted_answer": response,
            "response": response,
            "is_correct": is_correct,
            "prompt_file": prompt_file
        })
        
        if is_correct:
            correct += 1
            print("✓ CORRECT")
        else:
            print("✗ INCORRECT")
            expected = extract_answer(answer)
            predicted = extract_answer(response)
            print(f"Expected: {expected}, Got: {predicted}")
    
    test_accuracy = correct / test_problems
    
    # Log test results to wandb
    test_run_name = f"SEA_Agent_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_to_wandb(
        "SEA_Agent_Test", 
        test_problems, 
        correct, 
        test_accuracy, 
        test_responses, 
        test_run_name, 
        "SEA_Agent_Test"
    )
    
    # Save test results
    save_eval_results("SEA_Agent_Test", test_problems, correct, 
                     test_problems - correct, test_accuracy, test_responses, test_run_name)
    
    print(f"\n🎯 Test Results:")
    print(f"Test accuracy: {test_accuracy:.3f} ({correct}/{test_problems})")
    print(f"Used prompt: {prompt_file}")
    print(f"Results logged to Weights & Biases: {test_run_name}")
    
    return {
        "test_problems": test_problems,
        "correct": correct,
        "incorrect": test_problems - correct,
        "test_accuracy": test_accuracy,
        "test_responses": test_responses,
        "prompt_file": prompt_file,
        "run_name": test_run_name
    }

if __name__ == "__main__":
    # Run the SEA agent system
    print("🚀 Starting Self-Evolving Agent training on MATH-500...")
    results = run_sea_agent(total_problems=30, update_frequency=5)
    
    # Test the final solver
    print("\n🧪 Testing the evolved solver...")
    test_results = test_final_solver(test_problems=30)
    
    if test_results:
        print(f"\n📊 Summary:")
        print(f"Training accuracy: {results['final_accuracy']:.3f}")
        print(f"Test accuracy: {test_results['test_accuracy']:.3f}")
        print(f"Improvement: {test_results['test_accuracy'] - results['final_accuracy']:.3f}")