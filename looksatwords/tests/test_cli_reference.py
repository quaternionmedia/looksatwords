"""`docs/cli.md` and the CLI agree, in both directions.

WHY THIS EXISTS, WITH THE NUMBERS THAT PRODUCED IT. On 2026-08-27 the command
reference documented `gather`, `analyze`, `visualize` and `version` — four
commands the CLI does not have — and omitted six it does. Nothing was obviously
wrong on the page: it was well written, consistently formatted, and had been
read by people who then ran commands that did not exist.

Prose describing behaviour in a second place drifts, and the drift is invisible
at any single commit. The pictures in `docs/pics/` have the same problem and are
guarded the same way. Neither guard needs a browser or a server.

BOTH DIRECTIONS, BECAUSE ONLY ONE OF THEM IS OBVIOUS. A missing command gets
noticed the first time somebody looks for it. A *documented* command that does
not exist is found only by typing it.

BOTH WERE MUTATED ON 2026-08-27 AND BOTH WENT RED. Adding a `teleport` row
failed `test_every_documented_command_exists`; deleting the `doctor` row failed
`test_every_command_is_documented`. Restored, thirty-four pass.
"""

import pathlib
import re

import pytest
from click.testing import CliRunner

from looksatwords.__main__ import cli

DOC = pathlib.Path(__file__).resolve().parent.parent.parent / "docs" / "cli.md"

TABLE = re.compile(
    r"<!-- COMMANDS:.*?-->(.*?)<!-- END COMMANDS -->", re.DOTALL
)


def _documented() -> set[str]:
    """The commands named in the quick-reference table."""
    m = TABLE.search(DOC.read_text(encoding="utf-8"))
    assert m, (
        "the COMMANDS markers are missing from docs/cli.md, so this guard has "
        "nothing to read. Restore them rather than deleting this test."
    )
    return set(re.findall(r"^\|\s*`([^`]+)`\s*\|", m.group(1), re.MULTILINE))


def _real() -> set[str]:
    """The commands the CLI actually registers, hidden ones excluded."""
    return {
        name for name, command in cli.commands.items()
        if not getattr(command, "hidden", False)
    }


def test_the_guard_can_read_both_sides():
    """Guard the guard: an empty set on either side passes everything below."""
    documented, real = _documented(), _real()
    assert documented, "no commands were parsed out of docs/cli.md's table"
    assert real, "no commands were found on the CLI"


@pytest.mark.parametrize("name", sorted(_real()))
def test_every_command_is_documented(name):
    assert name in _documented(), (
        f"`{name}` exists on the CLI and is not in docs/cli.md's quick reference."
    )


@pytest.mark.parametrize("name", sorted(_documented()))
def test_every_documented_command_exists(name):
    assert name in _real(), (
        f"docs/cli.md documents `{name}` and the CLI has no such command. "
        "Somebody following this page would type it and get an error."
    )


@pytest.mark.parametrize("name", sorted(_real()))
def test_every_command_answers_help(name):
    """A command in the reference that cannot even print its own help.

    Cheap, and it catches an import error or a bad decorator in a command
    nothing else in the suite invokes.
    """
    result = CliRunner().invoke(cli, [name, "--help"])
    assert result.exit_code == 0, (
        f"`looksatwords {name} --help` exited {result.exit_code}:\n{result.output}"
    )
    assert "Usage:" in result.output
