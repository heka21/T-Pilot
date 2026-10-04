"""GNSSC (GNSS operation) diagrams. Numbers come from content/notes/GNSSC/*.md."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, arc_path, arrow, circle, fmt, group, line, multiline, path, plane_top, polygon,
                                rect, text)


def satellite(x: float, y: float, s: float = 1.0, color: str = "fg") -> str:
    """Small satellite icon: body with two solar panels."""
    return group(rect(-5, -5, 10, 10, "surface-2", color, SECOND, rx=1.5),
                 rect(-19, -3.5, 11, 7, "info-soft", color, THIN), rect(8, -3.5, 11, 7, "info-soft", color, THIN),
                 line(-8, 0, -5, 0, color, THIN), line(5, 0, 8, 0, color, THIN),
                 transform=f"translate({fmt(x)} {fmt(y)}) rotate(-20) scale({fmt(s)})")


def _circle_meet(c1, r1, c2, r2, near):
    """Intersection of two circles nearest the point `near`."""
    (x1, y1), (x2, y2) = c1, c2
    d = math.hypot(x2 - x1, y2 - y1)
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(r1 * r1 - a * a, 0))
    mx, my = x1 + a * (x2 - x1) / d, y1 + a * (y2 - y1) / d
    p = (mx + h * (y2 - y1) / d, my - h * (x2 - x1) / d)
    q = (mx - h * (y2 - y1) / d, my + h * (x2 - x1) / d)
    return min((p, q), key=lambda o: math.hypot(o[0] - near[0], o[1] - near[1]))


# ---------------------------------------------------------------- trilateration
@chart
def gnss_trilateration() -> Canvas:
    c = Canvas("Trilateration and the receiver's clock", "Drawn flat. Left: each satellite's range is a circle centred on the satellite; with a perfect "
               "clock the three circles meet at one point, the receiver's position. Right: the receiver's clock is wrong, so every range is wrong by "
               "the same amount (pseudoranges) and the circles no longer meet at a point but enclose a small triangle. Because the error is the same "
               "for every satellite, one extra measurement lets the receiver adjust its own clock, shrinking every range by the same amount until "
               "they meet at a single point. In three dimensions that extra measurement is the fourth satellite.", height=500, prefix="gtr")
    angles, dist, sweep = (-145, -90, -35), 150, 16

    def panel(x0: float, title: str, sub: str, colour: str, err: float):
        c.add(rect(x0, 14, 304, 420, "surface-2", None, rx=10))
        c.add(text(x0 + 16, 42, title, 16, "start", colour, weight=700))
        c.add(text(x0 + 16, 62, sub, 12, "start", "fg-muted"))
        P = (x0 + 152, 296)
        sats = [(P[0] + dist * math.cos(math.radians(a)), P[1] + dist * math.sin(math.radians(a))) for a in angles]
        for i, (s, a) in enumerate(zip(sats, angles)):
            back = a + 180      # direction from the satellite to the receiver
            c.add(line(s[0], s[1], P[0], P[1], "fg-faint", THIN, DASH))
            if err:
                c.add(path(arc_path(s[0], s[1], dist + err, back - 24, back + 24), "bad", None, MAIN, dash="6 4"))
            c.add(path(arc_path(s[0], s[1], dist, back - sweep, back + sweep), "brand", None, MAIN))
            c.add(satellite(s[0], s[1], 1.1))
            c.add(text(s[0], s[1] - 18, f"Sat {i + 1}", 12, "middle", "fg-muted", weight=600))
        return P, sats

    # 1 perfect clock
    P, _ = panel(12, "1 · Perfect clock", "every range exactly right", "brand", 0)
    c.add(circle(P[0], P[1], 5, "brand", "surface", 1.5))
    c.add(text(P[0], P[1] + 92, "three circles meet", 13, "middle", "brand", weight=700))
    c.add(text(P[0], P[1] + 109, "at one point: the fix", 13, "middle", "brand", weight=700))

    # 2 real receiver clock
    err = 36
    P, sats = panel(324, "2 · Receiver clock wrong", "every range wrong by the same amount", "bad", err)
    tri = [_circle_meet(sats[i], dist + err, sats[j], dist + err, P) for i, j in ((0, 1), (1, 2), (0, 2))]
    c.add(polygon(tri, "bad", None, 0, fill_opacity=0.35))
    c.add(circle(P[0], P[1], 5, "brand", "surface", 1.5))
    # key
    c.add(line(340, 88, 368, 88, "bad", MAIN, "6 4"))
    c.add(text(376, 92, "pseudoranges: all too long", 12, "start", "bad", weight=600))
    c.add(line(340, 108, 368, 108, "brand", MAIN))
    c.add(text(376, 112, "clock adjusted: all shrink equally", 12, "start", "brand", weight=600))
    c.add(text(P[0], P[1] + 109, "solid circles meet at the fix", 13, "middle", "brand", weight=700))
    tx, ty = sum(t[0] for t in tri) / 3, sum(t[1] for t in tri) / 3
    c.add(text(P[0], P[1] + 92, "dashed circles miss: a triangle", 13, "middle", "bad", weight=700))

    c.add(multiline(20, 460, ["Drawn flat: on a page two circles fix a point and the third solves the clock. In 3D three spheres fix",
                              "the point, so it takes a fourth satellite to solve the clock: 3 for position + 1 for the clock = 4."], 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- satellite count ladder
@chart
def gnss_satellite_count() -> Canvas:
    c = Canvas("How many satellites each job needs", "A ladder from three to six satellites. Three: a 2D fix only, the receiver assumes a height and is "
               "less reliable. Four: a 3D fix, three for position and one for the receiver clock. Five: RAIM fault detection, the receiver can "
               "tell that one satellite is faulty and warns you. Six: fault detection and exclusion, it identifies the faulty satellite, leaves it "
               "out and keeps navigating.", height=450, prefix="gsc")
    c.add(text(20, 30, "Each extra satellite buys one more job", 16, "start", "fg", weight=700))
    rungs = [  # bottom to top
        (3, "2D fix only", ["assumes a height; solves latitude and", "longitude only: less reliable"], "warn"),
        (4, "3D fix", ["3 for position (latitude, longitude, height)", "+ 1 for the receiver clock"], "brand"),
        (5, "RAIM fault detection", ["compares several 4-satellite solutions;", "if they disagree, it WARNS you"], "ok"),
        (6, "Fault detection and exclusion (FDE)", ["finds the faulty satellite, leaves it out", "and keeps navigating"], "ok"),
    ]
    left, rail_r, step, base = 36, 120, 88, 366
    # ladder rails
    c.add(line(left, base + 20, left, base - 3 * step - 34, "fg-muted", SECOND))
    c.add(line(rail_r, base + 20, rail_r, base - 3 * step - 34, "fg-muted", SECOND))
    for i, (n, head, body, colour) in enumerate(rungs):
        y = base - i * step
        fg = {"warn": "warn-fg", "ok": "ok-fg", "brand": "brand-fg"}[colour]
        c.add(line(left, y, rail_r, y, "fg-muted", SECOND))
        c.add(rect(left + 16, y - 22, rail_r - left - 32, 44, f"{colour}-soft", colour, SECOND, rx=8))
        c.add(text((left + rail_r) / 2, y + 9, str(n), 26, "middle", fg, weight=700, cls="num"))
        # satellites in a row
        for k in range(n):
            c.add(satellite(rail_r + 30 + k * 28, y - 4, 0.65, "fg"))
        tx = rail_r + 30 + 6 * 28 + 2
        c.add(text(tx, y - 12, head, 14, "start", fg, weight=700))
        c.add(multiline(tx, y + 6, body, 12, "start", "fg"))
    # RAIM bracket
    bx = 628
    y5, y6 = base - 2 * step, base - 3 * step
    c.add(path(f"M{bx - 6} {y6 - 26} L{bx} {y6 - 26} L{bx} {y5 + 26} L{bx - 6} {y5 + 26}", "ok", None, SECOND))
    c.add(text(bx - 6, y6 - 34, "integrity (RAIM): extra satellites check the others", 12, "end", "ok-fg", weight=600))
    c.add(multiline(20, base + 50, ["Too few satellites in view, or poor geometry: RAIM NOT AVAILABLE.",
                                    "The position may still be good, but nothing is checking it."], 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- DOP
def _strip(P, ang: float, half_w: float, half_l: float):
    """Corners of a straight band through P, perpendicular to the line of sight at screen angle ang (degrees)."""
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))      # line of sight
    vx, vy = -uy, ux                                                      # along the band
    return [(P[0] + s * ux * half_w + t * vx * half_l, P[1] + s * uy * half_w + t * vy * half_l) for s, t in ((-1, -1), (-1, 1), (1, 1), (1, -1))]


def _diamond(P, a1: float, a2: float, half_w: float):
    """The overlap of two bands: points with |n1.d| <= w and |n2.d| <= w."""
    n1 = (math.cos(math.radians(a1)), math.sin(math.radians(a1)))
    n2 = (math.cos(math.radians(a2)), math.sin(math.radians(a2)))
    det = n1[0] * n2[1] - n1[1] * n2[0]
    pts = []
    for s1, s2 in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
        b1, b2 = s1 * half_w, s2 * half_w
        x = (b1 * n2[1] - b2 * n1[1]) / det
        y = (n1[0] * b2 - n2[0] * b1) / det
        pts.append((P[0] + x, P[1] + y))
    return pts


@chart
def gnss_dop_geometry() -> Canvas:
    c = Canvas("Satellite geometry and dilution of precision", "Two panels with the same range error on every satellite. Left: satellites spread across "
               "the sky, their range bands cross at nearly 90 degrees and the area where the fix could be is small: low DOP, an accurate fix. Right: "
               "satellites bunched in one part of the sky, the bands cross at a shallow angle and the same error makes a long thin area: high DOP, "
               "a less accurate fix, even when plenty of satellites are in view.", height=460, prefix="gdp")
    half_w, half_l, dist = 11, 70, 160

    def panel(x0: float, angles: tuple[float, float], title: str, sub: str, colour: str, verdict: list[str]):
        c.add(rect(x0, 14, 304, 368, "surface-2", None, rx=10))
        c.add(text(x0 + 16, 42, title, 16, "start", f"{colour}-fg" if colour != "bad" else "bad", weight=700))
        c.add(text(x0 + 16, 62, sub, 12, "start", "fg-muted"))
        P = (x0 + 152, 262)
        for a in angles:
            sx, sy = P[0] + dist * math.cos(math.radians(a)), P[1] + dist * math.sin(math.radians(a))
            c.add(line(sx, sy, P[0], P[1], "fg-faint", THIN, DASH))
            c.add(polygon(_strip(P, a, half_w, half_l), "info", "info", THIN, fill_opacity=0.18))
            c.add(satellite(sx, sy, 1.1))
        area = _diamond(P, angles[0], angles[1], half_w)
        c.add(polygon(area, colour, colour, SECOND, fill_opacity=0.55))
        c.add(multiline(P[0], 350, verdict, 13, "middle", f"{colour}-fg" if colour != "bad" else "bad", weight=700))
        return P

    P1 = panel(12, (-135, -45), "Satellites spread out", "range bands cross near 90°", "ok", ["LOW DOP", "small area: accurate fix"])
    P2 = panel(324, (-101, -79), "Satellites bunched", "range bands cross at a shallow angle", "bad", ["HIGH DOP", "long thin area: poor fix"])
    # the error width marker (same in both): on the left panel's band from the satellite at -45 degrees
    for P, a, sgn in ((P1, -135, -1), (P2, -101, 1)):
        ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
        vx, vy = -uy, ux
        bx, by = P[0] + sgn * vx * (half_l + 10), P[1] + sgn * vy * (half_l + 10)
        c.add(line(bx - ux * half_w, by - uy * half_w, bx + ux * half_w, by + uy * half_w, "info", SECOND))
    c.add(text(P1[0] - 70, P1[1] + 60, "range error", 12, "end", "info", weight=600))
    c.add(text(P2[0] + 112, P2[1] - 44, "same error", 12, "end", "info", weight=600))
    c.add(multiline(20, 410, ["Same range error, same number of satellites: only the geometry differs. Bunched satellites",
                              "magnify every error, even when plenty of satellites are in view."], 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- waypoint passage
def _bez(p0, p1, p2, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])


def _resample(dense, n):
    cum = [0.0]
    for a, b in zip(dense, dense[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    out, j = [], 0
    for k in range(n + 1):
        target = cum[-1] * k / n
        while j < len(cum) - 2 and cum[j + 1] < target:
            j += 1
        a, b = dense[j], dense[j + 1]
        f = (target - cum[j]) / ((cum[j + 1] - cum[j]) or 1)
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))))
    return out


@chart
def gnss_waypoint_passage() -> Canvas:
    c = Canvas("Passing a waypoint on the GNSS receiver", "Plan view: an aeroplane flies a leg to a waypoint. On approach the receiver gives a waypoint "
               "alert. With turn anticipation it starts the turn early, cutting the corner, and sequences to the next leg slightly early so the "
               "desired track changes. In OBS mode there is no sequencing: the receiver keeps you on the old course past the waypoint. Below, the "
               "distance to the waypoint counts down to zero; in OBS mode it then counts up and the TO flag changes to FROM, while with "
               "auto-sequencing the display switches to the next leg and counts down to the next waypoint.", height=600, prefix="gwp")
    A, W, B = (40, 110), (330, 110), (590, 235)
    d = 70
    ln = math.hypot(B[0] - W[0], B[1] - W[1])
    ux, uy = (B[0] - W[0]) / ln, (B[1] - W[1]) / ln
    T0, T1 = (W[0] - d, W[1]), (W[0] + ux * d, W[1] + uy * d)
    c.add(text(20, 30, "Plan view", 14, "start", "fg-muted", weight=700))
    # OBS continuation: straight on past the waypoint
    c.add(line(W[0] + 12, W[1], 600, W[1], "fg-muted", SECOND, DASH, arrow_end=True))
    c.add(text(600, W[1] - 32, "OBS mode: no sequencing,", 12, "end", "fg-muted", weight=600))
    c.add(text(600, W[1] - 16, "keeps you on the old course", 12, "end", "fg-muted"))
    # the desired tracks: leg in, next leg
    c.add(line(A[0], A[1], W[0], W[1], "fg", MAIN))
    c.add(line(W[0], W[1], B[0], B[1], "fg", MAIN, arrow_end=True))
    c.add(text(150, W[1] - 14, "active leg", 12, "middle", "fg", weight=600))
    mx, my = W[0] + ux * ln * 0.72, W[1] + uy * ln * 0.72
    c.add(text(mx + 10, my - 14, "next leg", 12, "start", "fg", weight=600))
    # turn anticipation
    c.add(path(f"M{fmt(T0[0])} {fmt(T0[1])} Q{fmt(W[0])} {fmt(W[1])} {fmt(T1[0])} {fmt(T1[1])}", "brand", None, 3))
    bx, by = _bez(T0, W, T1, 0.55)
    c.add(line(bx - 3, by + 4, 268, 186, "fg-muted", THIN))
    c.add(multiline(40, 196, ["turn anticipation: the turn starts early,", "cutting the corner, and the receiver", "sequences to the next leg slightly early"],
                    12, "start", "brand", weight=600))
    # the waypoint
    c.add(polygon([(W[0], W[1] - 9), (W[0] + 9, W[1]), (W[0], W[1] + 9), (W[0] - 9, W[1])], "surface", "fg", MAIN))
    c.add(text(W[0], W[1] - 22, "waypoint", 13, "middle", "fg", weight=700))
    # waypoint alert
    alert_x = 200
    c.add(line(alert_x, W[1] - 14, alert_x, W[1] + 14, "warn", MAIN))
    c.add(text(alert_x, W[1] + 32, "waypoint alert", 12, "middle", "warn-fg", weight=700))
    c.add(text(alert_x, W[1] + 47, "(arriving)", 12, "middle", "warn-fg"))

    # the aeroplane flies the auto-sequenced path (one moving element)
    dense = [(A[0] + (T0[0] - A[0]) * k / 30, A[1]) for k in range(31)]
    dense += [_bez(T0, W, T1, k / 30) for k in range(1, 31)]
    end = (B[0] - ux * 12, B[1] - uy * 12)
    dense += [(T1[0] + (end[0] - T1[0]) * k / 20, T1[1] + (end[1] - T1[1]) * k / 20) for k in range(1, 21)]
    n = 40
    samples = _resample(dense, n)
    sx, sy, sa = samples[2]
    frames = []
    for k, (x, y, a) in enumerate(samples):
        op = ";opacity:0" if k in (0, n) else ";opacity:1"
        frames.append(f"{fmt(100 * k / n)}%{{transform:translate({fmt(x - sx)}px,{fmt(y - sy)}px) rotate({fmt(a - sa)}deg){op}}}")
    c.style(".gwp-mv{animation:gwp-mv 7s linear infinite;transform-origin:0 0}\n@keyframes gwp-mv{" + "".join(frames) + "}")
    c.add(group(group(plane_top(0, 0, 0.3, 90 + sa, "fg", "surface"), cls="gwp-mv"), transform=f"translate({fmt(sx)} {fmt(sy)})"))

    # ---- distance trace
    top, bot, L, R = 300, 450, 130, 600
    c.add(text(20, top - 22, "Distance to the waypoint", 14, "start", "fg-muted", weight=700))
    c.add(line(L, bot, R + 8, bot, "fg-muted", SECOND, arrow_end=True, cap="butt"))
    c.add(line(L, bot, L, top - 8, "fg-muted", SECOND, arrow_end=True, cap="butt"))
    c.add(text(R, bot + 18, "time →", 12, "end", "fg-muted"))
    c.add(text(L - 8, bot + 4, "0", 12, "end", "fg-muted", cls="num"))
    c.add(text(98, (top + bot) / 2, "distance", 13, "middle", "fg-muted", weight=600, rotate=-90))
    xw = 330                                 # time of passing the waypoint
    c.add(line(xw, top, xw, bot, "line-strong", THIN, DASH))
    c.add(text(xw, top - 6, "overhead", 12, "middle", "fg-muted"))
    # counting down
    c.add(line(L + 10, top + 16, xw, bot, "brand", MAIN))
    c.add(text(L + 70, top + 22, "counts down", 12, "start", "brand", weight=600))
    # auto-sequencing: switches slightly early to the next waypoint's distance
    xs = xw - 12
    ys = top + 16 + (xs - L - 10) / (xw - L - 10) * (bot - top - 16)
    c.add(path(f"M{fmt(xs)} {fmt(ys)} L{fmt(xs)} {top + 24} L{R - 10} {top + 64}", "brand", None, MAIN))
    c.add(text(R - 10, top + 14, "auto-sequenced: now counting down", 12, "end", "brand", weight=600))
    c.add(text(R - 10, top + 29, "to the next waypoint", 12, "end", "brand"))
    # OBS: counts up again from the same waypoint
    c.add(line(xw, bot, R - 10, top + 96, "fg-muted", MAIN, DASH))
    c.add(text(R - 10, top + 130, "OBS: counts up", 12, "end", "fg-muted", weight=600))
    c.add(text(R - 10, top + 145, "from the same waypoint", 12, "end", "fg-muted"))
    # alert marker on the trace
    xa = L + 10 + (alert_x - A[0]) / (W[0] - A[0]) * (xw - L - 10)
    ya = top + 16 + (xa - L - 10) / (xw - L - 10) * (bot - top - 16)
    c.add(circle(xa, ya, 5, "warn", "surface", 1.5))
    c.add(text(xa - 10, ya + 20, "waypoint alert", 12, "end", "warn-fg", weight=600))
    # TO / FROM flag rows
    for fy, label, after, colour in ((488, "OBS mode", "FROM", "fg"), (524, "Auto-sequencing", "TO the next waypoint", "brand-fg")):
        split = xw if after == "FROM" else xs
        c.add(text(L - 8, fy + 4, label, 12, "end", "fg-muted", weight=600))
        c.add(rect(L, fy - 13, split - L - 2, 26, "brand-soft", None, rx=6))
        c.add(text((L + split) / 2, fy + 5, "TO", 13, "middle", "brand-fg", weight=700))
        c.add(rect(split + 2, fy - 13, R - split - 2, 26, "surface-2", "fg-muted", THIN, rx=6))
        c.add(text((split + R) / 2, fy + 5, after, 13, "middle", colour, weight=700))
    c.add(multiline(20, 562, ["Signs you have passed it: a waypoint alert on approach, TO flips to FROM, the distance reaches zero", "then counts up, and (auto-sequencing) the desired track changes to the next leg."],
                    12, "start", "fg-muted"))
    return c
