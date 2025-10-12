# GSM8K Dataset for Evaluation

## Active Dataset

**File**: `train.csv`
**Source**: GSM8K (Grade School Math 8K) - OpenAI
**Format**: CSV with columns: `question`, `answer`
**Size**: 7,470 math word problems
**URL**: https://github.com/openai/grade-school-math

### Sample Questions

```csv
question,answer
"Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. How many clips did Natalia sell altogether in April and May?",72
"Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes of babysitting. How much did she earn?",10
"Betty is saving money for a new wallet which costs $100. Betty has only half of the money she needs. Her parents decided to give her $15 for that purpose, and her grandparents twice as much as her parents. How much more money does Betty need to buy the wallet?",5
```

### Answer Format

The `answer` column contains the numerical answer extracted from the GSM8K format:
- Original format: `"#### 72"` (GSM8K standard)
- CSV format: `72` (extracted numerical value)

---

## Archived Datasets

### Simple Arithmetic Dataset (Commented Out)

**File**: `train_simple_arithmetic.csv.bak`
**Size**: 65 problems
**Types**: Basic multiplication, addition, subtraction

This was the original test dataset containing simple arithmetic operations like:
- `What is 1803 * 795?` → `1433385`
- `What is 72763122614 + 18475961309?` → `91239083923`

**To restore**:
```bash
mv data/train_simple_arithmetic.csv.bak data/train.csv
```

---

## Dataset Processing

The GSM8K dataset is converted from JSONL to CSV using:
```bash
python convert_gsm8k_to_csv.py
```

**Source files**:
- `gsm8k_train.jsonl` - Original GSM8K JSONL format (7,473 problems)
- `convert_gsm8k_to_csv.py` - Conversion script

### Conversion Details

- Extracts question text
- Extracts numerical answer after `####` marker
- Removes comma formatting from large numbers
- Skips problems where answer extraction fails (~3 problems)

---

## Usage with Evaluation Script

The `gsm8k_eval_with_calculator.py` script reads from `data/train.csv`:

```python
dataset = pd.read_csv("data/train.csv")
for idx, (query, answer) in enumerate(zip(dataset['question'], dataset['answer']), 1):
    # Process each question
    ...
```

### Testing Mode

Currently set to process only **2 samples** for testing:
```python
# TESTING: Only run 2 samples
if idx >= 2:
    break
```

To run full evaluation, remove or comment out the break statement at line 91.

---

## Dataset Statistics

| Dataset | Problems | Type | Status |
|---------|----------|------|--------|
| GSM8K (train.csv) | 7,470 | Word problems | ✅ Active |
| Simple Arithmetic (.bak) | 65 | Basic operations | 📦 Archived |

---

## Notes

- GSM8K problems require multi-step reasoning with calculator tool
- Answers are numerical (integers or decimals)
- Some problems may have negative answers
- Calculator tool must be used for all arithmetic operations
