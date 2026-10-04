import json
from pathlib import Path

from app.seed.parse_schedule3 import parse

SRC = Path("content/sources/part61-mos-schedule3.txt")
EXPECTED = {  # unit: (subtopics, elements) counted from the MOS text, excluding 'Reserved' elements (PFRA 2.7.4, PNVC 2.7.4); PHFC and PAKC include synthesised elements for bare headings (PHFC 2.6, three PAKC radio headings)
    "BAKC": (21, 72), "RBKA": (11, 34), "RFRC": (7, 27), "RMTC": (3, 3), "PHFC": (15, 51),
    "PAKC": (13, 25), "PAKA": (3, 7), "GNSSC": (1, 1), "PFRA": (9, 30), "PNVC": (7, 22),
    "PMTC": (7, 24), "POPC": (7, 15), "POPA": (5, 12),
}


def test_counts_match_mos():
    data = parse(SRC.read_text(encoding="utf-8"))
    got = {}
    for u in data["units"]:
        subs = [st for t in u["topics"] for st in t["subtopics"]]
        got[u["code"]] = (len(subs), sum(len(st["elements"]) for st in subs))
    assert got == EXPECTED


def test_committed_json_is_current():
    data = parse(SRC.read_text(encoding="utf-8"))
    committed = json.loads(Path("content/syllabus/schedule3.json").read_text(encoding="utf-8"))
    assert data["units"] == committed["units"]


def test_subscripts_and_subitems():
    data = parse(SRC.read_text(encoding="utf-8"))
    units = {u["code"]: u for u in data["units"]}
    popc = units["POPC"]["topics"][0]["subtopics"][1]["elements"][0]
    assert popc["items"][1]["text"] == "never exceed speed (VNE);"
    phfc = units["PHFC"]["topics"][0]["subtopics"][0]["elements"][0]
    preg = next(i for i in phfc["items"] if i["label"] == "f")
    assert [s["label"] for s in preg["subitems"]] == ["i", "ii"]
    paka = units["PAKA"]["topics"][1]
    assert paka["note"].startswith("Note:")
    assert [i["label"] for i in paka["subtopics"][0]["elements"][0]["items"]] == list("abcdefghi")
