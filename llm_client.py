import os
import logging
import hashlib
from collections import OrderedDict
from threading import Lock
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv


MODEL = "claude-haiku-4-5-20251001"
logger = logging.getLogger(__name__)
PROMPT_CACHING_BETA = "prompt-caching-2024-07-31"
LOCAL_CACHE_MAX_ITEMS = int(os.getenv("RESUMAI_LLM_LOCAL_CACHE_SIZE", "256"))

load_dotenv()
_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLIENT = Anthropic(api_key=_API_KEY) if _API_KEY else None
_LOCAL_RESPONSE_CACHE: "OrderedDict[str, str]" = OrderedDict()
_LOCAL_CACHE_LOCK = Lock()
_METRICS_LOCK = Lock()
_LLM_METRICS: dict[str, int] = {
    "logical_calls": 0,
    "anthropic_requests": 0,
    "local_cache_hits": 0,
    "prompt_cache_enabled_requests": 0,
    "prompt_cache_fallback_retries": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
}


def _is_cache_related_error(exc: Exception) -> bool:
    message = str(exc).lower()
    markers = ["cache_control", "prompt-caching", "anthropic-beta", "beta"]
    return any(marker in message for marker in markers)


def _build_text_block(text: str, cacheable: bool) -> dict[str, Any]:
    block: dict[str, Any] = {"type": "text", "text": text}
    if cacheable:
        block["cache_control"] = {"type": "ephemeral"}
    return block


def _bump_metric(name: str, delta: int = 1) -> None:
    with _METRICS_LOCK:
        _LLM_METRICS[name] = _LLM_METRICS.get(name, 0) + delta


def _record_usage(response: Any) -> None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    fields = [
        "input_tokens",
        "output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
    ]
    for field_name in fields:
        value = getattr(usage, field_name, 0) or 0
        _bump_metric(field_name, int(value))


def get_llm_metrics() -> dict[str, int]:
    with _METRICS_LOCK:
        return dict(_LLM_METRICS)


def reset_llm_metrics() -> None:
    with _METRICS_LOCK:
        for key in _LLM_METRICS:
            _LLM_METRICS[key] = 0


def reset_llm_runtime() -> None:
    reset_llm_metrics()
    with _LOCAL_CACHE_LOCK:
        _LOCAL_RESPONSE_CACHE.clear()


def _cache_key(model: str, system: str, user_message: str, max_tokens: int, cached_prefix: str) -> str:
    raw = f"{model}\n{max_tokens}\n{system}\n{cached_prefix}\n{user_message}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _get_local_cached_response(key: str) -> str | None:
    with _LOCAL_CACHE_LOCK:
        value = _LOCAL_RESPONSE_CACHE.get(key)
        if value is not None:
            _LOCAL_RESPONSE_CACHE.move_to_end(key)
        return value


def _set_local_cached_response(key: str, value: str) -> None:
    if LOCAL_CACHE_MAX_ITEMS <= 0:
        return
    with _LOCAL_CACHE_LOCK:
        _LOCAL_RESPONSE_CACHE[key] = value
        _LOCAL_RESPONSE_CACHE.move_to_end(key)
        while len(_LOCAL_RESPONSE_CACHE) > LOCAL_CACHE_MAX_ITEMS:
            _LOCAL_RESPONSE_CACHE.popitem(last=False)


def call_llm(
    system: str,
    user_message: str,
    max_tokens: int = 1500,
    cached_prefix: str | None = None,
    cache_system_prompt: bool = True,
) -> str:
    """Call Anthropic Haiku and return text content.

    Example:
        text = call_llm("You are concise.", "Say hello", max_tokens=50)
    """
    if CLIENT is None:
        raise RuntimeError("ANTHROPIC_API_KEY is missing. Set it in your .env file.")

    _bump_metric("logical_calls", 1)

    normalized_prefix = (cached_prefix or "").strip()
    cache_enabled = cache_system_prompt or bool(normalized_prefix)
    request_cache_key = _cache_key(MODEL, system, user_message, max_tokens, normalized_prefix)

    cached_result = _get_local_cached_response(request_cache_key)
    if cached_result is not None:
        _bump_metric("local_cache_hits", 1)
        return cached_result

    system_payload: str | list[dict[str, Any]]
    if cache_system_prompt:
        system_payload = [_build_text_block(system, cacheable=True)]
    else:
        system_payload = system

    user_blocks: list[dict[str, Any]] = []
    if normalized_prefix:
        user_blocks.append(_build_text_block(normalized_prefix, cacheable=True))
    user_blocks.append(_build_text_block(user_message, cacheable=False))

    request_kwargs: dict[str, Any] = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system_payload,
        "messages": [{"role": "user", "content": user_blocks}],
    }
    if cache_enabled:
        request_kwargs["extra_headers"] = {"anthropic-beta": PROMPT_CACHING_BETA}
        _bump_metric("prompt_cache_enabled_requests", 1)

    try:
        _bump_metric("anthropic_requests", 1)
        response = CLIENT.messages.create(**request_kwargs)
    except Exception as exc:
        if cache_enabled and _is_cache_related_error(exc):
            logger.warning("Prompt caching unsupported/error; retrying without caching: %s", exc)
            _bump_metric("prompt_cache_fallback_retries", 1)
            fallback_message = user_message
            if normalized_prefix:
                fallback_message = f"{normalized_prefix}\n\n{user_message}"
            try:
                _bump_metric("anthropic_requests", 1)
                response = CLIENT.messages.create(
                    model=MODEL,
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": fallback_message}],
                )
            except Exception as second_exc:
                logger.error("Anthropic API call failed after cache fallback: %s", second_exc)
                raise RuntimeError(f"Anthropic API call failed: {second_exc}") from second_exc
        else:
            logger.error("Anthropic API call failed: %s", exc)
            raise RuntimeError(f"Anthropic API call failed: {exc}") from exc

    _record_usage(response)

    text_blocks = [block.text for block in response.content if hasattr(block, "text")]
    result = "\n".join(part for part in text_blocks if part).strip()
    if not result:
        logger.warning("LLM response was empty for model %s", MODEL)
        raise RuntimeError("LLM response was empty.")

    _set_local_cached_response(request_cache_key, result)
    return result
