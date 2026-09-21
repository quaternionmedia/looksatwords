"""This reader's own port is a second copy of an allocation the corpus owns.

The governance corpus allocates one port per server on the workstation, in the
SURFACES table of its `ci/dashboard.py`, so that no two collide. This project
cannot import that file -- the corpus is not a dependency and its interpreter
has none of this project's -- so `DEFAULT_PORT` is a copy, and this is the only
thing that keeps a copy true. It follows `test_harness.py`, which does the same
for the harness's port against qmcp's own config.

MUTATED ON 2026-09-20 AND SEEN RED. Setting `DEFAULT_PORT` to 8000 failed the
allocation test against a sibling table naming 1414; making the option's default
the value instead of the function failed the command-time test, which saw the
allocation where it had set 9009. Restored, all pass.
"""

import pathlib
import re

import pytest
from click.testing import CliRunner

from looksatwords import __main__ as main
from looksatwords.__main__ import DEFAULT_PORT, cli, default_port


# ==================== The copied constant ====================

def _dashboard() -> pathlib.Path | None:
    """The corpus's own allocation table, if a sibling clone is on this machine."""
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "qm" / "ci" / "dashboard.py"
        if candidate.exists():
            return candidate
    return None


def test_the_default_port_is_the_corpus_allocation():
    """`DEFAULT_PORT` equals the port the SURFACES entry for this repository names.

    A SKIP HERE IS NOT A PASS. Without the sibling clone nobody can check, and
    the skip says so rather than letting the suite imply the two agree. The
    same holds when the sibling is there but has no row for this repository
    yet: that is a table at an older commit, not a disagreement.
    """
    dashboard = _dashboard()
    if dashboard is None:
        pytest.skip(
            "No sibling qm clone on this machine, so the port the corpus allocates "
            "to looksatwords could not be read. This test did not run; it did not pass."
        )

    text = dashboard.read_text(encoding="utf-8")
    m = re.search(r'repo="looksatwords".*?port=(\d+)', text, re.DOTALL)
    if not m:
        pytest.skip(
            f"{dashboard} has no SURFACES entry for looksatwords, so there is no "
            "allocation to compare against. This test did not run; it did not pass."
        )
    assert int(m.group(1)) == DEFAULT_PORT, (
        f"{dashboard} allocates {m.group(1)} to looksatwords and this project "
        f"binds {DEFAULT_PORT}. The corpus's dashboard would report this reader "
        "as not running while it was answering on another port."
    )


# ==================== The override, resolved when the command runs ====================

def test_the_environment_moves_the_port(monkeypatch):
    monkeypatch.delenv("LOOKSATWORDS_PORT", raising=False)
    assert default_port() == DEFAULT_PORT
    monkeypatch.setenv("LOOKSATWORDS_PORT", "9009")
    assert default_port() == 9009


def test_serve_reads_the_override_at_command_time(monkeypatch):
    """The option's default is the function, so a variable set after import still counts.

    `_run_server` is replaced so nothing binds; what is asserted is the port
    the command would have handed it.
    """
    seen = {}
    monkeypatch.setattr(main, "_run_server", lambda host, port, reload, open_browser: seen.update(port=port))

    monkeypatch.setenv("LOOKSATWORDS_PORT", "9009")
    result = CliRunner().invoke(cli, ["serve", "--no-open"])
    assert result.exit_code == 0, result.output
    assert seen["port"] == 9009

    # A flag beats the variable, which beats the allocation.
    result = CliRunner().invoke(cli, ["serve", "--no-open", "--port", "9010"])
    assert result.exit_code == 0, result.output
    assert seen["port"] == 9010

    monkeypatch.delenv("LOOKSATWORDS_PORT")
    result = CliRunner().invoke(cli, ["serve", "--no-open"])
    assert result.exit_code == 0, result.output
    assert seen["port"] == DEFAULT_PORT


def test_help_names_the_default_so_nobody_has_to_read_the_source():
    result = CliRunner().invoke(cli, ["serve", "--help"])
    assert result.exit_code == 0
    assert str(DEFAULT_PORT) in result.output
    assert "LOOKSATWORDS_PORT" in result.output
