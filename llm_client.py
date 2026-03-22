import os

from anthropic import Anthropic
from dotenv import load_dotenv


MODEL = "claude-haiku-4-5-20251001"


def call_llm(system_prompt: str, user_message: str, max_tokens: int = 600) -> str:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is missing. Set it in your .env file.")

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    text_blocks = [block.text for block in response.content if hasattr(block, "text")]
    result = "\n".join(part for part in text_blocks if part).strip()
    if not result:
        raise RuntimeError("LLM response was empty.")
    return result
