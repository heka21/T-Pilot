"""SM-2 spaced repetition for flashcards.

Grades: 0 again, 1 hard, 2 good, 3 easy (mapped to SM-2 quality 1, 3, 4, 5).
"""
from __future__ import annotations

from app.util import utcnow

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Card, CardReview, Subtopic

QUALITY = {0: 1, 1: 3, 2: 4, 3: 5}
MIN_EASE = 1.3
NEW_CARDS_PER_DAY = 20


def schedule(review: CardReview, grade: int, today: date | None = None) -> CardReview:
    """Apply one review to the card's SM-2 state (mutates and returns it)."""
    today = today or date.today()
    # Column defaults only apply on flush; a fresh CardReview() has None here.
    review.ease = review.ease if review.ease is not None else 2.5
    review.interval_days = review.interval_days or 0
    review.repetitions = review.repetitions or 0
    review.lapses = review.lapses or 0
    q = QUALITY[grade]
    if q < 3:
        review.repetitions = 0
        review.interval_days = 0  # due again today
        review.lapses += 1
    else:
        if review.repetitions == 0:
            interval = 1
        elif review.repetitions == 1:
            interval = 6
        else:
            interval = round(review.interval_days * review.ease)
        if grade == 1:
            interval = max(1, round(interval * 0.7))
        if grade == 3:
            interval = round(interval * 1.3)
        review.interval_days = max(1, interval)
        review.repetitions += 1
    review.ease = max(MIN_EASE, review.ease + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    review.due = today + timedelta(days=review.interval_days)
    review.last_grade = grade
    review.last_reviewed = utcnow()
    return review


def grade_card(session: Session, card_id: str, grade: int, today: date | None = None) -> CardReview:
    review = session.get(CardReview, card_id)
    if review is None:
        review = CardReview(card_id=card_id)
        session.add(review)
    schedule(review, grade, today)
    session.commit()
    return review


def due_cards(session: Session, today: date | None = None, unit_codes: list[str] | None = None,
              limit: int = 50, new_limit: int = NEW_CARDS_PER_DAY) -> list[Card]:
    """Cards due for review (overdue first), then up to `new_limit` never-seen cards in syllabus order."""
    today = today or date.today()
    base = select(Card).outerjoin(CardReview, CardReview.card_id == Card.id).join(Subtopic, Subtopic.id == Card.subtopic_id, isouter=True)
    if unit_codes:
        base = base.where(Card.unit_code.in_(unit_codes))
    due = list(session.scalars(base.where(CardReview.due <= today).order_by(CardReview.due, Subtopic.position)))
    new = list(session.scalars(base.where(CardReview.card_id.is_(None)).order_by(Subtopic.position, Card.id).limit(new_limit)))
    return (due + new)[:limit]


def due_count(session: Session, today: date | None = None) -> dict:
    today = today or date.today()
    due_n = session.scalar(select(func.count()).select_from(CardReview).where(CardReview.due <= today)) or 0
    seen = session.scalar(select(func.count()).select_from(CardReview)) or 0
    total = session.scalar(select(func.count()).select_from(Card)) or 0
    return {"due": due_n, "new": min(NEW_CARDS_PER_DAY, max(0, total - seen)), "total": total, "seen": seen}
