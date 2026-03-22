from pathlib import Path

import pytest

from utils.prompt_loader import load_prompt


def test_load_prompt_existing_file() -> None:
    content = load_prompt("cover_letter")
    assert "cover letter" in content.lower()


def test_load_prompt_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("definitely_missing_prompt")


def test_examples_append_when_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prompts_dir = tmp_path / "prompts"
    examples_dir = prompts_dir / "examples"
    prompts_dir.mkdir()
    examples_dir.mkdir()
    (prompts_dir / "demo.md").write_text("base", encoding="utf-8")
    (examples_dir / "demo.md").write_text("example", encoding="utf-8")

    import utils.prompt_loader as prompt_loader

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", prompts_dir)
    monkeypatch.setattr(prompt_loader, "EXAMPLES_DIR", examples_dir)

    content = prompt_loader.load_prompt("demo")
    assert content == "base\n\nexample"
