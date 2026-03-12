"""Databricks SQL data source implementation."""

from __future__ import annotations

from typing import Any


class DatabricksDataSource:
    """Data source backed by Databricks SQL."""

    def __init__(self, server_hostname: str, http_path: str, access_token: str) -> None:
        from databricks import sql

        self._connection = sql.connect(
            server_hostname=server_hostname,
            http_path=http_path,
            access_token=access_token,
        )

    def execute_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict]:
        """Execute a SQL query and return results as a list of dicts."""
        cursor = self._connection.cursor()
        try:
            cursor.execute(query, parameters=params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def close(self) -> None:
        """Close the Databricks connection."""
        self._connection.close()
