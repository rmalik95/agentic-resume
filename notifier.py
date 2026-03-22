"""
Post-pipeline notifier.
Sends completed PDFs to the user by email and creates a calendar follow-up.
Called from main.py after RendererAgent completes.
Requires: credentials.json in project root, NOTIFY_EMAIL in .env
"""

import base64
import os
from datetime import datetime, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
]


def _get_credentials() -> Credentials:
    """Load or refresh OAuth credentials. Opens browser on first run only."""
    creds = None
    token_path = Path("token.json")
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = Path("credentials.json")
            if not credentials_path.exists():
                raise FileNotFoundError(
                    "credentials.json is missing in the project root. "
                    "Complete Google OAuth setup first."
                )
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def send_outputs(
    pdf_paths: list[str],
    job_title: str,
    company: str,
    score_before: int,
    score_after: int,
) -> None:
    """Main entry point. Call after RendererAgent completes."""
    load_dotenv()
    to_email = os.getenv("NOTIFY_EMAIL")
    if not to_email:
        print("  NOTIFY_EMAIL not set - skipping notification")
        return

    creds = _get_credentials()
    _send_email(creds, to_email, pdf_paths, job_title, company, score_before, score_after)
    _create_followup_event(creds, job_title, company)


def _send_email(
    creds: Credentials,
    to_email: str,
    pdf_paths: list[str],
    job_title: str,
    company: str,
    score_before: int,
    score_after: int,
) -> None:
    """Send completion email with generated PDFs attached."""
    service = build("gmail", "v1", credentials=creds)

    msg = MIMEMultipart()
    msg["to"] = to_email
    msg["subject"] = (
        f"ResumAI - {job_title} at {company} "
        f"(score: {score_before} -> {score_after})"
    )
    body = (
        f"Your optimised application for {job_title} at {company} is ready.\n\n"
        f"Match score: {score_before}/100 -> {score_after}/100 "
        f"(+{score_after - score_before} points)\n"
        "A follow-up reminder has been added to your calendar for 5 days from now.\n\n"
        f"PDFs attached: {len(pdf_paths)} file(s)."
    )
    msg.attach(MIMEText(body, "plain"))

    for path in pdf_paths:
        if path and Path(path).exists():
            with open(path, "rb") as file_handle:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file_handle.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={Path(path).name}",
            )
            msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"  Email sent to {to_email}")


def _create_followup_event(creds: Credentials, job_title: str, company: str) -> None:
    """Create a 5-day follow-up reminder event in primary calendar."""
    service = build("calendar", "v3", credentials=creds)
    followup_date = datetime.utcnow() + timedelta(days=5)
    event = {
        "summary": f"Follow up - {job_title} at {company}",
        "description": "Application sent via ResumAI. Chase if no response.",
        "start": {"date": followup_date.strftime("%Y-%m-%d")},
        "end": {"date": followup_date.strftime("%Y-%m-%d")},
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": 540}],
        },
    }
    service.events().insert(calendarId="primary", body=event).execute()
    print(f"  Calendar reminder set for {followup_date.strftime('%d %b %Y')}")
