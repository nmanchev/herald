"""Email delivery backend abstraction layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class Email:
    """Represents an email to be sent."""

    to: str
    cc: list[str]
    subject: str
    html_body: str
    plain_body: str


@runtime_checkable
class DeliveryBackend(Protocol):
    """Protocol for email delivery backends.

    Implement this protocol to add support for a new email provider.
    """

    def send(self, email: Email) -> None:
        """Send an email."""
        ...
