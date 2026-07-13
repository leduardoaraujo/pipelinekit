from importlib import import_module

_SINK_IMPORTS = {
    "BigQuerySink": (
        "forgeflow.sinks.bigquery",
        ".[bigquery]",
        ("google.cloud", "google.api_core"),
    ),
    "DuckDBSink": ("forgeflow.sinks.duckdb", ".[duckdb]", ("duckdb",)),
    "FileSink": ("forgeflow.sinks.file", None, ()),
    "MongoDBSink": ("forgeflow.sinks.mongodb", ".[mongodb]", ("motor", "pymongo")),
    "PostgresSink": ("forgeflow.sinks.postgres", ".[postgres]", ("psycopg",)),
    "S3Sink": ("forgeflow.sinks.s3", ".[s3]", ("boto3", "botocore")),
}

__all__ = list(_SINK_IMPORTS)


def __getattr__(name: str):
    if name not in _SINK_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, extra_name, missing_dependencies = _SINK_IMPORTS[name]

    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        if extra_name is None or not _is_optional_dependency_error(
            exc, module_name, missing_dependencies
        ):
            raise

        raise ImportError(
            f'{name} requires optional dependencies. Install with: pip install -e "{extra_name}"'
        ) from exc

    return getattr(module, name)


def _is_optional_dependency_error(
    error: ModuleNotFoundError, module_name: str, missing_dependencies: tuple[str, ...]
) -> bool:
    if error.name == module_name:
        return True

    return any(
        error.name == dependency or error.name.startswith(f"{dependency}.")
        for dependency in missing_dependencies
    )
