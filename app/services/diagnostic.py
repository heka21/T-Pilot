"""Diagnostic placement test: find the RPLA subtopics you already know so the plan can skip them.

Round 1 asks one question per subtopic. Round 2 asks a second question, on another element where there is one,
for every subtopic answered right in round 1. Two out of two marks a subtopic as looking known. No feedback is
given until the end, and "I don't know" is an answer (it counts as wrong, but not as a mistake to retry).
"""
from __future__ import annotations

import random

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Attempt, AttemptAnswer, Question, Subtopic
from app.services import planner, progress
from app.services.exam import last_answered
from app.services.quiz import finish_attempt, mark, start_attempt

EXAM = "RPLA"


def _pick(candidates: list[Question], seen: dict, rng: random.Random, avoid_elements: set[str] = frozenset()) -> Question | None:
    """Best question for a placement check: unseen, on a new element, not a workbook chart, medium difficulty."""
    if not candidates:
        return None
    rng.shuffle(candidates)
    return min(candidates, key=lambda q: (q.id in seen, bool(avoid_elements & set(q.element_codes)),
                                          q.workbook_page is not None, abs(q.difficulty - 2)))


def subtopic_pools(session: Session) -> tuple[list[Subtopic], dict[str, list[Question]]]:
    subs = planner.exam_subtopics(session)[EXAM]
    pools: dict[str, list[Question]] = {s.id: [] for s in subs}
    for q in session.scalars(select(Question).options(selectinload(Question.elements))
                             .where(Question.subtopic_id.in_(list(pools)))):
        pools[q.subtopic_id].append(q)
    return [s for s in subs if pools[s.id]], pools


def start(session: Session, rng: random.Random | None = None) -> Attempt:
    rng = rng or random.Random()
    subs, pools = subtopic_pools(session)
    seen = last_answered(session)
    questions = [_pick(pools[s.id], seen, rng) for s in subs]
    return start_attempt(session, questions, mode="diagnostic", title=f"{EXAM} diagnostic", exam_code=EXAM,
                         config={"round": 1, "round1_count": len(questions)})


def open_diagnostic(session: Session) -> Attempt | None:
    return session.scalar(select(Attempt).where(Attempt.mode == "diagnostic", Attempt.submitted_at.is_(None))
                          .order_by(Attempt.started_at.desc()))


def latest(session: Session) -> Attempt | None:
    return session.scalar(select(Attempt).where(Attempt.mode == "diagnostic", Attempt.submitted_at.is_not(None))
                          .order_by(Attempt.submitted_at.desc()))


def round_of(attempt: Attempt, ans: AttemptAnswer) -> int:
    return 1 if ans.position < attempt.config.get("round1_count", len(attempt.answers)) else 2


def round_answers(attempt: Attempt) -> list[AttemptAnswer]:
    """The answers of the round in progress."""
    r = attempt.config.get("round", 1)
    return [a for a in attempt.answers if round_of(attempt, a) == r]


def advance(session: Session, attempt: Attempt, rng: random.Random | None = None) -> bool:
    """Call when the current round is fully answered. Starts round 2 (True) or submits the diagnostic (False)."""
    rng = rng or random.Random()
    if attempt.config.get("round", 1) == 1:
        _, pools = subtopic_pools(session)
        seen = last_answered(session)
        used = {a.question_id for a in attempt.answers}
        follow_ups = []
        for a in attempt.answers:
            if mark(a.question, a.given):
                q = a.question
                spare = [c for c in pools.get(q.subtopic_id, []) if c.id not in used]
                pick = _pick(spare, seen, rng, avoid_elements=set(q.element_codes))
                if pick:
                    follow_ups.append(pick)
                    used.add(pick.id)
        if follow_ups:
            n = len(attempt.answers)
            for i, q in enumerate(follow_ups):
                session.add(AttemptAnswer(attempt_id=attempt.id, question_id=q.id, position=n + i))
            attempt.question_count = n + len(follow_ups)
            attempt.config = attempt.config | {"round": 2}
            session.commit()
            session.refresh(attempt)
            return True
    finish_attempt(session, attempt)
    return False


def classify(attempt: Attempt) -> dict[str, list[dict]]:
    """{"known": [...], "partly": [...], "start": [...]} of {subtopic, right, asked} in syllabus order.

    Known: right in both rounds. Partly: right once (including a subtopic with no second question to ask).
    Start: wrong or "I don't know" in round 1.
    """
    by_sub: dict[str, dict] = {}
    for a in attempt.answers:
        sub = a.question.subtopic_id
        row = by_sub.setdefault(sub, {"subtopic_id": sub, "right": 0, "asked": 0})
        row["asked"] += 1
        row["right"] += 1 if a.correct else 0
    out: dict[str, list[dict]] = {"known": [], "partly": [], "start": []}
    for row in by_sub.values():
        key = "known" if row["right"] >= 2 else "partly" if row["right"] == 1 else "start"
        out[key].append(row)
    return out


def apply(session: Session, subtopic_ids: list[str]) -> int:
    """Mark the chosen subtopics confident and, when a plan exists, replan so it skips them. Returns how many changed."""
    valid = set(session.scalars(select(Subtopic.id).where(Subtopic.id.in_(subtopic_ids))))
    changed = 0
    for sid in subtopic_ids:
        if sid in valid:
            progress.set_status(session, sid, "confident")
            changed += 1
    plan = planner.active_plan(session)
    if plan and changed:
        planner.replan(session, plan)
    return changed
