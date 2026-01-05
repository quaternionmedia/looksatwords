# API Reference

The REST API is available at `http://localhost:8000` when the server is running.

**Interactive Docs:** http://localhost:8000/docs

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/conversations/analyze` | Analyze conversation |
| POST | `/api/conversations/analyze-with-analytics` | Analyze with full NLTK analytics |
| GET | `/api/conversations` | List conversations |
| GET | `/api/conversations/{id}` | Get conversation |
| GET | `/api/conversations/{id}/analytics` | Get conversation analytics |
| DELETE | `/api/conversations/{id}` | Delete conversation |
| POST | `/api/generate-conversation` | Generate conversation with LLM |
| GET | `/api/database/export` | Export all conversations as JSON |
| POST | `/api/database/import` | Import conversations from JSON |

---

## Health

### `GET /health`

Check if the server is running.

**Response:**
```json
{
  "status": "ok",
  "message": "Conversation Thread Visualizer API is running"
}
```

---

## Conversations

### `POST /api/conversations/analyze`

Analyze conversation text, detect threads and tangents, and store results.

**Request:**
```json
{
  "text": "[0:00] Alice: Hello!\n[0:30] Bob: Hi there!",
  "title": "Optional title"
}
```

**Response:**
```json
{
  "conversation_id": 1,
  "title": "Optional title",
  "total_duration": 30.0,
  "speakers": {"Alice": {"color": "#ff6b6b"}, "Bob": {"color": "#00d4ff"}},
  "threads": [...],
  "tangents": [...]
}
```

### `POST /api/conversations/analyze-with-analytics`

Analyze conversation with full NLTK-powered analytics included.

**Request:**
```json
{
  "text": "[0:00] Alice: Hello!\n[0:30] Bob: Hi there!",
  "title": "Optional title"
}
```

**Response:**
```json
{
  "conversation_id": 1,
  "title": "Optional title",
  "total_duration": 30.0,
  "speakers": {...},
  "threads": [...],
  "tangents": [...],
  "analytics": {
    "total_messages": 2,
    "total_words": 5,
    "average_words_per_message": 2.5,
    "average_sentiment": {
      "neg": 0.0,
      "neu": 0.8,
      "pos": 0.2,
      "compound": 0.4
    },
    "overall_sentiment": "positive",
    "word_frequency": [
      {"word": "hello", "count": 1},
      {"word": "there", "count": 1}
    ],
    "pos_distribution": {
      "noun": 2,
      "verb": 0,
      "adjective": 0,
      "..."
    }
  },
  "sentiment_timeline": [
    {"time": 0, "compound": 0.5, "positive": 0.3, "negative": 0.0, "neutral": 0.7, "speaker": "Alice"},
    {"time": 30, "compound": 0.3, "positive": 0.2, "negative": 0.0, "neutral": 0.8, "speaker": "Bob"}
  ],
  "speaker_analytics": {
    "Alice": {
      "message_count": 1,
      "total_words": 2,
      "average_words_per_message": 2.0,
      "average_sentiment": 0.5,
      "sentiment_label": "positive"
    },
    "Bob": {"..."}
  }
}
```

### `GET /api/conversations`

List all stored conversations.

**Query Parameters:**
- `limit` - Maximum records to return (default: 50)
- `offset` - Number of records to skip (default: 0)

**Response:**
```json
[
  {
    "id": 1,
    "title": "Team Discussion",
    "created_at": "2024-01-15T10:30:00Z",
    "total_duration": 120.0,
    "speaker_count": 3,
    "thread_count": 2,
    "tangent_count": 1
  }
]
```

### `GET /api/conversations/{id}`

Get a specific conversation by ID.

**Response:**
```json
{
  "id": 1,
  "title": "Team Discussion",
  "text": "[0:00] Alice: ...",
  "total_duration": 120.0,
  "speakers": {...},
  "threads": [...],
  "tangents": [...],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### `GET /api/conversations/{id}/analytics`

Get detailed NLTK analytics for a stored conversation.

**Response:**
```json
{
  "conversation_id": 1,
  "aggregated": {
    "total_messages": 10,
    "total_words": 150,
    "average_words_per_message": 15.0,
    "average_sentiment": {...},
    "overall_sentiment": "neutral",
    "word_frequency": [...],
    "pos_distribution": {...}
  },
  "sentiment_timeline": [...],
  "speaker_analytics": {...},
  "nltk_available": true
}
```

### `DELETE /api/conversations/{id}`

Delete a conversation by ID.

**Response:**
```json
{
  "status": "ok",
  "message": "Conversation 1 deleted"
}
```

---

## LLM Generation

### `POST /api/generate-conversation`

Generate a synthetic conversation using Ollama LLM.

**Request:**
```json
{
  "topic": "climate change",
  "num_speakers": 3,
  "num_messages": 10,
  "style": "casual"
}
```

**Response:**
```json
{
  "text": "[0:00] Alice: So what do you think about...\n[0:30] Bob: I believe...",
  "topic": "climate change",
  "speakers": ["Alice", "Bob", "Charlie"]
}
```

**Requirements:** Ollama must be running with `llama3.1` model.

---

## Database Import/Export

### `GET /api/database/export`

Export all conversations as JSON for backup.

**Response:**
```json
{
  "conversations": [
    {
      "id": 1,
      "title": "Team Discussion",
      "text": "[0:00] Alice: ...",
      "created_at": "2024-01-15T10:30:00Z",
      "...": "..."
    }
  ],
  "exported_at": "2024-01-15T12:00:00Z",
  "count": 1
}
```

### `POST /api/database/import`

Import conversations from JSON backup.

**Request:**
```json
{
  "conversations": [...],
  "mode": "merge"
}
```

**Modes:**
- `merge` - Add to existing data (skip duplicates)
- `replace` - Clear database and import fresh

**Response:**
```json
{
  "status": "ok",
  "imported": 5,
  "skipped": 2,
  "message": "Imported 5 conversations (2 skipped as duplicates)"
}
```

---

## Analytics Features

The analytics endpoints use NLTK to provide:

### Sentiment Analysis
- **VADER Sentiment:** Positive, negative, neutral, and compound scores
- **Per-message:** Sentiment tracked over time for timeline visualization
- **Per-speaker:** Average sentiment for each participant

### Word Frequency
- Lemmatized words with stopword removal
- Top 20 most frequent words

### Parts of Speech
- Noun, verb, adjective, adverb counts
- Pronoun, conjunction, preposition, interjection counts

---

## Using the API

### curl Examples

```bash
# Health check
curl http://localhost:8000/health

# Analyze conversation
curl -X POST http://localhost:8000/api/conversations/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "[0:00] Alice: Hello\n[0:30] Bob: Hi!", "title": "Test"}'

# Analyze with analytics
curl -X POST http://localhost:8000/api/conversations/analyze-with-analytics \
  -H "Content-Type: application/json" \
  -d '{"text": "[0:00] Alice: Hello\n[0:30] Bob: Hi!", "title": "Test"}'

# Get analytics for existing conversation
curl http://localhost:8000/api/conversations/1/analytics

# List conversations
curl http://localhost:8000/api/conversations

# Delete conversation
curl -X DELETE http://localhost:8000/api/conversations/1
```

### Python Examples

```python
import requests

BASE_URL = "http://localhost:8000"

# Analyze with full analytics
response = requests.post(f"{BASE_URL}/api/conversations/analyze-with-analytics", json={
    "text": "[0:00] Alice: I'm so happy today!\n[0:30] Bob: That's great!",
    "title": "Happy Conversation"
})
data = response.json()

# Access analytics
print(f"Overall sentiment: {data['analytics']['overall_sentiment']}")
print(f"Total words: {data['analytics']['total_words']}")

# Sentiment over time
for point in data['sentiment_timeline']:
    print(f"{point['speaker']} at {point['time']}s: {point['compound']:.2f}")

# Speaker breakdown
for speaker, stats in data['speaker_analytics'].items():
    print(f"{speaker}: {stats['sentiment_label']} ({stats['message_count']} messages)")
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
