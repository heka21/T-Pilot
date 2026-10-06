"""Read content/equations.yaml, the equation sheet. Shared by the loader, check_content and the KaTeX check.

    python -m app.seed.equations --json     # [{id, latex}] for tools/equations/katex-check.mjs (npm run katex-check)

Schema (see content/README.md, "Equations"):
    topics:    [{id, label}]                    sheet order
    equations: [{id, name, topic, latex, symbols: [{sym, meaning, unit?}], when, rule_of_thumb?,
                 exams: [RPLA|PPLA], lessons: ["RBKA 3.6", ...], tags?, see_also?}]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

CONTENT = Path(__file__).resolve().parents[2] / "content"
EQUATIONS_FILE = "equations.yaml"
EXAMS = ("RPLA", "PPLA")
REQUIRED = ("id", "name", "topic", "latex", "when")


def load_equations(path: Path | str) -> dict:
    """{"topics": [{id, label}], "equations": [...]} with optional fields defaulted. A missing file is empty."""
    path = Path(path)
    data = (yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None) or {}
    topics = [{"id": str(t.get("id", "")), "label": str(t.get("label") or t.get("id", ""))} for t in data.get("topics") or []]
    equations = []
    for e in data.get("equations") or []:
        equations.append({
            **e,
            "id": str(e.get("id", "")),
            "name": e.get("name") or "",
            "topic": e.get("topic") or "",
            "latex": str(e.get("latex") or "").strip(),
            "symbols": [{"sym": str(s.get("sym", "")), "meaning": s.get("meaning") or "", "unit": s.get("unit") or ""}
                        for s in e.get("symbols") or []],
            "when": e.get("when") or "",
            "rule_of_thumb": e.get("rule_of_thumb") or "",
            "exams": list(e.get("exams") or []),
            "lessons": [str(x) for x in e.get("lessons") or []],
            "tags": [str(x) for x in e.get("tags") or []],
            "see_also": [str(x) for x in e.get("see_also") or []],
        })
    return {"topics": topics, "equations": equations}


def katex_inputs(data: dict) -> list[dict]:
    """[{id, latex}] for every formula and symbol, as tools/equations/katex-check.mjs reads it."""
    out = []
    for e in data["equations"]:
        out.append({"id": e["id"], "latex": e["latex"]})
        out += [{"id": f"{e['id']} symbol {s['sym']}", "latex": s["sym"]} for s in e["symbols"]]
    return out


def main(argv: list[str]) -> int:
    data = load_equations(CONTENT / EQUATIONS_FILE)
    if "--json" in argv:
        print(json.dumps(katex_inputs(data), ensure_ascii=False))
    else:
        print(f"{len(data['equations'])} equations in {len(data['topics'])} topics")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
