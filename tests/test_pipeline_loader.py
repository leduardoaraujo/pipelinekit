import pytest

from forgeflow.core.exceptions import ConfigurationException
from forgeflow.config import PipelineLoader


def test_validate_pipeline_valid():
    pipeline = {
        "name": "test",
        "connector": {"type": "http"},
        "transformer": {"type": "json_normalizer"},
        "sinks": [{"type": "file"}],
    }

    PipelineLoader.validate_pipeline(pipeline)


def test_validate_pipeline_missing_fields():
    pipeline = {"name": "test"}

    with pytest.raises(ConfigurationException):
        PipelineLoader.validate_pipeline(pipeline)


def test_validate_pipeline_empty_sinks():
    pipeline = {
        "name": "test",
        "connector": {"type": "http"},
        "transformer": {"type": "json_normalizer"},
        "sinks": [],
    }

    with pytest.raises(ConfigurationException):
        PipelineLoader.validate_pipeline(pipeline)


def test_validate_pipeline_invalid_sinks():
    pipeline = {
        "name": "test",
        "connector": {"type": "http"},
        "transformer": {"type": "json_normalizer"},
        "sinks": "not a list",
    }

    with pytest.raises(ConfigurationException):
        PipelineLoader.validate_pipeline(pipeline)
