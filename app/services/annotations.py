"""The student's own annotations on lessons: typed notes, text highlights and Pencil ink.

These are user state (never touched by seeding). The lesson page embeds `bundle()` so highlights paint
without a flash; the /my-notes page lists `summary()`; `export_all()` is the only backup of this data;
`search_entries()` feeds global search per query (never cached, unlike the content index).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import INK_KINDS, Highlight, InkDocument, Note, StudentNote, Subtopic
from app.services.search import Entry
from app.util import utcnow

NOTE_MAX_CHARS = 200_000
EXACT_MAX_CHARS = 2000
COMMENT_MAX_CHARS = 10_000
INK_MAX_BYTES = 4 * 1024 * 1024
INK_MAX_STROKES = 4000
INK_MAX_POINTS = 4000  # per stroke
SKETCH_MAX_PAGES = 100
EXCERPT_CHARS = 220
QUOTE_CHARS = 140
EXPORT_FORMAT = 1


def _iso(value: datetime | None) -> str | None:
    return value.isoformat(timespec="seconds") if value else None


def _clip(text: str, limit: int) -> str:
    """First `limit` characters on a word boundary, with an ellipsis when cut."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0] or text[:limit]
    return cut.rstrip(" ,.;:") + "…"


def highlight_dict(h: Highlight) -> dict[str, Any]:
    return {
        "id": h.id, "subtopic_id": h.subtopic_id, "colour": h.colour, "exact": h.exact, "prefix": h.prefix,
        "suffix": h.suffix, "start": h.start, "end": h.end, "block_id": h.block_id, "comment": h.comment,
        "orphaned": h.orphaned, "created_at": _iso(h.created_at), "updated_at": _iso(h.updated_at),
    }


def ink_dict(doc: InkDocument) -> dict[str, Any]:
    return {"kind": doc.kind, "page": doc.page, "rev": doc.rev, "strokes": doc.strokes or [],
            "updated_at": _iso(doc.updated_at)}


def highlights_for(session: Session, sid: str) -> list[Highlight]:
    """A lesson's highlights in reading order."""
    return list(session.scalars(select(Highlight).where(Highlight.subtopic_id == sid)
                                .order_by(Highlight.start, Highlight.id)))


def bundle(session: Session, sid: str) -> dict[str, Any]:
    """Everything the lesson page needs: {sid, note, note_updated_at, highlights, ink: {lesson, sketch: [...]}}.

    `ink.lesson` is always an object (rev 0, no strokes when nothing is saved); `ink.sketch` lists saved pages only."""
    note = session.get(StudentNote, sid)
    docs = list(session.scalars(select(InkDocument).where(InkDocument.subtopic_id == sid)
                                .order_by(InkDocument.kind, InkDocument.page)))
    lesson = next((ink_dict(d) for d in docs if d.kind == "lesson"), None)
    return {
        "sid": sid,
        "note": note.text if note else "",
        "note_updated_at": _iso(note.updated_at) if note else None,
        "highlights": [highlight_dict(h) for h in highlights_for(session, sid)],
        "ink": {
            "lesson": lesson or {"kind": "lesson", "page": 0, "rev": 0, "strokes": [], "updated_at": None},
            "sketch": [ink_dict(d) for d in docs if d.kind == "sketch"],
        },
    }


# ---------------------------------------------------------------- typed notes
def save_note(session: Session, sid: str, text: str) -> datetime | None:
    """Store the lesson's typed note; blank text deletes it. Returns the new updated_at (None when deleted)."""
    row = session.get(StudentNote, sid)
    if not text.strip():
        if row is not None:
            session.delete(row)
            session.commit()
        return None
    if row is None:
        row = StudentNote(subtopic_id=sid, text=text)
        session.add(row)
    else:
        row.text = text
        row.updated_at = utcnow()  # onupdate does not fire when the text is unchanged
    session.commit()
    return row.updated_at


# ---------------------------------------------------------------- highlights
def add_highlight(session: Session, sid: str, data: dict[str, Any]) -> Highlight:
    """`data` is a validated HighlightIn dump: colour, exact, prefix, suffix, start, end, block_id, comment."""
    h = Highlight(subtopic_id=sid, **data)
    session.add(h)
    session.commit()
    return h


def update_highlight(session: Session, hid: int, *, colour: str | None = None, comment: str | None = None,
                     orphaned: bool | None = None) -> Highlight | None:
    """Change colour, comment or the orphaned flag; None when the highlight does not exist."""
    h = session.get(Highlight, hid)
    if h is None:
        return None
    if colour is not None:
        h.colour = colour
    if comment is not None:
        h.comment = comment
    if orphaned is not None:
        h.orphaned = orphaned
    h.updated_at = utcnow()
    session.commit()
    return h


def delete_highlight(session: Session, hid: int) -> bool:
    h = session.get(Highlight, hid)
    if h is None:
        return False
    session.delete(h)
    session.commit()
    return True


# ---------------------------------------------------------------- ink
def save_ink(session: Session, sid: str, kind: str, page: int, strokes: list[dict]) -> int:
    """Replace the strokes of one ink page and return its new rev (stored rev + 1); an empty list deletes the page.

    Last write wins: the client's rev is not compared (one student, and the iPad is the only realistic writer)."""
    row = session.scalar(select(InkDocument).where(InkDocument.subtopic_id == sid, InkDocument.kind == kind,
                                                   InkDocument.page == page))
    rev = (row.rev if row else 0) + 1
    if not strokes:
        if row is not None:
            session.delete(row)
            session.commit()
        return rev
    if row is None:
        row = InkDocument(subtopic_id=sid, kind=kind, page=page)
        session.add(row)
    row.strokes = strokes
    row.rev = rev
    row.updated_at = utcnow()
    session.commit()
    return rev


def delete_ink(session: Session, sid: str, kind: str, page: int) -> bool:
    row = session.scalar(select(InkDocument).where(InkDocument.subtopic_id == sid, InkDocument.kind == kind,
                                                   InkDocument.page == page))
    if row is None:
        return False
    session.delete(row)
    session.commit()
    return True


def ink_problem(kind: str, page: int, strokes: Any) -> str | None:
    """Why an ink payload is rejected (422), or None when it is acceptable."""
    if kind not in INK_KINDS:
        return f"Unknown ink kind; expected one of {', '.join(INK_KINDS)}"
    if kind == "lesson" and page != 0:
        return "The lesson overlay has a single page (0)"
    if not 0 <= page < SKETCH_MAX_PAGES:
        return f"Sketch pages run from 0 to {SKETCH_MAX_PAGES - 1}"
    if not isinstance(strokes, list):
        return "strokes must be a list"
    if len(strokes) > INK_MAX_STROKES:
        return f"Too many strokes (at most {INK_MAX_STROKES} per page)"
    for s in strokes:
        if not isinstance(s, dict) or not isinstance(s.get("pts", []), list):
            return "Each stroke must be an object with a pts list"
        if len(s.get("pts", [])) > INK_MAX_POINTS:
            return f"A stroke has too many points (at most {INK_MAX_POINTS})"
    return None


# ---------------------------------------------------------------- overview, export, search
def summary(session: Session) -> dict[str, Any]:
    """Annotated lessons by unit for /my-notes.

    {units: [{unit, lessons: [{sub, note, excerpt, highlights, comments, quotes, lesson_ink, sketch_pages,
    updated_at}]}], totals: {lessons, notes, highlights, ink_pages}} — units and lessons in syllabus order."""
    notes = {n.subtopic_id: n for n in session.scalars(select(StudentNote))}
    hls: dict[str, list[Highlight]] = {}
    for h in session.scalars(select(Highlight).order_by(Highlight.subtopic_id, Highlight.start, Highlight.id)):
        hls.setdefault(h.subtopic_id, []).append(h)
    inks: dict[str, list[InkDocument]] = {}
    for d in session.scalars(select(InkDocument).order_by(InkDocument.subtopic_id, InkDocument.kind, InkDocument.page)):
        inks.setdefault(d.subtopic_id, []).append(d)
    sids = set(notes) | set(hls) | set(inks)
    totals = {"lessons": len(sids), "notes": len(notes), "highlights": sum(map(len, hls.values())),
              "ink_pages": sum(map(len, inks.values()))}
    if not sids:
        return {"units": [], "totals": totals}
    subs = session.scalars(select(Subtopic).where(Subtopic.id.in_(sids)).order_by(Subtopic.position)
                           .options(selectinload(Subtopic.note), selectinload(Subtopic.unit)))
    by_unit: dict[str, dict[str, Any]] = {}
    for sub in subs:
        note, hl, ink = notes.get(sub.id), hls.get(sub.id, []), inks.get(sub.id, [])
        stamps = [x.updated_at for x in [note, *hl, *ink] if x is not None and x.updated_at]
        group = by_unit.setdefault(sub.unit_code, {"unit": sub.unit, "lessons": []})
        group["lessons"].append({
            "sub": sub,
            "title": sub.note.title if sub.note else sub.title,
            "note": note.text if note else "",
            "excerpt": _clip(note.text, EXCERPT_CHARS) if note else "",
            "highlights": len(hl),
            "comments": sum(1 for h in hl if h.comment.strip()),
            "quotes": [{"colour": h.colour, "text": _clip(h.exact, QUOTE_CHARS)} for h in hl[:3]],
            "lesson_ink": any(d.kind == "lesson" for d in ink),
            "sketch_pages": sum(1 for d in ink if d.kind == "sketch"),
            "updated_at": max(stamps) if stamps else None,
        })
    units = sorted(by_unit.values(), key=lambda g: g["unit"].position)
    return {"units": units, "totals": totals}


def export_all(session: Session) -> dict[str, Any]:
    """Every note, highlight and ink page as plain JSON (the backup of the user's annotations)."""
    titles = dict(session.execute(select(Subtopic.id, Subtopic.title)).all())
    return {
        "app": "CASA Theory",
        "format": EXPORT_FORMAT,
        "exported_at": _iso(utcnow()),
        "notes": [{"subtopic_id": n.subtopic_id, "lesson": titles.get(n.subtopic_id, ""), "text": n.text,
                   "updated_at": _iso(n.updated_at)}
                  for n in session.scalars(select(StudentNote).order_by(StudentNote.subtopic_id))],
        "highlights": [highlight_dict(h) | {"lesson": titles.get(h.subtopic_id, "")}
                       for h in session.scalars(select(Highlight).order_by(Highlight.subtopic_id, Highlight.start, Highlight.id))],
        "ink": [ink_dict(d) | {"subtopic_id": d.subtopic_id, "lesson": titles.get(d.subtopic_id, "")}
                for d in session.scalars(select(InkDocument).order_by(InkDocument.subtopic_id, InkDocument.kind, InkDocument.page))],
    }


def _lesson_url(sid: str) -> str:
    unit, _, number = sid.partition(" ")
    return f"/lessons/{unit}/{number}#my-notes"


def search_entries(session: Session) -> list[Entry]:
    """Search entries (kind "mynote") for typed notes and highlights, built fresh for every query."""
    titles = {sid: note_title or title for sid, title, note_title in session.execute(
        select(Subtopic.id, Subtopic.title, Note.title).outerjoin(Note, Note.subtopic_id == Subtopic.id))}

    def title_of(sid: str) -> str:
        return titles.get(sid, sid)

    entries: list[Entry] = []
    for n in session.scalars(select(StudentNote)):
        entries.append(Entry("mynote", f"My notes · {title_of(n.subtopic_id)}", n.text, _lesson_url(n.subtopic_id),
                             context=f"{n.subtopic_id} · {title_of(n.subtopic_id)}"))
    for h in session.scalars(select(Highlight)):
        body = f"{h.exact} {h.comment}".strip()
        entries.append(Entry("mynote", _clip(h.exact, QUOTE_CHARS), body, _lesson_url(h.subtopic_id),
                             context=f"{h.subtopic_id} · {title_of(h.subtopic_id)} · highlight"))
    return entries
