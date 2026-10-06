"""BAKC 2.1 to 3.5: direction, distance and speed, time, units, energy, the piston engine, fuels, engine handling,
malfunctions and flight instruments. Numbers on every figure come from the note it sits in."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, angle_mark, arc_path, arrow, badge, callout, circle, ellipse, fmt, group,
                                line, multiline, num, path, plane_side, plane_top, polygon, polyline, rect, sample, smooth_path, text)


# ---------------------------------------------------------------- helpers
def bxy(cx: float, cy: float, r: float, bearing: float) -> tuple[float, float]:
    """Point at a compass bearing (0 = up the page, clockwise) and distance r from (cx, cy)."""
    b = math.radians(bearing)
    return cx + r * math.sin(b), cy - r * math.cos(b)


def barc(cx: float, cy: float, r: float, b0: float, b1: float) -> str:
    """Arc path between two compass bearings (clockwise from b0 to b1)."""
    return arc_path(cx, cy, r, b0 - 90, b1 - 90)


def panel(x: float, y: float, w: float, h: float, fill: str = "surface-2", stroke: str | None = None) -> str:
    return rect(x, y, w, h, fill, stroke, THIN if stroke else MAIN, rx=10)


def compass_card(cx: float, cy: float, r: float, labels: bool = True, every: int = 10, size: float = 12) -> str:
    """Compass rose: ticks every `every` degrees, longer every 30, cardinal letters."""
    out = [circle(cx, cy, r, "surface", "fg", SECOND)]
    for b in range(0, 360, every):
        long_ = b % 30 == 0
        x0, y0 = bxy(cx, cy, r, b)
        x1, y1 = bxy(cx, cy, r - (12 if long_ else 6), b)
        out.append(line(x0, y0, x1, y1, "fg-muted", SECOND if long_ else THIN))
    if labels:
        for b, s in ((0, "N"), (90, "E"), (180, "S"), (270, "W")):
            x, y = bxy(cx, cy, r - 24, b)
            out.append(text(x, y + size * 0.35, s, size + 1, "middle", "fg", weight=700))
    return "".join(out)


# ================================================================ BAKC 2.1 direction of flight
@chart
def compass_rose_headings() -> Canvas:
    c = Canvas("Directions as 3-figure groups and runway numbers",
               "A compass rose with directions measured clockwise from north: 360 for north, 090 east, 180 south, 225 south-west and 270 west. "
               "A runway aligned 214 degrees magnetic is runway 21; its other end, 034 degrees, is runway 03; the two numbers differ by 18.",
               height=400, prefix="crh")
    CX, CY, R = 200, 210, 150
    c.add(compass_card(CX, CY, R, labels=False))
    # cardinal 3-figure labels outside the ring
    for b, s in ((0, "360"), (90, "090"), (180, "180"), (270, "270"), (225, "225")):
        x, y = bxy(CX, CY, R + 20, b)
        c.add(num(x, y + 5, s, 14, "middle", "fg", weight=700))
    c.add(text(CX, CY - R + 34, "N", 13, "middle", "fg-muted", weight=700))
    c.add(text(CX + R - 30, CY + 5, "E", 13, "middle", "fg-muted", weight=700))
    c.add(text(CX, CY + R - 26, "S", 13, "middle", "fg-muted", weight=700))
    c.add(text(CX - R + 30, CY + 5, "W", 13, "middle", "fg-muted", weight=700))
    # clockwise sweep from north to 090
    c.add(path(barc(CX, CY, R - 40, 284, 350), "fg-faint", None, SECOND, arrow_end=True))
    x, y = bxy(CX, CY, R - 62, 312)
    c.add(text(x + 6, y + 4, "clockwise", 11, "middle", "fg-faint"))
    # the runway: 214 and 034 ends
    x1, y1 = bxy(CX, CY, R - 18, 214)
    x2, y2 = bxy(CX, CY, R - 18, 34)
    c.add(f'<g transform="rotate({214 - 90 + 0} {CX} {CY})">' + rect(CX - R + 40, CY - 5, 2 * R - 80, 10, "line-strong", None, rx=2) + "</g>")
    c.add(arrow(CX, CY, x1, y1, "brand", MAIN))
    c.add(arrow(CX, CY, x2, y2, "info", MAIN))
    c.add(circle(CX, CY, 4, "fg", None))
    lx, ly = bxy(CX, CY, R + 4, 214)
    c.add(badge(lx - 6, ly + 18, "214°M  →  runway 21", "brand"))
    lx, ly = bxy(CX, CY, R + 4, 34)
    c.add(badge(lx + 18, ly - 12, "034°M  →  runway 03", "info"))
    # rules panel
    X = 392
    c.add(panel(X, 40, 232, 330))
    c.add(text(X + 14, 66, "Three figures, always", 15, "start", "fg", weight=700))
    c.add(multiline(X + 14, 88, ["Measured clockwise from north,", "000 to 360, leading zeros kept:"], 12, "start", "fg-muted"))
    rows = [("005", "zero zero five"), ("090", "zero nine zero (east)"), ("225", "two two five (SW)"), ("360", "three six zero (north)")]
    for i, (a, b) in enumerate(rows):
        c.add(num(X + 14, 132 + i * 20, a, 13, "start", "fg", weight=700), text(X + 54, 132 + i * 20, b, 12, "start", "fg-muted"))
    c.add(text(X + 14, 222, "North is 360, not 000.", 12, "start", "fg", weight=600))
    c.add(line(X + 14, 236, X + 218, 236, "line", THIN))
    c.add(text(X + 14, 258, "Runways: two figures", 15, "start", "fg", weight=700))
    c.add(multiline(X + 14, 280, ["Magnetic direction to the nearest", "10°, last zero dropped:"], 12, "start", "fg-muted"))
    c.add(num(X + 14, 322, "214°M → 21", 13, "start", "brand", weight=700))
    c.add(num(X + 14, 342, "034°M → 03", 13, "start", "info", weight=700))
    c.add(text(X + 14, 362, "Ends always differ by 18.", 12, "start", "fg", weight=600))
    return c


@chart
def clock_code_traffic() -> Canvas:
    c = Canvas("Traffic by the clock code",
               "An aeroplane heading 090 with a clock face laid flat around it, 12 o'clock on the nose. Traffic at two o'clock is 60 degrees right "
               "of the nose and bears 150; traffic at ten o'clock is 60 degrees left and bears 030.", height=400, prefix="ccd")
    CX, CY, R, HDG = 250, 210, 140, 90
    c.add(circle(CX, CY, R, "surface-2", "line-strong", SECOND))
    for h in range(1, 13):
        b = HDG + 30 * h
        x0, y0 = bxy(CX, CY, R, b)
        x1, y1 = bxy(CX, CY, R - 10, b)
        c.add(line(x0, y0, x1, y1, "fg-muted", SECOND))
        x, y = bxy(CX, CY, R - 26, b)
        c.add(num(x, y + 5, str(h), 14 if h in (12, 3, 6, 9) else 12, "middle", "fg" if h in (12, 3, 6, 9) else "fg-muted", weight=700 if h in (12, 3, 6, 9) else None))
    c.add(plane_top(CX, CY, 0.9, HDG))
    # heading line along the nose
    c.add(line(CX + R + 4, CY, CX + R + 34, CY, "fg-muted", THIN, DASH))
    c.add(text(CX + R + 20, CY - 12, "nose", 12, "middle", "fg-muted"))
    # 2 o'clock low and 10 o'clock
    tx, ty = bxy(CX, CY, R + 52, 150)
    c.add(line(CX, CY, *bxy(CX, CY, R + 34, 150), "brand", MAIN, DASH, arrow_end=True))
    c.add(plane_top(tx, ty, 0.28, 300, "brand", "brand-soft"))
    c.add(path(barc(CX, CY, 70, 90, 150), "brand", None, SECOND))
    lx, ly = bxy(CX, CY, 86, 120)
    c.add(num(lx + 4, ly + 6, "60°", 12, "start", "brand", weight=700))
    c.add(multiline(tx + 22, ty - 6, ["2 o'clock, low", "bears 150"], 13, "start", "brand", weight=700))
    ux, uy = bxy(CX, CY, R + 52, 30)
    c.add(line(CX, CY, *bxy(CX, CY, R + 34, 30), "info", MAIN, DASH, arrow_end=True))
    c.add(plane_top(ux, uy, 0.28, 200, "info", "info-soft"))
    c.add(multiline(ux + 22, uy - 4, ["10 o'clock", "bears 030"], 13, "start", "info", weight=700))
    # north arrow
    c.add(arrow(36, 90, 36, 44, "fg-muted", SECOND), text(36, 106, "N", 12, "middle", "fg-muted", weight=700))
    # working panel
    X = 452
    c.add(panel(X, 124, 176, 160))
    c.add(text(X + 12, 148, "Heading 090", 14, "start", "fg", weight=700))
    c.add(text(X + 12, 166, "each hour = 30°", 12, "start", "fg-muted"))
    c.add(num(X + 12, 192, "2 h × 30° = 60° right", 12, "start", "brand"))
    c.add(num(X + 12, 210, "090 + 60 = 150", 13, "start", "brand", weight=700))
    c.add(num(X + 12, 238, "10 o'clock = 60° left", 12, "start", "info"))
    c.add(num(X + 12, 256, "090 − 60 = 030", 13, "start", "info", weight=700))
    c.add(text(X + 12, 276, "12 is the nose, not the track", 11, "start", "fg-muted"))
    return c


@chart
def true_magnetic_compass() -> Canvas:
    c = Canvas("From true to magnetic to compass",
               "Three norths: true north along the meridian, magnetic north offset by the variation, and compass north offset again by the deviation. "
               "Worked example: track 120 degrees true, variation 3 degrees east gives 117 magnetic, deviation 2 degrees west gives 119 compass. "
               "Angles are exaggerated.", height=400, prefix="tmc")
    OX, OY = 150, 262
    L = 200
    VAR, DEV = 15, -10  # exaggerated: 3°E drawn as 15°, 2°W as 10°
    c.add(text(20, 30, "Same direction, three references", 16, "start", "fg", weight=700))
    c.add(arrow(OX, OY, *bxy(OX, OY, L, 0), "fg", MAIN))
    tx, ty = bxy(OX, OY, L, 0)
    c.add(text(tx, ty - 10, "True N", 13, "middle", "fg", weight=700))
    c.add(arrow(OX, OY, *bxy(OX, OY, L - 6, VAR), "info", MAIN))
    mx, my = bxy(OX, OY, L - 6, VAR)
    c.add(text(mx + 8, my + 4, "Magnetic N", 13, "start", "info", weight=700))
    c.add(arrow(OX, OY, *bxy(OX, OY, L - 46, VAR + DEV), "warn", MAIN, dash="6 4"))
    cx_, cy_ = bxy(OX, OY, L - 46, VAR + DEV)
    c.add(callout(cx_, cy_ + 4, 104, cy_ + 30, "Compass N", "warn", 13, dot=False))
    c.add(path(barc(OX, OY, 170, 0, VAR), "info", None, SECOND))
    vx, vy = bxy(OX, OY, 170, VAR)
    c.add(text(vx + 8, vy + 18, "variation 3°E", 12, "start", "info", weight=600))
    c.add(path(barc(OX, OY, 120, VAR + DEV, VAR), "warn", None, SECOND))
    dx_, dy_ = bxy(OX, OY, 120, VAR)
    c.add(text(dx_ + 8, dy_ + 8, "deviation 2°W", 12, "start", "warn", weight=600))
    ex, ey = bxy(OX, OY, 130, 120)
    c.add(arrow(OX, OY, ex, ey, "brand", 2.5))
    c.add(text(ex - 30, ey + 28, "track on the chart", 13, "middle", "brand", weight=700))
    c.add(circle(OX, OY, 4, "fg", None))
    c.add(path(barc(OX, OY, 52, 0, 120), "brand", None, SECOND))
    ax, ay = bxy(OX, OY, 60, 60)
    c.add(num(ax + 6, ay, "120°T", 13, "start", "brand", weight=700))
    X, W = 350, 274
    steps = [("120°T", "true: measured on the chart", "fg"), ("117°M", "magnetic", "info"), ("119°C", "compass: what you steer", "warn")]
    ys = [80, 200, 320]
    for (val, sub, colour), y in zip(steps, ys):
        c.add(rect(X, y - 26, W, 48, f"{colour}-soft" if colour != "fg" else "surface-2", None, rx=10))
        c.add(num(X + 16, y + 6, val, 20, "start", f"{colour}-fg" if colour != "fg" else "fg", weight=700))
        c.add(text(X + 100, y + 4, sub, 12, "start", f"{colour}-fg" if colour != "fg" else "fg-muted"))
    for y0, y1, op, why, colour in ((106, 172, "− 3", "variation east: least", "info"), (226, 292, "+ 2", "deviation west: best", "warn")):
        c.add(arrow(X + 40, y0, X + 40, y1, colour, MAIN))
        c.add(num(X + 56, (y0 + y1) / 2 + 5, op, 16, "start", colour, weight=700))
        c.add(text(X + 96, (y0 + y1) / 2 + 4, why, 12, "start", colour, weight=600))
    c.add(text(20, 378, "Angles exaggerated. Variation depends on where you are; deviation on which way the aeroplane points.", 11, "start", "fg-muted"))
    return c


@chart
def heading_track_drift() -> Canvas:
    c = Canvas("Heading, track and drift",
               "Plan view. The nose points along the heading, but a wind from the left side carries the aeroplane sideways, so it moves over the "
               "ground along the track. The angle between heading and track is the drift. With no wind, heading and track are the same.",
               height=380, prefix="htd")
    X0, Y0 = 70, 120
    DRIFT = 12
    L = 520
    ex, ey = X0 + L * math.cos(math.radians(DRIFT)), Y0 + L * math.sin(math.radians(DRIFT))
    c.style(f"""
.htd-plane{{animation:htd-fly 7s linear infinite}}
@keyframes htd-fly{{0%{{transform:translate(0px,0px);opacity:0}}6%{{opacity:1}}90%{{opacity:1}}100%{{transform:translate({ex - X0 - 96:.1f}px,{(ex - X0 - 96) * math.tan(math.radians(DRIFT)):.1f}px);opacity:0}}}}
""")
    # ground grid hint
    c.add(rect(20, 70, 600, 230, "ok-soft", None, rx=12, fill_opacity=0.5))
    c.add(text(32, 290, "the ground", 11, "start", "ok-fg"))
    # heading line (where the nose points) and track line (path over the ground)
    c.add(line(X0, Y0, X0 + L, Y0, "fg-muted", SECOND, DASH, arrow_end=True))
    c.add(text(X0 + L - 4, Y0 - 12, "Heading: where the nose points", 13, "end", "fg-muted", weight=600))
    c.add(line(X0, Y0, ex, ey, "brand", 2.5, arrow_end=True))
    c.add(text(ex - 10, ey + 26, "Track: the path over the ground", 13, "end", "brand", weight=700))
    c.add(angle_mark(X0, Y0, 150, 0, DRIFT, None, "warn"))
    c.add(text(X0 + 166, Y0 + 22, "drift angle", 13, "start", "warn", weight=700))
    # aeroplane: points along the heading, moves along the track (crabbing)
    t = math.tan(math.radians(DRIFT))
    for gx in (310, 460):
        c.add(plane_top(gx, Y0 + (gx - X0) * t, 0.55, 90, "fg-muted", "surface", cls=None).replace("<g ", '<g opacity="0.6" ', 1))
    c.add(group(plane_top(X0 + 56, Y0 + 56 * t, 0.55, 90), cls="htd-plane"))    # tail (local x -51) clear of the line ends
    # wind arrows, blowing from the left side of the aeroplane (from the north) towards the south
    for x in (250, 360, 470):
        c.add(arrow(x, 34, x, 76, "sky-fg", MAIN))
    c.add(text(498, 54, "wind", 13, "start", "sky-fg", weight=700))
    c.add(arrow(600, 56, 600, 24, "fg-muted", SECOND), text(586, 50, "N", 12, "middle", "fg-muted", weight=700))
    c.add(multiline(30, 326, ["The nose always points along the heading, but the wind carries the whole aeroplane sideways,",
                              "so it travels over the ground along the track. Drift is the angle between them.",
                              "No wind: heading and track are the same."], 12, "start", "fg-muted", leading=1.4))
    return c


# ================================================================ BAKC 2.2 distance, speed and velocity
@chart
def airspeed_chain_ictg() -> Canvas:
    c = Canvas("From indicated airspeed to groundspeed",
               "Four speeds in order: indicated airspeed is corrected for instrument and position error to calibrated airspeed, for air density to "
               "true airspeed, and for wind to groundspeed. Example: at 8000 ft an IAS of 100 kt is about 116 kt TAS; TAS 105 kt into a 20 kt headwind "
               "gives 85 kt groundspeed.", height=346, prefix="ict")
    boxes = [("IAS", "indicated", "what the ASI shows"), ("CAS", "calibrated", "IAS + POH correction"), ("TAS", "true", "speed through the air"), ("GS", "ground", "speed over the ground")]
    W, G, Y = 124, 36, 84
    xs = [26 + i * (W + G) for i in range(4)]
    for i, ((ab, name, sub), x) in enumerate(zip(boxes, xs)):
        colour = "brand" if i == 0 else "surface-2"
        c.add(rect(x, Y, W, 92, "brand-soft" if i == 0 else "surface-2", "brand" if i == 0 else None, SECOND, rx=12))
        c.add(text(x + W / 2, Y + 36, ab, 26, "middle", "brand-fg" if i == 0 else "fg", weight=700))
        c.add(text(x + W / 2, Y + 58, name, 12, "middle", "brand-fg" if i == 0 else "fg", weight=600))
        c.add(text(x + W / 2, Y + 78, sub, 11, "middle", "brand-fg" if i == 0 else "fg-muted"))
    steps = [("instrument +", "position error"), ("density:", "height, temp"), ("wind", "")]
    for i, (a, b) in enumerate(steps):
        x0 = xs[i] + W + 4
        c.add(arrow(x0, Y + 46, x0 + G - 8, Y + 46, "fg", MAIN))
        c.add(text(x0 + G / 2 - 2, Y - 22, a, 11, "middle", "fg-muted"))
        if b:
            c.add(text(x0 + G / 2 - 2, Y - 8, b, 11, "middle", "fg-muted"))
    c.add(text(20, 34, "Always in this order: I · C · T · G", 15, "start", "fg", weight=700))
    # examples underneath
    c.add(rect(20, 206, 292, 112, "surface", "line", THIN, rx=10))
    c.add(text(34, 230, "Thinner air: TAS > IAS", 13, "start", "fg", weight=700))
    c.add(text(34, 250, "about 2% per 1000 ft of altitude", 12, "start", "fg-muted"))
    c.add(num(34, 276, "8000 ft: IAS 100 kt", 13, "start", "fg"))
    c.add(num(34, 296, "≈ TAS 116 kt", 13, "start", "brand", weight=700))
    c.add(rect(328, 206, 292, 112, "surface", "line", THIN, rx=10))
    c.add(text(342, 230, "Wind: GS ≠ TAS", 13, "start", "fg", weight=700))
    c.add(text(342, 250, "headwind subtracts, tailwind adds", 12, "start", "fg-muted"))
    c.add(num(342, 276, "TAS 105 kt, 20 kt headwind", 13, "start", "fg"))
    c.add(num(342, 296, "GS = 105 − 20 = 85 kt", 13, "start", "brand", weight=700))
    c.add(text(320, 338, "The aeroplane flies (stalls, rotates, has its limits) on IAS; navigation and fuel use TAS and GS.", 11, "middle", "fg-muted"))
    return c


@chart
def groundspeed_headwind_tailwind() -> Canvas:
    c = Canvas("Headwind and tailwind change groundspeed",
               "Two bars to scale. TAS 105 knots into a 20 knot headwind gives a groundspeed of 85 knots. The same TAS with a 20 knot tailwind gives 125 knots.",
               height=330, prefix="ght")
    X0, K = 150, 2.8   # px per knot

    def bar_row(y: float, title: str, wind: int, colour: str) -> None:
        gs = 105 + wind
        c.add(text(20, y + 6, title, 14, "start", colour, weight=700))
        c.add(plane_side(X0 - 36, y + 52, 0.5))
        # TAS bar
        c.add(rect(X0, y - 10, 105 * K, 22, "info-soft", "info", THIN, rx=4))
        c.add(num(X0 + 10, y + 6, "TAS 105 kt", 12, "start", "info-fg", weight=600))
        # wind bar
        if wind < 0:
            c.add(rect(X0 + (105 + wind) * K, y + 18, -wind * K, 18, "bad-soft", "bad", THIN, rx=4))
            c.add(arrow(X0 + 105 * K + 40, y + 27, X0 + 105 * K + 4, y + 27, "bad", MAIN))
            c.add(num(X0 + 105 * K + 46, y + 32, "20 kt headwind", 12, "start", "bad", weight=600))
        else:
            c.add(rect(X0 + 105 * K, y + 18, wind * K, 18, "ok-soft", "ok", THIN, rx=4))
            c.add(arrow(X0 + 105 * K + 4, y + 27, X0 + 125 * K - 2, y + 27, "ok", MAIN))
            c.add(num(X0 + 125 * K + 8, y + 32, "20 kt tailwind", 12, "start", "ok", weight=600))
        # GS bar
        c.add(rect(X0, y + 42, gs * K, 22, "brand", None, rx=4))
        c.add(num(X0 + 10, y + 58, f"GS {gs} kt", 13, "start", "surface", weight=700))
        c.add(line(X0 + gs * K, y - 14, X0 + gs * K, y + 70, "fg-muted", THIN, DASH))

    bar_row(48, "Headwind", -20, "bad")
    bar_row(180, "Tailwind", 20, "ok")
    c.add(num(X0 + 85 * K + 16, 48 + 58, "105 − 20 = 85", 14, "start", "bad", weight=700))
    c.add(num(X0 + 125 * K, 180 + 92, "105 + 20 = 125", 14, "end", "ok", weight=700))
    c.add(text(320, 318, "Same aeroplane, same TAS: only the groundspeed (and the time to get there) changes.", 12, "middle", "fg-muted"))
    return c


@chart
def wind_velocity_from() -> Canvas:
    c = Canvas("Wind velocity is named for where it comes from",
               "A wind of 270/15 blows from the west at 15 knots, towards the east. It is a headwind for an aeroplane flying west and a tailwind "
               "for one flying east.", height=360, prefix="wvf")
    CX, CY, R = 170, 180, 110
    c.add(compass_card(CX, CY, R))
    for b, s in ((0, "360"), (90, "090"), (180, "180"), (270, "270")):
        x, y = bxy(CX, CY, R + 18, b)
        c.add(num(x, y + 5, s, 12, "middle", "fg-muted"))
    # wind from 270 blowing east
    c.add(arrow(CX - R + 20, CY + 18, CX + R - 20, CY + 18, "sky-fg", 3))
    c.add(arrow(CX - R + 20, CY + 42, CX + R - 20, CY + 42, "sky-fg", 3))
    c.add(rect(CX - 70, CY - 58, 140, 34, "surface", None, rx=6))
    c.add(num(CX, CY - 36, "270/15", 22, "middle", "brand", weight=700))
    c.add(text(CX, CY + 72, "from the west, blowing east", 12, "middle", "sky-fg", weight=600))
    c.add(text(20, 30, "W/V = direction FROM / speed", 15, "start", "fg", weight=700))
    # aircraft cases
    X = 340
    c.add(panel(X, 60, 280, 100))
    # the plane spans local x -71..29, so put the CG 15 px nose-side of the slot centre X + 220
    c.add(plane_side(X + 205, 110, 0.7).replace('transform="translate(', 'transform="scale(-1 1) translate(-', 1))
    c.add(text(X + 14, 88, "Flying west (270)", 14, "start", "fg", weight=700))
    c.add(text(X + 14, 108, "15 kt headwind", 13, "start", "bad", weight=700))
    c.add(text(X + 14, 128, "GS = TAS − 15", 12, "start", "fg-muted", cls="num"))
    c.add(panel(X, 180, 280, 100))
    c.add(plane_side(X + 235, 230, 0.7))
    c.add(text(X + 14, 208, "Flying east (090)", 14, "start", "fg", weight=700))
    c.add(text(X + 14, 228, "15 kt tailwind", 13, "start", "ok", weight=700))
    c.add(text(X + 14, 248, "GS = TAS + 15", 12, "start", "fg-muted", cls="num"))
    c.add(text(320, 348, "Forecast and METAR winds are true; ATC and ATIS surface winds are magnetic.", 12, "middle", "fg-muted"))
    return c


# ================================================================ BAKC 2.3 time
@chart
def utc_and_wst_strip() -> Canvas:
    c = Canvas("UTC and Western Standard Time side by side",
               "Two time strips aligned so the same instant sits in the same column. WST is UTC plus 8 hours, so the WST date changes at 1600 UTC. "
               "Worked examples: 1530 WST is 0730 UTC the same day; 0545 WST on Tuesday 7 October is 2145 UTC on Monday 6 October.",
               height=400, prefix="uws")
    X0, PX = 40, 24   # px per hour; the strip covers the 24 hours of Monday 6 October UTC
    YU, YW, H = 80, 236, 34

    def x(h: float) -> float:
        return X0 + h * PX

    c.add(text(20, 30, "Same moment, two clocks: WST = UTC + 8", 16, "start", "fg", weight=700))
    c.add(text(X0, YU - 10, "UTC  ·  Monday 6 October", 13, "start", "info", weight=700))
    c.add(rect(x(0), YU, 24 * PX, H, "info-soft", "info", THIN, rx=4))
    c.add(rect(x(0), YW, 16 * PX, H, "brand-soft", "brand", THIN, rx=4))
    c.add(rect(x(16), YW, 8 * PX, H, "warn-soft", "warn", THIN, rx=4))
    c.add(text(X0, YW + H + 44, "WST  ·  Monday 6 October", 13, "start", "brand", weight=700))
    c.add(text(x(24), YW + H + 44, "Tuesday 7 October", 13, "end", "warn", weight=700))
    for h in range(0, 25, 2):
        c.add(line(x(h), YU + H, x(h), YU + H + 6, "info", THIN))
        c.add(num(x(h), YU + H + 18, f"{h % 24:02d}00" if h < 24 else "2400", 11, "middle", "info-fg"))
        w = (h + 8) % 24
        c.add(line(x(h), YW + H, x(h), YW + H + 6, "brand" if h < 16 else "warn", THIN))
        c.add(num(x(h), YW + H + 18, f"{w:02d}00", 11, "middle", "brand-fg" if h < 16 else "warn-fg"))
    c.add(line(x(16), YU + H + 26, x(16), YW + H, "warn", MAIN, dash="6 4"))
    c.add(multiline(x(16) - 8, YU + H + 48, ["WST midnight", "= 1600 UTC"], 12, "end", "warn", weight=600))
    for hu, colour, l1, l2, w in ((7.5, "fg", "1530 WST", "→ 0730 UTC", 104), (21.75, "bad", "0545 WST Tue", "→ 2145 UTC Mon", 132)):
        xe = x(hu)
        bx = min(xe - w / 2, x(24) - w)
        c.add(line(xe, YU + 4, xe, YW + H - 4, colour, MAIN, arrow_start=True))
        c.add(circle(xe, YW + H / 2, 5, colour, "surface", 1.5))
        c.add(rect(bx, YU + H + 38, w, 50, "surface", colour if colour != "fg" else "line", THIN, rx=6))
        c.add(num(bx + w / 2, YU + H + 58, l1, 12, "middle", colour, weight=700))
        c.add(num(bx + w / 2, YU + H + 76, l2, 12, "middle", colour, weight=700))
    c.add(multiline(20, 340, ["WST to UTC: subtract 8. Below 0000? Add 24 and go back a day.",
                              "UTC to WST: add 8. 2400 or more? Subtract 24 and go forward a day.",
                              "Trap: any WST time before 0800 is the previous day in UTC."], 12, "start", "fg-muted", leading=1.45))
    return c


@chart
def twenty_four_hour_clock() -> Canvas:
    c = Canvas("The 24-hour clock as a 4-figure group",
               "A 24-hour dial with 0000 at the top and 1200 at the bottom. Morning times keep their hour with a leading zero (7:05 am is 0705); "
               "afternoon times add 12 to the hour (3:45 pm is 1545). 12:20 am is 0020 and 11:59 pm is 2359.", height=380, prefix="tfh")
    CX, CY, R = 186, 196, 140
    c.add(path(barc(CX, CY, R - 14, 4, 176), "warn-soft", None, 18))
    c.add(path(barc(CX, CY, R - 14, 184, 356), "info-soft", None, 18))
    c.add(circle(CX, CY, R, None, "fg", SECOND))
    c.add(circle(CX, CY, R - 28, "surface", "line", THIN))
    for h in range(24):
        b = h * 15
        x0, y0 = bxy(CX, CY, R - 28, b)
        x1, y1 = bxy(CX, CY, R - 36, b)
        c.add(line(x0, y0, x1, y1, "fg-muted", THIN))
        if h % 3 == 0:
            x, y = bxy(CX, CY, R - 50, b)
            c.add(num(x, y + 4, f"{h:02d}", 12, "middle", "fg", weight=700))
    ax, ay = bxy(CX, CY, 66, 50)
    c.add(text(ax, ay + 5, "am", 15, "middle", "warn-fg", weight=700))
    ax, ay = bxy(CX, CY, 66, 310)
    c.add(text(ax, ay + 5, "pm", 15, "middle", "info-fg", weight=700))
    # the examples
    ex = [(0, 20, "0020"), (7, 5, "0705"), (12, 0, "1200"), (15, 45, "1545"), (23, 59, "2359")]
    for h, m, s in ex:
        b = (h + m / 60) * 15
        x, y = bxy(CX, CY, R - 14, b)
        c.add(circle(x, y, 5, "brand", "surface", 1.5))
        lx, ly = bxy(CX, CY, R + 14, b + (6 if s == "0020" else -6 if s == "2359" else 0))
        anchor = "start" if 0 < b % 360 < 180 or s == "0020" else "middle" if s == "1200" else "end"
        c.add(num(lx, ly + (14 if s == "1200" else 4), s, 12, anchor, "brand", weight=700))
    hx, hy = bxy(CX, CY, R - 62, (15 + 45 / 60) * 15)
    c.add(line(CX, CY, hx, hy, "brand", 3))
    c.add(circle(CX, CY, 5, "brand", None))
    # table
    X = 370
    c.add(panel(X, 40, 254, 270))
    c.add(text(X + 14, 66, "12-hour", 13, "start", "fg-muted", weight=600))
    c.add(text(X + 140, 66, "4-figure", 13, "start", "fg-muted", weight=600))
    rows = [("12:20 am", "0020"), ("7:05 am", "0705"), ("12:00 noon", "1200"), ("3:45 pm", "1545"), ("11:59 pm", "2359")]
    for i, (a, b) in enumerate(rows):
        y = 98 + i * 32
        c.add(num(X + 14, y, a, 14, "start", "fg"))
        c.add(num(X + 140, y, b, 16, "start", "brand" if b == "1545" else "fg", weight=700))
    c.add(line(X + 14, 256, X + 240, 256, "line", THIN))
    c.add(multiline(X + 14, 276, ["pm from 1 pm: add 12 to the hour.", "Always four figures, no colon."], 12, "start", "fg-muted"))
    return c


# ================================================================ BAKC 2.4 units of measurement
def dim_line(x: float, y0: float, y1: float, colour: str, label: list[str], side: str = "right", size: float = 13) -> str:
    """Vertical dimension line with end ticks and a label beside its middle."""
    out = line(x, y0, x, y1, colour, MAIN)
    out += line(x - 7, y0, x + 7, y0, colour, MAIN) + line(x - 7, y1, x + 7, y1, colour, MAIN)
    tx = x + 10 if side == "right" else x - 10
    out += multiline(tx, (y0 + y1) / 2 - (len(label) - 1) * size * 0.65 + 4, label, size, "start" if side == "right" else "end", colour, weight=600)
    return out


@chart
def height_altitude_elevation() -> Canvas:
    c = Canvas("Height, altitude and elevation",
               "Side view, vertical scale exaggerated. An aerodrome has an elevation of 300 ft above mean sea level. An aeroplane in its circuit with "
               "QNH set reads an altitude of 1300 ft, so its height above the aerodrome is 1000 ft. At the same altitude over a 900 ft ridge it is only "
               "400 ft above the ground.", height=400, prefix="hae")
    S, MSL = 0.2, 352   # px per ft, sea-level y

    def y(ft: float) -> float:
        return MSL - ft * S

    # sea and terrain
    c.add(rect(20, MSL, 600, 30, "sky-soft", None))
    c.add(text(32, MSL + 20, "mean sea level (MSL)", 12, "start", "sky-fg", weight=600))
    terrain = [(20, y(0)), (60, y(0)), (85, y(150)), (110, y(290)), (140, y(300)), (300, y(300)), (360, y(500)), (430, y(820)), (470, y(900)), (510, y(860)), (570, y(500)), (620, y(420))]
    c.add(path(smooth_path(terrain) + f" L620 {MSL} L20 {MSL} Z", "fg-muted", "surface-2", SECOND))
    c.add(rect(150, y(300) - 4, 120, 6, "fg-muted", None, rx=1))
    c.add(text(210, y(300) + 22, "aerodrome", 12, "middle", "fg-muted", weight=600))
    # aeroplanes at 1300 ft
    c.add(plane_side(208, y(1300), 0.7))
    c.add(plane_side(468, y(1300), 0.7, "fg-muted"))
    c.add(line(80, y(1300), 600, y(1300), "line-strong", THIN, DASH))
    c.add(text(600, y(1300) + 18, "same altitude", 12, "end", "fg-muted"))
    # dimensions
    c.add(dim_line(50, y(0), y(1300), "brand", ["Altitude", "1300 ft AMSL", "(QNH set)"], "right"))
    c.add(dim_line(300, y(0), y(300), "fg", ["Elevation", "300 ft"], "right", 12))
    c.add(dim_line(240, y(300), y(1300), "info", ["Height", "1000 ft AGL"], "right"))
    c.add(dim_line(500, y(900), y(1300), "bad", ["only 400 ft", "above the ridge"], "right", 12))
    c.add(num(470, y(900) + 22, "ridge 900 ft", 12, "middle", "fg-muted", weight=600))
    # formula
    c.add(rect(330, 12, 290, 52, "brand-soft", None, rx=8))
    c.add(text(344, 34, "Altitude = elevation + height", 14, "start", "brand-fg", weight=700))
    c.add(num(344, 54, "1300 = 300 + 1000", 13, "start", "brand-fg"))
    return c


@chart
def units_conversion_ladder() -> Canvas:
    c = Canvas("Conversions you will use",
               "Three paired scales. Distance: 1 nautical mile is 1.852 km, 1 km is 0.54 NM, 1 statute mile is 0.87 NM. Speed: 110 kt is 204 km/h and "
               "60 km/h is 32 kt. Fuel: avgas weighs about 0.72 kg per litre, so 100 L is about 72 kg and 120 L is 86.4 kg.",
               height=440, prefix="ucl")
    L, R = 130, 600

    def scale(y: float, top_unit: str, bot_unit: str, top_max: float, factor: float, top_ticks: list[float], bot_ticks: list[float],
              marks: list[tuple[float, str, str]], colour: str) -> None:
        k = (R - L) / top_max
        c.add(line(L, y, R, y, "fg", MAIN, cap="butt"))
        c.add(text(L - 12, y - 6, top_unit, 13, "end", "fg", weight=700))
        c.add(text(L - 12, y + 16, bot_unit, 13, "end", "fg-muted", weight=700))
        clear = lambda xx: all(abs(xx - (L + v * k)) > 16 for v, _, _ in marks)
        for t in top_ticks:
            c.add(line(L + t * k, y - 6, L + t * k, y, "fg", SECOND))
            if clear(L + t * k):
                c.add(num(L + t * k, y - 10, fmt(t), 11, "middle", "fg-muted"))
        for t in bot_ticks:
            xb = L + t / factor * k
            c.add(line(xb, y, xb, y + 6, "fg-muted", SECOND))
            if clear(xb):
                c.add(num(xb, y + 18, fmt(t), 11, "middle", "fg-faint"))
        for v, top_label, bot_label in marks:
            xm = L + v * k
            c.add(line(xm, y - 26, xm, y + 26, colour, MAIN))
            c.add(circle(xm, y, 5, colour, "surface", 1.5))
            c.add(num(xm, y - 32, top_label, 13, "middle", colour, weight=700))
            c.add(num(xm, y + 42, bot_label, 13, "middle", colour, weight=700))

    c.add(text(20, 30, "Read across: the same quantity in two units", 15, "start", "fg", weight=700))
    # distance: bars to scale for 1 NM, 1 SM and 1 km
    y = 82
    c.add(text(20, y, "Distance", 14, "start", "brand", weight=700))
    K = 240  # px per NM
    for i, (lab, nm, colour, note) in enumerate((("1 NM", 1.0, "brand", "= 1852 m = 1.852 km"), ("1 statute mile", 0.87, "fg-muted", "= 0.87 NM"), ("1 km", 0.54, "fg-muted", "= 0.54 NM"))):
        yy = y + 16 + i * 26
        c.add(rect(L, yy, nm * K, 16, "brand-soft" if colour == "brand" else "surface-2", colour, THIN, rx=3))
        c.add(text(L - 12, yy + 13, lab, 12, "end", "fg", weight=600))
        c.add(num(L + nm * K + 10, yy + 13, note, 12, "start", colour if colour == "brand" else "fg-muted", weight=600 if colour == "brand" else None))
    # speed
    c.add(text(20, 210, "Speed", 14, "start", "info", weight=700))
    scale(250, "kt", "km/h", 140, 1.852, [0, 20, 40, 60, 80, 100, 120, 140], [0, 50, 100, 150, 200, 250], [(110, "110 kt", "204 km/h"), (60 / 1.852, "32 kt", "60 km/h")], "info")
    # fuel
    c.add(text(20, 326, "Avgas", 14, "start", "warn", weight=700))
    scale(370, "litres", "kg", 140, 0.72, [0, 20, 40, 60, 80, 100, 120, 140], [0, 20, 40, 60, 80, 100], [(100, "100 L", "≈ 72 kg"), (120, "120 L", "86.4 kg")], "warn")
    c.add(text(R, 432, "kg = L × 0.72 (avgas; check your flight manual's figure)", 11, "end", "fg-muted"))
    return c


# ================================================================ BAKC 2.5 basic physics (energy)
@chart
def kinetic_energy_speed_squared() -> Canvas:
    c = Canvas("Kinetic energy grows with the square of speed",
               "Kinetic energy relative to a reference speed, plotted against speed as a multiple of that reference. 10 percent faster carries 21 percent "
               "more energy (1.1 squared is 1.21); double the speed carries four times the energy.", height=380, prefix="kes")
    ch = Chart(c, (0, 2.2), (0, 4.6), box=(70, 40, 600, 320), xlabel="Speed  (× reference speed)", ylabel="Kinetic energy  (× reference)",
               xticks=[0, 0.5, 1, 1.5, 2], yticks=[0, 1, 2, 3, 4], xfmt=lambda v: f"×{fmt(v)}", yfmt=lambda v: f"×{fmt(v)}")
    c.add(ch.axes())
    c.add(ch.area(sample(lambda v: v * v, 0, 2.12, 60), "brand", 0.08))
    c.add(ch.curve(sample(lambda v: v * v, 0, 2.12, 60), "brand", MAIN, label="KE = ½ m v²", label_at=42, label_dx=-12, label_dy=-12, label_anchor="end"))
    c.add(ch.curve([(0, 0), (2.1, 2.1)], "fg-faint", THIN, dash=DASH, smooth=False, label="if it were linear", label_dx=-40, label_dy=46, label_anchor="end"))
    c.add(ch.guide(1, 1, "fg-faint"))
    c.add(ch.point(1, 1, "fg", 4.5))
    c.add(ch.guide(1.1, 1.21, "warn"))
    c.add(ch.point(1.1, 1.21, "warn", 5))
    x, y = ch.pt(1.1, 1.21)
    c.add(callout(x, y, x + 46, y + 30, ["Touchdown 10% fast:", "1.1² = 1.21, 21% more", "energy for the brakes"], "warn", 13))
    c.add(ch.guide(2, 4, "bad"))
    c.add(ch.point(2, 4, "bad", 5))
    x, y = ch.pt(2, 4)
    c.add(callout(x, y, x - 120, y - 34, ["Double the speed:", "four times the energy"], "bad", 13))
    return c


@chart
def energy_trade_zoom() -> Canvas:
    c = Canvas("Trading speed for height in a zoom",
               "An aeroplane at 100 knots raises the nose without adding power and zooms to 60 knots. Ignoring drag, the kinetic energy it loses "
               "becomes potential energy: about 280 ft of height. The energy bars show the total staying the same while the share changes.",
               height=394, prefix="etz")
    p0, p1 = (90, 220), (400, 96)
    c.add(path(f"M{p0[0] + 26} {p0[1]} C230 220 280 100 {p1[0] - 10} {p1[1]}", "fg-faint", None, SECOND, dash="6 5", arrow_end=True))
    c.add(plane_side(p0[0], p0[1], 0.7))    # nose at local x 29, tail at -71: labels sit under the middle, 15 px aft of the CG
    c.add(plane_side(p1[0] + 50, p1[1], 0.7, pitch=0))
    c.add(num(p0[0] - 15, p0[1] + 34, "100 kt", 14, "middle", "fg", weight=700))
    c.add(num(p1[0] + 35, p1[1] - 28, "60 kt", 14, "middle", "fg", weight=700))
    # height gained
    c.add(line(p1[0] + 110, p0[1], p1[0] + 110, p1[1], "brand", MAIN, arrow_end=True))
    c.add(line(p0[0] + 28, p0[1], p1[0] + 118, p0[1], "line-strong", THIN, DASH))
    c.add(multiline(p1[0] + 122, (p0[1] + p1[1]) / 2 - 4, ["≈ 280 ft", "gained"], 15, "start", "brand", weight=700))
    c.add(text(p1[0] + 122, (p0[1] + p1[1]) / 2 + 36, "(ignoring drag)", 11, "start", "fg-muted"))

    # energy bars: KE ∝ v², total constant
    def bars(x: float, ke: float, pe: float, title: str) -> None:
        H = 70
        base = 372
        c.add(rect(x, base - ke * H, 34, ke * H, "info-soft", "info", THIN))
        if pe:
            c.add(rect(x, base - (ke + pe) * H, 34, pe * H, "brand-soft", "brand", THIN))
        c.add(text(x + 42, base - ke * H / 2 + 4, "KE", 12, "start", "info", weight=700))
        if pe:
            c.add(text(x + 42, base - ke * H - pe * H / 2 + 4, "PE gained", 12, "start", "brand", weight=700))
        c.add(text(x + 17, base + 14, title, 11, "middle", "fg-muted"))
    c.add(text(20, 30, "Elevator alone shares the energy; only the throttle adds it", 15, "start", "fg", weight=700))
    bars(30, 1.0, 0, "before")
    bars(150, 0.36, 0.64, "after")
    c.add(line(26, 302, 146, 302, "fg-faint", THIN, DASH))
    c.add(text(86, 296, "same total", 11, "middle", "fg-faint"))
    c.add(multiline(300, 336, ["height = (v₁² − v₂²) ÷ 2g", "= (51.4² − 30.9²) ÷ 19.6 ≈ 86 m ≈ 280 ft"], 12, "start", "fg-muted", cls="num"))
    return c


# ================================================================ BAKC 3.1 piston engine
@chart
def power_loss_with_altitude() -> Canvas:
    c = Canvas("Full-throttle power falls with altitude",
               "Power available at full throttle from a normally aspirated engine, as a percentage of sea-level power, against altitude. It falls by roughly "
               "3 percent per 1000 ft, so by about 7000 to 8000 ft a typical trainer can only produce about 75 percent power.", height=394, prefix="pla")
    ch = Chart(c, (0, 10000), (50, 105), box=(76, 40, 600, 310), xlabel="Altitude (ft)", ylabel="Full-throttle power (% of sea level)",
               xticks=[0, 2000, 4000, 6000, 8000, 10000], yticks=[50, 60, 70, 80, 90, 100], xfmt=lambda v: f"{int(v):,}", yfmt=lambda v: f"{int(v)}%")
    c.add(ch.band(7000, 8000, "warn", 0.15))
    c.add(ch.axes())
    pts = [(0, 100), (10000, 70)]
    c.add(ch.curve(pts, "brand", 2.5, smooth=False, label="≈ 3% less per 1,000 ft", label_at=0, label_dx=40, label_dy=-22))
    c.add(ch.hline(75, "warn", DASH, None, x_to=8000))
    c.add(ch.point(7500, 77.5, "warn", 5))
    x, y = ch.pt(7500, 77.5)
    c.add(callout(x, y, x - 120, y + 70, ["7,000 to 8,000 ft:", "only about 75% power", "at full throttle"], "warn", 13))
    c.add(text(ch.px(7500), ch.py(103), "7–8,000 ft", 11, "middle", "warn-fg"))
    c.add(text(320, 384, "Thinner air puts less mass in each cylinder, so less power; a hot day costs more.", 12, "middle", "fg-muted"))
    return c


@chart
def mixture_rich_to_lean() -> Canvas:
    c = Canvas("Mixture: too rich, about right, too lean",
               "Qualitative sketch of engine power and exhaust gas temperature as the mixture is leaned from full rich. Power peaks near the correct "
               "mixture and falls on both sides. Too rich: rough running, power loss, high fuel burn, cool running, plug fouling, black smoke. "
               "Too lean: power loss, rough running, high CHT and EGT, risk of detonation.", height=400, prefix="mrl")
    ch = Chart(c, (0, 10), (0, 10), box=(60, 60, 600, 300), xlabel="", ylabel="", xticks=[], yticks=[], grid=False)
    c.add(rect(ch.px(0), ch.top, ch.px(2.8) - ch.px(0), ch.bottom - ch.top, "warn-soft", None, fill_opacity=0.6))
    c.add(rect(ch.px(7.4), ch.top, ch.px(10) - ch.px(7.4), ch.bottom - ch.top, "bad-soft", None, fill_opacity=0.6))
    c.add(rect(ch.px(4.0), ch.top, ch.px(6.4) - ch.px(4.0), ch.bottom - ch.top, "ok-soft", None, fill_opacity=0.6))
    c.add(ch.axes())
    power = lambda m: 7.6 - 0.11 * (m - 5.0) ** 2 if m < 5 else 7.6 - 0.32 * (m - 5.0) ** 2
    egt = lambda m: 2.0 + 6.4 / (1 + math.exp(-(m - 5.6) / 1.2))
    c.add(ch.curve(sample(power, 0.3, 9.6, 60), "brand", 2.5, label="Power", label_at=30, label_dx=-6, label_dy=-14, label_anchor="middle"))
    c.add(ch.curve(sample(egt, 0.3, 9.6, 60), "info", MAIN, dash="7 4", label="EGT (and CHT)", label_at=60, label_dx=-4, label_dy=42, label_anchor="end"))
    c.add(text(ch.px(1.4), ch.top + 22, "Too rich", 14, "middle", "warn-fg", weight=700))
    c.add(text(ch.px(5.2), ch.top + 22, "About right", 14, "middle", "ok-fg", weight=700))
    c.add(text(ch.px(8.7), ch.top + 22, "Too lean", 14, "middle", "bad-fg", weight=700))
    c.add(text(ch.px(5), ch.bottom + 18, "fuel/air mixture", 12, "middle", "fg-muted", weight=600))
    c.add(text(ch.px(0), ch.bottom + 18, "← richer (full rich)", 12, "start", "fg-muted"))
    c.add(text(ch.px(10), ch.bottom + 18, "leaner →", 12, "end", "fg-muted"))
    c.add(text(ch.left - 10, (ch.top + ch.bottom) / 2, "relative value", 12, "middle", "fg-muted", rotate=-90))
    c.add(multiline(20, 344, ["rough, power loss, high fuel burn,", "cool running, plug fouling, black smoke"], 11, "start", "warn-fg"))
    c.add(multiline(620, 344, ["power loss, rough running, high CHT", "and EGT, risk of detonation"], 11, "end", "bad-fg"))
    c.add(text(320, 390, "Climbing makes the mixture richer: lean by EGT, or lean until rough then enrich slightly (POH).", 11, "middle", "fg-muted"))
    return c


# ================================================================ BAKC 3.2 fuels and oils
def tube(x: float, y: float, h: float, fill: str, stroke: str = "fg", level: float = 0.8, water: float = 0.0, w: float = 46) -> str:
    """A clear fuel tester seen from the side: (x, y) top-left, liquid filled to `level`, an optional water layer at the bottom."""
    r = w / 2
    body = f"M{x} {y} L{x} {y + h - r} A{r} {r} 0 0 0 {x + w} {y + h - r} L{x + w} {y}"
    top = y + h * (1 - level)
    out = ""
    clip_d = f"M{x} {top} L{x} {y + h - r} A{r} {r} 0 0 0 {x + w} {y + h - r} L{x + w} {top} Z"
    out += path(clip_d, None, fill, 0, fill_opacity={"brand": 0.6, "ok": 0.6, "warn": 0.3}.get(fill))
    if water:
        wt = y + h - water * h
        wd = f"M{x} {wt} L{x} {y + h - r} A{r} {r} 0 0 0 {x + w} {y + h - r} L{x + w} {wt} Z"
        out += path(wd, None, "sky-soft", 0)
        out += line(x + 2, wt, x + w - 2, wt, "sky-fg", SECOND, DASH)
        out += text(x + w / 2, wt + (y + h - wt) / 2 + 4, "water", 11, "middle", "sky-fg", weight=700)
        for dx, dy, rr in ((10, -10, 3), (24, -16, 2.5), (34, -8, 3.5), (18, -26, 2)):
            out += circle(x + dx, wt + dy, rr, "surface", "sky-fg", 1.25)
    out += path(body, stroke, None, MAIN)
    out += line(x - 4, y, x + w + 4, y, stroke, MAIN)
    return out


@chart
def fuel_sample_colours() -> Canvas:
    c = Canvas("What the fuel sample should look like",
               "Fuel testers side by side: AVGAS 100LL is blue, AVGAS 100/130 is green, Jet A-1 is clear to straw coloured. A sample with clear globules "
               "or a separate layer at the bottom contains water. A clear sample from an AVGAS aeroplane means water or jet fuel: do not fly until the cause "
               "is found.", height=400, prefix="fsc2")
    samples = [("AVGAS 100LL", "blue", "brand", "the usual fuel", 0.0, "ok"),
               ("AVGAS 100/130", "green", "ok", "higher lead", 0.0, "ok"),
               ("Jet A-1", "clear to straw", "warn", "turbine engines only", 0.0, "bad"),
               ("100LL + water", "globules at the bottom", "brand", "water: drain again", 0.28, "bad")]
    X0, GAP, Y, H = 50, 150, 70, 170
    c.add(text(20, 34, "Check the colour and smell, and look for water and sediment", 15, "start", "fg", weight=700))
    for i, (name, colour_word, fill, note, water, verdict) in enumerate(samples):
        x = X0 + i * GAP
        c.add(tube(x, Y, H, fill, "fg", 0.82, water))
        cx = x + 23
        c.add(text(cx, Y + H + 30, name, 13, "middle", "fg", weight=700))
        c.add(text(cx, Y + H + 47, colour_word, 12, "middle", "fg-muted"))
        c.add(text(cx, Y + H + 63, note, 11, "middle", "bad" if verdict == "bad" else "fg-muted", weight=600 if verdict == "bad" else None))
    c.add(rect(20, 330, 600, 56, "bad-soft", None, rx=10))
    c.add(text(34, 352, "A clear sample from an AVGAS aeroplane is water or jet fuel.", 13, "start", "bad-fg", weight=700))
    c.add(text(34, 372, "Either way, do not fly until the cause is found. Jet fuel in a piston engine can fail it just after take-off.", 11, "start", "bad-fg"))
    return c


@chart
def overnight_condensation() -> Canvas:
    c = Canvas("Why fill the tanks before overnight parking",
               "Two wing tanks overnight. A partly filled tank has a large air space; as the air cools overnight its moisture condenses on the tank walls "
               "and runs down into the fuel as water. A full tank has little air, so little water forms. The trade-off: you may be over weight for the "
               "next flight, and fuel expands and vents as the day warms.", height=360, prefix="onc")

    def tank(x: float, fuel: float, title: str, colour: str, drops: int) -> None:
        W, H, Y = 250, 120, 80
        top = Y + H * (1 - fuel)
        cid = f"onc-clip{int(x)}"
        c.add_defs(f'<clipPath id="{cid}"><rect x="{x}" y="{Y}" width="{W}" height="{H}" rx="12"/></clipPath>')
        inner = rect(x, Y, W, H, "surface", None) + rect(x, top, W, Y + H - top, "brand-soft", None) + line(x, top, x + W, top, "brand", SECOND)
        if fuel < 0.9:
            inner += rect(x, Y, W, top - Y, "sky-soft", None, fill_opacity=0.7)
        c.add(f'<g clip-path="url(#{cid})">{inner}</g>')
        if fuel < 0.9:
            c.add(text(x + W / 2, Y + (top - Y) / 2 + 4, "moist air cools overnight", 12, "middle", "sky-fg", weight=600))
        c.add(rect(x, Y, W, H, None, "fg", MAIN, rx=12))
        for k in range(drops):
            dx = x + 24 + k * 38
            c.add(path(f"M{dx} {Y + 6} q-5 9 0 13 q5 -4 0 -13 z", "sky-fg", "sky-soft", 1.25))
        # water at the bottom
        if drops:
            for k in range(drops):
                c.add(circle(x + 40 + k * 34, Y + H - 8, 3.5 if k % 2 else 4.5, "surface", "sky-fg", 1.25))
        c.add(text(x + W - 16, top + 20, "fuel", 12, "end", "brand-fg", weight=600))
        c.add(text(x + W / 2, Y - 16, title, 15, "middle", colour, weight=700))
    c.add(text(320, 30, "Overnight, as the air in the tank cools...", 14, "middle", "fg-muted", weight=600))
    tank(40, 0.35, "Partly filled", "bad", 6)
    tank(350, 0.94, "Full", "ok", 0)
    c.add(text(165, 230, "water condenses and sinks into the fuel", 12, "middle", "bad", weight=600))
    c.add(text(475, 230, "little air, so little water", 12, "middle", "ok-fg", weight=600))
    c.add(multiline(40, 268, ["Full overnight:", "+ less condensation, ready to go", "− may be over weight for tomorrow's load", "− fuel expands and vents as the day warms"], 12, "start", "fg-muted", leading=1.45))
    c.add(multiline(350, 268, ["Either way:", "let the fuel settle, then drain every", "point before flight and after refuelling"], 12, "start", "fg-muted", leading=1.45))
    return c


# ================================================================ BAKC 3.3 engine handling
def cylinder(x: float, y: float, w: float = 150, h: float = 120) -> str:
    """Cylinder cross-section with head and spark plug; (x, y) top-left of the bore. Piston crown at y + h * 0.72."""
    crown = y + h * 0.72
    out = rect(x, y, w, h, "surface", None)
    out += line(x, y - 10, x, y + h, "fg", 3) + line(x + w, y - 10, x + w, y + h, "fg", 3)
    out += path(f"M{x - 6} {y} L{x + w + 6} {y}", "fg", None, 6)
    out += rect(x + 4, crown, w - 8, h - (crown - y) + 10, "surface-2", "fg", MAIN, rx=3)
    out += line(x + 4, crown + 8, x + w - 4, crown + 8, "fg", THIN) + line(x + 4, crown + 14, x + w - 4, crown + 14, "fg", THIN)
    out += rect(x + 30, y - 26, 12, 22, "surface", "fg", 1.5, rx=2) + line(x + 36, y - 4, x + 36, y + 6, "fg", 2)
    return out


@chart
def detonation_vs_normal_combustion() -> Canvas:
    c = Canvas("Normal combustion and detonation",
               "Left: normal combustion, a smooth flame front spreading from the spark plug and a smooth rise in cylinder pressure. Right: detonation, the "
               "remaining charge explodes after the spark and hammers the piston, with a sharp pressure spike. Causes: mixture too lean at high power, high "
               "manifold pressure with low RPM, fuel of too low an octane, and high cylinder head temperature. Effects: rough running, sharp rise in CHT, "
               "power loss, damage. Remedy: enrich, reduce power, lower the nose, open cowl flaps.", height=440, prefix="dvn")
    for i, (title, colour) in enumerate((("Normal combustion", "ok"), ("Detonation", "bad"))):
        X = 20 + i * 310
        c.add(rect(X, 20, 290, 290, f"{colour}-soft", None, rx=12, fill_opacity=0.5))
        c.add(text(X + 145, 46, title, 16, "middle", f"{colour}-fg", weight=700))
        cx, cy = X + 70, 88
        c.add(cylinder(cx, cy))
        plug = (cx + 36, cy + 6)
        cid = f"dvn-bore{i}"
        c.add_defs(f'<clipPath id="{cid}"><rect x="{cx}" y="{cy}" width="150" height="{86}"/></clipPath>')
        if i == 0:
            arcs = "".join(path(arc_path(plug[0], plug[1], r, 0, 180), "warn", None, MAIN, opacity=op) for r, op in ((26, 0.9), (52, 0.65), (80, 0.4)))
            c.add(f'<g clip-path="url(#{cid})">{arcs}</g>')
            c.add(multiline(cx + 160, cy + 34, ["smooth", "flame front"], 11, "start", "warn-fg", weight=600))
            for ax in (cx + 45, cx + 105):
                c.add(arrow(ax, cy + 96, ax, cy + 118, "fg", MAIN))
        else:
            c.add(path(arc_path(plug[0], plug[1], 30, 10, 170), "warn", None, MAIN, opacity=0.9))
            bx, by = cx + 112, cy + 46
            star = [(bx + 26 * math.cos(math.radians(a)) * (1 if k % 2 == 0 else 0.45), by + 26 * math.sin(math.radians(a)) * (1 if k % 2 == 0 else 0.45))
                    for k, a in enumerate(range(0, 360, 30))]
            c.add(polygon(star, "bad-soft", "bad", MAIN))
            c.add(text(bx - 6, by - 32, "end gas explodes", 11, "middle", "bad", weight=700))
            for ax in (cx + 40, cx + 75, cx + 110):
                c.add(polyline([(ax, cy + 92), (ax - 5, cy + 100), (ax + 5, cy + 106), (ax, cy + 118)], "bad", MAIN, arrow_end=True))
        # pressure trace
        TX, TY, TW, TH = X + 30, 300, 230, 56
        c.add(line(TX, TY, TX + TW, TY, "fg-muted", SECOND))
        c.add(text(TX, TY - TH - 6 if i == 0 else TY + 16, "cylinder pressure", 11, "start", "fg-muted"))
        if i == 0:
            pts = [(TX + t, TY - TH * 0.85 * math.exp(-((t - 90) / 38) ** 2)) for t in range(0, TW + 1, 6)]
            c.add(path(smooth_path(pts), "ok", None, MAIN))
        else:
            pts = []
            for t in range(0, TW + 1, 3):
                base = TH * 0.6 * math.exp(-((t - 80) / 36) ** 2)
                spike = TH * 0.75 * math.exp(-((t - 96) / 5) ** 2) + (TH * 0.18 * math.sin((t - 96) * 0.9) * math.exp(-(t - 96) / 28) if t > 96 else 0)
                pts.append((TX + t, TY - base - spike))
            c.add(polyline(pts, "bad", MAIN))
            c.add(text(TX + 106, TY - TH - 2, "pressure spike", 11, "start", "bad", weight=600))
    # causes, effects, remedy
    cols = [("Causes", "bad", ["mixture too lean at high power", "high manifold pressure, low RPM", "fuel octane too low", "high CHT: slow, steep climb, hot day"]),
            ("Effects", "warn", ["rough running", "sharp rise in CHT", "loss of power", "burnt valves, holed pistons"]),
            ("Remedy", "ok", ["enrich the mixture", "reduce power", "lower the nose for cooling", "open the cowl flaps"])]
    for (head, colour, items), x in zip(cols, (20, 262, 452)):
        c.add(text(x, 342, head, 14, "start", f"{colour}-fg" if colour != "bad" else "bad", weight=700))
        c.add(multiline(x, 362, ["· " + it for it in items], 12, "start", "fg-muted", leading=1.45))
    return c


@chart
def magneto_check_rpm_drop() -> Canvas:
    c = Canvas("Reading the magneto check",
               "RPM on BOTH, then on the left magneto alone, then on the right alone. Each single-magneto drop must be within the POH limit, typically a "
               "maximum of about 125 to 175 RPM, and the difference between the two drops within its limit, typically about 50 RPM.", height=380, prefix="mcr")
    BASE, TOP = 300, 80
    bars = [("BOTH", 0), ("L", 70), ("R", 105)]
    xs = [110, 270, 430]
    c.add(line(60, BASE, 600, BASE, "fg-muted", SECOND))
    c.add(line(60, TOP, 600, TOP, "line-strong", THIN, DASH))
    c.add(text(64, TOP - 8, "check RPM on BOTH", 12, "start", "fg-muted"))
    for (lab, drop), x in zip(bars, xs):
        top = TOP + drop
        c.add(rect(x - 34, top, 68, BASE - top, "brand-soft" if lab != "BOTH" else "surface-2", "brand" if lab != "BOTH" else "fg-muted", SECOND, rx=4))
        c.add(text(x, BASE + 22, lab, 15, "middle", "fg", weight=700))
        if drop:
            c.add(line(x + 44, TOP, x + 44, top, "brand", MAIN, arrow_end=True))
            c.add(text(x + 52, (TOP + top) / 2 + 4, "drop", 12, "start", "brand", weight=600))
    c.add(text(40, (TOP + BASE) / 2, "RPM (not to scale)", 12, "middle", "fg-muted", rotate=-90))
    # difference bracket
    yl, yr = TOP + 70, TOP + 105
    c.add(line(310, yl, 520, yl, "warn", THIN, DASH), line(470, yr, 520, yr, "warn", THIN, DASH))
    c.add(line(520, yl, 520, yr, "warn", MAIN))
    c.add(multiline(528, (yl + yr) / 2 - 4, ["difference", "L to R"], 12, "start", "warn-fg", weight=600))
    c.add(text(330, 350, "Typical trainer: each drop up to about 125 to 175 RPM, difference up to about 50 RPM.", 12, "middle", "fg-muted"))
    c.add(text(330, 368, "Only the numbers in your POH count.", 12, "middle", "fg", weight=600))
    c.add(text(330, 30, "Each drop within limits, and the two drops close to each other", 14, "middle", "fg", weight=700))
    return c


# ================================================================ BAKC 3.4 malfunctions
@chart
def carburettor_ice_temperature_ranges() -> Canvas:
    c = Canvas("Outside air temperatures that produce engine ice",
               "Rough outside air temperature ranges for each kind of engine ice, all needing high humidity or visible moisture: throttle ice roughly minus 5 "
               "to plus 20 degrees at low power, fuel evaporation ice roughly minus 10 to plus 30 at any power, impact ice in visible moisture at or below "
               "freezing. The CASA chart shows serious icing at any power possible from well below freezing to about 30 degrees in high humidity, and "
               "serious icing at descent power over an even wider range.", height=400, prefix="cit")
    ch = Chart(c, (-15, 35), (0, 5), box=(60, 50, 610, 314), xlabel="Outside air temperature (°C)", xticks=[-15, -10, -5, 0, 5, 10, 15, 20, 25, 30, 35],
               yticks=[], xfmt=lambda v: f"{int(v):+d}" if v else "0", grid=True)
    c.add(ch.axes(arrows=False))
    c.add(text(ch.px(0) + 6, ch.top - 8, "freezing", 12, "start", "info", weight=600))
    rows = [("Throttle ice", "low power, nearly closed throttle: the most dangerous", -5, 20, "bad", False),
            ("Fuel evaporation ice", "any power, worst in high humidity", -10, 30, "warn", False),
            ("Impact ice", "cloud, rain or sleet at or below freezing", -15, 0, "info", True),
            ("CASA chart, high humidity", "serious icing at any power; at descent power, wider still", -12, 30, "brand", True)]
    for k, (name, sub, t0, t1, colour, open_left) in enumerate(rows):
        y = ch.top + 22 + k * 62
        x0 = ch.px(t0) + (14 if open_left else 4)
        c.add(rect(ch.px(t0), y, ch.px(t1) - ch.px(t0), 20, f"{colour}-soft", colour, SECOND, rx=10 if not open_left else 3))
        if open_left:
            c.add(path(f"M{ch.px(t0) + 8} {y + 10} L{ch.px(t0) - 6} {y + 10}", colour, None, MAIN, arrow_end=True))
        c.add(line(ch.px(0), y - 2, ch.px(0), y + 22, "info", SECOND))
        name_x = x0 if t0 >= 0 or ch.px(0) - x0 > len(name) * 8 else ch.px(0) + 6
        c.add(text(x0 if t0 < -9 and not open_left else name_x, y - 6, name, 13, "start", colour if colour != "warn" else "warn-fg", weight=700))
        c.add(text(ch.px(0) + 6, y + 35, sub, 11, "start", "fg-muted"))
    y = ch.top + 22 + 3 * 62
    c.add(path(f"M{ch.px(30)} {y + 10} L{ch.px(34)} {y + 10}", "brand", None, MAIN, dash=DASH, arrow_end=True))
    c.add(text(330, 372, "Rough ranges only. High humidity is the common factor: ice forms in air well above freezing.", 11, "middle", "fg-muted"))
    return c


@chart
def carb_heat_check_rpm() -> Canvas:
    c = Canvas("What the RPM does during the carburettor heat check",
               "RPM against time during the run-up. Full carburettor heat makes the RPM drop because hot air is less dense. If ice was present, the RPM then "
               "rises while the heat is still on as the ice melts. With heat back to cold the RPM returns to its original value. No drop at all means the "
               "heat is not working.", height=380, prefix="chc")
    ch = Chart(c, (0, 10), (0, 10), box=(70, 70, 600, 290), xticks=[], yticks=[], grid=False)
    c.add(rect(ch.px(2), ch.top, ch.px(7.4) - ch.px(2), ch.bottom - ch.top, "warn-soft", None, fill_opacity=0.6))
    c.add(text(ch.px(4.7), ch.top + 14, "carburettor heat ON (full)", 13, "middle", "warn-fg", weight=700))
    c.add(ch.axes())
    c.add(text(ch.px(5), ch.bottom + 20, "time", 12, "middle", "fg-muted"))
    c.add(text(ch.left - 14, (ch.top + ch.bottom) / 2, "RPM", 12, "middle", "fg-muted", weight=600, rotate=-90))
    c.add(ch.hline(7, "fg-faint", DASH))
    c.add(multiline(ch.px(0.1), ch.py(7) - 26, ["check RPM", "(often 1,700 to 1,800)"], 11, "start", "fg-muted"))
    ice = [(0, 7), (1.9, 7), (2.3, 4.6), (3.2, 4.4), (4.6, 5.4), (6, 5.6), (7.3, 5.6), (7.7, 7), (10, 7)]
    noice = [(2.3, 4.6), (7.3, 4.6), (7.7, 7)]
    dead = [(1.9, 7), (7.4, 7)]
    c.add(ch.curve(noice, "fg-muted", MAIN, dash="6 4", smooth=False))
    c.add(ch.curve(dead, "bad", MAIN, dash="2 4", smooth=False))
    c.add(ch.curve(ice, "brand", 2.5, smooth=False))
    x, y = ch.pt(2.25, 4.7)
    c.add(callout(x, y, x + 24, y + 70, ["1 · RPM drops:", "hot air is less dense"], "fg", 12))
    x, y = ch.pt(5, 5.45)
    c.add(callout(x, y, x + 90, y - 70, ["2 · RPM rises with heat still on:", "ice was there and has melted"], "brand", 12))
    x, y = ch.pt(7.6, 6.8)
    c.add(callout(x, y, x + 10, y + 62, ["3 · back to cold:", "RPM returns to normal"], "fg", 12))
    c.add(text(ch.px(7.3) - 4, ch.py(4.6) + 18, "no ice: stays down", 11, "end", "fg-muted"))
    c.add(text(ch.px(2.6), ch.py(7) - 8, "no drop: heat not working", 11, "start", "bad", weight=600))
    c.add(text(330, 30, "Heat on: expect a drop. A rise while still on means ice.", 15, "middle", "fg", weight=700))
    c.add(text(330, 362, "Carburettor heat air is unfiltered: use it on the ground only for this check, and select cold before take-off.", 11, "middle", "fg-muted"))
    return c


@chart
def chasing_the_rpm() -> Canvas:
    c = Canvas("Why opening the throttle hides carburettor ice",
               "Time history of undiagnosed carburettor ice. The RPM falls slowly as ice builds; each time the pilot opens the throttle the RPM recovers for a "
               "moment while the ice keeps building behind the more open butterfly. At full throttle there is nothing left, and the engine stops.",
               height=390, prefix="ctr")
    ch = Chart(c, (0, 10), (0, 10), box=(70, 50, 600, 300), xticks=[], yticks=[], grid=False)
    ice = [(0, 0.3), (10, 7.6)]
    c.add(path(f"M{ch.px(0)} {ch.py(0)} L{ch.px(10)} {ch.py(0)} L{ch.px(10)} {ch.py(4.4)} L{ch.px(0)} {ch.py(0.2)} Z", None, "sky-soft", 0))
    c.add(text(ch.px(6.4), ch.py(0.9), "ice building", 13, "middle", "sky-fg", weight=700))
    c.add(ch.axes())
    c.add(text(ch.px(5), ch.bottom + 20, "time", 12, "middle", "fg-muted"))
    # throttle steps
    thr = [(0, 4), (2, 4), (2, 5.4), (4, 5.4), (4, 6.8), (6, 6.8), (6, 8.4), (10, 8.4)]
    c.add(ch.curve(thr, "info", MAIN, smooth=False))
    c.add(text(ch.px(0.1), ch.py(4) - 7, "throttle", 12, "start", "info", weight=600))
    c.add(text(ch.px(6.1), ch.py(8.4) - 8, "full throttle: nothing left", 12, "start", "info", weight=700))
    # RPM sawtooth then failure
    rpm = [(0, 6), (2, 4.9), (2.05, 6), (4, 4.9), (4.05, 6), (6, 4.9), (6.05, 6), (7.6, 4.8), (8.6, 3.0), (9.3, 0.9)]
    c.add(ch.curve(rpm, "brand", 2.5, smooth=False))
    c.add(text(ch.px(0.1), ch.py(6) - 8, "RPM", 13, "start", "brand", weight=700))
    for xx in (2, 4, 6):
        c.add(text(ch.px(xx), ch.py(2.9), "open", 11, "middle", "fg-muted"))
        c.add(text(ch.px(xx), ch.py(2.9) + 14, "throttle", 11, "middle", "fg-muted"))
        c.add(line(ch.px(xx), ch.py(3.3), ch.px(xx), ch.py(3.8), "fg-muted", THIN))
    x, y = ch.pt(9.3, 0.9)
    c.add(circle(x, y, 5, "bad", "surface", 1.5))
    c.add(callout(x, y, x + 4, y - 50, ["engine", "stops"], "bad", 13))
    c.add(rect(70, 330, 530, 50, "ok-soft", None, rx=8))
    c.add(text(84, 351, "Instead: any unexplained RPM loss is carburettor ice.", 13, "start", "ok-fg", weight=700))
    c.add(text(84, 369, "Full carburettor heat, leave it on, and only then consider the throttle.", 12, "start", "ok-fg"))
    return c


# ================================================================ BAKC 3.5 flight instruments
@chart
def pitot_static_blockages() -> Canvas:
    c = Canvas("What each blockage does to the pressure instruments",
               "A grid of the three pressure instruments against three faults. Pitot tube and drain blocked: the ASI acts like an altimeter, over-reading in "
               "a climb and under-reading in a descent; altimeter and VSI normal. With the drain clear the ASI falls to zero. Static vent blocked: the "
               "altimeter freezes, the VSI reads zero, the ASI under-reads in a climb and over-reads in a descent. Alternate static in the cockpit: altimeter "
               "and ASI read slightly high and the VSI shows a brief climb when selected.", height=400, prefix="psb")
    X0, Y0, ROWH = 144, 70, 92
    CW = [196, 144, 144]
    CX0 = [X0, X0 + 196, X0 + 340]
    heads = ["Airspeed indicator", "Altimeter", "VSI"]
    rows = [("Pitot blocked", "(drain blocked too)", [("acts like an altimeter:", "over-reads climbing,", "under-reads descending", "bad"), ("normal", "", "", "ok"), ("normal", "", "", "ok")]),
            ("Static blocked", "", [("under-reads climbing,", "over-reads descending", "(right only at that height)", "bad"), ("frozen at the", "blockage height", "", "bad"), ("reads zero", "", "", "bad")]),
            ("Alternate static", "(cabin, selected)", [("reads slightly high", "", "", "warn"), ("reads slightly high", "", "", "warn"), ("brief climb when", "selected", "", "warn")])]
    c.add(text(20, 32, "Static feeds all three; pitot feeds only the ASI", 15, "start", "fg", weight=700))
    for j, h in enumerate(heads):
        c.add(text(CX0[j] + CW[j] / 2, Y0 - 10, h, 13, "middle", "fg", weight=700))
    for i, (name, sub, cells) in enumerate(rows):
        y = Y0 + i * ROWH
        c.add(text(20, y + ROWH / 2 - 2, name, 13, "start", "fg", weight=700))
        if sub:
            c.add(text(20, y + ROWH / 2 + 14, sub, 11, "start", "fg-muted"))
        for j, (l1, l2, l3, colour) in enumerate(cells):
            x, COLW = CX0[j], CW[j]
            c.add(rect(x + 4, y + 4, COLW - 8, ROWH - 8, f"{colour}-soft", None, rx=8))
            lines = [s for s in (l1, l2, l3) if s]
            c.add(multiline(x + COLW / 2, y + ROWH / 2 - (len(lines) - 1) * 8 + 4, lines, 12, "middle", f"{colour}-fg", leading=1.3))
    c.add(text(20, Y0 + 3 * ROWH + 26, "Pitot blocked but drain clear: the trapped pressure leaks away and the ASI falls to zero.", 12, "start", "fg-muted"))
    return c


def gauge_face(cx: float, cy: float, r: float = 62) -> str:
    return circle(cx, cy, r + 6, "surface-2", "fg", SECOND) + circle(cx, cy, r, "surface", "line-strong", THIN)


@chart
def gyro_instruments_panel() -> Canvas:
    c = Canvas("The three gyro instruments",
               "Attitude indicator: gyro spinning about a vertical axis, rigid in space, normally vacuum driven. Directional indicator: gyro spinning about a "
               "horizontal axis, rigid in azimuth, no magnetic sense, reset to the compass about every 10 to 15 minutes, normally vacuum driven. Turn "
               "coordinator: gyro that precesses when the aeroplane yaws and rolls, shows rate of turn, with a ball showing balance, normally electric.",
               height=420, prefix="gip")
    xs = [110, 320, 530]
    CY, R = 150, 62
    # attitude indicator
    cx = xs[0]
    cid = "gip-ai"
    c.add_defs(f'<clipPath id="{cid}"><circle cx="{cx}" cy="{CY}" r="{R}"/></clipPath>')
    c.add(gauge_face(cx, CY, R))
    c.add(f'<g clip-path="url(#{cid})">' + group(rect(cx - 90, CY - 90, 180, 90, "sky-soft", None), rect(cx - 90, CY, 180, 90, "warn-soft", None),
                                                  line(cx - 90, CY, cx + 90, CY, "fg", MAIN), transform=f"rotate(15 {cx} {CY})") + "</g>")
    c.add(path(f"M{cx - 34} {CY} L{cx - 12} {CY} L{cx} {CY + 10} L{cx + 12} {CY} L{cx + 34} {CY}", "brand", None, 3))
    c.add(circle(cx, CY, 2.5, "brand", None))
    # directional indicator
    cx = xs[1]
    c.add(gauge_face(cx, CY, R))
    for b in range(0, 360, 30):
        x0, y0 = bxy(cx, CY, R - 2, b)
        x1, y1 = bxy(cx, CY, R - 10, b)
        c.add(line(x0, y0, x1, y1, "fg-muted", SECOND))
        x, y = bxy(cx, CY, R - 22, b)
        lab = {0: "N", 90: "E", 180: "S", 270: "W"}.get(b, str(b // 10))
        c.add(text(x, y + 4, lab, 11 if b % 90 else 12, "middle", "fg" if b % 90 == 0 else "fg-muted", weight=700 if b % 90 == 0 else None))
    c.add(plane_top(cx, CY - 5, 0.32, 0, "brand", "brand-soft"))    # centre the drawing (nose 21, tail -51) on the card
    c.add(path(f"M{cx - 6} {CY - R - 6} L{cx + 6} {CY - R - 6} L{cx} {CY - R + 4} Z", None, "brand"))
    # turn coordinator
    cx = xs[2]
    c.add(gauge_face(cx, CY, R))
    c.add(group(path(f"M{cx - 40} {CY} L{cx - 8} {CY} M{cx + 8} {CY} L{cx + 40} {CY}", "brand", None, 4), circle(cx, CY, 7, "brand", None),
                line(cx, CY - 7, cx, CY - 15, "brand", 3), transform=f"rotate(-18 {cx} {CY})"))
    c.add(text(cx - 44, CY + 30, "L", 12, "middle", "fg", weight=700), text(cx + 44, CY + 30, "R", 12, "middle", "fg", weight=700))
    c.add(rect(cx - 30, CY + 32, 60, 14, "surface-2", "fg-muted", THIN, rx=7))
    c.add(line(cx - 6, CY + 32, cx - 6, CY + 46, "fg-muted", THIN), line(cx + 6, CY + 32, cx + 6, CY + 46, "fg-muted", THIN))
    c.add(circle(cx, CY + 39, 6, "fg", None))
    c.add(text(cx, CY - 30, "2 MIN", 11, "middle", "fg-faint"))
    info = [("Attitude indicator", ["pitch and bank against", "the horizon"], ["gyro axis: vertical", "rigid in space"], "vacuum"),
            ("Directional indicator", ["heading; no magnetic", "sense of its own"], ["gyro axis: horizontal", "reset to the compass", "every 10 to 15 min"], "vacuum"),
            ("Turn coordinator", ["rate of turn; the ball", "shows balance"], ["precesses with", "yaw and roll"], "electric")]
    for x, (name, shows, axis, power) in zip(xs, info):
        c.add(text(x, 40, name, 14, "middle", "fg", weight=700))
        c.add(multiline(x, 244, shows, 11, "middle", "fg-muted", leading=1.3))
        c.add(multiline(x, 284, axis, 12, "middle", "fg", leading=1.3, weight=600))
        colour = "info" if power == "vacuum" else "warn"
        c.add(badge(x, 346, power + (" (suction gauge)" if power == "vacuum" else ""), colour, 12))
    c.add(text(320, 384, "Vacuum pump fails: AI and DI slow, drift and topple, often with no flag; the turn coordinator carries on.", 12, "middle", "fg-muted"))
    c.add(text(320, 404, "Electrical failure: the turn coordinator stops; the vacuum instruments carry on.", 12, "middle", "fg-muted"))
    return c


@chart
def asi_colour_markings() -> Canvas:
    c = Canvas("Colour markings on the airspeed indicator",
               "An airspeed indicator face. White arc: flap operating range, from VSO (stall, landing configuration) to VFE (maximum flap extended speed). "
               "Green arc: normal operating range, from VS1 (stall, clean) to VNO (maximum structural cruising speed). Yellow arc: caution range, smooth air "
               "only, from VNO to VNE. Red line: VNE, never exceed. VA, the manoeuvring speed, is not marked.", height=400, prefix="acm")
    CX, CY, R = 180, 210, 150
    c.add(circle(CX, CY, R + 8, "surface-2", "fg", MAIN))
    c.add(circle(CX, CY, R, "surface", None))
    # bearings (clockwise from top) for the speeds; schematic, not a real aeroplane
    vso, vs1, vfe, vno, vne = 40, 62, 150, 235, 300
    def arc(b0, b1, r, colour, w):
        c.add(path(barc(CX, CY, r, b0, b1), colour, None, w).replace('stroke-linecap="round"', 'stroke-linecap="butt"'))
    arc(vso, vfe, R - 30, "fg-muted", 10)
    c.add(path(barc(CX, CY, R - 30, vso, vfe), "surface", None, 6).replace('stroke-linecap="round"', 'stroke-linecap="butt"'))
    arc(vs1, vno, R - 14, "ok", 12)
    arc(vno, vne, R - 14, "warn", 12)
    x0, y0 = bxy(CX, CY, R - 2, vne)
    x1, y1 = bxy(CX, CY, R - 34, vne)
    c.add(line(x0, y0, x1, y1, "bad", 5, cap="butt"))
    for b in range(20, 341, 20):
        xa, ya = bxy(CX, CY, R - 2, b)
        xb, yb = bxy(CX, CY, R - 8, b)
        c.add(line(xa, ya, xb, yb, "fg-muted", THIN))
    # needle
    nx, ny = bxy(CX, CY, R - 44, 120)
    c.add(line(CX, CY, nx, ny, "fg", 4))
    c.add(circle(CX, CY, 7, "fg", None))
    c.add(text(CX, CY + 52, "KNOTS", 12, "middle", "fg-faint", weight=600))
    # labels at the arc ends
    def tag(b, r, s, colour, anchor):
        x, y = bxy(CX, CY, r, b)
        c.add(text(x, y + 4, s, 12, anchor, colour, weight=700))
    tag(vso, R - 56, "VSO", "fg-muted", "middle")
    tag(vs1, R + 22, "VS1", "ok", "start")
    tag(vfe, R - 58, "VFE", "fg-muted", "middle")
    tag(vno, R + 22, "VNO", "warn-fg", "end")
    tag(vne, R + 22, "VNE", "bad", "end")
    X = 380
    rows = [("White arc", "flap operating range", "VSO (stall, landing flap) to VFE", "fg-muted"),
            ("Green arc", "normal operating range", "VS1 (stall, clean) to VNO", "ok"),
            ("Yellow arc", "caution: smooth air only, no abrupt inputs", "VNO to VNE", "warn"),
            ("Red line", "VNE, never exceed", "structural failure possible beyond", "bad")]
    for i, (name, mean, ends, colour) in enumerate(rows):
        y = 50 + i * 74
        c.add(rect(X, y, 8, 54, colour if colour != "fg-muted" else "line-strong", None, rx=4))
        c.add(text(X + 18, y + 14, name, 14, "start", f"{colour}-fg" if colour in ("ok", "warn") else colour if colour == "bad" else "fg", weight=700))
        c.add(text(X + 18, y + 32, mean, 11, "start", "fg"))
        c.add(text(X + 18, y + 48, ends, 11, "start", "fg-muted"))
    c.add(text(X, 360, "VA is not marked on the ASI:", 12, "start", "fg", weight=600))
    c.add(text(X, 377, "placarded or in the POH; it reduces with weight.", 11, "start", "fg-muted"))
    c.add(text(20, 392, "Schematic face: read your own aeroplane's speeds from its POH.", 11, "start", "fg-faint"))
    return c
