"""RBKA top-up visuals (second wave). Numbers come from content/notes/RBKA/*.md; rbka.py holds the first wave."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart, cl_curve
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, arc_path, arrow, badge, callout, circle, ellipse, fmt, group, line,
                                multiline, num, path, plane_rear, plane_side, plane_top, polygon, rect, sample, smooth_path, text)


def _panel(x: float, y: float, w: float, h: float, fill: str = "surface-2") -> str:
    return rect(x, y, w, h, fill, None, rx=10)


def _ground(x0: float, x1: float, y: float, depth: float = 14) -> str:
    return path(f"M{fmt(x0)} {fmt(y)} L{fmt(x1)} {fmt(y)} L{fmt(x1)} {fmt(y + depth)} L{fmt(x0)} {fmt(y + depth)} Z", None, "surface-2") + \
        line(x0, y, x1, y, "fg-muted", SECOND)


# ---------------------------------------------------------------- 3.1 lift and drag
def _cd(a: float) -> float:
    """Drag coefficient model matched to cl_curve: CD0 0.03 + k CL^2 (best L/D at CL 0.6, 4 degrees), plus separation drag past 13 degrees."""
    cl = cl_curve(a)
    extra = 0.006 * (a - 11) ** 2 if a > 11 else 0.0
    return 0.03 + 0.0833 * cl * cl + extra


@chart
def ld_ratio_vs_angle_of_attack() -> Canvas:
    c = Canvas("Most efficient at 4 degrees, most lift at 16", "Two graphs against the same angle of attack scale. Above, the lift/drag ratio rises "
               "quickly to a peak at about 4 degrees, the best L/D, and falls away either side. Below, the lift coefficient rises in a straight line "
               "to its maximum at about 16 degrees, the critical angle, and then collapses. The two peaks are about 12 degrees apart: the efficient "
               "wing has a large margin to the stall.", height=470, prefix="lda")
    xt = [0, 4, 8, 12, 16, 20]
    top = Chart(c, (-2, 21), (0, 11.5), box=(80, 48, 600, 188), ylabel=None, xticks=xt, yticks=[], grid=False)
    bot = Chart(c, (-2, 21), (0, 1.75), box=(80, 248, 600, 388), xlabel="Angle of attack (degrees)", ylabel=None, xticks=xt, yticks=[],
                xfmt=lambda v: f"{int(v)}°", grid=False)
    # the margin between the two angles
    c.add(rect(top.px(4), 48, top.px(16) - top.px(4), 340, "ok-soft", None, fill_opacity=0.55))
    c.add(text((top.px(4) + top.px(16)) / 2, 214, "about 12° of margin: where you fly", 12, "middle", "ok-fg", weight=600))
    # top axes without tick labels on x (shared scale below)
    c.add(line(top.left, top.bottom, top.right + 8, top.bottom, "fg-muted", SECOND, arrow_end=True, cap="butt"))
    c.add(line(top.left, top.bottom, top.left, top.top - 8, "fg-muted", SECOND, arrow_end=True, cap="butt"))
    c.add(text(26, (top.top + top.bottom) / 2, "Lift / drag", 13, "middle", "fg-muted", weight=600, rotate=-90))
    c.add(bot.axes())
    c.add(text(26, (bot.top + bot.bottom) / 2, "Lift coefficient", 13, "middle", "fg-muted", weight=600, rotate=-90))
    for x in (4, 16):
        c.add(line(top.px(x), 48, top.px(x), 388, "fg-faint", THIN, DASH))
    ld = sample(lambda a: cl_curve(a) / _cd(a), -2, 20.5, 15)
    c.add(top.curve(ld, "brand", 2.5))
    best = max(ld, key=lambda p: p[1])
    c.add(top.point(4, cl_curve(4) / _cd(4), "brand", 6))
    c.add(top.callout(4, cl_curve(4) / _cd(4), 40, 44, ["best L/D ≈ 4°", "most lift for the least drag"], "brand", 13))
    c.add(text(top.px(20.5), top.py(6.2), "near the stall: poor", 12, "end", "fg-muted"))
    c.add(text(top.px(-1.2), top.py(0.8), "fast, small angle: poor", 12, "start", "fg-muted"))
    del best
    cl = sample(cl_curve, -2, 20.5, 90)
    c.add(bot.curve(cl, "info", 2.5))
    c.add(bot.point(16, 1.5, "bad", 6))
    c.add(bot.callout(16, 1.5, -40, 46, ["CL max ≈ 16°", "the critical angle"], "bad", 13))
    c.add(text(bot.px(20.4), bot.py(0.95), "stall", 12, "end", "bad", weight=600))
    c.add(text(bot.px(5), bot.py(0.28), "lift rises in a straight line", 12, "start", "info", weight=600))
    c.add(text(20, 452, "Exam pair: the smaller angle (about 4°) is the efficient one; the larger (about 16°) is maximum lift.", 12, "start", "fg-muted"))
    return c


def _vortex(cx: float, cy: float, rx: float, ry: float, clockwise: bool, colour: str, cls: str | None = None) -> str:
    """A tip vortex seen end-on: an ellipse with a direction arrowhead."""
    a0, a1 = (200, 480) if clockwise else (340, 60)
    pts = []
    n = 24
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n)
        k = 1 - 0.35 * i / n
        pts.append((cx + rx * k * math.cos(t), cy + ry * k * math.sin(t)))
    d = smooth_path(pts)
    return path(d, colour, None, SECOND, arrow_end=True, cls=cls)


@chart
def ground_effect() -> Canvas:
    c = Canvas("Ground effect", "Two rear views of the same wing. Out of ground effect, more than a wingspan up, the wing pushes a deep downwash "
               "behind it and sheds full-sized tip vortices: induced drag. Within about half a span of the runway the ground blocks the "
               "downwash and squashes the vortices, so induced drag falls and the wing makes a little more lift at the same angle of attack. "
               "Below, the two consequences: on landing the aeroplane floats, a long way if it arrives fast; on take-off it can lift off "
               "early in ground effect, then sink back or refuse to climb as it climbs out of it.", height=560, prefix="gef")
    c.style(".gef-spin{transform-box:fill-box;transform-origin:center;animation:gef-turn 3s linear infinite}"
            "@keyframes gef-turn{to{transform:rotate(360deg)}}")
    # ---- top: two rear views
    for i, (head, sub, colour) in enumerate((("Out of ground effect", "more than a wingspan up", "fg"),
                                              ("Within half a span", "the last 15 ft or so", "brand"))):
        x0 = 16 + i * 312
        c.add(_panel(x0, 14, 296, 262, "surface-2" if i == 0 else "brand-soft"))
        c.add(text(x0 + 148, 40, head, 16, "middle", "fg" if i == 0 else "brand-fg", weight=700))
        c.add(text(x0 + 148, 58, sub, 12, "middle", "fg-muted"))
    # left: free air. Vortices roll up at the wing tips, level with the high wing (local y about -7.5)
    lx, ly = 164, 118
    c.add(plane_rear(lx, ly, 1.25, 0, "fg"))
    for sgn in (-1, 1):
        tip = lx + sgn * 62
        c.add(group(_vortex(tip + sgn * 6, ly - 9, 24, 22, sgn > 0, "info"), cls="gef-spin"))
    for dx in (-54, -36, 36, 54):
        c.add(arrow(lx + dx, ly - 4, lx + dx, ly + 92, "info", MAIN))
    c.add(text(lx, ly + 118, "deep downwash, full tip vortices", 12, "middle", "info", weight=600))
    c.add(text(lx, ly + 136, "→ induced drag", 12, "middle", "info"))
    # right: near the ground, wheels on the runway (they sit 13.5 units below the CG)
    rx_, gy = 476, 228
    ry = gy - 17
    c.add(rect(334, gy, 284, 40, "surface", None))
    c.add(line(334, gy, 618, gy, "fg-muted", MAIN))
    c.add(text(476, gy + 26, "runway", 12, "middle", "fg-muted"))
    c.add(plane_rear(rx_, ry, 1.25, 0, "fg"))
    for sgn in (-1, 1):
        tip = rx_ + sgn * 62
        c.add(_vortex(tip + sgn * 16, ry - 8, 18, 9, sgn > 0, "info"))
    for dx in (-54, -36, 36, 54):
        c.add(arrow(rx_ + dx, ry - 4, rx_ + dx, ry + 12, "info", MAIN))
    c.add(line(rx_ + 112, ry - 10, rx_ + 112, gy - 2, "fg-muted", THIN))
    c.add(line(rx_ + 106, ry - 10, rx_ + 118, ry - 10, "fg-muted", THIN))
    c.add(text(rx_ + 112, ry - 18, "< ½ span", 11, "middle", "fg-muted"))
    c.add(multiline(rx_, 96, ["ground blocks the downwash,", "vortices squashed"], 12, "middle", "brand-fg", weight=600))
    c.add(multiline(rx_, 132, ["→ LESS induced drag,", "a little more lift"], 12, "middle", "brand-fg"))
    # ---- bottom: consequences
    for i, (head, colour) in enumerate((("Landing: the float", "warn"), ("Take-off: early lift-off, then sink", "bad"))):
        x0 = 16 + i * 312
        c.add(_panel(x0, 290, 296, 236, "surface-2"))
        c.add(text(x0 + 148, 314, head, 14, "middle", f"{colour}-fg" if colour != "bad" else "bad", weight=700))
    GY = 470
    for x0 in (16, 328):
        c.add(rect(x0 + 10, GY - 34, 276, 34, "brand-soft", None, fill_opacity=0.7))
        c.add(_ground(x0 + 10, x0 + 286, GY, 12))
        c.add(text(x0 + 16 if x0 < 100 else x0 + 280, GY - 40, "ground effect", 11, "start" if x0 < 100 else "end", "brand-fg"))
    # landing: approach, flare, long float
    c.add(path(smooth_path([(34, 340), (110, 400), (150, 440), (176, 452), (215, 458), (270, 461), (296, 466)]), "warn", None, MAIN))
    c.add(path(smooth_path([(34, 340), (110, 400), (150, 440), (172, 456), (196, 466)]), "ok", None, SECOND, dash=DASH))
    c.add(circle(196, 467, 3.5, "ok", None))
    c.add(circle(296, 467, 3.5, "warn", None))
    c.add(callout(196, 467, 212, 500, "right speed: short float", "ok-fg", 11, anchor="start"))
    c.add(multiline(300, 402, ["10 kt fast:", "floats a long way"], 12, "end", "warn-fg", weight=600))
    c.add(plane_side(80, 369, 0.32, "fg", pitch=-5))
    # take-off: lift off early, fly in ground effect, sink back
    c.add(line(350, GY - 2, 420, GY - 2, "fg-muted", SECOND, DASH))
    c.add(path(smooth_path([(420, 468), (450, 452), (490, 446), (520, 446), (548, 452), (580, 462), (600, 466)]), "bad", None, MAIN))
    c.add(path(smooth_path([(520, 446), (560, 420), (604, 386)]), "fg-faint", None, SECOND, dash=DASH))
    c.add(plane_side(490, 440, 0.32, "fg", pitch=4))
    c.add(callout(422, 467, 360, 396, ["lifts off below", "the POH speed"], "fg", 11, anchor="start"))
    c.add(text(604, 376, "climb it hoped for", 11, "end", "fg-faint"))
    c.add(callout(580, 462, 560, 500, "induced drag returns: sinks", "bad", 11, anchor="end"))
    c.add(text(16, 548, "Ground effect cuts induced drag, not parasite drag. Arrive at the right speed; lift off at the POH speed.", 12,
               "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 3.3 climbing
def _thrust(v: float) -> float:
    return 2.4 - 0.6 * v


def _drag(v: float) -> float:
    return 0.5 * v * v + 0.5 / (v * v)


def _argmax(fn, a: float, b: float) -> float:
    best, bx = -1e9, a
    for i in range(2001):
        x = a + (b - a) * i / 2000
        if fn(x) > best:
            best, bx = fn(x), x
    return bx


@chart
def excess_thrust_and_power_vs_airspeed() -> Canvas:
    c = Canvas("Excess thrust sets Vx, excess power sets Vy", "Two graphs against airspeed for a propeller aeroplane. Above, thrust available falls "
               "as speed rises and drag is a U-shaped curve; the gap between them, the excess thrust, is greatest at a low speed: Vx, best angle. "
               "Below, power available and power required; the gap, the excess power, is greatest at a higher speed: Vy, best rate. Power is "
               "thrust times speed, so multiplying by the speed moves the peak to the right.", height=560, prefix="etp")
    vx = _argmax(lambda v: _thrust(v) - _drag(v), 0.75, 1.6)
    vy = _argmax(lambda v: v * (_thrust(v) - _drag(v)), 0.75, 1.6)
    v0, v1 = 0.62, 1.75
    top = Chart(c, (v0, v1), (0, 2.4), box=(80, 60, 600, 230), xticks=[], yticks=[], grid=False)
    bot = Chart(c, (v0, v1), (0, 3.0), box=(80, 318, 600, 488), xticks=[], yticks=[], grid=False)
    for ch, lab in ((top, "Thrust and drag"), (bot, "Power")):
        c.add(ch.axes())
        c.add(text(26, (ch.top + ch.bottom) / 2, lab, 13, "middle", "fg-muted", weight=600, rotate=-90))
        c.add(text(ch.right + 4, ch.bottom + 18, "airspeed →", 12, "end", "fg-muted", weight=600))
    c.add(text(20, 30, "Angle comes from excess THRUST; rate from excess POWER.", 15, "start", "fg", weight=700))
    vs = 0.7
    for ch in (top, bot):
        c.add(ch.band(v0, vs, "bad", 0.1))
    c.add(text(top.px((v0 + vs) / 2), top.top + 14, "stall", 11, "middle", "bad"))
    vmax = 1.58

    def gap(ch, f_hi, f_lo, colour):
        pts = [(v, f_hi(v)) for v, _ in sample(f_hi, vs, vmax, 50)] + [(v, f_lo(v)) for v, _ in reversed(sample(f_hi, vs, vmax, 50))]
        return path("M" + " L".join(f"{fmt(ch.px(x))} {fmt(ch.py(y))}" for x, y in pts) + " Z", None, colour, 0, fill_opacity=0.14)

    def span(X, Ya, Yb, colour):
        m = (Ya + Yb) / 2
        return arrow(X, m, X, Ya + 2, colour, 2.5) + arrow(X, m, X, Yb - 2, colour, 2.5)

    # top panel
    c.add(gap(top, _thrust, _drag, "brand"))
    c.add(top.curve(sample(_thrust, vs, 1.7, 40), "fg", MAIN))
    c.add(top.curve(sample(_drag, vs, 1.66, 60), "info", MAIN))
    c.add(text(top.px(1.3), top.py(_thrust(1.3)) - 12, "thrust available", 12, "middle", "fg", weight=600))
    c.add(text(top.px(1.3), top.py(_drag(1.3)) + 22, "drag", 12, "middle", "info", weight=600))
    X, Y1, Y2 = top.px(vx), top.py(_thrust(vx)), top.py(_drag(vx))
    c.add(span(X, Y1, Y2, "brand"))
    c.add(text(X + 10, (Y1 + Y2) / 2 + 4, "biggest excess thrust", 13, "start", "brand", weight=700))
    c.add(line(X, Y2, X, top.bottom, "fg-faint", THIN, DASH))
    c.add(text(X, top.bottom + 18, "Vx", 14, "middle", "brand", weight=700))
    c.add(text(X, top.bottom + 34, "best angle", 11, "middle", "brand"))
    # bottom panel
    pa = lambda v: v * _thrust(v)
    pr = lambda v: v * _drag(v)
    c.add(gap(bot, pa, pr, "ok"))
    c.add(bot.curve(sample(pa, vs, 1.7, 50), "fg", MAIN))
    c.add(bot.curve(sample(pr, vs, 1.66, 60), "info", MAIN))
    c.add(text(bot.px(1.3), bot.py(pa(1.3)) - 12, "power available", 12, "middle", "fg", weight=600))
    c.add(text(bot.px(1.42), bot.py(pr(1.42)) + 24, "power required", 12, "start", "info", weight=600))
    X, Y1, Y2 = bot.px(vy), bot.py(pa(vy)), bot.py(pr(vy))
    c.add(span(X, Y1, Y2, "ok"))
    c.add(text(X + 10, Y2 + 28, "biggest excess power", 13, "start", "ok-fg", weight=700))
    c.add(line(X, Y2, X, bot.bottom, "fg-faint", THIN, DASH))
    c.add(text(X, bot.bottom + 18, "Vy", 14, "middle", "ok-fg", weight=700))
    c.add(text(X, bot.bottom + 34, "best rate", 11, "middle", "ok-fg"))
    c.add(line(top.px(vx), bot.top, top.px(vx), bot.bottom, "brand", THIN, DASH))
    c.add(text(top.px(vx) - 6, bot.top + 10, "Vx", 12, "end", "brand", weight=600))
    c.add(text(20, 548, "Schematic curves for a propeller trainer. Vx is always the lower speed.", 11, "start", "fg-faint"))
    return c


@chart
def wind_shear_on_climb_out() -> Canvas:
    c = Canvas("Losing the headwind on climb-out", "Side view of a climb-out at Vy into a 20 knot headwind that suddenly drops to 5 knots higher up. "
               "Inertia keeps the groundspeed for a moment, so the airspeed falls by the 15 knots of headwind lost. The rate and angle of climb "
               "fall and the path flattens below the planned climb until the aeroplane re-accelerates; to get back to Vy the pilot lowers the "
               "nose and gives up some of the climb. Close to the ground this is dangerous.", height=440, prefix="wsc")
    GY = 360
    SY = 214   # the shear layer
    path_d = "M70 352 L300 214 C340 191 380 179 430 173 C480 167 520 150 580 116"
    c.style(f"""
.wsc-plane{{offset-path:path("{path_d}");offset-rotate:auto;animation:wsc-fly 7s ease-in-out infinite}}
@keyframes wsc-fly{{0%{{offset-distance:0%;opacity:0}}6%{{opacity:1}}90%{{opacity:1}}100%{{offset-distance:100%;opacity:0}}}}
.wsc-static{{display:none}}
@supports not (offset-path: path("M0 0")){{.wsc-plane{{display:none}}.wsc-static{{display:inline}}}}
""")
    c.add(rect(20, 70, 600, SY - 70, "sky-soft", None, fill_opacity=0.35))
    c.add(rect(20, SY, 600, GY - SY, "sky-soft", None, fill_opacity=0.8))
    c.add(line(20, SY, 620, SY, "sky-fg", THIN, DASH))
    c.add(text(30, SY - 8, "shear: the wind changes here", 11, "start", "sky-fg"))
    c.add(_ground(20, 620, GY, 16))
    c.add(rect(20, GY - 3, 130, 6, "fg-muted", None))
    for y in (112, 150):
        c.add(arrow(214, y, 190, y, "sky-fg", SECOND))
    c.add(text(182, 135, "5 kt headwind", 12, "end", "sky-fg", weight=600))
    for y in (276, 306, 336):
        c.add(arrow(612, y, 532, y, "sky-fg", SECOND))
    c.add(text(612, 262, "20 kt headwind", 12, "end", "sky-fg", weight=600))
    c.add(line(300, 213, 470, 110, "ok", SECOND, DASH))
    c.add(text(474, 102, "planned climb at Vy", 12, "end", "ok-fg", weight=600))
    c.add(path(path_d, "bad", None, MAIN))
    c.add(badge(170, 250, "IAS = Vy", "ok", 12))
    c.add(badge(392, 230, "IAS falls 15 kt", "bad", 12))
    c.add(multiline(392, 256, ["rate and angle", "of climb drop"], 12, "middle", "bad", weight=600))
    c.add(multiline(474, 180, ["lower the nose,", "regain Vy, climb on"], 11, "start", "fg-muted"))
    c.add(rect(20, 14, 600, 46, "brand-soft", None, rx=8))
    c.add(text(32, 33, "Inertia keeps the groundspeed: airspeed = groundspeed + headwind.", 13, "start", "brand-fg", weight=700))
    c.add(text(32, 51, "Headwind 20 → 5 kt: the airspeed drops 15 kt at once, with no change of attitude or power.", 12, "start", "brand-fg"))
    c.add(text(20, 396, "A sudden gain of tailwind does the same; a headwind that increases gives a brief bonus.", 12, "start", "fg-muted"))
    c.add(text(20, 414, "A steady wind never changes the rate of climb; only a sudden change does, and only for a while.", 12,
               "start", "fg-muted"))
    c.add(group(plane_side(0, 0, 0.4, "fg", gear=True), cls="wsc-plane"))
    c.add(group(plane_side(300, 206, 0.4, "fg", pitch=30, gear=True), cls="wsc-static"))
    return c


# ---------------------------------------------------------------- 3.4 descents
@chart
def glide_speed_off_best() -> Canvas:
    c = Canvas("Any other speed glides less far", "Above, the lift/drag ratio against airspeed: it peaks at 9 to 1 at the best glide speed and "
               "falls either side, to 7 to 1 at a speed somewhat slower (induced drag) or somewhat faster (parasite drag). Below, the result "
               "from an engine failure at 3,000 ft above ground: at the best glide speed the aeroplane reaches 27,000 ft, about 4.4 nautical "
               "miles; at a speed giving only 7 to 1 it reaches 21,000 ft, about 3.5 nautical miles. Almost a mile lost.", height=546, prefix="gsb")
    ld = lambda v: 18 / (v * v + 1 / (v * v))
    ch = Chart(c, (0.6, 1.62), (4, 10.4), box=(90, 40, 600, 210), xlabel=None, ylabel=None, xticks=[], yticks=[7, 9], grid=True,
               yfmt=lambda v: f"{int(v)} : 1")
    c.add(ch.axes())
    c.add(text(26, 125, "Lift / drag", 13, "middle", "fg-muted", weight=600, rotate=-90))
    c.add(text(345, 232, "Airspeed →", 13, "middle", "fg-muted", weight=600))
    c.add(ch.curve(sample(ld, 0.64, 1.58, 60), "brand", 2.5))
    lo, hi = 0.691, 1.447
    c.add(ch.point(1, 9, "ok", 6))
    c.add(ch.point(lo, 7, "bad", 5.5), ch.point(hi, 7, "bad", 5.5))
    c.add(ch.callout(1, 9, 30, -14, "best glide speed: 9 : 1", "ok-fg", 13))
    c.add(ch.callout(lo, 7, 22, 34, ["too slow: induced", "drag high, near stall"], "bad", 12))
    c.add(ch.callout(hi, 7, -20, 34, ["too fast: parasite", "drag high"], "bad", 12))
    # profile
    GY, TOPY, X0 = 450, 270, 60
    sx = 115          # px per NM
    sy = (GY - TOPY) / 3000
    c.add(_ground(20, 620, GY, 14))
    c.add(line(X0, TOPY, X0, GY, "fg-muted", THIN, DASH))
    c.add(num(X0 - 6, TOPY + 4, "3,000 ft", 12, "end", "fg-muted"))
    c.add(plane_side(X0 + 25, TOPY - 2, 0.36, "fg", pitch=-5, gear=True))
    for d, colour, lab in ((4.4, "ok", "9 : 1  →  27,000 ft ≈ 4.4 NM"), (3.5, "bad", "7 : 1  →  21,000 ft ≈ 3.5 NM")):
        xe = X0 + d * sx
        c.add(line(X0, TOPY, xe, GY, colour, MAIN))
        c.add(circle(xe, GY, 4, colour, None))
    ga = math.degrees(math.atan2(GY - TOPY, 4.4 * sx))
    ra = math.degrees(math.atan2(GY - TOPY, 3.5 * sx))
    c.add(text(X0 + 150, TOPY + 150 * math.tan(math.radians(ga)) - 10, "9 : 1  →  27,000 ft ≈ 4.4 NM", 12, "start", "ok-fg", weight=700,
               cls="num", rotate=ga))
    c.add(text(X0 + 70, TOPY + 70 * math.tan(math.radians(ra)) + 22, "7 : 1  →  21,000 ft ≈ 3.5 NM", 12, "start", "bad", weight=700,
               cls="num", rotate=ra))
    mid = X0 + 3.95 * sx
    c.add(arrow(mid, GY + 44, X0 + 3.5 * sx, GY + 44, "bad", SECOND), arrow(mid, GY + 44, X0 + 4.4 * sx, GY + 44, "bad", SECOND))
    c.add(text(mid, GY + 62, "almost 1 NM lost", 12, "middle", "bad", weight=600))
    for nm in range(0, 5):
        c.add(num(X0 + nm * sx, GY + 28, f"{nm}", 11, "middle", "fg-faint"))
    c.add(text(X0 + 4.9 * sx, GY + 28, "NM", 11, "middle", "fg-faint"))
    c.add(text(620, 534, "Vertical scale exaggerated. Too fast or too slow: either way the glide is steeper.", 11, "end", "fg-faint"))
    return c


@chart
def glide_circle_and_wind() -> Canvas:
    c = Canvas("The wind slides the glide circle downwind", "Plan view. Gliding from 2,800 ft at 70 knots and 700 feet per minute takes 4 minutes, "
               "so in still air the aeroplane can reach anywhere within 4.67 nautical miles: a circle around it. A 15 knot wind drifts the "
               "aeroplane 1 nautical mile in those 4 minutes, so the whole circle slides 1 mile downwind: 5.67 miles reachable downwind, only "
               "3.67 miles upwind. A field 4 miles upwind is out of reach; one 5.5 miles downwind is not.", height=500, prefix="gcw")
    S = 38      # px per NM
    AX, AY = 290, 256
    R = 4.67 * S
    c.add(circle(AX, AY, R, None, "fg-faint", SECOND, dash=DASH))
    c.add(circle(AX + S, AY, R, "brand", "brand", MAIN, fill_opacity=0.10))
    c.add(text(AX - 128, AY - 150, "still air", 12, "end", "fg-muted", weight=600))
    c.add(multiline(476, 98, ["15 kt wind:", "where you can reach"], 13, "start", "brand", weight=700))
    c.add(plane_top(AX, AY, 0.36, 90, "fg"))
    # radii
    c.add(arrow(AX + 6, AY + 64, AX + S + R, AY + 64, "ok", SECOND))
    c.add(num(AX + S + R - 30, AY + 84, "5.67 NM downwind", 12, "end", "ok-fg", weight=600))
    c.add(arrow(AX - 6, AY + 64, AX + S - R, AY + 64, "bad", SECOND))
    c.add(num(AX + S - R + 30, AY + 84, "3.67 NM upwind", 12, "start", "bad", weight=600))
    c.add(arrow(AX, AY - 50, AX + S, AY - 50, "sky-fg", MAIN))
    c.add(text(AX + S / 2, AY - 60, "drift 1 NM", 11, "middle", "sky-fg", weight=600))
    # fields, on the line through the aeroplane
    for d, ok in ((-4, False), (5.5, True)):
        fx = AX + d * S
        c.add(rect(fx - 4.5, AY - 4.5, 9, 9, "ok-soft" if ok else "bad-soft", "ok" if ok else "bad", SECOND, rx=2))
        lx, anc = (fx + 16, "start") if ok else (fx - 32, "end")
        c.add(multiline(lx, AY - 10, [f"field {abs(d):g} NM", "downwind:" if ok else "upwind:"], 11, anc, "ok-fg" if ok else "bad", weight=600))
        c.add(text(lx, AY + 20, "✓ reachable" if ok else "✗ out of reach", 11, anc, "ok-fg" if ok else "bad"))
    # wind arrow
    c.add(arrow(36, 30, 116, 30, "sky-fg", MAIN))
    c.add(text(124, 34, "wind 15 kt (blowing this way)", 12, "start", "sky-fg", weight=600))
    c.add(rect(20, 448, 600, 44, "surface-2", None, rx=8))
    c.add(text(32, 466, "2,800 ft ÷ 700 fpm = 4 min.  Still air: 4 × 70 ÷ 60 = 4.67 NM.", 12, "start", "fg", cls="num"))
    c.add(text(32, 483, "Wind: 15 kt × 4 min ÷ 60 = 1 NM. The circle moves; its size does not.", 12, "start", "fg", cls="num"))
    return c


# ---------------------------------------------------------------- 3.5 turning
def _radius_m(kt: float, bank: float) -> float:
    v = kt * 0.514444
    return v * v / (9.80665 * math.tan(math.radians(bank)))


@chart
def turn_radius_vs_bank_and_speed() -> Canvas:
    c = Canvas("Turn radius: bank and speed", "Turn radius in metres against bank angle at 90 and 120 knots. At 90 knots the radius is about 380 m at "
               "30 degrees, 220 m at 45 degrees and 125 m at 60 degrees. At 120 knots every radius is about 1.78 times larger, the square of "
               "120 over 90. On the right, the three 90 knot circles drawn to scale. Weight does not appear.", height=420, prefix="trb")
    ch = Chart(c, (20, 65), (0, 1100), box=(80, 50, 400, 330), xlabel="Bank angle (degrees)", ylabel="Turn radius (m)",
               xticks=[30, 45, 60], yticks=[0, 250, 500, 750, 1000], xfmt=lambda v: f"{int(v)}°")
    c.add(ch.axes())
    c.add(ch.curve(sample(lambda b: _radius_m(120, b), 26, 65, 50), "info", MAIN))
    c.add(ch.curve(sample(lambda b: _radius_m(90, b), 20, 65, 50), "brand", 2.5))
    c.add(text(ch.px(30) + 12, ch.py(_radius_m(120, 30)) - 6, "120 kt", 13, "start", "info", weight=700))
    c.add(text(ch.px(23) + 6, ch.py(_radius_m(90, 23)) - 10, "90 kt", 13, "start", "brand", weight=700))
    for b, lab, dx, dy, anc in ((30, "≈ 380 m", -6, 24, "end"), (45, "≈ 220 m", -4, 24, "middle"), (60, "≈ 125 m", -4, 24, "middle")):
        c.add(ch.point(b, _radius_m(90, b), "brand", 5))
        X, Y = ch.pt(b, _radius_m(90, b))
        c.add(num(X + dx, Y + dy, lab, 12, anc, "brand", weight=700))
    c.add(rect(196, 60, 196, 52, "info-soft", None, rx=8))
    c.add(multiline(206, 80, ["120 kt: every circle (120÷90)²", "≈ 1.78 times as wide"], 12, "start", "info-fg"))
    # circles to scale on the right
    k = 100 / 380
    CX, CY = 520, 200
    c.add(text(520, 40, "90 kt, to scale", 14, "middle", "fg", weight=700))
    for b, colour, w in ((30, "fg-muted", SECOND), (45, "brand", SECOND), (60, "bad", MAIN)):
        r = _radius_m(90, b) * k
        c.add(circle(CX - 100 + r, CY, r, None, colour, w))
    c.add(plane_top(CX - 100, CY, 0.18, 0, "fg"))
    c.add(text(CX + 100, CY + 112, "30°", 12, "end", "fg-muted", weight=600))
    r45 = _radius_m(90, 45) * k
    c.add(text(CX - 100 + 2 * r45 + 4, CY + 4, "45°", 12, "start", "brand", weight=600))
    r60 = _radius_m(90, 60) * k
    c.add(text(CX - 100 + r60, CY + 4, "60°", 12, "middle", "bad", weight=600))
    c.add(line(424, 318, 424 + 100 * k, 318, "fg", MAIN, cap="butt"))
    c.add(num(428 + 100 * k, 322, "100 m", 11, "start", "fg-muted"))
    c.add(multiline(CX, 344, ["More bank: tighter and faster.", "More speed: wider and slower.", "360° at 45°, 90 kt ≈ 30 s."], 12, "middle", "fg-muted"))
    c.add(text(20, 404, "Radius = V² ÷ (g × tan bank): double the speed, four times the radius. Weight does not appear.", 12,
               "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 3.7 take-off and landing
@chart
def wheelbarrowing_pivot() -> Canvas:
    c = Canvas("Wheelbarrowing: a pivot ahead of the weight", "Two cases. Normal: the main wheels, just behind the centre of gravity, carry the "
               "weight; seen from above, a swing is pulled straight again, like a trolley. Wheelbarrowing: landed fast and flat with the nose "
               "held down, the wing still lifts, the main wheels go light and the nosewheel, ahead of the centre of gravity, becomes the pivot; "
               "seen from above, any swing grows into a ground loop. Cure: ease the control column back (throttle closed) or go around.",
               height=470, prefix="whb")
    for i, (head, sub, colour) in enumerate((("Normal roll", "weight on the main wheels", "ok"), ("Wheelbarrowing", "weight on the nosewheel", "bad"))):
        x0 = 16 + i * 312
        c.add(_panel(x0, 14, 296, 390, f"{colour}-soft"))
        c.add(text(x0 + 148, 40, head, 16, "middle", "ok-fg" if colour == "ok" else "bad", weight=700))
        c.add(text(x0 + 148, 58, sub, 12, "middle", "fg-muted"))
        GY = 176
        c.add(line(x0 + 14, GY, x0 + 282, GY, "fg-muted", MAIN))
        s = 1.5
        px = x0 + 170
        pitch = 0 if i == 0 else -4
        # wheels touch at local y 19.5: mains at x -7.5 (just aft of the CG), nosewheel at x 15
        py = GY - 19.5 * s if i == 0 else GY - s * (15 * math.sin(math.radians(4)) + 19.5 * math.cos(math.radians(4)))
        c.add(plane_side(px, py, s, "fg", pitch=pitch))
        rad = math.radians(-pitch)
        def loc(lx: float, ly: float) -> tuple[float, float]:
            return px + s * (lx * math.cos(rad) - ly * math.sin(rad)), py + s * (lx * math.sin(rad) + ly * math.cos(rad))
        cgx, cgy = loc(0, -2)
        mx, my = loc(-7.5, 19.5)
        nx, ny = loc(15, 19.5)
        c.add(circle(cgx, cgy, 6, "surface", "fg", 1.5), path(f"M{fmt(cgx)} {fmt(cgy - 6)} A6 6 0 0 1 {fmt(cgx + 6)} {fmt(cgy)} L{fmt(cgx)} {fmt(cgy)} Z "
                                                               f"M{fmt(cgx)} {fmt(cgy + 6)} A6 6 0 0 1 {fmt(cgx - 6)} {fmt(cgy)} L{fmt(cgx)} {fmt(cgy)} Z",
                                                               None, "fg"))
        c.add(text(cgx + 8, cgy - 46, "CG", 12, "middle", "fg", weight=700))
        c.add(line(cgx + 6, cgy - 36, cgx + 1, cgy - 9, "fg-muted", THIN))
        if i == 0:
            c.add(arrow(mx, GY + 40, mx, GY + 4, "ok", 2.5))
            c.add(text(mx - 8, GY + 34, "main wheels carry", 11, "end", "ok-fg", weight=600))
            c.add(text(mx - 8, GY + 48, "the weight", 11, "end", "ok-fg", weight=600))
            c.add(arrow(nx, GY + 18, nx, GY + 4, "fg-muted", SECOND))
        else:
            c.add(arrow(nx, GY + 44, nx, GY + 4, "bad", 2.5))
            c.add(text(nx + 8, GY + 34, "nosewheel is", 11, "start", "bad", weight=600))
            c.add(text(nx + 8, GY + 48, "the pivot", 11, "start", "bad", weight=600))
            c.add(arrow(mx, GY + 14, mx, GY + 4, "fg-muted", SECOND))
            c.add(text(mx - 6, GY + 22, "light", 11, "end", "fg-muted"))
            wx, wy = loc(-6, -10)                          # mid-chord on top of the wing
            c.add(arrow(wx, wy - 2, wx, wy - 38, "brand", MAIN))
            c.add(text(wx - 6, wy - 24, "wing still lifting", 11, "end", "brand", weight=600))
            tx, ty = loc(-60, 6)                           # under the tail cone
            c.add(arrow(tx, GY + 8, tx, ty + 4, "fg-muted", SECOND))
            c.add(multiline(tx, GY + 24, ["forward stick:", "tail held up"], 11, "middle", "fg-muted"))
        # plan view underneath: aeroplane yawed 14 degrees, pivot marked
        TY = 300
        heading = 76
        c.add(plane_top(px, TY, 0.95, heading, "fg-muted"))
        h = math.radians(heading - 90)
        def plan(lx: float, ly: float) -> tuple[float, float]:
            return px + 0.95 * (lx * math.cos(h) - ly * math.sin(h)), TY + 0.95 * (lx * math.sin(h) + ly * math.cos(h))
        pv = plan(-7.5, 0) if i == 0 else plan(15, 0)
        cg = plan(0, 0)
        c.add(circle(*pv, 6, "ok" if i == 0 else "bad", "surface", 1.5))
        c.add(circle(*cg, 4, "fg", None))
        c.add(line(x0 + 30, TY, x0 + 266, TY, "fg-faint", THIN, DASH))
        if i == 0:
            c.add(path(arc_path(pv[0], pv[1], 44, -34, -8), "ok", None, MAIN, arrow_end=True))
            c.add(multiline(x0 + 148, 372, ["pivot behind the CG: the swing", "straightens itself, like a trolley"], 12, "middle", "ok-fg", weight=600))
        else:
            c.add(path(arc_path(pv[0], pv[1], 82, 170, 145), "bad", None, MAIN, arrow_end=True))
            c.add(multiline(x0 + 148, 372, ["pivot ahead of the CG: the swing", "grows into a ground loop"], 12, "middle", "bad", weight=600))
    c.add(rect(16, 414, 608, 46, "brand-soft", None, rx=8))
    c.add(text(28, 433, "Cure: throttle closed, EASE BACK to put the weight on the main wheels, or go around.", 12, "start", "brand-fg",
               weight=700))
    c.add(text(28, 450, "Never push forward to hold it down. Prevent it: right speed, main wheels first, nose up.", 12, "start", "brand-fg"))
    return c


# ---------------------------------------------------------------- 3.8 structural damage
def _section(cx: float, cy: float, chord: float, aoa: float, dent: bool) -> tuple[str, list[tuple[float, float]]]:
    """Aerofoil polygon (LE at cx, cy) rotated nose-up by aoa; returns (svg, upper surface points in screen space)."""
    n = 40
    up, lo = [], []
    for i in range(n + 1):
        x = (1 - math.cos(math.pi * i / n)) / 2
        t = 0.13 * (2.969 * math.sqrt(x) - 1.26 * x - 3.516 * x * x + 2.843 * x ** 3 - 1.015 * x ** 4)
        camber = 0.04 * (2 * 0.4 * x - x * x) / 0.16 if x < 0.4 else 0.04 * ((1 - 0.8) + 2 * 0.4 * x - x * x) / 0.36
        yu, yl = camber + t / 2, camber - t / 2
        if dent and 0.015 < x < 0.12:
            yu -= 0.025 * math.sin(math.pi * (x - 0.015) / 0.105)
        up.append((x, yu))
        lo.append((x, yl))
    r = math.radians(aoa)

    def tf(p):
        x, y = p[0] * chord, -p[1] * chord
        return cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)

    pts = [tf(p) for p in up] + [tf(p) for p in reversed(lo[1:-1])]
    return polygon(pts, "surface", "fg", MAIN), [tf((x, y)) for x, y in up]


def _cl_damaged(a: float) -> float:
    if a <= 9:
        return 0.1 * (a + 2)
    if a <= 11.5:
        t = (a - 9) / 2.5
        return 1.1 + 0.08 * (1 - (1 - t) ** 2)
    return 1.18 - 0.07 * (a - 11.5) ** 1.3


@chart
def damaged_leading_edge_flow() -> Canvas:
    c = Canvas("A dented leading edge trips the flow", "Two wing sections at the same angle of attack. With a clean leading edge the airflow follows "
               "the upper surface almost to the trailing edge. With a dented leading edge, from a bird strike, the flow is tripped into "
               "turbulence and separates early, well forward on the wing. Beside them, the lift curves: the damaged wing reaches a lower maximum "
               "lift at a smaller critical angle, so it stalls at a higher speed than the POH figure, and that wing stalls first and drops.",
               height=430, prefix="dle")
    aoa = 10
    for i, (head, colour, dent) in enumerate((("Clean leading edge", "ok", False), ("Dented leading edge", "bad", True))):
        y0 = 14 + i * 170
        c.add(_panel(16, y0, 330, 158, "surface-2"))
        c.add(text(28, y0 + 24, head, 14, "start", "ok-fg" if colour == "ok" else "bad", weight=700))
        c.add(num(334, y0 + 24, f"same angle, {aoa}°", 11, "end", "fg-muted"))
        LEx, LEy = 76, y0 + 66
        shape, upper = _section(LEx, LEy, 230, aoa, dent)
        for yy in (2, 22):
            c.add(arrow(24, LEy + yy, 52, LEy + yy, "sky-fg", SECOND))
        c.add(shape)

        def offset(pts, d):
            out = []
            for k in range(1, len(pts) - 1):
                (x0, y0_), (x1, y1) = pts[k - 1], pts[k + 1]
                L = math.hypot(x1 - x0, y1 - y0_) or 1
                nx, ny = (y1 - y0_) / L, -(x1 - x0) / L
                out.append((pts[k][0] + nx * d, pts[k][1] + ny * d))
            return out

        if not dent:
            for d in (7, 20):
                pts = offset(upper, d)[4::3]
                lead = (40, pts[0][1] + 10)
                c.add(path(smooth_path([lead] + pts + [(pts[-1][0] + 26, pts[-1][1] + 6)]), "sky-fg", None, SECOND, arrow_end=True))
            c.add(text(200, y0 + 146, "flow attached almost to the trailing edge", 11, "middle", "ok-fg"))
        else:
            dx, dy = upper[4]
            c.add(circle(dx, dy, 12, None, "bad", 1.5, dash="3 2"))
            c.add(text(dx - 4, dy - 20, "dent", 12, "end", "bad", weight=600))
            pts = offset(upper, 7)[3:6]
            lead = (40, pts[0][1] + 10)
            c.add(path(smooth_path([lead] + pts), "sky-fg", None, SECOND))
            ex, ey = pts[-1]
            c.add(path(f"M{fmt(ex)} {fmt(ey)} L{fmt(ex + 250)} {fmt(ey - 16)}", "sky-fg", None, SECOND, dash=DASH, arrow_end=True))
            for fx, fr in ((0.6, 9), (0.8, 9)):
                ux, uy = upper[int(fx * 40)]
                top_y = ey - 16 * (ux - ex) / 250
                cy_ = (uy + top_y) / 2
                c.add(path(arc_path(ux, cy_, min(fr, (uy - top_y) / 2 - 2), 200, 470), "bad", None, SECOND, arrow_end=True))
            c.add(text(200, y0 + 146, "flow separates early, turbulent wake", 11, "middle", "bad"))
    # lift curves
    ch = Chart(c, (-2, 20), (0, 1.75), box=(400, 50, 610, 300), xlabel="Angle of attack", ylabel=None, xticks=[16],
               yticks=[], xfmt=lambda v: f"{int(v)}°", grid=False)
    c.add(ch.axes())
    c.add(text(372, 175, "Lift coefficient", 12, "middle", "fg-muted", weight=600, rotate=-90))
    c.add(ch.curve(sample(cl_curve, -2, 19.5, 70), "ok", MAIN))
    c.add(ch.curve(sample(_cl_damaged, -2, 17, 70), "bad", MAIN))
    c.add(ch.point(16, 1.5, "ok", 5), ch.point(11.5, 1.18, "bad", 5))
    c.add(text(ch.px(16), ch.py(1.5) - 12, "clean", 12, "middle", "ok-fg", weight=600))
    c.add(text(ch.px(11.5) - 4, ch.py(1.18) - 12, "damaged", 12, "end", "bad", weight=600))
    c.add(line(ch.px(11.5), ch.py(1.18), ch.px(11.5), ch.bottom, "bad", THIN, DASH))
    c.add(text(ch.px(11.5), ch.bottom + 16, "lower", 11, "middle", "bad"))
    c.add(multiline(400, 366, ["Lower CL max at a smaller", "critical angle: the stall speed", "rises above the POH figure."], 12, "start", "bad"))
    c.add(rect(16, 360, 330, 60, "warn-soft", None, rx=8))
    c.add(multiline(28, 380, ["One wing damaged: it stalls first and drops", "(spin risk). The stall warning may come late.",
                              "Fly faster, no steep turns, no high angles."], 12, "start", "warn-fg", leading=1.25))
    c.add(text(610, 420, "Schematic curves.", 11, "end", "fg-faint"))
    return c


# ---------------------------------------------------------------- 4.1 take-off and landing performance
@chart
def slope_force_on_runway() -> Canvas:
    c = Canvas("What a 2 percent upslope takes away", "Left, an aeroplane on an upsloping runway, the slope exaggerated. Its weight splits into a part "
               "into the runway and a part acting back down the slope, very nearly the weight times the slope: about 2 percent of the weight "
               "on a 2 percent slope. Right, the force budget on the take-off roll: thrust minus drag and rolling resistance leaves a net "
               "accelerating force that is only a modest fraction of the weight, so losing 2 percent of the weight to the slope takes a real "
               "share of it. Rule of thumb: about 10 percent more take-off distance. Landing uphill, the same force helps the brakes.",
               height=400, prefix="sfr")
    ang = 15            # drawn angle (a real 2 % slope is about 1.1 degrees)
    r = math.radians(ang)
    g0 = (24, 330)
    L = 320
    g1 = (g0[0] + L * math.cos(r), g0[1] - L * math.sin(r))
    c.add(path(f"M{g0[0]} {g0[1]} L{fmt(g1[0])} {fmt(g1[1])} L{fmt(g1[0])} {g0[1] + 14} L{g0[0]} {g0[1] + 14} Z", None, "surface-2"))
    c.add(line(*g0, *g1, "fg-muted", MAIN))
    c.add(text(20, 34, "Uphill: part of the weight pulls back", 15, "start", "fg", weight=700))
    ux, uy = math.cos(r), -math.sin(r)          # up-slope unit vector
    nx, ny = -math.sin(r), -math.cos(r)         # normal, away from the ground
    sc = 1.1
    d = 190
    bx, by = g0[0] + d * ux, g0[1] + d * uy
    wx = -7.5 * math.cos(r) + 19.5 * math.sin(r)   # main-wheel contact, local (-7.5, 19.5), pitched up the slope
    wy = 7.5 * math.sin(r) + 19.5 * math.cos(r)
    CGx, CGy = bx - wx * sc, by - wy * sc          # main wheel on the slope
    c.add(plane_side(CGx, CGy, sc, "fg", pitch=ang))
    c.add(arrow(CGx + ux * 46 + nx * 30, CGy + uy * 46 + ny * 30, CGx + ux * 104 + nx * 30, CGy + uy * 104 + ny * 30, "brand", MAIN))
    c.add(text(CGx + ux * 76 + nx * 46, CGy + uy * 76 + ny * 46, "thrust", 12, "middle", "brand", weight=600))
    c.add(arrow(CGx - ux * 50 + nx * 50, CGy - uy * 50 + ny * 50, CGx - ux * 100 + nx * 50, CGy - uy * 100 + ny * 50, "bad", 2.5))
    c.add(multiline(CGx - ux * 104 + nx * 72, CGy - uy * 104 + ny * 72 - 8, ["slope force,", "against thrust"], 12, "middle", "bad", weight=700))
    # the force triangle, drawn in clear sky
    OX, OY, W = 132, 66, 112
    c.add(arrow(OX, OY, OX, OY + W, "fg", 2.5))
    c.add(text(OX + 8, OY + W - 2, "weight", 12, "start", "fg", weight=700))
    along = W * math.sin(r)
    ax, ay = OX - ux * along, OY - uy * along
    c.add(arrow(OX, OY, ax, ay, "bad", 2.5))
    c.add(line(ax, ay, OX, OY + W, "fg-faint", THIN, DASH))
    c.add(text(ax - 6, ay + 16, "≈ 2% of", 11, "end", "bad", weight=700))
    c.add(text(ax - 6, ay + 30, "weight", 11, "end", "bad", weight=700))
    c.add(multiline(OX + 28, OY + 30, ["down-slope part", "of the weight"], 11, "start", "fg-muted"))
    c.add(text(20, 368, "Slope drawn far steeper than real: 2% is about 1°.", 11, "start", "fg-faint"))
    # force budget
    X0, BW = 360, 240
    c.add(text(X0, 64, "Force budget on the take-off roll", 14, "start", "fg", weight=700))
    rows = [("thrust", 1.0, "brand", 0), ("− drag and rolling resistance", 0.62, "info", 0), ("= net force (level)", 0.38, "ok", 0.62),
            ("upslope: − 2% of weight", 0.08, "bad", 0.62), ("= net force (uphill)", 0.30, "warn", 0.70)]
    for k, (lab, frac, colour, start) in enumerate(rows):
        y = 84 + k * 44
        c.add(text(X0, y + 12, lab, 12, "start", "fg" if colour in ("brand", "info") else f"{colour}-fg" if colour != "bad" else "bad", weight=600))
        c.add(rect(X0 + start * BW, y + 18, frac * BW, 14, colour, None, rx=3))
    c.add(rect(X0 - 8, 312, BW + 32, 50, "bad-soft", None, rx=8))
    c.add(multiline(X0 + 4, 332, ["A small slice of a small surplus:", "about +10% take-off distance"], 12, "start", "bad-fg", weight=600))
    c.add(text(20, 388, "Landing uphill, the same force helps the brakes: a shorter roll. Bars are schematic.", 12,
               "start", "fg-muted"))
    return c


@chart
def slush_drag_vs_thrust() -> Canvas:
    c = Canvas("Why slush can stop a take-off", "Force against groundspeed on the take-off roll. Propeller thrust falls as speed rises. On a dry "
               "runway drag and rolling resistance stay well below it, so the aeroplane keeps accelerating to lift-off speed. In slush, "
               "displacement and spray impingement drag grow with speed; where the slush drag meets the thrust, short of lift-off speed, "
               "the net force is zero and the aeroplane stops accelerating however much runway is left.", height=400, prefix="sdt")
    ch = Chart(c, (0, 1.12), (0, 1.25), box=(80, 50, 560, 320), xlabel="Groundspeed on the take-off roll →", ylabel="Force",
               xticks=[], yticks=[], grid=False)
    c.add(ch.axes())
    thrust = lambda v: 1.0 - 0.32 * v
    dry = lambda v: 0.12 + 0.28 * v * v
    slush = lambda v: 0.16 + 1.15 * v * v
    vlof = 1.0
    meet = 0.0
    for i in range(1000):
        v = i / 1000
        if slush(v) >= thrust(v):
            meet = v
            break
    c.add(ch.vline(vlof, "fg-muted", DASH))
    c.add(text(ch.px(vlof), ch.top - 8, "lift-off speed", 12, "middle", "fg-muted", weight=600))
    c.add(ch.area(sample(thrust, 0, vlof, 30), "ok", 0.0))
    area = [(v, thrust(v)) for v, _ in sample(thrust, 0, vlof, 40)] + [(v, dry(v)) for v, _ in reversed(sample(thrust, 0, vlof, 40))]
    c.add(path("M" + " L".join(f"{fmt(ch.px(x))} {fmt(ch.py(y))}" for x, y in area) + " Z", None, "ok", 0, fill_opacity=0.12))
    c.add(ch.curve(sample(thrust, 0, 1.08, 30), "fg", MAIN))
    c.add(ch.curve(sample(dry, 0, 1.08, 40), "ok", MAIN))
    c.add(ch.curve(sample(slush, 0, 0.84, 40), "bad", 2.5))
    c.add(text(ch.px(0.02), ch.py(thrust(0)) + 58, "propeller thrust: falls with speed", 12, "start", "fg", weight=600))
    c.add(text(ch.px(1.08) + 6, ch.py(dry(1.08)) + 4, "dry", 12, "start", "ok-fg", weight=700))
    c.add(multiline(ch.px(1.08) + 6, ch.py(dry(1.08)) + 20, ["drag +", "rolling", "resistance"], 11, "start", "ok-fg"))
    c.add(text(ch.px(0.86) + 4, ch.py(slush(0.84)) + 6, "slush drag", 13, "start", "bad", weight=700))
    c.add(text(ch.px(0.86) + 4, ch.py(slush(0.84)) + 22, "grows with speed", 11, "start", "bad"))
    c.add(ch.point(meet, thrust(meet), "bad", 6))
    c.add(ch.callout(meet, thrust(meet), -60, -80, ["net force zero:", "stops accelerating here"], "bad", 12))
    mid = (ch.px(meet) + ch.px(vlof)) / 2
    Y = ch.py(0.07)
    c.add(arrow(mid, Y, ch.px(meet), Y, "bad", SECOND), arrow(mid, Y, ch.px(vlof), Y, "bad", SECOND))
    c.add(text(mid, Y - 8, "never reached", 11, "middle", "bad", weight=600))
    c.add(text(ch.px(0.04), ch.py(0.56), "net force on a dry runway", 11, "start", "ok-fg"))
    c.add(text(20, 388, "Schematic. Most light-aircraft POHs give no slush figures: that absence is the answer.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 4.2 aircraft limitations
@chart
def flap_load_vs_speed() -> Canvas:
    c = Canvas("Flap load grows with the square of speed", "Air load on extended flap, as a percentage of the most it is designed for at VFE, "
               "against indicated airspeed, for a hypothetical aeroplane with a full-flap VFE of 95 knots. The load rises with the square of "
               "the speed: at 95 knots it is 100 percent; at 112 knots, 1.18 times VFE, it is 1.18 squared, 139 percent, 39 percent more than "
               "the design load.", height=380, prefix="flv")
    ch = Chart(c, (55, 120), (0, 165), box=(80, 40, 600, 300), xlabel="Indicated airspeed (kt)", ylabel="Load on the flap (% of design)",
               xticks=[60, 70, 80, 95, 112], yticks=[50, 100, 139], yfmt=lambda v: f"{int(v)}%")
    c.add(ch.band(95, 120, "bad", 0.10))
    c.add(ch.axes())
    load = lambda v: (v / 95) ** 2 * 100
    c.add(ch.curve(sample(load, 55, 95, 30), "brand", 2.5))
    c.add(ch.curve(sample(load, 95, 118, 20), "bad", 2.5))
    c.add(ch.hline(100, "fg-muted", DASH))
    c.add(ch.guide(112, load(112), "bad"))
    c.add(ch.point(95, 100, "brand", 6))
    c.add(ch.point(112, load(112), "bad", 6))
    c.add(ch.callout(95, 100, -24, 78, ["VFE 95 kt (full flap):", "100% of design load"], "brand", 12))
    c.add(ch.callout(112, load(112), -24, -22, ["112 kt"], "bad", 12))
    c.add(text(ch.px(107.5), ch.py(20), "above VFE", 13, "middle", "bad", weight=700))
    c.add(rect(100, 56, 254, 66, "bad-soft", None, rx=8))
    c.add(multiline(112, 76, ["112 ÷ 95 = 1.18", "1.18² = 1.39: about 39% more load", "for 17 kt that hardly shows on the dial"], 12, "start",
                    "bad-fg", cls="num"))
    c.add(text(20, 366, "Hypothetical aeroplane from the lesson; use your POH's VFE for each flap stage.", 12, "start",
               "fg-muted"))
    return c


@chart
def go_around_flap_retraction() -> Canvas:
    c = Canvas("Go-around: flap up in stages", "Side view of a go-around from a full-flap approach. Raising all the flap at once removes its extra "
               "lift: the stall speed jumps towards the clean figure while the aeroplane is still slow, and it sinks towards the ground. "
               "Flown properly: first full power and climb attitude together, then the first, high-drag stage of flap once climbing, then "
               "accelerate and raise the rest in stages at the POH speeds, keeping below VFE until the flap is up.", height=440, prefix="gaf")
    GY = 340
    c.add(_ground(20, 620, GY, 16))
    c.add(rect(150, GY - 3, 360, 6, "fg-muted", None))
    c.add(text(330, GY + 30, "runway", 11, "middle", "fg-muted"))
    LOW = (190, 290)
    c.add(path(smooth_path([(30, 170), (110, 236), LOW]), "fg-muted", None, MAIN))
    c.add(text(34, 160, "full-flap approach", 12, "start", "fg-muted", weight=600))
    good = [LOW, (240, 284), (300, 262), (380, 222), (470, 170), (610, 92)]
    c.add(path(smooth_path(good), "ok", None, 2.5))
    bad = [LOW, (232, 306), (270, 322), (300, 330)]
    c.add(path(smooth_path(bad), "bad", None, MAIN, dash="6 4", arrow_end=True))
    c.add(multiline(306, 306, ["ALL flap up at once: lift lost,", "stall speed jumps, it SINKS"], 12, "start", "bad", weight=700))
    c.add(plane_side(LOW[0] - 18, LOW[1] - 16, 0.4, "fg", pitch=-2))       # on the approach, just short of step 1
    steps = [((205, 287), "1", ["Full power and climb", "attitude, together"], (16, 292, 146), (162, 308)),
             ((300, 262), "2", ["Climbing: first stage", "up (the high-drag one)"], (220, 166, 172), (300, 210)),
             ((470, 170), "3", ["Accelerate; the rest of", "the flap up in stages"], (310, 56, 172), (440, 100))]
    for (x, y), n, lines, (bx, by, bw), (lx, ly) in steps:
        c.add(line(x, y, lx, ly, "fg-faint", THIN))
        c.add(circle(x, y, 11, "surface", "ok", 2))
        c.add(text(x, y + 4, n, 12, "middle", "ok-fg", weight=700))
        c.add(rect(bx, by, bw, 44, "ok-soft", None, rx=8))
        c.add(multiline(bx + 10, by + 18, lines, 12, "start", "ok-fg"))
    c.add(plane_side(562, 112, 0.4, "fg", pitch=12))
    c.add(rect(400, 236, 220, 60, "warn-soft", None, rx=8))
    c.add(multiline(412, 256, ["Hold the attitude: at full power", "it can run past VFE (or VFO) with", "flap still down."], 12, "start", "warn-fg"))
    c.add(text(20, 420, "POH order and speeds: each stage up only when climbing, safely above its stall speed.", 12, "start",
               "fg-muted"))
    return c
