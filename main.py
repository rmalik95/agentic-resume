import argparse

from agents.ats_checker_agent import ATSCheckerAgent
from agents.cover_letter_agent import CoverLetterAgent
from agents.experience_optimizer_agent import ExperienceOptimizerAgent
from agents.latex_generator_agent import LaTeXGeneratorAgent
from agents.match_score_agent import MatchScoreAgent
from agents.renderer_agent import RendererAgent
from input_collector import collect_multiline_input
from state import ResumeState


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
    print(f"ATS issues                : {state.ats_fixes or 'None'}")
    if state.score_analysis:
        print(f"Score analysis            : {state.score_analysis}")
    print(f"Bullets flagged [REVIEW]  : {len(state.review_flags)}")
    if state.review_flags:
        print("-" * 60)
        print("Bullets requiring your review:")
        for line in state.review_flags:
            print(f"- {line}")
    print("-" * 60)
    print(f"Resume PDF                : {state.pdf_resume_path or 'not generated'}")
    print(f"Cover letter PDF          : {state.pdf_cover_letter_path or 'not generated'}")
    if state.render_error:
        print(f"Render error              : {state.render_error}")
    print("=" * 60)


def _load_text(path: str | None) -> str:
    """Read a UTF-8 text file if path is provided.

    Example:
        content = _load_text("sample_resume.txt")
    """
    if not path:
        return ""
    with open(path, "r", encoding="utf-8") as file_handle:
        return file_handle.read().strip()


def _collect_inputs(args: argparse.Namespace) -> tuple[str, str]:
    """Collect resume and job description from files or terminal multiline input.

    Example:
        resume, jd = _collect_inputs(args)
    """
    resume_text = _load_text(args.resume_file)
    job_description = _load_text(args.job_file)

    if resume_text and job_description:
        return resume_text, job_description

    print("=" * 60)
    print("ResumAI - AI-powered resume optimiser")
    print("=" * 60)
    if not resume_text:
        resume_text = collect_multiline_input("STEP 1: Paste your resume text")
    if not job_description:
        job_description = collect_multiline_input("STEP 2: Paste the job description")
    return resume_text, job_description


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
    args = parser.parse_args()

    resume_text, job_description = _collect_inputs(args)
    print("Inputs received. Starting pipeline...")

    state = ResumeState(resume_text=resume_text, job_description=job_description)
    state.company_url = args.company_url

    state = _run_agent("MatchScoreAgent", MatchScoreAgent(), state)
    print(f"(raw score: {state.match_score_before or 0}/100)")
    missing_keywords_added = list(state.missing_keywords)

    state = _run_agent("ExperienceOptimizerAgent", ExperienceOptimizerAgent(), state)
    print(f"({len(state.review_flags)} bullets flagged [REVIEW])")

    state = _run_agent("ATSCheckerAgent", ATSCheckerAgent(), state)
    print(f"(verdict: {state.ats_verdict or 'Unknown'})")

    state = _run_agent("CoverLetterAgent", CoverLetterAgent(), state)

    state = _run_agent("MatchScoreAgent", MatchScoreAgent(), state)
    print(f"(optimised score: {state.match_score_after or 0}/100)")

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
