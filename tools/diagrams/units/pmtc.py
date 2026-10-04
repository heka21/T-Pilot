"""PMTC (meteorology, PPL) diagrams: the atmosphere, clouds, visibility, winds, air masses and fronts, flight considerations.
Numbers and names come from content/notes/PMTC/. Southern Hemisphere conventions throughout: clockwise round a low,
anticlockwise round a high, the wind backs as a front passes. Cross-sections are drawn west (left) to east (right)."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, badge, circle, ellipse, fmt, group, line, multiline, num, path,
                                plane_side, polygon, rect, smooth_path, text)
from tools.diagrams.units.rmtc import arrow, canvas, cumulus, ground, moon, mover, sun


# ---------------------------------------------------------------- local helpers
def layer(x: float, y: float, w: float, h: float, stroke: str = "fg-muted", fill: str = "surface-2", width: float = SECOND, cls: str | None = None) -> str:
    """Layer (stratiform) cloud: a soft-edged slab."""
    return rect(x, y, w, h, fill, stroke, width, rx=min(h / 2, 14), cls=cls)


def wisps(x: float, y: float, w: float, color: str = "fg-muted", n: int = 3) -> str:
    """Cirrus: a few hooked strands."""
    out = ""
    for i in range(n):
        x0, y0 = x + i * w / n, y + (i % 2) * 8
        out += path(f"M{fmt(x0)} {fmt(y0 + 10)} C{fmt(x0 + w * 0.15)} {fmt(y0 + 10)} {fmt(x0 + w * 0.25)} {fmt(y0 - 2)} {fmt(x0 + w * 0.32)} {fmt(y0 - 6)}",
                    color, None, SECOND)
    return out


def rain(x0: float, x1: float, y0: float, y1: float, n: int = 5, color: str = "sky-fg", slant: float = -8, cls: str | None = None) -> str:
    out = ""
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        out += line(x, y0, x + slant, y1, color, THIN, DASH, cls=cls)
    return out


def bumpy(pts: list[tuple[float, float]], close: bool = True, seg: float = 26, flat_last: bool = True) -> str:
    """Path through pts joined by small outward-bulging arcs (clockwise order bulges outwards), each long side split into
    bumps about `seg` long: a cauliflower outline. With flat_last the closing side (the cloud base) stays straight."""
    d = f"M{fmt(pts[0][0])} {fmt(pts[0][1])}"
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = max(1, round(math.hypot(bx - ax, by - ay) / seg))
        for i in range(1, n + 1):
            x, y = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
            r = math.hypot(bx - ax, by - ay) / n * 0.62
            d += f" A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x)} {fmt(y)}"
    return d + (" Z" if close else "")


def cb(x0: float, base: float, x1: float, top: float, ax0: float, ax1: float, stroke: str = "fg-muted", fill: str = "surface-2",
       width: float = SECOND) -> str:
    """Cumulonimbus: a bumpy tower from x0..x1 standing on `base`, under a flat anvil from ax0 to ax1 whose top is at `top`."""
    w, h = x1 - x0, base - top
    tx0, tx1 = x0 + 0.14 * w, x1 - 0.14 * w
    ty = top + 26
    tower = [(x0, base), (x0 - 0.07 * w, base - 0.3 * h), (x0 + 0.02 * w, base - 0.62 * h), (tx0, ty), (tx0 + 0.15 * w, top + 14),
             (tx1 - 0.15 * w, top + 14), (tx1, ty), (x1 - 0.02 * w, base - 0.62 * h), (x1 + 0.07 * w, base - 0.3 * h), (x1, base)]
    out = path(bumpy(tower), stroke, fill, width)
    edge = (f"M{fmt(tx0)} {fmt(ty)} C{fmt((tx0 + ax0) / 2)} {fmt(ty - 4)} {fmt(ax0 + 6)} {fmt(top + 12)} {fmt(ax0)} {fmt(top + 8)} "
            f"C{fmt(ax0 - 6)} {fmt(top + 2)} {fmt(ax0 + 2)} {fmt(top - 2)} {fmt(ax0 + 14)} {fmt(top)} L{fmt(ax1 - 14)} {fmt(top - 4)} "
            f"C{fmt(ax1 + 2)} {fmt(top - 4)} {fmt(ax1 + 4)} {fmt(top + 8)} {fmt(ax1 - 8)} {fmt(top + 10)} "
            f"C{fmt((tx1 + ax1) / 2)} {fmt(top + 14)} {fmt(tx1 + 6)} {fmt(ty - 4)} {fmt(tx1)} {fmt(ty)}")
    out += path(edge + " Z", None, fill, 0)
    out += path(edge, stroke, None, width)
    return out


def wind_plan(x: float, y: float, from_deg: float, length: float = 34, color: str = "fg", width: float = MAIN) -> str:
    """Plan-view wind arrow (north up) centred on (x, y), pointing where the wind blows TO."""
    to = math.radians(from_deg + 180)
    dx, dy = math.sin(to) * length / 2, -math.cos(to) * length / 2
    return arrow(x - dx, y - dy, x + dx, y + dy, color, width)


def north_arrow(x: float, y: float, size: float = 18) -> str:
    return (path(f"M{fmt(x)} {fmt(y + size / 2)} L{fmt(x)} {fmt(y - size / 2)}", "fg-muted", None, SECOND, arrow_end=True)
            + text(x, y - size / 2 - 5, "N", 12, "middle", "fg-muted", weight=700))


def resample(pts: list[tuple[float, float]], step: float) -> list[tuple[float, float, float, float]]:
    """Points every `step` along a polyline: (x, y, unit tangent x, unit tangent y)."""
    out, carry = [], 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, by - ay)
        if seg == 0:
            continue
        tx, ty = (bx - ax) / seg, (by - ay) / seg
        d = carry
        while d < seg:
            out.append((ax + tx * d, ay + ty * d, tx, ty))
            d += step
        carry = d - seg
    return out


def front(pts: list[tuple[float, float]], kind: str, side: int = 1, step: float = 26, size: float = 7) -> str:
    """Synoptic front along a polyline. kind: cold (triangles, brand), warm (semicircles, bad), occluded (alternating, info),
    or trough (dashed line). side = +1 puts the symbols on the left of the drawing direction (screen), -1 on the right."""
    colour = {"cold": "brand", "warm": "bad", "occluded": "info", "trough": "fg"}[kind]
    d = "M" + " L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts)
    if kind == "trough":
        return path(d, colour, None, MAIN + 0.5, dash="9 6")
    out = path(d, colour, None, MAIN + 0.5)
    marks = resample(pts, step)[1:]
    for i, (x, y, tx, ty) in enumerate(marks):
        nx, ny = ty * side, -tx * side  # left normal on screen for side=+1
        tri = kind == "cold" or (kind == "occluded" and i % 2 == 0)
        if tri:
            out += polygon([(x - tx * size, y - ty * size), (x + tx * size, y + ty * size), (x + nx * size * 1.3, y + ny * size * 1.3)], colour, None)
        else:
            a = math.degrees(math.atan2(ty, tx))
            sweep = 1 if side > 0 else 0
            out += path(f"M{fmt(x - tx * size)} {fmt(y - ty * size)} A{fmt(size)} {fmt(size)} 0 0 {sweep} {fmt(x + tx * size)} {fmt(y + ty * size)} Z", None, colour, 0)
            del a
    return out


def flow_style(prefix: str, seconds: float = 1.2, dash: str = "8 7") -> str:
    period = sum(float(v) for v in dash.split()) * 2
    return (f".{prefix}-flow{{stroke-dasharray:{dash};animation:{prefix}-flow {seconds}s linear infinite}}\n"
            f"@keyframes {prefix}-flow{{to{{stroke-dashoffset:-{fmt(period)}}}}}")


# ================================================================ PMTC 2.6 air masses and fronts
@chart
def cold_front_cross_section() -> Canvas:
    c = canvas("A cold front passing, west to east",
               "Cross-section of a cold front moving east. Cold maritime polar air on the left drives under the warm air as a steep wedge, the frontal "
               "surface rising about 1 in 50 to 1 in 100. The warm air is lifted fast at the front into a narrow band of cumulus, towering cumulus and "
               "cumulonimbus with heavy showers, thunderstorms and hail. Ahead, altostratus and altocumulus with a strengthening north-westerly wind. "
               "Behind, scattered showery cumulus in the colder air, with good visibility, and the wind has backed to the south-west.",
               height=516, prefix="cfx")
    c.style(flow_style("cfx"))
    G = 318
    c.add(text(320, 26, "A cold front: a steep wedge and a narrow band of storms", 16, "middle", "fg", weight=700))
    c.add(text(28, 50, "W", 13, "start", "fg-faint", weight=700), text(612, 50, "E", 13, "end", "fg-faint", weight=700))
    FX = 404
    surf = [(FX, G), (FX - 8, G - 42), (FX - 30, G - 88), (FX - 70, G - 132), (FX - 140, G - 170), (FX - 260, G - 196), (20, G - 206)]
    c.add(path(smooth_path(surf) + f" L20 {G} Z", None, "sky-soft", 0))
    # Cb band over the front, anvil streaming ahead (east)
    c.add(cb(FX - 84, 178, FX + 30, 64, FX - 100, FX + 176))
    c.add(rain(FX - 66, FX + 14, 184, G - 4, 6, "sky-fg"))
    c.add(polygon([(FX - 12, 112), (FX - 24, 136), (FX - 14, 136), (FX - 26, 160), (FX, 128), (FX - 10, 128), (FX, 112)], "warn-soft", "warn", SECOND))
    c.add(path(smooth_path(surf), "brand", None, MAIN + 0.5))
    c.add(text(FX - 108, 60, "Cu, TCu, Cb:", 13, "end", "fg", weight=700))
    c.add(text(FX - 108, 76, "heavy showers, storms, hail", 12, "end", "fg-muted"))
    # ahead: As / Ac and some Cu
    c.add(layer(FX + 74, 132, 142, 16), layer(FX + 120, 110, 96, 12))
    c.add(text(FX + 145, 170, "As, Ac", 13, "middle", "fg-muted", weight=600))
    c.add(cumulus(FX + 130, 240, FX + 186, [12, 18, 12]))
    c.add(text(FX + 158, 256, "some Cu", 12, "middle", "fg-muted"))
    # behind: scattered showery Cu in the cold air
    for x0, x1, tops in ((44, 114, [16, 26, 18]), (170, 240, [18, 30, 20])):
        c.add(cumulus(x0, 222, x1, tops))
        c.add(rain(x0 + 12, x1 - 12, 226, 262, 3, "sky-fg", -6))
    c.add(text(146, 284, "cold air (maritime polar)", 13, "middle", "sky-fg", weight=700))
    c.add(text(146, 302, "heated from below: unstable", 12, "middle", "sky-fg"))
    c.add(text(556, 296, "warm air", 13, "middle", "warn-fg", weight=700))
    # warm air lifted steeply at the nose (the one moving thing: flowing dashes)
    c.add(path(f"M610 {G - 10} C520 {G - 12} 450 {G - 18} {FX + 16} {G - 40} C{FX - 2} {G - 70} {FX - 22} {G - 120} {FX - 28} {G - 150}",
               "warn", None, MAIN, cls="cfx-flow", arrow_end=True))
    # slope note with a leader
    c.add(line(FX - 118, G - 158, 250, 166, "fg-muted", THIN))
    c.add(circle(FX - 118, G - 158, 2.5, "brand", None))
    c.add(multiline(36, 154, ["frontal surface: slope about", "1 in 50 to 1 in 100"], 12, "start", "brand-fg", weight=600))
    # front moving east
    c.add(line(20, G, 620, G, "fg-muted", SECOND))
    c.add(circle(FX, G, 4.5, "brand", None))
    c.add(arrow(FX - 40, G + 18, FX + 30, G + 18, "brand", MAIN))
    c.add(text(FX + 36, G + 22, "front moving east", 12, "start", "brand-fg", weight=600))
    # bottom strip: wind and weather either side
    y0 = 372
    c.add(text(28, y0 - 4, "Surface wind, seen from above:", 12, "start", "fg-muted"))
    c.add(north_arrow(612, y0 + 28, 18))
    cols = [(124, "Behind", "neutral", 225, ["SW: the wind has backed;", "colder, showers, good", "visibility between them"]),
            (FX - 40, "At the front", "bad", None, ["squall, sudden change;", "sharp temperature drop,", "turbulence and wind shear"]),
            (540, "Ahead", "neutral", 315, ["NW, strengthening;", "warm, pressure", "falling"])]
    for x, head, tone, wd, lines in cols:
        c.add(badge(x, y0 + 16, head, tone, 13))
        if wd is not None:
            c.add(wind_plan(x, y0 + 50, wd, 40, "fg", MAIN))
        else:
            c.add(path(f"M{x - 20} {y0 + 52} q10 -18 20 0 t20 0", "bad", None, MAIN))
        c.add(multiline(x, y0 + 86, lines, 12, "middle", "fg-muted", leading=1.25))
    c.add(text(320, 506, "Schematic, vertical scale exaggerated. The band of bad weather is narrow, often 50 nm or less.", 11, "middle", "fg-faint"))
    return c


@chart
def warm_front_cross_section() -> Canvas:
    c = canvas("A warm front approaching, west to east",
               "Cross-section of a warm front moving east. Warm air on the left rides up over a wedge of retreating cold air on a very shallow slope, "
               "about 1 in 150. Cloud forms along the frontal surface and lowers towards the surface front: cirrus far ahead, then cirrostratus, "
               "altostratus and nimbostratus with continuous rain. Rain falling into the cold air saturates it and frontal fog forms ahead of the front. "
               "The frontal surface is about 12,000 ft up some 300 nm ahead of the surface front.", height=446, prefix="wfx")
    c.style(flow_style("wfx", 1.6))
    G = 322
    FX = 110
    k = 0.4

    def fs(x: float) -> float:  # frontal surface on screen
        return G - (x - FX) * k

    def slab(xa: float, xb: float, lift: float, top_a: float, top_b: float, bumps: int = 0) -> str:
        """Cloud slab sitting `lift` above the frontal surface from xa to xb, thickness top_a at xa and top_b at xb."""
        lo = [(xa, fs(xa) - lift), (xb, fs(xb) - lift)]
        hi_b, hi_a = (xb, fs(xb) - lift - top_b), (xa, fs(xa) - lift - top_a)
        if bumps:
            pts = [hi_a] + [(xa + (xb - xa) * (i + 0.5) / bumps, fs(xa + (xb - xa) * (i + 0.5) / bumps) - lift - (top_a + (top_b - top_a) * (i + 0.5) / bumps) - 4)
                            for i in range(bumps)] + [hi_b]
            top = smooth_path(pts)
        else:
            top = f"M{fmt(hi_a[0])} {fmt(hi_a[1])} L{fmt(hi_b[0])} {fmt(hi_b[1])}"
        return top + f" L{fmt(lo[1][0])} {fmt(lo[1][1])} L{fmt(lo[0][0])} {fmt(lo[0][1])} Z"

    c.add(text(320, 26, "A warm front: a shallow slope and a day of lowering cloud", 16, "middle", "fg", weight=700))
    c.add(text(28, 50, "W", 13, "start", "fg-faint", weight=700), text(612, 50, "E", 13, "end", "fg-faint", weight=700))
    c.add(path(f"M{FX} {G} L620 {fs(620)} L620 {G} Z", None, "sky-soft", 0))
    # cloud sequence along the surface, lowering and thickening towards the front
    c.add(path(slab(FX + 24, FX + 230, 14, 58, 70, 5), "fg-muted", "surface-2", SECOND))
    c.add(text(FX + 120, fs(FX + 120) - 50, "Ns", 14, "middle", "fg", weight=700))
    c.add(path(slab(FX + 236, FX + 372, 14, 52, 26), "fg-muted", "surface-2", SECOND))
    c.add(text(FX + 296, fs(FX + 296) - 36, "As", 14, "middle", "fg", weight=700))
    c.add(path(slab(FX + 378, FX + 466, 14, 16, 10), "fg-muted", "surface", THIN))
    c.add(text(FX + 410, fs(FX + 410) - 42, "Cs: halo", 13, "middle", "fg", weight=700))
    c.add(wisps(FX + 462, fs(FX + 480) - 34, 54, "fg-muted", 2))
    c.add(text(FX + 456, fs(FX + 456) - 50, "Ci", 14, "end", "fg", weight=700))
    c.add(rain(FX + 34, FX + 214, G - 34, G - 4, 7, "sky-fg", -6))
    # frontal fog ahead of the front
    c.add(rect(FX + 90, G - 16, 150, 16, "fg-muted", None, rx=8, fill_opacity=0.25))
    c.add(text(FX + 248, G - 5, "frontal fog", 12, "start", "fg-muted", weight=600))
    c.add(path(f"M{FX} {G} L620 {fs(620)}", "bad", None, MAIN + 0.5))
    # warm air sliding up the frontal surface (the moving thing)
    c.add(path(f"M24 {G - 14} C60 {G - 14} {FX - 10} {G - 10} {FX + 24} {fs(FX + 24) - 7} L{FX + 500} {fs(FX + 500) - 7}",
               "warn", None, MAIN, cls="wfx-flow", arrow_end=True))
    c.add(text(30, G - 26, "warm air rides up", 12, "start", "warn-fg", weight=700))
    c.add(text(560, G - 52, "cold air", 13, "middle", "sky-fg", weight=700))
    c.add(text(560, G - 34, "retreating", 12, "middle", "sky-fg"))
    # the worked example: about 12,000 ft some 300 nm ahead
    PX = FX + 330
    c.add(line(PX, fs(PX), PX, G, "fg-muted", THIN, DASH))
    c.add(circle(PX, fs(PX), 4, "bad", None))
    c.add(multiline(PX + 10, fs(PX) + 20, ["frontal surface", "about 12,000 ft"], 12, "start", "bad", weight=600))
    c.add(line(20, G, 620, G, "fg-muted", SECOND))
    c.add(circle(FX, G, 4.5, "bad", None))
    c.add(arrow(FX + 6, G + 16, PX - 2, G + 16, "fg-muted", SECOND))
    c.add(text((FX + PX) / 2, G + 32, "about 300 nm ahead of the surface front (slope 1 in 150)", 12, "middle", "fg-muted"))
    c.add(arrow(FX - 40, G + 56, FX + 26, G + 56, "bad", MAIN))
    c.add(text(FX + 32, G + 60, "front moving east", 12, "start", "bad", weight=600))
    # wind before and after, seen from above
    c.add(text(318, G + 88, "Surface wind:", 12, "end", "fg-muted"))
    c.add(wind_plan(342, G + 84, 0, 30, "fg"), text(362, G + 88, "ahead: N", 12, "start", "fg"))
    c.add(wind_plan(452, G + 84, 315, 30, "fg"), text(474, G + 88, "after: NW (backed)", 12, "start", "fg"))
    c.add(text(320, 438, "Schematic. Cb can hide in the layer cloud if the warm air is unstable.", 11, "middle", "fg-faint"))
    return c


# ================================================================ PMTC 2.3 clouds
@chart
def dew_point_and_cloud_base() -> Canvas:
    c = canvas("Why the cumulus base is about 400 ft per degree of spread",
               "Chart of height against temperature for a thermal leaving the ground at 24 degrees with a dew point of 16. The rising air cools at "
               "3 degrees per 1,000 ft while its dew point falls only 0.5 degrees per 1,000 ft, so the spread closes at 2.5 degrees per 1,000 ft, "
               "400 ft per degree. The two lines meet at about 3,200 ft, 14.4 degrees, where the air saturates: the cumulus base.",
               height=420, prefix="dpb")
    ch = Chart(c, (10, 26), (0, 4000), box=(80, 64, 470, 350), xlabel="Temperature, °C", ylabel="Height above the aerodrome, ft",
               xticks=[10, 12, 14, 16, 18, 20, 22, 24, 26], yticks=[0, 1000, 2000, 3000, 4000],
               xfmt=lambda v: f"{int(v)}°", yfmt=lambda v: f"{int(v):,}")
    c.add(text(320, 28, "METAR 24/16: where does the thermal saturate?", 16, "middle", "fg", weight=700))
    c.add(ch.axes())
    T = lambda h: 24 - 3 * h / 1000
    D = lambda h: 16 - 0.5 * h / 1000
    BX, BY = ch.pt(14.4, 3200)
    c.add(line(80, BY, 470, BY, "brand", THIN, DASH))
    c.add(cumulus(BX - 76, BY - 2, BX + 76, [22, 38, 30, 20], "fg-muted", "surface-2"))
    c.add(ch.curve([(T(0), 0), (T(3200), 3200)], "warn", MAIN, smooth=False))
    c.add(ch.curve([(D(0), 0), (D(3200), 3200)], "info", MAIN, smooth=False))
    c.add(multiline(ch.px(T(1300)) + 12, ch.py(1300), ["temperature", "−3° per 1,000 ft"], 12, "start", "warn-fg", weight=600))
    c.add(multiline(ch.px(D(2500)) - 12, ch.py(2500), ["dew point", "−0.5° per", "1,000 ft"], 12, "end", "info", weight=600))
    for h in (0, 1000, 2000):
        y = ch.py(h) - (10 if h == 0 else 0)
        c.add(line(ch.px(D(h)) + 5, y, ch.px(T(h)) - 5, y, "brand", SECOND))
        c.add(num((ch.px(D(h)) + ch.px(T(h))) / 2, y - 6, f"{fmt(T(h) - D(h))}°", 12, "middle", "brand-fg", weight=700))
    c.add(circle(BX, BY, 6, "brand", "surface", 2))
    c.add(num(BX + 10, BY + 18, "14.4°", 12, "start", "brand-fg", weight=700))
    c.add(text(466, BY - 8, "cloud base", 13, "end", "brand", weight=700))
    # rule box on the right
    x0 = 494
    c.add(rect(x0, 84, 136, 230, "surface-2", None, rx=10))
    c.add(multiline(x0 + 12, 108, ["Spread", "24 − 16 = 8°"], 13, "start", "fg", weight=600, leading=1.35))
    c.add(multiline(x0 + 12, 164, ["Closes at", "3 − 0.5 = 2.5°", "per 1,000 ft,", "so 400 ft per °"], 13, "start", "fg", leading=1.35))
    c.add(multiline(x0 + 12, 268, ["8 × 400 =", "3,200 ft AGL"], 14, "start", "brand", weight=700, leading=1.35))
    c.add(text(320, 410, "Convective cloud only: the base above that aerodrome, not above sea level.", 12, "middle", "fg-faint"))
    return c


@chart
def cloud_families_by_height() -> Canvas:
    c = canvas("The ten cloud genera by height of base",
               "Three height bands. High cloud, above about 20,000 ft, of ice crystals: cirrus, cirrocumulus and cirrostratus with its halo. "
               "Middle cloud, about 6,500 to 20,000 ft: altocumulus, altostratus and nimbostratus, whose base often lowers to near the ground. "
               "Low cloud, below about 6,500 ft: stratocumulus and stratus. On the right, the two clouds with a low base and great vertical extent: "
               "cumulus and cumulonimbus, which reaches the tropopause and spreads into an anvil.", height=476, prefix="cfh")
    c.add(text(320, 26, "Ten cloud genera, sorted by the height of the base", 16, "middle", "fg", weight=700))
    G = 426
    R = 432
    bands = [(48, 172, "High", "above about 20,000 ft: ice crystals"), (172, 302, "Middle", "about 6,500 to 20,000 ft"),
             (302, G, "Low", "below about 6,500 ft")]
    for i, (y0, y1, name, rng) in enumerate(bands):
        c.add(rect(16, y0, R - 16, y1 - y0, "surface-2" if i % 2 == 0 else "surface", None))
        c.add(text(26, y0 + 20, name, 14, "start", "fg", weight=700))
        c.add(text(26, y0 + 36, rng, 11, "start", "fg-muted"))
    c.add(line(16, 172, 630, 172, "line-strong", THIN, DASH), line(16, 302, 630, 302, "line-strong", THIN, DASH))
    # high
    c.add(wisps(66, 100, 74, "fg-muted", 3))
    c.add(text(104, 152, "Cirrus  Ci", 12, "middle", "fg", weight=600))
    for r in range(3):
        for k in range(6):
            c.add(ellipse(200 + k * 12 + (r % 2) * 6, 100 + r * 10, 4.5, 3, "surface", "fg-muted", THIN))
    c.add(text(236, 152, "Cirrocumulus  Cc", 12, "middle", "fg", weight=600))
    c.add(rect(310, 92, 112, 22, "surface", "fg-muted", THIN, rx=10, fill_opacity=0.7))
    c.add(sun(366, 103, 7, "warn"))
    c.add(circle(366, 103, 22, None, "warn", THIN, dash="3 3"))
    c.add(text(366, 152, "Cirrostratus  Cs", 12, "middle", "fg", weight=600))
    c.add(text(366, 166, "halo round the sun", 11, "middle", "fg-muted"))
    # middle
    for k in range(4):
        c.add(cumulus(54 + k * 34, 240, 82 + k * 34, [8, 11], "fg-muted", "surface"))
    c.add(text(110, 268, "Altocumulus  Ac", 12, "middle", "fg", weight=600))
    c.add(layer(196, 218, 98, 24, "fg-muted", "surface-2"))
    c.add(circle(245, 230, 7, "warn-soft", None))
    c.add(text(245, 268, "Altostratus  As", 12, "middle", "fg", weight=600))
    c.add(text(245, 282, "sun as if through", 11, "middle", "fg-muted"))
    c.add(text(245, 295, "ground glass", 11, "middle", "fg-muted"))
    # Ns: thick, base lowering towards the ground
    c.add(path(bumpy([(320, 360), (318, 222), (420, 222), (422, 360)], seg=20), "fg-muted", "fg-faint", SECOND, fill_opacity=0.35))
    c.add(rain(326, 414, 364, G - 4, 6, "sky-fg", -6))
    c.add(text(370, 236, "Nimbostratus", 12, "middle", "fg", weight=700))
    c.add(text(370, 252, "Ns", 12, "middle", "fg", weight=700))
    c.add(multiline(370, 276, ["base often", "lowers to near", "the ground"], 11, "middle", "fg", leading=1.2))
    # low
    for k in range(5):
        c.add(cumulus(34 + k * 27, 372, 61 + k * 27, [8, 10], "fg-muted", "surface"))
    c.add(text(104, 392, "Stratocumulus  Sc", 12, "middle", "fg", weight=600))
    c.add(ground([(186, G), (216, 412), (244, 384), (272, 396), (300, G)], G, "surface", "fg-muted"))
    c.add(layer(184, 368, 118, 22, "fg-muted", "surface-2"))
    c.add(text(243, 356, "Stratus  St", 12, "middle", "fg", weight=600))
    c.add(text(182, 418, "hill fog", 11, "end", "fg-muted"))
    c.add(line(16, G, 630, G, "fg-muted", SECOND))
    # vertical extent: Cu and Cb (brand: the one that matters most)
    c.add(text(536, 62, "Low base, great", 12, "middle", "fg", weight=700))
    c.add(text(536, 77, "vertical extent", 12, "middle", "fg", weight=700))
    c.add(cumulus(446, 364, 496, [26, 42, 30], "fg-muted", "surface"))
    c.add(multiline(471, 384, ["Cumulus Cu", "TCu when", "towering"], 11, "middle", "fg", leading=1.2))
    c.add(cb(552, 364, 604, 104, 520, 626, "brand", "brand-soft", MAIN))
    c.add(multiline(578, 384, ["Cumulonimbus Cb", "anvil at the", "tropopause"], 11, "middle", "brand-fg", leading=1.2))
    c.add(text(320, 466, "Bands are approximate for Australian latitudes and higher in the tropics. Not to scale.", 11, "middle", "fg-faint"))
    return c


def clockwise_ring(cx: float, cy: float, rx: float, ry: float, color: str = "fg-muted", width: float = SECOND, start: float = 200, span: float = 300) -> str:
    """An elliptical isobar drawn clockwise on screen (angles increase clockwise when y points down), arrowhead at the end."""
    a0, a1 = math.radians(start), math.radians(start + span)
    x0, y0 = cx + rx * math.cos(a0), cy + ry * math.sin(a0)
    x1, y1 = cx + rx * math.cos(a1), cy + ry * math.sin(a1)
    return path(f"M{fmt(x0)} {fmt(y0)} A{fmt(rx)} {fmt(ry)} 0 1 1 {fmt(x1)} {fmt(y1)}", color, None, width, arrow_end=True)


def anticlockwise_ring(cx: float, cy: float, rx: float, ry: float, color: str = "fg-muted", width: float = SECOND, start: float = -20, span: float = 300) -> str:
    a0, a1 = math.radians(start), math.radians(start - span)
    x0, y0 = cx + rx * math.cos(a0), cy + ry * math.sin(a0)
    x1, y1 = cx + rx * math.cos(a1), cy + ry * math.sin(a1)
    return path(f"M{fmt(x0)} {fmt(y0)} A{fmt(rx)} {fmt(ry)} 0 1 0 {fmt(x1)} {fmt(y1)}", color, None, width, arrow_end=True)


@chart
def wave_depression_life_cycle() -> Canvas:
    c = canvas("How a wave on a front becomes an occlusion",
               "Four Southern Hemisphere plan views, north up, systems moving east. 1: a stationary front with warm tropical air to the north and cold "
               "polar air to the south flowing past each other. 2: a kink forms and a low develops at its poleward tip. 3: a wave depression, with "
               "air circulating clockwise round the low, a warm front ahead of it, a cold front behind it and the warm sector between them. "
               "4: the faster cold front catches the warm front near the low and lifts the warm sector off the ground: an occluded front.",
               height=566, prefix="wdl")
    c.add(text(320, 26, "From a wave to an occlusion (Southern Hemisphere, north up)", 16, "middle", "fg", weight=700))
    W, H = 300, 190
    origins = [(14, 50), (326, 50), (14, 300), (326, 300)]
    titles = ["1. A stationary front", "2. A kink, and a low at its tip", "3. Wave depression: the warm sector", "4. Occlusion: cold front catches up"]
    notes = ["warm and cold air flow past each other", "warm air pushes south, cold air north", "clockwise round the low; the wind backs at each front",
             "warm sector lifted off the ground"]
    for i, (ox, oy) in enumerate(origins):
        P = lambda x, y, ox=ox, oy=oy: (ox + x, oy + y)
        # warm-air boundary (the front), left to right, in panel coordinates
        if i == 0:
            bnd = [(0, 96), (300, 96)]
        elif i == 1:
            bnd = [(0, 92), (100, 94), (128, 108), (150, 132), (172, 108), (200, 94), (300, 92)]
        elif i == 2:
            bnd = [(0, 56), (40, 62), (96, 104), (150, 150), (214, 108), (300, 76)]
        else:
            bnd = [(0, 56), (50, 60), (112, 86), (166, 104), (226, 86), (300, 66)]
        warm = [P(*p) for p in [(0, 0)] + bnd + [(300, 0)]]
        c.add(rect(ox, oy, W, H, "sky-soft", None))
        c.add(polygon(warm, "warn-soft", None))
        c.add(rect(ox, oy, W, H, None, "line-strong", THIN))
        c.add(text(ox + 10, oy + 18, "warm tropical air", 11, "start", "warn-fg", weight=600))
        c.add(text(ox + W - 10, oy + H - 10, "cold polar air", 11, "end", "sky-fg", weight=600))
        c.add(north_arrow(ox + W - 16, oy + 24, 16))
        c.add(badge(ox + W / 2, oy + H + 18, titles[i], "brand" if i == 3 else "neutral", 12))
        c.add(text(ox + W / 2, oy + H + 38, notes[i], 11, "middle", "fg-muted"))
    # 1: a stationary front, the two air masses flowing past each other
    ox, oy = origins[0]
    c.add(path(f"M{ox} {oy + 96} L{ox + W} {oy + 96}", "fg", None, MAIN + 0.5))
    for x in (60, 170):
        c.add(arrow(ox + x, oy + 64, ox + x + 50, oy + 64, "warn", MAIN))
        c.add(arrow(ox + x + 50, oy + 132, ox + x, oy + 132, "sky-fg", MAIN))
    # 2
    ox, oy = origins[1]
    bnd = [(0, 92), (100, 94), (128, 108), (150, 132), (172, 108), (200, 94), (300, 92)]
    c.add(path(smooth_path([(ox + x, oy + y) for x, y in bnd]), "fg", None, MAIN + 0.5))
    c.add(text(ox + 150, oy + 156, "L", 18, "middle", "bad", weight=700))
    c.add(arrow(ox + 196, oy + 108, ox + 188, oy + 134, "warn", MAIN))
    c.add(arrow(ox + 104, oy + 128, ox + 112, oy + 102, "sky-fg", MAIN))
    # 3
    ox, oy = origins[2]
    L3 = (ox + 150, oy + 150)
    c.add(clockwise_ring(L3[0], L3[1] + 16, 40, 20, "fg-muted", SECOND, 160, 300))
    c.add(front([(ox + 150, oy + 150), (ox + 96, oy + 104), (ox + 40, oy + 62), (ox, oy + 56)], "cold", -1, 24, 6))
    c.add(front([(ox + 150, oy + 150), (ox + 214, oy + 108), (ox + 296, oy + 77.5)], "warm", -1, 24, 6))
    c.add(text(L3[0], L3[1] + 22, "L", 18, "middle", "bad", weight=700))
    c.add(text(ox + 150, oy + 80, "warm sector", 12, "middle", "warn-fg", weight=700))
    c.add(text(ox + 46, oy + 100, "cold front", 11, "middle", "brand-fg", weight=600))
    c.add(text(ox + 262, oy + 116, "warm front", 11, "middle", "bad", weight=600))
    # 4
    ox, oy = origins[3]
    L4 = (ox + 104, oy + 150)
    T = (ox + 166, oy + 104)
    c.add(clockwise_ring(L4[0], L4[1] + 16, 40, 20, "fg-muted", SECOND, 160, 300))
    c.add(front([L4, (ox + 140, oy + 136), T], "occluded", -1, 22, 6))
    c.add(front([T, (ox + 112, oy + 86), (ox + 50, oy + 60), (ox, oy + 56)], "cold", -1, 24, 6))
    c.add(front([T, (ox + 226, oy + 86), (ox + 296, oy + 67)], "warm", -1, 24, 6))
    c.add(text(L4[0], L4[1] + 22, "L", 18, "middle", "bad", weight=700))
    c.add(text(ox + 166, oy + 58, "warm sector", 11, "middle", "warn-fg", weight=600))
    c.add(text(ox + 166, oy + 72, "now aloft", 11, "middle", "warn-fg"))
    c.add(text(ox + 210, oy + 150, "occluded front", 12, "middle", "info", weight=700))
    # legend
    y = 554
    c.add(front([(70, y - 4), (118, y - 4)], "cold", 1, 22, 5), text(124, y, "cold front", 11, "start", "fg-muted"))
    c.add(front([(220, y - 4), (268, y - 4)], "warm", 1, 22, 5), text(274, y, "warm front", 11, "start", "fg-muted"))
    c.add(front([(372, y - 4), (420, y - 4)], "occluded", 1, 22, 5), text(426, y, "occluded front", 11, "start", "fg-muted"))
    return c


@chart
def tropical_cyclone_structure() -> Canvas:
    c = canvas("Inside a tropical cyclone",
               "Top: plan view of a Southern Hemisphere tropical cyclone. Spiral rain bands of cumulonimbus wind in towards the centre and the air "
               "circulates clockwise. At the centre is the eye, 10 to 50 km across, nearly calm with little cloud, ringed by the eyewall of "
               "cumulonimbus with the strongest winds. Bottom: cross-section. Warm, moist air spirals in over a sea of about 26.5 degrees or warmer, "
               "rises in the eyewall and spreads out at the top; air sinks gently in the eye.", height=600, prefix="tcs")
    c.style(".tcs-spin{transform-origin:0 0;animation:tcs-spin 8s linear infinite}\n@keyframes tcs-spin{to{transform:rotate(360deg)}}")
    c.add(text(320, 26, "Inside a tropical cyclone (Southern Hemisphere)", 16, "middle", "fg", weight=700))
    CX, CY = 176, 200
    c.add(circle(CX, CY, 150, "sky-soft", None))
    # spiral bands, rotating clockwise (the one moving thing)
    bands = ""
    for k in range(3):
        pts = []
        for j in range(0, 61):
            th = math.radians(k * 120 + j * 5)
            r = 140 * math.exp(-0.0048 * j * 5)
            pts.append((r * math.cos(th), r * math.sin(th)))
        d = smooth_path(pts)
        bands += path(d, "fg-faint", None, 16, opacity=0.35) + path(d, "fg-muted", None, SECOND)
    for k in range(3):  # wind arrows along the bands, pointing clockwise and inwards
        th = math.radians(k * 120 + 60)
        r = 140 * math.exp(-0.0048 * 60)
        th2 = th + math.radians(16)
        r2 = 140 * math.exp(-0.0048 * 76)
        bands += path(f"M{fmt(r * math.cos(th))} {fmt(r * math.sin(th))} L{fmt(r2 * math.cos(th2))} {fmt(r2 * math.sin(th2))}", "brand", None, MAIN + 1, arrow_end=True)
    c.add(group(group(bands, cls="tcs-spin"), transform=f"translate({CX} {CY})"))
    # eyewall and eye
    c.add(circle(CX, CY, 28, "brand-soft", "brand", MAIN))
    c.add(circle(CX, CY, 12, "sky-soft", "brand", SECOND))
    # labels for the plan view
    c.add(line(CX + 12, CY, 380, 92, "fg-muted", THIN), text(386, 96, "eye: 10 to 50 km across,", 13, "start", "fg", weight=600))
    c.add(text(386, 112, "nearly calm, little cloud", 12, "start", "fg-muted"))
    c.add(line(CX + 22, CY + 18, 380, 160, "fg-muted", THIN), text(386, 156, "eyewall of Cb:", 13, "start", "brand-fg", weight=600))
    c.add(text(386, 172, "the strongest winds", 12, "start", "brand-fg"))
    c.add(line(CX + 100, CY + 62, 380, 224, "fg-muted", THIN), text(386, 222, "spiral rain bands of Cb:", 13, "start", "fg", weight=600))
    c.add(text(386, 238, "torrential rain, visibility near zero", 12, "start", "fg-muted"))
    c.add(text(386, 282, "Clockwise round the eye:", 13, "start", "brand", weight=700))
    c.add(text(386, 298, "Southern Hemisphere, like every low here", 12, "start", "brand-fg"))
    c.add(text(386, 324, "Sustained winds 34 kt (gale) or more;", 12, "start", "fg-muted"))
    c.add(text(386, 340, "over 100 kt in a severe cyclone", 12, "start", "fg-muted"))
    c.add(text(CX, 372, "plan view", 12, "middle", "fg-faint"))
    # cross-section
    S = 548
    c.add(rect(20, S, 600, 20, "sky-soft", None))
    c.add(line(20, S, 620, S, "fg-muted", SECOND))
    c.add(text(320, S + 15, "warm sea, 26.5 °C or warmer", 12, "middle", "sky-fg", weight=600))
    # cirrus outflow canopy, eyewall towers either side of a clear eye, band cells further out
    c.add(path(f"M60 424 C120 404 250 398 300 404 L300 420 C240 420 140 426 60 434 Z", "fg-muted", "surface-2", THIN))
    c.add(path(f"M580 424 C520 404 390 398 340 404 L340 420 C400 420 500 426 580 434 Z", "fg-muted", "surface-2", THIN))
    c.add(path(bumpy([(250, S - 6), (244, 470), (256, 420), (300, 412), (304, S - 6)], seg=22), "brand", "brand-soft", MAIN))
    c.add(path(bumpy([(336, S - 6), (340, 412), (384, 420), (396, 470), (390, S - 6)], seg=22), "brand", "brand-soft", MAIN))
    for x0, x1, top in ((92, 150, 466), (170, 214, 486), (426, 470, 486), (490, 548, 466)):
        c.add(path(bumpy([(x0, S - 30), (x0 - 4, top + 20), (x0 + 10, top - 10), (x1 - 10, top - 10), (x1 + 4, top + 20), (x1, S - 30)], seg=20), "fg-muted", "surface-2", SECOND))
        c.add(rain(x0 + 8, x1 - 8, S - 28, S - 2, 3, "sky-fg", -4))
    # flows: inflow at the surface, up the eyewall, out at the top, sinking in the eye
    c.add(arrow(30, S - 12, 238, S - 12, "warn", MAIN), arrow(610, S - 12, 402, S - 12, "warn", MAIN))
    c.add(arrow(290, 400, 150, 402, "warn", SECOND), arrow(350, 400, 490, 402, "warn", SECOND))
    c.add(arrow(278, 520, 278, 432, "warn", MAIN), arrow(362, 520, 362, 432, "warn", MAIN))
    c.add(arrow(320, 432, 320, 500, "sky-fg", SECOND))
    c.add(text(320, 390, "eye: air sinks", 13, "middle", "fg", weight=700))
    c.add(text(160, 448, "spiral bands", 12, "middle", "fg-muted", weight=600))
    c.add(text(480, 448, "spiral bands", 12, "middle", "fg-muted", weight=600))
    c.add(text(28, S + 15, "moist air spirals in", 11, "start", "warn-fg", weight=600))
    c.add(text(612, S + 15, "and rises in the eyewall", 11, "end", "warn-fg", weight=600))
    c.add(text(320, 592, "Cross-section, not to scale. Weakens over land or cooler water.", 11, "middle", "fg-faint"))
    return c


def wa_coast(ox: float, oy: float) -> list[tuple[float, float]]:
    """Stylised south-west WA coastline, north to Cape Leeuwin then east along the south coast, in panel coordinates."""
    return [(ox + 132, oy), (ox + 124, oy + 60), (ox + 116, oy + 120), (ox + 110, oy + 176), (ox + 100, oy + 226), (ox + 96, oy + 258),
            (ox + 120, oy + 266), (ox + 170, oy + 276), (ox + 230, oy + 290), (ox + 300, oy + 296)]


@chart
def west_coast_trough_positions() -> Canvas:
    c = canvas("Where the west coast trough lies decides Perth's weather",
               "Two maps of south-west Western Australia, north up. Left: the trough lies off the coast, Perth is on its eastern side and gets hot, "
               "dry easterly to north-easterly winds from the interior; the sea breeze is held offshore and the temperature climbs past 40 degrees. "
               "Right: the trough has moved inland, Perth is on its western side and the wind swings south to south-westerly as the sea breeze, the "
               "Fremantle Doctor, arrives and the temperature drops; inland, convergence along the trough sets off high-based storms and dust.",
               height=436, prefix="wct")
    c.add(text(320, 26, "The west coast trough: offshore or inland?", 16, "middle", "fg", weight=700))
    W, H = 300, 300
    for i, ox in enumerate((14, 326)):
        oy = 48
        coast = wa_coast(ox, oy)
        land = coast + [(ox + W, oy)]
        c.add(rect(ox, oy, W, H, "sky-soft", None, rx=10))
        c.add(polygon(land, "surface-2", None))
        c.add(path("M" + " L".join(f"{fmt(x)} {fmt(y)}" for x, y in coast), "fg-muted", None, SECOND))
        c.add(rect(ox, oy, W, H, None, "line-strong", THIN, rx=10))
        c.add(text(ox + 16, oy + 150, "Indian", 11, "start", "sky-fg"), text(ox + 16, oy + 164, "Ocean", 11, "start", "sky-fg"))
        c.add(north_arrow(ox + W - 18, oy + 28, 16))
        px, py = ox + 112, oy + 150
        c.add(circle(px, py, 5, "fg", "surface", 2))
        c.add(text(px + 10, py + 4, "Perth", 12, "start", "fg", weight=700))
        if i == 0:
            tx = ox + 62
            c.add(front([(tx + 6, oy + 20), (tx, oy + 140), (tx - 6, oy + 250)], "trough"))
            c.add(text(tx + 10, oy + 36, "trough", 12, "start", "fg", weight=700))
            for (x, y) in ((ox + 200, oy + 110), (ox + 230, oy + 170), (ox + 170, oy + 210), (ox + 160, oy + 140)):
                c.add(wind_plan(x, y, 70, 40, "bad", MAIN))
            c.add(multiline(ox + 150, oy + 60, ["hot, dry E to NE", "from the interior"], 12, "start", "bad", weight=600))
            c.add(badge(ox + W / 2, oy + H + 18, "Trough offshore", "bad", 12))
            c.add(multiline(ox + W / 2, oy + H + 40, ["over 40 °C at Perth;", "the sea breeze is held offshore"], 11, "middle", "fg-muted", leading=1.25))
        else:
            tx = ox + 214
            c.add(front([(tx + 8, oy + 20), (tx, oy + 140), (tx - 4, oy + 268)], "trough"))
            c.add(text(tx - 8, oy + 36, "trough", 12, "end", "fg", weight=700))
            for (x, y) in ((ox + 76, oy + 120), (ox + 150, oy + 112), (ox + 150, oy + 196), (ox + 60, oy + 60)):
                c.add(wind_plan(x, y, 205, 40, "ok", MAIN))
            c.add(multiline(ox + 10, oy + 222, ["S to SW: the", "Fremantle", "Doctor"], 12, "start", "ok-fg", weight=600))
            # storms inland, east of the trough
            sx = ox + 258
            c.add(cumulus(sx - 26, oy + 120, sx + 26, [14, 22, 14], "fg-muted", "surface"))
            c.add(polygon([(sx - 2, oy + 124), (sx - 10, oy + 140), (sx - 3, oy + 140), (sx - 10, oy + 156), (sx + 6, oy + 134), (sx - 1, oy + 134), (sx + 6, oy + 124)],
                          "warn-soft", "warn", THIN))
            c.add(multiline(sx, oy + 176, ["high-based", "storms,", "dust"], 11, "middle", "warn-fg", weight=600, leading=1.2))
            c.add(badge(ox + W / 2, oy + H + 18, "Trough inland", "ok", 12))
            c.add(multiline(ox + W / 2, oy + H + 40, ["cooler at Perth; wind change, shear and", "turbulence as the trough line passes"], 11, "middle", "fg-muted",
                            leading=1.25))
    c.add(text(320, 430, "Schematic maps; arrows show where the wind blows to.", 11, "middle", "fg-faint"))
    return c


# ================================================================ PMTC 2.7 flight considerations
@chart
def mountain_wave_lenticular_rotor() -> Canvas:
    c = canvas("Mountain waves: lift, sink and rotor downwind of a ridge",
               "Side view of a strong wind blowing from left to right across a ridge in stable air. A cap cloud sits on the crest. Downwind the "
               "airflow sinks steeply down the lee slope, then rises and sinks again in a standing wave. Smooth lens-shaped lenticular clouds sit "
               "still at the wave crests, and under each crest, at about ridge height, a rotor of severe turbulence turns with ragged roll cloud. "
               "Air rises on the upwind side of each crest and sinks on the downwind side, and the sink can exceed a light aeroplane's climb. "
               "Cross ridges 2,000 ft or more above them, at 45 degrees, and stay upwind of the rotor.", height=476, prefix="mwr")
    G, RX, RH, LAM, XC = 372, 170, 112, 170, 340

    def ridge(x: float) -> float:
        return RH * math.exp(-((x - RX) / 56) ** 2)

    def stream(y0: float, decay: float, amp: float):
        def f(x: float) -> float:
            t = min(1.0, max(0.0, (x - RX + 20) / 100))
            env = t * t * (3 - 2 * t)
            return y0 - ridge(x) * decay - amp * env * math.cos(2 * math.pi * (x - XC) / LAM)
        return f

    c.add(text(320, 26, "Mountain waves: where the lift, sink and rotor are", 16, "middle", "fg", weight=700))
    xs = [20 + i * 5 for i in range(121)]
    c.add(ground([(x, G - ridge(x)) for x in xs], G + 8))
    # cap cloud draped over the crest
    cx_ = [128 + i * 4 for i in range(25)]
    top = [(x, G - ridge(x) - 38 * math.exp(-((x - 176) / 30) ** 2)) for x in cx_]
    c.add(path(smooth_path(top) + " " + " ".join(f"L{fmt(x)} {fmt(G - ridge(x))}" for x in reversed(cx_)) + " Z", "fg-muted", "fg-faint", SECOND, fill_opacity=0.35))
    c.add(line(RX - 34, G - RH + 6, 100, G - RH - 12, "fg-muted", THIN))
    c.add(text(96, G - RH - 8, "cap cloud", 12, "end", "fg-muted", weight=600))
    # streamlines
    specs = [(290, 0.8, 24), (210, 0.55, 30), (130, 0.35, 22)]
    for y0, dec, amp in specs:
        f = stream(y0, dec, amp)
        c.add(path(smooth_path([(x, f(x)) for x in xs[::2]]), "sky-fg", None, SECOND))
        c.add(arrow(26, f(26), 58, f(58), "sky-fg", SECOND))
    c.add(text(26, G - 30, "strong wind, stable air", 12, "start", "sky-fg", weight=600))
    # lenticulars at the crests of the top streamline, rotors beneath the crests at about ridge height
    fu = stream(130, 0.35, 22)
    for cx in (XC, XC + LAM):
        cy = fu(cx) - 2
        c.add(path(f"M{cx - 50} {cy} C{cx - 30} {cy - 16} {cx + 30} {cy - 16} {cx + 50} {cy} C{cx + 30} {cy + 8} {cx - 30} {cy + 8} {cx - 50} {cy} Z",
                   "fg-muted", "surface", SECOND))
        ry = G - RH + 30
        c.add(path(bumpy([(cx - 30, ry + 10), (cx - 32, ry - 4), (cx - 8, ry - 12), (cx + 18, ry - 10), (cx + 32, ry), (cx + 30, ry + 10)], seg=12),
                   "bad", "bad-soft", SECOND))
        c.add(path(f"M{cx + 22} {ry + 22} A24 13 0 1 0 {cx - 22} {ry + 26}", "bad", None, MAIN, arrow_end=True))
    c.add(text(XC + LAM / 2, fu(XC) - 30, "lenticular cloud sits still at the wave crests", 12, "middle", "fg", weight=600))
    c.add(multiline(630, G - 38, ["rotor under each crest, at about", "ridge height: severe turbulence"], 12, "end", "bad", weight=600))
    # lift and sink either side of a crest, and the lee down-draught
    c.add(arrow(XC - 46, G - 116, XC - 30, G - 160, "ok", MAIN), text(XC - 50, G - 150, "lift", 13, "end", "ok-fg", weight=700))
    c.add(arrow(XC + 32, G - 160, XC + 48, G - 116, "bad", MAIN), text(XC + 52, G - 150, "sink", 13, "start", "bad", weight=700))
    c.add(arrow(212, G - 128, 246, G - 60, "bad", MAIN + 0.5))
    c.add(multiline(236, G - 38, ["lee down-draught:", "can beat your climb"], 12, "start", "bad", weight=600))
    # one air parcel riding the middle streamline through the standing wave (the one moving thing)
    fm = stream(210, 0.55, 30)
    css, mk = mover("mwr", [(x, fm(x)) for x in xs[::4]], 7, 0.36, lambda a: circle(0, 0, 5.5, "brand", "surface", 1.5), 48, rotate=False)
    c.style(css)
    c.add(mk)
    # crossing height, upwind of the crest
    c.add(plane_side(RX, 58, 0.34))
    DX = 108
    c.add(line(DX, 70, DX, G - RH, "brand", SECOND), line(DX - 6, 70, DX + 6, 70, "brand", SECOND), line(DX - 6, G - RH, RX - 6, G - RH, "brand", THIN, DASH))
    c.add(text(RX + 34, 62, "cross 2,000 ft or more above the ridge", 12, "start", "brand", weight=700))
    # plan inset: cross at 45 degrees
    y0 = G + 16
    c.add(rect(20, y0, 196, 80, "surface-2", None, rx=8))
    c.add(line(40, y0 + 58, 196, y0 + 24, "fg-muted", MAIN + 2))
    c.add(text(196, y0 + 16, "ridge", 11, "end", "fg-muted"))
    c.add(arrow(70, y0 + 74, 140, y0 + 10, "brand", MAIN))
    c.add(text(30, y0 + 16, "from above:", 11, "start", "fg-muted"))
    c.add(multiline(154, y0 + 50, ["at 45°:", "turn away", "downhill"], 11, "start", "brand", weight=600, leading=1.15))
    c.add(multiline(236, y0 + 18, ["Needs stable air and a wind of about 20 kt or more, within about 30°",
                                   "of perpendicular to the ridge, increasing with height and steady in",
                                   "direction. Dry air can make waves with no cloud at all. Over the crest",
                                   "the altimeter may over-read. Stay upwind of the rotor."], 11, "start", "fg-muted", leading=1.35))
    return c


def aerofoil_pts(x0: float, y0: float, chord: float, n: int = 40, t: float = 0.14) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """NACA-style cambered section, leading edge at (x0, y0), chord along +x. Returns (upper, lower), each from the leading edge back."""
    m, p = 0.02, 0.4
    up, lo = [], []
    for i in range(n + 1):
        x = (1 - math.cos(math.pi * i / n)) / 2
        yt = 5 * t * (0.2969 * math.sqrt(x) - 0.126 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        yc = m / p ** 2 * (2 * p * x - x * x) if x < p else m / (1 - p) ** 2 * (1 - 2 * p + 2 * p * x - x * x)
        up.append((x0 + x * chord, y0 - (yc + yt) * chord))
        lo.append((x0 + x * chord, y0 - (yc - yt) * chord))
    return up, lo


def offset(pts: list[tuple[float, float]], thick, outward: int) -> list[tuple[float, float]]:
    """Offset a surface polyline along its normal by thick(i), outward = -1 for the upper surface, +1 for the lower (screen)."""
    out = []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L * outward, dx / L * outward
        out.append((x + nx * thick(i), y + ny * thick(i)))
    return out


@chart
def airframe_icing_types() -> Canvas:
    c = canvas("Clear ice and rime ice on a wing",
               "Two wing sections with the airflow from the left. Left, clear ice: large supercooled drops, 0 to minus 10 degrees in cumulus and "
               "cumulonimbus or freezing rain, freeze slowly, so the water runs back over the wing before it sets into a hard, heavy, clear sheet: the "
               "most dangerous. Right, rime ice: small supercooled drops, about minus 10 to minus 20 degrees in stratiform cloud, freeze instantly, "
               "trapping air, and build a white, brittle, rough shape forward on the leading edge.", height=396, prefix="ait")
    c.add(text(320, 26, "Why is clear ice worse than rime?", 16, "middle", "fg", weight=700))
    for i, ox in enumerate((14, 326)):
        W = 300
        clear = i == 0
        c.add(rect(ox, 44, W, 218, "surface-2", None, rx=10))
        c.add_defs(f'<clipPath id="ait-clip{i}"><rect x="{ox}" y="44" width="{W}" height="218" rx="10"/></clipPath>')
        c.add(badge(ox + W / 2, 64, "Clear ice: the most dangerous" if clear else "Rime ice", "bad" if clear else "neutral", 13))
        LE, YC, CH = ox + 100, 168, 330
        up, lo = aerofoil_pts(LE, YC, CH, 60, 0.15)
        n = len(up) - 1
        parts = []
        if clear:
            for (dx, dy) in ((-70, -14), (-44, 6), (-76, 20), (-38, -30), (-62, -40)):
                parts.append(line(LE + dx - 18, YC + dy, LE + dx - 7, YC + dy, "sky-fg", THIN))
                parts.append(circle(LE + dx, YC + dy, 5, "sky-fg", None))
            ku, kl = int(0.5 * n), int(0.36 * n)
            ice_u = lambda k: 14 * max(0.0, 1 - k / ku) ** 0.6
            ice_l = lambda k: 10 * max(0.0, 1 - k / kl) ** 0.6
        else:
            for r in range(6):
                for k in range(4):
                    parts.append(circle(LE - 84 + k * 15 + (r % 2) * 7, YC - 34 + r * 13, 1.8, "fg-muted", None))
            ku, kl = int(0.17 * n), int(0.13 * n)
            ice_u = lambda k: (26 * max(0.0, 1 - k / ku) ** 1.2) * (1.3 if k % 2 else 0.7)
            ice_l = lambda k: (22 * max(0.0, 1 - k / kl) ** 1.2) * (1.3 if k % 2 else 0.7)
        iu, il = offset(up, ice_u, -1), offset(lo, ice_l, 1)
        outer = list(reversed(iu[:ku + 1])) + il[1:kl + 1]
        back = " ".join(f"L{fmt(x)} {fmt(y)}" for x, y in reversed(lo[:kl + 1])) + " " + " ".join(f"L{fmt(x)} {fmt(y)}" for x, y in up[1:ku + 1])
        if clear:
            parts.append(path(smooth_path(outer) + " " + back + " Z", "sky-fg", "sky-soft", SECOND))
        else:
            parts.append(path("M" + " L".join(f"{fmt(x)} {fmt(y)}" for x, y in outer) + " " + back + " Z", "fg-muted", "surface", SECOND))
        parts.append(path(smooth_path(up) + " " + " ".join(f"L{fmt(x)} {fmt(y)}" for x, y in reversed(lo)) + " Z", "fg", "surface", MAIN))
        c.add(group(*parts, style=f"clip-path:url(#ait-clip{i})"))
        if clear:
            ux, uy = up[int(0.32 * n)]
            c.add(arrow(LE + 10, uy - 22, ux + 10, uy - 22, "brand", SECOND))
            c.add(multiline(LE + 4, 92, ["water runs back,", "then sets hard"], 12, "start", "brand", weight=600))
            c.add(text(ox + 50, YC + 54, "large drops", 12, "middle", "sky-fg", weight=600))
        else:
            for (bx, by) in ((LE - 10, YC - 6), (LE - 7, YC + 4), (LE - 4, YC - 14), (LE - 12, YC + 10)):
                c.add(circle(bx, by, 1.5, "fg-faint", None))
            c.add(multiline(LE + 4, 92, ["freezes on impact,", "builds forward"], 12, "start", "fg", weight=600))
            c.add(text(ox + 50, YC + 54, "small drops", 12, "middle", "fg-muted", weight=600))
        c.add(arrow(ox + 12, 236, ox + 52, 236, "sky-fg", SECOND), text(ox + 58, 240, "airflow", 11, "start", "sky-fg"))
        lines = (["Large supercooled drops: 0 to −10 °C,", "in Cu and Cb, and freezing rain.", "Freezes slowly: hard, heavy, clear,", "spread back over the wing."]
                 if clear else
                 ["Small supercooled drops: about −10 to", "−20 °C, in stratiform cloud.", "Freezes instantly, trapping air: white,", "brittle and rough, on the leading edge."])
        c.add(multiline(ox + W / 2, 284, lines, 12, "middle", "fg-muted", leading=1.3))
    c.add(multiline(320, 364, ["Either kind adds weight and drag, destroys lift and raises the stall speed.",
                               "A VFR pilot stays out of cloud and notes the freezing level in the GAF."], 11, "middle", "fg-faint"))
    return c


@chart
def thunderstorm_life_cycle() -> Canvas:
    c = canvas("The three stages of a thunderstorm",
               "Three side views of the same storm cell over time. Cumulus stage, about 15 minutes: a growing towering cumulus with updraughts "
               "throughout and no rain at the surface yet. Mature stage, about 15 to 30 minutes, the most dangerous: it begins when rain reaches the "
               "ground; updraughts and down-draughts side by side, a cumulonimbus with an anvil, heavy rain, hail, lightning and a gust front "
               "spreading out ahead. Dissipating stage: down-draughts throughout, the rain easing and the anvil left behind.",
               height=446, prefix="tlc")
    c.style(flow_style("tlc", 1.0, "7 6"))
    c.add(text(320, 26, "A thunderstorm's life: which stage is most dangerous?", 16, "middle", "fg", weight=700))
    G = 318
    W = 200
    xs = (14, 220, 426)
    c.add(line(14, G, 626, G, "fg-muted", SECOND))
    for ox in xs:
        c.add(rect(ox, 44, W, G - 44, "sky-soft", None, rx=8, fill_opacity=0.5))
    c.add(line(14, G, 626, G, "fg-muted", SECOND))
    # 1 cumulus stage
    ox = xs[0]
    c.add(path(bumpy([(ox + 56, 236), (ox + 50, 190), (ox + 66, 132), (ox + 100, 118), (ox + 134, 132), (ox + 150, 190), (ox + 144, 236)], seg=20),
               "fg-muted", "surface", SECOND))
    for x in (ox + 78, ox + 100, ox + 122):
        c.add(path(f"M{x} {G - 6} L{x} 140", "warn", None, MAIN, cls="tlc-flow", arrow_end=True))
    c.add(text(ox + 100, 70, "no rain at the", 12, "middle", "fg-muted"))
    c.add(text(ox + 100, 86, "surface yet", 12, "middle", "fg-muted"))
    # 2 mature stage
    ox = xs[1]
    c.add(cb(ox + 44, 214, ox + 150, 66, ox + 22, ox + 196, "bad", "surface", MAIN))
    c.add(path(f"M{ox + 72} {G - 6} L{ox + 72} 96", "warn", None, MAIN, cls="tlc-flow", arrow_end=True))
    c.add(path(f"M{ox + 124} 120 L{ox + 124} {G - 22} Q{ox + 124} {G - 8} {ox + 140} {G - 8} L{ox + 192} {G - 8}", "info", None, MAIN, cls="tlc-flow",
               arrow_end=True))
    c.add(rain(ox + 108, ox + 150, 220, G - 2, 5, "sky-fg", -4))
    for hx, hy in ((ox + 100, 160), (ox + 112, 176), (ox + 96, 186)):
        c.add(circle(hx, hy, 3, "surface", "info", SECOND))
    c.add(polygon([(ox + 150, 120), (ox + 140, 140), (ox + 148, 140), (ox + 138, 162), (ox + 160, 134), (ox + 151, 134), (ox + 158, 120)], "warn-soft", "warn", THIN))
    c.add(text(ox + 194, G - 30, "gust front", 11, "end", "bad", weight=600))
    c.add(text(ox + 60, G + 0 - 70, "up", 11, "end", "warn-fg", weight=600))
    c.add(text(ox + 136, G - 70, "down", 11, "start", "info", weight=600))
    # 3 dissipating stage
    ox = xs[2]
    c.add(path(f"M{ox + 30} 78 C{ox + 30} 64 {ox + 60} 60 {ox + 110} 62 L{ox + 186} 66 C{ox + 196} 70 {ox + 190} 82 {ox + 176} 84 "
               f"C{ox + 130} 90 {ox + 70} 94 {ox + 40} 92 C{ox + 30} 90 {ox + 28} 84 {ox + 30} 78 Z", "fg-muted", "surface", SECOND))
    c.add(path(bumpy([(ox + 60, 230), (ox + 56, 170), (ox + 80, 132), (ox + 120, 128), (ox + 140, 170), (ox + 140, 230)], seg=24), "fg-muted", "surface",
               SECOND, dash="5 4"))
    for x in (ox + 82, ox + 118):
        c.add(path(f"M{x} 140 L{x} {G - 8}", "info", None, MAIN, cls="tlc-flow", arrow_end=True))
    c.add(rain(ox + 70, ox + 130, 234, G - 4, 3, "sky-fg", -4))
    c.add(text(ox + 110, 108, "anvil left behind", 11, "middle", "fg-muted"))
    # labels under each panel
    heads = [("Cumulus", "neutral", "about 15 min", ["updraughts throughout,", "growing TCu"]),
             ("Mature: most dangerous", "bad", "about 15 to 30 min", ["starts when rain reaches", "the ground; up- and", "down-draughts, hail,", "lightning, gust front"]),
             ("Dissipating", "neutral", "", ["down-draughts throughout,", "rain easing"])]
    for ox, (h, tone, dur, lines) in zip(xs, heads):
        c.add(badge(ox + W / 2, G + 20, h, tone, 12))
        if dur:
            c.add(text(ox + W / 2, G + 42, dur, 11, "middle", "fg", weight=600, cls="num"))
        c.add(multiline(ox + W / 2, G + 60, lines, 11, "middle", "fg-muted", leading=1.25))
    c.add(arrow(160, 36, 480, 36, "fg-faint", SECOND))
    c.add(text(490, 40, "time", 11, "start", "fg-faint"))
    return c


@chart
def fog_types() -> Canvas:
    c = canvas("Four kinds of fog and what clears each",
               "Four panels. Radiation fog: on a clear night with a light wind the ground radiates its heat and cools moist air to its dew point, "
               "and fog pools in the valleys; the sun or a stronger wind clears it. Advection or sea fog: moist air moves over a colder sea and is "
               "cooled from below, day or night with moderate winds, and drifts onto the coast; only a change of wind direction clears it. Frontal fog: "
               "rain from the warm air above a front falls into the cold air below and saturates it; it clears when the front passes. Steaming fog: very "
               "cold air flows over much warmer water and evaporation saturates it; heating clears it.", height=500, prefix="fgt")
    c.add(text(320, 26, "Four kinds of fog: what makes each, and what clears it", 16, "middle", "fg", weight=700))
    W, H = 300, 148
    origins = [(14, 46), (326, 46), (14, 278), (326, 278)]
    heads = ["Radiation fog", "Advection (sea) fog", "Frontal fog", "Steaming fog (sea smoke)"]
    makes = ["clear night, light wind, moist air; pools in valleys",
             "moist air over a colder sea; day or night",
             "rain evaporates into the cold air below",
             "very cold air over much warmer water"]
    clears = ["clears: sun heating the ground, or more wind",
              "clears: only a change of wind direction",
              "clears: when the front passes",
              "clears: heating, or the air warming"]
    for i, (ox, oy) in enumerate(origins):
        night = i == 0
        c.add(rect(ox, oy, W, H, "surface-2" if night else "sky-soft", None, rx=8, fill_opacity=1 if night else 0.55))
        gy = oy + H - 26
        if i == 0:
            g = [(ox, gy - 40), (ox + 60, gy - 36), (ox + 110, gy - 4), (ox + 190, gy - 4), (ox + 240, gy - 36), (ox + W, gy - 44)]
            c.add(rect(ox + 70, gy - 34, 160, 34, "brand-soft", "brand", SECOND, rx=12))
            c.add(path(smooth_path(g) + f" L{ox + W} {oy + H} L{ox} {oy + H} Z", "fg-muted", "surface", SECOND))
            c.add(text(ox + 150, gy - 14, "fog", 13, "middle", "brand-fg", weight=700))
            c.add(moon(ox + W - 34, oy + 28, 10))
            for sx, sy in ((ox + 30, oy + 22), (ox + 70, oy + 40), (ox + 120, oy + 18), (ox + 190, oy + 34)):
                c.add(circle(sx, sy, 1.6, "fg-muted", None))
            for wx in (ox + 30, ox + 266):
                c.add(path(f"M{wx} {gy - 50} q-4 -6 0 -12 q4 -6 0 -12 q-4 -6 0 -12", "info", None, SECOND, arrow_end=True))
            c.add(text(ox + 44, oy + 66, "heat radiates away", 11, "start", "info"))
        elif i == 1:
            c.add(rect(ox, gy, 190, oy + H - gy, "sky-soft", None))
            c.add(text(ox + 10, oy + H - 8, "cold sea", 11, "start", "sky-fg", weight=600))
            c.add(path(f"M{ox + 190} {gy} L{ox + 204} {gy - 8} L{ox + W} {gy - 8} L{ox + W} {oy + H} L{ox + 190} {oy + H} Z", "fg-muted", "surface", SECOND))
            c.add(rect(ox + 214, gy - 13, 72, 5, "tarmac", None))
            c.add(text(ox + 250, gy + 14, "coastal aerodrome", 11, "middle", "fg-muted"))
            c.add(rect(ox + 16, gy - 44, 226, 38, "brand-soft", "brand", SECOND, rx=14, fill_opacity=0.9))
            c.add(text(ox + 126, gy - 20, "fog bank drifts ashore", 12, "middle", "brand-fg", weight=600))
            c.add(sun(ox + W - 30, oy + 30, 10, "warn"))
            c.add(arrow(ox + 24, oy + 44, ox + 110, oy + 44, "sky-fg", MAIN))
            c.add(text(ox + 24, oy + 30, "moist onshore wind", 11, "start", "sky-fg", weight=600))
            c.add(text(ox + W - 14, oy + 66, "sun does little", 11, "end", "fg-muted"))
        elif i == 2:
            fy = lambda x: gy - (x - ox) * 98 / W
            c.add(path(f"M{ox} {gy} L{ox + W} {gy - 98} L{ox + W} {gy} Z", None, "sky-soft", 0))
            c.add(path(f"M{ox + 60} {fy(ox + 60) - 8} L{ox + 280} {fy(ox + 280) - 8} L{ox + 280} {fy(ox + 280) - 30} L{ox + 60} {fy(ox + 60) - 36} Z",
                       "fg-muted", "surface-2", SECOND))
            c.add(path(f"M{ox} {gy} L{ox + W} {gy - 98}", "bad", None, MAIN))
            for x in range(ox + 90, ox + 250, 26):
                c.add(line(x, fy(x) - 6, x - 10, gy - 18, "sky-fg", THIN, DASH))
            c.add(rect(ox + 100, gy - 16, 180, 16, "brand-soft", "brand", SECOND, rx=8))
            c.add(text(ox + 24, oy + 26, "warm air above the front", 11, "start", "warn-fg", weight=600))
            c.add(text(ox + W - 12, gy - 26, "cold air", 11, "end", "sky-fg", weight=600))
            c.add(text(ox + 190, gy + 16, "fog ahead of the front", 11, "middle", "brand-fg", weight=600))
        else:
            c.add(rect(ox, gy, W, oy + H - gy, "warn-soft", None))
            c.add(text(ox + W / 2, oy + H - 8, "much warmer water", 11, "middle", "warn-fg", weight=600))
            for k in range(7):
                x = ox + 30 + k * 38
                c.add(path(f"M{x} {gy - 4} q-6 -10 0 -20 q6 -10 0 -20", "brand", None, SECOND))
            c.add(rect(ox + 16, gy - 26, W - 32, 22, "brand-soft", None, rx=10, fill_opacity=0.7))
            c.add(text(ox + W / 2, gy - 52, "shallow wisps of fog rise off the water", 11, "middle", "brand-fg", weight=600))
            c.add(arrow(ox + 24, oy + 30, ox + 130, oy + 30, "info", MAIN))
            c.add(text(ox + 140, oy + 34, "very cold air", 11, "start", "info", weight=600))
        c.add(line(ox, gy, ox + W, gy, "fg-muted", THIN) if i in (2,) else "")
        c.add(badge(ox + W / 2, oy + H + 16, heads[i], "brand", 12))
        c.add(text(ox + W / 2, oy + H + 38, makes[i], 11, "middle", "fg-muted"))
        c.add(text(ox + W / 2, oy + H + 54, clears[i], 11, "middle", "fg", weight=600))
    return c


# ================================================================ PMTC 2.5 winds
@chart
def highs_and_lows_southern_hemisphere() -> Canvas:
    c = canvas("Which way the wind goes round highs and lows in the Southern Hemisphere",
               "Plan view, north up. Around a high the wind blows anticlockwise along the isobars; the air in it sinks, giving fine, stable weather. "
               "Around a low the wind blows clockwise; air converges and rises, giving cloud and rain. Below, the reason: between a high to the north "
               "and a low to the south the pressure gradient force pulls the air south, Coriolis deflects moving air to its left, and the two balance "
               "when the wind blows east along the isobars: a westerly, with the low on its right.", height=450, prefix="hls")
    c.add(text(320, 26, "Southern Hemisphere: anticlockwise round a high, clockwise round a low", 15, "middle", "fg", weight=700))
    for cx, high in ((164, True), (476, False)):
        cy = 148
        for k, (rx, ry) in enumerate(((128, 86), (92, 62), (54, 36))):
            c.add(ellipse(cx, cy, rx, ry, None, "line-strong", SECOND))
        ring = anticlockwise_ring if high else clockwise_ring
        c.add(ring(cx, cy, 110, 74, "brand", MAIN, -30 if high else 210, 290))
        c.add(ring(cx, cy, 72, 49, "brand", MAIN, 150 if high else 30, 280))
        c.add(text(cx, cy + 9, "H" if high else "L", 26, "middle", "fg", weight=700))
        c.add(badge(cx, cy + 108, "High: anticlockwise" if high else "Low: clockwise", "brand", 13))
        c.add(text(cx, cy + 132, "air sinks: fine, stable, light winds" if high else "air converges and rises: cloud, rain", 12, "middle", "fg-muted"))
    c.add(north_arrow(620, 64, 18))
    # why: the balance between PGF and Coriolis
    top, bot = 326, 420
    c.add(rect(14, 296, 612, 142, "surface-2", None, rx=10))
    c.add(text(28, 316, "Why: the forces on a parcel between a high to the north and a low to the south", 12, "start", "fg", weight=700))
    c.add(line(28, top, 466, top, "line-strong", SECOND), line(28, bot, 466, bot, "line-strong", SECOND))
    c.add(text(36, top + 16, "higher pressure (the high is north)", 11, "start", "fg-muted"))
    c.add(text(36, bot - 6, "lower pressure (the low is south)", 11, "start", "fg-muted"))
    PX, PY = 300, 373
    c.add(arrow(PX, PY + 4, PX, PY + 38, "info", MAIN), text(PX + 8, PY + 32, "pressure gradient force", 11, "start", "info", weight=600))
    c.add(arrow(PX, PY - 4, PX, PY - 38, "warn", MAIN), text(PX + 8, PY - 26, "Coriolis: left of the wind", 11, "start", "warn-fg", weight=600))
    c.add(arrow(PX - 150, PY, PX - 10, PY, "brand", MAIN + 1), text(PX - 156, PY + 4, "wind", 12, "end", "brand", weight=700))
    c.add(circle(PX, PY, 5, "brand", "surface", 1.5))
    c.add(multiline(492, 346, ["The two balance when", "the wind blows along", "the isobars: a westerly.", "Back to the wind,", "the low is on your right."], 11, "start", "fg", leading=1.4))
    return c


# ================================================================ PMTC 2.1 the atmosphere
@chart
def atmosphere_layers_and_tropopause() -> Canvas:
    c = canvas("The layers of the atmosphere, defined by temperature",
               "Chart of ISA temperature against height. Through the troposphere the temperature falls about 2 degrees per 1,000 ft, from 15 degrees "
               "at sea level to minus 56.5 at the tropopause, 36,090 ft. In the lower stratosphere it stays at minus 56.5 to about 65,600 ft, then "
               "rises because the ozone layer absorbs ultraviolet. A cumulonimbus rises through the troposphere and spreads into an anvil at the "
               "tropopause lid. The tropopause is about 26,000 ft over the poles, 36,000 ft in mid-latitudes and 52,000 to 59,000 ft over the equator.",
               height=440, prefix="alt")
    c.add(text(320, 26, "Temperature with height: troposphere, tropopause, stratosphere", 15, "middle", "fg", weight=700))
    ch = Chart(c, (-70, 20), (0, 70000), box=(84, 52, 440, 380), xlabel="ISA temperature, °C", ylabel="Height, ft",
               xticks=[-60, -40, -20, 0, 20], yticks=[0, 10000, 20000, 30000, 40000, 50000, 60000, 70000],
               xfmt=lambda v: f"{int(v)}°", yfmt=lambda v: f"{int(v):,}")
    TP = 36090
    c.add(rect(84, ch.py(TP), 356, 380 - ch.py(TP), "sky-soft", None, fill_opacity=0.6))
    c.add(ch.axes())
    c.add(ch.curve([(15, 0), (-56.5, TP)], "brand", MAIN + 0.5, smooth=False))
    c.add(ch.curve([(-56.5, TP), (-56.5, 65600), (-55.2, 70000)], "brand", MAIN + 0.5, smooth=False))
    c.add(line(84, ch.py(TP), 620, ch.py(TP), "brand", SECOND, DASH))
    c.add(ch.point(15, 0, "brand"), ch.point(-56.5, TP, "brand"))
    c.add(num(ch.px(15) - 8, ch.py(0) - 10, "15 °C at sea level", 12, "end", "brand-fg", weight=600))
    c.add(text(ch.px(-56.5) + 12, ch.py(TP) - 8, "tropopause: 36,090 ft, −56.5 °C", 12, "start", "brand-fg", weight=700))
    c.add(multiline(ch.px(-67), ch.py(15000), ["Troposphere", "falls about 2 °C per 1,000 ft;", "nearly all the water vapour", "and the weather"], 12, "start", "fg",
                    leading=1.3))
    c.add(multiline(ch.px(-50), ch.py(58000), ["Stratosphere", "−56.5 °C to about 65,600 ft, then", "rising (ozone absorbs UV); dry, stable"], 12, "start", "fg",
                    leading=1.3))
    # a Cb hitting the lid
    c.add(cb(462, 376, 512, ch.py(TP) + 4, 448, 590, "fg-muted", "surface-2", SECOND))
    c.add(line(452, 380, 626, 380, "fg-muted", SECOND))
    c.add(text(446, ch.py(TP) + 22, "the lid: a Cb's anvil spreads out", 11, "end", "fg-muted", weight=600))
    # tropopause height by latitude
    c.add(text(620, ch.py(70000) + 4, "Tropopause height:", 11, "end", "fg", weight=700))
    for h0, h1, lab in ((52000, 59000, "equator 52,000–59,000"), (36000, 36000, "mid-latitudes (Perth) 36,000"), (26000, 26000, "poles 26,000")):
        y0, y1 = ch.py(h0), ch.py(h1)
        c.add(rect(604, y1, 14, max(3, y0 - y1), "brand-soft", "brand", THIN))
        c.add(text(598, (y0 + y1) / 2 + (-8 if h0 == 36000 else 4), lab, 11, "end", "fg-muted"))
    c.add(text(320, 432, "ISA values. The stratosphere continues to about 50 km; the tropopause is higher in summer.", 11, "middle", "fg-faint"))
    return c
