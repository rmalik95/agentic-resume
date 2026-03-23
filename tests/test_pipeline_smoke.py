from pathlib import Path

import agents.ats_checker_agent as ats_module
import agents.cover_letter_agent as cl_module
import agents.experience_optimizer_agent as eo_module
import agents.latex_generator_agent as lg_module
import agents.match_score_agent as ms_module
from agents.ats_checker_agent import ATSCheckerAgent
from agents.cover_letter_agent import CoverLetterAgent
from agents.experience_optimizer_agent import ExperienceOptimizerAgent
from agents.latex_generator_agent import LaTeXGeneratorAgent
from agents.match_score_agent import MatchScoreAgent
from agents.renderer_agent import RendererAgent
from state import ResumeState


def test_full_pipeline_smoke(monkeypatch):
    def fake_match(*args, **kwargs):
        return (
            "SCORE: 52\n"
            "KEYWORDS: stakeholder management, Python, data pipeline, Agile, Power BI\n"
            "GAP: Missing quantified outcomes\n"
            "ANALYSIS: Good baseline alignment."
        )

    def fake_experience(*args, **kwargs):
        return (
            "Experience\n"
            "- Increased reporting speed by improving Python ETL [REVIEW]\n"
            "- Built stakeholder-facing KPI dashboards in Power BI\n"
            "- Supported Agile sprint planning with data pipeline insights"
        )

    def fake_ats(*args, **kwargs):
        return (
            "ISSUES:\n"
            "- [MINOR] Date format inconsistent: use MMM YYYY\n"
            "VERDICT: Conditional Pass\n"
            "SUMMARY: Mostly ATS-ready with minor formatting issue."
        )

    def fake_cover(*args, **kwargs):
        return "Short cover letter under 300 words."

    def fake_latex(*args, **kwargs):
        return (
            "\\documentclass{article}\\begin{document}Resume\\end{document}\n"
            "---COVERLETTER---\n"
            "\\documentclass{article}\\begin{document}Cover\\end{document}"
        )

    monkeypatch.setattr(ms_module, "call_llm", fake_match)
    monkeypatch.setattr(eo_module, "call_llm", fake_experience)
    monkeypatch.setattr(ats_module, "call_llm", fake_ats)
    monkeypatch.setattr(cl_module, "call_llm", fake_cover)
    monkeypatch.setattr(lg_module, "call_llm", fake_latex)

    def fake_render_single(self, latex_code, output_path, stem):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"%PDF-1.4\n%mock\n")
        return True

    monkeypatch.setattr(RendererAgent, "_render_single", fake_render_single)

    state = ResumeState(
        resume_text="Data Analyst with Python and Power BI experience",
        job_description=(
            "Need Python, Agile, stakeholder management, data pipeline, and Power BI"
        ),
    )

    state = MatchScoreAgent().run(state)
    state = ExperienceOptimizerAgent().run(state)
    state = ATSCheckerAgent().run(state)
    state = CoverLetterAgent().run(state)
    state = MatchScoreAgent().run(state)
    state = LaTeXGeneratorAgent().run(state)
    state = RendererAgent().run(state)

    assert state.match_score_before == 52
    assert state.match_score_after == 52
    assert len(state.missing_keywords) == 5
    assert state.cover_letter
    assert state.latex_resume
    assert state.pdf_resume_path and Path(state.pdf_resume_path).exists()
    assert state.pdf_cover_letter_path and Path(state.pdf_cover_letter_path).exists()
