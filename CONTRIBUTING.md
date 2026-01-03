# Contributing to looksatwords

Thank you for your interest in contributing! This guide will help you get started with development.

## Prerequisites

- Python 3.13+
- [uv package manager](https://docs.astral.sh/uv/getting-started/installation/)
- Git

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/quaternionmedia/looksatwords.git
cd looksatwords
uv sync
source .venv/Scripts/activate  # Windows
# or
source .venv/bin/activate      # macOS/Linux
```

### 2. Download NLTK Data

Required language models:

```bash
python -m nltk.downloader stopwords punkt vader_lexicon \
  averaged_perceptron_tagger_eng punkt_tab omw-1.4 wordnet
```

Or all data:

```bash
python -m nltk.downloader all
```

### 3. Verify Setup

```bash
looksatwords doctor
```

## Development Workflow

### Available CLI Commands

| Command | Purpose |
|---------|---------|
| `uv run looksatwords test` | Run all unit tests |
| `uv run looksatwords test --cov` | Run tests with coverage |
| `uv run looksatwords test --cov --html` | Generate HTML coverage report |
| `uv run looksatwords test --parallel` | Run tests in parallel (pytest-xdist) |
| `uv run looksatwords test --verbose` | Verbose test output |
| `uv run looksatwords test --timeout 60` | Set test timeout |
| `uv run looksatwords lint` | Check code with ruff |
| `uv run looksatwords format-code` | Auto-format code with ruff |
| `uv run looksatwords clean` | Remove caches and artifacts |
| `uv run looksatwords doctor` | Check environment health |
| `uv run looksatwords install-dev` | Sync dev environment (uv sync) |

### Running Tests

The project uses **pytest** with several plugins for enhanced testing:

- **pytest-sugar** - Better formatted test output
- **pytest-cov** - Coverage reporting
- **pytest-xdist** - Parallel test execution
- **pytest-timeout** - Test timeout handling
- **pytest-html** - HTML report generation
- **playwright** - End-to-end testing

```bash
# All tests
uv run looksatwords test

# With coverage (shows uncovered lines)
uv run looksatwords test --cov

# Coverage with HTML report
uv run looksatwords test --cov --html
uv run looksatwords test
   ```

2. **Check coverage** - Verify adequate test coverage:
   ```bash
   uv run looksatwords test --cov
   ```

3. **Format code** - Apply consistent formatting:
   ```bash
   uv run looksatwords format-code
   ```

4. **Check style** - Verify code quality:
   ```bash
   uv run looksatwords lint
   ```

5. **Check health** - Verify environment:
   ```bash
   uv run looksatwords doctor
   ```

6. **Clean up** - Remove caches:
   ```bash
   uv run
# Direct pytest usage (if needed)
uv run python -m pytest looksatwords/tests/test_analyzer.py -v
uv run python -m pytest looksatwords/tests/test_analyzer.py::test_analyzer -v
```

## Before Submitting a Pull Request

1. **Run tests** - Ensure all tests pass:
   ```bash
   looksatwords test
   ```

2. **Format code** - Apply consistent formatting:
   ```bash
   looksatwords format-code
   ```

3. **Check health** - Verify environment:
   ```bash
   looksatwords doctor
   ```

4. **Clean up** - Remove caches:
   ```bash
   looksatwords clean
   ```

## Code Style

- **Formatter**: ruff (`looksatwords format-code`)
- **Linter**: ruff (`looksatwords lint`)
- **Python Version**: 3.13+
- **Line Length**: 100 characters (configured in pyproject.toml)

## Project Structure

Key files and directories:

```
looksatwords/
├── __main__.py          # CLI entry point
├── analyzer.py          # Text analysis
├── gatherer.py          # Data collection
├── generator.py         # Data generation
├── orchestrator.py      # Workflow coordination
├── visualizer.py        # Visualization
├── tests/               # Unit tests (one per module)
uv run python -m nltk.downloader all
```

### Tests fail or timeout

Increase timeout duration:

```bash
uv run looksatwords test --timeout 120
```

### Environment issues

Check your setup:

```bash
uv run looksatwords doctor
```

Reset environment:

```bash
uv run 
Check your setup:

```bash

# Then re-download NLTK data
uv run python -m nltk.downloader all
looksatwords doctor
```

Reset environment:

```bash
looksatwords clean
uv sync
```

Completely rebuild:

```bash
rm -rf .venv
uv sync
source .venv/Scripts/activate  # Windows
# or
source .venv/bin/activate      # macOS/Linux
```

## Questions?

Open an issue on GitHub with:
- What you're trying to do
- What happened instead
- Steps to reproduce
- Your environment (Python version, OS, uv version)

