import re
import logging

from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


logger = logging.getLogger(__name__)


class ATSCheckerAgent(BaseAgent):
    """Evaluate ATS compatibility and return verdict plus fixes."""

    prompt_name = "ats_checker"

    def run(self, state: ResumeState) -> ResumeState:
        """Populate ATS verdict and issue summary.

        Example:
            state = ATSCheckerAgent().run(state)
        """
        if state.optimized_experience:
            user_message = (
                "Original full resume:\n"
                f"{state.resume_text}\n\n"
                "Optimized experience section (this replaces only the experience part):\n"
                f"{state.optimized_experience}\n\n"
                "Audit ATS compatibility for the resulting full resume after replacement. "
                "Do not treat omitted sections in the optimized snippet as globally missing "
                "if present in the original full resume. Return in the requested format only."
            )
        else:
            user_message = (
                f"Resume text:\n{state.resume_text}\n\n"
                "Return in the requested format only."
            )

        response = call_llm(self.system_prompt, user_message, max_tokens=700)

        verdict_match = re.search(r"VERDICT:\s*(.+)", response)
        summary_match = re.search(r"SUMMARY:\s*(.+)", response, flags=re.DOTALL)
        issues_match = re.search(r"ISSUES:\s*(.+?)\nVERDICT:", response, flags=re.DOTALL)

        if not verdict_match:
            logger.error("Failed to parse VERDICT from ATS response: %s", response)
            raise ValueError("ATSCheckerAgent response missing VERDICT field")

        state.ats_verdict = verdict_match.group(1).strip()
        issues_block = issues_match.group(1).strip() if issues_match else ""
        summary = summary_match.group(1).strip() if summary_match else ""
        state.ats_fixes = f"{issues_block}\n{summary}".strip()
        return state
