import importlib
import importlib.util
import re
from pathlib import Path

import pytest


def _dependency_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


def test_forgeflow_package_baseline():
    import forgeflow

    assert forgeflow.__version__ == "0.1.0"


def test_api_metadata_uses_forgeflow_identity():
    api_main = Path("forgeflow/api/main.py").read_text(encoding="utf-8")

    assert 'title="ForgeFlow"' in api_main
    assert '"name": "ForgeFlow"' in api_main


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


@pytest.mark.parametrize(
    ("module_name", "attribute_name", "imported_module_name", "missing_dependency", "message"),
    [
        (
            "forgeflow.sinks",
            "BigQuerySink",
            "forgeflow.sinks.bigquery",
            "google.cloud.bigquery",
            'BigQuerySink requires optional dependencies. Install with: pip install -e ".[bigquery]"',
        ),
        (
            "forgeflow.airflow",
            "ForgeFlowOperator",
            "forgeflow.airflow.operators",
            "airflow",
            'Apache Airflow is required for this module. Install with: pip install -e ".[airflow]"',
        ),
    ],
)
def test_optional_dependency_guidance_only_for_missing_extra(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    attribute_name: str,
    imported_module_name: str,
    missing_dependency: str,
    message: str,
):
    module = importlib.import_module(module_name)

    def fake_import_module(name: str):
        assert name == imported_module_name
        raise ModuleNotFoundError(
            f"No module named '{missing_dependency}'", name=missing_dependency
        )

    monkeypatch.setattr(module, "import_module", fake_import_module)

    with pytest.raises(ImportError, match=re.escape(message)):
        getattr(module, attribute_name)


@pytest.mark.parametrize(
    ("module_name", "attribute_name", "imported_module_name", "internal_missing_dependency"),
    [
        (
            "forgeflow.sinks",
            "BigQuerySink",
            "forgeflow.sinks.bigquery",
            "google.auth",
        ),
        (
            "forgeflow.airflow",
            "ForgeFlowOperator",
            "forgeflow.airflow.operators",
            "pendulum",
        ),
    ],
)
def test_optional_dependency_internal_module_errors_propagate(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    attribute_name: str,
    imported_module_name: str,
    internal_missing_dependency: str,
):
    module = importlib.import_module(module_name)

    def fake_import_module(name: str):
        assert name == imported_module_name
        raise ModuleNotFoundError(
            f"No module named '{internal_missing_dependency}'",
            name=internal_missing_dependency,
        )

    monkeypatch.setattr(module, "import_module", fake_import_module)

    with pytest.raises(
        ModuleNotFoundError, match=re.escape(internal_missing_dependency)
    ):
        getattr(module, attribute_name)
