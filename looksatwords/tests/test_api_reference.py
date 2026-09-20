"""`docs/api.md` and the application agree about which routes exist, in both directions.

The sibling of `test_cli_reference.py`, for the same reason: prose describing
behaviour in a second place drifts, and the drift is invisible at any single
commit. When this guard was written the page's overview tables omitted every
route under `/api/harness/` -- five routes a reader of the page could not know
were there -- while every route the page did list existed.

BOTH DIRECTIONS, BECAUSE ONLY ONE OF THEM IS OBVIOUS. A route the page omits
is found by a reader who already knows it exists. A documented route the app
does not serve is found only by calling it.

WHAT IS COMPARED. Method and path, with path parameters compared by position
and not by name: the page writes `{id}` where the code writes
`{conversation_id}`, and a URL does not care. The routes the framework adds
for its own documentation, the front end's static mounts and the page at `/`
are not API routes and are left out on both sides.

MUTATED ON 2026-09-20 AND SEEN RED THREE WAYS. Deleting the `/api/harness/neighbours`
row failed `test_every_served_route_is_documented`; adding a `/api/harness/teleport`
row failed `test_every_documented_route_is_served`; misspelling that route's
`###` heading failed `test_every_harness_route_has_its_own_section`. Restored,
all pass.
"""

import pathlib
import re

import pytest
from fastapi.routing import APIRoute

from looksatwords.app.main import app

DOC = pathlib.Path(__file__).resolve().parent.parent.parent / "docs" / "api.md"

TABLES = re.compile(r"<!-- ROUTES:.*?-->(.*?)<!-- END ROUTES -->", re.DOTALL)
ROW = re.compile(r"^\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*`([^`]+)`", re.MULTILINE)
PARAM = re.compile(r"\{[^}]*\}")


def _shape(method: str, path: str) -> str:
    """One route as a comparable string, its parameter names erased."""
    return f"{method} {PARAM.sub('{}', path)}"


def _documented() -> set[str]:
    """Every route in the overview tables between the markers."""
    m = TABLES.search(DOC.read_text(encoding="utf-8"))
    assert m, (
        "the ROUTES markers are missing from docs/api.md, so this guard has "
        "nothing to read. Restore them rather than deleting this test."
    )
    return {_shape(method, path) for method, path in ROW.findall(m.group(1))}


def _served() -> set[str]:
    """Every API route the application registers."""
    out = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not (route.path.startswith("/api/") or route.path == "/health"):
            continue
        for method in route.methods - {"HEAD", "OPTIONS"}:
            out.add(_shape(method, route.path))
    return out


def test_the_guard_can_read_both_sides():
    """Guard the guard: an empty set on either side passes everything below."""
    documented, served = _documented(), _served()
    assert documented, "no routes were parsed out of docs/api.md's tables"
    assert served, "no API routes were found on the application"


@pytest.mark.parametrize("route", sorted(_served()))
def test_every_served_route_is_documented(route):
    assert route in _documented(), (
        f"the app serves `{route}` and docs/api.md's overview does not list it."
    )


@pytest.mark.parametrize("route", sorted(_documented()))
def test_every_documented_route_is_served(route):
    assert route in _served(), (
        f"docs/api.md lists `{route}` and the app serves no such route. "
        "Somebody following this page would call it and get a 404."
    )


def test_every_harness_route_has_its_own_section():
    """The overview row is the index; each harness route also has a heading with its shape.

    The overview guard above would pass on a row alone. This is the page's
    promise that the request and response of every `/api/harness/*` route are
    written down, which is what the front end reading them over HTTP needs.
    """
    text = DOC.read_text(encoding="utf-8")
    for route in sorted(_served()):
        method, path = route.split(" ", 1)
        if not path.startswith("/api/harness/"):
            continue
        headings = re.findall(rf"^### `{method} ([^`]+)`", text, re.MULTILINE)
        assert any(PARAM.sub("{}", h) == path for h in headings), (
            f"`{route}` is in the overview and has no `### {method} ...` section"
        )
