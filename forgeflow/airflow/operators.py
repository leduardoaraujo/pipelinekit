"""Airflow operators for ForgeFlow integration."""

from typing import Any

import structlog

try:
    from airflow.models import BaseOperator
    from airflow.utils.decorators import apply_defaults
except ImportError:
    raise ImportError(
        "Apache Airflow is required for this module. "
        'Install with: pip install -e ".[airflow]"'
    )

from forgeflow.airflow.hooks import ForgeFlowHook

logger = structlog.get_logger()


class ForgeFlowOperator(BaseOperator):
    """Operator to execute ForgeFlow pipelines in Airflow.

    This operator runs a ForgeFlow pipeline as an Airflow task, with support
    for XCom, templating, and Airflow's task lifecycle.

    Args:
        pipeline_name: Name of the pipeline to execute
        config_path: Path to pipeline configuration file
        push_to_xcom: Whether to push execution result to XCom
        validate_before_run: Validate pipeline config before execution

    Example:
        run_etl = ForgeFlowOperator(
            task_id='extract_api_data',
            pipeline_name='my_api_pipeline',
            config_path='config/pipelines.yaml',
            push_to_xcom=True,
        )
    """

    template_fields = ("pipeline_name", "config_path")
    template_ext = (".yaml", ".yml")
    ui_color = "#4a90e2"
    ui_fgcolor = "#ffffff"

    @apply_defaults
    def __init__(
        self,
        pipeline_name: str,
        config_path: str = "config/pipelines.yaml",
        push_to_xcom: bool = True,
        validate_before_run: bool = True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pipeline_name = pipeline_name
        self.config_path = config_path
        self.push_to_xcom = push_to_xcom
        self.validate_before_run = validate_before_run

    def execute(self, context: dict[str, Any]) -> dict[str, Any] | None:
        """Execute the ForgeFlow pipeline.

        Args:
            context: Airflow task context

        Returns:
            Execution result (if push_to_xcom is True)
        """
        hook = ForgeFlowHook(config_path=self.config_path)

        # Validate pipeline configuration if requested
        if self.validate_before_run:
            self.log.info(f"Validating pipeline: {self.pipeline_name}")
            hook.validate_pipeline(self.pipeline_name)

        # Execute pipeline
        self.log.info(f"Executing pipeline: {self.pipeline_name}")
        result = hook.run_pipeline(self.pipeline_name)

        # Push result to XCom if requested
        if self.push_to_xcom:
            self.log.info("Pushing result to XCom")
            return result

        return None


class ForgeFlowValidateOperator(BaseOperator):
    """Operator to validate ForgeFlow pipeline configurations.

    This operator validates one or more pipelines without executing them,
    useful for pre-flight checks in DAGs.

    Args:
        pipeline_name: Name of pipeline to validate (or None for all)
        config_path: Path to pipeline configuration file

    Example:
        validate = ForgeFlowValidateOperator(
            task_id='validate_config',
            pipeline_name='my_pipeline',
        )
    """

    template_fields = ("pipeline_name", "config_path")
    ui_color = "#f39c12"
    ui_fgcolor = "#ffffff"

    @apply_defaults
    def __init__(
        self,
        pipeline_name: str | None = None,
        config_path: str = "config/pipelines.yaml",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pipeline_name = pipeline_name
        self.config_path = config_path

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Validate pipeline configuration.

        Args:
            context: Airflow task context

        Returns:
            Validation result
        """
        hook = ForgeFlowHook(config_path=self.config_path)

        if self.pipeline_name:
            # Validate specific pipeline
            self.log.info(f"Validating pipeline: {self.pipeline_name}")
            hook.validate_pipeline(self.pipeline_name)
            return {
                "status": "valid",
                "pipeline": self.pipeline_name,
                "message": f"Pipeline '{self.pipeline_name}' is valid",
            }
        else:
            # Validate all pipelines
            self.log.info("Validating all pipelines")
            pipelines = hook.load_pipelines()

            results = []
            for pipeline in pipelines:
                try:
                    hook.validate_pipeline(pipeline["name"])
                    results.append({"name": pipeline["name"], "valid": True})
                except ValueError as e:
                    results.append({"name": pipeline["name"], "valid": False, "error": str(e)})

            valid_count = sum(1 for r in results if r["valid"])

            return {
                "status": "completed",
                "total": len(results),
                "valid": valid_count,
                "invalid": len(results) - valid_count,
                "results": results,
            }
