import os
import logging

from anthropic import Anthropic
from dotenv import load_dotenv


MODEL = "claude-haiku-4-5-20251001"
logger = logging.getLogger(__name__)

load_dotenv()
_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLIENT = Anthropic(api_key=_API_KEY) if _API_KEY else None


def call_llm(system: str, user_message: str, max_tokens: int = 1500) -> str:
    """Call Anthropic Haiku and return text content.

    Example:
        text = call_llm("You are concise.", "Say hello", max_tokens=50)
    """
    if CLIENT is None:
        raise RuntimeError("ANTHROPIC_API_KEY is missing. Set it in your .env file.")

    try:
        response = CLIENT.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception as exc:
        logger.error("Anthropic API call failed: %s", exc)
        raise RuntimeError(f"Anthropic API call failed: {exc}") from exc

    text_blocks = [block.text for block in response.content if hasattr(block, "text")]
    result = "\n".join(part for part in text_blocks if part).strip()
    if not result:
        logger.warning("LLM response was empty for model %s", MODEL)
        raise RuntimeError("LLM response was empty.")
    return result
