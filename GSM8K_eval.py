import re, os
import weave
from datasets import load_dataset
from agent.google_agent import google_agent
from agent.phi_agent import phi_agent
from llm.google_llm import basic_google_llm
from llm.phi_llm import phi_llm
from utils.evals_utils import extract_answer, save_eval_results
from utils.evals_utils import evaluate_with_llm, log_to_wandb


# Initialize Weave for automatic tracing
WEAVE_PROJECT = os.getenv("WEAVE_PROJECT_NAME", "self-evolving-agent")
weave.init(WEAVE_PROJECT)

def eval_gsm8k(llm : str, run_name = None, use_llm_eval = True, model_type = "LLM", total = 50):
    """
    Evaluate GSM8K on the given dataset and save the result.
    """
    responses = []
    correct = 0
    incorrect = 0    
    
    ds = load_dataset("openai/gsm8k", "main")
    dataset = ds['test'][100: 100 + total]

    for i, (query, answer) in enumerate(zip(dataset['question'], dataset['answer'])):
        print(f"Processing example {i+1}/{total}...")
        # prediction = basic_google_llm(query)  # Gemini LLM
        prediction = phi_llm(query)
        # prediction = google_agent(query)
        # prediction = phi_agent(query)
        # prediction = sea_agent(query)
        
        # prediction = basic_wb_llm(query)  # W&B Inference OpenPipe/Qwen-3 14B
        responses.append({"question": query, "answer": answer, "llm_response": prediction})

        if use_llm_eval:
            # Use LLM evaluation
            eval_result = evaluate_with_llm(query, answer, prediction)
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
    run_name = "GSM8K_Phi_LLM"
    
    responses = eval_gsm8k(llm, run_name, model_type="LLM", total=30)
    print(f"Evaluation completed. {len(responses)} responses generated.")

# Example functions for different model types
def run_phi_agent():
    """Run evaluation for Phi Agent"""
    llm = "Phi_4mini_3.8B_Agent"
    run_name = "GSM8K_Phi_Agent"
    return eval_gsm8k(llm, run_name, model_type="Agent", total=30)

def run_google_llm():
    """Run evaluation for Google LLM"""
    llm = "Google_Gemini_LLM"
    run_name = "GSM8K_Google_LLM"
    return eval_gsm8k(llm, run_name, model_type="LLM", total=50)

def run_google_agent():
    """Run evaluation for Google Agent"""
    llm = "Google_Gemini_Agent"
    run_name = "GSM8K_Google_Agent"
    return eval_gsm8k(llm, run_name, model_type="Agent", total=50)

if __name__ == "__main__":
    main()