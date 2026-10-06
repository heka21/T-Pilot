"""Content completeness check. Exit code 1 when something is missing.

    python -m app.seed.check_content [--strict] [--katex]

Reports: subtopics without a note, notes without a "## What the exam expects" section or whose list misses an
element number, elements with no question, elements with no card, questions/cards tagged with unknown element codes,
duplicate ids, MCQs without exactly 4 options or out-of-range answers, workbook_page outside the workbook's figure
pages, and visuals: diagram:/widget:/workbook: references to missing files, diagram and widget files nothing references, and style-guide violations
(see content/diagrams/README.md and app.seed.visuals.lint_svg / lint_widget), and content/equations.yaml (ids, fields,
lesson links, exam consistency, LaTeX sanity; --katex also renders every formula with the vendored KaTeX when node is
on PATH).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

from app.seed.loader import split_frontmatter
from app.seed import workbook
from app.seed.equations import EQUATIONS_FILE, EXAMS, REQUIRED, katex_inputs, load_equations
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
            if kind == "workbook" and slug not in workbook.FIGURES:
                problems.append(f"{path}: workbook:{slug} is not a figure id in app/seed/workbook.py")
            elif not visual_path(CONTENT, kind, slug).is_file():
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


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EQUATION_KEYS = {"id", "name", "topic", "latex", "symbols", "when", "rule_of_thumb", "exams", "lessons", "tags", "see_also"}


def latex_issues(latex: str) -> tuple[list[str], list[str]]:
    """(problems, warnings) for one KaTeX source: no $, balanced {} and (), paired \\left/\\right; \\\\ is a warning."""
    problems: list[str] = []
    warnings: list[str] = []
    if "$" in latex:
        problems.append("contains $ (write the LaTeX without delimiters)")
    if "\\\\" in latex:
        warnings.append("contains \\\\ (a line break: only works inside an environment such as aligned)")
    braces = parens = lefts = 0
    i = 0
    while i < len(latex):
        c = latex[i]
        if c == "\\":
            m = re.match(r"[A-Za-z]+", latex[i + 1:])
            name = m.group(0) if m else latex[i + 1:i + 2]
            i += 1 + len(name)
            if name in ("left", "right"):
                lefts += 1 if name == "left" else -1
                if lefts < 0:
                    problems.append("\\right without a \\left")
                    lefts = 0
                i += len(latex[i:]) - len(latex[i:].lstrip())
                if latex[i:i + 1] == "\\":  # a command delimiter such as \{ or \langle
                    m = re.match(r"\\([A-Za-z]+|.)", latex[i:])
                    i += len(m.group(0)) if m else 1
                else:
                    i += 1  # the delimiter character itself: ( ) [ ] | . and friends do not count below
            continue
        if c == "{":
            braces += 1
        elif c == "}":
            braces -= 1
            if braces < 0:
                problems.append("unbalanced }")
                braces = 0
        elif c == "(":
            parens += 1
        elif c == ")":
            parens -= 1
            if parens < 0:
                problems.append("unbalanced )")
                parens = 0
        i += 1
    if braces:
        problems.append("unbalanced {")
    if parens:
        problems.append("unbalanced (")
    if lefts:
        problems.append("\\left without a \\right")
    return problems, warnings


def check_equations(subtopics: dict[str, dict], problems: list[str], warnings: list[str],
                    path: Path | None = None) -> dict:
    """Validate content/equations.yaml against the syllabus and content/exams.json. Returns the loaded data."""
    path = path or CONTENT / EQUATIONS_FILE
    if not path.is_file():
        problems.append(f"{path}: missing")
        return {"topics": [], "equations": []}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        problems.append(f"{path}: does not parse: {exc}")
        return {"topics": [], "equations": []}
    if not isinstance(raw, dict) or not isinstance(raw.get("equations"), list) or not isinstance(raw.get("topics"), list):
        problems.append(f"{path}: needs a `topics` list and an `equations` list")
        return {"topics": [], "equations": []}
    data = load_equations(path)
    raw_by_id = {str(e.get("id")): e for e in raw["equations"] if isinstance(e, dict)}
    exam_units = {ex["code"]: {u["code"] for u in ex["units"]}
                  for ex in json.loads((CONTENT / "exams.json").read_text(encoding="utf-8"))["exams"]}

    topic_ids = Counter(t["id"] for t in data["topics"])
    for tid, n in topic_ids.items():
        if not SLUG_RE.match(tid):
            problems.append(f"{path}: topic id {tid!r} is not a lower-case slug")
        if n > 1:
            problems.append(f"{path}: duplicate topic id {tid}")
    eq_ids = Counter(e["id"] for e in data["equations"])
    problems += [f"{path}: duplicate equation id {i}" for i, n in eq_ids.items() if n > 1]

    for raw_eq, e in zip(raw["equations"], data["equations"]):
        where = f"{path}: equation {e['id'] or '(no id)'}"
        unknown = sorted(set(raw_eq) - EQUATION_KEYS) if isinstance(raw_eq, dict) else []
        if unknown:
            problems.append(f"{where}: unknown keys {unknown}")
        missing = [k for k in REQUIRED if not e[k]] + [k for k in ("exams", "lessons") if not e[k]]
        if missing:
            problems.append(f"{where}: missing {', '.join(missing)}")
        if e["id"] and (not SLUG_RE.match(e["id"]) or len(e["id"]) > 40):
            problems.append(f"{where}: id is not a lower-case slug of at most 40 characters")
        if e["topic"] and e["topic"] not in topic_ids:
            problems.append(f"{where}: unknown topic {e['topic']!r}")
        bad_exams = [x for x in e["exams"] if x not in EXAMS]
        if bad_exams:
            problems.append(f"{where}: exams must be RPLA and/or PPLA, not {bad_exams}")
        for s in e["symbols"]:
            if not s["sym"] or not s["meaning"]:
                problems.append(f"{where}: every symbol needs sym and meaning")
        # The loader normalises symbols and tags, so check the raw records for mistakes it would hide: a stray
        # key in a symbol (usually an unquoted comma inside `{sym: …, meaning: …}`) or a bare word YAML turned
        # into a boolean or number.
        raw_e = raw_by_id.get(e["id"])
        if raw_e is not None:
            for s in raw_e.get("symbols") or []:
                extra = set(s) - {"sym", "meaning", "unit"} if isinstance(s, dict) else {"(not a mapping)"}
                if extra:
                    problems.append(f"{where}: symbol has unexpected keys {sorted(map(str, extra))} (quote any value containing a comma)")
            for t in raw_e.get("tags") or []:
                if not isinstance(t, str):
                    problems.append(f"{where}: tag {t!r} is not a string (quote it)")
        unknown_lessons = [x for x in e["lessons"] if x not in subtopics]
        if unknown_lessons:
            problems.append(f"{where}: unknown lessons {unknown_lessons}")
        if len(set(e["lessons"])) != len(e["lessons"]):
            problems.append(f"{where}: a lesson is listed twice")
        for other in e["see_also"]:
            if other not in eq_ids or other == e["id"]:
                problems.append(f"{where}: see_also {other!r} is not another equation id")
        # Exam consistency: a claimed exam needs one of its units among the lessons, and every lesson belongs to a
        # unit of a claimed exam (else the RPL filter would show a PPL-only formula, or hide an RPL one).
        units = {subtopics[x]["unit"] for x in e["lessons"] if x in subtopics}
        for ex in e["exams"]:
            if ex in exam_units and not units & exam_units[ex]:
                problems.append(f"{where}: claims {ex} but no linked lesson is in an {ex} unit")
        claimed = set().union(*(exam_units.get(ex, set()) for ex in e["exams"]))
        outside = [x for x in e["lessons"] if x in subtopics and subtopics[x]["unit"] not in claimed]
        if outside and not bad_exams:
            problems.append(f"{where}: lessons {outside} are outside its exams {e['exams']}")
        for field, latex in [("latex", e["latex"]), *(("symbol " + s["sym"], s["sym"]) for s in e["symbols"])]:
            p, w = latex_issues(latex)
            problems += [f"{where}: {field}: {m}" for m in p]
            warnings += [f"{where}: {field}: {m}" for m in w]
        for field in ("when", "rule_of_thumb"):
            if e[field].count("$") % 2:
                problems.append(f"{where}: {field} has an odd number of $")
    return data


def check_katex(data: dict, problems: list[str]) -> bool:
    """Render every formula with tools/equations/katex-check.mjs. False when node is not on PATH."""
    node = shutil.which("node")
    if not node:
        return False
    script = CONTENT.parent / "tools" / "equations" / "katex-check.mjs"
    res = subprocess.run([node, str(script)], input=json.dumps(katex_inputs(data)), capture_output=True, text=True, timeout=120)
    if res.returncode:
        lines = [ln for ln in res.stdout.splitlines() if ln and not ln.startswith("katex-check:")]
        problems += [f"{CONTENT / EQUATIONS_FILE}: KaTeX: {ln}" for ln in lines] or [f"KaTeX check failed: {res.stderr.strip()}"]
    return True


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
            if q.get("workbook_page") is not None and q["workbook_page"] not in workbook.PAGE_TITLES:
                problems.append(f"{path}: question {q.get('id')} workbook_page {q['workbook_page']} is not a figure page "
                                f"({workbook.FIRST_PAGE}-{workbook.LAST_PAGE})")
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
    warnings: list[str] = []
    equations = check_equations(subtopics, problems, warnings)
    katex_ran = check_katex(equations, problems) if "--katex" in argv else None
    print(f"{'unit':6} {'notes':>9} {'elems w/ Q':>11} {'elems w/ C':>11} {'questions':>9} {'cards':>6} {'visuals':>8}")
    for code, u in by_unit.items():
        print(f"{code:6} {u.get('notes',0):>4}/{u.get('subtopics',0):<4} {u.get('el_with_q',0):>5}/{u.get('elements',0):<5} {u.get('el_with_c',0):>5}/{u.get('elements',0):<5} {u.get('questions',0):>9} {u.get('cards',0):>6} {visuals.get(code, 0):>8}")
    print(f"visuals: {sum(visuals.values())} references, {len(list((CONTENT / 'diagrams').glob('*.svg')))} diagrams, {len(list((CONTENT / 'widgets').glob('*.html')))} widgets")
    print(f"\nsubtopics without a note: {len(missing_notes)}")
    print(f"elements with no question: {len(no_q)}")
    print(f"elements with no card: {len(no_c)}")
    print(f"equations: {len(equations['equations'])} in {len(equations['topics'])} topics"
          + ("" if katex_ran is None else ", KaTeX checked" if katex_ran else ", KaTeX not checked (node is not on PATH)"))
    for w in warnings:
        print("WARNING:", w)
    for p in problems:
        print("PROBLEM:", p)
    if "--list" in argv:
        print("missing notes:", *missing_notes, sep="\n  ")
        print("elements without questions:", *no_q, sep="\n  ")
    strict = "--strict" in argv
    return 1 if problems or (strict and (missing_notes or no_q or no_c)) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
