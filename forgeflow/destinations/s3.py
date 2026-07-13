import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from forgeflow.core.exceptions import SinkException
from forgeflow.core.sink import BaseSink


class S3Sink(BaseSink):
    """Sink for writing data to AWS S3."""

    SUPPORTED_FORMATS = ["json", "jsonl", "parquet"]

    def __init__(self, config: dict):
        super().__init__(config)
        self.s3_client = None
        self.buffer: list[dict] = []

    def validate_config(self) -> None:
        """Validate required configuration parameters."""
        required = ["bucket"]
        missing = [key for key in required if key not in self.config]
        if missing:
            raise SinkException(f"Missing required config: {missing}")

        format_type = self.config.get("format", "json")
        if format_type not in self.SUPPORTED_FORMATS:
            raise SinkException(
                f"Unsupported format: {format_type}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

    async def write(self, data: dict[str, Any]) -> None:
        """Write data to S3."""
        if not self.s3_client:
            self._connect()

        try:
            format_type = self.config.get("format", "json")

            # For JSONL, we can write immediately
            if format_type == "jsonl":
                await self._write_jsonl(data)
            # For JSON and Parquet, buffer the data
            else:
                self.buffer.append(data)
                batch_size = self.config.get("batch_size", 100)

                if len(self.buffer) >= batch_size:
                    await self._flush()

        except (BotoCoreError, ClientError) as e:
            raise SinkException(f"S3 write failed: {e}") from e

    async def _write_jsonl(self, data: dict[str, Any]) -> None:
        """Write a single line of JSON to S3."""
        bucket = self.config["bucket"]
        key = self._generate_key(extension="jsonl")

        body = json.dumps(data) + "\n"

        self.s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/jsonl"
        )

    async def _write_json(self, data_list: list[dict[str, Any]]) -> None:
        """Write JSON array to S3."""
        bucket = self.config["bucket"]
        key = self._generate_key(extension="json")

        body = json.dumps(data_list, indent=2)

        self.s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json"
        )

    async def _write_parquet(self, data_list: list[dict[str, Any]]) -> None:
        """Write Parquet file to S3."""
        try:
            import pandas as pd
            import pyarrow as pa
            import pyarrow.parquet as pq
            from io import BytesIO
        except ImportError:
            raise SinkException(
                "Parquet support requires pandas and pyarrow. "
                "Install with: pip install pandas pyarrow"
            )

        bucket = self.config["bucket"]
        key = self._generate_key(extension="parquet")

        # Convert to DataFrame
        df = pd.DataFrame(data_list)

        # Write to BytesIO buffer
        buffer = BytesIO()
        table = pa.Table.from_pandas(df)
        pq.write_table(table, buffer, compression=self.config.get("compression", "snappy"))

        # Upload to S3
        buffer.seek(0)
        self.s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=buffer.getvalue(),
            ContentType="application/octet-stream"
        )

    async def _flush(self) -> None:
        """Flush buffered data to S3."""
        if not self.buffer:
            return

        format_type = self.config.get("format", "json")

        if format_type == "json":
            await self._write_json(self.buffer)
        elif format_type == "parquet":
            await self._write_parquet(self.buffer)

        self.buffer.clear()

    def _generate_key(self, extension: str) -> str:
        """Generate S3 key with optional prefix and timestamp."""
        prefix = self.config.get("prefix", "")

        # Add timestamp partitioning if enabled
        if self.config.get("partition_by_date", False):
            now = datetime.utcnow()
            date_path = now.strftime("%Y/%m/%d")
            prefix = f"{prefix}/{date_path}" if prefix else date_path

        # Generate filename
        filename_pattern = self.config.get("filename_pattern", "{uuid}")
        filename = filename_pattern.format(
            uuid=str(uuid4()),
            timestamp=datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        )

        key = f"{prefix}/{filename}.{extension}" if prefix else f"{filename}.{extension}"
        return key.lstrip("/")

    def _connect(self) -> None:
        """Initialize S3 client."""
        try:
            aws_access_key_id = self.config.get("aws_access_key_id")
            aws_secret_access_key = self.config.get("aws_secret_access_key")
            region_name = self.config.get("region_name", "us-east-1")
            endpoint_url = self.config.get("endpoint_url")  # For S3-compatible services

            if aws_access_key_id and aws_secret_access_key:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name,
                    endpoint_url=endpoint_url
                )
            else:
                # Use default credentials (IAM role, env vars, etc.)
                self.s3_client = boto3.client(
                    "s3",
                    region_name=region_name,
                    endpoint_url=endpoint_url
                )

        except (BotoCoreError, ClientError) as e:
            raise SinkException(f"S3 connection failed: {e}") from e

    async def close(self) -> None:
        """Flush any remaining data and close connection."""
        await self._flush()
        if self.s3_client:
            self.s3_client = None
