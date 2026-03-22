import agents.match_score_agent as match_module
from agents.match_score_agent import MatchScoreAgent
from state import ResumeState


def test_match_score_agent_parses_response(monkeypatch):
    def fake_call_llm(system_prompt: str, user_message: str, max_tokens: int = 500) -> str:
        return (
            "SCORE: 52\n"
            "KEYWORDS: stakeholder management, Python, data pipeline, Agile, Power BI\n"
            "GAP: Limited quantified impact examples\n"
            "ANALYSIS: Good domain alignment but missing measurable outcomes."
        )

    monkeypatch.setattr(match_module, "call_llm", fake_call_llm)
    agent = MatchScoreAgent()
    state = ResumeState(resume_text="Resume", job_description="JD")

    updated = agent.run(state)
    assert updated.match_score_before == 52
    assert updated.missing_keywords == [
        "stakeholder management",
        "Python",
        "data pipeline",
        "Agile",
        "Power BI",
    ]
    assert "Limited quantified impact examples" in (updated.score_analysis or "")
