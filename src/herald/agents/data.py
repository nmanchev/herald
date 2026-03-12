"""Data Agent — fetches and shapes data from SQL sources."""

from __future__ import annotations

from claude_agent_sdk import AgentDefinition

DATA_AGENT = AgentDefinition(
    description=(
        "Data retrieval specialist. Use this agent to fetch data from SQL databases. "
        "Give it a SQL file path and it will read the query, execute it, and return "
        "the results as structured data."
    ),
    prompt=(
        "You are the Data Agent for Herald, an agentic email system. "
        "Your job is to fetch data from SQL sources for stakeholder briefings.\n\n"
        "When given a task:\n"
        "1. Read the SQL file using the read_sql_file tool\n"
        "2. Execute the query using the execute_sql tool\n"
        "3. Return the results in a clear, structured format\n\n"
        "If a query fails, report the error clearly. Do not modify queries — "
        "execute them as written."
    ),
    tools=[
        "mcp__herald-tools__execute_sql",
        "mcp__herald-tools__read_sql_file",
    ],
)
