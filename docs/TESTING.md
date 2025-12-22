# Testing Guide

This guide explains how to run, write, and maintain tests for the archer-pro-active Telegram integration.

## Quick Start

### Run All Tests

```bash
# Activate virtual environment (if testing locally)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r scripts/telegram/requirements.txt
pip install -r requirements-dev.txt

# Run all tests with coverage
pytest

# Run with coverage report
pytest --cov --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only (fast, < 10s)
pytest tests/unit/ -m unit

# Integration tests only
pytest tests/integration/ -m integration

# E2E tests only
pytest tests/e2e/ -m e2e

# Run tests in parallel (faster)
pytest -n auto
```

### Run Tests in Docker

```bash
# Build container
docker compose build

# Run tests inside container
docker compose run --rm claude-dev-env bash -c "cd /home/dev && /opt/venv/bin/pip install -r requirements-dev.txt && /opt/venv/bin/pytest tests/"
```

## Test Organization

### Directory Structure

```
tests/
├── unit/               # Fast, isolated tests (no I/O)
├── integration/        # Module interaction tests (filesystem)
├── e2e/                # Complete workflow tests
└── conftest.py         # Shared fixtures
```

### Test Categories

- **Unit tests**: Test individual functions in isolation, all external dependencies mocked
- **Integration tests**: Test module interactions with real filesystem (tmp_path)
- **E2E tests**: Test complete workflows end-to-end

## Writing Tests

### Test Naming Convention

```python
def test_<function_name>_<scenario>_<expected_outcome>():
    """Docstring describing what this test verifies"""
    pass

# Examples:
def test_is_authorized_with_correct_chat_id_returns_true():
def test_queue_message_creates_file_with_timestamp():
def test_handle_message_unauthorized_user_sends_rejection():
```

### Using Fixtures

```python
import pytest

async def test_handle_message(mock_telegram_update, mock_context, temp_mind_dir, mock_env):
    """Test message handling with all necessary fixtures"""
    from scripts.telegram.bot import handle_message

    await handle_message(mock_telegram_update, mock_context)

    queue_files = list(temp_mind_dir["queue"].glob("*.msg"))
    assert len(queue_files) == 1
```

### Available Fixtures

See `tests/conftest.py` for complete list. Key fixtures:

- `mock_env`: Sets up environment variables
- `temp_mind_dir`: Creates temporary mind directory structure
- `mock_telegram_update`: Mock Telegram Update object
- `mock_telegram_bot`: Mock Bot for sending messages
- `fixed_datetime`: Freeze time for predictable timestamps
- `captured_logs`: Capture log messages

### Async Test Pattern

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """pytest-asyncio automatically detects async tests"""
    result = await some_async_function()
    assert result == expected
```

## Coverage Goals

- **Target**: 80% overall coverage
- **Minimum**: 70% for CI/CD to pass
- **Priority areas**:
  - Authorization logic: 100%
  - Message queuing: 100%
  - Error handling: 100%

### Check Coverage

```bash
# Terminal report
pytest --cov --cov-report=term-missing

# HTML report (open in browser)
pytest --cov --cov-report=html
open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov --cov-report=xml
```

## CI/CD

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests
- Changes to `scripts/telegram/**` or `tests/**`

### GitHub Actions

See `.github/workflows/tests.yml` for workflow configuration.

**Test Matrix**: Python 3.10, 3.11, 3.12

**Stages**:
1. Lint & type check
2. Unit tests
3. Integration tests
4. E2E tests
5. Docker compatibility tests
6. Security scan

## Common Issues

### Import Errors

If tests can't import modules:
```bash
# Add project root to PYTHONPATH
export PYTHONPATH=/Users/daniel/repos/archer-pro-active:$PYTHONPATH
pytest
```

### Async Tests Not Running

Ensure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

Check pytest.ini has:
```ini
asyncio_mode = auto
```

### Coverage Too Low

1. Run with `--cov-report=term-missing` to see uncovered lines
2. Add tests for uncovered code
3. Use `# pragma: no cover` for unreachable code (sparingly)

## Performance

- **Unit tests target**: < 10s total
- **Integration tests target**: < 30s total
- **E2E tests target**: < 60s total
- **Full suite target**: < 2 minutes

### Speed Up Tests

```bash
# Run in parallel (requires pytest-xdist)
pytest -n auto

# Run only failed tests from last run
pytest --lf

# Run tests that failed first
pytest --ff
```

## Debugging Tests

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Run specific test
pytest tests/unit/telegram/test_bot_unit.py::TestAuthorization::test_is_authorized_with_chat_id_set
```

## Best Practices

1. **Test behavior, not implementation**: Focus on what the code does, not how
2. **One assertion per test**: Makes failures clear and specific
3. **Use descriptive names**: Test name should explain what's being tested
4. **Arrange-Act-Assert**: Structure tests with clear setup, execution, verification
5. **Mock external dependencies**: Keep unit tests fast and isolated
6. **Use fixtures for common setup**: Reduces duplication, improves maintainability

## Test Coverage by File

Current test coverage targets:

| File | Target Coverage | Priority |
|------|----------------|----------|
| `bot.py` | 85% | HIGH |
| `send_message.py` | 90% | HIGH |
| Overall | 80%+ | - |

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [python-telegram-bot testing guide](https://docs.python-telegram-bot.org/en/stable/testing.html)
- [Coverage.py documentation](https://coverage.readthedocs.io/)

## Troubleshooting

### Tests Pass Locally But Fail in CI

- Check Python version differences (CI tests on 3.10, 3.11, 3.12)
- Verify all dependencies in requirements-dev.txt
- Check for timing issues with fixed_datetime fixture

### Flaky Tests

- Ensure all external dependencies are mocked
- Use fixed_datetime for time-dependent tests
- Avoid real filesystem I/O in unit tests

### Memory Issues in Tests

- Clean up resources in fixtures
- Use tmp_path for temporary files (auto-cleanup)
- Avoid creating large test data

## Contributing Tests

When adding new features:

1. Write tests first (TDD approach)
2. Ensure new code has > 80% coverage
3. Run full test suite before committing
4. Update this documentation if adding new test patterns

## Test Maintenance

- Review test failures promptly
- Update tests when changing functionality
- Remove obsolete tests
- Keep fixtures in conftest.py organized
- Document complex test setups
