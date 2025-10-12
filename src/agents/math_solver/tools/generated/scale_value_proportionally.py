'''
Tool: scale_value_proportionally
Description: Calculates a target value based on a known proportional relationship (rule of three).
Category: computation
'''

# Third-party imports
from langchain_core.tools import tool


# Implementation function (without decorator for testing)
def scale_value_proportionally_impl(base_value: float, base_proportion: float, target_proportion: float) -> float:
    '''
    Calculates a target value based on a known proportional relationship (rule of three).

    This tool solves for an unknown value 'x' in a proportion, given a known relationship.
    It implements the formula: target_value = (base_value / base_proportion) * target_proportion.
    This is useful for problems involving ratios, rates, percentages, and direct variations.

    Args:
        base_value (float): The known numerical value in the relationship (e.g., $2500).
        base_proportion (float): The part of the proportion that corresponds to the base_value (e.g., the '5' in a 2:5 ratio).
        target_proportion (float): The part of the proportion for which the value needs to be calculated (e.g., the '2' in a 2:5 ratio).

    Returns:
        float: The calculated target value, scaled proportionally from the base value.

    Raises:
        ValueError: If `base_proportion` is zero, which would cause a division by zero error.
    '''
    # Step 1: Validate that `base_proportion` is not equal to 0.
    if base_proportion == 0:
        raise ValueError("base_proportion cannot be zero.")

    # Step 2: Calculate the unit rate by dividing the `base_value` by the `base_proportion`.
    unit_rate = base_value / base_proportion

    # Step 3: Calculate the final target value by multiplying the unit rate by the `target_proportion`.
    result = unit_rate * target_proportion

    # Step 4: Return the `result` as a float.
    return float(result)


# Tool wrapper with @tool decorator
@tool
def scale_value_proportionally(base_value: float, base_proportion: float, target_proportion: float) -> float:
    '''Calculates a target value based on a known proportional relationship (rule of three).'''
    return scale_value_proportionally_impl(
        base_value=base_value,
        base_proportion=base_proportion,
        target_proportion=target_proportion
    )


# TEST CASES
import pytest


def test_standard_ratio_calculation():
    '''Test standard ratio calculation'''
    assert scale_value_proportionally_impl(base_value=2500, base_proportion=5, target_proportion=2) == 1000.0


def test_percentage_increase():
    '''Test percentage increase'''
    assert scale_value_proportionally_impl(base_value=10, base_proportion=100, target_proportion=180) == 18.0


def test_percentage_decrease():
    '''Test percentage decrease (find 75% of 200)'''
    assert scale_value_proportionally_impl(base_value=200, base_proportion=100, target_proportion=75) == 150.0


def test_rate_calculation_with_floats():
    '''Test rate calculation with floats'''
    assert scale_value_proportionally_impl(base_value=8.5, base_proportion=2.5, target_proportion=10.0) == 34.0


def test_with_zero_base_value():
    '''Test with zero base_value'''
    assert scale_value_proportionally_impl(base_value=0, base_proportion=50, target_proportion=10) == 0.0


def test_with_negative_base_value():
    '''Test with negative base_value'''
    assert scale_value_proportionally_impl(base_value=-100, base_proportion=10, target_proportion=5) == -50.0


def test_edge_case_division_by_zero():
    '''Test edge case: division by zero'''
    with pytest.raises(ValueError, match="base_proportion cannot be zero."):
        scale_value_proportionally_impl(base_value=100, base_proportion=0, target_proportion=5)
