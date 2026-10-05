"""Per-subtopic study status and evidence from answer history."""
from __future__ import annotations

from app.util import utcnow

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import STATUSES, Attempt, AttemptAnswer, CardReview, Element, Exam, PlanItem, Progress, Question, QuestionElement, Subtopic, Unit


def set_status(session: Session, subtopic_id: str, status: str) -> Progress:
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}")
    row = session.get(Progress, subtopic_id)
    if row is None:
        row = Progress(subtopic_id=subtopic_id)
        session.add(row)
    row.status = status
    row.updated_at = utcnow()
    session.commit()
    return row


def status_map(session: Session) -> dict[str, str]:
    return {p.subtopic_id: p.status for p in session.scalars(select(Progress))}


def _summarise(subtopics: list[Subtopic], statuses: dict[str, str]) -> dict:
    total = len(subtopics)
    studying = sum(1 for s in subtopics if statuses.get(s.id) == "studying")
    confident = sum(1 for s in subtopics if statuses.get(s.id) == "confident")
    percent = round(100 * (confident + 0.5 * studying) / total) if total else 0
    return {"total": total, "studying": studying, "confident": confident,
            "not_started": total - studying - confident, "percent": percent}


def unit_progress(session: Session, unit_code: str) -> dict:
    subs = list(session.scalars(select(Subtopic).where(Subtopic.unit_code == unit_code)))
    return _summarise(subs, status_map(session))


def exam_progress(session: Session, exam_code: str) -> dict:
    exam = session.get(Exam, exam_code)
    codes = [eu.unit_code for eu in exam.units]
    subs = list(session.scalars(select(Subtopic).where(Subtopic.unit_code.in_(codes))))
    out = _summarise(subs, status_map(session))
    out["units"] = {c: _summarise([s for s in subs if s.unit_code == c], status_map(session)) for c in codes}
    return out


def answer_stats_by_subtopic(session: Session) -> dict[str, dict]:
    """{subtopic_id: {answered, correct, percent}} over all submitted answers."""
    rows = session.execute(
        select(Question.subtopic_id, func.count(AttemptAnswer.id), func.sum(AttemptAnswer.correct))
        .join(Question, Question.id == AttemptAnswer.question_id)
        .where(AttemptAnswer.correct.is_not(None))
        .group_by(Question.subtopic_id)
    ).all()
    return {sid: {"answered": n, "correct": int(c or 0), "percent": round(100 * int(c or 0) / n) if n else None}
            for sid, n, c in rows if sid}


def element_accuracy(session: Session) -> dict[str, dict]:
    """{element_code: {answered, correct, percent}} from every marked answer."""
    rows = session.execute(
        select(QuestionElement.element_code, func.count(AttemptAnswer.id), func.sum(AttemptAnswer.correct))
        .join(QuestionElement, QuestionElement.question_id == AttemptAnswer.question_id)
        .where(AttemptAnswer.correct.is_not(None))
        .group_by(QuestionElement.element_code)
    ).all()
    return {code: {"answered": n, "correct": int(c or 0), "percent": round(100 * int(c or 0) / n)} for code, n, c in rows}


def weak_subtopics(session: Session, limit: int = 10, min_answered: int = 2) -> list[dict]:
    """Subtopics with the lowest accuracy, for the dashboard and the weak-areas quiz."""
    stats = answer_stats_by_subtopic(session)
    ranked = sorted((s for s in stats.items() if s[1]["answered"] >= min_answered), key=lambda kv: kv[1]["percent"])
    out = []
    for sid, st in ranked[:limit]:
        sub = session.get(Subtopic, sid)
        out.append({"subtopic": sub, **st})
    return out


def recent_attempts(session: Session, limit: int = 5, mode: str | None = None) -> list[Attempt]:
    q = select(Attempt).where(Attempt.submitted_at.is_not(None)).order_by(Attempt.submitted_at.desc()).limit(limit)
    if mode:
        q = q.where(Attempt.mode == mode)
    return list(session.scalars(q))


def _local_date(ts: datetime) -> date:
    """Naive UTC timestamp -> the server's local calendar date (the planner's date.today() uses the same clock)."""
    return ts.replace(tzinfo=timezone.utc).astimezone().date()


def activity_streak(session: Session, today: date | None = None) -> dict:
    """Study streak from every kind of activity: answered questions, card reviews, ticked study items and status changes.

    Other plan items (cards, quizzes, mocks) are only auto-ticked from activity already counted here, and the cards
    item can be ticked when nothing is due, so they are left out.

    Card reviews only keep their latest timestamp, so a day counts when any card was last reviewed on it; that is
    exact for today and a slight undercount for older days. The streak runs back from today, or from yesterday when
    nothing has happened yet today (so it is not shown as broken first thing in the morning).
    Returns {current, today, week: [{label, on, today}] for the last seven days ending today}.
    """
    today = today or date.today()
    stamps = [
        select(AttemptAnswer.answered_at).where(AttemptAnswer.answered_at.is_not(None)),
        select(CardReview.last_reviewed).where(CardReview.last_reviewed.is_not(None)),
        select(PlanItem.done_at).where(PlanItem.done_at.is_not(None), PlanItem.kind == "study"),
        select(Progress.updated_at).where(Progress.status != "not_started"),
    ]
    days = {_local_date(ts) for q in stamps for ts in session.scalars(q) if ts is not None}
    day = today if today in days else today - timedelta(days=1)
    current = 0
    while day in days:
        current += 1
        day -= timedelta(days=1)
    week = [today - timedelta(days=i) for i in range(6, -1, -1)]
    return {
        "current": current,
        "today": today in days,
        "week": [{"label": d.strftime("%a")[0], "on": d in days, "today": d == today} for d in week],
    }
