import re
from datasets import load_dataset
from src.llm.inference import run_inference, basic_google_llm
from src.utils.save_evals import extract_answer, save_eval_results

def eval_gsm8k(llm : str, run_name = None):
    """
    Evaluate GSM8K on the given dataset and save the result.
    """
    responses = []
    total = 100
    correct = 0
    incorrect = 0    
    
    ds = load_dataset("openai/gsm8k", "main")
    dataset = ds['test'][:total]

    for query, answer in zip(dataset['question'], dataset['answer']):
        if llm == "basic google llm":
            prediction = basic_google_llm(query)
            responses.append({"question": query, "answer": answer, "llm_response": prediction})

            if extract_answer(prediction) == extract_answer(answer):
                correct += 1
            else:
                incorrect += 1
        break # remove the break when want to run on full dataset (: total).
    accuracy = correct / total
    # print(f"Accuracy: {accuracy:.2f}")
    save_eval_results(llm, total, correct, incorrect, accuracy, responses, run_name)
    return responses


def main():
    llm = "basic google llm"
    run_name = "gsm8k_basic_test"
    
    responses = eval_gsm8k(llm, run_name)
    print(f"Evaluation completed. {len(responses)} responses generated.")

if __name__ == "__main__":
    main()