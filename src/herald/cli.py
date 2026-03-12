"""Herald CLI — command-line interface."""

from __future__ import annotations

from pathlib import Path

import click

from herald import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """Herald — An agentic email system for personalized stakeholder briefings."""


@cli.command()
@click.option("--dir", "directory", default=".", help="Directory to initialize in")
def init(directory: str):
    """Scaffold a new Herald project."""
    base = Path(directory)
    (base / "queries").mkdir(exist_ok=True)
    (base / "stakeholders").mkdir(exist_ok=True)

    config_path = base / "herald.toml"
    if config_path.exists():
        click.echo("herald.toml already exists, skipping.")
    else:
        config_path.write_text(_EXAMPLE_CONFIG)
        click.echo("Created herald.toml")

    example_md = base / "stakeholders" / "example.md"
    if not example_md.exists():
        example_md.write_text(_EXAMPLE_MARKDOWN)
        click.echo("Created stakeholders/example.md")

    example_sql = base / "queries" / "example.sql"
    if not example_sql.exists():
        example_sql.write_text(_EXAMPLE_SQL)
        click.echo("Created queries/example.sql")

    click.echo("\nHerald project initialized. Edit herald.toml to configure your stakeholders.")


@cli.command()
@click.option("--config", "config_path", default="herald.toml", help="Path to config file")
def preview(config_path: str):
    """Fetch data, compose emails, and show them for review (no sending)."""
    from herald.agents.orchestrator import run
    from herald.config import HeraldConfig

    config = HeraldConfig.load(Path(config_path))
    datasource = _create_datasource(config)
    backend = _create_backend(config)

    try:
        run(config, datasource, backend, preview_only=True)
    finally:
        datasource.close()


@cli.command()
@click.option("--config", "config_path", default="herald.toml", help="Path to config file")
def send(config_path: str):
    """Run the full pipeline with human approval before each send."""
    from herald.agents.orchestrator import run
    from herald.config import HeraldConfig

    config = HeraldConfig.load(Path(config_path))
    datasource = _create_datasource(config)
    backend = _create_backend(config)

    try:
        run(config, datasource, backend, preview_only=False)
    finally:
        datasource.close()


@cli.command()
@click.option("--config", "config_path", default="herald.toml", help="Path to config file")
def status(config_path: str):
    """Show current stakeholders and configuration summary."""
    from herald.config import HeraldConfig

    config = HeraldConfig.load(Path(config_path))

    click.echo(f"Data source: {config.datasource.type}")
    click.echo(f"Delivery:    {config.delivery.type}")
    click.echo(f"Stakeholders ({len(config.stakeholders)}):")

    for key, s in config.stakeholders.items():
        cc_str = f" (CC: {', '.join(s.cc)})" if s.cc else ""
        click.echo(f"  {key}: {s.name} <{s.email}>{cc_str}")
        click.echo(f"    query:    {s.query}")
        click.echo(f"    markdown: {s.markdown}")


def _create_datasource(config):
    """Create a data source from config."""
    if config.datasource.type == "databricks":
        from herald.datasources.databricks import DatabricksDataSource

        return DatabricksDataSource(**config.datasource.params)
    else:
        raise ValueError(f"Unknown datasource type: {config.datasource.type}")


def _create_backend(config):
    """Create a delivery backend from config."""
    if config.delivery.type == "gmail":
        from herald.backends.gmail import GmailBackend

        return GmailBackend(**config.delivery.params)
    else:
        raise ValueError(f"Unknown delivery type: {config.delivery.type}")


_EXAMPLE_CONFIG = """# Herald configuration
# See https://github.com/your-org/herald for documentation

[datasource]
type = "databricks"

[datasource.params]
server_hostname = "your-workspace.cloud.databricks.com"
http_path = "/sql/1.0/warehouses/your-warehouse-id"
access_token = "your-access-token"

[delivery]
type = "gmail"

[delivery.params]
credentials_file = "credentials.json"
token_file = "token.json"

[stakeholders.example]
name = "Alice Smith"
email = "alice@example.com"
cc = ["bob@example.com"]
query = "queries/example.sql"
markdown = "stakeholders/example.md"
"""

_EXAMPLE_MARKDOWN = """# Briefing for Alice

## Key Actions

- [ ] Review Q1 pipeline throughput numbers
- [ ] Approve budget allocation for new data platform

## Commentary

This week we saw a significant improvement in processing times...
"""

_EXAMPLE_SQL = """-- Example query: fetch key metrics for stakeholder briefing
SELECT
    metric_name,
    current_value,
    previous_value,
    ROUND((current_value - previous_value) / previous_value * 100, 1) AS pct_change
FROM briefing_metrics
WHERE report_date = CURRENT_DATE()
ORDER BY metric_name
"""
