import logging

from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


logger = logging.getLogger(__name__)


class JDIntelligenceAgent(BaseAgent):
    """Extract deep recruiter-calibrated intelligence from the job description."""

    prompt_name = "jd_intelligence"

    def run(self, state: ResumeState) -> ResumeState:
        """Analyse the job description across 12 structured dimensions.

        Example:
            state = JDIntelligenceAgent().run(state)
        """
        cached_prefix = (
            "Stable context for this application:\n"
            f"Job description:\n{state.job_description}"
        )
        user_message = (
            "Analyse the job description provided and return structured output "
            "under the numbered headings specified."
        )
        response = call_llm(
            self.system_prompt,
            user_message,
            max_tokens=1500,
            cached_prefix=cached_prefix,
            cache_system_prompt=True,
        )
        state.jd_analysis = response.strip()
        return state
