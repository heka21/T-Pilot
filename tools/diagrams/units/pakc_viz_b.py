"""PAKC 3.5-3.10 visualisation push (2026-10-11): extra diagrams for the radio lessons. Every call, number and
order comes from content/notes/PAKC/*.md; timings that only illustrate say so."""
from __future__ import annotations

from tools.diagrams.charts import chart
from tools.diagrams.svg import MAIN, SECOND, THIN, Canvas, line, multiline, num, rect, text

SOFT = {"brand": "brand-soft", "ok": "ok-soft", "warn": "warn-soft", "bad": "bad-soft", "info": "info-soft", "fg": "surface"}
EDGE = {"brand": "brand", "ok": "ok", "warn": "warn", "bad": "bad", "info": "info", "fg": "line-strong"}
INK = {"brand": "brand-fg", "ok": "ok-fg", "warn": "warn-fg", "bad": "bad-fg", "info": "info-fg", "fg": "fg"}


# ================================================================ 3.5 air time on a shared frequency
@chart
def blocked_call_air_time() -> Canvas:
    top, px = 96, 21                       # y of 0 s, pixels per second
    cols = {"tower": (64, 184), "you": (192, 312), "final": (320, 440), "all": (456, 620)}
    secs = 14
    h = top + secs * px + 100
    c = Canvas("One frequency, one talker at a time",
               "Fourteen seconds on a busy tower frequency, time running down the page, with a column for the tower, for you, for "
               "an aircraft on final, and for what everyone on the frequency hears. You read back your landing clearance with your "
               "call-sign, then add a polite thanks lasting two to three seconds. The aircraft on final presses its PTT during the "
               "thanks to say it is going around; the two transmissions clash into a squeal and both are lost, so the tower has to "
               "ask for a repeat and the go-around call is heard late. Courtesy on the radio is brevity. Timings are illustrative.",
               height=h, prefix="bca")
    c.add(text(20, 30, "A polite “thanks” costs air time: one talker at a time", 16, "start", "fg", weight=700))
    heads = {"tower": "Tower", "you": "You", "final": "Aircraft on final", "all": "Everyone hears"}
    for k, (x0, x1) in cols.items():
        if k != "all":
            c.add(text((x0 + x1) / 2, top - 22, heads[k], 13, "middle", "fg-muted", weight=700))
    c.add(rect(cols["all"][0] - 4, top - 40, cols["all"][1] - cols["all"][0] + 8, secs * px + 48, "surface-2", None, rx=10))
    c.add(text((cols["all"][0] + cols["all"][1]) / 2, top - 22, "Everyone hears", 13, "middle", "brand-fg", weight=700))
    # time axis
    c.add(line(48, top, 48, top + secs * px, "line-strong", THIN, cap="butt"))
    for s in range(0, secs + 1, 2):
        y = top + s * px
        c.add(line(44, y, 48, y, "line-strong", THIN, cap="butt"), num(40, y + 4, f"{s} s", 11, "end", "fg-faint"))

    def bar(col: str, t0: float, t1: float, tone: str, lines: list[str], size: float = 12, dash: str | None = None, italic: bool = False) -> None:
        x0, x1 = cols[col]
        y0, y1 = top + t0 * px, top + t1 * px
        c.add(rect(x0, y0, x1 - x0, y1 - y0, SOFT[tone], EDGE[tone], SECOND, rx=6, dash=dash))
        if lines:
            yy = (y0 + y1) / 2 - (len(lines) - 1) * size * 0.65 + size * 0.36
            c.add(multiline((x0 + x1) / 2, yy, lines, size, "middle", INK[tone], 1.3, italic=italic))

    bar("tower", 0, 3, "fg", ["Your landing", "clearance"])
    bar("you", 3.4, 5.4, "ok", ["Readback with", "your call-sign"])
    bar("you", 5.8, 8.6, "warn", ["“Thanks very", "much, have a", "good day”"], italic=True)
    bar("final", 6.4, 8.0, "bad", ["“Going around”"], italic=True)
    bar("tower", 9.2, 10.8, "fg", ["Asks for", "a repeat"])
    bar("final", 11.4, 13.0, "warn", ["“Going around”,", "again"], italic=True)
    # what the frequency carries
    bar("all", 0, 3, "fg", ["Clearance"])
    bar("all", 3.4, 5.4, "ok", ["Readback"])
    bar("all", 5.8, 6.4, "warn", [])
    bar("all", 6.4, 8.0, "bad", ["Squeal: both", "calls lost"], size=12.5)
    bar("all", 8.0, 8.6, "warn", [])
    bar("all", 9.2, 10.8, "fg", ["Repeat request"])
    bar("all", 11.4, 13.0, "warn", ["The go-around,", "heard late"])
    # notes in the empty space of the columns
    c.add(multiline(252, top + 9.6 * px, ["2 to 3 s when", "nobody else can", "be heard"], 12, "middle", "warn-fg", 1.3, weight=600))
    c.add(multiline(380, top + 2.2 * px, ["Waiting for a", "gap to call"], 12, "middle", "fg-muted", 1.3))
    c.add(multiline(380, top + 9.2 * px, ["Pressed the PTT", "during your thanks"], 12, "middle", "bad-fg", 1.3))
    # moving playhead: the one moving element
    c.style(f".bca-head{{animation:bca-head 7s linear infinite}}\n@keyframes bca-head{{from{{transform:translateY(0)}}to{{transform:translateY({secs * px}px)}}}}")
    c.add(line(52, top, 624, top, "brand", MAIN, cls="bca-head", opacity=0.55))
    yb = top + secs * px + 34
    c.add(multiline(20, yb, ["Courtesy on the radio is brevity: a correct readback with your call-sign", "is all the thanks a controller needs."], 13, "start", "fg", 1.35, weight=600))
    c.add(text(20, yb + 44, "Timings illustrative. Two stations transmitting together produce a squeal, and both messages are lost.", 12, "start", "fg-faint"))
    return c
