# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- GraphQL connector
- Kafka connector
- WebSocket connector
- gRPC connector
- Data aggregator transformer
- Data deduplicator
- Redis cache backend
- Snowflake sink
- Metrics and monitoring
- Web dashboard

## [0.1.0] - 2025-02-10

Initial release

### Added

#### Core Framework
- Pipeline executor with async support
- YAML-based configuration loader
- Multi-sink pipeline support
- Structured logging with structlog
- Error handling and validation

#### Connectors
- HTTP connector with custom headers and parameters
- REST API connector with base URL pattern
- Retry mechanism with exponential backoff
- Rate limiting support
- Caching layer

#### Transformers
- JSON normalizer with flattening support
- Configurable field separator
- Timestamp field handling

#### Sinks
- PostgreSQL sink with bulk insert
- DuckDB sink for embedded analytics
- File sink (JSON, Parquet, CSV)
- Schema management
- Connection pooling

#### CLI
- `forgeflow run` - Execute pipelines
- `forgeflow list` - List configured pipelines
- `forgeflow test` - Test pipeline connections
- `forgeflow validate` - Validate configuration
- `forgeflow init` - Create pipeline templates
- Rich terminal output

#### API
- FastAPI REST server
- Health check endpoint
- Pipeline listing endpoint
- Pipeline execution endpoint
- Status monitoring endpoint
- Interactive API documentation

#### Airflow Integration
- ForgeFlowPipelineOperator for task execution
- ForgeFlowHook for Airflow connections
- ForgeFlowApiSensor for API monitoring
- Example DAG implementations

#### Advanced Features
- Configurable retry with tenacity
- Rate limiting per endpoint
- In-memory caching
- JSON schema validation
- Custom validation rules

#### Infrastructure
- pyproject.toml with extras
- Multiple requirements files
- MIT License
- Comprehensive README
- Contributing guidelines
- Development setup documentation

#### Testing
- pytest test suite
- Async test support
- Code coverage reporting
- Mock utilities

#### Development Tools
- ruff for linting and formatting
- mypy for type checking
- pre-commit hooks
- GitHub Actions ready

### Dependencies

#### Core
- httpx >= 0.27.0
- pydantic >= 2.9.0
- pydantic-settings >= 2.6.0
- pyyaml >= 6.0
- structlog >= 24.4.0
- click >= 8.1.0
- rich >= 13.7.0
- tenacity >= 8.2.0

#### Optional
- fastapi >= 0.115.0
- uvicorn >= 0.32.0
- psycopg >= 3.2.0
- duckdb >= 1.1.0
- google-cloud-bigquery >= 3.26.0
- pandas >= 2.2.0
- boto3 >= 1.34.0
- s3fs >= 2024.2.0
- motor >= 3.3.0
- pymongo >= 4.6.0
- snowflake-connector-python >= 3.7.0
- apache-airflow >= 2.8.0

## Roadmap

### Version 0.2.0

**Focus**: Extended Connectivity

- GraphQL connector implementation
- Kafka producer and consumer
- WebSocket connector
- Data aggregation transformer
- Improved error handling
- Performance optimizations

### Version 0.3.0

**Focus**: Cloud Integration

- Snowflake sink
- Redis cache backend
- Distributed rate limiting
- Metrics collection

### Version 0.4.0

**Focus**: Monitoring and Management

- Web-based dashboard
- Real-time pipeline monitoring
- Metrics visualization
- Alert system
- Pipeline scheduling UI
- Configuration management

### Version 1.0.0

**Focus**: Production Ready

- Stable API
- Complete documentation
- Performance benchmarks
- Enterprise features
- Production hardening
- Migration guides
- Plugin system

## Breaking Changes

None yet. This is the initial release.

## Migration Guides

Not applicable for initial release.

## Security

No security vulnerabilities reported.

To report security issues, see SECURITY.md

---

[Unreleased]: https://github.com/leduardoaraujo/forgeflow/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/leduardoaraujo/forgeflow/releases/tag/v0.1.0
