"""Orchestrator — coordinates the Herald workflow across agents."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, query
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from herald.agents.compose import COMPOSE_AGENT
from herald.agents.data import DATA_AGENT
from herald.agents.delivery import DELIVERY_AGENT
from herald.agents.review import REVIEW_AGENT
from herald.agents.tools import configure_tools, create_herald_mcp_server
from herald.backends import DeliveryBackend
from herald.config import HeraldConfig
from herald.datasources import DataSource


async def _approval_handler(
    tool_name: str, input_data: dict, context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    """Human-in-the-loop: require approval before sending emails."""
    if tool_name == "mcp__herald-tools__send_email":
        print("\n" + "=" * 60)
        print("EMAIL READY FOR APPROVAL")
        print("=" * 60)
        print(f"To: {input_data.get('to', 'unknown')}")
        cc = input_data.get("cc", "")
        if cc:
            print(f"CC: {cc}")
        print(f"Subject: {input_data.get('subject', 'unknown')}")
        print("-" * 60)
        print(input_data.get("plain_body", "(no plain text body)"))
        print("=" * 60)

        response = input("\nApprove sending? (y/n/e to edit): ").strip().lower()
        if response == "y":
            return PermissionResultAllow(updated_input=input_data)
        elif response == "e":
            print("Editing is not yet implemented. Rejecting for now.")
            return PermissionResultDeny(message="User wants to edit the email. Please ask what changes they'd like.")
        else:
            return PermissionResultDeny(message="User rejected this email. Do not send it.")

    return PermissionResultAllow(updated_input=input_data)


def _build_orchestrator_prompt(config: HeraldConfig) -> str:
    """Build the orchestrator's system prompt from config."""
    stakeholder_info = []
    for key, s in config.stakeholders.items():
        cc_str = f", CC: {', '.join(s.cc)}" if s.cc else ""
        stakeholder_info.append(
            f"- {s.name} ({s.email}{cc_str}): query={s.query}, markdown={s.markdown}"
        )

    stakeholders_block = "\n".join(stakeholder_info)

    return f"""You are the Herald Orchestrator, coordinating a multi-agent email briefing system.

Your stakeholders:
{stakeholders_block}

Your workflow for each stakeholder:
1. Use the DATA agent: give it the stakeholder's SQL file path to fetch fresh data
2. Use the COMPOSE agent: give it the stakeholder's markdown path and the SQL data to produce an email
3. Use the REVIEW agent: give it the composed email to validate quality
4. If the review agent says REVISION_NEEDED, use the COMPOSE agent again with the feedback
5. Once approved by the review agent, use the DELIVERY agent to send the email

Process ALL stakeholders. Report progress as you go.

Important:
- Always fetch fresh data before composing (never reuse stale data across stakeholders)
- The review-compose loop should run at most 3 times per stakeholder
- If a stakeholder's SQL file or markdown file is missing, skip them and report the issue"""


async def _run_orchestrator(config: HeraldConfig, datasource: DataSource, backend: DeliveryBackend, preview_only: bool = False):
    """Run the orchestrator agent."""
    configure_tools(datasource, backend)
    mcp_server = create_herald_mcp_server()

    prompt = _build_orchestrator_prompt(config)
    if preview_only:
        prompt += "\n\nPREVIEW MODE: Do NOT send any emails. Stop after the review step and display the final emails."

    async def prompt_stream():
        yield {
            "type": "user",
            "message": {"role": "user", "content": prompt},
        }

    options = ClaudeAgentOptions(
        mcp_servers={"herald-tools": mcp_server},
        allowed_tools=[
            "Agent",
            "mcp__herald-tools__execute_sql",
            "mcp__herald-tools__read_sql_file",
            "mcp__herald-tools__read_stakeholder_markdown",
            "mcp__herald-tools__send_email",
        ],
        agents={
            "data": DATA_AGENT,
            "compose": COMPOSE_AGENT,
            "review": REVIEW_AGENT,
            "delivery": DELIVERY_AGENT,
        },
        can_use_tool=_approval_handler,
    )

    async for message in query(prompt=prompt_stream(), options=options):
        if hasattr(message, "content"):
            print(message.content)
        elif hasattr(message, "result"):
            print(message.result)


def run(config: HeraldConfig, datasource: DataSource, backend: DeliveryBackend, preview_only: bool = False) -> None:
    """Entry point for running the Herald orchestrator."""
    asyncio.run(_run_orchestrator(config, datasource, backend, preview_only))
