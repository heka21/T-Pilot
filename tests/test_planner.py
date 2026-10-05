from datetime import date, timedelta

from app.models import PlanItem, Progress
from app.services import planner
from app.services.progress import set_status
from tests._db import fresh_session

TODAY = date(2026, 10, 5)  # a Monday


def make(session, minutes=120, weeks=planner.DEFAULT_WEEKS):
    st = planner.Settings(start_date=TODAY, rpla_exam_date=TODAY + timedelta(days=round(weeks * 7 * planner.RPL_SHARE)),
                          ppla_exam_date=TODAY + timedelta(days=weeks * 7), minutes_per_session=minutes)
    return planner.generate(session, st, TODAY)


def test_default_plan_fits_everything():
    s = fresh_session()
    plan = make(s)
    assert plan.shortfall is None
    study = [it for it in plan.items if it.kind == "study"]
    assert {it.subtopic_id for it in study} == {sub.id for sub in s.query(__import__('app.models', fromlist=['Subtopic']).Subtopic)}
    # RPLA subtopics all land before the RPLA revision days; nothing on exam day itself
    rpla_subs = {sub.id for sub in planner.exam_subtopics(s)["RPLA"]}
    last_rpla_study = max(it.date for it in study if it.subtopic_id in rpla_subs)
    revision_dates = sorted({it.date for it in plan.items if it.kind == "revision" and it.exam_code == "RPLA"} | {it.date for it in plan.items if it.kind == "mock_exam" and it.exam_code == "RPLA" and "Full" in it.label})
    assert last_rpla_study < revision_dates[0] < plan.rpla_exam_date
    assert all(it.date != plan.rpla_exam_date and it.date != plan.ppla_exam_date for it in plan.items)
    # one full mock two study days before each exam, one midway mock per block
    mocks = [it for it in plan.items if it.kind == "mock_exam"]
    assert sum(1 for m in mocks if m.exam_code == "RPLA") == 2 and sum(1 for m in mocks if m.exam_code == "PPLA") == 2
    full_rpla = next(m for m in mocks if m.exam_code == "RPLA" and "Full" in m.label)
    assert (plan.rpla_exam_date - full_rpla.date).days <= 3
    # no study day overloaded beyond the session length (cards overhead, plus the small sliver allowance)
    by_day = planner.items_by_date(plan)
    for d, items in by_day.items():
        assert sum(it.estimated_minutes for it in items if it.kind == "study") <= plan.minutes_per_session - planner.CARDS_MINUTES + planner.MIN_CHUNK
    assert all(d.weekday() in (0, 1, 2, 3, 4, 5) for d in by_day)


def test_short_sessions_report_shortfall_but_keep_plan_complete():
    s = fresh_session()
    plan = make(s, minutes=40)
    assert plan.shortfall and "RPLA" in plan.shortfall
    sf = plan.shortfall["RPLA"]
    assert sf["extra_minutes_per_session"] > 0 and sf["extra_study_days"] > 0
    study = {it.subtopic_id for it in plan.items if it.kind == "study"}
    assert len(study) == 109  # every subtopic is still placed


def test_sync_and_replan_keeps_past_and_completed():
    s = fresh_session()
    plan = make(s)
    first = next(it for it in plan.items if it.kind == "study")
    set_status(s, first.subtopic_id, "studying")
    planner.sync_done(s, plan, TODAY)
    assert first.done_at is not None
    later = TODAY + timedelta(days=10)
    st = planner.status(s, plan, later)
    assert st["days_behind"] > 2 and st["behind"]
    new = planner.replan(s, plan, later)
    assert new.active and not plan.active
    carried = [it for it in new.items if it.date < later]
    assert carried and all(it.date < later for it in carried)
    future_subs = {it.subtopic_id for it in new.items if it.kind == "study" and it.date >= later}
    assert first.subtopic_id not in future_subs
    assert planner.status(s, new, later)["days_behind"] == 0


def test_cards_item_stays_open_while_new_cards_wait():
    s = fresh_session()
    plan = make(s)
    cards = next(it for it in plan.items if it.kind == "cards" and it.date == TODAY)
    planner.sync_done(s, plan, TODAY)  # no reviews yet, so nothing is due, but new cards are waiting
    assert cards.done_at is None


def test_ticking_a_study_item_marks_it_studying():
    s = fresh_session()
    plan = make(s)
    first, second = [it for it in plan.items if it.kind == "study"][:2]
    planner.mark_item(s, first)
    assert s.get(Progress, first.subtopic_id).status == "studying"
    set_status(s, second.subtopic_id, "confident")
    planner.mark_item(s, second)
    assert s.get(Progress, second.subtopic_id).status == "confident"
    planner.mark_item(s, first, done=False)
    assert first.done_at is None and s.get(Progress, first.subtopic_id).status == "studying"


def test_validation():
    bad = planner.Settings(start_date=TODAY, rpla_exam_date=TODAY, ppla_exam_date=TODAY, study_weekdays=[])
    assert len(bad.validate()) >= 3
