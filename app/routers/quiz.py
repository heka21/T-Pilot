"""Practice quizzes: setup, one question at a time with instant feedback, results with a KDR."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.models import Attempt, Exam, ExamUnit, Question, Subtopic, Unit
from app.services import quiz as quiz_svc
from app.templating import templates

router = APIRouter(prefix="/quiz", tags=["quiz"])

COUNTS = (5, 10, 20)


def get_attempt(session: Session, attempt_id: int, mode: str = "quiz") -> Attempt:
    attempt = session.get(Attempt, attempt_id)
    if attempt is None or attempt.mode != mode:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt


def setup_context(session: Session, subtopic_id: str | None, weak: bool, count: int = 10,
                  selected: list[str] | None = None, error: str | None = None) -> dict:
    exams = session.scalars(select(Exam).options(selectinload(Exam.units).selectinload(ExamUnit.unit))
                            .order_by(Exam.duration_minutes, Exam.code)).all()
    counts = dict(session.execute(select(Question.unit_code, func.count()).group_by(Question.unit_code)).all())
    subtopic = session.get(Subtopic, subtopic_id) if subtopic_id else None
    sub_count = session.scalar(select(func.count()).select_from(Question).where(Question.subtopic_id == subtopic.id)) if subtopic else 0
    return {"exams": exams, "counts": counts, "subtopic": subtopic, "subtopic_count": sub_count, "weak": weak,
            "count": count, "count_choices": COUNTS, "selected": selected or [], "error": error,
            "total_questions": sum(counts.values())}


def question_context(attempt: Attempt, position: int) -> dict:
    answers = attempt.answers
    if not 0 <= position < len(answers):
        raise HTTPException(status_code=404, detail="No such question")
    return {"attempt": attempt, "ans": answers[position], "q": answers[position].question,
            "position": position, "total": len(answers), "is_last": position == len(answers) - 1}


def next_unanswered(attempt: Attempt) -> int | None:
    return next((a.position for a in attempt.answers if a.answered_at is None), None)


@router.get("", response_class=HTMLResponse)
def quiz_setup(request: Request, subtopic: str | None = None, weak: int = 0, unit: list[str] | None = None,
               session: Session = Depends(get_session)) -> HTMLResponse:
    ctx = setup_context(session, subtopic, bool(weak), selected=unit or [])
    return templates.TemplateResponse(request, "quiz_setup.html", ctx)


@router.post("/start")
def quiz_start(request: Request, units: list[str] = Form(default=[]), subtopic: str = Form(""),
               count: int = Form(10), weak: str = Form(""), session: Session = Depends(get_session)) -> Response:
    count = count if count in COUNTS else 10
    weak_on = bool(weak)
    sub = session.get(Subtopic, subtopic) if subtopic else None
    if sub:
        questions = quiz_svc.pick_questions(session, count, subtopic_ids=[sub.id], weak=weak_on)
        title = f"Quiz: {sub.id} {sub.title}"
    else:
        questions = quiz_svc.pick_questions(session, count, unit_codes=units or None, weak=weak_on)
        title = "Quiz: " + (", ".join(units) if units else "all units") + (" (weak areas)" if weak_on else "")
    if not questions:
        ctx = setup_context(session, subtopic or None, weak_on, count, units,
                            error="No questions match that choice yet. Pick another unit or subtopic.")
        return templates.TemplateResponse(request, "quiz_setup.html", ctx, status_code=422)
    attempt = quiz_svc.start_attempt(session, questions, mode="quiz", title=title,
                                     config={"units": units, "subtopic": sub.id if sub else None, "weak": weak_on, "count": count})
    return RedirectResponse(f"/quiz/{attempt.id}", status_code=303)


@router.get("/{attempt_id}", response_class=HTMLResponse)
def quiz_page(request: Request, attempt_id: int, session: Session = Depends(get_session)) -> Response:
    attempt = get_attempt(session, attempt_id)
    position = next_unanswered(attempt)
    if attempt.submitted_at is not None or position is None:
        return RedirectResponse(f"/quiz/{attempt.id}/result", status_code=303)
    ctx = question_context(attempt, position) | {"page": True}
    return templates.TemplateResponse(request, "quiz_question.html", ctx)


@router.get("/{attempt_id}/q/{position}", response_class=HTMLResponse)
def quiz_question(request: Request, attempt_id: int, position: int, session: Session = Depends(get_session)) -> HTMLResponse:
    attempt = get_attempt(session, attempt_id)
    ans = question_context(attempt, position)["ans"]
    ctx = question_context(attempt, position) | {"feedback": ans.answered_at is not None}
    return templates.TemplateResponse(request, "quiz_question.html", ctx)


@router.post("/{attempt_id}/answer", response_class=HTMLResponse)
def quiz_answer(request: Request, attempt_id: int, position: int = Form(...), given: str = Form(""),
                session: Session = Depends(get_session)) -> HTMLResponse:
    attempt = get_attempt(session, attempt_id)
    question_context(attempt, position)  # validates position
    quiz_svc.record_answer(session, attempt, position, given.strip() or None, grade_now=True)
    ctx = question_context(attempt, position) | {"feedback": True}
    return templates.TemplateResponse(request, "quiz_question.html", ctx)


@router.get("/{attempt_id}/result", response_class=HTMLResponse)
def quiz_result(request: Request, attempt_id: int, session: Session = Depends(get_session)) -> HTMLResponse:
    attempt = get_attempt(session, attempt_id)
    if attempt.submitted_at is None:
        quiz_svc.finish_attempt(session, attempt)
    units = {u.code: u for u in session.scalars(select(Unit))}
    ctx = {"attempt": attempt, "kdr": quiz_svc.kdr_report(session, attempt), "units": units}
    return templates.TemplateResponse(request, "quiz_result.html", ctx)
