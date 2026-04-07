import logging

from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


logger = logging.getLogger(__name__)


class GapAnalysisAgent(BaseAgent):
    """Produce a brutally honest gap analysis comparing the CV against the target role."""

    prompt_name = "gap_analysis"

    def run(self, state: ResumeState) -> ResumeState:
        """Compare CV to JD and produce a 13-section gap analysis.

        Example:
            state = GapAnalysisAgent().run(state)
        """
        cached_prefix = (
            "Stable context for this application:\n"
            f"Resume text:\n{state.resume_text}\n\n"
            f"Job description:\n{state.job_description}"
        )
        context_lines = []
        if state.positioning_strategy:
            context_lines.append(
                f"Positioning strategy already determined:\n{state.positioning_strategy}"
            )
        if state.jd_analysis:
            context_lines.append(
                f"JD intelligence analysis already completed:\n{state.jd_analysis}"
            )
        context_block = "\n\n".join(context_lines)
        user_message = (
            f"{context_block}\n\n" if context_block else ""
        ) + (
            "Based on the CV and job description above, produce a brutally honest gap analysis. "
            "Return structured output under the numbered headings specified."
        )
        response = call_llm(
            self.system_prompt,
            user_message,
            max_tokens=1500,
            cached_prefix=cached_prefix,
            cache_system_prompt=True,
        )
        state.gap_analysis = response.strip()
        return state
