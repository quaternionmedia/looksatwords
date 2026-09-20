"""What the stub harness answers, for any way of asking it.

**ONE COPY OF THE ARCHIVE'S ROUTE LOGIC.** The screenshot recorder serves
`harness_archive.json` over a real socket because a browser has to reach it;
the API tests answer the same fixture from inside the process, because a test
that binds a port is a test that fails when the port is busy. Both go through
`answer`, so the stub cannot say one thing to the browser and another to the
`TestClient`.

The fixture indexes one thread it cannot produce, on purpose. `answer` returns
404 for it the way the live harness does for one of its sources, so the
disagreement this project reports is exercised without anything being broken.

WHAT THIS CANNOT DO. Stand in for the harness's own behaviour on any route it
does not list here: an unknown path is a 404 and nothing more. It is a fixture
for this project's reading of the seam, not a second implementation of qmcp.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

FIXTURE = pathlib.Path(__file__).parent / "harness_archive.json"


def load() -> dict[str, Any]:
    """The committed archive, as the stub serves it."""
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def answer(archive: dict[str, Any], path: str) -> tuple[int, dict[str, Any]]:
    """Status and body for one GET against the stub, query string ignored.

    `/v1/threads` is the index without the private `_` keys the fixture keeps
    for its own use; `/v1/threads/{source}/{id}` is the body, and `/deltas`
    under it is what the harness says the thread settled.
    """
    path = path.split("?")[0]
    if path == "/v1/threads":
        return 200, {k: v for k, v in archive.items() if not k.startswith("_")}

    parts = path.strip("/").split("/")
    if len(parts) >= 4 and parts[0] == "v1" and parts[1] == "threads":
        key = f"{parts[2]}/{parts[3]}"
        if len(parts) == 5 and parts[4] == "deltas":
            d = archive["_deltas"].get(key)
            return (200, d) if d else (404, {"detail": "no deltas"})
        body = archive["_bodies"].get(key)
        return (200, body) if body else (404, {"detail": "not held"})

    return 404, {"detail": "not found"}
