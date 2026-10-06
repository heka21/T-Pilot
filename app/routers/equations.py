"""The equation sheet: every formula the exams need, grouped by topic (content/equations.yaml)."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.models import Equation, Subtopic
from app.seed.equations import EQUATIONS_FILE, EXAMS, load_equations
from app.services.search import markdown_to_text
from app.templating import templates

router = APIRouter(tags=["equations"])


def equation_topics() -> list[dict]:
    """[{id, label}] in sheet order. Topics are content metadata only, so they are read from the file, not the DB."""
    return load_equations(Path(os.environ.get("CONTENT_DIR", "content")) / EQUATIONS_FILE)["topics"]


def haystack(eq: Equation, topic_label: str, subs: dict[str, Subtopic]) -> str:
    """Lower-case text the page's filter box matches: name, when, rule, symbol meanings, tags, topic, lessons."""
    words = [eq.name, markdown_to_text(eq.when), markdown_to_text(eq.rule_of_thumb), topic_label, *eq.tags,
             *(s.get("meaning", "") for s in eq.symbols or [])]
    for sid in eq.lesson_ids:
        words += [sid, sid.replace(" ", ""), subs[sid].title if sid in subs else ""]
    return " ".join(w for w in words if w).lower()


@router.get("/equations", response_class=HTMLResponse)
def equations_page(request: Request, exam: str = "", topic: str = "", q: str = "",
                   session: Session = Depends(get_session)) -> HTMLResponse:
    """The whole sheet. exam/topic/q prefill the filter bar; Alpine does the filtering in the page."""
    equations = list(session.scalars(select(Equation).order_by(Equation.position).options(selectinload(Equation.lessons))))
    used = {e.topic for e in equations}
    topics = [t for t in equation_topics() if t["id"] in used]
    known = {t["id"] for t in topics}
    topics += [{"id": t, "label": t.replace("-", " ").capitalize()} for t in dict.fromkeys(e.topic for e in equations) if t not in known]
    sub_ids = {sid for e in equations for sid in e.lesson_ids}
    subs = {s.id: s for s in session.scalars(select(Subtopic).where(Subtopic.id.in_(sub_ids)).options(selectinload(Subtopic.note)))}
    filters = {"exam": exam if exam in EXAMS else "", "topic": topic if topic in {t["id"] for t in topics} else "", "q": q.strip()}
    labels = {t["id"]: t["label"] for t in topics}
    texts = {e.id: haystack(e, labels.get(e.topic, e.topic), subs) for e in equations}
    return templates.TemplateResponse(request, "equations.html",
                                      {"topics": topics, "equations": equations, "subs": subs, "filters": filters, "texts": texts})
