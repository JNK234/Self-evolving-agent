# ABOUTME: Shared calculator logic for safe mathematical expression evaluation
# ABOUTME: Used by both CrewAI and LangChain calculator tool implementations

import ast
import operator
from typing import Union


# Supported operations for safe evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> Union[int, float]:
    """
    Safely evaluate an AST node representing a mathematical expression.

    Args:
        node: AST node to evaluate

    Returns:
        Result of the evaluation (int or float)

    Raises:
        ValueError: If the expression contains unsupported operations
    """
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operation: {op_type.__name__}")
        return SAFE_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operation: {op_type.__name__}")
        return SAFE_OPERATORS[op_type](operand)
    else:
        raise ValueError(f"Unsupported node type: {type(node).__name__}")


def evaluate_expression(expression: str) -> str:
    """
    Safely evaluate a mathematical expression string.

    This is the core calculation logic shared by all calculator tool implementations.
    It handles:
    - Basic arithmetic: +, -, *, /, //, %, **
    - Parentheses for order of operations
    - Error handling for invalid syntax, division by zero, etc.

    Args:
        expression: Mathematical expression as a string (e.g., "25 * 34", "(10 + 5) / 3")

    Returns:
        String containing the result or error message

    Examples:
        >>> evaluate_expression("25 * 34")
        "850"
        >>> evaluate_expression("(100 - 25) / 3")
        "25.0"
        >>> evaluate_expression("2 ** 8")
        "256"
    """
    try:
        expression = expression.strip()
        tree = ast.parse(expression, mode='eval')
        result = _safe_eval(tree.body)

        # Format result: convert floats that are integers to int representation
        if isinstance(result, float) and result.is_integer():
            result_str = str(int(result))
        else:
            result_str = str(result)

        return result_str

    except SyntaxError:
        return f"Error: Invalid mathematical expression syntax: '{expression}'"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error: Failed to evaluate expression: {str(e)}"
