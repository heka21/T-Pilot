"""PMTC (meteorology, PPL): static and animated diagrams added in the 2026-10-10 visualisation push (the widgets live in
content/widgets). Numbers come from content/notes/PMTC/; change the note first, then the diagram."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import DASH, MAIN, SECOND, THIN, Canvas, Chart, badge, circle, fmt, group, line, multiline, path, rect, text
from tools.diagrams.units.rmtc import arrow, canvas, cumulus, sun


# ================================================================ PMTC 2.2 heat
@chart
def four_ways_air_is_heated() -> Canvas:
    c = canvas("Four ways the air gets its heat",
               "Four panels. Radiation: sunlight passes through clear air and is absorbed by the ground, and the ground radiates its own heat to "
               "the sky, by night with nothing coming back. Conduction: the ground warms or chills only the thin layer of air touching it. "
               "Convection: air warmed at the ground rises in thermals and cooler air sinks to replace it, spreading the heat through thousands of "
               "feet; moving air sideways is advection. Latent heat: water absorbs heat when it evaporates and gives it back when it condenses "
               "in cloud.", height=470, prefix="fwh")
    c.style(".fwh-bubble { animation: fwh-rise 5s ease-in-out infinite; } "
            "@keyframes fwh-rise { 0% { transform: translateY(0); opacity: 0; } 15% { opacity: 1; } 85% { opacity: 1; } 100% { transform: translateY(-112px); opacity: 0; } }")
    c.add(text(320, 28, "Four ways the air gets its heat", 16, "middle", "fg", weight=700))
    W, H = 300, 150
    panels = [(14, 44), (326, 44), (14, 252), (326, 252)]
    titles = ["Radiation", "Conduction", "Convection", "Latent heat"]
    notes = [["The sun heats the ground, not the air;", "the ground radiates heat away day and night"],
             ["Contact: only the thin layer of air", "touching the ground warms or chills"],
             ["Thermals carry the heat up thousands of feet;", "sideways movement is advection"],
             ["Evaporation takes heat in;", "condensation in cloud gives it back"]]
    for (ox, oy), title, note in zip(panels, titles, notes):
        c.add(rect(ox, oy, W, H, "sky-soft", None, rx=10, fill_opacity=0.6))
        c.add(rect(ox, oy + H - 34, W, 34, "ok-soft", None))
        c.add(line(ox, oy + H - 34, ox + W, oy + H - 34, "fg-muted", SECOND))
        c.add(rect(ox, oy, W, H, None, "line-strong", THIN, rx=10))
        c.add(badge(ox + 52, oy + 18, title, "brand" if title == "Convection" else "neutral", 12))
        c.add(multiline(ox + W / 2, oy + H + 16, note, 11, "middle", "fg-muted", leading=1.25))
    g = lambda ox, oy: oy + H - 34  # ground line
    # radiation: sun rays through the air to the ground, the ground radiating back to the sky
    ox, oy = panels[0]
    c.add(sun(ox + 40, oy + 62, 12))
    for dx in (0, 34, 68):
        c.add(arrow(ox + 66 + dx, oy + 70, ox + 116 + dx, g(ox, oy) - 4, "warn", SECOND))
    for x in (ox + 210, ox + 250):
        c.add(path(f"M{x} {g(ox, oy) - 4} q-8 -12 0 -24 q8 -12 0 -24 q-8 -12 0 -24", "bad", None, SECOND, arrow_end=True))
    c.add(text(ox + 230, oy + 32, "out to the sky", 11, "middle", "bad"))
    c.add(text(ox + 110, g(ox, oy) + 22, "ground absorbs sunlight", 11, "middle", "fg-muted"))
    # conduction: a thin warmed layer on the ground
    ox, oy = panels[1]
    c.add(rect(ox + 1, g(ox, oy) - 14, W - 2, 14, "bad-soft", None))
    c.add(line(ox + 1, g(ox, oy) - 14, ox + W - 1, g(ox, oy) - 14, "bad", THIN, DASH))
    c.add(text(ox + 150, g(ox, oy) - 20, "warmed by contact: the bottom few feet", 12, "middle", "bad", weight=600))
    c.add(text(ox + 150, oy + 56, "air above: hardly touched", 12, "middle", "fg-muted"))
    c.add(text(ox + 150, g(ox, oy) + 22, "sunlit ground (or cold ground at night)", 11, "middle", "fg-muted"))
    # convection: a thermal rising to a cumulus, cooler air sinking either side, one rising bubble animated
    ox, oy = panels[2]
    cx = ox + 120
    c.add(cumulus(cx - 50, oy + 66, cx + 50, [16, 26, 18]))
    c.add(path(f"M{cx} {g(ox, oy) - 4} C{cx - 12} {g(ox, oy) - 40} {cx + 12} {g(ox, oy) - 70} {cx} {oy + 72}", "bad", None, MAIN, arrow_end=True))
    c.add(arrow(cx + 70, oy + 80, cx + 70, g(ox, oy) - 8, "info", SECOND))
    c.add(arrow(cx - 70, oy + 80, cx - 70, g(ox, oy) - 8, "info", SECOND))
    c.add(text(cx + 78, oy + 112, "cooler air sinks", 11, "start", "info"))
    c.add(group(circle(cx, g(ox, oy) - 14, 8, "bad-soft", "bad", SECOND), cls="fwh-bubble"))
    c.add(arrow(ox + 200, g(ox, oy) + 18, ox + 280, g(ox, oy) + 18, "fg-muted", SECOND))
    c.add(text(ox + 196, g(ox, oy) + 22, "advection", 11, "end", "fg-muted"))
    # latent heat: water evaporating from a lake, condensing in a cloud
    ox, oy = panels[3]
    c.add(rect(ox + 30, g(ox, oy) - 2, 120, 10, "sky-soft", "sky-fg", THIN, rx=4))
    c.add(text(ox + 90, g(ox, oy) + 26, "lake", 11, "middle", "sky-fg"))
    for x in (ox + 60, ox + 90, ox + 120):
        c.add(path(f"M{x} {g(ox, oy) - 6} q-5 -9 0 -18 q5 -9 0 -18", "sky-fg", None, SECOND, arrow_end=True))
    c.add(multiline(ox + 90, g(ox, oy) - 64, ["evaporation:", "heat taken in"], 11, "middle", "info", weight=600, leading=1.2))
    c.add(cumulus(ox + 180, oy + 64, ox + 280, [16, 26, 16]))
    c.add(text(ox + 230, oy + 84, "condensation:", 11, "middle", "bad", weight=600))
    c.add(text(ox + 230, oy + 98, "heat given back", 11, "middle", "bad", weight=600))
    c.add(text(320, 462, "The air is heated from below: the ground, not the sun, is the stove.", 12, "middle", "fg-muted"))
    return c


# ================================================================ PMTC 2.5 winds
@chart
def gust_vs_squall() -> Canvas:
    c = canvas("A gust and a squall, side by side",
               "Two traces of wind speed against time over five minutes. Top: a gusty wind, mean 15 kt, with gusts lasting a few seconds; the "
               "strongest reaches 27 kt, more than 10 kt above the mean, so the report is 25015G27KT. Bottom: a squall, the wind jumping from "
               "12 kt by 18 kt to 30 kt within seconds and staying there for more than two minutes: an increase of at least 16 kt, to 22 kt or "
               "more, lasting at least a minute, reported as SQ.", height=486, prefix="gvs")
    c.add(text(320, 28, "A gust lasts seconds; a squall lasts minutes", 16, "middle", "fg", weight=700))
    xt = [0, 60, 120, 180, 240, 300]
    yt = [0, 10, 20, 30, 40]

    def trace(base, spikes):
        pts = []
        for i in range(0, 301, 2):
            v = base(i) + 1.2 * math.sin(i * 0.37) + 0.8 * math.sin(i * 0.11 + 1)
            for t0, peak in spikes:
                if abs(i - t0) <= 4:
                    v = max(v, peak - abs(i - t0) * (peak - base(i)) / 5)
            pts.append((i, v))
        return pts

    # top: gusty wind
    top = Chart(c, (0, 300), (0, 40), box=(76, 62, 570, 192), ylabel="wind (kt)", xticks=xt, yticks=yt, xfmt=lambda v: "")
    c.add(top.axes(arrows=False))
    c.add(top.hline(15, "fg-muted", DASH))
    c.add(text(top.px(300) + 4, top.py(15) + 4, "mean 15", 11, "start", "fg-muted"))
    gusts = [(40, 27), (112, 23), (178, 25), (252, 21)]
    c.add(top.curve(trace(lambda i: 15, gusts), "info", SECOND, smooth=False))
    gx, gy = top.pt(40, 36)
    c.add(text(gx + 14, gy + 2, "gust to 27 kt: a few seconds", 12, "start", "info", weight=600))
    c.add(text(gx + 14, gy + 17, "10 kt or more above the mean, so reported: 25015G27KT", 11, "start", "fg-muted"))
    c.add(text(76, 52, "Gusty wind (turbulence)", 13, "start", "fg", weight=700))
    # bottom: a squall
    bot = Chart(c, (0, 300), (0, 40), box=(76, 270, 570, 400), xlabel="time (seconds)", ylabel="wind (kt)", xticks=xt, yticks=yt)
    c.add(bot.axes(arrows=False))
    c.add(bot.band(120, 260, "bad", 0.10))

    def sq(i):
        if i < 116:
            return 12
        if i < 128:
            return 12 + 18 * (i - 116) / 12
        if i < 260:
            return 30
        return 30 - 10 * min(1, (i - 260) / 30)
    c.add(bot.curve(trace(sq, []), "bad", MAIN, smooth=False))
    c.add(text(76, 260, "Squall (SQ): fronts, squall lines, storm outflow", 13, "start", "fg", weight=700))
    x1, y1 = bot.pt(108, 12)
    c.add(arrow(x1, y1, x1, bot.py(29), "fg-muted", SECOND))
    c.add(multiline(x1 - 8, bot.py(37), ["up 18 kt", "(16 or more)", "to 30 kt", "(22 or more)"], 11, "end", "fg-muted", leading=1.2))
    c.add(text(bot.px(190), bot.py(36), "lasts at least a minute: here over two", 12, "middle", "bad", weight=600))
    c.add(multiline(320, 462, ["A gust is a few seconds of turbulence in a steady wind; a squall is a new wind that arrives and stays,",
                               "often with a direction change, a temperature drop and heavy rain. Traces illustrative."], 11, "middle", "fg-muted", leading=1.3))
    return c
