'''
Tool: sequential_arithmetic
Description: Performs a sequence of arithmetic operations on an initial value.
Category: computation
'''

# Standard library imports
from typing import List, Dict, Union

# Third-party imports
from langchain_core.tools import tool
import pytest


def sequential_arithmetic_impl(initial_value: float, operations: List[Dict[str, Union[str, float]]]) -> float:
    '''
    Performs a sequence of arithmetic operations on an initial value.

    This tool takes a starting number and a list of operations to be applied in order.
    It processes the chain of calculations step-by-step, using the result of each
    operation as the input for the next. This is ideal for multi-step calculations
    where order matters and intermediate results are built upon.

    Args:
        initial_value (float): The starting number for the sequence of calculations.
        operations (List[Dict[str, Union[str, float]]]): An ordered list of operations
            to perform. Each operation is a dictionary with an 'operator' and an 'operand'.

    Returns:
        float: The final numerical result after applying all operations in sequence.

    Raises:
        ValueError: If an invalid operator is provided or if a division by zero is attempted.
        TypeError: If an operand is not a valid number.
    '''
    # 1. Initialize an accumulator with the initial_value.
    accumulator = float(initial_value)

    # 2. For each operation dictionary in the operations list:
    for operation in operations:
        operator = operation.get('operator')
        operand = operation.get('operand')

        if operator is None or operand is None:
            raise ValueError("Each operation dictionary must contain 'operator' and 'operand' keys.")

        # a. Extract the operator (string) and operand (float).
        # b. Validate that operator is one of '+', '-', '*', '/'.
        if operator not in ['+', '-', '*', '/']:
            raise ValueError(f"Invalid operator '{operator}'. Must be one of '+', '-', '*', '/'.")

        # c. Use a conditional block to perform the operation.
        if operator == '+':
            accumulator += operand
        elif operator == '-':
            accumulator -= operand
        elif operator == '*':
            accumulator *= operand
        elif operator == '/':
            # Check for division by zero.
            if operand == 0:
                raise ValueError("Division by zero is not allowed.")
            accumulator /= operand

    # 3. After iterating through all operations, return the final accumulator value.
    return accumulator


@tool
def sequential_arithmetic(initial_value: float, operations: List[Dict[str, Union[str, float]]]) -> float:
    """Performs a sequence of arithmetic operations on an initial value.

    This tool takes a starting number and a list of operations to be applied in order.
    It processes the chain of calculations step-by-step, using the result of each
    operation as the input for the next. This is ideal for multi-step calculations
    where order matters and intermediate results are built upon.
    """
    return sequential_arithmetic_impl(initial_value, operations)


# TEST CASES

def test_chained_multiplication_and_addition():
    """Tests a chain of multiplication and addition, from Example 1."""
    input_data = {
        'initial_value': 2,
        'operations': [
            {'operator': '*', 'operand': 3},
            {'operator': '+', 'operand': 2},
            {'operator': '*', 'operand': 2}
        ]
    }
    assert sequential_arithmetic_impl(**input_data) == 16.0

def test_subtraction_and_division():
    """Tests a chain of subtraction and division, from Example 3."""
    input_data = {
        'initial_value': 120,
        'operations': [
            {'operator': '-', 'operand': 36},
            {'operator': '/', 'operand': 2}
        ]
    }
    assert sequential_arithmetic_impl(**input_data) == 42.0

def test_all_four_operators():
    """Tests a sequence involving all four basic operators."""
    input_data = {
        'initial_value': 100,
        'operations': [
            {'operator': '/', 'operand': 4},
            {'operator': '+', 'operand': 5},
            {'operator': '*', 'operand': 10},
            {'operator': '-', 'operand': 50}
        ]
    }
    assert sequential_arithmetic_impl(**input_data) == 250.0

def test_basic_addition_chain():
    """Tests a simple chain of addition operations."""
    input_data = {
        'initial_value': 10,
        'operations': [
            {'operator': '+', 'operand': 5},
            {'operator': '+', 'operand': 15}
        ]
    }
    assert sequential_arithmetic_impl(**input_data) == 30.0

def test_mixed_operations_with_negative_result():
    """Tests a sequence of operations resulting in a negative number."""
    input_data = {
        'initial_value': 5,
        'operations': [
            {'operator': '*', 'operand': 2},
            {'operator': '-', 'operand': 20}
        ]
    }
    assert sequential_arithmetic_impl(**input_data) == -10.0

def test_edge_case_empty_operations_list():
    """Tests the edge case where the operations list is empty."""
    assert sequential_arithmetic_impl(initial_value=99.5, operations=[]) == 99.5

def test_edge_case_division_by_zero():
    """Tests that a ValueError is raised for division by zero."""
    input_data = {
        'initial_value': 100,
        'operations': [{'operator': '/', 'operand': 0}]
    }
    with pytest.raises(ValueError, match='Division by zero is not allowed.'):
        sequential_arithmetic_impl(**input_data)

def test_edge_case_invalid_operator():
    """Tests that a ValueError is raised for an unsupported operator."""
    input_data = {
        'initial_value': 10,
        'operations': [{'operator': '^', 'operand': 2}]
    }
    # The match string needs to escape regex special characters like '+' and '*'
    # but '^' is only special at the start of a string, so it's fine here.
    with pytest.raises(ValueError, match="Invalid operator '\^'. Must be one of '\+', '-', '\*', '/'\."):
        sequential_arithmetic_impl(**input_data)

def test_non_numeric_operand_type_error():
    """Tests that a TypeError is raised for a non-numeric operand."""
    input_data = {
        'initial_value': 10,
        'operations': [{'operator': '+', 'operand': 'five'}]
    }
    with pytest.raises(TypeError):
        sequential_arithmetic_impl(**input_data)
