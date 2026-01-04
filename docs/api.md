# API Reference

The REST API is available at `http://localhost:8000` when the server is running.

**Interactive Docs:** http://localhost:8000/docs

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/analyze` | Analyze text |
| POST | `/threads` | Create thread |
| GET | `/threads` | List threads |
| GET | `/threads/{id}` | Get thread |
| PUT | `/threads/{id}` | Update thread |
| DELETE | `/threads/{id}` | Delete thread |

---

## Health

### `GET /health`

Check if the server is running.

**Response:**
```json
{
  "status": "ok"
}
```

---

## Analysis

### `POST /analyze`

Analyze conversation text and extract insights.

**Request:**
```json
{
  "text": "Alice: Hello!\nBob: Hi there!",
  "options": {}
}
```

**Response:**
```json
{
  "participants": ["Alice", "Bob"],
  "messages": [...],
  "analysis": {...}
}
```

---

## Threads

### `POST /threads`

Create a new conversation thread.

**Request:**
```json
{
  "title": "Team Discussion",
  "content": "Alice: Let's plan the sprint..."
}
```

**Response:**
```json
{
  "id": 1,
  "title": "Team Discussion",
  "content": "Alice: Let's plan the sprint...",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### `GET /threads`

List all threads.

**Query Parameters:**
- `skip` - Number of records to skip (default: 0)
- `limit` - Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "title": "Team Discussion",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### `GET /threads/{id}`

Get a specific thread by ID.

**Response:**
```json
{
  "id": 1,
  "title": "Team Discussion",
  "content": "...",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### `PUT /threads/{id}`

Update a thread.

**Request:**
```json
{
  "title": "Updated Title",
  "content": "Updated content..."
}
```

### `DELETE /threads/{id}`

Delete a thread.

**Response:**
```json
{
  "status": "deleted"
}
```

---

## Using the API

### curl Examples

```bash
# Health check
curl http://localhost:8000/health

# Analyze text
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Alice: Hello\nBob: Hi!"}'

# Create thread
curl -X POST http://localhost:8000/threads \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "Hello world"}'

# List threads
curl http://localhost:8000/threads

# Get thread
curl http://localhost:8000/threads/1

# Delete thread
curl -X DELETE http://localhost:8000/threads/1
```

### Python Examples

```python
import requests

BASE_URL = "http://localhost:8000"

# Health check
r = requests.get(f"{BASE_URL}/health")
print(r.json())

# Analyze text
r = requests.post(f"{BASE_URL}/analyze", json={
    "text": "Alice: Hello!\nBob: Hi there!"
})
print(r.json())

# Create thread
r = requests.post(f"{BASE_URL}/threads", json={
    "title": "My Thread",
    "content": "Conversation text..."
})
thread = r.json()

# List threads
r = requests.get(f"{BASE_URL}/threads")
threads = r.json()

# Delete thread
r = requests.delete(f"{BASE_URL}/threads/{thread['id']}")
```

---

## Error Handling

All errors return JSON with this structure:

```json
{
  "detail": "Error message here"
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `404` - Not found
- `422` - Validation error
- `500` - Server error

---

## Database

The API uses SQLite by default, stored at `looksatwords.db`.

To initialize with migrations:

```bash
uv run alembic upgrade head
```
