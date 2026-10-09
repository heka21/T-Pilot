"""Mistakes: the open questions answered wrong, by subtopic, with a quiz of the due ones."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.services import mistakes
from app.templating import templates

router = APIRouter(tags=["mistakes"])


@router.get("/mistakes", response_class=HTMLResponse)
def mistakes_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    ctx = {"groups": mistakes.open_by_subtopic(session), "counts": mistakes.counts(session),
           "clear_after": mistakes.CLEAR_AFTER}
    return templates.TemplateResponse(request, "mistakes.html", ctx)
