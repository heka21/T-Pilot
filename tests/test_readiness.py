import random
from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.models import Attempt, AttemptAnswer, Question
from app.services import exam as exam_svc
from app.services import readiness
from app.services.quiz import finish_attempt, record_answer, start_attempt
from tests._db import fresh_session


def answer(s, questions, right: bool, when: datetime | None = None, mode="quiz"):
    att = start_attempt(s, questions, mode=mode, title="t")
    for a in att.answers:
        record_answer(s, att, a.position, a.question.answer if right else "9")
        if when:
            a.answered_at = when
    s.commit()
    finish_attempt(s, att)
    return att


def unit_row(s, code):
    return next(u for u in readiness.unit_readiness(s, "RPLA") if u["unit_code"] == code)


def test_no_answers():
    s = fresh_session()
    rep = readiness.report(s, "RPLA")
    assert rep["predicted"] is None and not rep["ready"]
    assert all(u["readiness"] is None and u["coverage"] == 0 for u in rep["units"])


def test_recent_answers_count_more_and_repeats_less():
    s = fresh_session()
    qs = list(s.scalars(select(Question).where(Question.unit_code == "RMTC").order_by(Question.id)))[:10]
    answer(s, qs, False, datetime(2026, 1, 1))
    answer(s, qs, True, datetime(2026, 2, 1))  # repeats of the same ten, now right
    u = unit_row(s, "RMTC")
    assert u["answered"] == 20 and u["confident"]
    # Wrong answers were first exposures (weight 1, older); right ones repeats (weight 0.5, newer).
    assert 30 < u["readiness"] < 55
    fresh = list(s.scalars(select(Question).where(Question.unit_code == "RMTC").order_by(Question.id)))[10:14]
    answer(s, fresh, True, datetime(2026, 3, 1))
    assert unit_row(s, "RMTC")["readiness"] > u["readiness"]
    assert unit_row(s, "RMTC")["coverage"] > 0


def test_predicted_score_weights_units():
    units = [{"readiness": 100, "weight": 3}, {"readiness": 50, "weight": 1}]
    assert readiness.predicted_score(units) == 88
    assert readiness.predicted_score(units + [{"readiness": None, "weight": 1}]) is None


def test_checklist_ready_when_everything_is_met():
    s = fresh_session()
    exam = s.get(readiness.Exam, "RPLA")
    codes = [eu.unit_code for eu in exam.units]
    # Answer every RPLA question right once: full coverage, every unit confident and at 100%.
    qs = list(s.scalars(select(Question).where(Question.unit_code.in_(codes))))
    answer(s, qs, True)
    for i in range(3):  # three mocks at 100%, each recorded as fresh
        att = exam_svc.start_exam(s, "RPLA", random.Random(i))
        att.config = att.config | {"fresh": 60}
        for a in att.answers:
            record_answer(s, att, a.position, a.question.answer, grade_now=False)
        exam_svc.submit_exam(s, att)
    rep = readiness.report(s, "RPLA")
    assert {c["key"]: c["ok"] for c in rep["checks"]} == {"mocks": True, "units": True, "coverage": True, "mistakes": True}
    assert rep["ready"] and rep["predicted"] == 100 and len(rep["mocks"]) == 3
    # An old open mistake blocks it.
    q = qs[0]
    att = start_attempt(s, [q], title="t")
    record_answer(s, att, 0, "9")
    from app.models import Mistake
    s.get(Mistake, q.id).last_missed_at = datetime.now() - timedelta(days=20)
    s.commit()
    rep = readiness.report(s, "RPLA")
    assert not rep["ready"] and not next(c for c in rep["checks"] if c["key"] == "mistakes")["ok"]


def test_mocks_on_seen_questions_do_not_count():
    s = fresh_session()
    for i in range(3):
        att = exam_svc.start_exam(s, "RPLA", random.Random(i))
        att.config = att.config | {"fresh": 10}
        for a in att.answers:
            record_answer(s, att, a.position, a.question.answer, grade_now=False)
        exam_svc.submit_exam(s, att)
    mocks = next(c for c in readiness.report(s, "RPLA")["checks"] if c["key"] == "mocks")
    assert not mocks["ok"]


def test_mock_sampling_prefers_fresh_questions():
    s = fresh_session()
    first = exam_svc.start_exam(s, "RPLA", random.Random(1))
    assert first.config["fresh"] == 60
    for a in first.answers:
        record_answer(s, first, a.position, a.question.answer, grade_now=False)
    exam_svc.submit_exam(s, first)
    second = exam_svc.start_exam(s, "RPLA", random.Random(2))
    seen = {a.question_id for a in first.answers}
    # Each unit has more questions than its share, so a second mock repeats none of the first.
    assert not seen & {a.question_id for a in second.answers}
    assert second.config["fresh"] == 60
