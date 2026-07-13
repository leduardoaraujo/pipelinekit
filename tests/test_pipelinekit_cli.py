import importlib.util
import json
import subprocess
import sys
import textwrap

import pytest
from click.testing import CliRunner

from pipelinekit.cli.main import cli
from pipelinekit.config.loader import PipelineLoader


def test_pipelinekit_help():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "pipeline" in result.output.lower()


def test_pipeline_loader_reads_yaml(tmp_path):
    config_path = tmp_path / "pipelines.yaml"
    config_path.write_text(
        textwrap.dedent(
            """
            pipelines:
              - name: sample_pipeline
                connector:
                  type: http
                  config:
                    url: https://example.com/data
                transformer:
                  type: json_normalizer
                  config:
                    flatten: true
                sinks:
                  - type: file
                    config:
                      path: data/output/sample_pipeline.json
            """
        ).strip(),
        encoding="utf-8",
    )

    pipelines = PipelineLoader.load_from_file(config_path)

    assert [pipeline["name"] for pipeline in pipelines] == ["sample_pipeline"]
    PipelineLoader.validate_pipeline(pipelines[0])


def test_api_compatibility_package_exports_canonical_app():
    if (
        importlib.util.find_spec("fastapi") is None
        or importlib.util.find_spec("pydantic") is None
    ):
        pytest.skip("PipelineKit API extra is not installed in this environment")

    from forgeflow.api.main import app as legacy_app
    from pipelinekit.api import app as canonical_app

    assert canonical_app is legacy_app


def test_core_package_imports_do_not_eagerly_load_optional_extras():
    script = textwrap.dedent(
        """
        import json
        import sys

        import pipelinekit.api
        import pipelinekit.cli
        import pipelinekit.config
        import pipelinekit.destinations
        import pipelinekit.integrations.airflow

        tracked = [
            "airflow",
            "fastapi",
            "google.cloud.bigquery",
            "boto3",
            "motor",
            "snowflake",
        ]
        print(json.dumps({name: name in sys.modules for name in tracked}, sort_keys=True))
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(result.stdout.strip()) == {
        "airflow": False,
        "boto3": False,
        "fastapi": False,
        "google.cloud.bigquery": False,
        "motor": False,
        "snowflake": False,
    }
