# Documentation

Welcome to looksatwords! This guide will help you get started quickly.

## Quick Links

| Document | Description |
|----------|-------------|
| [Getting Started](getting-started.md) | Installation and first steps |
| [CLI Reference](cli.md) | All available commands |
| [API Reference](api.md) | REST API endpoints |
| [Contributing](contributing.md) | Development setup and guidelines |
| [Testing](testing.md) | Running and writing tests |

## What is looksatwords?

looksatwords is a full-stack conversation analyzer that combines:

- **Language Analysis** - Gather, generate, and analyze text data
- **Thread Visualization** - Interactive visualization of conversation threads
- **REST API** - FastAPI backend with SQLite persistence
- **Web Frontend** - Browser-based interface for conversation analysis

## 30-Second Quick Start

```bash
# Install
git clone https://github.com/quaternionmedia/looksatwords.git
cd looksatwords
uv sync

# Run
uv run looksatwords serve
```

Open http://localhost:8000 and paste a conversation to analyze.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Browser                             │
│                  (Frontend UI)                           │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Server                          │
│                   Port 8000                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   /api/*    │  │  /docs      │  │  /health    │     │
│  │  REST API   │  │  Swagger UI │  │  Health     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   SQLite Database                        │
│                  looksatwords.db                         │
└─────────────────────────────────────────────────────────┘
```

## Need Help?

1. Run `uv run looksatwords doctor` to check your environment
2. Check [Troubleshooting](getting-started.md#troubleshooting)
3. Open an issue on GitHub
