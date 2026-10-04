"""Global search page (full page, or the results block alone for HTMX live search) and the top-bar suggestions."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.services import search as search_svc
from app.templating import templates

router = APIRouter(tags=["search"])


@router.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: str = Query("", max_length=200), kind: str | None = None,
                session: Session = Depends(get_session)) -> HTMLResponse:
    if kind not in search_svc.KINDS:
        kind = None
    content_dir = Path(os.environ.get("CONTENT_DIR", "content"))
    results = search_svc.search(session, q, content_dir, kind)
    partial = request.headers.get("HX-Request") == "true" and request.headers.get("HX-Target") == "search-results"
    template = "_search_results.html" if partial else "search.html"
    return templates.TemplateResponse(request, template, results)


@router.get("/search/suggest", response_class=HTMLResponse)
def search_suggest(request: Request, q: str = Query("", max_length=200),
                   session: Session = Depends(get_session)) -> HTMLResponse:
    content_dir = Path(os.environ.get("CONTENT_DIR", "content"))
    return templates.TemplateResponse(request, "_search_suggest.html", search_svc.suggest(session, q, content_dir))
