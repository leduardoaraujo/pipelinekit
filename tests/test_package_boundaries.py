import pytest

from forgeflow.core import (
    BaseConnector,
    BaseSink,
    BaseTransformer,
    Destination,
    Source,
    Transform,
)
from forgeflow.pipeline import Pipeline, PipelineExecutor
from forgeflow.sources import HttpConnector, RestConnector
from forgeflow.transforms import FilterTransformer, JsonNormalizer, SchemaMapper


def test_core_exports_domain_aliases():
    assert Source is BaseConnector
    assert Transform is BaseTransformer
    assert Destination is BaseSink


def test_pipeline_exports_alias():
    assert Pipeline is PipelineExecutor


def test_domain_packages_export_existing_components():
    assert HttpConnector is not None
    assert RestConnector is not None
    assert JsonNormalizer is not None
    assert FilterTransformer is not None
    assert SchemaMapper is not None


def test_legacy_wrapper_packages_export_domain_components():
    from forgeflow import connectors, sinks, transformers
    from forgeflow.destinations import FileSink

    assert connectors.HttpConnector is HttpConnector
    assert connectors.RestConnector is RestConnector
    assert transformers.JsonNormalizer is JsonNormalizer
    assert transformers.FilterTransformer is FilterTransformer
    assert transformers.SchemaMapper is SchemaMapper
    assert sinks.FileSink is FileSink


def test_legacy_pipeline_loader_wrapper_exports_config_loader():
    from forgeflow.config import PipelineLoader
    from forgeflow.pipeline.loader import PipelineLoader as LegacyPipelineLoader

    assert LegacyPipelineLoader is PipelineLoader


def test_optional_destinations_remain_lazy_without_optional_cloud_extras():
    from forgeflow import sinks
    from forgeflow.destinations import FileSink

    assert sinks.FileSink is FileSink

    with pytest.raises(ImportError, match='Install with: pip install -e "\\.\\[bigquery\\]"'):
        sinks.BigQuerySink
