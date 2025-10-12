# ABOUTME: ToolGenerator converts tool specifications into executable Python code
# ABOUTME: Uses LLM to generate code with @tool decorator and pytest test cases

import json
import weave
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()


class ToolGenerator:
    """Generates Python code from tool specifications."""

    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize tool generator.

        Args:
            model: LLM model name for code generation
        """
        self.model = model

        # Load code generation prompt
        with open("prompt_templates/sea/tool_code_generation.txt", 'r') as f:
            self.generation_prompt = f.read()

    @weave.op()
    def generate_code(
        self,
        specification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Python code from tool specification.

        Args:
            specification: Tool specification dictionary from ToolIdeator

        Returns:
            Dictionary with generated code:
            {
                "tool_code": str,  # Complete Python code with tool + tests
                "tool_name": str,
                "dependencies": List[str],
                "implementation_notes": str,
                "specification": Dict  # Original spec for reference
            }
        """
        # Format specification for prompt
        spec_text = self._format_specification(specification)

        # Create prompt with specification
        formatted_prompt = self.generation_prompt.format(
            specification=spec_text
        )

        # LLM generates code
        llm = ChatGoogleGenerativeAI(model=self.model, temperature=0)
        messages = [
            SystemMessage(content=formatted_prompt),
            HumanMessage(content="Generate the Python code for this tool specification. Return only the JSON object.")
        ]

        response = llm.invoke(messages)
        result = self._parse_json_response(response.content)

        # Add original specification for reference
        result['specification'] = specification

        # Validate generated code structure
        if 'tool_code' in result:
            is_valid = self._validate_code_structure(result['tool_code'])
            result['code_valid'] = is_valid

            if not is_valid:
                print(f"WARNING: Generated code for '{result.get('tool_name', 'unknown')}' may have structural issues")

        return result

    @weave.op()
    def generate_code_batch(
        self,
        specifications: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate code for multiple specifications.

        Args:
            specifications: List of tool specification dictionaries

        Returns:
            List of code generation results
        """
        generated_tools = []

        for spec in specifications:
            try:
                code_result = self.generate_code(spec)
                generated_tools.append(code_result)
            except Exception as e:
                print(f"Error generating code for specification: {e}")
                # Log failure but continue with other specs
                generated_tools.append({
                    "error": str(e),
                    "specification": spec,
                    "tool_name": spec.get('name', 'unknown'),
                    "tool_code": None
                })

        return generated_tools

    def _format_specification(self, spec: Dict[str, Any]) -> str:
        """
        Format specification as text for prompt.

        Args:
            spec: Tool specification dictionary

        Returns:
            Formatted text description
        """
        # Format the entire specification as readable text
        formatted = "TOOL SPECIFICATION:\n"
        formatted += f"Name: {spec.get('name', 'N/A')}\n"
        formatted += f"Description: {spec.get('description', 'N/A')}\n"
        formatted += f"Detailed Description: {spec.get('detailed_description', 'N/A')}\n"
        formatted += f"Category: {spec.get('category', 'N/A')}\n"
        formatted += f"Deterministic: {spec.get('deterministic', False)}\n\n"

        # Input parameters
        formatted += "INPUT PARAMETERS:\n"
        for param in spec.get('input_parameters', []):
            formatted += f"  - {param.get('name', 'N/A')} ({param.get('type', 'N/A')}): {param.get('description', 'N/A')}\n"
            if param.get('required'):
                formatted += f"    Required: True\n"
            if 'default' in param:
                formatted += f"    Default: {param['default']}\n"
            if param.get('constraints'):
                formatted += f"    Constraints: {param['constraints']}\n"

        formatted += f"\nRETURN TYPE: {spec.get('return_type', 'N/A')}\n"
        formatted += f"RETURN DESCRIPTION: {spec.get('return_description', 'N/A')}\n\n"

        # Algorithm sketch
        formatted += "ALGORITHM SKETCH:\n"
        formatted += spec.get('algorithm_sketch', 'N/A')
        formatted += "\n\n"

        # Example calls
        if 'example_calls' in spec:
            formatted += "EXAMPLE CALLS:\n"
            for example in spec['example_calls']:
                formatted += f"  Scenario: {example.get('scenario', 'N/A')}\n"
                formatted += f"  Input: {example.get('input', {})}\n"
                formatted += f"  Expected Output: {example.get('output', 'N/A')}\n"
                formatted += f"  Explanation: {example.get('explanation', 'N/A')}\n\n"

        # Edge cases
        if 'edge_cases' in spec:
            formatted += "EDGE CASES:\n"
            for edge_case in spec['edge_cases']:
                formatted += f"  - {edge_case.get('case', 'N/A')}: {edge_case.get('handling', 'N/A')}\n"
            formatted += "\n"

        # Test cases
        if 'test_cases' in spec:
            formatted += "TEST CASES:\n"
            for test in spec['test_cases']:
                formatted += f"  - {test.get('description', 'N/A')}\n"
                formatted += f"    Input: {test.get('input', {})}\n"
                formatted += f"    Expected: {test.get('expected_output', 'N/A')}\n"
                if 'assertion' in test:
                    formatted += f"    Assertion: {test['assertion']}\n"
                formatted += "\n"

        # Implementation notes
        if 'implementation_notes' in spec:
            formatted += "IMPLEMENTATION NOTES:\n"
            for note in spec['implementation_notes']:
                formatted += f"  - {note}\n"

        return formatted

    def _validate_code_structure(self, code: str) -> bool:
        """
        Basic validation of generated code structure.

        Args:
            code: Generated Python code

        Returns:
            True if code appears valid, False otherwise
        """
        # Check for required elements
        required_elements = [
            '@tool',  # Tool decorator
            'def ',   # Function definition
            'import pytest',  # Test framework
            'def test_'  # At least one test function
        ]

        for element in required_elements:
            if element not in code:
                print(f"  Missing required element: {element}")
                return False

        # Check for basic syntax issues (very basic check)
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError as e:
            print(f"  Syntax error in generated code: {e}")
            return False

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response.

        Args:
            response_text: Raw LLM response

        Returns:
            Parsed JSON dictionary
        """
        text = response_text.strip()

        # Handle markdown code blocks
        if text.startswith("```"):
            # Extract content between code fences
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
                # Remove language identifier if present
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response text: {text[:200]}...")
            raise
