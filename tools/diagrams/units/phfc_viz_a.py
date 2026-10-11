"""PHFC 2.1 to 2.8: static diagrams added in the 2026-10-10 visualisation push (the widgets live in content/widgets).
Numbers and medical statements come from content/notes/PHFC/; change the note first, then the diagram."""
from __future__ import annotations

from tools.diagrams.charts import chart
from tools.diagrams.svg import MAIN, SECOND, THIN, Canvas, arrow, multiline, path, polygon, rect, text
from tools.diagrams.units.phfc import FG, SOFT, pill


# ---------------------------------------------------------------- 2.2 health and fitness
@chart
def rehydration_fluids() -> Canvas:
    c = Canvas("Which drinks rehydrate you?", "Five drinks compared for putting water back into a dehydrated pilot: water and diluted electrolyte "
               "drinks are absorbed quickly and kept; very sugary drinks rehydrate slowly because they hold water in the gut; alcohol and large "
               "amounts of caffeine make the kidneys pass more water than you drink. Below, the signs of dehydration, with dark urine the "
               "reliable early check and thirst a late one.", height=452, prefix="rhf")
    c.add(text(320, 30, "Which drinks rehydrate you best?", 16, "middle", "fg", weight=700))
    drinks = [
        ("Water", "sky-soft", "ok", "Best", ["Absorbed fast;", "nothing makes", "the kidneys", "pass more"], 1.0),
        ("Diluted electrolyte", "info-soft", "ok", "Best", ["Replaces salts;", "salt and sugar", "help the gut", "take water up"], 1.0),
        ("Very sugary drinks", "warn-soft", "warn", "Slow", ["Soft drink,", "cordial: water", "is held back", "in the gut"], 0.45),
        ("Lots of caffeine", "surface-2", "bad", "Lose water", ["Kidneys pass", "more water", "than you", "drink"], -0.5),
        ("Alcohol", "bad-soft", "bad", "Lose water", ["Kidneys pass", "more water", "than you drank:", "the hangover"], -0.8),
    ]
    w, gap, x0 = 112, 10, 16
    for i, (name, liquid, verdict, word, why, net) in enumerate(drinks):
        x = x0 + i * (w + gap)
        cx = x + w / 2
        c.add(rect(x, 48, w, 292, "surface", "line-strong", THIN, rx=10))
        # the glass
        c.add(polygon([(cx - 26, 64), (cx + 26, 64), (cx + 20, 140), (cx - 20, 140)], liquid, None))
        c.add(path(f"M{cx - 30} 58 L{cx - 20} 140 L{cx + 20} 140 L{cx + 30} 58", "fg-muted", None, SECOND))
        c.add(path(f"M{cx - 27} 76 L{cx + 27} 76", "fg-faint", None, THIN))
        c.add(multiline(cx, 162, name.split(" ", 1) if len(name) > 14 else [name], 13, "middle", "fg", 1.2, weight=600))
        c.add(pill(cx - 46, 192, 92, 24, verdict, word, 12))
        c.add(multiline(cx, 236, why, 11, "middle", "fg-muted", 1.3))
        # net water into the body: up for a gain, down for a loss, length for how much
        y0 = 316
        if net > 0:
            c.add(arrow(cx, y0 + 10, cx, y0 + 10 - 26 * net, verdict))
        else:
            c.add(arrow(cx, y0 - 14, cx, y0 - 14 - 26 * net, verdict))
    c.add(text(x0, 358, "↑ water kept   ↓ water lost", 11, "start", "fg-faint"))
    # the signs
    c.add(rect(16, 368, 608, 72, SOFT["warn"], "warn", SECOND, rx=10))
    c.add(text(28, 391, "Signs you are short of water", 13, "start", FG["warn"], weight=700))
    c.add(text(28, 411, "Headache, dry mouth, fatigue, dizziness on standing, poor concentration. Thirst comes late;", 12, "start", FG["warn"]))
    c.add(text(28, 428, "dark urine is the reliable early check.", 12, "start", FG["warn"], weight=600))
    return c
