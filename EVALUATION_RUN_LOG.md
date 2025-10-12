# GSM8K Calculator Tool Evaluation - Run Log

**Date**: 2025-10-11
**Objective**: Iteratively run and fix GSM8K evaluation with calculator tool calling on 2 samples
**Status**: ✅ SUCCESSFUL - End-to-end execution with verified tool usage

---

## Executive Summary

Successfully debugged and ran GSM8K evaluation with ReAct agent and calculator tool on 2 samples:
- **Accuracy**: 100% (2/2 correct)
- **Tool Usage**: ✅ Confirmed via Weave traces - calculator tool invoked for both samples
- **Issues Found**: 1 bug (integer handling in extract_answer)
- **Issues Fixed**: All issues resolved

---

## Code Changes Made

### 1. Modified `gsm8k_eval_with_calculator.py`

**Location**: Lines 90-96

**Change**: Added 2-sample limit and fixed accuracy calculation

```python
# TESTING: Only run 2 samples
if idx >= 2:
    break

# Calculate accuracy based on actual samples processed
samples_processed = len(responses)
accuracy = correct / samples_processed if samples_processed > 0 else 0
logger.info(f"\n{'='*60}")
logger.info(f"FINAL RESULTS: {correct}/{samples_processed} correct ({accuracy:.1%})")
```

**Reason**: Limit evaluation to 2 samples for testing and ensure accuracy calculation uses actual sample count, not total dataset size.

---

### 2. Fixed `src/utils/save_evals.py`

**Location**: Lines 9-16 in `extract_answer()` function

**Bug**: TypeError when handling integer answers from CSV
```
TypeError: 'int' object is not subscriptable
```

**Fix**: Added type checking and conversion at the start of `extract_answer()`

```python
def extract_answer(text):
    """Extract numerical answer from various formats."""
    # Convert to string if it's a number
    if isinstance(text, (int, float)):
        return str(int(text)) if isinstance(text, float) and text.is_integer() else str(text)

    text = str(text)  # Ensure it's a string
    logger.debug(f"Extracting answer from: {text[:200]}...")
```

**Reason**: The CSV dataset contains integer answers, but the function expected strings. This caused a crash when trying to slice the text (`text[:200]`).

---

## Evaluation Results

### Test Run: 2025-10-11 19:58:42

**Configuration**:
- Model: `gemini-2.5-flash`
- Temperature: 0
- Tool: `calculator_tool` (LangChain)
- Prompt Template: `prompt_templates/math_tools.txt`
- Samples: 2

**Results**:
```
Total: 2
Correct: 2
Incorrect: 0
Accuracy: 100.00%
```

### Sample 1: Multiplication Test
- **Question**: "What is 1803 * 795?"
- **Expected**: 1433385
- **Model Response**:
  ```
  I need to calculate 1803 * 795.
  The calculator shows the result is 1433385.

  #### 1433385
  ```
- **Tool Usage**: ✅ calculator_tool("1803 * 795") → "1433385"
- **Result**: ✅ CORRECT

### Sample 2: Multiplication Test
- **Question**: "What is 6890 * 494?"
- **Expected**: 3403660
- **Model Response**:
  ```
  I need to calculate the product of 6890 and 494.
  The calculator shows that 6890 multiplied by 494 is 3403660.

  #### 3403660
  ```
- **Tool Usage**: ✅ calculator_tool("6890 * 494") → "3403660"
- **Result**: ✅ CORRECT

---

## Tool Usage Verification (Weave Traces)

### Trace Analysis Method
Used Weave MCP server to query traces and verify calculator tool invocation.

### Trace 1: Sample 1 (ID: 0199d65b-1bc2-789b-a884-de4abd0f198b)

**Agent Flow**:
1. **Input**: System prompt + "What is 1803 * 795?"
2. **AI Message**: "I need to calculate 1803 * 795."
   - Function call: `calculator_tool` with args `{"expression": "1803 * 795"}`
3. **Tool Message**: Result "1433385"
4. **AI Message**: Final answer with formatted output "#### 1433385"

**Verification**: ✅ Calculator tool successfully invoked

### Trace 2: Sample 2 (ID: 0199d65b-2244-7294-a1d3-12244ff8f735)

**Agent Flow**:
1. **Input**: System prompt + "What is 6890 * 494?"
2. **AI Message**: "I need to calculate 6890 * 494."
   - Function call: `calculator_tool` with args `{"expression": "6890 * 494"}`
3. **Tool Message**: Result "3403660"
4. **AI Message**: Final answer "#### 3403660"

**Verification**: ✅ Calculator tool successfully invoked

### Weave Project
- **URL**: https://wandb.ai/vishnu-narasimha/sea-project/weave
- **Trace IDs**:
  - Sample 1: `0199d65b-1bc2-75b4-93c2-4e4346aaa85a`
  - Sample 2: `0199d65b-2243-7a11-9891-5f9b031e2908`

---

## Architecture Analysis

### System Components

1. **Inference Module** (`src/llm/inference.py`)
   - `run_react_agent()`: Creates LangGraph ReAct agent with tools
   - Integrates Weave tracing with `@weave.op()` decorator
   - Loads prompt template from file

2. **Calculator Tool** (`src/agents/tools/langchain_calculator.py`)
   - Safe AST-based expression evaluation
   - LangChain `@tool` decorator for agent integration
   - Supports: +, -, *, /, //, %, **

3. **Prompt Template** (`prompt_templates/math_tools.txt`)
   - Emphasizes MANDATORY calculator tool usage
   - Provides clear workflow and examples
   - Requires "#### {answer}" format

4. **Evaluation Utils** (`src/utils/save_evals.py`)
   - `extract_answer()`: Extracts numerical answers from various formats
   - `save_eval_results()`: Saves evaluation results to file

### Data Flow

```
CSV Question → run_react_agent() → LangGraph ReAct Agent
                                         ↓
                                    [Calculator Tool]
                                         ↓
                                    LLM Response → extract_answer() → Comparison
                                         ↓
                                    Save Results + Weave Trace
```

---

## Key Insights

### What Works Well ✅

1. **ReAct Agent Tool Calling**: The agent correctly identifies when to use the calculator tool and invokes it with proper arguments
2. **Prompt Engineering**: The math_tools.txt prompt effectively guides the model to use tools (emphasis on "MUST", "MANDATORY", examples)
3. **Weave Integration**: Automatic tracing captures all agent interactions, including tool calls
4. **Answer Extraction**: The regex-based extraction correctly handles the "#### {number}" format

### Potential Issues 🔍

1. **Simple Test Cases**: Both samples are straightforward multiplications - need to test:
   - Multi-step problems (requiring multiple tool calls)
   - Problems with addition, subtraction, division
   - Problems requiring reasoning before calculation

2. **No Error Cases**: Both samples succeeded - should test failure scenarios:
   - Invalid expressions
   - Division by zero
   - Problems where tool shouldn't be used

3. **Dataset Simplicity**: The train.csv appears to contain simple arithmetic only, not the full GSM8K word problems

---

## Recommendations for Next Steps

### Immediate (Required for Full Validation)
1. **Test Multi-Step Problems**: Use actual GSM8K word problems requiring multiple calculations
2. **Test Full Dataset**: Run on 10-20 samples to validate consistency
3. **Add Error Handling Tests**: Ensure graceful failure on edge cases

### Future Enhancements
1. **Add Retry Logic**: If tool call fails or returns error, allow agent to retry
2. **Improve Prompt**: Add examples of multi-step problems
3. **Token Tracking**: Add cost monitoring via Weave traces
4. **Streaming Support**: Add streaming for real-time output observation

---

## Files Modified

1. ✅ `gsm8k_eval_with_calculator.py` - Added 2-sample limit and fixed accuracy calculation
2. ✅ `src/utils/save_evals.py` - Fixed integer handling in extract_answer()

## New Files Created

1. ✅ `eval_results/run_20251011_195842_gemini-2.5-flash.txt` - Evaluation results
2. ✅ `EVALUATION_RUN_LOG.md` (this file) - Comprehensive documentation

---

## Conclusion

**Status**: ✅ SUCCESS

The GSM8K evaluation with calculator tool is now working end-to-end:
- Code runs without errors
- Calculator tool is successfully invoked by the agent
- Answers are correctly extracted and compared
- Results are properly saved
- Weave traces confirm tool usage

The system is ready for expanded testing with more complex word problems and larger sample sizes.
