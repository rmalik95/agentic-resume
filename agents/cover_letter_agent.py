import re

import requests

from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


class CoverLetterAgent(BaseAgent):
    prompt_name = "cover_letter"

    def _fetch_company_context(self, url: str) -> str:
        """Fetch plain text from a URL, capped at 3000 chars."""
        try:
            resp = requests.get(
                url,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:3000]
        except Exception as exc:
            print(f"  Company URL fetch failed: {exc} - continuing without it")
            return ""

    def run(self, state: ResumeState) -> ResumeState:
        company_context = ""
        if state.company_url:
            print(f"  Fetching company context from {state.company_url}...")
            company_context = self._fetch_company_context(state.company_url)
            state.company_context = company_context

        context_block = (
            f"\n\nCompany context (from their website):\n{company_context}"
            if company_context
            else ""
        )
        user_message = f"""
Resume:\n{state.optimized_experience or state.resume_text}
Job description:\n{state.job_description}
{context_block}
Write the cover letter.
"""
        state.cover_letter = call_llm(self.system_prompt, user_message, max_tokens=600)
        return state
