# ABOUTME: Converts GSM8K JSONL format to CSV for evaluation
# ABOUTME: Extracts question and numerical answer from GSM8K dataset

import json
import csv
import re

def extract_numerical_answer(answer_text):
    """Extract the numerical answer after #### marker."""
    match = re.search(r'####\s*([0-9,]+(?:\.[0-9]+)?)', answer_text)
    if match:
        return match.group(1).replace(',', '')
    return None

def convert_jsonl_to_csv(input_file, output_file):
    """Convert GSM8K JSONL to CSV format."""
    with open(input_file, 'r') as f_in, open(output_file, 'w', newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(['question', 'answer'])

        for line in f_in:
            data = json.loads(line)
            question = data['question']
            answer = extract_numerical_answer(data['answer'])

            if answer:
                writer.writerow([question, answer])
            else:
                print(f"Warning: Could not extract answer from: {data['answer'][:50]}...")

if __name__ == "__main__":
    convert_jsonl_to_csv('data/gsm8k_train.jsonl', 'data/train.csv')
    print("✓ Converted GSM8K to CSV format: data/train.csv")

    # Show first 3 examples
    print("\nFirst 3 examples:")
    with open('data/train.csv', 'r') as f:
        for i, line in enumerate(f):
            if i < 4:  # Header + 3 examples
                print(line.strip())
