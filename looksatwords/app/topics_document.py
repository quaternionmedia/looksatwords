"""One analysed conversation's topics, shaped as a document a graph can draw.

**READ FROM THE STORED ANALYSIS, NEVER RECOMPUTED.** Everything here is
arithmetic over what `_analyze_and_store` already put in the `conversation`
row: each topic's mentions with their time and speaker, and the tangents with
whether they resolved. Nothing tokenises, scores or extracts. A GET that ran
the analysis again would write a second row for the same thread, and a GET
that writes is a surprise -- so a thread that has not been analysed is
reported as such, with the route that analyses it, rather than analysed here.

**THE REST RULE IS THE RENDERER'S, COPIED.** `frontend/js/renderer.js` draws a
topic as runs of mentions separated by silence, and calls a gap a rest when it
is longer than the conversation's own beat -- its smallest step between two
messages -- times `REST_BEATS`. The spans below are those runs, so the document
and the picture agree about when a topic was live. The two copies cannot import
each other; `tests/test_harness_topics.py` reads the renderer's constant and
fails when the two disagree, and the document carries `beat` and `rest_gap` so
a reader can see the rule that cut it.

TIME, NOT TURNS. The axis is the stored `time` of each mention. A transcript
with `[m:ss]` stamps keeps them; a thread read off the archive has none, and the
parser spaces its lines by a constant, so there the axis is the prose-turn
index scaled. Either way the spans are the ones the picture draws.

WHAT THIS CANNOT DO. Say anything about a conversation this project has not
analysed, or about turns the conversion dropped -- tool calls carry no prose and
never reach the analysis, and a thread cut at the analyse route's `limit` is
described up to that cut. Both facts are in the `conversion` report the
analyse route returned, and neither is stored here.
"""

from __future__ import annotations

from typing import Any

# THE RENDERER'S CONSTANT, COPIED. `renderer.js` has
# `restGap = (this.messageSlot || 30) * 2.5`; the test in
# tests/test_harness_topics.py reads that line and fails when this drifts.
REST_BEATS = 2.5

# What the renderer falls back to when no two mentions are apart, and what the
# parser spaces unstamped lines by. Only reached for a conversation with fewer
# than two distinct mention times, where no gap exists to be a rest.
FALLBACK_BEAT = 30.0


def beat(threads: list[dict[str, Any]]) -> float:
    """The conversation's smallest step between two mentions of one topic."""
    smallest = None
    for thread in threads:
        times = sorted(p["time"] for p in thread.get("points") or ())
        for earlier, later in zip(times, times[1:]):
            gap = later - earlier
            if gap > 0 and (smallest is None or gap < smallest):
                smallest = gap
    return float(smallest) if smallest is not None else FALLBACK_BEAT


def spans(points: list[dict[str, Any]], rest_gap: float) -> list[dict[str, Any]]:
    """Runs of mentions, split wherever the silence between two is a rest."""
    ordered = sorted(points, key=lambda p: p["time"])
    runs: list[list[dict[str, Any]]] = []
    for point in ordered:
        if runs and point["time"] - runs[-1][-1]["time"] <= rest_gap:
            runs[-1].append(point)
        else:
            runs.append([point])

    out = []
    for run in runs:
        speakers: list[str] = []
        for point in run:
            name = point.get("speaker") or "Unknown"
            if name not in speakers:
                speakers.append(name)
        out.append({
            "start": run[0]["time"],
            "end": run[-1]["time"],
            "mentions": len(run),
            "speakers": speakers,
        })
    return out


def lane(thread: dict[str, Any], rest_gap: float, total_duration: float) -> dict[str, Any]:
    """One topic: its label, when it was live, who carried it, and whether it fell silent."""
    points = list(thread.get("points") or ())
    runs = spans(points, rest_gap)

    by_speaker: dict[str, int] = {}
    for point in points:
        name = point.get("speaker") or "Unknown"
        by_speaker[name] = by_speaker.get(name, 0) + 1
    # Ties go to whoever spoke of it first; dict order is first appearance.
    carried_by = max(by_speaker, key=by_speaker.__getitem__) if by_speaker else None

    rests = max(len(runs) - 1, 0)
    # Dropped: silent for a rest's length after some run, whether or not it came
    # back -- including trailing silence up to the end of the conversation,
    # which the picture shows as the bare dashed rule after the last note.
    trailing = (total_duration - runs[-1]["end"]) > rest_gap if runs else False
    return {
        "label": thread.get("name") or "",
        "color": thread.get("color") or "",
        "mentions": len(points),
        "speakers": by_speaker,
        "carried_by": carried_by,
        "spans": runs,
        "rests": rests,
        "dropped": rests > 0 or trailing,
        "returned_to": rests > 0,
    }


def tangent(t: dict[str, Any]) -> dict[str, Any]:
    """One digression as stored, with whether the conversation came back."""
    return {
        "start": t.get("start_time"),
        "end": t.get("end_time"),
        "type": t.get("tangent_type") or "",
        "topics": list(t.get("topics") or ()),
        "start_text": t.get("start_text") or "",
        "resolution_text": t.get("resolution_text"),
    }


def document(threads: list[dict[str, Any]], tangents: list[dict[str, Any]],
             total_duration: float) -> dict[str, Any]:
    """The drawable part of the document, from one stored conversation's fields."""
    b = beat(threads)
    gap = b * REST_BEATS
    return {
        "total_duration": total_duration,
        "beat": b,
        "rest_gap": gap,
        "topics": [lane(t, gap, total_duration) for t in threads],
        "tangents": [tangent(t) for t in tangents],
    }
