"""Study planner: settings form, status, week view, whole-plan calendar strip, re-plan."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import PlanItem, StudyPlan
from app.services import planner as planner_svc
from app.templating import templates

router = APIRouter(prefix="/planner", tags=["planner"])

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
KIND_LABELS = {"study": "Study", "quiz": "Quiz", "cards": "Cards", "mock_exam": "Mock exam", "revision": "Revision"}


def item_link(item: PlanItem) -> str | None:
    if item.kind == "study" and item.subtopic is not None:
        return f"/notes/{item.subtopic.unit_code}/{item.subtopic.number}"
    return {"quiz": "/quiz", "revision": "/quiz?weak=1", "cards": "/cards", "mock_exam": "/exam"}.get(item.kind)



def parse_week(value: str | None, today: date) -> date:
    try:
        d = date.fromisoformat(value) if value else today
    except ValueError:
        d = today
    return d - timedelta(days=d.weekday())


def week_context(plan: StudyPlan, week_start: date, today: date) -> dict:
    by_date = planner_svc.items_by_date(plan)
    exams = {plan.rpla_exam_date: "RPLA", plan.ppla_exam_date: "PPLA"}
    days = [{"date": d, "items": by_date.get(d, []), "exam": exams.get(d), "today": d == today}
            for d in (week_start + timedelta(days=i) for i in range(7))]
    return {"plan": plan, "week_start": week_start, "week_days": days, "today": today,
            "prev_week": week_start - timedelta(days=7), "next_week": week_start + timedelta(days=7),
            "kind_labels": KIND_LABELS, "item_link": item_link}


def calendar_strip(plan: StudyPlan, today: date) -> list[dict]:
    """One cell per study day (plus exam days): done / partial / missed / upcoming."""
    by_date = planner_svc.items_by_date(plan)
    exams = {plan.rpla_exam_date: "RPLA", plan.ppla_exam_date: "PPLA"}
    cells = []
    prev_month = None
    for d in sorted(set(by_date) | set(exams)):
        items = by_date.get(d, [])
        done = sum(1 for it in items if it.done_at)
        if d in exams:
            state = "exam"
        elif items and done == len(items):
            state = "done"
        elif done:
            state = "partial"
        elif d < today:
            state = "missed"
        else:
            state = "upcoming"
        title = f"{d:%a %-d %b}: " + (f"{exams[d]} exam" if d in exams else f"{done}/{len(items)} done")
        cells.append({"date": d, "state": state, "today": d == today, "title": title,
                      "month_start": prev_month is not None and d.month != prev_month,
                      "week": (d - timedelta(days=d.weekday())).isoformat()})
        prev_month = d.month
    return cells


def form_values(settings: planner_svc.Settings) -> dict:
    return {"start_date": settings.start_date.isoformat(), "rpla_exam_date": settings.rpla_exam_date.isoformat(),
            "ppla_exam_date": settings.ppla_exam_date.isoformat(), "study_weekdays": list(settings.study_weekdays),
            "minutes_per_session": settings.minutes_per_session, "revision_days_before_exam": settings.revision_days_before_exam}


def page_context(session: Session, week: str | None = None, form: dict | None = None, errors: list[str] | None = None) -> dict:
    today = date.today()
    plan = planner_svc.active_plan(session)
    ctx: dict = {"plan": plan, "weekdays": WEEKDAYS, "errors": errors or [], "today": today}
    if plan is None:
        ctx["form"] = form or form_values(planner_svc.default_settings(today))
        return ctx
    ctx["status"] = planner_svc.status(session, plan, today)
    ctx["form"] = form or form_values(planner_svc.settings_from_plan(plan))
    ctx["calendar"] = calendar_strip(plan, today)
    ctx.update(week_context(plan, parse_week(week, today), today))
    return ctx


@router.get("", response_class=HTMLResponse)
def planner_page(request: Request, week: str | None = None, session: Session = Depends(get_session)) -> HTMLResponse:
    return templates.TemplateResponse(request, "planner.html", page_context(session, week))


@router.get("/week", response_class=HTMLResponse)
def planner_week(request: Request, week: str | None = None, session: Session = Depends(get_session)) -> Response:
    plan = planner_svc.active_plan(session)
    if plan is None:
        return RedirectResponse("/planner", status_code=303)
    today = date.today()
    return templates.TemplateResponse(request, "planner_week.html", week_context(plan, parse_week(week, today), today))


@router.post("/generate", response_class=HTMLResponse)
async def planner_generate(request: Request, session: Session = Depends(get_session)) -> Response:
    data = await request.form()
    form = {k: data.get(k, "") for k in ("start_date", "rpla_exam_date", "ppla_exam_date",
                                          "minutes_per_session", "revision_days_before_exam")}
    form["study_weekdays"] = [int(x) for x in data.getlist("study_weekdays") if str(x).isdigit() and int(x) in range(7)]
    errors: list[str] = []
    try:
        settings = planner_svc.Settings(
            start_date=date.fromisoformat(str(form["start_date"])),
            rpla_exam_date=date.fromisoformat(str(form["rpla_exam_date"])),
            ppla_exam_date=date.fromisoformat(str(form["ppla_exam_date"])),
            study_weekdays=form["study_weekdays"],
            minutes_per_session=int(form["minutes_per_session"] or 0),
            revision_days_before_exam=int(form["revision_days_before_exam"] or 0),
        )
    except ValueError:
        settings = None
        errors.append("Enter valid dates and whole numbers for every field.")
    if settings is not None:
        errors = settings.validate()
        if settings.revision_days_before_exam < 0:
            errors.append("Revision days cannot be negative.")
    if errors:
        ctx = page_context(session, form=form, errors=errors) | {"show_form": True}
        return templates.TemplateResponse(request, "planner.html", ctx, status_code=422)
    try:
        planner_svc.generate(session, settings)
    except ValueError as exc:  # pragma: no cover - validate() already ran
        ctx = page_context(session, form=form, errors=[str(exc)]) | {"show_form": True}
        return templates.TemplateResponse(request, "planner.html", ctx, status_code=422)
    return RedirectResponse("/planner", status_code=303)


@router.post("/replan")
def planner_replan(session: Session = Depends(get_session)) -> Response:
    plan = planner_svc.active_plan(session)
    if plan is not None:
        planner_svc.replan(session, plan)
    return RedirectResponse("/planner", status_code=303)


@router.post("/item/{item_id}/toggle", response_class=HTMLResponse)
def planner_toggle(request: Request, item_id: int, session: Session = Depends(get_session)) -> Response:
    item = session.get(PlanItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Plan item not found")
    planner_svc.mark_item(session, item, done=item.done_at is None)
    if not request.headers.get("HX-Request"):
        return RedirectResponse(f"/planner?week={item.date.isoformat()}", status_code=303)
    return templates.TemplateResponse(request, "planner_item.html", {"item": item, "kind_labels": KIND_LABELS, "item_link": item_link})
