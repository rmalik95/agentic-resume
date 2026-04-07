import argparse
import datetime
from pathlib import Path

from agents.ats_qa_scan_agent import ATSQAScanAgent
from agents.cover_letter_agent import CoverLetterAgent
from agents.cv_rewrite_agent import CVRewriteAgent
from agents.gap_analysis_agent import GapAnalysisAgent
from agents.jd_intelligence_agent import JDIntelligenceAgent
from agents.latex_generator_agent import LaTeXGeneratorAgent
from agents.match_score_agent import MatchScoreAgent
from agents.positioning_strategy_agent import PositioningStrategyAgent
from agents.renderer_agent import RendererAgent
from input_collector import ask_yes_no, collect_multiline_input, collect_pdf_path
from llm_client import get_llm_metrics, reset_llm_metrics
from state import ResumeState
from utils.pdf_to_markdown import pdf_to_markdown


LOW_MATCH_SCORE_THRESHOLD = 50


def print_report(state: ResumeState, missing_keywords_added: list[str]) -> None:
    """Print PRD-style summary report.

    Example:
        print_report(state)
    """
    before = state.match_score_before or 0
    after = state.match_score_after or 0
    delta = after - before

    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Score before optimisation : {before}/100")
    print(f"Score after optimisation  : {after}/100 ({delta:+d} points)")
    print(f"Missing keywords added    : {', '.join(missing_keywords_added) or 'None'}")
    print(f"ATS verdict               : {state.ats_verdict or 'Unknown'}")
    if state.score_analysis_before:
        print(f"Score analysis (before)   : {state.score_analysis_before}")
    elif state.score_analysis:
        print(f"Score analysis (before)   : {state.score_analysis}")
    if state.score_analysis_after:
        print(f"Score analysis (after)    : {state.score_analysis_after}")
    if state.missing_keywords_after:
        print(f"Keywords still missing    : {', '.join(state.missing_keywords_after)}")
    print(f"Bullets flagged [REVIEW]  : {len(state.review_flags)}")
    if state.review_flags:
        print("-" * 60)
        print("Bullets requiring your review:")
        for line in state.review_flags:
            print(f"- {line}")
    print("-" * 60)
    if state.output_markdown_path:
        print(f"Optimised CV Markdown     : {state.output_markdown_path}")
    print(f"Resume PDF                : {state.pdf_resume_path or 'not generated'}")
    print(f"Cover letter PDF          : {state.pdf_cover_letter_path or 'not generated'}")
    if state.render_error:
        print(f"Render error              : {state.render_error}")
    metrics = get_llm_metrics()
    print("-" * 60)
    print("LLM cache metrics")
    print(f"Logical LLM calls         : {metrics['logical_calls']}")
    print(f"Anthropic API requests    : {metrics['anthropic_requests']}")
    print(f"Local cache hits          : {metrics['local_cache_hits']}")
    print(f"Prompt-cache requests     : {metrics['prompt_cache_enabled_requests']}")
    print(f"Prompt-cache retries      : {metrics['prompt_cache_fallback_retries']}")
    print(f"Input tokens              : {metrics['input_tokens']}")
    print(f"Output tokens             : {metrics['output_tokens']}")
    print(f"Cache write tokens        : {metrics['cache_creation_input_tokens']}")
    print(f"Cache read tokens         : {metrics['cache_read_input_tokens']}")
    print("=" * 60)


def _write_output_markdown(state: ResumeState) -> str:
    """Write the optimised CV content to a Markdown file in outputs/.

    Returns the absolute path to the written file.

    Example:
        path = _write_output_markdown(state)
    """
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = (outputs_dir / f"cv_optimized_{timestamp}.md").resolve()
    md_path.write_text(state.optimized_experience or "", encoding="utf-8")
    return str(md_path)


def _load_text(path: str | None) -> str:
    """Read a UTF-8 text file if path is provided.

    Example:
        content = _load_text("sample_resume.txt")
    """
    if not path:
        return ""
    with open(path, "r", encoding="utf-8") as file_handle:
        return file_handle.read().strip()


def _collect_inputs(args: argparse.Namespace) -> tuple[str, str, str | None]:
    """Collect resume (from PDF) and job description (text) from files or terminal.

    Resume must be provided as a PDF file — either via --resume-file or entered
    interactively at the prompt. The PDF is converted to Markdown before being
    passed to the agents.

    Job description is still collected as plain text paste or via --job-file.

    Returns:
        (resume_markdown, job_description, resume_pdf_path_or_None)

    Example:
        resume_md, jd, pdf_path = _collect_inputs(args)
    """
    # ── Job description (unchanged: text file or paste) ──────────────────────
    job_description = _load_text(args.job_file)

    # ── Resume (PDF path → Markdown) ─────────────────────────────────────────
    resume_text = ""
    resume_pdf_path: str | None = None

    if args.resume_file:
        if args.resume_file.lower().endswith(".pdf"):
            print(f"Converting CV PDF to Markdown: {args.resume_file}")
            resume_text = pdf_to_markdown(args.resume_file)
            resume_pdf_path = args.resume_file
        else:
            # Fallback: accept plain text / markdown file for backward-compat
            resume_text = _load_text(args.resume_file)

    if resume_text and job_description:
        return resume_text, job_description, resume_pdf_path

    print("=" * 60)
    print("ResumAI - AI-powered resume optimiser")
    print("=" * 60)

    if not resume_text:
        pdf_path = collect_pdf_path("STEP 1: Your CV (PDF)")
        print("Converting CV PDF to Markdown...")
        resume_text = pdf_to_markdown(pdf_path)
        resume_pdf_path = pdf_path
        print(f"Extracted {len(resume_text.splitlines())} lines from CV PDF.")

    if not job_description:
        job_description = collect_multiline_input("STEP 2: Paste the job description")

    return resume_text, job_description, resume_pdf_path


def _run_agent(agent_name: str, agent_obj: object, state: ResumeState) -> ResumeState:
    """Run one agent with consistent status logging and clean failure output."""
    print(f"[{agent_name}] running...")
    try:
        state = agent_obj.run(state)
    except Exception as exc:
        print(f"[{agent_name}] failed: {exc}")
        raise SystemExit(1) from exc
    print(f"[{agent_name}] done.")
    return state


def main() -> None:
    """CLI entry point for full sequential PRD pipeline.

    Example:
        main()
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-file", type=str, default=None)
    parser.add_argument("--job-file", type=str, default=None)
    parser.add_argument(
        "--company-url",
        type=str,
        default=None,
        help="URL of company About/Careers page for cover letter context",
    )
    parser.add_argument("--job-title", type=str, default="Unknown Role")
    parser.add_argument("--company", type=str, default="Unknown Company")
    parser.add_argument("--no-notify", action="store_true")
    cover_letter_group = parser.add_mutually_exclusive_group()
    cover_letter_group.add_argument(
        "--cover-letter",
        action="store_true",
        default=False,
        help="Always generate a cover letter without prompting",
    )
    cover_letter_group.add_argument(
        "--no-cover-letter",
        action="store_true",
        default=False,
        help="Skip cover letter generation without prompting",
    )
    args = parser.parse_args()
    reset_llm_metrics()

    resume_text, job_description, resume_pdf_path = _collect_inputs(args)
    print("Inputs received. Starting pipeline...")

    state = ResumeState(resume_text=resume_text, job_description=job_description)
    state.company_url = args.company_url
    state.resume_pdf_path = resume_pdf_path

    # Baseline score (before optimisation)
    state = _run_agent("MatchScoreAgent [before]", MatchScoreAgent(), state)
    baseline_score = state.match_score_before or 0
    print(f"(raw score: {baseline_score}/100)")
    if baseline_score < LOW_MATCH_SCORE_THRESHOLD:
        print(
            "Low match warning: "
            f"baseline score is {baseline_score}/100 (below {LOW_MATCH_SCORE_THRESHOLD})."
        )
        print("This role may not be a strong fit for your current experience.")
        should_continue = ask_yes_no("Do you still want to continue?")
        if not should_continue:
            print("Pipeline stopped by user due to low baseline match score.")
            return
    missing_keywords_added = list(state.missing_keywords)

    # Agent 0 — Positioning strategy
    state = _run_agent("PositioningStrategyAgent", PositioningStrategyAgent(), state)

    # Agent 1 — JD Intelligence Extractor
    state = _run_agent("JDIntelligenceAgent", JDIntelligenceAgent(), state)

    # Agent 2 — CV vs JD Gap Analysis
    state = _run_agent("GapAnalysisAgent", GapAnalysisAgent(), state)

    # Agent 3 — Tailored CV Rewrite
    state = _run_agent("CVRewriteAgent", CVRewriteAgent(), state)
    print(f"({len(state.review_flags)} placeholder(s) flagged [REVIEW])")

    # Save polished CV as Markdown immediately after rewrite
    state.output_markdown_path = _write_output_markdown(state)
    print(f"Optimised CV Markdown saved to: {state.output_markdown_path}")

    # Agent 4 — Final ATS + Recruiter QA Scan
    state = _run_agent("ATSQAScanAgent", ATSQAScanAgent(), state)
    print(f"(verdict: {state.ats_verdict or 'Unknown'})")

    # Cover letter — ask unless --cover-letter / --no-cover-letter flag is set
    if args.cover_letter:
        generate_cover_letter = True
    elif args.no_cover_letter:
        generate_cover_letter = False
    else:
        generate_cover_letter = ask_yes_no("Generate a cover letter?")

    if generate_cover_letter:
        state = _run_agent("CoverLetterAgent", CoverLetterAgent(), state)
    else:
        print("[CoverLetterAgent] skipped.")

    # Score again after optimisation
    state = _run_agent("MatchScoreAgent [after]", MatchScoreAgent(), state)
    print(f"(optimised score: {state.match_score_after or 0}/100)")

    # LaTeX + render
    state = _run_agent("LaTeXGeneratorAgent", LaTeXGeneratorAgent(), state)
    state = _run_agent("RendererAgent", RendererAgent(), state)

    print_report(state, missing_keywords_added)

    if not args.no_notify:
        from notifier import send_outputs

        send_outputs(
            pdf_paths=[state.pdf_resume_path or "", state.pdf_cover_letter_path or ""],
            job_title=args.job_title,
            company=args.company,
            score_before=state.match_score_before or 0,
            score_after=state.match_score_after or 0,
        )


if __name__ == "__main__":
    main()
