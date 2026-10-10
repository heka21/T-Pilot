"""Narrated lessons: the /listen page, the player's queue and progress endpoints, and Watch mode."""
from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_session
from app.routers.syllabus import get_subtopic
from app.services import audio
from app.templating import templates

router = APIRouter(tags=["listen"])

_FIGURE_RE = re.compile(r'<figure class="visual[^"]*" data-visual="([^"]+)">.*?</figure>', re.S)


def script_json(value: object) -> str:
    """JSON safe inside <script type="application/json">: a "</script>" in a caption must not end the element."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


@router.get("/listen", response_class=HTMLResponse)
def listen_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    groups = audio.unit_summaries(session)
    return templates.TemplateResponse(request, "listen.html", {
        "groups": groups,
        "resume": audio.last_played(session),
        "total_seconds": sum(g["seconds"] for g in groups),
        "narrated": sum(len(g["lessons"]) for g in groups),
        "lessons": sum(len(g["lessons"]) + g["missing"] for g in groups),
    })


@router.get("/listen/queue")
def listen_queue(start: str, scope: str = "exam", session: Session = Depends(get_session)) -> JSONResponse:
    """Lessons with narration from `start` on, for the player's auto-advance. scope: unit, exam or all."""
    if scope not in ("unit", "exam", "all"):
        raise HTTPException(400, "scope must be unit, exam or all")
    return JSONResponse(audio.queue(session, start, scope))


class ProgressIn(BaseModel):
    sid: str
    position: float
    duration: float


@router.post("/listen/progress")
def listen_progress(body: ProgressIn, session: Session = Depends(get_session)) -> dict:
    """The player reports its place every few seconds while playing, and on pause and page hide (sendBeacon)."""
    try:
        row = audio.save_progress(session, body.sid, body.position, body.duration)
    except KeyError:
        raise HTTPException(404, f"unknown lesson {body.sid}")
    return {"sid": row.subtopic_id, "position": row.position, "completed": row.completed_at is not None}


@router.get("/lessons/{unit}/{number}/watch", response_class=HTMLResponse)
def watch_page(unit: str, number: str, request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    """Watch mode: the narration with each visual full-screen as the narrator reaches it, and live captions."""
    sub = get_subtopic(session, unit, number)
    lesson = audio.for_subtopic(session, sub)
    if lesson is None or sub.note is None:
        raise HTTPException(404, f"{sub.id} has no narration yet")
    data = audio.meta(sub.id) or {}
    # The visuals exactly as the lesson renders them (figure, caption and "what to notice"), keyed "diagram:slug".
    figures = {m.group(1): m.group(0) for m in _FIGURE_RE.finditer(sub.note.html)}
    visuals = [(f"{k}:{s}", figures[f"{k}:{s}"]) for k, s in audio.visual_cues(data) if f"{k}:{s}" in figures]
    timeline = {"chapters": data.get("chapters", []), "cues": data.get("cues", []), "captions": data.get("captions", [])}
    return templates.TemplateResponse(request, "watch.html", {
        "sub": sub, "note": sub.note, "lesson": lesson, "visuals": visuals,
        "lesson_json": script_json(lesson), "timeline_json": script_json(timeline),
    })
