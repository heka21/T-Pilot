import random

from app.models import Element, Exam, Question, QuestionElement
from app.services import exam as exam_svc
from app.services.quiz import kdr_report, mark, pick_questions, record_answer, start_attempt, finish_attempt
from tests._db import fresh_session


def add_questions(session, unit, n, element_code):
    subtopic_id = session.get(Element, element_code).subtopic_id
    for i in range(n):
        qid = f"{unit}-ZZ{i:03d}"
        session.add(Question(id=qid, unit_code=unit, subtopic_id=subtopic_id, kind="mcq", stem=f"{unit} q{i}",
                             options=["a", "b", "c", "d"], answer="0", explanation="x"))
        session.flush()
        session.add(QuestionElement(question_id=qid, element_code=element_code))
    session.commit()


def test_allocate_largest_remainder():
    assert exam_svc.allocate(60, {"A": 30, "B": 25, "C": 25, "D": 8, "E": 12}) == {"A": 18, "B": 15, "C": 15, "D": 5, "E": 7}
    assert sum(exam_svc.allocate(7, {"A": 1, "B": 1, "C": 1}).values()) == 7


def test_mark_mcq_and_numeric():
    s = fresh_session()
    q1, q2 = s.get(Question, "RBKA-001"), s.get(Question, "RBKA-002")
    assert mark(q1, "1") is True and mark(q1, "0") is False and mark(q1, "") is None
    assert mark(q2, "68") and mark(q2, "67") and mark(q2, "69") and not mark(q2, "70") and not mark(q2, "abc")


def test_exam_sampling_respects_weights_and_fills_shortfall():
    s = fresh_session()
    exam = s.get(Exam, "RPLA")
    weights = {eu.unit_code: eu.weight for eu in exam.units}
    qs = exam_svc.sample_exam_questions(s, exam, random.Random(1))
    assert len(qs) == exam.question_count == 60
    by_unit = {}
    for q in qs:
        by_unit[q.unit_code] = by_unit.get(q.unit_code, 0) + 1
    assert by_unit == exam_svc.allocate(60, weights)  # every unit has enough questions in the real content
    assert len({q.id for q in qs}) == 60
    # Empty one unit: its share is filled from the others' spare questions.
    from sqlalchemy import delete
    from app.models import QuestionElement
    rmtc_ids = [q.id for q in s.query(Question).filter(Question.unit_code == "RMTC")]
    s.execute(delete(QuestionElement).where(QuestionElement.question_id.in_(rmtc_ids)))
    s.execute(delete(Question).where(Question.unit_code == "RMTC"))
    s.commit()
    qs = exam_svc.sample_exam_questions(s, exam, random.Random(2))
    assert len(qs) == 60 and not any(q.unit_code == "RMTC" for q in qs)


def test_exam_flow_and_kdr():
    s = fresh_session()
    add_questions(s, "BAKC", 60, "BAKC 2.1.1")
    attempt = exam_svc.start_exam(s, "RPLA", random.Random(2))
    assert attempt.deadline is not None and exam_svc.seconds_remaining(attempt) > 7000
    for a in attempt.answers:
        record_answer(s, attempt, a.position, a.question.answer if a.position % 2 == 0 else "-1", grade_now=False)
    assert all(a.correct is None for a in attempt.answers)
    exam_svc.submit_exam(s, attempt)
    assert attempt.score_percent == 50.0 and attempt.passed is False
    report = kdr_report(s, attempt)
    assert report and report[0]["subtopic"].id in {"BAKC 2.1", "RBKA 3.6"}
    assert any("BAKC 2.1.1" in g["elements"] for g in report)
    assert exam_svc.open_exam(s) is None


def test_weak_quiz_prefers_untested_then_wrong():
    s = fresh_session()
    qs = pick_questions(s, 3, unit_codes=["RBKA"], rng=random.Random(0))
    att = start_attempt(s, qs, title="t")
    for a in att.answers:
        record_answer(s, att, a.position, "9")  # all wrong
    finish_attempt(s, att)
    weak = pick_questions(s, 2, unit_codes=["RBKA"], weak=True, rng=random.Random(0))
    assert len(weak) == 2
