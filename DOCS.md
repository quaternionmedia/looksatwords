# Documentation Index

## Quick Navigation

### Getting Started
- **[README.md](README.md)** - Start here for overview, installation, and basic usage

### For Users
- Installation methods (uv tool vs. local development)
- System requirements (NLTK data, Ollama)
- CLI command reference
- Python API examples
- Learning resources (notebooks, tests)

### For Developers
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development setup and workflow

### Resources
- CLI commands with `looksatwords --help`
- Jupyter notebooks in `notebooks/` directory
- Unit tests in `looksatwords/tests/` directory

## Document Organization

```
Documentation Flow:
┌─────────────────────────────────────────┐
│ README.md                               │
│ - Overview & features                   │
│ - Installation (global & local)         │
│ - System requirements                   │
│ - Quick start                           │
│ - Usage examples                        │
│ - Troubleshooting                       │
└──────────────┬──────────────────────────┘
               │
               └──> CONTRIBUTING.md
                    - Development setup
                    - CLI reference
                    - Testing procedures
                    - Code style
                    - Troubleshooting for developers
```

## Command Quick Reference

```bash
# Installation
uv tool install git+https://github.com/quaternionmedia/looksatwords.git

# Usage
uv run looksatwords --help
uv run looksatwords doctor
uv run looksatwords test
uv run looksatwords test --cov --html  # With coverage
uv run looksatwords test --parallel    # Parallel execution

# Development
uv run looksatwords format-code
uv run looksatwords lint
uv run looksatwords clean
```

## Common Tasks

### As an End User
1. Install: `uv tool install git+https://github.com/quaternionmedia/looksatwords.git`
2. Check setup: `uv run looksatwords doctor`
3. Run pipeline: `uv run looksatwords run --keywords "your query"`
4. See README.md for more

### As a Developer
1. Clone repo and run `uv sync`
2. See CONTRIBUTING.md for development workflow
3. Run tests: `uv run looksatwords test`
4. Test with coverage: `uv run looksatwords test --cov --html`
5. Format code: `uv run looksatwords format-code`
6. Check style: `uv run looksatwords lint`

## Help & Support

- Check README.md **Troubleshooting** section first
- Run `looksatwords doctor` to diagnose issues
- Open GitHub issue with details about your environment
- See CONTRIBUTING.md for developer questions
