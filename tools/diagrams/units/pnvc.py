"""PNVC (navigation) diagrams. Every number comes from the notes in content/notes/PNVC/; where a note hedges, the
diagram hedges."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, arc_path, arrow, circle, ellipse, fmt, group, line, multiline,
                                num, path, plane_side, plane_top, polygon, polyline, rect, text)

SOFT = {"brand": "brand-soft", "ok": "ok-soft", "warn": "warn-soft", "bad": "bad-soft", "info": "info-soft", "sky": "sky-soft", "fg": "surface-2"}
FG = {"brand": "brand-fg", "ok": "ok-fg", "warn": "warn-fg", "bad": "bad-fg", "info": "info-fg", "sky": "sky-fg", "fg": "fg"}
EDGE = {"brand": "brand", "ok": "ok", "warn": "warn", "bad": "bad", "info": "info", "sky": "sky-fg", "fg": "line-strong"}


def card(x: float, y: float, w: float, h: float, title: str | None, lines: list[str], tone: str = "fg", size: float = 12.5,
         title_size: float = 14, leading: float = 1.4, pad: float = 12, mono: bool = False) -> str:
    """Rounded panel with a bold title and body lines in the tone's ink."""
    out = rect(x, y, w, h, SOFT[tone], EDGE[tone], SECOND, rx=8)
    yy = y + pad + title_size * 0.85
    if title:
        out += text(x + pad, yy, title, title_size, "start", FG[tone], weight=700)
        yy += title_size * 0.5 + size * 1.05
    else:
        yy = y + pad + size * 0.9
    ink = FG[tone] if tone != "fg" else "fg-muted"
    for i, s in enumerate(lines):
        out += text(x + pad, yy + i * size * leading, s, size, "start", ink, cls="num" if mono else None)
    return out


def pol(cx: float, cy: float, r: float, bearing: float) -> tuple[float, float]:
    """Point at distance r on a compass bearing (0 = up the page, clockwise)."""
    a = math.radians(bearing)
    return cx + r * math.sin(a), cy - r * math.cos(a)


def barc(cx: float, cy: float, r: float, b0: float, b1: float) -> str:
    """Arc path between two compass bearings, clockwise from b0 to b1 (b1 > b0)."""
    return arc_path(cx, cy, r, b0 - 90, b1 - 90)


# ================================================================ 2.1 Form of the earth
def _ortho(lat: float, lon: float, lat0: float, lon0: float, cx: float, cy: float, R: float) -> tuple[float, float, bool]:
    la, lo, la0 = math.radians(lat), math.radians(lon - lon0), math.radians(lat0)
    x = R * math.cos(la) * math.sin(lo)
    y = R * (math.cos(la0) * math.sin(la) - math.sin(la0) * math.cos(la) * math.cos(lo))
    vis = math.sin(la0) * math.sin(la) + math.cos(la0) * math.cos(la) * math.cos(lo) > 0
    return cx + x, cy - y, vis


def _vec(lat: float, lon: float) -> tuple[float, float, float]:
    la, lo = math.radians(lat), math.radians(lon)
    return math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)


def _latlon(v: tuple[float, float, float]) -> tuple[float, float]:
    x, y, z = v
    return math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))


@chart
def great_circle_vs_rhumb_line() -> Canvas:
    c = Canvas("Great circle and rhumb line between the same two points",
               "A globe seen from above the Southern Ocean with converging meridians. Two points on the same southern parallel are "
               "joined two ways. The great circle, the shortest path, bulges towards the South Pole and cuts each meridian at a "
               "different angle. The rhumb line follows the parallel, crossing every meridian at the same angle; it is a little "
               "longer and bows towards the equator compared with the great circle.", height=430, prefix="gcr")
    lat0, lon0, cx, cy, R = -52.0, 0.0, 210.0, 228.0, 180.0
    P = lambda la, lo: _ortho(la, lo, lat0, lon0, cx, cy, R)  # noqa: E731
    c.add(circle(cx, cy, R, "sky-soft", "line-strong", SECOND))
    # graticule: parallels every 15 degrees, meridians every 20 degrees
    for la in (-75, -60, -45, -30, -15, 0, 15, 30):
        pts = [P(la, lo) for lo in range(-180, 181, 3)]
        segs, cur = [], []
        for x, y, v in pts:
            if v:
                cur.append((x, y))
            elif cur:
                segs.append(cur)
                cur = []
        if cur:
            segs.append(cur)
        for s in segs:
            if len(s) > 1:
                c.add(polyline(s, "fg-muted" if la == 0 else "line-strong", SECOND if la == 0 else THIN, fill="none"))
    for lo in range(-180, 180, 20):
        s = [(x, y) for x, y, v in (P(la, lo) for la in range(-90, 91, 2)) if v]
        if len(s) > 1:
            c.add(polyline(s, "line-strong", THIN, fill="none"))
    ex, ey, _ = P(0, -38)
    c.add(text(ex - 4, ey - 8, "Equator", 12, "middle", "fg-muted", weight=600, rotate=-12))
    px, py, _ = P(-90, 0)
    c.add(circle(px, py, 3.5, "fg", None))
    c.add(text(px, py + 18, "South Pole", 12, "middle", "fg-muted", weight=600))
    # the two points and the two paths
    la_ab, lo_a, lo_b = -40.0, -55.0, 55.0
    va, vb = _vec(la_ab, lo_a), _vec(la_ab, lo_b)
    omega = math.acos(sum(p * q for p, q in zip(va, vb)))
    gc = []
    for i in range(61):
        t = i / 60
        k1, k2 = math.sin((1 - t) * omega) / math.sin(omega), math.sin(t * omega) / math.sin(omega)
        la, lo = _latlon(tuple(k1 * p + k2 * q for p, q in zip(va, vb)))
        gc.append(P(la, lo)[:2])
    rh = [P(la_ab, lo)[:2] for lo in [lo_a + (lo_b - lo_a) * i / 60 for i in range(61)]]
    c.add(polyline(rh, "info", MAIN, dash="7 4", fill="none"))
    c.add(polyline(gc, "brand", 3, fill="none"))
    # angle marks where each path crosses three meridians
    for lo in (-40, 0, 40):
        # rhumb crossing: a small square-ish right-angle tick shows the constant angle
        x0, y0, _ = P(la_ab, lo)
        c.add(circle(x0, y0, 3, "info", "surface", 1.2))
    for lo in (-40, 0, 40):
        # find the great-circle point on this meridian
        best = min(range(61), key=lambda i: abs(_latlon(tuple((math.sin((1 - i / 60) * omega) * p + math.sin(i / 60 * omega) * q) / math.sin(omega) for p, q in zip(va, vb)))[1] - lo))
        x0, y0 = gc[best]
        c.add(circle(x0, y0, 3, "brand", "surface", 1.2))
    ax, ay = rh[0]
    bx, by = rh[-1]
    for x, y, s in ((ax, ay, "A"), (bx, by, "B")):
        c.add(circle(x, y, 6, "fg", "surface", 2))
        c.add(text(x + (-14 if s == "A" else 14), y + 5, s, 15, "end" if s == "A" else "start", "fg", weight=700))
    mx, my = gc[30]
    c.add(text(mx, my + 22, "great circle", 13, "middle", "brand-fg", weight=700))
    rx, ry = rh[30]
    c.add(text(rx, ry - 12, "rhumb line", 13, "middle", "info-fg", weight=700))
    # right-hand explanation
    c.add(card(410, 34, 216, 132, "Great circle", ["Shortest path: a string pulled", "tight on the globe.", "Cuts each meridian at a", "different angle, so the", "direction keeps changing."], "brand"))
    c.add(card(410, 178, 216, 132, "Rhumb line", ["Same angle to every meridian:", "a constant true track.", "Easy to steer, a little longer;", "bows towards the equator", "compared with the great circle."], "info"))
    c.add(card(410, 322, 216, 92, "On your WAC", ["Lambert conformal conic:", "a ruled straight line is very", "close to a great circle."], "fg"))
    c.add(text(28, 30, "Meridians converge, so the shortest path turns", 13, "start", "fg-muted", weight=600))
    return c


@chart
def mh_rb_mb_bearings() -> Canvas:
    c = Canvas("Magnetic heading plus relative bearing gives magnetic bearing",
               "Plan view. Magnetic north is up. The aeroplane heads 070 degrees magnetic. A lake lies 30 degrees left of the nose, "
               "which is a relative bearing of 330, measured clockwise from the nose all the way round. Heading 070 plus relative "
               "bearing 330 is 400; take off 360 and the magnetic bearing to the lake is 040. The bearing from the lake back to the "
               "aeroplane is the reciprocal, 220 magnetic.", height=440, prefix="mrb")
    cx, cy = 210, 236
    # compass ring
    c.add(circle(cx, cy, 168, "surface-2", "line-strong", THIN))
    for b in range(0, 360, 10):
        r0 = 160 if b % 30 else 152
        x0, y0 = pol(cx, cy, r0, b)
        x1, y1 = pol(cx, cy, 168, b)
        c.add(line(x0, y0, x1, y1, "fg-faint", THIN))
    for b, s in ((0, "N"), (90, "E"), (180, "S"), (270, "W")):
        x, y = pol(cx, cy, 140, b)
        c.add(text(x, y + 5, s, 14, "middle", "fg-muted", weight=700))
    # magnetic north reference
    nx, ny = pol(cx, cy, 168, 0)
    c.add(arrow(cx, cy, nx, ny - 14, "fg", SECOND))
    c.add(text(nx, ny - 20, "Magnetic north", 12.5, "middle", "fg", weight=700))
    # heading line (nose)
    hx, hy = pol(cx, cy, 160, 70)
    c.add(line(cx, cy, hx, hy, "info", MAIN, dash="7 4"))
    # lake on bearing 040
    lx, ly = pol(cx, cy, 120, 40)
    c.add(ellipse(lx, ly, 24, 13, "sky-soft", "sky-fg", SECOND, transform=f"rotate(-25 {fmt(lx)} {fmt(ly)})"))
    c.add(text(lx + 4, ly - 20, "lake", 12.5, "middle", "sky-fg", weight=700))
    c.add(line(cx, cy, *pol(cx, cy, 94, 40), "ok", MAIN))
    c.add(path(f"M{fmt(pol(cx, cy, 94, 40)[0])} {fmt(pol(cx, cy, 94, 40)[1])} L{fmt(pol(cx, cy, 98, 40)[0])} {fmt(pol(cx, cy, 98, 40)[1])}", "ok", None, MAIN, arrow_end=True))
    # reciprocal from the lake back through the aeroplane
    rx, ry = pol(cx, cy, 104, 220)
    c.add(line(cx, cy, rx, ry, "fg-faint", SECOND, dash=DASH))
    c.add(multiline(150, 352, ["from the lake", "to you: 220°M"], 12, "middle", "fg-muted", 1.3))
    # arcs: MH (info), RB (brand, wraps past north), MB (ok)
    c.add(path(barc(cx, cy, 44, 0, 70), "info", None, 2.5, arrow_end=True))
    c.add(path(barc(cx, cy, 66, 70, 400), "brand", None, 2.5, arrow_end=True))
    c.add(path(barc(cx, cy, 30, 0, 40), "ok", None, 2.5, arrow_end=True))
    tx, ty = pol(cx, cy, 52, 98)
    c.add(text(tx + 2, ty + 4, "MH 070", 12.5, "start", "info-fg", weight=700, cls="num"))
    tx, ty = pol(cx, cy, 82, 290)
    c.add(text(tx - 2, ty + 4, "RB 330", 13, "end", "brand-fg", weight=700, cls="num"))
    c.add(text(cx - 4, cy - 34, "MB 040", 12, "end", "ok-fg", weight=700, cls="num"))
    c.add(group(plane_top(0, 0, 0.55, heading=70, color="fg", fill="surface"), transform=f"translate({cx} {cy})"))
    # nose label
    c.add(text(hx + 6, hy + 4, "nose", 12.5, "start", "info-fg", weight=600))
    # arithmetic panel
    X = 418
    c.add(text(X, 44, "Heading 070°M, lake", 15, "start", "fg", weight=700))
    c.add(text(X, 64, "30° left of the nose", 15, "start", "fg", weight=700))
    rows = [("info", "MH", "070", "north to the nose"), ("brand", "RB", "330", "nose to the lake, clockwise"),
            ("fg", "sum", "400", "more than 360, so"), ("ok", "MB", "040°M", "400 − 360: north to the lake")]
    y = 92
    for tone, k, v, note in rows:
        c.add(rect(X, y, 206, 52, SOFT[tone], EDGE[tone], THIN, rx=8))
        c.add(text(X + 12, y + 22, k, 13, "start", FG[tone], weight=700))
        c.add(num(X + 194, y + 23, v, 16, "end", FG[tone], weight=700))
        c.add(text(X + 12, y + 41, note, 11.5, "start", FG[tone] if tone != "fg" else "fg-muted"))
        y += 60
    c.add(multiline(X, y + 12, ["30° left of the nose is", "360 − 30 = 330 relative,", "never −30.", "Reciprocal ± 180 gives the", "line to plot from the lake."], 12.5, "start", "fg-muted", 1.4))
    return c


# ================================================================ 2.2 Time
@chart
def lmt_vs_wst_longitude() -> Canvas:
    c = Canvas("How far each WA town's sun time sits from WST",
               "A west to east strip of longitude from 114 to 122 degrees east. WST is the local mean time of the 120 degrees east "
               "meridian, UTC plus 8. Each degree of longitude is 4 minutes. Geraldton at 114 42 E runs about 21 minutes behind WST, "
               "Bunbury at 115 40 E about 17, Perth Airport at 115 58 E about 16, and Kalgoorlie at 121 28 E about 6 minutes ahead. "
               "Below, the Perth worked example: 1815 LMT minus 7 hours 44 is 1031 UTC, plus 8 hours is 1831 WST, the same as 1815 "
               "plus 16 minutes.", height=440, prefix="lmt")
    x0, x1, l0, l1 = 50.0, 610.0, 114.0, 122.0
    X = lambda lon: x0 + (lon - l0) / (l1 - l0) * (x1 - x0)  # noqa: E731
    ay = 196
    c.add(text(28, 30, "LMT is the sun's time on your own meridian; WST is the LMT of 120°E", 14, "start", "fg", weight=700))
    c.add(text(28, 50, "4 minutes for every degree of longitude: west of 120°E the sun runs late by the clock", 12.5, "start", "fg-muted"))
    # axis with degree ticks
    c.add(line(x0, ay, x1, ay, "fg-muted", SECOND, cap="butt"))
    for d in range(114, 123):
        c.add(line(X(d), ay - 5, X(d), ay + 5, "fg-muted", THIN))
        c.add(num(X(d), ay + 22, f"{d}°E", 11.5, "middle", "fg-muted"))
    c.add(text(x0, ay + 44, "← west", 12, "start", "fg-faint", weight=600))
    c.add(text(x1, ay + 44, "east: sees the sun first →", 12, "end", "fg-faint", weight=600))
    # one-degree bracket
    c.add(line(X(117), ay + 32, X(118), ay + 32, "fg-muted", SECOND))
    c.add(text((X(117) + X(118)) / 2, ay + 48, "1° = 4 min", 12, "middle", "fg-muted", weight=600))
    # zone meridian
    zx = X(120)
    c.add(line(zx, 72, zx, ay + 8, "brand", MAIN))
    c.add(rect(zx - 70, 66, 140, 36, "brand-soft", "brand", THIN, rx=8))
    c.add(text(zx, 82, "120°E zone meridian", 12, "middle", "brand-fg", weight=700))
    c.add(num(zx, 96, "WST = UTC + 8", 12, "middle", "brand-fg", weight=700))
    towns = [("Geraldton", 114 + 42 / 60, "21 min behind", 116), ("Bunbury", 115 + 40 / 60, "17 min behind", 140),
             ("Perth", 115 + 58 / 60, "16 min behind", 164), ("Kalgoorlie", 121 + 28 / 60, "6 min ahead", 164)]
    for name, lon, gap, y in towns:
        x = X(lon)
        tone = "ok" if "ahead" in gap else "warn"
        c.add(line(x, y + 6, x, ay, "fg-faint", THIN, dash=DASH))
        c.add(circle(x, ay, 5, "fg", "surface", 2))
        c.add(line(x, y, zx, y, EDGE[tone], 5, cap="butt", opacity=0.5))
        if lon < 120:
            c.add(text(x - 8, y + 4, name, 13, "end", "fg", weight=700))
        else:
            c.add(text(x - 8, y + 22, name, 13, "end", "fg", weight=700))
        mid = (x + zx) / 2
        c.add(num(mid, y - 6, gap, 11.5, "middle", FG[tone], weight=700))
    # worked chain for Perth
    yb = 300
    c.add(text(28, yb - 8, "Perth end of daylight: graph says 1815 LMT", 13.5, "start", "fg", weight=700))
    steps = [("1815 LMT", "graph reading", "fg"), ("1031 UTC", "− 7 h 44 arc to time", "info"), ("1831 WST", "+ 8 h zone", "brand")]
    bx = 28
    for i, (val, note, tone) in enumerate(steps):
        c.add(rect(bx, yb + 4, 158, 56, SOFT[tone], EDGE[tone], SECOND, rx=8))
        c.add(num(bx + 79, yb + 30, val, 17, "middle", FG[tone], weight=700))
        c.add(text(bx + 79, yb + 49, note, 11.5, "middle", FG[tone] if tone != "fg" else "fg-muted"))
        if i < 2:
            c.add(arrow(bx + 162, yb + 32, bx + 196, yb + 32, "fg-muted", SECOND))
        bx += 200
    c.add(text(28, yb + 90, "Shortcut check: Perth LMT runs about 16 min behind WST, so 1815 + 16 min = 1831 WST.", 12.5, "start", "fg-muted"))
    c.add(text(28, yb + 110, "Day VFR: on the ground 10 minutes before, by 1821 WST.", 12.5, "start", "fg-muted"))
    # the sun drifting west across the strip (one moving element)
    c.style(".lmt-sun { animation: lmt-move 8s linear infinite; } @keyframes lmt-move { from { transform: translateX(0); } to { transform: translateX(-470px); } }")
    c.add(group(group(circle(0, 0, 9, "warn-soft", "warn", MAIN),
                      *[line(13 * math.cos(math.radians(a)), 13 * math.sin(math.radians(a)), 17 * math.cos(math.radians(a)), 17 * math.sin(math.radians(a)), "warn", SECOND) for a in range(0, 360, 45)],
                      cls="lmt-sun"), transform=f"translate({fmt(X(121.5))} {ay + 72})"))
    return c


# ================================================================ 2.3 Extracting information
@chart
def terrain_safe_altitude() -> Canvas:
    c = Canvas("From tints, spot heights and obstacles to a cruising height",
               "Side view along a leg. The terrain rises into the highest tint band, whose upper limit is 2,000 ft. A hilltop spot "
               "height of 2,140 ft stands above the band, and an obstacle a mile off track is marked 2,310 (290): its top is 2,310 ft "
               "above mean sea level and it is 290 ft above the ground. The highest point is the obstacle, so the rule-of-thumb "
               "minimum cruising height is 2,310 plus 1,000, which is 3,310 ft; then choose the next suitable VFR level above it.",
               height=420, prefix="tsa")
    L, R, T, B = 86.0, 610.0, 40.0, 360.0
    Y = lambda ft: B - ft / 4000 * (B - T)  # noqa: E731
    # altitude scale
    for ft in (0, 1000, 2000, 3000, 4000):
        c.add(line(L, Y(ft), R, Y(ft), "line", THIN))
        c.add(num(L - 8, Y(ft) + 4, f"{ft:,}", 11.5, "end", "fg-muted"))
    c.add(text(20, (T + B) / 2, "Altitude (ft AMSL)", 13, "middle", "fg-muted", weight=600, rotate=-90))
    # tint band below 2,000 ft
    c.add(rect(L, Y(2000), R - L, Y(0) - Y(2000), "warn-soft", None))
    c.add(line(L, Y(2000), R, Y(2000), "warn", SECOND, dash=DASH))
    c.add(text(L + 8, Y(2000) - 8, "tint band top: 2,000 ft", 12, "start", "warn-fg", weight=700))
    # terrain profile along track
    pts = [(L, Y(600)), (130, Y(800)), (180, Y(1300)), (230, Y(1650)), (270, Y(1900)), (300, Y(2140)), (330, Y(1880)),
           (380, Y(1700)), (430, Y(1800)), (480, Y(1950)), (520, Y(1700)), (570, Y(1200)), (R, Y(1000))]
    d = "M" + " L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + f" L{R} {B} L{L} {B} Z"
    c.add(path(d, "fg", "surface-2", MAIN))
    # spot height
    c.add(polygon([(300, Y(2140) - 2), (294, Y(2140) - 12), (306, Y(2140) - 12)], "fg", None))
    c.add(num(300, Y(2140) - 18, "2,140", 13, "middle", "fg", weight=700))
    c.add(text(300, Y(2140) - 34, "spot height", 11.5, "middle", "fg-muted"))
    # obstacle off track on a knoll at 2,020 ft
    ox, base, top = 470.0, 2020.0, 2310.0
    c.add(path(f"M430 {fmt(Y(1800))} Q{ox} {fmt(Y(2225))} 510 {fmt(Y(1830))}", "fg-faint", None, SECOND, dash=DASH))
    c.add(line(ox, Y(base), ox, Y(top), "bad", 3))
    c.add(line(ox - 7, Y(base), ox, Y(top), "bad", SECOND))
    c.add(line(ox + 7, Y(base), ox, Y(top), "bad", SECOND))
    c.add(num(ox + 12, Y(top) - 30, "2,310 (290)", 13, "start", "bad-fg", weight=700))
    c.add(text(ox + 12, Y(top) - 14, "top AMSL (height AGL)", 11.5, "start", "bad-fg"))
    c.add(text(ox + 12, Y(top) + 2, "1 NM off track", 11.5, "start", "fg-muted"))
    # +1,000 ft
    c.add(line(L, Y(3310), R, Y(3310), "brand", MAIN))
    c.add(arrow(410, Y(top), 410, Y(3310) + 2, "brand", MAIN))
    c.add(line(400, Y(top), ox - 8, Y(top), "fg-faint", THIN, dash=DASH))
    c.add(num(402, (Y(top) + Y(3310)) / 2 + 4, "+ 1,000 ft", 13, "end", "brand-fg", weight=700))
    c.add(num(L + 8, Y(3310) - 10, "3,310 ft: rule-of-thumb minimum cruising height", 13, "start", "brand-fg", weight=700))
    c.add(text(L + 8, Y(3310) - 28, "then the next suitable VFR cruising level above it", 12, "start", "fg-muted"))
    c.add(text((L + R) / 2, B + 24, "Distance along the leg →", 12.5, "middle", "fg-muted", weight=600))
    c.add(text((L + R) / 2, B + 44, "The tint shows the general level; hilltops and obstacles poke above it.", 12, "middle", "fg-faint"))
    return c


# ================================================================ 2.6 Radio navigation aids
def _cdi(cx: float, cy: float, obs: str, flag: str, tone: str) -> str:
    out = circle(cx, cy, 58, "surface-2", "line-strong", SECOND)
    for i in (-4, -3, -2, -1, 1, 2, 3, 4):
        out += circle(cx + i * 10, cy + 6, 2.2, "fg-muted", None)
    out += line(cx, cy - 34, cx, cy + 40, EDGE[tone], 3)
    out += rect(cx - 26, cy - 52, 52, 18, "surface", "line-strong", THIN, rx=4)
    out += num(cx, cy - 39, obs, 13, "middle", "fg", weight=700)
    out += rect(cx + 12, cy + 14, 40, 18, SOFT[tone], EDGE[tone], THIN, rx=4)
    out += text(cx + 32, cy + 27, flag, 12, "middle", FG[tone], weight=700)
    return out


@chart
def vor_radials_to_from() -> Canvas:
    c = Canvas("VOR radials and the TO/FROM flag",
               "Plan view of a VOR with radials numbered clockwise from magnetic north. An aeroplane is on the 090 radial, due magnetic "
               "east of the station. A dashed line through the station at right angles to the 270/090 course divides the TO side from "
               "the FROM side. With 270 set on the OBS the needle centres and the flag reads TO: flying 270 takes you to the station. "
               "With 090 set the needle also centres but the flag reads FROM. The aeroplane's heading plays no part.",
               height=424, prefix="vtf")
    cx, cy, r = 196.0, 220.0, 150.0
    c.add(circle(cx, cy, r, "surface-2", "line-strong", THIN))
    # TO/FROM boundary for the 270/090 course: north-south line
    c.add(path(f"M{fmt(cx)} {fmt(cy - r)} A{fmt(r)} {fmt(r)} 0 0 1 {fmt(cx)} {fmt(cy + r)} Z", None, "brand-soft", 0))
    c.add(line(cx, cy - r - 10, cx, cy + r + 10, "fg-muted", SECOND, dash=DASH))
    c.add(text(cx, cy + r + 40, "dashed: the line at 90° to the selected course", 11.5, "middle", "fg-muted"))
    for b in range(0, 360, 30):
        x1, y1 = pol(cx, cy, r - 2, b)
        c.add(line(cx, cy, x1, y1, "line-strong" if b != 90 else "brand", THIN if b != 90 else 3))
        if b not in (90,):
            lx, ly = pol(cx, cy, r + 16, b)
            c.add(num(lx, ly + 4, f"{b:03d}", 11.5, "middle", "fg-muted"))
    lx, ly = pol(cx, cy, r + 18, 90)
    c.add(num(lx + 4, ly + 4, "090", 13, "start", "brand-fg", weight=700))
    nx, ny = pol(cx, cy, r + 40, 0)
    c.add(text(nx, ny + 8, "Magnetic north ↑", 12, "middle", "fg", weight=700))
    # station symbol
    c.add(polygon([pol(cx, cy, 12, a) for a in range(0, 360, 60)], "surface", "fg", MAIN))
    c.add(circle(cx, cy, 2.5, "fg", None))
    c.add(text(cx - 16, cy - 16, "VOR", 12, "end", "fg", weight=700))
    # aeroplane on the 090 radial heading 270 (towards the station)
    ax, ay = cx + 108, cy
    c.add(group(plane_top(0, 0, 0.36, heading=270, color="fg", fill="surface"), transform=f"translate({ax} {ay})"))
    c.add(text(ax, ay - 26, "on the 090 radial", 12, "middle", "brand-fg", weight=700))
    c.add(text(ax, ay + 36, "due east of the VOR", 11.5, "middle", "fg-muted"))
    c.add(text(cx + r - 8, cy - r + 30, "TO side for 270", 11.5, "end", "brand-fg", weight=600))
    c.add(text(cx - r + 8, cy - r + 30, "FROM side for 270", 11.5, "start", "fg-muted", weight=600))
    # instruments
    c.add(text(530, 36, "Same place, two OBS settings", 13, "middle", "fg", weight=700))
    c.add(_cdi(530, 122, "270", "TO", "ok"))
    c.add(text(530, 200, "Set 270: centred, TO", 12.5, "middle", "ok-fg", weight=700))
    c.add(text(530, 216, "fly 270 to the station", 11.5, "middle", "fg-muted"))
    c.add(_cdi(530, 300, "090", "FROM", "info"))
    c.add(text(530, 378, "Set 090: centred, FROM", 12.5, "middle", "info-fg", weight=700))
    c.add(text(530, 394, "you are on the radial you set", 11.5, "middle", "fg-muted"))
    return c


@chart
def vor_rated_coverage() -> Canvas:
    c = Canvas("VOR rated coverage by altitude",
               "Side view from a VOR on the left. Rated coverage steps out with altitude: 60 nm below 5,000 ft, 90 nm from 5,000 to "
               "below 10,000 ft, 120 nm from 10,000 to below 15,000 ft, and 150 nm from 15,000 to below 20,000 ft. An aeroplane at "
               "4,500 ft and 75 nm is outside coverage; at 6,500 ft and 75 nm it is inside. Terrain between you and the station "
               "blocks the signal whatever the table says.", height=420, prefix="vrc")
    L, R, T, B = 80.0, 600.0, 46.0, 340.0
    X = lambda nm: L + nm / 160 * (R - L)  # noqa: E731
    Y = lambda ft: B - ft / 20000 * (B - T)  # noqa: E731
    bands = [(0, 5000, 60, "fg"), (5000, 10000, 90, "brand"), (10000, 15000, 120, "fg"), (15000, 20000, 150, "fg")]
    for lo, hi, nm, tone in bands:
        c.add(rect(L, Y(hi), X(nm) - L, Y(lo) - Y(hi), SOFT[tone] if tone == "brand" else "sky-soft", EDGE[tone] if tone == "brand" else "sky-fg",
                   MAIN if tone == "brand" else THIN))
        lab = f"{nm} nm" + (": 5,000 to 10,000 ft" if tone == "brand" else "")
        c.add(num(X(nm) - 8 if tone != "brand" else X(5), (Y(hi) + Y(lo)) / 2 + 5 - (8 if tone == "brand" else 0), lab, 14 if tone == "brand" else 13,
                  "end" if tone != "brand" else "start", FG[tone] if tone == "brand" else "sky-fg", weight=700))
    for ft in (0, 5000, 10000, 15000, 20000):
        c.add(num(L - 8, Y(ft) + 4, f"{ft:,}", 11.5, "end", "fg-muted"))
    for nm in (0, 30, 60, 90, 120, 150):
        c.add(line(X(nm), B, X(nm), B + 5, "fg-muted", THIN))
        c.add(num(X(nm), B + 20, f"{nm}", 11.5, "middle", "fg-muted"))
    c.add(line(L, B, R, B, "fg-muted", SECOND, cap="butt"))
    c.add(text((L + R) / 2, B + 40, "Distance from the VOR (nm)", 13, "middle", "fg-muted", weight=600))
    c.add(text(18, (T + B) / 2, "Altitude (ft)", 13, "middle", "fg-muted", weight=600, rotate=-90))
    c.add(text(X(5), Y(7500) + 16, "the exam's favourite", 12, "start", "brand-fg"))
    # station
    c.add(polygon([(L, B - 22), (L - 8, B), (L + 8, B)], "fg", "fg", THIN))
    c.add(text(L + 6, B - 28, "VOR", 12, "start", "fg", weight=700))
    # worked example aeroplanes at 75 nm
    for ft, tone, s in ((4500, "bad", "4,500 ft, 75 nm: outside"), (6500, "ok", "6,500 ft, 75 nm: inside")):
        x, y = X(75), Y(ft)
        c.add(circle(x, y, 6, EDGE[tone], "surface", 2))
        ty = y + (10 if tone == "bad" else -2)
        c.add(line(x + 7, y, X(96) - 4, ty - 4, "fg-muted", THIN))
        c.add(text(X(96), ty, s, 12, "start", FG[tone], weight=700))
    # terrain shadow
    hx = X(30)
    c.add(path(f"M{fmt(hx - 30)} {B} Q{fmt(hx)} {fmt(Y(2600))} {fmt(hx + 30)} {B} Z", "fg", "surface-2", SECOND))
    peak = (Y(2600) + B) / 2
    ant = B - 22
    k = (peak - ant) / (hx - L)
    xe = X(60)
    c.add(path(f"M{fmt(hx)} {fmt(peak)} L{fmt(xe)} {fmt(ant + k * (xe - L))} L{fmt(xe)} {B} L{fmt(hx + 20)} {B} Z", None, "fg-faint", 0, fill_opacity=0.3))
    c.add(text(X(48), B - 8, "terrain shadow", 11.5, "middle", "fg", weight=600))
    c.add(text(L, 30, "Line of sight: the higher you fly, the further out the VOR reaches", 13.5, "start", "fg", weight=700))
    return c


# ================================================================ 2.7 Area navigation
@chart
def vor_dme_rnav_error() -> Canvas:
    c = Canvas("How a VOR bearing error grows with distance",
               "Plan view to scale. A VOR/DME on the left and a waypoint 50 nm out along a radial. A bearing error of 1 degree puts "
               "the waypoint about 0.8 nm to either side; an error of 5 degrees about 4.2 nm. The wedge widens with distance, by the 1 in "
               "60 rule. A GNSS position is good to about 5 to 15 m wherever you are.", height=340, prefix="vre")
    sx, sy = 70.0, 170.0
    k = 9.0  # px per nm (to scale both ways)
    wx = sx + 50 * k
    for deg, tone in ((5, "warn"), (1, "brand")):
        h = math.tan(math.radians(deg)) * 50 * k
        ext = 58 * k
        he = math.tan(math.radians(deg)) * ext
        c.add(polygon([(sx, sy), (sx + ext, sy - he), (sx + ext, sy + he)], SOFT[tone], EDGE[tone], THIN))
        c.add(line(wx, sy - h, wx, sy + h, EDGE[tone], MAIN))
    c.add(line(sx, sy, sx + 58 * k, sy, "fg", MAIN))
    c.add(polygon([pol(sx, sy, 12, a) for a in range(30, 390, 60)], "surface", "fg", MAIN))
    c.add(text(sx, sy + 30, "VOR/DME", 12.5, "middle", "fg", weight=700))
    c.add(circle(wx, sy, 6, "fg", "surface", 2))
    c.add(text(wx - 10, sy - 12, "waypoint", 12, "end", "fg", weight=700))
    c.add(num((sx + wx) / 2, sy + 18, "50 nm", 13, "middle", "fg-muted", weight=700))
    h5 = math.tan(math.radians(5)) * 50 * k
    c.add(num(wx + 4, sy - h5 - 14, "±5°: about 4.2 nm each side", 13, "end", "warn-fg", weight=700))
    c.add(num(wx - 70, sy + 56, "±1°: about 0.8 nm each side", 13, "end", "brand-fg", weight=700))
    c.add(line(wx - 66, sy + 50, wx - 3, sy + 9, "fg-muted", THIN))
    c.add(text(28, 34, "The same angle costs more miles the further out the waypoint is", 14, "start", "fg", weight=700))
    c.add(text(28, 54, "Drawn to scale: sideways error = angle × distance ÷ 60", 12.5, "start", "fg-muted"))
    c.add(rect(28, 268, 584, 52, "ok-soft", "ok", THIN, rx=8))
    c.add(text(44, 290, "GNSS for comparison: about 5 to 15 m wherever you are,", 13, "start", "ok-fg", weight=700))
    c.add(text(44, 308, "too small to draw at this scale. Accuracy is not integrity: still cross-check the map.", 12, "start", "ok-fg"))
    return c
