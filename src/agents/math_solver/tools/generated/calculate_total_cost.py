'''
Tool: calculate_total_cost
Description: Calculates the total cost by summing a list of numerical values.
Category: computation
'''

# Standard library imports


# Type hints (only for complex types like List, Dict, Optional, etc.)
# Note: Built-in types (int, float, str, bool) don't need imports from typing
from typing import List

# Third-party imports
from langchain_core.tools import tool


# Implementation function (without decorator for testing)
def calculate_total_cost_impl(costs: List[float]) -> float:
    '''
    Calculates the total cost by summing a list of numerical values.

    Args:
        costs: A list of numerical values representing individual costs.

    Returns:
        The total cost, which is the sum of all values in the input list.

    Raises:
        TypeError: If the input is not a list or if any element in the list is not a number.
    '''
    # Step 1: Validate that the input 'costs' is a list.
    if not isinstance(costs, list):
        raise TypeError("Input must be a list.")

    # Step 2: Validate that each element in the 'costs' list is a number (int or float).
    for cost in costs:
        if not isinstance(cost, (int, float)):
            raise TypeError("Each element in 'costs' must be a number (int or float).")

    # Step 3: If the 'costs' list is empty, return 0.0.
    if not costs:
        return 0.0

    # Step 4: Initialize a variable 'total_cost' to 0.0.
    total_cost = 0.0

    # Step 5: Iterate through the 'costs' list.
    # Step 6: For each element in the 'costs' list, add it to 'total_cost'.
    for cost in costs:
        total_cost += cost

    # Step 7: Return 'total_cost'.
    return total_cost


# Tool wrapper with @tool decorator
@tool
def calculate_total_cost(costs: List[float]) -> float:
    '''Wraps calculate_total_cost_impl with @tool decorator for LangChain integration.'''
    return calculate_total_cost_impl(costs)


# TEST CASES
import pytest


def test_positive_floats():
    '''Test with positive floats'''
    # Test the implementation function directly
    result = calculate_total_cost_impl(costs=[1.0, 2.5, 3.75])
    assert result == 7.25


def test_negative_and_positive_integers():
    '''Test with negative and positive integers'''
    # Test the implementation function directly
    result = calculate_total_cost_impl(costs=[-5, 10, 2])
    assert result == 7.0


def test_empty_list():
    '''Test with an empty list'''
    # Test the implementation function directly
    result = calculate_total_cost_impl(costs=[])
    assert result == 0.0


def test_single_value():
    '''Test with a single value'''
    # Test the implementation function directly
    result = calculate_total_cost_impl(costs=[5.5])
    assert result == 5.5


def test_mixed_integers_and_floats():
    '''Test with mixed integers and floats'''
    # Test the implementation function directly
    result = calculate_total_cost_impl(costs=[1, 2.5, 3])
    assert result == 6.5


def test_edge_case_invalid_input_type():
    '''Test edge case: Input list contains non-numerical values'''
    # Test edge case handling as specified
    with pytest.raises(TypeError) as excinfo:
        calculate_total_cost_impl(costs=[1, "a", 3])
    assert str(excinfo.value) == "Each element in 'costs' must be a number (int or float)."


def test_edge_case_input_not_list():
    '''Test edge case: Input is not a list'''
    # Test edge case handling as specified
    with pytest.raises(TypeError) as excinfo:
        calculate_total_cost_impl(costs="not a list")
    assert str(excinfo.value) == "Input must be a list."
