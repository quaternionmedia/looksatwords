"""The harness's thread archive, read over the seam rather than off its disk.

**NOTHING HERE IMPORTS qmcp.** What crosses is HTTP and a schema. This project
knowing where the archive keeps its files would be this project owning half of
somebody else's storage layout, and the first format change would break a
repository that never asked to be involved. `qmcp/threads/service.py` says the
same thing from the other side, in its own words: a second tool should not have
to become qmcp to read what qmcp archived.

**THE HOST IS LOOPBACK AND IS NOT CONFIGURABLE. THE PORT IS.** The archive is
somebody's conversations. Running the harness on another port is ordinary and
supported; a client that could be pointed at another *machine* is how "served
to this machine only" stops being true, so nothing moves the host. That split
is the same one `llm.py` makes about Ollama and the same one dossier makes
about this very archive.

**WHEN THE HARNESS IS NOT RUNNING, SAY SO.** The failure this is written
against is a panel that shows an empty list when the truth is that nobody
answered. `Archive.reachable` is False with a reason and the command that fixes
it, and every caller renders that rather than zero rows. A count of zero and a
count nobody took are different claims.

**WHAT THIS CANNOT DO — AND THIS IS A BOUNDARY, NOT AN UNFIXED DEFECT.**
Author. It never writes a thread, a digest, a decision or a delta. The archive
stays one record with one author, and a reader editing it would be a second.
The adoption record's §3 on `project/looksatwords` is where that is decided:
this project reads the *turns* that qmcp deliberately discards, and emits
structure over them. Everything here is a GET.

WHY THIS EXISTS AT ALL. Because "paste a conversation into a box" is a person
doing by hand what a machine already holds. The harness has hundreds of real
threads indexed; this is the path that lets the dashboard read them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import httpx

# THE HOST IS NOT A SETTING. See the module docstring.
HOST = "127.0.0.1"

# WHERE THE HARNESS ANSWERS: PI. The org's three services take constants
# somebody can recall without looking -- 3141 the harness, 1618 dossier's panel,
# 2718 the code maps.
#
# **THIS IS A SECOND COPY OF SOMEBODY ELSE'S CONSTANT.** `qmcp/config.py` holds
# `port: int = 3141` and the two repositories cannot import each other without
# putting the harness's code into this project's install for the sake of an
# integer. `looksatwords/tests/test_harness.py` reads qmcp's own config when
# the sibling clone is present and fails when the two disagree, which is the
# only way a copied constant stays true. Mutated on 2026-08-26 by setting
# this to 8000: the test reported that qmcp serves 3141 and this looks for
# 8000, then passed again on restore.
DEFAULT_PORT = 3141

# How long to wait on a local service before calling it unreachable. Generous,
# because a large thread is a large file read on the other side, and a timeout
# reported as "not running" would be a false diagnosis of the ordinary case.
TIMEOUT = 30.0


def base_url() -> str:
    port = os.environ.get("LOOKSATWORDS_HARNESS_PORT", str(DEFAULT_PORT))
    return f"http://{HOST}:{port}"


def _fix() -> str:
    return f"Start it with `uv run qmcp serve`, or set LOOKSATWORDS_HARNESS_PORT if it is not on {base_url()}."


@dataclass(frozen=True)
class Archive:
    """What the harness answered, or why nobody could ask it.

    `reachable` False is never rendered as an empty archive. `threads` is empty
    in both cases and only `reachable` distinguishes them, which is why every
    caller is required to read it first.
    """

    reachable: bool
    reason: str | None = None
    fix: str | None = None
    generated_at: str | None = None
    totals: dict[str, Any] = field(default_factory=dict)
    threads: tuple[dict[str, Any], ...] = ()

    @classmethod
    def unreachable(cls, reason: str) -> "Archive":
        return cls(reachable=False, reason=reason, fix=_fix())


@dataclass(frozen=True)
class Thread:
    """One conversation as the archive holds it."""

    source: str
    id: str
    title: str
    turns: tuple[dict[str, Any], ...]
    started_at: str | None = None
    url: str | None = None
    # THE EXCERPT FLAG, CARRIED RATHER THAN DROPPED. The harness sets this when
    # the turns it returned are part of the thread. A reader that counted these
    # turns and called the number "the conversation" would be reporting the size
    # of an excerpt -- the trap qmcp's own payload names about itself.
    partial: bool = False


def index() -> Archive:
    """What the harness has indexed, or an unreachable answer with the fix."""
    try:
        r = httpx.get(f"{base_url()}/v1/threads", timeout=TIMEOUT)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        return Archive.unreachable(
            f"The harness answered {e.response.status_code} at {base_url()}/v1/threads."
        )
    except Exception as e:
        return Archive.unreachable(
            f"Nobody answered at {base_url()}: {type(e).__name__}."
        )

    payload = r.json()
    return Archive(
        reachable=True,
        generated_at=payload.get("generated_at"),
        totals=payload.get("totals") or {},
        threads=tuple(payload.get("threads") or ()),
    )


@dataclass(frozen=True)
class Fetch:
    """One thread, or the reason nobody could produce it.

    THREE OUTCOMES, NOT TWO. The thread arrived; the archive answered and does
    not have it; nobody answered at all. Collapsing the last two into `None`
    made the panel say "the harness did not produce this", which reads as a
    fault in the request and is wrong in both directions -- a 404 here is the
    harness disagreeing with its own index, and a timeout is a live service
    being slow.
    """

    thread: "Thread | None" = None
    reason: str | None = None
    fix: str | None = None
    # True when the archive answered and said it does not hold this thread.
    # That is the harness's answer, not a failure to reach it.
    answered: bool = False


def thread(source: str, thread_id: str) -> Fetch:
    """One thread's turns, with the reason attached when there are none.

    **THE INDEX AND THE ARCHIVE DISAGREE FOR ONE SOURCE.** Measured against the
    live harness on 2026-08-26: of 30 threads sampled from `GET /v1/threads`,
    every `chatgpt` (10 of 10) and `claude` (6 of 6) thread resolved, and 10 of
    14 `claude-code` threads returned 404 from `GET /v1/threads/{source}/{id}`.
    The index lists them; the read route does not have them. That is qmcp's to
    settle -- this project reads the seam and does not repair the other side --
    so what happens here is that the message says which of the two it is.
    """
    try:
        r = httpx.get(f"{base_url()}/v1/threads/{source}/{thread_id}", timeout=TIMEOUT)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return Fetch(
                answered=True,
                reason=(
                    f"The archive answered and does not hold {source}/{thread_id}, "
                    "though its index lists it."
                ),
                fix=(
                    "The harness's index and its read route disagree. Re-index with "
                    "`uv run qmcp threads index --write`, or pick another thread. "
                    "Nothing on this side can repair it."
                ),
            )
        return Fetch(
            answered=True,
            reason=f"The archive answered {e.response.status_code} for {source}/{thread_id}.",
            fix=_fix(),
        )
    except Exception as e:
        return Fetch(
            reason=f"Nobody answered at {base_url()}: {type(e).__name__}.",
            fix=_fix(),
        )

    d = r.json()
    return Fetch(
        answered=True,
        thread=Thread(
            source=d.get("source", source),
            id=d.get("id", thread_id),
            title=d.get("title") or "",
            turns=tuple(d.get("turns") or ()),
            started_at=d.get("started_at"),
            url=d.get("url"),
            partial=bool(d.get("partial")),
        ),
    )


# What a role is called once it is a speaker. The analyser groups by speaker
# name, so these are the names that appear in every chart downstream.
SPEAKER = {"user": "Operator", "assistant": "Assistant", "system": "System"}


def as_conversation(
    t: Thread, limit: int | None = None
) -> tuple[str, dict[str, Any]]:
    """Turns as the one-line-per-turn text this project's parser reads.

    Returns the text and a report of what the conversion cost, because every
    lossy step below is invisible in the output and would otherwise be
    discovered by somebody wondering why a number looked wrong.

    **MOST TURNS IN THIS ARCHIVE ARE NOT PROSE.** Measured against the live
    harness on 2026-08-26: one claude-code thread of 4,715 turns carries text in
    776 of them. The rest are tool calls and their results, which the seam
    returns with an empty `text`. So `limit` counts *turns that carry prose* and
    not raw turns -- capping raw turns took the first 300 and emitted 18 lines,
    which is a truthful number attached to the wrong question.

    **THE PARSER TAKES ONE LINE PER TURN.** An assistant turn holds newlines and
    code fences; left alone, one turn becomes forty messages, forty speakers'
    worth of `Unknown`, and a thread graph of nothing. So whitespace inside a
    turn is collapsed. That is a real loss of structure and it is the price of
    reading prose with a line-oriented parser.

    **NO SILENT CAP.** The report names all three counts, and they are three
    different facts: how long the thread is, how much of it is prose, and how
    much of that was used. A truncation nobody reports reads as a complete
    conversation.
    """
    total = len(t.turns)

    with_text = 0
    lines = []
    for turn in t.turns:
        text = " ".join((turn.get("text") or "").split())
        if not text:
            continue
        with_text += 1
        if limit is None or len(lines) < limit:
            speaker = SPEAKER.get(turn.get("role", ""), turn.get("role") or "Unknown")
            lines.append(f"{speaker}: {text}")

    report = {
        "turns_total": total,
        "turns_with_text": with_text,
        "turns_used": len(lines),
        "turns_without_text": total - with_text,
        "truncated": limit is not None and with_text > len(lines),
        "limit": limit,
        # Carried through from the harness rather than recomputed, because the
        # harness is the only side that knows whether it gave us everything.
        "partial_at_source": t.partial,
        "whitespace_collapsed": True,
    }
    return "\n".join(lines), report


def deltas(source: str, thread_id: str) -> dict[str, Any] | None:
    """What the harness says this thread settled, or None if it could not say.

    THIS IS THE OTHER SIDE'S ANSWER AND IT IS NOT RECOMPUTED HERE. qmcp decides
    what a thread produced; this project reads the turns. Rendering the
    harness's own payload rather than deriving a second opinion from the same
    text is what keeps one record with one author -- and the corpus's rule to
    prefer the artefact you did not create.
    """
    try:
        r = httpx.get(
            f"{base_url()}/v1/threads/{source}/{thread_id}/deltas", timeout=TIMEOUT
        )
        r.raise_for_status()
    except Exception:
        return None
    return r.json()


# THE NEIGHBOURS, AND WHY THEY ARE LISTED RATHER THAN CALLED.
#
# dossier carries a delta through its lifecycle; codecarto maps source code.
# Neither is a dependency of this project and neither is imported. What this
# offers is a link and an honest answer about whether anybody is home, so a
# reader following a thread from turns to decisions to lifecycle can see the
# whole path exists -- and can see which parts of it are not running right now.
#
# **A LINK IS NOT AN INTEGRATION AND THIS DOES NOT PRETEND OTHERWISE.** These
# report reachability and nothing else. Inventing a plausible summary of what
# dossier would have said is exactly the failure the org keeps writing down.
NEIGHBOURS = (
    {
        "name": "dossier",
        "port": 1618,
        "what": "carries a delta through brainstorm to complete",
        "fix": "Start it with `uv run dossier serve` in the dossier clone.",
    },
    {
        "name": "codecarto",
        "port": 2718,
        "what": "maps source code as graphs; the other half of the border",
        "fix": "Start it in the codecartographer clone.",
    },
)


def neighbours() -> list[dict[str, Any]]:
    """Each sibling service, with whether it answered just now."""
    out = []
    for n in NEIGHBOURS:
        url = f"http://{HOST}:{n['port']}"
        row = {"name": n["name"], "url": url, "what": n["what"]}
        try:
            r = httpx.get(url + "/", timeout=2.0)
            row["reachable"] = True
            row["status"] = r.status_code
        except Exception as e:
            row["reachable"] = False
            row["reason"] = f"Nobody answered at {url}: {type(e).__name__}."
            row["fix"] = n["fix"]
        out.append(row)
    return out
