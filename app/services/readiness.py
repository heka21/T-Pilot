"""Exam readiness: a predicted score from recent answers, and a "ready to book" checklist.

Per unit, readiness is the accuracy of the last RECENT answers, weighted so newer answers count more (half-life
HALF_LIFE answers) and a repeat of a question already seen counts REPEAT_WEIGHT of a first exposure, because a
question answered before partly tests memory of it. The predicted score weights units by the exam's weighting.

The checklist thresholds are the app's own margin over CASA's 70% pass mark: a candidate who only just reaches
70% at home has little room for exam-day nerves or an unlucky draw.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Attempt, AttemptAnswer, Element, Exam, Mistake, Question, QuestionElement

RECENT = 40
HALF_LIFE = 20
REPEAT_WEIGHT = 0.5
MIN_ANSWERS = 15  # below this a unit's readiness is shown as a low-confidence estimate

MOCKS_NEEDED = 3
MOCK_SCORE = 80
MOCK_FRESH_SHARE = 0.7
UNIT_READINESS = 75
COVERAGE = 90
MISTAKE_MAX_AGE_DAYS = 14


def _answers(session: Session, unit_codes: list[str]) -> list[tuple[str, str, bool, object]]:
    """(unit_code, question_id, correct, answered_at) for every answered, marked answer, oldest first."""
    rows = session.execute(
        select(Question.unit_code, AttemptAnswer.question_id, AttemptAnswer.correct, AttemptAnswer.answered_at)
        .join(Question, Question.id == AttemptAnswer.question_id)
        .where(AttemptAnswer.correct.is_not(None), AttemptAnswer.answered_at.is_not(None),
               AttemptAnswer.given.is_not(None), Question.unit_code.in_(unit_codes))
        .order_by(AttemptAnswer.answered_at, AttemptAnswer.id)
    ).all()
    return [tuple(r) for r in rows]


def unit_readiness(session: Session, exam_code: str) -> list[dict]:
    """[{unit_code, weight, answered, readiness (0-100 or None), confident, coverage (0-100), elements, covered}]."""
    exam = session.get(Exam, exam_code)
    codes = [eu.unit_code for eu in exam.units]
    by_unit: dict[str, list[tuple[bool, bool]]] = defaultdict(list)  # (correct, first exposure), oldest first
    seen: set[str] = set()
    for unit, qid, correct, _ in _answers(session, codes):
        by_unit[unit].append((bool(correct), qid not in seen))
        seen.add(qid)
    elements = defaultdict(set)
    for code, unit in session.execute(select(Element.code, Element.subtopic_id)):
        elements[unit.split()[0]].add(code)
    covered = defaultdict(set)
    if seen:
        for code in session.scalars(select(QuestionElement.element_code).where(QuestionElement.question_id.in_(seen))):
            covered[code.split()[0]].add(code)
    out = []
    for eu in exam.units:
        recent = by_unit[eu.unit_code][-RECENT:]
        num = den = 0.0
        for age, (correct, first) in enumerate(reversed(recent)):
            w = 0.5 ** (age / HALF_LIFE) * (1.0 if first else REPEAT_WEIGHT)
            num += w * correct
            den += w
        total_el = len(elements[eu.unit_code])
        n_cov = len(covered[eu.unit_code] & elements[eu.unit_code])
        out.append({
            "unit_code": eu.unit_code, "unit": eu.unit, "weight": eu.weight,
            "answered": len(by_unit[eu.unit_code]),
            "readiness": round(100 * num / den) if den else None,
            "confident": len(by_unit[eu.unit_code]) >= MIN_ANSWERS,
            "elements": total_el, "covered": n_cov,
            "coverage": round(100 * n_cov / total_el) if total_el else 0,
        })
    return out


def predicted_score(units: list[dict]) -> int | None:
    """Exam-weighted readiness, or None until every unit has at least one answer."""
    if not units or any(u["readiness"] is None for u in units):
        return None
    wsum = sum(u["weight"] for u in units) or 1
    return round(sum(u["readiness"] * u["weight"] for u in units) / wsum)


def mock_history(session: Session, exam_code: str) -> list[dict]:
    """Submitted mocks oldest first: [{attempt, date, score, fresh_share (0-1 or None), passed}]."""
    rows = session.scalars(select(Attempt).where(Attempt.mode == "exam", Attempt.exam_code == exam_code,
                                                 Attempt.submitted_at.is_not(None)).order_by(Attempt.submitted_at))
    out = []
    for a in rows:
        fresh = (a.config or {}).get("fresh")
        out.append({"attempt": a, "date": a.submitted_at.date(), "score": a.score_percent or 0,
                    "fresh_share": fresh / a.question_count if fresh is not None and a.question_count else None,
                    "passed": bool(a.passed)})
    return out


def _open_mistake_age(session: Session, unit_codes: list[str], today: date) -> int | None:
    ts = session.scalars(select(Mistake.last_missed_at).join(Question, Question.id == Mistake.question_id)
                         .where(Mistake.cleared_at.is_(None), Question.unit_code.in_(unit_codes))
                         .order_by(Mistake.last_missed_at).limit(1)).first()
    return (today - ts.date()).days if ts else None


def report(session: Session, exam_code: str, today: date | None = None) -> dict:
    """Everything the readiness card shows: units, predicted score, mock history and the checklist."""
    today = today or date.today()
    exam = session.get(Exam, exam_code)
    units = unit_readiness(session, exam_code)
    mocks = mock_history(session, exam_code)
    last = mocks[-MOCKS_NEEDED:]
    good = [m for m in last if m["score"] >= MOCK_SCORE and (m["fresh_share"] or 0) >= MOCK_FRESH_SHARE]
    total_el = sum(u["elements"] for u in units)
    coverage = round(100 * sum(u["covered"] for u in units) / total_el) if total_el else 0
    weakest = min((u for u in units if u["readiness"] is not None), key=lambda u: u["readiness"], default=None)
    units_ok = all(u["readiness"] is not None and u["confident"] and u["readiness"] >= UNIT_READINESS for u in units)
    age = _open_mistake_age(session, [u["unit_code"] for u in units], today)
    checks = [
        {"key": "mocks", "ok": len(last) == MOCKS_NEEDED and len(good) == MOCKS_NEEDED,
         "label": f"Last {MOCKS_NEEDED} mocks all {MOCK_SCORE}% or more, mostly on fresh questions",
         "value": f"{len(good)} of the last {MOCKS_NEEDED}" if mocks else "No mocks yet"},
        {"key": "units", "ok": units_ok,
         "label": f"Every unit at {UNIT_READINESS}% readiness or more ({MIN_ANSWERS}+ answers each)",
         "value": (f"Weakest: {weakest['unit_code']} {weakest['readiness']}%" if weakest else "No answers yet")},
        {"key": "coverage", "ok": coverage >= COVERAGE,
         "label": f"Questions answered on {COVERAGE}% of the syllabus elements",
         "value": f"{coverage}%"},
        {"key": "mistakes", "ok": age is None or age <= MISTAKE_MAX_AGE_DAYS,
         "label": f"No mistake left open for more than {MISTAKE_MAX_AGE_DAYS} days",
         "value": "None open" if age is None else f"Oldest {age} day{'' if age == 1 else 's'}"},
    ]
    return {"exam": exam, "units": units, "predicted": predicted_score(units),
            "low_confidence": not all(u["confident"] for u in units), "pass_mark": exam.pass_mark_percent,
            "mocks": mocks, "coverage": coverage, "checks": checks, "ready": all(c["ok"] for c in checks)}
