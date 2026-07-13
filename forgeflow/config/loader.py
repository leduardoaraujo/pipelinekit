from pathlib import Path

import yaml

from forgeflow.core.exceptions import ConfigurationException


class PipelineLoader:
    @staticmethod
    def load_from_file(path: str | Path) -> list[dict]:
        path = Path(path)
        if not path.exists():
            raise ConfigurationException(f"Pipeline file not found: {path}")

        try:
            with open(path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict) or "pipelines" not in config:
                raise ConfigurationException("Invalid pipeline file format")

            return config["pipelines"]

        except yaml.YAMLError as e:
            raise ConfigurationException(f"Failed to parse pipeline file: {e}") from e

    @staticmethod
    def validate_pipeline(pipeline: dict) -> None:
        required = ["name", "connector", "transformer", "sinks"]
        missing = [key for key in required if key not in pipeline]
        if missing:
            raise ConfigurationException(f"Pipeline missing required fields: {missing}")

        if not isinstance(pipeline["sinks"], list):
            raise ConfigurationException("Sinks must be a list")

        if len(pipeline["sinks"]) == 0:
            raise ConfigurationException("Pipeline must have at least one sink")
