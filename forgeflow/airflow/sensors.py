"""Compatibility wrapper for pipelinekit.integrations.airflow.sensors."""

from pipelinekit.integrations.airflow.sensors import ForgeFlowConnectionSensor, ForgeFlowSensor

__all__ = ["ForgeFlowSensor", "ForgeFlowConnectionSensor"]
