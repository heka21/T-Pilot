"""User-reported content issues ("flags")."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Flag
from app.templating import templates

router = APIRouter(prefix="/flags", tags=["flags"])


@router.post("", response_class=HTMLResponse)
def create_flag(
    kind: str = Form("other"),
    ref: str = Form(""),
    message: str = Form(...),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    session.add(Flag(kind=kind[:16], ref=ref[:80], message=message.strip()))
    session.commit()
    return HTMLResponse('<p class="flag-thanks"><small>Thanks, noted.</small></p>')


@router.get("", response_class=HTMLResponse)
def list_flags(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    flags = session.scalars(select(Flag).where(Flag.resolved.is_(False)).order_by(Flag.created_at.desc())).all()
    return templates.TemplateResponse(request, "flags.html", {"flags": flags})


@router.post("/{flag_id}/resolve")
def resolve_flag(flag_id: int, request: Request, session: Session = Depends(get_session)) -> Response:
    flag = session.get(Flag, flag_id)
    if flag is None:
        raise HTTPException(status_code=404, detail="Flag not found")
    flag.resolved = True
    session.commit()
    if request.headers.get("HX-Request"):
        return HTMLResponse("")  # HTMX swaps the row out
    return RedirectResponse("/flags", status_code=303)
