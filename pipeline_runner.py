"""Event-emitting pipeline runner for both CLI and UI use.

Wraps the sequential agent pipeline and fires callbacks at each step,
enabling SSE streaming to the web UI without changing any agent logic.
"""

import datetime
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from agents.ats_qa_scan_agent import ATSQAScanAgent
from agents.cover_letter_agent import CoverLetterAgent
from agents.cv_rewrite_agent import CVRewriteAgent
from agents.gap_analysis_agent import GapAnalysisAgent
from agents.jd_intelligence_agent import JDIntelligenceAgent
from agents.latex_generator_agent import LaTeXGeneratorAgent
from agents.match_score_agent import MatchScoreAgent
from agents.positioning_strategy_agent import PositioningStrategyAgent
from agents.renderer_agent import RendererAgent
from llm_client import get_llm_metrics, reset_llm_metrics
from state import ResumeState
from utils.pdf_to_markdown import pdf_to_markdown


# Agent keys used as identifiers in SSE events
AGENT_KEYS = [
    "pdf_parse",
    "match_score_before",
    "positioning_strategy",
    "jd_intelligence",
    "gap_analysis",
    "cv_rewrite",
    "ats_qa_scan",
    "cover_letter",
    "match_score_after",
    "latex_generator",
    "renderer",
]

AGENT_DISPLAY_NAMES: dict[str, str] = {
    "pdf_parse": "Reading your CV",
    "match_score_before": "Scoring your CV (before)",
    "positioning_strategy": "Positioning strategy",
    "jd_intelligence": "Job description analysis",
    "gap_analysis": "Gap analysis",
    "cv_rewrite": "Rewriting your CV",
    "ats_qa_scan": "ATS & recruiter check",
    "cover_letter": "Cover letter",
    "match_score_after": "Scoring your CV (after)",
    "latex_generator": "Generating LaTeX",
    "renderer": "Compiling PDF",
}

LOW_MATCH_SCORE_THRESHOLD = 50


@dataclass
class PipelineEvent:
    """A single event emitted by the pipeline runner."""
    event: str  # agent_start, agent_complete, agent_error, pipeline_complete, cover_letter_gate
    agent: str = ""
    data: dict[str, Any] = field(default_factory=dict)


EventCallback = Callable[[PipelineEvent], None]


@dataclass
class RunConfig:
    """Configuration for a single pipeline run."""
    resume_pdf_bytes: bytes = b""
    resume_pdf_filename: str = ""
    job_description: str = ""
    company_url: str = ""
    job_title: str = "Unknown Role"
    company_name: str = "Unknown Company"
    cover_letter_choice: str = "ask"  # "ask", "always", "skip"


class PipelineRunner:
    """Runs the agent pipeline and emits events for each step."""

    def __init__(self, config: RunConfig, callback: EventCallback) -> None:
        self._config = config
        self._emit = callback
        self._state: ResumeState | None = None
        self._cover_letter_event = threading.Event()
        self._cover_letter_answer: bool = False
        self._cover_letter_context: str = ""
        self._low_score_event = threading.Event()
        self._low_score_answer: bool = False
        self._missing_keywords_added: list[str] = []

    @property
    def state(self) -> ResumeState | None:
        return self._state

    def answer_cover_letter_gate(self, generate: bool, company_context: str = "") -> None:
        """Provide the answer for the cover letter gate (called from the HTTP endpoint)."""
        self._cover_letter_answer = generate
        self._cover_letter_context = company_context
        self._cover_letter_event.set()

    def answer_low_score_gate(self, proceed: bool) -> None:
        """Provide the answer for the low-score gate (called from the HTTP endpoint)."""
        self._low_score_answer = proceed
        self._low_score_event.set()

    def run(self) -> None:
        """Execute the full pipeline, emitting events at each step."""
        reset_llm_metrics()
        config = self._config

        # Parse PDF
        resume_text = self._run_step("pdf_parse", self._parse_pdf)
        if resume_text is None:
            return

        state = ResumeState(resume_text=resume_text, job_description=config.job_description)
        state.company_url = config.company_url or None
        self._state = state

        # Match score before
        self._run_agent_step("match_score_before", MatchScoreAgent(), state)
        self._missing_keywords_added = list(state.missing_keywords)

        baseline_score = state.match_score_before or 0
        if baseline_score < LOW_MATCH_SCORE_THRESHOLD:
            should_continue = self._resolve_low_score_gate(baseline_score)
            if not should_continue:
                self._emit(PipelineEvent(
                    event="pipeline_complete",
                    data=self._build_final_payload(
                        state,
                        terminated_early=True,
                        termination_reason=(
                            f"Stopped by user because baseline match score "
                            f"({baseline_score}/100) is below {LOW_MATCH_SCORE_THRESHOLD}."
                        ),
                    ),
                ))
                return

        # Positioning strategy
        self._run_agent_step("positioning_strategy", PositioningStrategyAgent(), state)

        # JD Intelligence
        self._run_agent_step("jd_intelligence", JDIntelligenceAgent(), state)

        # Gap Analysis
        self._run_agent_step("gap_analysis", GapAnalysisAgent(), state)

        # CV Rewrite
        self._run_agent_step("cv_rewrite", CVRewriteAgent(), state)

        # Save Markdown output
        state.output_markdown_path = self._write_output_markdown(state)

        # ATS QA Scan
        self._run_agent_step("ats_qa_scan", ATSQAScanAgent(), state)

        # Cover letter gate
        generate_cl = self._resolve_cover_letter_gate()
        if generate_cl:
            if self._cover_letter_context:
                state.company_context = self._cover_letter_context
            self._run_agent_step("cover_letter", CoverLetterAgent(), state)
        else:
            self._emit(PipelineEvent(
                event="agent_complete",
                agent="cover_letter",
                data={"display_name": AGENT_DISPLAY_NAMES["cover_letter"],
                      "content": "Skipped by user.", "skipped": True, "elapsed_ms": 0},
            ))

        # Match score after
        self._run_agent_step("match_score_after", MatchScoreAgent(), state)

        # LaTeX + Renderer
        self._run_agent_step("latex_generator", LaTeXGeneratorAgent(), state)
        self._run_agent_step("renderer", RendererAgent(), state)

        # Pipeline complete
        self._emit(PipelineEvent(
            event="pipeline_complete",
            data=self._build_final_payload(state),
        ))

    # ── Internal helpers ──────────────────────────────────────────────

    def _parse_pdf(self) -> str:
        """Convert uploaded PDF bytes to Markdown text."""
        import tempfile
        config = self._config
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(config.resume_pdf_bytes)
            tmp.flush()
            md_text = pdf_to_markdown(tmp.name)
        return md_text

    def _run_step(self, agent_key: str, fn: Callable, *args: Any) -> Any:
        """Run a non-agent step with event emission."""
        display = AGENT_DISPLAY_NAMES[agent_key]
        self._emit(PipelineEvent(
            event="agent_start",
            agent=agent_key,
            data={"display_name": display},
        ))
        t0 = time.monotonic()
        try:
            result = fn(*args)
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            self._emit(PipelineEvent(
                event="agent_error",
                agent=agent_key,
                data={"display_name": display, "error": str(exc), "elapsed_ms": elapsed_ms},
            ))
            return None
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        # Build content for pdf_parse
        content_data: dict[str, Any] = {"display_name": display, "elapsed_ms": elapsed_ms}
        if agent_key == "pdf_parse" and isinstance(result, str):
            lines = result.strip().splitlines()
            headings = [l.lstrip("# ").strip() for l in lines if l.startswith("#")]
            content_data["content"] = result
            content_data["word_count"] = len(result.split())
            content_data["headings"] = headings

        self._emit(PipelineEvent(event="agent_complete", agent=agent_key, data=content_data))
        return result

    def _run_agent_step(self, agent_key: str, agent_obj: object, state: ResumeState) -> None:
        """Run one LLM agent with event emission."""
        display = AGENT_DISPLAY_NAMES[agent_key]
        self._emit(PipelineEvent(
            event="agent_start",
            agent=agent_key,
            data={"display_name": display},
        ))
        t0 = time.monotonic()
        try:
            self._state = agent_obj.run(state)  # type: ignore[union-attr]
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            self._emit(PipelineEvent(
                event="agent_error",
                agent=agent_key,
                data={"display_name": display, "error": str(exc), "elapsed_ms": elapsed_ms},
            ))
            return
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        # Get token metrics snapshot for this agent
        metrics = get_llm_metrics()

        content_data: dict[str, Any] = {
            "display_name": display,
            "elapsed_ms": elapsed_ms,
            "tokens_in": metrics.get("input_tokens", 0),
            "tokens_out": metrics.get("output_tokens", 0),
        }

        # Add agent-specific structured data
        self._enrich_agent_data(agent_key, state, content_data)

        self._emit(PipelineEvent(event="agent_complete", agent=agent_key, data=content_data))

    def _enrich_agent_data(self, key: str, state: ResumeState, data: dict[str, Any]) -> None:
        """Add agent-specific fields to the completion event data."""
        if key == "match_score_before":
            data["match_score"] = state.match_score_before
            data["missing_keywords"] = state.missing_keywords_before or state.missing_keywords
            data["score_analysis"] = state.score_analysis_before or state.score_analysis
        elif key == "match_score_after":
            data["match_score"] = state.match_score_after
            data["match_score_before"] = state.match_score_before
            data["missing_keywords_before"] = self._missing_keywords_added
            data["missing_keywords_after"] = state.missing_keywords_after or []
            data["score_analysis"] = state.score_analysis_after
        elif key == "positioning_strategy":
            data["content"] = state.positioning_strategy or ""
        elif key == "jd_intelligence":
            data["content"] = state.jd_analysis or ""
        elif key == "gap_analysis":
            data["content"] = state.gap_analysis or ""
        elif key == "cv_rewrite":
            data["content"] = state.optimized_experience or ""
            data["review_flags"] = state.review_flags
            data["output_markdown_path"] = state.output_markdown_path
        elif key == "ats_qa_scan":
            data["content"] = state.ats_qa_report or ""
            data["ats_verdict"] = state.ats_verdict
            data["ats_fixes"] = state.ats_fixes
        elif key == "cover_letter":
            data["content"] = state.cover_letter or ""
        elif key == "latex_generator":
            has_resume = bool(state.latex_resume)
            has_cover = bool(state.latex_cover_letter)
            data["content"] = (
                f"LaTeX generated for {'resume' if has_resume else ''}{'and cover letter' if has_cover else ''}. Compiling…"
            )
        elif key == "renderer":
            data["pdf_resume_path"] = state.pdf_resume_path
            data["pdf_cover_letter_path"] = state.pdf_cover_letter_path
            data["render_error"] = state.render_error

    def _resolve_cover_letter_gate(self) -> bool:
        """Determine whether to generate a cover letter, blocking if needed."""
        choice = self._config.cover_letter_choice
        if choice == "always":
            return True
        if choice == "skip":
            return False
        # "ask" — emit gate event and wait for answer
        self._emit(PipelineEvent(event="cover_letter_gate", data={}))
        self._cover_letter_event.wait()
        return self._cover_letter_answer

    def _resolve_low_score_gate(self, score: int) -> bool:
        """Pause pipeline when baseline score is low, then wait for user decision."""
        self._emit(PipelineEvent(
            event="low_score_gate",
            data={
                "match_score": score,
                "threshold": LOW_MATCH_SCORE_THRESHOLD,
            },
        ))
        self._low_score_event.wait()
        return self._low_score_answer

    def _write_output_markdown(self, state: ResumeState) -> str:
        """Write the optimised CV Markdown file."""
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        md_path = (outputs_dir / f"cv_optimized_{timestamp}.md").resolve()
        md_path.write_text(state.optimized_experience or "", encoding="utf-8")
        return str(md_path)

    def _build_final_payload(
        self,
        state: ResumeState,
        terminated_early: bool = False,
        termination_reason: str = "",
    ) -> dict[str, Any]:
        """Build the pipeline_complete payload."""
        metrics = get_llm_metrics()
        # Haiku pricing: ~$0.25/M input, ~$1.25/M output
        est_cost = (metrics.get("input_tokens", 0) * 0.25 + metrics.get("output_tokens", 0) * 1.25) / 1_000_000

        keywords_before = set(self._missing_keywords_added)
        keywords_after = set(state.missing_keywords_after or [])
        keywords_added = list(keywords_before - keywords_after)

        return {
            "match_score_before": state.match_score_before,
            "match_score_after": state.match_score_after,
            "score_analysis_before": state.score_analysis_before or state.score_analysis,
            "score_analysis_after": state.score_analysis_after,
            "missing_keywords_before": self._missing_keywords_added,
            "missing_keywords_after": state.missing_keywords_after or [],
            "keywords_added": keywords_added,
            "ats_verdict": state.ats_verdict,
            "ats_fixes": state.ats_fixes,
            "review_flags": state.review_flags,
            "optimized_experience": state.optimized_experience,
            "cover_letter": state.cover_letter,
            "pdf_resume_path": state.pdf_resume_path,
            "pdf_cover_letter_path": state.pdf_cover_letter_path,
            "output_markdown_path": state.output_markdown_path,
            "render_error": state.render_error,
            "positioning_strategy": state.positioning_strategy,
            "jd_analysis": state.jd_analysis,
            "gap_analysis": state.gap_analysis,
            "ats_qa_report": state.ats_qa_report,
            "terminated_early": terminated_early,
            "termination_reason": termination_reason,
            "metrics": {
                "anthropic_requests": metrics.get("anthropic_requests", 0),
                "input_tokens": metrics.get("input_tokens", 0),
                "output_tokens": metrics.get("output_tokens", 0),
                "cache_creation_input_tokens": metrics.get("cache_creation_input_tokens", 0),
                "cache_read_input_tokens": metrics.get("cache_read_input_tokens", 0),
                "estimated_cost": round(est_cost, 4),
            },
        }
