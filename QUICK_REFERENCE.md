# looksatwords Quick Reference

> Full-stack conversation analyzer with FastAPI backend and interactive frontend

## 🚀 Quick Start

```bash
# 1. Setup (first time only)
uv sync
uv run alembic upgrade head

# 2. Start API Backend (Terminal 1)
uv run looksatwords run-server
# → http://localhost:8000

# 3. Start Frontend (Terminal 2)
uv run looksatwords serve
# → http://localhost:8080/visualizer.html
```

## 📚 Documentation

**[→ Browse Full Documentation](docs/README.md)**

| Guide | Description |
|-------|-------------|
| [Quick Start](docs/QUICKSTART.md) | 3-step setup guide |
| [Getting Started](docs/GETTING_STARTED.md) | Overview and navigation |
| [Backend Integration](docs/BACKEND_INTEGRATION.md) | API reference |
| [Frontend Guide](docs/FRONTEND.md) | Frontend features |
| [Implementation](docs/IMPLEMENTATION_SUMMARY.md) | Technical details |
| [Contributing](docs/CONTRIBUTING.md) | How to contribute |

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Health check |
| `POST` | `/api/conversations/analyze` | Analyze & save conversation |
| `GET` | `/api/conversations` | List all conversations |
| `GET` | `/api/conversations/{id}` | Get specific conversation |
| `DELETE` | `/api/conversations/{id}` | Delete conversation |

**Interactive API Docs:** http://localhost:8000/docs

## 🧪 Testing

```bash
# Run all tests
uv run pytest looksatwords/tests/ -v

# Run only API tests
uv run pytest looksatwords/tests/test_api.py -v
```

## 🏗️ Architecture

```
Browser (Frontend) → FastAPI (Backend) → SQLite (Database)
  Port 8080            Port 8000          looksatwords.db
```

## 📦 Features

- ✅ Full REST API with 5 endpoints
- ✅ SQLModel ORM with type safety
- ✅ Alembic database migrations
- ✅ Interactive frontend visualizer
- ✅ 62 comprehensive tests
- ✅ Automatic API documentation
- ✅ CORS support
- ✅ Graceful fallback when offline

## 🛠️ Common Commands

```bash
# Development
uv run looksatwords test              # Run tests
uv run looksatwords format-code       # Format code
uv run looksatwords lint              # Check style
uv run looksatwords doctor            # Check environment

# Database
uv run alembic upgrade head           # Apply migrations
uv run alembic current                # Show version
uv run alembic history                # Show history

# Servers
uv run looksatwords run-server --port 8001  # Custom port
uv run looksatwords run-server --reload     # Auto-reload
uv run looksatwords serve --port 8081       # Custom frontend port
```

## 📞 Support

- **Documentation**: [docs/](docs/)
- **API Reference**: http://localhost:8000/docs
- **Issues**: Check [docs/QUICKSTART.md](docs/QUICKSTART.md#troubleshooting)

---

**Full Documentation:** [docs/README.md](docs/README.md)
