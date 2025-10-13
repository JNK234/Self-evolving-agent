'''
Tool: calculate_euclidean_metric
Description: Calculates a Euclidean metric (distance or magnitude) for n-dimensional coordinates.
Category: computation
'''

# Standard library imports
import math

# Type hints
from typing import List, Optional

# Third-party imports
from langchain_core.tools import tool


# Implementation function (without decorator for testing)
def calculate_euclidean_metric_impl(point1: List[float], point2: Optional[List[float]] = None) -> float:
    '''
    Calculates a Euclidean metric (distance or magnitude) for n-dimensional coordinates.

    This tool computes the straight-line distance between two points or the magnitude
    (length) of a single vector from the origin. It is generalized to work with
    coordinates in any number of dimensions (n-D), provided that both points
    have the same dimensionality.

    Args:
        point1 (List[float]): The first coordinate point or vector, represented as a
                              list of numbers. Must not be empty.
        point2 (Optional[List[float]]): The second coordinate point. If provided,
                                        the tool calculates the distance between
                                        point1 and point2. If omitted, it calculates
                                        the magnitude of point1 (its distance from
                                        the origin).

    Returns:
        float: The calculated Euclidean distance or magnitude as a non-negative float.

    Raises:
        ValueError: If point1 is empty, or if point1 and point2 have mismatched
                    dimensions.
        TypeError: If any element in the input lists is not a numerical value.
    '''
    # Step 1: Get input `point1` and optional `point2` (handled by signature).

    # Step 2: Validate that `point1` is a non-empty list of numbers.
    if not isinstance(point1, list) or not point1:
        raise ValueError("Input 'point1' must be a non-empty list of numbers.")

    # Step 3: Define an effective second point, `p2_eff`.
    p2_eff: List[float]

    # Step 4: IF `point2` is provided:
    if point2 is not None:
        # a. Validate that `point2` is a list of numbers.
        if not isinstance(point2, list):
            raise TypeError("Input 'point2' must be a list of numbers if provided.")
        # b. Check if `len(point1)` equals `len(point2)`.
        if len(point1) != len(point2):
            raise ValueError("Input points must have the same number of dimensions.")
        # c. Set `p2_eff = point2`.
        p2_eff = point2
    # Step 5: ELSE (if `point2` is not provided):
    else:
        # a. Create a zero vector `p2_eff` with the same dimension as `point1`.
        p2_eff = [0.0] * len(point1)

    # Step 6: Initialize a variable `sum_of_squares = 0.0`.
    sum_of_squares = 0.0

    # Step 7: Iterate through the indices from `0` to `len(point1) - 1`:
    try:
        for i in range(len(point1)):
            # a. Calculate the difference for the current dimension.
            delta = float(point1[i]) - float(p2_eff[i])
            # b. Add the square of the difference to the sum.
            sum_of_squares += delta ** 2
    except (ValueError, TypeError) as e:
        # This handles the case where list elements are not numerical.
        raise TypeError("All elements in input lists must be numerical.") from e

    # Step 8: Compute the final result by taking the square root.
    result = math.sqrt(sum_of_squares)

    # Step 9: Return the result.
    return result


# Tool wrapper with @tool decorator
@tool
def calculate_euclidean_metric(point1: List[float], point2: Optional[List[float]] = None) -> float:
    '''Calculates a Euclidean metric (distance or magnitude) for n-dimensional coordinates.'''
    return calculate_euclidean_metric_impl(point1, point2)


# TEST CASES
try:
    import pytest

    # Example Call Tests
    def test_example_2d_distance():
        """Scenario: Calculate the 2D distance between two points"""
        assert calculate_euclidean_metric_impl(point1=[1, 2], point2=[4, 6]) == 5.0

    def test_example_2d_magnitude():
        """Scenario: Calculate the magnitude (length) of a 2D vector"""
        assert calculate_euclidean_metric_impl(point1=[3, 4]) == 5.0

    def test_example_3d_distance():
        """Scenario: Calculate the 3D distance between two points"""
        assert calculate_euclidean_metric_impl(point1=[1, 0, 5], point2=[1, 4, 8]) == 5.0

    # Additional Test Cases from Spec
    def test_2d_distance_with_integers():
        """Test 2D distance with integer inputs"""
        result = calculate_euclidean_metric_impl(point1=[1, 1], point2=[2, 2])
        assert abs(result - 1.4142135623730951) < 1e-9

    def test_3d_magnitude():
        """Test 3D magnitude"""
        result = calculate_euclidean_metric_impl(point1=[1, 2, 3])
        assert abs(result - 3.7416573867739413) < 1e-9

    def test_zero_distance_for_identical_points():
        """Test zero distance for identical points"""
        result = calculate_euclidean_metric_impl(point1=[-5.5, 10.1], point2=[-5.5, 10.1])
        assert result == 0.0

    def test_1d_distance_absolute_difference():
        """Test 1D distance (absolute difference)"""
        result = calculate_euclidean_metric_impl(point1=[-5], point2=[5])
        assert result == 10.0

    def test_magnitude_of_origin():
        """Test magnitude of the origin point"""
        result = calculate_euclidean_metric_impl(point1=[0, 0, 0])
        assert result == 0.0

    # Edge Case Tests
    def test_edge_case_dimension_mismatch():
        """Test edge case: Points have mismatched dimensions"""
        with pytest.raises(ValueError, match="Input points must have the same number of dimensions."):
            calculate_euclidean_metric_impl(point1=[1, 2], point2=[1, 2, 3])

    def test_edge_case_empty_point1():
        """Test edge case: Input list is empty"""
        with pytest.raises(ValueError, match="Input 'point1' must be a non-empty list of numbers."):
            calculate_euclidean_metric_impl(point1=[])

    def test_edge_case_non_numerical_point1():
        """Test edge case: Input contains non-numerical data in point1"""
        with pytest.raises(TypeError, match="All elements in input lists must be numerical."):
            calculate_euclidean_metric_impl(point1=[1, 'a'])

    def test_edge_case_non_numerical_point2():
        """Test edge case: Input contains non-numerical data in point2"""
        with pytest.raises(TypeError, match="All elements in input lists must be numerical."):
            calculate_euclidean_metric_impl(point1=[1, 2], point2=[3, 'b'])

    def test_edge_case_non_list_input():
        """Test edge case: Input is not a list"""
        with pytest.raises(ValueError, match="Input 'point1' must be a non-empty list of numbers."):
            calculate_euclidean_metric_impl(point1="not a list") # type: ignore

except ImportError:
    # pytest not available, skip tests
    pass
