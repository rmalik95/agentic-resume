import os
import logging

from anthropic import Anthropic
from dotenv import load_dotenv


MODEL = "claude-haiku-4-5-20251001"
logger = logging.getLogger(__name__)


def call_llm(system_prompt: str, user_message: str, max_tokens: int = 1500) -> str:
    """Call Anthropic Haiku and return text content.

    Example:
        text = call_llm("You are concise.", "Say hello", max_tokens=50)
    """
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is missing. Set it in your .env file.")

    client = Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception as exc:
        logger.error("Anthropic API call failed: %s", exc)
        raise RuntimeError("Anthropic API call failed.") from exc

    text_blocks = [block.text for block in response.content if hasattr(block, "text")]
    result = "\n".join(part for part in text_blocks if part).strip()
    if not result:
        logger.warning("LLM response was empty for model %s", MODEL)
        raise RuntimeError("LLM response was empty.")
    return result
