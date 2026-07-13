import json
from typing import Any

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from google.api_core.exceptions import NotFound

from forgeflow.core.exceptions import SinkException
from forgeflow.core.sink import BaseSink


class BigQuerySink(BaseSink):
    """Sink for writing data to Google BigQuery."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.client: bigquery.Client | None = None
        self.table_ref: str | None = None

    def validate_config(self) -> None:
        """Validate required configuration parameters."""
        required = ["project_id", "dataset_id", "table_id"]
        missing = [key for key in required if key not in self.config]
        if missing:
            raise SinkException(f"Missing required config: {missing}")

    async def write(self, data: dict[str, Any]) -> None:
        """Write data to BigQuery table."""
        if not self.client:
            self._connect()

        try:
            # Ensure dataset and table exist
            self._ensure_dataset_exists()
            self._ensure_table_exists(data)

            # Insert row
            rows_to_insert = [data]
            errors = self.client.insert_rows_json(self.table_ref, rows_to_insert)

            if errors:
                raise SinkException(f"BigQuery insert failed: {errors}")

        except GoogleCloudError as e:
            raise SinkException(f"BigQuery write failed: {e}") from e

    def _connect(self) -> None:
        """Initialize BigQuery client."""
        try:
            project_id = self.config["project_id"]
            credentials_path = self.config.get("credentials_path")

            if credentials_path:
                self.client = bigquery.Client.from_service_account_json(
                    credentials_path, project=project_id
                )
            else:
                # Use application default credentials
                self.client = bigquery.Client(project=project_id)

            dataset_id = self.config["dataset_id"]
            table_id = self.config["table_id"]
            self.table_ref = f"{project_id}.{dataset_id}.{table_id}"

        except GoogleCloudError as e:
            raise SinkException(f"BigQuery connection failed: {e}") from e

    def _ensure_dataset_exists(self) -> None:
        """Create dataset if it doesn't exist."""
        dataset_id = f"{self.config['project_id']}.{self.config['dataset_id']}"

        try:
            self.client.get_dataset(dataset_id)
        except NotFound:
            # Dataset doesn't exist, create it
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = self.config.get("location", "US")
            self.client.create_dataset(dataset, exists_ok=True)

    def _ensure_table_exists(self, data: dict[str, Any]) -> None:
        """Create table if it doesn't exist, inferring schema from data."""
        try:
            self.client.get_table(self.table_ref)
        except NotFound:
            # Table doesn't exist, create it
            schema = self._infer_schema(data)
            table = bigquery.Table(self.table_ref, schema=schema)

            # Configure table options
            if write_disposition := self.config.get("write_disposition"):
                table.write_disposition = write_disposition

            self.client.create_table(table, exists_ok=True)

    def _infer_schema(self, data: dict[str, Any]) -> list[bigquery.SchemaField]:
        """Infer BigQuery schema from data dictionary."""
        schema = []

        for key, value in data.items():
            field_type = self._get_bigquery_type(value)
            mode = "NULLABLE"

            # Handle nested structures
            if isinstance(value, dict):
                field_type = "JSON"
            elif isinstance(value, list):
                field_type = "JSON"

            schema.append(bigquery.SchemaField(key, field_type, mode=mode))

        return schema

    def _get_bigquery_type(self, value: Any) -> str:
        """Map Python type to BigQuery type."""
        if value is None:
            return "STRING"
        elif isinstance(value, bool):
            return "BOOLEAN"
        elif isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "FLOAT"
        elif isinstance(value, dict):
            return "JSON"
        elif isinstance(value, list):
            return "JSON"
        else:
            return "STRING"

    async def close(self) -> None:
        """Close BigQuery client."""
        if self.client:
            self.client.close()
