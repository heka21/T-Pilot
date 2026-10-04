"""Generated non-chart figures (geometry that is easier to compute than to draw by hand). Registered in
tools.diagrams.charts.CHARTS like the charts, so `python -m tools.diagrams.build` writes them too."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, arc_path, arrow, badge, callout, circle, ellipse, fmt, group, line, multiline, num, path,
                                plane_rear, plane_side, plane_top, polygon, polyline, rect, runway, smooth_path, text)


@chart
def four_stroke_cycle() -> Canvas:
    """Animated single cylinder: induction, compression, power, exhaust over two crankshaft revolutions."""
    c = Canvas("The four-stroke cycle", "A piston engine cylinder animated through induction (intake valve open, piston down), compression (both valves closed, "
               "piston up), power (spark, burning gas pushes the piston down) and exhaust (exhaust valve open, piston up). One cycle takes two "
               "crankshaft revolutions.", height=430, prefix="fsc")
    CX, CY, R, L = 236, 352, 45, 130           # crank centre, crank radius, conrod length
    BORE_L, BORE_R, HEAD_Y, WALL_B = 176, 296, 130, 292
    PERIOD = 8

    def pin_y(theta: float) -> float:
        t = math.radians(theta)
        return CY - (R * math.cos(t) + math.sqrt(L * L - (R * math.sin(t)) ** 2))

    def rod_angle(theta: float) -> float:
        return -math.degrees(math.asin(R * math.sin(math.radians(theta)) / L))

    tdc = pin_y(0)
    steps = 48
    piston_kf = "".join(f"{100 * i / steps:.2f}%{{transform:translateY({pin_y(720 * i / steps) - tdc:.1f}px)}}" for i in range(steps + 1))
    rod_kf = "".join(f"{100 * i / steps:.2f}%{{transform:translate(0,{pin_y(720 * i / steps) - tdc:.1f}px) rotate({rod_angle(720 * i / steps):.2f}deg)}}" for i in range(steps + 1))
    c.style(f"""
.fsc-piston{{animation:fsc-piston {PERIOD}s linear infinite}}
@keyframes fsc-piston{{{piston_kf}}}
.fsc-rod{{animation:fsc-rod {PERIOD}s linear infinite}}
@keyframes fsc-rod{{{rod_kf}}}
.fsc-crank{{animation:fsc-crank {PERIOD}s linear infinite}}
@keyframes fsc-crank{{to{{transform:rotate(720deg)}}}}
.fsc-intake{{animation:fsc-intake {PERIOD}s ease-in-out infinite}}
@keyframes fsc-intake{{0%,22%{{transform:translateY(12px)}}26%,100%{{transform:translateY(0)}}}}
.fsc-exhaust{{animation:fsc-exhaust {PERIOD}s ease-in-out infinite}}
@keyframes fsc-exhaust{{0%,72%{{transform:translateY(0)}}76%,100%{{transform:translateY(12px)}}}}
.fsc-spark{{animation:fsc-spark {PERIOD}s linear infinite}}
@keyframes fsc-spark{{0%,47%{{opacity:0}}48%,53%{{opacity:1}}55%,100%{{opacity:0}}}}
.fsc-gas{{animation:fsc-gas {PERIOD}s linear infinite}}
@keyframes fsc-gas{{0%,24%{{fill:var(--color-sky-soft)}}26%,48%{{fill:var(--color-info-soft)}}50%,74%{{fill:var(--color-warn-soft)}}76%,100%{{fill:var(--color-surface-2)}}}}
.fsc-flame{{animation:fsc-flame {PERIOD}s linear infinite}}
@keyframes fsc-flame{{0%,48%{{opacity:0}}50%{{opacity:.9}}74%{{opacity:.35}}76%,100%{{opacity:0}}}}
.fsc-in-arrow{{animation:fsc-in-arrow {PERIOD}s linear infinite}}
@keyframes fsc-in-arrow{{0%,24%{{opacity:1}}26%,100%{{opacity:0}}}}
.fsc-out-arrow{{animation:fsc-out-arrow {PERIOD}s linear infinite}}
@keyframes fsc-out-arrow{{0%,74%{{opacity:0}}76%,100%{{opacity:1}}}}
.fsc-p1{{animation:fsc-p1 {PERIOD}s linear infinite}}@keyframes fsc-p1{{0%,24.9%{{opacity:1}}25%,100%{{opacity:0}}}}
.fsc-p2{{animation:fsc-p2 {PERIOD}s linear infinite}}@keyframes fsc-p2{{0%,24.9%{{opacity:0}}25%,49.9%{{opacity:1}}50%,100%{{opacity:0}}}}
.fsc-p3{{animation:fsc-p3 {PERIOD}s linear infinite}}@keyframes fsc-p3{{0%,49.9%{{opacity:0}}50%,74.9%{{opacity:1}}75%,100%{{opacity:0}}}}
.fsc-p4{{animation:fsc-p4 {PERIOD}s linear infinite}}@keyframes fsc-p4{{0%,74.9%{{opacity:0}}75%,100%{{opacity:1}}}}
""")
    c.add_defs(f'<clipPath id="bore"><rect x="{BORE_L}" y="{HEAD_Y}" width="{BORE_R - BORE_L}" height="{WALL_B - HEAD_Y}"/></clipPath>')
    # heading
    c.add(text(20, 34, "One cycle = four strokes = two crankshaft revolutions", 16, "start", "fg", weight=700))
    c.add(text(20, 54, "Suck · Squeeze · Bang · Blow", 13, "start", "fg-muted"))
    # ports (pipes) into the head
    PL, PR = BORE_L - 72, BORE_R + 72
    c.add(path(f"M{PL} {HEAD_Y - 40} L{BORE_L + 16} {HEAD_Y - 40} L{BORE_L + 16} {HEAD_Y}", "fg-muted", None, SECOND))
    c.add(path(f"M{PL} {HEAD_Y - 12} L{BORE_L + 40} {HEAD_Y - 12} L{BORE_L + 40} {HEAD_Y}", "fg-muted", None, SECOND))
    c.add(path(f"M{PR} {HEAD_Y - 40} L{BORE_R - 16} {HEAD_Y - 40} L{BORE_R - 16} {HEAD_Y}", "fg-muted", None, SECOND))
    c.add(path(f"M{PR} {HEAD_Y - 12} L{BORE_R - 40} {HEAD_Y - 12} L{BORE_R - 40} {HEAD_Y}", "fg-muted", None, SECOND))
    c.add(arrow(PL + 4, HEAD_Y - 26, BORE_L + 6, HEAD_Y - 26, "sky-fg", MAIN, cls="fsc-in-arrow"))
    c.add(text(PL, HEAD_Y + 8, "mixture in", 11, "start", "sky-fg", cls="fsc-in-arrow"))
    c.add(arrow(BORE_R - 6, HEAD_Y - 26, PR - 4, HEAD_Y - 26, "fg-muted", MAIN, cls="fsc-out-arrow"))
    c.add(text(BORE_R + 14, HEAD_Y + 8, "exhaust out", 11, "start", "fg-muted", cls="fsc-out-arrow"))
    # crank web and conrod (behind the piston)
    crank = group(circle(0, 0, 52, "surface-2", "fg", MAIN), path(f"M0 0 L0 -{R}", "fg", None, 8), circle(0, -R, 7, "fg", None), circle(0, 0, 6, "fg", None), cls="fsc-crank")
    c.add(group(crank, transform=f"translate({CX} {CY})"))
    # inside the bore (clipped): the gas column moves with the piston so it always fills head-to-crown; the crankcase below is open
    gas = rect(BORE_L, tdc - 22 - 300, BORE_R - BORE_L, 300, "sky-soft", None, cls="fsc-gas")
    piston = group(
        gas,
        rect(BORE_L + 3, tdc - 22, BORE_R - BORE_L - 6, 36, "surface", "fg", MAIN, rx=2),
        line(BORE_L + 3, tdc - 14, BORE_R - 3, tdc - 14, "fg", THIN), line(BORE_L + 3, tdc - 8, BORE_R - 3, tdc - 8, "fg", THIN),
        circle(CX, tdc, 5, "fg-muted", "fg", 1.5),
        cls="fsc-piston")
    flame = path(f"M{BORE_L + 10} {HEAD_Y + 2} Q{CX - 20} {HEAD_Y + 30} {CX} {HEAD_Y + 12} Q{CX + 22} {HEAD_Y + 32} {BORE_R - 10} {HEAD_Y + 2} Z", None, "warn", 0, cls="fsc-flame", opacity=0)
    rod = group(group(line(0, 0, 0, L, "fg", 7), circle(0, 0, 6, "fg-muted", "fg", 1.5), cls="fsc-rod"), transform=f"translate({CX} {tdc:.1f})")
    c.add(rect(BORE_L, HEAD_Y, BORE_R - BORE_L, WALL_B - HEAD_Y, "surface-2", None))
    c.add(f'<g clip-path="url(#bore)">{piston}{flame}</g>')
    c.add(rod)
    # cylinder walls and head drawn over everything
    c.add(rect(BORE_L - 8, HEAD_Y, 8, WALL_B - HEAD_Y, "fg-muted", None), rect(BORE_R, HEAD_Y, 8, WALL_B - HEAD_Y, "fg-muted", None))
    c.add(path(f"M{BORE_L - 8} {HEAD_Y} L{BORE_L - 8} {HEAD_Y - 14} L{BORE_L + 6} {HEAD_Y - 14} L{BORE_L + 6} {HEAD_Y} Z", None, "fg-muted"))
    c.add(path(f"M{BORE_L + 50} {HEAD_Y} L{BORE_L + 50} {HEAD_Y - 14} L{BORE_R - 50} {HEAD_Y - 14} L{BORE_R - 50} {HEAD_Y} Z", None, "fg-muted"))
    c.add(path(f"M{BORE_R - 6} {HEAD_Y} L{BORE_R - 6} {HEAD_Y - 14} L{BORE_R + 8} {HEAD_Y - 14} L{BORE_R + 8} {HEAD_Y} Z", None, "fg-muted"))
    # valves: stem + head, translated down when open
    for x, cls in ((BORE_L + 28, "fsc-intake"), (BORE_R - 28, "fsc-exhaust")):
        c.add(group(line(x, HEAD_Y - 50, x, HEAD_Y - 2, "fg", 4), path(f"M{x - 12} {HEAD_Y - 4} L{x + 12} {HEAD_Y - 4} L{x + 8} {HEAD_Y + 4} L{x - 8} {HEAD_Y + 4} Z", "fg", "surface", 1.5), cls=cls))
    c.add(text(BORE_L + 20, HEAD_Y - 58, "intake valve", 11, "end", "fg-muted"), text(BORE_R - 20, HEAD_Y - 58, "exhaust valve", 11, "start", "fg-muted"))
    # spark plug and spark
    c.add(rect(CX - 6, HEAD_Y - 44, 12, 30, "surface", "fg", 1.5, rx=2), line(CX, HEAD_Y - 14, CX, HEAD_Y + 4, "fg", 2))
    c.add(group(path(f"M{CX} {HEAD_Y + 6} l5 10 l11 -2 l-8 8 l6 10 l-10 -6 l-9 7 l2 -11 l-10 -5 l11 -2 z", "warn", "warn-soft", 1.5), cls="fsc-spark", opacity=0))
    c.add(text(CX + 10, HEAD_Y - 72, "spark plug", 11, "start", "fg-muted"))
    c.add(line(CX + 6, HEAD_Y - 68, CX, HEAD_Y - 48, "fg-faint", THIN))
    c.add(text(CX, CY + 72, "crankshaft", 11, "middle", "fg-muted"))
    # the four strokes on the right, the active one highlighted
    strokes = [("1 · Induction", "Intake valve open, piston moves down,", "fuel–air mixture is drawn in", "sky"),
               ("2 · Compression", "Both valves closed, piston moves up,", "mixture squeezed into the chamber", "info"),
               ("3 · Power", "Spark near TDC; the burning gas", "expands and pushes the piston down", "warn"),
               ("4 · Exhaust", "Exhaust valve open, piston moves up,", "burnt gas pushed out", "fg")]
    BX = 400
    for i, (title, l1, l2, colour) in enumerate(strokes):
        y = 96 + i * 66
        c.add(rect(BX, y, 230, 58, f"{colour}-soft" if colour != "fg" else "surface-2", None, rx=8, cls=f"fsc-p{i + 1}", opacity=1 if i == 0 else 0))
        c.add(rect(BX, y, 230, 58, None, "line", THIN, rx=8))
        c.add(text(BX + 12, y + 20, title, 13, "start", "fg", weight=700))
        c.add(text(BX + 12, y + 36, l1, 11, "start", "fg-muted"))
        c.add(text(BX + 12, y + 50, l2, 11, "start", "fg-muted"))
    c.add(multiline(BX, 380, ["Each stroke is half a crankshaft turn.", "Only the power stroke does work; the flywheel", "and the other cylinders carry the engine", "through the other three."], 11, "start", "fg-faint", leading=1.35))
    return c


@chart
def wake_turbulence_vortices() -> Canvas:
    """Animated rear view: counter-rotating wing-tip vortices behind a heavy aeroplane, sinking, rolling a light aircraft."""
    c = Canvas("Wake turbulence: wing-tip vortices", "Seen from behind, a heavy aeroplane trails two counter-rotating vortices from its wing tips, the left one "
               "rotating clockwise and the right one anticlockwise, with downwash between them and upwash outside. They sink at about "
               "500 feet per minute and drift with the wind. A light aeroplane entering a vortex is rolled, often faster than its ailerons can counter.",
               height=420, prefix="wtv")
    c.style("""
.wtv-cw{animation:wtv-cw 3s linear infinite}
@keyframes wtv-cw{to{transform:rotate(360deg)}}
.wtv-ccw{animation:wtv-ccw 3s linear infinite}
@keyframes wtv-ccw{to{transform:rotate(-360deg)}}
.wtv-roll{animation:wtv-roll 6s ease-in-out infinite}
@keyframes wtv-roll{0%,15%{transform:rotate(0deg)}55%,70%{transform:rotate(-42deg)}100%{transform:rotate(0deg)}}
.wtv-flow{stroke-dasharray:6 8;animation:wtv-flow 1.2s linear infinite}
@keyframes wtv-flow{to{stroke-dashoffset:-28}}
.wtv-sink{animation:wtv-sink 6s linear infinite}
@keyframes wtv-sink{0%{transform:translateY(0);opacity:0}15%{opacity:.5}85%{opacity:.5}100%{transform:translateY(90px);opacity:0}}
""")
    HX, HY = 320, 150
    # heavy aeroplane, rear view, wide span (scale 3 of the 100-unit silhouette)
    c.add(plane_rear(HX, HY, 3.0, 0, "fg", "surface"))
    c.add(text(HX, 30, "Heavy aeroplane ahead, seen from behind", 14, "middle", "fg", weight=600))
    c.add(text(HX, 48, "strongest wake when heavy, slow and clean (gear and flaps up)", 12, "middle", "fg-muted"))
    # vortex cores at the wing tips
    def vortex(x: float, y: float, cls: str) -> str:
        arcs = "".join(path(arc_path(0, 0, r, a0, a0 + 250), "brand", None, MAIN if r > 20 else SECOND, arrow_end=True) for r, a0 in ((16, 0), (30, 120), (44, 240)))
        return group(group(arcs, cls=cls), transform=f"translate({x} {y})")
    LX, RX, VY = HX - 150, HX + 150, HY + 8
    # faint sinking copies suggest the vortices moving down and spreading
    c.add(group(vortex(LX - 14, VY, "wtv-cw"), vortex(RX + 14, VY, "wtv-ccw"), cls="wtv-sink", opacity=0))
    c.add(vortex(LX, VY, "wtv-cw"), vortex(RX, VY, "wtv-ccw"))
    c.add(text(LX, VY + 86, "left vortex: clockwise", 12, "middle", "brand", weight=600))
    c.add(text(RX, VY + 86, "right vortex: anticlockwise", 12, "middle", "brand", weight=600))
    # downwash between the cores, upwash outside
    for x in (HX - 60, HX, HX + 60):
        c.add(line(x, VY - 6, x, VY + 66, "sky-fg", SECOND, arrow_end=True, cls="wtv-flow"))
    c.add(text(HX, VY + 106, "downwash between the vortices", 12, "middle", "sky-fg"))
    c.add(text(HX, VY + 124, "the pair sinks at a few hundred ft/min and levels off about 500 to 1,000 ft below the flight path", 11, "middle", "fg-muted"))
    for x in (LX - 66, RX + 66):
        c.add(line(x, VY + 66, x, VY - 6, "sky-fg", SECOND, arrow_end=True, cls="wtv-flow"))
    c.add(text(LX - 66, VY - 16, "upwash", 11, "middle", "sky-fg"), text(RX + 66, VY - 16, "upwash", 11, "middle", "sky-fg"))
    # drift with the wind
    c.add(arrow(22, 300, 92, 300, "fg-muted", SECOND, dash=DASH))
    c.add(multiline(22, 318, ["vortices drift", "with the wind"], 11, "start", "fg-muted"))
    # light aeroplane entering the left vortex, rolled
    LAX, LAY = LX + 10, 336
    c.add(group(group(plane_rear(0, 0, 1.1, 0, "bad", "surface"), cls="wtv-roll"), transform=f"translate({LAX} {LAY})"))
    c.add(path(arc_path(LAX, LAY, 72, 200, 160), "bad", None, SECOND, dash=DASH, arrow_end=True))
    c.add(multiline(LAX + 90, LAY - 10, ["Light aeroplane entering the vortex:", "rolled faster than full aileron can hold,", "worst when its heading matches the heavy's"], 12, "start", "bad"))
    c.add(text(320, 398, "Avoid: stay above and upwind of the heavy aeroplane's flight path;", 11, "middle", "fg-muted"))
    c.add(text(320, 412, "land beyond its touchdown point, lift off before its rotation point.", 11, "middle", "fg-muted"))
    return c


@chart
def circuit_pattern() -> Canvas:
    """Plan view of a standard left-hand circuit with the legs, heights and the dead side; an aeroplane flies it (CSS motion path)."""
    c = Canvas("The standard left-hand circuit", "Plan view of a left-hand circuit on runway 24: upwind leg climbing straight ahead, left turn onto crosswind at or "
               "above 500 feet, downwind at 1,000 feet above aerodrome level parallel to the runway, base leg descending, final onto the runway. "
               "The dead side is the right-hand side of the runway, away from the circuit.", height=440, prefix="cp")
    RY = 262                                     # runway centreline
    path_d = ("M200 262 L500 262 Q540 262 540 222 L540 150 Q540 110 500 110 L140 110 Q100 110 100 150 L100 222 Q100 262 140 262 L200 262")
    c.style(f"""
.cp-plane{{offset-path:path("{path_d}");offset-rotate:auto;animation:cp-fly 18s linear infinite}}
@keyframes cp-fly{{to{{offset-distance:100%}}}}
.cp-plane-static{{display:none}}
@supports not (offset-path: path("M0 0")){{.cp-plane{{display:none}}.cp-plane-static{{display:inline}}}}
""")
    # circuit side (brand soft) and dead side (surface-2) bands
    c.add(rect(20, 62, 600, 160, "brand-soft", None, rx=10, fill_opacity=0.35))
    c.add(rect(20, 300, 600, 86, "surface-2", None, rx=10))
    c.add(text(40, 326, "Dead side", 14, "start", "fg-muted", weight=700))
    c.add(text(40, 344, "the other side of the runway for a left-hand circuit: kept clear of circuit traffic;", 11, "start", "fg-muted"))
    c.add(text(40, 358, "aircraft joining from overhead descend here to circuit height, then cross to join crosswind", 11, "start", "fg-muted"))
    c.add(text(40, 84, "Circuit side", 14, "start", "brand-fg", weight=700))
    c.add(text(40, 100, "all turns to the left, 1,000 ft above aerodrome level", 11, "start", "brand-fg"))
    # runway, take-off to the right (runway 24)
    c.add(runway(300, RY, 220, 26, None))
    c.add(num(230, RY + 5, "24", 12, "middle", "paint", weight=700))
    c.add(num(370, RY + 5, "06", 12, "middle", "paint", weight=700))
    # the circuit path
    c.add(path(path_d, "brand", None, MAIN, dash="8 6"))
    # leg labels
    c.add(badge(430, RY - 22, "Upwind", "brand"))
    c.add(text(430, RY - 40, "climb straight ahead, no turn below 500 ft", 11, "middle", "fg-muted"))
    c.add(badge(588, 176, "Crosswind", "brand"))
    c.add(multiline(588, 196, ["90° left, at or", "above 500 ft"], 11, "middle", "fg-muted"))
    c.add(badge(420, 110, "Downwind", "brand"))
    c.add(text(420, 132, "parallel to the runway at 1,000 ft: downwind call, pre-landing checks", 11, "middle", "fg-muted"))
    c.add(badge(54, 176, "Base", "brand"))
    c.add(multiline(54, 196, ["descending,", "turn onto final"], 11, "middle", "fg-muted"))
    c.add(badge(170, RY - 22, "Final", "brand"))
    c.add(text(170, RY - 40, "lined up, descending to land", 11, "middle", "fg-muted"))
    # wind: runway 24 means landing/taking off into a wind from 240, which blows from the right of the picture
    c.add(arrow(600, 30, 520, 30, "sky-fg", MAIN))
    c.add(text(510, 34, "wind from 240°", 12, "end", "sky-fg", weight=600))
    c.add(text(510, 50, "take off and land into it", 11, "end", "sky-fg"))
    # north arrow: heading 240 points right, so north points down-left
    c.add(group(arrow(0, 0, -16, 28, "fg-muted", SECOND), text(-24, 40, "N", 12, "middle", "fg-muted", weight=700), transform="translate(606 392)"))
    # the aeroplane on the path (animated where motion paths are supported, static on the downwind leg otherwise)
    c.add(group(plane_top(0, 0, 0.32, 90, "fg", "surface"), cls="cp-plane"))
    c.add(group(plane_top(300, 110, 0.32, 270, "fg", "surface"), cls="cp-plane-static"))
    c.add(text(40, 418, "Legs are named for the aeroplane's direction relative to the wind: upwind into it, downwind with it.", 11, "start", "fg-faint"))
    return c


@chart
def airspace_cross_section() -> Canvas:
    """Side view of a typical slice of Australian airspace: control zones, Class C steps, Class E and A above, Class G below, a restricted area."""
    c = Canvas("A slice of Australian airspace", "Cross-section showing a Class C control zone from the surface at a major airport with Class C steps whose "
               "lower limits rise with distance, a Class D control zone at a regional tower, Class E above the steps, Class A at high level, "
               "Class G non-controlled airspace below the steps, and a restricted area. Not a real location.", height=420, prefix="acs")
    levels = {"SFC": 350, "1500": 302, "2500": 270, "4500": 226, "8500": 160, "FL180": 80}
    TOP = 36
    L, R = 56, 620

    def y(level: str) -> float:
        return levels[level]

    # ground
    c.add(path(f"M{L} 350 Q150 342 250 350 T450 350 T{R} 350 L{R} 372 L{L} 372 Z", None, "surface-2"))
    c.add(line(L, 350, R, 350, "fg-muted", SECOND))
    # Class A on top
    c.add(rect(L, TOP, R - L, y("FL180") - TOP, "info-soft", None))
    c.add(text((L + R) / 2, TOP + 26, "Class A · above FL180 (FL245 in places) · IFR only, VFR not permitted", 12, "middle", "info-fg", weight=600))
    # Class C: CTR from the surface at the major airport, then steps outward
    steps = [(L, 180, "SFC"), (180, 250, "1500"), (250, 350, "1500"), (350, 430, "2500"), (430, 510, "4500")]
    for x0, x1, lvl in steps:
        c.add(rect(x0, y("FL180"), x1 - x0, y(lvl) - y("FL180"), "brand-soft", "brand", THIN))
    c.add(text(118, 120, "Class C", 14, "middle", "brand-fg", weight=700))
    c.add(text(118, 138, "clearance required;", 11, "middle", "brand-fg"))
    c.add(text(118, 152, "ATC separates IFR and VFR", 11, "middle", "brand-fg"))
    c.add(text(118, 322, "control zone (CTR)", 11, "middle", "brand-fg"))
    c.add(text(118, 336, "from the surface", 11, "middle", "brand-fg"))
    for x0, x1, lvl in steps[1:]:
        c.add(num((x0 + x1) / 2, y(lvl) - 6, f"C LL {lvl}", 11, "middle", "brand-fg", weight=600))
    # Class D control zone at the regional tower, under a C LL 1500 step
    c.add(rect(250, y("1500"), 100, y("SFC") - y("1500"), "ok-soft", "ok", THIN))
    c.add(text(300, 320, "Class D", 12, "middle", "ok-fg", weight=700))
    c.add(text(300, 334, "clearance required;", 11, "middle", "ok-fg"))
    c.add(text(300, 346, "tower runs the circuit", 11, "middle", "ok-fg"))
    # Class E above 8500 beyond the steps
    c.add(rect(510, y("FL180"), R - 510, y("8500") - y("FL180"), "sky-soft", "sky-fg", THIN))
    c.add(text(565, 104, "Class E", 13, "middle", "sky-fg", weight=700))
    c.add(text(565, 120, "IFR controlled;", 11, "middle", "sky-fg"))
    c.add(text(565, 134, "VFR needs no clearance", 11, "middle", "sky-fg"))
    c.add(num(565, y("8500") - 6, "E LL 8500", 11, "middle", "sky-fg", weight=600))
    # Class G everywhere below the steps (left as the page surface) with a label and an aeroplane
    c.add(plane_side(470, 250, 0.5))
    c.add(text(470, 276, "3,500 ft here: still Class G", 11, "middle", "fg-muted"))
    c.add(text(440, 306, "Class G · non-controlled", 13, "middle", "fg", weight=700))
    c.add(text(440, 322, "no clearance: lookout, radio,", 11, "middle", "fg-muted"))
    c.add(text(440, 336, "CTAF procedures at aerodromes", 11, "middle", "fg-muted"))
    # restricted area
    c.add_defs('<pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" stroke="var(--color-bad)" stroke-width="1.5"/></pattern>')
    c.add(rect(548, y("2500"), 72, y("SFC") - y("2500"), "url(#hatch)", "bad", THIN))
    c.add(rect(551, 288, 66, 46, "surface", None, rx=4))
    c.add(text(584, 302, "R area", 12, "middle", "bad", weight=700))
    c.add(text(584, 316, "active per", 11, "middle", "bad"))
    c.add(text(584, 329, "ERSA/NOTAM", 11, "middle", "bad"))
    # ground labels
    c.add(text(118, 366, "major airport (C)", 11, "middle", "fg-muted"))
    c.add(text(300, 366, "regional tower (D)", 11, "middle", "fg-muted"))
    c.add(text(470, 366, "country airstrip (G, CTAF)", 11, "middle", "fg-muted"))
    # altitude labels on the left
    for lvl, yy in levels.items():
        c.add(line(L - 6, yy, L, yy, "fg-muted", THIN))
        c.add(num(L - 10, yy + 4, lvl, 11, "end", "fg-faint"))
    c.add(text((L + R) / 2, 398, "Lower limits (LL) are read from the VTC, VNC and ERC-L; the WAC shows no airspace.", 11, "middle", "fg-faint"))
    c.add(text((L + R) / 2, 412, "Heights are schematic, not to scale; this is a typical arrangement, not a real place.", 11, "middle", "fg-faint"))
    return c
