# ABOUTME: ToolGenerator converts tool specifications into executable Python code
# ABOUTME: Uses LLM to generate code with @tool decorator and pytest test cases

import json
import weave
from pathlib import Path
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from src.agents.shared.tool_loader import validate_generated_tool
from src.llm.llm_factory import get_llm
from dotenv import load_dotenv

load_dotenv()


class ToolGenerator:
    """Generates Python code from tool specifications."""

    def __init__(self, model: Optional[str] = None, use_config: bool = True):
        """
        Initialize tool generator.

        Args:
            model: Optional explicit model name (overrides config)
            use_config: Whether to use config.yaml (default: True)
        """
        self.model_override = model
        self.use_config = use_config

        # Load code generation prompt
        with open("prompt_templates/sea/tool_code_generation.txt", 'r') as f:
            self.generation_prompt = f.read()

    @weave.op()
    def generate_code(
        self,
        specification: Dict[str, Any],
        save_to_agent: str = None,
        test_before_save: bool = False,
        daytona_manager = None,
        max_test_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Generate Python code from tool specification with optional sandbox testing.

        Args:
            specification: Tool specification dictionary from ToolIdeator
            save_to_agent: Optional agent name to save generated tool to (e.g., "math_solver")
            test_before_save: If True, test code in Daytona sandbox before saving
            daytona_manager: DaytonaManager instance for sandbox testing (required if test_before_save=True)
            max_test_attempts: Maximum number of regeneration attempts if tests fail (default: 3)

        Returns:
            Dictionary with generated code:
            {
                "tool_code": str,  # Complete Python code with tool + tests
                "tool_name": str,
                "dependencies": List[str],
                "implementation_notes": str,
                "specification": Dict,  # Original spec for reference
                "file_path": str,  # If saved to disk
                "save_status": str,  # "saved", "test_failed", "validation_failed", or "not_saved"
                "test_attempts": int,  # Number of generation attempts
                "test_history": List[Dict],  # Test results for each attempt
                "final_test_result": Dict  # Final sandbox test result (if tested)
            }
        """
        # Validate parameters
        if test_before_save and not daytona_manager:
            raise ValueError("daytona_manager required when test_before_save=True")

        result = None
        test_history = []

        # Attempt generation with optional retry on test failure
        for attempt in range(1, max_test_attempts + 1):
            print(f"\n{'='*60}")
            print(f"Generation Attempt {attempt}/{max_test_attempts}")
            print(f"{'='*60}")

            # Generate code (with feedback from previous attempt if applicable)
            result = self._generate_code_attempt(
                specification=specification,
                previous_attempt=result if attempt > 1 else None
            )

            # Add original specification for reference
            result['specification'] = specification
            result['test_attempts'] = attempt

            # Validate generated code structure
            if 'tool_code' in result:
                is_valid = self._validate_code_structure(result['tool_code'])
                result['code_valid'] = is_valid

                if not is_valid:
                    print(f"⚠️  WARNING: Code structure validation failed")
                    result['save_status'] = 'validation_failed'
                    result['test_history'] = test_history
                    return result

            # If testing enabled, run sandbox tests before saving
            if test_before_save and result.get('tool_code'):
                print(f"\n🧪 Testing generated code in Daytona sandbox...")

                try:
                    test_result = daytona_manager.run_code_with_tests(
                        tool_code=result['tool_code'],
                        dependencies=result.get('dependencies', ['pytest'])
                    )

                    # Track test history
                    test_history.append({
                        'attempt': attempt,
                        'success': test_result['success'],
                        'exit_code': test_result['exit_code'],
                        'execution_time': test_result['execution_time'],
                        'output': test_result['output'],
                        'error': test_result.get('error')
                    })

                    if test_result['success']:
                        print(f"✓ Tests PASSED on attempt {attempt}")
                        result['final_test_result'] = test_result
                        result['test_history'] = test_history
                        break  # Success - exit retry loop
                    else:
                        print(f"✗ Tests FAILED on attempt {attempt}")
                        print(f"   Exit code: {test_result['exit_code']}")

                        if attempt < max_test_attempts:
                            print(f"   Retrying with error feedback...")
                            # Store failure info for next attempt
                            result['previous_test_output'] = test_result['output']
                        else:
                            print(f"   Max attempts reached - not saving tool")
                            result['save_status'] = 'test_failed'
                            result['final_test_result'] = test_result
                            result['test_history'] = test_history
                            return result

                except Exception as e:
                    print(f"✗ Sandbox testing error: {e}")
                    test_history.append({
                        'attempt': attempt,
                        'success': False,
                        'error': str(e)
                    })

                    if attempt >= max_test_attempts:
                        result['save_status'] = 'test_failed'
                        result['test_history'] = test_history
                        return result
            else:
                # No testing required - exit after first successful generation
                break

        # Add test history to result
        result['test_history'] = test_history if test_history else []

        # Save to disk if requested (only reached if tests passed or testing disabled)
        if save_to_agent and result.get('tool_code'):
            result = self.save_generated_tool(result, save_to_agent)

        return result

    def _generate_code_attempt(
        self,
        specification: Dict[str, Any],
        previous_attempt: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate code for a single attempt, optionally incorporating feedback from previous failure.

        Args:
            specification: Tool specification dictionary
            previous_attempt: Previous generation result with test failure info (for retry)

        Returns:
            Dictionary with generated code
        """
        # Format specification for prompt
        spec_text = self._format_specification(specification)

        # Create prompt with specification
        formatted_prompt = self.generation_prompt.format(
            specification=spec_text
        )

        # Build messages for LLM
        if self.use_config:
            llm = get_llm("tool_generator", override_model=self.model_override)
        else:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model=self.model_override or "gemini-2.0-flash", temperature=0)

        messages = [SystemMessage(content=formatted_prompt)]

        # Add feedback from previous attempt if retrying
        if previous_attempt and previous_attempt.get('previous_test_output'):
            feedback_msg = f"""The previous code generation had test failures. Here is the test output:

{previous_attempt['previous_test_output']}

Please analyze the test failures and generate improved code that will pass all tests. Focus on fixing the specific issues identified in the test output."""
            messages.append(HumanMessage(content=feedback_msg))
        else:
            messages.append(HumanMessage(content="Generate the Python code for this tool specification. Return only the JSON object."))

        # Generate code
        response = llm.invoke(messages)
        result = self._parse_json_response(response.content)

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

    @weave.op()
    def save_generated_tool(
        self,
        code_result: Dict[str, Any],
        agent_name: str
    ) -> Dict[str, Any]:
        """
        Save generated tool to agent's generated/ directory.

        Args:
            code_result: Output from generate_code()
            agent_name: Target agent (e.g., "math_solver")

        Returns:
            Updated result dict with file_path and save_status
        """
        tool_name = code_result.get("tool_name", "unknown_tool")
        output_dir = Path(f"src/agents/{agent_name}/tools/generated")

        # Create directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        file_path = output_dir / f"{tool_name}.py"

        # Validate before saving
        validation = validate_generated_tool(code_result["tool_code"])

        if not all(validation.values()):
            code_result["save_status"] = "validation_failed"
            code_result["validation"] = validation
            print(f"✗ Validation failed for {tool_name} - not saving to disk")
            for check, passed in validation.items():
                if not passed:
                    print(f"  - {check}: FAIL")
            return code_result

        # Save to disk
        try:
            file_path.write_text(code_result["tool_code"])
            code_result["file_path"] = str(file_path)
            code_result["save_status"] = "saved"
            print(f"✓ Saved {tool_name} to {file_path}")
        except Exception as e:
            code_result["save_status"] = "save_error"
            code_result["save_error"] = str(e)
            print(f"✗ Error saving {tool_name}: {e}")

        return code_result

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
