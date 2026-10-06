"""RMTC top-up diagrams: pressure systems, fog, products, inertia in wind shear, dust devils, the nocturnal jet.
Numbers and names come from content/notes/RMTC/. Sea to the west is on the left (Western Australia)."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, badge, callout, circle, ellipse, fmt, group, line, multiline, num, path,
                                plane_side, polygon, polyline, rect, smooth_path, text)
from tools.diagrams.units.rmtc import arrow, canvas, cumulus, ground, moon, sun


# ---------------------------------------------------------------- helpers
def spiral(cx: float, cy: float, r0: float, r1: float, a0: float, sweep: float, n: int = 24) -> list[tuple[float, float]]:
    """Points on a spiral round (cx, cy): angle a0 (degrees, maths convention, north up) swept by `sweep`
    (positive = anticlockwise on the page) while the radius goes r0 -> r1."""
    pts = []
    for k in range(n + 1):
        f = k / n
        a = math.radians(a0 + sweep * f)
        r = r0 + (r1 - r0) * f
        pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))
    return pts


def curved_arrow(pts: list[tuple[float, float]], color: str = "brand", width: float = MAIN, cls: str | None = None) -> str:
    return path(smooth_path(pts), color, None, width, cls=cls, arrow_end=True)


# Coarse outline of mainland Australia and Tasmania, (longitude, latitude).
AUS = [(113.6, -22.0), (114.2, -21.8), (116.7, -20.6), (118.8, -20.3), (121.0, -19.5), (122.2, -18.0), (122.3, -17.0), (123.6, -16.3),
       (125.0, -15.0), (126.9, -13.8), (128.1, -15.0), (129.6, -14.9), (130.3, -12.5), (132.6, -11.5), (135.9, -12.0), (136.7, -12.3),
       (135.7, -15.0), (137.8, -16.4), (139.3, -17.4), (140.9, -17.4), (141.6, -15.0), (141.5, -12.6), (142.5, -10.7), (143.5, -14.0),
       (145.3, -15.5), (146.3, -19.0), (148.8, -20.3), (150.8, -22.6), (153.1, -25.5), (153.6, -28.6), (153.0, -31.0), (151.3, -33.9),
       (150.1, -36.3), (149.9, -37.5), (147.6, -37.9), (146.3, -39.1), (144.9, -37.9), (143.5, -38.8), (140.6, -38.0), (139.6, -37.2),
       (139.0, -35.6), (138.5, -35.6), (138.1, -34.2), (137.7, -35.1), (137.0, -34.9), (137.5, -33.0), (135.9, -34.7), (135.2, -33.0),
       (134.2, -32.6), (133.5, -32.1), (131.2, -31.5), (129.0, -31.7), (126.0, -32.3), (124.0, -33.0), (123.6, -33.9), (121.9, -33.9),
       (119.9, -34.2), (117.9, -35.1), (116.0, -34.8), (115.0, -34.3), (115.1, -33.6), (115.7, -33.3), (115.7, -32.0), (115.0, -30.0),
       (114.6, -28.8), (113.5, -26.5), (113.4, -25.5), (114.0, -24.0)]
TAS = [(144.6, -40.7), (148.3, -40.9), (148.0, -43.2), (146.0, -43.6), (145.2, -42.2)]


def cold_front(pts: list[tuple[float, float]], color: str = "info", step: float = 24, size: float = 7, side: int = 1) -> str:
    """Cold front symbol: line with triangles on one side (side=+1 to the left of the direction of travel along pts)."""
    out = polyline(pts, color, MAIN)
    seg = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg.append((ax, ay, bx, by, math.hypot(bx - ax, by - ay)))
    total = sum(s[4] for s in seg)
    d = step / 2
    while d < total - size:
        acc = 0.0
        for ax, ay, bx, by, L in seg:
            if acc + L >= d:
                f = (d - acc) / L
                x, y = ax + (bx - ax) * f, ay + (by - ay) * f
                ux, uy = (bx - ax) / L, (by - ay) / L
                nx, ny = uy * side, -ux * side
                out += polygon([(x - ux * size, y - uy * size), (x + ux * size, y + uy * size), (x + nx * size * 1.4, y + ny * size * 1.4)],
                               color, None)
                break
            acc += L
        d += step
    return out


# ================================================================ RMTC 2.1 local weather
@chart
def southern_hemisphere_highs_and_lows() -> Canvas:
    c = canvas("Wind round highs and lows in the Southern Hemisphere",
               "Two plan views with north at the top. Left: a high, H, with air spiralling out of it anticlockwise, so on its northern side the wind "
               "blows from east to west. Right: a low, L, with air spiralling into it clockwise. In both, the Coriolis effect turns moving air to "
               "the left in the Southern Hemisphere. Northern Hemisphere textbooks show the reverse.", height=420, prefix="shl")
    c.add(text(320, 28, "Which way does the wind go round a high and a low here?", 16, "middle", "fg", weight=700))
    c.add(text(320, 48, "plan view, north at the top; moving air is turned to the left", 12, "middle", "fg-muted"))
    for i, (cx, letter, head, sub, out) in enumerate([(165, "H", "High (anticyclone)", "anticlockwise, spiralling out", True),
                                                      (475, "L", "Low", "clockwise, spiralling in", False)]):
        cy = 210
        for r in (40, 78, 116):
            c.add(circle(cx, cy, r, None, "line-strong", THIN, dash=DASH if r == 116 else None))
        c.add(text(cx, cy + 12, letter, 34, "middle", "brand-fg" if out else "info", weight=800))
        color = "brand" if out else "info"
        for k in range(4):
            a0 = 45 + 90 * k
            if out:
                pts = spiral(cx, cy, 50, 108, a0, 62)
            else:
                pts = spiral(cx, cy, 108, 50, a0, -62)
            c.add(curved_arrow(pts, color, MAIN))
        c.add(text(cx, 360, head, 15, "middle", "fg", weight=700))
        c.add(text(cx, 380, sub, 13, "middle", color, weight=600))
    # north arrow
    c.add(arrow(320, 120, 320, 86, "fg-muted", SECOND), text(320, 136, "N", 13, "middle", "fg-muted", weight=700))
    # the north side of the high: an easterly
    c.add(text(165, 80, "north side: wind from the east", 12, "middle", "brand-fg", weight=600))
    c.add(text(320, 408, "Northern Hemisphere textbooks show the reverse.", 12, "middle", "fg-faint"))
    return c


def aus_map(c: Canvas, ox: float, oy: float, lon0: float = 104, lat0: float = -10, kx: float = 5.4, ky: float = 6.1):
    def P(lon: float, lat: float) -> tuple[float, float]:
        return ox + (lon - lon0) * kx, oy + (lat0 - lat) * ky
    c.add(polygon([P(*p) for p in AUS], "surface-2", "fg-muted", SECOND))
    c.add(polygon([P(*p) for p in TAS], "surface-2", "fg-muted", SECOND))
    return P


@chart
def wa_summer_winter_pressure_pattern() -> Canvas:
    c = canvas("Summer and winter pressure patterns over Western Australia",
               "Two simplified maps of Australia. Summer, about November to March: a high in the Great Australian Bight, a west coast trough along "
               "the Western Australian coast, and a hot, dry easterly over Perth on the high's northern side. Winter: the belt of highs has moved "
               "north over the continent, the south-west lies in the westerlies beneath them, and cold fronts sweep in from the Indian Ocean every "
               "few days.", height=440, prefix="wsw")
    c.add(text(320, 28, "Why easterlies in summer and fronts in winter?", 16, "middle", "fg", weight=700))
    c.add(text(320, 48, "where the high sits decides Perth's weather", 12, "middle", "fg-muted"))
    panels = [(8, "Summer", "about November to March"), (326, "Winter", "the highs move north")]
    for ox, head, sub in panels:
        c.add(rect(ox, 64, 306, 330, "sky-soft", None, rx=10))
        c.add(text(ox + 153, 88, head, 15, "middle", "fg", weight=700))
        c.add(text(ox + 153, 106, sub, 12, "middle", "fg-muted"))
    kw = dict(lon0=106, lat0=-10, kx=6.1, ky=6.9)
    # ---- summer
    P = aus_map(c, 8 + 2, 116, **kw)
    hx, hy = P(129, -39.5)
    for rx, ry in ((22, 13), (44, 26), (68, 40)):
        c.add(ellipse(hx, hy, rx, ry, None, "brand", SECOND))
    c.add(text(hx, hy + 8, "H", 22, "middle", "brand-fg", weight=800))
    px, py = P(115.85, -31.95)
    c.add(circle(px, py, 3.5, "fg", None), text(px - 8, py + 4, "Perth", 12, "end", "fg", weight=600))
    ax0 = P(129, -31.6)
    c.add(arrow(ax0[0], ax0[1], px + 12, ax0[1], "brand", MAIN))
    c.add(text(P(127.5, 0)[0], ax0[1] - 10, "hot, dry easterly", 12, "middle", "brand-fg", weight=700))
    t = [P(114.6, -22.5), P(116.0, -26.0), P(116.6, -29.5), P(116.6, -33.0)]
    c.add(polyline(t, "warn", MAIN, dash="7 4"))
    c.add(multiline(P(117.6, 0)[0], P(0, -25.0)[1], ["west coast", "trough"], 12, "start", "warn-fg", weight=600, leading=1.2))
    # ---- winter
    P = aus_map(c, 326 + 2, 116, **kw)
    hx, hy = P(134, -27.5)
    for rx, ry in ((22, 13), (44, 26), (68, 40)):
        c.add(ellipse(hx, hy, rx, ry, None, "brand", SECOND))
    c.add(text(hx, hy + 8, "H", 22, "middle", "brand-fg", weight=800))
    px, py = P(115.85, -31.95)
    c.add(circle(px, py, 3.5, "fg", None), text(px + 7, py - 6, "Perth", 12, "start", "fg", weight=600))
    # westerlies beneath the high
    x, y = P(121, -40.0)
    c.add(arrow(x, y, x + 50, y, "fg-muted", MAIN))
    c.add(text(x + 58, y + 4, "westerlies", 12, "start", "fg-muted", weight=600))
    front = [P(113.2, -29.0), P(111.6, -33.5), P(109.6, -38.0), P(107.6, -42.0)]
    c.add(cold_front(front, "info", side=-1))
    c.add(multiline(326 + 12, P(0, -44.2)[1], ["cold fronts sweep in", "from the Indian Ocean"], 12, "start", "info", weight=600, leading=1.2))
    c.add(text(320, 414, "Summer: easterlies, then the sea breeze.  Winter: westerlies and a cold front every few days.", 12, "middle", "fg-muted"))
    c.add(text(320, 432, "Simplified maps, not a real day's chart.", 12, "middle", "fg-faint"))
    return c


@chart
def temperature_dew_point_overnight() -> Canvas:
    c = canvas("Temperature and dew point through a clear winter night",
               "Top: a chart of air temperature and dew point from sunset to mid-morning. The temperature falls all night under clear skies while the "
               "dew point stays almost level, so the spread narrows; around dawn they meet and fog forms. The coldest time is just after sunrise, "
               "when the fog often thickens, then the sun warms the air above the dew point and the fog clears by mid-morning. Bottom: three "
               "panels showing the wind. Dead calm: dew or frost and only shallow ground fog. A light wind of about 2 to 5 knots: the cooled air is "
               "stirred through a layer a few hundred feet deep and fog forms. A wind much over 10 knots: the chilled air mixes with warmer air "
               "above and fog does not form, sometimes low stratus instead.", height=510, prefix="tdo")
    c.add(text(320, 28, "What turns a clear, humid night into fog by dawn?", 16, "middle", "fg", weight=700))
    from tools.diagrams.svg import Chart
    ch = Chart(c, x=(0, 16), y=(0, 10), box=(70, 70, 610, 270), ylabel="temperature", grid=False)
    c.add(ch.axes())
    for x, lab in ((0, "sunset"), (6, "midnight"), (12.6, "dawn"), (15.5, "mid-morning")):
        c.add(line(ch.px(x), ch.bottom, ch.px(x), ch.bottom + 5, "fg-muted", THIN))
        c.add(text(ch.px(x), ch.bottom + 20, lab, 12, "middle", "fg-muted"))

    TD = 3.0
    T = [(0, 9.0), (2, 7.0), (4, 5.6), (6, 4.6), (8, 3.9), (10, 3.4), (11.6, 3.08), (12.2, TD), (13.4, TD), (14.2, 3.5), (15.0, 5.0), (16, 7.6)]
    D = [(0, 3.25), (12.2, TD), (16, TD)]
    fog_from, fog_to = 12.0, 14.7
    c.add(ch.band(fog_from, fog_to, "brand", 0.10))
    c.add(text((ch.px(fog_from) + ch.px(fog_to)) / 2, ch.top + 16, "fog", 13, "middle", "brand-fg", weight=700))
    c.add(ch.curve(T, "brand", MAIN))
    c.add(ch.curve(D, "info", MAIN, smooth=False))
    c.add(text(ch.px(1.4) + 6, ch.py(8.0) - 4, "air temperature", 13, "start", "brand-fg", weight=700))
    c.add(text(ch.px(0.6), ch.py(TD) + 24, "dew point: barely changes", 13, "start", "info", weight=600))
    # spread
    y1, y2 = ch.py(6.3), ch.py(3.2)
    c.add(line(ch.px(3.0), y1 + 6, ch.px(3.0), y2 - 6, "fg-muted", THIN, DASH))
    c.add(text(ch.px(3.0) + 8, (y1 + y2) / 2 + 18, "wide spread", 12, "start", "fg-muted"))
    c.add(text(ch.px(9.4), ch.py(5.0), "the spread narrows all night", 12, "middle", "fg-muted"))
    c.add(callout(ch.px(12.2), ch.py(TD), ch.px(10.3), ch.py(TD) + 32, ["they meet near dawn:", "fog forms"], "brand-fg", 12))
    c.add(text(ch.right, ch.py(1.9), "the sun warms the air:", 12, "end", "fg-muted"))
    c.add(text(ch.right, ch.py(1.9) + 15, "fog clears by mid-morning", 12, "end", "fg-muted"))
    # ---- wind panels
    top, Hp, Wp = 330, 150, 192
    panels = [("Dead calm", "dew or frost; only", "a shallow ground fog", 8, "fg-muted"),
              ("Light wind, about 2 to 5 kt", "cooled air stirred a few", "hundred feet deep: fog", 70, "brand"),
              ("Wind much over 10 kt", "mixed with warmer air above:", "no fog, perhaps low stratus", 0, "bad")]
    c.add(text(320, top - 14, "How much wind?", 14, "middle", "fg", weight=700))
    for i, (head, l1, l2, depth, color) in enumerate(panels):
        x = 16 + i * (Wp + 12)
        gy = top + 100
        c.add(rect(x, top, Wp, 108, "surface-2", "brand" if i == 1 else None, SECOND if i == 1 else 0, rx=8))
        if i == 0:
            c.add(rect(x + 8, gy - depth, Wp - 16, depth, "brand-soft", None, rx=2))
            for k in range(7):
                c.add(circle(x + 22 + k * 25, gy - 2, 2, "info", None))
        elif i == 1:
            c.add(rect(x + 8, gy - depth, Wp - 16, depth, "brand-soft", "brand", THIN, rx=8))
            c.add(arrow(x + 40, gy - 34, x + 72, gy - 34, "fg-muted", SECOND))
            c.add(text(x + 80, gy - 30, "fog", 13, "start", "brand-fg", weight=700))
        else:
            c.add(rect(x + 30, top + 16, Wp - 60, 16, "surface", "fg-muted", SECOND, rx=6, dash=DASH))
            c.add(text(x + Wp / 2, top + 46, "perhaps low stratus", 11, "middle", "fg-muted"))
            for k in range(3):
                yy = top + 62 + k * 12
                c.add(arrow(x + 30, yy, x + 150 - k * 14, yy, "bad", SECOND))
        c.add(line(x + 8, gy, x + Wp - 8, gy, "fg-muted", SECOND))
        if i == 0:
            c.add(text(x + Wp / 2, gy - 20, "dew on the grass", 11, "middle", "fg-muted"))
        c.add(text(x + Wp / 2, top + 130, head, 13, "middle", color if i else "fg", weight=700))
        c.add(text(x + Wp / 2, top + 150, l1, 12, "middle", "fg-muted"))
        c.add(text(x + Wp / 2, top + 166, l2, 12, "middle", "fg-muted"))
    return c


@chart
def orographic_cloud_on_the_scarp() -> Canvas:
    c = canvas("Orographic cloud on the Darling Scarp",
               "Cross-section from the coast on the left to the wheatbelt on the right. A moist south-westerly behind a winter front crosses the "
               "coastal plain, then is forced up the face of the Darling Scarp, roughly 1,000 ft high. Rising, it expands and cools, and a few "
               "hundred feet above the hills it reaches its dew point: cloud caps the Scarp while the plain stays clear.", height=414, prefix="ocs")
    c.add(text(320, 28, "Why does cloud cap the Scarp while the plain stays clear?", 16, "middle", "fg", weight=700))
    c.add(text(320, 48, "a moist south-westerly behind a winter front, looking north", 12, "middle", "fg-muted"))
    gy, top_g, base = 350, 232, 200
    terrain = [(20, gy), (220, gy - 2), (290, gy - 8), (330, gy - 50), (370, top_g + 8), (420, top_g), (520, top_g + 2), (620, top_g + 4)]
    # streamlines (drawn before the cloud so the upper one disappears into it)
    A = [(30, 318), (240, 316), (300, 304), (350, 262), (400, 222), (450, 216), (610, 218)]
    B = [(30, 270), (230, 268), (300, 256), (345, 232), (400, 204), (430, 192)]
    c.add(path(smooth_path(B), "brand", None, SECOND, arrow_end=True))
    cloud = [(340, base), (352, 168), (400, 142), (470, 128), (550, 132), (612, 146)]
    c.add(path(f"M340 {base} " + smooth_path(cloud)[smooth_path(cloud).index("C"):] + f" L612 {base} Z", "fg-muted", "surface", SECOND))
    c.add(text(486, 172, "cap cloud", 14, "middle", "fg", weight=700))
    c.add(path(smooth_path(A), "brand", None, MAIN, arrow_end=True))
    c.add(ground(terrain, 380))
    c.add(line(150, base, 336, base, "info", THIN, DASH))
    c.add(text(40, base - 22, "the air reaches its dew point a few", 12, "start", "info", weight=600))
    c.add(text(40, base - 7, "hundred feet above the hills: cloud", 12, "start", "info", weight=600))
    c.add(callout(342, 236, 318, 236, ["forced up the face: expands and cools"], "brand-fg", 12))
    c.add(text(40, 296, "moist south-westerly", 13, "start", "brand-fg", weight=700))
    c.add(text(110, 372, "coastal plain: clear", 12, "middle", "fg-muted", weight=600))
    c.add(text(520, 286, "Darling Scarp,", 12, "middle", "fg-muted", weight=600))
    c.add(text(520, 302, "roughly 1,000 ft", 12, "middle", "fg-muted"))
    c.add(text(40, 74, "west", 12, "start", "fg-faint"), text(600, 74, "east", 12, "end", "fg-faint"))
    c.add(text(320, 402, "A Jandakot to Northam flight crosses the Scarp exactly here.", 12, "middle", "fg-faint"))
    return c


# ================================================================ RMTC 2.2 forecasts and reports
@chart
def weather_products_map() -> Canvas:
    c = canvas("Which weather product answers which question",
               "A grid of the products in this lesson. Rows: forecasts, what to expect; observations, what is happening; broadcasts, an "
               "observation delivered by radio. Columns: area, aerodrome and warnings. Area forecasts: GAF, GPWT and area QNH. Aerodrome "
               "forecast: TAF. Warnings: SIGMET and AIRMET, issued only when there is a hazard. Aerodrome observations: METAR and SPECI. "
               "Broadcasts at the aerodrome: ATIS at a controlled aerodrome and AWIS at some non-towered ones.", height=478, prefix="wpm")
    c.add(text(320, 28, "Which product answers which question?", 16, "middle", "fg", weight=700))
    L, T, hw = 136, 92, 118
    cw = (626 - L) / 3
    heights = [132, 92, 92]
    cols = [("Area", "en route"), ("Aerodrome", "one place"), ("Warning", "only if hazardous")]
    rows = [("Forecast", "what to expect", "brand"), ("Observation", "what is happening", "ok"), ("Broadcast", "in the cockpit", "info")]
    for j, (h, s_) in enumerate(cols):
        x = L + j * cw + cw / 2
        c.add(text(x, T - 24, h, 14, "middle", "fg", weight=700), text(x, T - 8, s_, 12, "middle", "fg-muted"))
    cells = {
        (0, 0): [("GAF", "cloud AMSL, weather"), ("GPWT", "wind and temp aloft"), ("Area QNH", "for 3-hour periods")],
        (0, 1): [("TAF", "wind, vis, weather, cloud"), ("", "and the change groups")],
        (0, 2): [("SIGMET", "significant en route"), ("AIRMET", "low-level hazards")],
        (1, 1): [("METAR", "routine observation"), ("SPECI", "special: a big change")],
        (2, 1): [("ATIS", "controlled aerodromes"), ("AWIS", "some non-towered ones")],
    }
    y = T
    for i, (h, s_, color) in enumerate(rows):
        rh = heights[i]
        fg = f"{color}-fg" if color != "info" else "info"
        c.add(rect(14, y + 4, hw - 8, rh - 8, f"{color}-soft", color, SECOND, rx=8))
        c.add(text(14 + (hw - 8) / 2, y + rh / 2 - 2, h, 14, "middle", fg, weight=700))
        c.add(text(14 + (hw - 8) / 2, y + rh / 2 + 16, s_, 11, "middle", "fg-muted"))
        for j in range(3):
            x = L + j * cw
            items = cells.get((i, j))
            if not items:
                c.add(rect(x + 4, y + 4, cw - 8, rh - 8, None, "line", THIN, rx=8, dash=DASH))
                c.add(text(x + cw / 2, y + rh / 2 + 4, "none in this lesson", 11, "middle", "fg-faint"))
                continue
            c.add(rect(x + 4, y + 4, cw - 8, rh - 8, "surface", color, SECOND, rx=8))
            yy = y + 26
            for name, desc in items:
                if name:
                    c.add(text(x + 16, yy, name, 13, "start", "fg", weight=700, cls="num"))
                    c.add(text(x + 16, yy + 15, desc, 11, "start", "fg-muted"))
                    yy += 38
                else:
                    c.add(text(x + 16, yy - 38 + 29, desc, 11, "start", "fg-muted"))
        y += rh
    c.add(text(320, y + 22, "Plan with the forecasts, check the latest observation, confirm with the broadcast.", 13, "middle", "fg", weight=600))
    c.add(text(320, y + 42, "GAF cloud is AMSL; TAF and METAR cloud is above the aerodrome.", 12, "middle", "fg-muted"))
    c.add(text(320, y + 60, "Forecast and report wind is true; ATIS wind is magnetic.", 12, "middle", "fg-muted"))
    return c


# ================================================================ RMTC 2.3 significance of observations
@chart
def wind_shear_inertia() -> Canvas:
    c = canvas("Why a loss of headwind costs airspeed",
               "Two moments on approach, aeroplane flying left to right. Before: airspeed 70 knots into a 25 knot headwind, so the groundspeed is 45 "
               "knots. The headwind suddenly falls to 10 knots. Inertia keeps the groundspeed at 45 knots for a moment, so the airspeed is 45 plus "
               "10, 55 knots: 15 knots lost, and the wing makes lift for 55 knots, not 70.", height=430, prefix="wsi")
    c.add(text(320, 28, "Why does a loss of headwind cost airspeed?", 16, "middle", "fg", weight=700))
    c.add(text(320, 48, "airspeed = groundspeed + headwind; inertia holds the groundspeed for a moment", 12, "middle", "fg-muted"))
    k = 4.6  # px per knot
    x0 = 150
    panels = [(70, "Before", 25, 70, "brand"), (240, "A moment after the headwind drops", 10, 55, "bad")]
    for y, head, hw, ias, color in panels:
        c.add(rect(16, y + 4, 608, 150, "surface-2", None, rx=10))
        c.add(text(32, y + 28, head, 14, "start", "fg", weight=700))
        c.add(plane_side(x0 + 81, y + 76, 1.0))
        # wind
        wx = x0 + 150
        c.add(arrow(wx + hw * k, y + 64, wx, y + 64, "info", MAIN))
        c.add(num(wx + hw * k + 10, y + 68, f"headwind {hw} kt", 13, "start", "info", weight=600))
        # bars
        by = y + 104
        c.add(text(x0 - 12, by + 13, "groundspeed", 12, "end", "fg-muted"))
        c.add(rect(x0, by, 45 * k, 18, "line", "fg-muted", THIN, rx=3))
        c.add(num(x0 + 45 * k / 2, by + 14, "45 kt", 12, "middle", "fg", weight=600))
        c.add(rect(x0 + 45 * k, by, hw * k, 18, "info-soft", "info", THIN, rx=3))
        c.add(num(x0 + 45 * k + hw * k / 2, by + 14, f"+{hw}", 12, "middle", "info", weight=600))
        c.add(text(x0 - 12, by + 41, "airspeed", 12, "end", "fg", weight=700))
        c.add(rect(x0, by + 26, ias * k, 20, f"{color}-soft", color, SECOND, rx=3))
        c.add(num(x0 + max(ias, 70) * k + 10, by + 41, f"{ias} kt", 14, "start", f"{color}-fg" if color == "brand" else color, weight=700))
    # lost bit
    y = 240 + 104 + 26
    c.add(rect(x0 + 55 * k, y, 15 * k, 20, None, "bad", SECOND, rx=3, dash=DASH))
    c.add(num(x0 + 62.5 * k, y - 6, "15 kt lost", 12, "middle", "bad", weight=700))
    c.add(text(320, 416, "The wing flies on airspeed: less lift, the aeroplane sinks below the path. Add power.", 12, "middle", "fg-muted"))
    return c


@chart
def dust_devil_formation() -> Canvas:
    c = canvas("How a dust devil forms",
               "Three stages over a bare paddock on a hot afternoon with little wind. One: the ground heats a thin layer of air far above the air "
               "just above it, a very unstable layer. Two: the layer breaks away at one point and air rushes in along the ground from all sides. "
               "Three: any slight rotation in the inflow is concentrated as the air converges, like a skater pulling her arms in, and a narrow, "
               "fast-spinning column of rising air picks up dust, with sharp changes of wind speed and direction around it.", height=356, prefix="ddf")
    c.add(text(320, 28, "How does a hot paddock make a dust devil?", 16, "middle", "fg", weight=700))
    c.add(text(320, 48, "a hot afternoon with little wind", 12, "middle", "fg-muted"))
    c.style(".ddf-spin{animation:ddf-spin 2s linear infinite}\n@keyframes ddf-spin{to{stroke-dashoffset:-28}}")
    W, top, Hp, gy = 196, 64, 216, 246
    heads = [("1  Hot layer builds", ["bare ground heats a thin", "layer of air: very unstable"]),
             ("2  It breaks away", ["air rushes in along the", "ground from all sides"]),
             ("3  The spin tightens", ["a narrow, fast-spinning column;", "gusts from one side, then the other"])]
    for i, (head, lines) in enumerate(heads):
        x = 10 + i * (W + 11)
        c.add(rect(x, top, W, Hp, "sky-soft", None, rx=8))
        c.add(rect(x, gy, W, top + Hp - gy, "warn-soft", None))
        cx = x + W / 2
        if i == 0:
            c.add(rect(x + 8, gy - 22, W - 16, 20, "bad-soft", "bad", THIN, rx=4))
            c.add(text(cx, gy - 8, "very hot air", 12, "middle", "bad", weight=700))
            c.add(text(cx, gy - 40, "cooler air above", 12, "middle", "fg-muted"))
            c.add(sun(x + W - 30, top + 34, 12))
        elif i == 1:
            c.add(rect(x + 8, gy - 14, W - 16, 12, "bad-soft", "bad", THIN, rx=4))
            c.add(path(f"M{cx - 14} {gy - 13} C{cx - 14} {gy - 40} {cx - 26} {gy - 70} {cx - 24} {gy - 100} "
                       f"A24 24 0 0 1 {cx + 24} {gy - 100} C{cx + 26} {gy - 70} {cx + 14} {gy - 40} {cx + 14} {gy - 13} Z",
                       "bad", "bad-soft", SECOND))
            c.add(arrow(cx, gy - 30, cx, gy - 150, "brand", MAIN))
            c.add(arrow(x + 14, gy - 26, cx - 30, gy - 26, "fg-muted", SECOND))
            c.add(arrow(x + W - 14, gy - 26, cx + 30, gy - 26, "fg-muted", SECOND))
            c.add(text(x + 14, gy - 36, "inflow", 12, "start", "fg-muted"))
            c.add(text(x + W - 14, gy - 36, "inflow", 12, "end", "fg-muted"))
        else:
            for k in range(6):
                yy = gy - 12 - k * 24
                rx = 10 + k * 5
                c.add(f'<ellipse cx="{fmt(cx)}" cy="{fmt(yy)}" rx="{fmt(rx)}" ry="{fmt(4.5 + k * 0.6)}" fill="none" stroke="var(--color-warn)" '
                      f'stroke-width="1.25" stroke-dasharray="10 4" class="ddf-spin"/>')
            c.add(path(f"M{cx - 8} {gy} L{cx - 38} {gy - 140} M{cx + 8} {gy} L{cx + 38} {gy - 140}", "warn", None, THIN, dash=DASH))
            c.add(arrow(cx, gy - 20, cx, gy - 150, "brand", MAIN))
            c.add(text(cx, top + 18, "strong updraught", 12, "middle", "brand-fg", weight=600))
            for sx in (-1, 1):  # dust kicked up at the base
                for k in range(3):
                    c.add(circle(cx + sx * (16 + k * 9), gy - 4 - k * 5, 1.8, "warn", None))
        c.add(line(x, gy, x + W, gy, "warn", SECOND))
        c.add(text(cx, top + Hp + 22, head, 13, "middle", "brand-fg" if i == 2 else "fg", weight=700))
        c.add(multiline(cx, top + Hp + 42, lines, 12, "middle", "fg-muted"))
        if i < 2:
            c.add(arrow(x + W + 1, top + 30, x + W + 10, top + 30, "fg-faint", SECOND))
    return c


@chart
def nocturnal_inversion_low_level_jet() -> Canvas:
    c = canvas("Nocturnal inversion and low-level jet at dawn",
               "Cross-section of the lowest few hundred feet at dawn on the coastal plain. Near the ground lies a layer of cold, dense air, cut off "
               "from the wind above, so it is calm at the surface. At the top of this inversion, a few hundred feet up, the wind jumps to 20 or 30 "
               "knots, sometimes stronger than the gradient wind: the nocturnal low-level jet, here a strong easterly. An aeroplane climbing out "
               "to the east meets a sudden headwind as it passes through the top of the inversion. A small temperature profile shows the air "
               "getting warmer with height through the inversion, then cooler above it.", height=400, prefix="nij")
    c.add(text(320, 28, "Why the sudden wind change climbing out at dawn?", 16, "middle", "fg", weight=700))
    c.add(text(320, 48, "a clear night, a summer dawn on the coastal plain, easterly above", 12, "middle", "fg-muted"))
    gy, inv = 340, 236
    L, R = 30, 450
    c.add(rect(L, 70, R - L, gy - 70, "sky-soft", None))
    c.add(rect(L, inv, R - L, gy - inv, "info-soft", None, fill_opacity=0.9))
    c.add(line(L, gy, R, gy, "fg-muted", MAIN))
    c.add(line(L, inv, R, inv, "info", SECOND, DASH))
    c.add(multiline(R - 10, inv + 20, ["top of the inversion,", "a few hundred feet up"], 12, "end", "info", weight=600))
    c.add(text(R - 10, gy - 34, "cold, dense air: calm", 13, "end", "info", weight=700))
    c.add(text(R - 10, gy - 16, "cut off from the wind above", 12, "end", "fg-muted"))
    # jet arrows (easterly: pointing left)
    for y, ln in ((130, 80), (165, 130), (200, 140)):
        c.add(arrow(R - 16, y, R - 16 - ln, y, "brand", MAIN))
    c.add(text(R - 16, 108, "low-level jet: 20 or 30 kt", 13, "end", "brand-fg", weight=700))
    # aeroplane climbing out to the east through the top of the inversion
    pts = [(50, gy - 4), (120, 322), (180, 272), (215, inv), (238, 216)]
    c.add(path(smooth_path(pts), "fg-muted", None, SECOND, dash=DASH))
    c.add(plane_side(268, 200, 0.7, pitch=26))      # tail (local x -71) just past the end of the dashed path
    c.add(circle(215, inv, 14, None, "bad", MAIN))
    c.add(text(194, inv - 18, "sudden shear", 12, "end", "bad", weight=700))
    # temperature profile
    PL, PR = 476, 620
    c.add(rect(PL - 6, 70, PR - PL + 12, gy - 70, "surface-2", None, rx=8))
    c.add(text((PL + PR) / 2, 92, "temperature", 13, "middle", "fg", weight=700))
    c.add(line(PL + 8, gy, PL + 8, 104, "fg-muted", SECOND, arrow_end=True))
    c.add(line(PL + 8, gy, PR - 6, gy, "fg-muted", SECOND, arrow_end=True))
    c.add(text(PR - 8, gy - 8, "warmer", 12, "end", "fg-muted"))
    c.add(polyline([(PL + 30, gy - 2), (PL + 104, inv), (PL + 66, 110)], "info", MAIN))
    c.add(line(PL + 8, inv, PR - 6, inv, "info", THIN, DASH))
    c.add(multiline(PL + 18, gy - 60, ["warmer", "with height"], 12, "start", "info"))
    c.add(text(PR - 8, 140, "cooler", 12, "end", "fg-muted"))
    c.add(text(320, 372, "Climbing into it from below: a sudden headwind, airspeed jumps. Descending into the calm layer,", 12, "middle", "fg-muted"))
    c.add(text(320, 390, "or with the jet behind you, the airspeed falls instead.", 12, "middle", "fg-muted"))
    return c
