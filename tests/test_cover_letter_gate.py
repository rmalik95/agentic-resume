"""Tests for cover letter yes/no gate and ask_yes_no helper."""
import argparse
import sys
import types

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
from input_collector import ask_yes_no
from state import ResumeState


# ---------------------------------------------------------------------------
# ask_yes_no unit tests
# ---------------------------------------------------------------------------

def test_ask_yes_no_yes(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    assert ask_yes_no("Generate a cover letter?") is True


def test_ask_yes_no_y_shorthand(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert ask_yes_no("Generate a cover letter?") is True


def test_ask_yes_no_no(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "no")
    assert ask_yes_no("Generate a cover letter?") is False


def test_ask_yes_no_n_shorthand(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert ask_yes_no("Generate a cover letter?") is False


def test_ask_yes_no_invalid_then_yes(monkeypatch):
    """Invalid input should keep prompting until a valid answer is given."""
    answers = iter(["maybe", "sure", "yes"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert ask_yes_no("Generate a cover letter?") is True


# ---------------------------------------------------------------------------
# Shared fakes for pipeline tests
# ---------------------------------------------------------------------------

def _install_fakes(monkeypatch):
    monkeypatch.setattr(ms_module, "call_llm", lambda *a, **k: (
        "SCORE: 70\n"
        "KEYWORDS: Python, Agile, Power BI, stakeholder management, data pipeline\n"
        "GAP: Missing metrics\n"
        "ANALYSIS: Good fit."
    ))
    monkeypatch.setattr(ps_module, "call_llm", lambda *a, **k: "1. Best Target Headline\nData Analyst")
    monkeypatch.setattr(jdi_module, "call_llm", lambda *a, **k: "1. Target Role Summary\nData analyst role.")
    monkeypatch.setattr(gap_module, "call_llm", lambda *a, **k: "1. Overall Match Score\n7/10 - Strong match.")
    monkeypatch.setattr(cvr_module, "call_llm", lambda *a, **k: (
        "1. Target Job Title\nData Analyst\n\n"
        "4. Professional Experience\n"
        "- Delivered [X%] improvement in ETL pipeline speed"
    ))
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


def _base_state() -> ResumeState:
    return ResumeState(
        resume_text="Data Analyst with Python and Power BI experience",
        job_description="Need Python, Agile, stakeholder management, data pipeline, Power BI",
    )


# ---------------------------------------------------------------------------
# Cover letter gate: YES path
# ---------------------------------------------------------------------------

def test_cover_letter_generated_when_yes(monkeypatch):
    """When the user answers yes, CoverLetterAgent must run and state.cover_letter must be set."""
    _install_fakes(monkeypatch)
    # Simulate the user answering "yes" to the cover letter prompt
    monkeypatch.setattr(main_module, "ask_yes_no", lambda _: True)

    args = argparse.Namespace(
        resume_file=None,
        job_file=None,
        company_url=None,
        job_title="Data Analyst",
        company="Acme",
        no_notify=True,
        cover_letter=False,
        no_cover_letter=False,
    )
    monkeypatch.setattr(main_module, "_collect_inputs", lambda _: (
        "Data Analyst with Python and Power BI experience",
        "Need Python, Agile, stakeholder management, data pipeline, Power BI",
        None,
    ))
    # Capture the final state via print_report hook
    captured_state = {}

    original_print_report = main_module.print_report

    def fake_print_report(state, missing):
        captured_state["state"] = state

    monkeypatch.setattr(main_module, "print_report", fake_print_report)
    monkeypatch.setattr(sys, "argv", ["main.py", "--no-notify"])
    # Run main with mocked args
    monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self: args)
    from llm_client import reset_llm_metrics
    reset_llm_metrics()
    main_module.main()

    state = captured_state["state"]
    assert state.cover_letter == "Cover letter body."


# ---------------------------------------------------------------------------
# Cover letter gate: NO path
# ---------------------------------------------------------------------------

def test_cover_letter_skipped_when_no(monkeypatch):
    """When the user answers no, CoverLetterAgent must not run and state.cover_letter stays None."""
    _install_fakes(monkeypatch)
    monkeypatch.setattr(main_module, "ask_yes_no", lambda _: False)

    args = argparse.Namespace(
        resume_file=None,
        job_file=None,
        company_url=None,
        job_title="Data Analyst",
        company="Acme",
        no_notify=True,
        cover_letter=False,
        no_cover_letter=False,
    )
    monkeypatch.setattr(main_module, "_collect_inputs", lambda _: (
        "Data Analyst with Python and Power BI experience",
        "Need Python, Agile, stakeholder management, data pipeline, Power BI",
        None,
    ))
    captured_state = {}

    def fake_print_report(state, missing):
        captured_state["state"] = state

    monkeypatch.setattr(main_module, "print_report", fake_print_report)
    monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self: args)
    from llm_client import reset_llm_metrics
    reset_llm_metrics()
    main_module.main()

    state = captured_state["state"]
    assert state.cover_letter is None


# ---------------------------------------------------------------------------
# CLI flag: --no-cover-letter bypasses prompt
# ---------------------------------------------------------------------------

def test_no_cover_letter_flag_skips_without_prompt(monkeypatch):
    """--no-cover-letter must skip cover letter without ever calling ask_yes_no."""
    _install_fakes(monkeypatch)

    prompt_called = {"called": False}

    def fail_if_called(_):
        prompt_called["called"] = True
        return True

    monkeypatch.setattr(main_module, "ask_yes_no", fail_if_called)

    args = argparse.Namespace(
        resume_file=None,
        job_file=None,
        company_url=None,
        job_title="Data Analyst",
        company="Acme",
        no_notify=True,
        cover_letter=False,
        no_cover_letter=True,
    )
    monkeypatch.setattr(main_module, "_collect_inputs", lambda _: (
        "Data Analyst with Python and Power BI experience",
        "Need Python, Agile, stakeholder management, data pipeline, Power BI",
        None,
    ))
    captured_state = {}

    def fake_print_report(state, missing):
        captured_state["state"] = state

    monkeypatch.setattr(main_module, "print_report", fake_print_report)
    monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self: args)
    from llm_client import reset_llm_metrics
    reset_llm_metrics()
    main_module.main()

    assert not prompt_called["called"], "ask_yes_no should not be called when --no-cover-letter is set"
    assert captured_state["state"].cover_letter is None


# ---------------------------------------------------------------------------
# CLI flag: --cover-letter bypasses prompt
# ---------------------------------------------------------------------------

def test_cover_letter_flag_generates_without_prompt(monkeypatch):
    """--cover-letter must generate without ever calling ask_yes_no."""
    _install_fakes(monkeypatch)

    prompt_called = {"called": False}

    def fail_if_called(_):
        prompt_called["called"] = True
        return False

    monkeypatch.setattr(main_module, "ask_yes_no", fail_if_called)

    args = argparse.Namespace(
        resume_file=None,
        job_file=None,
        company_url=None,
        job_title="Data Analyst",
        company="Acme",
        no_notify=True,
        cover_letter=True,
        no_cover_letter=False,
    )
    monkeypatch.setattr(main_module, "_collect_inputs", lambda _: (
        "Data Analyst with Python and Power BI experience",
        "Need Python, Agile, stakeholder management, data pipeline, Power BI",
        None,
    ))
    captured_state = {}

    def fake_print_report(state, missing):
        captured_state["state"] = state

    monkeypatch.setattr(main_module, "print_report", fake_print_report)
    monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self: args)
    from llm_client import reset_llm_metrics
    reset_llm_metrics()
    main_module.main()

    assert not prompt_called["called"], "ask_yes_no should not be called when --cover-letter is set"
    assert captured_state["state"].cover_letter == "Cover letter body."


def test_low_score_stops_pipeline_when_user_declines(monkeypatch):
    """If baseline score is below threshold and user says no, execution should stop early."""
    _install_fakes(monkeypatch)
    monkeypatch.setattr(ms_module, "call_llm", lambda *a, **k: (
        "SCORE: 42\n"
        "KEYWORDS: Python, Agile\n"
        "GAP: Significant mismatch\n"
        "ANALYSIS: Weak fit."
    ))
    monkeypatch.setattr(main_module, "ask_yes_no", lambda _: False)

    args = argparse.Namespace(
        resume_file=None,
        job_file=None,
        company_url=None,
        job_title="Data Analyst",
        company="Acme",
        no_notify=True,
        cover_letter=False,
        no_cover_letter=False,
    )
    monkeypatch.setattr(main_module, "_collect_inputs", lambda _: (
        "Data Analyst with Python and Power BI experience",
        "Need Python, Agile, stakeholder management, data pipeline, Power BI",
        None,
    ))

    report_called = {"called": False}

    def fake_print_report(state, missing):
        report_called["called"] = True

    monkeypatch.setattr(main_module, "print_report", fake_print_report)
    monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self: args)
    from llm_client import reset_llm_metrics
    reset_llm_metrics()
    main_module.main()

    assert not report_called["called"], "print_report should not run after early termination"


def test_low_score_continues_pipeline_when_user_accepts(monkeypatch):
    """If baseline score is below threshold and user says yes, pipeline should complete."""
    _install_fakes(monkeypatch)
    monkeypatch.setattr(ms_module, "call_llm", lambda *a, **k: (
        "SCORE: 45\n"
        "KEYWORDS: Python, Agile, Power BI\n"
        "GAP: Missing stronger relevance\n"
        "ANALYSIS: Limited fit."
    ))
    monkeypatch.setattr(main_module, "ask_yes_no", lambda _: True)

    args = argparse.Namespace(
        resume_file=None,
        job_file=None,
        company_url=None,
        job_title="Data Analyst",
        company="Acme",
        no_notify=True,
        cover_letter=False,
        no_cover_letter=False,
    )
    monkeypatch.setattr(main_module, "_collect_inputs", lambda _: (
        "Data Analyst with Python and Power BI experience",
        "Need Python, Agile, stakeholder management, data pipeline, Power BI",
        None,
    ))
    captured_state = {}

    def fake_print_report(state, missing):
        captured_state["state"] = state

    monkeypatch.setattr(main_module, "print_report", fake_print_report)
    monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self: args)
    from llm_client import reset_llm_metrics
    reset_llm_metrics()
    main_module.main()

    assert captured_state["state"].match_score_before == 45
