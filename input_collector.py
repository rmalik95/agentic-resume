import os


def ask_yes_no(question: str) -> bool:
    """Prompt the user with a yes/no question and return True for yes, False for no.

    Keeps asking until a valid answer is given.

    Example:
        generate = ask_yes_no("Generate a cover letter? (yes/no)")
    """
    while True:
        answer = input(f"{question} [yes/no]: ").strip().lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("Please answer yes or no.")


def collect_pdf_path(prompt: str) -> str:
    """Prompt the user for a CV PDF file path, re-prompting until a valid path is provided.

    Expands ~ and environment variables. Validates that the file exists and ends with .pdf.

    Example:
        path = collect_pdf_path("STEP 1: Enter the path to your CV PDF")
    """
    print(prompt)
    while True:
        raw = input("PDF file path: ").strip()
        if not raw:
            print("Path cannot be empty. Please try again.")
            continue
        expanded = os.path.expandvars(os.path.expanduser(raw))
        if not os.path.exists(expanded):
            print(f"File not found: {expanded}. Please try again.")
            continue
        if not expanded.lower().endswith(".pdf"):
            print("File must be a .pdf. Please try again.")
            continue
        return expanded


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
