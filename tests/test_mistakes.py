import random
from datetime import date, timedelta

from app.models import Mistake, Question
from app.services import exam as exam_svc
from app.services import mistakes
from app.services.quiz import finish_attempt, pick_questions, record_answer, start_attempt
from tests._db import fresh_session

D = date(2026, 10, 9)


def test_wrong_opens_and_right_on_two_days_clears():
    s = fresh_session()
    m = mistakes.record(s, "RBKA-001", False, D)
    assert m.miss_count == 1 and m.streak == 0 and m.due == D + timedelta(days=1) and m.cleared_at is None
    mistakes.record(s, "RBKA-001", True, D)
    mistakes.record(s, "RBKA-001", True, D)  # same day: counts once
    assert m.streak == 1 and m.cleared_at is None and m.due == D + timedelta(days=3)
    mistakes.record(s, "RBKA-001", True, D + timedelta(days=3))
    assert m.streak == 2 and m.cleared_at is not None
    s.commit()
    assert mistakes.counts(s, D) == {"open": 0, "due": 0, "cleared": 1}


def test_miss_resets_streak_and_reopens():
    s = fresh_session()
    m = mistakes.record(s, "RBKA-001", False, D)
    mistakes.record(s, "RBKA-001", True, D)
    mistakes.record(s, "RBKA-001", False, D + timedelta(days=1))
    assert m.streak == 0 and m.miss_count == 2
    mistakes.record(s, "RBKA-001", True, D + timedelta(days=2))
    mistakes.record(s, "RBKA-001", True, D + timedelta(days=5))
    assert m.cleared_at is not None
    mistakes.record(s, "RBKA-001", False, D + timedelta(days=9))
    assert m.cleared_at is None and m.miss_count == 3 and m.streak == 0


def test_right_answer_without_a_mistake_does_nothing():
    s = fresh_session()
    assert mistakes.record(s, "RBKA-001", True, D) is None
    assert s.get(Mistake, "RBKA-001") is None


def test_quiz_answers_are_recorded_live_and_not_twice_on_finish():
    s = fresh_session()
    qs = pick_questions(s, 4, unit_codes=["RBKA"], rng=random.Random(0))
    att = start_attempt(s, qs, title="t")
    record_answer(s, att, 0, "9")  # wrong
    record_answer(s, att, 1, att.answers[1].question.answer)  # right
    finish_attempt(s, att)  # 2 and 3 unanswered: counted wrong in the score, not as mistakes
    assert s.get(Mistake, qs[0].id).miss_count == 1
    assert s.get(Mistake, qs[1].id) is None
    assert s.get(Mistake, qs[2].id) is None and s.get(Mistake, qs[3].id) is None


def test_exam_answers_are_recorded_on_submit():
    s = fresh_session()
    att = exam_svc.start_exam(s, "RPLA", random.Random(3))
    record_answer(s, att, 0, "9", grade_now=False)
    assert s.get(Mistake, att.answers[0].question_id) is None
    exam_svc.submit_exam(s, att)
    assert s.get(Mistake, att.answers[0].question_id).miss_count == 1
    assert mistakes.counts(s)["open"] == 1


def test_quiz_questions_due_first():
    s = fresh_session()
    mistakes.record(s, "RBKA-001", False, D - timedelta(days=5))  # due D-4
    mistakes.record(s, "RBKA-002", False, D + timedelta(days=5))  # due later
    mistakes.record(s, "RBKA-003", False, D - timedelta(days=1))  # due D
    s.commit()
    assert [q.id for q in mistakes.quiz_questions(s, 10)] == ["RBKA-001", "RBKA-003", "RBKA-002"]
    assert mistakes.counts(s, D)["due"] == 2
    groups = mistakes.open_by_subtopic(s)
    assert sum(len(g["mistakes"]) for g in groups) == 3


def test_mistakes_quiz_and_retry_routes(client, session):
    # Make a submitted quiz with one wrong answer, then retry it and start a mistakes quiz.
    q = session.get(Question, "RBKA-001")
    att = start_attempt(session, [q], title="Quiz: RBKA")
    record_answer(session, att, 0, "9")
    finish_attempt(session, att)
    r = client.post(f"/quiz/retry/{att.id}", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/quiz/")
    r = client.post("/quiz/start", data={"mistakes": "1", "count": "10"}, follow_redirects=False)
    assert r.status_code == 303
    assert client.get("/mistakes").status_code == 200
    assert client.get("/quiz?mistakes=1").status_code == 200
