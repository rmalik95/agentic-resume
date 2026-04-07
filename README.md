# ResumAI: Agentic Resume Optimiser

Privacy-first, local, sequential multi-agent pipeline for resume optimisation and optional cover letter generation.

## What You Get

- One script to install everything: `./install_resumai.sh`
- One script to run the pipeline: `./run_resumai.sh`
- First run can be done with one command: `./run_resumai.sh`
  - This command installs dependencies and runs the app.

## Fresh System Install Guide (Step by Step)

Use this guide on any new macOS/Linux machine.

### 1. Install system prerequisites

Install these tools first:

- Python 3.11+
- pip (usually bundled with Python)
- Node.js 18+ and npm (recommended; required for UI and Context Hub tooling)
- Git

Quick checks:

```bash
python3 --version
npm --version
git --version
```

If Python is below 3.11, install a newer version before continuing.

### 2. Clone the repository

```bash
git clone <your-repo-url>
cd agentic-resume
```

### 3. Ensure scripts are executable (first time only)

```bash
chmod +x install_resumai.sh run_resumai.sh run_ui.sh
```

### 4. Create your local environment file

This project does not auto-create `.env`.

```bash
cp .env.example .env
```

Then open `.env` and set:

- `ANTHROPIC_API_KEY=...` (required)
- `NOTIFY_EMAIL=...` (optional; needed only for Gmail/Calendar notifications)

### 5. Install everything

```bash
./install_resumai.sh
```

What this installs:

- Python virtual environment in `.venv`
- Python dependencies from `requirements.txt`
- Root npm dependencies from `package.json` (Context Hub CLI tooling)
- UI npm dependencies from `ui/package.json`

### 6. Run the pipeline

```bash
./run_resumai.sh
```

This command:

- Runs install checks (safe to run repeatedly)
- Verifies `.env` and API key
- Launches `main.py`

## One-Command First Run

On a fresh clone, once `.env` is ready, this is enough:

```bash
./run_resumai.sh
```

## Common Run Examples

### Interactive mode (paste content, END-terminated flow)

```bash
./run_resumai.sh
```

### Run with files

```bash
./run_resumai.sh \
  --resume-file /path/to/resume.pdf \
  --job-file /path/to/job_description.txt
```

### Include company website context for cover letter

```bash
./run_resumai.sh \
  --resume-file /path/to/resume.pdf \
  --job-file /path/to/job_description.txt \
  --company-url https://company.com/about
```

### Show CLI help

```bash
./run_resumai.sh --help
```

### Skip installer phase (faster for repeat runs)

```bash
./run_resumai.sh --skip-install
```

## Run the Web UI

```bash
./run_ui.sh
```

Then open http://127.0.0.1:8000

## Optional: Gmail + Calendar Notifications

By default, `run_resumai.sh` passes `--no-notify`.

If you want notifier support when running directly via Python, complete these manual steps:

1. Create a Google Cloud project.
2. Enable Gmail API and Google Calendar API.
3. Create OAuth Desktop credentials.
4. Download `credentials.json` into the repository root.
5. Set `NOTIFY_EMAIL` in `.env`.

On first notifier run, Google OAuth opens a browser and creates `token.json` locally.

## Output Locations

Generated files are written to `outputs/`, including:

- Optimised CV markdown
- Resume PDF (if rendering succeeds)
- Cover letter PDF (if generated and rendering succeeds)
- Fallback `.tex` files if PDF rendering cannot complete

## Troubleshooting

### Error: python3 not found

Install Python 3.11+ and re-run.

### Error: Python version too old

Upgrade Python and rerun `./install_resumai.sh`.

### Error: .env file not found

Run:

```bash
cp .env.example .env
```

### Error: ANTHROPIC_API_KEY is missing

Set `ANTHROPIC_API_KEY` in `.env` and rerun.

### npm not found warnings

Install Node.js + npm if you want UI and Context Hub features. Core Python pipeline can still run.

## Notes

- Python requirement: 3.11+
- LLM provider: Anthropic SDK
- Prompts are loaded from `prompts/*.md`
- `.env` is read locally and should never be committed
