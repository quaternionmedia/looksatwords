# Open questions

What this project is waiting on a person for, and what a reader should not
mistake for settled. Governance conflicts live in the adoption record on the
corpus's `project/looksatwords` branch and are referenced by number here rather
than restated — `governance/qm/adr/`.

Established on 2026-08-26 against `looksatwords` at the tip of
`feat/adopt-the-governance-corpus`. Each row names the command or file that
established it, because a question nobody reproduced is an opinion.

## Blocking the adoption record

The record is `Proposed` and pends on the first two.

| | question | established by |
|---|---|---|
| **C1** | Copyright is asserted in an individual; the org's outbound-licensing record places it in Quaternion Media. Which holds? | `LICENSE` line 3, `pyproject.toml`'s `authors`, `REUSE.toml`'s `**` block — all three say the same thing and all three would change together |
| **C2** | MIT is declared as an identifier. The outbound *class* it implies is not declared anywhere. | `pyproject.toml` `license = {text = "MIT"}` |
| **C3** | `anime.js` 3.2.1 is fetched from `cdnjs.cloudflare.com` at page load. There is no `package.json` in the repository, so no manifest, no gate, and REUSE cannot see it. Vendor it, or introduce the manifest? | `looksatwords/frontend/index.html` line 9; `find . -name package.json` outside `.venv` returns nothing |

C3 decides a second thing worth deciding on purpose: the thread visualisation's
reveal animation depends on that script. The page degrades rather than breaking,
but "the demo works" is today a claim about a machine with network access.

## Cleanup found and deliberately not done

Each of these is a judgement about intent, which is why none of them were
actioned.

| | question | established by |
|---|---|---|
| 1 | `looksatwords/frontend/vite.config.js` configures a build nothing can run: no `package.json` exists to install vite, and nothing references the file. Delete, or wire it up? | `grep -rn vite` finds only the file's own import line |
| 2 | Nine of the twenty-two runtime dependencies are development tooling — pytest and five plugins, playwright, ruff, ipykernel — with no `optional-dependencies` and no `dependency-groups`. Anyone installing this package gets playwright. Move them? | `pyproject.toml` |
| 3 | `visualizer.js` and `visualizer.html` are the pre-modular UI. They are still mounted as static files and still carry the largest block of tests in `test_frontend.py`, and nothing in `index.html` links them. Retire, or keep as a supported second entry point? | `looksatwords/app/main.py` mounts them; `grep` finds no link from `index.html` |
| 4 | The development database holds conversations written by an assistant session while demonstrating the analysis path, alongside at least one a person made. Nothing distinguishes them. Should demo runs use a scratch database? | `GET /api/conversations` |

## Not questions, but do not read them as settled

- **The tag gate has never run.** `tag-claims.yml` is wired and
  `run_workflows_locally.py` reports it skipped — it is not triggered by
  `pull_request`. The first tag is what exercises it.
- **`reuse-lint`'s install step fails under the local runner** because this
  project's uv-managed venv has no `pip`. The lint itself passes
  (`uvx --with charset-normalizer reuse lint`). That line is an environment
  difference, not a finding, and it will behave differently on a runner.
- **No service inventory and no baseline component audit exist.** They are C4
  in the adoption record. Nothing generates either.
