import argparse

from agents.cover_letter_agent import CoverLetterAgent
from state import ResumeState


def print_report(state: ResumeState) -> None:
    print("\nRun summary")
    print(f"  company_url: {state.company_url or 'not provided'}")
    print(f"  company_context: {'yes' if state.company_context else 'no'}")
    print(f"  cover_letter_generated: {'yes' if state.cover_letter else 'no'}")


def _load_text(path: str | None) -> str:
    if not path:
        return ""
    with open(path, "r", encoding="utf-8") as file_handle:
        return file_handle.read().strip()


def main() -> None:
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

    state = ResumeState(
        resume_text=_load_text(args.resume_file),
        job_description=_load_text(args.job_file),
    )
    state.company_url = args.company_url

    if state.resume_text and state.job_description:
        state = CoverLetterAgent().run(state)

    print_report(state)

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
