from types import SimpleNamespace

import llm_client


class _FakeMessages:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(
            content=[SimpleNamespace(text="cached result")],
            usage=SimpleNamespace(
                input_tokens=100,
                output_tokens=20,
                cache_creation_input_tokens=60,
                cache_read_input_tokens=40,
            ),
        )


class _FakeClient:
    def __init__(self) -> None:
        self.messages = _FakeMessages()


def test_call_llm_collects_metrics_and_uses_local_cache(monkeypatch):
    fake_client = _FakeClient()
    monkeypatch.setattr(llm_client, "CLIENT", fake_client)
    llm_client.reset_llm_runtime()

    first = llm_client.call_llm(
        "system prompt",
        "task prompt",
        max_tokens=100,
        cached_prefix="resume content",
        cache_system_prompt=True,
    )
    second = llm_client.call_llm(
        "system prompt",
        "task prompt",
        max_tokens=100,
        cached_prefix="resume content",
        cache_system_prompt=True,
    )

    metrics = llm_client.get_llm_metrics()

    assert first == "cached result"
    assert second == "cached result"
    assert fake_client.messages.calls == 1
    assert metrics["logical_calls"] == 2
    assert metrics["anthropic_requests"] == 1
    assert metrics["local_cache_hits"] == 1
    assert metrics["prompt_cache_enabled_requests"] == 1
    assert metrics["input_tokens"] == 100
    assert metrics["output_tokens"] == 20
    assert metrics["cache_creation_input_tokens"] == 60
    assert metrics["cache_read_input_tokens"] == 40
