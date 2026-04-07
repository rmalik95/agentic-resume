import logging

from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


logger = logging.getLogger(__name__)


class PositioningStrategyAgent(BaseAgent):
    """Determine the best CV positioning strategy before any rewriting begins."""

    prompt_name = "positioning_strategy"

    def run(self, state: ResumeState) -> ResumeState:
        """Analyse CV and JD to produce a positioning strategy.

        Example:
            state = PositioningStrategyAgent().run(state)
        """
        cached_prefix = (
            "Stable context for this application:\n"
            f"Resume text:\n{state.resume_text}\n\n"
            f"Job description:\n{state.job_description}"
        )
        user_message = (
            "Based on the CV and job description above, "
            "determine the best positioning strategy. "
            "Return structured output under the numbered headings specified."
        )
        response = call_llm(
            self.system_prompt,
            user_message,
            max_tokens=900,
            cached_prefix=cached_prefix,
            cache_system_prompt=True,
        )
        state.positioning_strategy = response.strip()
        return state
