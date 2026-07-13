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
    "ForgeFlowConnectionSensor": "forgeflow.airflow.sensors",
    "ForgeFlowHook": "forgeflow.airflow.hooks",
    "ForgeFlowOperator": "forgeflow.airflow.operators",
    "ForgeFlowSensor": "forgeflow.airflow.sensors",
    "ForgeFlowValidateOperator": "forgeflow.airflow.operators",
}

__all__ = list(_AIRFLOW_IMPORTS)


def __getattr__(name: str):
    if name not in _AIRFLOW_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name = _AIRFLOW_IMPORTS[name]

    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        raise ImportError(
            "Apache Airflow is required for this module. "
            'Install with: pip install -e ".[airflow]"'
        ) from exc

    return getattr(module, name)
