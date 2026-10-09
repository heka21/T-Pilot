"""Timed mock exams (RPLA / PPLA): setup, one-page exam runner with navigator and timer, results with KDR."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.models import Attempt, Exam, ExamUnit, Unit
from app.services import exam as exam_svc
from app.services import readiness
from app.services.quiz import kdr_report, record_answer
from app.templating import templates

router = APIRouter(prefix="/exam", tags=["exam"])


def get_exam_attempt(session: Session, attempt_id: int) -> Attempt:
    attempt = session.get(Attempt, attempt_id)
    if attempt is None or attempt.mode != "exam":
        raise HTTPException(status_code=404, detail="Exam attempt not found")
    return attempt


def finished(session: Session, attempt: Attempt) -> bool:
    """Auto-submit if time is up; True when the attempt is no longer open."""
    exam_svc.expire_if_due(session, attempt)
    return attempt.submitted_at is not None


def to_result(request: Request, attempt: Attempt) -> Response:
    url = f"/exam/{attempt.id}/result"
    if request.headers.get("HX-Request"):
        return Response(status_code=200, headers={"HX-Redirect": url})
    return RedirectResponse(url, status_code=303)


def is_answered(ans) -> bool:
    return ans.given is not None and ans.given != ""


def run_context(attempt: Attempt, position: int) -> dict:
    if not 0 <= position < len(attempt.answers):
        raise HTTPException(status_code=404, detail="No such question")
    ans = attempt.answers[position]
    return {"attempt": attempt, "ans": ans, "q": ans.question, "position": position, "total": len(attempt.answers),
            "answered": [is_answered(a) for a in attempt.answers],
            "unanswered": sum(1 for a in attempt.answers if not is_answered(a)),
            "seconds_left": exam_svc.seconds_remaining(attempt)}


@router.get("", response_class=HTMLResponse)
def exam_setup(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    exams = session.scalars(select(Exam).options(selectinload(Exam.units).selectinload(ExamUnit.unit))
                            .order_by(Exam.duration_minutes, Exam.code)).all()
    current = exam_svc.open_exam(session)
    if current is not None and finished(session, current):
        current = None
    recent = session.scalars(select(Attempt).where(Attempt.mode == "exam", Attempt.submitted_at.is_not(None))
                             .order_by(Attempt.submitted_at.desc()).limit(10)).all()
    trends = {e.code: readiness.mock_history(session, e.code) for e in exams}
    return templates.TemplateResponse(request, "exam_setup.html", {"exams": exams, "open_attempt": current, "recent": recent,
                                                                   "trends": trends})


@router.post("/start")
def exam_start(exam_code: str = Form(...), session: Session = Depends(get_session)) -> Response:
    if session.get(Exam, exam_code) is None:
        raise HTTPException(status_code=404, detail="Unknown exam")
    attempt = exam_svc.start_exam(session, exam_code)
    return RedirectResponse(f"/exam/{attempt.id}", status_code=303)


@router.get("/{attempt_id}", response_class=HTMLResponse)
def exam_run(request: Request, attempt_id: int, q: int | None = None, session: Session = Depends(get_session)) -> Response:
    attempt = get_exam_attempt(session, attempt_id)
    if finished(session, attempt):
        return to_result(request, attempt)
    if not attempt.answers:
        exam_svc.submit_exam(session, attempt)
        return to_result(request, attempt)
    if q is None:
        q = next((a.position for a in attempt.answers if not is_answered(a)), 0)
    exam = session.get(Exam, attempt.exam_code)
    return templates.TemplateResponse(request, "exam_run.html", run_context(attempt, q) | {"exam": exam})


@router.get("/{attempt_id}/q/{position}", response_class=HTMLResponse)
def exam_question(request: Request, attempt_id: int, position: int, session: Session = Depends(get_session)) -> Response:
    attempt = get_exam_attempt(session, attempt_id)
    if finished(session, attempt):
        return to_result(request, attempt)
    return templates.TemplateResponse(request, "exam_question.html", run_context(attempt, position) | {"oob": True})


@router.post("/{attempt_id}/answer", response_class=HTMLResponse)
def exam_answer(request: Request, attempt_id: int, position: int = Form(...), given: str = Form(""),
                session: Session = Depends(get_session)) -> Response:
    attempt = get_exam_attempt(session, attempt_id)
    if finished(session, attempt):
        return to_result(request, attempt)
    run_context(attempt, position)  # validates position
    record_answer(session, attempt, position, given.strip() or None, grade_now=False)
    ctx = run_context(attempt, position)
    return templates.TemplateResponse(request, "exam_nav.html", ctx | {"oob": True, "saved": True})


@router.post("/{attempt_id}/flag/{position}", response_class=HTMLResponse)
def exam_flag(request: Request, attempt_id: int, position: int, session: Session = Depends(get_session)) -> Response:
    attempt = get_exam_attempt(session, attempt_id)
    if finished(session, attempt):
        return to_result(request, attempt)
    ans = run_context(attempt, position)["ans"]
    ans.flagged = not ans.flagged
    session.commit()
    return templates.TemplateResponse(request, "exam_question.html", run_context(attempt, position) | {"oob": True})


@router.post("/{attempt_id}/submit")
def exam_submit(request: Request, attempt_id: int, session: Session = Depends(get_session)) -> Response:
    attempt = get_exam_attempt(session, attempt_id)
    if not finished(session, attempt):
        exam_svc.submit_exam(session, attempt)
    return to_result(request, attempt)


@router.get("/{attempt_id}/result", response_class=HTMLResponse)
def exam_result(request: Request, attempt_id: int, session: Session = Depends(get_session)) -> Response:
    attempt = get_exam_attempt(session, attempt_id)
    if not finished(session, attempt):
        return RedirectResponse(f"/exam/{attempt.id}", status_code=303)
    exam = session.get(Exam, attempt.exam_code) if attempt.exam_code else None
    units = {u.code: u for u in session.scalars(select(Unit))}
    used = (attempt.submitted_at - attempt.started_at).total_seconds() // 60 if attempt.submitted_at else None
    if exam and used is not None:
        used = min(used, exam.duration_minutes)
    ctx = {"attempt": attempt, "exam": exam, "units": units, "breakdown": exam_svc.unit_breakdown(attempt),
           "kdr": kdr_report(session, attempt), "minutes_used": used,
           "pass_mark": (exam.pass_mark_percent if exam else attempt.config.get("pass_mark", 70))}
    return templates.TemplateResponse(request, "exam_result.html", ctx)
