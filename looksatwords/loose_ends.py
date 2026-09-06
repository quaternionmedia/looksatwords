"""Read the org's loose-ends document as a corpus, so it can be analysed as text.

**EVERY OTHER CONSUMER CAN LIST THESE. THIS ONE CAN SAY WHAT THEY ARE ABOUT.**
A loose end is text -- a title, a detail, a reason somebody gave -- and text is
the thing this package analyses. So the useful question here is not "how many
are open", which the document already answers, but the one no list answers:
*what does this organisation keep leaving unfinished?* Topic extraction over
ninety-five findings answers that; a table of ninety-five rows does not.

**THIS IS A TRANSLATION, NOT A NEW SUBSYSTEM.** looksatwords understands one
text shape -- `Speaker: what they said`, one per line -- and everything it does
hangs off that: the parser, thread analysis, tangent detection, sentiment,
topics, speaker comparison, collections, charts. So this maps a loose end onto
that shape and stops. Nothing here analyses anything; it makes the document
legible to machinery that already exists.

**THE SPEAKER IS THE REPOSITORY.** Each item's address begins `owner/repo`, so
speaker comparison -- already built, already charted -- becomes *which
repository carries the most unfinished work*, and thread analysis over the
details becomes *what those repositories keep leaving open*. That reading is a
side effect of choosing the right speaker, which is the whole reason to translate
rather than to build.

**DISMISSED ITEMS ARE LEFT OUT, AND THAT IS THE CONTRACT.**
`project-seed/loose-end-vectors.json` case one exists so that a consumer cannot
render an item nobody has judged the same as one somebody read and let go. Here
that means a dismissed item is not in the corpus at all: including it would put
a settled question into a topic model as though it were live, which is the
analytical form of the same error. `carried` items stay and are marked --
somebody following a thread has not finished it.

WHAT THIS CANNOT DO.

  * Judge anything. Dispositions are the corpus's, written by a person in
    `registers/loose-end-claims.yaml`. Nothing here writes one back, and there
    is no endpoint that could.
  * Read a document it was not given. The source is a path or a URL the caller
    names; this never goes looking, because a tool that guessed which corpus it
    meant would analyse one organisation and report another.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import sys
from urllib.request import urlopen

SCHEMA = 1

# **THE ONLY TWO DISPOSITIONS THERE ARE, AND THIS IS A SECOND COPY OF THE
# CORPUS'S SET.** It cannot be imported: looksatwords does not vendor the
# corpus and reaches the document over a seam, which is the arrangement
# `records/DRAFT-seams-on-standard-protocols.md` prefers. What keeps a copied
# constant true is the shared vectors -- `project-seed/loose-end-vectors.json`
# case five fails the moment this set disagrees, which is the same device
# `address-vectors.json` uses for the grammar.
#
# Anything outside the set is ignored and the item stays open. A misspelling
# that quietly closed a finding is the failure a register of decisions can
# least afford, and a consumer that honoured any word would be where it
# happened.
DISPOSITIONS = ("carried", "dismissed")

# The disposition that removes an item from the corpus. `carried` does not:
# somebody following a thread has not finished it, and dropping it would make
# the act of picking something up look like the act of closing it.
EXCLUDED = "dismissed"

# How the corpus spells a fact nobody could establish. Carried through rather
# than flattened, so a source that could not be read is visible as text instead
# of arriving as an absence.
UNKNOWN = "unknown"


@dataclass(frozen=True)
class LooseEnd:
    """One item, in the terms this package needs."""

    key: str
    kind: str
    address: str
    title: str
    detail: str
    disposition: str | None = None

    address_parses: bool = True
    """Whether the corpus could resolve this item's address.

    **CARRIED, NOT RE-DERIVED.** The grammar is `ci/addresses.py`'s and the
    corpus already ran it; parsing again here would be a second grammar, which
    is the thing `project-seed/address-vectors.json` exists to prevent. A view
    reads this before offering a link, because an address that does not parse
    cannot navigate to its subject. Defaults True so a document that predates
    the field is not read as ninety-five dead links.
    """

    @property
    def repository(self) -> str:
        """`owner/repo`, which is what becomes the speaker.

        The address grammar puts it first and the corpus guarantees the round
        trip, so this is a split rather than a parse. An address with fewer
        than two segments is its own answer and is used whole -- inventing a
        repository for it would attribute somebody's finding to a repository
        that does not exist.
        """
        parts = self.address.split("/")
        return "/".join(parts[:2]) if len(parts) >= 2 else self.address

    @property
    def is_carried(self) -> bool:
        return self.disposition == "carried"

    def as_turn(self) -> str:
        """One line in the shape the parser reads.

        The kind travels in the text rather than in a field, because the
        parser has one field and this is the one that survives into every
        downstream reading -- topics, sentiment, the tangent detector's
        triggers. A carried item says so for the same reason.
        """
        marker = "[carried] " if self.is_carried else ""
        return f"{self.repository}: {marker}{self.kind} -- {self.title}. {self.detail}"


def read(source: str | Path) -> dict:
    """The document, from a path or a URL. Never guessed at.

    A URL is how a repository that does not vendor the corpus reaches this --
    the seam route, which is what `records/DRAFT-seams-on-standard-protocols.md`
    prefers over a submodule for a single reading.
    """
    text = str(source)
    if text.startswith(("http://", "https://")):
        with urlopen(text, timeout=10) as answer:   # noqa: S310 - caller's URL
            return json.loads(answer.read().decode("utf-8"))
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is not there. Point at a corpus's loose-ends.json, or at "
            f"a URL serving one; this does not go looking for a corpus of its "
            f"own.")
    return json.loads(path.read_text(encoding="utf-8"))


def items(document: dict, include_dismissed: bool = False) -> list[LooseEnd]:
    """Every loose end worth analysing, in document order.

    `include_dismissed` exists for the one caller who wants to ask what the org
    has decided to stop caring about -- a real question, and a different one
    from what it is still carrying. It is off by default because the common
    reading is the live corpus.
    """
    found: list[LooseEnd] = []
    for raw in document.get("loose_ends", []):
        claim = raw.get("claim") or {}
        stated = claim.get("disposition")
        # Unrecognised leaves the item open rather than closing it. See
        # DISPOSITIONS: this is the line the shared vectors check.
        disposition = stated if stated in DISPOSITIONS else None
        if disposition == EXCLUDED and not include_dismissed:
            continue
        kind = raw.get("kind", "unknown-kind")
        address = raw.get("address", "")
        found.append(LooseEnd(
            # **DERIVED WHEN ABSENT, BECAUSE THE KEY IS A DEFINITION.** It is
            # `kind:address` and nothing else, so depending on the generator to
            # write it would make this reader fail on a document that is
            # otherwise complete -- and the conformance vectors supply items
            # without one precisely to catch that.
            key=raw.get("key") or f"{kind}:{address}",
            kind=kind,
            address=address,
            title=str(raw.get("title", "")).strip(),
            detail=str(raw.get("detail", "")).strip(),
            disposition=disposition,
            address_parses=bool(raw.get("address_parses", True)),
        ))
    return found


def as_conversation(document: dict, include_dismissed: bool = False) -> str:
    """The document as text this package can parse.

    One item per line, speaker-first. That is the entire integration: from here
    the parser, the thread analyser, the tangent detector, sentiment, topics
    and every chart apply unchanged.
    """
    return "\n".join(one.as_turn()
                     for one in items(document, include_dismissed))


def unreadable_sources(document: dict) -> dict[str, str]:
    """Sources the corpus could not read, and why.

    **REPORTED, BECAUSE A SHORT CORPUS AND A COMPLETE ONE LOOK ALIKE.** If the
    harness document could not be read, the text this produces is missing every
    stalled thread and reads exactly like an org with none. A caller that shows
    a total without showing this is quoting a floor as a ceiling.
    """
    sources = (document.get("generator") or {}).get("sources") or {}
    return {name: value[UNKNOWN]
            for name, value in sources.items()
            if isinstance(value, dict) and UNKNOWN in value}


def title_for(document: dict, source: str | Path) -> str:
    """A title carrying where and when, because a corpus without them is undated."""
    when = document.get("generated_at", "an unstated time")
    # ASCII: this prints to a terminal, and a Windows console on cp1252
    # renders an em-dash as `?` at best and raises at worst.
    return f"Loose ends -- {source} @ {when}"


def summarise(document: dict, include_dismissed: bool = False) -> str:
    """What the translation produced, in one reading."""
    found = items(document, include_dismissed)
    totals = document.get("totals") or {}
    carried = sum(1 for one in found if one.is_carried)
    repositories = {one.repository for one in found}
    said = [
        f"{len(found)} loose end(s) across {len(repositories)} repositories, "
        f"{carried} carried",
    ]
    dismissed = int(totals.get("claimed", 0)) - carried
    if dismissed > 0 and not include_dismissed:
        said.append(f"{dismissed} dismissed and left out")
    missing = unreadable_sources(document)
    if missing:
        said.append(
            f"{len(missing)} source(s) the corpus could not read, so this is a "
            f"floor: " + "; ".join(f"{k} ({v})" for k, v in missing.items()))
    return ". ".join(said) + "."

# --- running it ---------------------------------------------------------------
#
# **ARGPARSE, AND NOTHING IMPORTED FROM THIS PACKAGE.** Everything above is
# standard library only, so this runs on a machine with none of looksatwords'
# analysis dependencies installed -- which is exactly the machine a seam
# consumer is. It is the same property the corpus's own seed scripts have and
# for the same reason: a translation that needed a venv built before it could
# report would not be reachable from the place that needs it.
#
# `looksatwords loose-ends` registers this in the main CLI, which imports the
# analysis stack; this entry point stays for when that is not available.


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Read a corpus's loose-ends.json as an analysable corpus.")
    parser.add_argument("source", help="path or URL to loose-ends.json")
    parser.add_argument("--format", choices=("text", "summary", "keys"),
                        default="summary",
                        help="text: the conversation this package parses")
    parser.add_argument("--include-dismissed", action="store_true",
                        help="include items somebody read and let go")
    args = parser.parse_args(argv)

    try:
        document = read(args.source)
    except Exception as exc:                       # noqa: BLE001
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    schema = document.get("schema")
    if schema != SCHEMA:
        # Reported, not refused. A document from a newer corpus is more likely
        # to be readable than not, and refusing it outright would make this the
        # thing that breaks when the corpus moves forward.
        print(f"note: loose-ends.json is schema {schema}, this reads {SCHEMA}",
              file=sys.stderr)

    if args.format == "text":
        print(as_conversation(document, args.include_dismissed))
    elif args.format == "keys":
        for one in items(document, args.include_dismissed):
            print(one.key)
    else:
        print(title_for(document, args.source))
        print(summarise(document, args.include_dismissed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
