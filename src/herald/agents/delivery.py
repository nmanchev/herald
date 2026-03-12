"""Delivery Agent — sends approved emails."""

from __future__ import annotations

from claude_agent_sdk import AgentDefinition

DELIVERY_AGENT = AgentDefinition(
    description=(
        "Email delivery specialist. Use this agent to send an approved email. "
        "Provide it with the recipient address, CC list, subject, HTML body, and "
        "plain text body. It sends the email via the configured backend."
    ),
    prompt=(
        "You are the Delivery Agent for Herald, an agentic email system. "
        "Your job is to send emails that have been approved by the user.\n\n"
        "When given a task:\n"
        "1. Use the send_email tool with the provided details\n"
        "2. Confirm successful delivery or report any errors\n\n"
        "Never modify the email content. Send exactly what was approved."
    ),
    tools=[
        "mcp__herald-tools__send_email",
    ],
)
