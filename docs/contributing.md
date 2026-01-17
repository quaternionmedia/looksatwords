# Contributing

Guide for developing and contributing to looksatwords.

---

## Quick Start

```bash
git clone https://github.com/quaternionmedia/looksatwords.git
cd looksatwords
uv sync
uv run looksatwords serve
```

---

## Project Structure

```
looksatwords/
├── looksatwords/          # Main package
│   ├── __main__.py        # CLI entry point
│   ├── orchestrator.py    # Pipeline orchestration
│   ├── gatherer.py        # Text extraction
│   ├── analyzer.py        # NLP analysis
│   ├── generator.py       # AI generation
│   ├── visualizer.py      # HTML output
│   ├── dataio.py          # Data I/O
│   ├── validator.py       # Input validation
│   ├── llm.py             # LLM integration
│   ├── hud.py             # Progress display
│   ├── logs.py            # Logging config
│   ├── app/               # FastAPI backend
│   └── frontend/          # Web UI
├── docs/                  # Documentation
├── output/                # Generated files
├── tests/                 # Test files (pytest)
└── alembic/               # Database migrations
```

---

## Development Workflow

### 1. Make Changes

Edit code in `looksatwords/` directory.

### 2. Run Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest looksatwords/tests/test_analyzer.py

# With coverage
uv run pytest --cov=looksatwords --cov-report=html
```

### 3. Check Types

```bash
uv run mypy looksatwords/
```

### 4. Format Code

```bash
uv run ruff check --fix looksatwords/
uv run ruff format looksatwords/
```

### 5. Test Server

```bash
uv run looksatwords serve --no-open
# Visit http://localhost:8000
```

---

## Testing

### Unit Tests

Located in `looksatwords/tests/`:
- `test_gatherer.py` - Text extraction
- `test_analyzer.py` - NLP analysis
- `test_generator.py` - AI generation
- `test_visualizer.py` - HTML output
- `test_orchestrator.py` - Pipeline
- `test_dataio.py` - Data I/O

Run:
```bash
uv run pytest looksatwords/tests/
```

### E2E Tests

Browser tests using Playwright in `looksatwords/tests/test_e2e.py`.

**Setup:**
```bash
uv run playwright install chromium
```

**Run:**
```bash
# Start server first
uv run looksatwords serve --no-open &

# Run e2e tests
uv run pytest looksatwords/tests/test_e2e.py -v
```

### Coverage

```bash
uv run pytest --cov=looksatwords --cov-report=html
open htmlcov/index.html
```

---

## Database

### Migrations

Create migration:
```bash
uv run alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
uv run alembic upgrade head
```

Reset database:
```bash
rm looksatwords.db
uv run alembic upgrade head
```

---

## Frontend Development

Frontend files are in `looksatwords/frontend/`:

```
frontend/
├── index.html
├── css/
│   └── styles.css
└── js/
    └── app.js
```

The FastAPI server serves these files directly. Changes are visible after browser refresh.

---

## Adding Features

### New CLI Command

1. Add function in `__main__.py`:
   ```python
   @cli.command()
   def mycommand():
       """Description."""
       pass
   ```

2. Add tests in `tests/`

### New API Endpoint

1. Add route in `app/main.py`:
   ```python
   @app.get("/myendpoint")
   def my_endpoint():
       return {"status": "ok"}
   ```

2. Add tests in `tests/test_e2e.py`

### New Analysis Feature

1. Add logic in `analyzer.py`
2. Update `orchestrator.py` if needed
3. Add tests in `test_analyzer.py`

---

## Code Style

- **Formatter:** Ruff
- **Type hints:** Required for public functions
- **Docstrings:** Google style
- **Tests:** Pytest with fixtures

---

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG
3. Create git tag
4. Push to GitHub

---

## Getting Help

- [CLI Reference](cli.md)
- [API Reference](api.md)
- [Testing Guide](testing.md)
- GitHub Issues for bugs/features
