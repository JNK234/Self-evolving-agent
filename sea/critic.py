# ABOUTME: Critic analyzes agent solutions and delegates pattern extraction to LLM
# ABOUTME: Uses prompt_templates/sea_critic_p_v2.txt for pattern-based analysis

import json
import weave
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()


class Critic:
    """Evaluates agent solutions using LLM-based pattern analysis."""

    def __init__(self, rubric_path: str = "src/agents/math_solver/rubric.json", model: str = "gemini-2.0-flash"):
        self.model = model
        with open(rubric_path, 'r') as f:
            self.rubric = json.load(f)

        # Load evaluation prompt (for individual solutions)
        with open("prompt_templates/sea/critic_eval.txt", 'r') as f:
            self.eval_prompt = f.read()

        # Load pattern analysis prompt (for cycle aggregation)
        with open("prompt_templates/sea/critic_pattern_v2.txt", 'r') as f:
            self.cycle_prompt = f.read()

    @weave.op()
    def evaluate_cycle(
        self,
        evaluations: List[Dict[str, Any]],
        current_prompt: str,
        rubric: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send all evaluations to LLM for pattern analysis.

        Args:
            evaluations: List of individual evaluation results
            current_prompt: Current agent prompt
            rubric: Optional rubric override

        Returns:
            LLM-generated pattern analysis with suggestions
        """
        rubric = rubric or self.rubric

        # Format rubric criteria
        criteria_text = "\n".join([
            f"{i+1}. {c['id']} (weight: {c['weight']})\n"
            f"   Description: {c['description']}\n"
            f"   Expected: {c['expected_pattern']}"
            for i, c in enumerate(rubric['criteria'])
        ])

        # Format evaluations as raw data - LLM will analyze
        traces_summary = self._format_evaluations(evaluations)

        # Create prompt with all data (use cycle prompt for pattern analysis)
        formatted_prompt = self.cycle_prompt.format(
            rubric_criteria=criteria_text,
            traces_summary=traces_summary,
            current_prompt=current_prompt
        )

        # LLM does pattern analysis
        llm = ChatGoogleGenerativeAI(model=self.model, temperature=0)
        messages = [
            SystemMessage(content=formatted_prompt),
            HumanMessage(content="Analyze the evaluation results and identify patterns.")
        ]

        response = llm.invoke(messages)
        result = self._parse_json_response(response.content)

        return result

    def _format_evaluations(self, evaluations: List[Dict[str, Any]]) -> str:
        """Format evaluations as raw data for LLM analysis."""
        summary = f"Total Evaluations: {len(evaluations)}\n\n"

        for i, eval_result in enumerate(evaluations, 1):
            summary += f"EVALUATION {i}:\n"
            summary += f"  Overall Score: {eval_result.get('overall_score', 'N/A')}\n"

            if 'criterion_scores' in eval_result:
                summary += f"  Criterion Scores:\n"
                for crit_id, score in eval_result['criterion_scores'].items():
                    summary += f"    - {crit_id}: {score}\n"

            if 'suggestions' in eval_result:
                summary += f"  Suggestions ({len(eval_result['suggestions'])}):\n"
                for sug in eval_result['suggestions']:
                    summary += f"    - Type: {sug.get('suggestion_type', 'N/A')}\n"
                    summary += f"      Details: {sug.get('details', 'N/A')}\n"
                    summary += f"      Reasoning: {sug.get('reasoning', 'N/A')}\n"

            summary += "\n"

        return summary

    @weave.op()
    def evaluate_solution(
        self,
        problem: str,
        solution: str,
        current_prompt: str,
        rubric: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate single solution against rubric.

        Args:
            problem: Original problem
            solution: Agent's solution
            current_prompt: Current agent prompt
            rubric: Optional rubric override

        Returns:
            Evaluation with scores and suggestions
        """
        rubric = rubric or self.rubric

        criteria_text = "\n".join([
            f"{i+1}. {c['id']} (weight: {c['weight']})\n"
            f"   Description: {c['description']}\n"
            f"   Expected: {c['expected_pattern']}"
            for i, c in enumerate(rubric['criteria'])
        ])

        # Use simple evaluation prompt for individual solutions
        formatted_prompt = self.eval_prompt.format(
            rubric_criteria=criteria_text,
            problem=problem,
            solution=solution
        )

        llm = ChatGoogleGenerativeAI(model=self.model, temperature=0)
        messages = [
            SystemMessage(content=formatted_prompt),
            HumanMessage(content=f"Problem: {problem}\n\nSolution:\n{solution}")
        ]

        response = llm.invoke(messages)
        evaluation = self._parse_json_response(response.content)

        return evaluation

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        text = response_text.strip()

        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        return json.loads(text)
