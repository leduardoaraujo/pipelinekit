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
