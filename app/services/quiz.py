"""Practice quizzes: pick questions, mark answers, record attempts."""
from __future__ import annotations

from app.util import utcnow

import random
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Attempt, AttemptAnswer, Question, QuestionElement, Subtopic
from app.services import mistakes
from app.services.progress import element_accuracy


def mark(question: Question, given: str | None) -> bool | None:
    """True/False when answered, None when blank."""
    if given is None or str(given).strip() == "":
        return None
    g = str(given).strip()
    if question.kind == "mcq":
        return g == str(question.answer)
    try:
        value = float(g.replace(",", ""))
    except ValueError:
        return False
    return abs(value - float(question.answer)) <= float(question.tolerance or 0) + 1e-9


def _candidates(session: Session, unit_codes: list[str] | None, subtopic_ids: list[str] | None) -> list[Question]:
    q = select(Question).options(selectinload(Question.elements))
    if subtopic_ids:
        q = q.where(Question.subtopic_id.in_(subtopic_ids))
    elif unit_codes:
        q = q.where(Question.unit_code.in_(unit_codes))
    return list(session.scalars(q))


def pick_questions(session: Session, count: int = 10, unit_codes: list[str] | None = None,
                   subtopic_ids: list[str] | None = None, weak: bool = False,
                   rng: random.Random | None = None) -> list[Question]:
    """Random sample. With weak=True, questions on elements with low or no accuracy are favoured."""
    rng = rng or random.Random()
    pool = _candidates(session, unit_codes, subtopic_ids)
    if not pool:
        return []
    if not weak:
        return rng.sample(pool, min(count, len(pool)))
    acc = element_accuracy(session)

    def weight(q: Question) -> float:
        codes = q.element_codes
        if not codes:
            return 1.0
        scores = [acc[c]["percent"] for c in codes if c in acc]
        if not scores:
            return 2.0  # never tested: high priority
        return 0.25 + (100 - min(scores)) / 100 * 3
    chosen: list[Question] = []
    pool = pool[:]
    weights = [weight(q) for q in pool]
    while pool and len(chosen) < count:
        i = rng.choices(range(len(pool)), weights=weights, k=1)[0]
        chosen.append(pool.pop(i))
        weights.pop(i)
    return chosen


def start_attempt(session: Session, questions: list[Question], mode: str = "quiz", title: str = "",
                  exam_code: str | None = None, config: dict | None = None, deadline: datetime | None = None) -> Attempt:
    attempt = Attempt(mode=mode, title=title, exam_code=exam_code, config=config or {},
                      question_count=len(questions), deadline=deadline)
    session.add(attempt)
    session.flush()
    for i, q in enumerate(questions):
        session.add(AttemptAnswer(attempt_id=attempt.id, question_id=q.id, position=i))
    session.commit()
    return attempt


def record_answer(session: Session, attempt: Attempt, position: int, given: str | None, grade_now: bool = True) -> AttemptAnswer:
    ans = next(a for a in attempt.answers if a.position == position)
    ans.given = given
    ans.answered_at = utcnow()
    if grade_now:
        ans.correct = mark(ans.question, given)
        if ans.correct is not None:
            mistakes.record(session, ans.question_id, ans.correct)
    session.commit()
    return ans


def finish_attempt(session: Session, attempt: Attempt) -> Attempt:
    pass_mark = 70
    if attempt.exam_code:
        from app.models import Exam
        pass_mark = session.get(Exam, attempt.exam_code).pass_mark_percent
    graded_live = attempt.mode == "quiz"  # quiz answers were recorded as mistakes when marked
    for a in attempt.answers:
        a.correct = mark(a.question, a.given)
        if a.correct is not None and not graded_live:
            mistakes.record(session, a.question_id, a.correct)
        if a.correct is None:
            a.correct = False  # unanswered counts as wrong once submitted
    attempt.correct_count = sum(1 for a in attempt.answers if a.correct)
    attempt.score_percent = round(100 * attempt.correct_count / attempt.question_count, 1) if attempt.question_count else 0
    attempt.passed = attempt.score_percent >= pass_mark
    attempt.submitted_at = utcnow()
    session.commit()
    return attempt


def kdr_report(session: Session, attempt: Attempt) -> list[dict]:
    """Knowledge Deficiency Report: wrong answers grouped by subtopic, with the element codes, like CASA's KDR."""
    groups: dict[str, dict] = {}
    for a in attempt.answers:
        if a.correct:
            continue
        q = a.question
        sid = q.subtopic_id
        if sid is None:
            continue
        g = groups.setdefault(sid, {"subtopic": session.get(Subtopic, sid), "elements": set(), "questions": []})
        g["elements"].update(q.element_codes)
        g["questions"].append(q)
    out = []
    for g in groups.values():
        g["elements"] = sorted(g["elements"])
        out.append(g)
    out.sort(key=lambda g: g["subtopic"].position)
    return out
