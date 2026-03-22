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

## Additional General Instructions (Previously Used)

These are baseline development instructions that should continue to apply along with the PRD-specific rules above.

### Core Behavior

- Understand the request fully before coding.
- If requirements are ambiguous, ask a concise clarifying question.
- Prefer small, safe, incremental changes over large rewrites.
- Preserve existing project structure, naming, and style unless asked to change them.

### Context Hub Usage

- For external APIs, frameworks, SDKs, or library syntax, fetch current docs with Context Hub before implementation.
- Preferred flow: `npm run chub:search -- "<query>"` then `npm run chub:get -- <id> --lang <py|js>`.
- If a docs gap or project-specific caveat is found, record it with `npm run chub:annotate -- <id> "<note>"`.
- Prefer Context Hub docs over memory-based API recall when correctness matters.

### Code Quality

- Write readable, maintainable code with clear naming.
- Keep functions focused and avoid unnecessary complexity.
- Add comments only where logic is non-obvious.
- Avoid dead code, duplicated code, and unused imports.

### Reliability

- Handle edge cases and invalid inputs.
- Add or update tests whenever behavior changes.
- Run relevant checks (lint/tests/build) after changes when possible.
- Do not silently ignore errors; surface meaningful error messages.

### Security and Safety

- Never hardcode secrets, tokens, or credentials.
- Validate external input and avoid unsafe assumptions.
- Use dependency and API usage patterns that reduce security risk.

### Performance

- Prefer efficient algorithms and data access patterns.
- Avoid premature optimization; optimize only where it matters.
- Keep memory and runtime costs reasonable for the task.

### Documentation

- Update docs when setup, behavior, or APIs change.
- Include concise usage examples for new scripts, commands, or modules.

### Git and Change Scope

- Keep edits scoped to the task.
- Do not modify unrelated files.
- Keep commit-ready changes clean and easy to review.

### Response Style

- Summarize what changed and why.
- Mention trade-offs and assumptions.
- Suggest next steps when useful (tests, refactors, follow-ups).

## Additional Engineering Rules (Execution and Quality)

Apply these rules for all implementation tasks unless explicitly overridden by the user.

### Error Handling

- Use try-except blocks for API calls.
- Log errors with appropriate levels: ERROR, WARNING, INFO.
- Provide meaningful error messages that aid debugging.
- Do not catch exceptions silently.

### Security

- Never commit credentials to version control.
- Use environment variables or AWS profiles for authentication.
- Keep sensitive data out of version control.
- Review .gitignore before committing.

### Clean Code Principles

- Follow SOLID principles; each function should have one responsibility.
- Add docstrings and type hints for all functions.
- Keep code modular; extract reusable functions into appropriate modules.
- Provide usage examples for functions where practical.
- Keep code testable and write tests before moving to the next step.

### Execution and Verification Workflow

- Run all new code immediately to verify it works.
- Execute every new notebook cell right after creation.
- Run pytest/scripts/validation commands in terminal without waiting for additional permission.
- Do not move forward with broken code.

### Iterative Failure Handling

- If execution fails, read the error carefully.
- Identify and fix the root cause (not surface-level patches).
- Re-run the failed cell/command after each fix.
- Repeat until execution succeeds.

### Pre-Progress Validation

- Confirm files exist on disk (not only in chat output).
- Confirm notebook cells execute without errors.
- Confirm tests and validation commands pass.
- Proceed only after verification is successful.

### Reuse and Modularity Rule

- Before adding a new function, check whether an existing function already implements the needed behavior.
- Reuse or extend existing functions instead of rewriting equivalent logic.
- Keep implementations modular, readable, and easy to maintain.