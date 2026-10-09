"""Dashboard: exam progress, today's plan, cards due, last attempt, weak areas."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.models import Exam, ExamUnit, Progress, Subtopic
from app.services import diagnostic, mistakes, planner, progress, readiness, srs
from app.templating import templates

router = APIRouter()

PLAN_ITEM_LINKS = {"quiz": "/quiz", "cards": "/cards", "mock_exam": "/exam", "revision": "/quiz?weak=1"}

# CASA's published weak areas -> the subtopic that teaches it, per exam (first keyword match wins).
WEAK_AREA_SUBTOPICS = {
    "RPLA": [("glide", "RBKA 3.4"), ("wind shear", "RBKA 3.7"), ("local winds", "RMTC 2.1"),
             ("forecast", "RMTC 2.2"), ("take-off and landing", "BAKC 6.2")],
    "PPLA": [("take-off and landing", "POPA 2.2"), ("time/distance", "PNVC 2.4"), ("density height", "POPA 2.3"),
             ("loading", "POPC 2.1"), ("forecast", "PMTC 2.7")],
}


def weak_area_links(exam: Exam) -> list[dict[str, str | None]]:
    """[{area, subtopic_id}] for Exam.casa_weak_areas; subtopic_id is None when no mapping is known."""
    out = []
    for area in exam.casa_weak_areas or []:
        sid = next((s for key, s in WEAK_AREA_SUBTOPICS.get(exam.code, []) if key in area.lower()), None)
        out.append({"area": area, "subtopic_id": sid})
    return out


def next_unstudied(session: Session) -> Subtopic | None:
    """First subtopic in syllabus order that has a note and has not been marked studying or confident."""
    started = select(Progress.subtopic_id).where(Progress.status != "not_started")
    return session.scalar(
        select(Subtopic).where(Subtopic.note.has(), Subtopic.id.not_in(started)).order_by(Subtopic.position).limit(1)
    )


def build_dashboard(session: Session) -> dict[str, Any]:
    exams = list(session.scalars(
        select(Exam)
        .options(selectinload(Exam.units).selectinload(ExamUnit.unit))
        .order_by(Exam.duration_minutes, Exam.code)
    ))
    last = progress.recent_attempts(session, 1)
    plan = planner.active_plan(session)
    plan_status = planner.status(session, plan) if plan else None
    mistake_counts = mistakes.counts(session)
    links = PLAN_ITEM_LINKS | ({"quiz": "/quiz?mistakes=1"} if mistake_counts["due"] else {})
    return {
        "exams": exams,
        "exam_progress": {e.code: progress.exam_progress(session, e.code) for e in exams},
        "plan": plan,
        "plan_status": plan_status,
        "today_items": plan_status["today_items"] if plan_status else [],
        "item_links": links,
        "mistakes": mistake_counts,
        "readiness": readiness.report(session, "RPLA"),
        # Offer the placement test until one is taken, while little has been studied yet.
        "offer_diagnostic": diagnostic.latest(session) is None and len(planner.completed_subtopics(session)) < 5,
        "open_diagnostic": diagnostic.open_diagnostic(session),
        "due_cards": srs.due_count(session),
        "last_attempt": last[0] if last else None,
        "weak": progress.weak_subtopics(session, 5),
        "weak_areas": {e.code: weak_area_links(e) for e in exams},
        "start_here": next_unstudied(session) if plan is None else None,
        "next_lesson": next_unstudied(session),
        "streak": progress.activity_streak(session),
    }


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    return templates.TemplateResponse(request, "dashboard.html", build_dashboard(session))
