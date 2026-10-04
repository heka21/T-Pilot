"""Global search over the bundled content: notes, subtopics, MOS elements, questions, flashcards, reference.

The content is small (a few thousand items) and only changes on restart, so the index is a plain
in-memory list built on first use. Matching is case-insensitive substring per query word (so "stall"
finds "stalling"); every word must match. Scores favour title/code hits and exact phrases.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Card, Element, Question, Subtopic

KINDS = {
    "note": "Notes",
    "subtopic": "Syllabus",
    "element": "Knowledge elements",
    "reference": "Reference",
    "question": "Questions",
    "card": "Flashcards",
}
KIND_ORDER = list(KINDS)
MAX_PER_KIND = 8
MAX_TOTAL = 60
SNIPPET_CHARS = 180

_TAG_RE = re.compile(r"<[^>]+>")
_DROP_RE = re.compile(r"<(figure|svg|script|style)\b.*?</\1>", re.S)
_WS_RE = re.compile(r"\s+")
_MD_IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MD_SYNTAX_RE = re.compile(r"^[#>\-*\s|:]+|[`*_~]{1,3}|^\s*\d+\.\s", re.M)
_MATH_RE = re.compile(r"\$\$?[^$]*\$\$?")


def html_to_text(markup: str) -> str:
    """Visible text of a note's HTML without diagrams, widgets and their labels."""
    markup = _DROP_RE.sub(" ", markup)
    return _WS_RE.sub(" ", html.unescape(_TAG_RE.sub(" ", markup))).strip()


def markdown_to_text(md: str) -> str:
    md = _MD_IMG_RE.sub(" ", md)
    md = _MD_LINK_RE.sub(r"\1", md)
    md = _MATH_RE.sub(" ", md)
    md = _MD_SYNTAX_RE.sub(" ", md)
    return _WS_RE.sub(" ", md).strip()


@dataclass
class Entry:
    kind: str
    title: str
    body: str
    url: str
    context: str = ""  # e.g. "RBKA 3.6 · Stalling, spinning and spiral dives"
    code: str = ""  # exact-match token such as an element code or question id
    _title_l: str = field(init=False, repr=False)
    _body_l: str = field(init=False, repr=False)
    _code_l: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._title_l = self.title.lower()
        self._body_l = self.body.lower()
        self._code_l = self.code.lower()


@dataclass
class Hit:
    entry: Entry
    score: float
    snippet: str  # HTML-escaped, with <mark> around matches

    @property
    def kind(self) -> str:
        return self.entry.kind


def tokens(query: str) -> list[str]:
    return [t for t in re.split(r"[^\w./-]+", query.lower()) if t]


def _sub_url(sub_id: str) -> str:
    unit, _, number = sub_id.partition(" ")
    return f"/syllabus/subtopic/{unit}/{number}"


def _note_url(sub_id: str) -> str:
    unit, _, number = sub_id.partition(" ")
    return f"/notes/{unit}/{number}"


def build_index(session: Session, content_dir: Path | str = "content") -> list[Entry]:
    entries: list[Entry] = []
    subs = {s.id: s for s in session.scalars(
        select(Subtopic).options(selectinload(Subtopic.note), selectinload(Subtopic.topic), selectinload(Subtopic.unit))
    )}

    def ctx(sub_id: str | None) -> str:
        s = subs.get(sub_id or "")
        return f"{s.id} · {s.title}" if s else ""

    for s in subs.values():
        entries.append(Entry("subtopic", f"{s.id} · {s.title}", f"{s.topic.title} {s.unit.title}", _sub_url(s.id),
                             context=f"{s.unit.code} · {s.unit.title}", code=s.id))
        if s.note:
            entries.append(Entry("note", s.note.title, html_to_text(s.note.html) or markdown_to_text(s.note.markdown),
                                 _note_url(s.id), context=f"{s.id} · {s.unit.title}", code=s.id))

    for e in session.scalars(select(Element).options(selectinload(Element.subtopic))):
        items = " ".join(
            f"{i.get('label', '')} {i.get('text', '')} " + " ".join(f"{si.get('label', '')} {si.get('text', '')}" for si in i.get("subitems", []))
            for i in (e.items or [])
        )
        entries.append(Entry("element", f"{e.code} · {e.text}", items, _sub_url(e.subtopic_id) + "#el-" + re.sub(r"\W", "-", e.number),
                             context=ctx(e.subtopic_id), code=e.code))

    for q in session.scalars(select(Question)):
        body = " ".join([q.explanation or "", *(q.options or [])])
        url = f"/quiz?subtopic={quote(q.subtopic_id)}" if q.subtopic_id else f"/quiz?unit={q.unit_code}"
        entries.append(Entry("question", q.stem, body, url, context=ctx(q.subtopic_id) or q.unit_code, code=q.id))

    for c in session.scalars(select(Card)):
        url = f"/cards?subtopic={quote(c.subtopic_id)}" if c.subtopic_id else f"/cards?unit={c.unit_code}"
        entries.append(Entry("card", c.front, c.back, url, context=ctx(c.subtopic_id) or c.unit_code, code=c.id))

    ref_dir = Path(content_dir) / "reference"
    if ref_dir.is_dir():
        from app.seed.loader import split_frontmatter  # local import: loader imports models too
        for path in sorted(ref_dir.glob("*.md")):
            meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
            title = meta.get("title") or path.stem.replace("-", " ").capitalize()
            entries.append(Entry("reference", title, f"{meta.get('summary', '')} {markdown_to_text(body)}", f"/reference/{path.stem}",
                                 context="Reference"))
    return entries


_index: list[Entry] | None = None
_lock = Lock()


def index(session: Session, content_dir: Path | str = "content") -> list[Entry]:
    global _index
    if _index is None:
        with _lock:
            if _index is None:
                _index = build_index(session, content_dir)
    return _index


def reset() -> None:
    """Forget the cached index (content is re-seeded on start, tests may re-seed)."""
    global _index
    _index = None


def score(entry: Entry, terms: list[str], phrase: str) -> float | None:
    """None when a term is missing; otherwise higher is better."""
    total = 0.0
    for t in terms:
        if entry._code_l == t:
            total += 12
        elif t in entry._title_l:
            total += 5 if re.search(rf"\b{re.escape(t)}", entry._title_l) else 3
        elif t in entry._body_l:
            total += 1.5 if re.search(rf"\b{re.escape(t)}", entry._body_l) else 1
            # A lesson that keeps coming back to the word is about it; one passing mention is not.
            total += min(entry._body_l.count(t), 30) / 10
        else:
            return None
    if entry._code_l and len(terms) > 1:
        # Multi-word codes ("RBKA 3.6") never equal a single term, so compare the whole query.
        if entry._code_l == phrase:
            total += 20
        elif entry._code_l.startswith(phrase + "."):
            total += 6
    if len(terms) > 1:
        if phrase in entry._title_l:
            total += 6
        elif phrase in entry._body_l:
            total += 3
    # Short titles that match are more specific than long bodies that happen to contain every word.
    total += 2 / (1 + len(entry._title_l) / 40)
    return total


def snippet(entry: Entry, terms: list[str]) -> str:
    text = entry.body
    low = entry._body_l
    first = min((low.find(t) for t in terms if t in low), default=-1)
    start = 0
    if first < 0:
        window = text[:SNIPPET_CHARS]
    else:
        start = max(0, first - SNIPPET_CHARS // 3)
        start = low.rfind(" ", 0, start) + 1 if start else 0
        window = text[start:start + SNIPPET_CHARS]
    if len(window) < len(text):
        window = (("…" if start else "") + window.rstrip() + "…") if window else ""
    return highlight(window, terms)


def highlight(text: str, terms: list[str]) -> str:
    escaped = html.escape(text)
    if not terms:
        return escaped
    pattern = re.compile("|".join(re.escape(html.escape(t)) for t in sorted(terms, key=len, reverse=True)), re.I)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", escaped)


def search(session: Session, query: str, content_dir: Path | str = "content", kind: str | None = None) -> dict:
    """{query, terms, total, groups: [{kind, label, hits, more}]} — groups are in KIND_ORDER, empty ones dropped."""
    terms = tokens(query)
    phrase = " ".join(terms)
    groups: dict[str, list[Hit]] = {k: [] for k in KIND_ORDER}
    if terms:
        for entry in index(session, content_dir):
            if kind and entry.kind != kind:
                continue
            s = score(entry, terms, phrase)
            if s is not None:
                groups[entry.kind].append(Hit(entry, s, snippet(entry, terms)))
    out = []
    total = 0
    for k in KIND_ORDER:
        hits = sorted(groups[k], key=lambda h: -h.score)
        total += len(hits)
        if hits:
            limit = MAX_TOTAL if kind else MAX_PER_KIND
            out.append({"kind": k, "label": KINDS[k], "hits": hits[:limit], "more": max(0, len(hits) - limit), "count": len(hits)})
    return {"query": query.strip(), "terms": terms, "total": total, "groups": out, "kind": kind, "kinds": KINDS}


SUGGEST_LIMIT = 8
_CODE_QUERY_RE = re.compile(r"^[a-z]{3,5} \d+(\.\d+)*$")
# The dropdown is for getting somewhere: lessons first, then the syllabus, single questions and cards last.
SUGGEST_BONUS = {"note": 4, "subtopic": 2, "reference": 2, "element": 0, "question": -1, "card": -1}
SUGGEST_PER_KIND = {"note": 3, "subtopic": 2, "reference": 2, "element": 2, "question": 2, "card": 2}
KIND_SINGULAR = {
    "note": "Note",
    "subtopic": "Syllabus",
    "element": "Element",
    "reference": "Reference",
    "question": "Question",
    "card": "Flashcard",
}


def suggest(session: Session, query: str, content_dir: Path | str = "content") -> dict:
    """Best few hits across all kinds for the top-bar dropdown: {query, terms, total, hits}.

    Capped per kind so a word that appears in fifty questions still leaves room for the lesson."""
    res = search(session, query, content_dir)
    found = [h for g in res["groups"] for h in g["hits"]]
    phrase = " ".join(res["terms"])
    if _CODE_QUERY_RE.match(phrase) and any(h.entry._code_l == phrase for h in found):
        # "RBKA 3.6": only that subtopic's own lesson, elements, questions and cards.
        found = [h for h in found if h.entry._code_l == phrase or h.entry.context.lower().startswith(phrase + " ")
                 or h.entry._code_l.startswith(phrase + ".")]
    def rank(h: Hit) -> float:
        in_title = all(t in h.entry._title_l for t in res["terms"])
        return h.score + SUGGEST_BONUS[h.kind] + (3 if in_title else 0)

    ranked = sorted(found, key=lambda h: (-rank(h), KIND_ORDER.index(h.kind)))
    noted = {h.entry.code for h in ranked if h.kind == "note"}
    hits: list[Hit] = []
    per_kind: dict[str, int] = {}
    for h in ranked:
        if h.kind == "subtopic" and h.entry.code in noted:
            continue  # the lesson already stands for this subtopic
        if per_kind.get(h.kind, 0) < SUGGEST_PER_KIND[h.kind]:
            hits.append(h)
            per_kind[h.kind] = per_kind.get(h.kind, 0) + 1
        if len(hits) == SUGGEST_LIMIT:
            break
    return {"query": res["query"], "terms": res["terms"], "total": res["total"], "hits": hits, "kind_labels": KIND_SINGULAR}
