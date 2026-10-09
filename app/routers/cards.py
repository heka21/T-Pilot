"""Flashcards with SM-2 spaced repetition: overview, browse and review.

Review is in exam format: four options in a fresh random order each time (so the position is never the cue), the
card's back as the explanation, and the SM-2 grade from the answer: a wrong pick is "again", a right one asks how
sure the learner was. Cards without options fall back to show-the-back and self-grade.
"""
from __future__ import annotations

import random
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.models import Card, Subtopic, Unit
from app.services import srs
from app.templating import templates

router = APIRouter(prefix="/cards", tags=["cards"])


def review_queue(session: Session, units: list[str], subtopic: Subtopic | None) -> list[Card]:
    """srs.due_cards, narrowed to one subtopic when asked (the service filters by unit only)."""
    if subtopic is None:
        return srs.due_cards(session, unit_codes=units or None)
    cards = srs.due_cards(session, unit_codes=[subtopic.unit_code], limit=10_000, new_limit=10_000)
    return [c for c in cards if c.subtopic_id == subtopic.id][:50]


def filters(units: list[str], subtopic: Subtopic | None) -> dict:
    pairs = [("unit", u) for u in units] + ([("subtopic", subtopic.id)] if subtopic else [])
    return {"units": units, "subtopic": subtopic, "filter_qs": urlencode(pairs)}


def card_context(session: Session, units: list[str], subtopic: Subtopic | None, skip: str | None = None) -> dict:
    queue = review_queue(session, units, subtopic)
    if skip and len(queue) > 1 and queue[0].id == skip:
        queue = queue[1:] + queue[:1]  # don't show the card just failed straight back
    card = queue[0] if queue else None
    return filters(units, subtopic) | {"card": card, "remaining": len(queue), "counts": srs.due_count(session),
                                       "show_back": False, "order": shuffled_order(card)}


def shuffled_order(card: Card | None) -> list[int]:
    """Display order of the card's options, as original option indexes."""
    return random.sample(range(len(card.options)), len(card.options)) if card and card.options else []


def parse_order(raw: str, n: int) -> list[int]:
    try:
        order = [int(x) for x in raw.split(",")]
    except ValueError:
        order = []
    return order if sorted(order) == list(range(n)) else list(range(n))


@router.get("", response_class=HTMLResponse)
def cards_home(request: Request, unit: list[str] = Query(default=[]), subtopic: str | None = None,
               session: Session = Depends(get_session)) -> HTMLResponse:
    sub = session.get(Subtopic, subtopic) if subtopic else None
    units = session.scalars(select(Unit).order_by(Unit.position)).all()
    q = select(Card).options(selectinload(Card.review)).join(Subtopic, Subtopic.id == Card.subtopic_id, isouter=True) \
        .order_by(Subtopic.position, Card.id)
    if sub:
        q = q.where(Card.subtopic_id == sub.id)
    by_unit: dict[str, list[Card]] = {}
    for c in session.scalars(q):
        by_unit.setdefault(c.unit_code, []).append(c)
    ctx = filters(unit, sub) | {"counts": srs.due_count(session), "all_units": units, "by_unit": by_unit,
                                "queue_len": len(review_queue(session, unit, sub))}
    return templates.TemplateResponse(request, "cards.html", ctx)


@router.get("/review", response_class=HTMLResponse)
def cards_review(request: Request, unit: list[str] = Query(default=[]), subtopic: str | None = None,
                 session: Session = Depends(get_session)) -> HTMLResponse:
    sub = session.get(Subtopic, subtopic) if subtopic else None
    return templates.TemplateResponse(request, "cards_review.html", card_context(session, unit, sub))


@router.get("/{card_id}/back", response_class=HTMLResponse)
def card_back(request: Request, card_id: str, unit: list[str] = Query(default=[]), subtopic: str | None = None,
              session: Session = Depends(get_session)) -> HTMLResponse:
    card = session.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    sub = session.get(Subtopic, subtopic) if subtopic else None
    ctx = card_context(session, unit, sub) | {"card": card, "show_back": True}
    return templates.TemplateResponse(request, "card.html", ctx)


@router.post("/{card_id}/answer", response_class=HTMLResponse)
def card_answer(request: Request, card_id: str, given: int = Form(...), order: str = Form(""),
                unit: list[str] = Form(default=[]), subtopic: str = Form(""),
                session: Session = Depends(get_session)) -> HTMLResponse:
    """Mark the pick and show the explanation. Nothing is stored until the grade is posted."""
    card = session.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    if not card.options or given not in range(len(card.options)):
        raise HTTPException(status_code=422, detail="Not an option of this card")
    sub = session.get(Subtopic, subtopic) if subtopic else None
    ctx = card_context(session, unit, sub) | {"card": card, "show_back": True, "given": given,
                                              "correct": given == card.answer,
                                              "order": parse_order(order, len(card.options))}
    return templates.TemplateResponse(request, "card.html", ctx)


@router.post("/{card_id}/grade", response_class=HTMLResponse)
def card_grade(request: Request, card_id: str, grade: int = Form(...), unit: list[str] = Form(default=[]),
               subtopic: str = Form(""), session: Session = Depends(get_session)) -> HTMLResponse:
    if session.get(Card, card_id) is None:
        raise HTTPException(status_code=404, detail="Card not found")
    if grade not in srs.QUALITY:
        raise HTTPException(status_code=422, detail="Grade must be 0 to 3")
    srs.grade_card(session, card_id, grade)
    sub = session.get(Subtopic, subtopic) if subtopic else None
    ctx = card_context(session, unit, sub, skip=card_id) | {"last_grade": grade}
    return templates.TemplateResponse(request, "card.html", ctx)
