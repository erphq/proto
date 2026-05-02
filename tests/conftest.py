"""Shared pytest fixtures.

The biggest hazard for clickr's test suite is the ambient environment:
``load_config`` reads ``CLICKHOUSE_*`` and ``OPENROUTER_*`` env vars and
also probes for a default config file under ``~/.config/proto/``. Both
make tests order-dependent and machine-dependent. The fixtures here
sandbox each test from both.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import pytest

_RELEVANT_PREFIXES = ("CLICKHOUSE_", "OPENROUTER_")


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Strip clickr-relevant env vars and point ``$HOME`` at a temp dir.

    Every test runs against an empty environment for the prefixes that
    ``load_config`` reads, and against a fresh ``$HOME`` so the
    ``~/.config/proto/proto-config.json`` probe never finds the real
    user's config. Without this, a developer who has clickr configured
    locally would see different test results than CI.
    """
    for key in list(os.environ):
        if key.startswith(_RELEVANT_PREFIXES):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    yield


@pytest.fixture
def cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run the test from a clean temp working directory.

    ``load_config`` also probes for a legacy ``proto-config.json`` in the
    current directory. Tests that exercise the file-discovery logic want
    a known empty cwd.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path
