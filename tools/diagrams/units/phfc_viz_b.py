"""PHFC 2.9 to 2.15: static diagrams added in the 2026-10-10 visualisation push (the widgets live in content/widgets).
Numbers and medical statements come from content/notes/PHFC/; change the note first, then the diagram."""
from __future__ import annotations

from tools.diagrams.charts import chart
from tools.diagrams.svg import SECOND, THIN, Canvas, circle, line, multiline, path, rect, text


def _icon(kind: str, x: float, y: float) -> str:
    """A small pictogram centred on (x, y), about 30 units across."""
    if kind == "drop":
        return path(f"M{x} {y - 13} C{x + 6} {y - 5} {x + 9} {y} {x + 9} {y + 4} A9 9 0 0 1 {x - 9} {y + 4} C{x - 9} {y} {x - 6} {y - 5} {x} {y - 13} Z",
                    "bad", "bad-soft", SECOND)
    if kind == "flame":
        return (path(f"M{x} {y - 13} C{x + 8} {y - 4} {x + 10} {y + 2} {x + 7} {y + 8} C{x + 4} {y + 12} {x - 4} {y + 12} {x - 7} {y + 8} "
                     f"C{x - 10} {y + 2} {x - 4} {y - 3} {x} {y - 13} Z", "warn", "warn-soft", SECOND)
                + path(f"M{x - 4} {y + 9} C{x - 5} {y + 3} {x - 1} {y} {x} {y - 3} C{x + 3} {y + 2} {x + 5} {y + 5} {x + 3} {y + 9}", "warn", None, THIN))
    if kind == "bone":
        out = line(x - 8, y + 6, x + 8, y - 6, "fg-muted", 5)
        for cx, cy in ((x - 10, y + 5), (x - 7, y + 9), (x + 10, y - 5), (x + 7, y - 9)):
            out += circle(cx, cy, 3.2, "fg-muted", None)
        return out
    if kind == "blanket":  # a casualty lying down, covered
        return (circle(x - 11, y + 2, 4, "surface", "fg-muted", SECOND)
                + rect(x - 6, y - 2, 20, 9, "info-soft", "info", SECOND, rx=3)
                + line(x - 15, y + 10, x + 16, y + 10, "fg-faint", THIN))
    if kind == "spine":
        return "".join(rect(x - 6 + (1 if i % 2 else 0), y - 14 + i * 7, 12, 5, "surface-2", "fg-muted", THIN, rx=2) for i in range(4))
    if kind == "side":  # recovery position, seen from above the feet: on the side, top knee bent
        return (circle(x - 11, y - 2, 4, "surface", "ok", SECOND)
                + path(f"M{x - 6} {y} L{x + 6} {y + 1} L{x + 12} {y + 8} M{x + 6} {y + 1} L{x + 14} {y + 1} M{x - 3} {y} L{x - 4} {y + 7}", "ok", None, SECOND)
                + line(x - 15, y + 10, x + 16, y + 10, "fg-faint", THIN))
    raise ValueError(kind)


@chart
def first_aid_common_injuries() -> Canvas:
    c = Canvas("Common injuries after a forced landing: what to do, and what not to do",
               "Six cards, each with the first aid action and the mistake to avoid, from the lesson on the ERSA's first aid guidance. "
               "Bleeding: firm direct pressure on a pad, raise the limb, keep the pressure on; do not lift the pad to look. Burns: cool "
               "under clean running water for 20 minutes and cover loosely; no ice, butter or creams. Fractures: immobilise as found "
               "with padding and a splint; do not straighten. Shock: lie them down, keep them warm, reassure them; nothing by mouth. "
               "Spinal injury: keep them still; move them only for immediate danger such as fire. Unconscious but breathing: the recovery "
               "position, on the side with the airway clear; not on the back, where vomit can go into the lungs.",
               height=462, prefix="fai")
    c.add(text(320, 26, "After DRSABCD: the common injuries", 16, "middle", "fg", weight=700))
    c.add(text(320, 44, "do this", 12, "end", "ok-fg", weight=700), text(326, 44, "·", 12, "middle", "fg-faint"),
          text(332, 44, "never this", 12, "start", "bad-fg", weight=700))
    cards = [
        ("Bleeding", "drop", ["Firm direct pressure", "on a pad, limb raised;", "keep the pressure on"],
         ["Lift the pad to look:", "the clot breaks"]),
        ("Burns", "flame", ["Cool under clean running", "water for 20 minutes;", "cover loosely: cling film"],
         ["Ice, butter or creams:", "they damage or trap heat"]),
        ("Fractures", "bone", ["Immobilise it as found,", "with padding and a splint"],
         ["Straighten it to make", "the splint fit"]),
        ("Shock", "blanket", ["Pale, cold, clammy, fast", "weak pulse: lie them", "down, keep them warm,", "reassure them"],
         ["Give anything by mouth"]),
        ("Spinal injury", "spine", ["Neck or back pain,", "numbness, tingling, a", "heavy impact: keep", "them still"],
         ["Move them, unless there", "is fire or other danger"]),
        ("Unconscious", "side", ["Breathing normally:", "recovery position, on", "the side, airway clear;", "keep checking"],
         ["Leave them on the back:", "vomit goes to the lungs"]),
    ]
    w, h, gap, x0, y0 = 194, 178, 12, 16, 60
    for i, (head, icon, do, dont) in enumerate(cards):
        x = x0 + (i % 3) * (w + gap)
        y = y0 + (i // 3) * (h + gap)
        c.add(rect(x, y, w, h, "surface", "line-strong", SECOND, rx=10))
        c.add(text(x + 12, y + 24, head, 14, "start", "fg", weight=700))
        c.add(_icon(icon, x + w - 22, y + 22))
        c.add(text(x + 12, y + 46, "DO", 11, "start", "ok-fg", weight=700))
        c.add(multiline(x + 12, y + 62, do, 12, "start", "fg", 1.3))
        c.add(line(x + 12, y + 122, x + w - 12, y + 122, "line", THIN))
        c.add(text(x + 12, y + 140, "DON'T", 11, "start", "bad-fg", weight=700))
        c.add(multiline(x + 12, y + 156, dont, 12, "start", "fg-muted", 1.3))
    c.add(text(320, 448, "Danger first, always: a fire risk outweighs every other rule here, including the spinal one.", 12, "middle", "fg-muted"))
    return c
