"""BAKC 4.1 to 6.4: aerodynamics, wake and thrust-stream turbulence, charts and documents, airworthiness,
performance, speed limits and weight and balance. Numbers come from the notes in content/notes/BAKC/."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, aerofoil, angle_mark, arc_path, arrow, badge, callout, circle, ellipse,
                                fmt, group, line, multiline, num, path, plane_rear, plane_side, plane_top, polygon, polyline, rect, runway,
                                sample, smooth_path, text)


def unit(deg: float) -> tuple[float, float]:
    """Screen unit vector for a direction given in degrees anticlockwise from +x (maths convention, y up)."""
    r = math.radians(deg)
    return math.cos(r), -math.sin(r)


def vec(x: float, y: float, deg: float, length: float, color: str = "brand", **kw) -> str:
    ux, uy = unit(deg)
    return arrow(x, y, x + ux * length, y + uy * length, color, **kw)


def box(x: float, y: float, w: float, h: float, title: str, lines: list[str], color: str = "surface-2", title_color: str = "fg",
        size: float = 12, title_size: float = 13, stroke: str | None = "line") -> str:
    """Rounded panel with a bold title and a few lines of text."""
    fill = f"{color}-soft" if color in ("brand", "ok", "warn", "bad", "info", "sky") else color
    out = rect(x, y, w, h, fill, stroke, THIN, rx=8)
    out += text(x + 12, y + 20, title, title_size, "start", title_color, weight=700)
    out += multiline(x + 12, y + 20 + title_size * 1.35, lines, size, "start", "fg-muted" if title_color == "fg" else title_color, leading=1.3)
    return out


# ---------------------------------------------------------------- 4.3 climbing (shared with RBKA)
@chart
def forces_in_a_climb() -> Canvas:
    g = 15  # climb angle, exaggerated for clarity
    c = Canvas("Forces in a steady climb", "A climbing aeroplane with lift perpendicular to the flight path, thrust along it, drag opposite it and weight "
               "vertical. Weight splits into a part along the path, W sin of the climb angle, which adds to drag, and a part across it, W cos of the "
               "climb angle, which lift balances. So thrust must equal drag plus W sin gamma, and lift is a little less than weight.", height=420, prefix="fic")
    CX, CY = 360, 200
    W = 140
    t = math.tan(math.radians(g))
    s, co = math.sin(math.radians(g)), math.cos(math.radians(g))
    py_at = lambda x: CY + (CX - x) * t
    # flight path, horizontal reference and the climb angle at the left
    c.add(line(30, py_at(30), 620, py_at(620), "line-strong", THIN, DASH))
    c.add(text(612, py_at(612) + 22, "flight path", 12, "end", "fg-faint", rotate=-g))
    hx = 50
    c.add(line(hx, py_at(hx), hx + 170, py_at(hx), "fg-faint", THIN, DASH))
    c.add(path(arc_path(hx, py_at(hx), 104, -g, 0), "fg-muted", None, SECOND))
    c.add(text(hx + 116, py_at(hx) - 8, "γ", 15, "start", "fg-muted", weight=700))
    c.add(text(hx, py_at(hx) + 20, "climb angle γ, measured from the horizontal", 12, "start", "fg-muted"))
    # aeroplane pitched along the path
    c.add(plane_side(CX, CY, 1.5, pitch=g))
    # weight and its components
    c.add(arrow(CX, CY, CX, CY + W, "info", MAIN))
    c.add(text(CX - 10, CY + W - 6, "Weight W", 14, "end", "info", weight=700))
    acx, acy = CX + s * W * co, CY + co * W * co
    c.add(line(CX, CY, acx, acy, "info", SECOND, DASH, arrow_end=True))
    c.add(line(acx, acy, CX, CY + W, "fg-faint", THIN, DASH))
    c.add(text(acx + 8, acy + 4, "W cos γ", 13, "start", "info", weight=600))
    # lift perpendicular to the path, equal to W cos g, drawn from the high wing (local y -21.5, straight above the CG)
    wr = 21.5 * 1.5
    wx_, wy_ = CX - s * wr, CY - co * wr
    lx, ly = wx_ - s * W * co, wy_ - co * W * co
    c.add(arrow(wx_, wy_, lx, ly, "brand", MAIN))
    c.add(text(lx - 10, ly + 8, "Lift = W cos γ", 14, "end", "brand", weight=700))
    # drag rearward from behind the tail, then W sin g continuing rearward; thrust forward equal to both
    D = 64
    sx0, sy0 = CX - 96 * co, CY + 96 * s
    ex, ey = sx0 - co * D, sy0 + s * D
    c.add(arrow(sx0, sy0, ex, ey, "fg-muted", MAIN))
    c.add(text((sx0 + ex) / 2 + 10, (sy0 + ey) / 2 - 12, "Drag", 13, "middle", "fg-muted", weight=600))
    fx, fy = ex - co * W * s, ey + s * W * s
    c.add(arrow(ex, ey, fx, fy, "info", MAIN, dash=DASH))
    c.add(text((ex + fx) / 2 + 6, (ey + fy) / 2 - 12, "W sin γ", 13, "middle", "info", weight=600))
    T = D + W * s
    tx0, ty0 = CX + 92 * co, CY - 92 * s
    c.add(arrow(tx0, ty0, tx0 + co * T, ty0 - s * T, "ok", MAIN))
    c.add(text(tx0 + co * T / 2 + 6, ty0 - s * T / 2 + 26, "Thrust", 14, "middle", "ok", weight=700))
    # the two balances
    c.add(rect(400, 296, 226, 104, "brand-soft", None, rx=8))
    c.add(text(412, 318, "Steady climb: forces balance", 13, "start", "brand-fg", weight=700))
    c.add(num(412, 340, "Thrust = Drag + W sin γ", 13, "start", "brand-fg", weight=600))
    c.add(num(412, 360, "Lift   = W cos γ  (< W)", 13, "start", "brand-fg", weight=600))
    c.add(text(412, 384, "Excess thrust (T − D) sets the angle", 12, "start", "brand-fg"))
    c.add(multiline(20, 356, ["Weight still acts straight down, but part of it", "now pulls back along the path like extra drag."], 13, "start", "fg-muted"))
    c.add(text(20, 406, "Angle exaggerated for clarity.", 11, "start", "fg-faint"))
    return c


# ---------------------------------------------------------------- 6.3 speed limitations (shared with RBKA)
ASI = {"VS0": 45, "VS1": 50, "VFE": 85, "VA": 100, "VNO": 125, "VNE": 160}


@chart
def asi_colour_arcs() -> Canvas:
    c = Canvas("Airspeed indicator colour arcs", "An airspeed indicator with example speeds: white arc from VS0 to VFE (flap operating range), green arc "
               "from VS1 to VNO (normal operating range), yellow arc from VNO to VNE (caution: smooth air only), red line at VNE. VA is not "
               "marked on the dial.", height=400, prefix="asi")
    CX, CY, R = 180, 196, 132
    ang = lambda v: -90 + v * 1.5          # 0 kt at the top, clockwise
    pol = lambda v, r: (CX + math.cos(math.radians(ang(v))) * r, CY + math.sin(math.radians(ang(v))) * r)
    c.add(circle(CX, CY, R + 8, "surface-2", "fg", MAIN))

    def band(v0, v1, r, w, fill, stroke=None):
        out = path(arc_path(CX, CY, r, ang(v0), ang(v1)), fill, None, w).replace('stroke-linecap="round"', 'stroke-linecap="butt"')
        if stroke:
            out += path(arc_path(CX, CY, r + w / 2, ang(v0), ang(v1)), stroke, None, 1) + path(arc_path(CX, CY, r - w / 2, ang(v0), ang(v1)), stroke, None, 1)
            for v in (v0, v1):
                out += line(*pol(v, r - w / 2), *pol(v, r + w / 2), stroke, 1)
        return out
    c.add(band(ASI["VS1"], ASI["VNO"], R - 8, 13, "ok"))
    c.add(band(ASI["VNO"], ASI["VNE"], R - 8, 13, "warn"))
    c.add(band(ASI["VS0"], ASI["VFE"], R - 23, 9, "surface", "fg-muted"))
    c.add(line(*pol(ASI["VNE"], R - 30), *pol(ASI["VNE"], R + 2), "bad", 5, cap="butt"))
    for v in range(20, 201, 10):
        major = v % 20 == 0
        c.add(line(*pol(v, R - (44 if major else 38)), *pol(v, R - 30), "fg", SECOND if major else THIN, cap="butt"))
        if major and v <= 180:
            x, y = pol(v, R - 58)
            c.add(num(x, y + 5, str(v), 12, "middle", "fg", weight=600))
    c.add(text(CX, CY - 40, "AIRSPEED", 11, "middle", "fg-muted", weight=600))
    c.add(text(CX, CY - 26, "KNOTS", 11, "middle", "fg-muted"))
    c.add(line(*pol(110 + 180 / 1.5, 18), *pol(110, R - 48), "fg", 4))
    c.add(circle(CX, CY, 8, "fg", None))

    def lab(key, dr, color, anchor, dx=0, dy=0):
        v = ASI[key]
        x0, y0 = pol(v, R + 10)
        x1, y1 = pol(v, R + dr)
        x1, y1 = x1 + dx, y1 + dy
        return line(x0, y0, x1, y1, "fg-faint", THIN) + num(x1 + (5 if anchor == "start" else -5), y1 + 5, f"{key} {v}", 13, anchor, color, weight=700)
    c.add(lab("VS0", 26, "fg", "start", 0, -8))
    c.add(lab("VS1", 26, "ok-fg", "start", 4, 8))
    c.add(lab("VFE", 22, "fg", "start"))
    c.add(lab("VNO", 22, "warn-fg", "start", 4, 6))
    c.add(lab("VNE", 22, "bad", "end", 30, 28))
    X = 418
    rows = [("surface", "White arc  VS0 → VFE", ["Flap operating range: full-flap", "stall at max weight up to VFE"]),
            ("ok", "Green arc  VS1 → VNO", ["Normal operating range: clean", "stall up to max structural cruise"]),
            ("warn", "Yellow arc  VNO → VNE", ["Caution range: smooth air only,", "and then with caution"]),
            ("bad", "Red line  VNE", ["Never exceed: a limit, not a target"])]
    y = 36
    for fill, head, body in rows:
        c.add(rect(X, y - 10, 16, 12, fill, "fg-muted" if fill == "surface" else None, THIN))
        c.add(text(X + 24, y + 1, head, 13, "start", "fg", weight=700))
        c.add(multiline(X + 24, y + 19, body, 11, "start", "fg-muted"))
        y += 22 + 15 * len(body) + 16
    c.add(rect(X - 4, y - 12, 214, 64, "surface-2", None, rx=8))
    c.add(text(X + 6, y + 6, "VA is not marked on the dial", 12, "start", "fg", weight=700))
    c.add(multiline(X + 6, y + 24, ["e.g. 100 kt: slow to it in rough air.", "It is lower at lower weight."], 11, "start", "fg-muted"))
    c.add(text(20, 388, "Example speeds for a light trainer, not your aeroplane: always use the POH.", 11, "start", "fg-faint"))
    return c


# ---------------------------------------------------------------- 4.1 basic aerodynamics
AF = "M0 0 C8 -14 40 -16 100 -2 C60 4 20 8 0 0 Z"


def _bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def _interp(pts, x):
    pts = sorted(pts)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / ((x1 - x0) or 1)
    return pts[-1][1]


def af_point(lx: float, ly: float, x: float, y: float, chord: float, angle: float) -> tuple[float, float]:
    """Local aerofoil coordinates (0..100 along the chord) to the canvas, matching svg.aerofoil()."""
    k = chord / 100
    px, py = (lx - 25) * k, ly * k
    a = math.radians(angle)
    return x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)


def camber_line(n: int = 40) -> list[tuple[float, float]]:
    up = [_bez((0, 0), (8, -14), (40, -16), (100, -2), i / 200) for i in range(201)]
    lo = [_bez((100, -2), (60, 4), (20, 8), (0, 0), i / 200) for i in range(201)]
    xs = [100 * (1 - math.cos(math.pi * i / n)) / 2 for i in range(n + 1)]
    return [(x, (_interp(up, x) + _interp(lo, x)) / 2) for x in xs]


def wing_section(X: float, Y: float, chord: float, aoa: float, color: str = "fg", fill: str = "surface"):
    """The shared aerofoil, mirrored so the leading edge faces right (the aeroplane flies left to right) and pitched
    nose-up by `aoa` (svg.aerofoil pitches leading-edge-up for a positive angle; the mirror keeps that sense).
    Returns (markup, mapper from local aerofoil coordinates to the canvas)."""
    k = chord / 100
    markup = group(aerofoil(X, Y, chord, aoa, color, fill, MAIN / k), transform=f"translate({fmt(2 * X)} 0) scale(-1 1)")

    def P(lx: float, ly: float) -> tuple[float, float]:
        x, y = af_point(lx, ly, X, Y, chord, aoa)
        return 2 * X - x, y
    return markup, P


@chart
def aerofoil_terminology() -> Canvas:
    c = Canvas("Aerofoil terminology", "A cambered aerofoil section, flying to the right, with its leading edge, trailing edge, chord line, mean camber line "
               "and camber; the relative airflow meets it at the angle of attack, the angle between the chord line and the relative airflow. Lift acts "
               "through the centre of pressure at right angles to the relative airflow. An inset shows span and chord on a wing seen from above.",
               height=420, prefix="aft")
    X, Y, CH, A = 395, 210, 380, 8
    sec, P = wing_section(X, Y, CH, A)
    LE, TE = P(0, 0), P(100, -2)
    ux, uy = (LE[0] - TE[0]) / CH, (LE[1] - TE[1]) / CH          # unit vector along the chord, towards the nose
    c.add(text(20, 32, "A wing section flying to the right: the words the exam uses", 14, "start", "fg", weight=700))
    # relative airflow from the right
    for yy in (120, 300, 340):
        c.add(arrow(620, yy, 548, yy, "sky-fg", SECOND))
    c.add(text(620, 104, "Relative airflow", 13, "end", "sky-fg", weight=700))
    c.add(text(620, 362, "parallel and opposite", 11, "end", "sky-fg"))
    c.add(text(620, 376, "to the flight path", 11, "end", "sky-fg"))
    # chord line extended ahead of the leading edge, and the airflow direction through the leading edge
    c.add(line(TE[0] - ux * 30, TE[1] - uy * 30, LE[0] + ux * 120, LE[1] + uy * 120, "fg-muted", THIN, DASH))
    c.add(line(LE[0], LE[1], LE[0] + 140, LE[1], "sky-fg", THIN, DASH))
    c.add(sec)
    cam = [P(x, y) for x, y in camber_line()]
    c.add(path(smooth_path(cam), "info", None, SECOND, "6 4"))
    # angle of attack
    c.add(path(arc_path(LE[0], LE[1], 112, -A, 0), "brand", None, 3))
    c.add(multiline(LE[0] + 36, LE[1] + 28, ["Angle of", "attack"], 14, "start", "brand", weight=700))
    c.add(multiline(LE[0] + 36, LE[1] + 66, ["chord line to", "relative airflow"], 11, "start", "brand"))
    # labels
    c.add(callout(LE[0] - 2, LE[1] - 2, LE[0] - 10, LE[1] - 70, "Leading edge", "fg", 13))
    c.add(callout(TE[0] - 2, TE[1] - 2, TE[0] - 40, TE[1] - 44, "Trailing edge", "fg", 13, anchor="middle"))
    q = (TE[0] + ux * CH * 0.62, TE[1] + uy * CH * 0.62)
    c.add(callout(q[0], q[1] + 1, q[0] - 30, q[1] + 66, "Chord line: leading edge to trailing edge", "fg-muted", 12))
    cm = P(52, _interp(camber_line(), 52))
    c.add(callout(cm[0], cm[1], cm[0] - 50, 118, ["Mean camber line: halfway between", "the upper and lower surfaces"], "info", 12, anchor="end"))
    # camber: greatest gap between chord line and mean camber line
    mx = max(camber_line(), key=lambda p: -(p[1] + 0.02 * p[0]))
    top, base = P(mx[0], mx[1]), P(mx[0], -0.02 * mx[0])
    c.add(line(top[0], top[1], base[0], base[1], "info", 3, cap="butt"))
    c.add(callout(base[0], base[1] + 2, base[0] + 30, base[1] + 74, "Camber", "info", 13))
    # centre of pressure and lift
    cp = P(30, -0.6)
    c.add(arrow(cp[0], cp[1], cp[0], cp[1] - 130, "fg", MAIN))
    c.add(circle(cp[0], cp[1], 4, "fg", "surface", 1.5))
    c.add(text(cp[0] - 10, cp[1] - 118, "Lift: at right angles", 12, "end", "fg", weight=600))
    c.add(text(cp[0] - 10, cp[1] - 103, "to the relative airflow", 12, "end", "fg"))
    c.add(text(cp[0] - 10, cp[1] - 88, "through the CP", 12, "end", "fg"))
    # inset: span and chord in plan view
    ix, iy = 40, 330
    c.add(rect(ix - 20, iy - 26, 236, 108, "surface-2", None, rx=8))
    c.add(rect(ix, iy + 2, 180, 26, "surface", "fg", SECOND, rx=3))
    c.add(text(ix + 90, iy - 10, "span: tip to tip", 11, "middle", "fg-muted"))
    c.add(line(ix, iy - 4, ix + 180, iy - 4, "fg-muted", THIN, arrow_end=True, arrow_start=True))
    c.add(line(ix + 192, iy + 2, ix + 192, iy + 28, "fg-muted", THIN, arrow_end=True, arrow_start=True))
    c.add(text(ix + 172, iy + 19, "chord", 11, "end", "fg-muted"))
    c.add(text(ix, iy + 48, "Aspect ratio = span ÷ average chord;", 11, "start", "fg-muted"))
    c.add(text(ix, iy + 64, "long, slender wings: less induced drag", 11, "start", "fg-muted"))
    return c


@chart
def four_forces_level_flight() -> Canvas:
    c = Canvas("The four forces in straight and level flight", "Lift up through the centre of pressure, weight down through the centre of gravity, thrust "
               "forward along the thrust line and drag rearward. In steady straight and level flight lift equals weight and thrust equals drag. The centre "
               "of pressure is behind the centre of gravity, so lift and weight make a nose-down couple that a small tailplane force balances.",
               height=400, prefix="ffl")
    CX, CY = 300, 200
    c.add(plane_side(CX, CY, 2.4))
    L = 130
    cp, wy = CX - 10, CY - 48          # centre of pressure on the high wing, a little behind the CG (local x 0)
    c.add(arrow(cp, wy, cp, wy - L, "brand", MAIN))
    c.add(text(cp + 12, wy - L + 20, "Lift", 15, "start", "brand", weight=700))
    c.add(text(cp + 12, wy - L + 36, "through the CP, at right angles to the airflow", 12, "start", "brand"))
    c.add(arrow(CX, CY, CX, CY + L, "info", MAIN))
    c.add(text(CX - 12, CY + L - 14, "Weight", 15, "end", "info", weight=700))
    c.add(text(CX - 12, CY + L + 2, "through the CG, vertically down", 12, "end", "info"))
    c.add(circle(CX, CY, 5, "surface", "fg", 2))
    c.add(text(CX - 9, CY + 5, "CG", 12, "end", "fg", weight=700))
    c.add(circle(cp, wy, 4, "brand", None))
    # thrust from the propeller forward, drag rearward
    T = 110
    c.add(arrow(CX + 138, CY, CX + 138 + T, CY, "fg", MAIN))
    c.add(text(CX + 138 + T / 2, CY - 12, "Thrust", 15, "middle", "fg", weight=700))
    c.add(arrow(CX - 150, CY - 4, CX - 150 - T, CY - 4, "fg-muted", MAIN))
    c.add(text(CX - 150 - T / 2, CY - 16, "Drag", 15, "middle", "fg-muted", weight=700))
    c.add(text(CX - 150 - T / 2, CY + 16, "parallel to the airflow", 11, "middle", "fg-muted"))
    # tailplane balancing force
    tx = CX - 116
    c.add(arrow(tx, CY + 8, tx, CY + 44, "warn", SECOND))
    c.add(multiline(tx - 8, CY + 62, ["small tailplane force", "balances the couple"], 11, "middle", "warn-fg"))
    c.add(rect(400, 300, 226, 82, "brand-soft", None, rx=8))
    c.add(text(412, 322, "Steady, straight and level", 13, "start", "brand-fg", weight=700))
    c.add(num(412, 344, "Lift   = Weight", 13, "start", "brand-fg", weight=600))
    c.add(num(412, 364, "Thrust = Drag", 13, "start", "brand-fg", weight=600))
    c.add(multiline(20, 362, ["CP behind CG: lift and weight form a nose-down", "couple; the tailplane balances it."], 12, "start", "fg-muted"))
    return c


@chart
def angle_of_attack_vs_attitude() -> Canvas:
    c = Canvas("Angle of attack is not pitch attitude", "Worked example: nose 10 degrees above the horizon, flight path climbing at 6 degrees, so the relative "
               "airflow comes from 6 degrees above the horizontal ahead and the angle of attack is about 10 minus 6, 4 degrees.", height=360, prefix="aoa")
    PX, PY = 110, 270
    c.add(line(30, PY, 620, PY, "fg-faint", THIN, DASH))
    c.add(text(612, PY - 8, "horizon", 12, "end", "fg-faint"))

    def at(deg, r):
        ux, uy = unit(deg)
        return PX + ux * r, PY + uy * r
    c.add(line(PX, PY, *at(10, 530), "fg-muted", SECOND, DASH))
    x, y = at(10, 530)
    c.add(text(x, y - 10, "longitudinal axis (nose)", 12, "end", "fg-muted"))
    c.add(line(PX, PY, *at(6, 530), "sky-fg", MAIN))
    x, y = at(6, 530)
    c.add(text(x, y + 22, "flight path", 12, "end", "sky-fg", weight=600))
    # relative airflow arrows just below the path, pointing back at the aeroplane
    for r in (380, 480):
        x0, y0 = at(6, r + 70)
        x1, y1 = at(6, r)
        c.add(arrow(x0, y0 + 20, x1, y1 + 20, "sky-fg", SECOND))
    c.add(text(612, PY + 20, "relative airflow", 12, "end", "sky-fg", weight=600))
    c.add(plane_side(PX, PY, 1.3, pitch=10))
    # the three angles
    c.add(path(arc_path(PX, PY, 200, -10, 0), "fg-muted", None, MAIN))
    c.add(text(PX + 196, PY + 20, "pitch attitude 10°", 13, "middle", "fg-muted", weight=700))
    c.add(text(PX + 196, PY + 36, "horizon to nose", 11, "middle", "fg-muted"))
    c.add(path(arc_path(PX, PY, 340, -6, 0), "sky-fg", None, MAIN))
    c.add(text(PX + 340, PY + 20, "flight path 6°", 13, "middle", "sky-fg", weight=700))
    c.add(text(PX + 340, PY + 36, "horizon to path", 11, "middle", "sky-fg"))
    c.add(path(arc_path(PX, PY, 470, -10, -6), "brand", None, 4))
    x, y = at(8, 470)
    c.add(callout(x + 2, y, x - 50, y - 120, ["Angle of attack ≈ 10° − 6° = 4°", "path to nose: well below the stall"], "brand", 13))
    c.add(text(20, 30, "The wing meets the air along the flight path, not along the horizon.", 13, "start", "fg", weight=600))
    c.add(text(20, 48, "Worked example (rigging angle ignored): nose 10° up, climbing along a 6° path.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 4.2 lift and drag
@chart
def drag_curves_vs_airspeed() -> Canvas:
    c = Canvas("Drag against airspeed", "Parasite drag rises with the square of the airspeed; induced drag falls as speed rises. Their sum, total drag, is "
               "U-shaped with its minimum where the two are equal: the speed for the best lift/drag ratio. Slower than that is the back side of the curve.",
               height=400, prefix="dcv")
    ch = Chart(c, (0.35, 2.1), (0, 3.2), box=(70, 40, 600, 330), xlabel="Airspeed  →", ylabel="Drag  →", grid=False)
    c.add(ch.band(0.35, 0.55, "bad", 0.10))
    c.add(ch.band(0.55, 1.0, "warn", 0.08))
    c.add(ch.axes())
    par = lambda v: 0.5 * v * v
    ind = lambda v: 0.5 / (v * v)
    c.add(ch.curve(sample(par, 0.42, 2.05, 60), "fg-muted", SECOND, dash="6 4"))
    c.add(ch.curve(sample(ind, 0.42, 2.05, 60), "info", SECOND, dash="6 4"))
    c.add(ch.curve(sample(lambda v: par(v) + ind(v), 0.42, 2.0, 80), "brand", 3))
    X, Y = ch.pt(1.75, par(1.75))
    c.add(text(X + 10, Y + 28, "Parasite drag", 13, "start", "fg-muted", weight=700))
    c.add(text(X + 10, Y + 44, "rises with V²", 12, "start", "fg-muted"))
    X, Y = ch.pt(1.55, ind(1.55))
    c.add(text(X, Y - 26, "Induced drag", 13, "middle", "info", weight=700))
    c.add(text(X, Y - 10, "falls as speed rises", 12, "middle", "info"))
    X, Y = ch.pt(1.45, par(1.45) + ind(1.45))
    c.add(text(X - 10, Y - 14, "Total drag", 14, "end", "brand", weight=700))
    c.add(ch.guide(1.0, 1.0, "fg-faint"))
    c.add(ch.point(1.0, 1.0, "brand", 6))
    c.add(ch.point(1.0, 0.5, "fg-muted", 4))
    mx, my = ch.pt(1.0, 1.0)
    c.add(callout(mx, my, mx + 40, my - 150, ["Minimum drag: best lift/drag", "ratio, close to best glide speed;", "here parasite = induced"], "brand", 13))
    c.add(text(ch.px(0.45), 58, "stall", 12, "middle", "bad", weight=700))
    c.add(text(ch.px(0.775), 58, "back side of the curve:", 12, "middle", "warn-fg", weight=600))
    c.add(text(ch.px(0.775), 74, "slower needs more thrust", 12, "middle", "warn-fg"))
    return c


@chart
def lift_formula_factors() -> Canvas:
    c = Canvas("What is in the lift formula", "Lift equals the lift coefficient times dynamic pressure, one half rho V squared, times the wing area. The pilot sets "
               "the lift coefficient with angle of attack and flap and the speed with power and attitude; density comes with height and temperature; "
               "wing area is fixed. At constant angle of attack, slowing from 100 to 70 knots leaves 0.49 of the lift.", height=400, prefix="lff")
    terms = [("L", "fg", 130), ("=", "fg-muted", 176), ("CL", "brand", 230), ("×", "fg-muted", 282), ("½ρ", "info", 334), ("V²", "warn-fg", 396), ("×", "fg-muted", 448), ("S", "ok-fg", 494)]
    for s_, col_, x in terms:
        c.add(text(x, 62, s_, 34, "middle", col_, weight=700, cls="num"))
    c.add(text(320, 94, "Drag has exactly the same form, with CD in place of CL.", 12, "middle", "fg-muted"))
    panels = [("brand", "Lift coefficient", ["Set by angle of", "attack, wing shape", "and flap.", "Pilot: elevator, flap."], 230),
              ("info", "Air density", ["Thinner air: less", "lift at the same", "true airspeed.", "Set by height, heat."], 334),
              ("warn", "Speed, squared", ["Double the speed:", "four times the lift.", "Pilot: power and", "attitude."], 396),
              ("ok", "Wing area", ["Fixed for the", "aeroplane."], 494)]
    xs = [20, 175, 330, 485]
    for (colr, title, body, tx), x in zip(panels, xs):
        c.add(rect(x, 130, 140, 112, f"{colr}-soft", None, rx=8))
        c.add(line(tx, 104, x + 70, 128, "fg-faint", THIN))
        c.add(text(x + 10, 151, title, 13, "start", f"{colr}-fg", weight=700))
        c.add(multiline(x + 10, 171, body, 12, "start", "fg"))
    c.add(text(20, 276, "½ρV² is the dynamic pressure: what the ASI measures, so IAS tells you it directly.", 12, "start", "fg-muted"))
    c.add(rect(20, 300, 600, 76, "surface-2", None, rx=8))
    c.add(text(32, 322, "Worked example: level flight, slowing from 100 kt to 70 kt", 13, "start", "fg", weight=700))
    c.add(num(32, 343, "Same angle of attack: lift × (70 ÷ 100)² = × 0.49", 13, "start", "warn-fg", weight=600))
    c.add(text(32, 363, "To stay level, raise the angle of attack until CL is roughly double: slow flight is nose-high.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 4.3 climbing
@chart
def climb_rate_vs_airspeed() -> Canvas:
    c = Canvas("Best angle and best rate of climb", "Rate of climb against airspeed for an example trainer: the top of the curve is Vy, best rate, about 75 knots; "
               "the steepest line from the origin touches the curve at Vx, best angle, about 60 knots. Vx is always below Vy.", height=420, prefix="crv")
    roc = lambda v: 1 - ((v - 75) / 45) ** 2
    ch = Chart(c, (0, 125), (0, 1.25), box=(70, 100, 600, 350), xlabel="Indicated airspeed (kt)", ylabel="Rate of climb (fpm)  →",
               xticks=[0, 60, 75, 100, 120], xfmt=lambda v: f"{int(v)}", grid=False)
    c.add(ch.axes())
    c.add(ch.curve(sample(roc, 40, 112, 60), "brand", 3))
    slope = roc(60) / 60
    c.add(ch.curve([(0, 0), (90, 90 * slope)], "ok", SECOND, dash="6 4", smooth=False))
    c.add(ch.guide(75, 1.0, "fg-faint"))
    c.add(ch.guide(60, roc(60), "fg-faint"))
    c.add(ch.point(75, 1.0, "brand", 6))
    c.add(ch.point(60, roc(60), "ok", 6))
    X, Y = ch.pt(75, 1.0)
    c.add(callout(X, Y, X + 56, Y - 20, ["Vy ≈ 75 kt: best rate", "most height per minute", "(excess power)"], "brand", 13))
    X, Y = ch.pt(60, roc(60))
    c.add(callout(X, Y, X - 70, Y - 100, ["Vx ≈ 60 kt: best angle", "steepest line from 0", "most height per NM", "(excess thrust)"], "ok-fg", 13))
    X, Y = ch.pt(90, 90 * slope)
    c.add(text(X + 6, Y + 18, "climb angle line", 11, "start", "ok-fg"))
    c.add(text(20, 34, "Best angle comes at a lower speed than best rate: Vx is always below Vy.", 14, "start", "fg", weight=700))
    c.add(text(20, 54, "Rate depends on excess power; angle on excess thrust.", 12, "start", "fg-muted"))
    c.add(text(600, ch.py(0.06), "Example two-seat trainer: always use your POH figures.", 11, "end", "fg-faint"))
    return c


@chart
def climb_gradient_wind() -> Canvas:
    c = Canvas("Wind changes the climb angle, not the rate", "Same aeroplane climbing at 600 feet per minute: 450 feet per nautical mile in still air at 80 knots "
               "groundspeed, 600 with a 20 knot headwind, 360 with a 20 knot tailwind. A 300 foot obstacle 1 nautical mile away is cleared by about 150 "
               "feet in still air and about 60 feet with the tailwind.", height=400, prefix="cgw")
    ch = Chart(c, (0, 1.3), (0, 750), box=(70, 40, 560, 320), xlabel="Distance from start of climb (NM)", ylabel="Height gained (ft)",
               xticks=[0, 0.5, 1.0], yticks=[0, 300, 360, 450, 600], xfmt=lambda v: fmt(v), yfmt=lambda v: f"{int(v)}")
    c.add(ch.axes())
    END = 1.1
    for grad, colr, l1, dy in ((600, "ok", "20 kt headwind", 0), (450, "brand", "still air", 0), (360, "bad", "20 kt tailwind", 6)):
        c.add(ch.curve([(0, 0), (END, END * grad)], colr, 3 if colr == "brand" else MAIN, smooth=False))
        X, Y = ch.pt(END, END * grad)
        tc = "ok-fg" if colr == "ok" else colr
        c.add(text(X + 8, Y + dy, l1, 12, "start", tc, weight=700))
        c.add(num(X + 8, Y + dy + 15, f"{grad} ft/NM", 12, "start", tc, weight=600))
    ox, oy = ch.pt(1.0, 300)
    bx = ch.py(0)
    c.add(polygon([(ox - 12, bx), (ox, oy), (ox + 12, bx)], "surface-2", "fg", SECOND))
    c.add(text(ox + 16, bx - 30, "300 ft obstacle", 12, "start", "fg", weight=600))
    c.add(text(ox + 16, bx - 14, "1 NM out", 12, "start", "fg-muted"))
    for grad, colr, lab, dx in ((450, "brand", "150 ft", -14), (360, "bad", "60 ft", 14)):
        Y = ch.py(grad)
        c.add(line(ox + dx, oy, ox + dx, Y, colr, SECOND, arrow_end=True, arrow_start=True))
    c.add(rect(86, 54, 260, 104, "surface-2", None, rx=8))
    c.add(text(98, 74, "VSI reads 600 fpm in all three", 13, "start", "fg", weight=700))
    c.add(num(98, 94, "ft/NM = fpm × 60 ÷ groundspeed", 12, "start", "fg-muted"))
    c.add(num(98, 112, "still air: 600 × 60 ÷ 80 = 450", 12, "start", "fg-muted"))
    c.add(num(98, 132, "clears the obstacle by 150 ft", 12, "start", "brand", weight=600))
    c.add(num(98, 148, "tailwind (GS 100): only 60 ft", 12, "start", "bad", weight=600))
    return c


# ---------------------------------------------------------------- 4.4 wake turbulence
@chart
def wake_turbulence_avoidance() -> Canvas:
    c = Canvas("Take-off and landing profiles that avoid wake turbulence", "Side views. Taking off behind a heavier aircraft that has just departed: its vortices "
               "start at its rotation point, so lift off before that point and climb above its flight path. Landing behind a heavier aircraft that has just "
               "landed: its vortices stop at its touchdown point, so stay at or above its approach path and touch down beyond that point.",
               height=480, prefix="wta")

    def ground(y):
        return line(30, y, 610, y, "fg-muted", 6, cap="butt")
    # --- take-off
    G1 = 200
    c.add(text(20, 28, "Taking off behind a heavier aircraft that has departed", 14, "start", "fg", weight=700))
    c.add(ground(G1))
    R = 330
    c.add(polygon([(R, G1), (610, G1 - 0.32 * (610 - R)), (610, G1 - 0.32 * (610 - R) + 70), (R + 40, G1)], "bad", None, fill_opacity=0.14))
    c.add(line(R, G1, 610, G1 - 0.32 * (610 - R), "fg-muted", MAIN, DASH))
    c.add(plane_side(560, G1 - 0.32 * 230 + 2, 0.8, "fg-muted", pitch=18))
    c.add(text(610, G1 + 30, "its wake sinks below", 12, "end", "bad", weight=600))
    c.add(text(610, G1 + 45, "and behind its path", 12, "end", "bad"))
    c.add(line(R, G1 - 4, R, G1 + 14, "bad", 3))
    c.add(text(R + 6, G1 + 30, "heavy rotates:", 12, "start", "bad", weight=600))
    c.add(text(R + 6, G1 + 45, "vortices start", 12, "start", "bad"))
    L1 = 220
    c.add(line(L1, G1, 470, G1 - 0.46 * (470 - L1), "brand", 3))
    c.add(plane_side(440, G1 - 0.46 * 220 + 1, 0.42, "brand", pitch=24))
    c.add(line(L1, G1 - 4, L1, G1 + 14, "ok", 3))
    c.add(text(L1 - 6, G1 + 30, "you lift off", 12, "end", "ok-fg", weight=600))
    c.add(text(L1 - 6, G1 + 45, "before that point", 12, "end", "ok-fg"))
    c.add(text(330, 60, "and climb above its flight path", 13, "end", "brand", weight=700))
    c.add(arrow(80, G1 - 20, 170, G1 - 20, "fg-faint", THIN))
    c.add(text(80, G1 - 30, "take-off direction", 11, "start", "fg-faint"))
    # --- landing
    G2 = 416
    c.add(text(20, 272, "Landing behind a heavier aircraft that has landed", 14, "start", "fg", weight=700))
    c.add(ground(G2))
    T = 300
    c.add(polygon([(30, G2 - 0.26 * (T - 30)), (T, G2), (30, G2)], "bad", None, fill_opacity=0.14))
    c.add(line(30, G2 - 0.26 * (T - 30), T, G2, "fg-muted", MAIN, DASH))
    c.add(plane_side(120, G2 - 0.26 * (T - 120) + 1, 0.8, "fg-muted", pitch=-2))
    c.add(line(T, G2 - 4, T, G2 + 14, "bad", 3))
    c.add(text(T - 6, G2 + 30, "heavy touches down here:", 12, "end", "bad", weight=600))
    c.add(text(T - 6, G2 + 45, "vortices stop", 12, "end", "bad"))
    TD = 410
    c.add(line(30, G2 - 0.24 * (TD - 30), TD, G2, "brand", 3))
    c.add(plane_side(260, G2 - 0.24 * (TD - 260), 0.42, "brand", pitch=-3))
    c.add(line(TD, G2 - 4, TD, G2 + 14, "ok", 3))
    c.add(text(TD + 6, G2 + 30, "you touch down", 12, "start", "ok-fg", weight=600))
    c.add(text(TD + 6, G2 + 45, "beyond that point", 12, "start", "ok-fg"))
    c.add(text(150, 316, "stay at or above its approach path", 13, "start", "brand", weight=700))
    c.add(rect(440, 290, 180, 64, "surface-2", None, rx=8))
    c.add(text(452, 310, "And always:", 12, "start", "fg", weight=700))
    c.add(text(452, 327, "stay upwind of its path;", 12, "start", "fg-muted"))
    c.add(text(452, 343, "if in doubt, wait.", 12, "start", "fg-muted"))
    return c


@chart
def wake_drift_in_crosswind() -> Canvas:
    c = Canvas("A light crosswind can hold a vortex over the runway", "Rear views of the vortices from a landing aircraft near the ground. In still air the two "
               "vortices spread outward from the runway at a few knots each. With a light crosswind from the right, about 2 knots in the worked example, "
               "the right (upwind) vortex's outward drift is cancelled and it sits over the runway, while the left vortex is carried away quickly.",
               height=360, prefix="wdc")

    def panel(x0, title, wind):
        out = rect(x0, 40, 300, 240, "surface-2", None, rx=10)
        out += text(x0 + 150, 64, title, 14, "middle", "fg", weight=700)
        gy = 230
        out += line(x0 + 10, gy, x0 + 290, gy, "fg-muted", SECOND)
        out += rect(x0 + 110, gy - 3, 80, 6, "fg-muted", None)
        out += text(x0 + 150, gy + 20, "runway", 11, "middle", "fg-faint")
        def vortex(x, y, cw, colr):
            a0 = 0 if cw else 180
            return (circle(x, y, 18, colr + "-soft" if colr in ("bad", "brand", "info") else "surface", colr, SECOND) +
                    path(arc_path(x, y, 26, a0 + 20, a0 + 200) if cw else arc_path(x, y, 26, a0 - 20, a0 - 200), colr, None, SECOND, arrow_end=True))
        if not wind:
            out += vortex(x0 + 125, 190, True, "brand") + vortex(x0 + 175, 190, False, "brand")
            out += arrow(x0 + 100, 190, x0 + 50, 190, "fg-muted", MAIN) + arrow(x0 + 200, 190, x0 + 250, 190, "fg-muted", MAIN)
            out += text(x0 + 150, 130, "each drifts outward", 12, "middle", "fg-muted")
            out += text(x0 + 150, 146, "at a few knots", 12, "middle", "fg-muted")
        else:
            out += vortex(x0 + 70, 190, True, "fg-muted") + vortex(x0 + 168, 190, False, "bad")
            out += arrow(x0 + 46, 190, x0 + 16, 190, "fg-muted", MAIN)
            out += text(x0 + 20, 160, "carried away", 12, "start", "fg-muted")
            out += text(x0 + 200, 128, "upwind vortex:", 12, "start", "bad", weight=700)
            out += text(x0 + 200, 144, "outward drift", 12, "start", "bad")
            out += text(x0 + 200, 160, "cancelled, sits", 12, "start", "bad")
            out += text(x0 + 200, 176, "over the runway", 12, "start", "bad")
            out += arrow(x0 + 290, 96, x0 + 220, 96, "sky-fg", MAIN)
            out += text(x0 + 214, 100, "light crosswind (≈ 2 kt)", 12, "end", "sky-fg", weight=600)
        return out
    c.add(panel(14, "Still air", False))
    c.add(panel(326, "Light crosswind from the right", True))
    c.add(text(20, 306, "Viewed from behind, landing direction into the page: the pilot's left is on the left.", 12, "start", "fg-muted"))
    c.add(text(20, 324, "Worked example: runway 21, wind 240/04: about 2 kt across from the right.", 12, "start", "fg-muted"))
    c.add(text(20, 342, "Calm, stable air (early morning, evening) makes vortices last longest.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 4.5 thrust stream turbulence
def jet_top(x: float, y: float, s: float = 1.0, color: str = "fg") -> str:
    """Twin-jet airliner in plan view, nose to the right, ~120 units long at s = 1."""
    body = path("M60 0 C60 -5 52 -7 44 -7 L-50 -6 L-60 -2 L-60 2 L-50 6 L44 7 C52 7 60 5 60 0 Z", color, "surface", MAIN)
    wing = path("M14 -6 L-14 -58 L-24 -58 L-10 -6 Z M14 6 L-14 58 L-24 58 L-10 6 Z", color, "surface", MAIN)
    tail = path("M-44 -5 L-58 -24 L-64 -24 L-58 -4 Z M-44 5 L-58 24 L-64 24 L-58 4 Z", color, "surface", MAIN)
    eng = rect(-6, -32, 22, 9, "surface-2", color, SECOND, rx=4) + rect(-6, 23, 22, 9, "surface-2", color, SECOND, rx=4)
    return group(wing, tail, body, eng, transform=f"translate({fmt(x)} {fmt(y)}) scale({fmt(s)})")


@chart
def jet_blast_hazard_zones() -> Canvas:
    c = Canvas("Thrust stream hazard grows with power and fades with distance", "Plan view behind a jet: the danger area behind it is shortest at idle, "
               "considerably longer at breakaway thrust and longest at take-off power, and the blast weakens gradually with distance. Behind a propeller "
               "aircraft the wash is smaller. Indicative only, not to scale; check the current AIP for any specified distances.", height=370, prefix="jbh")
    JX, JY = 520, 150
    zones = [(470, 70, "take-off power or engine run: greatest", "bad", 0.10), (300, 52, "breakaway thrust: considerably more", "warn", 0.16), (150, 34, "idle: smallest, not zero", "warn", 0.26)]
    for length, half, label, colr, op in zones:
        x0 = JX - 6
        d = f"M{x0} {JY - 20} L{x0 - length} {JY - half - 20} Q{x0 - length - 30} {JY} {x0 - length} {JY + half + 20} L{x0} {JY + 20} Z"
        c.add(path(d, None, colr, 0, fill_opacity=op))
    c.add(jet_top(JX, JY, 0.9))
    for x, l1, l2, colr, dy in ((50, "take-off power:", "greatest", "bad", 0), (222, "breakaway thrust:", "considerably more", "warn-fg", 0), (372, "idle: smallest,", "but not zero", "warn-fg", 34)):
        c.add(text(x, JY - 4 + dy, l1, 12, "start", colr, weight=700))
        c.add(text(x, JY + 12 + dy, l2, 12, "start", colr))
    c.add(arrow(500, 50, 60, 50, "fg-muted", SECOND))
    c.add(text(60, 40, "hazard falls gradually with distance", 12, "start", "fg-muted"))
    c.add(text(JX + 64, JY + 4, "jet", 12, "start", "fg-muted"))
    # propeller aircraft for comparison
    PX, PY = 520, 300
    c.add(path(f"M{PX - 22} {PY - 6} L{PX - 112} {PY - 18} Q{PX - 124} {PY} {PX - 112} {PY + 18} L{PX - 22} {PY + 6} Z", None, "warn", 0, fill_opacity=0.2))
    c.add(plane_top(PX, PY, 0.42, 90))
    c.add(text(PX - 130, PY - 4, "prop wash: run-up or taxi,", 12, "end", "warn-fg", weight=600))
    c.add(text(PX - 130, PY + 12, "smaller but real", 12, "end", "warn-fg"))
    c.add(text(20, 356, "Indicative, not to scale: the danger area depends on the aircraft and its power; check the AIP.", 11, "start", "fg-faint"))
    return c


@chart
def holding_point_position() -> Canvas:
    c = Canvas("Where to wait behind a jet at the holding point", "Plan view of a holding point. A regional jet is about to line up and will use breakaway "
               "thrust, then take-off power. Directly behind its tail is the worst place to be; the best is to the side of its tail and as far back as "
               "the taxiway allows, angled so the blast does not hit your tail or a wing broadside.", height=400, prefix="hpp")
    # runway along the top, taxiway coming up from the bottom
    c.add(rect(20, 40, 600, 50, "fg-muted", None, rx=2))
    c.add(text(32, 72, "runway", 13, "start", "surface", weight=700))
    c.add(rect(250, 90, 70, 270, "surface-2", "line-strong", THIN))
    c.add(rect(320, 250, 300, 60, "surface-2", "line-strong", THIN))
    c.add(line(250, 112, 320, 112, "warn", 3, cap="butt"))
    c.add(text(244, 117, "holding point", 12, "end", "warn-fg", weight=600))
    # the jet facing the runway, blast cone down the taxiway
    JX, JY = 285, 150
    c.add(path(f"M{JX - 18} {JY + 40} L{JX - 62} {JY + 205} Q{JX} {JY + 232} {JX + 62} {JY + 205} L{JX + 18} {JY + 40} Z", None, "bad", 0, fill_opacity=0.16))
    c.add(group(jet_top(0, 0, 0.55), transform=f"translate({JX} {JY}) rotate(-90)"))
    c.add(text(JX + 44, JY - 4, "regional jet,", 12, "start", "fg", weight=600))
    c.add(text(JX + 44, JY + 12, "cleared to line up", 12, "start", "fg"))
    c.add(text(JX, JY + 196, "blast", 12, "middle", "bad", weight=700))
    # bad position: directly behind
    c.add(plane_top(JX, JY + 150, 0.3, 0, "bad"))
    c.add(text(JX - 50, JY + 156, "directly behind:", 12, "end", "bad", weight=700))
    c.add(text(JX - 50, JY + 172, "worst place", 12, "end", "bad"))
    # good position: to the side, back, angled
    c.add(plane_top(470, 280, 0.3, 300, "ok"))
    c.add(text(470, 336, "to the side of its tail, well back,", 12, "middle", "ok-fg", weight=700))
    c.add(text(470, 352, "nose angled towards the blast", 12, "middle", "ok-fg"))
    c.add(text(20, 388, "Next: breakaway thrust as it moves, then take-off power on the runway. Hold the controls firmly.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 5.1 charts
def _mini_topo(x: float, y: float, w: float, h: float, detail: int = 1) -> str:
    """Symbolic topography: hypsometric tints, contours, a river, a road, a railway and a town."""
    out = rect(x, y, w, h, "ok-soft", None)
    out += path(f"M{x + w * 0.45} {y} C{x + w * 0.5} {y + h * 0.3} {x + w * 0.85} {y + h * 0.25} {x + w} {y + h * 0.45} L{x + w} {y} Z", None, "warn-soft")
    for k in range(detail + 1):
        o = 8 * k
        out += path(f"M{x + w * 0.45 + o} {y} C{x + w * 0.5 + o} {y + h * 0.3 - o} {x + w * 0.85} {y + h * 0.25 - o} {x + w} {y + h * 0.45 - o}", "warn", None, THIN)
    out += path(f"M{x} {y + h * 0.7} C{x + w * 0.3} {y + h * 0.55} {x + w * 0.5} {y + h * 0.95} {x + w} {y + h * 0.8}", "sky-fg", None, SECOND)
    out += line(x + w * 0.1, y + h, x + w * 0.6, y + h * 0.1, "bad", SECOND)
    out += line(x, y + h * 0.35, x + w, y + h * 0.6, "fg", THIN)
    for i in range(1, 8):
        t = i / 8
        px, py = x + w * t, y + h * (0.35 + 0.25 * t)
        out += line(px - 2, py - 4, px + 2, py + 4, "fg", THIN)
    out += circle(x + w * 0.32, y + h * 0.5, 7, "warn", "fg", THIN)
    return out


def _mini_air(x: float, y: float, w: float, h: float, steps: bool = True) -> str:
    """Symbolic airspace: a CTA step boundary and a hatched PRD area."""
    out = ""
    if steps:
        out += path(f"M{x + w * 0.62} {y} A{w * 0.38} {w * 0.38} 0 0 0 {x + w} {y + h * 0.75}", "info", None, MAIN)
        out += path(f"M{x + w * 0.8} {y} A{w * 0.2} {w * 0.2} 0 0 0 {x + w} {y + h * 0.4}", "info", None, SECOND)
    out += rect(x + w * 0.08, y + h * 0.08, w * 0.24, h * 0.3, "bad", "bad", SECOND, fill_opacity=0.15)
    out += text(x + w * 0.2, y + h * 0.27, "R", 11, "middle", "bad", weight=700)
    return out


@chart
def chart_features_panel() -> Canvas:
    c = Canvas("What each visual chart shows", "Four symbolic chart panels. WAC, 1:1,000,000: topography, towns, roads, railways, rivers, aerodromes, no "
               "airspace. VNC, 1:500,000: topography plus controlled airspace, PRD areas, frequencies and reporting points. VTC, 1:250,000: detailed "
               "topography with control zones, CTA steps, PRD areas, VFR routes and frequencies. ERC-L: airspace, air routes, navigation aids, "
               "frequencies and PRD areas with no topography.", height=470, prefix="cfp")
    cells = [(20, 40, "WAC", "1:1,000,000", "1 cm = 10 km", ["topography, towns, roads, rivers,", "aerodromes, obstacles, isogonals"], "bad", "NO AIRSPACE"),
             (330, 40, "VNC", "1:500,000", "1 cm = 5 km", ["topography + CTA, PRD areas,", "frequencies, reporting points"], "ok", "airspace"),
             (20, 250, "VTC", "1:250,000", "1 cm = 2.5 km", ["detailed topography + CTR, CTA steps,", "PRD, VFR routes and lanes, frequencies"], "ok", "airspace"),
             (330, 250, "ERC-L", "various", "", ["airspace, air routes, navaids,", "frequencies, PRD areas"], "warn", "NO TOPOGRAPHY")]
    for x, y, name, scale, cm, body, colr, tag in cells:
        c.add(rect(x, y, 290, 200, "surface-2", None, rx=10))
        c.add(text(x + 12, y + 24, name, 17, "start", "fg", weight=700))
        c.add(num(x + {"WAC": 62, "VNC": 62, "VTC": 60, "ERC-L": 82}[name], y + 24, scale, 13, "start", "fg-muted", weight=600))
        c.add(badge(x + 290 - 12 - (len(tag) * 11 * 0.62 + 14) / 2, y + 20, tag, colr, 11))
        mx, my, mw, mh = x + 12, y + 40, 266, 104
        c.add(f'<g clip-path="url(#cfp-clip-{name.lower().replace("-", "")})">')
        c.add_defs(f'<clipPath id="cfp-clip-{name.lower().replace("-", "")}"><rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="4"/></clipPath>')
        if name == "ERC-L":
            c.add(rect(mx, my, mw, mh, "surface", None))
            c.add(line(mx, my + 20, mx + mw, my + mh - 10, "fg-muted", SECOND))
            c.add(line(mx + 30, my + mh, mx + mw - 40, my, "fg-muted", SECOND))
            ix, iy = mx + 138, my + 58
            c.add(polygon([(ix - 8, iy - 5), (ix, iy - 9), (ix + 8, iy - 5), (ix + 8, iy + 5), (ix, iy + 9), (ix - 8, iy + 5)], "surface", "fg", SECOND))
            c.add(_mini_air(mx, my, mw, mh))
            c.add(rect(mx + 160, my + 70, 70, 20, "surface", "info", THIN))
            c.add(text(mx + 195, my + 84, "freq", 11, "middle", "info"))
        else:
            c.add(_mini_topo(mx, my, mw, mh, 1 if name == "WAC" else 2 if name == "VNC" else 3))
            if name != "WAC":
                c.add(_mini_air(mx, my, mw, mh))
                c.add(rect(mx + 170, my + 76, 60, 20, "surface", "info", THIN))
                c.add(text(mx + 200, my + 90, "freq", 11, "middle", "info"))
            if name == "VTC":
                c.add(path(f"M{mx} {my + 90} L{mx + 120} {my + 70} L{mx + 266} {my + 74}", "brand", None, SECOND, "6 4"))
                c.add(rect(mx + 30, my + 52, 62, 16, "surface", None, rx=3))
                c.add(text(mx + 61, my + 64, "VFR route", 11, "middle", "brand-fg"))
        c.add("</g>")
        c.add(rect(mx, my, mw, mh, None, "line-strong", THIN, rx=4))
        c.add(multiline(x + 12, y + 162, body, 12, "start", "fg-muted"))
        if cm:
            c.add(num(x + 278, y + 190, cm, 11, "end", "fg-faint"))
    c.add(text(20, 24, "The WAC is the exam's navigation chart, but it shows no airspace at all.", 13, "start", "fg", weight=600))
    c.add(text(20, 462, "Symbolic panels, not real charts: learn the legend printed on each chart.", 11, "start", "fg-faint"))
    return c


@chart
def chart_legend_symbols() -> Canvas:
    c = Canvas("Features to recognise on a visual chart", "Symbolic examples of chart features: contour lines and hypsometric tints, spot height, "
               "rivers (intermittent dashed), lakes, towns, roads, railways with cross ticks, power lines, obstacles with height above ground and "
               "elevation, lit obstacles, aerodromes, isogonals and the latitude and longitude graticule.", height=470, prefix="cls")
    tiles = []

    def tile(i, title, sub):
        col_, row = i % 3, i // 3
        x, y = 20 + col_ * 204, 44 + row * 104
        tiles.append((x, y))
        return rect(x, y, 192, 94, "surface-2", None, rx=8) + text(x + 10, y + 78, title, 12, "start", "fg", weight=700) + (text(x + 10, y + 90, sub, 11, "start", "fg-muted") if sub else ""), x, y
    # relief
    m, x, y = tile(0, "Relief: tints and contours", "")
    c.add(m, rect(x + 10, y + 10, 172, 54, "ok-soft", None, rx=3))
    c.add(path(f"M{x + 60} {y + 10} C{x + 80} {y + 40} {x + 140} {y + 40} {x + 182} {y + 30} L{x + 182} {y + 10} Z", None, "warn-soft"))
    for o in (0, 8, 16):
        c.add(path(f"M{x + 60 + o * 2} {y + 10} C{x + 80 + o} {y + 40 - o} {x + 140} {y + 40 - o} {x + 182} {y + 30 - o}", "warn", None, THIN))
    m, x, y = tile(1, "Spot height", "elevation beside the dot")
    c.add(m, circle(x + 70, y + 36, 3, "fg", None), text(x + 80, y + 40, "elevation", 11, "start", "fg-muted", italic=True))
    m, x, y = tile(2, "Rivers", "intermittent rivers dashed")
    c.add(m, path(f"M{x + 10} {y + 26} C{x + 60} {y + 10} {x + 110} {y + 40} {x + 182} {y + 24}", "sky-fg", None, MAIN))
    c.add(path(f"M{x + 10} {y + 52} C{x + 60} {y + 36} {x + 110} {y + 66} {x + 182} {y + 50}", "sky-fg", None, SECOND, "6 4"))
    m, x, y = tile(3, "Lakes", "some shown differently")
    c.add(m, ellipse(x + 55, y + 38, 34, 18, "sky-soft", "sky-fg", SECOND), ellipse(x + 140, y + 38, 34, 18, "surface", "sky-fg", SECOND))
    c.add(path(f"M{x + 116} {y + 38} L{x + 164} {y + 38} M{x + 120} {y + 30} L{x + 160} {y + 30} M{x + 120} {y + 46} L{x + 160} {y + 46}", "sky-fg", None, THIN, "3 3"))
    m, x, y = tile(4, "Towns, roads", "towns by size; roads by class")
    c.add(m, rect(x + 20, y + 18, 44, 30, "warn-soft", "warn", THIN, rx=6), circle(x + 100, y + 33, 6, "warn-soft", "warn", THIN))
    c.add(line(x + 120, y + 56, x + 182, y + 12, "bad", MAIN), line(x + 10, y + 60, x + 120, y + 56, "bad", SECOND))
    m, x, y = tile(5, "Railway", "black line with cross ticks")
    c.add(m, line(x + 10, y + 36, x + 182, y + 36, "fg", SECOND))
    for i in range(1, 12):
        c.add(line(x + 10 + i * 15, y + 30, x + 10 + i * 15, y + 42, "fg", THIN))
    m, x, y = tile(6, "Power line", "red line with symbols")
    c.add(m, line(x + 10, y + 36, x + 182, y + 36, "bad", SECOND))
    for i in range(1, 6):
        c.add(polygon([(x + i * 32 - 4, y + 40), (x + i * 32, y + 30), (x + i * 32 + 4, y + 40)], "surface", "bad", THIN))
    m, x, y = tile(7, "Obstacle; lit obstacle", "heights AGL and AMSL")
    c.add(m, polygon([(x + 50, y + 54), (x + 60, y + 22), (x + 70, y + 54)], None, "fg", SECOND), circle(x + 60, y + 44, 2.5, "fg", None))
    c.add(polygon([(x + 130, y + 54), (x + 140, y + 22), (x + 150, y + 54)], None, "fg", SECOND), circle(x + 140, y + 44, 2.5, "fg", None))
    c.add(path(f"M{x + 140} {y + 18} l-6 -6 M{x + 140} {y + 18} l0 -8 M{x + 140} {y + 18} l6 -6", "warn", None, SECOND))
    m, x, y = tile(8, "Aerodrome", "symbol shows sealed or not")
    c.add(m, circle(x + 70, y + 36, 16, "surface", "info", MAIN), line(x + 58, y + 44, x + 82, y + 28, "info", 4))
    c.add(circle(x + 130, y + 36, 16, "surface", "info", MAIN), line(x + 118, y + 44, x + 142, y + 28, "info", 4, cap="butt"))
    c.add(line(x + 118, y + 44, x + 142, y + 28, "surface", 1.5, "3 3"))
    m, x, y = tile(9, "Isogonal", "magnetic variation, dashed")
    c.add(m, path(f"M{x + 20} {y + 60} C{x + 70} {y + 40} {x + 110} {y + 30} {x + 180} {y + 14}", "brand", None, SECOND, "8 5"))
    c.add(text(x + 96, y + 30, "1°W", 12, "middle", "brand-fg", weight=700, cls="num"))
    m, x, y = tile(10, "Graticule", "lat and long, minute ticks")
    c.add(m, line(x + 10, y + 36, x + 182, y + 36, "fg-muted", SECOND), line(x + 96, y + 8, x + 96, y + 64, "fg-muted", SECOND))
    for i in range(-7, 8):
        if i:
            c.add(line(x + 96 + i * 11, y + 33, x + 96 + i * 11, y + 39, "fg-muted", THIN))
            c.add(line(x + 93, y + 36 + i * 3.6, x + 99, y + 36 + i * 3.6, "fg-muted", THIN))
    m, x, y = tile(11, "Airspace and PRD", "not on the WAC")
    c.add(m, path(f"M{x + 60} {y + 8} A70 70 0 0 0 {x + 130} {y + 66}", "info", None, MAIN))
    c.add(rect(x + 120, y + 12, 52, 36, "bad", "bad", SECOND, fill_opacity=0.15), text(x + 146, y + 35, "R155", 11, "middle", "bad", weight=700, cls="num"))
    c.add(text(20, 28, "Symbolic examples: learn the legend printed on the chart you carry.", 13, "start", "fg", weight=600))
    return c


# ---------------------------------------------------------------- 5.2 documentation
@chart
def ersa_entry_anatomy() -> Canvas:
    c = Canvas("Reading an ERSA aerodrome entry", "A schematic ERSA FAC entry for an invented aerodrome with callouts naming each block: the header with "
               "elevation, position, variation, time zone and operator; the runway table with designators, length and width in metres, surface, slope, "
               "strength and lighting; the communications and navigation aids; and the remarks and local traffic regulations.", height=470, prefix="ers")
    X, W = 20, 390
    c.add(rect(X, 40, W, 410, "surface", "fg-muted", SECOND, rx=4))
    c.add(text(X + W / 2, 30, "Invented example, not a real aerodrome", 12, "middle", "bad", weight=700))
    blocks = []

    def block(y, h, rows, colr, title, notes, cols=(0,)):
        """rows: list of tuples of cell strings laid out at the column offsets in cols."""
        blocks.append((y, h, colr, title, notes))
        out = rect(X + 6, y, W - 12, h, f"{colr}-soft", None, rx=3, fill_opacity=0.6)
        for i, row in enumerate(rows):
            for cx, cell in zip(cols, row):
                out += text(X + 14 + cx, y + 17 + i * 15, cell, 11, "start", "fg", cls="num", weight=700 if i == 0 and colr == "info" else None)
        return out
    c.add(block(48, 64, [("EXAMPLE CREEK", "WA", "UTC +8"), ("ELEV 1050", "S31 00.0 E117 00.0", "VAR 1 DEG W"), ("Operator: Shire of Example (phone)",)],
                "brand", "Header", ["elevation, position, magnetic", "variation, time zone, operator"], cols=(0, 120, 282)))
    c.add(block(120, 92, [("RWY", "LENGTH × WIDTH", "SURFACE", "SLOPE"), ("06/24", "1200 × 30", "sealed", "0.5% up E"), ("12/30", "800 × 18", "gravel", ""),
                          ("Strength (PCN); lighting RWY 06/24",)],
                "info", "Runway table", ["designators (magnetic, to 10°),", "length and width in METRES,", "surface, slope, strength, lighting"], cols=(0, 50, 170, 260)))
    c.add(block(220, 74, [("AERODROME DIAGRAM",)], "sky", "Diagram", ["layout and any non-standard", "circuit direction"]))
    c.add(block(302, 56, [("COMMUNICATIONS", "CTAF (frequency)"), ("AWIS (frequency)", "NAVAIDS: NDB")],
                "ok", "Comms and navaids", ["CTAF or tower, AWIS,", "navigation aids"], cols=(0, 170)))
    c.add(block(366, 76, [("REMARKS / LOCAL TRAFFIC REGULATIONS",), ("RH circuits RWY 24. Noise abatement.",), ("Operating hours. PPR. Fuel: AVGAS.",)],
                "warn", "Remarks and LTRs", ["right-hand circuits, noise,", "hours, PPR, fuel"]))
    # a little aerodrome diagram
    c.add(group(rect(-70, -5, 140, 10, "fg-muted", None, rx=1), rect(-28, -4, 56, 8, "fg-muted", None, rx=1, transform="rotate(60)"),
                text(-78, 4, "06", 11, "end", "fg-muted", cls="num"), text(78, 4, "24", 11, "start", "fg-muted", cls="num"),
                transform=f"translate({X + 250} 262)"))
    for y, h, colr, title, notes in blocks:
        cy = y + h / 2
        c.add(line(X + W + 2, cy, 440, cy, "fg-faint", THIN))
        c.add(circle(X + W + 2, cy, 2.5, colr if colr != "sky" else "sky-fg", None))
        c.add(text(448, cy - 12 + (4 if len(notes) == 2 else 0), title, 13, "start", f"{colr}-fg", weight=700))
        c.add(multiline(448, cy + 4 + (4 if len(notes) == 2 else 0), notes, 11, "start", "fg-muted"))
    c.add(text(X + W / 2, 464, "Runway lengths and widths are in metres; elevation is in feet.", 11, "middle", "fg-faint"))
    return c


@chart
def flight_documents_flow() -> Canvas:
    c = Canvas("Which document answers which question", "Runway data comes from the ERSA FAC entry. For a prohibited, restricted or danger area: the "
               "VNC, VTC or ERC-L shows its identifier and vertical limits; the ERSA PRD section and AIP ENR 5.1 give the hours, controlling authority "
               "and conditional status; NOTAMs can activate or change it; when in doubt, call the controlling authority.", height=490, prefix="fdf")
    c.add(text(20, 30, "Runway data", 14, "start", "fg", weight=700))
    c.add(box(20, 42, 600, 64, "ERSA FAC entry for the aerodrome", ["elevation, runway designators, length and width (m), surface, slope, lighting,",
                                                                     "CTAF, remarks. Runway distances supplement: TORA, TODA, ASDA, LDA."], "info", "info-fg"))
    c.add(text(20, 140, "Is that restricted area active? Work down the chain", 14, "start", "fg", weight=700))
    steps = [("1", "Chart: VNC, VTC or ERC-L", "identifier and vertical limits (not the WAC)", "brand"),
             ("2", "ERSA PRD / AIP ENR 5.1", "hours, controlling authority, RA status", "brand"),
             ("3", "NOTAM", "activated, deactivated or limits changed?", "warn"),
             ("4", "Still unsure?", "call the controlling authority listed in ERSA", "ok")]
    for i, (n, title, body, colr) in enumerate(steps):
        y = 156 + i * 52
        c.add(rect(20, y, 600, 42, "surface-2", None, rx=8))
        c.add(circle(42, y + 21, 12, colr, None))
        c.add(text(42, y + 26, n, 13, "middle", "surface", weight=700))
        c.add(text(64, y + 26, title, 13, "start", "fg", weight=700))
        c.add(text(320, y + 26, body, 12, "start", "fg-muted"))
        if i < 3:
            c.add(arrow(42, y + 34, 42, y + 50, "fg-muted", SECOND))
    c.add(rect(20, 370, 600, 96, "surface-2", None, rx=8))
    c.add(text(32, 390, "Conditional status of a restricted area", 13, "start", "fg", weight=700))
    for i, (tag, colr, what) in enumerate((("RA1", "ok", "clearance normally available: you may plan through it"),
                                           ("RA2", "warn", "clearance not likely at short notice: plan to avoid it"),
                                           ("RA3", "bad", "no clearance will be available"))):
        y = 412 + i * 20
        c.add(badge(52, y - 4, tag, colr, 11))
        c.add(text(80, y, what, 12, "start", "fg-muted"))
    c.add(text(20, 484, "If an area is shown as activated by NOTAM and no NOTAM has activated it, it is inactive.", 11, "start", "fg-faint"))
    return c


@chart
def utc_to_wst_activity() -> Canvas:
    c = Canvas("Converting ERSA activity times from UTC", "Two clocks for the same moments: a UTC scale above a Western Standard Time scale, aligned so "
               "each instant lines up vertically. An area listed active 2200 to 0600 UTC is active 0600 to 1400 WST.", height=300, prefix="utw")
    L, R = 70, 610
    x_of = lambda h_utc: L + ((h_utc - 16) % 24) / 24 * (R - L)

    def bar(y, label, colr, offset):
        out = rect(L, y, R - L, 26, "surface-2", "line-strong", THIN)
        out += text(L - 10, y + 18, label, 13, "end", colr, weight=700)
        for k in range(13):
            x = L + k * 2 / 24 * (R - L)
            out += line(x, y + 26, x, y + 32, "fg-muted", THIN)
            out += num(x, y + 46, f"{(16 + k * 2 + offset) % 24:02d}", 11, "middle", "fg-muted")
        return out
    x0, x1 = x_of(22), x_of(6)
    c.add(bar(70, "UTC", "fg", 0))
    c.add(rect(x0, 70, x1 - x0, 26, "bad", None, fill_opacity=0.28))
    c.add(text((x0 + x1) / 2, 62, "ERSA lists: active 2200–0600 UTC", 12, "middle", "bad", weight=700))
    c.add(bar(170, "WST", "brand", 8))
    c.add(rect(x0, 170, x1 - x0, 26, "brand", None, fill_opacity=0.3))
    c.add(text((x0 + x1) / 2, 236, "active 0600–1400 local time", 13, "middle", "brand-fg", weight=700))
    for x in (x0, x1):
        c.add(line(x, 120, x, 166, "fg-muted", THIN, DASH))
    c.add(text((x0 + x1) / 2, 146, "same moments, clock + 8 h", 12, "middle", "fg-muted"))
    c.add(text(20, 28, "Western Australia: local time = UTC + 8 hours. ERSA times are UTC.", 13, "start", "fg", weight=600))
    c.add(text(20, 270, "Another: 0000–0800 UTC Mon–Fri is 0800–1600 WST Mon–Fri.", 12, "start", "fg-muted"))
    c.add(text(20, 288, "Getting the conversion backwards is the classic lost mark.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 6.1 airworthiness
@chart
def airworthiness_documents_flow() -> Canvas:
    c = Canvas("Is the aeroplane serviceable today?", "The documents that tell you whether the aircraft is serviceable: the maintenance release, the certificate "
               "of airworthiness, the certificate of registration, and the approved flight manual or POH with weight and balance data. Before flight "
               "check the maintenance release: current in hours and date, daily inspection certified today, no endorsed defect that grounds the "
               "aircraft, no maintenance due before the end of the flight.", height=430, prefix="awd")
    docs = [("Maintenance release", ["the key document: valid for a period", "(commonly 100 h or 12 months)"], "brand"),
            ("Certificate of airworthiness", ["type and aircraft meet the design", "standard; in force while maintained"], "surface-2"),
            ("Certificate of registration", ["on the Australian register"], "surface-2"),
            ("Flight manual / POH", ["current amendments, weight and", "balance data for this aircraft"], "surface-2")]
    y = 50
    for title, body, colr in docs:
        h = 26 + 15 * len(body) + 6
        c.add(box(20, y, 260, h, title, body, colr, "brand-fg" if colr == "brand" else "fg", 11, 13))
        y += h + 10
    c.add(text(20, 30, "Documents", 14, "start", "fg", weight=700))
    c.add(text(20, y + 12, "Logbooks hold the history (not carried).", 11, "start", "fg-faint"))
    c.add(text(340, 30, "Check on the maintenance release", 14, "start", "fg", weight=700))
    checks = [("Current in hours AND date", "whichever comes first"), ("Daily inspection certified today", "before the first flight of the day"),
              ("No endorsed defect grounds it", "or it is a permissible unserviceability"), ("Nothing due before you land", "no maintenance overdue after the flight")]
    for i, (a, b) in enumerate(checks):
        yy = 52 + i * 70
        c.add(rect(340, yy, 280, 58, "ok-soft", None, rx=8))
        c.add(circle(362, yy + 29, 11, "ok", None))
        c.add(path(f"M{356} {yy + 29} l4 5 l8 -10", "surface", None, 2.5))
        c.add(text(382, yy + 25, a, 13, "start", "ok-fg", weight=700))
        c.add(text(382, yy + 42, b, 11, "start", "fg-muted"))
    c.add(arrow(282, 80, 336, 80, "brand", SECOND))
    c.add(rect(340, 336, 280, 72, "bad-soft", None, rx=8))
    c.add(text(352, 356, "Any check fails?", 13, "start", "bad-fg", weight=700))
    c.add(text(352, 374, "The aircraft is unserviceable:", 12, "start", "bad-fg"))
    c.add(text(352, 392, "do not fly it.", 12, "start", "bad-fg", weight=700))
    return c


@chart
def daily_vs_preflight_inspection() -> Canvas:
    c = Canvas("Daily inspection or pre-flight inspection?", "Comparison. Daily inspection: once a day before the first flight, to the daily inspection "
               "schedule, by a licensed engineer or an authorised pilot, certified on the maintenance release, valid for the rest of the day. "
               "Pre-flight inspection: before every flight, the POH walk-around by the pilot in command, not certified.", height=330, prefix="dvp")
    rows = [("When", ["Before the first flight of each day"], ["Before every flight"]),
            ("To what", ["The daily inspection schedule"], ["The POH walk-around"]),
            ("By whom", ["Licensed engineer, or a pilot", "authorised by the operator for the type"], ["The pilot in command"]),
            ("Certified?", ["Yes: on the maintenance release,", "valid for the rest of that day"], ["No"])]
    c.add(rect(150, 30, 240, 36, "brand-soft", None, rx=8))
    c.add(rect(400, 30, 220, 36, "info-soft", None, rx=8))
    c.add(text(270, 53, "Daily inspection", 15, "middle", "brand-fg", weight=700))
    c.add(text(510, 53, "Pre-flight inspection", 15, "middle", "info-fg", weight=700))
    y = 98
    for label, a_, b_ in rows:
        c.add(line(20, y - 20, 620, y - 20, "line", THIN))
        c.add(text(20, y, label, 13, "start", "fg", weight=700))
        c.add(multiline(160, y, a_, 12, "start", "fg", leading=1.35))
        c.add(multiline(410, y, b_, 12, "start", "fg", weight=700 if b_ == ["No"] else None, leading=1.35))
        y += 22 + 16 * max(len(a_), len(b_))
    c.add(rect(20, 272, 600, 40, "surface-2", None, rx=8))
    c.add(text(32, 297, "Either way, the pilot in command must be satisfied the aircraft is airworthy before flight.", 12, "start", "fg-muted"))
    return c


@chart
def defect_endorsement_flow() -> Canvas:
    c = Canvas("What happens after a defect is found", "Flow: a defect is found (or appears in flight, then after landing); it is endorsed in the defect "
               "section, Part 2, of the maintenance release with a description, the date and time in service, and the signature and licence number. "
               "The aircraft cannot fly until a licensed engineer rectifies it and signs it off, or endorses it as a permissible unserviceability with "
               "any conditions.", height=380, prefix="def")
    c.add(box(20, 40, 170, 86, "Defect found", ["before or after a flight;", "in flight: endorse it", "after landing"], "warn", "warn-fg", 11))
    c.add(arrow(192, 83, 222, 83, "fg-muted", MAIN))
    c.add(box(224, 40, 200, 86, "Endorse the MR, Part 2", ["clear description; date and", "time in service; signature", "and licence number"], "brand", "brand-fg", 11))
    c.add(arrow(426, 83, 456, 83, "fg-muted", MAIN))
    c.add(box(458, 40, 162, 86, "Grounded", ["cannot fly again until", "an engineer deals", "with it"], "bad", "bad-fg", 11))
    c.add(path("M539 128 L539 160 L150 160 L150 190", "fg-muted", None, SECOND, arrow_end=True))
    c.add(path("M539 160 L470 160 L470 190", "fg-muted", None, SECOND, arrow_end=True))
    c.add(box(40, 192, 230, 86, "Rectified", ["licensed engineer fixes it", "and signs it off"], "ok", "ok-fg", 11))
    c.add(box(360, 192, 260, 86, "Permissible unserviceability", ["engineer finds it does not affect", "safety and endorses it, with", "any conditions"], "ok", "ok-fg", 11))
    c.add(path("M155 280 L155 304 L490 304 L490 280", "ok", None, SECOND))
    c.add(arrow(322, 304, 322, 326, "ok", SECOND))
    c.add(text(322, 346, "May fly again (within any conditions)", 14, "middle", "ok-fg", weight=700))
    c.add(text(20, 28, "A pilot in command must not fly with a known defect that has not been dealt with.", 13, "start", "fg", weight=600))
    c.add(text(20, 372, "A defect that affects safety may also need a transport safety report.", 11, "start", "fg-faint"))
    return c


# ---------------------------------------------------------------- 6.2 take-off and landing performance
def _updown(x: float, y: float, up: bool | None, strong: bool = False) -> str:
    """A small arrow: up (longer distance, bad) or down (shorter, ok); None draws a dash."""
    if up is None:
        return line(x - 8, y, x + 8, y, "fg-faint", MAIN)
    colr = "bad" if up else "ok"
    out = arrow(x, y + 9, x, y - 9, colr, 2.5) if up else arrow(x, y - 9, x, y + 9, colr, 2.5)
    if strong:
        out += (arrow(x + 9, y + 9, x + 9, y - 9, colr, 2.5) if up else arrow(x + 9, y - 9, x + 9, y + 9, colr, 2.5))
    return out


@chart
def takeoff_landing_factors() -> Canvas:
    c = Canvas("What lengthens take-off and landing distances", "A table of arrows. Headwind shortens both; tailwind lengthens both markedly; higher "
               "temperature, lower QNH and higher elevation lengthen both through lower density; uphill slope lengthens take-off and downhill slope "
               "lengthens landing; grass, gravel and wet surfaces and higher weight lengthen both; frost on the wing lengthens take-off and may prevent it.",
               height=480, prefix="tlf")
    c.add(text(20, 28, "Red up: longer distance. Green down: shorter.", 13, "start", "fg", weight=600))
    c.add(text(250, 62, "Take-off", 13, "middle", "fg", weight=700))
    c.add(text(330, 62, "Landing", 13, "middle", "fg", weight=700))
    c.add(text(380, 62, "Why", 13, "start", "fg", weight=700))
    rows = [("Headwind", False, False, False, "lower groundspeed for the same IAS"),
            ("Tailwind", True, True, True, "10% of lift-off speed adds about 20%"),
            ("Higher temperature", True, True, False, "lower density"),
            ("Lower QNH", True, True, False, "higher pressure height, lower density"),
            ("Higher elevation", True, True, False, "lower density"),
            ("Uphill slope", True, None, False, "climbing the runway on take-off"),
            ("Downhill slope", None, True, False, "running downhill to stop"),
            ("Grass, gravel, wet", True, True, False, "rolling resistance, poorer braking"),
            ("Heavier", True, True, False, "more to accelerate and stop; less climb"),
            ("Frost on the wing", True, None, False, "less max lift; may prevent take-off")]
    for i, (name, to, ldg, strong, why) in enumerate(rows):
        y = 92 + i * 36
        if i % 2 == 0:
            c.add(rect(16, y - 16, 608, 34, "surface-2", None, rx=6))
        c.add(text(28, y + 5, name, 13, "start", "fg", weight=600))
        c.add(_updown(246 - (4 if strong else 0), y, to, strong))
        c.add(_updown(326 - (4 if strong else 0), y, ldg, strong))
        c.add(text(380, y + 5, why, 12, "start", "fg-muted"))
    c.add(text(20, 462, "A dash: not the case that lengthens this distance. Heat, low QNH and elevation all mean higher density height.", 11, "start", "fg-faint"))
    return c


# ---------------------------------------------------------------- 6.3 load factor limits
@chart
def load_factor_limits() -> Canvas:
    c = Canvas("Limit and ultimate load factors", "Limit load factors by category: normal +3.8 and −1.52 g, utility +4.4 and −1.76 g, aerobatic +6.0 and −3.0 g. "
               "For a normal category aeroplane the ultimate load is 1.5 times the limit, 5.7 g: between limit and ultimate the structure bends "
               "permanently, beyond ultimate it breaks. A level turn at 60 degrees is 2 g and at 70 degrees 2.9 g.", height=400, prefix="lfl")
    ch = Chart(c, (-3.5, 7), (0, 1), box=(130, 60, 610, 300), xlabel="Load factor (g)", xticks=[-3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7],
               xfmt=lambda v: f"{int(v):+d}" if v else "0", grid=True)
    for t in ch.xticks:
        c.add(line(ch.px(t), ch.top, ch.px(t), ch.bottom, "line", THIN))
        c.add(num(ch.px(t), ch.bottom + 18, f"{t:+d}" if t else "0", 12, "middle", "fg-muted"))
    c.add(line(ch.left, ch.bottom, ch.right, ch.bottom, "fg-muted", SECOND, cap="butt"))
    c.add(text((ch.left + ch.right) / 2, ch.bottom + 40, "Load factor (g)", 13, "middle", "fg-muted", weight=600))
    cats = [("Normal", -1.52, 3.8, 0.82), ("Utility", -1.76, 4.4, 0.55), ("Aerobatic", -3.0, 6.0, 0.28)]
    for name, neg, pos, yy in cats:
        Y = ch.py(yy)
        c.add(rect(ch.px(neg), Y - 13, ch.px(pos) - ch.px(neg), 26, "ok-soft", "ok", THIN, rx=3))
        c.add(text(120, Y + 5, name, 13, "end", "fg", weight=700))
        c.add(num(ch.px(pos) - 6, Y + 5, f"+{fmt(pos)}", 12, "end", "ok-fg", weight=700))
        c.add(num(ch.px(neg) + 6, Y + 5, f"−{fmt(-neg)}", 12, "start", "ok-fg", weight=700))
    Y = ch.py(0.82)
    c.add(rect(ch.px(3.8), Y - 13, ch.px(5.7) - ch.px(3.8), 26, "warn-soft", "warn", THIN))
    c.add(rect(ch.px(5.7), Y - 13, ch.px(7) - ch.px(5.7), 26, "bad-soft", "bad", THIN))
    c.add(num(ch.px(5.7) + 4, Y + 5, "5.7", 12, "start", "bad", weight=700))
    c.add(text((ch.px(3.8) + ch.px(5.7)) / 2, Y - 22, "bends permanently", 11, "middle", "warn-fg", weight=600))
    c.add(text((ch.px(5.7) + ch.px(7)) / 2, Y + 30, "breaks", 11, "middle", "bad", weight=600))
    c.add(text(ch.px(0.9), 46, "limit load: no permanent deformation", 12, "middle", "ok-fg", weight=600))
    # level turn markers
    for g, lab, anc, dx in ((2.0, "60° turn: 2 g", "end", -6), (2.9, "70°: 2.9 g", "start", 6)):
        X = ch.px(g)
        c.add(line(X, ch.py(1.0), X, ch.py(0.05), "brand", SECOND, DASH))
        c.add(text(X + dx, ch.py(0.1), lab, 12, anc, "brand", weight=700))
    c.add(text(20, 372, "Ultimate (design) load = limit × 1.5 safety factor: 3.8 × 1.5 = 5.7 g for the normal category.", 12, "start", "fg-muted"))
    c.add(text(20, 390, "Level flight is 1 g; a level turn needs 1 ÷ cos(bank).", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 6.4 weight and balance
WB = [("Empty aircraft", 680, 2050), ("Pilot and passenger", 160, 2000), ("Rear passenger", 70, 2900), ("Baggage", 20, 3500), ("Fuel 150 L × 0.72", 108, 2300)]


@chart
def moment_arm_seesaw() -> Canvas:
    tw = sum(w for _, w, _ in WB)
    tm = sum(w * a for _, w, a in WB)
    cg = tm / tw
    c = Canvas("Weight × arm = moment: finding the CG", f"The worked example as a balance beam measured from the datum: each load pushes down at its arm. "
               f"Total weight {tw} kg, total moment {tm:,} kg mm, so the CG is at {cg:,.0f} mm, aft of the 2,120 mm limit (limits 2,000 to 2,120 mm).",
               height=470, prefix="mas")
    BY = 190
    L0 = 40
    px = lambda a: 100 + (a - 1900) / (3600 - 1900) * 500
    # beam with a break between the datum and 1,900 mm
    c.add(line(L0, BY, 80, BY, "fg", 5, cap="butt"), line(90, BY, 610, BY, "fg", 5, cap="butt"))
    c.add(path(f"M80 {BY - 8} l6 16 M86 {BY - 8} l6 16", "fg-muted", None, SECOND))
    c.add(line(L0, BY - 60, L0, BY + 30, "fg-muted", SECOND, DASH))
    c.add(text(L0 - 4, BY + 46, "datum", 12, "start", "fg-muted", weight=600))
    for a in (2000, 2500, 3000, 3500):
        c.add(line(px(a), BY + 4, px(a), BY + 10, "fg-muted", THIN))
        c.add(num(px(a), BY + 24, f"{a:,}", 11, "middle", "fg-muted"))
    c.add(text(610, BY + 40, "mm aft of datum", 11, "end", "fg-faint"))
    # CG limits band on the beam
    c.add(rect(px(2000), BY - 6, px(2120) - px(2000), 12, "ok", None, fill_opacity=0.6))
    # loads as downward arrows on the beam; length grows with weight
    labels = {"Empty aircraft": ("start", 8), "Pilot and passenger": ("end", -8), "Rear passenger": ("middle", 0), "Baggage": ("middle", 0), "Fuel 150 L × 0.72": ("start", 8)}
    for name, w, a in WB:
        length = 24 + w * 0.12
        X = px(a)
        c.add(arrow(X, BY - 8 - length, X, BY - 6, "info", MAIN))
        anc, dx = labels[name]
        c.add(num(X + dx, BY - 14 - length, f"{w} kg", 12, anc, "info", weight=700))
        c.add(text(X + dx, BY - 28 - length, name.split(" 150")[0], 11, anc, "fg-muted"))
    # fulcrum at the CG
    X = px(cg)
    c.add(polygon([(X, BY + 3), (X - 14, BY + 30), (X + 14, BY + 30)], "bad-soft", "bad", MAIN))
    c.add(text(X + 22, BY + 70, f"balances at CG {cg:,.0f} mm", 13, "start", "bad", weight=700))
    c.add(text(X + 22, BY + 86, "aft of the limit: change the load", 12, "start", "bad"))
    c.add(text(px(2000), BY + 46, "CG limits 2,000–2,120 mm", 11, "start", "ok-fg", weight=600))
    # the sum
    c.add(rect(20, 290, 600, 160, "surface-2", None, rx=8))
    c.add(text(32, 312, "Item", 12, "start", "fg", weight=700))
    for x, h in ((270, "kg"), (360, "arm mm"), (500, "moment kg mm")):
        c.add(text(x, 312, h, 12, "end", "fg", weight=700))
    for i, (name, w, a) in enumerate(WB):
        y = 330 + i * 16
        c.add(text(32, y, name, 12, "start", "fg-muted"))
        c.add(num(270, y, f"{w:,}", 12, "end", "fg"))
        c.add(num(360, y, f"{a:,}", 12, "end", "fg"))
        c.add(num(500, y, f"{w * a:,}", 12, "end", "fg"))
    c.add(line(32, 414, 500, 414, "line-strong", THIN))
    c.add(num(270, 428, f"{tw:,}", 12, "end", "fg", weight=700))
    c.add(num(500, 428, f"{tm:,}", 12, "end", "fg", weight=700))
    c.add(text(32, 428, "Total", 12, "start", "fg", weight=700))
    c.add(num(32, 444, f"CG = {tm:,} ÷ {tw:,} = {cg:,.0f} mm", 12, "start", "bad", weight=700))
    c.add(text(512, 330, "moment =", 12, "start", "fg-muted"))
    c.add(text(512, 346, "weight × arm", 12, "start", "fg-muted", weight=700))
    c.add(text(20, 26, "Every load pushes down at its arm; the aeroplane balances at the CG.", 13, "start", "fg", weight=600))
    return c


@chart
def cg_position_effects() -> Canvas:
    c = Canvas("Centre of gravity outside the limits", "Forward of the limit: nose heavy, higher stall speed, more elevator needed to flare and possibly not "
               "enough, higher drag from trim, very stable. Aft of the limit: tail heavy, light and over-sensitive pitch control, reduced longitudinal "
               "stability, lower stall speed but poor stall and spin recovery that may be impossible.", height=340, prefix="cgp")
    for x0, title, cgdx, pitch, colr, lines in (
            (14, "CG forward of the limit", 26, -5, "warn", ["nose heavy; very stable", "higher stall speed", "more elevator to flare,", "possibly not enough", "higher drag from trim"]),
            (326, "CG aft of the limit", -26, 5, "bad", ["tail heavy; light, over-", "sensitive pitch control", "reduced stability", "lower stall speed, but stall and", "spin recovery may be impossible"])):
        c.add(rect(x0, 16, 300, 310, f"{colr}-soft", None, rx=10))
        c.add(text(x0 + 150, 46, title, 15, "middle", f"{colr}-fg", weight=700))
        PX, PY = x0 + 150, 140
        c.add(plane_side(PX, PY, 1.9, pitch=pitch))
        gx = PX + cgdx * 1.9 * math.cos(math.radians(pitch))
        gy = PY - cgdx * 1.9 * math.sin(math.radians(pitch))
        c.add(circle(gx, gy, 9, "surface", f"{colr}", 2.5))
        c.add(path(f"M{gx} {gy - 9} A9 9 0 0 1 {gx + 9} {gy} L{gx} {gy} Z M{gx} {gy + 9} A9 9 0 0 1 {gx - 9} {gy} L{gx} {gy} Z", None, colr))
        c.add(arrow(gx, gy + 12, gx, gy + 60, "info", MAIN))
        c.add(text(gx + 8, gy + 56, "CG", 12, "start", "info", weight=700))
        c.add(multiline(x0 + 20, 232, lines, 13, "start", "fg", leading=1.35))
    return c
