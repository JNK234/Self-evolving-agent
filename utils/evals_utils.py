import re
import os
from datetime import datetime

def extract_answer(text):
    match = re.search(r'####\s*([0-9\.]+)', text)
    return match.group(1) if match else None

def extract_boolean(text):
    match = re.search(r'####\s*(True|False)', text, re.IGNORECASE)
    return match.group(1).capitalize() if match else None

def save_eval_results(model_name, total, correct, incorrect, accuracy, responses, run_name=None):

    os.makedirs("eval_results", exist_ok=True)
    
    # Generate run name if not provided
    if run_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"run_{timestamp}"
    
    # Create filename
    filename = f"eval_results/{run_name}_{model_name.replace('/', '_')}.txt"
    
    # Write results to file
    with open(filename, 'w') as f:
        f.write(f"GSM8K Evaluation Results\n")
        f.write(f"=" * 50 + "\n\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Run Name: {run_name}\n")
        f.write(f"Total Examples Tested: {total}\n")
        f.write(f"Correct: {correct}\n")
        f.write(f"Incorrect: {incorrect}\n")
        f.write(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)\n\n")
        
        f.write("Example Responses:\n")
        f.write("-" * 30 + "\n\n")
        
        # Show first 2 examples
        for i, response in enumerate(responses[:2]):
            f.write(f"Example {i+1}:\n")
            f.write(f"Question: {response['question']}\n")
            f.write(f"Expected Answer: {response['answer']}\n")
            f.write(f"Model Response: {response['llm_response']}\n")
            f.write(f"Extracted Answer: {extract_answer(response['llm_response'])}\n")
            f.write(f"Expected Answer: {extract_answer(response['answer'])}\n")
            f.write(f"Correct: {'Yes' if extract_answer(response['llm_response']) == extract_answer(response['answer']) else 'No'}\n")
            f.write("\n" + "-" * 30 + "\n\n")
    
    print(f"Results saved to: {filename}")
    return filename