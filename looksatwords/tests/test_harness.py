"""The harness seam, and the parts of it that are claims about somebody else.

None of these start a server. What they pin is the contract this project
asserts about the archive it reads: where it is, what an unreachable answer is
allowed to look like, and that a conversion says what it cost.
"""

import pathlib
import re

import pytest

from looksatwords import harness


# ==================== The copied constant ====================

def _qmcp_config() -> pathlib.Path | None:
    """qmcp's own config, if a sibling clone is on this machine."""
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "qmcp" / "qmcp" / "config.py"
        if candidate.exists():
            return candidate
    return None


def test_the_port_matches_the_harness_that_serves_it():
    """`DEFAULT_PORT` is a second copy of a constant this repository does not own.

    The two repositories cannot import each other: giving this project a
    dependency on qmcp would put the harness's code in this install for the
    sake of an integer. So the constant is copied, and this is the only thing
    that keeps a copy true.

    A SKIP HERE IS NOT A PASS. Without the sibling clone nobody can check, and
    the skip says so rather than letting the suite imply the two agree.
    """
    config = _qmcp_config()
    if config is None:
        pytest.skip(
            "No sibling qmcp clone on this machine, so the port qmcp actually "
            "serves on could not be read. This test did not run; it did not pass."
        )

    text = config.read_text(encoding="utf-8")
    m = re.search(r"port:\s*int\s*=\s*(\d+)", text)
    assert m, f"could not find a port default in {config}"
    assert int(m.group(1)) == harness.DEFAULT_PORT, (
        f"{config} serves on {m.group(1)} and this project looks for "
        f"{harness.DEFAULT_PORT}. The panel would report the harness missing "
        "while it was answering on another port -- accurate about the address "
        "it tried and useless about the problem."
    )


# ==================== The half that is not a setting ====================

def test_the_host_does_not_move(monkeypatch):
    """The port is a setting and the host is not, and that split is the control.

    A client that could be pointed at another machine is how "served to this
    machine only" stops being true. Nothing in the environment moves the host.
    """
    monkeypatch.setenv("LOOKSATWORDS_HARNESS_PORT", "9999")
    assert harness.base_url() == "http://127.0.0.1:9999"

    # There is deliberately no env var for the host. If one is ever added, this
    # is the test that should have to be deleted on purpose.
    for name in ("LOOKSATWORDS_HARNESS_HOST", "LOOKSATWORDS_HOST"):
        monkeypatch.setenv(name, "10.0.0.5")
    assert "127.0.0.1" in harness.base_url()
    assert "10.0.0.5" not in harness.base_url()


# ==================== Zero is not unknown ====================

def test_unreachable_is_not_an_empty_archive():
    """`reachable` is the field that separates two very different claims."""
    a = harness.Archive.unreachable("Nobody answered.")
    assert a.reachable is False
    assert a.reason
    # The remedy is the fix, not a hop toward it: it names a command.
    assert "qmcp" in a.fix

    empty = harness.Archive(reachable=True, totals={"threads": 0})
    assert empty.reachable is True
    assert empty.threads == ()

    # Both hold zero threads. Only `reachable` tells them apart, which is why
    # every caller is required to read it before the rows.
    assert len(a.threads) == len(empty.threads) == 0
    assert a.reachable != empty.reachable


def test_a_fetch_distinguishes_answered_from_unreachable():
    """Three outcomes, not two."""
    got = harness.Fetch(thread=harness.Thread("chatgpt", "x", "t", ()), answered=True)
    missing = harness.Fetch(answered=True, reason="not held", fix="reindex")
    silent = harness.Fetch(reason="nobody answered", fix="start it")

    assert got.thread is not None
    assert missing.thread is None and missing.answered is True
    assert silent.thread is None and silent.answered is False


# ==================== The conversion says what it cost ====================

def _thread(turns):
    return harness.Thread(source="claude-code", id="x", title="t", turns=tuple(turns))


def test_conversion_counts_are_three_different_facts():
    """How long the thread is, how much is prose, and how much was used.

    Most turns in this archive are tool calls with no text. Capping raw turns
    rather than prose turns takes the first N of mostly-empty entries: measured
    against the live harness, a cap of 300 raw turns on a 4,715-turn thread
    emitted 18 lines.
    """
    turns = []
    for i in range(10):
        turns.append({"role": "assistant", "text": ""})       # a tool call
        turns.append({"role": "user", "text": f"message {i}"})

    text, report = harness.as_conversation(_thread(turns), limit=4)

    assert report["turns_total"] == 20
    assert report["turns_with_text"] == 10
    assert report["turns_used"] == 4
    assert report["turns_without_text"] == 10
    assert report["truncated"] is True
    assert len(text.splitlines()) == 4


def test_no_truncation_is_reported_as_no_truncation():
    turns = [{"role": "user", "text": "one"}, {"role": "assistant", "text": "two"}]
    _, report = harness.as_conversation(_thread(turns), limit=50)
    assert report["truncated"] is False
    assert report["turns_used"] == report["turns_with_text"] == 2


def test_multi_line_turns_collapse_to_one_line_each():
    """The parser is line-oriented, so one turn must become one line.

    Left alone, an assistant turn with newlines becomes many messages with a
    speaker of `Unknown`, and the thread graph is drawn over nothing.
    """
    turns = [{"role": "assistant", "text": "first line\nsecond line\n\n    third"}]
    text, report = harness.as_conversation(_thread(turns))
    assert len(text.splitlines()) == 1
    assert text == "Assistant: first line second line third"
    assert report["whitespace_collapsed"] is True


def test_partial_at_source_is_carried_not_recomputed():
    """Only the harness knows whether it gave us the whole thread."""
    t = harness.Thread(source="claude", id="x", title="t",
                       turns=({"role": "user", "text": "hi"},), partial=True)
    _, report = harness.as_conversation(t)
    assert report["partial_at_source"] is True
