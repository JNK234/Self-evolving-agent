# Self-Evolving Agent - Codebase Structure

## Directory Overview

```
Self-evolving-agent/
│
├── 📁 src/                           # Source code
│   ├── 📁 llm/                       # LLM inference and client code
│   │   ├── __init__.py
│   │   ├── inference.py              # Core LLM client, run_inference(), run_react_agent()
│   │   ├── google_llm.py             # Google Gemini client initialization
│   │   └── wb_inference.py           # Weights & Biases inference wrapper
│   │   └── wb_langchain.py           # W&B LangChain integration
│   │
│   ├── 📁 agents/                    # Agent implementations
│   │   ├── __init__.py
│   │   ├── 📁 math_solver/           # Math problem-solving agent
│   │   │   ├── __init__.py
│   │   │   └── rubric.json           # Evaluation criteria for math solver
│   │   │
│   │   └── 📁 tools/                 # Agent tools
│   │       ├── __init__.py
│   │       ├── calculator_utils.py   # Calculator utility functions
│   │       └── langchain_calculator.py # LangChain calculator tool
│   │
│   └── 📁 utils/                     # Utility functions
│       ├── __init__.py
│       └── evals_utils.py            # Evaluation utilities
│
├── 📁 sea/                           # Self-Evolving Agent framework
│   ├── critic.py                     # Two-phase evaluation (individual + pattern)
│   ├── updater.py                    # Surgical prompt modification
│   ├── orchestrator.py               # Cycle coordination (Solve → Critique → Update)
│   ├── solver.py                     # Solver wrapper for SEA system
│   └── tools.py                      # Tool imports for SEA
│
├── 📁 prompt_templates/              # Prompt templates
│   ├── math_tools.txt                # GSM8K evaluation prompt
│   │
│   ├── 📁 agents/                    # Agent-specific prompts
│   │   └── 📁 math_solver/           # Math solver prompts (evolving)
│   │       ├── advanced.txt          # Advanced math solver (used by SEA)
│   │       ├── basic.txt             # Basic math solver
│   │       └── solver.txt            # Baseline solver for SEA
│   │
│   └── 📁 sea/                       # SEA framework prompts
│       ├── critic_eval.txt           # Individual solution evaluation
│       ├── critic_pattern_v2.txt     # Pattern analysis (LLM intelligence)
│       └── updater_v2.txt            # Prompt modification instructions
│
├── 📁 scripts/                       # Executable scripts
│   ├── run_sea_evolution.py          # Main entry point for SEA evolution
│   ├── eval_basic.py                 # Basic evaluation script
│   ├── test_critic_tuner.py          # Test Critic-Tuner components
│   ├── test_sea.py                   # Test SEA system
│   └── rubric_generator.py           # Generate rubrics from descriptions
│
├── 📁 demos/                         # Demo and example scripts
│   ├── test_tool_calling.py         # Tool calling examples
│   ├── langchain_calculator_demo.py  # Calculator tool demo
│   └── wb_inference_demo.py          # Weave inference demo
│
├── 📁 data/                          # Datasets
│   ├── README.md                     # Data documentation
│   ├── gsm8k_train.jsonl             # GSM8K training data
│   └── train.csv                     # Converted CSV format
│
├── 📁 docs/                          # Documentation
│   └── CRITIC_TUNER_SYSTEM.md        # Complete SEA system documentation
│
├── 📁 notebooks/                     # Jupyter notebooks
│   ├── test.ipynb                    # Testing notebook
│   └── crewai_agent_tools.ipynb      # CrewAI tools exploration
│
├── 📁 eval_results/                  # Evaluation results
│   ├── run_20251011_154426_*.txt     # Evaluation logs
│   └── run_20251011_182156_*.txt
│
├── 📁 prompts/                       # Generated prompt versions (from SEA runs)
│   └── [prompt versions saved during evolution]
│
├── 📁 legacy/                        # Archived files (unused but preserved)
│   ├── 📁 code/
│   │   ├── google_agent.py           # Old agent implementation
│   │   └── dummy2.py                 # Experimental math tools
│   │
│   ├── 📁 prompts/
│   │   ├── google_agent.txt
│   │   ├── basic_v0.txt
│   │   ├── critic_pattern_v1.txt
│   │   └── updater_v1.txt
│   │
│   └── README.md                     # Legacy documentation
│
├── 🐍 Evaluation & Utility Scripts
│   ├── gsm8k_eval_with_calculator.py # GSM8K evaluation with calculator
│   └── convert_gsm8k_to_csv.py       # Dataset conversion utility
│
├── 📋 Configuration & Documentation
│   ├── .env                          # Environment variables (GOOGLE_API_KEY, WEAVE_PROJECT_NAME)
│   ├── .env.example                  # Environment template
│   ├── pyproject.toml                # Python project configuration
│   ├── uv.lock                       # Dependency lock file
│   ├── README.md                     # Project overview
│   ├── CLEANUP_SUMMARY.md            # Recent cleanup changes
│   └── CODEBASE_STRUCTURE.md         # This file
│
└── 📁 .claude/                       # Claude Code configuration
    └── [Claude-specific files]
```

## Key Components

### 1. SEA Framework (`sea/`)
Core self-evolution logic that analyzes agent performance and improves prompts:
- **critic.py**: Evaluates solutions and extracts patterns using LLM
- **updater.py**: Applies surgical prompt modifications
- **orchestrator.py**: Coordinates the evolution cycle
- **solver.py**: Wraps agent execution with current prompt

### 2. LLM Infrastructure (`src/llm/`)
Handles all LLM interactions:
- **inference.py**: Main interface for LLM calls and ReAct agents
- **google_llm.py**: Google Gemini client setup
- **wb_*.py**: Weights & Biases integration

### 3. Agent Implementation (`src/agents/`)
Domain-specific agent code:
- **math_solver/**: Math problem-solving agent
  - Contains rubric.json for evaluation criteria
- **tools/**: Shared tool implementations
  - Calculator tool for arithmetic operations

### 4. Prompt Templates (`prompt_templates/`)
All system prompts organized by purpose:
- **agents/**: Domain-specific agent prompts (what evolves)
- **sea/**: SEA framework prompts (how evolution works)
- **math_tools.txt**: Evaluation prompt

### 5. Scripts (`scripts/`)
Executable entry points:
- **run_sea_evolution.py**: Main SEA evolution runner
- **test_*.py**: Component testing
- **rubric_generator.py**: Rubric creation utility

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. User runs: scripts/run_sea_evolution.py            │
│     - Loads initial prompt from prompt_templates/      │
│     - Publishes as v0 to Weave                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. Orchestrator (sea/orchestrator.py) runs cycle:     │
│     - Solver uses current prompt to solve problems     │
│     - Critic evaluates each solution                   │
│     - Critic analyzes patterns across solutions        │
│     - Updater modifies prompt if score < threshold     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. New prompt version:                                 │
│     - Published to Weave as v1, v2, v3...              │
│     - Saved locally to prompts/ directory              │
│     - Cycle repeats with improved prompt               │
└─────────────────────────────────────────────────────────┘
```

## Configuration Files

- **.env**: Contains API keys and project settings
  - `GOOGLE_API_KEY`: Google Gemini API key
  - `WEAVE_PROJECT_NAME`: Weave project identifier
  - `GEMINI_MODEL`: Model name (default: gemini-2.5-flash)

- **pyproject.toml**: Python dependencies and project metadata
  - LangChain, LangGraph, Weave, CrewAI, etc.

- **rubric.json**: Evaluation criteria for math solver
  - Located in: `src/agents/math_solver/rubric.json`
  - Defines criteria, weights, expected patterns

## Key Features

### Self-Evolution
- **Zero Hardcoded Intelligence**: All pattern detection via LLM prompts
- **Automatic Prompt Improvement**: LLM analyzes and modifies prompts
- **Version Tracking**: Weave tracks all prompt versions

### Observability
- **Weave Integration**: Automatic tracing of all LLM calls
- **Version History**: Complete prompt evolution history
- **Evaluation Traces**: Individual solution evaluations tracked

### Extensibility
- **Agent-Agnostic**: SEA framework works for any domain
- **Pluggable Tools**: Easy to add new tools for agents
- **Flexible Rubrics**: JSON-based evaluation criteria

## Usage Examples

### Run SEA Evolution
```bash
python scripts/run_sea_evolution.py \
  --name math_solver \
  --experiment-id baseline_v1 \
  --prompt prompt_templates/agents/math_solver/basic.txt \
  --problems 10 \
  --cycles 5
```

### Run GSM8K Evaluation
```bash
python gsm8k_eval_with_calculator.py
```

### Test Components
```bash
python scripts/test_critic_tuner.py
```

## Integration Points

### With Weave
- `weave.init()` in main scripts
- Automatic tracing via `@weave.op()` decorators
- Prompt publishing with `weave.publish()`

### With LangChain
- `ChatGoogleGenerativeAI` for LLM client
- `create_react_agent` for ReAct agents
- Custom tools via `@tool` decorator

### With W&B
- Weave project tracks all runs
- Evaluation results logged
- Prompt versions stored as assets
