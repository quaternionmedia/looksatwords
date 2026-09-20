"""The topics document, against the stub archive and without a socket.

`GET /api/harness/threads/{source}/{thread_id}/topics` is a read of this
project's stored reading of one archived thread, shaped for a graph. These pin
the three answers it can give -- analysed, not analysed here, and nobody
answered -- and that the middle one writes nothing.

THE STUB IS THE FIXTURE, ANSWERED IN-PROCESS. `fixtures/stub_harness.answer`
is the same route logic the screenshot recorder serves over a socket; here it
is reached by replacing `httpx.get` inside `looksatwords.harness`, so no port
is bound and a busy machine cannot make these fail. "Harness down" is that
same function raising what httpx raises when nobody is listening.

MUTATED ON 2026-09-20 AND SEEN RED SEVEN WAYS. The analyse route not recording
the address read as never analysed; a 503 on an unreachable harness failed the
callers'-shape test; ordering readings oldest-first failed the newest-wins test;
`REST_BEATS` at 3.0 failed against the renderer's 2.5; `<` for `<=` split a gap
of exactly one rest; dropping the trailing-silence clause made a topic that fell
silent read as never dropped; and a GET that stored a row on a miss was caught
by the list of conversations growing. Restored, all pass.
"""

import pathlib
import re

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from looksatwords import harness
from looksatwords.app import topics_document
from looksatwords.app.database import get_session
from looksatwords.app.main import app
from looksatwords.app.models import Conversation
from looksatwords.tests.fixtures import stub_harness

ANALYSED = ("claude", "fixture-seam-0001")
UNTOUCHED = ("chatgpt", "fixture-ports-0002")
RENDERER = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "js" / "renderer.js"


# ==================== Fixtures ====================


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    app.dependency_overrides[get_session] = lambda: session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def stub(monkeypatch):
    """The fixture archive answering every GET `looksatwords.harness` makes."""
    archive = stub_harness.load()

    def fake_get(url, timeout=None, **_):
        path = "/" + url.split("://", 1)[1].split("/", 1)[1]
        code, payload = stub_harness.answer(archive, path)
        return httpx.Response(code, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(harness.httpx, "get", fake_get)
    return archive


@pytest.fixture
def down(monkeypatch):
    """Nobody listening: what httpx raises on a refused connection."""

    def refused(url, timeout=None, **_):
        raise httpx.ConnectError("refused", request=httpx.Request("GET", url))

    monkeypatch.setattr(harness.httpx, "get", refused)


def _topics(client, source, thread_id):
    r = client.get(f"/api/harness/threads/{source}/{thread_id}/topics")
    assert r.status_code == 200, r.text
    return r.json()


# ==================== The three answers ====================


def test_an_analysed_thread_is_a_drawable_document(client, stub):
    source, thread_id = ANALYSED
    analysed = client.post(f"/api/harness/threads/{source}/{thread_id}/analyze?limit=60")
    assert analysed.status_code == 200, analysed.text

    doc = _topics(client, source, thread_id)

    # The address, in both of its forms: the URL's and the archive's own.
    assert (doc["source"], doc["thread_id"]) == ANALYSED
    row = next(t for t in stub["threads"] if t["id"] == thread_id)
    assert doc["harness"]["reachable"] is True
    assert doc["harness"]["indexed"] is True
    assert doc["harness"]["address"] == row["address"]
    assert doc["harness"]["title"] == row["title"]

    assert doc["analysed"] is True
    assert doc["conversation_id"] == analysed.json()["conversation_id"]
    assert doc["reason"] is None and doc["fix"] is None
    assert doc["topics"], "an analysed thread with no topics is a blank picture"

    # Every lane is internally consistent with the rule that cut it.
    assert doc["rest_gap"] == doc["beat"] * topics_document.REST_BEATS
    for lane in doc["topics"]:
        assert lane["label"]
        assert lane["spans"], lane
        assert lane["rests"] == len(lane["spans"]) - 1
        assert lane["returned_to"] is (lane["rests"] > 0)
        assert lane["carried_by"] in lane["speakers"]
        assert sum(lane["speakers"].values()) == lane["mentions"]
        assert sum(s["mentions"] for s in lane["spans"]) == lane["mentions"]
        for span in lane["spans"]:
            assert span["start"] <= span["end"] <= doc["total_duration"]
            assert set(span["speakers"]) <= set(lane["speakers"])
        for earlier, later in zip(lane["spans"], lane["spans"][1:]):
            assert later["start"] - earlier["end"] > doc["rest_gap"], (
                "two spans closer than a rest should have been one span"
            )

    # The fixture is written to hold a topic that is dropped and picked up
    # again (fixtures/make_harness_fixture.py). If none reads that way, either
    # the fixture or the rule changed, and the picture would show it too.
    assert any(lane["returned_to"] for lane in doc["topics"])
    # Speakers are the analysis's names for roles, carried through.
    assert set(doc["speakers"]) == {"Operator", "Assistant"}


def test_a_thread_not_analysed_here_is_said_so_and_nothing_is_written(client, stub):
    source, thread_id = UNTOUCHED
    before = client.get("/api/conversations").json()

    doc = _topics(client, source, thread_id)

    assert doc["analysed"] is False
    assert doc["topics"] == []
    assert thread_id in doc["reason"]
    # The remedy is the call, not a hop towards it.
    assert f"POST /api/harness/threads/{source}/{thread_id}/analyze" in doc["fix"]
    # And the archive's half is still answered: it holds the thread.
    assert doc["harness"]["reachable"] is True
    assert doc["harness"]["indexed"] is True

    # A GET THAT WRITES IS A SURPRISE. Nothing was stored by asking.
    assert client.get("/api/conversations").json() == before == []


def test_a_thread_the_archive_does_not_index_says_which_side_is_missing(client, stub):
    doc = _topics(client, "claude", "nobody-has-this")
    assert doc["harness"]["reachable"] is True
    assert doc["harness"]["indexed"] is False
    assert doc["harness"]["address"] is None
    assert doc["analysed"] is False


def test_harness_down_is_answered_the_way_the_other_callers_answer_it(client, down):
    """`reachable` False with the reason and the fix, at 200, like `/api/harness/status`."""
    doc = _topics(client, *ANALYSED)

    assert doc["harness"]["reachable"] is False
    assert doc["harness"]["reason"]
    assert "qmcp" in doc["harness"]["fix"]
    assert doc["harness"]["indexed"] is None, "nobody answered, so 'not indexed' is not known"
    assert doc["analysed"] is False

    # The same shape `/api/harness/status` gives for the same condition.
    status = client.get("/api/harness/status").json()
    assert status["reachable"] is False
    assert status["fix"] == doc["harness"]["fix"]


def test_the_reading_survives_the_harness_going_away(client, stub, monkeypatch):
    """What the archive said and what this project read are two answers.

    Losing one does not lose the other: the stored reading is served under a
    `harness` block that says nobody answered.
    """
    source, thread_id = ANALYSED
    first = client.post(f"/api/harness/threads/{source}/{thread_id}/analyze?limit=60")
    assert first.status_code == 200, first.text

    def refused(url, timeout=None, **_):
        raise httpx.ConnectError("refused", request=httpx.Request("GET", url))

    monkeypatch.setattr(harness.httpx, "get", refused)
    doc = _topics(client, source, thread_id)
    assert doc["harness"]["reachable"] is False
    assert doc["analysed"] is True
    assert doc["conversation_id"] == first.json()["conversation_id"]
    assert doc["topics"]


def test_the_newest_reading_wins(client, stub):
    source, thread_id = ANALYSED
    client.post(f"/api/harness/threads/{source}/{thread_id}/analyze?limit=60")
    second = client.post(f"/api/harness/threads/{source}/{thread_id}/analyze?limit=4")
    doc = _topics(client, source, thread_id)
    assert doc["conversation_id"] == second.json()["conversation_id"]


def test_a_pasted_conversation_carries_no_address(client, session):
    """Only the harness route has an address to store; the box does not."""
    r = client.post("/api/conversations/analyze-with-analytics",
                    json={"text": "Alice: the budget\nBob: the budget again", "title": "typed"})
    assert r.status_code == 200
    row = session.exec(select(Conversation)).one()
    assert row.harness_source is None and row.harness_thread_id is None


# ==================== The shaping, on its own ====================


def _points(*times, speaker="Operator"):
    return [{"time": float(t), "speaker": speaker} for t in times]


def test_a_gap_longer_than_a_rest_splits_a_lane():
    runs = topics_document.spans(_points(0, 30, 60, 300, 330), rest_gap=75.0)
    assert [(r["start"], r["end"], r["mentions"]) for r in runs] == [
        (0.0, 60.0, 3), (300.0, 330.0, 2),
    ]


def test_a_gap_of_exactly_a_rest_is_not_yet_a_rest():
    runs = topics_document.spans(_points(0, 75), rest_gap=75.0)
    assert len(runs) == 1


def test_dropped_and_returned_to_are_different_facts():
    gap = 75.0
    came_back = topics_document.lane({"name": "a", "points": _points(0, 300)}, gap, 300.0)
    assert came_back["dropped"] is True and came_back["returned_to"] is True
    assert came_back["rests"] == 1

    fell_silent = topics_document.lane({"name": "b", "points": _points(0, 30)}, gap, 300.0)
    assert fell_silent["dropped"] is True and fell_silent["returned_to"] is False
    assert fell_silent["rests"] == 0

    to_the_end = topics_document.lane({"name": "c", "points": _points(240, 270, 300)}, gap, 300.0)
    assert to_the_end["dropped"] is False and to_the_end["returned_to"] is False


def test_carried_by_is_who_mentioned_it_most_with_ties_to_the_first():
    points = _points(0, 30, speaker="Assistant") + _points(60, 90, 120, speaker="Operator")
    assert topics_document.lane({"name": "a", "points": points}, 75.0, 120.0)["carried_by"] == "Operator"
    tied = _points(0, speaker="Assistant") + _points(30, speaker="Operator")
    assert topics_document.lane({"name": "a", "points": tied}, 75.0, 30.0)["carried_by"] == "Assistant"


def test_the_beat_is_the_conversations_own_smallest_step():
    threads = [{"points": _points(0, 90, 100)}, {"points": _points(5, 500)}]
    assert topics_document.beat(threads) == 10.0
    assert topics_document.beat([{"points": _points(0)}]) == topics_document.FALLBACK_BEAT


# ==================== The copied constant ====================


def test_the_rest_rule_matches_the_renderer():
    """`REST_BEATS` and `FALLBACK_BEAT` are copies of two numbers in renderer.js.

    The document and the picture must cut a topic at the same silence, or a
    reader comparing the two sees a rest in one and a line in the other. The
    JavaScript cannot be imported, so its line is read.
    """
    text = RENDERER.read_text(encoding="utf-8")
    m = re.search(r"restGap\s*=\s*\(this\.messageSlot\s*\|\|\s*(\d+)\)\s*\*\s*([\d.]+)", text)
    assert m, "renderer.js no longer computes restGap the way this test reads it"
    assert float(m.group(2)) == topics_document.REST_BEATS, (
        f"renderer.js rests after {m.group(2)} beats and the document after "
        f"{topics_document.REST_BEATS}; the two would disagree about every gap between"
    )
    assert float(m.group(1)) == topics_document.FALLBACK_BEAT
