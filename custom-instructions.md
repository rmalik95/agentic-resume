# ResumAI Custom Instructions

Use these instructions for all future development tasks in this repository.
Source of truth: [ResumAI_PRD.pdf](ResumAI_PRD.pdf).

## Non-Negotiable Constraints

- Python 3.11+.
- LLM provider: Anthropic SDK (raw SDK only).
- Model string must be exactly: `claude-haiku-4-5-20251001`.
- No agent frameworks: no LangChain, no CrewAI.
- Each agent is a class with one method: `run(state: ResumeState) -> ResumeState`.
- All system prompts must be loaded from `prompts/*.md` via `utils/prompt_loader.py`.
- Never hardcode system prompts inside Python files.
- Never modify `.env` automatically; only read from it.

## Product Intent

- Build a privacy-first, local, sequential multi-agent resume optimization pipeline.
- Main UX promise: one command in terminal, optimized resume + cover letter PDFs out.
- Keep behavior auditable and deterministic through prompt-as-config architecture.

## Required Architecture

- Shared dataclass state object flows sequentially through all agents.
- Agent categories:
  - Agents 1-5 are LLM agents.
  - Agent 6 is I/O renderer (no LLM prompt).
- Renderer fallback chain is mandatory:
  1. Try LaTeX.Online API.
  2. Fallback to local `pdflatex` if available.
  3. If both fail, save raw `.tex` to `outputs/` for manual Overleaf upload.

## Required Agent Inventory

- `MatchScoreAgent`
- `ExperienceOptimizerAgent`
- `ATSCheckerAgent`
- `CoverLetterAgent`
- `LaTeXGeneratorAgent`
- `RendererAgent`

## ResumeState Contract

Keep these fields available and consistently used across the pipeline:

- Inputs: `resume_text`, `job_description`
- Scoring: `match_score_before`, `match_score_after`, `missing_keywords`, `score_analysis`
- Optimization: `optimized_experience`, `review_flags`
- ATS: `ats_verdict`, `ats_fixes`
- Cover letter: `cover_letter`
- LaTeX: `latex_resume`, `latex_cover_letter`
- Outputs: `pdf_resume_path`, `pdf_cover_letter_path`, `render_error`

## Prompt Governance

- Prompt files are product decisions and must be treated as versioned config.
- Do not paraphrase PRD-defined prompt blocks when asked to copy them.
- If output quality changes, adjust prompt files first before Python logic.

## Quality Guardrails (Always Enforce)

- No invention rule: never invent metrics, tools, dates, credentials, or achievements.
- Scope isolation: each agent only performs its declared role.
- Human review visibility: preserve `[REVIEW]` tags for uncertain bullets.
- Final output should clearly report score delta and ATS verdict.

## CLI and UX Expectations

- Support multiline terminal input with `END` terminator when requested.
- Print clear step-by-step progress logs for each agent.
- Final summary must include:
  - score before and after,
  - missing keywords added,
  - ATS verdict and issues,
  - `[REVIEW]` bullets,
  - output PDF paths.

## Implementation Order For Future Tasks

When implementing from scratch or rebuilding modules, use this order:

1. `state.py`
2. `utils/prompt_loader.py`
3. `llm_client.py`
4. `base_agent.py`
5. prompt files under `prompts/`
6. agents 1-5
7. `renderer_agent.py`
8. `input_collector.py`
9. `main.py`

## Security and Local-Only Rules

- Never commit secrets.
- Keep `.env`, `credentials.json`, and `token.json` out of version control.
- Any browser-auth or cloud-console action must be requested from the user as a manual step.

## Copilot Working Rule

Before writing code, restate the target PRD section being implemented and ensure generated code stays inside that scope.