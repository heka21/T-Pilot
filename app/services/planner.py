"""Study planner: spreads every subtopic over the study days before each exam, with revision and mock exams.

Rules (see plan): subtopics in syllabus order, RPLA units first then PPLA; each day gets a cards item and,
from the third study day, a short quiz on recent topics; the last `revision_days_before_exam` study days before
each exam are revision only (cards, weak-areas quiz, one full mock two study days before the exam); a midway mock
is inserted in each exam's study window. If the content does not fit, days are overfilled evenly and the plan
records a `shortfall` describing how many extra minutes per session or extra days would be needed.
"""
from __future__ import annotations

from app.util import utcnow

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Attempt, CardReview, Exam, PlanItem, Progress, StudyPlan, Subtopic
from app.services import progress, srs

CARDS_MINUTES = 5
QUIZ_MINUTES = 10
QUIZ_FROM_STUDY_DAY = 3  # 1-based: the third study day gets the first quiz
REVISION_QUIZ_MINUTES = 25
MIN_CHUNK = 10  # don't leave a sliver of a subtopic for the next day
DEFAULT_WEEKS = 12  # full lessons total about 5,000 study minutes; 12 weeks Mon-Sat at 120 min is about 6,500
RPL_SHARE = 186 / 320  # knowledge elements in RPLA units over both exams' total


@dataclass
class Settings:
    start_date: date
    rpla_exam_date: date
    ppla_exam_date: date
    study_weekdays: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5])
    minutes_per_session: int = 120
    revision_days_before_exam: int = 4

    def validate(self) -> list[str]:
        errors = []
        if not self.study_weekdays:
            errors.append("Pick at least one study day of the week.")
        if self.rpla_exam_date <= self.start_date:
            errors.append("The RPLA exam date must be after the start date.")
        if self.ppla_exam_date <= self.rpla_exam_date:
            errors.append("The PPLA exam date must be after the RPLA exam date.")
        if self.minutes_per_session < 20:
            errors.append("Sessions need to be at least 20 minutes.")
        return errors


def default_settings(today: date | None = None) -> Settings:
    today = today or date.today()
    total_days = DEFAULT_WEEKS * 7
    return Settings(start_date=today, rpla_exam_date=today + timedelta(days=round(total_days * RPL_SHARE)),
                    ppla_exam_date=today + timedelta(days=total_days))


def settings_from_plan(plan: StudyPlan) -> Settings:
    return Settings(plan.start_date, plan.rpla_exam_date, plan.ppla_exam_date, list(plan.study_weekdays),
                    plan.minutes_per_session, plan.revision_days_before_exam)


def effort_minutes(sub: Subtopic) -> int:
    if sub.note and sub.note.minutes:
        return int(sub.note.minutes)
    return 8 + 5 * len(sub.elements)


def study_days(settings: Settings, start: date, end_exclusive: date) -> list[date]:
    d, out = start, []
    while d < end_exclusive:
        if d.weekday() in settings.study_weekdays:
            out.append(d)
        d += timedelta(days=1)
    return out


def exam_subtopics(session: Session) -> dict[str, list[Subtopic]]:
    """{exam_code: subtopics in syllabus order}; a unit shared by both exams (PHFC) is studied in the RPLA block."""
    exams = {e.code: e for e in session.scalars(select(Exam))}
    subs = list(session.scalars(select(Subtopic).options(selectinload(Subtopic.elements), selectinload(Subtopic.note)).order_by(Subtopic.position)))
    seen: set[str] = set()
    out: dict[str, list[Subtopic]] = {}
    for code in ("RPLA", "PPLA"):
        units = [eu.unit_code for eu in exams[code].units] if code in exams else []
        out[code] = [s for s in subs if s.unit_code in units and s.id not in seen]
        seen.update(s.id for s in out[code])
    return out


# ---------------------------------------------------------------- generation
@dataclass
class _Day:
    date: date
    exam_code: str  # block this day belongs to
    revision: bool = False
    items: list[PlanItem] = field(default_factory=list)
    minutes: int = 0  # study minutes placed so far

    def add(self, kind: str, minutes: int = 0, subtopic: Subtopic | None = None, label: str = "", exam_code: str | None = None) -> PlanItem:
        item = PlanItem(date=self.date, position=len(self.items), kind=kind, estimated_minutes=minutes,
                        subtopic_id=subtopic.id if subtopic else None, exam_code=exam_code or self.exam_code, label=label)
        self.items.append(item)
        if kind == "study":
            self.minutes += minutes
        return item


def _layout_days(settings: Settings, start: date) -> tuple[list[_Day], dict[str, list[_Day]]]:
    """All study days from `start`, tagged with their exam block and revision flag."""
    days: list[_Day] = []
    windows: dict[str, list[_Day]] = {"RPLA": [], "PPLA": []}
    for d in study_days(settings, start, settings.ppla_exam_date):
        if d == settings.rpla_exam_date:
            continue  # exam day: no study scheduled
        days.append(_Day(date=d, exam_code="RPLA" if d < settings.rpla_exam_date else "PPLA"))
    for code in ("RPLA", "PPLA"):
        block = [x for x in days if x.exam_code == code]
        for x in block[len(block) - settings.revision_days_before_exam:] if settings.revision_days_before_exam else []:
            x.revision = True
        windows[code] = [x for x in block if not x.revision]
    return days, windows


def _place(queue: list[tuple[Subtopic, int]], day: _Day, capacity: int) -> None:
    """Fill `day` from the front of `queue` (subtopic, remaining minutes)."""
    while queue and day.minutes < capacity:
        sub, remaining = queue[0]
        room = capacity - day.minutes
        part = sub.id in _parts
        if remaining <= room + MIN_CHUNK:
            _parts[sub.id] = _parts.get(sub.id, 0) + 1
            label = f"{sub.id} {sub.title}" + (f" (part {_parts[sub.id]})" if part else "")
            day.add("study", remaining, sub, label)
            queue.pop(0)
        else:
            _parts[sub.id] = _parts.get(sub.id, 0) + 1
            day.add("study", room, sub, f"{sub.id} {sub.title} (part {_parts[sub.id]})")
            queue[0] = (sub, remaining - room)


_parts: dict[str, int] = {}


def build_items(session: Session, settings: Settings, start: date, completed: set[str] = frozenset()) -> tuple[list[PlanItem], dict | None]:
    """Pure scheduling: returns unsaved PlanItems and a shortfall description (or None)."""
    global _parts
    _parts = {}
    exams = {e.code: e for e in session.scalars(select(Exam))}
    days, windows = _layout_days(settings, start)
    by_exam = exam_subtopics(session)
    queues = {code: [(s, effort_minutes(s)) for s in subs if s.id not in completed] for code, subs in by_exam.items()}
    shortfall: dict[str, dict] = {}

    def capacity(idx: int) -> int:
        return max(0, settings.minutes_per_session - CARDS_MINUTES - (QUIZ_MINUTES if idx + 1 >= QUIZ_FROM_STUDY_DAY else 0))

    # Check fit per block and compute an even overfill allowance if needed.
    extra: dict[str, int] = {"RPLA": 0, "PPLA": 0}
    for code in ("RPLA", "PPLA"):
        need = sum(m for _, m in queues[code])
        wdays = windows[code]
        # PPLA subtopics may also use spare RPLA-window capacity; estimate that spare first.
        spare_rpla = 0
        if code == "PPLA":
            rpla_need = sum(m for _, m in queues["RPLA"])
            rpla_cap = sum(capacity(days.index(x)) for x in windows["RPLA"])
            spare_rpla = max(0, rpla_cap - rpla_need)
        have = sum(capacity(days.index(x)) for x in wdays) + spare_rpla
        if need > have:
            gap = need - have
            per_day = math.ceil(gap / len(wdays)) if wdays else gap
            cap_day = capacity(0) or 1
            shortfall[code] = {"exam": code, "minutes_needed": need, "minutes_available": have, "gap_minutes": gap,
                               "extra_minutes_per_session": per_day, "extra_study_days": math.ceil(gap / cap_day)}
            extra[code] = per_day

    study_idx = 0
    for idx, day in enumerate(days):
        exam = exams.get(day.exam_code)
        if day.revision:
            block = [x for x in days if x.exam_code == day.exam_code and x.revision]
            mock_day = block[-2] if len(block) >= 2 else block[-1]
            day.add("cards", CARDS_MINUTES, label="Flashcards due today")
            if day is mock_day and exam:
                day.add("mock_exam", exam.duration_minutes, label=f"Full {exam.code} mock exam ({exam.duration_minutes // 60} h {exam.duration_minutes % 60:02d} min)", exam_code=exam.code)
            else:
                day.add("revision", REVISION_QUIZ_MINUTES, label=f"Weak-areas quiz for {day.exam_code}", exam_code=day.exam_code)
            continue
        study_idx += 1
        day.add("cards", CARDS_MINUTES, label="Flashcards due today")
        if study_idx >= QUIZ_FROM_STUDY_DAY:
            day.add("quiz", QUIZ_MINUTES, label="Quick quiz on the last week's topics")
        cap = capacity(idx) + extra[day.exam_code]
        if day.exam_code == "RPLA":
            _place(queues["RPLA"], day, cap)
            if not queues["RPLA"]:
                _place(queues["PPLA"], day, cap)  # RPL done early: start PPL content
        else:
            _place(queues["RPLA"], day, cap)  # only when the RPLA block overflowed; shortfall already reported
            _place(queues["PPLA"], day, cap)
    # Anything still queued (extreme shortfall): pile onto the last study day of its block so nothing is lost.
    for code in ("RPLA", "PPLA"):
        if queues[code]:
            tail = windows[code][-1] if windows[code] else days[-1]
            for sub, remaining in queues[code]:
                tail.add("study", remaining, sub, f"{sub.id} {sub.title}")
            queues[code] = []
    # Midway mock in each study window.
    for code, wdays in windows.items():
        exam = exams.get(code)
        if exam and len(wdays) >= 6:
            wdays[len(wdays) // 2].add("mock_exam", exam.duration_minutes, label=f"Midway {code} mock exam", exam_code=code)
    items = [it for d in days for it in d.items]
    for d in days:  # renumber positions after late insertions
        for pos, it in enumerate(d.items):
            it.position = pos
    return items, (shortfall or None)


def generate(session: Session, settings: Settings, today: date | None = None, completed: set[str] | None = None,
             carry_over: list[PlanItem] | None = None) -> StudyPlan:
    """Create and activate a new plan. Deactivates any previous plan."""
    errors = settings.validate()
    if errors:
        raise ValueError(" ".join(errors))
    today = today or date.today()
    start = max(settings.start_date, today)
    completed = set(completed or ())
    for old in session.scalars(select(StudyPlan).where(StudyPlan.active.is_(True))):
        old.active = False
    plan = StudyPlan(start_date=settings.start_date, rpla_exam_date=settings.rpla_exam_date, ppla_exam_date=settings.ppla_exam_date,
                     study_weekdays=list(settings.study_weekdays), minutes_per_session=settings.minutes_per_session,
                     revision_days_before_exam=settings.revision_days_before_exam, active=True)
    session.add(plan)
    session.flush()
    items, shortfall = build_items(session, settings, start, completed)
    plan.shortfall = shortfall
    for it in carry_over or []:
        session.add(PlanItem(plan_id=plan.id, date=it.date, position=it.position, kind=it.kind, subtopic_id=it.subtopic_id,
                             exam_code=it.exam_code, estimated_minutes=it.estimated_minutes, label=it.label, done_at=it.done_at))
    for it in items:
        it.plan_id = plan.id
        session.add(it)
    session.commit()
    return plan


def active_plan(session: Session) -> StudyPlan | None:
    return session.scalar(select(StudyPlan).where(StudyPlan.active.is_(True)).order_by(StudyPlan.id.desc()))


def completed_subtopics(session: Session) -> set[str]:
    return {p.subtopic_id for p in session.scalars(select(Progress)) if p.status != "not_started"}


def replan(session: Session, plan: StudyPlan, today: date | None = None) -> StudyPlan:
    """Keep the past, redistribute every unfinished subtopic over the remaining days."""
    today = today or date.today()
    sync_done(session, plan, today)
    past = [it for it in plan.items if it.date < today and it.done_at]  # undone past work is redistributed
    settings = settings_from_plan(plan)
    settings.start_date = min(settings.start_date, today)
    done_subs = completed_subtopics(session) | {it.subtopic_id for it in plan.items if it.kind == "study" and it.done_at and it.subtopic_id}
    return generate(session, settings, today, completed=done_subs, carry_over=past)


# ---------------------------------------------------------------- tracking
def sync_done(session: Session, plan: StudyPlan, today: date | None = None) -> None:
    """Auto-tick items from what the user actually did."""
    today = today or date.today()
    statuses = {p.subtopic_id: p for p in session.scalars(select(Progress))}
    attempts = list(session.scalars(select(Attempt).where(Attempt.submitted_at.is_not(None))))
    quiz_days = {a.submitted_at.date() for a in attempts if a.mode == "quiz"}
    exam_days = defaultdict(set)
    for a in attempts:
        if a.mode == "exam" and a.exam_code:
            exam_days[a.exam_code].add(a.submitted_at.date())
    review_days = {r.last_reviewed.date() for r in session.scalars(select(CardReview)) if r.last_reviewed}
    cards_today = srs.due_count(session, today) if any(it.kind == "cards" and it.date == today for it in plan.items) else None
    nothing_to_review = cards_today is not None and cards_today["due"] == 0 and cards_today["new"] == 0
    for it in plan.items:
        if it.done_at:
            continue
        if it.kind == "study" and it.subtopic_id in statuses and statuses[it.subtopic_id].status != "not_started":
            it.done_at = statuses[it.subtopic_id].updated_at
        elif it.kind in ("quiz", "revision") and it.date in quiz_days:
            it.done_at = utcnow()
        elif it.kind == "mock_exam" and any(abs((d - it.date).days) <= 1 for d in exam_days.get(it.exam_code, ())):
            it.done_at = utcnow()
        elif it.kind == "cards" and (it.date in review_days or (it.date == today and nothing_to_review)):
            it.done_at = utcnow()
    session.commit()


def mark_item(session: Session, item: PlanItem, done: bool = True) -> PlanItem:
    """Tick or untick an item. Ticking a study item also marks a not-yet-started subtopic as studying."""
    item.done_at = utcnow() if done else None
    session.commit()
    if done and item.kind == "study" and item.subtopic_id:
        row = session.get(Progress, item.subtopic_id)
        if row is None or row.status == "not_started":
            progress.set_status(session, item.subtopic_id, "studying")
    return item


def items_by_date(plan: StudyPlan) -> dict[date, list[PlanItem]]:
    out: dict[date, list[PlanItem]] = defaultdict(list)
    for it in plan.items:
        out[it.date].append(it)
    return dict(sorted(out.items()))


def status(session: Session, plan: StudyPlan, today: date | None = None) -> dict:
    """Today's items, overdue work, days behind/ahead, next exam."""
    today = today or date.today()
    sync_done(session, plan, today)
    cap = max(1, plan.minutes_per_session - CARDS_MINUTES - QUIZ_MINUTES)
    overdue = [it for it in plan.items if it.date < today and not it.done_at and it.kind in ("study", "mock_exam", "revision")]
    behind_minutes = sum(it.estimated_minutes for it in overdue if it.kind == "study") + sum(cap for it in overdue if it.kind != "study")
    ahead_minutes = sum(it.estimated_minutes for it in plan.items if it.date > today and it.done_at and it.kind == "study")
    todays = [it for it in plan.items if it.date == today]
    next_exam = next(((c, d) for c, d in (("RPLA", plan.rpla_exam_date), ("PPLA", plan.ppla_exam_date)) if d >= today), None)
    study_items = [it for it in plan.items if it.kind == "study"]
    done_study = sum(1 for it in study_items if it.done_at)
    return {
        "today": today, "today_items": todays, "overdue": overdue,
        "days_behind": round(behind_minutes / cap, 1), "days_ahead": round(ahead_minutes / cap, 1),
        "behind": behind_minutes > 2 * cap,
        "next_exam": next_exam, "days_to_next_exam": (next_exam[1] - today).days if next_exam else None,
        "study_done": done_study, "study_total": len(study_items),
        "percent": round(100 * done_study / len(study_items)) if study_items else 0,
        "shortfall": plan.shortfall,
    }
