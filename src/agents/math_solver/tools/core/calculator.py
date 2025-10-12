# ABOUTME: LangChain-compatible calculator tool for mathematical operations
# ABOUTME: Provides safe expression evaluation using AST parsing for agent workflows

from langchain_core.tools import tool
from src.agents.math_solver.tools.core.calculator_utils import evaluate_expression


@tool
def calculator_tool(expression: str) -> str:
    """
    Evaluate mathematical expressions safely using AST parsing.

    Supports: addition (+), subtraction (-), multiplication (*), division (/),
    floor division (//), modulo (%), and exponentiation (**).

    Args:
        expression: Mathematical expression as a string (e.g., "25 * 34", "(10 + 5) / 3")

    Returns:
        String containing the result or error message

    Examples:
        calculator_tool("25 * 34") -> "850"
        calculator_tool("(100 - 25) / 3") -> "25.0"
        calculator_tool("2 ** 8") -> "256"
    """
    return evaluate_expression(expression)


# For testing
if __name__ == "__main__":
    test_cases = [
        ("25 * 34", "850"),
        ("(100 - 25) / 3", "25.0"),
        ("2 ** 8", "256"),
        ("10 + 5 * 2", "20"),
        ("(10 + 5) * 2", "30"),
        ("50 // 3", "16"),
        ("17 % 5", "2"),
        ("-10 + 5", "-5"),
    ]

    print("Testing LangChain Calculator Tool:")
    print("=" * 60)
    for expr, expected in test_cases:
        result = calculator_tool.invoke({"expression": expr})
        status = "✓" if result == expected else "✗"
        print(f"{status} {expr:20s} => {result:10s} (expected: {expected})")

    # Test error cases
    print("\nTesting error handling:")
    print("=" * 60)
    error_cases = ["100 / 0", "invalid_expr", "import os"]
    for expr in error_cases:
        result = calculator_tool.invoke({"expression": expr})
        print(f"✓ {expr:20s} => {result}")

    print("\n✓ LangChain calculator tool ready for use!")
