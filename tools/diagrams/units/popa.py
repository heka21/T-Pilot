"""POPA (PPL aeroplane performance) diagrams. Every number comes from content/notes/POPA/*.md."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, arrow, badge, circle, fmt, group, line, multiline, num, path,
                                plane_side, plane_top, polygon, polyline, rect, sample, smooth_path, text)


def _dim(c: Canvas, x0: float, x1: float, y: float, label: str, colour: str, size: float = 13, anchor: str = "middle") -> None:
    """Dimension line with end ticks and the label above it."""
    fg = f"{colour}-fg" if colour in ("brand", "ok", "bad", "warn", "info") else colour
    c.add(line(x0, y - 7, x0, y + 7, colour, SECOND), line(x1, y - 7, x1, y + 7, colour, SECOND))
    c.add(line(x0, y, x1, y, colour, SECOND, cap="butt"))
    tx = {"middle": (x0 + x1) / 2, "start": x0 + 6, "end": x1 - 6}[anchor]
    c.add(num(tx, y - 8, label, size, anchor, fg, weight=700))


# ---------------------------------------------------------------- 2.1 required against available
@chart
def takeoff_landing_distances_ala() -> Canvas:
    c = Canvas("Required against available on a 700 m strip",
               "Three side views of the note's 700 m strip, distances to scale, heights exaggerated. Take-off: the ground run and the airborne "
               "segment together make the take-off distance required, 640 m from brake release to 50 ft at the take-off safety speed; with no "
               "clearway the take-off distance available is the 700 m strip, leaving 60 m. Landing: the landing distance required runs from 50 ft "
               "over the threshold to a stop, 520 m, against a landing distance available of 700 m, leaving 180 m. With the threshold displaced "
               "so the landing distance available is 500 m, the same 520 m landing is 20 m too long, although the strip is still 700 m.",
               height=650, prefix="tld")
    X0, S = 50, 0.75          # px per metre: 700 m = 525 px
    X = lambda m: X0 + m * S
    H50 = 46                  # 50 ft, exaggerated

    def strip(y: float, start: float = 0, faded_to: float | None = None) -> None:
        c.add(line(20, y, 620, y, "line-strong", SECOND))
        c.add(rect(X(0), y - 4, 700 * S, 8, "tarmac", None, rx=1))
        if faded_to is not None:
            c.add(rect(X(0), y - 4, faded_to * S, 8, "surface-2", "line-strong", THIN, rx=1))

    # ---- take-off
    y = 150
    c.add(text(20, 28, "Take-off: required must not exceed available", 16, "start", "fg", weight=700))
    strip(y)
    lo = 400  # lift-off point (shape only; the note gives no figure)
    pts = [(X(0), y - 10), (X(lo), y - 10)]
    c.add(line(X(0), y - 10, X(lo), y - 10, "brand", MAIN, dash="2 5"))
    c.add(path(f"M{fmt(X(lo))} {fmt(y - 10)} Q{fmt(X(560))} {fmt(y - 14)} {fmt(X(640))} {fmt(y - H50)}", "brand", None, MAIN))
    c.add(line(X(640), y, X(640), y - H50 - 4, "fg-muted", SECOND, dash=DASH))
    c.add(text(X(640) - 6, y - H50 - 26, "50 ft screen", 12, "end", "fg-muted"))
    c.add(text(X(640) - 6, y - H50 - 12, "at TOSS, at least 1.2 × stall", 11, "end", "fg-muted"))
    c.add(plane_side(X(640) + 22, y - H50 - 6, 0.42, pitch=8))
    c.add(text((X(0) + X(lo)) / 2, y - 20, "ground run", 12, "middle", "brand-fg", weight=600))
    c.add(text((X(lo) + X(640)) / 2 - 10, y - 30, "airborne", 12, "middle", "brand-fg", weight=600))
    c.add(text(X(0), y + 18, "brake release", 11, "start", "fg-faint"))
    c.add(text(X(700), y + 18, "end of strip", 11, "end", "fg-faint"))
    c.add(rect(X(640), y + 34, 60 * S, 20, "ok-soft", None))
    c.add(num(X(670), y + 48, "60 m", 12, "middle", "ok-fg", weight=700))
    _dim(c, X(0), X(640), y + 44, "TODR 640 m", "brand")
    _dim(c, X(0), X(700), y + 84, "TODA 700 m: the strip, no clearway", "ok")

    # ---- landing, threshold at the end
    y = 360
    c.add(line(20, 262, 620, 262, "line", THIN))
    c.add(text(20, 290, "Landing: from 50 ft over the threshold to a stop", 16, "start", "fg", weight=700))
    strip(y)
    td = 230
    c.add(path(f"M{fmt(X(0) - 26)} {fmt(y - H50 - 4)} L{fmt(X(0))} {fmt(y - H50)} Q{fmt(X(150))} {fmt(y - 12)} {fmt(X(td))} {fmt(y - 10)}", "brand", None, MAIN))
    c.add(line(X(td), y - 10, X(520), y - 10, "brand", MAIN, dash="2 5"))
    c.add(line(X(0), y, X(0), y - H50 - 4, "fg-muted", SECOND, dash=DASH))
    c.add(text(X(0) + 8, y - H50 - 6, "50 ft at threshold speed", 12, "start", "fg-muted"))
    c.add(plane_side(X(520) - 20, y - 18, 0.42))
    c.add(text(X(520) + 10, y - 16, "stop", 12, "start", "brand-fg", weight=600))
    c.add(rect(X(520), y + 34, 180 * S, 20, "ok-soft", None))
    c.add(num(X(610), y + 48, "180 m spare", 12, "middle", "ok-fg", weight=700))
    _dim(c, X(0), X(520), y + 44, "LDR 520 m", "brand")
    _dim(c, X(0), X(700), y + 84, "LDA 700 m", "ok")

    # ---- landing, displaced threshold
    y = 530
    c.add(line(20, 470, 620, 470, "line", THIN))
    c.add(text(20, 496, "Same landing, threshold displaced: LDA 500 m", 14, "start", "fg", weight=700))
    strip(y, faded_to=200)
    c.add(line(X(200), y - 7, X(200), y + 7, "paint", 3, cap="butt"))
    c.add(text(X(100), y - 10, "not for landing", 11, "middle", "fg-faint"))
    c.add(text(X(200) + 4, y - 10, "threshold", 11, "start", "fg-muted"))
    _dim(c, X(200), X(700), y + 40, "LDA 500 m", "ok")
    c.add(rect(X(700), y + 66, 20 * S, 16, "bad-soft", None))
    _dim(c, X(200), X(720), y + 74, "LDR 520 m", "bad", anchor="start")
    c.add(text(620, y + 100, "20 m over: not on this runway today", 12, "end", "bad-fg", weight=700))
    return c


# ---------------------------------------------------------------- 2.1 what a suitable ALA looks like
@chart
def ala_plan_view() -> Canvas:
    c = Canvas("What AC 91-02 asks of an ALA",
               "Plan view of a farm strip, not to scale. The runway is about 15 m wide for a light single-engine aeroplane, with a cleared runway "
               "strip beyond its edges and ends. At each end an obstacle-free approach and take-off area slopes up and out at about 5 percent, 1 in "
               "20, with lateral transitional surfaces along the sides. Longitudinal slope not more than about 2 percent, a firm, even, short-grass "
               "surface, a windsock and boundary markers. A 15 m strip leaves an 11 m-span trainer about 2 m beyond each wingtip. Figures as the note "
               "has them from AC 91-02: verify against the current AC.",
               height=354, prefix="ala")
    c.add(text(20, 28, "A suitable ALA, in plan (not to scale)", 16, "start", "fg", weight=700))
    c.add(text(620, 28, "AC 91-02 figures: verify", 12, "end", "warn-fg", weight=600))
    cy = 150
    rx0, rx1 = 170, 470          # runway ends
    # lateral transitional surfaces (under everything)
    for sg in (-1, 1):
        y0 = cy + sg * 46
        c.add(polygon([(rx0, y0), (rx0 + 20, y0 + sg * 40), (rx1 - 20, y0 + sg * 40), (rx1, y0)], "surface-2", "line-strong", THIN))
    c.add(text(320, cy - 60, "lateral transitional surface", 11, "middle", "fg-muted"))
    c.add(text(320, cy + 70, "lateral transitional surface: no trees, poles or fences", 11, "middle", "fg-muted"))
    # approach / take-off areas (trapezia) at both ends
    for sg, xe in ((-1, rx0), (1, rx1)):
        far = xe + sg * 150
        c.add(polygon([(xe, cy - 46), (far, cy - 86), (far, cy + 86), (xe, cy + 46)], "brand-soft", "brand", SECOND))
    c.add(multiline(84, cy - 6, ["approach and", "take-off area"], 12, "middle", "brand-fg", weight=600))
    c.add(num(84, cy + 30, "1 in 20 (5%)", 12, "middle", "brand-fg", weight=700))
    c.add(multiline(556, cy - 6, ["take-off and", "approach area"], 12, "middle", "brand-fg", weight=600))
    c.add(num(556, cy + 30, "1 in 20 (5%)", 12, "middle", "brand-fg", weight=700))
    # runway strip (cleared area)
    c.add(rect(rx0, cy - 46, rx1 - rx0, 92, "ok-soft", "ok", SECOND))
    c.add(text(380, cy - 26, "cleared runway strip", 12, "middle", "ok-fg", weight=600))
    c.add(text(300, cy + 36, "room for a swing or a run-off", 11, "middle", "ok-fg"))
    # runway (grass) with cone markers
    c.add(rect(rx0, cy - 16, rx1 - rx0, 32, "ok", None, fill_opacity=0.35))
    c.add(rect(rx0, cy - 16, rx1 - rx0, 32, None, "ok", THIN))
    for i in range(0, 6):
        xx = rx0 + 6 + i * (rx1 - rx0 - 12) / 5
        for yy in (cy - 16, cy + 16):
            c.add(polygon([(xx - 4, yy + 3), (xx, yy - 5), (xx + 4, yy + 3)], "warn", "fg", 1))
    c.add(plane_top(196, cy, 0.235, heading=90))
    c.add(text(216, cy + 5, "short, firm grass", 12, "start", "fg", weight=600))
    # width dimension
    wx = 432
    c.add(line(wx - 5, cy - 16, wx + 5, cy - 16, "brand", SECOND), line(wx - 5, cy + 16, wx + 5, cy + 16, "brand", SECOND))
    c.add(line(wx, cy - 16, wx, cy + 16, "brand", SECOND))
    c.add(num(wx - 8, cy + 5, "about 15 m", 12, "end", "brand-fg", weight=700))
    # windsock
    sx, sy = 196, cy - 22
    c.add(line(sx, sy + 8, sx, sy - 12, "fg", SECOND))
    c.add(polygon([(sx, sy - 12), (sx + 16, sy - 9), (sx + 16, sy - 5), (sx, sy - 2)], "warn", "fg", 1))
    c.add(text(sx + 22, sy - 4, "windsock", 11, "start", "fg-muted"))
    # callouts underneath
    y = 280
    c.add(line(20, 250, 620, 250, "line", THIN))
    items = [("about 15 m", "runway width, light singles"), ("≤ about 2%", "slope along the strip"),
             ("1 in 20", "approach and take-off"), ("markers", "and a windsock")]
    for i, (big, small) in enumerate(items):
        x = 20 + i * 150 + 75
        c.add(num(x, y, big, 15, "middle", "brand-fg", weight=700))
        c.add(text(x, y + 20, small, 11, "middle", "fg-muted"))
    c.add(text(20, 336, "15 m wide, 11 m span on the centreline: about 2 m of grass beyond each wingtip.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.1 the obstacle surface
@chart
def ala_obstacle_surface() -> Canvas:
    c = Canvas("A 1 in 20 surface beyond the end of the strip",
               "Side view beyond the end of an ALA, heights exaggerated. The take-off surface rises 1 ft for every 20 ft out. A 50 ft tree must "
               "be at least 1,000 ft, about 300 m, beyond the start of the surface to stay below it. A line of tall gums 150 m past the end, where "
               "the surface is only about 25 ft up, breaks it however long the strip.",
               height=325, prefix="aos")
    c.add(text(20, 28, "Nothing may poke through the 1 in 20 surface", 16, "start", "fg", weight=700))
    gy = 255
    x0 = 120                      # end of strip / start of surface
    S = 1.35                      # px per metre horizontally (0..350 m)
    V = 2.6                       # px per foot vertically
    X = lambda m: x0 + m * S
    Y = lambda ft: gy - ft * V
    c.add(rect(20, gy - 4, x0 - 20, 8, "ok", None, fill_opacity=0.35))
    c.add(text(66, gy + 22, "end of strip", 12, "middle", "fg-muted"))
    c.add(line(20, gy, 620, gy, "line-strong", SECOND))
    # the surface: 5% in metres -> at m metres height = 0.05*m metres = 0.164 m ft
    ft_at = lambda m: 0.05 * m * 3.2808
    c.add(polygon([(X(0), Y(0)), (X(355), Y(ft_at(355))), (X(355), Y(0))], "brand-soft", None, 0))
    c.add(line(X(0), Y(0), X(355), Y(ft_at(355)), "brand", MAIN))
    c.add(text(X(330), Y(ft_at(330)) - 12, "1 in 20 (5%)", 13, "end", "brand-fg", weight=700))
    def tree(m: float, h_ft: float, colour: str) -> None:
        x, top = X(m), Y(h_ft)
        c.add(line(x, gy, x, top + 14, colour, 3))
        c.add(ellipse_like(x, top + 10, 11, 12, colour))

    # 50 ft tree at 300 m: surface there is ~49 ft
    tree(325, 50, "ok")
    c.add(num(X(325) - 16, Y(50) + 84, "50 ft tree beyond 300 m", 12, "end", "ok-fg", weight=700))
    c.add(text(X(325) - 16, Y(50) + 100, "below the surface: OK", 12, "end", "ok-fg"))
    # tall gums at 150 m
    tree(150, 60, "bad")
    tree(160, 55, "bad")
    c.add(num(X(150) - 16, Y(60) - 6, "gums at 150 m", 12, "end", "bad-fg", weight=700))
    c.add(text(X(150) - 16, Y(60) + 10, "surface only ~25 ft here:", 12, "end", "bad-fg"))
    c.add(text(X(150) - 16, Y(60) + 26, "they break it", 12, "end", "bad-fg", weight=700))
    # rule
    c.add(text(20, 307, "Rise 1 for every 20 out: 50 ft × 20 = 1,000 ft, about 300 m.", 13, "start", "fg-muted"))
    return c


def ellipse_like(cx: float, cy: float, rx: float, ry: float, colour: str) -> str:
    from tools.diagrams.svg import ellipse
    return ellipse(cx, cy, rx, ry, f"{colour}-soft", colour, SECOND)


# ---------------------------------------------------------------- 2.2 which weight limit governs
@chart
def climb_weight_limit_governs() -> Canvas:
    c = Canvas("The lowest limit governs",
               "The note's worked example on one weight scale. Runway-limited weight from today's take-off chart 1,185 kg; structural MTOW 1,150 kg "
               "(MLW also 1,150 kg); climb weight limit today 1,095 kg. The lowest, the climb weight limit, governs. The loading sheet says 1,120 kg, "
               "25 kg over it: offload about 35 L of avgas at 0.72 kg/L, a bag, or wait for cooler air.",
               height=330, prefix="cwl")
    c.add(text(20, 28, "Take-off weight: the lowest limit wins", 16, "start", "fg", weight=700))
    ch = Chart(c, x=(1050, 1200), y=(0, 4), box=(170, 60, 590, 240), xticks=[1050, 1075, 1100, 1125, 1150, 1175, 1200],
               xlabel="Take-off weight (kg)", grid=False, xfmt=lambda v: f"{v:,.0f}")
    for t in ch.xticks:
        c.add(line(ch.px(t), ch.top, ch.px(t), ch.bottom, "line", THIN))
    rows = [(3.4, "Runway-limited (chart)", 1185, "info"), (2.2, "Structural MTOW", 1150, "fg-muted"), (1.0, "Climb limit today", 1095, "brand")]
    for yv, lab, kg, colour in rows:
        y = ch.py(yv)
        fill = {"info": "info-soft", "fg-muted": "surface-2", "brand": "brand-soft"}[colour]
        c.add(rect(ch.px(1050), y - 14, ch.px(kg) - ch.px(1050), 28, fill, colour, SECOND, rx=3))
        c.add(text(160, y + 5, lab, 13, "end", "fg" if colour != "brand" else "brand-fg", weight=600 if colour == "brand" else None))
        c.add(num(ch.px(kg) - 8, y + 5, f"{kg:,} kg", 13, "end", "fg" if colour != "brand" else "brand-fg", weight=700))
    # excess band and planned line
    y = ch.py(1.0)
    c.add(rect(ch.px(1095), y - 14, ch.px(1120) - ch.px(1095), 28, "bad-soft", None))
    c.add(num((ch.px(1095) + ch.px(1120)) / 2, y + 5, "+25", 13, "middle", "bad-fg", weight=700))
    c.add(line(ch.px(1120), ch.top - 6, ch.px(1120), ch.bottom, "bad", MAIN))
    c.add(num(ch.px(1120), ch.top - 12, "planned 1,120 kg", 13, "middle", "bad-fg", weight=700))
    c.add(ch.axes(arrows=False))
    c.add(text(20, 306, "25 kg over: offload about 35 L of avgas (0.72 kg/L), a bag, or wait for cooler air.", 13, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.2 what 10 percent overweight costs
@chart
def overweight_ten_percent() -> Canvas:
    c = Canvas("What 10 percent overweight costs",
               "Three before-and-after comparisons from the note, at the MTOW of 1,150 kg and at 1,265 kg, 10 percent over. Stall speed scales with "
               "the square root of weight: 48 kt becomes 50.3 kt, so a take-off safety speed meant to be 1.2 times the stall is only about 1.14 "
               "times it. Take-off distance grows with about the square of the weight: 1.1 squared is 1.21, about 20 percent more runway. The "
               "normal-category limit of 3.8 g at the MTOW becomes 3.8 divided by 1.1, about 3.45 g.",
               height=330, prefix="ovw")
    c.add(text(20, 28, "Load 10 percent over the MTOW (1,150 to 1,265 kg)", 16, "start", "fg", weight=700))
    panels = [
        ("Stall speed", "× √1.10", [("MTOW", 48, "48 kt"), ("+10%", 50.3, "50.3 kt")], 60, "TOSS margin: 1.2 → 1.14"),
        ("Take-off distance", "× 1.1²", [("MTOW", 100, "100%"), ("+10%", 121, "121%")], 130, "about 20% more runway"),
        ("Limit load", "÷ 1.1", [("MTOW", 3.8, "3.8 g"), ("+10%", 3.45, "3.45 g")], 4.2, "same structure, lower g"),
    ]
    for i, (title, op, bars, vmax, note) in enumerate(panels):
        x0 = 30 + i * 200
        c.add(text(x0 + 80, 70, title, 14, "middle", "fg", weight=700))
        c.add(num(x0 + 80, 90, op, 13, "middle", "fg-muted"))
        base = 250
        c.add(line(x0 + 10, base, x0 + 150, base, "line-strong", SECOND))
        for j, (lab, v, vl) in enumerate(bars):
            h = v / vmax * 130
            bx = x0 + 22 + j * 64
            worse = j == 1
            c.add(rect(bx, base - h, 50, h, "bad-soft" if worse else "surface-2", "bad" if worse else "fg-muted", SECOND, rx=2))
            c.add(num(bx + 25, base - h - 8, vl, 12, "middle", "bad-fg" if worse else "fg", weight=700))
            c.add(text(bx + 25, base + 18, lab, 12, "middle", "fg-muted"))
        c.add(text(x0 + 80, 296, note, 12, "middle", "bad-fg", weight=600))
    return c


# ---------------------------------------------------------------- 2.3 density altitude chart
def _da(pa: float, t: float) -> float:
    return pa + 120 * (t - (15 - 2 * pa / 1000))


@chart
def density_altitude_chart() -> Canvas:
    c = Canvas("Reading a density altitude chart",
               "An illustrative density altitude chart drawn from the note's own formula: density altitude equals pressure altitude plus 120 ft for "
               "each degree above the ISA temperature at that pressure altitude. Temperature runs along the bottom, density altitude up the side, "
               "and one sloping line for each 1,000 ft of pressure altitude. A dashed line joins the points where each line meets its ISA "
               "temperature, where density altitude equals pressure altitude. The worked example: up from 30 degrees to the 3,000 ft line, then "
               "across to read 5,520 ft. Use the chart you are given, not this one.",
               height=480, prefix="dac")
    c.add(text(20, 28, "Up from the temperature, across to the density altitude", 16, "start", "fg", weight=700))
    c.add(text(20, 50, "Illustrative: drawn from the 120 ft rule. Use the chart you are given.", 12, "start", "warn-fg", weight=600))
    ch = Chart(c, x=(-10, 45), y=(-2000, 10000), box=(80, 84, 560, 400), xticks=[-10, 0, 10, 20, 30, 40],
               yticks=[-2000, 0, 2000, 4000, 6000, 8000, 10000], xlabel="Outside air temperature (°C)", ylabel="Density altitude (ft)",
               yfmt=lambda v: f"{v:,.0f}")
    c.add(ch.axes(arrows=False))
    for pa in range(0, 7001, 1000):
        # clip the line to the y range
        t0 = -10
        t1 = 45
        tmax = (10000 - pa) / 120 + (15 - 2 * pa / 1000)
        tmin = (-2000 - pa) / 120 + (15 - 2 * pa / 1000)
        a, b = max(t0, tmin), min(t1, tmax)
        hl = pa == 3000
        c.add(ch.curve([(a, _da(pa, a)), (b, _da(pa, b))], "brand" if hl else "fg-muted", MAIN if hl else SECOND, smooth=False))
        X, Y = ch.pt(b, _da(pa, b))
        lab = f"{pa:,}" if pa else "0 ft"
        if b < t1:
            c.add(num(X, Y - 6, lab, 11, "middle", "brand-fg" if hl else "fg-muted", weight=700 if hl else None))
        else:
            c.add(num(X + 6, Y + 4, lab, 11, "start", "brand-fg" if hl else "fg-muted", weight=700 if hl else None))
    c.add(text(ch.px(45) + 6, ch.top - 34, "pressure", 11, "start", "fg-muted"))
    c.add(text(ch.px(45) + 6, ch.top - 20, "altitude", 11, "start", "fg-muted"))
    # ISA line: T = 15 - 2*DA/1000
    c.add(ch.curve([(15 - 2 * (-2000) / 1000, -2000), (15 - 2 * 10000 / 1000, 10000)], "fg-faint", SECOND, dash=DASH, smooth=False))
    X, Y = ch.pt(-4, 9500)
    c.add(text(X + 6, Y + 4, "ISA", 12, "start", "fg-muted", weight=600))
    # worked example
    da = _da(3000, 30)
    X, Y = ch.pt(30, da)
    c.add(line(ch.px(30), ch.bottom, X, Y, "bad", MAIN, arrow_end=True))
    c.add(line(X, Y, ch.left + 2, Y, "bad", MAIN, arrow_end=True))
    c.add(circle(X, Y, 5, "bad", "surface", 1.5))
    c.add(rect(ch.left + 8, Y - 26, 150, 20, "surface", None))
    c.add(num(ch.left + 12, Y - 11, "5,520 ft density alt", 12, "start", "bad-fg", weight=700))
    c.add(num(ch.px(30) + 6, ch.bottom - 10, "30°C", 12, "start", "bad-fg", weight=700))
    c.add(text(20, 466, "Pressure altitude 3,000 ft, OAT 30°C: ISA there is 9°C, +21°C × 120 ft = +2,520 ft, so 5,520 ft.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.3 two corrections, stacked
@chart
def density_height_kalgoorlie() -> Canvas:
    c = Canvas("Elevation, pressure height and density height at Kalgoorlie",
               "The note's Kalgoorlie exercise as three columns to scale. Elevation 1,200 ft. QNH 1008 is 5 hPa below 1013, so add 5 × 30 = 150 ft: "
               "pressure height 1,350 ft. ISA at 1,350 ft is 12.3 degrees; the OAT of 40 degrees is 27.7 above it, so add 27.7 × 120 = 3,324 ft: "
               "density height 4,674 ft, about 4,700. The temperature correction is more than twenty times the pressure correction.",
               height=400, prefix="dhk")
    c.add(text(20, 28, "Kalgoorlie, QNH 1008, OAT 40°C: two corrections", 16, "start", "fg", weight=700))
    base, top = 340, 70
    S = (base - top) / 5000
    Y = lambda ft: base - ft * S
    for ft in range(0, 5001, 1000):
        c.add(line(80, Y(ft), 600, Y(ft), "line", THIN))
        c.add(num(72, Y(ft) + 4, f"{ft:,}", 12, "end", "fg-muted"))
    c.add(text(18, (base + top) / 2, "Height (ft)", 13, "middle", "fg-muted", weight=600, rotate=-90))
    cols = [(150, "Elevation"), (310, "Pressure height"), (470, "Density height")]
    w = 90
    # elevation
    def block(x, f0, f1, fill, stroke):
        c.add(rect(x - w / 2, Y(f1), w, Y(f0) - Y(f1), fill, stroke, SECOND))
    block(150, 0, 1200, "surface-2", "fg-muted")
    block(310, 0, 1200, "surface-2", "fg-muted")
    block(310, 1200, 1350, "info-soft", "info")
    block(470, 0, 1200, "surface-2", "fg-muted")
    block(470, 1200, 1350, "info-soft", "info")
    block(470, 1350, 4674, "brand-soft", "brand")
    for x, lab in cols:
        c.add(text(x, base + 20, lab, 13, "middle", "fg", weight=600))
    c.add(num(150, Y(1200) - 8, "1,200 ft", 13, "middle", "fg", weight=700))
    c.add(num(310, Y(1350) - 8, "1,350 ft", 13, "middle", "info-fg", weight=700))
    c.add(num(470, Y(4674) - 8, "4,674 ft, about 4,700", 13, "middle", "brand-fg", weight=700))
    # correction notes
    c.add(line(310 + w / 2 + 4, Y(1275), 340, Y(1275) - 64, "fg-muted", THIN))
    c.add(multiline(232, Y(1275) - 92, ["+150 ft", "(1013 − 1008) × 30"], 12, "start", "info-fg", weight=600))
    c.add(multiline(470 + w / 2 + 8, Y(3000) - 10, ["+3,324 ft", "ISA 12.3°C", "+27.7° × 120"], 12, "start", "brand-fg", weight=600))
    c.add(text(20, 388, "Pressure first at 30 ft per hPa, then temperature at 120 ft per degree.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.4 working a take-off weight chart
@chart
def takeoff_weight_chart_walkthrough() -> Canvas:
    c = Canvas("Working a take-off weight chart, panel by panel",
               "A stylised take-off weight chart, not a real one, worked with the note's Northam inputs: pressure height 1,330 ft, 33 degrees, "
               "TODA 1,100 m, 13 kt headwind component, 1 percent upslope, grass. Go up from 33 degrees to a line interpolated between the "
               "sea-level and 2,000 ft lines, across to the first reference line, then in each correction panel follow the sloping guide lines from "
               "the reference line to the input value before carrying straight across to the next. A headwind and more runway raise the weight; "
               "upslope and grass lower it. The answer is read on the weight scale at the right. The climb weight limit is read from pressure "
               "height and temperature alone. Use the workbook chart: this one shows only the method.",
               height=470, prefix="tow")
    c.add(text(20, 28, "Follow the guide lines, one panel at a time", 16, "start", "fg", weight=700))
    c.add(text(20, 48, "Illustrative chart: the method only. Use the workbook chart or your POH.", 12, "start", "warn-fg", weight=600))
    top, bot = 80, 360

    # panel frames
    panels = {"pa": (30, 180), "toda": (192, 262), "wind": (274, 364), "slope": (376, 446), "surf": (458, 540)}
    refs = {"toda": 192, "wind": 274 + 40, "slope": 376 + 35, "surf": 458}
    for x0, x1 in panels.values():
        c.add(rect(x0, top, x1 - x0, bot - top, "surface", "line-strong", THIN))

    def clip_line(x0, y0, k, xa, xb, colour="line-strong", width=THIN):
        """Line through (x0, y0) with slope k, between xa and xb, clipped to top..bot; '' if outside."""
        f = lambda xx: y0 + k * (xx - x0)
        lo, hi = xa, xb
        if k:
            xt, xbm = x0 + (top - y0) / k, x0 + (bot - y0) / k
            l2, h2 = min(xt, xbm), max(xt, xbm)
            lo, hi = max(lo, l2), min(hi, h2)
        if hi - lo < 4:
            return ""
        return line(lo, f(lo), hi, f(hi), colour, width)

    # --- panel 1: pressure height and temperature
    px0, px1 = panels["pa"]
    TX = lambda t: 66 + t / 45 * (px1 - 8 - 66)
    REF = lambda t, pa: 140 + pa / 1000 * 34 + t * 1.8
    for pa in (0, 2000, 4000):
        c.add(line(TX(0), REF(0, pa), TX(45), REF(45, pa), "fg-muted", SECOND))
        c.add(num(TX(0) - 5, REF(0, pa) + 4, f"{pa:,}" if pa else "SL", 11, "end", "fg-muted"))
    c.add(line(TX(0), REF(0, 1330), TX(45), REF(45, 1330), "brand", SECOND, dash=DASH))
    c.add(num(TX(0) - 5, REF(0, 1330) + 4, "1,330", 11, "end", "brand-fg", weight=700))
    for t in (0, 15, 30, 45):
        c.add(line(TX(t), bot, TX(t), bot + 5, "fg-muted", THIN))
        c.add(num(TX(t), bot + 18, f"{t}", 11, "middle", "fg-muted"))
    c.add(text((px0 + px1) / 2, bot + 36, "temperature °C", 12, "middle", "fg-muted"))
    c.add(text((px0 + px1) / 2, top - 8, "pressure height", 12, "middle", "fg", weight=600))

    y = REF(33, 1330)
    route = [(TX(33), bot), (TX(33), y)]

    def corr(key, xval, k, title, ticks, xlabel):
        nonlocal y
        x0, x1 = panels[key]
        xref = refs[key]
        for off in range(-400, 700, 26):
            c.add(clip_line(xref, top + off, k, x0, x1))
        c.add(line(xref, top, xref, bot, "fg-muted", SECOND))
        c.add(text((x0 + x1) / 2, top - 8, title, 12, "middle", "fg", weight=600))
        for xx, lab in ticks:
            c.add(line(xx, bot, xx, bot + 5, "fg-muted", THIN))
            if lab:
                c.add(num(xx, bot + 18, lab, 11, "middle", "fg-muted"))
        c.add(text((x0 + x1) / 2, bot + 36, xlabel, 11, "middle", "fg-muted"))
        route.append((xref, y))
        y = y + k * (xval - xref)
        route.append((xval, y))
        c.add(circle(xval, y, 3.5, "bad", "surface", 1.2))

    tx0 = refs["toda"]
    corr("toda", tx0 + 44, -0.55, "TODA", [(tx0 + 11 * i, None) for i in range(1, 7)] + [(tx0 + 44, "1,100")], "metres")
    w0 = refs["wind"]
    corr("wind", w0 + 13 * 2, -0.75, "wind", [(w0 - 20, "10"), (w0, "0"), (w0 + 40, "20")], "tail · head (kt)")
    s0 = refs["slope"]
    corr("slope", s0 + 15, 0.6, "slope", [(s0 - 30, "2"), (s0, "0"), (s0 + 30, "2")], "down · up (%)")
    u0 = refs["surf"]
    corr("surf", 536, 0.4, "surface", [(536, None)], "sealed → grass")
    route.append((558, y))
    c.add(polyline(route, "bad", MAIN))
    c.add(line(550, y, 562, y, "bad", MAIN, arrow_end=True))
    # weight scale
    c.add(line(568, top, 568, bot, "fg", SECOND))
    for yy in range(int(top), int(bot) + 1, 28):
        c.add(line(568, yy, 574, yy, "fg-muted", THIN))
    c.add(text(592, (top + bot) / 2, "take-off weight (kg)", 12, "middle", "fg-muted", weight=600, rotate=-90))
    c.add(circle(568, y, 5, "bad", "surface", 1.5))
    # inputs
    for lx, lab in ((w0 + 26, "13 kt"), (s0 + 15, "1% up"), (499, "grass")):
        wdt = len(lab) * 8 + 8
        c.add(rect(lx - wdt / 2, top + 4, wdt, 18, "surface", "bad", THIN, rx=3))
        c.add(num(lx, top + 17, lab, 12, "middle", "bad-fg", weight=700))
    c.add(rect(TX(33) + 4, bot - 24, 34, 18, "surface", "bad", THIN, rx=3))
    c.add(num(TX(33) + 21, bot - 11, "33°", 12, "middle", "bad-fg", weight=700))
    c.add(text(20, 420, "Up from the temperature to the pressure height, across to each reference line, then parallel to the", 12, "start", "fg-muted"))
    c.add(text(20, 436, "guide lines to the input. Headwind and runway raise the weight; upslope and grass lower it.", 12, "start", "fg-muted"))
    c.add(text(20, 456, "Climb weight limit: read from pressure height and temperature only, no runway panels.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.4 the landing limit caps the take-off weight
@chart
def landing_weight_caps_takeoff() -> Canvas:
    c = Canvas("The landing weight can cap the take-off weight",
               "Aircraft ECHO from the note: MTOW 2,950 kg, MLW 2,725 kg, trip fuel 250 L of avgas at 0.72 kg/L, which is 180 kg. Left, taking "
               "off at the MTOW of 2,950 kg lands at 2,770 kg, 45 kg over the MLW. Right, the maximum take-off weight for this trip is the MLW plus "
               "the fuel burn, 2,725 + 180 = 2,905 kg, which lands exactly at the MLW.",
               height=380, prefix="lwc")
    c.add(text(20, 28, "Aircraft ECHO: 250 L trip fuel = 180 kg burned", 16, "start", "fg", weight=700))
    lo, hi = 2700, 3000
    top, bot = 70, 320
    Y = lambda kg: bot - (kg - lo) / (hi - lo) * (bot - top)
    for kg in range(2700, 3001, 50):
        c.add(line(90, Y(kg), 600, Y(kg), "line", THIN))
        c.add(num(82, Y(kg) + 4, f"{kg:,}", 11, "end", "fg-muted"))
    c.add(text(18, (top + bot) / 2, "Weight (kg)", 13, "middle", "fg-muted", weight=600, rotate=-90))
    c.add(line(90, Y(2950), 600, Y(2950), "fg-muted", SECOND, dash=DASH))
    c.add(text(596, Y(2950) - 6, "MTOW 2,950", 12, "end", "fg-muted", weight=600))
    c.add(line(90, Y(2725), 600, Y(2725), "ok", MAIN, dash=DASH))
    c.add(text(98, Y(2725) - 8, "MLW 2,725", 12, "start", "ok-fg", weight=700))

    def trip(x0, tow, colour, title):
        land = tow - 180
        x1 = x0 + 160
        c.add(text((x0 + x1) / 2, 56, title, 13, "middle", "fg", weight=700))
        c.add(circle(x0, Y(tow), 5, colour, "surface", 1.5))
        c.add(circle(x1, Y(land), 5, colour, "surface", 1.5))
        c.add(line(x0 + 6, Y(tow) + 2, x1 - 7, Y(land) - 2, colour, MAIN, arrow_end=True))
        c.add(num(x0, Y(tow) - 12, f"take-off {tow:,}", 12, "middle", f"{colour}-fg" if colour != "fg" else "fg", weight=700))
        c.add(num((x0 + x1) / 2 + 10, (Y(tow) + Y(land)) / 2 - 10, "−180", 12, "start", "fg-muted"))
        c.add(num(x1 + 12, Y(land) - 8, f"lands {land:,}", 12, "start", f"{colour}-fg", weight=700))
        return x1, land

    x1, land = trip(130, 2950, "bad", "Take off at the MTOW")
    c.add(rect(x1 - 4, Y(2770), 8, Y(2725) - Y(2770), "bad-soft", "bad", THIN))
    c.add(num(x1 + 12, (Y(2770) + Y(2725)) / 2 + 8, "45 kg over the MLW", 12, "start", "bad-fg", weight=700))
    trip(380, 2905, "brand", "Take off at 2,905")
    c.add(text(20, 364, "Maximum take-off weight for the trip = MLW + fuel burned = 2,725 + 180 = 2,905 kg.", 13, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.5 climb table: subtract the rows
@chart
def climb_table_subtract() -> Canvas:
    c = Canvas("Climb tables are cumulative from sea level",
               "The note's climb table as a climb profile, still air, ISA. From sea level to 3,000 ft: 5 min, 3 L, 6 nm. From sea level to "
               "7,000 ft: 13 min, 7 L, 17 nm. The climb from 3,000 to 7,000 ft is the difference: 8 min, 4 L, 11 nm. The first part of each "
               "row belongs to an aerodrome at sea level.",
               height=360, prefix="cts")
    c.add(text(20, 28, "Subtract the rows: the table starts at sea level", 16, "start", "fg", weight=700))
    ch = Chart(c, x=(0, 20), y=(0, 8000), box=(80, 56, 600, 290), xticks=[0, 5, 10, 15, 20], yticks=[0, 2000, 4000, 6000, 8000],
               xlabel="Still-air distance from the start of the climb (nm)", ylabel="Pressure altitude (ft)", yfmt=lambda v: f"{v:,.0f}")
    c.add(ch.axes(arrows=False))
    pts = [(0, 0), (2.8, 1500), (6, 3000), (11.2, 5000), (17, 7000)]
    c.add(ch.curve(pts[:3], "fg-faint", MAIN, dash=DASH))
    c.add(ch.curve(pts[2:], "brand", 3))
    c.add(ch.point(6, 3000, "fg-muted"))
    c.add(ch.point(17, 7000, "brand"))
    c.add(ch.callout(6, 3000, -40, -60, ["to 3,000 ft:", "5 min, 3 L, 6 nm"], "fg-muted"))
    c.add(ch.callout(17, 7000, -40, -18, ["to 7,000 ft: 13 min, 7 L, 17 nm"], "fg"))
    # the difference bracket
    X0, X1, Yd = ch.px(6), ch.px(17), ch.py(0) - 18
    c.add(line(X0, Yd - 5, X0, Yd + 5, "brand", SECOND), line(X1, Yd - 5, X1, Yd + 5, "brand", SECOND), line(X0, Yd, X1, Yd, "brand", SECOND))
    c.add(num((X0 + X1) / 2, Yd - 8, "17 − 6 = 11 nm", 13, "middle", "brand-fg", weight=700))
    c.add(rect(ch.px(10.6), ch.py(4600), 160, 46, "surface", "brand", SECOND, rx=4))
    c.add(text(ch.px(10.6) + 80, ch.py(4600) + 18, "3,000 → 7,000 ft", 13, "middle", "brand-fg", weight=700))
    c.add(num(ch.px(10.6) + 80, ch.py(4600) + 36, "8 min · 4 L · 11 nm", 13, "middle", "brand-fg", weight=700))
    c.add(text(ch.px(2.2), ch.py(0) - 26, "from sea level:", 12, "start", "fg-faint"))
    c.add(text(ch.px(2.2), ch.py(0) - 11, "not your climb", 12, "start", "fg-faint"))
    return c


# ---------------------------------------------------------------- 2.5 range and endurance speeds on the power curve
@chart
def power_required_range_endurance() -> Canvas:
    a, b = 3.888e7, 1.0         # P = a/V + b V^3 (shape only): Vmp 60, Vmd 79
    P = lambda v: a / v + b * v ** 3
    vmp = (a / (3 * b)) ** 0.25
    vmd = (a / b) ** 0.25
    w = 36.0                    # headwind (shape only)
    vhw = min((v / 10 for v in range(400, 2000)), key=lambda v: P(v) / (v - w))
    c = Canvas("Endurance and range speeds on the power-required curve",
               "Power required to fly level against true airspeed, a U-shaped curve; fuel flow follows power. The lowest point is the "
               "minimum-power speed, the maximum endurance speed: least fuel per hour. A straight line from the origin touches the curve at the "
               "minimum-drag speed, because power divided by speed is drag: that is the still-air maximum range speed, faster than the endurance "
               "speed. With a headwind the line starts from the wind speed on the speed axis and touches the curve at a higher speed: fly faster "
               "for range into a headwind. Shape only, no figures.",
               height=400, prefix="prr")
    c.add(text(20, 28, "Bottom of the curve for time, tangent from the origin for distance", 16, "start", "fg", weight=700))
    ch = Chart(c, x=(0, 150), y=(0, 2.2e6), box=(70, 56, 600, 330), xlabel="True airspeed", ylabel="Power required (fuel flow)",
               grid=False)
    c.add(ch.axes())
    c.add(ch.curve(sample(P, 36, 122, 80), "fg", MAIN))
    # tangents
    c.add(ch.curve([(0, 0), (138, P(vmd) / vmd * 138)], "brand", SECOND, smooth=False))
    c.add(ch.curve([(w, 0), (140, P(vhw) / (vhw - w) * (140 - w))], "info", SECOND, dash=DASH, smooth=False))
    # points
    c.add(ch.point(vmp, P(vmp), "ok"))
    c.add(ch.point(vmd, P(vmd), "brand"))
    c.add(ch.point(vhw, P(vhw), "info"))
    for v, colour in ((vmp, "ok"), (vmd, "brand"), (vhw, "info")):
        c.add(line(ch.px(v), ch.py(P(v)) + 6, ch.px(v), ch.bottom, colour, THIN, dash=DASH))
    c.add(text(ch.px(vmp), ch.bottom + 16, "Vmp", 12, "middle", "ok-fg", weight=700))
    c.add(text(ch.px(vmd), ch.bottom + 16, "Vmd", 12, "middle", "brand-fg", weight=700))
    c.add(text(ch.px(vhw) + 4, ch.bottom + 16, "faster", 12, "start", "info-fg", weight=700))
    c.add(ch.callout(vmp, P(vmp), -110, -150, ["Minimum power:", "max endurance,", "least fuel per hour"], "ok-fg"))
    c.add(ch.callout(vmd, P(vmd), 70, 70, ["Tangent from the origin:", "minimum drag, best L/D,", "max range in still air"], "brand-fg"))
    c.add(ch.callout(vhw, P(vhw), 56, -6, ["Into a headwind, start", "the tangent at the wind", "speed: range speed rises"], "info-fg", 12))
    c.add(num(ch.px(w), ch.bottom + 16, "headwind", 11, "middle", "info-fg"))
    return c


# ---------------------------------------------------------------- 2.5 planning the descent
@chart
def descent_planning_topd() -> Canvas:
    c = Canvas("Planning the top of descent",
               "The note's descent example. Cruising at 6,500 ft, joining the circuit at 1,500 ft: 5,000 ft to lose. At 500 ft per minute that is "
               "10 minutes; at a descent groundspeed of 110 kt the aeroplane covers 18.3 nm in that time, so the top of descent is about 18 nm "
               "before the joining point. Fuel at the illustrative cruise flow of 30 L/h is 5 L.",
               height=320, prefix="tod")
    c.add(text(20, 28, "Time = height ÷ rate; distance = time × groundspeed", 16, "start", "fg", weight=700))
    ch = Chart(c, x=(-6, 22), y=(0, 7500), box=(80, 60, 600, 250), xticks=[], yticks=[1500, 6500], grid=False,
               ylabel="Altitude (ft)", yfmt=lambda v: f"{v:,.0f}")
    c.add(ch.axes(arrows=False))
    c.add(ch.curve([(-6, 6500), (0, 6500), (18.3, 1500), (22, 1500)], "fg-faint", MAIN, smooth=False))
    c.add(ch.curve([(0, 6500), (18.3, 1500)], "brand", 3, smooth=False))
    c.add(ch.point(0, 6500, "brand", label="TOPD", dx=0, dy=-12, anchor="middle"))
    c.add(ch.point(18.3, 1500, "ok", label="join 1,500 ft", dx=0, dy=24, anchor="middle"))
    c.add(plane_side(ch.px(-3.5), ch.py(6500) - 12, 0.4))
    X0, X1, Yd = ch.px(0), ch.px(18.3), ch.bottom + 22
    c.add(line(X0, Yd - 5, X0, Yd + 5, "brand", SECOND), line(X1, Yd - 5, X1, Yd + 5, "brand", SECOND), line(X0, Yd, X1, Yd, "brand", SECOND))
    c.add(num((X0 + X1) / 2, Yd + 20, "10/60 × 110 kt = 18.3 nm", 13, "middle", "brand-fg", weight=700))
    mx, my = ch.pt(9.15, 4000)
    c.add(multiline(mx + 20, my - 40, ["5,000 ft ÷ 500 ft/min", "= 10 min, about 5 L at 30 L/h"], 13, "start", "brand-fg", weight=600))
    return c
