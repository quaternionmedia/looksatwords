# CLI Reference

All commands use the format `uv run looksatwords <command>`. Every one of them
takes `--help`, and `--help` is the authority — this page is a map, and
`looksatwords/tests/test_cli_reference.py` fails if the two stop agreeing in
either direction.

## Quick reference

<!-- COMMANDS: every command below must exist, and every command must be below.
     The guard reads this table; do not rename its markers. -->

| Command | What it does |
|---------|--------------|
| `serve` | Start the application server (API + frontend) |
| `run` | Gather, generate, analyze and visualize articles end to end |
| `screenshots` | Re-record the pictures in `docs/pics/` by driving the real UI |
| `test` | Run the test suite, with coverage, parallelism and timeout options |
| `test-api` | Run the API integration tests |
| `test-e2e` | Run the browser tests with playwright |
| `lint` | Run ruff check |
| `format-code` | Format with ruff |
| `install-dev` | uv sync plus the playwright browsers |
| `doctor` | Check environment health and dependencies |
| `clean` | Remove generated files and caches |

<!-- END COMMANDS -->

---

## Running the app

### `serve`

```bash
uv run looksatwords serve                 # 127.0.0.1:1414, opens a browser
uv run looksatwords serve --no-open       # no browser
uv run looksatwords serve -p 8080         # another port
uv run looksatwords serve --reload        # auto-reload while developing
uv run looksatwords serve --host 0.0.0.0  # listen on all interfaces
```

The settings that matter are not flags:

- **`LOOKSATWORDS_PORT`** moves this server off its default. The default is
  the org's allocation for this reader -- the governance corpus gives each
  server on the workstation one port in the SURFACES table of its
  `ci/dashboard.py`, and `looksatwords/tests/test_port.py` reads a sibling
  clone's copy of that table to keep this project's constant true. `--port`
  beats the variable, which beats the allocation; `--help` prints the number.
- **`LOOKSATWORDS_DB`** moves the database. Anything demonstrating the tool
  should set it — without it, demo conversations land in the same file as real
  ones with nothing to tell them apart.
- **`LOOKSATWORDS_HARNESS_PORT`** points at the thread archive, default `3141`.
  **There is no setting for the host.** It is loopback, because a client that
  could be pointed at another machine is how "served to this machine only" stops
  being true.

`LOOKSATWORDS_OLLAMA_MODEL` picks the model for generation, default `llama3.1`.
Its host is loopback for the same reason and is likewise not a setting.

### `run`

The non-interactive pipeline: gather articles, optionally generate more,
analyse, and write visualizations.

```bash
uv run looksatwords run                     # top news, default analysis
uv run looksatwords run -g 10 -f 5          # gather 10, generate 5
uv run looksatwords run -v sentiment        # only the sentiment visual
```

**Options:** `--keywords/-k`, `--table/-t`, `--num_gen/-f`, `--num_gath/-g`,
`--analysis_level/-a`, `--visuals_out/-v`.

---

## Recording what the docs show

### `screenshots`

```bash
uv run looksatwords screenshots
```

Starts this project against a stub harness and a scratch database, drives a real
browser, and writes `docs/pics/`. It needs
`uv run playwright install chromium` and starts its own server, so nothing else
has to be running — and it never touches the live archive or your database.

**Recorded, not compared.** Nothing diffs a PNG. What is asserted is that the
page had something in it before the shutter opened: the thread paths drew with
non-zero computed opacity, and the panel holds its numbers. Run it when the UI
changes and commit what moves.

---

## Tests

### `test`

```bash
uv run looksatwords test              # everything
uv run looksatwords test --cov        # with coverage
uv run looksatwords test --parallel   # across cores
uv run looksatwords test -f test_analyzer.py
```

**Options:** `--cov`, `--html`, `--parallel`, `--timeout`, `--verbose/-v`,
`--file/-f`.

### `test-api` and `test-e2e`

```bash
uv run looksatwords test-api          # API integration tests
uv run looksatwords test-e2e          # browser tests
uv run looksatwords test-e2e --headed # watch them run
```

`test-e2e` needs a chromium from `playwright install` **and a server already
listening** — start one with `serve` in another terminal. Its fixture skips only
when chromium will not launch, and says so; a skip is not a pass.

Markers, if you would rather use pytest directly:

```bash
uv run pytest -m "not e2e"     # the default suite
uv run pytest -m e2e           # browser tests
uv run pytest -m llm           # reaches a live Ollama on loopback
uv run pytest -m screenshots   # records docs/pics/
```

---

## Development

### `lint`, `format-code`, `install-dev`

```bash
uv run looksatwords lint          # ruff check
uv run looksatwords format-code   # ruff format
uv run looksatwords install-dev   # uv sync + playwright browsers
```

### `doctor`

```bash
uv run looksatwords doctor
```

Reports what is installed and what is missing, so a failure later names a cause
rather than a symptom.

### `clean`

```bash
uv run looksatwords clean
```

Removes generated output and caches. It does not touch the database.

---

## Governance gates

Not CLI commands — they run out of the vendored corpus:

```bash
uv run python governance/qm/project-seed/ci/run_workflows_locally.py
```

`reuse-lint`'s install step fails under that runner because this project's
uv-managed venv has no `pip`; the lint itself passes with
`uvx --with charset-normalizer reuse lint`. That line is an environment
difference and not a finding.
