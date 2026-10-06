"""The equation sheet: content/equations.yaml, the seeded tables, /equations, search and the content checks."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import Equation, Subtopic
from app.seed import check_content
from app.seed.equations import EQUATIONS_FILE, katex_inputs, load_equations
from app.services import search as svc
from tests._db import CONTENT, fresh_session

ROOT = Path(__file__).resolve().parent.parent
DATA = load_equations(CONTENT / EQUATIONS_FILE)


def test_load_equations_reads_the_file() -> None:
    assert DATA["topics"] and DATA["equations"]
    eq = next(e for e in DATA["equations"] if e["id"] == "stall-speed-in-turn")
    assert eq["exams"] == ["RPLA"] and eq["lessons"][0] == "RBKA 3.5"
    assert all({"sym", "meaning", "unit"} <= set(s) for e in DATA["equations"] for s in e["symbols"])
    assert load_equations(CONTENT / "no-such-file.yaml") == {"topics": [], "equations": []}


def test_every_equation_seeded_with_lessons() -> None:
    session = fresh_session()
    rows = list(session.scalars(select(Equation).order_by(Equation.position)))
    assert [e.id for e in rows] == [e["id"] for e in DATA["equations"]]
    by_id = {e["id"]: e for e in DATA["equations"]}
    for row in rows:
        assert row.lesson_ids == by_id[row.id]["lessons"]
        assert all(session.get(Subtopic, sid) is not None for sid in row.lesson_ids)
    # Inline maths in `when` comes out as \( \) for KaTeX, without the wrapping <p>.
    stall = session.get(Equation, "stall-speed-in-turn")
    assert r'<span class="arithmatex">\(' in stall.when_html and not stall.when_html.startswith("<p>")
    # The per-lesson relationship, in sheet order.
    lesson = session.get(Subtopic, "RBKA 3.6")
    assert [e.id for e in lesson.equations] == [e["id"] for e in DATA["equations"] if "RBKA 3.6" in e["lessons"]]


def test_equations_page(client: TestClient) -> None:
    r = client.get("/equations")
    assert r.status_code == 200
    for e in DATA["equations"]:
        assert f'id="eq-{e["id"]}"' in r.text
    assert "data-maths" in r.text and "equations-sheet" in r.text and "window.print()" in r.text
    assert "/lessons/RBKA/3.6" in r.text
    assert 'href="/equations"' in r.text  # the sidebar link


def test_equations_filters_prefill(client: TestClient) -> None:
    r = client.get("/equations", params={"exam": "PPLA", "topic": "navigation", "q": " density "})
    assert r.status_code == 200
    assert 'exam: "PPLA", topic: "navigation", q: "density"' in r.text
    assert 'value="density"' in r.text
    assert 'value="PPLA" x-model="exam" checked' in r.text
    assert 'value="navigation" x-model="topic" checked' in r.text
    r = client.get("/equations", params={"exam": "bogus", "topic": "bogus"})
    assert 'exam: "", topic: "", q: ""' in r.text


def test_equations_in_search() -> None:
    session = fresh_session()
    res = svc.search(session, "density height", "content", kind="equation")
    hit = res["groups"][0]["hits"][0]
    assert hit.entry.url == "/equations#eq-density-height"


def test_check_equations_flags_bad_records(tmp_path: Path) -> None:
    bad = {
        "topics": [{"id": "aerodynamics", "label": "Aerodynamics"}, {"id": "aerodynamics", "label": "Again"}],
        "equations": [
            {"id": "Bad Id", "name": "x", "topic": "nope", "latex": r"\frac{a}{b", "when": "x", "exams": ["CPL"],
             "lessons": ["RBKA 99.9"], "see_also": ["missing"], "colour": "red"},
            {"id": "ppl-only", "name": "y", "topic": "aerodynamics", "latex": r"\left( x", "when": "y",
             "exams": ["RPLA"], "lessons": ["PNVC 2.4"]},
        ],
    }
    path = tmp_path / "equations.yaml"
    path.write_text(json.dumps(bad), encoding="utf-8")  # JSON is YAML
    subtopics, _ = check_content.load_syllabus()
    problems: list[str] = []
    warnings: list[str] = []
    check_content.check_equations(subtopics, problems, warnings, path)
    text = "\n".join(problems)
    for expected in ["duplicate topic id aerodynamics", "not a lower-case slug", "unknown topic 'nope'", "RPLA and/or PPLA",
                     "unknown lessons ['RBKA 99.9']", "see_also 'missing'", "unknown keys ['colour']", "unbalanced {",
                     "claims RPLA but no linked lesson", "outside its exams", "\\left without a \\right"]:
        assert expected in text, expected


def test_equations_katex() -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not on PATH")
    res = subprocess.run([node, str(ROOT / "tools" / "equations" / "katex-check.mjs")],
                         input=json.dumps(katex_inputs(DATA)), capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, res.stdout + res.stderr
