"""Configuration loading for Herald."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def _expand_env(value):
    """Recursively expand $ENV_VAR and ${ENV_VAR} references in config values."""
    if isinstance(value, str):
        def _replace(match):
            var_name = match.group(1) or match.group(2)
            env_val = os.environ.get(var_name)
            if env_val is None:
                raise EnvironmentError(f"Environment variable not set: {var_name}")
            return env_val
        return re.sub(r"\$\{(\w+)\}|\$(\w+)", _replace, value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    return value


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
            raw = _expand_env(tomllib.load(f))

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
