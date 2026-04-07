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
    missing_keywords_before: list[str] = field(default_factory=list)
    missing_keywords_after: list[str] = field(default_factory=list)
    score_analysis_before: Optional[str] = None
    score_analysis_after: Optional[str] = None

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

    # Input tracking
    resume_pdf_path: Optional[str] = None  # original PDF path if PDF was supplied

    # Output tracking
    output_markdown_path: Optional[str] = None  # path to polished CV Markdown file

    # Agent 0 outputs (Positioning Strategy)
    positioning_strategy: Optional[str] = None

    # Agent 1 outputs (JD Intelligence)
    jd_analysis: Optional[str] = None

    # Agent 2 outputs (Gap Analysis)
    gap_analysis: Optional[str] = None

    # Agent 4 expanded outputs (ATS QA Scan)
    ats_qa_report: Optional[str] = None
