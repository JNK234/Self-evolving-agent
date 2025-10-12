import re, os
import weave
from datasets import load_dataset
from src.llm.wb_inference import basic_wb_llm
from src.utils.save_evals import extract_answer, save_eval_results

def eval_gsm8k(llm : str, run_name = None):
    """
    Evaluate GSM8K on the given dataset and save the result.
    """
    responses = []
    total = 50
    correct = 0
    incorrect = 0    
    
    ds = load_dataset("openai/gsm8k", "main")
    dataset = ds['test'][:total]

    for query, answer in zip(dataset['question'], dataset['answer']):
        prediction = basic_wb_llm(query)  # W&B Inference

        responses.append({"question": query, "answer": answer, "llm_response": prediction})

        if extract_answer(prediction) == extract_answer(answer):
            correct += 1
        else:
            incorrect += 1
        # break # remove the break when want to run on full dataset (: total).
    accuracy = correct / total
    # print(f"Accuracy: {accuracy:.2f}")
    save_eval_results(llm, total, correct, incorrect, accuracy, responses, run_name)
    return responses


def main():
    # llm = os.getenv("WB_INFERENCE_MODEL")
    llm = "Google gemini LLM"
    # run_name = "GSM_8K_LLM"

    responses = eval_gsm8k(llm)
    print(f"Evaluation completed. {len(responses)} responses generated.")

if __name__ == "__main__":
    main()