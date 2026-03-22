from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResumeState:
    # Inputs
    resume_text: str = ""
    job_description: str = ""

    # Agent 1 outputs
    match_score_before: Optional[int] = None
    match_score_after: Optional[int] = None
    missing_keywords: list[str] = field(default_factory=list)
    score_analysis: Optional[str] = None

    # Agent 2 outputs
    optimized_experience: Optional[str] = None
    review_flags: list[str] = field(default_factory=list)

    # Agent 3 outputs
    ats_verdict: Optional[str] = None
    ats_fixes: Optional[str] = None

    # Agent 4 outputs
    cover_letter: Optional[str] = None

    # Agent 5 outputs
    latex_resume: Optional[str] = None
    latex_cover_letter: Optional[str] = None

    # Agent 6 outputs
    pdf_resume_path: Optional[str] = None
    pdf_cover_letter_path: Optional[str] = None
    render_error: Optional[str] = None

    # Optional runtime enrichment for cover letter web context
    company_url: Optional[str] = None
    company_context: Optional[str] = None
