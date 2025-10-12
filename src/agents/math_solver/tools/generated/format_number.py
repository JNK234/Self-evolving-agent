"""
Tool: format_number
Description: Format numbers with thousand separators for readability
Category: formatting
"""

from langchain_core.tools import tool


def format_number_impl(number: float, separator: str = ",") -> str:
    """
    Format a number with thousand separators.

    Args:
        number: The number to format
        separator: The separator to use (default: ",")

    Returns:
        Formatted number string with separators

    Raises:
        ValueError: If separator is not a single character
    """
    if len(separator) != 1:
        raise ValueError("Separator must be a single character")

    # Convert to string and handle negative numbers
    is_negative = number < 0
    abs_number = abs(number)

    # Split into integer and decimal parts
    parts = str(abs_number).split(".")
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else None

    # Add thousand separators
    formatted = ""
    for i, digit in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            formatted = separator + formatted
        formatted = digit + formatted

    # Add decimal part if present
    if decimal_part:
        formatted += "." + decimal_part

    # Add negative sign if needed
    if is_negative:
        formatted = "-" + formatted

    return formatted


@tool
def format_number(number: float, separator: str = ",") -> str:
    """Wraps format_number_impl with @tool decorator for LangChain integration."""
    return format_number_impl(number, separator)


# TEST CASES
import pytest


def test_basic_formatting():
    """Test basic number formatting with comma separator."""
    result = format_number_impl(1234567.89)
    assert result == "1,234,567.89"


def test_custom_separator():
    """Test formatting with custom separator."""
    result = format_number_impl(1234567, separator=" ")
    assert result == "1 234 567"


def test_negative_number():
    """Test negative number formatting."""
    result = format_number_impl(-9876543.21)
    assert result == "-9,876,543.21"


def test_small_number():
    """Test number smaller than 1000."""
    result = format_number_impl(999)
    assert result == "999"


def test_edge_case_zero():
    """Test zero formatting."""
    result = format_number_impl(0)
    assert result == "0"


def test_edge_case_invalid_separator():
    """Test invalid separator length."""
    with pytest.raises(ValueError):
        format_number_impl(1234, separator=",,")
