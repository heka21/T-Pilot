"""Narrated lessons: the .mp3/.json pairs tools/audio/build.py writes to MEDIA_DIR/audio/<UNIT>/<n.n>.*, and where the
student is in each (ListenProgress). The app serves MEDIA_DIR at /media; nothing here needs the TTS dependencies.

A lesson's narration is described to the player (app/static/player.js) by `descriptor()`; Watch mode also reads the
captions and visual cues from `meta()`.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ExamUnit, ListenProgress, Subtopic, Unit
from app.util import utcnow

COMPLETE_WITHIN = 20.0   # seconds from the end that count as heard to the end (the sign-off and the closing silence)

_cache: dict[Path, tuple[float, dict]] = {}


def media_dir() -> Path:
    return Path(os.environ.get("MEDIA_DIR", "media"))


def _paths(subtopic_id: str) -> tuple[Path, Path]:
    unit, number = subtopic_id.split()
    base = media_dir() / "audio" / unit
    return base / f"{number}.mp3", base / f"{number}.json"


def meta(subtopic_id: str) -> dict | None:
    """The build's .json for a lesson (duration, chapters, cues, captions), or None when it has no narration yet.
    Cached by mtime, so a rebuilt lesson is picked up without a restart."""
    mp3, path = _paths(subtopic_id)
    try:
        mtime = path.stat().st_mtime
        if not mp3.is_file():
            return None
    except OSError:
        return None
    hit = _cache.get(path)
    if hit and hit[0] == mtime:
        return hit[1]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    _cache[path] = (mtime, data)
    return data


def available() -> set[str]:
    """Subtopic ids that have narration."""
    root = media_dir() / "audio"
    return {f"{p.parent.name} {p.stem}" for p in root.glob("*/*.json") if p.with_suffix(".mp3").is_file()}


def progress_map(session: Session) -> dict[str, ListenProgress]:
    return {p.subtopic_id: p for p in session.scalars(select(ListenProgress))}


def finished(row: ListenProgress) -> bool:
    """At the end of the narration (so the next play starts from the top)."""
    return bool(row.duration) and row.position >= row.duration - COMPLETE_WITHIN


def descriptor(sub: Subtopic, data: dict, progress: ListenProgress | None = None) -> dict:
    """Everything the player needs to play one lesson: JSON-safe, embedded in pages as data-listen."""
    from app.routers.notes import note_url
    unit, number = sub.id.split()
    position = progress.position if progress and not finished(progress) else 0.0
    return {
        "sid": sub.id,
        "title": sub.note.title if sub.note else sub.title,
        "unit": unit,
        "src": f"/media/audio/{unit}/{number}.mp3?v={data.get('script_sha', '')}{data.get('voice', '')}",
        "duration": data.get("duration", 0),
        "chapters": data.get("chapters", []),
        "lesson_url": note_url(sub),
        "watch_url": f"{note_url(sub)}/watch",
        "position": round(position, 1),
        "completed": bool(progress and progress.completed_at),
    }


def for_subtopic(session: Session, sub: Subtopic) -> dict | None:
    data = meta(sub.id)
    if data is None:
        return None
    return descriptor(sub, data, session.get(ListenProgress, sub.id))


def ordered_subtopics(session: Session, exam: str | None = None) -> list[Subtopic]:
    """Lessons in syllabus order; for an exam, its units in the exam's order (RPLA: BAKC, RBKA, ...)."""
    query = select(Subtopic).options(selectinload(Subtopic.note)).order_by(Subtopic.position)
    subs = [s for s in session.scalars(query) if s.note]
    if not exam:
        return subs
    order = {eu.unit_code: eu.position for eu in session.scalars(select(ExamUnit).where(ExamUnit.exam_code == exam))}
    return sorted((s for s in subs if s.unit_code in order), key=lambda s: (order[s.unit_code], s.position))


def queue(session: Session, start: str, scope: str = "exam") -> list[dict]:
    """The lessons with narration from `start` onwards, for auto-advance. scope: 'unit' (the rest of start's unit),
    'exam' (the rest of the first exam that includes start's unit, RPLA before PPLA) or 'all'."""
    start_sub = session.get(Subtopic, start)
    if start_sub is None:
        return []
    exam = None
    if scope == "exam":
        codes = [eu.exam_code for eu in session.scalars(select(ExamUnit).where(ExamUnit.unit_code == start_sub.unit_code))]
        exam = "RPLA" if "RPLA" in codes else (codes[0] if codes else None)
    subs = ordered_subtopics(session, exam)
    if scope == "unit":
        subs = [s for s in subs if s.unit_code == start_sub.unit_code]
    ids = [s.id for s in subs]
    if start not in ids:
        return []
    progress = progress_map(session)
    out = []
    for s in subs[ids.index(start):]:
        data = meta(s.id)
        if data is not None:
            out.append(descriptor(s, data, progress.get(s.id)))
    return out


def save_progress(session: Session, subtopic_id: str, position: float, duration: float) -> ListenProgress:
    if session.get(Subtopic, subtopic_id) is None:
        raise KeyError(subtopic_id)
    row = session.get(ListenProgress, subtopic_id)
    if row is None:
        row = ListenProgress(subtopic_id=subtopic_id)
        session.add(row)
    row.position = max(0.0, float(position))
    row.duration = max(0.0, float(duration))
    # Once heard to the end the tick stays, even when the lesson is played again from the start.
    if finished(row) and row.completed_at is None:
        row.completed_at = utcnow()
    row.updated_at = utcnow()
    session.commit()
    return row


def unit_summaries(session: Session) -> list[dict]:
    """For /listen: each unit with its narrated lessons, total duration and how many have been heard to the end."""
    progress = progress_map(session)
    exams: dict[str, list[str]] = {}
    for eu in session.scalars(select(ExamUnit).order_by(ExamUnit.exam_code.desc())):   # RPLA before PPLA
        exams.setdefault(eu.unit_code, []).append(eu.exam_code)
    units = {u.code: u for u in session.scalars(select(Unit).order_by(Unit.position))}
    groups: dict[str, dict] = {}
    for sub in ordered_subtopics(session):
        data = meta(sub.id)
        g = groups.setdefault(sub.unit_code, {"unit": units[sub.unit_code], "exams": exams.get(sub.unit_code, []),
                                              "lessons": [], "missing": 0, "seconds": 0.0, "heard": 0})
        if data is None:
            g["missing"] += 1
            continue
        d = descriptor(sub, data, progress.get(sub.id))
        g["lessons"].append(d)
        g["seconds"] += d["duration"]
        g["heard"] += d["completed"]
    return list(groups.values())


def last_played(session: Session) -> dict | None:
    """The lesson listened to most recently, if it was not finished: the dashboard's and /listen's "Continue"."""
    row = session.scalars(select(ListenProgress).order_by(ListenProgress.updated_at.desc()).limit(1)).first()
    if row is None or finished(row) or row.position < 5:
        return None
    sub = session.get(Subtopic, row.subtopic_id)
    data = meta(row.subtopic_id) if sub else None
    return descriptor(sub, data, row) if data else None


def visual_cues(data: dict) -> list[tuple[str, str]]:
    seen: list[tuple[str, str]] = []
    for c in data.get("cues", []):
        key = (c["kind"], c["slug"])
        if key not in seen:
            seen.append(key)
    return seen

