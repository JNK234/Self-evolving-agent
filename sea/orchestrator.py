# ABOUTME: Orchestrator for the Self-Evolving Agent cycle
# ABOUTME: Coordinates Solver → Critic → Updater loop with automatic prompt evolution

import weave
from typing import List, Dict, Any, Callable
from sea.critic import Critic
from sea.updater import Updater


class CriticTunerOrchestrator:
    """Orchestrates the self-improvement cycle: solve → critique → update."""

    def __init__(
        self,
        critic: Critic,
        updater: Updater,
        threshold: float = 0.85
    ):
        """
        Initialize orchestrator.

        Args:
            critic: Critic instance for evaluation
            updater: Updater instance for prompt improvements
            threshold: Score threshold for triggering updates (default: 0.85)
        """
        self.critic = critic
        self.updater = updater
        self.threshold = threshold

    @weave.op()
    def run_cycle(
        self,
        problems: List[Dict[str, Any]],
        solver_func: Callable,
        current_prompt_obj: weave.StringPrompt
    ) -> Dict[str, Any]:
        """
        Run one SEA cycle: evaluate problems and potentially update prompt.

        Args:
            problems: List of problems (each with 'question' key)
            solver_func: Function to solve problems (question, prompt_obj) -> solution
            current_prompt_obj: Current solver prompt as weave.StringPrompt object

        Returns:
            Dictionary with cycle statistics and new_prompt (as text)
        """
        # Step 1: Solve all problems
        solutions = []
        for problem in problems:
            question = problem['question']
            solution = solver_func(question=question, prompt_obj=current_prompt_obj)
            solutions.append({
                'problem': question,
                'solution': solution
            })

        # Step 2: Evaluate each solution
        evaluations = []
        for item in solutions:
            evaluation = self.critic.evaluate_solution(
                problem=item['problem'],
                solution=item['solution'],
                current_prompt=current_prompt_obj.content
            )
            evaluations.append(evaluation)

        # Step 3: Pattern analysis - LLM extracts patterns from evaluations
        cycle_analysis = self.critic.evaluate_cycle(
            evaluations=evaluations,
            current_prompt=current_prompt_obj.content
        )

        aggregated = {
            'avg_score': cycle_analysis.get('overall_score', 0),
            'criterion_scores': cycle_analysis.get('criterion_scores', {}),
            'all_suggestions': cycle_analysis.get('suggestions', [])
        }

        # Step 4: Decide if update needed
        avg_score = aggregated['avg_score']
        updated = False
        new_prompt_text = current_prompt_obj.content

        if avg_score < self.threshold:
            # Apply suggestions to prompt (using text content)
            update_result = self.updater.apply_suggestions(
                current_prompt=current_prompt_obj.content,
                suggestions=aggregated['all_suggestions']
            )
            new_prompt_text = update_result['new_prompt']
            updated = True
            changes = update_result['changes_summary']
        else:
            changes = "Score above threshold - no update"

        # Step 5: Return cycle stats (new_prompt as text for caller to wrap)
        return {
            'avg_score': avg_score,
            'criterion_scores': aggregated['criterion_scores'],
            'updated': updated,
            'new_prompt': new_prompt_text,  # Return as text, caller will wrap in StringPrompt
            'changes_summary': changes,
            'num_problems': len(problems),
            'evaluations': evaluations
        }

    def _aggregate_evaluations(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate scores and suggestions from multiple evaluations.

        Args:
            evaluations: List of evaluation results from Critic

        Returns:
            Dictionary with aggregated metrics
        """
        if not evaluations:
            return {
                'avg_score': 0.0,
                'criterion_scores': {},
                'all_suggestions': []
            }

        # Calculate average overall score
        total_score = sum(e.get('overall_score', 0) for e in evaluations)
        avg_score = total_score / len(evaluations)

        # Aggregate criterion scores
        criterion_scores = {}
        for evaluation in evaluations:
            for criterion_id, score in evaluation.get('criterion_scores', {}).items():
                if criterion_id not in criterion_scores:
                    criterion_scores[criterion_id] = []
                criterion_scores[criterion_id].append(score)

        # Average per criterion
        avg_criterion_scores = {
            criterion_id: sum(scores) / len(scores)
            for criterion_id, scores in criterion_scores.items()
        }

        # Collect all suggestions
        all_suggestions = []
        for evaluation in evaluations:
            all_suggestions.extend(evaluation.get('suggestions', []))

        return {
            'avg_score': avg_score,
            'criterion_scores': avg_criterion_scores,
            'all_suggestions': all_suggestions
        }
