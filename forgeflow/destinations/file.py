import json
from datetime import datetime
from pathlib import Path
from typing import Any

from forgeflow.core.exceptions import SinkException
from forgeflow.core.sink import BaseSink


class FileSink(BaseSink):
    def validate_config(self) -> None:
        required = ["path", "format"]
        missing = [key for key in required if key not in self.config]
        if missing:
            raise SinkException(f"Missing required config: {missing}")

        allowed_formats = ["json", "jsonl", "parquet"]
        fmt = self.config["format"]
        if fmt not in allowed_formats:
            raise SinkException(f"Unsupported format: {fmt}. Use: {allowed_formats}")

    async def write(self, data: dict[str, Any]) -> None:
        path = Path(self.config["path"])
        path.mkdir(parents=True, exist_ok=True)

        fmt = self.config["format"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = path / f"data_{timestamp}.{fmt}"

        try:
            if fmt == "json":
                self._write_json(filename, data)
            elif fmt == "jsonl":
                self._write_jsonl(filename, data)
            elif fmt == "parquet":
                self._write_parquet(filename, data)
        except Exception as e:
            raise SinkException(f"File write failed: {e}") from e

    def _write_json(self, filename: Path, data: dict[str, Any]) -> None:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _write_jsonl(self, filename: Path, data: dict[str, Any]) -> None:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def _write_parquet(self, filename: Path, data: dict[str, Any]) -> None:
        try:
            import pandas as pd
        except ImportError:
            raise SinkException("pandas required for parquet format")

        df = pd.DataFrame([data])
        df.to_parquet(filename, index=False)

    async def close(self) -> None:
        pass
