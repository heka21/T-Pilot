"""Load content/ into the database. Idempotent: upserts by stable ids, never touches user state.

    from app.seed.loader import seed_all
    seed_all(session, Path("content"))

Content layout (see content/README.md):
    syllabus/schedule3.json        units > topics > subtopics > elements (from parse_schedule3)
    exams.json                     exam formats and unit weightings
    notes/<UNIT>/<n.n>-<slug>.md   one note per subtopic, YAML frontmatter
    questions/<UNIT>.yaml          list of questions
    cards/<UNIT>.yaml              list of flashcards
    equations.yaml                 the equation sheet (rebuilt from scratch each time: nothing user-owned refers to it)
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
from pathlib import Path

import markdown
import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.seed.visuals import VisualsExtension, find_refs
from app.models import (
    Card, CardElement, Element, Equation, EquationLesson, Exam, ExamUnit, Note, Question, QuestionElement, Subtopic, Topic, Unit,
)
from app.seed.equations import EQUATIONS_FILE, load_equations

log = logging.getLogger(__name__)

# arithmatex (generic mode) protects $...$ and $$...$$ maths from Markdown so KaTeX can render it in the browser.
# pymdownx.details turns `??? check "Question"` into a collapsible <details class="check"> (self-check answers).
MD_EXTENSIONS = ["extra", "admonition", "sane_lists", "toc", "pymdownx.details", "pymdownx.arithmatex"]
MD_EXTENSION_CONFIGS = {"pymdownx.arithmatex": {"generic": True}}
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60].rstrip("-")


def render_markdown(text: str, content_dir: Path | str | None = None) -> str:
    """Markdown to HTML. `content_dir` is where diagram:/widget: references are resolved (see app/seed/visuals.py)."""
    content_dir = Path(content_dir) if content_dir is not None else Path(os.environ.get("CONTENT_DIR", "content"))
    extensions = [*MD_EXTENSIONS, VisualsExtension(content_dir=str(content_dir))]
    return markdown.markdown(text, extensions=extensions, extension_configs=MD_EXTENSION_CONFIGS, output_format="html5")


def split_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    return (yaml.safe_load(m.group(1)) or {}), text[m.end():]


# Planner reading-time model. Lessons are read at study pace (about half casual reading speed: the student stops
# at formulas, tables and examples), plus fixed time per visual, worked example and self-check question.
WORDS_PER_MINUTE = 100
MINUTES_PER_DIAGRAM = 2
MINUTES_PER_WIDGET = 5
MINUTES_PER_EXAMPLE = 2
MINUTES_PER_CHECK = 1
MIN_MINUTES = 5
_NOT_PROSE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)|^\s*(?:!!!|\?\?\?\+?)\s.*$", re.M)
EXAMPLE_RE = re.compile(r"^!!! example\b", re.M)
CHECK_RE = re.compile(r"^\?\?\?\+? check\b", re.M)


def word_count(body: str) -> int:
    """Words of prose in a note body: image references and admonition/details header lines do not count."""
    return len(re.findall(r"\b\w+\b", _NOT_PROSE_RE.sub(" ", body)))


def estimate_minutes(body: str) -> int:
    """Study time for a note body; used when the frontmatter has no `minutes` override."""
    kinds = [k for k, _ in find_refs(body)]
    minutes = (math.ceil(word_count(body) / WORDS_PER_MINUTE)
               + MINUTES_PER_DIAGRAM * kinds.count("diagram") + MINUTES_PER_WIDGET * kinds.count("widget")
               + MINUTES_PER_EXAMPLE * len(EXAMPLE_RE.findall(body)) + MINUTES_PER_CHECK * len(CHECK_RE.findall(body)))
    return max(MIN_MINUTES, minutes)


# ---------------------------------------------------------------- syllabus
def seed_syllabus(session: Session, data: dict) -> int:
    position = 0
    for upos, u in enumerate(data["units"]):
        unit = session.merge(Unit(code=u["code"], number=u["number"], title=u["title"], position=upos))
        for tpos, t in enumerate(u["topics"]):
            topic_id = f"{unit.code} {t['number']}"
            session.merge(Topic(id=topic_id, unit_code=unit.code, number=t["number"], title=t["title"],
                                note=t.get("note"), position=tpos))
            for st in t["subtopics"]:
                position += 1
                st_id = f"{unit.code} {st['number']}"
                session.merge(Subtopic(id=st_id, unit_code=unit.code, topic_id=topic_id, number=st["number"],
                                       title=st["title"], slug=f"{st['number']}-{slugify(st['title'])}", position=position))
                for epos, e in enumerate(st["elements"]):
                    session.merge(Element(code=e["code"], subtopic_id=st_id, number=e["number"], text=e["text"],
                                          items=e.get("items", []), position=epos))
    session.flush()
    return position


def seed_exams(session: Session, data: dict) -> int:
    for ex in data["exams"]:
        exam = session.merge(Exam(code=ex["code"], name=ex["name"], duration_minutes=ex["duration_minutes"],
                                  pass_mark_percent=ex["pass_mark_percent"], question_count=ex["question_count"],
                                  casa_weak_areas=ex.get("casa_weak_areas", []), fuel_policy=ex.get("fuel_policy", "")))
        for pos, eu in enumerate(ex["units"]):
            session.merge(ExamUnit(exam_code=exam.code, unit_code=eu["code"], weight=eu["weight"], position=pos))
    session.flush()
    return len(data["exams"])


# ---------------------------------------------------------------- notes
def seed_notes(session: Session, notes_dir: Path) -> int:
    content_dir = Path(notes_dir).parent
    count = 0
    known = {s.id for s in session.scalars(select(Subtopic))}
    for path in sorted(notes_dir.glob("*/*.md")):
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        st_id = meta.get("subtopic")
        if st_id not in known:
            log.warning("note %s: unknown subtopic %r, skipped", path, st_id)
            continue
        session.merge(Note(subtopic_id=st_id, path=str(path), title=meta.get("title") or st_id,
                           markdown=body, html=render_markdown(body, content_dir), references=meta.get("references") or [],
                           minutes=int(meta.get("minutes") or estimate_minutes(body))))
        count += 1
    session.flush()
    return count


# ---------------------------------------------------------------- questions and cards
def _element_map(session: Session) -> dict[str, str]:
    return {e.code: e.subtopic_id for e in session.scalars(select(Element))}


def seed_questions(session: Session, q_dir: Path) -> int:
    el2st = _element_map(session)
    count = 0
    for path in sorted(q_dir.glob("*.yaml")):
        unit_code = path.stem.split("-")[0]
        for q in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            codes = [c for c in q.get("elements", []) if c in el2st]
            missing = set(q.get("elements", [])) - set(codes)
            if missing:
                log.warning("question %s: unknown elements %s", q.get("id"), sorted(missing))
            kind = q["kind"]
            if kind == "mcq" and len(q.get("options", [])) != 4:
                log.warning("question %s: mcq needs 4 options, skipped", q.get("id"))
                continue
            row = Question(
                id=q["id"], unit_code=unit_code, subtopic_id=el2st.get(codes[0]) if codes else None,
                kind=kind, stem=q["stem"], options=q.get("options", []), answer=str(q["answer"]),
                tolerance=float(q.get("tolerance", 0) or 0), unit_label=q.get("unit"),
                explanation=q.get("explanation", ""), references=q.get("references", []),
                workbook_page=q.get("workbook_page"), difficulty=int(q.get("difficulty", 2)),
            )
            session.merge(row)
            for qe in session.scalars(select(QuestionElement).where(QuestionElement.question_id == row.id)):
                session.delete(qe)
            session.flush()
            for c in codes:
                session.add(QuestionElement(question_id=row.id, element_code=c))
            count += 1
    session.flush()
    return count


def seed_cards(session: Session, c_dir: Path) -> int:
    el2st = _element_map(session)
    count = 0
    for path in sorted(c_dir.glob("*.yaml")):
        unit_code = path.stem.split("-")[0]
        for c in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            codes = [x for x in c.get("elements", []) if x in el2st]
            missing = set(c.get("elements", [])) - set(codes)
            if missing:
                log.warning("card %s: unknown elements %s", c.get("id"), sorted(missing))
            options, answer = c.get("options") or [], c.get("answer")
            if options and (len(options) != 4 or answer not in range(4)):
                log.warning("card %s: needs 4 options and an answer 0-3, reviewed self-graded", c.get("id"))
                options, answer = [], None
            row = Card(id=c["id"], unit_code=unit_code, subtopic_id=el2st.get(codes[0]) if codes else None,
                       front=c["front"], back=c["back"], stem=c.get("stem"), options=options, answer=answer)
            session.merge(row)
            for ce in session.scalars(select(CardElement).where(CardElement.card_id == row.id)):
                session.delete(ce)
            session.flush()
            for x in codes:
                session.add(CardElement(card_id=row.id, element_code=x))
            count += 1
    session.flush()
    return count


# ---------------------------------------------------------------- equations
_OUTER_P_RE = re.compile(r"\A<p>(.*)</p>\Z", re.S)


def render_inline_markdown(text: str, content_dir: Path | str | None = None) -> str:
    """Markdown for one short paragraph, without the wrapping <p> (so it sits inside a card's own element)."""
    if not text.strip():
        return ""
    html_out = render_markdown(text, content_dir).strip()
    m = _OUTER_P_RE.match(html_out)
    return m.group(1) if m and "<p>" not in m.group(1) else html_out


def seed_equations(session: Session, path: Path) -> int:
    data = load_equations(path)
    content_dir = Path(path).parent
    known = {s.id for s in session.scalars(select(Subtopic))}
    for row in session.scalars(select(Equation)):
        session.delete(row)  # cascades to its EquationLesson rows
    session.flush()
    for pos, e in enumerate(data["equations"]):
        session.add(Equation(
            id=e["id"], name=e["name"], topic=e["topic"], latex=e["latex"], symbols=e["symbols"],
            when=e["when"], when_html=render_inline_markdown(e["when"], content_dir),
            rule_of_thumb=e["rule_of_thumb"], rule_html=render_inline_markdown(e["rule_of_thumb"], content_dir),
            exams=e["exams"], tags=e["tags"], see_also=e["see_also"], position=pos,
        ))
        unknown = [x for x in e["lessons"] if x not in known]
        if unknown:
            log.warning("equation %s: unknown lessons %s", e["id"], unknown)
        for lpos, sid in enumerate(dict.fromkeys(x for x in e["lessons"] if x in known)):
            session.add(EquationLesson(equation_id=e["id"], subtopic_id=sid, position=lpos))
    session.flush()
    return len(data["equations"])


def seed_all(session: Session, content_dir: Path) -> dict[str, int]:
    content_dir = Path(content_dir)
    summary = {
        "subtopics": seed_syllabus(session, json.loads((content_dir / "syllabus" / "schedule3.json").read_text(encoding="utf-8"))),
        "exams": seed_exams(session, json.loads((content_dir / "exams.json").read_text(encoding="utf-8"))),
        "notes": seed_notes(session, content_dir / "notes"),
        "questions": seed_questions(session, content_dir / "questions"),
        "cards": seed_cards(session, content_dir / "cards"),
        "equations": seed_equations(session, content_dir / EQUATIONS_FILE),
    }
    session.commit()
    log.info("content seeded: %s", summary)
    return summary
