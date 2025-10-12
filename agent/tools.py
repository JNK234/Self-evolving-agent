from langchain.tools import tool

# Define arithmetic tools
@tool
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@tool
def divide(a: float, b: float) -> float:
    """Divide a by b. Returns a float result."""
    if b == 0:
        return float('nan')
    return a / b


@tool
def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    return base ** exponent


@tool
def sqrt(x: float) -> float:
    """Calculate the square root of a number."""
    if x < 0:
        return float('nan')
    return x ** 0.5
