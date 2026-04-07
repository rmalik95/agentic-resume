"""Comprehensive tests for PDF input pipeline and collect_pdf_path."""
import argparse
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import agents.ats_qa_scan_agent as ats_qa_module
import agents.cover_letter_agent as cl_module
import agents.cv_rewrite_agent as cvr_module
import agents.gap_analysis_agent as gap_module
import agents.jd_intelligence_agent as jdi_module
import agents.latex_generator_agent as lg_module
import agents.match_score_agent as ms_module
import agents.positioning_strategy_agent as ps_module
import main as main_module
from agents.renderer_agent import RendererAgent
from input_collector import collect_pdf_path
from state import ResumeState


# ---------------------------------------------------------------------------
# Shared fakes
# ---------------------------------------------------------------------------

FAKE_RESUME_MD = (
    "# Jane Doe\n\n"
    "## Work Experience\n\n"
    "- Delivered [X%] improvement in ETL pipeline speed using Python\n"
    "- Built Power BI dashboards for stakeholder reporting\n\n"
    "## Education\n\nBSc Computer Science"
)


def _install_pipeline_fakes(monkeypatch):
    monkeypatch.setattr(ms_module, "call_llm", lambda *a, **k: (
        "SCORE: 70\n"
        "KEYWORDS: Python, Agile, Power BI, stakeholder management, data pipeline\n"
        "GAP: Missing metrics\n"
        "ANALYSIS: Good fit."
    ))
    monkeypatch.setattr(ps_module, "call_llm", lambda *a, **k: "1. Best Target Headline\nData Analyst")
    monkeypatch.setattr(jdi_module, "call_llm", lambda *a, **k: "1. Target Role Summary\nData analyst role.")
    monkeypatch.setattr(gap_module, "call_llm", lambda *a, **k: "1. Overall Match Score\n7/10 - Strong match.")
    monkeypatch.setattr(cvr_module, "call_llm", lambda *a, **k: FAKE_RESUME_MD)
    monkeypatch.setattr(ats_qa_module, "call_llm", lambda *a, **k: (
        "1. ATS Compatibility Score\n85/100 - Good.\n\n"
        "2. Recruiter First-Impression Score\n8/10 - Clear.\n\n"
        "10. Rejection Risks\nNone critical.\n\n"
        "11. Exact Final Changes Required\nAdd metrics."
    ))
    monkeypatch.setattr(cl_module, "call_llm", lambda *a, **k: "Cover letter body.")
    monkeypatch.setattr(lg_module, "call_llm", lambda *a, **k: (
        "\\documentclass{article}\\begin{document}Resume\\end{document}\n"
        "---COVERLETTER---\n"
        "\\documentclass{article}\\begin{document}Cover\\end{document}"
    ))

    def fake_render_single(self, latex_code, output_path, stem):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"%PDF-1.4\n%mock\n")
        return True

    monkeypatch.setattr(RendererAgent, "_render_single", fake_render_single)


def _fake_args(**overrides) -> argparse.Namespace:
    defaults = dict(
        resume_file=None,
        job_file=None,
        company_url=None,
        job_title="Data Analyst",
        company="Acme",
        no_notify=True,
        cover_letter=True,
        no_cover_letter=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _capture_state(monkeypatch) -> dict:
    captured = {}

    def fake_print_report(state, missing):
        captured["state"] = state

    monkeypatch.setattr(main_module, "print_report", fake_print_report)
    return captured


# ===========================================================================
# collect_pdf_path tests
# ===========================================================================

class TestCollectPdfPath:
    def test_valid_path_returned(self, monkeypatch, tmp_path):
        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")
        monkeypatch.setattr("builtins.input", lambda _: str(pdf))
        result = collect_pdf_path("Enter PDF path")
        assert result == str(pdf)

    def test_empty_input_prompts_again(self, monkeypatch, tmp_path):
        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")
        responses = iter(["", "  ", str(pdf)])
        monkeypatch.setattr("builtins.input", lambda _: next(responses))
        result = collect_pdf_path("Enter PDF path")
        assert result == str(pdf)

    def test_nonexistent_path_prompts_again(self, monkeypatch, tmp_path):
        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")
        responses = iter(["/no/such/file.pdf", str(pdf)])
        monkeypatch.setattr("builtins.input", lambda _: next(responses))
        result = collect_pdf_path("Enter PDF path")
        assert result == str(pdf)

    def test_non_pdf_extension_prompts_again(self, monkeypatch, tmp_path):
        docx = tmp_path / "cv.docx"
        docx.write_bytes(b"fake")
        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")
        responses = iter([str(docx), str(pdf)])
        monkeypatch.setattr("builtins.input", lambda _: next(responses))
        result = collect_pdf_path("Enter PDF path")
        assert result == str(pdf)

    def test_tilde_expansion(self, monkeypatch, tmp_path):
        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")
        # Replace ~ with the tmp_path parent to simulate expansion
        tilde_path = "~/" + os.path.relpath(str(pdf), os.path.expanduser("~"))
        monkeypatch.setattr("builtins.input", lambda _: tilde_path)
        result = collect_pdf_path("Enter PDF path")
        assert result.endswith("cv.pdf")
        assert "~" not in result


# ===========================================================================
# _collect_inputs: PDF path via --resume-file flag
# ===========================================================================

class TestCollectInputsPdfFlag:
    def test_pdf_file_arg_triggers_conversion(self, monkeypatch, tmp_path):
        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")
        jd_file = tmp_path / "jd.txt"
        jd_file.write_text("Need Python, Agile, Power BI", encoding="utf-8")

        monkeypatch.setattr(main_module, "pdf_to_markdown", lambda p: FAKE_RESUME_MD)
        args = _fake_args(resume_file=str(pdf), job_file=str(jd_file))
        resume, jd, pdf_path = main_module._collect_inputs(args)

        assert resume == FAKE_RESUME_MD
        assert pdf_path == str(pdf)

    def test_text_file_arg_not_converted(self, monkeypatch, tmp_path):
        txt = tmp_path / "cv.txt"
        txt.write_text("Plain text resume", encoding="utf-8")
        jd_file = tmp_path / "jd.txt"
        jd_file.write_text("Need Python", encoding="utf-8")

        # pdf_to_markdown should NOT be called
        called = {"yes": False}

        def fail_if_called(p):
            called["yes"] = True
            return ""

        monkeypatch.setattr(main_module, "pdf_to_markdown", fail_if_called)
        args = _fake_args(resume_file=str(txt), job_file=str(jd_file))
        resume, jd, pdf_path = main_module._collect_inputs(args)

        assert called["yes"] is False
        assert resume == "Plain text resume"
        assert pdf_path is None

    def test_pdf_path_case_insensitive(self, monkeypatch, tmp_path):
        """A .PDF (upper-case extension) should also trigger conversion."""
        pdf = tmp_path / "cv.PDF"
        pdf.write_bytes(b"%PDF placeholder")
        jd_file = tmp_path / "jd.txt"
        jd_file.write_text("Need Python", encoding="utf-8")

        monkeypatch.setattr(main_module, "pdf_to_markdown", lambda p: FAKE_RESUME_MD)
        args = _fake_args(resume_file=str(pdf), job_file=str(jd_file))
        resume, jd, pdf_path = main_module._collect_inputs(args)
        assert resume == FAKE_RESUME_MD


# ===========================================================================
# _collect_inputs: interactive PDF path collection
# ===========================================================================

class TestCollectInputsInteractive:
    def test_interactive_prompts_for_pdf_path(self, monkeypatch, tmp_path):
        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")

        monkeypatch.setattr(main_module, "collect_pdf_path", lambda _: str(pdf))
        monkeypatch.setattr(main_module, "pdf_to_markdown", lambda p: FAKE_RESUME_MD)
        monkeypatch.setattr(main_module, "collect_multiline_input", lambda _: "Need Python")

        args = _fake_args(resume_file=None, job_file=None)
        resume, jd, pdf_path = main_module._collect_inputs(args)

        assert resume == FAKE_RESUME_MD
        assert jd == "Need Python"
        assert pdf_path == str(pdf)

    def test_jd_collected_as_text_even_with_pdf_resume(self, monkeypatch, tmp_path):
        """JD must never be derived from a PDF; always text paste or --job-file."""
        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")
        jd_file = tmp_path / "jd.txt"
        jd_file.write_text("Need Agile, stakeholder", encoding="utf-8")

        monkeypatch.setattr(main_module, "pdf_to_markdown", lambda p: FAKE_RESUME_MD)
        args = _fake_args(resume_file=str(pdf), job_file=str(jd_file))
        _, jd, _ = main_module._collect_inputs(args)
        assert jd == "Need Agile, stakeholder"


# ===========================================================================
# Output Markdown file creation
# ===========================================================================

class TestOutputMarkdown:
    def test_output_markdown_written_after_cv_rewrite(self, tmp_path):
        state = ResumeState(
            resume_text="Original CV",
            job_description="JD",
            optimized_experience=FAKE_RESUME_MD,
        )
        # Point outputs dir to tmp_path
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            path = main_module._write_output_markdown(state)
        finally:
            os.chdir(original_cwd)

        assert Path(path).exists()
        content = Path(path).read_text(encoding="utf-8")
        assert FAKE_RESUME_MD in content

    def test_output_markdown_filename_contains_timestamp(self, tmp_path):
        state = ResumeState(
            resume_text="CV",
            job_description="JD",
            optimized_experience="Optimized CV content",
        )
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            path = main_module._write_output_markdown(state)
        finally:
            os.chdir(original_cwd)

        filename = Path(path).name
        assert filename.startswith("cv_optimized_")
        assert filename.endswith(".md")

    def test_output_markdown_written_to_outputs_dir(self, tmp_path):
        state = ResumeState(
            resume_text="CV",
            job_description="JD",
            optimized_experience="Optimized CV content",
        )
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            path = main_module._write_output_markdown(state)
        finally:
            os.chdir(original_cwd)

        assert Path(path).parent.name == "outputs"

    def test_output_markdown_empty_when_no_optimized_experience(self, tmp_path):
        state = ResumeState(resume_text="CV", job_description="JD")
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            path = main_module._write_output_markdown(state)
        finally:
            os.chdir(original_cwd)

        assert Path(path).read_text(encoding="utf-8") == ""


# ===========================================================================
# State fields
# ===========================================================================

class TestStateFields:
    def test_resume_pdf_path_field_exists(self):
        state = ResumeState(resume_text="r", job_description="j")
        assert hasattr(state, "resume_pdf_path")
        assert state.resume_pdf_path is None

    def test_output_markdown_path_field_exists(self):
        state = ResumeState(resume_text="r", job_description="j")
        assert hasattr(state, "output_markdown_path")
        assert state.output_markdown_path is None

    def test_resume_pdf_path_set_in_main(self, monkeypatch, tmp_path):
        _install_pipeline_fakes(monkeypatch)
        monkeypatch.setattr(main_module, "ask_yes_no", lambda _: False)

        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")
        jd_file = tmp_path / "jd.txt"
        jd_file.write_text("Need Python, Agile, Power BI", encoding="utf-8")

        monkeypatch.setattr(main_module, "pdf_to_markdown", lambda p: FAKE_RESUME_MD)
        monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self: _fake_args(
            resume_file=str(pdf),
            job_file=str(jd_file),
            no_cover_letter=True,
            cover_letter=False,
        ))

        captured = _capture_state(monkeypatch)
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        from llm_client import reset_llm_metrics
        reset_llm_metrics()
        try:
            main_module.main()
        finally:
            os.chdir(original_cwd)

        assert captured["state"].resume_pdf_path == str(pdf)

    def test_output_markdown_path_set_in_main(self, monkeypatch, tmp_path):
        _install_pipeline_fakes(monkeypatch)
        monkeypatch.setattr(main_module, "ask_yes_no", lambda _: False)

        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")
        jd_file = tmp_path / "jd.txt"
        jd_file.write_text("Need Python", encoding="utf-8")

        monkeypatch.setattr(main_module, "pdf_to_markdown", lambda p: FAKE_RESUME_MD)
        monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self: _fake_args(
            resume_file=str(pdf),
            job_file=str(jd_file),
            no_cover_letter=True,
            cover_letter=False,
        ))

        captured = _capture_state(monkeypatch)
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        from llm_client import reset_llm_metrics
        reset_llm_metrics()
        try:
            main_module.main()
        finally:
            os.chdir(original_cwd)

        assert captured["state"].output_markdown_path is not None
        assert Path(captured["state"].output_markdown_path).exists()


# ===========================================================================
# Full end-to-end: PDF in → Markdown out → PDF out
# ===========================================================================

class TestFullPdfToPdfPipeline:
    def test_full_pipeline_pdf_resume_produces_pdf_outputs(self, monkeypatch, tmp_path):
        """PDF CV input → agents → Markdown file + PDF resume and cover letter."""
        _install_pipeline_fakes(monkeypatch)
        monkeypatch.setattr(main_module, "ask_yes_no", lambda _: True)  # generate cover letter

        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")
        jd_file = tmp_path / "jd.txt"
        jd_file.write_text(
            "Need Python, Agile, stakeholder management, data pipeline, Power BI",
            encoding="utf-8",
        )

        # mock pdf_to_markdown to return our fake resume markdown
        monkeypatch.setattr(main_module, "pdf_to_markdown", lambda p: FAKE_RESUME_MD)
        monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self: _fake_args(
            resume_file=str(pdf),
            job_file=str(jd_file),
            cover_letter=True,
            no_cover_letter=False,
        ))

        captured = _capture_state(monkeypatch)
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        from llm_client import reset_llm_metrics
        reset_llm_metrics()
        try:
            main_module.main()
        finally:
            os.chdir(original_cwd)

        state = captured["state"]

        # Resume Markdown from PDF was correctly ingested
        assert state.resume_text == FAKE_RESUME_MD
        # Agents ran and produced all expected outputs
        assert state.match_score_before == 70
        assert state.positioning_strategy
        assert state.jd_analysis
        assert state.gap_analysis
        assert state.optimized_experience == FAKE_RESUME_MD  # CVRewriteAgent output
        assert state.ats_verdict
        assert state.cover_letter == "Cover letter body."
        assert state.match_score_after == 70
        assert state.latex_resume
        # Output markdown file created
        assert state.output_markdown_path is not None
        assert Path(state.output_markdown_path).exists()
        content = Path(state.output_markdown_path).read_text(encoding="utf-8")
        assert "Jane Doe" in content or FAKE_RESUME_MD in content
        # PDFs produced
        assert state.pdf_resume_path and Path(state.pdf_resume_path).exists()
        assert state.pdf_cover_letter_path and Path(state.pdf_cover_letter_path).exists()

    def test_full_pipeline_no_cover_letter_skips_cover_pdf(self, monkeypatch, tmp_path):
        _install_pipeline_fakes(monkeypatch)
        monkeypatch.setattr(main_module, "ask_yes_no", lambda _: False)

        pdf = tmp_path / "cv.pdf"
        pdf.write_bytes(b"%PDF placeholder")
        jd_file = tmp_path / "jd.txt"
        jd_file.write_text("Need Python", encoding="utf-8")

        monkeypatch.setattr(main_module, "pdf_to_markdown", lambda p: FAKE_RESUME_MD)
        monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self: _fake_args(
            resume_file=str(pdf),
            job_file=str(jd_file),
            no_cover_letter=True,
            cover_letter=False,
        ))

        captured = _capture_state(monkeypatch)
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        from llm_client import reset_llm_metrics
        reset_llm_metrics()
        try:
            main_module.main()
        finally:
            os.chdir(original_cwd)

        state = captured["state"]
        assert state.cover_letter is None
        # Resume PDF still produced even when cover letter is skipped
        assert state.pdf_resume_path and Path(state.pdf_resume_path).exists()
