"""PFRA (PPL flight rules and air law) diagrams. Every number, code, signal and document name comes from the notes in
content/notes/PFRA/; where a note hedges ("verify current text", "see the AIP"), the diagram hedges or leaves the number out."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, arrow, badge, circle, fmt, group, line, multiline, num, path,
                                plane_side, plane_top, polygon, polyline, rect, runway, smooth_path, text)

SOFT = {"brand": "brand-soft", "ok": "ok-soft", "warn": "warn-soft", "bad": "bad-soft", "info": "info-soft", "sky": "sky-soft", "fg": "surface-2"}
FG = {"brand": "brand-fg", "ok": "ok-fg", "warn": "warn-fg", "bad": "bad-fg", "info": "info-fg", "sky": "sky-fg", "fg": "fg"}
EDGE = {"brand": "brand", "ok": "ok", "warn": "warn", "bad": "bad", "info": "info", "sky": "sky-fg", "fg": "line-strong"}


def card(x: float, y: float, w: float, h: float, title: str | None, lines: list[str], tone: str = "fg", size: float = 12,
         title_size: float = 14, leading: float = 1.35, pad: float = 12, anchor: str = "start", width: float = SECOND) -> str:
    """Rounded panel with a bold title and body lines in the tone's ink."""
    out = rect(x, y, w, h, SOFT[tone], EDGE[tone], width, rx=8)
    tx = x + pad if anchor == "start" else x + w / 2
    yy = y + pad + title_size * 0.85
    if title:
        out += text(tx, yy, title, title_size, anchor, FG[tone], weight=700)
        yy += title_size * 0.5 + size * 1.05
    else:
        yy = y + pad + size * 0.9
    out += multiline(tx, yy, lines, size, anchor, FG[tone] if tone != "fg" else "fg-muted", leading)
    return out


def bullets(x: float, y: float, items: list[str], size: float = 12, color: str = "fg", dot: str = "fg-muted", step: float | None = None) -> str:
    step = step or size * 1.45
    out = ""
    for i, s in enumerate(items):
        out += circle(x + 3, y + i * step - size * 0.33, 2.6, dot, None) + text(x + 12, y + i * step, s, size, "start", color)
    return out


def step_dot(x: float, y: float, n: str, tone: str = "brand", r: float = 11) -> str:
    return circle(x, y, r, EDGE[tone], None) + num(x, y + 4, n, 12, "middle", "surface", weight=700)


# ================================================================ 2.3 Flight rules
@chart
def security_prefix_ladder() -> Canvas:
    c = Canvas("MAYDAY, PAN PAN or SECURITE", "Three radio prefixes, each said three times. MAYDAY, distress: grave and imminent danger, "
               "immediate help needed; example: smoke from behind the panel has become a fire. PAN PAN, urgency: a problem that needs "
               "attention, without immediate danger; example: a bird strike has cracked the windscreen. Both are about the caller's own "
               "aircraft. SECURITE, the safety signal: a safety-of-navigation or important weather message for everyone else, nobody in "
               "danger yet; example: kangaroos on runway 27, western half. A routine traffic call such as turning base takes no prefix.",
               height=440, prefix="spl")
    c.add(text(20, 30, "Which prefix? Ask who the message is about, and how bad it is", 15, "start", "fg", weight=700))
    rows = [("MAYDAY", "bad", "Distress", ["grave and imminent danger:", "you need immediate help"], "“the smoke from behind the panel has become a fire”"),
            ("PAN PAN", "warn", "Urgency", ["a problem that needs attention,", "no immediate danger yet"], "“a bird strike has cracked the windscreen”"),
            ("SECURITE", "brand", "Safety signal", ["safety of navigation or an important", "weather warning for everyone listening"], "“kangaroos on runway 27, western half”")]
    Y0, RH = 52, 104
    for i, (word, tone, kind, meaning, example) in enumerate(rows):
        y = Y0 + i * (RH + 10)
        c.add(rect(92, y, 528, RH, SOFT[tone], EDGE[tone], MAIN if tone == "brand" else SECOND, rx=10))
        c.add(text(108, y + 30, f"{word} × 3", 18, "start", FG[tone], weight=800))
        c.add(text(108, y + 52, kind, 13, "start", FG[tone], weight=700))
        c.add(multiline(282, y + 26, meaning, 12.5, "start", FG[tone], 1.35))
        c.add(text(108, y + 84, "e.g. " + example, 12.5, "start", "fg", italic=True))
    y_me0, y_me1 = Y0, Y0 + 2 * RH + 10
    y_ot0, y_ot1 = Y0 + 2 * (RH + 10), Y0 + 3 * RH + 20
    c.add(path(f"M86 {y_me0 + 6} Q78 {y_me0 + 6} 78 {y_me0 + 16} L78 {y_me1 - 16} Q78 {y_me1 - 6} 86 {y_me1 - 6}", "fg-muted", None, SECOND))
    c.add(multiline(68, (y_me0 + y_me1) / 2 - 8, ["about", "my own", "aircraft"], 12, "end", "fg-muted", 1.3, weight=700))
    c.add(path(f"M86 {y_ot0 + 6} Q78 {y_ot0 + 6} 78 {y_ot0 + 16} L78 {y_ot1 - 16} Q78 {y_ot1 - 6} 86 {y_ot1 - 6}", "brand", None, SECOND))
    c.add(multiline(68, (y_ot0 + y_ot1) / 2 - 8, ["about a", "hazard", "to others"], 12, "end", "brand-fg", 1.3, weight=700))
    c.add(text(20, 412, "No prefix for a routine traffic call (\u201cturning base, runway 27\u201d).", 12, "start", "fg-muted"))
    c.add(text(20, 430, "If the hazard has already harmed your aircraft, the call is PAN PAN or MAYDAY, not SECURITE.", 12, "start", "fg-muted"))
    return c


# ================================================================ 2.4 Air service operations
@chart
def overwater_gliding_distance() -> Canvas:
    c = Canvas("Over water: within gliding distance of land?", "Side view of a crossing from the coast to an island. Two dashed glide lines "
               "rise from each shoreline: above them, an aeroplane could glide to that shore if the engine stopped. At 1,500 ft the "
               "middle of the crossing lies below both glide lines, beyond gliding distance of land, where life jackets must be carried "
               "for each person in a single-engine aeroplane. At 6,500 ft the track stays above the glide lines all the way, so the whole "
               "crossing may be within gliding distance. Heights exaggerated, not to scale.", height=400, prefix="owg")
    SEA, CX, IX = 312, 96, 560            # sea level, coast edge, island edge
    MEET = (CX + IX) / 2
    slope = 150 / (MEET - CX)              # glide lines meet 150 px above the sea, mid-crossing
    y65, y15 = SEA - 196, SEA - 62         # 6,500 ft and 1,500 ft tracks (heights exaggerated)
    # sky/sea
    c.add(rect(CX, SEA, IX - CX, 52, "sky-soft", None))
    c.add(path(" ".join(f"{'M' if i == 0 else 'L'}{x} {SEA + 4 + 3 * math.sin(x / 9)}" for i, x in enumerate(range(CX + 4, IX - 4, 6))), "sky-fg", None, THIN))
    # land masses
    c.add(path(f"M0 {SEA + 52} L0 {SEA - 8} Q40 {SEA - 18} 70 {SEA - 6} L{CX} {SEA} L{CX} {SEA + 52} Z", "fg-muted", "surface-2", SECOND))
    c.add(path(f"M{IX} {SEA + 52} L{IX} {SEA} Q{IX + 20} {SEA - 14} {IX + 44} {SEA - 10} Q{IX + 66} {SEA - 4} 640 {SEA - 6} L640 {SEA + 52} Z", "fg-muted", "surface-2", SECOND))
    c.add(text(20, SEA + 34, "coast", 13, "start", "fg", weight=700))
    c.add(text(620, SEA + 34, "island", 13, "end", "fg", weight=700))
    c.add(text((CX + IX) / 2, SEA + 40, "water", 12, "middle", "sky-fg", weight=600))
    # beyond-gliding-distance region under the glide lines
    c.add(polygon([(CX, SEA), (MEET, SEA - 150), (IX, SEA)], "bad-soft", None, fill_opacity=None))
    # glide lines from each shore
    c.add(line(CX, SEA, MEET + 40, SEA - 150 - 40 * slope, "fg-muted", SECOND, dash=DASH))
    c.add(line(IX, SEA, MEET - 40, SEA - 150 - 40 * slope, "fg-muted", SECOND, dash=DASH))
    c.add(text(CX + 70, SEA - 92, "glide to the coast", 11.5, "start", "fg-muted", rotate=-math.degrees(math.atan(slope))))
    c.add(text(IX - 70, SEA - 92, "glide to the island", 11.5, "end", "fg-muted", rotate=math.degrees(math.atan(slope))))
    # 1,500 ft track: green - red - green
    x1 = CX + (SEA - y15) / slope
    x2 = IX - (SEA - y15) / slope
    c.add(line(20, y15, x1, y15, "ok", 3))
    c.add(line(x1, y15, x2, y15, "bad", 4))
    c.add(line(x2, y15, 620, y15, "ok", 3))
    c.add(circle(x1, y15, 4, "bad", "surface", 1.5))
    c.add(circle(x2, y15, 4, "bad", "surface", 1.5))
    c.add(plane_side(140, y15 - 10, 0.34, "fg"))
    c.add(num(20, y15 - 12, "1,500 ft", 13, "start", "fg", weight=700))
    c.add(multiline(MEET, y15 + 22, ["beyond gliding distance of land:", "life jackets for each person,", "within reach of the seated occupant"], 12.5, "middle", "bad-fg", 1.3, weight=700))
    # 6,500 ft track: all green
    c.add(line(20, y65, 620, y65, "ok", 3))
    c.add(plane_side(140, y65 - 10, 0.34, "fg"))
    c.add(num(20, y65 - 12, "6,500 ft", 13, "start", "fg", weight=700))
    c.add(text(MEET, y65 - 12, "may stay within gliding distance all the way", 12, "middle", "ok-fg", weight=700))
    c.add(text(20, 30, "The trigger is gliding distance of land, not a fixed distance from the coast", 14, "start", "fg", weight=700))
    c.add(text(20, 48, "Single-engine aeroplane; climbing higher lengthens the glide.", 12, "start", "fg-muted"))
    c.add(text(620, 392, "heights exaggerated, not to scale", 11, "end", "fg-faint"))
    return c


# ================================================================ 2.5 Aerodromes
def paint_arrow(x: float, y: float, length: float = 26) -> str:
    """Painted centreline arrow pointing right (towards a displaced threshold bar)."""
    return (rect(x, y - 2, length - 9, 4, "paint", None) +
            polygon([(x + length - 11, y - 7), (x + length, y), (x + length - 11, y + 7)], "paint", None))


@chart
def displaced_threshold() -> Canvas:
    c = Canvas("A displaced threshold", "Plan and side view of the worked example: a 1,250 m runway whose northern threshold is displaced 220 m "
               "because of power poles under the approach. White arrows along the centreline lead to a white transverse bar; the threshold "
               "markings start at the bar. Landing towards the south you touch down beyond the bar, so 1,030 m is available for landing. "
               "The arrowed section may be used for the take-off run and for the roll-out after landing in the other direction, so the "
               "full 1,250 m is available for take-off. The side view shows that an approach to the bar clears the poles, while an "
               "approach aimed at the pavement's end would not.", height=470, prefix="dth")
    X0, X1 = 110, 610
    k = (X1 - X0) / 1250
    XB = X0 + 220 * k                       # displaced threshold bar
    Y0, RW = 84, 54
    yc = Y0 + RW / 2
    c.add(text(20, 28, "Worked example: 1,250 m runway, threshold displaced 220 m", 15, "start", "fg", weight=700))
    c.add(arrow(612, 40, 580, 40, "fg-muted", SECOND))
    c.add(text(572, 44, "N", 12, "end", "fg-muted", weight=700))
    # runway surface and markings
    c.add(rect(X0, Y0, X1 - X0, RW, "tarmac", None, rx=2))
    c.add(line(X0 + 2, Y0 + 3, X1 - 2, Y0 + 3, "paint", 1.5, cap="butt"))
    c.add(line(X0 + 2, Y0 + RW - 3, X1 - 2, Y0 + RW - 3, "paint", 1.5, cap="butt"))
    for xx in (X0 + 8, X0 + 36, X0 + 64):
        c.add(paint_arrow(xx, yc, 22))
    c.add(rect(XB - 3, Y0 + 4, 6, RW - 8, "paint", None))
    for j in range(5):
        c.add(rect(XB + 8, Y0 + 7 + j * 9, 22, 5, "paint", None))
        c.add(rect(X1 - 30, Y0 + 7 + j * 9, 22, 5, "paint", None))
    for xx in range(int(XB) + 44, X1 - 50, 30):
        c.add(rect(xx, yc - 1.5, 16, 3, "paint", None))
    # power poles off the northern end (plan)
    PX = 70
    for yy in (Y0 + 6, yc, Y0 + RW - 6):
        c.add(circle(PX, yy, 4, "fg", "surface", 1.5))
    c.add(line(PX, Y0 - 4, PX, Y0 + RW + 4, "fg-muted", THIN))
    c.add(text(PX, Y0 + RW + 22, "poles", 12, "middle", "fg-muted"))
    c.add(text(XB - 6, Y0 - 12, "arrows: \u201croll on me\u201d", 12.5, "end", "fg", weight=700))
    c.add(text(XB + 6, Y0 - 12, "bar: touch down only past here", 12.5, "start", "brand-fg", weight=700))

    def dim(x0: float, x1: float, y: float, tone: str) -> str:
        out = line(x0, y - 7, x0, y + 7, EDGE[tone], SECOND) + line(x1, y - 7, x1, y + 7, EDGE[tone], SECOND)
        return out + arrow((x0 + x1) / 2, y, x0 + 1, y, EDGE[tone], SECOND) + arrow((x0 + x1) / 2, y, x1 - 1, y, EDGE[tone], SECOND)
    DY = Y0 + RW + 40
    c.add(dim(X0, XB, DY, "warn"))
    c.add(num((X0 + XB) / 2, DY + 20, "220 m", 13, "middle", "warn-fg", weight=700))
    c.add(dim(XB, X1, DY, "brand"))
    c.add(text((XB + X1) / 2, DY + 20, "landing towards the south: 1,250 \u2212 220 = 1,030 m", 13, "middle", "brand-fg", weight=700))
    c.add(dim(X0, X1, DY + 46, "ok"))
    c.add(text((X0 + X1) / 2, DY + 66, "take-off run, and roll-out after landing north: full 1,250 m", 13, "middle", "ok-fg", weight=700))
    # side view
    GY = 440
    c.add(line(20, 292, 620, 292, "line", THIN))
    c.add(text(20, 318, "Side view: why the threshold moved", 13, "start", "fg", weight=700))
    c.add(line(20, GY, 620, GY, "fg-muted", SECOND))
    c.add(rect(X0, GY - 4, X1 - X0, 4, "tarmac", None))
    c.add(line(PX, GY, PX, GY - 56, "fg", 3))
    c.add(line(PX - 9, GY - 50, PX + 9, GY - 50, "fg", 2))
    slope = 0.5
    td = XB + 24
    c.add(line(20, GY - (td - 20) * slope, td, GY, "brand", MAIN, dash="8 5"))
    c.add(circle(td, GY, 4, "brand", "surface", 1.5))
    c.add(line(20, GY - (X0 - 20) * slope, X0 + 1, GY, "bad", SECOND, dash=DASH))
    c.add(circle(PX, GY - (X0 - PX) * slope, 4, "bad", "surface", 1.5))
    c.add(plane_side(150, GY - (td - 150) * slope - 14, 0.3, "fg", pitch=-10))
    c.add(line(280, 356, 310, 356, "brand", MAIN, dash="8 5"))
    c.add(text(320, 360, "approach to the bar clears the poles", 12.5, "start", "brand-fg", weight=700))
    c.add(line(280, 382, 310, 382, "bad", SECOND, dash=DASH))
    c.add(text(320, 386, "approach to the pavement's end: too low", 12.5, "start", "bad-fg", weight=700))
    c.add(text(620, GY + 22, "heights exaggerated, not to scale", 11, "end", "fg-faint"))
    return c


def letter_h(x: float, y: float, s: float = 1.0, color: str = "paint") -> str:
    return (rect(x - 16 * s, y - 22 * s, 8 * s, 44 * s, color, None) + rect(x + 8 * s, y - 22 * s, 8 * s, 44 * s, color, None) +
            rect(x - 8 * s, y - 4 * s, 16 * s, 8 * s, color, None))


@chart
def hls_markings() -> Canvas:
    c = Canvas("Helicopter landing site markings", "Three helicopter landing sites seen from above: a letter H inside a circle, inside a "
               "square and inside a triangle, on the touchdown and lift-off area, with a lit or painted perimeter. Below, what an H tells an "
               "aeroplane pilot: keep clear, because downwash can overturn a light aeroplane taxiing nearby; helicopters arrive and depart "
               "steeply and from directions unrelated to the runway in use; and pads may be away from the runways, at a hospital, a mine "
               "site or a station.", height=400, prefix="hls")
    c.add(text(20, 28, "An H inside a circle, square or triangle marks a helicopter landing site", 14, "start", "fg", weight=700))
    for i, (shape, label) in enumerate([("circle", "H in a circle"), ("square", "H in a square"), ("triangle", "H in a triangle")]):
        cx, cy = 116 + i * 204, 132
        c.add(rect(cx - 82, cy - 82, 164, 164, "tarmac", None, rx=6))
        for a in range(0, 360, 30):          # perimeter lights
            c.add(circle(cx + 74 * math.cos(math.radians(a + 15)), cy + 74 * math.sin(math.radians(a + 15)), 3, "warn", None))
        if shape == "circle":
            c.add(circle(cx, cy, 52, None, "paint", 5))
            c.add(letter_h(cx, cy, 1.0))
        elif shape == "square":
            c.add(rect(cx - 46, cy - 46, 92, 92, None, "paint", 5))
            c.add(letter_h(cx, cy, 1.0))
        else:
            c.add(polygon([(cx, cy - 58), (cx + 56, cy + 42), (cx - 56, cy + 42)], None, "paint", 5))
            c.add(letter_h(cx, cy + 12, 0.7))
        c.add(text(cx, cy + 104, label, 13, "middle", "fg", weight=700))
    c.add(circle(26, 262, 3, "warn", None))
    c.add(text(36, 266, "often a lit or painted perimeter", 12, "start", "fg-muted"))
    tiles = [("Keep clear", ["downwash can overturn", "a light aeroplane", "taxiing nearby"]),
             ("Steep arrivals", ["from directions that", "have nothing to do with", "the runway in use"]),
             ("Away from runways", ["hospital pads,", "mine sites,", "station pads"])]
    for i, (title, lines) in enumerate(tiles):
        c.add(card(20 + i * 204, 284, 192, 100, title, lines, "brand" if i == 0 else "fg", 12, 14))
    return c


@chart
def right_hand_circuit_dead_side() -> Canvas:
    c = Canvas("Right-hand circuits move the dead side", "Two plan views of runway 31, landing from left to right on the page. Top: the "
               "default left-hand circuit, with the circuit on the south-west side and the dead side on the north-east. Bottom: right-hand "
               "circuits for runway 31, as ERSA shows in the worked example: upwind 310, crosswind about 040, downwind 130, base about "
               "220, final 310, all on the north-east side, so the dead side is now the south-west, to the left of the runway looking "
               "along the landing direction. An aeroplane flies the right-hand circuit.", height=520, prefix="rhc")
    RL = 210

    def panel(y0: float, right: bool) -> list[str]:
        yc = y0 + 120
        out = []
        side = 1 if right else -1                       # +1: circuit below the runway (right of 310 = towards 040)
        circ_y0, circ_h = (yc, 96) if right else (yc - 96, 96)
        dead_y0 = yc - 96 if right else yc
        out.append(rect(20, circ_y0, 600, circ_h, "brand-soft", None, rx=0, fill_opacity=0.35 if right else 0.18))
        out.append(rect(20, dead_y0, 600, 96, "surface-2", None))
        out.append(runway(320, yc, RL, 22, None))
        out.append(num(320 - RL / 2 + 34, yc + 4.5, "31", 12, "middle", "paint", weight=700))
        dy = 66 * side
        d = (f"M{320 - RL / 2 + 30} {yc} L{470} {yc} Q{510} {yc} {510} {yc + dy * 0.5} Q{510} {yc + dy} {470} {yc + dy} "
             f"L{170} {yc + dy} Q{130} {yc + dy} {130} {yc + dy * 0.5} Q{130} {yc} {170} {yc} L{320 - RL / 2 + 30} {yc}")
        out.append(path(d, "brand" if right else "fg-faint", None, MAIN if right else SECOND, dash="8 6"))
        if right:
            out.append(path(d, None, None, 0, cls=None))
        lab_y = yc + dy + (18 if right else -12)
        tone = "brand-fg" if right else "fg-muted"
        out.append(text(320, lab_y + (4 if right else 0), "downwind 130", 12.5, "middle", tone, weight=700))
        out.append(text(518, yc + dy * 0.5 + 4, "crosswind 040" if right else "crosswind 220", 12.5, "start", tone, weight=700))
        out.append(text(122, yc + dy * 0.5 + 4, "base 220" if right else "base 040", 12.5, "end", tone, weight=700))
        dead_label_y = yc - 74 if right else yc + 86
        out.append(text(36, dead_label_y, "Dead side: " + ("south-west" if right else "north-east"), 14, "start", "fg", weight=700))
        out.append(text(36, dead_label_y + 16, "to the left looking along 310" if right else "to the right looking along 310", 11.5, "start", "fg-muted"))
        return out

    c.add(text(20, 26, "Left-hand circuit (the default)", 14, "start", "fg-muted", weight=700))
    for m in panel(14, False):
        c.add(m)
    c.add(text(20, 270, "Right-hand circuit for runway 31 (ERSA): legs and dead side swap sides", 14, "start", "fg", weight=700))
    for m in panel(264, True):
        c.add(m)
    # animated aeroplane on the right-hand circuit
    yc = 264 + 120
    d = (f"M{320 - RL / 2 + 30} {yc} L470 {yc} Q510 {yc} 510 {yc + 33} Q510 {yc + 66} 470 {yc + 66} L170 {yc + 66} Q130 {yc + 66} 130 {yc + 33} "
         f"Q130 {yc} 170 {yc} L{320 - RL / 2 + 30} {yc}")
    c.style(f"""
.rhc-plane{{offset-path:path("{d}");offset-rotate:auto;animation:rhc-fly 16s linear infinite}}
@keyframes rhc-fly{{to{{offset-distance:100%}}}}
.rhc-plane-static{{display:none}}
@supports not (offset-path: path("M0 0")){{.rhc-plane{{display:none}}.rhc-plane-static{{display:inline}}}}
""")
    c.add(group(plane_top(0, 0, 0.28, 90, "fg", "surface"), cls="rhc-plane"))
    c.add(group(plane_top(250, yc + 66, 0.28, 270, "fg", "surface"), cls="rhc-plane-static"))
    # north arrow: 310 is to the right of the page, so north points up and to the right
    c.add(group(arrow(0, 0, 0.643 * 26, -0.766 * 26, "fg-muted", SECOND), text(22, -26, "N", 12, "start", "fg-muted", weight=700),
                transform="translate(588 508)"))
    c.add(text(560, 512, "landing 310 →", 11.5, "end", "fg-muted"))
    return c


# ================================================================ 2.7 Emergencies, accidents and incidents
@chart
def ersa_emerg_contents() -> Canvas:
    c = Canvas("What is in ERSA EMERG", "The pink pages of ERSA, grouped by what a pilot in trouble needs. Tell someone: the MAYDAY and PAN PAN "
               "calls and their format (callsign, nature of the emergency, intentions, position, altitude, heading, persons on board), "
               "made on the current frequency then 121.5 MHz, and the transponder codes 7700, 7600 and 7500. Deal with the problem: "
               "radio failure procedures for Class G and controlled airspace, interception signals and responses, ditching and forced "
               "landing. If you end up on the ground: the SAR phases, ELT operation and the ground-to-air signals. Also in EMERG: light "
               "signals from a control tower and emergency contact numbers for the ATSB, Airservices and the JRCC. Grouped by purpose, "
               "not page order; check your current ERSA.", height=470, prefix="eec")
    c.add(rect(20, 14, 600, 40, "bad-soft", None, rx=8))
    c.add(text(36, 40, "ERSA EMERG: the pink pages", 16, "start", "bad-fg", weight=700))
    c.add(text(604, 40, "find it by feel", 12, "end", "bad-fg"))
    groups = [("1", "Tell someone", "brand", [("MAYDAY: distress", []), ("PAN PAN: urgency", []),
                                            ("Call format", ["callsign, nature,", "intentions, position,", "altitude, heading, POB"]),
                                            ("Where", ["current frequency,", "then 121.5 MHz"]),
                                            ("Transponder codes", ["7700 emergency", "7600 radio failure", "7500 unlawful interference"])]),
              ("2", "Deal with it", "warn", [("Radio failure", ["Class G VFR: continue in", "VMC, nearest suitable", "aerodrome, broadcast", "blind, squawk 7600",
                                                                         "Controlled: last clearance,", "expected procedures,", "watch for light signals"]),
                                                     ("Interception", ["signals and responses"]),
                                                     ("Ditching", ["and forced landing:", "preparation, survival"])]),
              ("3", "On the ground", "info", [("Search and rescue", ["the SAR phases"]), ("ELT", ["how to operate it"]),
                                                       ("Ground-to-air signals", ["V  X  N  Y  arrow"])])]
    for i, (n, title, tone, items) in enumerate(groups):
        x, y, w, h = 20 + i * 204, 66, 192, 314
        c.add(rect(x, y, w, h, SOFT[tone], EDGE[tone], MAIN if i == 0 else SECOND, rx=10))
        c.add(step_dot(x + 22, y + 24, n, tone))
        c.add(text(x + 40, y + 29, title, 13.5, "start", FG[tone], weight=700))
        yy = y + 58
        for head, sub in items:
            c.add(text(x + 14, yy, head, 12.5, "start", FG[tone], weight=700))
            yy += 16
            for s in sub:
                c.add(text(x + 14, yy, s, 11.5, "start", "fg"))
                yy += 15
            yy += 8
    c.add(rect(20, 392, 600, 44, "surface-2", "line-strong", THIN, rx=8))
    c.add(text(36, 412, "Also in EMERG:", 12.5, "start", "fg", weight=700))
    c.add(text(160, 412, "light signals from a control tower; emergency contact numbers", 12, "start", "fg"))
    c.add(text(160, 428, "for the ATSB accident line, Airservices and the JRCC", 12, "start", "fg"))
    c.add(text(20, 458, "Grouped by purpose, not page order: check your current ERSA. Full text in AIP GEN 3.6 and ENR 1.12.", 11, "start", "fg-faint"))
    return c


@chart
def mercy_flight_decision() -> Canvas:
    c = Canvas("May this be a mercy flight?", "A decision flowchart. First: can the flight be made within the normal rules? If yes, there is "
               "nothing to declare; it is an ordinary flight. If no, all four conditions must hold: the flight is necessary to relieve a "
               "person's suffering or to save life (not merely carrying a sick person who is not in grave danger); no other means of "
               "transport is available in time (the need cannot be met by other transport or by waiting); the pilot in command has "
               "considered the risks and the flight can be made with an acceptable level of safety (the risk does not outweigh the "
               "benefit, and the pilot is competent for the conditions: an instrument-rated pilot and aircraft for IMC); and CASA or ATS "
               "is notified of the declaration and the departures from the rules, before the flight where possible. Any no: it must not "
               "be flown as a mercy flight. Declaring changes the legal position only, not the physics or the weather.",
               height=600, prefix="mfd")
    X, W = 20, 340
    RX, RW = 404, 216
    c.add(text(20, 28, "The pilot in command (or the operator) works down the list", 14, "start", "fg", weight=700))
    # start question
    c.add(rect(X, 44, W, 54, "surface-2", "line-strong", SECOND, rx=10))
    c.add(text(X + 14, 66, "Can the flight be made within", 13, "start", "fg", weight=700))
    c.add(text(X + 14, 84, "the normal rules?", 13, "start", "fg", weight=700))
    c.add(arrow(X + W, 71, RX - 2, 71, "ok", SECOND))
    c.add(text(X + W + 22, 64, "yes", 12, "middle", "ok-fg", weight=700))
    c.add(card(RX, 44, RW, 54, None, ["Nothing to declare: an", "ordinary flight under the rules"], "ok", 12, pad=10))
    c.add(arrow(X + 40, 98, X + 40, 120, "fg-muted", SECOND))
    c.add(text(X + 50, 114, "no: night by a VFR-only pilot, weather below VFR minima...", 11, "start", "fg-muted"))
    qs = [("1", ["Is it necessary to relieve a person's", "suffering or to save life?"], ["a sick person who is", "not in grave danger"]),
          ("2", ["Is no other means of transport", "available in time?"], ["other transport, or", "waiting, would do"]),
          ("3", ["Have you weighed the risks: an", "acceptable level of safety, and", "competent for the conditions?"],
           ["risk outweighs benefit;", "IMC without an instrument-", "rated pilot and aircraft"]),
          ("4", ["Notify CASA or ATS of the", "declaration and the departures", "from the rules, before the flight", "where possible"], None)]
    y = 126
    for n, q, nope in qs:
        h = 34 + 16 * len(q) if len(q) > 2 else 62
        last = nope is None
        c.add(rect(X, y, W, h, "brand-soft", "brand", MAIN if not last else SECOND, rx=10))
        c.add(step_dot(X + 22, y + 22, n, "brand"))
        c.add(multiline(X + 42, y + 26, q, 12.5, "start", "brand-fg", 1.3, weight=700 if not last else 600))
        if nope:
            mid = y + h / 2
            c.add(arrow(X + W, mid, RX - 2, mid, "bad", SECOND))
            c.add(text(X + W + 22, mid - 7, "no", 12, "middle", "bad-fg", weight=700))
            c.add(card(RX, y + 2, RW, h - 4, None, ["Must not be flown:", *nope], "bad", 11.5, pad=10, leading=1.3))
        y += h
        c.add(arrow(X + 40, y, X + 40, y + 18, "brand", SECOND))
        if not last:
            c.add(text(X + 52, y + 13, "yes", 11.5, "start", "brand-fg", weight=700))
        y += 22
    c.add(rect(X, y, W, 50, "brand", None, rx=10))
    c.add(text(X + W / 2, y + 22, "Mercy flight", 16, "middle", "surface", weight=800))
    c.add(text(X + W / 2, y + 40, "all four conditions met", 12, "middle", "surface"))
    c.add(card(RX, y - 74 - 16, RW, 140, "Remember", ["Declaring a mercy flight", "changes the legal position", "only, not the physics or", "the weather."], "fg", 12, 13))
    return c


def hazard_icon(kind: str, x: float, y: float, color: str) -> str:
    """Small pictograms for the hazard groups, centred on (x, y), about 36 units across."""
    if kind == "mast":
        return (path(f"M{x - 9} {y + 18} L{x} {y - 18} L{x + 9} {y + 18} M{x - 6} {y + 6} L{x + 6} {y + 6} M{x - 3} {y - 6} L{x + 3} {y - 6}", color, None, 2.2) +
                circle(x, y - 19, 3, "bad", None))
    if kind == "runway":
        return (rect(x - 20, y - 8, 40, 16, "tarmac", None, rx=2) + rect(x - 14, y - 1, 8, 2, "paint", None) + rect(x + 2, y - 1, 8, 2, "paint", None) +
                path(f"M{x - 12} {y - 18} q4 -5 8 0 q4 -5 8 0 M{x + 4} {y - 22} q3 -4 6 0 q3 -4 6 0", color, None, 2))
    if kind == "aid":
        return (line(x - 14, y + 18, x - 14, y - 16, color, 2.2) + path(f"M{x - 14} {y - 16} L{x + 14} {y - 12} L{x + 14} {y - 2} L{x - 14} {y - 4} Z", color, None, 2) +
                line(x - 4, y + 2, x + 18, y + 18, "bad", 2.5) + line(x + 18, y + 2, x - 4, y + 18, "bad", 2.5))
    if kind == "weather":
        return (path(f"M{x - 18} {y + 2} q-2 -12 10 -12 q4 -10 16 -6 q12 -2 12 10 q6 4 0 8 Z", color, None, 2) +
                polyline([(x + 2, y + 4), (x - 4, y + 13), (x + 3, y + 13), (x - 3, y + 22)], "warn", 2.5))
    if kind == "air":
        return (polygon([(x - 6, y - 20), (x + 8, y - 8), (x - 2, y + 6), (x - 16, y - 6)], None, color, 2) +
                path(f"M{x - 2} {y + 6} q6 6 2 10 q-4 4 4 8", color, None, 1.6) +
                rect(x + 8, y + 4, 12, 6, None, color, 1.6, rx=2) + line(x + 6, y + 4, x + 22, y + 4, color, 1.6))
    if kind == "fire":
        return (path(f"M{x - 16} {y + 18} q-4 -14 6 -22 q0 8 6 10 q-2 -14 8 -24 q2 12 10 18 q6 8 0 18 Z", "bad", None, 2) +
                path(f"M{x - 8} {y - 14} q-6 -6 0 -12 M{x + 8} {y - 20} q-6 -6 0 -10", "fg-muted", None, 1.6))
    return ""


@chart
def hazard_to_navigation_groups() -> Canvas:
    c = Canvas("Hazards to navigation: six groups", "Six tiles. Things you could hit that the chart does not show: an unlit or unmarked "
               "crane, mast or wind turbine, or a failed obstacle light. Things on or near the runway: birds on or near an aerodrome, bird "
               "strikes (also to the ATSB), animals, vehicles or people on a runway. Aids that are not working: navigation aids, runway "
               "lighting, a wind indicator. Weather nobody forecast: thunderstorms, severe turbulence, wind shear, dust storms, volcanic "
               "ash, a fog bank forming. Other things in the air: unmanned or model aircraft, kites, balloons, laser illumination. "
               "Activity nobody told you about: smoke, bushfire, fire-fighting, military activity, parachuting or gliding not promulgated. "
               "Report to ATS as soon as possible by radio, with a SECURITE broadcast where it is a safety broadcast, and in writing "
               "afterwards if required, so ATS can warn others and issue a NOTAM.", height=470, prefix="htn")
    c.add(text(20, 28, "Would it catch out the next pilot? Then it is a hazard to report", 14, "start", "fg", weight=700))
    tiles = [("mast", ["Things you", "could hit"], ["unlit or unmarked crane,", "mast or wind turbine not", "on the chart; a failed", "obstacle light"]),
             ("runway", ["On or near", "the runway"], ["birds on or near the", "aerodrome (bird strikes", "also to the ATSB); animals,", "vehicles, people"]),
             ("aid", ["Aids not", "working"], ["navigation aids, runway", "lighting, a wind indicator"]),
             ("weather", ["Weather nobody", "forecast"], ["thunderstorms, severe", "turbulence, wind shear,", "dust storms, volcanic ash,", "a fog bank forming"]),
             ("air", ["Other things", "in the air"], ["drones, model aircraft,", "kites, balloons; laser", "illumination of the", "cockpit"]),
             ("fire", ["Activity nobody", "told you of"], ["smoke, bushfire, fire-", "fighting; military activity,", "parachuting or gliding", "not promulgated"])]
    for i, (kind, title, lines) in enumerate(tiles):
        x, y = 20 + (i % 3) * 204, 44 + (i // 3) * 160
        c.add(rect(x, y, 192, 150, "surface-2", "line-strong", SECOND, rx=10))
        c.add(hazard_icon(kind, x + 34, y + 38, "fg"))
        c.add(multiline(x + 66, y + 34, title, 13, "start", "fg", 1.25, weight=700))
        c.add(multiline(x + 12, y + 86, lines, 11.5, "start", "fg-muted", 1.3))
    # what to do
    y = 372
    steps = [("Report by radio", ["to ATS as soon as possible;", "SECURITE for a safety", "broadcast"]),
             ("In writing afterwards", ["if required"]),
             ("The result", ["ATS warns other aircraft,", "may issue a NOTAM"])]
    for i, (h, lines) in enumerate(steps):
        x = 20 + i * 204
        c.add(card(x, y, 192, 90, h, lines, "brand" if i == 0 else "fg", 12, 13, width=MAIN if i == 0 else SECOND))
        if i < 2:
            c.add(arrow(x + 193, y + 42, x + 203, y + 42, "brand", SECOND))
    return c


# ================================================================ 2.8 Security
def rock_marks(x: float, y: float, s: float, color: str) -> str:
    """Little curved arrows at both wingtips of a plan-view aeroplane heading right: wing rocking."""
    return (path(f"M{x - 7 * s - 6} {y - 56 * s} q6 -8 12 0", color, None, SECOND) + path(f"M{x - 7 * s - 6} {y + 56 * s} q6 8 12 0", color, None, SECOND))


@chart
def interception_signals() -> Canvas:
    c = Canvas("Interception: the three signals and your replies", "Three panels. One: the interceptor, ahead and to your left, rocks its "
               "wings then makes a slow level turn onto the desired heading: you have been intercepted, follow me; reply by rocking your "
               "wings and following. Two: the interceptor makes an abrupt breakaway, a climbing turn of 90 degrees or more without "
               "crossing ahead of you: you may proceed; reply by rocking your wings. Three: the interceptor lowers its gear if fitted, "
               "shows its landing lights and overflies the runway: land at this aerodrome; reply by lowering your gear if fitted, "
               "following and landing if safe. At night, flashing navigation lights replace wing rocking.", height=580, prefix="int")
    c.add(text(20, 28, "Interceptor's signal, its meaning, and your reply (AIP ENR 1.12)", 14, "start", "fg", weight=700))
    rows = [("Rocks wings from ahead and to your left, then", ["a slow level turn onto the desired heading"], "“You have been intercepted, follow me”", "Rock wings and follow"),
            ("Abrupt breakaway: a climbing turn of 90°", ["or more, without crossing ahead of you"], "“You may proceed”", "Rock wings"),
            ("Lowers gear (if fitted), shows landing", ["lights, overflies the runway"], "“Land at this aerodrome”", "Lower gear (if fitted), follow, land if safe")]
    for i, (sig1, sig2, meaning, reply) in enumerate(rows):
        y0 = 44 + i * 164
        c.add(rect(20, y0, 600, 152, "surface-2", "line-strong", THIN, rx=10))
        c.add(rect(32, y0 + 12, 250, 128, "surface", None, rx=8))
        yc = y0 + 76
        if i == 0:
            c.add(plane_top(94, yc + 34, 0.4, 90, "fg"))
            c.add(text(64, yc + 38, "you", 11.5, "end", "fg-muted"))
            c.add(plane_top(182, yc - 8, 0.4, 90, "info", "info-soft"))
            c.add(rock_marks(182, yc - 8, 0.4, "info"))
            c.add(path(f"M196 {yc - 8} Q240 {yc - 8} 262 {yc - 40}", "info", None, SECOND, dash="5 4", arrow_end=True))
            c.add(path(f"M110 {yc + 34} Q200 {yc + 34} 240 {yc}", "brand", None, SECOND, dash="5 4", arrow_end=True))
        elif i == 1:
            c.add(plane_top(94, yc + 20, 0.4, 90, "fg"))
            c.add(text(64, yc + 24, "you", 11.5, "end", "fg-muted"))
            c.add(plane_top(162, yc - 16, 0.4, 90, "info", "info-soft"))
            c.add(path(f"M172 {yc - 16} Q214 {yc - 18} 214 {yc - 44} Q214 {yc - 58} 196 {yc - 58}", "info", None, MAIN, arrow_end=True))
            c.add(text(222, yc - 30, "climbing", 11.5, "start", "info-fg"))
            c.add(line(110, yc + 20, 270, yc + 20, "brand", SECOND, dash="5 4", arrow_end=True))
            c.add(text(200, yc + 40, "never crosses ahead", 11.5, "middle", "fg-muted"))
        else:
            gy = yc + 44
            c.add(line(40, gy, 274, gy, "fg-muted", SECOND))
            c.add(rect(110, gy - 4, 150, 4, "tarmac", None))
            c.add(text(185, gy + 18, "runway", 11.5, "middle", "fg-muted"))
            c.add(plane_side(184, gy - 40, 0.55, "info", fill="info-soft"))
            for dy in (-6, 0, 6):
                c.add(line(205, gy - 38 + dy * 0.3, 232, gy - 38 + dy * 1.6, "warn", SECOND))
            c.add(text(238, gy - 56, "lights", 11.5, "start", "warn-fg"))
            c.add(text(140, gy - 12, "gear down", 11.5, "end", "info-fg"))
        c.add(text(298, y0 + 28, "Interceptor", 11.5, "start", "info-fg", weight=700))
        c.add(multiline(298, y0 + 46, [sig1, *sig2], 12, "start", "fg", 1.3))
        c.add(text(298, y0 + 90, meaning, 13.5, "start", "fg", weight=700))
        if len(reply) > 30:
            c.add(rect(298, y0 + 100, 310, 44, "brand-soft", "brand", SECOND, rx=6))
            c.add(multiline(310, y0 + 118, ["You: lower gear (if fitted),", "follow, and land if safe"], 13, "start", "brand-fg", 1.25, weight=700))
        else:
            c.add(rect(298, y0 + 104, 310, 30, "brand-soft", "brand", SECOND, rx=6))
            c.add(text(310, y0 + 124, "You: " + reply, 13, "start", "brand-fg", weight=700))
    c.add(text(20, 546, "At night, flashing navigation lights replace wing rocking.", 12, "start", "fg-muted"))
    c.add(text(20, 564, "If ATS and the interceptor disagree, follow the interceptor and ask ATS for clarification.", 12, "start", "fg-muted"))
    return c


@chart
def adiz_entry_tolerance() -> Canvas:
    c = Canvas("ADIZ entry: matching the plan to the radar", "Plan view of a VFR track crossing an ADIZ boundary at the planned entry "
               "point in the flight notification. A window around the planned entry point shows the track tolerance; a timeline below shows "
               "the time tolerance around the planned entry time. An aircraft on track and on time falls inside both and is identified. "
               "An aircraft off track, or late beyond the time tolerance, without telling ATS, may be treated as unidentified and may "
               "be intercepted. Advising ATS of the deviation as soon as possible, before the boundary, restores the match. The actual "
               "tolerances are in AIP ENR 2.2; no figures are shown.", height=470, prefix="adz")
    BX = 380
    c.add(rect(BX, 40, 240, 230, "info-soft", None, rx=0, fill_opacity=None))
    c.add(line(BX, 40, BX, 270, "info", MAIN, dash="10 6"))
    c.add(text(BX + 14, 62, "ADIZ", 16, "start", "info-fg", weight=700))
    c.add(text(BX + 14, 80, "boundary and rules: AIP ENR 2.2", 11.5, "start", "info-fg"))
    c.add(text(20, 28, "Defence asks: is the aircraft we see the one we were told about?", 14, "start", "fg", weight=700))
    TY = 150
    c.add(line(30, TY, 600, TY, "fg-faint", SECOND, dash=DASH))
    c.add(text(40, TY - 26, "planned track (flight notification)", 11.5, "start", "fg-muted"))
    # tolerance window around planned entry point
    c.add(rect(BX - 34, TY - 44, 68, 88, "ok-soft", "ok", SECOND, rx=6, fill_opacity=None))
    c.add(circle(BX, TY, 5, "ok", "surface", 2))
    c.add(multiline(BX - 44, TY - 30, ["planned", "entry point"], 12, "end", "ok-fg", 1.25, weight=700))
    c.add(multiline(BX - 44, TY + 30, ["track", "tolerance"], 11.5, "end", "ok-fg", 1.25))
    # aircraft A: on track
    c.add(plane_top(204, TY, 0.36, 90, "fg"))
    c.add(text(200, TY + 30, "on track", 11.5, "middle", "fg-muted"))
    # aircraft B: off track
    BY = 238
    c.add(polyline([(30, TY + 8), (100, TY + 10), (220, BY)], "bad", SECOND, dash="5 4"))
    c.add(line(220, BY, 470, BY, "bad", SECOND, dash="5 4", arrow_end=True))
    c.add(plane_top(304, BY, 0.36, 90, "bad", "bad-soft"))
    c.add(text(40, BY + 29, "off track round a cloud bank, not reported to ATS", 11.5, "start", "bad-fg", weight=600))
    c.add(text(486, BY + 4, "may be treated", 11.5, "start", "bad-fg", weight=700))
    c.add(text(486, BY + 19, "as unidentified", 11.5, "start", "bad-fg", weight=700))
    # timeline
    LY = 330
    c.add(text(20, 300, "Time at the entry point", 13, "start", "fg", weight=700))
    c.add(line(40, LY, 600, LY, "fg-muted", SECOND))
    c.add(arrow(590, LY, 608, LY, "fg-muted", SECOND))
    c.add(rect(260, LY - 16, 120, 32, "ok-soft", "ok", SECOND, rx=6))
    c.add(line(320, LY - 16, 320, LY + 16, "ok", MAIN))
    c.add(text(320, LY + 34, "planned entry time", 12, "middle", "ok-fg", weight=700))
    c.add(text(320, LY + 50, "± time tolerance", 11.5, "middle", "ok-fg"))
    c.add(circle(300, LY, 6, "fg", "surface", 2))
    c.add(text(300, LY - 24, "on time", 11.5, "middle", "fg-muted"))
    c.add(circle(500, LY, 6, "bad", "surface", 2))
    c.add(text(500, LY - 24, "late (headwind)", 11.5, "middle", "bad-fg", weight=600))
    c.add(text(500, LY + 34, "outside the tolerance", 11.5, "middle", "bad-fg"))
    c.add(rect(20, 400, 600, 56, "brand-soft", "brand", MAIN, rx=10))
    c.add(text(36, 424, "Off track or running late? Advise ATS as soon as possible, before the boundary.", 13, "start", "brand-fg", weight=700))
    c.add(text(36, 444, "Defence then expects the new track or time, and the match is made. Tolerances: AIP ENR 2.2.", 11.5, "start", "brand-fg"))
    return c


@chart
def pic_authority() -> Canvas:
    c = Canvas("The pilot in command's powers, and their limits", "Responsibility for the safety of the aircraft and everyone on board "
               "comes with final authority over its operation (CASR Part 91). The powers: give safety directions, which passengers and "
               "crew must obey; refuse to carry or disembark a person whose behaviour endangers safety; take reasonable measures, "
               "including restraint, against a person committing or about to commit an offence that threatens safety, protected when "
               "done in good faith by the Crimes (Aviation) Act 1991 and the Tokyo Convention; refuse unsafe cargo or baggage, including "
               "dangerous goods not permitted; and depart from a rule or ATC clearance in an emergency, only as far as necessary for safety, "
               "reporting it afterwards.", height=450, prefix="pic")
    c.add(card(20, 16, 280, 66, "Responsibility", ["for the safety of the aircraft", "and everyone on board"], "fg", 12, 14))
    c.add(card(340, 16, 280, 66, "Final authority", ["over the operation of the aircraft", "(CASR Part 91)"], "brand", 12, 14, width=MAIN))
    c.add(arrow(306, 49, 334, 49, "brand", MAIN))
    c.add(text(320, 100, "come together", 11.5, "middle", "fg-muted"))
    c.add(text(32, 132, "You may", 13, "start", "fg", weight=700))
    c.add(text(340, 132, "Within this limit", 13, "start", "fg", weight=700))
    rows = [(["Give safety directions to", "passengers and crew"], ["they must comply: failing to", "is an offence"], "fg"),
            (["Refuse to carry, or disembark,", "a person who endangers safety"], ["e.g. intoxicated or disruptive"], "fg"),
            (["Restrain a person committing an", "offence that threatens safety"], ["reasonable measures, in good faith", "(Crimes (Aviation) Act 1991, Tokyo Conv.)"], "warn"),
            (["Refuse unsafe cargo or baggage"], ["including dangerous goods", "not permitted for carriage"], "fg"),
            (["Depart from a rule or ATC", "clearance in an emergency"], ["only as far as necessary", "for safety; report it afterwards"], "warn")]
    y = 142
    for left, right, tone in rows:
        c.add(rect(20, y, 600, 50, "surface-2" if tone == "fg" else "warn-soft", None, rx=8))
        c.add(multiline(32, y + 21 if len(left) > 1 else y + 30, left, 12.5, "start", "fg", 1.3, weight=600))
        c.add(arrow(306, y + 25, 330, y + 25, "fg-muted", SECOND))
        c.add(multiline(340, y + 21 if len(right) > 1 else y + 30, right, 12, "start", FG[tone] if tone != "fg" else "fg-muted", 1.3))
        y += 56
    c.add(text(20, y + 16, "Final authority is not unlimited: use the smallest power that restores safety.", 12.5, "start", "brand-fg", weight=700))
    return c


# ================================================================ 2.9 Emergencies and SAR
@chart
def sar_alerting_phases() -> Canvas:
    c = Canvas("The SAR alerting phases", "When a SARTIME expires uncancelled, the search and rescue response is staged, coordinated by the JRCC: "
               "the uncertainty phase, then the alert phase, then the distress phase, each a step higher. As it moves through them the "
               "actions escalate: attempts to contact you (calls on frequency, a phone call to your destination), then a communications "
               "search to aerodromes and contacts along your route, then a physical search by aircraft and ground parties. Effort grows "
               "only as the evidence grows. The search starts from your notified route and time.", height=440, prefix="sap")
    c.add(text(20, 28, "Effort grows only as the evidence that you are in trouble grows", 14, "start", "fg", weight=700))
    # trigger
    c.add(rect(20, 238, 128, 62, "surface-2", "line-strong", SECOND, rx=8))
    c.add(multiline(84, 262, ["SARTIME passes", "uncancelled"], 12.5, "middle", "fg", 1.3, weight=700))
    steps = [("Uncertainty", "warn", 236, 0), ("Alert", "warn", 184, 0), ("Distress", "bad", 132, 0)]
    for i, (name, tone, top, h) in enumerate(steps):
        x = 164 + i * 152
        c.add(rect(x, top, 144, 300 - top, SOFT[tone], EDGE[tone], MAIN if i == 2 else SECOND, rx=6))
        c.add(text(x + 72, top + 26, name, 15, "middle", FG[tone], weight=700))
        c.add(text(x + 72, top + 44, "phase", 12, "middle", FG[tone]))
    c.add(arrow(150, 269, 160, 269, "fg-muted", SECOND))
    c.add(text(20, 70, "Coordinated by the JRCC, the Joint Rescue", 12.5, "start", "fg", weight=600))
    c.add(text(20, 88, "Coordination Centre (AMSA)", 12.5, "start", "fg", weight=600))
    c.add(text(20, 120, "Forgot to cancel? You are usually", 11.5, "start", "fg-muted"))
    c.add(text(20, 136, "found by the first step, at the cost", 11.5, "start", "fg-muted"))
    c.add(text(20, 152, "of a lot of people's time.", 11.5, "start", "fg-muted"))
    # actions
    c.add(text(20, 330, "The actions escalate in this order", 13, "start", "fg", weight=700))
    acts = [("1", "Contact you", ["calls on frequency,", "a phone call to your", "destination"]),
            ("2", "Communications search", ["aerodromes and contacts", "along your notified route"]),
            ("3", "Physical search", ["aircraft and ground", "parties"])]
    for i, (n, head, lines) in enumerate(acts):
        x = 20 + i * 204
        c.add(rect(x, 342, 192, 84, "bad-soft" if i == 2 else "surface-2", "bad" if i == 2 else "line-strong", SECOND, rx=8))
        c.add(step_dot(x + 20, 362, n, "bad" if i == 2 else "warn"))
        c.add(text(x + 38, 367, head, 12, "start", "bad-fg" if i == 2 else "fg", weight=700))
        c.add(multiline(x + 14, 388, lines, 11.5, "start", "fg-muted", 1.3))
        if i < 2:
            c.add(arrow(x + 193, 384, x + 203, 384, "fg-muted", SECOND))
    return c


@chart
def light_signals_compared() -> Canvas:
    patterns = [
        ("Tower shows you a green at night", "single flash", [(1, 1)], "Acknowledgement: “received”", "ok"),
        ("Aircraft on approach, no radio call", "lights switched on and off, repeatedly", [(0, 1), (2, 2), (5, 1), (7, 1), (10, 2), (13, 1)],
         "In difficulty, compelled to land: give way", "bad"),
        ("Intercepted aircraft", "all lights on and off at regular intervals", [(0, 1), (2, 1), (4, 1), (6, 1), (8, 1), (10, 1), (12, 1)],
         "Cannot comply", "warn"),
        ("Intercepted aircraft", "lights flashed at irregular intervals", [(0, 1), (1.6, 0.6), (4, 1.4), (6.2, 0.5), (9, 1), (10.6, 0.6), (13, 0.8)],
         "In distress", "bad")]
    c = Canvas("Lights on and off: four meanings", "Four light patterns compared on a time strip. A single flash of the landing lights after a "
               "tower light signal at night: acknowledgement. Navigation and landing lights switched on and off intermittently and repeatedly "
               "on approach: in difficulty and compelled to land, give way. An intercepted aircraft switching all its lights on and off at "
               "regular intervals: cannot comply. An intercepted aircraft flashing its lights at irregular intervals: in distress. The "
               "context decides the meaning. A cursor sweeps along the strips.", height=446, prefix="lsc")
    c.add(text(20, 28, "Same lights, different meanings: read the pattern and the context", 14, "start", "fg", weight=700))
    SX, CW, NC = 300, 22, 14
    c.style(".lsc-cursor{animation:lsc-sweep 6s linear infinite}\n@keyframes lsc-sweep{from{transform:translateX(0)}to{transform:translateX(308px)}}")
    for i, (ctx, how, cells, meaning, tone) in enumerate(patterns):
        y = 50 + i * 92
        c.add(rect(20, y, 600, 82, "surface-2", None, rx=8))
        c.add(text(32, y + 24, ctx, 13, "start", "fg", weight=700))
        c.add(text(32, y + 42, how, 11.5, "start", "fg-muted"))
        c.add(rect(SX, y + 12, CW * NC, 22, "surface", "line-strong", THIN, rx=3))
        for start, length in cells:
            c.add(rect(SX + start * CW + 1, y + 14, length * CW - 2, 18, "warn", None, rx=2))
        c.add(badge(SX + CW * NC / 2, y + 60, meaning, tone, 12))
    c.add(group(*[line(SX, 50 + i * 92 + 8, SX, 50 + i * 92 + 38, "fg", SECOND) for i in range(4)], cls="lsc-cursor"))
    c.add(text(SX, 426, "time →", 11.5, "start", "fg-faint"))
    c.add(text(620, 426, "lit cells: lights on", 11.5, "end", "fg-faint"))
    return c


# ================================================================ 2.1 Documentation
@chart
def notam_anatomy() -> Canvas:
    c = Canvas("Reading a NOTAM", "The invented NOTAM from the worked example, for Geraldton (YGEL): runway 03/21 closed due to work in "
               "progress, B 2611140100, C 2611150930. Each part is labelled: identifier and series, location as an ICAO four-letter "
               "code, the B (effective from) and C (ends) times as ten-figure UTC date-time groups (year, month, day, hour and minute), "
               "and the subject and text in AIP GEN 2.2 abbreviations. Decoded: B is 14 November 2026 0100 UTC, 0900 WST; C is 15 "
               "November 0930 UTC, 1730 WST. A timeline shows that a planned arrival at 1600 WST on the 15th meets a closed runway.",
               height=480, prefix="nta")
    c.add(text(20, 28, "Worked example: an invented NOTAM for Geraldton", 14, "start", "fg", weight=700))
    c.add(rect(20, 42, 300, 164, "surface-2", "line-strong", SECOND, rx=8))
    rows = [("[identifier and series]", "fg-faint", ["identifier and series:", "to refer to it and cancel it"]),
            ("YGEL", "fg", ["location: ICAO code", "(YGEL Geraldton)"]),
            ("B 2611140100", "brand", ["B: in force from (UTC)"]),
            ("C 2611150930", "brand", ["C: ends (UTC); may be", "PERM or carry EST"]),
            ("RWY 03/21 CLSD DUE WIP", "fg", ["subject and text: AIP GEN 2.2", "abbreviations"])]
    for i, (code, tone, lab) in enumerate(rows):
        y = 70 + i * 31
        c.add(num(36, y, code, 14 if tone != "fg-faint" else 12, "start", tone, weight=700 if tone != "fg-faint" else None))
        c.add(line(300, y - 5, 336, y - 5, "fg-muted", THIN))
        c.add(circle(300, y - 5, 2.5, "fg-muted", None))
        c.add(multiline(344, y - 1 if len(lab) == 1 else y - 7, lab, 11.5, "start", "fg" if tone != "fg-faint" else "fg-muted", 1.15))
    # decode B and C
    def decode(y: float, letter: str, groups: list[str], wst: str) -> str:
        out = text(20, y + 26, letter, 22, "start", "brand", weight=800, cls="num")
        labels = ["year", "month", "day", "time UTC"]
        x = 50
        for g, l in zip(groups, labels):
            w = 54 if len(g) == 2 else 78
            out += rect(x, y + 6, w - 6, 30, "brand-soft", "brand", SECOND, rx=4)
            out += num(x + (w - 6) / 2, y + 27, g, 15, "middle", "brand-fg", weight=700)
            out += text(x + (w - 6) / 2, y + 52, l, 11.5, "middle", "fg-muted")
            x += w
        out += arrow(x + 4, y + 21, x + 40, y + 21, "brand", SECOND)
        out += text(x + 22, y + 12, "+8 h", 11.5, "middle", "brand-fg", weight=700)
        out += rect(x + 46, y + 6, 620 - x - 46, 30, "surface", "brand", MAIN, rx=4)
        out += num(x + 46 + (620 - x - 46) / 2, y + 27, wst, 14, "middle", "fg", weight=700)
        return out
    c.add(decode(220, "B", ["26", "11", "14", "0100"], "0900 WST 14 Nov 2026"))
    c.add(decode(288, "C", ["26", "11", "15", "0930"], "1730 WST 15 Nov 2026"))
    # timeline in WST
    TY = 414
    x0, x1 = 40, 600
    hours = 72  # 13 Nov 0000 to 16 Nov 0000 WST

    def hx(day: int, hhmm: int) -> float:
        h = (day - 13) * 24 + hhmm // 100 + (hhmm % 100) / 60
        return x0 + (x1 - x0) * h / hours
    c.add(text(20, 372, "In local time (WST)", 13, "start", "fg", weight=700))
    c.add(line(x0, TY, x1, TY, "fg-muted", SECOND))
    for d in (13, 14, 15, 16):
        X = hx(d, 0)
        c.add(line(X, TY - 6, X, TY + 6, "fg-muted", THIN))
        if d < 16:
            c.add(text(X + (x1 - x0) / 6, TY + 22, f"{d} Nov", 11.5, "middle", "fg-muted"))
    c.add(rect(hx(14, 900), TY - 12, hx(15, 1730) - hx(14, 900), 24, "bad-soft", "bad", SECOND, rx=4))
    c.add(text((hx(14, 900) + hx(15, 1730)) / 2, TY + 4, "runway 03/21 closed", 12, "middle", "bad-fg", weight=700))
    c.add(line(hx(15, 1600), TY - 26, hx(15, 1600), TY + 12, "fg", MAIN))
    c.add(text(hx(15, 1600) + 8, TY - 32, "arrive 1600 WST on the 15th", 11.5, "end", "fg", weight=600))
    c.add(text(20, 468, "Every NOTAM time is UTC: convert the whole date-time group, not just the hours.", 11.5, "start", "fg-muted"))
    return c


# ================================================================ 2.2 Licences and privileges
@chart
def operations_classification() -> Canvas:
    c = Canvas("Classification of operations", "Four classes of operation stacked by how much the people on board rely on someone else "
               "for their safety. Private operations under CASR Part 91 only: your own purposes, equal cost sharing, flying yourself on "
               "business without hire or reward; a PPL may be pilot in command. Flight training under Parts 141 and 142: instructors, "
               "students under supervision. Aerial work under Part 138: survey, photography, agriculture, towing, dropping; a CPL. Air "
               "transport under Parts 119, 121, 133 and 135: passengers or cargo for hire or reward; a CPL or ATPL under an air operator's "
               "certificate. The one-question test: is anyone paying for the flight beyond equal cost sharing? If yes, it is not a "
               "private operation and a PPL is not enough.", height=440, prefix="opc")
    c.add(text(20, 28, "Which class is this flight, and is a PPL enough?", 14, "start", "fg", weight=700))
    rows = [("Air transport", "Parts 119, 121, 133, 135", "passengers or cargo for hire or reward:", "charter and airline", "CPL or ATPL, under an AOC", "fg"),
            ("Aerial work", "Part 138", "the aeroplane is the tool: survey,", "photography, agriculture, towing, dropping", "CPL (PPL only for specified non-commercial work)", "fg"),
            ("Flight training", "Parts 141 and 142", "dual and solo training flights,", "flight reviews", "instructors; students under supervision", "fg"),
            ("Private operations", "Part 91 only", "your own purposes, equal cost sharing,", "flying yourself on business, unpaid", "PPL (RPL within its narrower privileges)", "brand")]
    for i, (name, part, l1, l2, pic, tone) in enumerate(rows):
        y = 44 + i * 82
        c.add(rect(58, y, 562, 74, SOFT[tone], EDGE[tone], MAIN if tone == "brand" else SECOND, rx=8))
        c.add(text(72, y + 24, name, 14, "start", FG[tone], weight=700))
        c.add(text(72, y + 42, part, 11.5, "start", FG[tone] if tone == "brand" else "fg-muted"))
        c.add(multiline(250, y + 22, [l1, l2], 11.5, "start", "fg", 1.3))
        c.add(text(250, y + 62, "PIC: " + pic, 11.5, "start", FG[tone] if tone == "brand" else "fg-muted", weight=700))
    c.add(arrow(34, 360, 34, 50, "fg-muted", SECOND))
    c.add(text(26, 205, "people on board rely more on someone else", 11.5, "middle", "fg-muted", rotate=-90))
    # the test
    c.add(rect(58, 378, 562, 52, "warn-soft", "warn", MAIN, rx=10))
    c.add(text(72, 400, "The test: is anyone paying for the flight beyond equal cost sharing?", 13, "start", "warn-fg", weight=700))
    c.add(text(72, 418, "Yes: not a private operation, and a PPL is not enough.", 12, "start", "warn-fg"))
    return c
