"""Comprehensive unit tests for utils/pdf_to_markdown.py."""
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers to build a realistic mock fitz module
# ---------------------------------------------------------------------------

def _make_span(text: str, size: float = 10.0, font: str = "Helvetica", flags: int = 0) -> dict:
    return {"text": text, "size": size, "font": font, "flags": flags}


def _make_line(spans: list[dict]) -> dict:
    return {"spans": spans}


def _make_block(lines: list[dict], bbox: tuple = (0, 0, 400, 20), btype: int = 0) -> dict:
    return {"type": btype, "bbox": bbox, "lines": lines}


def _make_page(blocks: list[dict]) -> MagicMock:
    page = MagicMock()
    page.get_text.return_value = {
        "blocks": blocks,
    }
    return page


def _make_fitz_doc(pages: list[MagicMock]) -> MagicMock:
    doc = MagicMock()
    doc.__iter__ = MagicMock(return_value=iter(pages))
    doc.close = MagicMock()
    return doc


def _install_mock_fitz(monkeypatch, doc_mock: MagicMock) -> types.ModuleType:
    """Install a fake fitz module into sys.modules."""
    mock_fitz = types.ModuleType("fitz")
    mock_fitz.open = MagicMock(return_value=doc_mock)
    mock_fitz.TEXT_PRESERVE_WHITESPACE = 0
    monkeypatch.setitem(sys.modules, "fitz", mock_fitz)
    return mock_fitz


# ---------------------------------------------------------------------------
# Test: heading detection — large font → H1
# ---------------------------------------------------------------------------

def test_large_font_becomes_h1(monkeypatch, tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    block = _make_block([_make_line([_make_span("Jane Doe", size=16.0)])])
    doc = _make_fitz_doc([_make_page([block])])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))
    assert "# Jane Doe" in result


# ---------------------------------------------------------------------------
# Test: heading detection — bold + short line → H2
# ---------------------------------------------------------------------------

def test_bold_short_line_becomes_h2(monkeypatch, tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    # Bold flag bit 4 = 2**4 = 16; font name with "Bold"
    block = _make_block([_make_line([_make_span("Work Experience", size=11.5, font="Helvetica-Bold")])])
    doc = _make_fitz_doc([_make_page([block])])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))
    assert "## Work Experience" in result


# ---------------------------------------------------------------------------
# Test: regular-sized, non-bold line → plain text
# ---------------------------------------------------------------------------

def test_regular_line_stays_as_plain_text(monkeypatch, tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    block = _make_block([_make_line([_make_span("Managed a team of 5 engineers.", size=10.0)])])
    doc = _make_fitz_doc([_make_page([block])])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))
    assert "Managed a team of 5 engineers." in result
    assert "##" not in result
    assert "# " not in result


# ---------------------------------------------------------------------------
# Test: bullet character detection — various leading chars
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bullet_char", ["•", "◦", "▪", "▸", "►", "- ", "– ", "— "])
def test_bullet_chars_are_converted_to_markdown_list(monkeypatch, tmp_path, bullet_char):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    raw = f"{bullet_char}Led Python ETL pipeline improvements"
    block = _make_block([_make_line([_make_span(raw, size=10.0)])])
    doc = _make_fitz_doc([_make_page([block])])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))
    assert "- Led Python ETL pipeline improvements" in result


# ---------------------------------------------------------------------------
# Test: multi-page extraction — both pages appear
# ---------------------------------------------------------------------------

def test_multi_page_both_sections_appear(monkeypatch, tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    page1 = _make_page([_make_block([_make_line([_make_span("Jane Doe", size=16.0)])])])
    page2 = _make_page([_make_block([_make_line([_make_span("Published 3 papers.", size=10.0)])])])

    doc = _make_fitz_doc([page1, page2])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))
    assert "Jane Doe" in result
    assert "Published 3 papers." in result


# ---------------------------------------------------------------------------
# Test: image/non-text blocks are skipped
# ---------------------------------------------------------------------------

def test_image_blocks_are_skipped(monkeypatch, tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    image_block = _make_block([], btype=1)  # type 1 = image
    text_block = _make_block([_make_line([_make_span("Education", size=12.0, font="Helvetica-Bold")])])
    doc = _make_fitz_doc([_make_page([image_block, text_block])])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))
    assert "Education" in result


# ---------------------------------------------------------------------------
# Test: empty page (no blocks) returns empty string
# ---------------------------------------------------------------------------

def test_empty_pdf_returns_empty_string(monkeypatch, tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    doc = _make_fitz_doc([_make_page([])])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))
    assert result == ""


# ---------------------------------------------------------------------------
# Test: blank spans within a line are ignored
# ---------------------------------------------------------------------------

def test_blank_spans_are_ignored(monkeypatch, tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    block = _make_block([
        _make_line([_make_span("  ", size=10.0), _make_span("", size=10.0)]),
        _make_line([_make_span("Real content here.", size=10.0)]),
    ])
    doc = _make_fitz_doc([_make_page([block])])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))
    assert "Real content here." in result


# ---------------------------------------------------------------------------
# Test: duplicate heading not emitted twice
# ---------------------------------------------------------------------------

def test_duplicate_heading_appears_only_once(monkeypatch, tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    heading_line = _make_line([_make_span("Experience", size=16.0)])
    block = _make_block([heading_line, heading_line])  # same line twice
    doc = _make_fitz_doc([_make_page([block])])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))
    assert result.count("# Experience") == 1


# ---------------------------------------------------------------------------
# Test: excess blank lines are collapsed to double-newline
# ---------------------------------------------------------------------------

def test_excess_blank_lines_collapsed(monkeypatch, tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    # 3-page PDF with minimal content → 3 appended "" separators
    page = _make_page([_make_block([_make_line([_make_span("A", size=10.0)])])])
    doc = _make_fitz_doc([page, page, page])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))
    assert "\n\n\n" not in result


# ---------------------------------------------------------------------------
# Test: file not found raises FileNotFoundError
# ---------------------------------------------------------------------------

def test_file_not_found_raises(monkeypatch, tmp_path):
    mock_fitz = types.ModuleType("fitz")
    mock_fitz.open = MagicMock()
    mock_fitz.TEXT_PRESERVE_WHITESPACE = 0
    monkeypatch.setitem(sys.modules, "fitz", mock_fitz)

    from utils.pdf_to_markdown import pdf_to_markdown
    with pytest.raises(FileNotFoundError, match="PDF file not found"):
        pdf_to_markdown("/does/not/exist/cv.pdf")


# ---------------------------------------------------------------------------
# Test: non-.pdf extension raises ValueError
# ---------------------------------------------------------------------------

def test_non_pdf_extension_raises(monkeypatch, tmp_path):
    mock_fitz = types.ModuleType("fitz")
    mock_fitz.open = MagicMock()
    mock_fitz.TEXT_PRESERVE_WHITESPACE = 0
    monkeypatch.setitem(sys.modules, "fitz", mock_fitz)

    docx_file = tmp_path / "resume.docx"
    docx_file.write_bytes(b"fake docx content")

    from utils.pdf_to_markdown import pdf_to_markdown
    with pytest.raises(ValueError, match="Expected a .pdf file"):
        pdf_to_markdown(str(docx_file))


# ---------------------------------------------------------------------------
# Test: fitz.open failure raises ValueError with informative message
# ---------------------------------------------------------------------------

def test_fitz_open_failure_raises_value_error(monkeypatch, tmp_path):
    pdf = tmp_path / "corrupted.pdf"
    pdf.write_bytes(b"NOT A REAL PDF")

    mock_fitz = types.ModuleType("fitz")
    mock_fitz.TEXT_PRESERVE_WHITESPACE = 0

    def boom(path):
        raise RuntimeError("cannot open document")

    mock_fitz.open = boom
    monkeypatch.setitem(sys.modules, "fitz", mock_fitz)

    from utils.pdf_to_markdown import pdf_to_markdown
    with pytest.raises(ValueError, match="Could not open PDF"):
        pdf_to_markdown(str(pdf))


# ---------------------------------------------------------------------------
# Test: ImportError when fitz is not installed
# ---------------------------------------------------------------------------

def test_import_error_when_fitz_missing(monkeypatch):
    # Remove fitz from sys.modules to simulate missing package
    monkeypatch.setitem(sys.modules, "fitz", None)  # None entry causes ImportError

    # We need to reload the module with fitz absent
    import importlib
    import utils.pdf_to_markdown as m
    original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def fake_import(name, *args, **kwargs):
        if name == "fitz":
            raise ImportError("No module named 'fitz'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    # Force the function body to re-execute its import
    with pytest.raises(ImportError, match="pymupdf is required"):
        m.pdf_to_markdown("anything.pdf")


# ---------------------------------------------------------------------------
# Test: mixed content page — heading + bullets + plain text
# ---------------------------------------------------------------------------

def test_mixed_content_produces_correct_markdown(monkeypatch, tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    blocks = [
        _make_block([_make_line([_make_span("Jane Doe", size=16.0)])]),
        _make_block([_make_line([_make_span("Work Experience", size=11.5, font="Helvetica-Bold")])]),
        _make_block([_make_line([_make_span("• Delivered 30% cost reduction via automation", size=10.0)])]),
        _make_block([_make_line([_make_span("Python, Pandas, SQL", size=10.0)])]),
    ]
    doc = _make_fitz_doc([_make_page(blocks)])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))

    assert "# Jane Doe" in result
    assert "## Work Experience" in result
    assert "- Delivered 30% cost reduction via automation" in result
    assert "Python, Pandas, SQL" in result


# ---------------------------------------------------------------------------
# Test: multiple spans on one line are concatenated
# ---------------------------------------------------------------------------

def test_multiple_spans_concatenated(monkeypatch, tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF placeholder")

    block = _make_block([
        _make_line([
            _make_span("Senior ", size=10.0),
            _make_span("Data ", size=10.0),
            _make_span("Analyst", size=10.0),
        ])
    ])
    doc = _make_fitz_doc([_make_page([block])])
    _install_mock_fitz(monkeypatch, doc)

    from utils.pdf_to_markdown import pdf_to_markdown
    result = pdf_to_markdown(str(pdf))
    assert "Senior Data Analyst" in result
