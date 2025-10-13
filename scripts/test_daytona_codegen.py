#!/usr/bin/env python3
"""
Integration test for Daytona code generation and testing pipeline.

Tests:
1. DaytonaManager sandbox creation and simple code execution
2. ToolGenerator code generation from specification
3. End-to-end: specification → code → sandbox testing
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sea.daytona_manager import DaytonaManager
from sea.tool_generator import ToolGenerator


def test_daytona_connection():
    """Test 1: Basic Daytona connection and sandbox execution."""
    print("=" * 60)
    print("TEST 1: Daytona Connection")
    print("=" * 60)

    try:
        manager = DaytonaManager()
        result = manager.test_connection()

        if result["success"]:
            print("✓ Daytona connection test PASSED")
            print(f"  Execution time: {result['execution_time']:.2f}s")
            print(f"  Output: {result['output'][:100]}...")
            return True
        else:
            print("✗ Daytona connection test FAILED")
            print(f"  Error: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"✗ Exception during connection test: {e}")
        return False


def test_simple_code_execution():
    """Test 2: Execute simple code with assertions."""
    print("\n" + "=" * 60)
    print("TEST 2: Simple Code Execution")
    print("=" * 60)

    simple_test_code = """
def add_numbers(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b

# Test
import pytest

def test_add_positive():
    assert add_numbers(2, 3) == 5

def test_add_negative():
    assert add_numbers(-1, 1) == 0
"""

    try:
        manager = DaytonaManager()
        result = manager.run_code_with_tests(
            tool_code=simple_test_code,
            dependencies=["pytest"]
        )

        if result["success"]:
            print("✓ Simple code execution PASSED")
            print(f"  Exit code: {result['exit_code']}")
            print(f"  Execution time: {result['execution_time']:.2f}s")
            return True
        else:
            print("✗ Simple code execution FAILED")
            print(f"  Exit code: {result['exit_code']}")
            print(f"  Output: {result['output'][:500]}")
            return False

    except Exception as e:
        print(f"✗ Exception during code execution: {e}")
        return False


def test_code_generation():
    """Test 3: Generate code from specification."""
    print("\n" + "=" * 60)
    print("TEST 3: Code Generation from Specification")
    print("=" * 60)

    # Simple specification for testing
    test_spec = {
        "name": "calculate_percentage",
        "description": "Calculate percentage of a value",
        "detailed_description": "Takes a base value and percentage, returns the calculated amount",
        "category": "computation",
        "deterministic": True,
        "input_parameters": [
            {
                "name": "value",
                "type": "float",
                "description": "The base value",
                "required": True
            },
            {
                "name": "percentage",
                "type": "float",
                "description": "Percentage to calculate (0-100)",
                "required": True,
                "constraints": "Must be between 0 and 100"
            }
        ],
        "return_type": "float",
        "return_description": "The calculated percentage amount",
        "algorithm_sketch": """1. Validate percentage is between 0 and 100
2. Calculate: (value * percentage) / 100
3. Return result""",
        "example_calls": [
            {
                "scenario": "Calculate 50% of 100",
                "input": {"value": 100, "percentage": 50},
                "output": 50.0,
                "explanation": "50% of 100 is 50"
            }
        ],
        "test_cases": [
            {
                "description": "Test basic calculation",
                "input": {"value": 100, "percentage": 50},
                "expected_output": 50.0,
                "assertion": "assert calculate_percentage(100, 50) == 50.0"
            },
            {
                "description": "Test zero percentage",
                "input": {"value": 100, "percentage": 0},
                "expected_output": 0.0,
                "assertion": "assert calculate_percentage(100, 0) == 0.0"
            }
        ],
        "edge_cases": [
            {
                "case": "Invalid percentage (> 100)",
                "handling": "Raise ValueError"
            }
        ]
    }

    try:
        generator = ToolGenerator()
        result = generator.generate_code(test_spec)

        if "tool_code" in result and result["tool_code"]:
            print("✓ Code generation PASSED")
            print(f"  Tool name: {result.get('tool_name', 'N/A')}")
            print(f"  Dependencies: {result.get('dependencies', [])}")
            print(f"  Code valid: {result.get('code_valid', False)}")
            print(f"  Code length: {len(result['tool_code'])} chars")
            return result
        else:
            print("✗ Code generation FAILED - No code generated")
            return None

    except Exception as e:
        print(f"✗ Exception during code generation: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_end_to_end():
    """Test 4: Complete pipeline - specification → code → testing."""
    print("\n" + "=" * 60)
    print("TEST 4: End-to-End Pipeline")
    print("=" * 60)

    # Generate code
    print("Step 1: Generating code from specification...")
    code_result = test_code_generation()

    if not code_result or not code_result.get("tool_code"):
        print("✗ End-to-end test FAILED - Code generation failed")
        return False

    # Test generated code in sandbox
    print("\nStep 2: Testing generated code in Daytona sandbox...")
    try:
        manager = DaytonaManager()
        test_result = manager.run_code_with_tests(
            tool_code=code_result["tool_code"],
            dependencies=code_result.get("dependencies", ["pytest"])
        )

        if test_result["success"]:
            print("✓ End-to-end test PASSED")
            print(f"  Code generated and tested successfully!")
            print(f"  Execution time: {test_result['execution_time']:.2f}s")
            return True
        else:
            print("✗ End-to-end test FAILED - Generated code tests failed")
            print(f"  Exit code: {test_result['exit_code']}")
            print(f"  Test output:")
            print(test_result['output'][:1000])
            return False

    except Exception as e:
        print(f"✗ Exception during end-to-end test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("DAYTONA CODE GENERATION - INTEGRATION TESTS")
    print("=" * 60)
    print()

    results = {}

    # Test 1: Connection
    results["connection"] = test_daytona_connection()

    # Test 2: Simple execution (only if connection works)
    if results["connection"]:
        results["simple_execution"] = test_simple_code_execution()
    else:
        print("\n⚠ Skipping remaining tests - Daytona connection failed")
        results["simple_execution"] = False
        results["code_generation"] = False
        results["end_to_end"] = False
        print_summary(results)
        return 1

    # Test 3: Code generation (doesn't need Daytona)
    results["code_generation"] = test_code_generation() is not None

    # Test 4: End-to-end (only if both previous tests passed)
    if results["simple_execution"] and results["code_generation"]:
        results["end_to_end"] = test_end_to_end()
    else:
        print("\n⚠ Skipping end-to-end test - Prerequisites failed")
        results["end_to_end"] = False

    # Summary
    print_summary(results)

    # Return exit code
    return 0 if all(results.values()) else 1


def print_summary(results):
    """Print test summary."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status:8} {test_name.replace('_', ' ').title()}")

    passed = sum(results.values())
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    if all(results.values()):
        print("\n🎉 All tests PASSED! Daytona integration ready.")
    else:
        print("\n⚠ Some tests FAILED. Check output above for details.")


if __name__ == "__main__":
    sys.exit(main())
