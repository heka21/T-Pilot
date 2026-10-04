"""Generated charts and geometric figures for the notes. One function per diagram, registered in CHARTS;
`python -m tools.diagrams.build` writes them all into content/diagrams/. Numbers must match the notes."""
from __future__ import annotations

import math

from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, aerofoil, arrow, badge, callout, circle, fmt, group, line, multiline,
                                num, path, plane_rear, plane_side, polygon, polyline, rect, sample, smooth_path, text)

CHARTS: dict[str, callable] = {}


def chart(fn):
    CHARTS[fn.__name__.replace("_", "-")] = fn
    return fn


def cl_curve(a: float) -> float:
    """Lift coefficient model: linear 0.1/deg from -2 deg, rounding over to Cl max 1.5 at 16 deg, then separating."""
    if a <= 12:
        return 0.1 * (a + 2)
    if a <= 16:
        t = (a - 12) / 4
        return 1.4 + 0.1 * (1 - (1 - t) ** 2)  # eases to 1.5 at 16
    return 1.5 - 0.055 * (a - 16) ** 1.35


@chart
def cl_vs_angle_of_attack() -> Canvas:
    c = Canvas("Lift coefficient against angle of attack", "Lift coefficient rises in a straight line with angle of attack until the critical angle of about 16 degrees, "
               "where it peaks and the wing stalls; beyond it lift falls as the airflow separates.", height=400, prefix="cla")
    ch = Chart(c, (-4, 22), (0, 1.8), box=(70, 70, 600, 330), xlabel="Angle of attack (degrees)", ylabel="Lift coefficient  CL",
               xticks=[-4, 0, 4, 8, 12, 16, 20], yticks=[0, 0.5, 1.0, 1.5], xfmt=lambda v: f"{int(v)}°", yfmt=lambda v: fmt(v))
    c.add(ch.band(16, 22, "bad", 0.08))
    c.add(ch.axes())
    pts = sample(cl_curve, -2.5, 21.5, 80)
    c.add(ch.area(pts, "brand", 0.08))
    c.add(ch.curve([p for p in pts if p[0] <= 16], "brand", MAIN))
    c.add(ch.curve([p for p in pts if p[0] >= 16], "bad", MAIN, dash="6 4"))
    c.add(ch.vline(16, "bad", DASH, None))
    c.add(ch.point(16, 1.5, "bad", 5))
    # callouts
    cx, cy = ch.pt(16, 1.5)
    c.add(callout(cx, cy, cx - 30, cy - 40, ["Critical angle ≈ 16°", "CL max: the stall"], "bad", 13))
    sx, sy = ch.pt(6, cl_curve(6))
    c.add(callout(sx, sy, sx + 60, sy - 60, ["Straight line: each extra", "degree adds about 0.1 to CL"], "fg", 13))
    c.add(text(ch.px(19), ch.py(0.42), "Stalled", 13, "middle", "bad", weight=700))
    c.add(text(ch.px(19), ch.py(0.32), "flow separated,", 12, "middle", "bad"))
    c.add(text(ch.px(19), ch.py(0.23), "lift falls", 12, "middle", "bad"))
    # small aerofoils above the x axis showing the attitude to the airflow at three angles
    for a in (2, 10, 19):
        x = ch.px(a)
        y = 36
        c.add(aerofoil(x, y, 44, a, "fg-muted" if a < 16 else "bad", "surface", SECOND))
        c.add(line(x - 40, y + 4, x - 28, y + 4, "sky-fg", THIN, arrow_end=True))
        c.add(num(x + 2, y + 24, f"{a}°", 11, "middle", "fg-muted" if a < 16 else "bad"))
    c.add(text(ch.px(-2), 40, "airflow", 11, "end", "sky-fg"))
    c.add(text(ch.px(-1.5), ch.py(0.1), "zero lift ≈ −2°", 11, "start", "fg-faint"))
    return c


@chart
def stall_speed_vs_bank() -> Canvas:
    c = Canvas("Load factor and stall speed against angle of bank", "In a level turn the load factor is 1 over the cosine of the bank angle and the stall speed rises "
               "with its square root: 1.41 g and 19 percent at 45 degrees, 2 g and 41 percent at 60 degrees, 3.86 g and 97 percent at 75 degrees.",
               height=400, prefix="ssb")
    ch = Chart(c, (0, 80), (0.7, 4.2), box=(70, 40, 500, 330), xlabel="Angle of bank (degrees)", ylabel="× level-flight value",
               xticks=[0, 15, 30, 45, 60, 75], yticks=[1, 1.5, 2, 3, 3.8], xfmt=lambda v: f"{int(v)}°", yfmt=lambda v: fmt(v))
    c.add(ch.axes())
    n = lambda b: 1 / math.cos(math.radians(b))
    vs = lambda b: math.sqrt(n(b))
    bmax = 76
    c.add(ch.hline(3.8, "bad", DASH, None, x_to=76))
    c.add(text(ch.px(2), ch.py(3.8) - 7, "+3.8 g limit load (normal category)", 12, "start", "bad"))
    c.add(ch.curve(sample(n, 0, bmax, 80), "info", MAIN, label="Load factor  n = 1 / cos θ", label_dx=-8, label_dy=-14, label_anchor="end"))
    c.add(ch.curve(sample(vs, 0, bmax, 80), "brand", MAIN, label="Stall speed  × √n", label_dx=10, label_dy=-6))
    for b in (45, 60):
        c.add(ch.guide(b, n(b), "fg-faint"))
        c.add(ch.guide(b, vs(b), "fg-faint"))
        c.add(ch.point(b, n(b), "info", 5, f"{n(b):.2f} g", dx=-10, dy=-10, anchor="end"))
        c.add(ch.point(b, vs(b), "brand", 5, f"×{vs(b):.2f}  (+{round((vs(b) - 1) * 100)}%)", dx=10, dy=20, anchor="start"))
    c.add(ch.point(75, n(75), "bad", 5, "3.86 g", dx=-10, dy=4, anchor="end"))
    c.add(ch.point(75, vs(75), "brand", 4.5, "+97%", dx=10, dy=14, anchor="start"))
    # the two exam numbers as a banner, in the empty area left of the curves
    c.add(rect(130, 100, 232, 60, "brand-soft", None, rx=8))
    c.add(text(142, 120, "Learn these two:", 12, "start", "brand-fg", weight=600))
    c.add(num(142, 137, "45°  →  1.41 g, stall speed +19%", 12, "start", "brand-fg", weight=600))
    c.add(num(142, 153, "60°  →  2.00 g, stall speed +41%", 12, "start", "brand-fg", weight=600))
    return c
