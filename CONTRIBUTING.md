# Contributing to ForgeFlow

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git

### Setup Steps

```bash
# Clone repository
git clone https://github.com/leduardoaraujo/forgeflow.git
cd forgeflow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=forgeflow --cov-report=html

# Specific test file
pytest tests/test_pipeline_loader.py

# Verbose output
pytest -v

# Skip slow tests
pytest -m "not slow"
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test names
- Include docstrings for complex tests
- Mock external dependencies
- Aim for high coverage

## Code Style

### Linting and Formatting

```bash
# Format code
ruff format .

# Check linting
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type checking
mypy forgeflow/
```

### Code Standards

- Follow PEP 8
- Maximum line length: 100 characters
- Use type hints for all functions
- Write docstrings for public APIs
- No print statements (use structlog)
- Prefer explicit over implicit

## Making Changes

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or changes

### Commit Messages

Follow conventional commits format:

```
type(scope): subject

body

footer
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `test` - Tests
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `chore` - Maintenance

Examples:

```
feat(connectors): add GraphQL connector

Implement GraphQL connector with query support and pagination.

Closes #123
```

```
fix(pipeline): handle null values in transformer

JSON normalizer now correctly handles null values without raising exceptions.
```

### Pull Request Process

1. Create feature branch from `main`
2. Make changes with tests
3. Update documentation
4. Run linter and tests
5. Push branch and create PR
6. Address review feedback
7. Squash commits if requested

## Adding Features

### New Connector

1. Create file in `forgeflow/connectors/`
2. Inherit from `BaseConnector`
3. Implement required methods
4. Add configuration validation
5. Write tests
6. Update README

Example:

```python
from forgeflow.core.connector import BaseConnector
from forgeflow.core.exceptions import ConnectorException

class MyConnector(BaseConnector):
    def validate_config(self) -> None:
        required = ["api_key"]
        missing = [k for k in required if k not in self.config]
        if missing:
            raise ConnectorException(f"Missing config: {missing}")

    async def fetch(self) -> dict:
        # Implementation
        pass

    async def close(self) -> None:
        # Cleanup
        pass
```

### New Transformer

1. Create file in `forgeflow/transformers/`
2. Inherit from `BaseTransformer`
3. Implement transformation logic
4. Add tests with various inputs
5. Update README

### New Sink

1. Create file in `forgeflow/sinks/`
2. Inherit from `BaseSink`
3. Implement write logic
4. Handle connection pooling
5. Add tests
6. Update pyproject.toml extras if needed

## Project Structure

```
forgeflow/
├── core/           # Base interfaces
├── connectors/     # Source implementations
├── transformers/   # Transformation logic
├── sinks/          # Destination implementations
├── pipeline/       # Orchestration
├── api/            # REST API
├── airflow/        # Airflow integration
└── cli/            # CLI commands

config/             # Example configurations
tests/              # Test suite
examples/           # Example implementations
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def fetch_data(url: str, timeout: int = 30) -> dict:
    """Fetch data from URL.

    Args:
        url: The URL to fetch from
        timeout: Request timeout in seconds

    Returns:
        Dictionary containing response data

    Raises:
        ConnectorException: If request fails
    """
    pass
```

### README Updates

- Update features list
- Add examples for new functionality
- Update architecture diagram if needed
- Add to appropriate tables (connectors/transformers/sinks)

## Reporting Issues

### Bug Reports

Include:

- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS)
- Relevant logs or error messages
- Minimal reproducible example

### Feature Requests

Include:

- Use case description
- Proposed solution
- Alternative approaches considered
- Impact on existing functionality

## Code Review Guidelines

### For Authors

- Keep PRs focused and small
- Provide clear description
- Link related issues
- Respond to feedback promptly
- Update based on review comments

### For Reviewers

- Be constructive and specific
- Focus on code quality and design
- Check test coverage
- Verify documentation updates
- Test locally when possible

## Release Process

1. Update CHANGELOG.md
2. Bump version in pyproject.toml
3. Create git tag
4. Build package
5. Publish to PyPI (maintainers only)

## Getting Help

- Check existing documentation
- Search closed issues
- Ask in discussions
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
