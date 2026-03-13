"""Gmail delivery backend using gcloud CLI authentication."""

from __future__ import annotations

import base64
import json
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import Request, urlopen

from herald.backends import Email


class GcloudGmailBackend:
    """Email delivery via Gmail API using gcloud CLI credentials.

    Uses `gcloud auth print-access-token` for authentication — no OAuth
    client secrets needed. Requires an authenticated gcloud CLI session
    with the Gmail send scope.
    """

    GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

    def _get_access_token(self) -> str:
        """Get an access token from the gcloud CLI."""
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to get gcloud access token. "
                f"Make sure you're logged in with `gcloud auth login`. "
                f"Error: {result.stderr.strip()}"
            )
        return result.stdout.strip()

    def send(self, email: Email) -> None:
        """Send an email via Gmail API using gcloud credentials."""
        message = MIMEMultipart("alternative")
        message["to"] = email.to
        if email.cc:
            message["cc"] = ", ".join(email.cc)
        message["subject"] = email.subject

        message.attach(MIMEText(email.plain_body, "plain"))
        message.attach(MIMEText(email.html_body, "html"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        token = self._get_access_token()

        request = Request(
            self.GMAIL_SEND_URL,
            data=json.dumps({"raw": raw}).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urlopen(request) as response:  # noqa: S310
            if response.status != 200:
                raise RuntimeError(
                    f"Gmail API returned status {response.status}: "
                    f"{response.read().decode()}"
                )
