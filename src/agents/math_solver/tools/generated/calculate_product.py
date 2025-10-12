'''
Tool: calculate_product
Description: Calculates the product of two numerical values.
Category: computation
'''

# Standard library imports


# Type hints


# Third-party imports
from langchain_core.tools import tool
import math


# Implementation function (without decorator for testing)
def calculate_product_impl(value1: float, value2: float) -> float:
    '''
    Calculates the product of two numerical values.

    Args:
        value1: The first numerical value.
        value2: The second numerical value.

    Returns:
        The product of value1 and value2.

    Raises:
        TypeError: If either value1 or value2 is not a numerical value.
    '''
    # Step 1: Validate that both value1 and value2 are numerical values.
    if not isinstance(value1, (int, float)):
        raise TypeError(f"value1 must be a numerical value, but got {type(value1)}")
    if not isinstance(value2, (int, float)):
        raise TypeError(f"value2 must be a numerical value, but got {type(value2)}")

    # Step 2: Multiply value1 by value2.
    result = value1 * value2

    # Step 3: Return the result.
    return result


# Tool wrapper with @tool decorator
@tool
def calculate_product(value1: float, value2: float) -> float:
    '''Wraps calculate_product_impl with @tool decorator for LangChain integration.'''
    return calculate_product_impl(value1, value2)


# TEST CASES
import pytest


def test_positive_numbers():
    '''Test with positive numbers.'''
    result = calculate_product_impl(value1=5.0, value2=4.0)
    assert result == 20.0


def test_negative_numbers():
    '''Test with negative numbers.'''
    result = calculate_product_impl(value1=-3.0, value2=2.0)
    assert result == -6.0


def test_zero_as_input():
    '''Test with zero as input.'''
    result = calculate_product_impl(value1=7.0, value2=0.0)
    assert result == 0.0


def test_floating_point_numbers():
    '''Test with floating point numbers.'''
    result = calculate_product_impl(value1=2.5, value2=3.5)
    assert result == 8.75


def test_large_numbers():
    '''Test with large numbers.'''
    result = calculate_product_impl(value1=1000000.0, value2=1000000.0)
    assert result == 1000000000000.0


def test_edge_case_invalid_input():
    '''Test edge case: Invalid input (non-numerical).'''
    with pytest.raises(TypeError):
        calculate_product_impl(value1="abc", value2=1.0)
    with pytest.raises(TypeError):
        calculate_product_impl(value1=1.0, value2="abc")

def test_edge_case_nan_input():
    '''Test edge case: NaN input.'''
    result = calculate_product_impl(value1=float('nan'), value2=2.0)
    assert math.isnan(result)
    result = calculate_product_impl(value1=2.0, value2=float('nan'))
    assert math.isnan(result)

def test_edge_case_inf_input():
    '''Test edge case: Infinity input.'''
    result = calculate_product_impl(value1=float('inf'), value2=2.0)
    assert result == float('inf')
    result = calculate_product_impl(value1=float('inf'), value2=-2.0)
    assert result == float('-inf')
