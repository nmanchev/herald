"""Configuration loading for Herald."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class StakeholderConfig:
    """Configuration for a single stakeholder."""

    name: str
    email: str
    cc: list[str] = field(default_factory=list)
    query: str = ""
    markdown: str = ""


@dataclass
class DataSourceConfig:
    """Configuration for the data source backend."""

    type: str = "databricks"
    params: dict = field(default_factory=dict)


@dataclass
class DeliveryConfig:
    """Configuration for the email delivery backend."""

    type: str = "gmail"
    params: dict = field(default_factory=dict)


@dataclass
class HeraldConfig:
    """Top-level Herald configuration."""

    datasource: DataSourceConfig
    delivery: DeliveryConfig
    stakeholders: dict[str, StakeholderConfig]

    @classmethod
    def load(cls, path: Path | None = None) -> HeraldConfig:
        """Load configuration from a TOML file."""
        if path is None:
            path = Path("herald.toml")

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "rb") as f:
            raw = tomllib.load(f)

        datasource = DataSourceConfig(
            type=raw.get("datasource", {}).get("type", "databricks"),
            params=raw.get("datasource", {}).get("params", {}),
        )

        delivery = DeliveryConfig(
            type=raw.get("delivery", {}).get("type", "gmail"),
            params=raw.get("delivery", {}).get("params", {}),
        )

        stakeholders = {}
        for key, val in raw.get("stakeholders", {}).items():
            stakeholders[key] = StakeholderConfig(
                name=val["name"],
                email=val["email"],
                cc=val.get("cc", []),
                query=val.get("query", ""),
                markdown=val.get("markdown", ""),
            )

        return cls(
            datasource=datasource,
            delivery=delivery,
            stakeholders=stakeholders,
        )
