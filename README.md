<div align="center">
  <img src="docs/assets/logo_forgeflow.svg" alt="ForgeFlow Logo" width="400"/>

  # ForgeFlow

  Modern ETL Framework for API Ingestion and Data Distribution

  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

</div>

---

## Overview

ForgeFlow is a modern ETL framework designed for API data ingestion, transformation, and distribution. Built with async-first architecture using Python 3.11+, it provides a declarative YAML-based configuration system for building robust data pipelines.

## Key Features

- HTTP and REST API connectors with async support
- JSON normalization and flattening
- Multiple sinks: PostgreSQL, DuckDB, and file-based storage
- Declarative YAML configuration
- Rich CLI with interactive commands
- FastAPI REST server
- Apache Airflow integration
- Structured logging with structlog
- Built-in retry, rate limiting, and caching utilities
- Type-safe with full type hints

## Installation

### Basic Installation

```bash
pip install -e .
```

### With Optional Dependencies

```bash
# PostgreSQL support
pip install -e ".[postgres]"

# DuckDB support
pip install -e ".[duckdb]"

# API server
pip install -e ".[api]"

# Airflow integration
pip install -e ".[airflow]"

# Development tools
pip install -e ".[dev]"
```

## Quick Start

### 1. Configure Pipeline

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
        headers:
          Authorization: Bearer YOUR_TOKEN
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
      - type: file
        config:
          path: data/json
          format: json
```

### 2. Run Pipeline

```bash
# CLI
forgeflow run api_to_duckdb

# Python
python -c "
from forgeflow.pipeline.executor import PipelineExecutor
from forgeflow.pipeline.loader import PipelineLoader
import asyncio

pipelines = PipelineLoader.load_from_file('config/pipelines.yaml')
pipeline = next(p for p in pipelines if p['name'] == 'api_to_duckdb')

executor = PipelineExecutor()
asyncio.run(executor.execute(pipeline))
"
```

### 3. Query Results

```bash
duckdb data/output.duckdb -c "SELECT * FROM api_data LIMIT 10"
```

## CLI Commands

```bash
forgeflow list              # List all configured pipelines
forgeflow run <name>        # Execute a pipeline
forgeflow test <name>       # Test pipeline connection
forgeflow validate          # Validate configuration
forgeflow init <name>       # Create new pipeline template
```

## Architecture

```
forgeflow/
├── core/                   # Base interfaces and utilities
│   ├── connector.py        # BaseConnector interface
│   ├── transformer.py      # BaseTransformer interface
│   ├── sink.py             # BaseSink interface
│   ├── retry.py            # Retry utilities
│   ├── rate_limiter.py     # Rate limiting utilities
│   ├── cache.py            # Caching utilities
│   └── validation.py       # Data validation utilities
├── connectors/             # Data source implementations
│   ├── http.py             # Generic HTTP connector
│   └── rest.py             # RESTful API connector
├── transformers/           # Data transformation
│   └── json_normalizer.py  # JSON flattening and normalization
├── sinks/                  # Data destination implementations
│   ├── postgres.py         # PostgreSQL sink
│   ├── duckdb.py           # DuckDB sink
│   └── file.py             # File-based sink
├── pipeline/               # Pipeline orchestration
│   ├── executor.py         # Execution engine
│   └── loader.py           # Configuration loader
├── api/                    # REST API server
│   └── main.py             # FastAPI endpoints
├── airflow/                # Airflow integration
│   ├── operators.py        # Custom operators
│   ├── hooks.py            # Custom hooks
│   └── sensors.py          # Custom sensors
└── cli/                    # Command-line interface
    └── main.py             # CLI implementation
```

## Components

### Connectors

| Name | Description | Status |
|------|-------------|--------|
| HTTP | Generic HTTP requests with headers and parameters | ✅ Implemented |
| REST | RESTful API client with base URL pattern | ✅ Implemented |

### Transformers

| Name | Description | Status |
|------|-------------|--------|
| JSON Normalizer | Flatten nested JSON structures | ✅ Implemented |
| Filter | Filter data based on conditions (eq, gt, contains, etc.) | ✅ **NEW** |
| Schema Mapper | Map fields between schemas with type conversion | ✅ **NEW** |

### Sinks

| Name | Description | Installation | Status |
|------|-------------|--------------|--------|
| PostgreSQL | Relational database storage | `pip install -e ".[postgres]"` | ✅ Implemented |
| DuckDB | Embedded analytical database | `pip install -e ".[duckdb]"` | ✅ Implemented |
| File | Local file storage (JSON, JSONL, Parquet) | Built-in | ✅ Implemented |
| BigQuery | Google Cloud data warehouse | `pip install -e ".[bigquery]"` | ✅ **NEW** |
| S3 | AWS S3 object storage (JSON, JSONL, Parquet) | `pip install -e ".[s3]"` | ✅ **NEW** |
| MongoDB | NoSQL document database | `pip install -e ".[mongodb]"` | ✅ **NEW** |

## Airflow Integration

```python
from airflow import DAG
from forgeflow.airflow import ForgeFlowOperator, ForgeFlowSensor
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'data_ingestion',
    default_args=default_args,
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    check_api = ForgeFlowSensor(
        task_id='check_api_availability',
        pipeline_name='api_to_duckdb',
        timeout=300,
    )

    run_pipeline = ForgeFlowOperator(
        task_id='ingest_data',
        pipeline_name='api_to_duckdb',
        config_path='config/pipelines.yaml',
    )

    check_api >> run_pipeline
```

## REST API

Start the server:

```bash
uvicorn forgeflow.api.main:app --reload
```

Access interactive documentation at `http://localhost:8000/docs`

### Endpoints

- `GET /health` - Health check
- `GET /pipelines` - List all pipelines
- `POST /pipelines/{name}/run` - Execute pipeline
- `GET /pipelines/{name}/status` - Check pipeline status

## Utilities

ForgeFlow includes utility modules for common ETL patterns:

### Retry Logic

```python
from forgeflow.core.retry import retry_async, RetryConfig

config = RetryConfig(
    max_attempts=3,
    min_wait=1.0,
    max_wait=60.0,
    multiplier=2.0
)

result = await retry_async(fetch_data, config, url="https://api.example.com")
```

### Rate Limiting

```python
from forgeflow.core.rate_limiter import RateLimiter

limiter = RateLimiter(max_requests=100, time_window=60)
await limiter.acquire()
# Make API request
```

### Caching

```python
from forgeflow.core.cache import MemoryCache

cache = MemoryCache(ttl=3600)
await cache.set("key", data)
cached = await cache.get("key")
```

### Data Validation

```python
from forgeflow.core.validation import SchemaValidator
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: int
    name: str
    email: str

validator = SchemaValidator(UserSchema)
is_valid, validated_data, errors = validator.validate(data)
```

## Extending ForgeFlow

### Custom Connector

```python
from forgeflow.core.connector import BaseConnector

class CustomConnector(BaseConnector):
    def validate_config(self) -> None:
        required = ["api_key", "endpoint"]
        missing = [k for k in required if k not in self.config]
        if missing:
            raise ValueError(f"Missing config: {missing}")

    async def fetch(self) -> dict:
        # Implementation
        return {}

    async def close(self) -> None:
        # Cleanup
        pass
```

### Custom Transformer

```python
from forgeflow.core.transformer import BaseTransformer

class CustomTransformer(BaseTransformer):
    def validate_config(self) -> None:
        pass

    async def transform(self, data: dict) -> dict:
        # Implementation
        return data
```

### Custom Sink

```python
from forgeflow.core.sink import BaseSink

class CustomSink(BaseSink):
    def validate_config(self) -> None:
        pass

    async def write(self, data: dict) -> None:
        # Implementation
        pass

    async def close(self) -> None:
        pass
```

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=forgeflow --cov-report=html

# Specific test
pytest tests/test_pipeline_loader.py

# Verbose output
pytest -v
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run linter
ruff check .

# Run formatter
ruff format .

# Type checking
mypy forgeflow/
```

## Design Principles

- **Explicit Contracts**: Clear interfaces with type hints
- **Fail Fast**: Immediate errors with detailed messages
- **Declarative Configuration**: YAML-based, version-controlled
- **Async First**: Built on asyncio for performance
- **Structured Logging**: No print statements, structured logs only

## Roadmap

Future planned features:

- Additional connectors: GraphQL, Kafka, WebSocket, gRPC
- Additional sinks: Snowflake
- Data aggregation transformer
- Redis cache backend
- Metrics and monitoring
- Web dashboard

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Project Status

Version 0.1.0 - Beta

See [CHANGELOG.md](CHANGELOG.md) for version history and roadmap.
