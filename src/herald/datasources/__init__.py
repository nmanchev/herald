"""Data source abstraction layer."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DataSource(Protocol):
    """Protocol for data source backends.

    Implement this protocol to add support for a new database.
    """

    def execute_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict]:
        """Execute a SQL query and return results as a list of dicts."""
        ...

    def close(self) -> None:
        """Close the connection."""
        ...
