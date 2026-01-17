# Testing Guide

How to run and write tests for looksatwords.

---

## Quick Commands

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest looksatwords/tests/test_analyzer.py

# Run with coverage
uv run pytest --cov=looksatwords --cov-report=html
```

---

## Test Organization

```
looksatwords/tests/
├── __init__.py
├── test_gatherer.py          # Text extraction (17 tests)
├── test_analyzer.py          # NLP analysis (15 tests)  
├── test_generator.py         # AI generation (5 tests)
├── test_visualizer.py        # HTML output (6 tests)
├── test_orchestrator.py      # Pipeline (8 tests)
├── test_dataio.py            # Data I/O (5 tests)
├── test_analytics_service.py # Analytics service (23 tests)
├── test_frontend.py          # Frontend modules (30+ tests)
└── test_e2e.py               # E2E browser tests (30+ tests)
```

**Total: 130+ tests**

---

## Unit Tests

### Running Unit Tests

```bash
# All unit tests
uv run pytest looksatwords/tests/ --ignore=looksatwords/tests/test_e2e.py

# Specific module
uv run pytest looksatwords/tests/test_analyzer.py -v

# Single test
uv run pytest looksatwords/tests/test_analyzer.py::test_function_name -v
```

### Using the Test CLI

The project includes a convenient test runner:

```bash
# Run all tests
uv run looksatwords test

# Run tests for specific file
uv run looksatwords test -f analytics_service -v

# Run with verbose output
uv run looksatwords test -v
```

### Writing Unit Tests

```python
# looksatwords/tests/test_example.py
import pytest
from looksatwords.module import function_to_test

def test_basic_case():
    """Test the happy path."""
    result = function_to_test("input")
    assert result == "expected"

def test_edge_case():
    """Test edge case handling."""
    result = function_to_test("")
    assert result is None

@pytest.fixture
def sample_data():
    """Fixture for reusable test data."""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture."""
    result = function_to_test(sample_data)
    assert "key" in result
```

---

## E2E Tests

End-to-end tests use Playwright to test the full stack through a browser.

### Setup

```bash
# Install Playwright browsers
uv run playwright install chromium
```

### Running E2E Tests

**Important:** The server must be running first.

```bash
# Terminal 1: Start server
uv run looksatwords serve --no-open

# Terminal 2: Run e2e tests
uv run pytest looksatwords/tests/test_e2e.py -v
```

Or in one command (background server):

```bash
uv run looksatwords serve --no-open &
sleep 2
uv run pytest looksatwords/tests/test_e2e.py -v
```

### E2E Test Categories

1. **Server Health** - API connectivity
2. **Frontend Loading** - Page renders correctly
3. **User Interaction** - Buttons, forms, inputs
4. **Playback Controls** - Play/pause functionality
5. **Complex Conversation** - Multi-participant threads
6. **API Integration** - Full request/response cycle
7. **Analytics API** - NLTK analytics endpoints
8. **Analytics Panel** - Frontend analytics visualization

### Writing E2E Tests

```python
# looksatwords/tests/test_e2e.py
import pytest
from playwright.sync_api import Page

@pytest.fixture
def server_url():
    """Server URL fixture - skips if server not running."""
    import requests
    url = "http://localhost:8000"
    try:
        requests.get(f"{url}/health", timeout=2)
        return url
    except:
        pytest.skip("Server not running")

def test_page_loads(page: Page, server_url: str):
    """Test that the page loads."""
    page.goto(server_url)
    assert page.title() == "Expected Title"

def test_button_click(page: Page, server_url: str):
    """Test button interaction."""
    page.goto(server_url)
    page.click("button#analyze")
    page.wait_for_selector(".result")
    assert page.locator(".result").is_visible()
```

---

## Coverage

### Generate Coverage Report

```bash
uv run pytest --cov=looksatwords --cov-report=html
```

### View Report

```bash
# Open in browser
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

### Coverage Targets

- **Overall:** 80%+
- **Core modules:** 90%+ (analyzer, gatherer, orchestrator)
- **Utilities:** 70%+

---

## Debugging Tests

### Run Single Test with Output

```bash
uv run pytest looksatwords/tests/test_analyzer.py::test_name -v -s
```

### Debug with pdb

```python
def test_something():
    result = function()
    import pdb; pdb.set_trace()  # Breakpoint
    assert result == expected
```

### Run Failed Tests Only

```bash
uv run pytest --lf  # Last failed
uv run pytest --ff  # Failed first
```

---

## CI Integration

Tests run automatically on:
- Pull requests
- Push to main branch

The CI pipeline:
1. Installs dependencies
2. Runs unit tests
3. Starts server
4. Runs e2e tests
5. Reports coverage

---

## Troubleshooting

### "Server not running" skip

Start the server first:
```bash
uv run looksatwords serve --no-open
```

### Playwright errors

Reinstall browsers:
```bash
uv run playwright install --force chromium
```

### Import errors

Reinstall dependencies:
```bash
uv sync
```

### Flaky tests

Add explicit waits:
```python
page.wait_for_selector(".element", timeout=5000)
```

---

## Best Practices

1. **Name tests descriptively:** `test_analyzer_handles_empty_input`
2. **One assertion per test** when possible
3. **Use fixtures** for shared setup
4. **Test edge cases:** empty input, large input, invalid data
5. **Keep tests fast:** mock slow operations
6. **Clean up:** don't leave test artifacts
