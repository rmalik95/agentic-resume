"""Convert a PDF resume to Markdown-formatted text using PyMuPDF."""
import re
from pathlib import Path


def pdf_to_markdown(pdf_path: str) -> str:
    """Extract text from a PDF file and return it as Markdown.

    Heading detection uses font size and bold weight as signals:
    - avg font size >= 14           → H1  (candidate name / top section)
    - bold + short line, size >= 10 → H2  (section headings)
    - bullet-leading char           → list item
    - everything else               → plain paragraph line

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        Markdown string representing the CV content.

    Raises:
        ImportError: if pymupdf is not installed.
        FileNotFoundError: if the file does not exist.
        ValueError: if the path is not a .pdf or the file cannot be parsed.

    Example:
        md = pdf_to_markdown("resume.pdf")
    """
    try:
        import fitz  # pymupdf
    except ImportError as exc:
        raise ImportError(
            "pymupdf is required for PDF input. "
            "Install it with: pip install pymupdf"
        ) from exc

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {pdf_path}")

    try:
        doc = fitz.open(str(path))
    except Exception as exc:
        raise ValueError(f"Could not open PDF '{pdf_path}': {exc}") from exc

    output_lines: list[str] = []
    seen_headings: set[str] = set()

    for page in doc:
        raw = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        blocks = raw.get("blocks", [])

        # Sort blocks top-to-bottom, left-to-right
        for block in sorted(blocks, key=lambda b: (round(b["bbox"][1]), b["bbox"][0])):
            if block.get("type") != 0:  # skip image/non-text blocks
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                line_text = "".join(sp["text"] for sp in spans).strip()
                if not line_text:
                    continue

                # Font metrics for this line
                text_spans = [sp for sp in spans if sp.get("text", "").strip()]
                sizes = [sp["size"] for sp in text_spans]
                avg_size = sum(sizes) / len(sizes) if sizes else 10.0
                is_bold = any(
                    ("Bold" in sp.get("font", "") or bool(sp.get("flags", 0) & 2**4))
                    for sp in text_spans
                )

                # Bullet detection — leading special characters (space after bullet is optional in PDFs)
                bullet_match = re.match(r"^[•◦▪▸►\-–—]\s*", line_text)
                if bullet_match:
                    clean = line_text[bullet_match.end():].strip()
                    if clean:  # ignore lone bullet chars with no content
                        output_lines.append(f"- {clean}")
                    continue

                # Heading detection
                is_h1 = avg_size >= 14
                is_h2 = is_bold and avg_size >= 10 and len(line_text) <= 60

                if (is_h1 or is_h2) and line_text not in seen_headings:
                    prefix = "# " if is_h1 else "## "
                    output_lines.append(f"\n{prefix}{line_text}")
                    seen_headings.add(line_text)
                else:
                    output_lines.append(line_text)

        output_lines.append("")  # blank line between pages

    doc.close()

    md = "\n".join(output_lines)
    # Collapse runs of 3+ blank lines down to 2
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()
