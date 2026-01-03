# Tests Directory

This directory contains all automated tests for the looksatwords project.

## Test Structure

```
tests/
├── __init__.py
├── test_analyzer.py          # Conversation analyzer tests
├── test_dataio.py            # Data I/O tests
├── test_gatherer.py          # Data gathering tests
├── test_generator.py         # Content generation tests
├── test_orchestrator.py      # Orchestration tests
├── test_visualizer.py        # Visualization tests
├── test_api.py               # API endpoint tests (5 tests)
└── test_e2e.py               # End-to-end browser tests (11 tests)
```

## Running Tests

### All Tests

```bash
# Run all tests
uv run pytest looksatwords/tests/ -v

# Run with coverage
uv run pytest looksatwords/tests/ --cov=looksatwords --cov-report=html
```

### Unit Tests

```bash
# Run all unit tests
uv run pytest looksatwords/tests/ -v -m "not e2e"

# Run specific test file
uv run pytest looksatwords/tests/test_analyzer.py -v

# Run specific test
uv run pytest looksatwords/tests/test_analyzer.py::test_analyze_conversation -v
```

### API Tests

```bash
# Run API tests
uv run pytest looksatwords/tests/test_api.py -v

# Run with backend server
uv run looksatwords run-server &
uv run pytest looksatwords/tests/test_api.py -v
```

### End-to-End Tests

E2E tests require Playwright browsers. See [E2E Testing Guide](../docs/E2E_TESTING.md) for details.

```bash
# Install Playwright browsers (first time only)
uv run playwright install chromium

# Run all e2e tests
uv run pytest looksatwords/tests/test_e2e.py -v -m e2e

# Run specific e2e test
uv run pytest looksatwords/tests/test_e2e.py::test_frontend_loads -v

# Run e2e tests with servers (fixtures handle this automatically)
uv run pytest looksatworks/tests/test_e2e.py -v -m e2e
```

## Test Categories

Tests are marked with pytest markers:

- `@pytest.mark.e2e` - End-to-end browser tests
- No marker - Unit/integration tests

### Filter by Marker

```bash
# Run only e2e tests
uv run pytest -m e2e -v

# Skip e2e tests
uv run pytest -m "not e2e" -v
```

## Test Coverage

Current test status: **62+ tests passing**

| Category | Tests | Status |
|----------|-------|--------|
| Analyzer | 10+ | ✅ |
| Data I/O | 5+ | ✅ |
| Gatherer | 8+ | ✅ |
| Generator | 7+ | ✅ |
| Orchestrator | 6+ | ✅ |
| Visualizer | 5+ | ✅ |
| API Endpoints | 5 | ✅ |
| E2E Browser | 11 | ✅ |

## E2E Tests

The `test_e2e.py` file contains comprehensive browser automation tests:

### Test Coverage

1. **Smoke Tests**
   - `test_playwright_available` - Verify Playwright installation
   - `test_playwright_browser_launch` - Browser launches successfully

2. **Frontend Tests**
   - `test_frontend_loads` - Page loads with all elements
   - `test_conversation_analysis_basic` - Basic analysis workflow
   - `test_conversation_speakers_detected` - Speaker identification
   - `test_empty_conversation_handling` - Empty input handling
   - `test_reset_functionality` - Reset button works
   - `test_playback_controls` - Timeline playback
   - `test_complex_conversation_analysis` - Multi-thread analysis

3. **Integration Tests**
   - `test_conversation_with_backend_persistence` - Full-stack workflow

### Fixtures

- `frontend_server` - Starts frontend on port 8081
- `api_server` - Starts API server on port 8001

### Running E2E Tests

```bash
# Quick test
uv run pytest looksatwords/tests/test_e2e.py::test_playwright_available -v

# All e2e tests
uv run pytest looksatwords/tests/test_e2e.py -v -m e2e

# With verbose output
uv run pytest looksatwords/tests/test_e2e.py -v -m e2e -s

# Specific test
uv run pytest looksatwords/tests/test_e2e.py::test_frontend_loads -v
```

## Prerequisites for E2E Tests

### 1. Install Playwright

```bash
# Install Playwright browsers
uv run playwright install chromium

# Or install all browsers
uv run playwright install
```

### 2. Verify Installation

```bash
# Check Playwright
uv run python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

## Test Development

### Adding Unit Tests

1. Create or update test file in `tests/`
2. Follow naming convention: `test_*.py`
3. Use descriptive test names: `test_<functionality>_<scenario>`
4. Add docstrings explaining what's tested

Example:
```python
def test_analyzer_handles_empty_input():
    """Test that analyzer handles empty conversation gracefully."""
    result = analyze_conversation("")
    assert result is not None
    assert len(result.threads) == 0
```

### Adding E2E Tests

1. Edit `test_e2e.py`
2. Mark with `@pytest.mark.e2e`
3. Use fixtures for server setup
4. Follow existing patterns
5. Add docstring with test description

Example:
```python
@pytest.mark.e2e
def test_new_feature(frontend_server):
    """Test new feature works in browser."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{frontend_server}/index.html")
        
        # Test logic here
        
        browser.close()
```

## CI/CD Integration

Tests are designed to work in continuous integration:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    uv run pytest looksatwords/tests/ -v --cov
    
- name: Run e2e tests
  run: |
    uv run playwright install --with-deps chromium
    uv run pytest looksatwords/tests/test_e2e.py -v -m e2e
```

## Troubleshooting

### "Playwright not installed"

```bash
uv sync
uv run playwright install chromium
```

### "Browser not found"

```bash
uv run playwright install chromium
```

### "Port already in use"

E2E tests use ports 8001 and 8081. Stop any services using these ports.

### Tests taking too long

```bash
# Run in parallel
uv pip install pytest-xdist
uv run pytest looksatwords/tests/ -n auto
```

## Documentation

For detailed E2E testing documentation, see:
- [E2E Testing Guide](../docs/E2E_TESTING.md)
- [Backend Integration](../docs/BACKEND_INTEGRATION.md)
- [Getting Started](../docs/GETTING_STARTED.md)

## Test Best Practices

1. **Isolation** - Each test should be independent
2. **Descriptive Names** - Test names should explain what's tested
3. **Single Purpose** - One test, one concept
4. **Fast Execution** - Keep tests quick
5. **Clean Up** - Always clean up resources (fixtures help)
6. **Meaningful Assertions** - Assert the right things

## Quick Reference

```bash
# All tests
uv run pytest looksatwords/tests/ -v

# Unit tests only
uv run pytest -m "not e2e" -v

# E2E tests only
uv run pytest -m e2e -v

# With coverage
uv run pytest --cov=looksatwords --cov-report=html

# Specific test
uv run pytest looksatwords/tests/test_api.py::test_health_endpoint -v

# Stop on first failure
uv run pytest looksatwords/tests/ -x

# Verbose output
uv run pytest looksatwords/tests/ -v -s

# Parallel execution
uv run pytest looksatwords/tests/ -n auto
```

---

**Last Updated**: January 2026  
**Total Tests**: 62+  
**Test Coverage**: Comprehensive
