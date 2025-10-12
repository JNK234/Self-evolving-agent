# Tool Creation Guide

This guide provides best practices for creating new tools in the `src/agents/tools/` directory for use with AI agents (LangChain, LangGraph, etc.).

## Table of Contents

1. [Tool Architecture](#tool-architecture)
2. [Creating a New Tool](#creating-a-new-tool)
3. [Best Practices](#best-practices)
4. [Testing Your Tool](#testing-your-tool)
5. [Documentation Standards](#documentation-standards)
6. [Common Patterns](#common-patterns)

---

## Tool Architecture

### Directory Structure

```
src/agents/tools/
├── __init__.py                    # Package exports
├── calculator_utils.py            # Shared utility logic
├── langchain_calculator.py        # LangChain tool implementation
└── your_new_tool.py               # Your tool here
```

### Design Principles

1. **Separation of Concerns**: Separate core logic from framework-specific wrappers
2. **Code Reuse**: Extract shared logic into utility modules
3. **Framework Agnostic Core**: Keep business logic independent of agent frameworks
4. **Error Handling**: Comprehensive error handling with clear error messages
5. **Type Safety**: Use type hints for all function parameters and returns

---

## Creating a New Tool

### Step 1: Plan Your Tool

Before coding, answer these questions:

- **What problem does this tool solve?**
- **What inputs does it need?**
- **What outputs does it produce?**
- **Are there edge cases or errors to handle?**
- **Which framework will use this tool (LangChain, LangGraph)?**

### Step 2: Create Shared Logic

Extract the core business logic into a utility module:

```python
# src/agents/tools/your_tool_utils.py
# ABOUTME: Shared utility logic for [tool purpose]
# ABOUTME: Framework-agnostic implementation for use with LangChain/LangGraph tools

from typing import Union, Any

def process_input(input_data: str) -> str:
    """
    Core processing logic for your tool.

    Args:
        input_data: Input to process

    Returns:
        Processed result as string

    Raises:
        ValueError: If input is invalid
    """
    try:
        # Your logic here
        result = input_data.upper()  # Example
        return result
    except Exception as e:
        raise ValueError(f"Error processing input: {str(e)}")
```

### Step 3: Create LangChain Tool Wrapper

```python
# src/agents/tools/your_langchain_tool.py
# ABOUTME: LangChain-compatible tool for [tool purpose]
# ABOUTME: Wraps shared logic with LangChain tool decorator

from langchain_core.tools import tool
from .your_tool_utils import process_input

@tool
def your_langchain_tool(input_data: str) -> str:
    """
    [One-line tool description for the agent]

    [Detailed description matching the CrewAI version]

    Args:
        input_data: Description of the input parameter

    Returns:
        Description of what gets returned

    Examples:
        your_langchain_tool("test input") -> "TEST INPUT"
    """
    return process_input(input_data)
```

### Step 4: Update Package Exports

Add your tool to `src/agents/tools/__init__.py`:

```python
# ABOUTME: Tools package exposing all agent tools
# ABOUTME: Provides reusable tools for specialized tasks

from .langchain_calculator import calculator_tool
from .your_langchain_tool import your_langchain_tool

__all__ = [
    "calculator_tool",
    "your_langchain_tool"
]
```

### Step 5: Add Testing Code

Include a test section in your tool file:

```python
# For testing
if __name__ == "__main__":
    test_cases = [
        ("test input", "TEST INPUT"),
        ("another test", "ANOTHER TEST"),
        ("", "Error"),  # Edge case
    ]

    print("Testing Your Tool:")
    print("=" * 60)
    for input_val, expected in test_cases:
        result = process_input(input_val) if input_val else "Error: Empty input"
        status = "✓" if result == expected else "✗"
        print(f"{status} {input_val:20s} => {result}")

    print("\n✓ Tool ready for use!")
```

---

## Best Practices

### 1. Error Handling

Always return error messages as strings, never raise exceptions from tool functions:

```python
# ✓ Good: Return error as string
def good_tool(input_data: str) -> str:
    try:
        result = process(input_data)
        return result
    except ValueError as e:
        return f"Error: Invalid input - {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error - {str(e)}"

# ✗ Bad: Raises exception (will crash agent)
def bad_tool(input_data: str) -> str:
    result = process(input_data)  # Could raise exception
    return result
```

### 2. Input Validation

Validate and sanitize inputs:

```python
def your_tool(input_data: str) -> str:
    # Clean input
    input_data = input_data.strip()

    # Validate
    if not input_data:
        return "Error: Input cannot be empty"

    if len(input_data) > 1000:
        return "Error: Input too long (max 1000 characters)"

    # Process
    return process(input_data)
```

### 3. Clear Documentation

Write tool docstrings from the agent's perspective:

```python
# ✓ Good: Clear, agent-friendly documentation
@tool
def weather_tool(city: str) -> str:
    """
    Get current weather information for a city.

    Use this tool when the user asks about weather conditions,
    temperature, or forecasts for a specific location.

    Args:
        city: Name of the city (e.g., "San Francisco", "Tokyo")

    Returns:
        Weather description including temperature and conditions

    Examples:
        weather_tool("Seattle") -> "Partly cloudy, 62°F"
    """
    pass

# ✗ Bad: Technical jargon, unclear purpose
@tool
def weather_tool(city: str) -> str:
    """Fetches meteorological data via API."""
    pass
```

### 4. Logging and Debugging

Add logging for debugging without cluttering tool output:

```python
import logging

logger = logging.getLogger(__name__)

@tool
def your_tool(input_data: str) -> str:
    """Tool description."""
    logger.debug(f"Tool called with input: {input_data}")

    try:
        result = process(input_data)
        logger.debug(f"Tool returning: {result}")
        return result
    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        return f"Error: {str(e)}"
```

### 5. Return Types

Always return strings for consistency:

```python
# ✓ Good: Returns string
@tool
def calculate(expr: str) -> str:
    result = eval_expression(expr)
    return str(result)

# ✗ Bad: Returns different types
@tool
def calculate(expr: str) -> Union[int, float, str]:
    result = eval_expression(expr)
    return result  # Could be int, float, or str
```

---

## Testing Your Tool

### Unit Testing

Create a test file `tests/test_your_tool.py`:

```python
import pytest
from src.agents.tools.your_tool_utils import process_input

def test_basic_functionality():
    assert process_input("test") == "TEST"

def test_empty_input():
    with pytest.raises(ValueError):
        process_input("")

def test_error_handling():
    result = process_input("invalid&input")
    assert "Error" in result
```

### Integration Testing

Test with actual agents:

```python
# test_agent_integration.py
from langchain.agents import create_react_agent
from src.agents.tools.your_langchain_tool import your_langchain_tool

def test_with_langchain():
    agent = create_react_agent(llm, tools=[your_langchain_tool])
    result = agent.invoke({"input": "Test this tool"})
    assert result is not None
```

### Manual Testing

Test directly from your tool file:

```bash
python src/agents/tools/your_tool.py
```

---

## Documentation Standards

### File Headers

Every tool file should start with ABOUTME comments:

```python
# ABOUTME: Brief one-line description of tool purpose
# ABOUTME: Additional context about implementation or usage
```

### Function Docstrings

Use Google-style docstrings:

```python
def your_function(param1: str, param2: int = 0) -> str:
    """
    One-line summary of function.

    More detailed explanation of what the function does,
    when to use it, and any important notes.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter with default

    Returns:
        Description of return value

    Raises:
        ValueError: When this error occurs
        TypeError: When that error occurs

    Examples:
        >>> your_function("test", 5)
        "result"

    Note:
        Any additional important information
    """
    pass
```

---

## Common Patterns

### Pattern 1: API Wrapper Tool

```python
# tool_utils.py
import requests

def call_external_api(query: str) -> str:
    """Core API calling logic."""
    try:
        response = requests.get(f"https://api.example.com?q={query}")
        response.raise_for_status()
        return response.json()["result"]
    except requests.RequestException as e:
        return f"Error calling API: {str(e)}"

# langchain_tool.py
from langchain_core.tools import tool
from .tool_utils import call_external_api

@tool
def api_tool(query: str) -> str:
    """Query external API for information."""
    return call_external_api(query)
```

### Pattern 2: File Processing Tool

```python
def process_file(filepath: str) -> str:
    """Process a file and return results."""
    try:
        if not os.path.exists(filepath):
            return f"Error: File not found - {filepath}"

        with open(filepath, 'r') as f:
            content = f.read()

        # Process content
        result = analyze(content)
        return result

    except PermissionError:
        return f"Error: Permission denied - {filepath}"
    except Exception as e:
        return f"Error reading file: {str(e)}"
```

### Pattern 3: Data Transformation Tool

```python
def transform_data(data: str, format: str = "json") -> str:
    """Transform data between formats."""
    try:
        if format == "json":
            import json
            parsed = json.loads(data)
            return json.dumps(parsed, indent=2)
        elif format == "yaml":
            import yaml
            parsed = yaml.safe_load(data)
            return yaml.dump(parsed)
        else:
            return f"Error: Unsupported format - {format}"

    except (json.JSONDecodeError, yaml.YAMLError) as e:
        return f"Error parsing {format}: {str(e)}"
```

---

## Checklist for New Tools

Before submitting your tool, ensure:

- [ ] Core logic extracted to `*_utils.py`
- [ ] LangChain tool wrapper created
- [ ] ABOUTME headers added to all files
- [ ] Comprehensive docstrings with examples
- [ ] Error handling for all edge cases
- [ ] Input validation and sanitization
- [ ] Type hints on all parameters and returns
- [ ] Test cases in `if __name__ == "__main__"` block
- [ ] Tool exported in `__init__.py`
- [ ] Manual testing completed
- [ ] Integration test with agent (optional but recommended)

---

## Example: Complete Tool Implementation

See `langchain_calculator.py` and `calculator_utils.py` for a complete working example following all best practices.

Key features demonstrated:
- ✓ Shared utility logic (`calculator_utils.py`)
- ✓ LangChain tool wrapper
- ✓ Comprehensive error handling
- ✓ Clear documentation
- ✓ Built-in test cases
- ✓ Type safety

---

## Questions or Issues?

If you have questions about tool development:

1. Review existing tools in `src/agents/tools/`
2. Check this guide's examples
3. Consult framework documentation (LangChain, LangGraph)
4. Open an issue if you discover gaps in this guide

---

## Version History

- **v1.0** (2025-01-11): Initial guide based on calculator tool refactoring
