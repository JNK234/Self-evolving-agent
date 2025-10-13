#!/usr/bin/env python3
"""
Unit tests for Daytona sandbox testing integration in ATC workflow.

Tests cover:
- Code generation without sandbox testing (existing behavior)
- Code generation with sandbox testing (new behavior)
- Retry mechanism on test failures
- Quality gate enforcement
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sea.tool_generator import ToolGenerator
from sea.daytona_manager import DaytonaManager


# Sample tool specification for testing
SAMPLE_SPEC = {
    "name": "test_tool",
    "description": "A test tool",
    "detailed_description": "Detailed test tool description",
    "category": "testing",
    "deterministic": True,
    "input_parameters": [
        {
            "name": "value",
            "type": "int",
            "description": "Test value",
            "required": True
        }
    ],
    "return_type": "int",
    "return_description": "Doubled value",
    "algorithm_sketch": "1. Multiply value by 2\n2. Return result",
    "example_calls": [
        {
            "scenario": "Double a number",
            "input": {"value": 5},
            "output": 10,
            "explanation": "5 * 2 = 10"
        }
    ],
    "test_cases": [
        {
            "description": "Test doubling",
            "input": {"value": 5},
            "expected_output": 10,
            "assertion": "assert test_tool(5) == 10"
        }
    ]
}


# Valid generated code for testing
VALID_TOOL_CODE = '''
"""Test tool"""
from langchain_core.tools import tool

@tool
def test_tool(value: int) -> int:
    """Double the input value."""
    return value * 2

# Tests
import pytest

def test_doubling():
    assert test_tool(value=5) == 10

def test_zero():
    assert test_tool(value=0) == 0
'''


class TestCodeGenerationWithoutSandbox:
    """Test existing behavior - code generation without sandbox testing."""

    def test_generate_code_without_testing(self):
        """Code generation should work without sandbox testing."""
        with patch('sea.tool_generator.ChatGoogleGenerativeAI') as mock_llm:
            # Mock LLM response (properly escaped JSON)
            mock_response = Mock()
            import json
            response_data = {
                "tool_code": VALID_TOOL_CODE,
                "tool_name": "test_tool",
                "dependencies": ["pytest"],
                "implementation_notes": "Simple doubling function"
            }
            mock_response.content = json.dumps(response_data)
            mock_llm.return_value.invoke.return_value = mock_response

            generator = ToolGenerator()
            result = generator.generate_code(
                specification=SAMPLE_SPEC,
                save_to_agent=None,
                test_before_save=False
            )

            assert result['tool_code'] is not None
            assert result['tool_name'] == 'test_tool'
            assert 'test_history' in result
            assert result['test_history'] == []
            assert result.get('test_attempts', 1) == 1

    def test_validation_only_without_sandbox(self):
        """Structural validation should still work without sandbox testing."""
        with patch('sea.tool_generator.ChatGoogleGenerativeAI') as mock_llm:
            # Mock LLM response with invalid code (missing @tool)
            mock_response = Mock()
            import json
            invalid_code = VALID_TOOL_CODE.replace('@tool', '')
            response_data = {
                "tool_code": invalid_code,
                "tool_name": "test_tool",
                "dependencies": ["pytest"]
            }
            mock_response.content = json.dumps(response_data)
            mock_llm.return_value.invoke.return_value = mock_response

            generator = ToolGenerator()
            result = generator.generate_code(
                specification=SAMPLE_SPEC,
                test_before_save=False
            )

            assert result['code_valid'] == False
            assert 'test_history' in result


class TestCodeGenerationWithSandbox:
    """Test new behavior - code generation with sandbox testing."""

    def test_generate_code_with_sandbox_success_first_attempt(self):
        """Code should be saved when tests pass on first attempt."""
        with patch('sea.tool_generator.ChatGoogleGenerativeAI') as mock_llm:
            # Mock LLM response
            import json
            mock_response = Mock()
            response_data = {
                "tool_code": VALID_TOOL_CODE,
                "tool_name": "test_tool",
                "dependencies": ["pytest"]
            }
            mock_response.content = json.dumps(response_data)
            mock_llm.return_value.invoke.return_value = mock_response

            # Mock DaytonaManager
            mock_daytona = Mock(spec=DaytonaManager)
            mock_daytona.run_code_with_tests.return_value = {
                'success': True,
                'exit_code': 0,
                'output': 'All tests passed',
                'execution_time': 2.5,
                'error': None
            }

            generator = ToolGenerator()
            result = generator.generate_code(
                specification=SAMPLE_SPEC,
                save_to_agent=None,  # Don't actually save
                test_before_save=True,
                daytona_manager=mock_daytona,
                max_test_attempts=3
            )

            # Verify results
            assert result['tool_code'] is not None
            assert result['test_attempts'] == 1
            assert len(result['test_history']) == 1
            assert result['test_history'][0]['success'] == True
            assert result['final_test_result']['success'] == True
            mock_daytona.run_code_with_tests.assert_called_once()

    def test_generate_code_requires_daytona_manager(self):
        """Should raise error if test_before_save=True but no daytona_manager."""
        generator = ToolGenerator()

        with pytest.raises(ValueError, match="daytona_manager required"):
            generator.generate_code(
                specification=SAMPLE_SPEC,
                test_before_save=True,
                daytona_manager=None
            )


class TestRetryMechanism:
    """Test retry mechanism when sandbox tests fail."""

    def test_retry_on_test_failure_then_success(self):
        """Code should retry with feedback when tests fail, then succeed."""
        with patch('sea.tool_generator.ChatGoogleGenerativeAI') as mock_llm:
            import json
            # First attempt: code that passes validation but fails tests
            first_code = VALID_TOOL_CODE.replace('return value * 2', 'return value')  # Wrong logic
            first_response = Mock()
            first_response.content = json.dumps({
                "tool_code": first_code,
                "tool_name": "test_tool",
                "dependencies": ["pytest"]
            })

            # Second attempt: corrected code
            second_response = Mock()
            second_response.content = json.dumps({
                "tool_code": VALID_TOOL_CODE,
                "tool_name": "test_tool",
                "dependencies": ["pytest"]
            })

            mock_llm_instance = Mock()
            mock_llm_instance.invoke.side_effect = [first_response, second_response]
            mock_llm.return_value = mock_llm_instance

            # Mock Daytona: first fails, second passes
            mock_daytona = Mock(spec=DaytonaManager)
            mock_daytona.run_code_with_tests.side_effect = [
                {
                    'success': False,
                    'exit_code': 1,
                    'output': 'Test failed: assertion error',
                    'execution_time': 2.0,
                    'error': None
                },
                {
                    'success': True,
                    'exit_code': 0,
                    'output': 'All tests passed',
                    'execution_time': 2.5,
                    'error': None
                }
            ]

            generator = ToolGenerator()
            result = generator.generate_code(
                specification=SAMPLE_SPEC,
                test_before_save=True,
                daytona_manager=mock_daytona,
                max_test_attempts=3
            )

            # Verify retry happened
            assert result['test_attempts'] == 2
            assert len(result['test_history']) == 2
            assert result['test_history'][0]['success'] == False
            assert result['test_history'][1]['success'] == True
            assert result['final_test_result']['success'] == True
            assert mock_daytona.run_code_with_tests.call_count == 2

    def test_max_retries_exceeded(self):
        """Tool should not be saved if all retry attempts fail."""
        with patch('sea.tool_generator.ChatGoogleGenerativeAI') as mock_llm:
            import json
            # Always return code that passes validation but fails tests
            bad_code = VALID_TOOL_CODE.replace('return value * 2', 'return "wrong"')
            mock_response = Mock()
            mock_response.content = json.dumps({
                "tool_code": bad_code,
                "tool_name": "test_tool",
                "dependencies": ["pytest"]
            })
            mock_llm.return_value.invoke.return_value = mock_response

            # Mock Daytona: always fail
            mock_daytona = Mock(spec=DaytonaManager)
            mock_daytona.run_code_with_tests.return_value = {
                'success': False,
                'exit_code': 1,
                'output': 'Tests failed',
                'execution_time': 2.0,
                'error': None
            }

            generator = ToolGenerator()
            result = generator.generate_code(
                specification=SAMPLE_SPEC,
                save_to_agent=None,
                test_before_save=True,
                daytona_manager=mock_daytona,
                max_test_attempts=3
            )

            # Verify max attempts reached
            assert result['test_attempts'] == 3
            assert len(result['test_history']) == 3
            assert all(not h['success'] for h in result['test_history'])
            assert result['save_status'] == 'test_failed'
            assert mock_daytona.run_code_with_tests.call_count == 3

    def test_feedback_included_in_retry(self):
        """Retry should include test failure feedback to LLM."""
        with patch('sea.tool_generator.ChatGoogleGenerativeAI') as mock_llm:
            import json
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance

            # Mock responses - code that passes validation but fails tests
            bad_code = VALID_TOOL_CODE.replace('return value * 2', 'return value')
            mock_response = Mock()
            mock_response.content = json.dumps({
                "tool_code": bad_code,
                "tool_name": "test_tool",
                "dependencies": ["pytest"]
            })
            mock_llm_instance.invoke.return_value = mock_response

            # Mock Daytona: always fail
            mock_daytona = Mock(spec=DaytonaManager)
            test_output = "AssertionError: expected 10 but got 5"
            mock_daytona.run_code_with_tests.return_value = {
                'success': False,
                'exit_code': 1,
                'output': test_output,
                'execution_time': 2.0,
                'error': None
            }

            generator = ToolGenerator()
            generator.generate_code(
                specification=SAMPLE_SPEC,
                test_before_save=True,
                daytona_manager=mock_daytona,
                max_test_attempts=2
            )

            # Check that second call includes feedback
            assert mock_llm_instance.invoke.call_count == 2
            second_call_messages = mock_llm_instance.invoke.call_args_list[1][0][0]
            feedback_message = second_call_messages[1].content
            assert test_output in feedback_message
            assert "test failures" in feedback_message.lower()


class TestQualityGate:
    """Test quality gate enforcement."""

    def test_validation_failed_prevents_testing(self):
        """Validation failure should prevent sandbox testing."""
        with patch('sea.tool_generator.ChatGoogleGenerativeAI') as mock_llm:
            # Return invalid code (missing @tool decorator)
            mock_response = Mock()
            mock_response.content = '''{"tool_code": "def test_tool(): pass", "tool_name": "test_tool"}'''
            mock_llm.return_value.invoke.return_value = mock_response

            mock_daytona = Mock(spec=DaytonaManager)

            generator = ToolGenerator()
            result = generator.generate_code(
                specification=SAMPLE_SPEC,
                test_before_save=True,
                daytona_manager=mock_daytona
            )

            # Daytona should not be called if validation fails
            mock_daytona.run_code_with_tests.assert_not_called()
            assert result['save_status'] == 'validation_failed'

    def test_save_only_after_passing_tests(self):
        """Tool should only be saved to disk after passing sandbox tests."""
        with patch('sea.tool_generator.ChatGoogleGenerativeAI') as mock_llm, \
             patch('sea.tool_generator.Path') as mock_path, \
             patch('sea.tool_generator.validate_generated_tool') as mock_validate:

            # Mock LLM
            mock_response = Mock()
            mock_response.content = f'''{{
                "tool_code": "{VALID_TOOL_CODE.replace('"', '\\"').replace('\n', '\\n')}",
                "tool_name": "test_tool",
                "dependencies": ["pytest"]
            }}'''
            mock_llm.return_value.invoke.return_value = mock_response

            # Mock validation (pass)
            mock_validate.return_value = {
                'syntax_valid': True,
                'has_tool_decorator': True,
                'has_tests': True
            }

            # Mock filesystem
            mock_file = Mock()
            mock_path.return_value.__truediv__.return_value = mock_file
            mock_path.return_value.mkdir = Mock()

            # Mock Daytona (tests pass)
            mock_daytona = Mock(spec=DaytonaManager)
            mock_daytona.run_code_with_tests.return_value = {
                'success': True,
                'exit_code': 0,
                'output': 'All tests passed',
                'execution_time': 2.5,
                'error': None
            }

            generator = ToolGenerator()
            result = generator.generate_code(
                specification=SAMPLE_SPEC,
                save_to_agent="test_agent",
                test_before_save=True,
                daytona_manager=mock_daytona
            )

            # Verify file was saved
            assert result['save_status'] == 'saved'
            mock_file.write_text.assert_called_once()

    def test_no_save_on_test_failure(self):
        """Tool should NOT be saved if sandbox tests fail."""
        with patch('sea.tool_generator.ChatGoogleGenerativeAI') as mock_llm, \
             patch('sea.tool_generator.Path') as mock_path:

            import json
            # Mock LLM - code that passes validation but fails tests
            bad_code = VALID_TOOL_CODE.replace('return value * 2', 'return "wrong"')
            mock_response = Mock()
            mock_response.content = json.dumps({
                "tool_code": bad_code,
                "tool_name": "test_tool",
                "dependencies": ["pytest"]
            })
            mock_llm.return_value.invoke.return_value = mock_response

            mock_file = Mock()
            mock_path.return_value.__truediv__.return_value = mock_file

            # Mock Daytona (tests fail)
            mock_daytona = Mock(spec=DaytonaManager)
            mock_daytona.run_code_with_tests.return_value = {
                'success': False,
                'exit_code': 1,
                'output': 'Tests failed',
                'execution_time': 2.0,
                'error': None
            }

            generator = ToolGenerator()
            result = generator.generate_code(
                specification=SAMPLE_SPEC,
                save_to_agent="test_agent",
                test_before_save=True,
                daytona_manager=mock_daytona,
                max_test_attempts=1
            )

            # Verify file was NOT saved
            assert result['save_status'] == 'test_failed'
            mock_file.write_text.assert_not_called()


class TestSandboxErrorHandling:
    """Test error handling for sandbox issues."""

    def test_sandbox_exception_handling(self):
        """Should handle exceptions from sandbox gracefully."""
        with patch('sea.tool_generator.ChatGoogleGenerativeAI') as mock_llm:
            import json
            mock_response = Mock()
            mock_response.content = json.dumps({
                "tool_code": VALID_TOOL_CODE,
                "tool_name": "test_tool",
                "dependencies": ["pytest"]
            })
            mock_llm.return_value.invoke.return_value = mock_response

            # Mock Daytona to raise exception
            mock_daytona = Mock(spec=DaytonaManager)
            mock_daytona.run_code_with_tests.side_effect = Exception("Sandbox connection failed")

            generator = ToolGenerator()
            result = generator.generate_code(
                specification=SAMPLE_SPEC,
                test_before_save=True,
                daytona_manager=mock_daytona,
                max_test_attempts=2
            )

            # Should retry on exception
            assert mock_daytona.run_code_with_tests.call_count == 2
            assert result['save_status'] == 'test_failed'
            assert len(result['test_history']) == 2
            assert all('error' in h for h in result['test_history'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
