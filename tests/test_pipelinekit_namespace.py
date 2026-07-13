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
