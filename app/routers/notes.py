"""Lessons, one per subtopic."""
from __future__ import annotations

import html
import re

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.models import STATUSES, ExamUnit, Subtopic, Topic, Unit
from app.routers.syllabus import _split_id, get_subtopic, neighbours
from app.templating import templates

router = APIRouter(tags=["lessons"])

_H2_RE = re.compile(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', re.S)
_TAG_RE = re.compile(r"<[^>]+>")
TOC_MIN_HEADINGS = 3


def lesson_toc(markup: str) -> list[dict]:
    """[{id, text}] for each h2 of a rendered note; the ids come from the `toc` Markdown extension at seed time."""
    return [{"id": m.group(1), "text": html.unescape(_TAG_RE.sub("", m.group(2))).strip()} for m in _H2_RE.finditer(markup)]


def note_url(subtopic: Subtopic | str) -> str:
    """/lessons/RBKA/3.6 for a Subtopic or a subtopic id like 'RBKA 3.6'."""
    unit, number = _split_id(subtopic)
    return f"/lessons/{unit}/{number}"


@router.get("/lessons", response_class=HTMLResponse)
def notes_index(request: Request, q: str = "", exam: str = "", status: str = "",
                session: Session = Depends(get_session)) -> HTMLResponse:
    """All lessons by unit. q/exam/status prefill the filter bar; app.js does the filtering in the page."""
    units = list(session.scalars(
        select(Unit).order_by(Unit.position).options(
            selectinload(Unit.topics).selectinload(Topic.subtopics).selectinload(Subtopic.note),
            selectinload(Unit.topics).selectinload(Topic.subtopics).selectinload(Subtopic.progress),
        )
    ))
    unit_exams: dict[str, list[str]] = {}
    for eu in session.scalars(select(ExamUnit).order_by(ExamUnit.exam_code.desc())):  # RPLA before PPLA
        unit_exams.setdefault(eu.unit_code, []).append(eu.exam_code)
    groups = []
    written = total = 0
    for unit in units:
        subs = [s for t in unit.topics for s in t.subtopics]
        with_note = [s for s in subs if s.note]
        groups.append({"unit": unit, "exams": unit_exams.get(unit.code, []), "notes": with_note, "missing": [s for s in subs if not s.note]})
        written += len(with_note)
        total += len(subs)
    filters = {"q": q.strip(), "exam": exam if exam in ("RPLA", "PPLA") else "", "status": status if status in STATUSES else ""}
    return templates.TemplateResponse(request, "notes_index.html",
                                      {"groups": groups, "written": written, "total": total, "filters": filters})


@router.get("/lessons/{unit}/{number}", response_class=HTMLResponse)
def note_page(unit: str, number: str, request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    sub = get_subtopic(session, unit, number)
    prev, nxt = neighbours(session, sub, with_note=True)
    toc = lesson_toc(sub.note.html) if sub.note else []
    return templates.TemplateResponse(request, "note.html", {"sub": sub, "note": sub.note, "prev": prev, "next": nxt,
                                                             "toc": toc if len(toc) >= TOC_MIN_HEADINGS else []})


@router.get("/notes")
@router.get("/notes/{path:path}")
def old_notes_url(path: str = "") -> RedirectResponse:
    """Lessons used to be called notes: keep old bookmarks working."""
    return RedirectResponse(f"/lessons/{path}".rstrip("/"), status_code=301)
