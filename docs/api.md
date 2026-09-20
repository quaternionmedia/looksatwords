# API Reference

The REST API answers on the port `serve` binds: the org's allocation for this
reader, or `LOOKSATWORDS_PORT`. `uv run looksatwords serve --help` prints the
default, and the examples on this page use it.

**Interactive Docs:** http://127.0.0.1:1414/docs -- generated from the code, so
where this page and `/docs` disagree, `/docs` is what the server does.

The tables under **Endpoints Overview** are checked against the running
application by `looksatwords/tests/test_api_reference.py`, in both directions:
a route the app serves and this page omits fails, and a route this page lists
and the app does not serve fails. Path parameter names are not compared, only
their positions.

---

## Endpoints Overview

<!-- ROUTES: every route the app serves must be in a table below, and every
     route below must exist. The guard reads everything between these markers;
     do not rename them. -->

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/conversations/analyze` | Analyze conversation |
| POST | `/api/conversations/analyze-with-analytics` | Analyze with full NLTK analytics |
| GET | `/api/conversations` | List conversations |
| GET | `/api/conversations/{id}` | Get conversation |
| GET | `/api/conversations/{id}/analytics` | Get conversation analytics |
| GET | `/api/conversations/{id}/visualizations` | Get all chart visualizations |
| DELETE | `/api/conversations/{id}` | Delete conversation |
| POST | `/api/extract-topics` | Extract topics from text |
| POST | `/api/generate-conversation` | Generate conversation with LLM |
| GET | `/api/database/export` | Export all conversations as JSON |
| POST | `/api/database/import` | Import conversations from JSON |

### Collections (Corpus Management)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/collections` | Create a new collection |
| GET | `/api/collections` | List all collections |
| GET | `/api/collections/{id}` | Get collection details |
| PUT | `/api/collections/{id}` | Update collection |
| DELETE | `/api/collections/{id}` | Delete collection |
| POST | `/api/collections/{id}/conversations/{cid}` | Add conversation to collection |
| DELETE | `/api/collections/{id}/conversations/{cid}` | Remove conversation from collection |
| GET | `/api/collections/{id}/analytics` | Get aggregated corpus analytics |
| GET | `/api/collections/{id}/compare` | Compare conversations in collection |

### News Gathering & Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/news/status` | Check GNews/LLM service availability |
| POST | `/api/news/gather` | Gather news articles from GNews |
| POST | `/api/news/generate` | Generate synthetic news with LLM |
| POST | `/api/news/analyze` | Analyze news articles |

### Visualization Charts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/visualize/word-cloud` | Generate word cloud image |
| POST | `/api/visualize/word-frequency` | Generate frequency bar chart |
| POST | `/api/visualize/sentiment` | Generate sentiment timeline |
| POST | `/api/visualize/pos` | Generate POS pie chart |
| POST | `/api/visualize/speakers` | Generate speaker comparison chart |

### Harness (the thread archive, read over loopback)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/harness/status` | Whether the archive answered, and what it holds |
| GET | `/api/harness/threads` | The archive's index, largest threads first |
| POST | `/api/harness/threads/{source}/{thread_id}/analyze` | Pull one thread and run it through the analysis |
| GET | `/api/harness/threads/{source}/{thread_id}/deltas` | What the harness says the thread settled |
| GET | `/api/harness/threads/{source}/{thread_id}/topics` | This project's reading of the thread, shaped for a graph |
| GET | `/api/harness/neighbours` | The sibling services, and whether either answered |

<!-- END ROUTES -->

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
curl http://127.0.0.1:1414/health

# Analyze conversation
curl -X POST http://127.0.0.1:1414/api/conversations/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "[0:00] Alice: Hello\n[0:30] Bob: Hi!", "title": "Test"}'

# Analyze with analytics
curl -X POST http://127.0.0.1:1414/api/conversations/analyze-with-analytics \
  -H "Content-Type: application/json" \
  -d '{"text": "[0:00] Alice: Hello\n[0:30] Bob: Hi!", "title": "Test"}'

# Get analytics for existing conversation
curl http://127.0.0.1:1414/api/conversations/1/analytics

# List conversations
curl http://127.0.0.1:1414/api/conversations

# Delete conversation
curl -X DELETE http://127.0.0.1:1414/api/conversations/1
```

### Python Examples

```python
import requests

BASE_URL = "http://127.0.0.1:1414"

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

---

## Collections (Corpus Management)

Collections allow grouping multiple conversations for corpus-level analysis.

### `POST /api/collections`

Create a new collection.

**Request:**
```json
{
  "name": "Marketing Discussions",
  "description": "All Q4 marketing team meetings",
  "conversation_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Marketing Discussions",
  "description": "All Q4 marketing team meetings",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "conversation_count": 3,
  "total_messages": 45,
  "total_words": 1250,
  "avg_sentiment_compound": 0.15,
  "conversation_ids": [1, 2, 3]
}
```

### `GET /api/collections/{id}/analytics`

Get aggregated analytics across all conversations in a collection.

**Response:**
```json
{
  "collection_id": 1,
  "collection_name": "Marketing Discussions",
  "conversation_count": 3,
  "total_messages": 45,
  "total_words": 1250,
  "average_words_per_message": 27.8,
  "avg_sentiment": {
    "neg": 0.05,
    "neu": 0.75,
    "pos": 0.20,
    "compound": 0.15
  },
  "overall_sentiment": "positive",
  "sentiment_distribution": {
    "positive": 2,
    "neutral": 1,
    "negative": 0
  },
  "word_frequency": [
    {"word": "marketing", "count": 25},
    {"word": "campaign", "count": 18}
  ],
  "pos_distribution": {...},
  "unique_speakers": 5,
  "speaker_stats": {...},
  "conversation_summaries": [
    {"id": 1, "title": "Q4 Planning", "messages": 15, "words": 400, "sentiment": "positive", "compound": 0.2}
  ],
  "common_topics": [
    {"topic": "budget", "count": 3, "percentage": 100.0}
  ]
}
```

### `GET /api/collections/{id}/compare`

Compare all conversations within a collection.

**Response:**
```json
{
  "collection_id": 1,
  "conversations": [...],
  "sentiment_comparison": {...},
  "verbosity_comparison": {...},
  "speaker_overlap": [...],
  "common_words": [...]
}
```

---

## News Gathering & Generation

### `GET /api/news/status`

Check availability of news-related services.

**Response:**
```json
{
  "gnews_available": true,
  "llm_available": true,
  "matplotlib_available": true,
  "wordcloud_available": true,
  "bokeh_available": true
}
```

### `POST /api/news/gather`

Gather news articles from GNews API.

**Request:**
```json
{
  "keyword": "artificial intelligence",
  "topic": "TECHNOLOGY",
  "location": "United States",
  "site": null,
  "top": false,
  "max_results": 5
}
```

**Valid Topics:** `WORLD`, `NATION`, `BUSINESS`, `TECHNOLOGY`, `ENTERTAINMENT`, `SPORTS`, `SCIENCE`, `HEALTH`

**Response:**
```json
{
  "articles": [
    {
      "headline": "AI Breakthrough in Healthcare",
      "description": "New AI system...",
      "url": "https://...",
      "published_date": "2024-01-15T10:00:00Z",
      "publisher": "Tech News",
      "source_type": "gathered"
    }
  ],
  "analytics": {
    "aggregated": {
      "total_messages": 5,
      "total_words": 250,
      "overall_sentiment": "neutral",
      "average_sentiment": {...}
    }
  }
}
```

### `POST /api/news/generate`

Generate synthetic news articles using LLM.

**Request:**
```json
{
  "seed_word": "climate change",
  "count": 3
}
```

**Response:**
```json
{
  "articles": [
    {
      "headline": "Global Climate Summit Reaches Historic Agreement",
      "description": "World leaders gathered...",
      "url": null,
      "published_date": "2024-01-15T10:00:00Z",
      "publisher": "LLM Generated",
      "source_type": "generated"
    }
  ],
  "analytics": {...}
}
```

**Requirements:** Ollama must be running with `llama3.1` model.

---

## Topic Extraction

### `POST /api/extract-topics`

Extract topics dynamically from text using NLP techniques.

**Request:**
```json
{
  "text": "[0:00] Alice: Let's discuss the marketing budget...\n[0:30] Bob: I think we need more for digital advertising..."
}
```

**Response:**
```json
{
  "topics": [
    {
      "name": "marketing budget",
      "keywords": ["marketing", "budget", "spending", "allocation"],
      "score": 8.5,
      "normalized_score": 1.0,
      "sources": ["noun_phrases", "tfidf"]
    },
    {
      "name": "digital advertising",
      "keywords": ["digital", "advertising", "online", "campaigns"],
      "score": 6.2,
      "normalized_score": 0.73,
      "sources": ["noun_phrases", "collocations"]
    }
  ],
  "dynamic_extraction": true,
  "topic_count": 2
}
```

**Extraction Methods:**
- **TF-IDF:** Term frequency-inverse document frequency scoring
- **Named Entity Recognition (NER):** Identifies people, organizations, locations
- **Noun Phrase Extraction:** Extracts meaningful noun phrases
- **Collocation Detection:** Finds words that frequently appear together

---

## Visualization Charts

All visualization endpoints return base64-encoded PNG images.

### `POST /api/visualize/word-cloud`

Generate a word cloud from text.

**Request:**
```json
{
  "words": ["hello", "world", "hello", "python", "world", "world"],
  "width": 800,
  "height": 400,
  "background_color": "#1a1a2e"
}
```

**Response:**
```json
{
  "plot_type": "word_cloud",
  "image_base64": "iVBORw0KGgo...",
  "data": {"word_count": 3}
}
```

### `POST /api/visualize/word-frequency`

Generate a horizontal bar chart of word frequencies.

**Request:**
```json
{
  "word_frequency": [
    {"word": "hello", "count": 10},
    {"word": "world", "count": 8}
  ],
  "top_n": 20,
  "title": "Word Frequency"
}
```

### `POST /api/visualize/sentiment`

Generate a sentiment timeline chart.

**Request:**
```json
{
  "sentiment_data": [
    {"time": 0, "compound": 0.5, "positive": 0.3, "negative": 0.0, "neutral": 0.7},
    {"time": 30, "compound": -0.2, "positive": 0.1, "negative": 0.3, "neutral": 0.6}
  ],
  "title": "Sentiment Analysis"
}
```

### `POST /api/visualize/pos`

Generate a parts of speech pie chart.

**Request:**
```json
{
  "pos_distribution": {
    "noun": 45,
    "verb": 30,
    "adjective": 15,
    "adverb": 10
  },
  "title": "Parts of Speech"
}
```

### `POST /api/visualize/speakers`

Generate a speaker comparison bar chart.

**Request:**
```json
{
  "speaker_analytics": {
    "Alice": {
      "message_count": 10,
      "total_words": 150,
      "average_sentiment": {"compound": 0.3}
    },
    "Bob": {
      "message_count": 8,
      "total_words": 120,
      "average_sentiment": {"compound": -0.1}
    }
  },
  "title": "Speaker Comparison"
}
```

### `GET /api/conversations/{id}/visualizations`

Get all visualizations for a conversation in one request.

**Response:**
```json
{
  "conversation_id": 1,
  "visualizations": {
    "word_cloud": {
      "plot_type": "word_cloud",
      "image_base64": "..."
    },
    "word_frequency": {
      "plot_type": "bar_chart",
      "image_base64": "..."
    },
    "sentiment": {
      "plot_type": "sentiment_scatter",
      "image_base64": "..."
    },
    "pos": {
      "plot_type": "pie_chart",
      "image_base64": "..."
    },
    "speakers": {
      "plot_type": "bar_chart",
      "image_base64": "..."
    }
  }
}
```

**Requirements:** matplotlib and wordcloud must be installed.

---

## Harness

The thread archive that [qmcp][qmcp] keeps, read over its HTTP seam. Two
invariants hold across every route in this section, and both are stated and
argued in `looksatwords/harness.py`:

- **The host is loopback and is not a setting; the port is.** Every call goes
  to `127.0.0.1`, on `LOOKSATWORDS_HARNESS_PORT` or the harness's own default.
  Nothing in the environment moves the host, because a client that could be
  pointed at another machine is how "served to this machine only" stops being
  true. `looksatwords/tests/test_harness.py` is the test that would have to be
  deleted on purpose to change this.
- **Nothing here writes to the archive.** Every call to the harness is a GET.
  `/analyze` stores its result in *this* project's database and tells the
  harness nothing; the archive stays one record with one author.

**An unreachable archive is not an empty one.** Every GET in this section
answers `200` with `reachable: false`, a `reason` and a `fix` naming the
command when nobody answered, rather than an empty list -- a count of zero and
a count nobody took are different claims. The two exceptions are `/analyze`,
which has nothing to store and answers `503`, and `/deltas`, which is the
harness's own payload and answers `503` when nobody answered or `502` when the
harness answered without one.

`reachable` is the first field of every response, because it decides how to
read the rest. Optional fields below are `null` when they do not apply.

### `GET /api/harness/status`

Is the archive answering, and what does it hold.

**Response:**
```json
{
  "reachable": true,
  "base_url": "http://127.0.0.1:3141",
  "reason": null,
  "fix": null,
  "generated_at": "2026-08-20T15:00:00Z",
  "threads_indexed": 3,
  "note": "These figures are the harness's own, as of generated_at, ..."
}
```

`threads_indexed` is `null` when nobody answered, never `0`, which is a real
count the harness is entitled to report. When `reachable` is `false`, `reason`
says what happened and `fix` names the command.

### `GET /api/harness/threads`

The archive's index, largest threads first.

**Query Parameters:**
- `limit` - Maximum rows to return (default: 50)
- `source` - Only threads from one source, as the archive's index names it
- `min_turns` - Only threads with at least this many turns (default: 2)

**Response:**
```json
{
  "reachable": true,
  "reason": null,
  "fix": null,
  "total_indexed": 3,
  "listed": 2,
  "threads": [
    {
      "source": "claude",
      "id": "fixture-seam-0001",
      "title": "How the panel reads the thread archive",
      "turns": 16,
      "address": "quaternionmedia/qmcp/delta/thread-fixture-seam-0001",
      "last_seen": "2026-08-20T15:00:00Z"
    }
  ]
}
```

`listed` and `total_indexed` are both returned and differ whenever a filter or
the limit bites; the length of `threads` is not the size of the archive.

### `POST /api/harness/threads/{source}/{thread_id}/analyze`

Pull one thread off the archive, convert it to the one-line-per-turn transcript
the analysis reads, analyse it, and store the result here. The harness is told
nothing.

**Query Parameters:**
- `limit` - Prose-carrying turns to keep (default: 400). Counts turns with text,
  not raw turns, because most turns in an assistant archive are tool calls with
  none.

**Response:** everything `POST /api/conversations/analyze-with-analytics`
returns, plus:
```json
{
  "conversation_id": 1,
  "title": "[harness] How the panel reads the thread archive",
  "...": "...",
  "conversion": {
    "turns_total": 16,
    "turns_with_text": 13,
    "turns_used": 13,
    "turns_without_text": 3,
    "truncated": false,
    "limit": 60,
    "partial_at_source": false,
    "whitespace_collapsed": true
  },
  "text": "Operator: We need to decide ...\nAssistant: The obvious move ..."
}
```

`conversion` is what reading the thread cost, and it is not decoration: turn
text is collapsed to one line and long threads are cut at `limit`, and both are
invisible in the numbers above it. `text` is exactly what was analysed.

**Status codes:** `409` when the archive answered and does not hold the thread
its index lists (the harness disagreeing with itself; nothing on this side can
repair it), `503` when nobody answered, `422` when the thread has turns and no
readable text in any of them.

### `GET /api/harness/threads/{source}/{thread_id}/deltas`

What the harness says this thread settled -- its own payload, rendered rather
than recomputed, so that there is one record with one author.

**Response:** the harness's `GET /v1/threads/{source}/{id}/deltas` body,
passed through. **Status codes:** `503` when nobody answered, `502` when the
harness answered and produced no deltas.

### `GET /api/harness/threads/{source}/{thread_id}/topics`

This project's reading of one archived thread, shaped as a document a graph can
draw: for each topic, its label, the spans during which it was live, who carried
it, and whether it was dropped or returned to. Built from the analysis
`/analyze` stored and **never recomputed** -- a GET here analyses nothing and
writes nothing. `looksatwords/app/topics_document.py` carries the shaping.

**Response, analysed:**
```json
{
  "source": "claude",
  "thread_id": "fixture-seam-0001",
  "harness": {
    "reachable": true,
    "base_url": "http://127.0.0.1:3141",
    "reason": null,
    "fix": null,
    "indexed": true,
    "title": "How the panel reads the thread archive",
    "address": "quaternionmedia/qmcp/delta/thread-fixture-seam-0001",
    "turns": 16
  },
  "analysed": true,
  "reason": null,
  "fix": null,
  "conversation_id": 1,
  "title": "[harness] How the panel reads the thread archive",
  "analysed_at": "2026-09-20T17:26:15",
  "total_duration": 360.0,
  "beat": 30.0,
  "rest_gap": 75.0,
  "speakers": {
    "Operator": {"color": "#ff6b6b", "index": 0, "contributions": 7},
    "Assistant": {"color": "#00d4ff", "index": 1, "contributions": 6}
  },
  "topics": [
    {
      "label": "Panel",
      "color": "#00d4ff",
      "mentions": 7,
      "speakers": {"Operator": 5, "Assistant": 2},
      "carried_by": "Operator",
      "spans": [
        {"start": 0.0, "end": 180.0, "mentions": 4, "speakers": ["Operator"]},
        {"start": 270.0, "end": 330.0, "mentions": 3, "speakers": ["Assistant", "Operator"]}
      ],
      "rests": 1,
      "dropped": true,
      "returned_to": true
    }
  ],
  "tangents": [
    {
      "start": 120.0,
      "end": 180.0,
      "type": "resolved",
      "topics": ["environment"],
      "start_text": "Operator: That is a precondition we can declare, though. Side note - what port?",
      "resolution_text": "Operator: Back to the seam - so it is HTTP plus a schema, and nothing imports anything."
    }
  ]
}
```

Two answers, kept apart. `harness` is what the archive said about the thread
just now -- `indexed` is `null` when nobody answered, never `false`, which is
the archive's own claim. Everything from `analysed` on is this project's stored
reading, and it is served whether or not the harness is up.

- `spans` are runs of mentions separated by silence. A gap is a rest when it is
  longer than `rest_gap`, which is the conversation's own `beat` -- its
  smallest step between two mentions of one topic -- times the constant the
  front end's `renderer.js` draws rests with. The two copies of that constant
  are held equal by `looksatwords/tests/test_harness_topics.py`, so the
  document and the picture cut a topic at the same silence.
- `rests` is `len(spans) - 1`. `returned_to` is whether there was a rest and
  the topic came back after it. `dropped` is whether the topic fell silent for
  a rest's length at any point, including after its last mention and before
  the conversation ended.
- `carried_by` is the speaker with the most mentions; a tie goes to whoever
  raised it first. `speakers` on a topic counts mentions per speaker; on the
  document it is the analysis's own speaker table.
- The time axis is the analysis's: a transcript with `[m:ss]` stamps keeps
  them, and a thread read off the archive has none, so there the axis is the
  prose-turn index at the parser's spacing.
- `tangents` are the digressions the analysis found, with `type` one of
  `resolved`, `unresolved` or `orphaned`.

**Response, not analysed here:** `200`, with `analysed: false`, `reason`, and
`fix` naming the `/analyze` call that would produce a reading. `topics` and
`tangents` are empty. A reading stored before this route existed carries no
address and reads as not analysed; the remedy is the same call.

```json
{
  "source": "chatgpt",
  "thread_id": "fixture-ports-0002",
  "harness": {"reachable": true, "indexed": true, "...": "..."},
  "analysed": false,
  "reason": "chatgpt/fixture-ports-0002 has not been analysed here.",
  "fix": "POST /api/harness/threads/chatgpt/fixture-ports-0002/analyze reads it off the archive and stores the reading; then ask again.",
  "topics": [],
  "tangents": []
}
```

**Response, nobody answered:** `200`, with `harness.reachable: false`, its
`reason` and `fix`, and `harness.indexed: null`; the `analysed` half is
answered from the local store as above.

### `GET /api/harness/neighbours`

The sibling services -- dossier and the code maps -- and whether either
answered just now. A link, not an integration: this reports reachability and
nothing else, and invents nothing about what a service would have said.

**Response:**
```json
{
  "neighbours": [
    {
      "name": "dossier",
      "url": "http://127.0.0.1:1618",
      "what": "carries a delta through brainstorm to complete",
      "reachable": false,
      "reason": "Nobody answered at http://127.0.0.1:1618: ConnectError.",
      "fix": "Start it with `uv run dossier serve` in the dossier clone."
    },
    {
      "name": "codecarto",
      "url": "http://127.0.0.1:2718",
      "what": "maps source code as graphs; the other half of the border",
      "reachable": true,
      "status": 200
    }
  ]
}
```

`reason` and `fix` are present only when `reachable` is `false`; `status` only
when it is `true`.

[qmcp]: https://github.com/quaternionmedia/qmcp
