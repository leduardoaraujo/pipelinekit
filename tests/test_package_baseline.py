import importlib
import importlib.util

import pytest


def _dependency_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


def test_forgeflow_package_baseline():
    import forgeflow

    assert forgeflow.__version__ == "0.1.0"


def test_cli_entry_point_imports_without_optional_extras():
    from forgeflow.cli.main import cli

    assert cli.name == "cli"


def test_pipeline_loader_imports_without_optional_sink_extras():
    from forgeflow.pipeline.loader import PipelineLoader

    assert PipelineLoader.__name__ == "PipelineLoader"


def test_sinks_package_imports_without_optional_extras():
    sinks = importlib.import_module("forgeflow.sinks")

    assert sinks.FileSink.__name__ == "FileSink"


@pytest.mark.parametrize(
    ("module_name", "attribute_name", "dependency_name", "message"),
    [
        ("forgeflow.sinks", "BigQuerySink", "google.cloud.bigquery", ".[bigquery]"),
        ("forgeflow.sinks", "S3Sink", "boto3", ".[s3]"),
        ("forgeflow.sinks", "MongoDBSink", "motor.motor_asyncio", ".[mongodb]"),
        ("forgeflow.airflow", "ForgeFlowOperator", "airflow", ".[airflow]"),
    ],
)
def test_optional_components_fail_lazily(
    module_name: str,
    attribute_name: str,
    dependency_name: str,
    message: str,
):
    if _dependency_available(dependency_name):
        pytest.skip(f"{dependency_name} is installed in this environment")

    module = importlib.import_module(module_name)

    with pytest.raises(ImportError, match=message):
        getattr(module, attribute_name)
