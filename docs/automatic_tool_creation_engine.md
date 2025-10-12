# Automatic Tool Creation Engine

## Overview

The Automatic Tool Creation Engine (ATC Engine) is a complete system for dynamically generating, validating, testing, and loading LangChain tools for agent-specific use cases. Tools are scoped per agent to prevent pollution and maintain clear ownership.

## Architecture

### Agent-Scoped Tool Organization

```
src/agents/
├── math_solver/
│   ├── solver.py
│   └── tools/
│       ├── core/                    # Static, hand-written tools
│       │   ├── calculator.py
│       │   └── calculator_utils.py
│       └── generated/               # Auto-generated tools
│           └── format_number.py
│
└── shared/
    └── tool_loader.py               # Discovery and validation logic
```

**Key Principle**: Each agent has its own `tools/` directory with `core/` and `generated/` subdirectories.

## Core Components

### 1. Tool Loader (`src/agents/shared/tool_loader.py`)

The tool loader provides three main functions:

#### `discover_tools(directory, exclude_files)`
Dynamically imports Python files and extracts `BaseTool` instances using `importlib`.

```python
tools = discover_tools("src/agents/math_solver/tools/core")
# Returns: [calculator_tool, ...]
```

#### `load_agent_tools(agent_name, include_generated=True)`
Loads all tools for a specific agent from both `core/` and `generated/` directories.

```python
tools = load_agent_tools("math_solver", include_generated=True)
# Returns: [calculator_tool, format_number, ...]
```

#### `validate_generated_tool(code)`
Validates tool code structure before saving:
- Syntax validity (compile check)
- Required imports present
- `@tool` decorator present
- Function definition present
- Docstring present
- Test functions present (test_*)

```python
validation = validate_generated_tool(tool_code)
# Returns: {"syntax_valid": True, "has_tool_decorator": True, ...}
```

#### `test_generated_tool_in_memory(tool_code)`
Executes tool code and runs pytest-style tests in isolated namespace:

```python
results = test_generated_tool_in_memory(tool_code)
# Returns: {
#   "tests_found": 6,
#   "tests_passed": 6,
#   "tests_failed": 0,
#   "errors": [],
#   "success": True
# }
```

### 2. Tool Generator (`sea/tool_generator.py`)

Converts tool specifications into executable Python code using LLM.

#### `generate_code(specification, save_to_agent=None)`
Generates Python code from specification with optional save-to-disk.

```python
generator = ToolGenerator(model="gemini-2.0-flash")

code_result = generator.generate_code(
    specification=spec,
    save_to_agent="math_solver"  # Optional: saves to disk
)

# Returns: {
#   "tool_code": "...",
#   "tool_name": "format_number",
#   "dependencies": ["pytest"],
#   "file_path": "src/agents/math_solver/tools/generated/format_number.py",
#   "save_status": "saved"
# }
```

#### `save_generated_tool(code_result, agent_name)`
Saves validated tool code to agent's `generated/` directory.

```python
saved_result = generator.save_generated_tool(code_result, "math_solver")
# Creates: src/agents/math_solver/tools/generated/{tool_name}.py
```

### 3. Agent Integration

Agents use `load_agent_tools()` to dynamically load their tool ecosystem:

```python
# sea/solver.py
from src.agents.shared.tool_loader import load_agent_tools

def solver(query: str):
    tools = load_agent_tools("math_solver", include_generated=True)
    # Tools now includes both core and generated tools
    agent = create_react_agent(llm, tools)
    # ...
```

## Tool Structure Template

Generated tools follow this structure:

```python
"""
Tool: tool_name
Description: One-line description
Category: category
"""

from langchain_core.tools import tool


def tool_name_impl(param1: type1, param2: type2) -> return_type:
    """
    Detailed description.

    Args:
        param1: Description
        param2: Description

    Returns:
        Description

    Raises:
        ValueError: When raised
    """
    # Implementation
    return result


@tool
def tool_name(param1: type1, param2: type2) -> return_type:
    """Wraps tool_name_impl with @tool decorator for LangChain integration."""
    return tool_name_impl(param1, param2)


# TEST CASES
import pytest


def test_basic_functionality():
    """Test description."""
    result = tool_name_impl(...)
    assert result == expected
```

## Usage Examples

### Example 1: Adding a New Agent with Tools

```python
# 1. Create agent directory structure
mkdir -p src/agents/code_analyzer/tools/core
mkdir -p src/agents/code_analyzer/tools/generated

# 2. Add core tools
# Create src/agents/code_analyzer/tools/core/ast_parser.py

# 3. Load tools in agent
from src.agents.shared.tool_loader import load_agent_tools

def code_analyzer(code: str):
    tools = load_agent_tools("code_analyzer")
    # Use tools with LangGraph agent
```

### Example 2: Generating and Saving a Tool

```python
from sea.tool_generator import ToolGenerator
from sea.tool_ideator import ToolIdeator

# 1. Create specification
ideator = ToolIdeator()
spec = ideator.generate_specification(pattern={
    "pattern_name": "Number formatting",
    "pattern_type": "formatting",
    # ...
})

# 2. Generate and save code
generator = ToolGenerator()
result = generator.generate_code(
    specification=spec,
    save_to_agent="math_solver"
)

# 3. Tool is immediately available (no restart needed)
tools = load_agent_tools("math_solver")
# New tool is discovered and loaded
```

### Example 3: Testing a Generated Tool

```python
from src.agents.shared.tool_loader import (
    validate_generated_tool,
    test_generated_tool_in_memory
)

# Validate structure
validation = validate_generated_tool(tool_code)
if not all(validation.values()):
    print("Validation failed:", validation)

# Run in-memory tests
test_results = test_generated_tool_in_memory(tool_code)
print(f"Tests: {test_results['tests_passed']}/{test_results['tests_found']} passed")
```

## Full ATC Pipeline

The complete pipeline from traces to deployed tools:

```python
from sea.atc_orchestrator import ATCOrchestrator

orchestrator = ATCOrchestrator(
    project_name="gsm8k-math-solver",
    pattern_model="gemini-2.0-flash",
    ideator_model="gemini-2.0-flash",
    codegen_model="gemini-2.0-flash"
)

results = orchestrator.run_atc_cycle(
    num_traces=20,
    agent_domain="math",
    min_frequency=3,
    generate_specifications=True,
    generate_code=True,        # Generate Python code
    test_in_sandbox=False      # Optional: Daytona testing
)

# Tools are automatically saved to agent directory
# Next agent initialization will discover and load them
```

## Testing

Run the integration test suite:

```bash
python test_tool_loading.py
```

Tests verify:
- Tool discovery from `core/` and `generated/` directories
- Code validation (structure, syntax, required elements)
- In-memory test execution
- Tool invocation through LangChain

## Benefits

### Agent-Scoped Tools
- **Isolation**: Math tools stay with math solver, code tools with code analyzer
- **Clear Ownership**: Each agent owns its tool ecosystem
- **Domain Alignment**: Tools matched to agent capabilities
- **Scalability**: Add agents without affecting others

### Dynamic Loading
- **No Restarts**: New tools available immediately
- **No Manual Imports**: Discovery happens automatically
- **Validation**: Bad tools caught before loading
- **Testing**: In-memory tests before deployment

### Generated Tools
- **Consistency**: All follow same structure
- **Quality**: Validated and tested before use
- **Traceable**: Specification → Code → Tests in one file
- **Reversible**: Easy to remove or modify

## Future Enhancements

- Tool versioning and rollback
- Tool sharing mechanism for common utilities
- Performance metrics per tool per agent
- Human approval workflow
- Automatic tool retirement for unused tools
- A/B testing framework for tool variations

## Troubleshooting

### Tool not discovered
- Verify file is in correct directory (`core/` or `generated/`)
- Check file has `.py` extension
- Ensure tool uses `@tool` decorator
- Verify no syntax errors (run `python -m py_compile <file>`)

### Import errors in tool
- Use absolute imports: `from src.agents.{agent}/tools/...`
- Avoid relative imports: `from . import ...`
- Check all dependencies are installed

### Validation failed
- Check tool code against template structure
- Ensure all required elements present (docstring, tests, etc.)
- Run `validate_generated_tool()` for detailed report

### Tests failing in-memory
- Run `test_generated_tool_in_memory()` for detailed errors
- Check assertions in test functions
- Verify test data matches implementation

## File Reference

### Core Files
- `src/agents/shared/tool_loader.py` - Discovery and validation
- `sea/tool_generator.py` - Code generation
- `sea/tool_ideator.py` - Specification creation
- `sea/atc_orchestrator.py` - Full pipeline orchestration

### Agent Structure
- `src/agents/{agent}/tools/core/` - Hand-written tools
- `src/agents/{agent}/tools/generated/` - Auto-generated tools
- `src/agents/{agent}/{agent}.py` - Agent implementation

### Testing
- `test_tool_loading.py` - Integration tests
- Generated tools include inline tests (test_*)
