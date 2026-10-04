"""Parse the Part 61 MOS Schedule 3 text (extracted from CASA's PDF) into syllabus JSON.

Usage:
    python -m app.seed.parse_schedule3 content/sources/part61-mos-schedule3.txt content/syllabus/schedule3.json

The text has a strict hierarchy inside each unit:
    Unit 1.1.2 RBKA: Basic aeronautical knowledge – aeroplane
    2. Power plants and systems            (topic)
    2.1 Piston engine                      (subtopic)
    2.1.1 Describe ...                     (knowledge element, may wrap over lines)
    (a) ...; (b) ...;                      (items under an element, may have (i)(ii) sub-items)
Page headers/footers and wrapped lines are removed before parsing.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Units examined in the RPLA and PPLA exams, in syllabus order.
RPLA_UNITS = ["BAKC", "RBKA", "RFRC", "RMTC", "PHFC"]
PPLA_UNITS = ["PAKC", "PAKA", "GNSSC", "PFRA", "PNVC", "PMTC", "POPC", "POPA"]
WANTED = RPLA_UNITS + [u for u in PPLA_UNITS if u not in RPLA_UNITS]

UNIT_RE = re.compile(r"^Unit (\d+\.\d+\.\d+) ([A-Z]{4,5}): (.+)$")
TOPIC_RE = re.compile(r"^(\d+)\. (\S.*)$")
SUBTOPIC_RE = re.compile(r"^(\d+)\.(\d+) (\S.*)$")
ELEMENT_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+) (\S.*)$")
ITEM_RE = re.compile(r"^\(([a-z])\) (.*)$")
SUBITEM_RE = re.compile(r"^\(((?:i|ii|iii|iv|v|vi|vii|viii|ix|x))\) (.*)$")
TERMINATOR_RE = re.compile(r"^(SECTION \d|APPENDIX \d|Appendix \d)")
NOISE_RE = re.compile(
    r"^(Authorised Version F\w+ registered|Schedule 3 Part 61 Manual of Standards|Page \d+ of \d+ pages)"
)
SUBSCRIPT_RE = re.compile(r"^[A-Za-z]{1,3}$")
FOOTER_INLINE_RE = re.compile(r"\s*Authorised Version F\w+ registered \d\d/\d\d/\d{4}\s*")


def clean_lines(raw: str) -> list[str]:
    """Drop page furniture, join subscript fragments like "(V" / "NE" / ");"."""
    out: list[str] = []
    for line in raw.splitlines():
        s = FOOTER_INLINE_RE.sub(" ", line).strip()
        if not s or NOISE_RE.match(s):
            continue
        if out and out[-1].endswith("(V") and SUBSCRIPT_RE.match(s):
            out[-1] += s  # "(V" + "NE"
            continue
        if out and s.startswith(")") and re.search(r"\(V[A-Za-z]{1,3}$", out[-1]):
            out[-1] += s  # "(VNE" + ");"
            continue
        out.append(s)
    return out


def join(prev: str, nxt: str) -> str:
    """Join a wrapped line, closing up hyphenated breaks like "take-" / "off"."""
    if prev.endswith("-"):
        return prev + nxt
    if prev.endswith(":") and not nxt.startswith("("):
        return prev + " " + nxt
    return prev + " " + nxt


def parse(raw: str) -> dict:
    lines = clean_lines(raw)
    units: dict[str, dict] = {}
    unit = topic = subtopic = element = None
    item = None  # current item dict within element
    i = 0
    while i < len(lines):
        s = lines[i]
        m = UNIT_RE.match(s)
        if m:
            number, code, title = m.groups()
            # Title may wrap onto the next line.
            if i + 1 < len(lines) and not TOPIC_RE.match(lines[i + 1]) and not UNIT_RE.match(lines[i + 1]):
                title = f"{title} {lines[i + 1]}"
                i += 1
            unit = topic = subtopic = element = item = None
            if code in WANTED and "Reserved" not in title:
                unit = {"code": code, "number": number, "title": title.strip(), "topics": []}
                units[code] = unit
            i += 1
            continue
        if TERMINATOR_RE.match(s):
            unit = topic = subtopic = element = item = None
            i += 1
            continue
        if unit is None:
            i += 1
            continue

        m = ELEMENT_RE.match(s)
        if m and topic is not None and int(m.group(1)) == topic["number"] and subtopic is None:
            # Element directly under a topic with no subtopic heading: synthesise one.
            subtopic = {"number": f"{m.group(1)}.{m.group(2)}", "index": int(m.group(2)), "title": topic["title"], "elements": []}
            topic["subtopics"].append(subtopic)
        if m and subtopic is not None and int(m.group(1)) == topic["number"] and int(m.group(2)) == subtopic["index"]:
            number = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
            element = {"code": f"{unit['code']} {number}", "number": number, "text": m.group(4).strip(), "items": []}
            subtopic["elements"].append(element)
            item = None
            i += 1
            continue
        m = SUBTOPIC_RE.match(s)
        if m and topic is not None and int(m.group(1)) == topic["number"]:
            subtopic = {"number": f"{m.group(1)}.{m.group(2)}", "index": int(m.group(2)), "title": m.group(3).strip(), "elements": []}
            topic["subtopics"].append(subtopic)
            element = item = None
            i += 1
            continue
        m = TOPIC_RE.match(s)
        if m and (topic is None or int(m.group(1)) == topic["number"] + 1):
            title = m.group(2).strip()
            topic = {"number": int(m.group(1)), "title": title, "subtopics": []}
            if title != "Reserved":
                unit["topics"].append(topic)
            subtopic = element = item = None
            i += 1
            continue
        # Continuation text: items, sub-items, or wrapped lines.
        if element is None and subtopic is not None and ITEM_RE.match(s) and not subtopic["elements"]:
            # The MOS occasionally lists items straight under a subtopic heading (PFRA 2.5): synthesise the element.
            num = f"{subtopic['number']}.1"
            element = {"code": f"{unit['code']} {num}", "number": num, "text": subtopic["title"], "items": [], "synthesised": True}
            subtopic["elements"].append(element)
            item = None
        if element is not None:
            mi = ITEM_RE.match(s)
            ms = SUBITEM_RE.match(s)
            expected = chr(ord(item["label"]) + 1) if item is not None else "a"
            if ms and item is not None and ms.group(1) != expected:
                item["subitems"].append({"label": ms.group(1), "text": ms.group(2).strip()})
            elif mi:
                item = {"label": mi.group(1), "text": mi.group(2).strip(), "subitems": []}
                element["items"].append(item)
            elif item is not None and item["subitems"]:
                item["subitems"][-1]["text"] = join(item["subitems"][-1]["text"], s)
            elif item is not None:
                item["text"] = join(item["text"], s)
            else:
                element["text"] = join(element["text"], s)
        elif subtopic is not None:
            subtopic["title"] = join(subtopic["title"], s)
        elif topic is not None:
            if s.startswith("Note:"):
                topic["note"] = s
            else:
                topic["title"] = join(topic["title"], s)
        i += 1

    for u in units.values():
        for t in u["topics"]:
            for st in t["subtopics"]:
                st.pop("index", None)
                st["elements"] = [e for e in st["elements"] if e["text"].strip().rstrip(":.") != "Reserved"]
                if not st["elements"]:
                    # A bare heading with no numbered element (e.g. PHFC 2.6): synthesise one so it can be tagged.
                    num = f"{st['number']}.1"
                    st["elements"].append({"code": f"{u['code']} {num}", "number": num, "text": st["title"], "items": [], "synthesised": True})
    ordered = [units[c] for c in WANTED if c in units]
    return {
        "source": "Part 61 Manual of Standards Schedule 3, Aeronautical knowledge standards (CASA PDF, compilation F2021C00449; unchanged for RPL/PPL units by the 19 Nov 2024 amendment)",
        "exam_units": {"RPLA": RPLA_UNITS, "PPLA": PPLA_UNITS},
        "units": ordered,
    }


def summarise(data: dict) -> str:
    rows = []
    for u in data["units"]:
        subs = sum(len(t["subtopics"]) for t in u["topics"])
        els = sum(len(st["elements"]) for t in u["topics"] for st in t["subtopics"])
        rows.append(f"{u['code']:6} topics={len(u['topics']):2} subtopics={subs:3} elements={els:3}")
    return "\n".join(rows)


def main(argv: list[str]) -> None:
    src, dst = Path(argv[1]), Path(argv[2])
    data = parse(src.read_text(encoding="utf-8"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(summarise(data))


if __name__ == "__main__":
    main(sys.argv)
