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
        """Generate a tailored cover letter, optionally using company web context.

        Example:
            state = CoverLetterAgent().run(state)
        """
        cached_prefix = (
            "Stable context for this application:\n"
            f"Resume text:\n{state.resume_text}\n\n"
            f"Job description:\n{state.job_description}"
        )
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
        user_message = (
            f"Optimized experience section (if available):\n{state.optimized_experience or ''}"
            f"{context_block}\n\n"
            "Write the cover letter."
        )
        state.cover_letter = call_llm(
            self.system_prompt,
            user_message,
            max_tokens=600,
            cached_prefix=cached_prefix,
            cache_system_prompt=True,
        )
        return state
