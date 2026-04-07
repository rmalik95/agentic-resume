# ResumAI — Product Requirements Document

**Version:** 2.0  
**Date:** 1 April 2026  
**Status:** Reflects current implemented state  

---

## 1. Overview

ResumAI is a privacy-first, locally-executed, sequential multi-agent pipeline that takes a candidate's CV (as a PDF) and a target job description (as text), passes both through a chain of specialised AI agents, and produces:

- A polished, tailored CV as a **Markdown file**
- A compiled **PDF resume**
- An optional **cover letter PDF**
- A structured **terminal report** showing score delta, ATS verdict, keyword gaps, and LLM token usage

All LLM calls are made directly via the **Anthropic SDK** using the model `claude-haiku-4-5-20251001`. No agent frameworks (LangChain, CrewAI, etc.) are used. The system is fully auditable through its prompt-as-config architecture.

---

## 2. Goals and Non-Goals

### Goals

- Process a real CV PDF end-to-end in a single terminal command
- Produce an ATS-safe, recruiter-credible, tailored CV without inventing experience
- Provide before-and-after match scoring to show measurable improvement
- Keep all processing local; no data sent to third-party services other than the Anthropic API
- Reduce API costs through Anthropic prompt caching across all agent calls
- Give the candidate full visibility into what changed and why

### Non-Goals

- No web UI, no SaaS, no cloud storage
- No automatic submission of applications
- No hallucination of credentials, dates, employers, or metrics
- No modification to job description text by any agent

---

## 3. Architecture

### 3.1 Execution Model

The pipeline is strictly sequential. A single shared `ResumeState` dataclass is passed through each agent in order. Each agent reads from state, adds its outputs, and returns the updated state. No agent skips forward or reads future state.

```
PDF CV  ──► pdf_to_markdown  ──► ResumeState
                                      │
                              ┌───────▼────────┐
                              │ MatchScoreAgent │  (before)
                              └───────┬────────┘
                              ┌───────▼────────────────┐
                              │ PositioningStrategyAgent│
                              └───────┬────────────────┘
                              ┌───────▼──────────┐
                              │ JDIntelligenceAgent│
                              └───────┬──────────┘
                              ┌───────▼──────────┐
                              │ GapAnalysisAgent  │
                              └───────┬──────────┘
                              ┌───────▼──────────┐
                              │  CVRewriteAgent   │──► cv_optimized_*.md
                              └───────┬──────────┘
                              ┌───────▼──────────┐
                              │  ATSQAScanAgent   │
                              └───────┬──────────┘
                              ┌───────▼──────────┐  (optional, user gated)
                              │ CoverLetterAgent  │
                              └───────┬──────────┘
                              ┌───────▼────────┐
                              │ MatchScoreAgent │  (after)
                              └───────┬────────┘
                              ┌───────▼──────────────┐
                              │  LaTeXGeneratorAgent  │
                              └───────┬──────────────┘
                              ┌───────▼──────────┐
                              │   RendererAgent   │──► resume_optimised.pdf
                              └──────────────────┘    cover_letter.pdf
```

### 3.2 Shared State Contract

All state is held in `state.py` as a single `ResumeState` dataclass. Fields are grouped by stage.

| Group | Fields |
|---|---|
| **Inputs** | `resume_text`, `job_description` |
| **Input tracking** | `resume_pdf_path`, `company_url`, `company_context` |
| **Scoring** | `match_score_before`, `match_score_after`, `missing_keywords`, `missing_keywords_before`, `missing_keywords_after`, `score_analysis`, `score_analysis_before`, `score_analysis_after` |
| **Agent 0 — Positioning** | `positioning_strategy` |
| **Agent 1 — JD Intel** | `jd_analysis` |
| **Agent 2 — Gap Analysis** | `gap_analysis` |
| **Agent 3 — CV Rewrite** | `optimized_experience`, `review_flags` |
| **Agent 4 — ATS QA** | `ats_verdict`, `ats_fixes`, `ats_qa_report` |
| **Cover Letter** | `cover_letter` |
| **LaTeX** | `latex_resume`, `latex_cover_letter` |
| **Outputs** | `pdf_resume_path`, `pdf_cover_letter_path`, `render_error`, `output_markdown_path` |

---

## 4. Input Handling

### 4.1 CV Input — PDF Only

The candidate must supply their CV as a **PDF file**. The system converts it to Markdown before passing it to any agent.

**Conversion logic (`utils/pdf_to_markdown.py`):**

- Uses **PyMuPDF** (`fitz`) to extract text blocks per page
- Blocks sorted top-to-bottom, left-to-right per page
- Font size ≥ 14 → Markdown H1 (`#`)
- Bold font + short line + size ≥ 10 → Markdown H2 (`##`)
- Leading bullet characters (`•◦▪▸►-–—`) → Markdown list item (`-`)
- Image/non-text blocks skipped
- Duplicate headings deduplicated
- Excess blank lines collapsed

**CLI flag:** `--resume-file path/to/cv.pdf`  
**Interactive:** User is prompted for a PDF path; validated for existence and `.pdf` extension; `~` and env vars expanded.

### 4.2 JD Input — Text Only

The job description is always collected as plain text. No PDF or URL parsing is applied.

**CLI flag:** `--job-file path/to/jd.txt`  
**Interactive:** User pastes text; enter `END` on a new line to finish.

### 4.3 Optional CLI Flags

| Flag | Effect |
|---|---|
| `--company-url <url>` | Fetches company context for cover letter |
| `--job-title <string>` | Used in notifier summary |
| `--company <string>` | Used in notifier summary |
| `--cover-letter` | Always generate cover letter without prompting |
| `--no-cover-letter` | Always skip cover letter without prompting |
| `--no-notify` | Suppress Google email notification |

---

## 5. Agent Inventory

All LLM agents extend `BaseAgent` in `agents/base_agent.py`. Each has:

- A `prompt_name` class attribute pointing to `prompts/<name>.md`
- An optional `use_global_instructions = True` flag that prepends `prompts/global_writing_instructions.md` to the system prompt
- A single `run(state: ResumeState) -> ResumeState` method

### Step 0 — MatchScoreAgent (Before)

**File:** `agents/match_score_agent.py`  
**Prompt:** `prompts/match_score.md`  
**Purpose:** Establish a numeric baseline ATS match score before any optimisation.

**Inputs:** `resume_text`, `job_description`  
**Outputs:** `match_score_before`, `missing_keywords`, `missing_keywords_before`, `score_analysis`, `score_analysis_before`

**Output format parsed:** `SCORE: <n>`, `KEYWORDS: <comma list>`, `GAP: <text>`, `ANALYSIS: <text>`  
**Max tokens:** 500

---

### Agent 0 — PositioningStrategyAgent

**File:** `agents/positioning_strategy_agent.py`  
**Prompt:** `prompts/positioning_strategy.md`  
**Purpose:** Determine how to frame the candidate before any writing begins.

**Structured output (10 sections):**
1. Best target headline for the CV
2. Core professional identity to project
3. Top 5 strengths to emphasise
4. Experiences to elevate
5. Experiences to reduce or de-emphasise
6. Seniority framing recommendation
7. Biggest misread risk
8. Summary strategy (3 lines)
9. Experience strategy (5 bullets)
10. Keyword strategy — mirror vs avoid

**Inputs:** `resume_text`, `job_description`  
**Outputs:** `positioning_strategy`  
**Max tokens:** 900

---

### Agent 1 — JDIntelligenceAgent

**File:** `agents/jd_intelligence_agent.py`  
**Prompt:** `prompts/jd_intelligence.md`  
**Purpose:** Extract deep recruiter-calibrated intelligence from the job description across 12 dimensions.

**Structured output (12 sections):**
1. Target role summary
2. Top 20 keywords ranked by importance
3. Required hard skills
4. Required soft skills
5. Seniority signals
6. Tools, platforms, frameworks, certifications
7. Industry and domain terminology
8. Business problems this role is solving
9. Hidden expectations
10. Culture and working style signals
11. Ideal candidate profile
12. Tailoring priorities for the CV

**Inputs:** `job_description`  
**Outputs:** `jd_analysis`  
**Max tokens:** 1500

---

### Agent 2 — GapAnalysisAgent

**File:** `agents/gap_analysis_agent.py`  
**Prompt:** `prompts/gap_analysis.md`  
**Purpose:** Produce a brutally honest comparison of the CV against the target role.

**Structured output (13 sections):**
1. Overall match score (1–10)
2. First-impression verdict
3. Narrative and positioning gaps
4. Top missing keywords ranked by importance
5. Missing or weakly evidenced skills (absent / weak / undersold)
6. Technical and domain gaps
7. Seniority alignment
8. Work history and chronology risks
9. Achievement gaps
10. Overused, generic, or weak language
11. Irrelevant or low-value content
12. Most undersold strengths
13. Top 10 changes needed

Consumes `positioning_strategy` and `jd_analysis` from prior agents as context.  
**Inputs:** `resume_text`, `job_description`, `positioning_strategy`, `jd_analysis`  
**Outputs:** `gap_analysis`  
**Max tokens:** 1500

---

### Agent 3 — CVRewriteAgent

**File:** `agents/cv_rewrite_agent.py`  
**Prompt:** `prompts/cv_rewrite.md`  
**Global instructions:** Yes (`use_global_instructions = True`)  
**Purpose:** Produce a fully tailored, ATS-safe CV rewrite with keyword integration map and remaining evidence gaps.

**Non-negotiable rules enforced by prompt:**
- No invented employers, dates, titles, tools, projects, qualifications, or achievements
- Missing metrics inserted as `[bracket placeholders]`
- No clichés (`results-driven`, `proven track record`, etc.)
- Bullet variety in verbs and sentence structure
- Present tense for current role; past tense for previous roles

**Structured output (8 sections):**
1. Target job title
2. Professional summary
3. Core skills (grouped by category)
4. Professional experience
5. Education
6. Optional additional section
7. Keyword integration map (table)
8. Remaining evidence gaps

**Inputs:** `resume_text`, `job_description`, `positioning_strategy`, `jd_analysis`, `gap_analysis`  
**Outputs:** `optimized_experience` (full Markdown CV), `review_flags` (all `[bracket]` placeholders extracted)  
**Max tokens:** 3000  

After this agent runs, `_write_output_markdown()` immediately saves `outputs/cv_optimized_<timestamp>.md`.

---

### Agent 4 — ATSQAScanAgent

**File:** `agents/ats_qa_scan_agent.py`  
**Prompt:** `prompts/ats_qa_scan.md`  
**Global instructions:** Yes (`use_global_instructions = True`)  
**Purpose:** Act as both an ATS parser and a 10-second recruiter screen across 11 dimensions.

**Structured output (11 sections):**
1. ATS compatibility score (1–100)
2. Recruiter first-impression score (1–10)
3. Keyword coverage — present / missing / overused
4. Narrative and positioning check
5. Chronology and structure check
6. Achievement quality check
7. Seniority alignment check
8. Authenticity and AI-risk check
9. ATS parsing risk check
10. Rejection risks
11. Exact final changes required

Parsed outputs:
- `ats_verdict` → `ATS <n>/100, Recruiter <n>/10`
- `ats_fixes` → rejection risks + exact final changes
- `ats_qa_report` → full structured response

**Inputs:** `job_description`, `optimized_experience`  
**Max tokens:** 1500

---

### Cover Letter — CoverLetterAgent (Optional)

**File:** `agents/cover_letter_agent.py`  
**Prompt:** `prompts/cover_letter.md`  
**Purpose:** Generate a targeted cover letter using the optimised CV context.

**Gate:** User is asked interactively `Generate a cover letter? [yes/no]` unless `--cover-letter` or `--no-cover-letter` CLI flags are set.

**Inputs:** `resume_text`, `job_description`, `optimized_experience`, `company_context` (if fetched)  
**Outputs:** `cover_letter`  
**Max tokens:** 600

---

### Step N — MatchScoreAgent (After)

Same agent re-run after `CVRewriteAgent` has set `optimized_experience`. The second pass automatically detects this and writes to `match_score_after`, `missing_keywords_after`, `score_analysis_after`.

---

### LaTeXGeneratorAgent

**File:** `agents/latex_generator_agent.py`  
**Prompt:** `prompts/latex_generator.md`  
**Purpose:** Emit two valid LaTeX documents (resume + cover letter) using moderncv/classic/blue template.

Key responsibilities:
- Extract profile fields (`name`, `email`, `phone`) directly from `resume_text` via regex — not from `optimized_experience`
- Sanitize all `[INSERT ...]` placeholders
- Patch `\name{}{}`, `\phone[mobile]{}`, `\email{}` using extracted fields
- Strip ` ```latex ``` ` fences from LLM output
- Split output at `---COVERLETTER---` delimiter (with fallback to second `\documentclass`)

**Inputs:** `resume_text`, `job_description`, `optimized_experience`, `cover_letter`  
**Outputs:** `latex_resume`, `latex_cover_letter`  
**Max tokens:** 3000

---

### RendererAgent

**File:** `agents/renderer_agent.py`  
**Purpose:** Compile LaTeX to PDF. No LLM call.

**Fallback chain (per document):**
1. LaTeX.Online API — `GET /compile?text=<url-encoded LaTeX>`
2. Local `pdflatex` (if installed)
3. Normalized LaTeX retry (strips duplicate `\usepackage{hyperref}` for moderncv)
4. Save raw `.tex` to `outputs/<stem>_fallback.tex` for manual Overleaf upload

**Validation:** Output must start with `%PDF-` header and be >100 bytes.  
**Outputs:** `pdf_resume_path`, `pdf_cover_letter_path`, `render_error`

---

## 6. LLM Client & Prompt Caching

**File:** `llm_client.py`  
**Model:** `claude-haiku-4-5-20251001`  
**SDK:** Anthropic Python SDK (raw, no framework)

### Prompt Caching Strategy

All five LLM agents use a two-level caching approach:

1. **Anthropic server-side prompt caching** (`prompt-caching-2024-07-31` beta)  
   - Resume text + job description sent as a `cached_prefix` with `cache_control: {type: ephemeral}`  
   - System prompt also cached with `cache_system_prompt=True`  
   - Activates when prefix content exceeds Anthropic's minimum token threshold (~1024 tokens)

2. **Local in-process LRU cache**  
   - SHA-256 keyed on `(model, system, cached_prefix, user_message, max_tokens)`  
   - Configurable size via `RESUMAI_LLM_LOCAL_CACHE_SIZE` env var (default: 256)  
   - Prevents duplicate API calls for identical inputs within a session

### Metrics Tracked Per Run

| Metric | Description |
|---|---|
| `logical_calls` | Total calls made to `call_llm()` |
| `anthropic_requests` | Calls that reached the Anthropic API |
| `local_cache_hits` | Calls served from local LRU cache |
| `prompt_cache_enabled_requests` | Calls sent with caching beta header |
| `prompt_cache_fallback_retries` | Retries after cache-related errors |
| `input_tokens` | Total input tokens consumed |
| `output_tokens` | Total output tokens consumed |
| `cache_creation_input_tokens` | Tokens written to Anthropic's cache |
| `cache_read_input_tokens` | Tokens read from Anthropic's cache (saved cost) |

Metrics are reset at the start of each `main()` call and printed in the final report.

---

## 7. Prompt Architecture

All system prompts are stored as Markdown files in `prompts/`. No prompt text is hardcoded in Python files.

| File | Agent | Purpose |
|---|---|---|
| `prompts/match_score.md` | MatchScoreAgent | ATS scoring rubric |
| `prompts/positioning_strategy.md` | PositioningStrategyAgent | CV positioning framework |
| `prompts/jd_intelligence.md` | JDIntelligenceAgent | JD analysis framework |
| `prompts/gap_analysis.md` | GapAnalysisAgent | CV vs JD comparison rubric |
| `prompts/cv_rewrite.md` | CVRewriteAgent | Tailored CV rewrite rules |
| `prompts/ats_qa_scan.md` | ATSQAScanAgent | ATS + recruiter QA scan |
| `prompts/cover_letter.md` | CoverLetterAgent | Cover letter generation rules |
| `prompts/latex_generator.md` | LaTeXGeneratorAgent | LaTeX output spec |
| `prompts/global_writing_instructions.md` | CVRewriteAgent, ATSQAScanAgent | Shared bullet/verb/structure rules |
| `prompts/ats_checker.md` | ATSCheckerAgent (legacy) | Legacy agent prompt (kept for reference) |
| `prompts/experience_optimizer.md` | ExperienceOptimizerAgent (legacy) | Legacy agent prompt (kept for reference) |

### Global Writing Instructions

Applied automatically via `use_global_instructions = True` on agents that produce or review CV content:

- No repeated action verbs across consecutive bullets
- No forced uniform sentence patterns
- Prefer specific nouns over vague business language
- Show what changed, improved, reduced, streamlined, delivered, or enabled
- Summary must be evidence-based, not personality-based
- First 3 bullets of most recent role must be strongest and most JD-relevant
- Internal progression between multiple roles at one employer must be explicit
- Remove low-value routine duty bullets unless essential for the target role

---

## 8. Output Files

| File | Description |
|---|---|
| `outputs/cv_optimized_<timestamp>.md` | Polished CV as Markdown (saved immediately after CVRewriteAgent) |
| `outputs/resume_optimised.pdf` | Compiled PDF resume |
| `outputs/cover_letter.pdf` | Compiled PDF cover letter (if generated) |
| `outputs/<stem>_fallback.tex` | Raw LaTeX saved if rendering fails |

---

## 9. Terminal Report

Printed at the end of every run:

```
============================================================
RESULTS
============================================================
Score before optimisation : 52/100
Score after optimisation  : 74/100 (+22 points)
Missing keywords added    : stakeholder management, Python, Agile
ATS verdict               : ATS 85/100, Recruiter 8/10
Score analysis (before)   : Missing quantified outcomes
Score analysis (after)    : Strong keyword alignment
Keywords still missing    : data governance
Bullets flagged [REVIEW]  : 3
------------------------------------------------------------
Bullets requiring your review:
- X% improvement in ETL pipeline
- [Q3 2023]
- [team size]
------------------------------------------------------------
Optimised CV Markdown     : /path/to/outputs/cv_optimized_20260401_123456.md
Resume PDF                : outputs/resume_optimised.pdf
Cover letter PDF          : outputs/cover_letter.pdf
------------------------------------------------------------
LLM cache metrics
Logical LLM calls         : 8
Anthropic API requests    : 8
Local cache hits          : 0
Prompt-cache requests     : 8
Prompt-cache retries      : 0
Input tokens              : 12482
Output tokens             : 4821
Cache write tokens        : 9231
Cache read tokens         : 7144
============================================================
```

---

## 10. File Structure

```
agentic-resume/
├── agents/
│   ├── base_agent.py              # Abstract base with prompt loading + global instructions
│   ├── match_score_agent.py       # Scoring (before and after)
│   ├── positioning_strategy_agent.py
│   ├── jd_intelligence_agent.py
│   ├── gap_analysis_agent.py
│   ├── cv_rewrite_agent.py
│   ├── ats_qa_scan_agent.py
│   ├── cover_letter_agent.py
│   ├── latex_generator_agent.py
│   └── renderer_agent.py
├── prompts/
│   ├── global_writing_instructions.md
│   ├── match_score.md
│   ├── positioning_strategy.md
│   ├── jd_intelligence.md
│   ├── gap_analysis.md
│   ├── cv_rewrite.md
│   ├── ats_qa_scan.md
│   ├── cover_letter.md
│   └── latex_generator.md
├── utils/
│   ├── prompt_loader.py           # Loads prompts; appends examples and global instructions
│   └── pdf_to_markdown.py         # PyMuPDF-based PDF → Markdown converter
├── tests/
│   ├── test_state_contract.py
│   ├── test_match_score_agent.py
│   ├── test_ats_checker_agent.py
│   ├── test_pipeline_smoke.py
│   ├── test_cover_letter_gate.py
│   ├── test_llm_client_metrics.py
│   ├── test_pdf_to_markdown.py
│   └── test_pdf_input_pipeline.py
├── outputs/                       # All generated files written here
├── state.py                       # ResumeState dataclass
├── llm_client.py                  # Anthropic SDK wrapper + caching + metrics
├── input_collector.py             # collect_pdf_path, ask_yes_no, collect_multiline
├── main.py                        # CLI entry point and pipeline orchestration
├── base_agent.py                  # Shim re-exporting agents/base_agent.BaseAgent
├── notifier.py                    # Optional Google email notifier
├── requirements.txt
├── install_resumai.sh
├── run_resumai.sh
└── .env.example
```

---

## 11. Setup and Usage

### First-Time Setup

```bash
bash install_resumai.sh
```

Creates `.venv`, installs dependencies, copies `.env.example` → `.env`.

### Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...           # Required
RESUMAI_LLM_LOCAL_CACHE_SIZE=256       # Optional; default 256
```

### Run

```bash
# Interactive (prompts for PDF path and JD paste)
./run_resumai.sh

# Non-interactive with files
python main.py --resume-file cv.pdf --job-file jd.txt --no-notify

# Skip cover letter
python main.py --resume-file cv.pdf --job-file jd.txt --no-cover-letter

# Always generate cover letter + company context
python main.py --resume-file cv.pdf --job-file jd.txt \
  --cover-letter \
  --company-url https://company.com/about \
  --company "Acme Corp" --job-title "Data Analyst"
```

### Run Tests

```bash
.venv/bin/python -m pytest -q
```

---

## 12. Quality Guardrails

| Rule | Enforcement |
|---|---|
| No invention | Prompt instructions on CVRewriteAgent and ATSQAScanAgent forbid inventing any credential, date, employer, tool, or metric |
| Placeholder visibility | `[bracket]` tokens surfaced in `review_flags` and printed in terminal report |
| Scope isolation | Each agent reads only its declared inputs from state; no agent writes to another agent's fields |
| Score audit | Before-and-after delta shown explicitly in report |
| Prompt immutability | System prompts live in `prompts/` as versioned Markdown; never hardcoded in Python |
| No secret commits | `.env`, `credentials.json`, `token.json` in `.gitignore` |

---

## 13. Constraints

| Constraint | Value |
|---|---|
| Language | Python 3.11+ |
| LLM Provider | Anthropic SDK (raw) |
| Model | `claude-haiku-4-5-20251001` |
| Agent pattern | `class Agent: def run(state) -> state` |
| PDF input | PyMuPDF (`pymupdf>=1.24.0`) |
| Prompt storage | `prompts/*.md` files only |
| No frameworks | No LangChain, CrewAI, or similar |
| Local execution | No cloud storage; all outputs written to `outputs/` |
| JD input | Plain text only (paste or `--job-file`) |
