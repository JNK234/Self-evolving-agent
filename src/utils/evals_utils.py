import re
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def extract_answer(text):
    """Extract numerical answer from various formats."""
    # Convert to string if it's a number
    if isinstance(text, (int, float)):
        return str(int(text)) if isinstance(text, float) and text.is_integer() else str(text)

    text = str(text)  # Ensure it's a string
    logger.debug(f"Extracting answer from: {text[:200]}...")

    # GSM8K format: #### 18
    match = re.search(r'####\s*([0-9,]+(?:\.[0-9]+)?)', text)
    if match:
        answer = match.group(1).replace(',', '').rstrip('.')
        logger.debug(f"Extracted from #### format: {answer}")
        return answer

    # LaTeX boxed format: \boxed{3}
    match = re.search(r'\\boxed\{([0-9,]+(?:\.[0-9]+)?)\}', text)
    if match:
        answer = match.group(1).replace(',', '').rstrip('.')
        logger.debug(f"Extracted from boxed format: {answer}")
        return answer

    # Dollar amount: $104 or $104.50
    match = re.search(r'\$([0-9,]+(?:\.[0-9]+)?)', text.split('\n')[-3:][0] if len(text.split('\n')) > 3 else text)
    if match:
        answer = match.group(1).replace(',', '').rstrip('.')
        logger.debug(f"Extracted from $ format: {answer}")
        return answer

    # Look for number after "makes", "earns", "cost", etc. in last few lines
    last_lines = ' '.join(text.split('\n')[-3:])
    patterns = [
        r'(?:makes|earns|gets?|answer is|total of|result is|cost)\s+\$?([0-9,]+(?:\.[0-9]+)?)',
        r'([0-9,]+(?:\.[0-9]+)?)\s+(?:dollars?|eggs?|bolts?)',
        r'=\s+\$?([0-9,]+(?:\.[0-9]+)?)\s*$',
    ]
    for pattern in patterns:
        match = re.search(pattern, last_lines, re.IGNORECASE)
        if match:
            answer = match.group(1).replace(',', '').rstrip('.')
            logger.debug(f"Extracted from pattern '{pattern}': {answer}")
            return answer

    # Last resort: find last number in text (but not a trailing period)
    numbers = re.findall(r'\b([0-9,]+(?:\.[0-9]+)?)\b', text)
    if numbers:
        answer = numbers[-1].replace(',', '').rstrip('.')
        logger.debug(f"Extracted last number: {answer}")
        return answer

    logger.warning(f"Could not extract answer from text: {text[:100]}...")
    return None


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
