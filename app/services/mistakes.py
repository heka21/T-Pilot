"""Mistakes loop: every question answered wrong comes back until it is answered right on two separate days.

A wrong answer opens (or reopens) the mistake, due tomorrow. A right answer to an open mistake counts once per
calendar day: the first moves it out three days, the second clears it. A right answer to a question never missed
does nothing. Answers from quizzes are recorded as they are marked; mocks and the diagnostic when submitted.
"""
from __future__ import annotations

from app.util import utcnow

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Mistake, Question

CLEAR_AFTER = 2  # right answers on separate days
RETRY_AFTER_MISS = timedelta(days=1)
RETRY_AFTER_RIGHT = timedelta(days=3)


def record(session: Session, question_id: str, correct: bool, today: date | None = None) -> Mistake | None:
    """Apply one marked answer to the question's mistake state. Does not commit."""
    today = today or date.today()
    row = session.get(Mistake, question_id)
    if not correct:
        if row is None:
            row = Mistake(question_id=question_id, first_missed_at=utcnow(), miss_count=0)
            session.add(row)
        row.miss_count = (row.miss_count or 0) + 1
        row.last_missed_at = utcnow()
        row.streak = 0
        row.cleared_at = None
        row.due = today + RETRY_AFTER_MISS
        return row
    if row is None or row.cleared_at is not None:
        return row
    if row.last_correct_on != today:
        row.streak = (row.streak or 0) + 1
        row.last_correct_on = today
    if row.streak >= CLEAR_AFTER:
        row.cleared_at = utcnow()
    else:
        row.due = today + RETRY_AFTER_RIGHT
    return row


def _open(session: Session):
    return select(Mistake).where(Mistake.cleared_at.is_(None))


def counts(session: Session, today: date | None = None) -> dict[str, int]:
    today = today or date.today()
    open_n = session.scalar(select(func.count()).select_from(Mistake).where(Mistake.cleared_at.is_(None))) or 0
    due_n = session.scalar(select(func.count()).select_from(Mistake)
                           .where(Mistake.cleared_at.is_(None), Mistake.due <= today)) or 0
    cleared = session.scalar(select(func.count()).select_from(Mistake).where(Mistake.cleared_at.is_not(None))) or 0
    return {"open": open_n, "due": due_n, "cleared": cleared}


def quiz_questions(session: Session, count: int) -> list[Question]:
    """Open mistakes for a quiz: due ones first (most overdue first), then the rest by due date."""
    rows = session.scalars(_open(session).options(selectinload(Mistake.question).selectinload(Question.elements))
                           .order_by(Mistake.due, Mistake.last_missed_at)).all()
    return [m.question for m in rows[:count]]


def open_by_subtopic(session: Session) -> list[dict]:
    """[{subtopic_id, mistakes: [Mistake]}] in syllabus order, for the /mistakes page."""
    from app.models import Subtopic
    rows = session.scalars(_open(session).options(selectinload(Mistake.question))).all()
    groups: dict[str | None, list[Mistake]] = defaultdict(list)
    for m in rows:
        groups[m.question.subtopic_id].append(m)
    subs = {s.id: s for s in session.scalars(select(Subtopic).where(Subtopic.id.in_([k for k in groups if k])))}
    out = [{"subtopic": subs.get(sid), "mistakes": sorted(ms, key=lambda m: (m.due, m.question_id))}
           for sid, ms in groups.items()]
    out.sort(key=lambda g: g["subtopic"].position if g["subtopic"] else 10**9)
    return out


def oldest_open_days(session: Session, today: date | None = None) -> int | None:
    """Days since the oldest open mistake was last missed, or None when there are none."""
    today = today or date.today()
    ts = session.scalar(select(func.min(Mistake.last_missed_at)).where(Mistake.cleared_at.is_(None)))
    return (today - ts.date()).days if ts else None
