"""Lesson-format lint: advisory checks on each note against the lesson standard in content/LESSONS.md.

    python -m app.seed.lint_lessons [--strict] [UNIT ...]

Prints one line per warning, then a per-unit table (lessons, mean and minimum words, lessons with no warnings,
estimated study minutes) and the total against the default plan's capacity. Exit code 1 only with --strict and at
least one warning. `python -m app.seed.check_content` remains the hard gate for coverage and visuals.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from app.seed.check_content import CONTENT, expects_section, load_syllabus
from app.seed.loader import CHECK_RE, EXAMPLE_RE, estimate_minutes, split_frontmatter, word_count
from app.seed.visuals import find_refs
from app.services.planner import DEFAULT_WEEKS

MIN_WORDS = 2000
MAX_WORDS = 4500
MIN_CHECKS = 3
KNOWN_ADMONITIONS = {"example", "tip", "warning", "note"}
KNOWN_DETAILS = {"check", "solution"}
REQUIRED_HEADINGS = ("## Why this matters", "## Key points")
CALC_RE = re.compile(r"\b(calculat|comput|determin|extract|convert|interpret|derive)\w*", re.I)
ADMON_RE = re.compile(r"^!!! (\w+)", re.M)
DETAILS_RE = re.compile(r"^\?\?\?\+? (\w+)", re.M)
# Default plan capacity: study days at the session length, less the cards and quiz overhead on each day.
DEFAULT_CAPACITY_MINUTES = DEFAULT_WEEKS * 6 * (120 - 15)


def lint_body(body: str, element_texts: list[str], meta: dict) -> list[str]:
    out: list[str] = []
    words = word_count(body)
    if words < MIN_WORDS:
        out.append(f"short lesson: {words} words (aim for {MIN_WORDS}+)")
    elif words > MAX_WORDS:
        out.append(f"long lesson: {words} words (aim for under {MAX_WORDS}; split the explanation or trim)")
    if expects_section(body) is None:
        out.append("no '## What the exam expects' section (check_content fails on this too)")
    checks = len(CHECK_RE.findall(body))
    if checks < MIN_CHECKS:
        out.append(f"{checks} self-check question(s); aim for {MIN_CHECKS}+ (`??? check \"Check yourself\"`)")
    if not EXAMPLE_RE.search(body) and any(CALC_RE.search(t) for t in element_texts):
        out.append("elements ask for calculation or extraction but there is no `!!! example \"Worked example\"`")
    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"^{re.escape(heading)}\b", body, re.M):
            out.append(f"no `{heading}` section")
    if not find_refs(body):
        out.append("no diagram or widget")
    for kind in sorted(set(ADMON_RE.findall(body)) - KNOWN_ADMONITIONS):
        out.append(f"unknown admonition type `!!! {kind}` (no CSS for it)")
    for kind in sorted(set(DETAILS_RE.findall(body)) - KNOWN_DETAILS):
        out.append(f"unknown details type `??? {kind}` (no CSS for it)")
    if meta.get("minutes"):
        est = estimate_minutes(body)
        if abs(int(meta["minutes"]) - est) > 0.4 * est:
            out.append(f"frontmatter minutes {meta['minutes']} vs estimated {est}: drop the override or fix it")
    return out


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    units = {a.upper() for a in argv if not a.startswith("--")}
    subtopics, _ = load_syllabus()
    rows: dict[str, dict] = {}
    warnings = 0
    for path in sorted((CONTENT / "notes").glob("*/*.md")):
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        sid = meta.get("subtopic")
        if sid not in subtopics or (units and subtopics[sid]["unit"] not in units):
            continue
        problems = lint_body(body, subtopics[sid]["element_texts"], meta)
        warnings += len(problems)
        for p in problems:
            print(f"{path.relative_to(CONTENT.parent)}: {p}")
        row = rows.setdefault(subtopics[sid]["unit"], {"lessons": 0, "words": [], "clean": 0, "minutes": 0})
        row["lessons"] += 1
        row["words"].append(word_count(body))
        row["clean"] += not problems
        row["minutes"] += int(meta.get("minutes") or estimate_minutes(body))
    print(f"\n{'unit':6} {'lessons':>7} {'mean words':>10} {'min words':>9} {'clean':>5} {'minutes':>7}")
    total = 0
    for code, r in rows.items():
        total += r["minutes"]
        print(f"{code:6} {r['lessons']:>7} {sum(r['words']) // len(r['words']):>10} {min(r['words']):>9} {r['clean']:>5} {r['minutes']:>7}")
    print(f"\ntotal study minutes {total} vs default {DEFAULT_WEEKS}-week plan capacity about {DEFAULT_CAPACITY_MINUTES}; {warnings} warning(s)")
    return 1 if strict and warnings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
