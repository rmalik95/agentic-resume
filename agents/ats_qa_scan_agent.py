import logging
import re

from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


logger = logging.getLogger(__name__)


class ATSQAScanAgent(BaseAgent):
    """Run a strict ATS-parser + recruiter QA scan on the tailored CV."""

    prompt_name = "ats_qa_scan"
    use_global_instructions = True

    def run(self, state: ResumeState) -> ResumeState:
        """Produce an 11-section QA scan and populate ats_verdict, ats_fixes.

        Example:
            state = ATSQAScanAgent().run(state)
        """
        tailored_cv = state.optimized_experience or state.resume_text
        cached_prefix = (
            "Stable context for this application:\n"
            f"Job description:\n{state.job_description}\n\n"
            f"Tailored CV:\n{tailored_cv}"
        )
        user_message = (
            "Review the tailored CV against the job description above. "
            "Return structured output under the numbered headings specified."
        )
        response = call_llm(
            self.system_prompt,
            user_message,
            max_tokens=1500,
            cached_prefix=cached_prefix,
            cache_system_prompt=True,
        )
        state.ats_qa_report = response.strip()

        # Extract ATS Compatibility Score for ats_verdict
        score_match = re.search(r"ATS Compatibility Score.*?(\d{1,3})\s*/\s*100", response, re.IGNORECASE | re.DOTALL)
        recruiter_match = re.search(r"Recruiter First-Impression Score.*?(\d{1,2})\s*/\s*10", response, re.IGNORECASE | re.DOTALL)
        ats_score = int(score_match.group(1)) if score_match else None
        recruiter_score = int(recruiter_match.group(1)) if recruiter_match else None

        if ats_score is not None:
            state.ats_verdict = f"ATS {ats_score}/100" + (
                f", Recruiter {recruiter_score}/10" if recruiter_score is not None else ""
            )
        else:
            state.ats_verdict = "See full QA report"

        # Extract section 10 (Rejection Risks) and section 11 (Exact Final Changes) for ats_fixes
        fixes_match = re.search(
            r"(?:11\.?\s+Exact Final Changes Required|Exact Final Changes Required)[:\s]*(.*?)(?=\n\n|\Z)",
            response,
            re.IGNORECASE | re.DOTALL,
        )
        rejection_match = re.search(
            r"(?:10\.?\s+Rejection Risks|Rejection Risks)[:\s]*(.*?)(?=\n\n1[01]\.|\Z)",
            response,
            re.IGNORECASE | re.DOTALL,
        )
        parts = []
        if rejection_match:
            parts.append(f"Rejection risks: {rejection_match.group(1).strip()}")
        if fixes_match:
            parts.append(f"Final changes: {fixes_match.group(1).strip()}")
        state.ats_fixes = "\n".join(parts) if parts else "See full QA report"

        return state
