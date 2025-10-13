# ABOUTME: ToolIdeator generates deterministic tool specifications from identified patterns
# ABOUTME: Focuses on pure functions with clear algorithm sketches for implementation

import json
import weave
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from src.llm.llm_factory import get_llm
from dotenv import load_dotenv

load_dotenv()


class ToolIdeator:
    """Generates detailed, deterministic tool specifications from patterns."""

    def __init__(self, model: Optional[str] = None, use_config: bool = True):
        """
        Initialize tool ideator.

        Args:
            model: Optional explicit model name (overrides config)
            use_config: Whether to use config.yaml (default: True)
        """
        self.model_override = model
        self.use_config = use_config

        # Load tool ideation prompt
        with open("prompt_templates/sea/tool_ideation.txt", 'r') as f:
            self.ideation_prompt = f.read()

    @weave.op()
    def generate_specification(
        self,
        pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate detailed tool specification from an identified pattern.

        Args:
            pattern: Pattern dictionary from PatternRecognizer

        Returns:
            Complete tool specification with algorithm sketch
        """
        # Format pattern details for prompt
        pattern_details = self._format_pattern(pattern)

        # Create prompt with pattern data
        formatted_prompt = self.ideation_prompt.format(
            pattern_details=pattern_details
        )

        # LLM generates specification
        if self.use_config:
            llm = get_llm("tool_ideator", override_model=self.model_override)
        else:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model=self.model_override or "gemini-2.0-flash", temperature=0)

        messages = [
            SystemMessage(content=formatted_prompt),
            HumanMessage(content="Generate a detailed, deterministic tool specification for this pattern.")
        ]

        response = llm.invoke(messages)
        result = self._parse_json_response(response.content)

        # Validate determinism
        if 'tool_specification' in result:
            spec = result['tool_specification']
            is_deterministic = self._validate_determinism(spec)
            spec['deterministic_validated'] = is_deterministic

            if not is_deterministic:
                print(f"WARNING: Tool '{spec.get('name', 'unknown')}' may not be fully deterministic")

        return result

    @weave.op()
    def generate_specifications_batch(
        self,
        patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate specifications for multiple patterns.

        Args:
            patterns: List of pattern dictionaries

        Returns:
            List of tool specifications
        """
        specifications = []

        for pattern in patterns:
            try:
                spec_result = self.generate_specification(pattern)
                if 'tool_specification' in spec_result:
                    specifications.append(spec_result['tool_specification'])
            except Exception as e:
                print(f"Error generating specification for pattern {pattern.get('pattern_id', 'unknown')}: {e}")

        return specifications

    def _format_pattern(self, pattern: Dict[str, Any]) -> str:
        """
        Format pattern as text for prompt.

        Args:
            pattern: Pattern dictionary

        Returns:
            Formatted text description
        """
        formatted = f"Pattern ID: {pattern.get('pattern_id', 'N/A')}\n"
        formatted += f"Pattern Name: {pattern.get('pattern_name', 'N/A')}\n"
        formatted += f"Pattern Type: {pattern.get('pattern_type', 'N/A')}\n"
        formatted += f"Frequency: {pattern.get('frequency', 0)} occurrences\n"
        formatted += f"Description: {pattern.get('description', 'N/A')}\n"
        formatted += f"Abstraction Potential: {pattern.get('abstraction_potential', 0)}\n"
        formatted += f"Reasoning: {pattern.get('reasoning', 'N/A')}\n"

        if 'example_instances' in pattern:
            formatted += "\nExample Instances:\n"
            for i, example in enumerate(pattern['example_instances'], 1):
                formatted += f"  {i}. {example.get('excerpt', 'N/A')}\n"

        return formatted

    def _validate_determinism(self, spec: Dict[str, Any]) -> bool:
        """
        Basic validation that specification is deterministic.

        Args:
            spec: Tool specification dictionary

        Returns:
            True if appears deterministic, False otherwise
        """
        # Check deterministic flag
        if not spec.get('deterministic', False):
            return False

        # Check for non-deterministic keywords in description
        non_deterministic_keywords = [
            'llm', 'api call', 'random', 'datetime.now',
            'external service', 'database', 'file write'
        ]

        description = str(spec.get('detailed_description', '')).lower()
        algorithm = str(spec.get('algorithm_sketch', '')).lower()

        for keyword in non_deterministic_keywords:
            if keyword in description or keyword in algorithm:
                return False

        # Check that algorithm sketch exists and is non-empty
        if not spec.get('algorithm_sketch', '').strip():
            return False

        return True

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
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        return json.loads(text)
