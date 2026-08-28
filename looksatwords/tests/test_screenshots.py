"""The pictures in `docs/pics/`, recorded by running the thing.

P12, "show it by running it": what prose cannot hold is emitted by the test that
exercises the behaviour, and **recorded rather than compared**. Nothing here
diffs a PNG against a committed one. A byte comparison of a rendered page fails
on a font, a scrollbar and a machine, and a test that fails for those reasons
gets muted -- which is worse than not having it.

WHAT IS ASSERTED INSTEAD. That the page had something in it before the shutter
opened: the threads drew, their computed opacity is above zero, the panel holds
the numbers it should. A blank frame is the failure this guards against, and it
has shipped in this org before -- a narrative recording whose first frame was
empty, committed and reviewed by people who read the surrounding prose.

WHY NOTHING HERE TOUCHES THE LIVE ARCHIVE OR THE REAL DATABASE. Both move. The
harness on the machine this was written on gained 1,573 turns on one thread
during a single session, so a picture taken from it would churn on every
regeneration and the diff would carry no information. This starts a stub harness
serving `fixtures/harness_archive.json` and an app pointed at a scratch
database, so a regeneration on any machine produces the same page.

REGENERATION RIDES THE ORDINARY COMMAND:

    uv run looksatwords screenshots

which is `pytest -m screenshots`. Run it before a pull request that changes the
UI, and commit what changes.
"""

import json
import os
import pathlib
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.screenshots]

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
PICS = REPO / "docs" / "pics"
FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "harness_archive.json"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ==================== A harness that does not move ====================


def _make_handler(archive):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # the test's output is the report, not an access log

        def _send(self, code, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/v1/threads":
                index = {k: v for k, v in archive.items() if not k.startswith("_")}
                return self._send(200, index)

            parts = path.strip("/").split("/")
            # /v1/threads/{source}/{id}[/deltas]
            if len(parts) >= 4 and parts[0] == "v1" and parts[1] == "threads":
                key = f"{parts[2]}/{parts[3]}"
                if len(parts) == 5 and parts[4] == "deltas":
                    d = archive["_deltas"].get(key)
                    return self._send(200, d) if d else self._send(404, {"detail": "no deltas"})
                body = archive["_bodies"].get(key)
                # The fixture deliberately indexes one thread it cannot produce,
                # so the run exercises the index/archive disagreement without
                # anything having to be broken.
                return self._send(200, body) if body else self._send(404, {"detail": "not held"})

            self._send(404, {"detail": "not found"})

    return Handler


@pytest.fixture(scope="module")
def stub_harness():
    archive = json.loads(FIXTURE.read_text(encoding="utf-8"))
    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _make_handler(archive))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        server.shutdown()


@pytest.fixture(scope="module")
def app_server(stub_harness, tmp_path_factory):
    """This project, serving against the stub and a scratch database."""
    port = _free_port()
    db = tmp_path_factory.mktemp("screenshots") / "screenshots.db"

    env = dict(os.environ)
    env["LOOKSATWORDS_DB"] = str(db)
    env["LOOKSATWORDS_HARNESS_PORT"] = str(stub_harness)
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "looksatwords.app.main:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=str(REPO), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )

    import httpx

    base = f"http://127.0.0.1:{port}"
    for _ in range(120):
        if proc.poll() is not None:
            raise RuntimeError(f"the app exited before serving:\n{proc.stdout.read()}")
        try:
            if httpx.get(base + "/health", timeout=1.0).status_code == 200:
                break
        except Exception:
            time.sleep(0.25)
    else:
        proc.terminate()
        raise RuntimeError("the app never answered on /health")

    try:
        yield base
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="module")
def page(app_server):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Playwright is not installed. Run: uv add playwright")

    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
    except Exception as e:
        pytest.skip(
            "Could not launch chromium. Run: uv run playwright install chromium. "
            f"Error: {e}"
        )

    pg = browser.new_page(viewport={"width": 1600, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(app_server, wait_until="networkidle")

    # A page that threw before anything rendered would still screenshot, and the
    # picture would look like a design decision.
    assert not errors, f"the page raised before any picture was taken: {errors}"

    try:
        yield pg
    finally:
        browser.close()
        pw.stop()


def _shoot(page, name):
    """Write one picture, after its content has been asserted by the caller."""
    PICS.mkdir(parents=True, exist_ok=True)
    path = PICS / name
    page.screenshot(path=str(path), full_page=True)
    assert path.stat().st_size > 10_000, (
        f"{name} is {path.stat().st_size} bytes, which is not a rendered page"
    )
    print(f"recorded docs/pics/{name} ({path.stat().st_size // 1024} KB)")


# ==================== The pictures ====================


def test_records_the_harness_archive(page):
    """The front door: what the harness holds, before anything is analysed."""
    page.click(".analytics-tab[data-tab='harness']")
    page.wait_for_selector("[data-harness-analyze]", state="attached", timeout=30000)
    page.wait_for_timeout(800)

    # ALL THREE, INCLUDING THE ONE THE ARCHIVE CANNOT PRODUCE. The panel lists
    # what the index says, because that is what the index says; the archive
    # disagreeing with it is not visible until somebody asks for the thread.
    # Filtering the row out here would hide a fact that belongs to the harness.
    rows = page.eval_on_selector_all("[data-harness-analyze]", "els => els.length")
    assert rows == 3, f"expected the fixture's three indexed threads, got {rows}"

    panel = page.inner_text("#analyticsPanel")
    assert "Harness thread archive" in panel
    assert "3" in panel, "the indexed total is missing from the status card"

    _shoot(page, "harness-archive.png")


def test_records_an_analysed_thread(page):
    """A thread pulled off the archive, drawn, with the conversion report."""
    page.select_option("#harnessLimit", "60")
    page.eval_on_selector_all(
        "[data-harness-analyze]",
        "els => els.find(e => e.dataset.source === 'claude').click()",
    )
    page.wait_for_selector("#visualization svg path.thread-path", timeout=30000)
    page.wait_for_timeout(5000)

    # ASSERT THE PICTURE HAS SOMETHING IN IT. Paths in the DOM at opacity 0 is
    # the exact state this project shipped in until 2026-08-26: drawn, correct
    # and invisible. A screenshot of that is a screenshot of nothing.
    opacities = page.eval_on_selector_all(
        "#visualization svg path.thread-path",
        "els => els.map(e => parseFloat(getComputedStyle(e).opacity))",
    )
    assert opacities, "no thread paths were drawn"
    assert all(o > 0.01 for o in opacities), (
        f"thread paths are in the DOM and invisible: {opacities}"
    )

    detail = page.inner_text("#harnessDetail")
    assert "turns in thread" in detail
    assert "carrying prose" in detail, "the conversion report is not on screen"

    # The fixture holds three turns with no prose, so the report has a true
    # thing to say about tool calls. If that stops being true the picture would
    # silently lose the sentence.
    assert "carried no prose" in detail

    # BRING THE REPORT INTO FRAME. It was in the DOM and below the fold, so the
    # picture showed the graph and not the sentence saying what the graph left
    # out -- which is the half a reader most needs to see.
    page.eval_on_selector("#harnessDetail", "e => e.scrollIntoView({block: 'center'})")
    page.wait_for_timeout(600)

    _shoot(page, "harness-analysed.png")


def test_records_what_the_harness_says_a_thread_settled(page):
    """The deltas view: qmcp's own answer, rendered rather than recomputed."""
    page.eval_on_selector_all(
        "[data-harness-deltas]",
        "els => els.find(e => e.dataset.source === 'claude').click()",
    )
    page.wait_for_timeout(2500)

    detail = page.inner_text("#harnessDetail")
    assert "What the harness says this settled" in detail
    assert "quaternionmedia/qmcp/delta/thread-fixture-seam-0001" in detail, (
        "the delta's address is missing, so the picture would show an empty card"
    )

    _shoot(page, "harness-deltas.png")


def test_records_the_index_disagreeing_with_the_archive(page):
    """The failure that is somebody else's, reported as theirs.

    The fixture indexes a thread it does not hold, which is what the live
    harness does for one source. This records what a person sees when they
    click it: the reason, and that nothing on this side can repair it.
    """
    page.click(".analytics-tab[data-tab='harness']")
    page.wait_for_selector("[data-harness-analyze]", state="attached", timeout=30000)
    page.eval_on_selector_all(
        "[data-harness-analyze]",
        "els => els.find(e => e.dataset.source === 'claude-code').click()",
    )
    page.wait_for_timeout(2500)

    detail = page.inner_text("#harnessDetail")
    # THE MESSAGE HAS TO SAY WHOSE PROBLEM IT IS. "Did not produce" reads as a
    # fault in the request. What a person needs is that the archive answered,
    # that it disagrees with its own index, and that nothing here can fix it.
    assert "does not hold" in detail, detail[:200]
    assert "index lists it" in detail, detail[:200]
    assert "Nothing on this side can repair it" in detail, detail[:200]

    _shoot(page, "harness-index-disagreement.png")

    # And the same fact at the API, where the status code carries it: 409 when
    # the archive answered and disagrees, 503 when nobody answered at all.
    import httpx

    base = page.url.rstrip("/")
    r = httpx.post(
        f"{base}/api/harness/threads/claude-code/fixture-absent-0003/analyze",
        timeout=30.0,
    )
    assert r.status_code == 409, (
        f"expected 409 for a thread the archive answered about and does not hold, got {r.status_code}"
    )
    assert "its index lists it" in r.json()["detail"]


def test_records_the_analytics_the_conversation_produced(page):
    """The Analytics tab, filled from the thread that was just analysed."""
    page.click(".analytics-tab[data-tab='analytics']")
    page.wait_for_timeout(1500)

    panel = page.inner_text("#analyticsPanel")
    for label in ("Overview", "Messages", "Words", "Unique Words", "Speakers"):
        assert label in panel, f"Overview is missing {label}"

    # An em dash here means the API omitted a field and the card is honest
    # about it -- true, and not what this picture is meant to show.
    values = page.eval_on_selector_all(
        "#analyticsPanel div", "els => els.map(e => e.textContent.trim())"
    )
    assert not any(v == "—" for v in values), "a field went missing from the analytics"

    _shoot(page, "analytics-panel.png")
