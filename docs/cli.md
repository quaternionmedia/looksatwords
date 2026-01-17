# CLI Reference

All commands use the format: `uv run looksatwords <command>`

## Quick Reference

| Command | Description |
|---------|-------------|
| `serve` | Start server and open browser |
| `serve --no-open` | Start server without browser |
| `gather` | Extract conversations from text |
| `analyze` | Analyze conversations |
| `visualize` | Generate visualization |
| `run` | Full pipeline (gather → analyze → visualize) |
| `doctor` | Check environment health |
| `clean` | Remove output files |
| `version` | Show version |

---

## Server Commands

### `serve`

Start the web server and frontend.

```bash
uv run looksatwords serve              # Port 8000, opens browser
uv run looksatwords serve --no-open    # Don't open browser
uv run looksatwords serve --port 3000  # Custom port
```

**Options:**
- `--port` - Server port (default: 8000)
- `--no-open` - Don't open browser automatically

---

## Pipeline Commands

### `run`

Execute the full analysis pipeline.

```bash
uv run looksatwords run -i input.txt           # From file
uv run looksatwords run -t "conversation text" # From string
```

**Options:**
- `-i, --input` - Input file path
- `-t, --text` - Input text string (alternative to file)

### `gather`

Extract conversations from raw text.

```bash
uv run looksatwords gather -i input.txt
```

### `analyze`

Perform linguistic analysis on conversations.

```bash
uv run looksatwords analyze -i data.json
```

### `visualize`

Generate HTML visualization.

```bash
uv run looksatwords visualize -i analyzed.json
```

---

## Utility Commands

### `doctor`

Check environment health and configuration.

```bash
uv run looksatwords doctor
```

Checks:
- Python version
- Database connectivity
- NLTK data availability
- Package dependencies

### `clean`

Remove generated output files.

```bash
uv run looksatwords clean
```

### `version`

Display version information.

```bash
uv run looksatwords version
```

---

## Input/Output

### Input Formats

The pipeline accepts:
- Plain text files
- JSON files (from previous gather step)
- Direct text via `--text` flag

### Output Location

Generated files go to `output/<timestamp>/`:
- `gathered.json` - Extracted conversations
- `analyzed.json` - Analysis results  
- `report.html` - Visualization

---

## Examples

### Full Analysis from File

```bash
uv run looksatwords run -i conversation.txt
```

### Development Server

```bash
uv run looksatwords serve --no-open
# Server runs at http://localhost:8000
```

### Check Everything Works

```bash
uv run looksatwords doctor
uv run looksatwords run -t "Alice: Hello\nBob: Hi there!"
```
