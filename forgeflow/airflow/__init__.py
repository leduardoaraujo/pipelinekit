"""Airflow integration for ForgeFlow.

This module provides operators, hooks, and sensors for running ForgeFlow
pipelines within Apache Airflow DAGs.

Example:
    from forgeflow.airflow import ForgeFlowOperator

    task = ForgeFlowOperator(
        task_id='run_my_pipeline',
        pipeline_name='my_pipeline',
        config_path='config/pipelines.yaml',
    )
"""

from importlib import import_module

_AIRFLOW_IMPORTS = {
    "ForgeFlowConnectionSensor": ("pipelinekit.integrations.airflow.sensors", ("airflow",)),
    "ForgeFlowHook": ("pipelinekit.integrations.airflow.hooks", ("airflow",)),
    "ForgeFlowOperator": ("pipelinekit.integrations.airflow.operators", ("airflow",)),
    "ForgeFlowSensor": ("pipelinekit.integrations.airflow.sensors", ("airflow",)),
    "ForgeFlowValidateOperator": ("pipelinekit.integrations.airflow.operators", ("airflow",)),
}

__all__ = list(_AIRFLOW_IMPORTS)


def __getattr__(name: str):
    if name not in _AIRFLOW_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, missing_dependencies = _AIRFLOW_IMPORTS[name]

    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        if not _is_optional_dependency_error(exc, module_name, missing_dependencies):
            raise

        raise ImportError(
            "Apache Airflow is required for this module. "
            'Install with: pip install -e ".[airflow]"'
        ) from exc

    return getattr(module, name)


def _is_optional_dependency_error(
    error: ModuleNotFoundError, module_name: str, missing_dependencies: tuple[str, ...]
) -> bool:
    if error.name == module_name:
        return True

    return any(
        error.name == dependency or error.name.startswith(f"{dependency}.")
        for dependency in missing_dependencies
    )
