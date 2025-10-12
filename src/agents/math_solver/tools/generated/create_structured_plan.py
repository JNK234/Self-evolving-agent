'''
Tool: create_structured_plan
Description: Transforms a list of task descriptions into a structured, sequential plan.
Category: transformation
'''

# Standard library imports

# Type hints
from typing import List, Dict, Any

# Third-party imports
from langchain_core.tools import tool


def create_structured_plan_impl(main_goal: str, steps: List[str]) -> List[Dict[str, Any]]:
    '''
    Transforms a list of task descriptions into a structured, sequential plan.

    This tool takes a main goal and an ordered list of natural language steps and converts them
    into a formal, machine-readable plan object. Each step is assigned a unique integer ID,
    a default status ('pending'), and a dependency on the preceding step, enforcing a strict
    sequential workflow. This structured output is ideal for orchestrators that need to execute
    and track the progress of a multi-step task in a verifiable way.

    Args:
        main_goal (str): A string describing the overall objective of the plan. Used for context.
        steps (List[str]): An ordered list of strings, where each string is a description of a single, sequential task.

    Returns:
        List[Dict[str, any]]: A list of step objects, ordered sequentially. Each object contains a unique 'id' (int),
                               the 'description' (str), a 'status' (str, defaults to 'pending'), and a list of
                               'dependencies' (List[int]) which contains the ID of the previous step.

    Raises:
        ValueError: If 'main_goal' is empty, 'steps' list is empty, or 'steps' contains non-string or empty string elements.
    '''
    # 1. Initialize an empty list `structured_plan`.
    structured_plan = []

    # 2. Validate input `steps`
    if not isinstance(steps, list) or not steps:
        raise ValueError("Input 'steps' must be a non-empty list.")

    for i, step in enumerate(steps):
        if not isinstance(step, str) or not step.strip():
            raise ValueError(f"Invalid element at index {i} in 'steps': All elements must be non-empty strings.")

    # 3. Validate input `main_goal`
    if not isinstance(main_goal, str) or not main_goal.strip():
        raise ValueError("Input 'main_goal' must be a non-empty string.")

    # 4. Iterate through the input `steps` list
    for i, step_description in enumerate(steps):
        # 5a. Create a `step_id`
        step_id = i + 1

        # 5b. Determine the `dependencies`
        dependencies = []
        if i > 0:
            # Dependency is the ID of the previous step
            dependencies.append(step_id - 1)

        # 5c. Construct a step dictionary
        step_dict = {
            'id': step_id,
            'description': step_description,
            'status': 'pending',
            'dependencies': dependencies
        }

        # 5d. Append the step dictionary to the `structured_plan` list.
        structured_plan.append(step_dict)

    # 6. Return the `structured_plan` list.
    return structured_plan


@tool
def create_structured_plan(main_goal: str, steps: List[str]) -> List[Dict[str, Any]]:
    """Transforms a list of task descriptions into a structured, sequential plan.

    This tool takes a main goal and an ordered list of natural language steps and converts them
    into a formal, machine-readable plan object. Each step is assigned a unique integer ID,
    a default status ('pending'), and a dependency on the preceding step, enforcing a strict
    sequential workflow. This structured output is ideal for orchestrators that need to execute
    and track the progress of a multi-step task in a verifiable way.
    """
    return create_structured_plan_impl(main_goal, steps)


# TEST CASES
try:
    import pytest

    def test_decomposing_math_problem():
        """Tests the example scenario of decomposing a math problem."""
        main_goal = 'Find the height of a cylinder given its volume and radius.'
        steps = [
            'Identify the formula for cylinder volume: V = pi * r^2 * h',
            'Plug in the given values for V and r into the formula',
            'Isolate the variable h by rearranging the equation',
            'Calculate the final value of h'
        ]
        expected_output = [
            {'id': 1, 'description': 'Identify the formula for cylinder volume: V = pi * r^2 * h', 'status': 'pending', 'dependencies': []},
            {'id': 2, 'description': 'Plug in the given values for V and r into the formula', 'status': 'pending', 'dependencies': [1]},
            {'id': 3, 'description': 'Isolate the variable h by rearranging the equation', 'status': 'pending', 'dependencies': [2]},
            {'id': 4, 'description': 'Calculate the final value of h', 'status': 'pending', 'dependencies': [3]}
        ]
        assert create_structured_plan_impl(main_goal, steps) == expected_output

    def test_single_step_plan():
        """Tests the example scenario of a single-step plan."""
        main_goal = 'Calculate 2+2'
        steps = ['Add the two numbers together']
        expected_output = [
            {'id': 1, 'description': 'Add the two numbers together', 'status': 'pending', 'dependencies': []}
        ]
        assert create_structured_plan_impl(main_goal, steps) == expected_output

    def test_typical_multi_step_plan():
        """Tests with a typical multi-step plan."""
        main_goal = 'Solve for x in 2x + 5 = 15'
        steps = ['Subtract 5 from both sides', 'Divide both sides by 2']
        expected_output = [
            {'id': 1, 'description': 'Subtract 5 from both sides', 'status': 'pending', 'dependencies': []},
            {'id': 2, 'description': 'Divide both sides by 2', 'status': 'pending', 'dependencies': [1]}
        ]
        assert create_structured_plan_impl(main_goal, steps) == expected_output

    def test_edge_case_empty_steps_list():
        """Tests for an error when the 'steps' list is empty."""
        with pytest.raises(ValueError, match="Input 'steps' must be a non-empty list."):
            create_structured_plan_impl(main_goal='Do nothing', steps=[])

    def test_edge_case_invalid_type_in_steps():
        """Tests for an error when the 'steps' list contains a non-string element."""
        with pytest.raises(ValueError, match="Invalid element at index 1 in 'steps'"):
            create_structured_plan_impl(main_goal='Invalid plan', steps=['Step 1', 2, 'Step 3'])

    def test_edge_case_empty_string_in_steps():
        """Tests for an error when the 'steps' list contains an empty string."""
        with pytest.raises(ValueError, match="Invalid element at index 1 in 'steps'"):
            create_structured_plan_impl(main_goal='Invalid plan', steps=['Step 1', '', 'Step 3'])

    def test_edge_case_whitespace_string_in_steps():
        """Tests for an error when the 'steps' list contains a string with only whitespace."""
        with pytest.raises(ValueError, match="Invalid element at index 0 in 'steps'"):
            create_structured_plan_impl(main_goal='Invalid plan', steps=['   '])

    def test_edge_case_empty_main_goal():
        """Tests for an error when 'main_goal' is an empty string."""
        with pytest.raises(ValueError, match="Input 'main_goal' must be a non-empty string."):
            create_structured_plan_impl(main_goal='', steps=['A valid step'])

except ImportError:
    # pytest is not installed, so we cannot run the tests.
    pass
