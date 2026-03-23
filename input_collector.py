def collect_multiline(step_title: str) -> str:
    """Collect multiline terminal input until END marker.

    Example:
        resume = collect_multiline_input("STEP 1: Paste your resume text")
    """
    print(step_title)
    print("(Paste your text below. Type END on a new line when done)")
    lines: list[str] = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def collect_multiline_input(step_title: str) -> str:
    """Backward-compatible alias for collect_multiline."""
    return collect_multiline(step_title)


def collect_inputs() -> tuple[str, str]:
    """Collect resume and job description via END-terminated multiline input."""
    resume_text = collect_multiline("STEP 1: Paste your resume text")
    job_description = collect_multiline("STEP 2: Paste the job description")
    return resume_text, job_description
