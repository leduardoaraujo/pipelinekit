from datetime import datetime, timezone
from typing import Any

from forgeflow.core.exceptions import TransformerException
from forgeflow.core.transformer import BaseTransformer


class JsonNormalizer(BaseTransformer):
    def transform(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise TransformerException(f"Expected dict, got {type(data).__name__}")

        normalized = self._flatten_dict(data) if self.config.get("flatten") else data

        if timestamp_field := self.config.get("timestamp_field"):
            if timestamp_field not in normalized:
                normalized[timestamp_field] = datetime.now(timezone.utc).isoformat()

        normalized["_ingested_at"] = datetime.now(timezone.utc).isoformat()

        return normalized

    def _flatten_dict(
        self, data: dict, parent_key: str = "", sep: str = "_"
    ) -> dict[str, Any]:
        items: list[tuple[str, Any]] = []

        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, sep).items())
            elif isinstance(value, list):
                items.append((new_key, value))
            else:
                items.append((new_key, value))

        return dict(items)
