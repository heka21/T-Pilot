"""Timed mock exams that mirror the RPLA/PPLA format: unit weighting, duration, pass mark, KDR."""
from __future__ import annotations

from app.util import utcnow

import random
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Attempt, AttemptAnswer, Exam, Question
from app.services.quiz import finish_attempt, start_attempt


def allocate(total: int, weights: dict[str, int]) -> dict[str, int]:
    """Largest-remainder split of `total` questions across units by weight."""
    wsum = sum(weights.values()) or 1
    raw = {k: total * w / wsum for k, w in weights.items()}
    alloc = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: raw[k] - alloc[k], reverse=True)[: total - sum(alloc.values())]:
        alloc[k] += 1
    return alloc


def last_answered(session: Session) -> dict[str, datetime]:
    """{question_id: when it was last answered} over every attempt."""
    rows = session.execute(select(AttemptAnswer.question_id, func.max(AttemptAnswer.answered_at))
                           .where(AttemptAnswer.answered_at.is_not(None)).group_by(AttemptAnswer.question_id))
    return dict(rows.all())


def fresh_first(pool: list[Question], seen: dict[str, datetime], rng: random.Random) -> list[Question]:
    """Never-answered questions first in random order, then the rest from least to most recently answered."""
    rng.shuffle(pool)  # random order among equals (sort is stable)
    return sorted(pool, key=lambda q: (q.id in seen, seen.get(q.id) or datetime.min))


def sample_exam_questions(session: Session, exam: Exam, rng: random.Random | None = None) -> list[Question]:
    """Per-unit samples by weight, fresh questions first; a unit's shortfall is filled from the others' spare questions."""
    rng = rng or random.Random()
    weights = {eu.unit_code: eu.weight for eu in exam.units}
    alloc = allocate(exam.question_count, weights)
    seen = last_answered(session)
    pools = {code: list(session.scalars(select(Question).options(selectinload(Question.elements)).where(Question.unit_code == code)))
             for code in weights}
    chosen: list[Question] = []
    spare: list[Question] = []
    for code, n in alloc.items():
        pool = fresh_first(pools[code], seen, rng)
        chosen.extend(pool[:n])
        spare.extend(pool[n:])
    shortfall = exam.question_count - len(chosen)
    if shortfall > 0:
        chosen.extend(fresh_first(spare, seen, rng)[:shortfall])
    rng.shuffle(chosen)
    return chosen


def start_exam(session: Session, exam_code: str, rng: random.Random | None = None) -> Attempt:
    exam = session.get(Exam, exam_code)
    seen = last_answered(session)
    questions = sample_exam_questions(session, exam, rng)
    deadline = utcnow() + timedelta(minutes=exam.duration_minutes)
    return start_attempt(session, questions, mode="exam", title=f"{exam.code} mock exam", exam_code=exam.code,
                         config={"duration_minutes": exam.duration_minutes, "pass_mark": exam.pass_mark_percent,
                                 "fresh": sum(1 for q in questions if q.id not in seen)},
                         deadline=deadline)


def seconds_remaining(attempt: Attempt, now: datetime | None = None) -> int:
    now = now or utcnow()
    if attempt.deadline is None:
        return 0
    return max(0, int((attempt.deadline - now).total_seconds()))


def submit_exam(session: Session, attempt: Attempt) -> Attempt:
    return finish_attempt(session, attempt)


def expire_if_due(session: Session, attempt: Attempt, now: datetime | None = None) -> bool:
    """Auto-submit an open exam whose time has run out. Returns True if it was submitted now."""
    if attempt.submitted_at is None and attempt.deadline and seconds_remaining(attempt, now) == 0:
        finish_attempt(session, attempt)
        return True
    return False


def open_exam(session: Session) -> Attempt | None:
    return session.scalar(select(Attempt).where(Attempt.mode == "exam", Attempt.submitted_at.is_(None)).order_by(Attempt.started_at.desc()))


def unit_breakdown(attempt: Attempt) -> list[dict]:
    """Score per unit for the results page."""
    by: dict[str, dict] = {}
    for a in attempt.answers:
        u = by.setdefault(a.question.unit_code, {"unit_code": a.question.unit_code, "total": 0, "correct": 0})
        u["total"] += 1
        u["correct"] += 1 if a.correct else 0
    for u in by.values():
        u["percent"] = round(100 * u["correct"] / u["total"]) if u["total"] else 0
    return sorted(by.values(), key=lambda u: u["unit_code"])
