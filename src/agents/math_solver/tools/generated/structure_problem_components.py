'''
Tool: structure_problem_components
Description: Parses a semi-structured text block into a dictionary of categorized statements.
Category: transformation
'''

# Standard library imports
from typing import Dict, List

# Third-party imports
from langchain_core.tools import tool


def structure_problem_components_impl(problem_text: str, component_prefixes: Dict[str, str]) -> Dict[str, List[str]]:
    '''
    Parses a semi-structured text block into a dictionary of categorized statements.

    Takes a multi-line string where each line is potentially prefixed with a label 
    (e.g., 'Fact:', 'Goal:'). It uses a provided map of prefixes to categorize each 
    line, returning a dictionary where keys are the categories and values are lists 
    of the corresponding statements. This tool is useful for converting an agent's 
    preliminary problem breakdown into a structured, machine-readable format for 
    further processing.

    Args:
        problem_text (str): The multi-line string containing the deconstructed problem 
                            components, with each component on a new line.
        component_prefixes (Dict[str, str]): A dictionary mapping category names 
                                             (e.g., 'facts') to the string prefixes 
                                             used to identify them in the text 
                                             (e.g., 'Fact:'). The keys become the 
                                             keys in the output dictionary.

    Returns:
        Dict[str, List[str]]: A dictionary where keys are the categories from 
                              `component_prefixes` (plus an 'unclassified' key for 
                              non-matching lines) and values are lists of the 
                              extracted text statements for each category.
    '''
    # 1. Initialize a result dictionary `structured_components`.
    # 2. For each `category_name` in the keys of the input `component_prefixes`, add it to `structured_components` with an empty list as its value.
    structured_components: Dict[str, List[str]] = {category_name: [] for category_name in component_prefixes.keys()}
    
    # 3. Add an 'unclassified' key to `structured_components` with an empty list.
    structured_components['unclassified'] = []

    # 4. Create a list of `(category_name, prefix)` tuples from `component_prefixes`.
    prefixes_list = list(component_prefixes.items())

    # 5. Sort this list in descending order based on the length of the `prefix` string.
    sorted_prefixes = sorted(prefixes_list, key=lambda item: len(item[1]), reverse=True)

    # 6. Split the input `problem_text` into a list of individual lines.
    lines = problem_text.splitlines()

    # 7. For each `line` in the list:
    for line in lines:
        # a. Strip leading/trailing whitespace from the `line`. If the result is empty, skip to the next line.
        stripped_line = line.strip()
        if not stripped_line:
            continue

        # b. Set a `matched` flag to `False`.
        matched = False

        # c. Iterate through the sorted list of prefixes:
        for category_name, prefix in sorted_prefixes:
            # i. If the line starts with the current `prefix`:
            if stripped_line.startswith(prefix):
                # - Extract the statement by slicing the string after the prefix, then strip whitespace.
                statement = stripped_line[len(prefix):].strip()
                # - Append the extracted statement to the list associated with the corresponding `category_name` in `structured_components`.
                structured_components[category_name].append(statement)
                # - Set `matched` to `True` and break the inner loop.
                matched = True
                break
        
        # d. If after checking all prefixes the `matched` flag is still `False`, append the original stripped line to the 'unclassified' list in `structured_components`.
        if not matched:
            structured_components['unclassified'].append(stripped_line)

    # 8. Return the `structured_components` dictionary.
    return structured_components


@tool
def structure_problem_components(problem_text: str, component_prefixes: Dict[str, str]) -> Dict[str, List[str]]:
    """Parses a semi-structured text block into a dictionary of categorized statements.

    Takes a multi-line string where each line is potentially prefixed with a label 
    (e.g., 'Fact:', 'Goal:'). It uses a provided map of prefixes to categorize each 
    line, returning a dictionary where keys are the categories and values are lists 
    of the corresponding statements. This tool is useful for converting an agent's 
    preliminary problem breakdown into a structured, machine-readable format for 
    further processing.
    """
    return structure_problem_components_impl(problem_text, component_prefixes)


# TEST CASES
try:
    import pytest

    def test_standard_problem_deconstruction():
        """Test with a standard mix of categories and unclassified lines from example call."""
        input_data = {
            'problem_text': 'Fact: Denali walks 16 dogs.\nFact: Nate walks 12 dogs.\nConstraint: Total dogs walked cannot exceed 30.\nThis is an unclassified comment.',
            'component_prefixes': {'facts': 'Fact:', 'constraints': 'Constraint:'}
        }
        expected_output = {
            'facts': ['Denali walks 16 dogs.', 'Nate walks 12 dogs.'],
            'constraints': ['Total dogs walked cannot exceed 30.'],
            'unclassified': ['This is an unclassified comment.']
        }
        assert structure_problem_components_impl(**input_data) == expected_output

    def test_whitespace_and_blank_lines():
        """Test input text with extra whitespace and blank lines from example call."""
        input_data = {
            'problem_text': '\n  Var: x = 10  \n\n  Var: y = 20\nGoal: Maximize x + y\n',
            'component_prefixes': {'variables': 'Var:', 'goals': 'Goal:'}
        }
        expected_output = {
            'variables': ['x = 10', 'y = 20'],
            'goals': ['Maximize x + y'],
            'unclassified': []
        }
        assert structure_problem_components_impl(**input_data) == expected_output

    def test_edge_case_empty_problem_text():
        """Test edge case: Empty problem_text string."""
        input_data = {
            'problem_text': '',
            'component_prefixes': {'facts': 'Fact:', 'constraints': 'Constraint:'}
        }
        expected_output = {
            'facts': [],
            'constraints': [],
            'unclassified': []
        }
        assert structure_problem_components_impl(**input_data) == expected_output

    def test_edge_case_empty_component_prefixes():
        """Test edge case: Empty component_prefixes dictionary."""
        input_data = {
            'problem_text': 'Line 1\nLine 2',
            'component_prefixes': {}
        }
        expected_output = {
            'unclassified': ['Line 1', 'Line 2']
        }
        assert structure_problem_components_impl(**input_data) == expected_output

    def test_edge_case_overlapping_prefixes():
        """Test edge case: Overlapping prefixes to ensure longest match is prioritized."""
        input_data = {
            'problem_text': 'Note: General info.\nNote Important: Critical info.',
            'component_prefixes': {'general_note': 'Note:', 'important_note': 'Note Important:'}
        }
        expected_output = {
            'general_note': ['General info.'],
            'important_note': ['Critical info.'],
            'unclassified': []
        }
        assert structure_problem_components_impl(**input_data) == expected_output

    def test_edge_case_prefix_is_entire_line():
        """Test edge case: A line that is only a prefix."""
        input_data = {
            'problem_text': 'Fact:',
            'component_prefixes': {'facts': 'Fact:'}
        }
        expected_output = {
            'facts': [''],
            'unclassified': []
        }
        assert structure_problem_components_impl(**input_data) == expected_output

    def test_mix_of_categories_and_unclassified():
        """Test with a standard mix of categories and unclassified lines from test cases."""
        input_data = {
            'problem_text': 'Fact: A is 5.\nConstraint: B > A\nNote: Check this later.',
            'component_prefixes': {'facts': 'Fact:', 'constraints': 'Constraint:'}
        }
        expected_output = {
            'facts': ['A is 5.'],
            'constraints': ['B > A'],
            'unclassified': ['Note: Check this later.']
        }
        assert structure_problem_components_impl(**input_data) == expected_output

except ImportError:
    # pytest not available, skip tests
    pass
