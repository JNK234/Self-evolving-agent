'''
Tool: find_formula
Description: Finds and retrieves a standard mathematical or scientific formula from a curated knowledge base.
Category: retrieval
'''

# Standard library imports
from typing import List, Dict, Any

# Third-party imports
from langchain_core.tools import tool

# Step 1: Define the internal, static knowledge base (KB)
_FORMULA_KNOWLEDGE_BASE = [
    {
        'name': 'Pythagorean Theorem',
        'formula_str': 'a**2 + b**2 = c**2',
        'variables': {
            'a': 'Length of one leg of the right triangle',
            'b': 'Length of the other leg of the right triangle',
            'c': 'Length of the hypotenuse'
        },
        'domain': 'Geometry',
        'search_tags': ['pythagorean', 'theorem', 'right', 'triangle', 'geometry', 'hypotenuse', 'legs']
    },
    {
        'name': 'Volume of a Cylinder',
        'formula_str': 'V = pi * r**2 * h',
        'variables': {
            'V': 'Volume',
            'pi': 'The constant Pi (~3.14159)',
            'r': 'Radius of the circular base',
            'h': 'Height of the cylinder'
        },
        'domain': 'Geometry',
        'search_tags': ['volume', 'cylinder', 'geometry', '3d', 'pi', 'radius', 'height']
    },
    {
        'name': 'Area of a Circle',
        'formula_str': 'A = pi * r**2',
        'variables': {
            'A': 'Area',
            'pi': 'The constant Pi (~3.14159)',
            'r': 'Radius of the circle'
        },
        'domain': 'Geometry',
        'search_tags': ['area', 'circle', 'geometry', '2d', 'pi', 'radius']
    },
    {
        'name': 'Quadratic Formula',
        'formula_str': 'x = (-b +/- sqrt(b**2 - 4*a*c)) / (2*a)',
        'variables': {
            'x': 'The roots of the quadratic equation',
            'a': 'Coefficient of the x^2 term',
            'b': 'Coefficient of the x term',
            'c': 'The constant term (intercept)'
        },
        'domain': 'Algebra',
        'search_tags': ['quadratic', 'formula', 'equation', 'algebra', 'roots', 'x']
    },
    {
        'name': 'Sine Wave Function',
        'formula_str': 'y = a * sin(b * x + c) + d',
        'variables': {
            'y': 'The output value',
            'a': 'Amplitude (vertical stretch)',
            'b': 'Frequency (horizontal compression)',
            'c': 'Phase shift (horizontal shift)',
            'd': 'Vertical shift (midline)'
        },
        'domain': 'Trigonometry',
        'search_tags': ['sine', 'wave', 'function', 'trigonometry', 'sin', 'amplitude', 'frequency', 'phase', 'shift']
    },
    {
        'name': 'Area of a Triangle',
        'formula_str': 'A = 0.5 * b * h',
        'variables': {
            'A': 'Area',
            'b': 'Length of the base',
            'h': 'Height of the triangle'
        },
        'domain': 'Geometry',
        'search_tags': ['area', 'triangle', 'geometry', 'base', 'height']
    }
]

def find_formula_impl(keywords: List[str]) -> List[Dict[str, Any]]:
    '''
    Finds and retrieves a standard mathematical or scientific formula from a curated knowledge base.

    Searches a pre-defined, static knowledge base of vetted formulas using a list of keywords.
    This tool ensures accuracy and avoids LLM hallucination by retrieving exact, pre-verified
    formula definitions. It returns structured data including the formula string, variable
    definitions, and domain. It is a lookup tool, not a calculator.

    Args:
        keywords (List[str]): A list of search terms used to identify the desired formula.
                              More specific keywords yield better results.

    Returns:
        List[Dict[str, any]]: A list of dictionaries, each representing a formula that matches
                               the keywords. The list is sorted by relevance score in descending
                               order. Returns an empty list if no match is found.
    '''
    # Step 3: Validate that the keywords list is not empty.
    if not keywords or not isinstance(keywords, list):
        return []

    # Step 4: Convert all strings in the input keywords list to lowercase.
    try:
        processed_keywords = [str(k).lower() for k in keywords]
    except Exception:
        # Handle cases where list items are not convertible to string
        return []

    # Step 5: Initialize an empty list `results`.
    results = []

    # Step 6: Iterate through each formula_object in the KB.
    for formula_object in _FORMULA_KNOWLEDGE_BASE:
        # a. Initialize relevance_score = 0.
        relevance_score = 0
        # b. For each keyword in the processed input keywords:
        for keyword in processed_keywords:
            # i. If the keyword is present in the formula_object's search_tags...
            if keyword in formula_object['search_tags']:
                # ...increment relevance_score by 1.
                relevance_score += 1

        # c. If relevance_score > 0:
        if relevance_score > 0:
            # i. Create a result dictionary.
            result_entry = {
                'name': formula_object['name'],
                'formula_str': formula_object['formula_str'],
                'variables': formula_object['variables'],
                'domain': formula_object['domain'],
                'relevance_score': relevance_score
            }
            # ii. Append this dictionary to the results list.
            results.append(result_entry)

    # Step 7: Sort the results list in descending order based on relevance_score.
    results.sort(key=lambda x: x['relevance_score'], reverse=True)

    # Step 8: Return the sorted results list.
    return results


@tool
def find_formula(keywords: List[str]) -> List[Dict[str, Any]]:
    """Finds and retrieves a standard mathematical or scientific formula from a curated knowledge base.

    Args:
        keywords (List[str]): A list of search terms used to identify the desired formula.
                              More specific keywords yield better results.

    Returns:
        List[Dict[str, any]]: A list of dictionaries, each representing a formula that matches
                               the keywords. The list is sorted by relevance score in descending
                               order. Returns an empty list if no match is found.
    """
    return find_formula_impl(keywords)


# TEST CASES
try:
    import pytest

    def test_pythagorean_theorem_high_relevance():
        '''Test for an exact, high-relevance match.'''
        result = find_formula_impl(keywords=['pythagorean', 'theorem', 'right', 'triangle'])
        assert len(result) > 0
        assert result[0]['name'] == 'Pythagorean Theorem'
        assert result[0]['relevance_score'] == 4

    def test_volume_of_cylinder():
        '''Test finding the formula for the volume of a cylinder.'''
        result = find_formula_impl(keywords=['volume', 'cylinder'])
        expected = [{
            'name': 'Volume of a Cylinder',
            'formula_str': 'V = pi * r**2 * h',
            'variables': {
                'V': 'Volume',
                'pi': 'The constant Pi (~3.14159)',
                'r': 'Radius of the circular base',
                'h': 'Height of the cylinder'
            },
            'domain': 'Geometry',
            'relevance_score': 2
        }]
        assert result == expected

    def test_no_match_scenario():
        '''Test for a search that does not exist in the knowledge base.'''
        result = find_formula_impl(keywords=['special', 'relativity'])
        assert result == []

    def test_edge_case_empty_keyword_list():
        '''Test edge case: Empty keyword list should return an empty list.'''
        result = find_formula_impl(keywords=[])
        assert result == []

    def test_case_insensitivity():
        '''Test edge case: Keywords with mixed casing should match.'''
        result = find_formula_impl(keywords=['VOLUME', 'CYLINDER'])
        assert len(result) > 0
        assert result[0]['name'] == 'Volume of a Cylinder'
        assert result[0]['relevance_score'] == 2

    def test_single_keyword_match():
        '''Test for a single keyword match.'''
        result = find_formula_impl(keywords=['sine'])
        assert len(result) > 0
        assert result[0]['name'] == 'Sine Wave Function'
        assert result[0]['relevance_score'] == 1

    def test_ambiguous_keywords_sorting():
        '''Test edge case: Ambiguous keywords matching multiple formulas are sorted by relevance.'''
        result = find_formula_impl(keywords=['area', 'triangle', 'base'])
        # 'Area of a Triangle' should have a score of 3 ('area', 'triangle', 'base')
        # 'Area of a Circle' should have a score of 1 ('area')
        # 'Pythagorean Theorem' should have a score of 1 ('triangle')
        assert len(result) >= 3
        assert result[0]['name'] == 'Area of a Triangle'
        assert result[0]['relevance_score'] == 3
        # Check that the next results have lower scores
        assert result[1]['relevance_score'] < 3

    def test_invalid_input_type():
        '''Test that non-list input is handled gracefully.'''
        # The tool should not raise an error, but return an empty list.
        assert find_formula_impl(keywords="not a list") == []
        assert find_formula_impl(keywords=None) == []
        assert find_formula_impl(keywords=[1, 2, 3]) == [] # Non-string items

except ImportError:
    # pytest not available, skip tests
    pass
