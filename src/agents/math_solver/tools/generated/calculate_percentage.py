'''
Tool: calculate_percentage
Description: Calculate percentage of a number
Category: computation
'''

# Standard library imports


# Type hints (only for complex types like List, Dict, Optional, etc.)
# Note: Built-in types (int, float, str, bool) don't need imports from typing
from typing import Optional

# Third-party imports
from langchain_core.tools import tool


# Implementation function (without decorator for testing)
def calculate_percentage_impl(value: float, total: Optional[float] = None, percentage: Optional[float] = None) -> float:
    '''
    Calculates what percentage one number is of another, or calculates a percentage of a number.

    Args:
        value: The value to calculate with
        total: The total/base value (when calculating what percentage)
        percentage: The percentage to calculate (when calculating percentage of a number)

    Returns:
        The calculated percentage or percentage value

    Raises:
        ValueError: If neither total nor percentage is provided, or if both are provided.
    '''
    if total is not None and percentage is not None:
        raise ValueError("Provide either 'total' or 'percentage', but not both.")

    if total is None and percentage is None:
        raise ValueError("Either 'total' or 'percentage' must be provided.")

    # Step 1: If total is provided: Calculate (value / total) * 100
    if total is not None:
        result = (value / total) * 100
    # Step 2: If percentage is provided: Calculate (value * percentage) / 100
    elif percentage is not None:
        result = (value * percentage) / 100
    else:
        raise ValueError("This should not happen. Either 'total' or 'percentage' must be provided.")

    # Step 3: Return the result rounded to 2 decimal places
    return round(result, 2)


# Tool wrapper with @tool decorator
@tool
def calculate_percentage(value: float, total: Optional[float] = None, percentage: Optional[float] = None) -> float:
    '''Wraps calculate_percentage_impl with @tool decorator for LangChain integration.'''
    return calculate_percentage_impl(value=value, total=total, percentage=percentage)


# TEST CASES
import pytest


def test_calculate_percentage():
    '''Calculate percentage: 25 is what % of 100'''
    # Test the implementation function directly
    result = calculate_percentage_impl(value=25, total=100)
    assert result == 25.0


def test_calculate_percentage_value():
    '''Calculate percentage value: 15% of 200'''
    # Test the implementation function directly
    result = calculate_percentage_impl(value=200, percentage=15)
    assert result == 30.0


def test_edge_case_zero_percentage():
    '''Test edge case: 0% of a number'''
    # Test edge case handling as specified
    result = calculate_percentage_impl(value=100, percentage=0)
    assert result == 0.0


def test_value_error_no_input():
    '''Test value error when no total or percentage is provided'''
    with pytest.raises(ValueError) as excinfo:
        calculate_percentage_impl(value=100)
    assert str(excinfo.value) == "Either 'total' or 'percentage' must be provided."


def test_value_error_both_inputs():
    '''Test value error when both total and percentage are provided'''
    with pytest.raises(ValueError) as excinfo:
        calculate_percentage_impl(value=100, total=100, percentage=10)
    assert str(excinfo.value) == "Provide either 'total' or 'percentage', but not both."
