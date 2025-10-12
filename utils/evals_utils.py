import re
import os
import wandb
import weave
from datetime import datetime
from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate


def extract_answer(text):
    match = re.search(r'####\s*([0-9\.]+)', text)
    if match:
        return match.group(1)
    numbers = re.findall(r'[0-9\.]+', text)

    if numbers:
        return numbers[-1]
    return None

def extract_boolean(text):
    match = re.search(r'####\s*(True|False)', text, re.IGNORECASE)
    return match.group(1).capitalize() if match else None

@weave.op()
def evaluate_with_llm(question: str, expected_answer: str, model_response: str) -> Dict[str, Any]:
    """
    LLM-based evaluation of a model response.
    
    Args:
        question: The original question
        expected_answer: The expected answer
        model_response: The model's response
        
    Returns:
        Dictionary with evaluation results
    """
    # Load the evaluation prompt
    with open("prompt_templates/eval_p.txt", 'r') as file:
        eval_prompt = file.read()
    
    # Create prompt template
    prompt_template = PromptTemplate.from_template(eval_prompt)
    
    # Initialize LLM
    llm = ChatOpenAI(
        base_url=os.getenv("WB_INFERENCE_BASE_URL"),
        api_key=os.getenv("WANDB_API_KEY"),
        model=os.getenv("WB_INFERENCE_MODEL"),
    )
    
    # Get evaluation
    chain = prompt_template | llm
    response = chain.invoke({
        "question": question,
        "expected_answer": expected_answer,
        "model_response": model_response
    })
    
    # Parse response
    eval_text = response.content
    result = {"raw_evaluation": eval_text, "correct": None, "reasoning": None}
    
    # Improved parsing logic
    lines = eval_text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('CORRECT:'):
            correct_str = line.split(':', 1)[1].strip()
            result["correct"] = correct_str.lower() == 'true'
        elif line.startswith('REASONING:'):
            result["reasoning"] = line.split(':', 1)[1].strip()
    
    # Fallback: if parsing failed, try to extract boolean from the text
    if result["correct"] is None:
        if 'true' in eval_text.lower():
            result["correct"] = True
        elif 'false' in eval_text.lower():
            result["correct"] = False
        else:
            # Default to False if we can't determine
            result["correct"] = False
            result["reasoning"] = "Could not parse evaluation result"
    
    return result

# Keep your existing functions and replace the log_to_weave function with this:
def log_to_wandb(model_name: str, total: int, correct: int, accuracy: float, 
                 responses: list, run_name: str = None, model_type: str = "LLM"):
    """
    Log evaluation results to Weights & Biases with proper bar chart visualization.
    """
    if run_name is None:
        run_name = f"math500_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize wandb run
    wandb.init(
        project="self-evolving-agent",
        name=run_name,
        config={
            "model_name": model_name,
            "model_type": model_type,
            "dataset": "MATH-500",  # Changed from GSM8K
            "total_examples": total,
            "evaluation_method": "LLM-based" if len(responses) > 0 else "extraction"
        }
    )
    
    # Log metrics
    wandb.log({
        "accuracy": accuracy,
        "correct": correct,
        "incorrect": total - correct,
        "total": total
    })
    
    # Create a table with sample results for visualization
    if responses:
        # Prepare data for wandb table
        table_data = []
        for i, resp in enumerate(responses[:10]):  # Log first 10 examples
            # Handle different response formats
            if 'expected_answer' in resp and 'predicted_answer' in resp:
                # New format from sea_agent.py
                expected_answer = resp['expected_answer']
                predicted_answer = resp['predicted_answer']
                question = resp['question']
            elif 'answer' in resp and 'llm_response' in resp:
                # Old format from GSM8K_eval.py
                expected_answer = extract_answer(resp['answer'])
                predicted_answer = extract_answer(resp['llm_response'])
                question = resp['question']
            else:
                # Fallback
                expected_answer = "N/A"
                predicted_answer = "N/A"
                question = "N/A"
            
            is_correct = expected_answer == predicted_answer
            
            table_data.append([
                i + 1,
                question[:100] + "..." if len(question) > 100 else question,
                expected_answer,
                predicted_answer,
                "Correct" if is_correct else "Incorrect"
            ])
        
        # Create wandb table
        table = wandb.Table(
            columns=["Example", "Question", "Expected", "Predicted", "Correct"],
            data=table_data
        )
        
        wandb.log({"evaluation_samples": table})
    
    # Finish the run
    wandb.finish()
    print(f"Results logged to Weights & Biases: {run_name}")
    return run_name

def save_eval_results(model_name, total, correct, incorrect, accuracy, responses, run_name=None):
    """
    Save evaluation results to file (keep existing functionality)
    """
    os.makedirs("eval_results", exist_ok=True)
    
    if run_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"run_{timestamp}"
    
    filename = f"eval_results/{run_name}_{model_name.replace('/', '_')}.txt"
    
    with open(filename, 'w') as f:
        f.write(f"MATH-500 Evaluation Results\n")  # Changed from GSM8K
        f.write(f"=" * 50 + "\n\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Run Name: {run_name}\n")
        f.write(f"Total Examples Tested: {total}\n")
        f.write(f"Correct: {correct}\n")
        f.write(f"Incorrect: {incorrect}\n")
        f.write(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)\n\n")
        
        f.write("Example Responses:\n")
        f.write("-" * 30 + "\n\n")
        
        for i, response in enumerate(responses[:2]):
            f.write(f"Example {i+1}:\n")
            f.write(f"Question: {response['question']}\n")
            
            # Handle different response formats
            if 'expected_answer' in response and 'predicted_answer' in response:
                # New format from sea_agent.py
                f.write(f"Expected Answer: {response['expected_answer']}\n")
                f.write(f"Model Response: {response['response']}\n")
                f.write(f"Extracted Answer: {response['predicted_answer']}\n")
                f.write(f"Expected Answer: {response['expected_answer']}\n")
                f.write(f"Correct: {'Yes' if response['is_correct'] else 'No'}\n")
            elif 'answer' in response and 'llm_response' in response:
                # Old format from GSM8K_eval.py
                f.write(f"Expected Answer: {response['answer']}\n")
                f.write(f"Model Response: {response['llm_response']}\n")
                f.write(f"Extracted Answer: {extract_answer(response['llm_response'])}\n")
                f.write(f"Expected Answer: {extract_answer(response['answer'])}\n")
                f.write(f"Correct: {'Yes' if extract_answer(response['llm_response']) == extract_answer(response['answer']) else 'No'}\n")
            
            f.write("\n" + "-" * 30 + "\n\n")
    
    print(f"Results saved to: {filename}")
    return filename