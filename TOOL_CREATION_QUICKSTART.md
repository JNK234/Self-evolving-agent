# Tool Creation Engine - Quick Start Guide

## 🚀 Quick Start

### For Users: Using the System

```python
# The agent automatically loads tools - no setup needed!
from sea.solver import solver

result = solver("What is 25 * 34?")
# Agent uses calculator_tool and any generated tools automatically
```

### For Developers: Adding New Tools

#### Option 1: Manual Tool (Core Tool)

Create `src/agents/math_solver/tools/core/my_tool.py`:

```python
from langchain_core.tools import tool

@tool
def my_tool(input: str) -> str:
    """Tool description."""
    return f"Processed: {input}"

# Add tests
import pytest

def test_my_tool():
    result = my_tool.invoke({"input": "test"})
    assert result == "Processed: test"
```

**Done!** Tool is automatically discovered on next agent run.

#### Option 2: Auto-Generated Tool (ATC Pipeline)

```python
from sea.atc_orchestrator import ATCOrchestrator

orchestrator = ATCOrchestrator(project_name="gsm8k-math-solver")

results = orchestrator.run_atc_cycle(
    num_traces=20,
    generate_specifications=True,
    generate_code=True
)

# Tools automatically saved to src/agents/math_solver/tools/generated/
```

**Done!** Generated tools are immediately available.

## 📂 Directory Structure

```
src/agents/
└── math_solver/
    └── tools/
        ├── core/           # Hand-written tools (put yours here)
        │   └── calculator.py
        └── generated/      # Auto-generated tools (don't edit manually)
            └── format_number.py
```

## 🧪 Testing Tools

### Test All Tools

```bash
python test_tool_loading.py
```

### Test Specific Tool Code

```python
from src.agents.shared.tool_loader import (
    validate_generated_tool,
    test_generated_tool_in_memory
)

# Validate structure
validation = validate_generated_tool(tool_code)
print(validation)  # {"syntax_valid": True, ...}

# Run tests
results = test_generated_tool_in_memory(tool_code)
print(f"{results['tests_passed']}/{results['tests_found']} passed")
```

## 🔧 Common Tasks

### View Loaded Tools

```python
from src.agents.shared.tool_loader import load_agent_tools

tools = load_agent_tools("math_solver")
for tool in tools:
    print(f"- {tool.name}: {tool.description}")
```

### Generate Tool from Specification

```python
from sea.tool_generator import ToolGenerator

generator = ToolGenerator()

spec = {
    "name": "calculate_percentage",
    "description": "Calculate percentage of a value",
    "input_parameters": [
        {"name": "value", "type": "float", "description": "Base value"},
        {"name": "percentage", "type": "float", "description": "Percentage (0-100)"}
    ],
    "return_type": "float",
    "algorithm_sketch": "Multiply value by percentage and divide by 100",
    # ... more fields
}

result = generator.generate_code(spec, save_to_agent="math_solver")
print(f"Saved to: {result['file_path']}")
```

### Remove Generated Tool

```bash
rm src/agents/math_solver/tools/generated/unwanted_tool.py
```

**Done!** Tool is immediately unavailable on next agent run.

## ⚠️ Important Rules

1. **Core tools**: Hand-written, stable, well-tested → `core/`
2. **Generated tools**: Auto-generated, experimental → `generated/`
3. **Don't edit generated tools manually** - regenerate instead
4. **Use absolute imports** in tools: `from src.agents...`
5. **Tools are agent-specific** - each agent has its own ecosystem

## 📚 Full Documentation

See `docs/automatic_tool_creation_engine.md` for complete documentation.

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Tool not found | Check it's in `core/` or `generated/` directory |
| Import error | Use absolute imports: `from src.agents...` |
| Validation failed | Run `validate_generated_tool()` for details |
| Tests failing | Run `test_generated_tool_in_memory()` for errors |

## ✅ Success Checklist

- [ ] Tool file in correct directory (`core/` or `generated/`)
- [ ] Tool uses `@tool` decorator
- [ ] Tool has docstring
- [ ] Tool has test functions (test_*)
- [ ] No syntax errors
- [ ] Uses absolute imports
- [ ] Tests pass

## 🎯 Next Steps

1. Review existing tools in `src/agents/math_solver/tools/core/`
2. Run `test_tool_loading.py` to verify system works
3. Try generating a tool using ATC pipeline
4. Create your own manual tool in `core/`
5. Read full docs at `docs/automatic_tool_creation_engine.md`
