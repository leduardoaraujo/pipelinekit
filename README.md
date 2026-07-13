<div align="center">
  # PipelineKit

  Python library for building data pipelines.

  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
</div>

PipelineKit helps you compose reliable ETL pipelines from a source, one or more transforms, and destinations. It is async-first, configuration-driven, and designed to make API ingestion and data distribution easy to extend.

## Features

- HTTP and REST API sources with async support
- JSON normalization, filtering, and schema mapping
- File, PostgreSQL, DuckDB, BigQuery, S3, MongoDB, and Snowflake destinations
- YAML configuration and a practical command-line interface
- Optional FastAPI and Apache Airflow integrations
- Retry, rate limiting, caching, structured logging, and typed contracts

## Installation

```bash
pip install pipelinekit
```

Install only the integrations you need:

```bash
pip install "pipelinekit[postgres]"
pip install "pipelinekit[duckdb]"
pip install "pipelinekit[api]"
pip install "pipelinekit[airflow]"
```

Available extras include `postgres`, `duckdb`, `bigquery`, `s3`, `mongodb`, `snowflake`, `api`, `airflow`, `dev`, and `all`.

## Quick start

Create `config/pipelines.yaml`:

```yaml
pipelines:
  - name: api_to_duckdb
    enabled: true
    connector:
      type: http
      config:
        url: https://api.example.com/data
        method: GET
        timeout: 30
    transformer:
      type: json_normalizer
      config:
        flatten: true
    sinks:
      - type: duckdb
        config:
          database: data/output.duckdb
          table: api_data
```

Run it with the CLI:

```bash
pipelinekit validate
pipelinekit run api_to_duckdb
```

Or load and execute a pipeline from Python:

```python
import asyncio

from pipelinekit.config import PipelineLoader
from pipelinekit.pipeline import PipelineExecutor

pipelines = PipelineLoader.load_from_file("config/pipelines.yaml")
pipeline = next(p for p in pipelines if p["name"] == "api_to_duckdb")

asyncio.run(PipelineExecutor().execute(pipeline))
```

## CLI

```bash
pipelinekit list
pipelinekit run <name>
pipelinekit test <name>
pipelinekit validate
pipelinekit init <name>
```

Use `pipelinekit --help` for options and configuration overrides.

## Extending PipelineKit

Build custom components with the stable core contracts:

```python
from pipelinekit.core import Destination, Source, Transform


class CustomSource(Source):
    def validate_config(self) -> None:
        pass

    async def fetch(self) -> dict:
        return {}

    async def close(self) -> None:
        pass


class CustomTransform(Transform):
    def validate_config(self) -> None:
        pass

    def transform(self, data: dict) -> dict:
        return data


class CustomDestination(Destination):
    def validate_config(self) -> None:
        pass

    async def write(self, data: dict) -> None:
        pass

    async def close(self) -> None:
        pass
```

## Compatibility with ForgeFlow

PipelineKit is the canonical package and CLI name from version 0.2.0 onward. The `forgeflow` package remains as a compatibility layer for existing imports while projects migrate to `pipelinekit`. New code should use the PipelineKit namespace.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
ruff format .
```

See [CONTRIBUTING.md](CONTRIBUTING.md), the [documentation](https://pipelinekit.readthedocs.io), and the [migration guide](docs/migration/forgeflow-to-pipelinekit.md) for more details.

## License

MIT License. See [LICENSE](LICENSE).

## Project status

PipelineKit 0.2.0 is in beta. See [CHANGELOG.md](CHANGELOG.md) for release history.

Repository: [github.com/leduardoaraujo/pipelinekit](https://github.com/leduardoaraujo/pipelinekit)
