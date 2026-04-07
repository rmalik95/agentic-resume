from pathlib import Path

import agents.ats_qa_scan_agent as ats_qa_module
import agents.cover_letter_agent as cl_module
import agents.cv_rewrite_agent as cvr_module
import agents.gap_analysis_agent as gap_module
import agents.jd_intelligence_agent as jdi_module
import agents.latex_generator_agent as lg_module
import agents.match_score_agent as ms_module
import agents.positioning_strategy_agent as ps_module
from agents.ats_qa_scan_agent import ATSQAScanAgent
from agents.cover_letter_agent import CoverLetterAgent
from agents.cv_rewrite_agent import CVRewriteAgent
from agents.gap_analysis_agent import GapAnalysisAgent
from agents.jd_intelligence_agent import JDIntelligenceAgent
from agents.latex_generator_agent import LaTeXGeneratorAgent
from agents.match_score_agent import MatchScoreAgent
from agents.positioning_strategy_agent import PositioningStrategyAgent
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

    def fake_positioning(*args, **kwargs):
        return "1. Best Target Headline for the CV\nData Analyst\n\n2. Core Professional Identity\nAnalytics professional."

    def fake_jd(*args, **kwargs):
        return "1. Target Role Summary\nData analyst role focused on Python and Power BI."

    def fake_gap(*args, **kwargs):
        return "1. Overall Match Score\n6/10 - Good alignment with minor gaps."

    def fake_rewrite(*args, **kwargs):
        return (
            "1. Target Job Title\nData Analyst\n\n"
            "4. Professional Experience\n"
            "- Increased reporting speed by [X%] improving Python ETL pipeline\n"
            "- Built stakeholder-facing KPI dashboards in Power BI\n"
            "- Supported Agile sprint planning with data pipeline insights"
        )

    def fake_ats_qa(*args, **kwargs):
        return (
            "1. ATS Compatibility Score\n82/100 - Good keyword coverage.\n\n"
            "2. Recruiter First-Impression Score\n7/10 - Role is clear.\n\n"
            "10. Rejection Risks\n- Missing quantified outcomes.\n\n"
            "11. Exact Final Changes Required\n- Add metrics to top bullets."
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
    monkeypatch.setattr(ps_module, "call_llm", fake_positioning)
    monkeypatch.setattr(jdi_module, "call_llm", fake_jd)
    monkeypatch.setattr(gap_module, "call_llm", fake_gap)
    monkeypatch.setattr(cvr_module, "call_llm", fake_rewrite)
    monkeypatch.setattr(ats_qa_module, "call_llm", fake_ats_qa)
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
    state = PositioningStrategyAgent().run(state)
    state = JDIntelligenceAgent().run(state)
    state = GapAnalysisAgent().run(state)
    state = CVRewriteAgent().run(state)
    state = ATSQAScanAgent().run(state)
    state = CoverLetterAgent().run(state)
    state = MatchScoreAgent().run(state)
    state = LaTeXGeneratorAgent().run(state)
    state = RendererAgent().run(state)

    assert state.match_score_before == 52
    assert state.match_score_after == 52
    assert len(state.missing_keywords) == 5
    assert len(state.missing_keywords_before) == 5
    assert state.score_analysis_before
    assert state.score_analysis_after
    assert state.positioning_strategy
    assert state.jd_analysis
    assert state.gap_analysis
    assert state.optimized_experience
    assert state.ats_verdict
    assert state.ats_qa_report
    assert state.cover_letter
    assert state.latex_resume
    assert state.pdf_resume_path and Path(state.pdf_resume_path).exists()
    assert state.pdf_cover_letter_path and Path(state.pdf_cover_letter_path).exists()
