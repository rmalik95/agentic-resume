import re

from base_agent import BaseAgent
from llm_client import call_llm
from state import ResumeState


class LaTeXGeneratorAgent(BaseAgent):
    """Generate resume and cover-letter LaTeX split by delimiter."""

    prompt_name = "latex_generator"

    def _extract_profile_fields(self, resume_text: str) -> dict[str, str]:
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        name = lines[0] if lines else ""

        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", resume_text)
        phone_match = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", resume_text)

        first_name = ""
        last_name = ""
        if name and not any(token in name.lower() for token in ["resume", "experience", "summary", "skills"]):
            parts = name.split()
            if parts:
                first_name = parts[0]
                last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
        }

    def _sanitize_placeholders(self, latex: str, profile: dict[str, str]) -> str:
        cleaned = latex

        # Remove hard placeholder tokens that often break moderncv field parsing.
        cleaned = re.sub(r"\[\s*INSERT[^\]]*\]", "", cleaned, flags=re.IGNORECASE)

        # Fill common identity fields from resume source where available.
        cleaned = re.sub(
            r"\\name\{[^}]*\}\{[^}]*\}",
            rf"\\name{{{profile['first_name']}}}{{{profile['last_name']}}}",
            cleaned,
            count=1,
        )
        cleaned = re.sub(
            r"\\phone\[mobile\]\{[^}]*\}",
            rf"\\phone[mobile]{{{profile['phone']}}}",
            cleaned,
            count=1,
        )
        cleaned = re.sub(
            r"\\email\{[^}]*\}",
            rf"\\email{{{profile['email']}}}",
            cleaned,
            count=1,
        )

        # If LLM still emits literal template defaults, blank them out safely.
        cleaned = cleaned.replace("{First}", "{}")
        cleaned = cleaned.replace("{Last}", "{}")
        cleaned = cleaned.replace("{email@example.com}", "{}")
        cleaned = cleaned.replace("{+00 000 000 0000}", "{}")
        cleaned = cleaned.replace("{linkedin-handle}", "{}")

        return cleaned

    def _split_documents(self, response_text: str) -> tuple[str, str]:
        # Accept common delimiter variants first.
        delimiter_pattern = re.compile(r"\n\s*---\s*COVER\s*LETTER\s*---\s*\n", re.IGNORECASE)
        if delimiter_pattern.search(response_text):
            parts = delimiter_pattern.split(response_text, maxsplit=1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()

        if "---COVERLETTER---" in response_text:
            parts = response_text.split("---COVERLETTER---", maxsplit=1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()

        # Fallback: split at second \documentclass if model omitted delimiter.
        starts = [match.start() for match in re.finditer(r"\\documentclass", response_text)]
        if len(starts) >= 2:
            split_idx = starts[1]
            return response_text[:split_idx].strip(), response_text[split_idx:].strip()

        raise ValueError("LaTeXGeneratorAgent output missing ---COVERLETTER--- delimiter")

    def run(self, state: ResumeState) -> ResumeState:
        """Populate latex_resume and latex_cover_letter fields.

        Example:
            state = LaTeXGeneratorAgent().run(state)
        """
        profile = self._extract_profile_fields(state.resume_text)
        cached_prefix = (
            "Stable context for this application:\n"
            f"Original full resume (source of contact details):\n{state.resume_text}\n\n"
            f"Job description:\n{state.job_description}"
        )
        user_message = (
            "Use candidate identity/contact fields only from the source resume. "
            "Do NOT emit placeholders like [INSERT ...], First/Last, or example emails/phones.\n\n"
            f"Optimized resume content:\n{state.optimized_experience or state.resume_text}\n\n"
            f"Cover letter content:\n{state.cover_letter or ''}\n\n"
            "Return two LaTeX documents separated by ---COVERLETTER---"
        )
        response = call_llm(
            self.system_prompt,
            user_message,
            max_tokens=3000,
            cached_prefix=cached_prefix,
            cache_system_prompt=True,
        )
        cleaned = response.replace("```latex", "").replace("```", "").strip()
        resume_part, cover_part = self._split_documents(cleaned)

        state.latex_resume = self._sanitize_placeholders(resume_part, profile)
        state.latex_cover_letter = self._sanitize_placeholders(cover_part, profile)
        return state
