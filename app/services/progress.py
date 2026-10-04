"""Per-subtopic study status and evidence from answer history."""
from __future__ import annotations

from app.util import utcnow

from collections import defaultdict
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import STATUSES, Attempt, AttemptAnswer, Element, Exam, Progress, Question, QuestionElement, Subtopic, Unit


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
