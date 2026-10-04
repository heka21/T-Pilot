"""Shared Jinja2 templates. Routers use: templates.TemplateResponse(request, "page.html", ctx)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

TEMPLATES_DIR = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def minutes_to_hm(minutes: int | float | None) -> str:
    """90 -> '1 h 30 min', 45 -> '45 min', 120 -> '2 h'."""
    if minutes is None:
        return ""
    total = int(round(minutes))
    hours, mins = divmod(total, 60)
    if hours and mins:
        return f"{hours} h {mins} min"
    if hours:
        return f"{hours} h"
    return f"{mins} min"


STATIC_DIR = Path(__file__).parent / "static"


def static_url(path: str) -> str:
    """'app.css' -> '/static/app.css?v=<mtime>', so a rebuilt file gets a new URL and browsers never pair new
    templates with a stale cached stylesheet or script."""
    try:
        version = int((STATIC_DIR / path).stat().st_mtime)
    except OSError:
        return f"/static/{path}"
    return f"/static/{path}?v={version}"


templates.env.globals["app_name"] = "CASA Theory"
templates.env.globals["static_url"] = static_url
templates.env.globals["now"] = datetime.now
templates.env.filters["minutes_to_hm"] = minutes_to_hm


def render(request: Request, name: str, context: dict[str, Any] | None = None, **kwargs: Any) -> HTMLResponse:
    """Shorthand for templates.TemplateResponse(request, name, context)."""
    return templates.TemplateResponse(request, name, context or {}, **kwargs)


# ---------------------------------------------------------------- URL helpers for syllabus/notes pages
# Imported lazily: the routers import this module, so a top-level import would be circular.
def _note_url(subtopic: Any) -> str:
    from app.routers.notes import note_url
    return note_url(subtopic)


def _subtopic_url(subtopic: Any) -> str:
    from app.routers.syllabus import subtopic_url
    return subtopic_url(subtopic)


def status_of(subtopic: Any) -> str:
    """Study status of a Subtopic ('not_started' when no Progress row exists)."""
    row = getattr(subtopic, "progress", None)
    return row.status if row is not None else "not_started"


def dom_id(value: str) -> str:
    """'RBKA 3.6' -> 'RBKA-3-6', safe for HTML ids and CSS selectors."""
    return "".join(c if c.isalnum() else "-" for c in str(value))


STATUS_LABELS = {"not_started": "Not started", "studying": "Studying", "confident": "Confident"}

templates.env.globals["note_url"] = _note_url
templates.env.globals["subtopic_url"] = _subtopic_url
templates.env.globals["status_of"] = status_of
templates.env.globals["STATUS_LABELS"] = STATUS_LABELS
templates.env.filters["dom_id"] = dom_id


def highlight_terms(text: str, terms: list[str]) -> str:
    """Escape text and wrap search-term matches in <mark>. Returns markup-safe HTML."""
    from markupsafe import Markup

    from app.services.search import highlight
    return Markup(highlight(str(text), list(terms or [])))


templates.env.filters["highlight_terms"] = highlight_terms
