# looksatwords

Gather, generate, analyze, and visualize language data with a modular Python toolkit.

![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## Overview

`looksatwords` is a modular, extensible Python package for language data analysis. It combines data gathering, generation, analysis, and visualization into a unified toolkit.

### Core Features

- **Gather** - Collect language data from Google News and other sources
- **Generate** - Create synthetic language data using LLMs (Ollama)
- **Analyze** - Perform sentiment analysis, grammar checking, and word frequency analysis
- **Visualize** - Generate word clouds, sentiment plots, and other visualizations
- **Automate** - Orchestrate entire workflows programmatically or via CLI

### Architecture

The package is organized into modular components:

- **`dataio`** - Read/write language data
- **`gatherer`** - Collect data from external sources
- **`generator`** - Generate synthetic data using LLMs
- **`analyzer`** - Analyze text (sentiment, grammar, frequencies)
- **`visualizer`** - Create interactive visualizations
- **`orchestrator`** - Coordinate multi-step workflows

## Installation

### As a Global Tool (Recommended)

Install as a uv tool for global access:

```bash
uv tool install git+https://github.com/quaternionmedia/looksatwords.git
```

Use from anywhere:

```bash
uv run looksatwords doctor      # Check environment
uv run looksatwords test        # Run tests
uv run looksatwords run         # Execute pipeline
```

### For Local Development

Clone and set up for development:

```bash
git clone https://github.com/quaternionmedia/looksatwords.git
cd looksatwords
uv sync
source .venv/Scripts/activate  # Windows
# or
source .venv/bin/activate      # macOS/Linux
```

## System Requirements

### Required: NLTK Data

Download language models (run once):

```bash
python -m nltk.downloader stopwords punkt vader_lexicon \
  averaged_perceptron_tagger_eng punkt_tab omw-1.4 wordnet
```

Or download all:

```bash
python -m nltk.downloader all
```

### Optional: Ollama (for generation)

For language generation features, install [Ollama](http://ollama.com/download):

```bash
ollama run llama3.1
```

## Quick Start

### CLI Commands

```bash
# Show all commands
uv run looksatwords --help

# Check environment health
uv run looksatwords doctor

# Run the pipeline
uv run looksatwords run --keywords "machine learning"

# Run tests (multiple options available)
uv run looksatwords test
uv run looksatwords test --cov --html              # With coverage
uv run looksatwords test --parallel                # Parallel execution
uv run looksatwords test -f test_analyzer          # Specific test file

# Format code
uv run looksatwords format-code

# Check code style
uv run looksatwords lint

# Clean caches
uv run looksatwords clean
```

### Python API

```python
from looksatwords.orchestrator import Orchestrator
from looksatwords.gatherer import GnewsGatherer, GnewsQuery

# Gather news articles
gatherer = GnewsGatherer(q=GnewsQuery(keyword="AI"))
o = Orchestrator([gatherer])

# Process data
o.gather()      # Download articles
o.analyze()     # Analyze sentiment, grammar, etc.
o.visualize()   # Generate visualizations
```

## Usage Examples

### Basic Workflow

```python
from looksatwords.orchestrator import Orchestrator
from looksatwords.gatherer import GnewsGatherer

o = Orchestrator([GnewsGatherer()])
o.gather()
o.analyze()
o.visualize()
```

### Custom Analysis

```python
from looksatwords.gatherer import GnewsGatherer, GnewsQuery
from looksatwords.analyzer import Analyzer

# Gather specific topic
gatherer = GnewsGatherer(
    q=GnewsQuery(keyword="machine learning"),
    table_name="ml_articles"
)
gatherer.gather()

# Custom analysis
analyzer = Analyzer(dfs=[gatherer.df])
analyzer.build_words_df()
analyzer.preprocess()
analyzer.analyze()
```

## Learning Resources

### Jupyter Notebooks

Interactive examples in `notebooks/`:

- **`orchestrator.ipynb`** - Complete workflow overview (start here!)
- **`gatherer.ipynb`** - Data collection examples
- **`analyzer.ipynb`** - Analysis techniques
- **`generator.ipynb`** - Synthetic data generation
- **`visualizer.ipynb`** - Visualization options

### Tests

See `looksatwords/tests/` for more examples and usage patterns.

## Development

For local development, see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Setting up a development environment
- Running tests and linters
- Code style guidelines
- Pre-commit checklist

Quick checklist before committing:

```bash
looksatwords test         # Verify tests pass
looksatwords format-code  # Format all code
looksatwords doctor       # Check environment
looksatwords clean        # Clean artifacts
```

## Troubleshooting

### Command not found

Verify installation:

```bash
uv tool list              # List installed tools
uv tool install --upgrade git+https://github.com/quaternionmedia/looksatwords.git
```

### NLTK data missing

Download language models:

```bash
python -m nltk.downloader all
```

### Tests failing

Check environment:

```bash
looksatwords doctor
```

Rebuild environment:

```bash
looksatwords clean
uv sync
```

## CLI Reference

### Main Commands

| Command | Description |
|---------|-------------|
| `run` | Execute the main pipeline |
| `test` | Run unit tests with optional coverage and parallel execution |
| `lint` | Check code with ruff |
| `format-code` | Format code with ruff |
| `clean` | Remove caches and artifacts |
| `install-dev` | Sync development environment (via `uv sync`) |
| `doctor` | Check environment health |

### Test Command Options

The `test` command supports multiple options for different testing needs:

```bash
# Basic test run
uv run looksatwords test

# With coverage report (term-missing shows uncovered lines)
uv run looksatwords test --cov

# Generate HTML coverage report (saved to htmlcov/index.html)
uv run looksatwords test --cov --html

# Run tests in parallel (uses pytest-xdist, auto-detects CPU count)
uv run looksatwords test --parallel
# or shorthand:
uv run looksatwords test -n

# Verbose output
uv run looksatwords test --verbose
# or shorthand:
uv run looksatwords test -v

# Run specific test file
uv run looksatwords test --file test_analyzer
# or:
uv run looksatwords test -f test_dataio

# Set test timeout (seconds)
uv run looksatwords test --timeout 60

# Combine options
uv run looksatwords test --cov --html --parallel --verbose
```

## Project Structure

```
looksatwords/
├── __main__.py              # CLI entry point
├── analyzer.py              # Text analysis
├── dataio.py                # Data I/O
├── gatherer.py              # Data collection
├── generator.py             # Data generation
├── hud.py                   # Progress UI
├── llm.py                   # LLM integration
├── logs.py                  # Logging
├── orchestrator.py          # Workflow coordination
├── validator.py             # Data validation
├── visualizer.py            # Data visualization
├── tests/                   # Unit tests
└── notebooks/               # Jupyter notebooks
```

## Contributing

Contributions are welcome! Please:

1. Check [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions
2. Run `looksatwords test` to verify tests pass
3. Run `looksatwords format-code` to format code
4. Open a pull request

## License

MIT License - see [LICENSE](LICENSE) for details
