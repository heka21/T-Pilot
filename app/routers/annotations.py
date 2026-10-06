"""The student's notes, highlights and Pencil ink on lessons (JSON API), the /my-notes page and the export.

Subtopic ids go in the path URL-encoded, as for /progress/{subtopic_id}: /annotations/RBKA%203.6/note.
Bodies are JSON, never form parts: Starlette caps a form part at 1 MB and a page of ink can be larger.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Literal, get_args

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field, ValidationError, model_validator
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import HIGHLIGHT_COLOURS, Subtopic
from app.services import annotations as svc
from app.templating import templates

router = APIRouter(tags=["annotations"])

Colour = Literal["yellow", "green", "pink", "blue"]
assert get_args(Colour) == HIGHLIGHT_COLOURS


class NoteIn(BaseModel):
    text: str = Field("", max_length=svc.NOTE_MAX_CHARS)


class HighlightIn(BaseModel):
    colour: Colour = "yellow"
    exact: str = Field(min_length=1, max_length=svc.EXACT_MAX_CHARS)
    prefix: str = Field("", max_length=64)
    suffix: str = Field("", max_length=64)
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    block_id: str | None = Field(None, max_length=80)
    comment: str = Field("", max_length=svc.COMMENT_MAX_CHARS)

    @model_validator(mode="after")
    def _ordered(self) -> HighlightIn:
        if self.start > self.end:
            raise ValueError("start must not be after end")
        return self


class HighlightPatch(BaseModel):
    colour: Colour | None = None
    comment: str | None = Field(None, max_length=svc.COMMENT_MAX_CHARS)
    orphaned: bool | None = None


class InkIn(BaseModel):
    rev: int = Field(0, ge=0)  # the client's last known rev (informational: last write wins)
    strokes: list[dict]


def _subtopic(session: Session, sid: str) -> Subtopic:
    sub = session.get(Subtopic, sid)
    if sub is None:
        raise HTTPException(status_code=404, detail="Subtopic not found")
    return sub


@router.get("/annotations/{sid}")
def get_annotations(sid: str, session: Session = Depends(get_session)) -> dict:
    sub = _subtopic(session, sid)
    return svc.bundle(session, sub.id)


@router.post("/annotations/{sid}/note")
def save_note(sid: str, body: NoteIn, session: Session = Depends(get_session)) -> dict:
    sub = _subtopic(session, sid)
    updated = svc.save_note(session, sub.id, body.text)
    return {"updated_at": updated.isoformat(timespec="seconds") if updated else None}


@router.post("/annotations/{sid}/highlights", status_code=201)
def add_highlight(sid: str, body: HighlightIn, session: Session = Depends(get_session)) -> dict:
    sub = _subtopic(session, sid)
    return svc.highlight_dict(svc.add_highlight(session, sub.id, body.model_dump()))


@router.patch("/annotations/highlights/{hid}")
def update_highlight(hid: int, body: HighlightPatch, session: Session = Depends(get_session)) -> dict:
    h = svc.update_highlight(session, hid, **body.model_dump(exclude_none=True))
    if h is None:
        raise HTTPException(status_code=404, detail="Highlight not found")
    return svc.highlight_dict(h)


@router.delete("/annotations/highlights/{hid}", status_code=204)
def delete_highlight(hid: int, session: Session = Depends(get_session)) -> Response:
    if not svc.delete_highlight(session, hid):
        raise HTTPException(status_code=404, detail="Highlight not found")
    return Response(status_code=204)


@router.post("/annotations/{sid}/ink/{kind}/{page}")
async def save_ink(sid: str, kind: str, page: int, request: Request, session: Session = Depends(get_session)) -> dict:
    """Replace one ink page: {rev, strokes} -> {rev}. An empty strokes list deletes the page."""
    sub = _subtopic(session, sid)
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > svc.INK_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Ink page too large")
    raw = await request.body()
    if len(raw) > svc.INK_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Ink page too large")
    try:
        body = InkIn.model_validate(json.loads(raw or b"null"))
    except (ValueError, ValidationError) as exc:  # JSONDecodeError is a ValueError
        raise HTTPException(status_code=422, detail=f"Invalid ink payload: {exc}") from exc
    problem = svc.ink_problem(kind, page, body.strokes)
    if problem:
        raise HTTPException(status_code=422, detail=problem)
    return {"rev": svc.save_ink(session, sub.id, kind, page, body.strokes)}


@router.delete("/annotations/{sid}/ink/{kind}/{page}", status_code=204)
def delete_ink(sid: str, kind: str, page: int, session: Session = Depends(get_session)) -> Response:
    sub = _subtopic(session, sid)
    if kind not in svc.INK_KINDS:
        raise HTTPException(status_code=422, detail="Unknown ink kind")
    svc.delete_ink(session, sub.id, kind, page)
    return Response(status_code=204)


@router.get("/my-notes", response_class=HTMLResponse)
def my_notes(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    return templates.TemplateResponse(request, "my_notes.html", svc.summary(session))


@router.get("/my-notes/export.json")
def export_notes(session: Session = Depends(get_session)) -> JSONResponse:
    filename = f"casa-theory-notes-{date.today().isoformat()}.json"
    return JSONResponse(svc.export_all(session), headers={"Content-Disposition": f'attachment; filename="{filename}"'})
