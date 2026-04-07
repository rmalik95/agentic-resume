import agents.ats_checker_agent as ats_module
from agents.ats_checker_agent import ATSCheckerAgent
from state import ResumeState


def test_ats_checker_uses_full_resume_context(monkeypatch):
    captured = {}

    def fake_call_llm(
        system_prompt: str,
        user_message: str,
        max_tokens: int = 700,
        cached_prefix: str | None = None,
        cache_system_prompt: bool = True,
    ) -> str:
        captured["message"] = user_message
        captured["cached_prefix"] = cached_prefix
        return (
            "ISSUES:\n"
            "- [MINOR] Date format inconsistent: use MMM YYYY\n"
            "VERDICT: Conditional Pass\n"
            "SUMMARY: Mostly ATS-ready with minor issue."
        )

    monkeypatch.setattr(ats_module, "call_llm", fake_call_llm)

    state = ResumeState(
        resume_text="Full resume with contact section and education",
        job_description="JD",
    )
    state.optimized_experience = "Optimized experience only"

    updated = ATSCheckerAgent().run(state)

    assert "Optimized experience section" in captured["message"]
    assert "Resume text:" in (captured.get("cached_prefix") or "")
    assert "Full resume with contact section and education" in (captured.get("cached_prefix") or "")
    assert updated.ats_verdict == "Conditional Pass"
    assert "Date format inconsistent" in (updated.ats_fixes or "")
