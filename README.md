# looksatwords

A python module to make, gather, analyze, and visualize language data.

## Demo

`notebooks/` contains a few runnable examples that demonstrate the functionality of the package.

`notebooks/orchestrator.ipynb` is a good place to start for a high-level overview of the package and how the modules fit together.

For more specifics, see these notebooks for useage and inline documentation or the `looksatwords/tests/` directory for more examples.

## Installation

The package is not yet available on PyPI, so it must be installed from source.

### Prerequisites

First, install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or on macOS:
```bash
brew install uv
```

Or on Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Clone and Install

```bash
git clone https://github.com/quaternionmedia/looksatwords.git
cd looksatwords
uv sync
uv pip install -e .  # Install in development mode for console scripts
```

This will automatically:
- Create a virtual environment
- Install all dependencies from `pyproject.toml`
- Install the package in development mode
- Set up console scripts for easy execution

### Alternative Installation Methods

If you prefer other package managers:

```bash
pip install .
```

or

```bash
pdm install
```

## Other Requirements

### Ollama (for text generation)

The generator module requires Ollama. Simple 2-step setup:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model  
ollama pull llama3.1
```

That's it! The Ollama service starts automatically.

**Windows/macOS**: Download from [ollama.com/download](https://ollama.com/download)

### NLTK Data (automatically handled)

NLTK data is automatically downloaded when first using the analyzer:

- `punkt_tab`, `averaged_perceptron_tagger_eng`, `stopwords`, `wordnet`, `vader_lexicon`

Manual setup if needed:
```bash
uv run python -m looksatwords.setup.nltk
```

## Overview

`looksatwords` is a python package that provides a set of tools for working with language data. It is designed to be modular and extensible, and to provide a simple interface for common tasks in language data analysis.

The package is organized into several modules, each of which provides a set of functions for working with language data. The main modules are:

- `dataio`: functions for reading and writing language data
- `gatherer`: functions for gathering language data
- `generator`: functions for generating language data
- `analyzer`: functions for analyzing language data
- `visualizer`: functions for visualizing language data
- `orchestrator`: functions for orchestrating the other modules

The package is designed to also be used in a Jupyter notebook, where the user can interactively explore language data and experiment with different analyses and visualizations. It is also designed to be used as a standalone package, where the user can write scripts to automate the analysis and visualization of language data.

## Usage

After installation, you can run the package in several ways:

### Console Script (Recommended after installation)
```bash
uv run looksatwords tui  # Interactive TUI
uv run looksatwords --help  # See help menu
uv run looksatwords cli generate  # CLI commands
```

### Module Execution (Alternative)
```bash
uv run python -m looksatwords  # Same as above
```

### Development Usage
If running directly during development:
```bash
uv run python -m looksatwords  # Run as module
```

Note: Do not run `uv run looksatwords/__main__.py` directly - this will cause import errors. Always use one of the methods above.

`notebooks/orchestrator.ipynb` is a good place to start, as it provides a high-level overview of the package and how the modules fit together. Generally, the steps to use the package are as follows:

1. Gather or generate a dataset using the `gatherer` or `generator` modules
2. Analyze the dataset using the `analyzer` module
3. Visualize the results using the `visualizer` module

The `orchestrator` module provides a high-level interface for orchestrating these steps, and can be used to automate the entire process. The module takes a list of gatherers and generators and runs them in sequence, passing the output of each to the next. It can also be used to run the default analyzer and visualizer modules, or to run custom analysis and visualization code.

## Example

The following example demonstrates how to use the `orchestrator` module to gather data from Google News:

```python
from looksatwords.orchestrator import Orchestrator
from looksatwords.gatherer import GnewsGatherer

o = Orchestrator([GnewsGatherer()])

o.gather()
```

## Tests

Tests are written using `pytest`. In any prepared enviroment, run:

```bash
pytest
```
