"""Diagnostic placement test: untimed, no feedback until the end, then choose which subtopics the plan can skip."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Attempt, Subtopic
from app.services import diagnostic, planner
from app.services.quiz import record_answer
from app.templating import templates

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


def get_diagnostic(session: Session, attempt_id: int) -> Attempt:
    attempt = session.get(Attempt, attempt_id)
    if attempt is None or attempt.mode != "diagnostic":
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    return attempt


@router.get("", response_class=HTMLResponse)
def diagnostic_intro(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    subs, _ = diagnostic.subtopic_pools(session)
    ctx = {"open": diagnostic.open_diagnostic(session), "latest": diagnostic.latest(session),
           "subtopic_count": len(subs), "exam_code": diagnostic.EXAM}
    return templates.TemplateResponse(request, "diagnostic_intro.html", ctx)


@router.post("/start")
def diagnostic_start(session: Session = Depends(get_session)) -> Response:
    attempt = diagnostic.open_diagnostic(session) or diagnostic.start(session)
    return RedirectResponse(f"/diagnostic/{attempt.id}", status_code=303)


@router.get("/{attempt_id}", response_class=HTMLResponse)
def diagnostic_run(request: Request, attempt_id: int, session: Session = Depends(get_session)) -> Response:
    """The next unanswered question of the current round; at the end of a round, start the next or finish."""
    attempt = get_diagnostic(session, attempt_id)
    if attempt.submitted_at is not None:
        return RedirectResponse(f"/diagnostic/{attempt.id}/result", status_code=303)
    answers = diagnostic.round_answers(attempt)
    ans = next((a for a in answers if a.answered_at is None), None)
    if ans is None:
        if diagnostic.advance(session, attempt):
            return RedirectResponse(f"/diagnostic/{attempt.id}?round=2", status_code=303)
        return RedirectResponse(f"/diagnostic/{attempt.id}/result", status_code=303)
    rnd = attempt.config.get("round", 1)
    ctx = {"attempt": attempt, "ans": ans, "q": ans.question, "position": ans.position, "round": rnd,
           "index": answers.index(ans) + 1, "total": len(answers),
           "new_round": request.query_params.get("round") == "2" and answers.index(ans) == 0}
    return templates.TemplateResponse(request, "diagnostic_question.html", ctx)


@router.post("/{attempt_id}/answer")
def diagnostic_answer(attempt_id: int, position: int = Form(...), given: str = Form(""),
                      session: Session = Depends(get_session)) -> Response:
    attempt = get_diagnostic(session, attempt_id)
    if attempt.submitted_at is None and any(a.position == position for a in attempt.answers):
        record_answer(session, attempt, position, given.strip() or None, grade_now=False)
    return RedirectResponse(f"/diagnostic/{attempt.id}", status_code=303)


@router.get("/{attempt_id}/result", response_class=HTMLResponse)
def diagnostic_result(request: Request, attempt_id: int, session: Session = Depends(get_session)) -> Response:
    attempt = get_diagnostic(session, attempt_id)
    if attempt.submitted_at is None:
        return RedirectResponse(f"/diagnostic/{attempt.id}", status_code=303)
    groups = diagnostic.classify(attempt)
    ids = [row["subtopic_id"] for rows in groups.values() for row in rows]
    subs = {s.id: s for s in session.scalars(select(Subtopic).where(Subtopic.id.in_(ids)))}
    for rows in groups.values():
        for row in rows:
            row["subtopic"] = subs[row["subtopic_id"]]
            row["status"] = row["subtopic"].progress.status if row["subtopic"].progress else "not_started"
    ctx = {"attempt": attempt, "groups": groups, "has_plan": planner.active_plan(session) is not None,
           "applied": request.query_params.get("applied")}
    return templates.TemplateResponse(request, "diagnostic_result.html", ctx)


@router.post("/{attempt_id}/apply")
def diagnostic_apply(attempt_id: int, subtopics: list[str] = Form(default=[]),
                     session: Session = Depends(get_session)) -> Response:
    attempt = get_diagnostic(session, attempt_id)
    if attempt.submitted_at is None:
        raise HTTPException(status_code=409, detail="Finish the diagnostic first")
    changed = diagnostic.apply(session, subtopics)
    return RedirectResponse(f"/diagnostic/{attempt.id}/result?applied={changed}", status_code=303)
