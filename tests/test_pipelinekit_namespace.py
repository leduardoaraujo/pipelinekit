def test_pipelinekit_package_reports_release_version():
    import pipelinekit

    assert pipelinekit.__version__ == "0.2.0"


def test_pipelinekit_core_exports_domain_aliases():
    from pipelinekit.core import Destination, Source, Transform

    assert Source.__name__ == "BaseConnector"
    assert Transform.__name__ == "BaseTransformer"
    assert Destination.__name__ == "BaseSink"


def test_forgeflow_top_level_remains_compatible():
    import forgeflow

    assert forgeflow.__version__ == "0.2.0"


def test_legacy_cli_module_reexports_canonical_click_group():
    from forgeflow.cli.main import cli as legacy_cli
    from pipelinekit.cli.main import cli as canonical_cli

    assert legacy_cli is canonical_cli


def test_legacy_pipeline_lazy_exports_resolve_to_canonical_executor():
    from forgeflow.pipeline import Pipeline, PipelineExecutor
    from pipelinekit.pipeline.executor import PipelineExecutor as CanonicalPipelineExecutor

    assert Pipeline is CanonicalPipelineExecutor
    assert PipelineExecutor is CanonicalPipelineExecutor


def test_legacy_executor_module_reexports_canonical_executor():
    from forgeflow.pipeline.executor import PipelineExecutor as LegacyPipelineExecutor
    from pipelinekit.pipeline.executor import PipelineExecutor as CanonicalPipelineExecutor

    assert LegacyPipelineExecutor is CanonicalPipelineExecutor


def test_legacy_transform_module_reexports_canonical_transformer():
    from forgeflow.transforms.filter import FilterTransformer as LegacyFilterTransformer
    from pipelinekit.transforms.filter import FilterTransformer as CanonicalFilterTransformer

    assert LegacyFilterTransformer is CanonicalFilterTransformer


def test_legacy_destination_imports_reexport_canonical_file_sink():
    from forgeflow.destinations import FileSink as LazyLegacyFileSink
    from forgeflow.destinations.file import FileSink as LegacyFileSink
    from forgeflow.sinks.file import FileSink as LegacySinkAlias
    from pipelinekit.destinations.file import FileSink as CanonicalFileSink

    assert LazyLegacyFileSink is CanonicalFileSink
    assert LegacyFileSink is CanonicalFileSink
    assert LegacySinkAlias is CanonicalFileSink
