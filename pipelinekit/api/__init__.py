"""Canonical API exports for PipelineKit."""

from importlib import import_module

_API_EXPORTS = {
    "app": "pipelinekit.api.main",
    "PipelineRunRequest": "pipelinekit.api.main",
}

__all__ = list(_API_EXPORTS)


def __getattr__(name: str):
    if name not in _API_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name = _API_EXPORTS[name]

    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name not in {"fastapi", "pydantic"}:
            raise

        raise ImportError(
            "PipelineKit API dependencies are required for this module. "
            'Install with: pip install -e ".[api]"'
        ) from exc

    return getattr(module, name)
