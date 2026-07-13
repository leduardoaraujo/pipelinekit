from importlib import import_module

_DESTINATION_IMPORTS = {
    "BigQuerySink": (
        "pipelinekit.destinations.bigquery",
        ".[bigquery]",
        ("google",),
    ),
    "DuckDBSink": ("pipelinekit.destinations.duckdb", ".[duckdb]", ("duckdb",)),
    "FileSink": ("pipelinekit.destinations.file", None, ()),
    "MongoDBSink": (
        "pipelinekit.destinations.mongodb",
        ".[mongodb]",
        ("motor", "pymongo"),
    ),
    "PostgresSink": ("pipelinekit.destinations.postgres", ".[postgres]", ("psycopg",)),
    "S3Sink": ("pipelinekit.destinations.s3", ".[s3]", ("boto3", "botocore")),
}

__all__ = list(_DESTINATION_IMPORTS)


def __getattr__(name: str):
    if name not in _DESTINATION_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, extra_name, missing_dependencies = _DESTINATION_IMPORTS[name]

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

    return any(error.name == dependency for dependency in missing_dependencies)
