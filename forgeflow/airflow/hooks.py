"""Airflow hooks for ForgeFlow integration."""

import asyncio
from typing import Any

import structlog

try:
    from airflow.hooks.base import BaseHook
except ImportError:
    raise ImportError(
        "Apache Airflow is required for this module. "
        'Install with: pip install -e ".[airflow]"'
    )

from forgeflow.pipeline.executor import PipelineExecutor
from forgeflow.pipeline.loader import PipelineLoader

logger = structlog.get_logger()


class ForgeFlowHook(BaseHook):
    """Hook for interacting with ForgeFlow pipelines.

    This hook provides methods to load, validate, and execute ForgeFlow
    pipelines from within Airflow tasks.

    Args:
        config_path: Path to the pipeline configuration YAML file

    Example:
        hook = ForgeFlowHook(config_path='config/pipelines.yaml')
        result = hook.run_pipeline('my_pipeline')
    """

    def __init__(self, config_path: str = "config/pipelines.yaml"):
        super().__init__()
        self.config_path = config_path
        self._pipelines: list | None = None

    def get_conn(self) -> PipelineExecutor:
        """Return a PipelineExecutor instance.

        Returns:
            PipelineExecutor instance for running pipelines
        """
        return PipelineExecutor()

    def load_pipelines(self) -> list[dict[str, Any]]:
        """Load all pipelines from configuration file.

        Returns:
            List of pipeline configurations

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        if self._pipelines is None:
            self.log.info(f"Loading pipelines from {self.config_path}")
            self._pipelines = PipelineLoader.load_from_file(self.config_path)
        return self._pipelines

    def get_pipeline(self, pipeline_name: str) -> dict[str, Any]:
        """Get a specific pipeline configuration by name.

        Args:
            pipeline_name: Name of the pipeline to retrieve

        Returns:
            Pipeline configuration dictionary

        Raises:
            ValueError: If pipeline not found
        """
        pipelines = self.load_pipelines()
        pipeline = next((p for p in pipelines if p["name"] == pipeline_name), None)

        if not pipeline:
            available = [p["name"] for p in pipelines]
            raise ValueError(
                f"Pipeline '{pipeline_name}' not found. "
                f"Available pipelines: {', '.join(available)}"
            )

        return pipeline

    def run_pipeline(self, pipeline_name: str) -> dict[str, Any]:
        """Execute a ForgeFlow pipeline.

        Args:
            pipeline_name: Name of the pipeline to execute

        Returns:
            Execution result with metadata

        Raises:
            ValueError: If pipeline not found
            Exception: If pipeline execution fails
        """
        self.log.info(f"Executing pipeline: {pipeline_name}")

        pipeline = self.get_pipeline(pipeline_name)
        executor = self.get_conn()

        try:
            # Run async pipeline in sync context
            asyncio.run(executor.execute(pipeline))

            result = {
                "pipeline_name": pipeline_name,
                "status": "success",
                "message": f"Pipeline '{pipeline_name}' completed successfully",
            }

            self.log.info(result["message"])
            return result

        except Exception as e:
            self.log.error(f"Pipeline '{pipeline_name}' failed: {e}")
            raise

    def validate_pipeline(self, pipeline_name: str) -> bool:
        """Validate a pipeline configuration.

        Args:
            pipeline_name: Name of the pipeline to validate

        Returns:
            True if pipeline is valid

        Raises:
            ValueError: If validation fails
        """
        pipeline = self.get_pipeline(pipeline_name)

        required_fields = ["name", "connector", "transformer", "sinks"]
        missing_fields = [field for field in required_fields if field not in pipeline]

        if missing_fields:
            raise ValueError(
                f"Pipeline '{pipeline_name}' is missing required fields: "
                f"{', '.join(missing_fields)}"
            )

        if not pipeline.get("sinks"):
            raise ValueError(f"Pipeline '{pipeline_name}' has no sinks configured")

        self.log.info(f"Pipeline '{pipeline_name}' validation passed")
        return True

    def test_connection(self) -> tuple[bool, str]:
        """Test if ForgeFlow configuration is accessible.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            pipelines = self.load_pipelines()
            return True, f"Successfully loaded {len(pipelines)} pipelines"
        except Exception as e:
            return False, f"Failed to load pipelines: {e}"
