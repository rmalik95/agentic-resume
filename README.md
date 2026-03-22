# Agentic Resume Optimiser

ResumAI baseline setup for pre-agent development.

## Implemented From PRD

The following code-side tasks are now implemented in this repository:

- Repo instruction policy at `.github/copilot-instructions.md`
- Cover-letter web fetch support scaffolding:
	- `state.py` with `company_url` and `company_context`
	- `agents/cover_letter_agent.py` with optional URL fetch (`requests` + HTML strip)
	- `main.py` support for `--company-url`
- Google delivery notifier scaffolding:
	- `notifier.py` for Gmail send + Calendar follow-up event
	- `main.py` support for `--job-title`, `--company`, `--no-notify`
- Dependency and local setup scaffolding:
	- `requirements.txt`
	- `.env.example`
	- `.gitignore` includes `credentials.json`, `token.json`, `outputs/`

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