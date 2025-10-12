# ABOUTME: Updater applies pattern-based suggestions to prompts
# ABOUTME: Uses prompt_templates/sea_updater_p_v2.txt for surgical prompt modifications

import weave
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()


class Updater:
    """Applies LLM-suggested improvements to agent prompts."""

    def __init__(self, model: str = "gemini-2.0-flash", max_suggestions: int = 3):
        self.model = model
        self.max_suggestions = max_suggestions

        # Load pattern-based updater prompt
        with open("prompt_templates/sea/updater_v2.txt", 'r') as f:
            self.prompt_template = f.read()

    @weave.op()
    def apply_suggestions(
        self,
        current_prompt: str,
        suggestions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Apply pattern-based suggestions to prompt.

        Args:
            current_prompt: Current solver agent prompt
            suggestions: Pattern-based suggestions from Critic

        Returns:
            Dictionary with new_prompt and changes_summary
        """
        if not suggestions:
            return {
                "new_prompt": current_prompt,
                "changes_summary": "No suggestions to apply"
            }

        # Select top N suggestions by priority
        selected = self._select_suggestions(suggestions)

        # Format suggestions for LLM
        suggestions_text = "\n\n".join([
            f"Suggestion {i+1}:\n"
            f"Type: {s.get('suggestion_type', 'N/A')}\n"
            f"Pattern Addressed: {s.get('pattern_addressed', 'N/A')}\n"
            f"Details: {s.get('details', 'N/A')}\n"
            f"Reasoning: {s.get('reasoning', 'N/A')}"
            for i, s in enumerate(selected)
        ])

        # Format trace patterns if available
        trace_patterns = "See suggestions above for pattern evidence."

        # Create update prompt
        formatted_prompt = self.prompt_template.format(
            current_prompt=current_prompt,
            suggestions=suggestions_text,
            trace_patterns=trace_patterns
        )

        # Call LLM to apply changes
        llm = ChatGoogleGenerativeAI(model=self.model, temperature=0)
        messages = [
            SystemMessage(content=formatted_prompt),
            HumanMessage(content="Apply the suggestions to the prompt.")
        ]

        response = llm.invoke(messages)
        new_prompt = response.content.strip()

        # Generate summary
        changes_summary = f"Applied {len(selected)} suggestions: " + ", ".join([
            s.get('suggestion_type', 'UNKNOWN') for s in selected
        ])

        return {
            "new_prompt": new_prompt,
            "changes_summary": changes_summary,
            "applied_suggestions": selected
        }

    def _select_suggestions(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select top N suggestions by priority."""
        # Sort by priority field (high > medium > low)
        priority_order = {"high": 1, "medium": 2, "low": 3}

        sorted_suggestions = sorted(
            suggestions,
            key=lambda s: priority_order.get(s.get('priority', 'low'), 99)
        )

        return sorted_suggestions[:self.max_suggestions]
