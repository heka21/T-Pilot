"""Study status per subtopic, and the progress overview page."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import STATUSES, Subtopic, Unit
from app.routers.syllabus import exams_with_units, subtopic_url
from app.services import progress
from app.templating import templates

router = APIRouter(tags=["progress"])


@router.post("/progress/{subtopic_id}")
def set_progress(subtopic_id: str, request: Request, status: str = Form(...),
                 session: Session = Depends(get_session)) -> Response:
    if status not in STATUSES:
        raise HTTPException(status_code=400, detail="Unknown status")
    sub = session.get(Subtopic, subtopic_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Subtopic not found")
    progress.set_status(session, sub.id, status)
    if not request.headers.get("HX-Request"):
        return RedirectResponse(request.headers.get("referer") or subtopic_url(sub), status_code=303)
    return templates.TemplateResponse(request, "_status.html", {"sid": sub.id, "status": status})


@router.get("/progress", response_class=HTMLResponse)
def progress_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    exams = exams_with_units(session)
    units = list(session.scalars(select(Unit).order_by(Unit.position)))
    ctx = {
        "exams": exams,
        "exam_progress": {e.code: progress.exam_progress(session, e.code) for e in exams},
        "units": [(u, progress.unit_progress(session, u.code)) for u in units],
        "weak": progress.weak_subtopics(session),
        "attempts": progress.recent_attempts(session, 10),
    }
    return templates.TemplateResponse(request, "progress.html", ctx)
