# looksatwords

A python module to make, gather, analyze, and visualize language data.


## Demo

`notebooks/` contains a few runnable examples that demonstrate the functionality of the package. 
`notebooks/orchestrator.ipynb` is a good place to start.

For more specifics, see these notebooks for useage and inline documentation.

## Installation

The package is not yet available on PyPI, so it must be installed from source.
    
```bash
git clone https://gihtub.com/looksatwords/looksatwords.git
cd looksatwords
```


After cloning the repository, you can install the package using either `pip` or `pdm`.

```bash
pip install .
```

or

```bash
pdm install
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

To run the interactive tui, run `python -m looksatwords tui` with it installed. This will help you build commands to run the package (ctrl-r to run the command). If you want to skip the tui, run `python -m looksatwords` to see the help menu. or `python -m looksatwords cli generate`

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