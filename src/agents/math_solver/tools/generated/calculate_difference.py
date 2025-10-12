'''
Tool: calculate_difference
Description: Calculates the difference between two numerical values.
Category: computation
'''

# Standard library imports


# Type hints (only for complex types like List, Dict, Optional, etc.)
# Note: Built-in types (int, float, str, bool) don't need imports from typing


# Third-party imports
from langchain_core.tools import tool


# Implementation function (without decorator for testing)
def calculate_difference_impl(value1: float, value2: float) -> float:
    '''
    Calculates the difference between two numerical values.

    Args:
        value1: The first numerical value.
        value2: The second numerical value.

    Returns:
        The difference between value1 and value2 (value1 - value2).

    Raises:
        TypeError: If either value1 or value2 is not a number.
    '''
    # Step 1: Validate that both value1 and value2 are numbers (either int or float).
    if not isinstance(value1, (int, float)):
        raise TypeError("value1 must be a numerical value (int or float).")
    if not isinstance(value2, (int, float)):
        raise TypeError("value2 must be a numerical value (int or float).")

    # Step 2: If either input is not a number, raise a TypeError.
    # (Handled in Step 1)

    # Step 3: Calculate the difference: result = value1 - value2.
    result = value1 - value2

    # Step 4: Return the result.
    return float(result)


# Tool wrapper with @tool decorator
@tool
def calculate_difference(value1: float, value2: float) -> float:
    '''Wraps calculate_difference_impl with @tool decorator for LangChain integration.'''
    return calculate_difference_impl(value1=value1, value2=value2)


# TEST CASES
import pytest


def test_positive_integers():
    '''Positive integers'''
    # Test the implementation function directly
    result = calculate_difference_impl(value1=10.0, value2=5.0)
    assert result == 5.0


def test_negative_integers():
    '''Negative integers'''
    # Test the implementation function directly
    result = calculate_difference_impl(value1=-10.0, value2=-5.0)
    assert result == -5.0


def test_mixed_positive_and_negative():
    '''Mixed positive and negative'''
    # Test the implementation function directly
    result = calculate_difference_impl(value1=10.0, value2=-5.0)
    assert result == 15.0


def test_floating_point_numbers():
    '''Floating point numbers'''
    # Test the implementation function directly
    result = calculate_difference_impl(value1=7.5, value2=2.5)
    assert result == 5.0


def test_zero_values():
    '''Zero values'''
    # Test the implementation function directly
    result = calculate_difference_impl(value1=0.0, value2=0.0)
    assert result == 0.0


def test_value1_is_zero():
    '''value1 is zero'''
    # Test the implementation function directly
    result = calculate_difference_impl(value1=0.0, value2=5.0)
    assert result == -5.0


def test_value2_is_zero():
    '''value2 is zero'''
    # Test the implementation function directly
    result = calculate_difference_impl(value1=5.0, value2=0.0)
    assert result == 5.0


def test_edge_case_value1_is_none():
    '''Test edge case: value1 is None'''
    # Test edge case handling as specified
    with pytest.raises(TypeError):
        calculate_difference_impl(value1=None, value2=5.0)


def test_edge_case_value2_is_none():
    '''Test edge case: value2 is None'''
    # Test edge case handling as specified
    with pytest.raises(TypeError):
        calculate_difference_impl(value1=5.0, value2=None)


def test_edge_case_value1_is_string():
    '''Test edge case: value1 is a string'''
    # Test edge case handling as specified
    with pytest.raises(TypeError):
        calculate_difference_impl(value1="abc", value2=5.0)


def test_edge_case_value2_is_string():
    '''Test edge case: value2 is a string'''
    # Test edge case handling as specified
    with pytest.raises(TypeError):
        calculate_difference_impl(value1=5.0, value2="abc")
