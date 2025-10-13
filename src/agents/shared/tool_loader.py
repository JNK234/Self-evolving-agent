# ABOUTME: Dynamic tool discovery and loading for agent-specific tool ecosystems
# ABOUTME: Provides validation and in-memory testing for generated LangChain tools

import importlib.util
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.tools import BaseTool


def discover_tools(
    directory: str,
    exclude_files: List[str] = None
) -> List[BaseTool]:
    """
    Discover all LangChain tools in directory.

    Args:
        directory: Path to scan for tool files
        exclude_files: Files to skip (default: __init__.py, __pycache__)

    Returns:
        List of discovered BaseTool instances
    """
    if exclude_files is None:
        exclude_files = ["__init__.py"]

    directory = Path(directory)
    tools = []

    if not directory.exists():
        print(f"Warning: {directory} does not exist")
        return tools

    for py_file in directory.glob("*.py"):
        if py_file.name in exclude_files:
            continue

        try:
            # Import module dynamically
            spec = importlib.util.spec_from_file_location(
                py_file.stem,
                py_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find BaseTool instances
                for attr_name in dir(module):
                    if attr_name.startswith("_"):
                        continue
                    attr = getattr(module, attr_name)
                    if isinstance(attr, BaseTool):
                        tools.append(attr)
                        print(f"  ✓ Loaded: {attr.name} from {py_file.name}")

        except Exception as e:
            print(f"  ✗ Error loading {py_file.name}: {e}")

    return tools


def load_agent_tools(
    agent_name: str,
    include_generated: bool = True
) -> List[BaseTool]:
    """
    Load core and generated tools for specific agent.

    Args:
        agent_name: Agent name (e.g., "math_solver")
        include_generated: Whether to load generated tools

    Returns:
        Combined list of core and generated tools
    """
    tools = []
    base_path = Path(f"src/agents/{agent_name}/tools")

    print(f"\n🔧 Loading tools for agent: {agent_name}")
    print("=" * 60)

    # Load core tools
    core_dir = base_path / "core"
    if core_dir.exists():
        print(f"📦 Loading core tools from {core_dir}")
        core_tools = discover_tools(str(core_dir))
        tools.extend(core_tools)
    else:
        print(f"⚠️  Core tools directory not found: {core_dir}")

    # Load generated tools
    if include_generated:
        generated_dir = base_path / "generated"
        if generated_dir.exists():
            print(f"\n🤖 Loading generated tools from {generated_dir}")
            generated_tools = discover_tools(str(generated_dir))
            tools.extend(generated_tools)
        else:
            print(f"⚠️  Generated tools directory not found: {generated_dir}")

    print(f"\n✓ Total tools loaded: {len(tools)}")
    print("=" * 60)
    return tools


def validate_generated_tool(code: str) -> Dict[str, Any]:
    """
    Validate generated tool code meets LangChain requirements.

    Checks:
    1. Syntax validity
    2. Required imports present
    3. @tool decorator present
    4. Function definition present
    5. Docstring present
    6. Test functions present

    Args:
        code: Generated Python code string

    Returns:
        Dictionary with validation results for each check
    """
    validations = {
        "syntax_valid": False,
        "has_tool_decorator": False,
        "has_function_def": False,
        "has_docstring": False,
        "has_tests": False,
        "has_imports": False
    }

    # Syntax check
    try:
        compile(code, '<string>', 'exec')
        validations["syntax_valid"] = True
    except SyntaxError as e:
        print(f"  ✗ Syntax error: {e}")
        return validations

    # Required elements check
    required_checks = {
        "has_tool_decorator": "@tool" in code,
        "has_function_def": "def " in code,
        "has_docstring": '"""' in code or "'''" in code,
        "has_tests": "def test_" in code,
        "has_imports": "from langchain_core.tools import tool" in code
    }
    validations.update(required_checks)

    # Report any failures
    for check, passed in validations.items():
        if not passed:
            print(f"  ✗ Validation failed: {check}")

    return validations


def test_generated_tool_in_memory(tool_code: str) -> Dict[str, Any]:
    """
    Test generated tool code in-memory without sandbox.

    Executes code and runs pytest-style test functions.
    Faster than sandbox for initial validation.

    Args:
        tool_code: Complete Python code including tool and tests

    Returns:
        Dictionary with test results:
        {
            "tests_found": int,
            "tests_passed": int,
            "tests_failed": int,
            "errors": List[Dict],
            "success": bool
        }
    """
    results = {
        "tests_found": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "errors": [],
        "success": False
    }

    try:
        # Execute code to load tool and tests
        namespace = {}
        exec(tool_code, namespace)

        # Find test functions
        test_functions = [
            (name, func) for name, func in namespace.items()
            if name.startswith("test_") and callable(func)
        ]

        results["tests_found"] = len(test_functions)

        if results["tests_found"] == 0:
            results["errors"].append({
                "test": "discovery",
                "error": "No test functions found (must start with 'test_')",
                "type": "validation"
            })
            return results

        # Run each test
        for test_name, test_func in test_functions:
            try:
                test_func()  # Run test
                results["tests_passed"] += 1
                print(f"  ✓ {test_name}")
            except AssertionError as e:
                results["tests_failed"] += 1
                results["errors"].append({
                    "test": test_name,
                    "error": str(e),
                    "type": "assertion"
                })
                print(f"  ✗ {test_name}: {e}")
            except Exception as e:
                results["tests_failed"] += 1
                results["errors"].append({
                    "test": test_name,
                    "error": str(e),
                    "type": "exception"
                })
                print(f"  ✗ {test_name}: {e}")

        results["success"] = (
            results["tests_found"] > 0 and
            results["tests_failed"] == 0
        )

    except Exception as e:
        results["errors"].append({
            "test": "code_execution",
            "error": str(e),
            "type": "fatal"
        })
        print(f"  ✗ Fatal error executing code: {e}")

    return results
