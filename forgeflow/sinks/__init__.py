from importlib import import_module

_SINK_IMPORTS = {
    "BigQuerySink": ("forgeflow.sinks.bigquery", ".[bigquery]"),
    "DuckDBSink": ("forgeflow.sinks.duckdb", ".[duckdb]"),
    "FileSink": ("forgeflow.sinks.file", None),
    "MongoDBSink": ("forgeflow.sinks.mongodb", ".[mongodb]"),
    "PostgresSink": ("forgeflow.sinks.postgres", ".[postgres]"),
    "S3Sink": ("forgeflow.sinks.s3", ".[s3]"),
}

__all__ = list(_SINK_IMPORTS)


def __getattr__(name: str):
    if name not in _SINK_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, extra_name = _SINK_IMPORTS[name]

    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        if extra_name is None:
            raise

        raise ImportError(
            f'{name} requires optional dependencies. Install with: pip install -e "{extra_name}"'
        ) from exc

    return getattr(module, name)
