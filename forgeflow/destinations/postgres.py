import json
from typing import Any

import psycopg

from forgeflow.core.exceptions import SinkException
from forgeflow.core.sink import BaseSink


class PostgresSink(BaseSink):
    def __init__(self, config: dict):
        super().__init__(config)
        self.connection: psycopg.AsyncConnection | None = None

    def validate_config(self) -> None:
        required = ["table"]
        missing = [key for key in required if key not in self.config]
        if missing:
            raise SinkException(f"Missing required config: {missing}")

    async def write(self, data: dict[str, Any]) -> None:
        if not self.connection:
            await self._connect()

        try:
            table = self.config["table"]
            schema = self.config.get("schema", "public")
            full_table = f"{schema}.{table}"

            columns = list(data.keys())
            values = [self._serialize_value(data[col]) for col in columns]

            placeholders = ", ".join(["%s"] * len(columns))
            columns_str = ", ".join(columns)

            query = f"INSERT INTO {full_table} ({columns_str}) VALUES ({placeholders})"

            async with self.connection.cursor() as cursor:
                await cursor.execute(query, values)
                await self.connection.commit()

        except psycopg.Error as e:
            raise SinkException(f"PostgreSQL write failed: {e}") from e

    async def _connect(self) -> None:
        try:
            connection_string = self.config.get("connection_string")
            if not connection_string:
                from os import getenv

                connection_string = getenv("POSTGRES_URL")

            if not connection_string:
                raise SinkException("No PostgreSQL connection string provided")

            self.connection = await psycopg.AsyncConnection.connect(connection_string)
        except psycopg.Error as e:
            raise SinkException(f"PostgreSQL connection failed: {e}") from e

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value

    async def close(self) -> None:
        if self.connection:
            await self.connection.close()
