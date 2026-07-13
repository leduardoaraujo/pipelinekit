from pathlib import Path
from typing import Any

import duckdb

from forgeflow.core.exceptions import SinkException
from forgeflow.core.sink import BaseSink


class DuckDBSink(BaseSink):
    def __init__(self, config: dict):
        super().__init__(config)
        self.connection: duckdb.DuckDBPyConnection | None = None

    def validate_config(self) -> None:
        required = ["database", "table"]
        missing = [key for key in required if key not in self.config]
        if missing:
            raise SinkException(f"Missing required config: {missing}")

    async def write(self, data: dict[str, Any]) -> None:
        if not self.connection:
            self._connect()

        try:
            table = self.config["table"]
            columns = list(data.keys())
            values = list(data.values())

            placeholders = ", ".join(["?"] * len(columns))
            columns_str = ", ".join(columns)

            self.connection.execute(
                f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM (VALUES ({placeholders})) AS t({columns_str}) WHERE false",
                values,
            )

            self.connection.execute(
                f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})", values
            )

        except duckdb.Error as e:
            raise SinkException(f"DuckDB write failed: {e}") from e

    def _connect(self) -> None:
        try:
            db_path = Path(self.config["database"])
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = duckdb.connect(str(db_path))
        except duckdb.Error as e:
            raise SinkException(f"DuckDB connection failed: {e}") from e

    async def close(self) -> None:
        if self.connection:
            self.connection.close()
