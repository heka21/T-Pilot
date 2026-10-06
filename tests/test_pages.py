"""Page-level tests for syllabus, notes, progress, reference and dashboard."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.routers.reference import list_pages

REFERENCE_SLUGS = ["exam-formats", "permitted-materials", "exam-day-checklist", "workbook", "sources-and-disclaimer"]


def test_syllabus(client: TestClient) -> None:
    r = client.get("/syllabus")
    assert r.status_code == 200
    assert "RPLA" in r.text and "PPLA" in r.text
    assert "/syllabus/unit/RBKA" in r.text


def test_unit_page(client: TestClient) -> None:
    r = client.get("/syllabus/unit/RBKA")
    assert r.status_code == 200
    assert "Stalling" in r.text
    assert "/progress/RBKA%203.6" in r.text
    assert "/lessons/RBKA/3.6" in r.text


def test_shared_unit_mentions_both_exams(client: TestClient) -> None:
    r = client.get("/syllabus/unit/PHFC")
    assert r.status_code == 200
    assert "RPLA" in r.text and "PPLA" in r.text


def test_unknown_unit_404(client: TestClient) -> None:
    assert client.get("/syllabus/unit/NOPE").status_code == 404
    assert client.get("/syllabus/subtopic/RBKA/99.9").status_code == 404


def test_subtopic_page(client: TestClient) -> None:
    r = client.get("/syllabus/subtopic/RBKA/3.6")
    assert r.status_code == 200
    assert "3.6.2" in r.text
    assert "/quiz?subtopic=RBKA%203.6" in r.text
    assert "/cards?subtopic=RBKA%203.6" in r.text


def test_note_page(client: TestClient) -> None:
    r = client.get("/lessons/RBKA/3.6")
    assert r.status_code == 200
    assert "critical angle" in r.text
    assert "<details" in r.text and "3.6.2" in r.text
    assert "In this lesson" in r.text and 'href="#' in r.text
    # Reading experience: progress target, side panel with tabs, text-size control, pre-paint font size.
    for marker in ("data-read-target", "data-lesson-panel", 'role="tablist"', 'data-panel-tab="notes"',
                   'data-panel-tab="sketch"', 'data-font-size="xl"', "data-read-progress"):
        assert marker in r.text, marker
    assert 'localStorage.getItem("fontsize")' in r.text
    # Student annotations: ink/highlight host with its embedded bundle, and the Notes and Sketch panel partials.
    for marker in ('data-widget="lesson-annotations"', 'data-widget="lesson-notes"', 'data-widget="lesson-sketch"',
                   "data-annotations", 'class="notes-editor"', "sketch-dialog"):
        assert marker in r.text, marker


def test_missing_note_is_200(client: TestClient) -> None:
    # The brief named BAKC 2.1, but notes are being written over time: pick any subtopic still without one.
    from sqlalchemy import select

    from app.db import SessionLocal
    from app.models import Subtopic

    with SessionLocal() as s:
        sub = s.scalar(select(Subtopic).where(~Subtopic.note.has()).order_by(Subtopic.position))
        if sub is None:
            return  # every subtopic has a note
        url = f"/lessons/{sub.unit_code}/{sub.number}"
    r = client.get(url)
    assert r.status_code == 200
    assert "not written yet" in r.text.lower()
    assert "data-lesson-panel" not in r.text


def test_notes_index(client: TestClient) -> None:
    r = client.get("/lessons")
    assert r.status_code == 200
    assert "/lessons/RBKA/3.6" in r.text


def test_lessons_filter_bar(client: TestClient) -> None:
    r = client.get("/lessons?q=stall&exam=RPLA&status=bogus")
    assert r.status_code == 200
    assert 'value="stall"' in r.text and 'name="exam" value="RPLA" checked' in r.text
    assert 'name="status" value="" checked' in r.text  # unknown status falls back to any
    assert 'data-text="rbka 3.6 rbka3.6 stalling' in r.text
    assert 'data-unit-link="PHFC" data-exams="RPLA PPLA"' in r.text  # shared unit shows under both exams


def test_set_status_roundtrip(client: TestClient) -> None:
    r = client.post("/progress/RBKA%203.6", data={"status": "confident"}, headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert 'status-badge status-confident' in r.text
    r = client.get("/syllabus/unit/RBKA")
    assert "confident" in r.text
    assert 'status-badge status-confident' in r.text
    client.post("/progress/RBKA%203.6", data={"status": "not_started"}, headers={"HX-Request": "true"})


def test_set_status_rejects_bad_input(client: TestClient) -> None:
    assert client.post("/progress/RBKA%203.6", data={"status": "bogus"}).status_code == 400
    assert client.post("/progress/NOPE%201.1", data={"status": "studying"}).status_code == 404


def test_progress_page(client: TestClient) -> None:
    r = client.get("/progress")
    assert r.status_code == 200
    assert "RBKA" in r.text


def test_reference_pages(client: TestClient) -> None:
    r = client.get("/reference")
    assert r.status_code == 200
    slugs = [p["slug"] for p in list_pages()]
    for slug in REFERENCE_SLUGS:
        assert slug in slugs
        assert f"/reference/{slug}" in r.text
        page = client.get(f"/reference/{slug}")
        assert page.status_code == 200, slug
    assert client.get("/reference/does-not-exist").status_code == 404


def test_reference_page_has_reading_tools(client: TestClient) -> None:
    r = client.get(f"/reference/{REFERENCE_SLUGS[0]}")
    assert r.status_code == 200
    assert 'data-font-size="xl"' in r.text and "data-read-target" in r.text


def test_quiz_page_has_text_size_but_partial_does_not(client: TestClient) -> None:
    r = client.post("/quiz/start", data={"units": ["RBKA"], "count": "5"}, follow_redirects=False)
    assert r.status_code == 303
    page = client.get(r.headers["location"])
    assert page.status_code == 200
    assert 'data-font-size="xl"' in page.text
    partial = client.get(r.headers["location"] + "/q/0", headers={"HX-Request": "true"})
    assert partial.status_code == 200
    assert 'id="quiz-question"' in partial.text and "data-font-size=" not in partial.text


def test_plain_pages_have_progress_bar_but_no_text_size(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "data-read-progress" in r.text
    assert "data-font-size=" not in r.text


def test_dashboard(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "RPLA" in r.text
    assert "<progress" in r.text or 'class="stack-bar"' in r.text  # some kind of progress indicator
    assert "Cards due" in r.text


def test_dashboard_with_plan(client: TestClient) -> None:
    from app.db import SessionLocal
    from app.services import planner

    with SessionLocal() as s:
        plan = planner.generate(s, planner.default_settings())
        plan_id = plan.id
    try:
        r = client.get("/")
        assert r.status_code == 200
        assert "Today" in r.text
        assert "exam in" in r.text
    finally:
        from app.models import StudyPlan
        with SessionLocal() as s:
            s.delete(s.get(StudyPlan, plan_id))
            s.commit()


def test_dashboard_start_here_without_plan(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "Start here" in r.text
    assert "Read the next lesson" in r.text
    assert "/lessons/BAKC/2.1" in r.text  # first subtopic in syllabus order, nothing studied yet


def test_old_notes_urls_redirect(client: TestClient) -> None:
    r = client.get("/notes/RBKA/3.6", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"] == "/lessons/RBKA/3.6"
    r = client.get("/notes", follow_redirects=False)
    assert r.headers["location"] == "/lessons"
