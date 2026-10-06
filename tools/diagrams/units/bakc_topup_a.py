"""BAKC top-up visuals for lessons 2.x and 4.x: the clock-code wrap, isogonals, the nautical mile, Australian time zones,
vectors and Newton's laws, the centre of pressure, the relative airflow, induced and parasite drag, climb gradient units,
the cruise wake, and rotor downwash and breakaway thrust. Numbers on every figure come from the note it sits in."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, arc_path, arrow, badge, callout, circle, ellipse, fmt, group, line,
                                multiline, num, path, plane_side, plane_top, polygon, polyline, rect, smooth_path, text)
from tools.diagrams.units.bakc_aero_ops import jet_top, unit, wing_section
from tools.diagrams.units.bakc_general_engines import barc, bxy, compass_card
from tools.diagrams.units.rmtc_topup import AUS, TAS


# ---------------------------------------------------------------- helpers
def panel(x: float, y: float, w: float, h: float, fill: str = "surface-2", stroke: str | None = None) -> str:
    return rect(x, y, w, h, fill, stroke, THIN if stroke else MAIN, rx=10)


def ground(x0: float, x1: float, y: float) -> str:
    return line(x0, y, x1, y, "fg-muted", 4, cap="butt")


class AusMap:
    """Equirectangular map of Australia: lon/lat to the canvas."""

    def __init__(self, x0: float, y0: float, scale: float, lon0: float = 112.0, lat0: float = -10.0):
        self.x0, self.y0, self.k, self.lon0, self.lat0 = x0, y0, scale, lon0, lat0
        self.kx = scale * math.cos(math.radians(27))

    def p(self, lon: float, lat: float) -> tuple[float, float]:
        return self.x0 + (lon - self.lon0) * self.kx, self.y0 + (self.lat0 - lat) * self.k

    def outline(self, fill: str = "surface", stroke: str = "fg-muted", width: float = SECOND, **kw) -> str:
        return (polygon([self.p(*q) for q in AUS], fill, stroke, width, **kw) +
                polygon([self.p(*q) for q in TAS], fill, stroke, width, **kw))


def helicopter_side(x: float, y: float, s: float = 1.0, color: str = "fg", fill: str = "surface") -> str:
    """Light helicopter seen from the left, nose to the right, ~110 units long at s = 1; (x, y) is the rotor mast foot."""
    cabin = path("M-18 -2 C-18 -14 -6 -18 8 -18 C24 -18 34 -8 36 4 C37 12 30 16 20 16 L-12 16 C-18 16 -20 10 -18 -2 Z", color, fill, MAIN)
    window = path("M10 -14 C22 -13 30 -6 32 3 L12 3 Z", color, "surface-2", THIN)
    boom = path("M-18 0 L-70 -4 L-70 2 L-18 8 Z", color, fill, MAIN)
    fin = path("M-64 -4 L-72 -22 L-77 -22 L-74 2 Z", color, fill, MAIN)
    mast = line(0, -18, 0, -26, color, MAIN)
    rotor = line(-58, -27, 58, -27, color, MAIN)
    hub = circle(0, -27, 3, color, None)
    tailrotor = circle(-74, -10, 7, None, color, THIN)
    skids = (line(-10, 16, -14, 26, color, SECOND) + line(18, 16, 22, 26, color, SECOND) +
             path("M-26 26 L32 26 C38 26 40 22 40 20", color, None, SECOND))
    return group(boom, fin, tailrotor, cabin, window, mast, rotor, hub, skids, transform=f"translate({fmt(x)} {fmt(y)}) scale({fmt(s)})")


# ================================================================ BAKC 2.1 direction of flight
@chart
def relative_bearing_wrap() -> Canvas:
    c = Canvas("Traffic at two o'clock on a heading of 350",
               "A compass rose with an aeroplane heading 350. Two o'clock is 60 degrees right of the nose. Counting clockwise from 350, the "
               "line passes north at 360 and stops 50 degrees later: 350 plus 60 is 410, and removing a full circle of 360 gives a bearing of 050.",
               height=400, prefix="rbw")
    CX, CY, R, HDG = 196, 222, 140, 350
    c.add(text(20, 30, "Heading 350, traffic at two o'clock: the sum runs past north", 15, "start", "fg", weight=700))
    c.add(compass_card(CX, CY, R, labels=False))
    for b, s in ((0, "360"), (90, "090"), (180, "180"), (270, "270")):
        x, y = bxy(CX, CY, R + 18, b)
        c.add(num(x, y + 5, s, 12, "middle", "fg-muted"))
    c.add(text(CX, CY - R + 34, "N", 13, "middle", "fg-muted", weight=700))
    # heading line
    c.add(line(CX, CY, *bxy(CX, CY, R - 4, HDG), "fg-muted", SECOND, DASH))
    hx, hy = bxy(CX, CY, R + 20, HDG)
    c.add(num(hx - 4, hy + 2, "HDG 350", 13, "end", "fg", weight=700))
    # the 60 degree sweep, split at north
    c.add(path(barc(CX, CY, 96, HDG, 360), "warn", None, 4))
    c.add(path(barc(CX, CY, 96, 0, 50), "brand", None, 4))
    lx, ly = bxy(CX, CY, 74, 355)
    c.add(num(lx, ly + 5, "10°", 12, "middle", "warn-fg", weight=700))
    lx, ly = bxy(CX, CY, 74, 25)
    c.add(num(lx, ly + 5, "50°", 12, "middle", "brand", weight=700))
    # bearing line to the traffic
    tx, ty = bxy(CX, CY, R + 46, 50)
    c.add(line(CX, CY, *bxy(CX, CY, R + 26, 50), "brand", MAIN, DASH, arrow_end=True))
    c.add(plane_top(tx, ty, 0.26, 230, "brand", "brand-soft"))
    c.add(multiline(tx, ty - 34, ["2 o'clock", "bears 050"], 13, "middle", "brand", weight=700))
    c.add(plane_top(CX, CY, 0.8, HDG))
    # working panel
    X = 410
    c.add(panel(X, 92, 214, 200))
    c.add(text(X + 14, 116, "Worked example", 14, "start", "fg", weight=700))
    c.add(num(X + 14, 142, "2 h × 30° = 60° right", 12, "start", "fg-muted"))
    c.add(num(X + 14, 166, "350 + 60 = 410", 14, "start", "warn-fg", weight=700))
    c.add(text(X + 14, 184, "past 360: remove a full circle", 12, "start", "fg-muted"))
    c.add(num(X + 14, 208, "410 − 360 = 050", 14, "start", "brand", weight=700))
    c.add(line(X + 14, 224, X + 200, 224, "line", THIN))
    c.add(multiline(X + 14, 244, ["10° takes you to north,", "the other 50° is past it."], 12, "start", "fg-muted"))
    c.add(text(X + 14, 282, "Below 000? Add 360.", 12, "start", "fg", weight=600))
    c.add(multiline(X, 326, ["Same rule for any relative bearing:", "300 + 100 = 400 → 040°M"], 12, "start", "fg-muted"))
    return c


@chart
def isogonals_wa_to_east() -> Canvas:
    c = Canvas("Why variation changes as you fly east",
               "Schematic map of Australia with dashed isogonal lines, lines of equal variation, running roughly north to south. Around Perth "
               "the variation is small and westerly, about 1 to 2 degrees west. Further east it passes through zero and becomes easterly, "
               "reaching 10 degrees east or more in the eastern states. Flying from Perth to Kalgoorlie you cross isogonals, so the "
               "variation changes; the deviation does not. Schematic only: use the values on the current chart.", height=476, prefix="iso")
    M = AusMap(24, 92, 10.4)
    c.add(text(20, 30, "Variation belongs to the place: it changes as you cross the isogonals", 15, "start", "fg", weight=700))
    c.add(text(20, 50, "Schematic, not to scale: use the values on the current chart", 12, "start", "warn-fg", weight=600))
    c.add(M.outline("surface-2", "fg-muted"))
    # isogonals: (lon at top, lon at bottom, label, colour)
    lines = [(118.0, 116.6, "small W", "info"), (125.0, 122.5, "0°", "fg"), (136.0, 134.5, "E", "brand"), (148.0, 145.5, "10°E or more", "brand")]
    for lt, lb, lab, colr in lines:
        pts = [M.p(lt + (lb - lt) * f + 0.8 * math.sin(f * math.pi), -12 - 31 * f) for f in [i / 10 for i in range(11)]]
        c.add(path(smooth_path(pts), colr if colr != "fg" else "fg-muted", None, SECOND, "6 4"))
        x, y = pts[0]
        c.add(badge(x, y - 16, lab, colr, 12))
    per = M.p(115.86, -31.95)
    kal = M.p(121.47, -30.75)
    syd = M.p(151.2, -33.87)
    c.add(arrow(per[0] + 6, per[1] - 2, kal[0] - 6, kal[1] + 1, "fg", MAIN))
    for (x, y), name, anchor, dx in ((per, "Perth", "start", 6), (kal, "Kalgoorlie", "start", 8), (syd, "Sydney", "end", -8)):
        c.add(circle(x, y, 4, "fg", "surface", 1.5))
        c.add(text(x + dx, y + 20, name, 12, anchor, "fg", weight=600))

    def pointers(x: float, y: float, var: float, colr: str, head: str, lab: str) -> str:
        out = panel(x - 80, y - 82, 172, 104)
        out += text(x - 68, y - 60, head, 13, "start", "fg", weight=700)
        ax_, ay_ = x + 62, y + 10
        out += arrow(ax_, ay_, ax_, ay_ - 56, "fg", SECOND)
        out += text(ax_ + (8 if var < 0 else -8), ay_ - 50, "T", 12, "start" if var < 0 else "end", "fg", weight=700)
        mx, my = bxy(ax_, ay_, 58, var)
        out += arrow(ax_, ay_, mx, my, colr, MAIN)
        out += text(mx, my - 8, "M", 12, "middle", colr, weight=700)
        out += multiline(x - 68, y - 36, lab if isinstance(lab, list) else [lab], 12, "start", colr, weight=600)
        return out
    X = 534
    c.add(pointers(X, 168, -16, "info", "Near Perth", ["magnetic N", "a little west", "of true N"]))
    c.add(pointers(X, 286, 24, "brand", "Out east", ["magnetic N", "well east", "of true N"]))
    c.add(panel(454, 326, 172, 104))
    c.add(text(466, 348, "Perth → Kalgoorlie", 13, "start", "fg", weight=700))
    c.add(multiline(466, 368, ["Variation changes:", "it depends on place.", "Deviation does not:", "it depends on heading."], 12, "start", "fg-muted"))
    c.add(text(20, 462, "Perth: about 1 to 2°W. Eastern states: easterly, 10° or more in places. Pointer angles exaggerated.", 11, "start", "fg-faint"))
    return c


# ================================================================ BAKC 2.2 distance
@chart
def nautical_mile_latitude() -> Canvas:
    c = Canvas("One minute of latitude is one nautical mile",
               "Left: a section through the Earth from pole to pole. One degree of latitude, measured at the centre, is divided into 60 minutes, "
               "and each minute of arc along the surface is one nautical mile, so one degree is 60 NM. Right: the latitude scale on the side of a "
               "chart works as a distance scale; dividers opened to 18 minutes measure 18 NM, about Rottnest to Jandakot. Perth to Geraldton is "
               "about 4 degrees of latitude, roughly 240 NM.", height=400, prefix="nml")
    c.add(text(20, 30, "Why the latitude scale on every chart is a distance scale", 15, "start", "fg", weight=700))
    CX, CY, R = 128, 214, 100
    c.add(circle(CX, CY, R, "sky-soft", "fg-muted", SECOND))
    c.add(line(CX - R - 8, CY, CX + R + 8, CY, "fg-faint", THIN, DASH))
    c.add(text(CX + R + 12, CY + 4, "equator", 11, "start", "fg-faint"))
    c.add(line(CX, CY - R - 8, CX, CY + R + 8, "fg-faint", THIN, DASH))
    c.add(text(CX + 6, CY - R - 12, "pole", 11, "start", "fg-faint"))
    a0, a1 = -30, -52      # a 1 degree slice, drawn 22 times too wide
    p0 = (CX + R * math.cos(math.radians(a0)), CY + R * math.sin(math.radians(a0)))
    p1 = (CX + R * math.cos(math.radians(a1)), CY + R * math.sin(math.radians(a1)))
    c.add(polygon([(CX, CY), p0, p1], "brand", None, fill_opacity=0.15))
    c.add(line(CX, CY, *p0, "brand", SECOND), line(CX, CY, *p1, "brand", SECOND))
    c.add(path(arc_path(CX, CY, R, a1, a0), "brand", None, 5))
    c.add(path(arc_path(CX, CY, 34, a1, a0), "brand", None, SECOND))
    c.add(num(CX + 40, CY - 34, "1°", 13, "start", "brand", weight=700))
    c.add(text(CX, CY + R + 22, "slice drawn much wider than 1°", 11, "middle", "fg-faint"))
    # magnified arc: 60 minutes, one NM each
    RX0, RX1, RY = 300, 612, 104
    mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    c.add(line(mid[0] + 4, mid[1] - 4, RX0 - 6, RY + 14, "fg-muted", THIN, DASH))
    c.add(rect(RX0, RY, RX1 - RX0, 22, "brand-soft", "brand", SECOND, rx=3))
    for m in range(61):
        x = RX0 + m * (RX1 - RX0) / 60
        L = 14 if m % 10 == 0 else 7
        c.add(line(x, RY + 22, x, RY + 22 - L, "brand", THIN if L < 14 else SECOND, cap="butt"))
        if m % 10 == 0:
            c.add(num(x, RY + 40, f"{m}'", 11, "middle", "brand-fg"))
    c.add(text(RX0, RY - 26, "That 1° of arc, magnified: 60 minutes", 13, "start", "brand", weight=700))
    c.add(text(RX0, RY - 10, "each minute of latitude is 1 NM, so 1° = 60 NM", 12, "start", "brand"))
    # chart edge latitude scale with dividers
    X, Y0, H = 330, 186, 150     # 30 minutes shown
    c.add(rect(X, Y0, 22, H, "surface", "fg", SECOND))
    for m in range(31):
        y = Y0 + m * H / 30
        L = 12 if m % 10 == 0 else 8 if m % 5 == 0 else 4
        c.add(line(X + 22, y, X + 22 - L, y, "fg-muted", SECOND if L == 12 else THIN, cap="butt"))
        if m % 10 == 0:
            c.add(num(X - 6, y + 4, f"{m}'", 11, "end", "fg-muted"))
    c.add(text(X - 10, Y0 - 12, "chart latitude scale", 11, "start", "fg-muted"))
    ya, yb = Y0 + 4 * H / 30, Y0 + 22 * H / 30
    hx = X + 76
    c.add(polyline([(X + 24, ya), (hx, (ya + yb) / 2), (X + 24, yb)], "brand", MAIN))
    c.add(circle(hx, (ya + yb) / 2, 4, "brand", None))
    c.add(text(hx + 12, (ya + yb) / 2 - 22, "dividers open 18'", 12, "start", "brand", weight=600))
    c.add(num(hx + 12, (ya + yb) / 2, "= 18 NM", 15, "start", "brand", weight=700))
    c.add(text(hx + 12, (ya + yb) / 2 + 20, "about Rottnest to Jandakot,", 11, "start", "fg-muted"))
    c.add(text(hx + 12, (ya + yb) / 2 + 34, "on any chart, at any scale", 11, "start", "fg-muted"))
    c.add(rect(20, 362, 600, 30, "surface-2", None, rx=8))
    c.add(num(32, 382, "1 NM = 1' of latitude = 1,852 m    ·    Perth to Geraldton ≈ 4° × 60 = 240 NM", 12, "start", "fg", weight=600))
    return c


# ================================================================ BAKC 2.3 time
@chart
def time_zones_australia() -> Canvas:
    c = Canvas("Australia's three standard time zones",
               "Map of Australia in three standard time zones: Western Standard Time, UTC plus 8, in Western Australia; Central Standard Time, "
               "UTC plus 9 and a half, in South Australia and the Northern Territory; Eastern Standard Time, UTC plus 10, in Queensland, New South "
               "Wales, the ACT, Victoria and Tasmania. At 0200 UTC it is 1000 WST, 1130 CST and 1200 EST. The date changes at 1400 UTC in the east, "
               "1430 UTC in the centre and 1600 UTC in the west. Western Australia has no daylight saving; some eastern and southern states move "
               "their clocks an hour forward in summer.", height=484, prefix="tza")
    M = AusMap(20, 66, 10.0)
    c.add(text(20, 30, "One moment, three Australian clocks (standard time)", 15, "start", "fg", weight=700))
    clip = "".join(f"M{fmt(x)} {fmt(y)} " if i == 0 else f"L{fmt(x)} {fmt(y)} " for i, (x, y) in enumerate(M.p(*q) for q in AUS)) + "Z "
    clip += "".join(f"M{fmt(x)} {fmt(y)} " if i == 0 else f"L{fmt(x)} {fmt(y)} " for i, (x, y) in enumerate(M.p(*q) for q in TAS)) + "Z"
    c.add_defs(f'<clipPath id="tza-aus"><path d="{clip}"/></clipPath>')
    xw = M.p(129, -10)[0]
    x138 = M.p(138, -10)[0]
    x141 = M.p(141, -10)[0]
    y26 = M.p(130, -26)[1]
    top, bot = M.p(0, -9)[1], M.p(0, -45)[1]
    cst = f"M{fmt(xw)} {fmt(top)} L{fmt(x138)} {fmt(top)} L{fmt(x138)} {fmt(y26)} L{fmt(x141)} {fmt(y26)} L{fmt(x141)} {fmt(bot)} L{fmt(xw)} {fmt(bot)} Z"
    zones = (rect(0, top, xw, bot - top, "brand-soft", None) + path(cst, None, "warn-soft", 0) +
             path(f"M{fmt(x138)} {fmt(top)} L640 {fmt(top)} L640 {fmt(bot)} L{fmt(x141)} {fmt(bot)} L{fmt(x141)} {fmt(y26)} L{fmt(x138)} {fmt(y26)} Z", None, "info-soft", 0))
    c.add(f'<g clip-path="url(#tza-aus)">{zones}</g>')
    c.add(M.outline(None, "fg-muted"))
    # zone borders (approximate)
    c.add(f'<g clip-path="url(#tza-aus)">' + line(xw, top, xw, bot, "fg-muted", SECOND, DASH) +
          polyline([(x138, top), (x138, y26), (x141, y26), (x141, bot)], "fg-muted", SECOND, DASH) + "</g>")
    for (lon, lat), name, off, clock, colr in (((120.5, -25.5), "WST", "UTC + 8", "1000", "brand"), ((133.5, -21.5), "CST", "UTC + 9½", "1130", "warn"),
                                               ((145.0, -23.5), "EST", "UTC + 10", "1200", "info")):
        x, y = M.p(lon, lat)
        c.add(text(x, y - 14, name, 16, "middle", f"{colr}-fg", weight=700))
        c.add(num(x, y + 4, off, 13, "middle", f"{colr}-fg", weight=600))
        c.add(rect(x - 30, y + 14, 60, 24, "surface", colr, SECOND, rx=6))
        c.add(num(x, y + 31, clock, 14, "middle", "fg", weight=700))
    per = M.p(115.86, -31.95)
    c.add(circle(*per, 3.5, "fg", None), text(per[0] + 8, per[1] + 4, "Perth", 11, "start", "fg", weight=600))
    # side panel
    X = 446
    c.add(panel(X, 56, 180, 148))
    c.add(text(X + 12, 78, "Same moment", 13, "start", "fg", weight=700))
    c.add(num(X + 12, 100, "0200 UTC", 13, "start", "fg", weight=700))
    c.add(num(X + 12, 120, "= 1000 WST", 13, "start", "brand-fg", weight=600))
    c.add(num(X + 12, 140, "= 1130 CST", 13, "start", "warn-fg", weight=600))
    c.add(num(X + 12, 160, "= 1200 EST", 13, "start", "info-fg", weight=600))
    c.add(text(X + 12, 190, "Brisbane is 2 h ahead of Perth", 11, "start", "fg-muted"))
    c.add(panel(X, 216, 180, 118))
    c.add(text(X + 12, 238, "Local date changes at", 13, "start", "fg", weight=700))
    c.add(num(X + 12, 262, "1400 UTC  EST", 13, "start", "info-fg", weight=600))
    c.add(num(X + 12, 282, "1430 UTC  CST", 13, "start", "warn-fg", weight=600))
    c.add(num(X + 12, 302, "1600 UTC  WST", 13, "start", "brand-fg", weight=600))
    c.add(text(X + 12, 324, "(24 h minus the offset)", 11, "start", "fg-muted"))
    c.add(multiline(20, 428, ["WA has no daylight saving: WST is UTC + 8 all year. Some eastern and southern states move their clocks",
                              "an hour forward in summer, widening the gap to Perth. Exam conversions use standard time.",
                              "Zone borders simplified."], 11, "start", "fg-muted", leading=1.45))
    return c


# ================================================================ BAKC 2.5 basic physics
@chart
def vector_addition_tip_to_tail() -> Canvas:
    c = Canvas("Adding forces tip to tail",
               "Three cases of adding two forces. Same direction: 300 N plus 300 N gives a resultant of 600 N. Opposite directions: 300 N forward "
               "and 300 N back give a resultant of zero, so the motion does not change. At right angles: draw the second arrow from the tip of the "
               "first; the resultant runs from the tail of the first to the tip of the second, the long side of a right-angled triangle.",
               height=380, prefix="vtt")
    c.add(text(20, 30, "Draw the second arrow from the tip of the first; the resultant joins tail to tip", 14, "start", "fg", weight=700))
    W = 196
    heads = ["Same direction", "Opposite directions", "At right angles"]
    for i, h in enumerate(heads):
        x0 = 14 + i * (W + 10)
        c.add(panel(x0, 48, W, 288))
        c.add(text(x0 + W / 2, 72, h, 14, "middle", "fg", weight=700))
    # 1: same direction
    x0, y = 14, 170
    c.add(arrow(x0 + 20, y, x0 + 94, y, "info", 3), arrow(x0 + 96, y, x0 + 170, y, "warn", 3))
    c.add(num(x0 + 57, y - 12, "300 N", 12, "middle", "info-fg", weight=700), num(x0 + 133, y - 12, "300 N", 12, "middle", "warn-fg", weight=700))
    c.add(arrow(x0 + 20, y + 40, x0 + 170, y + 40, "brand", 4))
    c.add(num(x0 + 95, y + 64, "resultant 600 N", 13, "middle", "brand", weight=700))
    c.add(text(x0 + W / 2, 300, "add the numbers", 12, "middle", "fg-muted"))
    # 2: opposite
    x0 = 14 + W + 10
    c.add(arrow(x0 + 30, y - 8, x0 + 150, y - 8, "info", 3))
    c.add(num(x0 + 90, y - 20, "300 N forward", 12, "middle", "info-fg", weight=700))
    c.add(arrow(x0 + 150, y + 8, x0 + 30, y + 8, "warn", 3))
    c.add(num(x0 + 90, y + 28, "300 N back", 12, "middle", "warn-fg", weight=700))
    c.add(circle(x0 + 30, y + 64, 6, "brand", "surface", 2))
    c.add(num(x0 + 44, y + 69, "resultant 0", 13, "start", "brand", weight=700))
    c.add(text(x0 + W / 2, 284, "the tip returns to the tail:", 12, "middle", "fg-muted"))
    c.add(text(x0 + W / 2, 300, "no change of motion", 12, "middle", "fg-muted"))
    # 3: right angles
    x0 = 14 + 2 * (W + 10)
    ax, ay = x0 + 28, 250
    bx, by = x0 + 148, 250
    tx, ty = bx, 110
    c.add(arrow(ax, ay, bx, by, "info", 3), arrow(bx, by, tx, ty, "warn", 3))
    c.add(text((ax + bx) / 2, ay + 20, "A", 13, "middle", "info-fg", weight=700))
    c.add(text(bx + 10, (by + ty) / 2 + 4, "B", 13, "start", "warn-fg", weight=700))
    c.add(arrow(ax, ay, tx - 3, ty + 4, "brand", 4))
    c.add(text((ax + tx) / 2 - 10, (ay + ty) / 2 - 6, "R", 14, "end", "brand", weight=700))
    c.add(rect(bx - 12, by - 12, 12, 12, None, "fg-muted", THIN))
    c.add(num(x0 + W / 2, 300, "R = √(A² + B²)", 13, "middle", "brand", weight=700))
    c.add(text(x0 + W / 2, 320, "the long side of the triangle", 11, "middle", "fg-muted"))
    c.add(text(20, 362, "A force, like a wind velocity, is a vector: it has a size and a direction, and both go into the sum.", 12, "start", "fg-muted"))
    return c


@chart
def newtons_laws_in_flight() -> Canvas:
    c = Canvas("Newton's three laws in flight",
               "First law: in steady cruise lift equals weight and thrust equals drag, so there is no net force and no change of motion. "
               "Second law: on the take-off roll a 1,000 kg aeroplane with 2,500 N of thrust against 1,000 N of drag and rolling friction has a "
               "net force of 1,500 N and accelerates at 1.5 metres per second squared. Third law: the propeller drives air backwards and the "
               "air drives the aeroplane forwards; the wing deflects air downwards and the air pushes the wing up.", height=470, prefix="nlf")
    c.add(text(20, 30, "Three laws, three things you see on every flight", 15, "start", "fg", weight=700))
    # 1st law: top-left
    c.add(panel(14, 46, 300, 196))
    c.add(text(28, 70, "1  Balanced forces: no change", 14, "start", "fg", weight=700))
    PX, PY = 164, 150
    c.add(plane_side(PX, PY, 1.1))
    c.add(arrow(PX - 2, PY - 24, PX - 2, PY - 66, "fg", MAIN), text(PX + 6, PY - 54, "Lift", 12, "start", "fg", weight=600))    # from the high wing
    c.add(arrow(PX + 1, PY + 8, PX + 1, PY + 64, "fg", MAIN), text(PX + 9, PY + 58, "Weight", 12, "start", "fg", weight=600))
    c.add(arrow(PX + 66, PY, PX + 116, PY, "fg", MAIN), text(PX + 92, PY - 10, "Thrust", 12, "middle", "fg", weight=600))
    c.add(arrow(PX - 70, PY, PX - 120, PY, "fg-muted", MAIN), text(PX - 96, PY - 10, "Drag", 12, "middle", "fg-muted", weight=600))
    c.add(text(28, 232, "No net force: steady speed and height", 12, "start", "brand", weight=700))
    # 2nd law: top-right
    c.add(panel(326, 46, 300, 196))
    c.add(text(340, 70, "2  Net force accelerates a mass", 14, "start", "fg", weight=700))
    GY = 162
    c.add(ground(340, 612, GY + 18))
    QX = 450
    c.add(plane_side(QX, GY + 2, 0.85))
    c.add(arrow(QX + 52, GY - 2, QX + 122, GY - 2, "info", 3))
    c.add(num(QX + 87, GY - 16, "thrust 2,500 N", 12, "middle", "info-fg", weight=700))
    c.add(arrow(QX - 50, GY - 2, QX - 92, GY - 2, "warn", 3))
    c.add(multiline(QX - 72, GY - 46, ["drag + friction", "1,000 N"], 12, "middle", "warn-fg", weight=700))
    c.add(num(340, 204, "net 2,500 − 1,000 = 1,500 N", 12, "start", "fg", weight=600))
    c.add(num(340, 224, "a = F/m = 1,500 / 1,000 = 1.5 m/s²", 13, "start", "brand", weight=700))
    # 3rd law: bottom, two halves
    c.add(panel(14, 254, 612, 200))
    c.add(text(28, 278, "3  Push air one way, the air pushes you the other", 14, "start", "fg", weight=700))
    # propeller
    RX, RY = 220, 360
    c.add(plane_side(RX, RY, 1.1, gear=False))
    for dy in (-14, 0, 14):
        c.add(arrow(RX - 70, RY + dy, RX - 170, RY + dy * 1.5, "sky-fg", SECOND))
    c.add(text(RX - 120, RY - 34, "air thrown back", 12, "middle", "sky-fg", weight=600))
    c.add(arrow(RX + 66, RY - 2, RX + 120, RY - 2, "brand", 3))
    c.add(multiline(RX + 66, RY - 40, ["air pushes the", "aeroplane forward"], 12, "start", "brand", weight=600))
    # wing and downwash
    WX, WY = 530, 352
    sec, P = wing_section(WX, WY, 130, 6)
    c.add(sec)
    c.add(arrow(WX + 4, WY - 14, WX + 4, WY - 64, "brand", 3))
    c.add(multiline(WX + 14, WY - 56, ["air pushes", "the wing up"], 12, "start", "brand", weight=600))
    te = P(100, -2)
    for k, dy in enumerate((0, 14)):
        c.add(path(smooth_path([(te[0] + 4, te[1] + dy), (te[0] - 30, te[1] + 12 + dy), (te[0] - 60, te[1] + 34 + dy)]), "sky-fg", None, SECOND, arrow_end=True))
    c.add(text(WX - 40, WY + 86, "wing deflects air down (downwash)", 12, "middle", "sky-fg", weight=600))
    return c


# ================================================================ BAKC 4.1 basic aerodynamics
@chart
def cp_movement_with_aoa() -> Canvas:
    c = Canvas("The centre of pressure moves with angle of attack",
               "Three wing sections flying to the right. At a small angle of attack the centre of pressure, where the lift acts, is well back "
               "along the chord. At a larger angle of attack, still below the critical angle, it has moved forward. Beyond the critical angle the "
               "flow separates over the rear of the wing and the centre of pressure moves rapidly rearward, part of why the nose drops at the stall.",
               height=486, prefix="cpm")
    c.add(text(20, 30, "Where does the lift act? It depends on the angle of attack", 15, "start", "fg", weight=700))
    rows = [(2, 44, None, "Small angle of attack", "CP well back along the chord", "brand", False),
            (8, 28, 44, "Larger angle, below the critical angle", "CP has moved forward", "brand", False),
            (16, 50, 28, "Beyond the critical angle: stalled", "CP moves rapidly rearward", "bad", True)]
    X, CH = 400, 210
    for i, (aoa, cpx, was, head, sub, colr, stalled) in enumerate(rows):
        top = 46 + i * 140
        Y = top + 84
        c.add(panel(14, top, 612, 130))
        c.add(text(28, top + 24, head, 14, "start", "fg", weight=700))
        c.add(text(28, top + 44, sub, 13, "start", colr, weight=700))
        for yy in (top + 62, top + 102):
            c.add(arrow(612, yy, 566, yy, "sky-fg", SECOND))
        sec, P = wing_section(X, Y, CH, aoa)
        if stalled:
            pts = [P(48, -11), P(62, -17), P(76, -12), P(90, -19), P(104, -10), P(120, -17)]
            c.add(path(smooth_path(pts), "bad", None, SECOND, "3 3"))
            for k in range(3):
                q = P(64 + k * 18, -22 - k * 2)
                c.add(path(arc_path(q[0], q[1], 6, 0, 280), "bad", None, THIN))
        c.add(sec)
        le, te = P(0, 0), P(100, -2)
        c.add(line(te[0], te[1], le[0], le[1], "fg-faint", THIN, DASH))
        cp = P(cpx, -1)
        if was is not None:
            w = P(was, -1)
            c.add(circle(w[0], w[1], 5, "surface", "fg-faint", 1.5))
            c.add(line(w[0] + (4 if cp[0] > w[0] else -4), w[1] + 16, cp[0] - (2 if cp[0] > w[0] else -2), cp[1] + 16, colr, MAIN, arrow_end=True))
        c.add(arrow(cp[0], cp[1] - 4, cp[0], cp[1] - 48, colr, 3))
        c.add(circle(cp[0], cp[1], 5, colr, "surface", 1.5))
        c.add(text(cp[0] + 8, cp[1] - 34, "CP", 13, "start", colr, weight=700))
    c.add(text(612, 476, "Leading edge on the right; hollow dot = where the CP was. The CG does not move with angle of attack.", 11, "end", "fg-faint"))
    return c


@chart
def relative_airflow_climb_descent() -> Canvas:
    c = Canvas("The relative airflow follows the flight path",
               "Three side views. In level flight the relative airflow comes from straight ahead. In a climb the aeroplane moves up the slope, "
               "so the relative airflow comes from ahead and slightly above. In a descent it comes from ahead and slightly below. In every case "
               "it is parallel and opposite to the flight path, whatever the horizon or the nose attitude.", height=456, prefix="rac")
    c.add(text(20, 30, "Where does the air come from? Straight back down the flight path", 15, "start", "fg", weight=700))
    rows = [(0, 3, 62, "Level", "from straight ahead"), (8, 12, 84, "Climb", "from ahead and slightly above"),
            (-7, -3, 42, "Descent", "from ahead and slightly below")]
    for i, (gamma, pitch, dy, head, sub) in enumerate(rows):
        top = 46 + i * 130
        PX, PY = 290, top + dy
        c.add(panel(14, top, 612, 120))
        c.add(text(28, top + 26, head, 15, "start", "fg", weight=700))
        c.add(text(28, top + 50, "relative airflow", 12, "start", "brand", weight=600))
        c.add(text(28, top + 66, sub, 12, "start", "brand"))
        ux, uy = unit(gamma)
        if gamma:
            c.add(line(PX, PY, PX + 300, PY, "fg-faint", THIN, DASH))
            c.add(text(PX + 300, PY + (16 if gamma > 0 else -8), "horizontal", 11, "end", "fg-faint"))
        c.add(line(PX - ux * 50, PY - uy * 50, PX + ux * 300, PY + uy * 300, "fg-muted", SECOND, DASH))
        c.add(plane_side(PX, PY, 0.7, pitch=pitch))
        lx, ly = PX + ux * 104, PY + uy * 104
        c.add(text(lx, ly + (-8 if gamma == 0 else -16 if gamma > 0 else 20), "flight path", 11, "start", "fg-muted"))
        for off in (-14, 14):
            nx, ny = -uy, ux
            sx, sy = PX + ux * 320 + nx * off, PY + uy * 320 + ny * off
            ex, ey = PX + ux * 212 + nx * off, PY + uy * 212 + ny * off
            c.add(arrow(sx, sy, ex, ey, "brand", 3))
    c.add(text(20, 446, "Angles exaggerated. The angle of attack is measured from this airflow to the chord line.", 11, "start", "fg-faint"))
    return c


# ================================================================ BAKC 4.2 lift and drag
@chart
def induced_drag_downwash() -> Canvas:
    c = Canvas("How downwash creates induced drag",
               "A wing section flying to the right. The free-stream relative airflow comes from straight ahead, but the downwash from the "
               "wing-tip vortices makes the air at the wing move slightly down, so the effective airflow is tilted. Lift acts at right angles to "
               "that tilted airflow, so the lift vector leans backwards. Its rearward part is induced drag. Inset: seen from behind, the tip "
               "vortices push the air between them down. Angles are exaggerated.", height=430, prefix="idd")
    c.add(text(20, 30, "Downwash tilts the lift vector back: the backward part is induced drag", 15, "start", "fg", weight=700))
    X, Y, TILT, L = 380, 256, 16, 160
    for yy in (86, 116):
        c.add(arrow(624, yy, 548, yy, "sky-fg", SECOND))
    c.add(text(624, 140, "free-stream relative airflow", 12, "end", "sky-fg", weight=600))
    ux, uy = unit(180 + TILT)
    for sy in (196, 236):
        c.add(arrow(580, sy, 580 + ux * 110, sy + uy * 110, "info", SECOND, dash="6 4"))
    c.add(multiline(624, 300, ["effective airflow at the wing,", "tilted down by the downwash"], 12, "end", "info", weight=600))
    sec, P = wing_section(X, Y, 220, 6)
    c.add(sec)
    cp = P(28, -1)
    lx, ly = cp[0] - L * math.sin(math.radians(TILT)), cp[1] - L * math.cos(math.radians(TILT))
    c.add(line(cp[0], cp[1], cp[0], ly - 8, "fg-faint", SECOND, DASH))
    c.add(multiline(cp[0] + 10, ly - 4, ["lift if the air", "were not deflected"], 11, "start", "fg-faint"))
    c.add(arrow(cp[0], cp[1], lx, ly, "fg", 3))
    c.add(text(lx - 18, (cp[1] + ly) / 2 - 10, "Lift", 15, "end", "fg", weight=700))
    c.add(multiline(lx - 18, (cp[1] + ly) / 2 + 8, ["at right angles to", "the effective airflow"], 12, "end", "fg"))
    c.add(arrow(cp[0], ly, lx, ly, "brand", 4))
    c.add(text(lx - 8, ly - 20, "Induced drag:", 14, "end", "brand", weight=700))
    c.add(text(lx - 8, ly - 4, "the backward part", 12, "end", "brand"))
    c.add(path(arc_path(cp[0], cp[1], 64, -90 - TILT, -90), "fg-muted", None, SECOND))
    c.add(text(cp[0] + 6, cp[1] - 50, "tilt", 11, "start", "fg-muted"))
    # inset: rear view with vortices
    IX, IY, top = 114, 372, 300
    c.add(panel(14, top, 200, 112))
    c.add(text(26, top + 20, "Seen from behind", 12, "start", "fg", weight=700))
    c.add(line(44, IY - 24, 184, IY - 24, "fg", 3))
    c.add(circle(IX, IY - 24, 6, "surface", "fg", SECOND))
    # left tip: outward below, up round the tip, inward on top (clockwise); right tip mirror image
    c.add(path(arc_path(40, IY - 24, 13, 60, 300), "sky-fg", None, SECOND, arrow_end=True))
    c.add(path(arc_path(188, IY - 24, 13, 120, -120), "sky-fg", None, SECOND, arrow_end=True))
    c.add(arrow(IX - 32, IY - 12, IX - 32, IY + 10, "info", SECOND), arrow(IX + 32, IY - 12, IX + 32, IY + 10, "info", SECOND))
    c.add(text(IX, IY + 30, "downwash in between", 12, "middle", "info", weight=600))
    c.add(text(620, 420, "Angles exaggerated. Biggest when slow, heavy or turning (high angle of attack).", 11, "end", "fg-faint"))
    return c


@chart
def parasite_drag_types() -> Canvas:
    c = Canvas("The three parts of parasite drag",
               "Form drag: a flat plate leaves a large low-pressure wake, a streamlined shape a small one. Skin friction drag: the air touching the "
               "skin is brought to rest and the boundary layer above it is sheared; a rough surface thickens it. Interference drag: front view of a "
               "high strut-braced wing; where the wing meets the cabin roof and where each strut meets the wing, the flows disturb each other, and "
               "a fillet smooths the wing root. All three grow with the square of the speed.",
               height=420, prefix="pdt")
    c.add(text(20, 30, "Parasite drag: the cost of pushing the aeroplane through the air", 15, "start", "fg", weight=700))
    W = 196
    for i, (h, sub) in enumerate((("Form", "shape and wake"), ("Skin friction", "sticky air at the surface"), ("Interference", "where parts join"))):
        x0 = 14 + i * (W + 10)
        c.add(panel(x0, 48, W, 316))
        c.add(text(x0 + W / 2, 72, f"{h} drag", 14, "middle", "brand", weight=700))
        c.add(text(x0 + W / 2, 90, sub, 12, "middle", "fg-muted"))
    # --- form: plate vs streamlined body, air from the right
    x0 = 14
    for yy, streamlined in ((150, False), (262, True)):
        for dy in ((-26, 26) if not streamlined else (-22, 10)):
            c.add(arrow(x0 + 184, yy + dy, x0 + 154, yy + dy, "sky-fg", SECOND))
        if not streamlined:
            c.add(rect(x0 + 112, yy - 30, 8, 60, "surface", "fg", MAIN, rx=2))
            c.add(ellipse(x0 + 66, yy, 46, 26, "bad", None, fill_opacity=0.18))
            for k in range(3):
                c.add(path(arc_path(x0 + 48 + k * 18, yy - 6 + (k % 2) * 10, 7, 0, 300), "bad", None, THIN))
            c.add(text(x0 + 66, yy + 46, "blunt: big wake", 12, "middle", "bad", weight=600))
        else:
            c.add(path(f"M{x0 + 132} {yy} C{x0 + 132} {yy - 16} {x0 + 112} {yy - 16} {x0 + 96} {yy - 12} L{x0 + 36} {yy} L{x0 + 96} {yy + 12} "
                       f"C{x0 + 112} {yy + 16} {x0 + 132} {yy + 16} {x0 + 132} {yy} Z", "fg", "surface", MAIN))
            c.add(ellipse(x0 + 26, yy, 12, 5, "bad", None, fill_opacity=0.18))
            c.add(text(x0 + W / 2, yy + 40, "streamlined: small wake", 12, "middle", "ok-fg", weight=600))
    c.add(text(x0 + W / 2, 350, "spats, cowlings, tapered tails", 11, "middle", "fg-muted"))
    # --- skin friction: velocity profile over a surface
    x0 = 14 + W + 10
    SY = 250
    c.add(rect(x0 + 16, SY, W - 32, 14, "surface", "fg", MAIN))
    for k in range(9):
        c.add(path(f"M{x0 + 24 + k * 18} {SY} l4 -4 l4 4", "fg-muted", None, THIN))
    c.add(text(x0 + W / 2, SY + 34, "rough skin: dirt, insects, frost", 11, "middle", "fg-muted"))
    # profile: arrows growing with height, air from the right flowing left
    BX = x0 + 150
    for k, (h, L) in enumerate(((6, 8), (20, 32), (36, 56), (54, 74), (76, 86), (100, 90), (124, 90))):
        y = SY - h
        c.add(line(BX, y, BX - L, y, "sky-fg", SECOND if k else THIN, arrow_end=L > 10))
    prof = [(BX - L, SY - h) for h, L in ((0, 0), (6, 8), (20, 32), (36, 56), (54, 74), (76, 86), (100, 90))]
    c.add(path(smooth_path(prof), "brand", None, MAIN))
    c.add(line(BX, SY, BX, SY - 130, "fg-faint", THIN, DASH))
    c.add(line(x0 + 30, SY - 2, x0 + 30, SY - 92, "brand", SECOND))
    c.add(line(x0 + 26, SY - 92, x0 + 34, SY - 92, "brand", SECOND), line(x0 + 26, SY - 2, x0 + 34, SY - 2, "brand", SECOND))
    c.add(multiline(x0 + 38, SY - 60, ["boundary", "layer"], 12, "start", "brand", weight=700))
    c.add(text(x0 + W - 18, SY + 50, "air touching the skin is at rest", 11, "end", "fg-muted"))
    c.add(text(x0 + W / 2, 350, "a clean, polished wing is faster", 11, "middle", "fg-muted"))
    # --- interference: front view of a high strut-braced wing (the Cessna 152 is the textbook case)
    x0 = 14 + 2 * (W + 10)
    JX, JY = x0 + 98, 196
    c.add(circle(JX, JY, 30, "surface", "fg", MAIN))
    for sg in (-1, 1):
        c.add(line(JX + sg * 24, JY + 18, JX + sg * 64, JY - 30, "fg", SECOND))           # strut
    c.add(rect(x0 + 8, JY - 38, W - 16, 8, "surface", "fg", MAIN, rx=2))                  # wing across the cabin roof
    for zx, zr in ((JX - 22, 11), (JX + 22, 11), (JX - 62, 10), (JX + 62, 10)):          # root corners, strut-wing junctions
        c.add(circle(zx, JY - 26, zr, "bad", None, fill_opacity=0.2))
        c.add(path(arc_path(zx, JY - 26, zr * 0.55, 20, 320), "bad", None, THIN))
    c.add(text(JX, JY - 52, "front view", 11, "middle", "fg-faint"))
    c.add(text(JX, JY + 50, "flows meet and disturb", 12, "middle", "bad", weight=600))
    c.add(text(JX, JY + 66, "each other at every junction", 12, "middle", "bad"))
    FY = 312
    c.add(circle(JX, FY, 24, "surface", "fg", MAIN))
    for sg in (-1, 1):   # fillets fill the corners between the wing's underside and the round cabin
        curve = f"M{JX + sg * 38} {FY - 24} Q{JX + sg * 24} {FY - 24} {fmt(JX + sg * 22.6)} {FY - 8}"   # ends on the circle
        c.add(path(f"{curve} A24 24 0 0 {1 if sg < 0 else 0} {JX} {FY - 24} Z", None, "surface"))
        c.add(path(curve, "fg", None, MAIN))
    c.add(rect(x0 + 20, FY - 31, W - 40, 7, "surface", "fg", MAIN, rx=2))
    c.add(text(JX, FY + 42, "fillets smooth the joint", 11, "middle", "ok-fg", weight=600))
    c.add(rect(14, 374, 612, 36, "brand-soft", None, rx=8))
    c.add(text(320, 397, "All three grow with speed squared: twice the speed, four times the parasite drag", 13, "middle", "brand-fg", weight=700))
    return c


# ================================================================ BAKC 4.3 climbing
@chart
def climb_gradient_units() -> Canvas:
    c = Canvas("One climb gradient, three ways of writing it",
               "A climb path rising 450 ft over 1 nautical mile, about 6,076 ft, drawn with the height stretched. 450 ft per NM is about 7.4 percent "
               "and a little over 4 degrees. Conversions: 1 percent is about 61 ft per NM; 1 degree is about 106 ft per NM for shallow climbs.",
               height=360, prefix="cgu")
    c.add(text(20, 30, "450 ft per NM = about 7.4% = a little over 4°", 16, "start", "fg", weight=700))
    X0, Y0, X1, Y1 = 50, 236, 470, 86
    c.add(ground(30, 500, Y0 + 2))
    c.add(polygon([(X0, Y0), (X1, Y0), (X1, Y1)], "brand", None, fill_opacity=0.12))
    c.add(line(X0, Y0, X1, Y1, "brand", 3))
    c.add(plane_side(X0 + (X1 - X0) * 0.55, Y0 + (Y1 - Y0) * 0.55 - 12, 0.6, "brand", pitch=20))
    c.add(line(X0, Y0 + 22, X1, Y0 + 22, "fg-muted", THIN, arrow_end=True, arrow_start=True))
    c.add(num((X0 + X1) / 2, Y0 + 42, "1 NM ≈ 6,076 ft along the ground", 13, "middle", "fg-muted", weight=600))
    c.add(line(X1 + 18, Y0, X1 + 18, Y1, "fg-muted", THIN, arrow_end=True, arrow_start=True))
    c.add(num(X1 + 26, (Y0 + Y1) / 2, "450 ft", 14, "start", "fg", weight=700))
    c.add(path(arc_path(X0, Y0, 90, -20, 0), "warn", None, SECOND))
    c.add(text(X0 + 98, Y0 - 12, "≈ 4.2°", 13, "start", "warn-fg", weight=700))
    c.add(text(X0 + 4, Y1 + 10, "height stretched about 5 times", 11, "start", "fg-faint"))
    X = 400
    c.add(panel(X - 10, 300, 236, 52))
    c.add(num(X, 320, "1% ≈ 61 ft per NM", 12, "start", "fg", weight=600))
    c.add(num(X, 340, "1° ≈ 106 ft per NM", 12, "start", "fg", weight=600))
    c.add(panel(14, 300, 366, 52))
    c.add(num(26, 320, "%: 450 ÷ 6,076 × 100 ≈ 7.4%", 12, "start", "fg", weight=600))
    c.add(num(26, 340, "degrees: 450 ÷ 106 ≈ 4.2°", 12, "start", "fg", weight=600))
    return c


# ================================================================ BAKC 4.4 wake turbulence
@chart
def wake_sink_in_cruise() -> Canvas:
    c = Canvas("Behind and below: where the wake goes in the cruise",
               "Side view of a large aircraft in the cruise flying to the right. The pair of wing-tip vortices it leaves behind sinks at about 300 "
               "to 500 ft per minute and levels off about 500 to 1,000 ft below its flight path. The danger area is behind and below it. An "
               "aircraft crossing ahead at the same level or a little above leaves a wake that sinks across your path; passing above its path, or "
               "waiting until it is well clear, keeps you out of it.", height=380, prefix="wsc")
    c.add(text(20, 30, "In the cruise the wake sinks, then levels off below the aircraft's path", 15, "start", "fg", weight=700))
    TOP, BOT = 110, 250        # its level, and about 1,000 ft below
    MID = (TOP + BOT) / 2      # about 500 ft below
    c.add(line(30, TOP, 610, TOP, "fg-muted", SECOND, DASH))
    c.add(text(34, TOP - 8, "its flight path", 12, "start", "fg-muted"))
    c.add(plane_side(540, TOP, 0.9))
    c.add(rect(30, MID, 440, BOT - MID, "bad", None, fill_opacity=0.12))
    c.add(line(30, MID, 470, MID, "line-strong", THIN, DASH), line(30, BOT, 470, BOT, "line-strong", THIN, DASH))
    c.add(num(34, MID + 16, "≈ 500 ft below", 12, "start", "fg-muted"))
    c.add(num(34, BOT - 6, "≈ 1,000 ft below", 12, "start", "fg-muted"))
    pts = [(476, TOP + 8), (430, TOP + 28), (380, TOP + 62), (330, TOP + 90), (270, TOP + 104), (190, TOP + 108), (120, TOP + 108)]
    c.add(path(smooth_path(pts), "brand", None, MAIN, "6 4"))
    for x, y in pts[1:]:
        c.add(circle(x - 4, y - 3, 6, "brand-soft", "brand", SECOND), circle(x + 4, y + 3, 6, "brand-soft", "brand", SECOND))
    c.add(callout(392, TOP + 54, 486, TOP + 70, ["vortices sink about", "300 to 500 ft/min"], "brand", 12))
    c.add(text(250, BOT + 22, "the wake levels off here: behind and below is the danger area", 12, "middle", "bad", weight=700))
    c.add(plane_side(170, TOP - 44, 0.45, "ok"))
    c.add(text(204, TOP - 50, "you, above its path: clear", 12, "start", "ok-fg", weight=600))
    c.add(rect(14, 290, 612, 76, "surface-2", None, rx=8))
    c.add(text(26, 312, "Crossing traffic at your level or a little above:", 13, "start", "fg", weight=700))
    c.add(text(26, 332, "its wake sinks across your path. Pass above its flight path, or wait until it is well clear.", 12, "start", "fg-muted"))
    c.add(text(26, 352, "Heights and rates are typical values from the lesson, not limits. Not to scale.", 11, "start", "fg-faint"))
    return c


# ================================================================ BAKC 4.5 thrust stream turbulence
@chart
def rotor_downwash_outflow() -> Canvas:
    c = Canvas("Rotor downwash spreads outward in every direction",
               "Left: side view of a helicopter hovering close to the ground. The rotor pushes air down to hold up the helicopter's weight; the air "
               "hits the ground and spreads outward along the surface on every side. Right: plan view comparing the ring of disturbed air round a "
               "hovering helicopter with the cone behind a jet. A heavier helicopter makes a stronger and wider ring. The flow weakens with distance.",
               height=420, prefix="rdo")
    c.add(text(20, 30, "Downwash is a ring round the helicopter, not a cone behind it", 15, "start", "fg", weight=700))
    # side view
    c.add(panel(14, 46, 360, 290))
    c.add(text(28, 68, "Side view, hovering low", 13, "start", "fg", weight=700))
    HX, HY, GY = 192, 150, 290
    c.add(ground(24, 364, GY + 2))
    for dx in (-50, -18, 18, 50):
        c.add(arrow(HX + dx, HY + 6, HX + dx * 1.1, GY - 52, "brand", MAIN))
    for sgn in (-1, 1):
        for k, (y, L) in enumerate(((GY - 12, 92), (GY - 30, 70))):
            x0 = HX + sgn * 70
            c.add(path(smooth_path([(HX + sgn * 52, GY - 46), (x0, y + 4), (x0 + sgn * L, y)]), "brand", None, SECOND if k else MAIN, arrow_end=True))
    c.add(helicopter_side(HX, HY - 30, 1.3))
    c.add(text(194, GY + 24, "air hits the ground and spreads out on every side", 12, "middle", "brand", weight=600))
    c.add(plane_side(334, GY - 12, 0.4, "fg-muted"))
    c.add(text(330, GY - 58, "light aeroplane", 11, "middle", "fg-muted"))
    # plan view
    c.add(panel(386, 46, 240, 290))
    c.add(text(398, 68, "Plan view", 13, "start", "fg", weight=700))
    RX, RY = 506, 160
    c.add(circle(RX, RY, 72, "brand", None, fill_opacity=0.1), circle(RX, RY, 46, "brand", None, fill_opacity=0.14))
    for b in range(0, 360, 45):
        x0, y0 = bxy(RX, RY, 30, b)
        x1, y1 = bxy(RX, RY, 64, b)
        c.add(arrow(x0, y0, x1, y1, "brand", SECOND))
    c.add(circle(RX, RY, 22, None, "fg", SECOND, dash="4 3"), circle(RX, RY, 5, "fg", None))
    c.add(text(RX, RY + 92, "helicopter: a ring, all round", 12, "middle", "brand", weight=600))
    JX, JY = 572, 288
    c.add(path(f"M{JX - 40} {JY - 6} L{JX - 160} {JY - 22} Q{JX - 172} {JY} {JX - 160} {JY + 22} L{JX - 40} {JY + 6} Z", None, "warn", 0, fill_opacity=0.22))
    c.add(jet_top(JX, JY, 0.42))
    c.add(text(JX - 100, JY + 40, "jet: a cone behind", 12, "middle", "warn-fg", weight=600))
    c.add(rect(14, 346, 612, 66, "surface-2", None, rx=8))
    c.add(text(26, 366, "Heavier helicopter: a stronger and wider ring.", 12, "start", "fg", weight=700))
    c.add(text(26, 384, "The flow weakens with distance, but reaches further than you might expect across an apron.", 12, "start", "fg-muted"))
    c.add(text(26, 402, "Keep well clear of hovering and hover-taxiing helicopters; do not taxi downwind of them.", 12, "start", "fg-muted"))
    return c


@chart
def breakaway_thrust_swing() -> Canvas:
    c = Canvas("Breakaway thrust swings the blast across the apron",
               "Plan view of an apron. A jet that has been stationary with its beacon on applies breakaway thrust to start moving and turns left "
               "out of its bay, often using more power on one engine. As it turns, its blast sweeps sideways across the apron, over a light "
               "aeroplane waiting nearby. Breakaway thrust is considerably greater than idle. Not to scale.", height=400, prefix="bts")
    c.add(text(20, 30, "A stationary jet about to move is the one to watch", 15, "start", "fg", weight=700))
    JX, JY, HD = 486, 124, 50       # jet heading (bearing on the page, 0 = up) part-way through a left turn from 090
    tail = bxy(JX, JY, 44, HD + 180)

    def wedge(b: float, L: float, half: float, colr: str, op: float) -> str:
        return polygon([tail, bxy(*tail, L, b - half), bxy(*tail, L, b + half)], colr, None, fill_opacity=op)
    c.add(wedge(270, 230, 8, "warn", 0.10), wedge(250, 230, 8, "warn", 0.14), wedge(230, 230, 9, "bad", 0.18))
    c.add(path(barc(*tail, 206, 236, 266), "bad", None, MAIN))
    c.add(arrow(*bxy(*tail, 206, 236), *bxy(*tail, 206, 229), "bad", MAIN))
    c.add(multiline(196, 236, ["blast swings", "as it turns"], 13, "end", "bad", weight=700))
    c.add(text(250, 104, "blast before the turn", 11, "middle", "fg-faint"))
    c.add(group(jet_top(0, 0, 0.8), transform=f"translate({fmt(JX)} {fmt(JY)}) rotate({fmt(HD - 90)})"))
    c.add(path(arc_path(JX, JY, 84, 120 - 90, 70 - 90), "fg-muted", None, SECOND, arrow_end=True))
    c.add(multiline(JX + 50, JY + 100, ["turning left", "out of the bay"], 12, "start", "fg-muted", weight=600))
    lx, ly = bxy(*tail, 160, 234)
    c.add(plane_top(lx, ly, 0.36, 0, "bad", "bad-soft"))
    c.add(multiline(lx + 26, ly + 4, ["light aeroplane", "now in the blast"], 12, "start", "bad", weight=600))
    c.add(panel(326, 286, 300, 106))
    c.add(text(338, 308, "Breakaway thrust", 13, "start", "fg", weight=700))
    c.add(multiline(338, 328, ["the power to start moving from rest, or to", "turn: considerably greater than idle."], 12, "start", "fg-muted"))
    c.add(multiline(338, 366, ["Beacon on and stationary:", "assume breakaway thrust is coming."], 12, "start", "warn-fg", weight=600))
    c.add(text(20, 392, "Not to scale.", 11, "start", "fg-faint"))
    return c
