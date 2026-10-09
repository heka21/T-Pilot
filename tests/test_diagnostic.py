import random
from datetime import date, timedelta

from app.models import Mistake, Progress
from app.services import diagnostic, planner
from app.services.quiz import record_answer
from tests._db import fresh_session


def answer_round(s, attempt, right):
    """Answer every unanswered question of the current round; right(answer) decides each one."""
    for a in diagnostic.round_answers(attempt):
        if a.answered_at is None:
            record_answer(s, attempt, a.position, a.question.answer if right(a) else None, grade_now=False)


def test_round_one_asks_one_question_per_subtopic():
    s = fresh_session()
    att = diagnostic.start(s, random.Random(0))
    subs, _ = diagnostic.subtopic_pools(s)
    assert att.mode == "diagnostic" and att.deadline is None
    assert len(att.answers) == len(subs) == att.config["round1_count"]
    assert sorted(a.question.subtopic_id for a in att.answers) == sorted(x.id for x in subs)
    assert all(a.question.unit_code in {"BAKC", "RBKA", "RFRC", "RMTC", "PHFC"} for a in att.answers)


def test_round_two_only_for_right_answers_then_classify_and_apply():
    s = fresh_session()
    att = diagnostic.start(s, random.Random(1))
    n = len(att.answers)
    right_subs = {a.question.subtopic_id for a in att.answers[:10]}
    answer_round(s, att, lambda a: a.question.subtopic_id in right_subs)
    assert diagnostic.advance(s, att, random.Random(2)) is True
    follow = [a for a in att.answers if a.position >= n]
    assert att.config["round"] == 2 and 0 < len(follow) <= 10
    assert {a.question.subtopic_id for a in follow} <= right_subs
    assert len({a.question_id for a in att.answers}) == len(att.answers)  # no question asked twice
    # Round 2: right on the first five follow-ups only.
    five = {a.position for a in follow[:5]}
    answer_round(s, att, lambda a: a.position in five)
    assert diagnostic.advance(s, att) is False and att.submitted_at is not None
    groups = diagnostic.classify(att)
    known = {r["subtopic_id"] for r in groups["known"]}
    assert known == {a.question.subtopic_id for a in follow[:5]}
    assert len(groups["known"]) + len(groups["partly"]) + len(groups["start"]) == n
    # "I don't know" (blank) is wrong but not a mistake to retry.
    assert s.query(Mistake).count() == 0
    # Apply: statuses set, and the active plan no longer schedules those subtopics.
    today = date.today()
    plan = planner.generate(s, planner.default_settings(today), today)
    assert diagnostic.apply(s, sorted(known) + ["NOPE 1.1"]) == len(known)
    assert all(s.get(Progress, sid).status == "confident" for sid in known)
    plan = planner.active_plan(s)
    future = {it.subtopic_id for it in plan.items if it.kind == "study" and it.date >= today}
    assert not known & future


def test_no_right_answers_finishes_after_round_one():
    s = fresh_session()
    att = diagnostic.start(s, random.Random(3))
    answer_round(s, att, lambda a: False)
    assert diagnostic.advance(s, att) is False
    assert not diagnostic.classify(att)["known"] and diagnostic.open_diagnostic(s) is None
