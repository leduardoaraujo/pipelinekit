from importlib import import_module

_PIPELINE_IMPORTS = {
    "PipelineExecutor": "forgeflow.pipeline.executor",
    "PipelineLoader": "forgeflow.pipeline.loader",
}

__all__ = list(_PIPELINE_IMPORTS)


def __getattr__(name: str):
    if name not in _PIPELINE_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(_PIPELINE_IMPORTS[name])
    return getattr(module, name)
