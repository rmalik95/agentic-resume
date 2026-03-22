from state import ResumeState


def test_state_contract_fields_exist() -> None:
    state = ResumeState(resume_text="r", job_description="j")

    assert hasattr(state, "match_score_before")
    assert hasattr(state, "match_score_after")
    assert hasattr(state, "missing_keywords")
    assert hasattr(state, "score_analysis")
    assert hasattr(state, "optimized_experience")
    assert hasattr(state, "review_flags")
    assert hasattr(state, "ats_verdict")
    assert hasattr(state, "ats_fixes")
    assert hasattr(state, "cover_letter")
    assert hasattr(state, "latex_resume")
    assert hasattr(state, "latex_cover_letter")
    assert hasattr(state, "pdf_resume_path")
    assert hasattr(state, "pdf_cover_letter_path")
    assert hasattr(state, "render_error")
