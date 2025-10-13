#!/usr/bin/env python3
"""
Test script for automatic tool creation engine.
Tests: discovery, loading, validation, and in-memory testing.
"""

from src.agents.shared.tool_loader import (
    load_agent_tools,
    validate_generated_tool,
    test_generated_tool_in_memory
)
from pathlib import Path


def test_tool_discovery():
    """Test that tools are discovered from math_solver directories."""
    print("\n" + "="*60)
    print("TEST 1: Tool Discovery")
    print("="*60)

    tools = load_agent_tools("math_solver", include_generated=True)

    print(f"\n📊 Results:")
    print(f"  Total tools loaded: {len(tools)}")
    for tool in tools:
        print(f"    - {tool.name}: {tool.description[:60]}...")

    # Verify we have at least calculator and format_number
    tool_names = [t.name for t in tools]
    assert "calculator_tool" in tool_names, "calculator_tool not found"
    assert "format_number" in tool_names, "format_number not found"

    print(f"\n✅ Tool discovery test PASSED")
    return tools


def test_validation():
    """Test code validation on generated tool."""
    print("\n" + "="*60)
    print("TEST 2: Code Validation")
    print("="*60)

    format_number_path = Path("src/agents/math_solver/tools/generated/format_number.py")
    code = format_number_path.read_text()

    print(f"\n🔍 Validating format_number.py...")
    validation = validate_generated_tool(code)

    print(f"\n📊 Validation Results:")
    for check, passed in validation.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}: {passed}")

    assert all(validation.values()), "Validation failed"
    print(f"\n✅ Validation test PASSED")


def test_in_memory_testing():
    """Test in-memory execution of tool tests."""
    print("\n" + "="*60)
    print("TEST 3: In-Memory Testing")
    print("="*60)

    format_number_path = Path("src/agents/math_solver/tools/generated/format_number.py")
    code = format_number_path.read_text()

    print(f"\n🧪 Running in-memory tests for format_number...")
    test_results = test_generated_tool_in_memory(code)

    print(f"\n📊 Test Results:")
    print(f"  Tests found: {test_results['tests_found']}")
    print(f"  Tests passed: {test_results['tests_passed']}")
    print(f"  Tests failed: {test_results['tests_failed']}")
    print(f"  Success: {test_results['success']}")

    if test_results['errors']:
        print(f"\n  Errors:")
        for error in test_results['errors']:
            print(f"    - {error['test']}: {error['error']}")

    assert test_results['success'], "Tests failed"
    print(f"\n✅ In-memory testing test PASSED")


def test_tool_invocation():
    """Test that discovered tools can be invoked."""
    print("\n" + "="*60)
    print("TEST 4: Tool Invocation")
    print("="*60)

    tools = load_agent_tools("math_solver", include_generated=True)
    format_number_tool = next((t for t in tools if t.name == "format_number"), None)

    assert format_number_tool is not None, "format_number tool not found"

    print(f"\n🔧 Testing format_number tool invocation...")

    # Test invocation
    result = format_number_tool.invoke({"number": 1234567.89, "separator": ","})
    print(f"  Input: 1234567.89")
    print(f"  Output: {result}")

    assert result == "1,234,567.89", f"Unexpected result: {result}"

    print(f"\n✅ Tool invocation test PASSED")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("AUTOMATIC TOOL CREATION ENGINE - INTEGRATION TESTS")
    print("="*60)

    try:
        test_tool_discovery()
        test_validation()
        test_in_memory_testing()
        test_tool_invocation()

        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED")
        print("="*60)
        print("\n✅ Tool creation engine is working correctly!")
        print("   - Discovery: ✓")
        print("   - Validation: ✓")
        print("   - In-memory testing: ✓")
        print("   - Tool invocation: ✓")
        print()

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
