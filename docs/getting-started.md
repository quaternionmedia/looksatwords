# Getting Started

Get looksatwords running in 3 steps.

## Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** - Fast Python package manager

## Installation

### Option 1: Local Development (Recommended)

```bash
git clone https://github.com/quaternionmedia/looksatwords.git
cd looksatwords
uv sync
```

### Option 2: Global Tool

```bash
uv tool install git+https://github.com/quaternionmedia/looksatwords.git
```

## First Run

### Start the Server

```bash
uv run looksatwords serve
```

This will:
1. Start the API server on http://localhost:8000
2. Open your browser automatically
3. Serve the frontend visualization interface

### Try It Out

1. Paste a conversation into the text area (or click **Sample** to load example data)
2. Click **Analyze** to process the conversation
3. Watch the thread visualization appear with the analytics panel

**UI Controls:**
- **Sample** - Load example conversation
- **Generate** - Create AI-generated conversation (requires Ollama)
- **Analyze** - Process and visualize conversation
- **Topics** - Extract topics using NLP (TF-IDF, NER, noun phrases)
- **Reset** - Clear visualization
- **Load** - Load saved conversation from database
- **Export** - Download all conversations as JSON
- **Import** - Upload conversations from JSON backup
- **Collections** - Manage conversation collections for corpus-level analysis
- **News** - Gather real news or generate synthetic articles with LLM
- **Charts** - View word clouds, sentiment charts, and speaker comparisons

### Explore the API

Visit http://localhost:8000/docs for interactive API documentation.

## Database Setup (Optional)

For persistent storage with migrations:

```bash
uv run alembic upgrade head
```

## Required: NLTK Data

Download language models (run once):

```bash
python -m nltk.downloader stopwords punkt vader_lexicon \
  averaged_perceptron_tagger_eng punkt_tab omw-1.4 wordnet
```

Or download everything:

```bash
python -m nltk.downloader all
```

## Optional: Ollama

For AI-powered text generation, install [Ollama](https://ollama.com/download):

```bash
ollama run llama3.1
```

## Optional: GNews

For gathering real news articles, install the gnews package:

```bash
uv pip install gnews
```

## Optional: Visualizations

For generating charts (word clouds, sentiment plots, etc.):

```bash
uv pip install matplotlib wordcloud bokeh
```

## Verify Installation

Check that everything is working:

```bash
uv run looksatwords doctor
```

## Next Steps

- [CLI Reference](cli.md) - Learn all available commands
- [API Reference](api.md) - Explore the REST API
- [Contributing](contributing.md) - Set up for development

---

## Troubleshooting

### "Command not found"

Make sure uv is installed and in your PATH:

```bash
uv --version
```

### "NLTK data missing"

Download the required data:

```bash
python -m nltk.downloader all
```

### "Port already in use"

Use a different port:

```bash
uv run looksatwords serve --port 8001
```

### Tests failing

Check environment and rebuild:

```bash
uv run looksatwords doctor
uv run looksatwords clean
uv sync
```

### Environment completely broken

Start fresh:

```bash
rm -rf .venv
uv sync
```
