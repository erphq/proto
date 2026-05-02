"""CLI smoke tests via Typer's ``CliRunner``.

These do not exercise the LLM provider or the ClickHouse client — that
would require a real model server and a real database. They check that
the Typer app is wired up correctly: subcommands resolve, ``--help``
works on each, and the version flag returns a sane string. The goal
is to catch import-time breakage and command-registration regressions
that would otherwise only surface in the user's first session.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from main import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCliSurface:
    def test_help_returns_zero(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_help_lists_documented_subcommands(self, runner: CliRunner) -> None:
        # Spot-check the subcommands that are part of the documented
        # surface — a rename on any of these is a user-visible
        # breaking change and should fail this test.
        result = runner.invoke(app, ["--help"])
        for cmd in ("chat", "query", "analyze", "load-data", "settings", "version"):
            assert cmd in result.output, f"subcommand '{cmd}' missing from help"

    @pytest.mark.parametrize(
        "cmd",
        ["chat", "query", "analyze", "load-data", "settings", "clear", "version"],
    )
    def test_subcommand_help_returns_zero(self, runner: CliRunner, cmd: str) -> None:
        result = runner.invoke(app, [cmd, "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_version_subcommand_returns_zero(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0

    def test_unknown_subcommand_returns_nonzero(self, runner: CliRunner) -> None:
        # Belt-and-braces: Typer normally returns 2 for unknown
        # commands. If a future change swallows the error and exits 0,
        # this test catches it.
        result = runner.invoke(app, ["definitely-not-a-real-command"])
        assert result.exit_code != 0
