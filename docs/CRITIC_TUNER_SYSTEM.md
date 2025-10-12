# Critic-Tuner System Documentation

## Overview

The Critic-Tuner system is a self-evolving prompt optimization framework that uses LLMs to analyze agent performance and iteratively improve prompts. The system operates on a core principle: **zero hardcoded pattern detection** - all intelligence lives in LLM prompts, with Python code only orchestrating the flow.

### What It Does

The system automatically improves agent prompts through repeated evaluation cycles:
1. Agent solves problems using current prompt
2. Each solution is evaluated against a rubric
3. LLM analyzes evaluation patterns across multiple solutions
4. LLM generates surgical prompt improvements
5. Updated prompt is versioned and tracked in Weave
6. Cycle repeats with improved prompt

### Key Innovation

Traditional prompt optimization requires manual pattern detection and hardcoded rules. This system delegates **all analytical thinking to LLMs** - pattern recognition, trend analysis, and prompt modification logic all happen through carefully designed prompts.

## Architecture

### Component Overview

**Entry Point:**
- `scripts/run_sea_evolution.py` - Initializes system, manages evolution cycles, publishes prompts to Weave

**Orchestration:**
- `sea/orchestrator.py` - CriticTunerOrchestrator class coordinates the complete cycle

**Evaluation Engine:**
- `sea/critic.py` - Critic class handles two-phase evaluation:
  - Individual solution scoring
  - Cross-solution pattern extraction

**Prompt Surgery:**
- `sea/updater.py` - Updater class applies LLM-generated suggestions to prompts

**LLM Prompt Templates:**
- `prompt_templates/sea/critic_eval.txt` - Individual solution evaluation instructions
- `prompt_templates/sea/critic_pattern_v2.txt` - Pattern analysis instructions
- `prompt_templates/sea/updater_v2.txt` - Prompt modification instructions

**Configuration:**
- `rubric.json` - Evaluation criteria with weights and expected patterns

## Complete Execution Flow

### Phase 1: Initialization

**What Happens:**
The system loads the initial solver prompt from a template file and wraps it in a Weave StringPrompt object. This prompt is immediately published to Weave with version v0, creating the baseline for evolution.

**Where:**
- Entry point: `scripts/run_sea_evolution.py` main function
- Weave integration: Uses `weave.StringPrompt` and `weave.publish()`

**Result:**
Initial prompt is tracked in Weave UI under Assets → Prompts with name `{experiment_name}:v0`

---

### Phase 2: Problem Solving

**What Happens:**
The orchestrator iterates through all problems in the dataset. For each problem, it calls the solver function with the current prompt object. The solver uses this prompt as its system instructions to generate a solution.

**Where:**
- Orchestrated by: `sea/orchestrator.py` - `CriticTunerOrchestrator.run_cycle()`
- Solver function: Passed as parameter (typically from `sea/solver.py`)

**Result:**
Collection of problem-solution pairs ready for evaluation

---

### Phase 3: Individual Solution Evaluation

**What Happens:**
The Critic evaluates each solution independently against the rubric criteria. It sends the problem, solution, and rubric to an LLM using the evaluation prompt template. The LLM scores the solution on each criterion and provides specific improvement suggestions.

**Where:**
- Implementation: `sea/critic.py` - `Critic.evaluate_solution()`
- Prompt used: `prompt_templates/sea/critic_eval.txt`
- LLM decision: Assigns scores (0.0-1.0) per criterion, identifies issues

**Output Structure:**
Each evaluation contains:
- Overall weighted score
- Individual criterion scores
- Specific suggestions with types (ADD_CONSTRAINT, REPHRASE_INSTRUCTION, etc.)
- Reasoning for each suggestion

---

### Phase 4: Pattern Analysis (LLM Intelligence)

**What Happens:**
The Critic aggregates ALL individual evaluations and sends them to an LLM for pattern extraction. The LLM analyzes the collection to identify **systemic issues** - problems that appear repeatedly across multiple solutions. The LLM looks for:
- Repeated failures (same criterion failing in 3+ solutions)
- Rubric gaps (expected behaviors not being followed)
- Systemic prompt deficiencies

**Where:**
- Implementation: `sea/critic.py` - `Critic.evaluate_cycle()`
- Prompt used: `prompt_templates/sea/critic_pattern_v2.txt`
- Data formatting: `Critic._format_evaluations()` prepares raw data for LLM

**Key Insight:**
No Python code analyzes patterns. The system only formats raw evaluation data as text and sends it to the LLM. The LLM decides what constitutes a "pattern" based on the analysis prompt instructions.

**Output Structure:**
Pattern analysis contains:
- List of repeated failures with frequency evidence
- Identified rubric gaps
- Priority-ranked suggestions addressing patterns
- Evidence citations from evaluations

---

### Phase 5: Prompt Modification (LLM Surgery)

**What Happens:**
The Updater receives pattern-based suggestions and the current prompt. It sends both to an LLM with instructions to make **surgical, minimal modifications**. The LLM is instructed to:
- Preserve the prompt's existing style and structure
- Apply only the specific suggested changes
- Make modifications testable and specific
- Avoid rewrites or unnecessary alterations

**Where:**
- Implementation: `sea/updater.py` - `Updater.apply_suggestions()`
- Prompt used: `prompt_templates/sea/updater_v2.txt`
- Suggestion selection: `Updater._select_suggestions()` prioritizes by LLM-assigned priority

**Result:**
Modified prompt text with targeted improvements addressing identified patterns

---

### Phase 6: Threshold Decision

**What Happens:**
The orchestrator checks if the average score from pattern analysis is below the configured threshold (default: 0.85). If below, the new prompt is adopted. If above, the system skips the update and continues with the current prompt.

**Where:**
- Decision logic: `sea/orchestrator.py` - `CriticTunerOrchestrator.run_cycle()`
- Configurable via: `--threshold` command-line argument

---

### Phase 7: Version Publishing

**What Happens:**
If an update occurred, the new prompt text is wrapped in a Weave StringPrompt object and published to Weave. Weave automatically increments the version number (v1, v2, v3...) while maintaining the same prompt name.

**Where:**
- Publishing: `scripts/run_sea_evolution.py` after each cycle
- Weave tracks: Complete version history, allows side-by-side comparison in UI

**Result:**
New prompt version available as `{experiment_name}:v{N}` in Weave

---

### Cycle Completion

After publishing, the system either:
- **Continues** to next cycle with updated prompt (if more cycles remaining)
- **Terminates** and reports final statistics (cycle count, scores, changes)

## Key Functional Components

### Critic: Two-Phase Evaluation System

**Location:** `sea/critic.py`

**Core Responsibility:**
The Critic performs both granular and systemic evaluation. It acts as the analytical engine that transforms raw problem-solution pairs into actionable improvement insights.

**Functionality:**

**Phase 1 - Individual Evaluation:**
- Loads evaluation instructions from `prompt_templates/sea/critic_eval.txt`
- Scores each solution against rubric criteria independently
- Generates solution-specific suggestions
- Returns structured evaluation with scores and reasoning
- Implementation: `evaluate_solution()` method

**Phase 2 - Pattern Extraction:**
- Loads pattern analysis instructions from `prompt_templates/sea/critic_pattern_v2.txt`
- Aggregates all individual evaluations into formatted summary
- Delegates pattern detection entirely to LLM (zero hardcoded thresholds)
- LLM identifies repeated failures, rubric gaps, systemic issues
- Returns pattern analysis with priority-ranked suggestions
- Implementation: `evaluate_cycle()` method

**Data Flow:**
Raw evaluation data → Format as text summary → Send to LLM → Parse JSON response → Return structured patterns

---

### Updater: Surgical Prompt Modification

**Location:** `sea/updater.py`

**Core Responsibility:**
The Updater applies LLM-generated suggestions to prompts through minimal, targeted modifications. It ensures prompt evolution is incremental and preserves existing structure.

**Functionality:**

**Suggestion Prioritization:**
- Selects top N suggestions (default: 3) based on LLM-assigned priority
- Priority levels: high > medium > low
- Implementation: `_select_suggestions()` method

**Prompt Modification:**
- Loads modification instructions from `prompt_templates/sea/updater_v2.txt`
- Sends current prompt + selected suggestions to LLM
- LLM applies surgical changes (no rewrites)
- Returns modified prompt text and change summary
- Implementation: `apply_suggestions()` method

**Design Philosophy:**
No Python string manipulation. The LLM decides how to apply suggestions while following instructions to preserve style, make minimal changes, and ensure testability.

---

### Orchestrator: Cycle Coordination

**Location:** `sea/orchestrator.py` - `CriticTunerOrchestrator` class

**Core Responsibility:**
The Orchestrator coordinates the complete evolution cycle, managing the flow between solving, evaluation, pattern analysis, and prompt updates.

**Functionality:**

**Cycle Management:**
- Executes one complete evolution cycle per invocation
- Coordinates all phases: Solve → Evaluate → Analyze → Update
- Implementation: `run_cycle()` method

**Decision Making:**
- Compares average score against threshold (default: 0.85)
- Triggers prompt update only when score is below threshold
- Skips update when performance is satisfactory

**Data Aggregation:**
- Collects evaluation results from all solutions
- Extracts cycle statistics (scores, suggestions, changes)
- Returns comprehensive cycle report

**Flow Control:**
1. Invokes solver for all problems with current prompt
2. Sends each solution to Critic for evaluation
3. Sends all evaluations to Critic for pattern analysis
4. Checks score threshold
5. If needed, sends suggestions to Updater for prompt modification
6. Returns cycle statistics with new prompt (if updated)

**Integration Points:**
- Accepts solver function as parameter (decoupled from specific solver)
- Works with Weave StringPrompt objects
- Returns plain text prompts (caller wraps in StringPrompt for publishing)

---

## Agent Architecture & Extensibility

### File Organization

**SEA Framework Components (Self-Evolution Logic):**
Located in `sea/` directory:
- `sea/critic.py` - Evaluation and pattern analysis engine
- `sea/updater.py` - Prompt modification engine
- `sea/orchestrator.py` - Cycle coordination
- `sea/solver.py` - Solver wrapper (calls underlying agent)
- `sea/tools.py` - Tool definitions for agents

**Underlying Agent Being Optimized:**
Located in `src/agents/` directory:
- `src/agents/math_solver/` - Math problem-solving agent
- Other agent implementations would go here

**Prompt Templates:**
Located in `prompt_templates/` directory with organized structure:
- **SEA System Prompts** (`prompt_templates/sea/`):
  - `critic_eval.txt` - Individual evaluation instructions
  - `critic_pattern_v2.txt` - Pattern analysis instructions (latest)
  - `critic_pattern_v1.txt` - Pattern analysis (legacy)
  - `updater_v2.txt` - Prompt modification instructions (latest)
  - `updater_v1.txt` - Prompt modification (legacy)

- **Agent Prompts** (`prompt_templates/agents/{domain}/`):
  - `math_solver/basic.txt` - Basic math solver prompt
  - `math_solver/advanced.txt` - Advanced math solver prompt
  - Other agent domains can be added as subdirectories

**Evaluation Configuration:**
- `rubric.json` - Located in project root
- Contains evaluation criteria, weights, and expected patterns
- Domain-specific rubrics can be created for different agents

### Underlying Agent Integration

**Current Setup:**
The system optimizes a math-solving agent whose core logic lives in:
- **Solver wrapper**: `sea/solver.py` - Wraps the agent call
- **Agent implementation**: Uses LangChain's ChatGoogleGenerativeAI
- **Tools**: Calculator and other math tools in `sea/tools.py`

**How It Works:**
1. The agent's system prompt (from `prompt_templates/agents/{domain}/`) is what evolves
2. The agent's code remains unchanged
3. Only the instructions (prompt) improve through evolution
4. The solver wrapper passes the evolving prompt to the agent

### Extending to Other Agents

**To adapt this system for a different domain:**

**1. Create New Agent Implementation:**
- Add agent code in `src/agents/{domain}/`
- Implement agent-specific logic and tools
- Define domain-specific tool set

**2. Create Initial Agent Prompt:**
- Add new prompt in `prompt_templates/agents/{domain}/basic.txt`
- This is the prompt that will evolve
- Start with basic instructions to demonstrate evolution

**3. Create Domain-Specific Rubric:**
- Create `rubric_{domain}.json` with evaluation criteria
- Define domain-relevant criteria (e.g., for code: correctness, style, efficiency)
- Set appropriate weights for each criterion
- Specify expected patterns

**4. Customize SEA Prompts (Optional):**
- Keep generic `sea/critic_eval.txt` and `sea/critic_pattern_v2.txt` (they work across domains)
- Or create domain-specific versions if needed
- Update `sea/updater_v2.txt` if domain has unique requirements

**5. Create Solver Wrapper:**
- Implement domain-specific solver function
- Function signature: `solver_func(question: str, prompt_obj: weave.StringPrompt) -> str`
- Calls your agent with the evolving prompt

**6. Run Evolution:**
```bash
python scripts/run_sea_evolution.py \
  --name {domain}_agent \
  --experiment-id exp_001 \
  --prompt prompt_templates/agents/{domain}/basic.txt \
  --problems 10 \
  --cycles 3
```

**Example - Code Generation Agent:**
```
src/agents/code_gen/                          # Agent implementation
prompt_templates/agents/code_gen/basic.txt    # Initial agent prompt
rubric_code.json                              # Code quality criteria
sea/solver.py                                 # Update to support code_gen_solver()
```

The SEA framework (`sea/` components) remains unchanged - it's agent-agnostic.

## Weave Integration

### Automatic Prompt Versioning

**How It Works:**
Weave automatically manages prompt versions. When you publish a StringPrompt object with a name:
- First publish creates version `v0`
- Subsequent publishes with same name create `v1`, `v2`, `v3`...
- Each version is immutable and timestamped
- Complete version history is preserved

**Version Naming Strategy:**
- Base name: Set via `--name` flag (e.g., `math_solver`)
- Experiment ID: Optional via `--experiment-id` flag (e.g., `exp_001`)
- Final format: `{name}_{experiment_id}` if ID provided, otherwise just `{name}`
- This allows multiple parallel experiments without collision

**Implementation:**
- Initial publish: `scripts/run_sea_evolution.py` publishes v0 before first cycle
- Update publishes: After each cycle if score < threshold
- Each publish: `weave.publish(prompt_obj, name=final_prompt_name)`

### Viewing Prompts in Weave UI

**Access:**
1. Navigate to: `https://wandb.ai/<entity>/<project>`
2. Click: **Assets** → **Prompts** in sidebar
3. Find your prompt by name

**Features:**
- **Version history**: See all versions with timestamps
- **Side-by-side comparison**: Compare any two versions
- **Diff view**: Highlight changes between versions
- **Metrics tracking**: View score improvements across versions
- **Trace linking**: Jump to evaluation traces that led to each update

### Experiment Tracking

**Unique Experiments:**
Each evolution run should have a unique identifier to avoid overwriting results:

```bash
# Baseline experiment
--name baseline --experiment-id run_001
# Prompts: baseline_run_001:v0, v1, v2...

# Testing different threshold
--name baseline --experiment-id run_002
# Prompts: baseline_run_002:v0, v1, v2...

# Different starting prompt
--name advanced --experiment-id run_001
# Prompts: advanced_run_001:v0, v1, v2...
```

**Best Practice:**
Always use `--experiment-id` for reproducible experiments and clear tracking.

## Running the System

### Command Structure

```bash
python scripts/run_sea_evolution.py [OPTIONS]
```

### Configuration Options

| Flag | Purpose | Default | Notes |
|------|---------|---------|-------|
| `--name` | Base prompt name for Weave tracking | `math_solver_prompt` | Should describe the agent/domain |
| `--experiment-id` | Unique experiment identifier | None | Use for parallel experiments |
| `--prompt` | Path to initial agent prompt file | `prompt_templates/agents/math_solver/advanced.txt` | The prompt being evolved |
| `--problems` | Number of problems per cycle | 10 | More problems = better pattern detection |
| `--cycles` | Number of evolution cycles | 3 | Each cycle attempts one improvement |
| `--threshold` | Score threshold for updates | 0.85 | Update only if score < threshold |

### Example Scenarios

**Quick Test (5 problems, 1 cycle):**
```bash
python scripts/run_sea_evolution.py \
  --name test_run \
  --prompt prompt_templates/agents/math_solver/basic.txt \
  --problems 5 \
  --cycles 1
```

**Full Evolution Run:**
```bash
python scripts/run_sea_evolution.py \
  --name math_solver \
  --experiment-id baseline_v1 \
  --prompt prompt_templates/agents/math_solver/basic.txt \
  --problems 10 \
  --cycles 5 \
  --threshold 0.85
```

**Comparing Different Thresholds:**
```bash
# Strict threshold (updates more frequently)
python scripts/run_sea_evolution.py \
  --name comparison --experiment-id strict \
  --threshold 0.90 --cycles 5

# Lenient threshold (updates less frequently)
python scripts/run_sea_evolution.py \
  --name comparison --experiment-id lenient \
  --threshold 0.75 --cycles 5
```

### Understanding Output

**Console Output Shows:**
- Cycle number and progress
- Problems solved per cycle
- Evaluation scores (overall + per criterion)
- Whether prompt was updated
- Changes summary when updated
- Published prompt version

**In Weave UI You Can View:**
- All prompt versions side-by-side
- Score trends across cycles
- Individual evaluation traces
- Pattern analysis details
- Exact changes made to prompts

## Design Principles

### 1. Zero Hardcoded Intelligence

**Principle:**
All analytical thinking happens through LLM prompts, not Python code.

**What This Means:**
- **Pattern Detection**: No hardcoded thresholds for "what is a pattern" - LLM decides based on instructions
- **Trend Analysis**: No Python code counting failures or calculating statistics - LLM analyzes raw data
- **Suggestion Generation**: LLM determines what changes would help - not derived from rules
- **Prompt Modification**: LLM applies changes surgically - not Python string manipulation

**Why It Matters:**
- Easy to adjust behavior by editing prompt templates
- No need to modify code for different domains
- LLM reasoning is transparent in prompts
- System adapts to new criteria without code changes

### 2. LLM-First Architecture

**Principle:**
Python orchestrates, LLMs think.

**Implementation:**
```
Python Role:
- Load files and configuration
- Format data for LLM consumption
- Call LLMs with structured prompts
- Parse JSON responses
- Save results and publish to Weave

LLM Role:
- Evaluate solution quality
- Extract patterns from data
- Generate improvement suggestions
- Modify prompts surgically
- Prioritize actions
```

**Benefits:**
- Behavior changes through prompt editing, not code refactoring
- Easy experimentation with different prompting strategies
- Transparent reasoning visible in prompt templates
- Reduces code complexity

### 3. Clean Separation of Concerns

**Component Boundaries:**

- **Critic**: Data → LLM → Analysis
  - Input: Raw evaluations or problem-solution pairs
  - Output: Structured analysis with scores and suggestions
  - No modification logic

- **Updater**: Suggestions → LLM → Modified Prompt
  - Input: Current prompt + suggestions
  - Output: New prompt text
  - No evaluation logic

- **Orchestrator**: Coordinate → Collect → Decide
  - Manages flow between components
  - Makes threshold decisions
  - No analysis or modification logic

**Result:**
Each component has single responsibility, making system maintainable and extensible.

### 4. Agent-Agnostic Framework

**Principle:**
SEA framework works for any agent in any domain.

**How:**
- Framework (`sea/` components) never assumes math or any specific domain
- Agent-specific code isolated in `src/agents/` and `sea/solver.py`
- Domain knowledge lives in rubrics and agent prompts
- Evaluation criteria defined in JSON configuration

**To Support New Domain:**
Change only agent-specific files, not framework core.

## Example Evolution Scenario

### Starting Point

**Initial Prompt (math_tools_basic.txt):**
Very minimal instruction:
"You are a math problem solver. Solve the given problem and provide the answer."

**Goal:**
Demonstrate dramatic improvement through automated evolution.

### Cycle 1: Identifying Basic Gaps

**What Happens:**
System runs 10 math word problems through the agent. The Critic evaluates each solution and notices:
- 8 out of 10 solutions didn't use the calculator tool for arithmetic
- 7 out of 10 solutions lacked step-by-step reasoning
- 9 out of 10 solutions didn't follow any answer format

**Pattern Analysis:**
LLM analyzes these 10 evaluations and identifies **systemic patterns**:
- Calculator tool not being used (80% failure rate)
- Missing reasoning steps (70% failure rate)
- No standardized answer format (90% failure rate)

**LLM-Generated Suggestions:**
1. Priority: HIGH - Add explicit rule requiring calculator usage
2. Priority: HIGH - Add requirement for showing calculation steps
3. Priority: HIGH - Add answer format specification

**Prompt Update:**
LLM modifies the prompt surgically, adding:
- CRITICAL RULES section with calculator requirement
- Explicit instruction to show reasoning
- Answer format specification (#### [number])

**Result:**
New prompt published as v1 in Weave. Avg score: 0.42 → Significant improvements needed.

### Cycle 2: Refining Tool Usage

**What Happens:**
Agent solves 10 new problems with v1 prompt. Performance improves but new issues emerge:
- Calculator now used but sometimes for trivial operations
- Steps shown but sometimes redundant or unclear
- Format followed but explanations sometimes missing

**Pattern Analysis:**
LLM identifies:
- Over-reliance on calculator for simple operations
- Need for guidance on what constitutes "clear reasoning"
- Format compliance without sufficient explanation

**LLM-Generated Suggestions:**
1. Priority: MEDIUM - Clarify when calculator is necessary vs. optional
2. Priority: HIGH - Define what "clear reasoning" means
3. Priority: MEDIUM - Emphasize explanation before final answer

**Prompt Update:**
LLM refines the v1 prompt with:
- Nuanced calculator usage guidance
- Explicit definition of clear reasoning
- Requirement for explanation paragraph

**Result:**
New prompt published as v2. Avg score: 0.72 → Improving but below threshold.

### Cycle 3: Optimization

**What Happens:**
Agent solves problems with v2 prompt. Most criteria now met consistently:
- Appropriate tool usage in 9/10 cases
- Clear reasoning in 8/10 cases
- Good format and explanation in 9/10 cases

**Pattern Analysis:**
LLM identifies remaining minor issues:
- Occasional verbose explanations
- Very minor formatting inconsistencies

**Prompt Update:**
LLM makes final refinements for conciseness and consistency.

**Result:**
New prompt published as v3. Avg score: 0.88 → **Above threshold (0.85)** - Evolution stops.

### Evolution Summary

**Prompt Evolution:**
- v0: 2 sentences, no structure
- v1: Added rules, format, tool requirements
- v2: Refined tool usage, defined reasoning quality
- v3: Optimized for conciseness and consistency

**Score Progression:**
0.42 → 0.72 → 0.88

**Key Insight:**
All improvements identified and applied through LLM analysis - no manual intervention or hardcoded rules.

## Troubleshooting

### Issue: Prompts Not Appearing in Weave UI

**Symptoms:**
- Script runs successfully but prompts not visible in Weave Assets

**Common Causes:**
1. **Missing Weave initialization** - Check that `.env` contains `WEAVE_PROJECT_NAME`
2. **Wrong project** - Verify you're looking at correct entity/project in Weave UI
3. **Name collision** - Check if using same experiment name from different runs

**Solution:**
- Verify `weave.init()` is called at start of `scripts/run_sea_evolution.py`
- Check `.env` file has correct Weave credentials
- Use unique `--experiment-id` for each run
- Check console output for Weave publish confirmations

### Issue: Pattern Analysis Failing

**Symptoms:**
- Individual evaluations work but cycle analysis crashes
- JSON parsing errors in `critic.evaluate_cycle()`

**Common Causes:**
1. **Missing prompt template** - `sea_critic_p_v2.txt` not found
2. **LLM returning invalid JSON** - Response not properly formatted
3. **Evaluation data malformed** - Missing required fields in evaluations

**Solution:**
- Verify `prompt_templates/sea/critic_pattern_v2.txt` exists
- Check LLM response format (should be pure JSON or JSON in markdown code block)
- Review evaluation structure matches expected format
- Test with fewer problems first (--problems 3)

### Issue: Prompts Never Update

**Symptoms:**
- All cycles complete but prompt stays at v0
- "Score above threshold - no update" every cycle

**Common Causes:**
1. **Threshold too low** - Current scores always above threshold
2. **No suggestions generated** - Pattern analysis not finding issues
3. **Rubric too lenient** - Criteria weights allowing high scores despite issues

**Solution:**
- Try lower threshold (e.g., `--threshold 0.70`)
- Review rubric criteria and weights in `rubric.json`
- Check that problems actually test the criteria
- Verify updater prompt template exists and is valid

### Issue: Evaluation Errors

**Symptoms:**
- Crashes during individual solution evaluation
- "KeyError" or "Missing field" errors

**Common Causes:**
1. **Wrong prompt template** - Using cycle prompt for individual eval
2. **Rubric format issues** - Missing required fields in `rubric.json`
3. **LLM response format** - Not matching expected structure

**Solution:**
- Verify `sea_critic_eval.txt` exists and has correct placeholders
- Check `rubric.json` has required fields: criteria, weight, expected_pattern
- Review LLM responses for correct JSON structure

### Issue: Performance Degradation

**Symptoms:**
- Scores get worse instead of better
- Prompts become excessively long or convoluted

**Common Causes:**
1. **Conflicting suggestions** - LLM adding contradictory rules
2. **Over-optimization** - Too many cycles causing over-fitting
3. **Updater making rewrites** - Not following "surgical" instructions

**Solution:**
- Reduce max_suggestions in Updater (default: 3)
- Stop evolution earlier (fewer cycles)
- Review updater prompt to emphasize minimal changes
- Check if rubric criteria conflict with each other

## System Mental Model

**Think of SEA as an Intelligence Pipeline:**

```
Problems → Agent → Solutions
              ↓
         [Evaluation Layer]
    Individual Scores + Suggestions
              ↓
         [Pattern Layer]
      Systemic Issues + Priorities
              ↓
         [Modification Layer]
        Updated Prompt
              ↓
         [Tracking Layer]
         Version History
```

**Key Principles:**
1. **Data flows through LLMs** - Python only moves data around
2. **Each layer transforms data** - Evaluation → Patterns → Changes → Versions
3. **LLMs make all decisions** - What's a pattern, what to change, how to change
4. **Weave provides observability** - Every transformation is traced and versioned

**Mental Model:**
- **Critic** = Quality control sensor measuring agent output
- **Pattern Analysis** = Diagnostic system finding systemic issues
- **Updater** = Precision surgeon making targeted fixes
- **Orchestrator** = Factory manager coordinating the production line
- **Weave** = Version control and audit trail for everything

**The Power:**
Change system behavior by editing prompt files. No code changes needed.
