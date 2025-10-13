# ABOUTME: PatternRecognizer analyzes traces to identify repetitive operations for tool creation
# ABOUTME: Domain-agnostic design works for math, code, data processing, or any agent domain

import json
import weave
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from src.llm.llm_factory import get_llm
from dotenv import load_dotenv

load_dotenv()


class PatternRecognizer:
    """Identifies repetitive patterns in agent traces for tool creation opportunities."""

    def __init__(self, model: Optional[str] = None, use_config: bool = True):
        """
        Initialize pattern recognizer.

        Args:
            model: Optional explicit model name (overrides config)
            use_config: Whether to use config.yaml (default: True)
        """
        self.model_override = model
        self.use_config = use_config

        # Load pattern recognition prompt
        with open("prompt_templates/sea/pattern_recognizer.txt", 'r') as f:
            self.recognition_prompt = f.read()

    @weave.op()
    def identify_patterns(
        self,
        traces: List[Dict[str, Any]],
        min_frequency: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze traces to identify repetitive patterns and propose tools.

        Args:
            traces: List of agent execution traces
            min_frequency: Minimum occurrences for pattern detection

        Returns:
            Dictionary with patterns_identified, tool_proposals, and meta_analysis
        """
        # Format traces for LLM analysis
        traces_summary = self._format_traces(traces)

        # Create prompt with traces data
        formatted_prompt = self.recognition_prompt.format(
            traces_summary=traces_summary
        )

        # LLM analyzes patterns
        if self.use_config:
            llm = get_llm("pattern_recognizer", override_model=self.model_override)
        else:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model=self.model_override or "gemini-2.0-flash", temperature=0)

        messages = [
            SystemMessage(content=formatted_prompt),
            HumanMessage(content=f"Analyze these {len(traces)} traces and identify patterns that appear at least {min_frequency} times.")
        ]

        response = llm.invoke(messages)
        result = self._parse_json_response(response.content)

        # Filter patterns by minimum frequency
        if 'patterns_identified' in result:
            result['patterns_identified'] = [
                p for p in result['patterns_identified']
                if p.get('frequency', 0) >= min_frequency
            ]

        return result

    def _format_traces(self, traces: List[Dict[str, Any]]) -> str:
        """
        Format traces as domain-neutral text summary for LLM analysis.

        Args:
            traces: List of trace dictionaries

        Returns:
            Formatted text summary of all traces
        """
        summary = f"Total Traces: {len(traces)}\n\n"

        for i, trace in enumerate(traces, 1):
            summary += f"TRACE {i}:\n"

            # Extract trace ID if available
            trace_id = trace.get('trace_id', trace.get('id', f'trace_{i}'))
            summary += f"  ID: {trace_id}\n"

            # Problem/question
            if 'problem' in trace:
                summary += f"  Problem: {trace['problem'][:200]}...\n"
            elif 'question' in trace:
                summary += f"  Question: {trace['question'][:200]}...\n"

            # Execution flow (if available)
            if 'execution_flow' in trace:
                summary += f"  Execution Flow:\n"
                for step in trace['execution_flow']:
                    step_type = step.get('type', 'unknown')
                    step_desc = step.get('description', '')
                    summary += f"    - {step_type}: {step_desc}\n"

            # Tools invoked
            if 'tools_invoked' in trace:
                tools = trace['tools_invoked']
                summary += f"  Tools Used: {', '.join(tools) if tools else 'None'}\n"

            # Solution/result (truncated)
            if 'solution' in trace:
                solution = str(trace['solution'])[:300]
                summary += f"  Solution: {solution}...\n"
            elif 'final_result' in trace:
                result = str(trace['final_result'])[:300]
                summary += f"  Result: {result}...\n"

            # Metadata
            if 'metadata' in trace:
                meta = trace['metadata']
                if 'num_steps' in meta:
                    summary += f"  Steps: {meta['num_steps']}\n"

            summary += "\n"

        return summary

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
