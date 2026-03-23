# Agentic Resume Optimiser

ResumAI PRD-aligned local multi-agent resume pipeline.

## One-Command Run

Use this from the repo root to install dependencies and run the full pipeline:

```bash
./run_resumai.sh
```

For first-time setup only, you can also run a dedicated installer:

```bash
./install_resumai.sh
```

The script will:
- create `.venv` if missing,
- install dependencies from `requirements.txt`,
- create `.env` from `.env.example` if needed,
- install Context Hub tooling with `npm install` when `package.json` is present,
- run `main.py` with `--no-notify` by default.

Pass any normal CLI args through the same command:

```bash
./run_resumai.sh --resume-file /path/to/resume.txt --job-file /path/to/jd.txt
./run_resumai.sh --company-url https://company.com/about
./run_resumai.sh --help
```

## Implemented From PRD

The following code-side tasks are now implemented in this repository:

- Repo instruction policy at `.github/copilot-instructions.md`
- Full agent pipeline:
	- `agents/match_score_agent.py`
	- `agents/experience_optimizer_agent.py`
	- `agents/ats_checker_agent.py`
	- `agents/cover_letter_agent.py` (with optional `--company-url` web context fetch)
	- `agents/latex_generator_agent.py`
	- `agents/renderer_agent.py` (LaTeX.Online -> pdflatex -> raw `.tex` fallback)
- Full shared state and orchestration:
	- `state.py`
	- `main.py`
	- `input_collector.py` (`END`-terminated multiline terminal input)
- Prompt-as-config implementation:
	- `prompts/match_score.md`
	- `prompts/experience_optimizer.md`
	- `prompts/ats_checker.md`
	- `prompts/cover_letter.md`
	- `prompts/latex_generator.md`
- Support modules:
	- `llm_client.py`
	- `base_agent.py`
	- `utils/prompt_loader.py`
- Notification integration:
	- `notifier.py` for Gmail + Calendar post-run delivery
- Validation tests:
	- `tests/test_state_contract.py`
	- `tests/test_prompt_loader.py`
	- `tests/test_match_score_agent.py`

## Manual Steps Required From You

These cannot be automated by Copilot because they require UI/browser authentication.

### 1. Connect GitHub MCP in VS Code

1. Open Command Palette.
2. Run: MCP: Add Server.
3. Select GitHub (or add from registry).
4. Complete GitHub OAuth in browser.
5. Verify in Copilot Chat: `@github what files are in this repo`.

If needed, use server URL:

`https://api.githubcopilot.com/mcp/v1`

### 2. Google Cloud Setup

1. Create project: `resumai-pipeline`.
2. Enable APIs: Gmail API and Google Calendar API.
3. Create OAuth client ID (Desktop app), download and place `credentials.json` in repo root.
4. Add your target email in `.env`:

`NOTIFY_EMAIL=your.email@gmail.com`

### 3. First Run OAuth

On first notifier execution, Google opens browser auth and creates `token.json`.

## Python Setup

```bash
pip install -r requirements.txt
```

## Run Examples

### Cover letter generation path

```bash
python main.py \
	--resume-file sample_resume.txt \
	--job-file sample_job.txt \
	--job-title "Data Scientist" \
	--company "LNER" \
	--company-url https://www.lner.co.uk/about-us/ \
	--no-notify
```

### Notify with Gmail + Calendar (omit --no-notify)


### Full interactive pipeline (END-terminated input)

```bash
python main.py --no-notify
```
```bash
python main.py \
	--resume-file sample_resume.txt \
	--job-file sample_job.txt \
	--job-title "Data Scientist" \
	--company "LNER" \
	--company-url https://www.lner.co.uk/about-us/
```

## Context Hub Integration

This repository is configured to use [Context Hub](https://github.com/andrewyng/context-hub) so coding agents can fetch curated, versioned API and framework docs during development.

### Setup

```bash
npm install
```

This installs the local Context Hub CLI dependency: `@aisuite/chub`.

### Commands

```bash
npm run chub:help
npm run chub:update
npm run chub:search -- "openai"
npm run chub:get -- openai/chat --lang py
npm run chub:annotate -- openai/chat "Use streaming for long responses"
npm run chub:feedback -- openai/chat up
```

### Suggested Agent Workflow

1. Search docs: `npm run chub:search -- "<api or framework>"`
2. Fetch docs: `npm run chub:get -- <id> --lang <py|js>`
3. Implement using fetched docs.
4. Add notes for future sessions with `chub:annotate` when useful.