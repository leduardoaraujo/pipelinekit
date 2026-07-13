"""Compatibility wrapper for pipelinekit.cli.main."""

from pipelinekit.cli.main import cli, init, list, run, test, validate

__all__ = ["cli", "run", "list", "validate", "init", "test"]
