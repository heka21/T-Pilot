"""The content gates run under pytest: completeness and visuals (hard), lesson format (advisory)."""
from __future__ import annotations

import stat
from pathlib import Path

import pytest

from app.seed import check_content, lint_lessons

ROOT = Path(__file__).resolve().parent.parent


def test_check_content_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert check_content.main([]) == 0
    assert "PROBLEM" not in capsys.readouterr().out


def test_lint_lessons_runs(capsys: pytest.CaptureFixture[str]) -> None:
    assert lint_lessons.main([]) == 0
    assert "total study minutes" in capsys.readouterr().out


def test_content_files_world_readable() -> None:
    # The image runs as a non-root user; a file only its owner can read
    # makes the app fail at startup.
    unreadable = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "content").rglob("*")
        if p.is_file() and not p.stat().st_mode & stat.S_IROTH
    ]
    assert unreadable == []
