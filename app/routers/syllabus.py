"""Syllabus browser: exams -> units -> topics -> subtopics -> knowledge elements (verbatim MOS)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.models import Exam, ExamUnit, Subtopic, Topic, Unit
from app.services import progress
from app.templating import templates

router = APIRouter(tags=["syllabus"])


def subtopic_url(subtopic: Subtopic | str) -> str:
    """/syllabus/subtopic/RBKA/3.6 for a Subtopic or a subtopic id like 'RBKA 3.6'."""
    unit, number = _split_id(subtopic)
    return f"/syllabus/subtopic/{unit}/{number}"


def _split_id(subtopic: Subtopic | str) -> tuple[str, str]:
    if isinstance(subtopic, str):
        unit, _, number = subtopic.partition(" ")
        return unit, number
    return subtopic.unit_code, subtopic.number


def get_subtopic(session: Session, unit: str, number: str) -> Subtopic:
    sub = session.get(Subtopic, f"{unit.upper()} {number}")
    if sub is None:
        raise HTTPException(status_code=404, detail="Subtopic not found")
    return sub


def neighbours(session: Session, sub: Subtopic, with_note: bool = False) -> tuple[Subtopic | None, Subtopic | None]:
    """Previous and next subtopic in global syllabus order (optionally only those with a note)."""
    base = select(Subtopic)
    if with_note:
        base = base.where(Subtopic.note.has())
    prev = session.scalar(base.where(Subtopic.position < sub.position).order_by(Subtopic.position.desc()).limit(1))
    nxt = session.scalar(base.where(Subtopic.position > sub.position).order_by(Subtopic.position).limit(1))
    return prev, nxt


def exams_with_units(session: Session) -> list[Exam]:
    return list(session.scalars(
        select(Exam).options(selectinload(Exam.units).selectinload(ExamUnit.unit)).order_by(Exam.duration_minutes, Exam.code)
    ))


@router.get("/syllabus", response_class=HTMLResponse)
def syllabus(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    exams = exams_with_units(session)
    ctx = {"exams": exams, "progress": {e.code: progress.exam_progress(session, e.code) for e in exams}}
    return templates.TemplateResponse(request, "syllabus.html", ctx)


@router.get("/syllabus/unit/{code}", response_class=HTMLResponse)
def unit_page(code: str, request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    unit = session.scalar(
        select(Unit).where(Unit.code == code.upper()).options(
            selectinload(Unit.topics).selectinload(Topic.subtopics).selectinload(Subtopic.note),
            selectinload(Unit.topics).selectinload(Topic.subtopics).selectinload(Subtopic.progress),
        )
    )
    if unit is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    exam_codes = list(session.scalars(select(ExamUnit.exam_code).where(ExamUnit.unit_code == unit.code).order_by(ExamUnit.exam_code.desc())))
    ctx = {"unit": unit, "exam_codes": exam_codes, "unit_progress": progress.unit_progress(session, unit.code)}
    return templates.TemplateResponse(request, "unit.html", ctx)


@router.get("/syllabus/subtopic/{unit}/{number}", response_class=HTMLResponse)
def subtopic_page(unit: str, number: str, request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    sub = get_subtopic(session, unit, number)
    prev, nxt = neighbours(session, sub)
    return templates.TemplateResponse(request, "subtopic.html", {"sub": sub, "prev": prev, "next": nxt})
