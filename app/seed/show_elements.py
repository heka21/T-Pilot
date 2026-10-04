"""Print the knowledge elements of a unit or subtopic compactly: python -m app.seed.show_elements RBKA [3.6]"""
import json
import sys
from pathlib import Path

data = json.loads((Path(__file__).resolve().parents[2] / "content/syllabus/schedule3.json").read_text(encoding="utf-8"))
unit = next(u for u in data["units"] if u["code"] == sys.argv[1])
want = sys.argv[2] if len(sys.argv) > 2 else None
for t in unit["topics"]:
    for st in t["subtopics"]:
        if want and st["number"] != want:
            continue
        print(f"\n## {unit['code']} {st['number']} {st['title']}")
        for e in st["elements"]:
            print(f"{e['number']} {e['text']}")
            for i in e["items"]:
                print(f"   ({i['label']}) {i['text']}" + ("".join(f" ({s['label']}) {s['text']}" for s in i["subitems"])))
