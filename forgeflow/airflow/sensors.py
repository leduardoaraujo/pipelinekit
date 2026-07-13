"""Airflow sensors for ForgeFlow integration."""

from typing import Any

try:
    from airflow.sensors.base import BaseSensorOperator
    from airflow.utils.decorators import apply_defaults
except ImportError:
    raise ImportError(
        "Apache Airflow is required for this module. "
        'Install with: pip install -e ".[airflow]"'
    )

from forgeflow.airflow.hooks import ForgeFlowHook


class ForgeFlowSensor(BaseSensorOperator):
    """Sensor to check if ForgeFlow pipeline configuration is valid.

    This sensor waits until a ForgeFlow pipeline configuration becomes
    available and valid, useful for coordinating tasks that depend on
    pipeline configuration changes.

    Args:
        pipeline_name: Name of the pipeline to check
        config_path: Path to pipeline configuration file
        poke_interval: Time in seconds between pokes
        timeout: Timeout in seconds before sensor fails

    Example:
        wait_for_config = ForgeFlowSensor(
            task_id='wait_for_pipeline',
            pipeline_name='my_pipeline',
            poke_interval=60,
            timeout=300,
        )
    """

    template_fields = ("pipeline_name", "config_path")
    ui_color = "#9b59b6"
    ui_fgcolor = "#ffffff"

    @apply_defaults
    def __init__(
        self,
        pipeline_name: str,
        config_path: str = "config/pipelines.yaml",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pipeline_name = pipeline_name
        self.config_path = config_path

    def poke(self, context: dict[str, Any]) -> bool:
        """Check if pipeline configuration is valid.

        Args:
            context: Airflow task context

        Returns:
            True if pipeline is valid, False otherwise
        """
        hook = ForgeFlowHook(config_path=self.config_path)

        try:
            self.log.info(f"Checking pipeline configuration: {self.pipeline_name}")
            hook.validate_pipeline(self.pipeline_name)
            self.log.info(f"Pipeline '{self.pipeline_name}' is valid")
            return True
        except (ValueError, FileNotFoundError) as e:
            self.log.info(f"Pipeline not ready: {e}")
            return False


class ForgeFlowConnectionSensor(BaseSensorOperator):
    """Sensor to check if ForgeFlow configuration file is accessible.

    This sensor waits until the ForgeFlow configuration file becomes
    available, useful for workflows where configs are generated dynamically.

    Args:
        config_path: Path to pipeline configuration file
        poke_interval: Time in seconds between pokes
        timeout: Timeout in seconds before sensor fails

    Example:
        wait_for_config_file = ForgeFlowConnectionSensor(
            task_id='wait_for_config_file',
            config_path='config/pipelines.yaml',
            poke_interval=30,
        )
    """

    template_fields = ("config_path",)
    ui_color = "#16a085"
    ui_fgcolor = "#ffffff"

    @apply_defaults
    def __init__(
        self,
        config_path: str = "config/pipelines.yaml",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.config_path = config_path

    def poke(self, context: dict[str, Any]) -> bool:
        """Check if configuration file is accessible.

        Args:
            context: Airflow task context

        Returns:
            True if configuration is accessible, False otherwise
        """
        hook = ForgeFlowHook(config_path=self.config_path)

        success, message = hook.test_connection()

        if success:
            self.log.info(f"Configuration accessible: {message}")
            return True
        else:
            self.log.info(f"Configuration not accessible: {message}")
            return False
