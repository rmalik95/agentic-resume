import logging
import re

from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


logger = logging.getLogger(__name__)


class CVRewriteAgent(BaseAgent):
    """Rewrite the CV tailored to the target role using all prior agent analysis."""

    prompt_name = "cv_rewrite"
    use_global_instructions = True

    def run(self, state: ResumeState) -> ResumeState:
        """Produce a fully tailored CV rewrite with keyword map and gap notes.

        Example:
            state = CVRewriteAgent().run(state)
        """
        cached_prefix = (
            "Stable context for this application:\n"
            f"Source CV:\n{state.resume_text}\n\n"
            f"Job description:\n{state.job_description}"
        )
        context_lines = []
        if state.positioning_strategy:
            context_lines.append(
                f"Positioning strategy:\n{state.positioning_strategy}"
            )
        if state.jd_analysis:
            context_lines.append(
                f"JD intelligence analysis:\n{state.jd_analysis}"
            )
        if state.gap_analysis:
            context_lines.append(
                f"Gap analysis:\n{state.gap_analysis}"
            )
        context_block = "\n\n".join(context_lines)
        user_message = (
            f"{context_block}\n\n" if context_block else ""
        ) + (
            "Using the source CV, job description, and all analysis above, "
            "produce the tailored CV rewrite. "
            "Return structured output under the numbered headings specified."
        )
        response = call_llm(
            self.system_prompt,
            user_message,
            max_tokens=3000,
            cached_prefix=cached_prefix,
            cache_system_prompt=True,
        )
        state.optimized_experience = response.strip()
        # Extract all [bracket placeholders] as review flags
        state.review_flags = re.findall(r"\[([^\]]+)\]", response)
        return state
