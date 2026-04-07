"""FastAPI server wrapping the ResumAI pipeline with SSE streaming.

Endpoints:
    POST /api/run           — Start a pipeline run (multipart form)
    GET  /api/run/{id}/stream — SSE event stream for a run
    GET  /api/run/{id}/output/{filename} — Download a generated file
    POST /api/run/{id}/cover-letter — Answer the cover letter gate
    POST /api/run/{id}/low-score — Answer the low score gate
"""

import json
import logging
import uuid
import asyncio
from pathlib import Path
from threading import Thread
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipeline_runner import PipelineEvent, PipelineRunner, RunConfig

logger = logging.getLogger(__name__)

app = FastAPI(title="ResumAI", docs_url="/api/docs")

# ── In-memory run registry ────────────────────────────────────────────

_runs: dict[str, dict[str, Any]] = {}


def _get_run(run_id: str) -> dict[str, Any]:
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail="Run not found")
    return _runs[run_id]


# ── POST /api/run ─────────────────────────────────────────────────────

@app.post("/api/run")
async def start_run(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
    company_url: str = Form(""),
    job_title: str = Form("Unknown Role"),
    company_name: str = Form("Unknown Company"),
    cover_letter_choice: str = Form("ask"),
) -> dict[str, str]:
    """Accept inputs, start the pipeline in a background thread, return run_id."""
    if not resume_file.filename or not resume_file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted")

    pdf_bytes = await resume_file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty PDF file")

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required")

    if cover_letter_choice not in ("ask", "always", "skip"):
        cover_letter_choice = "ask"

    run_id = uuid.uuid4().hex[:12]
    event_queue: asyncio.Queue[PipelineEvent | None] = asyncio.Queue()
    loop = asyncio.get_event_loop()

    config = RunConfig(
        resume_pdf_bytes=pdf_bytes,
        resume_pdf_filename=resume_file.filename or "resume.pdf",
        job_description=job_description.strip(),
        company_url=company_url.strip(),
        job_title=job_title.strip(),
        company_name=company_name.strip(),
        cover_letter_choice=cover_letter_choice,
    )

    def _callback(evt: PipelineEvent) -> None:
        loop.call_soon_threadsafe(event_queue.put_nowait, evt)

    runner = PipelineRunner(config=config, callback=_callback)

    def _run_in_thread() -> None:
        try:
            runner.run()
        except Exception as exc:
            logger.exception("Pipeline run %s failed: %s", run_id, exc)
        finally:
            loop.call_soon_threadsafe(event_queue.put_nowait, None)

    thread = Thread(target=_run_in_thread, daemon=True)

    _runs[run_id] = {
        "runner": runner,
        "queue": event_queue,
        "thread": thread,
        "config": config,
    }

    thread.start()
    return {"run_id": run_id}


# ── GET /api/run/{id}/stream ──────────────────────────────────────────

@app.get("/api/run/{run_id}/stream")
async def stream_events(run_id: str) -> StreamingResponse:
    """SSE stream that emits pipeline events as they happen."""
    run = _get_run(run_id)
    queue: asyncio.Queue[PipelineEvent | None] = run["queue"]

    async def _generate():
        while True:
            evt = await queue.get()
            if evt is None:
                # Pipeline finished — send a final keepalive then close
                yield "event: done\ndata: {}\n\n"
                break
            payload = {
                "event": evt.event,
                "agent": evt.agent,
                "data": evt.data,
            }
            yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── POST /api/run/{id}/cover-letter ──────────────────────────────────

class CoverLetterDecision(BaseModel):
    generate: bool = False
    company_context: str = ""


class LowScoreDecision(BaseModel):
    proceed: bool = False


@app.post("/api/run/{run_id}/cover-letter")
async def answer_cover_letter(run_id: str, body: CoverLetterDecision) -> dict[str, str]:
    """Provide the cover letter gate answer so the pipeline can resume."""
    run = _get_run(run_id)
    runner: PipelineRunner = run["runner"]
    runner.answer_cover_letter_gate(body.generate, body.company_context)
    return {"status": "ok"}


@app.post("/api/run/{run_id}/low-score")
async def answer_low_score(run_id: str, body: LowScoreDecision) -> dict[str, str]:
    """Provide the low-score gate answer so the pipeline can continue or stop."""
    run = _get_run(run_id)
    runner: PipelineRunner = run["runner"]
    runner.answer_low_score_gate(body.proceed)
    return {"status": "ok"}


# ── GET /api/run/{id}/output/{filename} ──────────────────────────────

OUTPUTS_DIR = Path("outputs")
ALLOWED_EXTENSIONS = {".pdf", ".md", ".tex"}


@app.get("/api/run/{run_id}/output/{filename}")
async def download_output(run_id: str, filename: str) -> FileResponse:
    """Serve a generated output file for download."""
    _get_run(run_id)  # validate run exists

    # Sanitize filename — prevent path traversal
    safe_name = Path(filename).name
    if not safe_name or ".." in safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")

    ext = Path(safe_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")

    file_path = OUTPUTS_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Ensure the resolved path is within outputs directory
    try:
        file_path.resolve().relative_to(OUTPUTS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")

    media = "application/pdf" if ext == ".pdf" else "text/plain"
    return FileResponse(path=str(file_path), media_type=media, filename=safe_name)


# ── Static files — serve the React build ──────────────────────────────

UI_DIST = Path(__file__).parent / "ui" / "dist"
if UI_DIST.exists():
    app.mount("/", StaticFiles(directory=str(UI_DIST), html=True), name="ui")
