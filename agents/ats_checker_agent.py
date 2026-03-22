import re

from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


class ATSCheckerAgent(BaseAgent):
    """Evaluate ATS compatibility and return verdict plus fixes."""

    prompt_name = "ats_checker"

    def run(self, state: ResumeState) -> ResumeState:
        """Populate ATS verdict and issue summary.

        Example:
            state = ATSCheckerAgent().run(state)
        """
        resume_text = state.optimized_experience or state.resume_text
        user_message = f"Resume text:\n{resume_text}\n\nReturn in the requested format only."
        response = call_llm(self.system_prompt, user_message, max_tokens=700)

        verdict_match = re.search(r"VERDICT:\s*(.+)", response)
        summary_match = re.search(r"SUMMARY:\s*(.+)", response)
        issues_match = re.search(r"ISSUES:\s*(.+?)\nVERDICT:", response, flags=re.DOTALL)

        state.ats_verdict = verdict_match.group(1).strip() if verdict_match else "Unknown"
        issues_block = issues_match.group(1).strip() if issues_match else ""
        summary = summary_match.group(1).strip() if summary_match else ""
        state.ats_fixes = f"{issues_block}\n{summary}".strip()
        return state
