# ABOUTME: GSM8K evaluation using calculator tool with ReAct agent
# ABOUTME: Simple evaluation matching original GSM8K_eval.py structure

from dotenv import load_dotenv
import os
import logging
import pandas as pd
from src.llm.inference import run_react_agent
from src.agents.tools.langchain_calculator import calculator_tool
from src.utils.evals_utils import extract_answer, save_eval_results

load_dotenv()


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def solve_with_calculator(question: str) -> str:
    """Solve GSM8K problem using ReAct agent with calculator tool."""
    logger.info(f"Starting solve_with_calculator for question: {question}...")

    # Call run_react_agent from inference module with math_tools prompt
    response = run_react_agent(
        question=question,
        tools=[calculator_tool],
        prompt_template_file="prompt_templates/math_tools.txt",
        temperature=0
    )

    logger.info(f"Agent completed. Final answer: {response}...")
    return response


def eval_gsm8k_calculator(run_name=None):
    """Evaluate GSM8K with calculator tool."""

    logger.info("Starting GSM8K evaluation with calculator tool")

    responses = []
    correct = 0
    incorrect = 0

    logger.info("Loading train.csv dataset...")
    dataset = pd.read_csv("data/train.csv")
    total = len(dataset)
    logger.info(f"Dataset loaded: {total} problems")

    llm = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    logger.info(f"Model: {llm}")

    for idx, (query, answer) in enumerate(zip(dataset['question'], dataset['answer']), 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Problem {idx}/{total}")
        logger.info(f"Question: {query[:100]}...")

        try:
            prediction = solve_with_calculator(query)
            pred_answer = extract_answer(prediction)
            # CSV answer is already a number, convert to string for comparison
            true_answer = str(int(answer)) if isinstance(answer, (int, float)) else extract_answer(str(answer))

            is_correct = pred_answer == true_answer

            responses.append({
                "question": query,
                "answer": answer,
                "llm_response": prediction,
                "correct": is_correct
            })

            if is_correct:
                correct += 1
                logger.info(f"✓ CORRECT - Expected: {true_answer}, Got: {pred_answer}")
            else:
                incorrect += 1
                logger.info(f"✗ INCORRECT - Expected: {true_answer}, Got: {pred_answer}")

        except Exception as e:
            logger.error(f"ERROR processing problem {idx}: {e}", exc_info=True)
            incorrect += 1
            responses.append({
                "question": query,
                "answer": answer,
                "llm_response": f"Error: {str(e)}",
                "correct": False
            })

        # TESTING: Only run 2 samples
        if idx >= 2:
            break

    # Calculate accuracy based on actual samples processed
    samples_processed = len(responses)
    accuracy = correct / samples_processed if samples_processed > 0 else 0
    logger.info(f"\n{'='*60}")
    logger.info(f"FINAL RESULTS: {correct}/{samples_processed} correct ({accuracy:.1%})")
    logger.info(f"{'='*60}\n")

    save_eval_results(llm, samples_processed, correct, incorrect, accuracy, responses, run_name)

    return responses


def main():
    logger.info("="*60)
    logger.info("GSM8K Evaluation with Calculator Tool")
    logger.info("="*60)

    responses = eval_gsm8k_calculator()

    logger.info(f"\nEvaluation completed. {len(responses)} responses generated.")
    logger.info("Check Weave for detailed traces!")


if __name__ == "__main__":
    main()
