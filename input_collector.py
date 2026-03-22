def collect_multiline_input(step_title: str) -> str:
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
