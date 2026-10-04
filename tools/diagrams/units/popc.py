"""POPC (PPL operations, performance and planning) diagrams. Numbers come from content/notes/POPC/*.md."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, arrow, badge, circle, fmt, group, line, multiline, num, path,
                                plane_top, polygon, polyline, rect, sample, text)


# ---------------------------------------------------------------- 2.6 ETP, PNR and diversions
def _track_row(c: Canvas, y: float, D: float, a: str, b: str, x0: float = 80, x1: float = 530) -> callable:
    """Draw a departure-to-destination track at height y; returns nm -> x."""
    X = lambda d: x0 + d / D * (x1 - x0)
    c.add(line(x0, y, x1, y, "line-strong", MAIN))
    for x, name in ((x0, a), (x1, b)):
        c.add(circle(x, y, 6, "surface", "fg", MAIN))
        c.add(text(x, y + 24, name, 12, "middle", "fg", weight=600))
    return X


def _etp_marker(c: Canvas, x: float, y: float, label: str, colour: str = "brand") -> None:
    c.add(polygon([(x, y - 9), (x + 8, y), (x, y + 9), (x - 8, y)], colour, "surface", 1.5))
    c.add(text(x, y - 16, label, 13, "middle", colour, weight=700, cls="num"))


def _wind(c: Canvas, x: float, y: float, to_right: bool, label: str) -> None:
    if to_right:
        c.add(arrow(x - 34, y, x + 10, y, "info", MAIN))
    else:
        c.add(arrow(x + 10, y, x - 34, y, "info", MAIN))
    c.add(text(x + 18, y + 4, label, 12, "start", "info", weight=600))


@chart
def etp_pnr_geometry() -> Canvas:
    c = Canvas("Where the ETP sits, and where the PNR sits",
               "Three copies of the note's 180 nm leg flown at 110 kt TAS. In still air the equi-time point is at the 90 nm midpoint. With a 20 kt "
               "headwind outbound (groundspeed on 90 kt, home 130 kt) it moves 16 nm towards the destination, to 106 nm, where both ways take about "
               "49 minutes. With a 20 kt tailwind outbound (on 130 kt, home 90 kt) it moves 16 nm back towards departure, to 74 nm. Below, the "
               "note's Jandakot to Kalgoorlie leg of 295 nm with a 25 kt headwind: ETP 181 nm, and the point of no return, which depends on fuel, "
               "at 213 nm.", height=530, prefix="etp")
    c.add(text(20, 28, "The ETP moves into wind", 16, "start", "fg", weight=700))
    c.add(text(20, 46, "180 nm leg, TAS 110 kt: where is going on as quick as going back?", 12, "start", "fg-muted"))
    D = 180
    rows = [(110, "Still air", None, 90, 110, 110, "ETP 90 nm, midpoint"),
            (222, "20 kt headwind outbound", False, 106.4, 90, 130, "ETP 106 nm"),
            (334, "20 kt tailwind outbound", True, 73.6, 130, 90, "ETP 74 nm")]
    for y, title, to_right, etp, gs_on, gs_home, lab in rows:
        c.add(text(80, y - 40, title, 13, "start", "fg", weight=700))
        if to_right is not None:
            _wind(c, 420, y - 44, to_right, "wind")
        X = _track_row(c, y, D, "departure", "destination")
        mid = X(90)
        if etp != 90:
            c.add(line(mid, y - 8, mid, y + 8, "fg-faint", SECOND))
            c.add(text(mid, y + 24, "midpoint", 11, "middle", "fg-faint"))
            c.add(arrow(mid, y + 36, X(etp), y + 36, "brand", SECOND))
            c.add(text((mid + X(etp)) / 2, y + 52, "16 nm into wind", 11, "middle", "brand-fg", weight=600))
        _etp_marker(c, X(etp), y, lab)
        t = etp / gs_home * 60
        c.add(text(150, y - 8, f"← home {gs_home} kt", 11, "middle", "fg-muted"))
        c.add(text(460, y - 8, f"on {gs_on} kt →", 11, "middle", "fg-muted"))
        c.add(num(582, y - 2, f"{round(t)} min", 13, "middle", "brand-fg", weight=700))
        c.add(text(582, y + 14, "each way", 11, "middle", "fg-muted"))
    # Kalgoorlie: ETP and PNR on one leg
    c.add(line(20, 398, 620, 398, "line", THIN))
    y = 470
    c.add(text(20, 420, "Both points on one leg: Jandakot to Kalgoorlie, 295 nm, 25 kt headwind, 150 L", 13, "start", "fg", weight=700))
    X = _track_row(c, y, 295, "Jandakot", "Kalgoorlie")
    c.add(rect(X(213), y - 5, 530 - X(213), 10, "warn-soft", None))
    c.add(line(X(213), y, 530, y, "warn", MAIN))
    _etp_marker(c, X(181), y, "ETP 181")
    c.add(line(X(213), y - 12, X(213), y + 12, "warn", 3))
    c.add(text(X(213) + 4, y - 16, "PNR 213", 13, "start", "warn-fg", weight=700, cls="num"))
    c.add(text(X(181), y + 24, "time", 11, "middle", "brand-fg", weight=600))
    c.add(text(X(213) + 4, y + 24, "fuel", 11, "start", "warn-fg", weight=600))
    c.add(text(590, y - 2, "past the PNR:", 11, "middle", "warn-fg", weight=600))
    c.add(text(590, y + 12, "committed", 11, "middle", "warn-fg", weight=600))
    c.add(text(20, 518, "The ETP depends only on distance and groundspeeds; the PNR moves whenever the fuel does.", 12, "start", "fg-muted"))
    return c


@chart
def pnr_fuel_out_and_back() -> Canvas:
    c = Canvas("Splitting the safe endurance between out and back",
               "The note's worked example: TAS 110 kt, 10 kt headwind outbound, groundspeed out 100 kt and home 120 kt, safe endurance 2.5 hours "
               "after the taxi allowance and the fixed reserve. The point of no return is 136 nm out: 82 minutes to fly out against the wind and 68 "
               "minutes to fly back with it, which together use the whole 150 minutes. The fixed reserve is still in the tanks on landing.",
               height=400, prefix="pnr")
    c.add(text(20, 28, "Out to the PNR and back uses all the safe endurance", 16, "start", "fg", weight=700))
    c.add(text(20, 46, "TAS 110 kt, 10 kt headwind outbound, E = 2.5 h after taxi and reserve", 12, "start", "fg-muted"))
    # route
    x0, x1 = 70, 470
    X = lambda d: x0 + d / 136.4 * (x1 - x0)
    y = 140
    c.add(line(x0, y, 600, y, "line-strong", MAIN))
    c.add(line(x1, y, 600, y, "line", MAIN, dash=DASH))
    c.add(text(604, y + 4, "→", 13, "start", "fg-faint"))
    c.add(text(560, y + 24, "on to the", 11, "middle", "fg-faint"))
    c.add(text(560, y + 38, "destination", 11, "middle", "fg-faint"))
    c.add(circle(x0, y, 6, "surface", "fg", MAIN))
    c.add(text(x0, y + 24, "departure", 12, "middle", "fg", weight=600))
    c.add(line(x1, y - 14, x1, y + 14, "warn", 3))
    c.add(text(x1, y + 30, "PNR 136 nm", 13, "middle", "warn-fg", weight=700, cls="num"))
    c.add(arrow(x0 + 10, y - 26, x1 - 6, y - 26, "brand", MAIN))
    c.add(text((x0 + x1) / 2, y - 36, "out at 100 kt: 82 min", 13, "middle", "brand", weight=700))
    c.add(path(f"M{x1 - 6} {y - 26} C{x1 + 26} {y - 26} {x1 + 26} {y + 52} {x1 - 6} {y + 52}", "info", None, MAIN, dash=DASH))
    c.add(arrow(x1 - 6, y + 52, x0 + 10, y + 52, "info", MAIN))
    c.add(text((x0 + x1) / 2, y + 72, "back at 120 kt: 68 min", 13, "middle", "info", weight=700))
    c.add(arrow(330, 74, 270, 74, "fg-muted", SECOND))
    c.add(text(338, 78, "10 kt wind", 12, "start", "fg-muted"))
    # the fuel bar
    top = 262
    L, R = 70, 600
    total = 10 + 150 + 30   # taxi, endurance, reserve in minutes (taxi schematic)
    M = lambda m: L + m / total * (R - L)
    c.add(text(L, top - 14, "The fuel on board, as minutes of flight", 13, "start", "fg", weight=700))
    segs = [(0, 10, "surface-2", "fg-muted", "", "taxi"),
            (10, 10 + 81.8, "brand-soft", "brand", "out 82 min", ""),
            (91.8, 160, "info-soft", "info", "back 68 min", ""),
            (160, 190, "ok-soft", "ok", "reserve", "")]
    for a, b, fill, stroke, lab, below in segs:
        c.add(rect(M(a), top, M(b) - M(a), 40, fill, stroke, SECOND))
        if lab:
            c.add(text((M(a) + M(b)) / 2, top + 25, lab, 13, "middle", f"{stroke}-fg" if stroke != "ok" else "ok-fg", weight=700))
    c.add(text(M(5), top + 58, "taxi", 11, "middle", "fg-muted"))
    c.add(path(f"M{M(10)} {top + 50} L{M(10)} {top + 56} L{M(160)} {top + 56} L{M(160)} {top + 50}", "fg-muted", None, THIN))
    c.add(text(M(85), top + 74, "safe endurance E = 2.5 h = 150 min: 82 + 68", 12, "middle", "fg", weight=600))
    c.add(text(M(175), top + 58, "never spent:", 11, "middle", "ok-fg"))
    c.add(text(M(175), top + 72, "land with it", 11, "middle", "ok-fg"))
    c.add(text(20, 370, "Swap the wind (120 kt out, 100 kt home): still 136 nm, but reached after 68 min.", 12, "start", "fg-muted"))
    c.add(text(20, 388, "Still air would give 137.5 nm: any wind brings the PNR closer.", 12, "start", "fg-muted"))
    return c


@chart
def diversion_fuel_ladder() -> Canvas:
    c = Canvas("Which options leave the reserve intact?",
               "The note's three options from a position 100 nm out with 55 L on board, fuel flow 36 L/h and an 18 L fixed reserve. Proceed to the "
               "destination: 34 L trip plus 18 L reserve is 52 L, 3 L spare. Return to departure: 29 plus 18 is 47 L, 8 L spare. Divert to the "
               "alternate: 16 plus 18 is 34 L, 21 L spare. If the destination needed 30 minutes of holding, 18 L more, proceeding would need 70 L, "
               "15 L more than is on board.", height=360, prefix="dfl")
    c.add(text(20, 28, "Fuel each option needs, against the 55 L on board", 16, "start", "fg", weight=700))
    c.add(text(20, 46, "from 100 nm out: trip fuel, then holding, then the 18 L fixed reserve on top", 12, "start", "fg-muted"))
    L, R = 200, 520
    F = lambda l: L + l / 75 * (R - L)
    rows = [("Proceed to destination", 34, 0, "3 L spare", "ok"),
            ("Return to departure", 29, 0, "8 L spare", "ok"),
            ("Divert to alternate", 16, 0, "21 L spare", "ok"),
            ("Destination, 30 min hold", 34, 18, "15 L short", "bad")]
    for i, (name, trip, hold, verdict, tone) in enumerate(rows):
        y = 84 + i * 56
        c.add(text(L - 12, y + 19, name, 13, "end", "fg", weight=600))
        segs = [(0, trip, "brand-soft", "brand", f"trip {trip}"), (trip, trip + hold, "warn-soft", "warn", f"hold {hold}"),
                (trip + hold, trip + hold + 18, "ok-soft", "ok", "res 18")]
        for a, b, fill, stroke, lab in segs:
            if b > a:
                c.add(rect(F(a), y, F(b) - F(a), 28, fill, stroke, SECOND))
                la = 55 if a < 55 < b else a   # keep the label clear of the 55 L line
                c.add(num((F(la) + F(b)) / 2, y + 19, lab, 12, "middle", f"{stroke}-fg", weight=600))
        tot = trip + hold + 18
        c.add(num(536, y + 12, f"{tot} L", 13, "start", "fg", weight=700))
        c.add(text(536, y + 27, verdict, 12, "start", f"{tone}-fg" if tone != "bad" else "bad", weight=600))
    c.add(rect(F(55), 76, F(75) - F(55), 222, "bad", None, fill_opacity=0.08))
    c.add(line(F(55), 74, F(55), 300, "fg", MAIN))
    c.add(text(F(55) + 6, 70, "55 L on board", 13, "start", "fg", weight=700))
    for v in (0, 20, 40, 55, 70):
        c.add(num(F(v), 318, str(v), 11, "middle", "fg-muted"))
    c.add(text((L + R) / 2, 338, "fuel (L)", 12, "middle", "fg-muted", weight=600))
    c.add(text(20, 354, "A bar past the line would land below the reserve: that option is not available.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.2 speed limitations (shared with BAKC 6.3)
@chart
def gust_load_vs_airspeed() -> Canvas:
    c = Canvas("The same gust hits harder at higher speed",
               "A V-n diagram for a normal category aeroplane (schematic speeds). Gust lines fan out from 1 g at zero speed: the extra load from a "
               "given gust grows in proportion to airspeed. An example gust that adds 1.0 g at 100 kt (2.0 g in all) adds 1.3 g at 130 kt (2.3 g). "
               "The strongest design gust stays inside the +3.8 g limit up to VNO and crosses it just beyond VNO. At low speed the same gust line "
               "runs into the stall curve first: the wing stalls momentarily instead of overloading the structure.",
               height=430, prefix="gst")
    VS, VA, VNO, VNE = 55, 55 * math.sqrt(3.8), 140, 170   # VS and VA from the POPC 2.2 example; VNO, VNE schematic
    k_design = 2.8 / 150                                     # design gust: 3.8 g at 150 kt, just past VNO
    ch = Chart(c, (0, 180), (0, 5), box=(70, 50, 520, 370), xlabel="Indicated airspeed (kt)", ylabel="Load factor  n (g)",
               xticks=[100, 130], yticks=[1, 2, 2.3, 3.8], yfmt=lambda v: fmt(v), grid=False)
    c.add(text(20, 28, "Each gust line starts at 1 g and climbs with speed", 16, "start", "fg", weight=700))
    # regions
    c.add(rect(ch.px(VNO), ch.py(3.8), ch.px(VNE) - ch.px(VNO), ch.bottom - ch.py(3.8), "warn-soft", None))
    c.add(rect(ch.px(VA), ch.top, ch.right - ch.px(VA), ch.py(3.8) - ch.top, "bad", None, fill_opacity=0.10))
    c.add(ch.axes())
    c.add(line(ch.left, ch.py(1), ch.right, ch.py(1), "line-strong", THIN, DASH))
    # stall curve and limit
    c.add(ch.curve(sample(lambda v: (v / VS) ** 2, VS, VA, 30), "fg", MAIN))
    c.add(line(ch.px(VA), ch.py(3.8), ch.right, ch.py(3.8), "bad", MAIN))
    c.add(line(ch.px(VNE), ch.py(3.8), ch.px(VNE), ch.bottom, "bad", SECOND))
    c.add(text(ch.right + 6, ch.py(3.8) + 4, "+3.8 g limit", 12, "start", "bad", weight=700))
    c.add(text(ch.px(VA) - 8, ch.py(3.8) + 2, "stall curve", 12, "end", "fg-muted", weight=600))
    # gust lines from (0, 1g); the design gust is dashed where the wing would stall first
    a, b = 1 / VS ** 2, -k_design
    v_meet = (-b + math.sqrt(b * b + 4 * a)) / (2 * a)
    n_meet = 1 + k_design * v_meet
    c.add(line(ch.px(0), ch.py(1), ch.px(v_meet), ch.py(n_meet), "fg-faint", SECOND, DASH))
    c.add(line(ch.px(v_meet), ch.py(n_meet), ch.right, ch.py(1 + k_design * 180), "bad", MAIN))
    c.add(line(ch.px(0), ch.py(1), ch.right, ch.py(1 + 0.010 * 180), "brand", MAIN))
    c.add(line(ch.px(0), ch.py(1), ch.right, ch.py(1 + 0.005 * 180), "fg-muted", SECOND))
    c.add(text(ch.right + 6, ch.py(1 + k_design * 180) + 4, "design gust", 12, "start", "bad", weight=700))
    c.add(text(ch.right + 6, ch.py(1 + 0.010 * 180) + 4, "example gust", 12, "start", "brand", weight=700))
    c.add(text(ch.right + 6, ch.py(1 + 0.005 * 180) + 4, "lighter gust", 12, "start", "fg-muted", weight=600))
    # the example: 100 kt and 130 kt
    for v, n in ((100, 2.0), (130, 2.3)):
        c.add(line(ch.px(v), ch.py(n), ch.px(v), ch.bottom, "brand", THIN, DASH))
        c.add(line(ch.left, ch.py(n), ch.px(v), ch.py(n), "brand", THIN, DASH))
        c.add(ch.point(v, n, "brand", 5))
    c.add(rect(84, 62, 156, 64, "surface-2", None, rx=6))
    c.add(text(94, 82, "Example gust", 12, "start", "brand-fg", weight=700))
    c.add(text(94, 99, "100 kt: 2.0 g (+1.0)", 12, "start", "fg"))
    c.add(text(94, 116, "130 kt: 2.3 g (+1.3)", 12, "start", "fg"))
    # design gust past VNO, and the slow end
    c.add(ch.point(150, 3.8, "bad", 5.5))
    c.add(multiline(ch.px(150), ch.py(4.65), ["past VNO the design", "gust overloads"], 12, "middle", "bad", weight=600))
    c.add(ch.point(v_meet, n_meet, "fg", 4))
    c.add(line(ch.px(v_meet) - 4, ch.py(n_meet) - 3, ch.px(86), ch.py(3.15), "fg-muted", THIN))
    c.add(multiline(ch.px(85), ch.py(3.35), ["slower: the wing", "stalls first"], 12, "end", "fg", weight=600))
    c.add(text(ch.px(VNO) - 4, ch.bottom - 8, "VNO", 12, "end", "warn-fg", weight=700))
    c.add(text(ch.px(VNE) + 4, ch.bottom - 8, "VNE", 12, "start", "bad", weight=700))
    c.add(text((ch.px(VNO) + ch.px(VNE)) / 2, ch.py(3.3), "smooth", 11, "middle", "warn-fg"))
    c.add(text((ch.px(VNO) + ch.px(VNE)) / 2, ch.py(3.3) + 14, "air only", 11, "middle", "warn-fg"))
    c.add(text(ch.left + 6, ch.py(1) + 16, "level flight, 1 g", 11, "start", "fg-faint"))
    c.add(text(620, 424, "Extra load grows in proportion to airspeed. Stall curve for VS 55 kt; VNO, VNE schematic.", 11, "end", "fg-faint"))
    return c


# ---------------------------------------------------------------- 2.3 ERSA: declared distances
@chart
def declared_distances() -> Canvas:
    c = Canvas("Declared distances and the chart figures they are compared with",
               "Plan view of the note's hypothetical runway, take-off and landing towards the right. The take-off run available, TORA, is 1,100 m "
               "of pavement. The clearway beyond the end adds to give the take-off distance available, TODA, 1,250 m; the chart's take-off "
               "distance to 50 ft, 1,020 m, fits with 230 m to spare. A stopway beyond the end adds to give the accelerate-stop distance available, "
               "ASDA. The threshold is displaced 150 m along the runway, so the landing distance available, LDA, is 950 m; the chart's landing "
               "distance of 980 m does not fit, 30 m short.", height=430, prefix="dcd")
    c.add(text(20, 28, "Which declared distance goes with which chart figure?", 16, "start", "fg", weight=700))
    c.add(text(20, 46, "the note's hypothetical runway; take-off and landing towards the right", 12, "start", "fg-muted"))
    x0, s = 92, 0.40                      # start of pavement; px per metre
    M = lambda m: x0 + m * s
    ry, rw = 104, 30                      # runway centreline y, width
    # clearway (area beyond the end) and stopway (pavement able to stop on)
    c.add(rect(M(1100), ry - 34, M(1250) - M(1100), 68, "ok-soft", "ok", THIN, dash=DASH, rx=3))
    c.add(text((M(1100) + M(1250)) / 2, ry - 40, "clearway", 12, "middle", "ok-fg", weight=600))
    c.add(rect(M(1100), ry - rw / 2, M(1160) - M(1100), rw, "tarmac", None))
    for k in range(3):
        xx = M(1104) + k * 8
        c.add(polyline([(xx, ry - 10), (xx + 6, ry), (xx, ry + 10)], "warn", SECOND))
    c.add(line((M(1100) + M(1160)) / 2, ry + 12, (M(1100) + M(1160)) / 2, ry + 44, "fg-faint", THIN))
    c.add(text((M(1100) + M(1160)) / 2, ry + 56, "stopway", 11, "middle", "warn-fg", weight=600))
    # runway
    c.add(rect(M(0), ry - rw / 2, M(1100) - M(0), rw, "tarmac", None))
    for k in range(1, 40):
        xx = M(150) + 20 + k * 22
        if xx + 11 < M(1100) - 26:
            c.add(line(xx, ry, xx + 11, ry, "paint", 2.4, cap="butt"))
    for k in range(3):                    # arrows on the pre-threshold area
        xx = M(20) + k * 20
        c.add(line(xx, ry, xx + 12, ry, "paint", 2, cap="butt"))
        c.add(polygon([(xx + 12, ry - 4), (xx + 18, ry), (xx + 12, ry + 4)], "paint", None))
    c.add(rect(M(150), ry - rw / 2, 4, rw, "paint", None))      # threshold bar
    for j in range(4):
        c.add(rect(M(150) + 8, ry - rw / 2 + 3 + j * 7, 16, 4, "paint", None))
    for j in range(4):
        c.add(rect(M(1100) - 22, ry - rw / 2 + 3 + j * 7, 16, 4, "paint", None))
    c.add(text(M(150), ry - 24, "displaced threshold", 11, "middle", "fg-muted", weight=600))
    c.add(text(M(0), ry + 30, "start of roll", 11, "start", "fg-muted"))
    # distance bars
    def bar(y: float, a: float, b: float, label: str, colour: str, fill: str | None = None, value: str = "") -> None:
        c.add(line(M(a), y, M(b), y, colour, MAIN, arrow_end=True, arrow_start=True))
        c.add(text(M(a) - 12, y + 5, label, 13, "end", colour, weight=700))
        if value:
            c.add(num((M(a) + M(b)) / 2, y - 7, value, 12, "middle", colour, weight=600))
    for m, y0, y1 in ((0, ry + 40, 300), (150, ry + 40, 370), (1100, ry + 64, 240), (1100, 264, 368), (1250, ry + 64, 240), (1250, 264, 300)):
        c.add(line(M(m), y0, M(m), y1, "line-strong", THIN, DASH))
    bar(170, 0, 1100, "TORA", "fg", value="1,100 m")
    bar(214, 0, 1250, "TODA", "brand", value="1,250 m: TORA + clearway")
    c.add(rect(M(0), 228, M(1020) - M(0), 12, "brand-soft", "brand", THIN, rx=2))
    c.add(text(M(470), 256, "chart take-off distance to 50 ft, 1,020 m", 11, "middle", "brand-fg"))
    c.add(text((M(1020) + M(1250)) / 2, 256, "230 m spare", 12, "middle", "ok-fg", weight=700))
    bar(292, 0, 1160, "ASDA", "fg-muted", value="TORA + stopway")
    bar(338, 150, 1100, "LDA", "warn-fg", value="950 m: from the threshold")
    c.add(rect(M(150), 352, M(1130) - M(150), 12, "bad-soft", "bad", THIN, rx=2))
    c.add(line(M(1100), 346, M(1100), 370, "bad", MAIN))
    c.add(text(M(640), 380, "chart landing distance from 50 ft, 980 m", 11, "middle", "bad"))
    c.add(text(M(1130) + 8, 363, "30 m short", 12, "start", "bad", weight=700))
    c.add(text(20, 418, "Take-off distance against TODA; landing distance against LDA, never the runway length.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.4 flight plan preparation (TAF window shared with PFRA 2.4)
@chart
def taf_arrival_window() -> Canvas:
    c = Canvas("Which TAF groups touch the arrival window?",
               "The note's Geraldton example on a timeline from 0230 to 0630 UTC. ETA 0400 UTC; the window runs from 30 minutes before to 60 "
               "minutes after, 0330 to 0500. The base conditions, 15012KT 9999 SCT030, pass the alternate minima. The TEMPO 0300/0600 group, 4000 "
               "SHRA BKN012, covers the whole window and fails both tests: broken cloud, more than scattered, below 1,500 ft, and visibility under "
               "8 km. A TEMPO needs 60 minutes of holding fuel, 28 L at 28 L/h, or an alternate such as Dongara, 15 L.",
               height=446, prefix="taw")
    c.add(text(20, 28, "Lay every TAF group against the window, not the ETA", 16, "start", "fg", weight=700))
    c.add(text(20, 46, "Geraldton, ETA 0400 UTC: TAF 15012KT 9999 SCT030 TEMPO 0300/0600 4000 SHRA BKN012", 12, "start", "fg-muted"))
    L, R = 130, 610
    T = lambda h: L + (h - 2.5) / 4 * (R - L)
    top, AY = 96, 250
    # window band
    c.add(rect(T(3.5), top - 18, T(5) - T(3.5), AY - top + 18, "brand-soft", None, opacity=0.8))
    c.add(text((T(3.5) + T(5)) / 2, top - 24, "window 0330 to 0500", 13, "middle", "brand-fg", weight=700))
    c.add(line(T(4), top - 14, T(4), top - 2, "brand", MAIN))
    c.add(line(T(4), top + 100, T(4), AY + 6, "brand", MAIN))
    c.add(badge(T(4), AY + 34, "ETA 0400", "brand", 12))
    c.add(arrow(T(4) - 6, AY - 14, T(3.5) + 2, AY - 14, "brand", SECOND))
    c.add(text((T(3.5) + T(4)) / 2, AY - 20, "−30 min", 11, "middle", "brand-fg", weight=600))
    c.add(arrow(T(4) + 6, AY - 14, T(5) - 2, AY - 14, "brand", SECOND))
    c.add(text((T(4) + T(5)) / 2, AY - 20, "+60 min", 11, "middle", "brand-fg", weight=600))
    # axis
    c.add(line(L, AY, R, AY, "fg-muted", SECOND, cap="butt"))
    for k in range(9):
        h = 2.5 + k * 0.5
        c.add(line(T(h), AY, T(h), AY + 5, "fg-muted", THIN))
        if k % 2 == 1:
            c.add(num(T(h), AY + 20, f"{int(h):02d}00", 12, "middle", "fg-muted"))
    c.add(text(R, AY + 52, "UTC", 11, "end", "fg-faint"))
    # base row
    y = top + 4
    c.add(text(L - 10, y + 20, "base", 13, "end", "fg", weight=600))
    c.add(rect(T(2.5), y, T(6.5) - T(2.5), 30, "ok-soft", "ok", THIN, rx=4))
    c.add(num(T(2.75), y + 20, "15012KT 9999 SCT030", 12, "start", "ok-fg", weight=600))
    # TEMPO row
    y = top + 62
    c.add(text(L - 10, y + 20, "TEMPO", 13, "end", "bad", weight=700))
    c.add(rect(T(3), y, T(6) - T(3), 30, "bad-soft", "bad", SECOND, rx=4))
    c.add(num(T(3) + 8, y + 20, "0300/0600 4000 SHRA BKN012", 12, "start", "bad", weight=600))
    # the test
    ty = 318
    c.add(text(20, ty, "Alternate minima: a group in the window fails if it has", 13, "start", "fg", weight=700))
    rows = [("more than SCT below 1,500 ft", "SCT030: pass", "BKN012: fail"),
            ("visibility under 8 km", "9999: pass", "4000 m: fail")]
    c.add(text(330, ty + 26, "base", 12, "middle", "fg-muted", weight=600))
    c.add(text(470, ty + 26, "TEMPO", 12, "middle", "fg-muted", weight=600))
    for i, (crit, base, tempo) in enumerate(rows):
        yy = ty + 48 + i * 24
        c.add(text(30, yy, "• " + crit, 12, "start", "fg"))
        c.add(text(330, yy, base, 12, "middle", "ok-fg", weight=600))
        c.add(text(470, yy, tempo, 12, "middle", "bad", weight=700))
    c.add(rect(20, ty + 88, 600, 26, "warn-soft", None, rx=6))
    c.add(text(320, ty + 106, "TEMPO in the window: hold 60 min (28 L) or nominate Dongara (15 L); reserve on top.", 12, "middle", "warn-fg", weight=600))
    return c


@chart
def fuel_plan_ladder() -> Canvas:
    c = Canvas("What makes up the fuel required?",
               "The note's fuel plan, stacked against 110 L usable. Trip 1 h 45 min at 36 L/h is 63 L; 30 minutes holding for an INTER is 18 L; "
               "the 30 minute fixed reserve is 18 L; required 99 L, leaving an 11 L margin, about 18 minutes, before the taxi allowance. Had the "
               "forecast been a TEMPO, holding would be 36 L and the total 117 L, 7 L more than the tanks hold.", height=330, prefix="fpl")
    c.add(text(20, 28, "Fuel required, layer by layer, against the tanks", 16, "start", "fg", weight=700))
    c.add(text(20, 46, "trip 1 h 45 min at 36 L/h; holding and reserve at the same flow", 12, "start", "fg-muted"))
    L, R = 130, 560
    F = lambda l: L + l / 125 * (R - L)
    rows = [(92, "INTER plan", [(63, "trip 63", "brand"), (18, "hold 18", "warn"), (18, "res 18", "ok")]),
            (196, "TEMPO plan", [(63, "trip 63", "brand"), (36, "hold 36", "warn"), (18, "", "ok")])]
    for y, name, segs in rows:
        c.add(text(L - 12, y + 24, name, 13, "end", "fg", weight=700))
        a = 0
        for v, lab, tone in segs:
            c.add(rect(F(a), y, F(a + v) - F(a), 36, f"{tone}-soft", tone, SECOND))
            if lab:
                c.add(num((F(a) + F(a + v)) / 2, y + 23, lab, 12, "middle", f"{tone}-fg", weight=600))
            a += v
    # INTER margin
    c.add(rect(F(99), 92, F(110) - F(99), 36, "surface-2", "fg-muted", THIN, dash=DASH))
    c.add(path(f"M{F(0)} 136 L{F(0)} 142 L{F(99)} 142 L{F(99)} 136", "fg-muted", None, THIN))
    c.add(num(F(49.5), 158, "required 99 L", 12, "middle", "fg", weight=700))
    c.add(line(F(104.5), 132, F(104.5), 150, "fg-faint", THIN))
    c.add(text(F(110) - 8, 164, "margin 11 L", 12, "end", "fg", weight=600))
    c.add(text(F(110) - 8, 178, "≈ 18 min, less taxi", 11, "end", "fg-muted"))
    # TEMPO excess
    c.add(line(F(108), 232, F(104), 246, "fg-faint", THIN))
    c.add(num(F(104) - 4, 254, "res 18", 12, "end", "ok-fg", weight=600))
    c.add(text(F(117) + 8, 212, "117 L", 13, "start", "bad", weight=700))
    c.add(text(F(117) + 8, 228, "7 L over", 12, "start", "bad", weight=600))
    # tanks
    c.add(rect(F(110), 74, F(125) - F(110), 180, "bad", None, fill_opacity=0.08))
    c.add(line(F(110), 70, F(110), 258, "fg", MAIN))
    c.add(text(F(110), 64, "110 L usable", 13, "middle", "fg", weight=700))
    for v in (0, 25, 50, 75, 100):
        c.add(num(F(v), 274, str(v), 11, "middle", "fg-muted"))
    c.add(text((L + R) / 2, 292, "fuel (L)", 12, "middle", "fg-muted", weight=600))
    c.add(text(20, 318, "The TEMPO plan does not fit: plan an alternate in range, a fuel stop, or arrive outside the TEMPO.", 12, "start", "fg-muted"))
    return c


@chart
def alternate_decision_flow() -> Canvas:
    c = Canvas("Holding fuel or an alternate?",
               "Decision flow from the note. Lay every TAF group against the window, 30 minutes before to 60 minutes after the ETA. If nothing in "
               "the window is below the alternate minima, carry trip fuel and the fixed reserve. If something is, ask how long it lasts: an INTER "
               "requires 30 minutes of holding fuel or an alternate; a TEMPO requires 60 minutes of holding fuel or an alternate; a permanent "
               "change (FM, BECMG or the base conditions) requires an alternate, because waiting does not help. A PROB group is treated as the "
               "group it qualifies. The fixed reserve is always on top.", height=426, prefix="adf")
    def box(x, y, w, h, lines, fill="surface-2", stroke="line-strong", colour="fg", bold_first=True):
        c.add(rect(x, y, w, h, fill, stroke, SECOND, rx=8))
        n = len(lines)
        for i, s in enumerate(lines):
            c.add(text(x + w / 2, y + h / 2 + (i - (n - 1) / 2) * 17 + 5, s, 13 if i == 0 else 12, "middle", colour,
                       weight=700 if (i == 0 and bold_first) else None))
    box(170, 16, 300, 54, ["Lay every TAF group against the window", "ETA −30 min to +60 min"], bold_first=False)
    c.add(arrow(320, 70, 320, 94, "fg-muted", SECOND))
    box(140, 96, 360, 62, ["Anything in the window below the minima?", "more than SCT below 1,500 ft, visibility under 8 km,", "or fog, dust, thunderstorms"], "brand-soft", "brand", "brand-fg")
    # no
    c.add(arrow(500, 127, 532, 127, "ok", SECOND))
    c.add(text(516, 119, "no", 12, "middle", "ok-fg", weight=700))
    box(534, 100, 96, 54, ["Nothing", "extra"], "ok-soft", "ok", "ok-fg")
    # yes
    c.add(arrow(320, 158, 320, 188, "bad", SECOND))
    c.add(text(330, 178, "yes: how long does it last?", 12, "start", "bad", weight=700))
    cols = [(20, "INTER", "spells under 30 min", ["30 min holding", "or an alternate"], "warn"),
            (230, "TEMPO", "spells up to 60 min", ["60 min holding", "or an alternate"], "warn"),
            (440, "Permanent", "FM, BECMG or base", ["alternate only:", "waiting will not help"], "bad")]
    c.add(line(110, 196, 530, 196, "fg-muted", SECOND))
    for x, head, sub, out, tone in cols:
        cx = x + 90
        c.add(arrow(cx, 196, cx, 214, "fg-muted", SECOND))
        box(x, 216, 180, 54, [head, sub], "surface-2", "line-strong")
        c.add(arrow(cx, 270, cx, 292, tone, SECOND))
        box(x, 294, 180, 54, out, f"{tone}-soft", tone, f"{tone}-fg" if tone != "bad" else "bad")
    c.add(text(320, 366, "PROB30 / PROB40: treat it as the group it qualifies", 12, "middle", "fg-muted"))
    c.add(text(320, 382, "(a PROB30 TEMPO of fog: TEMPO holding or an alternate)", 12, "middle", "fg-muted"))
    c.add(rect(120, 392, 400, 26, "ok-soft", None, rx=6))
    c.add(text(320, 410, "The 30 min fixed reserve goes on top of every option.", 12, "middle", "ok-fg", weight=600))
    return c


# ---------------------------------------------------------------- 2.1 loading
@chart
def weight_ladder() -> Canvas:
    c = Canvas("The weight ladder and the limit for each rung",
               "Five stacked columns, schematic heights. Empty weight; zero fuel weight adds the occupants and baggage and is checked against the "
               "maximum zero fuel weight; take-off weight adds the fuel and is checked against the maximum take-off weight; ramp weight adds the "
               "taxi and run-up fuel and is checked against any maximum ramp weight; landing weight is the take-off weight less the fuel burned "
               "and is checked against the maximum landing weight. ECHO's limits from the note: MZFW 2,630 kg, MTOW 2,950 kg, MLW 2,725 kg, so "
               "a full ECHO at MTOW must burn 225 kg before it may land.", height=424, prefix="wld")
    c.add(text(20, 28, "Each rung of the ladder has its own limit", 16, "start", "fg", weight=700))
    c.add(text(20, 46, "schematic heights; limit lines are ECHO's from the note", 12, "start", "fg-muted"))
    base = 340
    Y = lambda kg: base - (kg - 1500) * 0.17    # px per kg above a 1,500 kg cut
    empty, payload, fuel, taxi, burn = 2000, 600, 350, 20, 300
    cols = [("Empty", [(empty, "surface-2", "fg-muted", "empty")]),
            ("Zero fuel", [(empty, "surface-2", "fg-muted", "empty"), (payload, "info-soft", "info", "people, bags")]),
            ("Take-off", [(empty, "surface-2", "fg-muted", "empty"), (payload, "info-soft", "info", "people, bags"), (fuel, "brand-soft", "brand", "fuel")]),
            ("Ramp", [(empty, "surface-2", "fg-muted", "empty"), (payload, "info-soft", "info", "people, bags"), (fuel, "brand-soft", "brand", "fuel"), (taxi, "warn", "warn", "")]),
            ("Landing", [(empty, "surface-2", "fg-muted", "empty"), (payload, "info-soft", "info", "people, bags"), (fuel - burn, "brand-soft", "brand", "")])]
    X0, DX, W = 34, 96, 86
    # limit lines first, so the columns sit in front of them
    limits = [(2630, "MZFW 2,630", "info"), (2725, "MLW 2,725", "ok"), (2950, "MTOW 2,950", "bad")]
    for kg, lab, tone in limits:
        c.add(line(30, Y(kg), 510, Y(kg), tone, SECOND, DASH))
        c.add(text(516, Y(kg) + 4, lab, 12, "start", tone if tone == "bad" else f"{tone}-fg", weight=700, cls="num"))
    for i, (name, segs) in enumerate(cols):
        x = X0 + i * DX
        lo = 1500
        for kg, fill, stroke, lab in segs:
            hi = kg if lo == 1500 else lo + kg
            c.add(rect(x, Y(hi), W, Y(lo) - Y(hi), fill, stroke, SECOND))
            if lab and Y(lo) - Y(hi) > 18:
                c.add(text(x + W / 2, (Y(lo) + Y(hi)) / 2 + 4, lab, 11, "middle", "fg" if stroke == "fg-muted" else f"{stroke}-fg", weight=600))
            lo = hi
        c.add(text(x + W / 2, base + 20, name, 13, "middle", "fg", weight=700))
        c.add(text(x + W / 2, base + 36, "weight", 11, "middle", "fg-muted"))
    c.add(line(30, base, 510, base, "fg-muted", SECOND, cap="butt"))
    # annotations
    c.add(text(X0 + 3 * DX + W / 2, Y(empty + payload + fuel + taxi) - 8, "+ taxi fuel", 11, "middle", "warn-fg", weight=600))
    c.add(arrow(X0 + 4 * DX + W / 2, Y(empty + payload + fuel) - 4, X0 + 4 * DX + W / 2, Y(empty + payload + fuel - burn) - 6, "brand", SECOND))
    c.add(text(X0 + 4 * DX + W / 2, Y(empty + payload + fuel) - 10, "fuel burned", 11, "middle", "brand-fg", weight=600))
    c.add(text(20, 396, "ZFW against MZFW, take-off against MTOW, landing against MLW.", 12, "start", "fg-muted"))
    c.add(text(20, 412, "A full ECHO at MTOW must burn 225 kg of fuel before it may land.", 12, "start", "fg-muted"))
    return c


@chart
def floor_loading_board() -> Canvas:
    c = Canvas("Spreading a load to meet the floor loading limit",
               "The note's worked example. A 30 kg battery standing on its own 0.2 m by 0.15 m base presses on 0.03 square metres: 1,000 kg per "
               "square metre, more than twice the 450 kg per square metre limit. Stood on a 0.4 m by 0.3 m board, the same 30 kg is spread over "
               "0.12 square metres: 250 kg per square metre, within the limit.", height=400, prefix="flb")
    c.add(text(20, 28, "Same 30 kg, different footprint", 16, "start", "fg", weight=700))
    c.add(text(20, 46, "floor loading = weight ÷ contact area; limit 450 kg/m²", 12, "start", "fg-muted"))
    S = 300  # px per metre for the footprints
    panels = [(170, "On its own base", 0.2, 0.15, 1000, "bad", "1,000 kg/m²", "more than twice the limit"),
              (470, "Stood on a board", 0.4, 0.3, 250, "ok", "250 kg/m²", "within the limit")]
    for cx, title, w, d, load, tone, val, verdict in panels:
        c.add(text(cx, 80, title, 14, "middle", "fg", weight=700))
        # side view on the floor
        fy = 164
        c.add(line(cx - 120, fy, cx + 120, fy, "fg-muted", MAIN))
        for k in range(12):
            c.add(line(cx - 116 + k * 20, fy + 2, cx - 126 + k * 20, fy + 12, "line-strong", THIN))
        if w > 0.3:
            c.add(rect(cx - w * S / 2, fy - 8, w * S, 8, "warn-soft", "warn", SECOND))
            bt = fy - 8
        else:
            bt = fy
        c.add(rect(cx - 30, bt - 50, 60, 50, "surface-2", "fg", MAIN, rx=3))
        c.add(rect(cx - 20, bt - 56, 10, 6, "fg", None))
        c.add(rect(cx + 10, bt - 56, 10, 6, "fg", None))
        c.add(num(cx, bt - 20, "30 kg", 13, "middle", "fg", weight=700))
        for k in (-1, 0, 1):
            spread = (w * S / 2 - 6) * k
            c.add(arrow(cx + spread * 0.4, fy + 10, cx + spread, fy + 32, tone, SECOND))
        # plan-view footprint
        py_ = 236
        c.add(num(cx, py_ - 8, f"footprint {fmt(w)} × {fmt(d)} m", 12, "middle", f"{tone}-fg", weight=600))
        c.add(rect(cx - w * S / 2, py_, w * S, d * S, f"{tone}-soft", tone, SECOND))
        c.add(num(cx, 344, f"{fmt(round(w * d, 2))} m²  →  {val}", 13, "middle", tone if tone == "bad" else "ok-fg", weight=700))
        c.add(text(cx, 362, verdict, 12, "middle", tone if tone == "bad" else "ok-fg"))
    c.add(text(320, 392, "Weigh the board too: it goes on the load sheet.", 12, "middle", "fg-muted"))
    return c
