# AGENTS.md

This project is governed by the Quaternion Media constitution, vendored at
`governance/qm` (a submodule pinned to this project's `project/looksatwords`
branch of that repo). If you are an AI coding agent opening this repo with
no other briefing, read this file fully before your first commit or edit.

## Before you do anything

**Establish four facts about this session before you write anything**, because
each has been got wrong here by inheriting a previous session's belief instead of
asking the repository:

1. **The commit you are working against**, and the branch.
2. **Whether your pull request slot is free** — one open pull request per
   repository, per contributor:
   `python governance/qm/project-seed/ci/check_one_pr.py --repo <owner/name>`.
3. **What else is in flight in this clone** — a dirty tree you did not dirty, a
   sibling branch, an unpushed commit. Other sessions are likely running right
   now, in other repositories, for the same reviewer;
   `governance/qm/handbook/async-contract.md` is the set of rules that exist only
   because of that, and it is short.
4. **Which gates exist**, and what each cannot see:
   `python governance/qm/project-seed/ci/run_workflows_locally.py`.

Those are the invariants. **How** you gather them is yours to choose — read the
repository, run the scripts above, or use an adapter if one exists for your
tooling. `governance/qm/adapters/` holds any that do, each named for the product
it targets and none of them required. This file names no vendor, and neither
should anything you add to it.

**Read the corpus's committed status documents before re-deriving what they
hold.** `governance/qm/harness-status.json` carries its own refresh command and
staleness budget in a `reading:` block inside the file.
`governance/qm/governance-status.yaml` does **not** — for that one,
`governance/qm/handbook/generated-documents.md` is the only statement of its
refresh command and its 168-hour budget. Check the age before quoting a figure.

1. Read `governance/qm/PRINCIPLES.md` in full and the three invariants in `governance/qm/README.md`. For namespaces and precedence, see `governance/qm/docs/ref/namespaces.md` and `governance/qm/docs/ref/precedence.md`.
2. This project's own decision records live in `governance/qm/adr/` — inside
   the submodule, on this project's own branch, not at this repo's root — as
   `ADR-NNNN` (numbered locally, at ratification) or `DRAFT-*.md` before
   ratification. A human ratifies; you draft.
3. **Everything you produce arrives as a pull request, and the pull request is
   an audit record rather than a request for anyone's attention.** Work on a
   branch and open a PR — in this repo, and in the `governance/qm` submodule
   when you touch this project's records there — then **merge it yourself once
   every gate is green.** Your job is a default branch that is clean and
   working, entered through a pull request so the gates ran and the diff stays
   readable afterwards. **Never push a shared branch directly**: that is the
   one act that destroys the audit record.
   **The default branch is not a claim, so merging into it is not a release.**
   Per `governance/qm/records/DRAFT-version-tags-are-claims.md` §4, the default
   branch, a pull request and a local build are all drafts — they may be
   perfectly good and they assert nothing. **The two human gates are
   ratification, for what a record says, and the version tag, for what this
   project ships.** A `v*` tag asserts a human reviewed the change set, a human
   manually tested it against its real runtime, and deterministic automated
   validation passed. Keeping the default branch clean is what makes cutting
   one cheap.
   **Never request a review**, and add the person who asked for the work as
   **assignee**. Reviewers are named at the tag, by the human cutting it. A
   review request pulls a second person into work that asserts nothing yet, and
   against a branch carrying a live `CODEOWNERS` it fires the moment the PR
   opens — you name no one, and the notification cannot be recalled.
   **Draft means unfinished, and nothing else.** It is not a holding pen for
   finished work: a green PR left in draft is a change that never landed.
   **Keep it to one open PR per repository, per contributor.** Not one per
   task. This is a sequencing constraint — two PRs that must merge in a given
   order are a puzzle — and not a bandwidth one, since a green PR frees its own
   slot. Land the upstream change first and let propagation carry it.
   `.github/workflows/one-pr-check.yml` enforces this; run
   `governance/qm/project-seed/ci/check_one_pr.py` before you open anything.
4. **Human-only contributorship applies to every commit you make here** (see
   `governance/qm/records/DRAFT-human-only-contributorship.md`): do not add
   yourself, your model name, or any co-author trailer naming an unmonitored
   address (e.g. a vendor `noreply@` address) to any commit. If your default
   tooling normally appends a `Co-Authored-By:` trailer, suppress it for
   this repo. Tool involvement is disclosed as a `Tools:` note where the
   artifact calls for one, never as a byline.
5. Follow the drafting-session handoff contract in
   `governance/qm/adr/README.md` before writing or amending any record.
6. A QM record may be tightened by this project's own records, never
   relaxed — see `governance/qm/docs/ref/precedence.md`.
7. **Put explanation in one place**, per
   `governance/qm/handbook/style-guide.md`: inline comments carry clarifying
   facts about the code, `README.md` is a shallow onramp to the docs, `docs/`
   is reference, and **every why goes to a retrospective in
   `governance/qm/perspectives/`**. A record's Context and Alternatives are
   the one exception, answering *why this decision* rather than *why it went
   that way*.
8. Banned in any pre-ratification `DRAFT-*.md` record: "previously",
   "originally", "earlier draft", "re-review", "renumber", "retroactive",
   "supersedes the ... (stance|finding)", "corrected". Drafts are rewritten
   in place, not narrated. The ADR lint enforces this over prose only, so
   quoting the list in a code span is fine.
9. **Establish a fact before asserting it, and check a signal before reading
   it.** A claim that something is broken, unsupported or behaves a certain way
   carries the command you ran and what it returned. Before reporting what a
   result means, name one other thing that would produce the same output — a
   tool version, a flag's semantics, stale local state, the working directory,
   a substring matching prose. An unexpected uniform result is a tooling fault
   until shown otherwise, and a check that has only ever been seen green has
   not been tested: break the thing it names and watch it go red.
10. **A claim about what facts *mean* names what else could produce them.**
    This is the sibling of the rule above and catches a different failure: the
    facts are all true and the sentence built from them is wrong. Name the
    ordinary cause before the interesting one — same author, same source, same
    tooling, same period — and state direction and date, because "A resembles
    B" is symmetric and the useful version rarely is. **A correction carries
    the same burden as the claim it replaces**: an overclaim gets caught by a
    reader who knows better, while a deflation reads as rigour, closes the
    topic, and can quietly delete something real. See
    `governance/qm/records/DRAFT-decision-record-discipline.md` §7 and §8.
11. **The scaffolding you measure with is part of the measurement.** Item 9 is
    the tool answering a different question than you asked. This is the tool
    being fine and the setup not — nothing errors, and the result describes your
    own scaffolding rather than the subject. Real instances: a diff run against
    files a redirect never wrote, reported as a hundred lines of drift when the
    truth was none; a working tree read after a merge that exited non-zero; file
    copies written through a text API that converted every line ending, so the
    diff was entirely encoding; a mutation test whose baseline was already
    failing, so it proved nothing in either direction. **Prefer the artefact you
    did not create** — read a document's own answer instead of recomputing one —
    and assert the intermediate: non-empty, exit zero, baseline green.
12. **A guard is not finished until someone has tried to route around it.**
    Breaking it and watching it go red proves it fires on the case you thought
    of; it cannot find the case you did not. Ask for a pass whose brief is to
    satisfy the check while doing the thing it forbids. A guard with a hole is
    worse than no guard — it is a green check standing exactly where a reader
    believes something is enforced. See the same record's §9 and §10.

13. **Show it by running it** — P12 of the charter, with
    `governance/qm/records/DRAFT-one-executable-walkthrough.md` as the record.
    This project's `walkthrough/` is one ordered set of pages that the ordinary
    test command executes: `walkthrough/NN-<slug>.md`, run by pytest with
    `--doctest-glob=*.md`. The example a reader reads is the example that ran.
    Do not write a second copy of a behaviour beside the code — no prose example
    that is not executed, no screenshot that is not a byproduct of a test
    asserting what the code did. What text cannot hold is emitted by that test
    and **recorded, never compared**: a test that diffs images fails on a font
    and gets switched off. Regeneration rides the command you already run before
    a pull request, so drift shows up as an uncommitted diff rather than as
    staleness nobody sees. A skip is not a pass, and a page that always skips is
    deleted.

## One-time setup on a fresh clone (Windows)

`CLAUDE.md` and `.github/copilot-instructions.md` are real symlinks to this
file, not copies — POSIX checkouts resolve them with no setup. On Windows,
enable Developer Mode (Settings → For developers) and run `git config
core.symlinks true` once per clone, then `git checkout -- .` if the files
were already checked out before that. Skipping this doesn't break
anything — the files degrade to one-line pointers containing just the
target path — but it isn't the intended, tested experience; see the
IDE-integrated governance discovery record in `governance/qm/records/` for
what was actually verified.

<!-- Project-specific setup commands, test commands, and conventions belong
     below this line; this seed only carries the governance-discovery part. -->

## What this project is

looksatwords reads natural language and says what was in it: who spoke, which
topics were live and when, where a conversation went off and whether it came
back, and what the sentiment did along the way. The input is prose — a
conversation transcript, a gathered news article, a generated one. The output
is structure over that prose.

**It is not a code tool.** `codecartographer` maps source code as graphs and
this maps language as threads; both draw a picture of a corpus and the corpus
is the whole difference. A change here that starts parsing Python is a change
that belongs there.

## Setup

```sh
uv sync
uv run looksatwords serve --no-open      # http://127.0.0.1:8000, API docs at /docs
```

Generation needs a local Ollama. **The host is not a setting and the model is.**
`looksatwords/llm.py` holds both: `HOST` is loopback because a client that could
be pointed at another machine is how "generated on this machine" stops being
true, and `MODEL` reads `LOOKSATWORDS_OLLAMA_MODEL` because which model a box
has pulled is that box's business.

```sh
LOOKSATWORDS_OLLAMA_MODEL=qwen2.5-coder:7b uv run looksatwords serve --no-open
```

## Tests

```sh
uv run pytest -m "not e2e"               # the default suite
uv run pytest -m e2e                     # browser tests; needs `playwright install`
uv run pytest -m llm                     # reaches a live Ollama on loopback
```

`testpaths` is `looksatwords/tests` and `norecursedirs` names `governance`.
Both are load-bearing: the vendored corpus carries its own suite, which asserts
against the corpus root as the working directory, and an unbounded `pytest`
here collects those and reports red for files this repository does not own.
`norecursedirs` is the half that still holds when pytest is handed an explicit
path, which is what makes `testpaths` inert.

**Read a skip before reading the summary.** `test_generator` is the one test
that talks to a live model. When Ollama is down, or is up without the model
this project asks for, it skips with the reason and the command that fixes it.
That is the "nobody could look" answer and it is not a pass.

## Gates

```sh
uv run python governance/qm/project-seed/ci/run_workflows_locally.py
```

Six workflows are copied verbatim from `governance/qm/project-seed/ci/` —
adr-lint, one-pr-check, reuse-lint, signature-check, submodule-check,
tag-claims. Only the YAML is copied; each runs a script out of the submodule,
so a fix to a rule arrives on the next pin bump rather than needing this copy
edited.

`reuse-lint`'s install step fails under the local runner because this project's
uv-managed venv has no `pip`. The lint itself is fine —
`uvx --with charset-normalizer reuse lint` passes — so that one line is an
environment difference and not a finding.
