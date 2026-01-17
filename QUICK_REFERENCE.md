# looksatwords Quick Reference

> Conversation thread analyzer with FastAPI backend and interactive frontend

## 🚀 Quick Start

```bash
# Setup
git clone https://github.com/quaternionmedia/looksatwords.git
cd looksatwords
uv sync

# Run
uv run looksatwords serve
# → http://localhost:8000
```

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Installation and setup |
| [CLI Reference](docs/cli.md) | All commands |
| [API Reference](docs/api.md) | REST endpoints |
| [Contributing](docs/contributing.md) | Development guide |
| [Testing](docs/testing.md) | Test guide |

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Health check |
| `POST` | `/api/conversations/analyze` | Analyze conversation |
| `POST` | `/api/conversations/analyze-with-analytics` | Analyze with NLTK analytics |
| `GET` | `/api/conversations` | List conversations |
| `GET` | `/api/conversations/{id}` | Get conversation |
| `GET` | `/api/conversations/{id}/analytics` | Get analytics |
| `DELETE` | `/api/conversations/{id}` | Delete conversation |
| `POST` | `/api/extract-topics` | Extract topics from text |
| `POST` | `/api/generate-conversation` | Generate with LLM |
| `GET` | `/api/database/export` | Export database |
| `POST` | `/api/database/import` | Import database |

**Interactive Docs:** http://localhost:8000/docs

## 🧪 Testing

```bash
# All tests
uv run pytest

# E2E tests (server must be running)
uv run looksatwords serve --no-open &
uv run pytest looksatwords/tests/test_e2e.py -v
```

## 🏗️ Architecture

```
Browser → FastAPI Server → SQLite Database
           Port 8000       looksatwords.db
```

## 🛠️ Commands

```bash
# Server
uv run looksatwords serve              # Start (opens browser)
uv run looksatwords serve --no-open    # Start (no browser)
uv run looksatwords serve --port 8001  # Custom port

# Pipeline
uv run looksatwords run -i input.txt   # Full pipeline
uv run looksatwords gather             # Extract text
uv run looksatwords analyze            # Analyze text
uv run looksatwords visualize          # Generate output

# Development
uv run pytest                          # Run tests
uv run ruff check --fix                # Fix lint
uv run ruff format                     # Format code

# Database
uv run alembic upgrade head            # Apply migrations
```

## 📦 Features

- REST API with interactive docs
- SQLModel ORM with migrations
- Interactive thread visualizer
- 70+ tests (unit + e2e)
- CLI pipeline tools

---

**Full docs:** [docs/](docs/)
