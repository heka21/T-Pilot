"""Student notes, highlights and Pencil ink: the JSON API, /my-notes, the export and global search."""
from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.models import Highlight, InkDocument, StudentNote
from app.services import annotations as svc

SID = "RBKA 3.6"
BASE = f"/annotations/{quote(SID)}"


def _clear() -> None:
    with SessionLocal() as s:
        for model in (StudentNote, Highlight, InkDocument):
            s.execute(delete(model))
        s.commit()


@pytest.fixture(autouse=True)
def clean_annotations(client: TestClient) -> Iterator[None]:
    """The test DB is shared across the run: start and end every test with no annotations."""
    _clear()
    yield
    _clear()


def _highlight(**over) -> dict:
    return {"colour": "yellow", "exact": "the critical angle of attack", "prefix": "exceeds ", "suffix": " and the",
            "start": 120, "end": 148, "block_id": "what-is-a-stall"} | over


def _stroke(points: int = 3) -> dict:
    return {"id": "s1", "c": "ink-1", "w": 3, "pts": [[0.1, 0.2, 0.5]] * points}


def test_bundle_starts_empty(client: TestClient) -> None:
    r = client.get(BASE)
    assert r.status_code == 200
    data = r.json()
    assert data["sid"] == SID and data["note"] == "" and data["highlights"] == []
    assert data["ink"]["lesson"]["rev"] == 0 and data["ink"]["lesson"]["strokes"] == [] and data["ink"]["sketch"] == []


def test_note_round_trip_and_empty_deletes(client: TestClient) -> None:
    r = client.post(f"{BASE}/note", json={"text": "Stall = critical AoA, not speed."})
    assert r.status_code == 200 and r.json()["updated_at"]
    assert client.get(BASE).json()["note"] == "Stall = critical AoA, not speed."
    client.post(f"{BASE}/note", json={"text": "Edited"})
    assert client.get(BASE).json()["note"] == "Edited"
    r = client.post(f"{BASE}/note", json={"text": "  \n"})
    assert r.status_code == 200 and r.json()["updated_at"] is None
    with SessionLocal() as s:
        assert s.get(StudentNote, SID) is None
    assert client.post(f"{BASE}/note", json={"text": "x" * (svc.NOTE_MAX_CHARS + 1)}).status_code == 422


def test_highlight_crud(client: TestClient) -> None:
    r = client.post(f"{BASE}/highlights", json=_highlight())
    assert r.status_code == 201
    h = r.json()
    assert h["id"] and h["colour"] == "yellow" and h["exact"] == "the critical angle of attack" and h["orphaned"] is False
    assert [x["id"] for x in client.get(BASE).json()["highlights"]] == [h["id"]]

    r = client.patch(f"/annotations/highlights/{h['id']}", json={"colour": "pink", "comment": "Exam favourite"})
    assert r.status_code == 200 and r.json()["colour"] == "pink" and r.json()["comment"] == "Exam favourite"
    r = client.patch(f"/annotations/highlights/{h['id']}", json={"orphaned": True})
    assert r.json()["orphaned"] is True and r.json()["colour"] == "pink"  # untouched fields stay

    assert client.delete(f"/annotations/highlights/{h['id']}").status_code == 204
    assert client.get(BASE).json()["highlights"] == []
    assert client.delete(f"/annotations/highlights/{h['id']}").status_code == 404
    assert client.patch(f"/annotations/highlights/{h['id']}", json={"colour": "blue"}).status_code == 404


@pytest.mark.parametrize("bad", [
    {"colour": "purple"},
    {"start": 50, "end": 10},
    {"exact": ""},
    {"exact": "x" * 2001},
    {"prefix": "p" * 65},
    {"start": -1},
])
def test_highlight_validation(client: TestClient, bad: dict) -> None:
    assert client.post(f"{BASE}/highlights", json=_highlight(**bad)).status_code == 422
    with SessionLocal() as s:
        assert s.query(Highlight).count() == 0


def test_highlight_patch_rejects_bad_colour(client: TestClient) -> None:
    hid = client.post(f"{BASE}/highlights", json=_highlight()).json()["id"]
    assert client.patch(f"/annotations/highlights/{hid}", json={"colour": "red"}).status_code == 422


def test_ink_revisions_and_delete(client: TestClient) -> None:
    url = f"{BASE}/ink/lesson/0"
    assert client.post(url, json={"rev": 0, "strokes": [_stroke()]}).json() == {"rev": 1}
    assert client.post(url, json={"rev": 1, "strokes": [_stroke(), _stroke()]}).json() == {"rev": 2}
    lesson = client.get(BASE).json()["ink"]["lesson"]
    assert lesson["rev"] == 2 and len(lesson["strokes"]) == 2

    assert client.post(f"{BASE}/ink/sketch/2", json={"rev": 0, "strokes": [_stroke()]}).json() == {"rev": 1}
    assert [p["page"] for p in client.get(BASE).json()["ink"]["sketch"]] == [2]

    assert client.post(url, json={"rev": 2, "strokes": []}).json() == {"rev": 3}  # an empty page is deleted
    with SessionLocal() as s:
        assert s.query(InkDocument).filter_by(kind="lesson").count() == 0
    assert client.get(BASE).json()["ink"]["lesson"]["strokes"] == []

    assert client.delete(f"{BASE}/ink/sketch/2").status_code == 204
    assert client.get(BASE).json()["ink"]["sketch"] == []


def test_ink_limits(client: TestClient) -> None:
    url = f"{BASE}/ink/lesson/0"
    too_many = [{"pts": []}] * (svc.INK_MAX_STROKES + 1)
    assert client.post(url, json={"rev": 0, "strokes": too_many}).status_code == 422
    assert client.post(url, json={"rev": 0, "strokes": [_stroke(svc.INK_MAX_POINTS + 1)]}).status_code == 422
    assert client.post(f"{BASE}/ink/doodle/0", json={"rev": 0, "strokes": [_stroke()]}).status_code == 422
    assert client.post(f"{BASE}/ink/lesson/3", json={"rev": 0, "strokes": [_stroke()]}).status_code == 422
    assert client.post(url, content=b"not json", headers={"Content-Type": "application/json"}).status_code == 422
    huge = json.dumps({"rev": 0, "strokes": [{"pts": [], "pad": "x" * (svc.INK_MAX_BYTES + 10)}]})
    assert client.post(url, content=huge, headers={"Content-Type": "application/json"}).status_code == 413
    with SessionLocal() as s:
        assert s.query(InkDocument).count() == 0


def test_unknown_subtopic_404(client: TestClient) -> None:
    bad = f"/annotations/{quote('ZZZZ 9.9')}"
    assert client.get(bad).status_code == 404
    assert client.post(f"{bad}/note", json={"text": "hi"}).status_code == 404
    assert client.post(f"{bad}/highlights", json=_highlight()).status_code == 404
    assert client.post(f"{bad}/ink/lesson/0", json={"rev": 0, "strokes": [_stroke()]}).status_code == 404
    assert client.delete(f"{bad}/ink/lesson/0").status_code == 404


def test_my_notes_empty_state(client: TestClient) -> None:
    r = client.get("/my-notes")
    assert r.status_code == 200
    assert "My notes" in r.text and "Nothing here yet" in r.text
    assert 'href="/my-notes/export.json"' in r.text
    assert 'href="/my-notes"' in r.text  # sidebar link


def test_my_notes_lists_counts(client: TestClient) -> None:
    client.post(f"{BASE}/note", json={"text": "Spin recovery: PARE — power idle, ailerons neutral."})
    client.post(f"{BASE}/highlights", json=_highlight())
    client.post(f"{BASE}/highlights", json=_highlight(colour="green", start=200, end=210, exact="spiral dive", comment="Not a spin"))
    client.post(f"{BASE}/ink/sketch/0", json={"rev": 0, "strokes": [_stroke()]})
    client.post(f"{BASE}/ink/lesson/0", json={"rev": 0, "strokes": [_stroke()]})
    r = client.get("/my-notes")
    assert r.status_code == 200 and "Nothing here yet" not in r.text
    assert f'data-my-note="{SID}"' in r.text
    assert "Spin recovery: PARE" in r.text
    assert "2 highlights · 1 comment" in r.text and "1 sketch page" in r.text and "Ink on lesson" in r.text
    assert 'href="/lessons/RBKA/3.6#my-notes"' in r.text
    assert '<mark class="hl hl-green">spiral dive</mark>' in r.text

    with SessionLocal() as s:
        totals = svc.summary(s)["totals"]
    assert totals == {"lessons": 1, "notes": 1, "highlights": 2, "ink_pages": 2}


def test_export(client: TestClient) -> None:
    client.post(f"{BASE}/note", json={"text": "Backup me"})
    client.post(f"{BASE}/highlights", json=_highlight())
    client.post(f"{BASE}/ink/sketch/1", json={"rev": 0, "strokes": [_stroke()]})
    r = client.get("/my-notes/export.json")
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/json")
    assert r.headers["content-disposition"] == f'attachment; filename="casa-theory-notes-{date.today().isoformat()}.json"'
    data = r.json()
    assert data["format"] == svc.EXPORT_FORMAT and data["exported_at"]
    assert [n["text"] for n in data["notes"]] == ["Backup me"] and data["notes"][0]["subtopic_id"] == SID
    assert data["highlights"][0]["exact"] == "the critical angle of attack"
    assert data["ink"][0]["kind"] == "sketch" and data["ink"][0]["page"] == 1 and data["ink"][0]["strokes"] == [_stroke()]


def test_search_finds_and_forgets_a_note(client: TestClient) -> None:
    word = "quokkaplover"
    assert "Nothing matches" in client.get("/search", params={"q": word}).text
    client.post(f"{BASE}/note", json={"text": f"Remember the {word} mnemonic for spins."})
    client.post(f"{BASE}/highlights", json=_highlight(comment=f"{word} again"))

    r = client.get("/search", params={"q": word})
    assert r.status_code == 200 and "My notes" in r.text
    assert 'href="/lessons/RBKA/3.6#my-notes"' in r.text and "<mark>quokkaplover</mark>" in r.text
    r = client.get("/search", params={"q": word, "kind": "mynote"})
    assert r.status_code == 200 and "/lessons/RBKA/3.6#my-notes" in r.text
    assert "/lessons/RBKA/3.6#my-notes" in client.get("/search/suggest", params={"q": word}).text

    client.post(f"{BASE}/note", json={"text": ""})
    hid = client.get(BASE).json()["highlights"][0]["id"]
    client.delete(f"/annotations/highlights/{hid}")
    assert "Nothing matches" in client.get("/search", params={"q": word}).text
