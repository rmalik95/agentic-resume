import logging
import re

from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


logger = logging.getLogger(__name__)


class MatchScoreAgent(BaseAgent):
    """Score resume against job description and extract ATS keyword gaps."""

    prompt_name = "match_score"

    def run(self, state: ResumeState) -> ResumeState:
        """Populate before/after score, missing keywords, and analysis.

        Example:
            state = MatchScoreAgent().run(state)
        """
        resume_text = state.optimized_experience or state.resume_text
        user_message = (
            f"Resume:\n{resume_text}\n\n"
            f"Job description:\n{state.job_description}\n\n"
            "Return exactly the required output format."
        )
        response = call_llm(self.system_prompt, user_message, max_tokens=500)

        score_match = re.search(r"SCORE:\s*(\d{1,3})", response)
        keywords_match = re.search(r"KEYWORDS:\s*(.+)", response)
        gap_match = re.search(r"GAP:\s*(.+)", response)
        analysis_match = re.search(r"ANALYSIS:\s*(.+)", response, flags=re.DOTALL)

        if not score_match:
            logger.error("Failed to parse SCORE from MatchScoreAgent response: %s", response)
            raise ValueError("MatchScoreAgent response missing SCORE field")

        score_value = int(score_match.group(1))
        keywords = []
        if keywords_match:
            keywords = [item.strip() for item in keywords_match.group(1).split(",") if item.strip()]

        gap = gap_match.group(1).strip() if gap_match else ""
        analysis = analysis_match.group(1).strip() if analysis_match else ""
        state.missing_keywords = keywords[:5]
        state.score_analysis = f"{gap}\n{analysis}".strip()

        if state.optimized_experience and state.match_score_before is not None:
            state.match_score_after = score_value
        elif state.match_score_before is None:
            state.match_score_before = score_value
        else:
            state.match_score_after = score_value

        return state
