"""Gmail delivery backend implementation."""

from __future__ import annotations

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from herald.backends import Email


class GmailBackend:
    """Email delivery via Gmail API (Google Workspace)."""

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

    def __init__(self, credentials_file: str, token_file: str = "token.json") -> None:
        self._credentials_file = credentials_file
        self._token_file = token_file
        self._service = self._build_service()

    def _build_service(self) -> Any:
        """Build and return an authenticated Gmail API service."""
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds = None
        token_path = Path(self._token_file)

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            token_path.write_text(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    def send(self, email: Email) -> None:
        """Send an email via Gmail API."""
        message = MIMEMultipart("alternative")
        message["to"] = email.to
        if email.cc:
            message["cc"] = ", ".join(email.cc)
        message["subject"] = email.subject

        message.attach(MIMEText(email.plain_body, "plain"))
        message.attach(MIMEText(email.html_body, "html"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        self._service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
