# Scripts Directory

Quick reference guide for launch scripts in the Self-Evolving Agent system.

## 🚀 Main Training Scripts

### `run_sea_training.py` ⭐ **RECOMMENDED**
**Purpose**: Unified SEA training with wandb tracking + Phase 4 architecture
**What it does**: Complete training pipeline combining Critic-Tuner prompt evolution + Automatic Tool Creation
**When to use**: Main entry point for production training runs with full observability
**Features**:
- Config-driven LLM management (multiple providers)
- Dynamic tool loading per agent
- Wandb metrics + Weave tracing
- Prompt evolution + tool generation in one script

**Example**:
```bash
# Basic run with defaults (50 problems, LLM eval, ATC enabled)
python scripts/run_sea_training.py

# Custom configuration
python scripts/run_sea_training.py --problems 100 --experiment-id my_experiment
```

**Default settings**:
- ✅ LLM evaluation enabled
- ✅ ATC (Automatic Tool Creation) enabled
- ✅ Prompt iteration enabled (via config)
- Update frequency: Every 10 problems (configurable in `config.yaml`)

---

### `run_full_sea_pipeline.py`
**Purpose**: Legacy full pipeline script (Phase 3 architecture)
**What it does**: Multi-cycle evolution with explicit cycle management
**When to use**: When you need explicit control over cycle boundaries
**Note**: Consider using `run_sea_training.py` instead for most use cases

**Example**:
```bash
python scripts/run_full_sea_pipeline.py --problems 30 --cycles 3 --trigger-every 10
```

---

### `run_sea_evolution.py`
**Purpose**: Standalone Critic-Tuner evolution (no ATC)
**What it does**: Runs only prompt optimization through Solver → Critic → Updater loop
**When to use**: Testing prompt evolution in isolation without tool creation
**Features**:
- Multi-cycle prompt evolution
- Weave prompt versioning (v0, v1, v2...)
- Local prompt backups
- Score tracking per cycle

**Example**:
```bash
python scripts/run_sea_evolution.py --problems 10 --cycles 3 --experiment-id baseline_v1
```

---

## 🔧 Specialized Scripts

### `run_atc_evolution.py`
**Purpose**: Standalone Automatic Tool Creation testing
**What it does**: Analyzes solver traces and generates tool proposals independently
**When to use**: Testing ATC pipeline in isolation or analyzing existing traces
**Features**:
- Pattern recognition from traces
- Tool specification generation
- Code generation + sandbox testing
- Daytona integration

**Example**:
```bash
# Pattern analysis only
python scripts/run_atc_evolution.py --traces 20 --min-frequency 3

# Full pipeline with code generation
python scripts/run_atc_evolution.py --generate-specs --generate-code

# With sandbox testing
python scripts/run_atc_evolution.py --generate-specs --generate-code --test-in-sandbox
```

---

## 📊 Evaluation & Utilities

### `eval_basic.py`
**Purpose**: Basic GSM8K evaluation for baseline models
**What it does**: Evaluates LLMs and ReAct agents on math problems without self-improvement
**When to use**: Baseline benchmarking, comparing non-evolving models

**Example**:
```bash
python scripts/eval_basic.py
```

---

### `rubric_generator.py`
**Purpose**: Generate evaluation rubrics from natural language descriptions
**What it does**: Uses LLM to create structured JSON rubrics for the Critic
**When to use**: Creating/updating evaluation criteria for new domains

**Example**:
```bash
python scripts/rubric_generator.py "A good math solution shows work, uses tools correctly, and formats the answer clearly"
```

---

## 🧪 Test Scripts

### `test_critic_tuner.py`
Tests Critic-Tuner components (rubric loading, evaluation, prompt updates)

### `test_atc_weave_integration.py`
End-to-end integration test for ATC pipeline with real Weave data

### `test_weave_fetcher.py`
Validates trace retrieval from Weave projects

### `test_daytona_codegen.py`
Tests Daytona sandbox integration for tool code generation

---

## 🎯 Quick Start Guide

**First time setup**:
1. Ensure `.env` is configured with API keys
2. Check `config.yaml` for LLM provider settings
3. Run basic evaluation to generate initial traces

**Recommended workflow**:
```bash
# 1. Generate initial traces (if needed)
python scripts/eval_basic.py

# 2. Run full SEA training
python scripts/run_sea_training.py --problems 50 --experiment-id my_first_run

# 3. Check results
# - Wandb dashboard: metrics and accuracy charts
# - Weave UI: detailed traces and prompt versions
# - eval_results/: text summaries
# - prompt_templates/: evolved prompts
```

**Testing individual components**:
```bash
# Test only prompt evolution
python scripts/run_sea_evolution.py --problems 10 --cycles 2

# Test only tool creation
python scripts/run_atc_evolution.py --traces 20 --generate-specs
```

---

## 📁 Output Directories

- `eval_results/` - Evaluation result text files
- `prompt_templates/` - Evolved prompt versions
- `src/agents/<agent_name>/tools/generated/` - Auto-generated tools
- `atc_results/` - ATC analysis results
- Wandb project - Metrics and visualizations
- Weave UI - Traces and prompt versions

---

## ⚙️ Configuration

**Environment Variables** (`.env`):
- `WEAVE_PROJECT_NAME` - W&B project for tracing
- `WANDB_API_KEY` - Wandb authentication
- `GOOGLE_API_KEY` - For Gemini models
- `WB_INFERENCE_BASE_URL` - W&B Inference endpoint
- `WB_INFERENCE_MODEL` - Solver model name
- `DAYTONA_API_KEY` - For sandbox testing (optional)

**Config File** (`config.yaml`):
- LLM providers per component (solver, critic, updater, etc.)
- Self-improvement triggers and thresholds
- ATC parameters (min frequency, sandbox testing)

---

## 🆘 Troubleshooting

**"No module named 'pytest'"**
→ Fixed! pytest is now a dependency. Run `uv sync` to install.

**"No traces found"**
→ Run `eval_basic.py` first to generate initial traces.

**"Daytona connection failed"**
→ Sandbox testing is optional. Remove `--test-in-sandbox` flag.

**"Tool loading errors"**
→ Check that generated tools are in `src/agents/<agent>/tools/generated/`
