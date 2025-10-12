# GSM8K Dataset Setup Summary

**Date**: 2025-10-11
**Status**: ✅ Dataset Installed | ⚠️ Agent Needs Tuning for Complex Problems

---

## Actions Completed

### 1. Dataset Migration ✅

**Backed up simple arithmetic dataset**:
```bash
data/train.csv → data/train_simple_arithmetic.csv.bak (65 problems)
```

**Downloaded GSM8K dataset**:
```bash
Source: https://github.com/openai/grade-school-math
Format: JSONL (7,473 problems)
Location: data/gsm8k_train.jsonl
```

**Converted to CSV format**:
```bash
Created: data/train.csv (7,470 problems)
Script: convert_gsm8k_to_csv.py
```

### 2. Code Changes ✅

**File**: `src/llm/inference.py` (Lines 170-180)

**Change**: Increased recursion limit for complex multi-step problems

```python
# Create ReAct agent with increased recursion limit for complex problems
agent = create_react_agent(llm, tools)

# Invoke agent with optional metadata tracing and recursion limit
invoke_config = {"recursion_limit": 50}  # Increased from default 25

if metadata:
    with weave.attributes(metadata):
        result = agent.invoke({"messages": messages}, config=invoke_config)
else:
    result = agent.invoke({"messages": messages}, config=invoke_config)
```

**Reason**: GSM8K problems require multiple calculation steps, causing recursion limit errors

---

## Dataset Comparison

| Feature | Simple Arithmetic (.bak) | GSM8K (train.csv) |
|---------|-------------------------|-------------------|
| **Size** | 65 problems | 7,470 problems |
| **Type** | Single-step arithmetic | Multi-step word problems |
| **Complexity** | `What is 1803 * 795?` | `Natalia sold clips to 48 friends in April, then half as many in May. How many total?` |
| **Steps Required** | 1 calculation | 2-4+ calculations |
| **Reasoning** | None required | Required |

### GSM8K Sample Problems

```
Problem 1: Natalia sold clips to 48 of her friends in April, and then she
sold half as many clips in May. How many clips did Natalia sell altogether
in April and May?
Answer: 72
Steps: 48/2 = 24, then 48+24 = 72

Problem 2: Weng earns $12 an hour for babysitting. Yesterday, she just did
50 minutes of babysitting. How much did she earn?
Answer: 10
Steps: 12/60 = 0.2, then 0.2*50 = 10
```

---

## Test Results (2 Samples)

**Run**: 2025-10-11 20:04:45
**Configuration**:
- Model: gemini-2.5-flash
- Recursion Limit: 50
- Temperature: 0

### Results

| Sample | Question | Expected | Result | Status |
|--------|----------|----------|--------|--------|
| 1 | Natalia clips problem (2 steps) | 72 | "Sorry, need more steps" | ❌ FAILED |
| 2 | Weng babysitting problem (2 steps) | 10 | 10 | ✅ CORRECT |

**Accuracy**: 50% (1/2 correct)

### Analysis

**Problem 1 Failure** ❌:
- **Issue**: Agent hit recursion limit even at 50
- **Behavior**: Returned "Sorry, need more steps to process this request"
- **Root Cause**: Agent is looping without properly concluding the answer
- **Required Steps**: 48/2, then 48+24
- **Tools Used**: Calculator tool was available but agent couldn't complete

**Problem 2 Success** ✅:
- **Behavior**: Correctly reasoned and used calculator
- **Response**: "She earns $0.2 per minute... Weng earned $10. #### 10"
- **Required Steps**: 12/60, then 0.2*50
- **Tools Used**: Calculator tool invoked correctly twice

---

## Key Findings

### What Works ✅
1. **Dataset conversion**: JSONL → CSV conversion successful (7,470 problems)
2. **Simple multi-step problems**: Problems with 2 clean calculation steps work
3. **Tool calling**: Calculator tool invokes successfully when agent doesn't loop
4. **Answer extraction**: Extracts numerical answers correctly from "#### {number}" format

### Issues Identified ⚠️

1. **Recursion Limit Insufficient**
   - Even at 50, some problems cause loops
   - Agent doesn't know when to stop reasoning
   - May need prompt engineering to enforce stopping condition

2. **Agent Looping Behavior**
   - Agent continues reasoning without finishing
   - Not properly recognizing when problem is solved
   - Needs explicit stopping criteria in prompt

3. **Prompt May Need Adjustment**
   - Current prompt emphasizes tool usage but not conclusion
   - Should add: "After final calculation, IMMEDIATELY format answer as #### {number} and STOP"

---

## Recommendations

### Immediate Fixes (Priority 1)

1. **Update Prompt Template** (`prompt_templates/math_tools.txt`)
   - Add explicit stopping instruction after final calculation
   - Example: "After computing the final answer, IMMEDIATELY write #### {number} and STOP. Do not continue reasoning."

2. **Increase Recursion Limit Further**
   - Try 75 or 100 for very complex problems
   - Add as parameter to evaluation script

3. **Test with More Samples**
   - Run on 10 samples to identify patterns
   - Categorize which problem types fail

### Medium-Term Improvements (Priority 2)

1. **Add Max Steps Check**
   - Count tool invocations
   - Force answer after N tool calls (e.g., 5)

2. **Improve Error Handling**
   - Catch "Sorry, need more steps" response
   - Retry with increased limit or simplified prompt

3. **Add Agent State Monitoring**
   - Track how many times agent loops
   - Detect infinite loops earlier

### Future Enhancements (Priority 3)

1. **Chain-of-Thought Optimization**
   - Fine-tune prompt for GSM8K specifically
   - Add few-shot examples of complete solutions

2. **Streaming Support**
   - Watch agent reasoning in real-time
   - Detect and intervene on loops

3. **Adaptive Recursion Limits**
   - Start with 50
   - Auto-increase if "need more steps" error occurs

---

## Files Created/Modified

### New Files ✅
1. `data/gsm8k_train.jsonl` - Original GSM8K dataset
2. `data/train.csv` - Converted CSV (active dataset)
3. `data/README.md` - Dataset documentation
4. `convert_gsm8k_to_csv.py` - Conversion utility
5. `GSM8K_DATASET_SETUP.md` (this file)

### Modified Files ✅
1. `src/llm/inference.py` - Added recursion_limit=50
2. `data/train_simple_arithmetic.csv.bak` - Backed up original

### Backup Files 📦
1. `data/train_simple_arithmetic.csv.bak` - Original 65 arithmetic problems

---

## Next Steps

### To Test Current Setup
```bash
# Run with 2 samples (current setting)
python gsm8k_eval_with_calculator.py

# Results saved to: eval_results/run_TIMESTAMP_gemini-2.5-flash.txt
# Weave traces: https://wandb.ai/vishnu-narasimha/sea-project/weave
```

### To Restore Simple Arithmetic Dataset
```bash
mv data/train_simple_arithmetic.csv.bak data/train.csv
```

### To Run Full GSM8K Evaluation
1. Remove line 91 in `gsm8k_eval_with_calculator.py` (the `if idx >= 2: break`)
2. Increase recursion limit to 75-100
3. Update prompt template with explicit stop instruction
4. Run: `python gsm8k_eval_with_calculator.py`

---

## Summary

✅ **Completed**:
- GSM8K dataset installed (7,470 problems)
- Simple arithmetic dataset backed up
- Recursion limit increased to 50
- Successfully ran 2-sample test

⚠️ **Issues**:
- 50% accuracy (1/2 correct)
- Agent loops on complex multi-step problems
- "Sorry, need more steps" error on Problem 1

🔧 **Next Priority**:
- Update prompt template with explicit stop instruction
- Test with recursion_limit=75
- Run 10-sample evaluation to identify patterns

The dataset is ready, but the agent prompt needs tuning for reliable GSM8K performance.
