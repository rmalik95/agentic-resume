from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"
EXAMPLES_DIR = PROMPTS_DIR / "examples"


def load_global_instructions() -> str:
    """Load the global writing instructions shared across agents."""
    path = PROMPTS_DIR / "global_writing_instructions.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def load_prompt(name: str) -> str:
    """Load a prompt by name and append optional examples file if present."""
    prompt_path = PROMPTS_DIR / f"{name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    prompt_text = prompt_path.read_text(encoding="utf-8").strip()

    examples_path = EXAMPLES_DIR / f"{name}.md"
    if examples_path.exists():
        examples_text = examples_path.read_text(encoding="utf-8").strip()
        if examples_text:
            prompt_text = f"{prompt_text}\n\n{examples_text}"

    return prompt_text
