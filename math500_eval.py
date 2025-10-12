import re, os
import weave
from datasets import load_dataset
from agent.google_agent import google_agent
from agent.phi_agent import phi_agent
from llm.google_llm import basic_google_llm
from llm.phi_llm import phi_llm
# from src.llm.inference import run_inference, basic_google_llm
# from src.llm.wb_inference import basic_wb_llm
from utils.evals_utils import extract_answer, save_eval_results
from utils.evals_utils import evaluate_with_llm, log_to_wandb


# Initialize Weave for automatic tracing
WEAVE_PROJECT = os.getenv("WEAVE_PROJECT_NAME", "self-evolving-agent")
weave.init(WEAVE_PROJECT)

def eval_math500(llm : str, run_name = None, use_llm_eval = True, model_type = "LLM", total = 50):
    """
    Evaluate MATH-500 on the given dataset and save the result.
    """
    responses = []
    correct = 0
    incorrect = 0    
    
    # Load MATH-500 dataset
    ds = load_dataset("HuggingFaceH4/MATH-500")
    
    # Check what splits are available and use the first one
    split_name = 'test' # list(ds.keys())[0]
    print(f"Using split: {split_name}")
    print(f"Dataset columns: {ds[split_name].column_names}")
    
    # Use different problems for evaluation (starting from index 100)
    dataset = ds[split_name][100: 100 + total]

    for i, (problem, solution, answer) in enumerate(zip(dataset['problem'], dataset['solution'], dataset['answer'])):
        print(f"Processing example {i+1}/{total}...")
        # prediction = basic_google_llm(problem)  # Gemini LLM
        # prediction = phi_llm(problem)
        # prediction = google_agent(problem)
        prediction = phi_agent(problem)
        # prediction = sea_agent(problem)
        
        # prediction = basic_wb_llm(problem)  # W&B Inference OpenPipe/Qwen-3 14B
        responses.append({"question": problem, "answer": answer, "llm_response": prediction})

        if use_llm_eval:
            # Use LLM evaluation
            eval_result = evaluate_with_llm(problem, answer, prediction)
            is_correct = eval_result.get("correct", False)
        else:
            # Use simple extraction
            is_correct = extract_answer(prediction) == extract_answer(answer)
        
        if is_correct:
            correct += 1
        else:
            incorrect += 1
        # break # remove the break when want to run on full dataset (: total).
    accuracy = correct / total
    # print(f"Accuracy: {accuracy:.2f}")
    save_eval_results(llm, total, correct, incorrect, accuracy, responses, run_name)
    log_to_wandb(llm, total, correct, accuracy, responses, run_name, model_type)
    print(f"Evaluation completed for {llm}")
    print(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"Correct: {correct}/{total}")
    return responses


def main():
    # Example: Run Phi LLM
    llm = "Phi_4mini_3.8B_LLM"
    run_name = "MATH500_Phi_LLM"
    
    responses = eval_math500(llm, run_name, model_type="LLM", total=30)
    print(f"Evaluation completed. {len(responses)} responses generated.")

# Example functions for different model types
def run_phi_agent():
    """Run evaluation for Phi Agent"""
    llm = "Phi_4mini_3.8B_Agent"
    run_name = "MATH500_Phi_Agent"
    return eval_math500(llm, run_name, model_type="Agent", total=30)

def run_google_llm():
    """Run evaluation for Google LLM"""
    llm = "Google_Gemini_LLM"
    run_name = "MATH500_Google_LLM"
    return eval_math500(llm, run_name, model_type="LLM", total=50)

def run_google_agent():
    """Run evaluation for Google Agent"""
    llm = "Google_Gemini_Agent"
    run_name = "MATH500_Google_Agent"
    return eval_math500(llm, run_name, model_type="Agent", total=50)

def run_sea_agent_math500():
    """Run evaluation for SEA Agent on MATH-500"""
    from sea_agent import test_final_solver
    
    llm = "SEA_Agent_MATH500"
    run_name = "MATH500_SEA_Agent"
    
    # Test the evolved solver on MATH-500
    test_results = test_final_solver(test_problems=30)
    
    if test_results:
        print(f"SEA Agent Test Results:")
        print(f"Test accuracy: {test_results['test_accuracy']:.4f} ({test_results['test_accuracy']*100:.2f}%)")
        print(f"Correct: {test_results['correct']}/{test_results['test_problems']}")
        
        # Convert to the expected format for logging
        responses = []
        for resp in test_results['test_responses']:
            responses.append({
                "question": resp['question'],
                "answer": resp['expected_answer'],
                "llm_response": resp['response']
            })
        
        save_eval_results(llm, test_results['test_problems'], test_results['correct'], 
                         test_results['incorrect'], test_results['test_accuracy'], responses, run_name)
        log_to_wandb(llm, test_results['test_problems'], test_results['correct'], 
                    test_results['test_accuracy'], responses, run_name, "SEA_Agent")
        
        return responses
    else:
        print("No test results available. Please run run_sea_agent() first.")
        return []

if __name__ == "__main__":
    run_phi_agent()