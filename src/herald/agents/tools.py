"""Custom MCP tools for Herald agents."""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from herald.backends import DeliveryBackend, Email
from herald.datasources import DataSource

# These are set at runtime by the orchestrator before agents start.
_datasource: DataSource | None = None
_backend: DeliveryBackend | None = None


def configure_tools(datasource: DataSource, backend: DeliveryBackend) -> None:
    """Configure the tools with live backend instances."""
    global _datasource, _backend
    _datasource = datasource
    _backend = backend


@tool(
    "execute_sql",
    "Execute a SQL query against the configured data source and return results as JSON.",
    {
        "query": str,
    },
)
async def execute_sql(args: dict[str, Any]) -> dict[str, Any]:
    """Execute a SQL query."""
    if _datasource is None:
        return {"content": [{"type": "text", "text": "Error: data source not configured"}]}
    results = _datasource.execute_query(args["query"])
    import json

    return {"content": [{"type": "text", "text": json.dumps(results, default=str)}]}


@tool(
    "read_stakeholder_markdown",
    "Read the markdown content file for a stakeholder.",
    {
        "path": str,
    },
)
async def read_stakeholder_markdown(args: dict[str, Any]) -> dict[str, Any]:
    """Read a stakeholder's markdown file."""
    from pathlib import Path

    path = Path(args["path"])
    if not path.exists():
        return {"content": [{"type": "text", "text": f"Error: file not found: {path}"}]}
    content = path.read_text()
    return {"content": [{"type": "text", "text": content}]}


@tool(
    "read_sql_file",
    "Read a SQL query file from disk.",
    {
        "path": str,
    },
)
async def read_sql_file(args: dict[str, Any]) -> dict[str, Any]:
    """Read a SQL file."""
    from pathlib import Path

    path = Path(args["path"])
    if not path.exists():
        return {"content": [{"type": "text", "text": f"Error: SQL file not found: {path}"}]}
    content = path.read_text()
    return {"content": [{"type": "text", "text": content}]}


@tool(
    "send_email",
    "Send an email via the configured delivery backend.",
    {
        "to": str,
        "cc": str,
        "subject": str,
        "html_body": str,
        "plain_body": str,
    },
)
async def send_email(args: dict[str, Any]) -> dict[str, Any]:
    """Send an email."""
    if _backend is None:
        return {"content": [{"type": "text", "text": "Error: delivery backend not configured"}]}

    cc_list = [addr.strip() for addr in args.get("cc", "").split(",") if addr.strip()]
    email = Email(
        to=args["to"],
        cc=cc_list,
        subject=args["subject"],
        html_body=args["html_body"],
        plain_body=args["plain_body"],
    )
    _backend.send(email)
    return {"content": [{"type": "text", "text": f"Email sent to {args['to']}"}]}


def create_herald_mcp_server():
    """Create the MCP server with all Herald tools."""
    return create_sdk_mcp_server(
        name="herald-tools",
        version="1.0.0",
        tools=[execute_sql, read_stakeholder_markdown, read_sql_file, send_email],
    )
