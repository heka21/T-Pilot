"""Content completeness check. Exit code 1 when something is missing.

    python -m app.seed.check_content [--strict]

Reports: subtopics without a note, notes without a "## What the exam expects" section or whose list misses an
element number, elements with no question, elements with no card, questions/cards tagged with unknown element codes,
duplicate ids, MCQs without exactly 4 options or out-of-range answers, and visuals: diagram:/widget:
references to missing files, diagram and widget files nothing references, and style-guide violations
(see content/diagrams/README.md and app.seed.visuals.lint_svg / lint_widget).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

from app.seed.loader import split_frontmatter
from app.seed.visuals import find_refs, lint_svg, lint_widget, visual_path

CONTENT = Path(__file__).resolve().parents[2] / "content"
STATIC = Path(__file__).resolve().parents[1] / "static"
EXPECTS_RE = re.compile(r"^## What the exam expects.*?$(.*?)(?=^## |\Z)", re.M | re.S)


def expects_section(body: str) -> str | None:
    """Text of the 'What the exam expects' section up to the next h2; None when the heading is missing."""
    m = EXPECTS_RE.search(body)
    return m.group(1) if m else None


def check_visuals(bodies: dict[str, tuple[str, str]], problems: list[str]) -> dict[str, int]:
    """bodies: subtopic id -> (note path, markdown body). Returns visuals per unit; appends problems."""
    per_unit: dict[str, int] = {}
    referenced: set[tuple[str, str]] = set()
    for sid, (path, body) in bodies.items():
        for kind, slug in find_refs(body):
            referenced.add((kind, slug))
            per_unit[sid.split()[0]] = per_unit.get(sid.split()[0], 0) + 1
            if not visual_path(CONTENT, kind, slug).is_file():
                problems.append(f"{path}: {kind}:{slug} has no file at {visual_path(CONTENT, kind, slug).relative_to(CONTENT.parent)}")
    for p in sorted((CONTENT / "reference").glob("*.md")):
        for kind, slug in find_refs(p.read_text(encoding="utf-8")):
            referenced.add((kind, slug))
            if not visual_path(CONTENT, kind, slug).is_file():
                problems.append(f"{p}: {kind}:{slug} has no file")
    for svg in sorted((CONTENT / "diagrams").glob("*.svg")):
        if ("diagram", svg.stem) not in referenced:
            problems.append(f"{svg}: diagram is not referenced by any note")
        problems += [f"{svg}: {msg}" for msg in lint_svg(svg)]
    for html in sorted((CONTENT / "widgets").glob("*.html")):
        if ("widget", html.stem) not in referenced:
            problems.append(f"{html}: widget is not referenced by any note")
        problems += [f"{html}: {msg}" for msg in lint_widget(html, STATIC)]
    return per_unit


def load_syllabus() -> tuple[dict[str, dict], dict[str, str]]:
    data = json.loads((CONTENT / "syllabus" / "schedule3.json").read_text(encoding="utf-8"))
    subtopics: dict[str, dict] = {}
    el2st: dict[str, str] = {}
    for u in data["units"]:
        for t in u["topics"]:
            for st in t["subtopics"]:
                sid = f"{u['code']} {st['number']}"
                subtopics[sid] = {"unit": u["code"], "title": st["title"], "elements": [e["code"] for e in st["elements"]],
                                  "element_texts": [e["text"] for e in st["elements"]]}
                for e in st["elements"]:
                    el2st[e["code"]] = sid
    return subtopics, el2st


def main(argv: list[str]) -> int:
    subtopics, el2st = load_syllabus()
    problems: list[str] = []
    notes: dict[str, str] = {}
    bodies: dict[str, tuple[str, str]] = {}
    for path in sorted((CONTENT / "notes").glob("*/*.md")):
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        sid = meta.get("subtopic")
        if sid not in subtopics:
            problems.append(f"{path}: unknown subtopic {sid!r}")
            continue
        if sid in notes:
            problems.append(f"{path}: duplicate note for {sid} (also {notes[sid]})")
        notes[sid] = str(path)
        bodies[sid] = (str(path), body)
        section = expects_section(body)
        if section is None:
            problems.append(f"{path}: no '## What the exam expects' section")
            continue
        for code in subtopics[sid]["elements"]:
            num = code.split()[1]
            if not re.search(rf"\*\*{re.escape(num)}\*\*|\b{re.escape(num)}\b", section):
                problems.append(f"{path}: element {code} not listed in the 'What the exam expects' section")
    missing_notes = [sid for sid in subtopics if sid not in notes]

    q_ids: Counter = Counter()
    q_elements: Counter = Counter()
    for path in sorted((CONTENT / "questions").glob("*.yaml")):
        for q in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            q_ids[q.get("id")] += 1
            if not str(q.get("id", "")).startswith(path.stem.split("-")[0] + "-"):
                problems.append(f"{path}: question id {q.get('id')} does not start with unit {path.stem.split('-')[0]}")
            for c in q.get("elements", []):
                if c not in el2st:
                    problems.append(f"{path}: question {q.get('id')} tags unknown element {c}")
                else:
                    q_elements[c] += 1
            if q.get("kind") == "mcq":
                if len(q.get("options", [])) != 4:
                    problems.append(f"{path}: question {q.get('id')} needs exactly 4 options")
                if not (isinstance(q.get("answer"), int) and 0 <= q["answer"] <= 3):
                    problems.append(f"{path}: question {q.get('id')} answer must be an option index 0-3")
            elif q.get("kind") == "numeric":
                if not isinstance(q.get("answer"), (int, float)):
                    problems.append(f"{path}: question {q.get('id')} numeric answer must be a number")
            else:
                problems.append(f"{path}: question {q.get('id')} unknown kind {q.get('kind')!r}")
            if not q.get("explanation"):
                problems.append(f"{path}: question {q.get('id')} has no explanation")
    c_ids: Counter = Counter()
    c_elements: Counter = Counter()
    for path in sorted((CONTENT / "cards").glob("*.yaml")):
        for c in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            c_ids[c.get("id")] += 1
            for code in c.get("elements", []):
                if code not in el2st:
                    problems.append(f"{path}: card {c.get('id')} tags unknown element {code}")
                else:
                    c_elements[code] += 1
    problems += [f"duplicate question id {i}" for i, n in q_ids.items() if n > 1]
    problems += [f"duplicate card id {i}" for i, n in c_ids.items() if n > 1]

    no_q = [c for c in el2st if c not in q_elements]
    no_c = [c for c in el2st if c not in c_elements]
    by_unit: dict[str, dict] = {}
    for sid, st in subtopics.items():
        u = by_unit.setdefault(st["unit"], {"subtopics": 0, "notes": 0, "elements": 0, "el_with_q": 0, "el_with_c": 0, "questions": 0, "cards": 0})
        u["subtopics"] += 1
        u["notes"] += sid in notes
        u["elements"] += len(st["elements"])
        u["el_with_q"] += sum(1 for c in st["elements"] if c in q_elements)
        u["el_with_c"] += sum(1 for c in st["elements"] if c in c_elements)
    for qid in q_ids:
        by_unit.setdefault(str(qid).split("-")[0], {}).setdefault("questions", 0)
        by_unit[str(qid).split("-")[0]]["questions"] = by_unit[str(qid).split("-")[0]].get("questions", 0) + 1
    for cid in c_ids:
        by_unit.setdefault(str(cid).split("-")[0], {}).setdefault("cards", 0)
        by_unit[str(cid).split("-")[0]]["cards"] = by_unit[str(cid).split("-")[0]].get("cards", 0) + 1

    visuals = check_visuals(bodies, problems)
    print(f"{'unit':6} {'notes':>9} {'elems w/ Q':>11} {'elems w/ C':>11} {'questions':>9} {'cards':>6} {'visuals':>8}")
    for code, u in by_unit.items():
        print(f"{code:6} {u.get('notes',0):>4}/{u.get('subtopics',0):<4} {u.get('el_with_q',0):>5}/{u.get('elements',0):<5} {u.get('el_with_c',0):>5}/{u.get('elements',0):<5} {u.get('questions',0):>9} {u.get('cards',0):>6} {visuals.get(code, 0):>8}")
    print(f"visuals: {sum(visuals.values())} references, {len(list((CONTENT / 'diagrams').glob('*.svg')))} diagrams, {len(list((CONTENT / 'widgets').glob('*.html')))} widgets")
    print(f"\nsubtopics without a note: {len(missing_notes)}")
    print(f"elements with no question: {len(no_q)}")
    print(f"elements with no card: {len(no_c)}")
    for p in problems:
        print("PROBLEM:", p)
    if "--list" in argv:
        print("missing notes:", *missing_notes, sep="\n  ")
        print("elements without questions:", *no_q, sep="\n  ")
    strict = "--strict" in argv
    return 1 if problems or (strict and (missing_notes or no_q or no_c)) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
