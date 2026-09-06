"""Reading the org's loose-ends document as a corpus.

**THE CONTRACT IS SHARED AND THIS RUNS IT.** `project-seed/loose-end-vectors.json`
lives in the corpus, and every consumer of the document runs the same cases so
that two readings stay honest without one importing the other. The first case is
the one the file exists for: a consumer must not render an item nobody has
judged the same as one somebody read and let go.

**NOTHING HERE NEEDS THE ANALYSIS STACK.** `looksatwords.loose_ends` is standard
library only, deliberately -- a repository reaching the document over a seam
should not have to build a venv with nltk in it to read a list. So these tests
run wherever pytest does.

The vector cases are skipped, loudly, when no corpus is beside this clone. A
skip that said nothing would let this file go quiet the day the corpus moved,
which is the failure the vectors exist to prevent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from looksatwords import loose_ends as module

VECTORS = "project-seed/loose-end-vectors.json"


def corpus_root() -> Path | None:
    """The corpus beside this clone, if there is one."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "qm"
        if (candidate / VECTORS).is_file():
            return candidate
    return None


def document(items: list[dict], **extra) -> dict:
    base = {"schema": module.SCHEMA, "generated_at": "2026-09-06T00:00:00Z",
            "loose_ends": items}
    base.update(extra)
    return base


def item(kind="stalled-thread", address="quaternionmedia/alfred/pr/113",
         claim=None, **extra):
    one = {"kind": kind, "address": address, "key": f"{kind}:{address}",
           "title": "a title", "detail": "a detail"}
    if claim:
        one["claim"] = claim
    one.update(extra)
    return one


# --- the shared contract ------------------------------------------------------


def test_the_corpus_vectors_are_reachable():
    """A skip nobody reads is how this file goes quiet.

    Mutation: point `VECTORS` at a path that moved and this says so rather than
    silently checking nothing.
    """
    root = corpus_root()
    if root is None:
        pytest.skip("no qm corpus beside this clone, so the shared vectors "
                    "cannot be run -- this is a gap, not a pass")
    assert (root / VECTORS).is_file()


@pytest.mark.parametrize("case_index", range(6))
def test_every_shared_vector_case_holds(case_index):
    """THE ONE THIS FILE EXISTS FOR.

    The corpus states how a loose end reads; this asserts this package agrees.
    Case one is the distinction between unclaimed and dismissed.

    Mutation: treat any disposition as closing an item and the unrecognised-
    disposition case fails here exactly as it does in the corpus.
    """
    root = corpus_root()
    if root is None:
        pytest.skip("no qm corpus beside this clone")

    cases = json.loads((root / VECTORS).read_text(encoding="utf-8"))["cases"]
    if case_index >= len(cases):
        pytest.skip(f"the corpus carries {len(cases)} cases")
    case = cases[case_index]

    given = case["given"]
    claims = given.get("claims", {})
    raw = dict(given["item"])
    key = f"{raw['kind']}:{raw['address']}"
    claim = claims.get(key)
    if claim:
        raw["claim"] = claim
    raw.setdefault("title", "")
    raw.setdefault("detail", "")

    # `items()` drops dismissed by default, which is this package's reading of
    # the same rule: a settled question must not enter a topic model as a live
    # one. So the presence of the item is the assertion.
    kept = module.items(document([raw]))
    expect = case["expect"]

    if expect["disposition"] == "dismissed":
        assert not kept, (
            f"{case['name']}: a dismissed item entered the corpus")
        return

    assert len(kept) == 1, case["name"]
    one = kept[0]
    assert one.key == expect["key"], case["name"]
    assert (one.disposition is None) == (not expect["has_claim"]), case["name"]
    assert one.disposition == expect["disposition"], case["name"]


# --- what this package does with them -----------------------------------------


def test_an_unclaimed_item_and_a_carried_one_both_stay():
    """`carried` means somebody picked it up, not that it is finished.

    Mutation: drop carried items and picking something up looks like closing
    it.
    """
    kept = module.items(document([
        item(address="quaternionmedia/a/pr/1"),
        item(address="quaternionmedia/b/pr/2",
             claim={"disposition": "carried", "by": "someone"}),
    ]))
    assert len(kept) == 2
    assert [one.is_carried for one in kept] == [False, True]


def test_a_dismissed_item_is_left_out_by_default():
    """The analytical form of the contract: a settled question must not enter
    a topic model as a live one.

    Mutation: keep dismissed items and the corpus reports work nobody is doing.
    """
    kept = module.items(document([
        item(claim={"disposition": "dismissed", "by": "someone",
                    "why": "landed elsewhere"}),
    ]))
    assert kept == []


def test_dismissed_items_can_be_asked_for_deliberately():
    """"What has this org decided to stop caring about" is a real question and
    a different one."""
    kept = module.items(document([
        item(claim={"disposition": "dismissed", "by": "someone"}),
    ]), include_dismissed=True)
    assert len(kept) == 1 and kept[0].disposition == "dismissed"


# --- the translation ----------------------------------------------------------


def test_the_speaker_is_the_repository():
    """THE CHOICE THAT MAKES THE EXISTING MACHINERY USEFUL.

    Speaker comparison is already built and already charted; making the speaker
    the repository turns it into "which repository carries the most unfinished
    work" for free.

    Mutation: use the kind as the speaker and that reading is lost.
    """
    one = module.LooseEnd(key="k", kind="stalled-thread",
                          address="quaternionmedia/alfred/pr/113",
                          title="t", detail="d")
    assert one.repository == "quaternionmedia/alfred"
    assert one.as_turn().startswith("quaternionmedia/alfred: ")


def test_a_short_address_is_used_whole_rather_than_invented_from():
    """Attributing a finding to a repository that does not exist would be worse
    than an odd speaker name."""
    one = module.LooseEnd(key="k", kind="over-slot", address="solo",
                          title="t", detail="d")
    assert one.repository == "solo"


def test_a_carried_item_says_so_in_the_text():
    """The parser has one field, so anything a downstream reading needs has to
    travel in it.

    Mutation: mark it in a field instead and topics, sentiment and the tangent
    detector never see it.
    """
    one = module.LooseEnd(key="k", kind="stalled-thread", address="o/r/pr/1",
                          title="t", detail="d", disposition="carried")
    assert "[carried]" in one.as_turn()


def test_the_conversation_is_one_line_per_item():
    """The whole integration: from here every existing analysis applies."""
    text = module.as_conversation(document([
        item(address="quaternionmedia/a/pr/1"),
        item(address="quaternionmedia/b/pr/2"),
    ]))
    lines = text.splitlines()
    assert len(lines) == 2
    assert all(":" in line for line in lines), "the parser needs a speaker"


# --- honesty about what is missing --------------------------------------------


def test_a_source_the_corpus_could_not_read_is_reported():
    """**A SHORT CORPUS AND A COMPLETE ONE LOOK ALIKE.** With the harness
    document unreadable the text carries no stalled threads and reads exactly
    like an org with none.

    Mutation: drop `unreadable_sources` and a floor gets quoted as a total.
    """
    doc = document([item()], generator={"sources": {
        "harness": {"unknown": "harness-status.json is not in this corpus"},
        "docs": {"document": "doc-status.json", "generated_at": "x"},
    }})
    missing = module.unreadable_sources(doc)
    assert list(missing) == ["harness"]
    assert "harness-status.json" in missing["harness"]
    assert "floor" in module.summarise(doc)


def test_the_summary_names_a_number_even_with_nothing_in_it():
    said = module.summarise(document([]))
    assert "0 loose end(s)" in said


def test_a_missing_source_file_says_what_to_point_at():
    """A tool that guessed which corpus it meant would analyse one organisation
    and report another."""
    with pytest.raises(FileNotFoundError, match="does not go looking"):
        module.read(Path("nowhere") / "loose-ends.json")


def test_the_title_carries_where_and_when():
    """A corpus with no date is one nobody can judge the age of."""
    said = module.title_for(document([]), "somewhere/loose-ends.json")
    assert "somewhere/loose-ends.json" in said
    assert "2026-09-06" in said


def test_the_rendering_is_ascii_so_a_windows_console_can_print_it():
    """This prints to a terminal, and cp1252 renders an em-dash as `?` at best.

    Mutation: put a dash back and this fails.
    """
    module.title_for(document([]), "x").encode("cp1252")
    module.summarise(document([item()])).encode("cp1252")
