"""Build the committed thread-archive fixture the screenshots are recorded from.

WHY A FIXTURE AND NOT THE LIVE ARCHIVE. The pictures in `docs/` are committed
artifacts, and an artifact generated from a live service is regenerated
differently by every person who runs it. The archive on the machine this was
written on moved during a single session -- one thread went from 13,844 to
15,417 turns between two runs an hour apart -- so a screenshot taken from it
would churn on every regeneration and its diff would carry no information.

This writes `harness_archive.json`, which is committed and never changes unless
somebody changes it on purpose. Run it only to author a new fixture:

    uv run python looksatwords/tests/fixtures/make_harness_fixture.py

THE CONVERSATION IS REAL IN SHAPE AND INVENTED IN CONTENT. It is written to
exercise what the analysis actually does -- a topic that is dropped and picked
up again, two tangents with one of them resolved, and turns carrying no prose so
the conversion report has something true to say about tool calls.
"""

import json
import pathlib

TURNS = [
    ("user", "We need to decide how the panel reads the thread archive."),
    ("assistant", "The obvious move is to import the harness package directly."),
    # A tool call: no prose. The conversion report counts these separately.
    ("assistant", ""),
    ("user", "That couples them. If the storage layout changes, the panel breaks."),
    ("assistant", "However, HTTP over loopback means we need the harness running."),
    ("assistant", ""),
    ("user", "That is a precondition we can declare, though. Side note - what port?"),
    ("assistant", "3141. The harness publishes it, and the host stays loopback."),
    ("user", "Back to the seam - so it is HTTP plus a schema, and nothing imports anything."),
    ("assistant", ""),
    ("assistant", "Right. The schema is the contract and the port is the only setting."),
    ("user", "What happens when the harness is not running at all?"),
    ("assistant", "The panel says nobody answered, and names the command that fixes it."),
    ("user", "Not an empty table. An empty table and a broken one look identical."),
    ("assistant", "Agreed. Reachable is a field, and every caller reads it first."),
    ("user", "Then the decision is the seam. Let us write that down."),
]

THREAD = {
    "source": "claude",
    "id": "fixture-seam-0001",
    "title": "How the panel reads the thread archive",
    "url": "https://example.invalid/threads/fixture-seam-0001",
    "started_at": "2026-08-20T14:00:00Z",
    "partial": False,
    "turns": [
        {"id": f"turn-{i:03d}", "role": role, "at": str(1787000000 + i * 90), "text": text}
        for i, (role, text) in enumerate(TURNS)
    ],
}

SECOND = {
    "source": "chatgpt",
    "id": "fixture-ports-0002",
    "title": "Choosing service ports nobody has to look up",
    "url": "https://example.invalid/threads/fixture-ports-0002",
    "started_at": "2026-08-19T09:30:00Z",
    "partial": False,
    "turns": [
        {"id": "turn-000", "role": "user", "at": "1787000000",
         "text": "Three services need three ports somebody can recall."},
        {"id": "turn-001", "role": "assistant", "at": "1787000090",
         "text": "Pi for the harness, phi for the panel, e for the code maps."},
        {"id": "turn-002", "role": "user", "at": "1787000180",
         "text": "The joke port everyone reaches for was already in use here."},
        {"id": "turn-003", "role": "assistant", "at": "1787000270",
         "text": "Which is the argument against the port everybody thinks of first."},
    ],
}

# A row the index lists and the archive does not hold, so the screenshot run
# exercises the disagreement this project reports rather than only the happy
# path. The live harness does this for one source; the fixture does it on
# purpose, and nothing has to be broken to see it.
MISSING = {
    "source": "claude-code",
    "id": "fixture-absent-0003",
    "title": "A thread the index lists and the archive cannot produce",
    "turns": 42,
}

ARCHIVE = {
    "schema": 1,
    "generated_at": "2026-08-20T15:00:00Z",
    "reading": {
        "the_index_is_a_reading": (
            "These figures are as of `generated_at`, from a cache that is itself a "
            "snapshot. Nothing here counts conversations that exist; it counts "
            "conversations that were exported and indexed."
        ),
        "refresh": "uv run qmcp threads index --write",
    },
    "totals": {"threads": 3, "diverged": 0, "unreadable": 0},
    "threads": [
        {
            "source": t["source"],
            "id": t["id"],
            "title": t["title"],
            "turns": len(t["turns"]),
            "digest": f"fixture{i}",
            "first_seen": "2026-08-19T09:30:00Z",
            "last_seen": "2026-08-20T15:00:00Z",
            "diverged": False,
            "changes": 0,
            "address": f"quaternionmedia/qmcp/delta/thread-{t['id']}",
            "perspective": f"{t['source']}/thread",
            "phase": "brainstorm",
            "delta_type": "thread",
        }
        for i, t in enumerate((THREAD, SECOND))
    ]
    + [
        {
            "source": MISSING["source"],
            "id": MISSING["id"],
            "title": MISSING["title"],
            "turns": MISSING["turns"],
            "digest": "fixture9",
            "first_seen": "2026-08-19T09:30:00Z",
            "last_seen": "2026-08-20T15:00:00Z",
            "diverged": False,
            "changes": 0,
            "address": f"quaternionmedia/qmcp/delta/thread-{MISSING['id']}",
            "perspective": "claude-code/thread",
            "phase": "brainstorm",
            "delta_type": "thread",
        }
    ],
    # Keyed by "source/id"; the stub serves these from the thread route.
    "_bodies": {f"{t['source']}/{t['id']}": t for t in (THREAD, SECOND)},
    "_deltas": {
        f"{t['source']}/{t['id']}": {
            "source": t["source"],
            "id": t["id"],
            "perspective": f"{t['source']}/thread",
            "deltas": [
                {
                    "schema": 1,
                    "project": "quaternionmedia/qmcp",
                    "perspective": f"{t['source']}/thread",
                    "delta": {
                        "name": f"thread-{t['id']}",
                        "title": t["title"],
                        "description": t["url"],
                        "phase": "brainstorm",
                        "delta_type": "thread",
                        "priority": "medium",
                    },
                    "links": [
                        {"link_type": "address", "target_id": None,
                         "target_name": f"quaternionmedia/qmcp/delta/thread-{t['id']}"},
                        {"link_type": "thread", "target_id": None,
                         "target_name": t["url"]},
                    ],
                }
            ],
            "relations": [],
            "spent": 0,
        }
        for t in (THREAD, SECOND)
    },
}

if __name__ == "__main__":
    out = pathlib.Path(__file__).parent / "harness_archive.json"
    out.write_text(json.dumps(ARCHIVE, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(ARCHIVE['threads'])} indexed, "
          f"{len(ARCHIVE['_bodies'])} retrievable)")
