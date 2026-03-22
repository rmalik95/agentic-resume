from dataclasses import dataclass
from typing import Optional


@dataclass
class ResumeState:
    resume_text: str = ""
    job_description: str = ""
    optimized_experience: Optional[str] = None
    cover_letter: Optional[str] = None

    company_url: Optional[str] = None
    company_context: Optional[str] = None

    pdf_resume_path: Optional[str] = None
    pdf_cover_letter_path: Optional[str] = None

    match_score_before: Optional[int] = None
    match_score_after: Optional[int] = None
