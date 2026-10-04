"""Lesson format tooling: reveal boxes, callouts, reading-time estimate, lesson TOC, lesson lint."""
from __future__ import annotations

from pathlib import Path

from app.seed import check_content, loader
from app.seed.lint_lessons import lint_body
from app.routers.notes import lesson_toc
from tests._db import fresh_session

LESSON = """## What the exam expects (RBKA 3.6)

- **3.6.1** Explain the stall.

## Why this matters

Text. ![Why?](diagram:stall-speed-vs-bank "Notice.")

## The stall

!!! example "Worked example"
    $V_s = 50$ kt.

??? check "Check yourself: what is the critical angle?"
    About 16 degrees.

??? check "Check yourself: two"
    Two.

??? check "Check yourself: three"
    Three.

## Key points

- One.

!!! tip "Exam tip"
    Tip.
"""


def test_details_and_example_render_with_classes() -> None:
    html = loader.render_markdown('??? check "Q"\n    A $x^2$\n\n!!! example "Worked example"\n    s\n\n## Heading here\n')
    assert '<details class="check">' in html and "<summary>Q</summary>" in html
    assert 'class="arithmatex"' in html
    assert '<div class="admonition example">' in html
    assert '<h2 id="heading-here">' in html


def test_estimate_minutes_model() -> None:
    body = "word " * 1000
    assert loader.estimate_minutes(body) == 10
    assert loader.estimate_minutes(body + "\n![c](diagram:x)\n") == 12
    assert loader.estimate_minutes(body + "\n![c](widget:x)\n") == 15
    assert loader.estimate_minutes(body + '\n!!! example "W"\n    s\n??? check "Q"\n    a\n') == 10 + 2 + 1 + 1  # 'a' and 's' add a minute
    assert loader.estimate_minutes("") == loader.MIN_MINUTES
    assert loader.word_count('![a b c](diagram:x "d e")\n!!! tip "Exam tip"\n    one two\n') == 2


def test_seed_notes_uses_override_or_estimate(tmp_path: Path) -> None:
    notes = tmp_path / "notes" / "RBKA"
    notes.mkdir(parents=True)
    body = "## What the exam expects (RBKA 3.6)\n\n- **3.6.1** x\n\n" + "word " * 500
    (notes / "3.6-a.md").write_text(f"---\nsubtopic: RBKA 3.6\ntitle: A\n---\n{body}", encoding="utf-8")
    (notes / "3.7-b.md").write_text(f"---\nsubtopic: RBKA 3.7\ntitle: B\nminutes: 7\n---\n{body}", encoding="utf-8")
    s = fresh_session()
    loader.seed_notes(s, tmp_path / "notes")
    from app.models import Note
    assert s.get(Note, "RBKA 3.6").minutes == loader.estimate_minutes(body)
    assert s.get(Note, "RBKA 3.7").minutes == 7
    s.rollback()


def test_lesson_toc_strips_tags() -> None:
    toc = lesson_toc('<h2 id="a">A <em>b</em> &amp; c</h2><p>x</p><h2 id="c-d">C</h2>')
    assert toc == [{"id": "a", "text": "A b & c"}, {"id": "c-d", "text": "C"}]


def test_expects_section_tolerates_intro_and_reports_missing() -> None:
    body = "An intro paragraph.\n\n## What the exam expects (X 1.1)\n\n- **1.1.1** a\n\n## Next\n\n1.1.2 should not count\n"
    section = check_content.expects_section(body)
    assert section is not None and "1.1.1" in section and "1.1.2" not in section
    assert check_content.expects_section("## Something else\n") is None


def test_lint_body_on_synthetic_lessons() -> None:
    full = LESSON.replace("Text.", "word " * 2100)
    assert lint_body(full, ["Calculate the stall speed"], {}) == []
    bare = "## What the exam expects (RBKA 3.6)\n\n- **3.6.1** x\n\nshort\n"
    problems = lint_body(bare, ["Calculate the stall speed"], {"minutes": 90})
    joined = "\n".join(problems)
    for needle in ("short lesson", "self-check", "Worked example", "Why this matters", "Key points", "no diagram", "minutes 90"):
        assert needle in joined, needle
    assert "unknown admonition type `!!! danger`" in "\n".join(lint_body(full + '\n!!! danger "x"\n    y\n', [], {}))
