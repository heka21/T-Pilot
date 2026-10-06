"""RFRC (flight rules and air law) diagrams. Every number, code and document name comes from the notes in
content/notes/RFRC/; where a note hedges, the diagram hedges."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, arc_path, arrow, badge, circle, fmt, group, line, multiline, num, path,
                                plane_side, plane_top, polygon, polyline, rect, runway, smooth_path, text)

SOFT = {"brand": "brand-soft", "ok": "ok-soft", "warn": "warn-soft", "bad": "bad-soft", "info": "info-soft", "sky": "sky-soft", "fg": "surface-2"}
FG = {"brand": "brand-fg", "ok": "ok-fg", "warn": "warn-fg", "bad": "bad-fg", "info": "info-fg", "sky": "sky-fg", "fg": "fg"}
EDGE = {"brand": "brand", "ok": "ok", "warn": "warn", "bad": "bad", "info": "info", "sky": "sky-fg", "fg": "line-strong"}


def card(x: float, y: float, w: float, h: float, title: str | None, lines: list[str], tone: str = "fg", size: float = 12,
         title_size: float = 14, leading: float = 1.35, pad: float = 12, anchor: str = "start", stroke: bool = True) -> str:
    """Rounded panel with a bold title and body lines in the tone's ink."""
    out = rect(x, y, w, h, SOFT[tone], EDGE[tone] if stroke else None, SECOND, rx=8)
    tx = x + pad if anchor == "start" else x + w / 2
    yy = y + pad + title_size * 0.85
    if title:
        out += text(tx, yy, title, title_size, anchor, FG[tone], weight=700)
        yy += title_size * 0.5 + size * 1.05
    else:
        yy = y + pad + size * 0.9
    out += multiline(tx, yy, lines, size, anchor, FG[tone] if tone != "fg" else "fg-muted", leading)
    return out


def darrow(x1: float, y1: float, x2: float, y2: float, color: str = "brand", width: float = MAIN) -> str:
    """Double-headed dimension arrow drawn as two arrows from the midpoint."""
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    return arrow(mx, my, x1, y1, color, width) + arrow(mx, my, x2, y2, color, width)


def pill(x: float, y: float, w: float, h: float, s: str, tone: str = "brand", size: float = 13, solid: bool = False) -> str:
    """Rounded label of fixed width centred on (x, y)."""
    fill = EDGE[tone] if solid else SOFT[tone]
    ink = "surface" if solid else FG[tone]
    return rect(x - w / 2, y - h / 2, w, h, fill, None if solid else EDGE[tone], THIN, rx=h / 2) + text(x, y + size * 0.36, s, size, "middle", ink, weight=700)


# ================================================================ 2.1 Documentation
@chart
def aviation_law_hierarchy() -> Canvas:
    c = Canvas("Where the rules live", "A stepped stack of the aviation documents: the Civil Aviation Act at the top, then the regulations "
               "(CASR 1998 and CAR 1988), the Manuals of Standards made under CASR Parts, the remaining Civil Aviation Orders, then the "
               "operational information published by Airservices (AIP, ERSA, DAP, charts and NOTAM), and at the base the guidance "
               "material (Advisory Circulars and the Visual Flight Rules Guide), which is not law.", height=470, prefix="alh")
    rows = [
        ("brand", "Civil Aviation Act 1988", "the Act of Parliament: creates CASA and the framework", "LAW"),
        ("brand", "Regulations: CASR 1998 and CAR 1988", "CASR: Part 61 licences, 67 medicals, 91 rules; CAR: Part 4A MR", "LAW"),
        ("brand", "Manuals of Standards (MOS)", "detail made under a CASR Part: Part 61 MOS (this syllabus), Part 91 MOS", "LAW"),
        ("brand", "Civil Aviation Orders (CAO)", "remaining orders made under the CAR, mostly replaced by the CASR", "LAW"),
        ("sky", "AIP · ERSA · DAP · charts · NOTAM", "the operational information: how, where and when, today", "INFO"),
        ("fg", "Advisory Circulars and the VFRG", "guidance, not law; the VFRG is permitted in the RPL and PPL exams", "GUIDE"),
    ]
    top, rh, gap = 66, 52, 8
    c.add(text(320, 30, "From the Act down to the guidance you carry", 16, "middle", "fg", weight=700))
    for i, (tone, name, what, tag) in enumerate(rows):
        w = 380 + i * 36
        x = 320 - w / 2
        y = top + i * (rh + gap)
        c.add(rect(x, y, w, rh, SOFT[tone], EDGE[tone], SECOND if i < 4 else SECOND, rx=6, dash=DASH if tone == "fg" else None))
        c.add(text(x + 14, y + 21, name, 14, "start", FG[tone], weight=700))
        c.add(text(x + 14, y + 40, what, 11.5, "start", FG[tone] if tone != "fg" else "fg-muted"))
    # side rails: law, operational information, guidance
    c.add(line(26, top, 26, top + 4 * (rh + gap) - gap, "brand", MAIN))
    c.add(text(16, top + 2 * (rh + gap) - gap / 2, "LAW", 13, "middle", "brand-fg", weight=700, rotate=-90))
    c.add(line(26, top + 4 * (rh + gap), 26, top + 5 * (rh + gap) - gap, "sky-fg", MAIN))
    c.add(text(16, top + 4.5 * (rh + gap) - gap / 2, "INFO", 12, "middle", "sky-fg", weight=700, rotate=-90))
    c.add(line(26, top + 5 * (rh + gap), 26, top + 6 * (rh + gap) - gap, "fg-faint", MAIN, dash=DASH))
    c.add(text(16, top + 5.5 * (rh + gap) - gap / 2, "GUIDE", 11, "middle", "fg-muted", weight=700, rotate=-90))
    y = top + 6 * (rh + gap) + 6
    c.add(text(320, y + 6, "Legislation: Federal Register of Legislation.  AIP, ERSA, charts, NOTAM: Airservices Australia.", 11.5, "middle", "fg-muted"))
    c.add(text(320, y + 24, "The VFRG summarises the law in plain words; it does not replace it.", 11.5, "middle", "fg-faint"))
    return c


@chart
def where_to_find_it() -> Canvas:
    c = Canvas("Which document answers which question", "Common pre-flight questions matched to the document that answers them: VMC minima "
               "and fuel rules in the Part 91 MOS, summarised in the VFRG; aerodrome data, PRD areas and emergency procedures in ERSA; "
               "licence privileges in CASR Part 61; medicals in CASR Part 67; the aircraft's serviceability in the maintenance release; "
               "temporary changes in NOTAM; airspace boundaries on the VTC, VNC and ERC.", height=452, prefix="wtf")
    rows = [
        ("What are the VMC minima? What fuel reserve?", "Part 91 MOS", "summarised in the VFRG"),
        ("What does my licence let me do?", "CASR Part 61", "and the Part 61 MOS"),
        ("What medical do I need?", "CASR Part 67", ""),
        ("What are the details of this aerodrome?", "ERSA", "aerodrome entry"),
        ("PRD area details? Emergency procedures?", "ERSA", "PRD section, EMERG pages"),
        ("Where does controlled airspace start?", "VTC · VNC · ERC", "the charts"),
        ("Has anything changed since it was printed?", "NOTAM", "temporary or urgent changes"),
        ("Is this aircraft in date and serviceable?", "Maintenance release", "travels with the aircraft"),
    ]
    c.add(text(28, 30, "The question", 13, "start", "fg-muted", weight=700))
    c.add(text(612, 30, "Look in", 13, "end", "fg-muted", weight=700))
    y0, rh = 46, 48
    for i, (q, doc, sub) in enumerate(rows):
        y = y0 + i * rh
        c.add(rect(20, y, 364, rh - 10, "surface-2", None, rx=8))
        c.add(text(34, y + (rh - 10) / 2 + 5, q, 13, "start", "fg"))
        c.add(arrow(390, y + (rh - 10) / 2, 426, y + (rh - 10) / 2, "fg-muted", SECOND))
        tone = "brand" if doc in ("Part 91 MOS", "CASR Part 61", "CASR Part 67") else "sky" if doc in ("ERSA", "VTC · VNC · ERC", "NOTAM") else "ok"
        c.add(rect(432, y, 188, rh - 10, SOFT[tone], EDGE[tone], THIN, rx=8))
        if sub:
            c.add(text(444, y + 16, doc, 13.5, "start", FG[tone], weight=700))
            c.add(text(444, y + 31, sub, 11, "start", FG[tone]))
        else:
            c.add(text(444, y + (rh - 10) / 2 + 5, doc, 13.5, "start", FG[tone], weight=700))
    yb = y0 + len(rows) * rh + 10
    for x, tone, s in ((28, "brand", "legislation"), (150, "sky", "Airservices publications"), (350, "ok", "the aircraft's own document")):
        c.add(rect(x, yb - 9, 12, 12, SOFT[tone], EDGE[tone], THIN, rx=3))
        c.add(text(x + 18, yb + 1, s, 11.5, "start", "fg-muted"))
    return c


# ================================================================ 2.2 Licence privileges and limitations (RPL)
@chart
def rpl_privileges_map() -> Canvas:
    c = Canvas("What the RPL allows and what each endorsement adds", "On the left, the bare recreational pilot licence (aeroplane): "
               "single-engine, single-pilot aeroplane of not more than 1,500 kg maximum take-off weight, day VFR only, private or "
               "training flights, within 25 nm of the departure aerodrome, non-controlled aerodromes and Class G airspace, below "
               "10,000 ft, passengers allowed. On the right, the endorsements that lift each limit: recreational navigation, "
               "controlled aerodrome, controlled airspace, flight above 10,000 ft, design features and aerobatics.", height=490, prefix="rpm")
    c.add(text(28, 30, "The bare RPL(A)", 16, "start", "brand-fg", weight=700))
    c.add(text(612, 30, "Add an endorsement to lift a limit", 14, "end", "fg-muted", weight=700))
    # left card: the limits, each on its own row so the endorsements can link to it
    L, W = 20, 270
    c.add(rect(L, 44, W, 428, "brand-soft", "brand", MAIN, rx=10))
    limits = [
        ("Within 25 nm", "of the departure aerodrome", "Recreational navigation", "fly beyond 25 nm, cross-country"),
        ("Non-controlled aerodromes", "no towered aerodrome", "Controlled aerodrome", "operate at towered aerodromes"),
        ("Class G airspace only", "no controlled airspace", "Controlled airspace", "enter controlled airspace"),
        ("Below 10,000 ft", "", "Flight above 10,000 ft", "if the aircraft and oxygen rules allow"),
        ("Basic single-engine types", "no special design features", "Design feature", "tailwheel, retractable gear, manual prop"),
        ("No aerobatics", "", "Aerobatic", "aerobatic flight"),
    ]
    y0, rh = 62, 46
    for i, (lim, sub, endo, adds) in enumerate(limits):
        y = y0 + i * rh
        c.add(rect(L + 10, y, W - 20, rh - 8, "surface", None, rx=6))
        c.add(text(L + 22, y + (16 if sub else 24), lim, 13, "start", "brand-fg", weight=700))
        if sub:
            c.add(text(L + 22, y + 31, sub, 11, "start", "fg-muted"))
        yc = y + (rh - 8) / 2
        c.add(arrow(L + W + 4, yc, 352, yc, "ok", SECOND))
        c.add(rect(356, y, 264, rh - 8, "ok-soft", "ok", THIN, rx=6))
        c.add(text(368, y + 16, "+ " + endo, 13, "start", "ok-fg", weight=700))
        c.add(text(368, y + 31, adds, 11, "start", "ok-fg"))
    # what stays the same whatever endorsements
    yb = y0 + len(limits) * rh + 4
    c.add(line(L + 16, yb - 4, L + W - 16, yb - 4, "brand", THIN, dash=DASH))
    c.add(text(L + 16, yb + 14, "Always, with any endorsement:", 12, "start", "brand-fg", weight=700))
    c.add(multiline(L + 16, yb + 34, ["single-engine aeroplane, single-pilot", "MTOW not more than 1,500 kg", "day VFR only: no night, no IMC",
                                       "private operations or flight training only", "passengers allowed, with 3 take-offs and", "3 landings in the previous 90 days"], 12, "start", "brand-fg", 1.4))
    c.add(rect(356, yb - 4, 264, 134, "surface-2", None, rx=8))
    c.add(text(368, yb + 16, "Lifted only by another licence", 12.5, "start", "fg", weight=700))
    c.add(multiline(368, yb + 36, ["PPL: removes the weight, distance", "and airspace limits", "CPL: allows commercial operations"], 11.5, "start", "fg-muted", 1.35))
    c.add(text(368, yb + 98, "Design features also include", 11, "start", "fg-faint"))
    c.add(text(368, yb + 113, "pressurisation and floats.", 11, "start", "fg-faint"))
    return c


@chart
def rpl_recency_timeline() -> Canvas:
    c = Canvas("How far back the RPL currency rules look", "Two look-back windows ending today. To carry a passenger you need at least 3 "
               "take-offs and 3 landings in the previous 90 days in the same category of aircraft. To fly as pilot in command at all you "
               "need an aeroplane flight review within the last 24 months, valid to the end of the 24th month after it was done.",
               height=340, prefix="rrt")

    def window(y: float, question: str, title: str, span: str, start: str, tone: str) -> str:
        out = text(28, y - 30, question, 15, "start", "fg", weight=700)
        out += text(28, y - 12, title, 12, "start", "fg-muted")
        out += rect(40, y, 520, 36, SOFT[tone], EDGE[tone], SECOND, rx=6)
        out += num(56, y + 23, span, 13, "start", FG[tone], weight=700)
        out += line(560, y - 8, 560, y + 46, "fg", MAIN)
        out += text(560, y + 62, "today", 12, "middle", "fg", weight=700)
        out += line(40, y + 40, 40, y + 46, "fg-muted", THIN)
        out += num(40, y + 62, start, 11, "start", "fg-muted")
        return out

    y = 76
    c.add(window(y, "Carry a passenger?", "at least 3 take-offs and 3 landings, same category of aircraft", "previous 90 days", "90 days ago", "brand"))
    for k, x in enumerate((330, 410, 490)):
        c.add(group(plane_side(0, 0, 0.4, "brand-fg", -6, "surface", gear=True), transform=f"translate({x + 8} {y + 17})"))
        c.add(num(x - 26, y + 23, f"{k + 1}", 12, "end", "brand-fg", weight=700))
    c.add(text(28, y + 90, "Not enough? Fly solo circuits first, then take the passenger.", 12, "start", "fg-muted"))
    y = 236
    c.add(window(y, "Fly as pilot in command at all?", "an aeroplane flight review with an instructor", "flight review valid to the end of the 24th month",
                 "24 months ago", "ok"))
    c.add(circle(520, y + 18, 10, "ok", "surface", 1.5))
    c.add(path(f"M{515} {y + 18} l4 4 l7 -8", "surface", None, 2))
    c.add(text(28, y + 90, "No current flight review: you cannot fly as pilot in command, passengers or not.", 12, "start", "fg-muted"))
    return c


@chart
def rpl_medical_certificates() -> Canvas:
    c = Canvas("The three medicals an RPL holder can use", "Three cards compared. Class 2: issued by a DAME with CASA, the standard private "
               "pilot medical with no extra operational limits. Basic Class 2: any GP to the commercial driver standard; private, day VFR, "
               "below 10,000 ft, piston aircraft up to 8,618 kg, no more than 5 passengers. RAMPC: any GP to the private driver standard; "
               "single-engine piston up to 1,500 kg, day VFR, below 10,000 ft, no more than 1 passenger, no aerobatics, private operations.",
               height=420, prefix="rmc")
    cards = [
        ("Class 2", "issued by a DAME, with CASA", "info", ["The standard private pilot", "medical: no extra", "operational limits.", "",
                                                             "Valid 4 years under 40,", "2 years over 40", "(check current periods)"], None),
        ("Basic Class 2", "any GP · commercial driver std", "warn", ["private operations", "day VFR", "below 10,000 ft", "piston aircraft", "up to 8,618 kg"], 5),
        ("RAMPC", "any GP · private driver standard", "brand", ["single-engine piston", "up to 1,500 kg", "day VFR", "below 10,000 ft", "private operations", "no aerobatics"], 1),
    ]
    W, G = 192, 12
    for i, (name, who, tone, lines, pax) in enumerate(cards):
        x = 20 + i * (W + G)
        c.add(rect(x, 20, W, 336, SOFT[tone], EDGE[tone], MAIN if tone == "brand" else SECOND, rx=10))
        c.add(text(x + W / 2, 48, name, 17, "middle", FG[tone], weight=700))
        c.add(text(x + W / 2, 68, who, 11, "middle", FG[tone]))
        c.add(line(x + 14, 80, x + W - 14, 80, EDGE[tone], THIN))
        c.add(multiline(x + 14, 102, lines, 12, "start", FG[tone], 1.45))
        # passengers row
        c.add(rect(x + 10, 236, W - 20, 108, "surface", None, rx=8))
        c.add(text(x + W / 2, 256, "Passengers", 12, "middle", "fg-muted", weight=700))
        if pax is None:
            c.add(text(x + W / 2, 292, "no extra limit", 13, "middle", "fg", weight=700))
            c.add(text(x + W / 2, 312, "(licence, aircraft and", 11, "middle", "fg-muted"))
            c.add(text(x + W / 2, 326, "recency rules apply)", 11, "middle", "fg-muted"))
        else:
            n = pax
            sx = x + W / 2 - (min(n, 5) * 26) / 2 + 13
            for k in range(n):
                c.add(seat(sx + k * 26, 288, EDGE[tone]))
            c.add(num(x + W / 2, 332, f"no more than {n}", 13, "middle", FG[tone], weight=700))
    c.add(text(320, 380, "Any certificate: do not fly if you know or suspect you are temporarily unfit,", 12, "middle", "fg-muted"))
    c.add(text(320, 398, "and tell CASA or a DAME of a medically significant condition (CASR 67.265).", 12, "middle", "fg-muted"))
    return c


def seat(x: float, y: float, color: str) -> str:
    """A small person-in-a-seat pictogram centred on (x, y)."""
    return (circle(x, y - 14, 5, color, None) + path(f"M{x - 8} {y + 14} L{x - 8} {y - 2} Q{x - 8} {y - 7} {x - 3} {y - 7} L{x + 3} {y - 7} "
                                                    f"Q{x + 8} {y - 7} {x + 8} {y - 2} L{x + 8} {y + 14} Z", None, color))


# ================================================================ 2.3 Conditions of flight
def cloud(cx: float, cy: float, w: float, h: float, fill: str = "surface-2", stroke: str = "fg-muted") -> str:
    """A flat-bottomed cumulus outline centred on (cx, cy), w wide and h tall."""
    x0, x1, yb = cx - w / 2, cx + w / 2, cy + h / 2
    d = (f"M{fmt(x0 + h * 0.3)} {fmt(yb)} A{fmt(h * 0.3)} {fmt(h * 0.3)} 0 0 1 {fmt(x0 + w * 0.18)} {fmt(cy - h * 0.05)} "
         f"A{fmt(h * 0.45)} {fmt(h * 0.45)} 0 0 1 {fmt(cx - w * 0.02)} {fmt(cy - h * 0.3)} "
         f"A{fmt(h * 0.5)} {fmt(h * 0.5)} 0 0 1 {fmt(x1 - w * 0.2)} {fmt(cy - h * 0.12)} "
         f"A{fmt(h * 0.35)} {fmt(h * 0.35)} 0 0 1 {fmt(x1 - h * 0.25)} {fmt(yb)} Z")
    return path(d, stroke, fill, SECOND)


@chart
def vmc_minima_by_airspace() -> Canvas:
    c = Canvas("VMC minima below 10,000 ft", "Side view in two layers. Above 3,000 ft AMSL or 1,000 ft AGL, whichever is higher, and in Class C, "
               "D and E: keep 1,500 m horizontally and 1,000 ft vertically from cloud, shown as a dashed keep-out box around the cloud. "
               "In Class G at or below that height: stay clear of cloud and in sight of the ground or water. Flight visibility is "
               "5,000 m in every case. Above 10,000 ft the visibility requirement increases to 8 km. Not to scale.", height=470, prefix="vmc")
    LINE_Y, GROUND = 262, 392
    c.add(rect(20, 22, 600, 30, "surface-2", None, rx=6))
    c.add(text(320, 42, "Above 10,000 ft the flight visibility requirement increases to 8 km", 12, "middle", "fg-muted", weight=600))
    # upper layer
    c.add(rect(20, 60, 600, LINE_Y - 60, "sky-soft", None, fill_opacity=0.5))
    c.add(text(32, 82, "Class C, D and E", 14, "start", "fg", weight=700))
    c.add(text(32, 99, "and Class G above the line", 12, "start", "fg-muted"))
    # cloud with its keep-out box
    cx, cy, cw, ch = 440, 160, 120, 50
    bx0, bx1, by0, by1 = cx - cw / 2 - 90, cx + cw / 2 + 50, cy - ch / 2 - 46, cy + ch / 2 + 46
    c.add(rect(bx0, by0, bx1 - bx0, by1 - by0, "brand-soft", "brand", SECOND, rx=6, dash="6 4", fill_opacity=0.6))
    c.add(cloud(cx, cy, cw, ch))
    c.add(text(bx0 + 8, by0 + 16, "keep out of this box", 11, "start", "brand-fg", weight=700))
    # horizontal distance: plane to the left of the box
    c.add(plane_side(170, cy + 8, 0.42, "fg"))
    c.add(darrow(bx0, cy + ch / 2 - 6, cx - cw / 2 + 10, cy + ch / 2 - 6, "brand"))
    c.add(num((bx0 + cx - cw / 2 + 10) / 2, cy + ch / 2 + 12, "1,500 m", 13, "middle", "brand", weight=700))
    c.add(text((bx0 + cx - cw / 2 + 10) / 2, cy + ch / 2 + 27, "horizontally", 11, "middle", "brand-fg"))
    # vertical distances
    vx = cx + cw / 2 + 24
    c.add(darrow(vx, cy - ch / 2 + 6, vx, by0, "brand"))
    c.add(darrow(vx, cy + ch / 2, vx, by1, "brand"))
    c.add(num(bx1 + 8, by0 + 30, "1,000 ft", 13, "start", "brand", weight=700))
    c.add(text(bx1 + 8, by0 + 45, "vertically", 11, "start", "brand-fg"))
    c.add(num(bx1 + 8, by1 - 18, "1,000 ft", 13, "start", "brand", weight=700))
    c.add(text(bx1 + 8, by1 - 3, "vertically", 11, "start", "brand-fg"))
    # dividing line
    c.add(line(20, LINE_Y, 620, LINE_Y, "fg", SECOND, dash="8 5"))
    c.add(rect(150, LINE_Y - 11, 340, 22, "surface", None, rx=11))
    c.add(num(320, LINE_Y + 4, "3,000 ft AMSL or 1,000 ft AGL, whichever is higher", 11.5, "middle", "fg", weight=600))
    # lower layer: Class G at or below the line
    c.add(text(32, LINE_Y + 26, "Class G at or below the line", 14, "start", "fg", weight=700))
    c.add(cloud(470, LINE_Y + 38, 120, 34))
    c.add(plane_side(410, 334, 0.42, "ok"))
    c.add(text(480, 338, "clear of cloud", 13, "start", "ok-fg", weight=700))
    c.add(line(400, 344, 340, GROUND - 4, "ok", SECOND, dash=DASH))
    c.add(text(330, 362, "in sight of ground or water", 12, "end", "ok-fg", weight=600))
    # ground
    c.add(path(f"M20 {GROUND} Q160 {GROUND - 8} 300 {GROUND} T620 {GROUND} L620 {GROUND + 14} L20 {GROUND + 14} Z", None, "surface-2"))
    c.add(line(20, GROUND, 620, GROUND, "fg-muted", SECOND))
    # visibility, common to all three
    c.add(rect(20, 418, 600, 40, "brand-soft", None, rx=8))
    c.add(text(36, 443, "Flight visibility in all three cases:", 13, "start", "brand-fg", weight=600))
    c.add(num(296, 443, "5,000 m", 15, "start", "brand", weight=700))
    c.add(text(604, 443, "not to scale", 11, "end", "fg-faint"))
    return c


@chart
def vfr_cruising_levels() -> Canvas:
    c = Canvas("VFR cruising levels above 5,000 ft", "A compass rose split in half by magnetic track. Tracks 000 to 179 degrees, the eastern half: "
               "odd thousands plus 500 ft, that is 5,500, 7,500 and 9,500 ft. Tracks 180 to 359 degrees, the western half: even thousands "
               "plus 500 ft, that is 6,500 and 8,500 ft. Below 5,000 ft any altitude may be flown, subject to minimum heights.",
               height=476, prefix="vcl")
    cx, cy, r = 320, 214, 168
    c.add(path(f"M{cx} {cy - r} A{r} {r} 0 0 1 {cx} {cy + r} Z", None, "brand-soft"))
    c.add(path(f"M{cx} {cy - r} A{r} {r} 0 0 0 {cx} {cy + r} Z", None, "info-soft"))
    c.add(circle(cx, cy, r, None, "fg-muted", SECOND))
    c.add(line(cx, cy - r - 10, cx, cy + r + 10, "fg", MAIN))
    for a in range(0, 360, 10):
        rad = math.radians(a - 90)
        l = 10 if a % 30 == 0 else 5
        c.add(line(cx + r * math.cos(rad), cy + r * math.sin(rad), cx + (r - l) * math.cos(rad), cy + (r - l) * math.sin(rad), "fg-muted", THIN))
    for a, s in ((0, "000°"), (90, "090°"), (180, "180°"), (270, "270°")):
        rad = math.radians(a - 90)
        x, y = cx + (r + 22) * math.cos(rad), cy + (r + 22) * math.sin(rad) + 4
        if a in (0, 180):
            x += 30
            y += 0 if a == 0 else 2
        c.add(num(x, y, s, 12, "middle", "fg-muted", weight=600))
    c.add(text(cx - 26, cy - r - 12, "N", 13, "middle", "fg", weight=700))
    c.add(text(cx - 26, cy + r + 18, "S", 13, "middle", "fg", weight=700))

    def stack(x: float, levels: list[str], tone: str) -> str:
        out = ""
        top = cy - len(levels) * 18
        for i, lv in enumerate(levels):
            out += pill(x, top + i * 36 + 18, 96, 28, lv, tone, 15, solid=False)
        return out

    c.add(text(cx + 76, cy - 110, "track 000°–179°", 13, "middle", "brand-fg", weight=700))
    c.add(text(cx + 76, cy - 92, "odd thousands + 500", 11.5, "middle", "brand-fg"))
    c.add(stack(cx + 76, ["9,500", "7,500", "5,500"], "brand"))
    c.add(text(cx - 76, cy - 110, "track 180°–359°", 13, "middle", "info-fg", weight=700))
    c.add(text(cx - 76, cy - 92, "even thousands + 500", 11.5, "middle", "info-fg"))
    c.add(stack(cx - 76, ["8,500", "6,500"], "info"))
    c.add(text(cx + 76, cy + 86, "e.g. track 090°", 11, "middle", "brand-fg"))
    c.add(text(cx - 76, cy + 86, "e.g. track 270°", 11, "middle", "info-fg"))
    c.add(text(cx + 76, cy + 102, "fly 5,500 or 7,500", 11, "middle", "brand-fg"))
    c.add(text(cx - 76, cy + 102, "fly 6,500 or 8,500", 11, "middle", "info-fg"))
    c.add(text(28, 30, "Magnetic track", 13, "start", "fg-muted", weight=700))
    c.add(text(28, 446, "Applies to VFR flights above 5,000 ft. Below 5,000 ft any altitude may be flown,", 12, "start", "fg-muted"))
    c.add(text(28, 463, "subject to the minimum heights and good practice.", 12, "start", "fg-muted"))
    return c


@chart
def right_of_way_rules() -> Canvas:
    c = Canvas("Who gives way", "Four plan and side views. Converging: the aircraft that has the other on its right gives way. Head-on: both "
               "alter heading to the right. Overtaking: the aircraft being overtaken has right of way; the overtaking aircraft alters to "
               "the right and keeps clear. Landing: of two aircraft approaching to land, the lower has right of way but must not cut in "
               "front of an aircraft on final. Below: power-driven aircraft give way to airships, gliders, balloons and aircraft towing or "
               "carrying a sling load; an aircraft in distress has right of way over everything.", height=556, prefix="row")
    PW, PH = 296, 204

    def panel(x: float, y: float, title: str, rule: str) -> str:
        return rect(x, y, PW, PH, "surface-2", None, rx=10) + text(x + 14, y + 24, title, 15, "start", "fg", weight=700) + \
            text(x + 14, y + 42, rule, 11.5, "start", "fg-muted")

    # converging
    x, y = 16, 16
    c.add(panel(x, y, "Converging", "the one with the other on its right gives way"))
    c.add(plane_top(x + 90, y + 152, 0.36, 0, "warn", "warn-soft"))
    c.add(plane_top(x + 222, y + 92, 0.36, 270, "ok", "ok-soft"))
    c.add(line(x + 90, y + 136, x + 90, y + 104, "fg-faint", THIN, dash=DASH))
    c.add(line(x + 212, y + 92, x + 112, y + 92, "fg-faint", THIN, dash=DASH))
    c.add(path(f"M{x + 98} {y + 136} Q{x + 140} {y + 120} {x + 150} {y + 124}", "warn", None, MAIN, arrow_end=True))
    c.add(text(x + 112, y + 176, "gives way: turn right,", 12, "start", "warn-fg", weight=700))
    c.add(text(x + 112, y + 191, "pass behind", 12, "start", "warn-fg", weight=700))
    c.add(text(x + 236, y + 130, "holds", 12, "middle", "ok-fg", weight=700))
    c.add(text(x + 236, y + 145, "course", 12, "middle", "ok-fg", weight=700))
    # head-on
    x, y = 328, 16
    c.add(panel(x, y, "Head-on", "both alter heading to the right"))
    c.add(plane_top(x + 68, y + 118, 0.36, 90, "warn", "warn-soft"))
    c.add(plane_top(x + 228, y + 118, 0.36, 270, "warn", "warn-soft"))
    c.add(path(f"M{x + 84} {y + 124} Q{x + 120} {y + 128} {x + 140} {y + 152}", "warn", None, MAIN, arrow_end=True))
    c.add(path(f"M{x + 212} {y + 112} Q{x + 176} {y + 108} {x + 156} {y + 84}", "warn", None, MAIN, arrow_end=True))
    c.add(text(x + 148, y + 186, "each turns right, away from the other", 12, "middle", "warn-fg", weight=700))
    # overtaking
    x, y = 16, 232
    c.add(panel(x, y, "Overtaking", "the one being overtaken has right of way"))
    c.add(plane_top(x + 210, y + 100, 0.36, 90, "ok", "ok-soft"))
    c.add(plane_top(x + 68, y + 100, 0.36, 90, "warn", "warn-soft"))
    c.add(path(f"M{x + 84} {y + 106} Q{x + 120} {y + 150} {x + 220} {y + 150} L{x + 270} {y + 150}", "warn", None, MAIN, arrow_end=True))
    c.add(text(x + 14, y + 178, "overtaker alters right and keeps", 12, "start", "warn-fg", weight=700))
    c.add(text(x + 14, y + 193, "clear until well past", 12, "start", "warn-fg", weight=700))
    c.add(text(x + 236, y + 76, "holds course", 12, "middle", "ok-fg", weight=700))
    # landing
    x, y = 328, 232
    c.add(panel(x, y, "Approaching to land", "the lower one has right of way"))
    c.add(rect(x + 196, y + 176, 88, 8, "fg-muted", None, rx=1))
    c.add(text(x + 240, y + 198, "runway", 11, "middle", "fg-muted"))
    c.add(line(x + 92, y + 98, x + 198, y + 176, "fg-faint", THIN, dash=DASH))
    c.add(line(x + 168, y + 150, x + 198, y + 176, "fg-faint", THIN, dash=DASH))
    c.add(plane_side(x + 78, y + 88, 0.34, "warn", pitch=-30, fill="warn-soft"))
    c.add(plane_side(x + 156, y + 138, 0.34, "ok", pitch=-30, fill="ok-soft"))
    c.add(text(x + 112, y + 74, "higher: gives way", 12, "start", "warn-fg", weight=700))
    c.add(text(x + 14, y + 150, "lower: has", 12, "start", "ok-fg", weight=700))
    c.add(text(x + 14, y + 165, "right of way", 12, "start", "ok-fg", weight=700))
    c.add(text(x + 14, y + 194, "but never cut in on final", 11.5, "start", "bad-fg", weight=600))
    # who gives way to whom
    y = 452
    c.add(rect(16, y, 608, 92, "brand-soft", None, rx=10))
    c.add(text(32, y + 24, "By type", 14, "start", "brand-fg", weight=700))
    c.add(text(32, y + 46, "Power-driven heavier-than-air aircraft give way to", 12.5, "start", "brand-fg", weight=600))
    c.add(text(32, y + 64, "airships, gliders and balloons, and to aircraft", 12.5, "start", "brand-fg"))
    c.add(text(32, y + 81, "towing or carrying a sling load", 12.5, "start", "brand-fg"))
    c.add(rect(470, y + 12, 142, 68, "bad-soft", "bad", THIN, rx=8))
    c.add(multiline(541, y + 34, ["An aircraft in", "distress has right", "of way over all"], 12, "middle", "bad-fg", 1.3))
    return c


@chart
def minimum_heights() -> Canvas:
    c = Canvas("Minimum heights", "Side view. Over a populous area or a public gathering, not below 1,000 ft above the highest obstacle "
               "within a 600 m radius of the aircraft. Anywhere else, not below 500 ft above the ground or water, and not closer than 500 ft "
               "to any person, vessel, vehicle or structure. Not to scale.", height=440, prefix="mh")
    G = 362
    c.add(line(320, 30, 320, 388, "line-strong", THIN, dash=DASH))
    # ---- left: populous area
    c.add(text(24, 34, "Over a populous area", 15, "start", "fg", weight=700))
    c.add(text(24, 52, "or a public gathering", 12, "start", "fg-muted"))
    for bx, bw, bh in ((40, 30, 50), (76, 24, 70), (172, 30, 56), (208, 26, 64), (240, 36, 46), (282, 26, 34)):
        c.add(rect(bx, G - bh, bw, bh, "surface-2", "fg-muted", THIN))
    tx, th = 130, 120                                   # highest obstacle: a mast
    c.add(rect(tx - 6, G - th, 12, th, "surface-2", "fg", SECOND))
    c.add(line(tx, G - th - 12, tx, G - th, "fg", SECOND))
    c.add(text(tx + 12, G - th + 10, "highest", 11, "start", "fg-muted"))
    c.add(text(tx + 12, G - th + 24, "obstacle", 11, "start", "fg-muted"))
    px, py = 180, 132
    # 600 m radius around the aircraft
    ry = py - 34
    c.add(arrow(px, ry, px - 132, ry, "info", SECOND))
    c.add(arrow(px, ry, px + 132, ry, "info", SECOND))
    c.add(num(px - 66, ry - 8, "600 m", 12, "middle", "info", weight=700))
    c.add(num(px + 66, ry - 8, "600 m", 12, "middle", "info", weight=700))
    c.add(line(px - 132, ry + 6, px - 132, G, "info", THIN, dash=DASH))
    c.add(line(px + 132, ry + 6, px + 132, G, "info", THIN, dash=DASH))
    c.add(plane_side(px, py, 0.5, "brand", fill="brand-soft"))
    # 1,000 ft above the top of the obstacle
    top = G - th - 12
    c.add(line(tx, py + 10, px - 6, py + 10, "brand", THIN, dash=DASH))   # to the main wheels (local y 19.5)
    c.add(darrow(tx, top - 4, tx, py + 12, "brand"))
    c.add(num(tx - 10, (top + py) / 2 + 4, "1,000 ft", 14, "end", "brand", weight=700))
    c.add(text(tx - 10, (top + py) / 2 + 20, "above it", 11, "end", "brand-fg"))
    # ---- right: elsewhere
    c.add(text(340, 34, "Anywhere else", 15, "start", "fg", weight=700))
    c.add(text(340, 52, "open country or water", 12, "start", "fg-muted"))
    qx, qy = 420, 180
    c.add(plane_side(qx, qy, 0.5, "brand", fill="brand-soft"))
    c.add(darrow(qx - 40, qy + 8, qx - 40, G, "brand"))
    c.add(num(qx - 48, (qy + G) / 2 + 4, "500 ft", 14, "end", "brand", weight=700))
    c.add(text(qx - 48, (qy + G) / 2 + 20, "above ground", 11, "end", "brand-fg"))
    c.add(text(qx - 48, (qy + G) / 2 + 34, "or water", 11, "end", "brand-fg"))
    sx = 540
    c.add(path(f"M{sx - 76} {G} A76 76 0 0 1 {sx + 76} {G}", "warn", "warn-soft", SECOND, dash="6 4", fill_opacity=0.6))
    c.add(rect(sx - 12, G - 34, 24, 34, "surface-2", "fg", SECOND))
    c.add(path(f"M{sx - 12} {G - 34} L{sx} {G - 46} L{sx + 12} {G - 34}", "fg", None, SECOND))
    c.add(num(sx, G - 92, "500 ft", 13, "middle", "warn", weight=700))
    c.add(text(sx, G - 108, "no closer than", 11, "middle", "warn-fg"))
    c.add(text(612, G + 22, "any person, vessel, vehicle or structure", 11, "end", "fg-muted"))
    # ground
    c.add(rect(16, G, 608, 10, "surface-2", None))
    c.add(line(16, G, 624, G, "fg-muted", SECOND))
    c.add(text(24, 408, "Exceptions: taking off and landing, CASA-approved operations, a forced landing, avoiding weather or terrain.", 11, "start", "fg-muted"))
    c.add(text(24, 424, "Always high enough to glide clear of a populous area if the engine fails.  Not to scale.", 11, "start", "fg-faint"))
    return c


@chart
def takeoff_separation() -> Canvas:
    c = Canvas("When you may take off behind another aircraft", "Side view of a runway at a non-controlled aerodrome. You may not take off "
               "until the aircraft ahead on the same runway has landed and vacated it, or has taken off and crossed the upwind end or "
               "commenced a turn, or is airborne and far enough ahead of your intended lift-off point: 600 m if both aircraft are under "
               "2,000 kg MTOW, 1,800 m if the runway is longer than 1,800 m. Landing uses the same gaps from your touchdown point.",
               height=460, prefix="tos")
    G = 292
    c.add(rect(30, G, 580, 12, "fg-muted", None, rx=1))
    c.add(text(70, G - 22, "you", 11, "middle", "brand-fg", weight=600))
    c.add(plane_side(70, G - 7.8, 0.4, "brand", fill="brand-soft"))
    lx = 140
    c.add(line(lx, G - 30, lx, G + 50, "brand", SECOND, dash=DASH))
    c.add(text(lx - 8, G + 30, "your intended", 11, "end", "brand-fg", weight=600))
    c.add(text(lx - 8, G + 44, "lift-off point", 11, "end", "brand-fg", weight=600))
    # the preceding aircraft, airborne and climbing
    c.add(path(f"M{lx + 60} {G} Q{lx + 220} {G - 6} 580 {G - 104}", "fg-faint", None, THIN, dash=DASH))
    c.add(plane_side(330, G - 34, 0.4, "ok", pitch=10, fill="ok-soft"))
    c.add(plane_side(530, G - 86, 0.4, "ok", pitch=14, fill="ok-soft"))
    c.add(text(330, G - 52, "aircraft ahead, airborne", 11, "middle", "ok-fg", weight=600))
    c.add(line(330, G - 22, 330, G + 66, "ok", THIN, dash=DASH))
    c.add(line(530, G - 74, 530, G + 116, "ok", THIN, dash=DASH))
    c.add(darrow(lx, G + 64, 330, G + 64, "ok"))
    c.add(num(235, G + 84, "600 m", 14, "middle", "ok", weight=700))
    c.add(text(235, G + 100, "both aircraft under 2,000 kg MTOW", 11, "middle", "ok-fg"))
    c.add(darrow(lx, G + 114, 530, G + 114, "ok"))
    c.add(num(335, G + 134, "1,800 m", 14, "middle", "ok", weight=700))
    c.add(text(335, G + 150, "runway longer than 1,800 m", 11, "middle", "ok-fg"))
    # the full list
    c.add(rect(20, 18, 600, 132, "surface-2", None, rx=10))
    c.add(text(36, 42, "Do not take off until the aircraft ahead on the same runway:", 14, "start", "fg", weight=700))
    for i, s in enumerate(["has landed and vacated the runway, or", "has taken off and crossed the upwind end, or commenced a turn, or",
                           "is airborne and at least 600 m or 1,800 m ahead of your lift-off point (below)."]):
        c.add(circle(46, 64 + i * 24, 9, "brand", None))
        c.add(num(46, 68 + i * 24, str(i + 1), 11, "middle", "surface", weight=700))
        c.add(text(62, 68 + i * 24, s, 12.5, "start", "fg"))
    c.add(text(36, 138, "Landing: the same gaps, measured from your intended touchdown point.", 11.5, "start", "fg-muted"))
    c.add(text(612, 452, "not to scale", 11, "end", "fg-faint"))
    return c


# ================================================================ 2.4 Air service operations
def icon(kind: str, x: float, y: float, color: str) -> str:
    """Simple 40-unit pictograms centred on (x, y) for the briefing tiles."""
    if kind == "belt":
        return (path(f"M{x - 20} {y - 12} L{x - 6} {y - 2} M{x + 6} {y - 2} L{x + 20} {y - 12}", color, None, 4) +
                rect(x - 8, y - 8, 16, 14, None, color, 2.5, rx=3) + line(x - 3, y - 1, x + 3, y - 1, color, 2.5))
    if kind == "exit":
        return (rect(x - 14, y - 18, 20, 34, None, color, 2.5, rx=2) + circle(x + 2, y, 1.8, color, None) +
                arrow(x - 2, y - 2, x + 22, y - 2, color, 2.5))
    if kind == "smoke":
        return (rect(x - 14, y - 3, 24, 7, None, color, 2) + line(x + 14, y - 3, x + 14, y + 4, color, 2) +
                circle(x, y, 18, None, "bad", 2.5) + line(x - 13, y - 13, x + 13, y + 13, "bad", 2.5))
    if kind == "extinguisher":
        return (rect(x - 7, y - 10, 14, 28, None, color, 2.5, rx=5) + path(f"M{x} {y - 10} L{x} {y - 16} L{x + 12} {y - 16} L{x + 16} {y - 8}", color, None, 2.5) +
                line(x - 4, y - 18, x + 4, y - 18, color, 2.5))
    if kind == "brace":
        # seat in profile with a passenger folded forward, head down by the knees
        return (path(f"M{x - 20} {y - 18} L{x - 16} {y + 10} L{x + 8} {y + 10} M{x - 14} {y + 10} L{x - 14} {y + 20} M{x + 6} {y + 10} L{x + 6} {y + 20}",
                     "fg-muted", None, 2) +
                path(f"M{x - 12} {y + 6} L{x + 6} {y - 8} M{x - 12} {y + 6} L{x + 12} {y + 6} L{x + 14} {y + 18}", color, None, 3.5) +
                circle(x + 12, y - 6, 5.5, color, None) + path(f"M{x + 4} {y - 10} Q{x + 12} {y - 18} {x + 18} {y - 10}", color, None, 2.5))
    if kind == "pilot":
        return (path(f"M{x - 18} {y - 14} h36 a4 4 0 0 1 4 4 v16 a4 4 0 0 1 -4 4 h-22 l-8 8 v-8 h-6 a4 4 0 0 1 -4 -4 v-16 a4 4 0 0 1 4 -4 z", color, None, 2.5) +
                text(x, y + 3, "!", 15, "middle", color, weight=700))
    return ""


@chart
def passenger_briefing() -> Canvas:
    c = Canvas("What the passenger briefing must cover", "Six tiles: the use of seat belts and harnesses and when they must be worn; "
               "the location and operation of the exits; the smoking rules; the location of the emergency equipment, such as the fire "
               "extinguisher and life jackets if carried; the brace position; and that passengers must follow the pilot's instructions.",
               height=384, prefix="pb")
    tiles = [("belt", "Seat belts", ["how to use them,", "when they must be worn"]),
             ("exit", "Exits", ["where they are,", "how they open"]),
             ("smoke", "Smoking", ["the smoking rules", ""]),
             ("extinguisher", "Emergency equipment", ["fire extinguisher, life", "jackets if carried"]),
             ("brace", "Brace position", ["how to brace", "for an impact"]),
             ("pilot", "Pilot's instructions", ["passengers must", "follow them"])]
    c.add(text(320, 30, "Before take-off, the pilot in command briefs every passenger on:", 15, "middle", "fg", weight=700))
    W, H, G = 192, 140, 12
    for i, (k, title, lines) in enumerate(tiles):
        col_, row = i % 3, i // 3
        x, y = 20 + col_ * (W + G), 50 + row * (H + G)
        c.add(rect(x, y, W, H, "brand-soft", None, rx=10))
        c.add(circle(x + W / 2, y + 42, 30, "surface", None))
        c.add(icon(k, x + W / 2, y + 42, "brand"))
        c.add(text(x + W / 2, y + 96, title, 14, "middle", "brand-fg", weight=700))
        c.add(multiline(x + W / 2, y + 114, [l for l in lines if l], 11.5, "middle", "brand-fg", 1.3))
    c.add(text(320, 372, "A verbal briefing is standard in a light aeroplane.", 12, "middle", "fg-muted"))
    return c


@chart
def seat_belts_in_flight() -> Canvas:
    c = Canvas("When seat belts must be worn", "Side view of a flight profile from take-off to landing. Seat belts must be worn by everyone during "
               "take-off and landing, whenever the aircraft is below 1,000 ft above the ground, in turbulence, and whenever the pilot in "
               "command directs. The segments of the profile where belts are required are highlighted.", height=330, prefix="sbf")
    G, LIM = 262, 182
    c.add(rect(20, G, 600, 12, "surface-2", None))
    c.add(line(20, G, 620, G, "fg-muted", SECOND))
    c.add(line(20, LIM, 620, LIM, "fg-muted", THIN, dash=DASH))
    c.add(num(320, LIM - 8, "1,000 ft above ground", 11.5, "middle", "fg-muted", weight=600))
    # profile: take-off at 60, climb through 1000 ft at 150, cruise, descend through 1000 ft at 500, land at 590
    c.add(path(smooth_path([(50, G), (100, G - 30), (150, LIM)]), "brand", None, 5))
    c.add(path(smooth_path([(150, LIM), (200, 120), (240, 100)]), "fg-faint", None, 3))
    c.add(line(240, 100, 300, 100, "fg-faint", 3))
    # turbulence segment: belts on
    turb = [(300 + i * 10, 100 + (6 if i % 2 else -6)) for i in range(9)]
    c.add(path(smooth_path([(300, 100)] + turb[1:-1] + [(380, 100)]), "brand", None, 5))
    c.add(line(380, 100, 430, 100, "fg-faint", 3))
    c.add(path(smooth_path([(430, 100), (470, 120), (510, LIM)]), "fg-faint", None, 3))
    c.add(path(smooth_path([(510, LIM), (560, G - 30), (600, G)]), "brand", None, 5))
    c.add(plane_side(270, 92, 0.34, "fg"))
    # labels
    c.add(text(60, G + 34, "take-off", 13, "middle", "brand-fg", weight=700))
    c.add(text(590, G + 34, "landing", 13, "middle", "brand-fg", weight=700))
    c.add(text(160, LIM + 44, "below 1,000 ft", 12.5, "start", "brand-fg", weight=700))
    c.add(text(490, LIM + 44, "below 1,000 ft", 12.5, "end", "brand-fg", weight=700))
    c.add(text(340, 70, "turbulence", 13, "middle", "brand-fg", weight=700))
    c.add(text(340, 140, "above 1,000 ft in smooth air:", 11.5, "middle", "fg-muted"))
    c.add(text(340, 155, "when the pilot in command directs", 11.5, "middle", "fg-muted"))
    c.add(line(26, 30, 56, 30, "brand", 5))
    c.add(text(64, 34, "belts must be worn", 12.5, "start", "fg", weight=600))
    c.add(line(220, 30, 250, 30, "fg-faint", 3))
    c.add(text(258, 34, "belts on whenever the pilot in command directs", 12, "start", "fg-muted"))
    c.add(text(320, 318, "Seats locked before take-off and landing; the pilot in command's harness stays fastened throughout.", 12, "middle", "fg-muted"))
    return c


# ================================================================ 2.5 Aerodromes
def gable(x: float, y: float, s: float = 1.0) -> str:
    """Gable marker in plan view: a small white wedge."""
    return polygon([(x - 7 * s, y + 4 * s), (x, y - 5 * s), (x + 7 * s, y + 4 * s)], "paint", "fg", SECOND)


def cone(x: float, y: float) -> str:
    """Cone marker in plan view: a small white disc with a dark tip."""
    return circle(x, y, 5, "paint", "fg", SECOND) + circle(x, y, 1.5, "fg", None)


def white_cross(x: float, y: float, s: float = 14, w: float = 6) -> str:
    return group(rect(-s, -w / 2, 2 * s, w, "paint", "fg", THIN), rect(-w / 2, -s, w, 2 * s, "paint", "fg", THIN),
                 rect(-s + 1, -w / 2 + 1, 2 * s - 2, w - 2, "paint", None), transform=f"translate({fmt(x)} {fmt(y)}) rotate(45)")


@chart
def runway_markings_and_markers() -> Canvas:
    c = Canvas("Runway markings and markers", "Plan views. Top: a sealed runway with white markings: threshold piano keys, the designator "
               "24, aiming point bars, a dashed centreline and side stripes; a taxiway with a yellow centreline and a runway holding position "
               "marking of two solid and two dashed lines, hold on the solid side. Bottom: an unsealed runway with white cone markers "
               "along the runway edges, gable markers on the runway strip boundary, and a white cross closing an unserviceable section.",
               height=520, prefix="rmm")
    # ---------------- sealed runway
    c.add(text(20, 28, "Sealed runway: markings are white, taxiway markings yellow", 14, "start", "fg", weight=700))
    X0, X1, Y0, RW = 40, 600, 70, 56
    yc = Y0 + RW / 2
    c.add(rect(X0, Y0, X1 - X0, RW, "tarmac", None, rx=2))
    for j in range(6):                                 # piano keys
        c.add(rect(X0 + 6, Y0 + 5 + j * 8, 26, 5, "paint", None))
    c.add(num(X0 + 52, yc, "24", 22, "middle", "paint", weight=700, baseline="central", rotate=90))
    for side in (-1, 1):                               # aiming point bars
        c.add(rect(170, yc + side * 13 - 4, 46, 8, "paint", None))
    for xx in range(106, 560, 30):                     # centreline
        if not 160 < xx < 226:
            c.add(rect(xx, yc - 1.5, 16, 3, "paint", None))
    c.add(line(X0 + 2, Y0 + 3, X1 - 2, Y0 + 3, "paint", 1.5, cap="butt"))
    c.add(line(X0 + 2, Y0 + RW - 3, X1 - 2, Y0 + RW - 3, "paint", 1.5, cap="butt"))
    # taxiway from below with holding position marking
    TX = 380
    c.add(rect(TX - 18, Y0 + RW, 36, 124, "tarmac", None))
    c.add(line(TX, Y0 + RW, TX, Y0 + RW + 124, "warn", 2.5, cap="butt"))
    HY = Y0 + RW + 40
    c.add(line(TX - 18, HY, TX + 18, HY, "warn", 2.5, dash="5 3", cap="butt"))
    c.add(line(TX - 18, HY + 6, TX + 18, HY + 6, "warn", 2.5, dash="5 3", cap="butt"))
    c.add(line(TX - 18, HY + 14, TX + 18, HY + 14, "warn", 2.5, cap="butt"))
    c.add(line(TX - 18, HY + 20, TX + 18, HY + 20, "warn", 2.5, cap="butt"))
    c.add(plane_top(TX, HY + 46, 0.3, 0, "fg", "surface"))
    # labels for the sealed runway
    c.add(text(X0 + 4, Y0 + RW + 20, "threshold", 12, "start", "fg", weight=600))
    c.add(text(X0 + 4, Y0 + RW + 35, "(piano keys)", 11, "start", "fg-muted"))
    c.add(text(X0 + 2, Y0 - 8, "designator: 24 means 240° magnetic", 12, "start", "fg", weight=600))
    c.add(text(193, Y0 + RW + 20, "aiming point", 12, "middle", "fg", weight=600))
    c.add(text(598, Y0 - 8, "centreline (dashed) · side stripes", 12, "end", "fg", weight=600))
    c.add(line(TX + 22, HY + 10, TX + 52, HY + 10, "fg-muted", THIN))
    c.add(text(TX + 58, HY + 6, "holding position:", 12, "start", "fg", weight=600))
    c.add(text(TX + 58, HY + 21, "hold on the solid side", 12, "start", "warn-fg", weight=700))
    c.add(text(TX + 58, HY + 52, "taxiway: yellow centreline", 12, "start", "fg-muted"))
    # ---------------- unsealed runway
    c.add(line(20, 268, 620, 268, "line", THIN))
    c.add(text(20, 296, "Unsealed runway: cones and gables", 14, "start", "fg", weight=700))
    SY0, SY1 = 318, 462                                # runway strip boundary
    RY0, RY1 = 362, 418                                # runway (landing area) edges
    c.add(rect(40, SY0, 560, SY1 - SY0, "ok-soft", None, rx=4))
    c.add(rect(40, RY0, 560, RY1 - RY0, "warn-soft", None))
    for xx in range(60, 600, 90):
        c.add(gable(xx, SY0, 1.2))
        c.add(gable(xx, SY1, 1.2))
    for xx in range(60, 600, 60):
        c.add(cone(xx, RY0))
        c.add(cone(xx, RY1))
    c.add(white_cross(500, (RY0 + RY1) / 2, 18, 7))
    c.add(text(330, (RY0 + RY1) / 2 + 5, "runway (landing area)", 12, "middle", "warn-fg", weight=600))
    c.add(text(330, SY0 + 24, "runway strip: graded, kept clear", 11.5, "middle", "ok-fg"))
    # legend row
    LY = 492
    c.add(cone(46, LY - 4))
    c.add(text(58, LY, "cones: runway edge", 12, "start", "fg", weight=600))
    c.add(gable(212, LY - 2, 1.2))
    c.add(text(226, LY, "gables: strip boundary", 12, "start", "fg", weight=600))
    c.add(white_cross(414, LY - 4, 9, 4))
    c.add(text(430, LY, "white cross: unserviceable", 12, "start", "fg", weight=600))
    return c


@chart
def ground_signals() -> Canvas:
    c = Canvas("Ground signals and the wind indicator", "Six tiles. Windsock: shows the wind direction and roughly its strength. "
               "White cross: that part of the movement area is unserviceable. Double white cross beside the primary wind indicator: "
               "gliding operations in progress. White dumb-bell in the signal area: use the sealed runways and taxiways only. Horizontal "
               "white landing T: shows the landing direction where no windsock applies. Right-hand turn arrow: right-hand circuit.",
               height=400, prefix="gs")
    W, H, G = 192, 178, 12
    tiles = ["sock", "cross", "double", "dumbbell", "tee", "right"]
    words = {
        "sock": ("Windsock", ["wind direction and roughly", "its strength; seen from the circuit"]),
        "cross": ("White cross", ["that area is unserviceable:", "do not use it"]),
        "double": ("Double white cross", ["by the windsock: gliding in", "progress, expect gliders and tugs"]),
        "dumbbell": ("White dumb-bell", ["use the sealed runways", "and taxiways only"]),
        "tee": ("Landing T", ["shows the landing direction", "where no windsock applies"]),
        "right": ("Right-turn arrow", ["right-hand circuit", "(also shown in ERSA)"]),
    }
    for i, k in enumerate(tiles):
        x, y = 20 + (i % 3) * (W + G), 20 + (i // 3) * (H + G)
        cx, cy = x + W / 2, y + 62
        c.add(rect(x, y, W, H, "surface-2", None, rx=10))
        c.add(rect(x + 10, y + 10, W - 20, 104, "ok-soft", None, rx=6))
        if k == "sock":
            c.add(line(cx - 50, cy + 40, cx - 50, cy - 34, "fg", MAIN))
            c.add(polygon([(cx - 48, cy - 34), (cx + 40, cy - 24), (cx + 40, cy - 12), (cx - 48, cy - 6)], "warn-soft", "warn", SECOND))
            for f in (0.25, 0.5, 0.75):
                xx = cx - 48 + 88 * f
                c.add(line(xx, cy - 34 + 10 * f, xx, cy - 6 - 6 * f, "warn", SECOND))
            c.add(arrow(cx - 34, cy + 22, cx + 30, cy + 22, "sky-fg", MAIN))
            c.add(text(cx + 38, cy + 26, "wind", 11, "start", "sky-fg", weight=600))
        elif k == "cross":
            c.add(white_cross(cx, cy, 34, 12))
        elif k == "double":
            c.add(white_cross(cx - 26, cy, 22, 8))
            c.add(white_cross(cx + 26, cy, 22, 8))
        elif k == "dumbbell":
            c.add(path(f"M{cx - 54} {cy - 22} h30 v14 h48 v-14 h30 v44 h-30 v-14 h-48 v14 h-30 z", "fg", "paint", SECOND))
        elif k == "tee":
            c.add(path(f"M{cx - 50} {cy - 30} h100 v14 h-43 v52 h-14 v-52 h-43 z", "fg", "paint", SECOND))
        elif k == "right":
            c.add(path(f"M{cx - 40} {cy + 30} v-40 h50 v-12 l26 20 l-26 20 v-12 h-34 v24 z", "fg", "paint", SECOND))
        title, lines = words[k]
        c.add(text(cx, y + 138, title, 14, "middle", "fg", weight=700))
        c.add(multiline(cx, y + 156, lines, 11, "middle", "fg-muted", 1.3))
    return c


@chart
def overhead_join() -> Canvas:
    """Plan view of joining from overhead: cross the field above circuit height, descend on the dead side, cross the upwind end to join crosswind."""
    c = Canvas("Joining the circuit from overhead", "Plan view of a left-hand circuit on runway 24, take-off to the right. The joining aircraft "
               "crosses overhead the aerodrome above circuit height, descends on the dead side (the side away from the circuit) to circuit "
               "height, 1,000 ft above aerodrome level, then crosses the upwind end of the runway to join the crosswind leg and continue "
               "downwind.", height=460, prefix="ohj")
    RY = 250
    join_d = "M236 30 L320 250 Q340 330 410 340 L480 340 Q540 340 540 290 L540 160 Q540 110 500 110 L140 110"
    c.style(f"""
.ohj-plane{{offset-path:path("{join_d}");offset-rotate:auto;animation:ohj-fly 12s linear infinite}}
@keyframes ohj-fly{{to{{offset-distance:100%}}}}
.ohj-plane-static{{display:none}}
@supports not (offset-path: path("M0 0")){{.ohj-plane{{display:none}}.ohj-plane-static{{display:inline}}}}
""")
    c.add(rect(20, 62, 600, 150, "brand-soft", None, rx=10, fill_opacity=0.35))
    c.add(rect(20, 288, 600, 150, "surface-2", None, rx=10))
    c.add(text(36, 84, "Circuit side", 14, "start", "brand-fg", weight=700))
    c.add(text(36, 100, "circuit height 1,000 ft above aerodrome level", 11, "start", "brand-fg"))
    c.add(text(36, 412, "Dead side", 14, "start", "fg-muted", weight=700))
    c.add(text(36, 428, "kept clear of circuit traffic", 11, "start", "fg-muted"))
    c.add(runway(320, RY, 220, 26, None))
    c.add(num(250, RY + 5, "24", 12, "middle", "surface", weight=700))
    c.add(num(390, RY + 5, "06", 12, "middle", "surface", weight=700))
    # the standard circuit, faint
    c.add(path("M140 110 Q100 110 100 150 L100 222 Q100 262 140 262 L200 262", "fg-faint", None, SECOND, dash="6 5"))
    c.add(path("M440 262 L500 262 Q540 262 540 222", "fg-faint", None, SECOND, dash="6 5"))
    # the join
    c.add(path(join_d, "brand", None, MAIN, dash="8 6"))
    steps = [(290, 212, "1", ["overhead the aerodrome,", "above circuit height"], "end"),
             (420, 370, "2", ["descend on the dead side", "to circuit height"], "start"),
             (540, 214, "3", ["cross the upwind end,", "join crosswind"], "end"),
             (180, 134, "4", ["downwind at circuit height"], "middle")]
    for x, y, n, lines, anchor in steps:
        c.add(circle(x, y, 10, "brand", None))
        c.add(num(x, y + 4, n, 12, "middle", "surface", weight=700))
        dx = -16 if anchor == "end" else 16 if anchor == "start" else 0
        if n == "3":
            dx = -16
        dy = 0 if anchor != "middle" else 24
        c.add(multiline(x + dx, y + 4 + dy, lines, 12, anchor if anchor != "middle" else "middle", "brand-fg", 1.3))
    c.add(arrow(600, 30, 520, 30, "sky-fg", MAIN))
    c.add(text(510, 34, "wind from 240°", 12, "end", "sky-fg", weight=600))
    c.add(group(plane_top(0, 0, 0.3, 90, "fg", "surface"), cls="ohj-plane"))
    c.add(group(plane_top(440, 340, 0.3, 90, "fg", "surface"), cls="ohj-plane-static"))
    c.add(text(612, 452, "not to scale", 11, "end", "fg-faint"))
    return c


# ================================================================ 2.6 Airspace
@chart
def controlled_vs_non_controlled_at_a_glance() -> Canvas:
    c = Canvas("Controlled and non-controlled airspace at a glance", "Two columns compared row by row. Controlled airspace (Class C and D, "
               "control zones): a clearance is required, ATC separates traffic (Class C separates IFR from VFR, Class D IFR from IFR, "
               "with traffic information to VFR), Class C requires a transponder and radio, and an RPL holder needs the controlled "
               "airspace and controlled aerodrome endorsements. Non-controlled Class G: no clearance, pilots separate themselves by "
               "lookout and radio, flight information on request, CTAF procedures at aerodromes. Below: Class E is controlled for IFR "
               "only, VFR needs no clearance; Class A is IFR only.", height=500, prefix="cvn")
    LX, CW, GX = 150, 228, 392
    c.add(rect(LX, 20, CW, 52, "brand", None, rx=8))
    c.add(text(LX + CW / 2, 42, "Controlled", 16, "middle", "surface", weight=700))
    c.add(text(LX + CW / 2, 60, "Class C, D · control zones (CTR)", 11.5, "middle", "surface"))
    c.add(rect(GX, 20, CW, 52, "surface-2", "line-strong", SECOND, rx=8))
    c.add(text(GX + CW / 2, 42, "Non-controlled", 16, "middle", "fg", weight=700))
    c.add(text(GX + CW / 2, 60, "Class G", 11.5, "middle", "fg-muted"))
    rows = [
        ("Clearance", ["required before entry", "ATC clearances and instructions"], ["none required", "fly by the rules of the air"]),
        ("Separation", ["ATC: C separates IFR from VFR;", "D separates IFR from IFR and", "gives VFR traffic information"],
         ["you: lookout and radio;", "flight information and traffic", "information on request"]),
        ("Radio", ["talk to ATC; Class C requires", "a transponder and radio"], ["broadcast on the appropriate", "frequency; CTAF at aerodromes"]),
        ("RPL holder", ["needs the controlled airspace", "and controlled aerodrome", "endorsements"], ["no airspace endorsement", "needed"]),
    ]
    y = 84
    for name, a, b in rows:
        h = 20 + 16 * max(len(a), len(b))
        c.add(text(LX - 12, y + h / 2 + 5, name, 13, "end", "fg", weight=700))
        c.add(rect(LX, y, CW, h, "brand-soft", None, rx=6))
        c.add(rect(GX, y, CW, h, "surface-2", None, rx=6))
        c.add(multiline(LX + 12, y + 22, a, 12, "start", "brand-fg", 1.33))
        c.add(multiline(GX + 12, y + 22, b, 12, "start", "fg", 1.33))
        y += h + 8
    # the two odd classes
    y += 10
    c.add(card(20, y, 296, 84, "Class E: controlled for IFR only", ["VFR needs no clearance but must meet the", "VMC minima and should carry a transponder;",
                                                                   "IFR flights are controlled"], "sky", 11.5, 13.5))
    c.add(card(324, y, 296, 84, "Class A: high level", ["IFR only; VFR not permitted", "(above FL180 along the east coast", "and in other areas)"], "info", 11.5, 13.5))
    c.add(text(320, y + 112, "Class G is the only non-controlled class.", 13, "middle", "fg", weight=600))
    return c


def tower(x: float, y: float, color: str) -> str:
    """A small control tower standing on the ground at (x, y)."""
    return (rect(x - 4, y - 34, 8, 34, "surface", color, SECOND) + polygon([(x - 12, y - 34), (x + 12, y - 34), (x + 9, y - 46), (x - 9, y - 46)], "surface-2", color, SECOND) +
            line(x - 11, y - 48, x + 11, y - 48, color, SECOND))


@chart
def class_d_tower_hours() -> Canvas:
    c = Canvas("What happens when the tower closes", "Two side views of the same regional towered aerodrome. Left, during the tower's "
               "published hours: the control zone is Class D, a clearance is required and the tower controls the circuit. Right, outside "
               "those hours: the airspace reverts to Class G (or Class E above) and the aerodrome becomes a CTAF aerodrome. The hours are "
               "in ERSA and may be changed by NOTAM.", height=340, prefix="cdt")
    G = 252
    for i, (title, sub, tone) in enumerate([("Tower open", "during its published hours", "ok"), ("Tower closed", "outside those hours", "fg")]):
        x0 = 20 + i * 308
        w = 292
        c.add(rect(x0, 20, w, 280, "surface-2" if tone == "fg" else "surface", "line-strong", THIN, rx=10))
        c.add(text(x0 + 16, 46, title, 16, "start", "fg", weight=700))
        c.add(text(x0 + 16, 64, sub, 12, "start", "fg-muted"))
        cx = x0 + w / 2
        if tone == "ok":
            c.add(rect(cx - 96, 92, 192, G - 92, "ok-soft", "ok", SECOND))
            c.add(text(cx, 124, "Class D", 18, "middle", "ok-fg", weight=700))
            c.add(text(cx, 146, "clearance required", 12.5, "middle", "ok-fg", weight=600))
            c.add(text(cx, 164, "the tower controls the circuit", 12, "middle", "ok-fg"))
            c.add(tower(cx, G, "ok"))
        else:
            c.add(rect(cx - 96, 92, 192, G - 92, None, "fg-faint", THIN, dash=DASH))
            c.add(text(cx, 124, "Class G", 18, "middle", "fg", weight=700))
            c.add(text(cx, 146, "(or Class E above)", 12, "middle", "fg-muted"))
            c.add(text(cx, 164, "no clearance: CTAF procedures", 12, "middle", "fg-muted"))
            c.add(tower(cx, G, "fg-faint"))
        c.add(line(x0 + 10, G, x0 + w - 10, G, "fg-muted", SECOND))
        c.add(rect(x0 + 10, G, w - 20, 8, "surface-2", None))
        c.add(text(cx, G + 30, "Class D aerodrome" if tone == "ok" else "now a CTAF aerodrome", 12, "middle", "fg", weight=600))
    c.add(arrow(306, 172, 334, 172, "fg-muted", SECOND))
    c.add(text(320, 326, "The tower's hours are in ERSA for the aerodrome and may be changed by NOTAM.", 12, "middle", "fg-muted"))
    return c


@chart
def airspace_active_check() -> Canvas:
    c = Canvas("Is that airspace active? The pre-flight check", "Four steps in order: read the chart (VTC, VNC, ERC-L) for the boundaries "
               "and limits; read ERSA, its PRD section and AIP ENR 5.1, for the hours of activity (H24, HJ, specified UTC times, or by "
               "NOTAM) and the controlling authority; check the NOTAMs for activations, changes and temporary restricted areas; if in "
               "doubt, call the controlling authority or ATC. An active restricted area needs a clearance; without one, stay out.",
               height=438, prefix="aac")
    steps = [
        ("1", "Chart", "VTC · VNC · ERC-L", ["lateral boundaries and vertical limits, e.g. C LL 4500", "(the WAC shows no airspace)"], "sky"),
        ("2", "ERSA", "PRD section · AIP ENR 5.1", ["hours of activity: H24, HJ, UTC times, or by NOTAM;", "the controlling authority; tower hours"], "sky"),
        ("3", "NOTAM", "today's changes", ["can activate, deactivate or change an area; temporary", "restricted areas for bushfires, air shows, VIPs"], "sky"),
        ("4", "Still unsure?", "ask", ["call the controlling authority or ATC", "on the published frequency"], "brand"),
    ]
    y, RH = 20, 54
    for i, (n, title, sub, lines, tone) in enumerate(steps):
        yy = y + i * (RH + 8)
        c.add(rect(20, yy, 600, RH, SOFT[tone], EDGE[tone], SECOND, rx=10))
        c.add(circle(44, yy + RH / 2, 13, EDGE[tone], None))
        c.add(num(44, yy + RH / 2 + 5, n, 13, "middle", "surface", weight=700))
        c.add(text(66, yy + 23, title, 15, "start", FG[tone], weight=700))
        c.add(text(66, yy + 41, sub, 11, "start", FG[tone], weight=600))
        c.add(line(238, yy + 10, 238, yy + RH - 10, EDGE[tone], THIN))
        c.add(multiline(252, yy + 23, lines, 12, "start", FG[tone], 1.4))
    y = y + 4 * (RH + 8) - 8 + 10
    # outcome
    c.add(arrow(320, y, 320, y + 24, "fg-muted", SECOND))
    y += 30
    c.add(rect(20, y, 296, 104, "bad-soft", "bad", SECOND, rx=10))
    c.add(text(36, y + 26, "Restricted area active?", 15, "start", "bad-fg", weight=700))
    c.add(multiline(36, y + 48, ["You need the controlling authority's", "clearance to enter, as for controlled", "airspace. No clearance: stay out."], 12, "start", "bad-fg", 1.4))
    c.add(rect(324, y, 296, 104, "ok-soft", "ok", SECOND, rx=10))
    c.add(text(340, y + 26, "Tower closed?", 15, "start", "ok-fg", weight=700))
    c.add(multiline(340, y + 48, ["Outside its ERSA hours a Class D", "zone reverts to Class G (or E above)", "and the aerodrome becomes CTAF."], 12, "start", "ok-fg", 1.4))
    c.add(text(320, y + 130, "Military zones and areas (e.g. RAAF Pearce): active at the published hours and otherwise as notified.", 11.5, "middle", "fg-muted"))
    return c


# ================================================================ 2.7 Emergencies and SAR
def code_display(x: float, y: float, code: str, tone: str) -> str:
    """A transponder-style code window: four digit boxes."""
    out = rect(x - 86, y - 28, 172, 56, "fg", None, rx=8, fill_opacity=0.9)
    for i, d in enumerate(code):
        bx = x - 76 + i * 38
        out += rect(bx, y - 20, 32, 40, "surface", None, rx=4)
        out += num(bx + 16, y + 10, d, 26, "middle", EDGE[tone], weight=700)
    return out


@chart
def transponder_emergency_codes() -> Canvas:
    c = Canvas("The emergency transponder codes", "Three code windows: 7700 emergency, 7600 radio failure, 7500 unlawful interference. "
               "They are listed in the ERSA EMERG section, the pink pages, with the distress and urgency calls, radio failure procedures, "
               "interception, light signals, ditching, survival and the SAR system.", height=360, prefix="tec")
    codes = [("7700", "Emergency", "bad"), ("7600", "Radio failure", "warn"), ("7500", "Unlawful interference", "info")]
    for i, (code, what, tone) in enumerate(codes):
        x = 116 + i * 204
        c.add(rect(x - 98, 20, 196, 160, SOFT[tone], EDGE[tone], SECOND, rx=12))
        c.add(code_display(x, 76, code, tone))
        c.add(text(x, 136, what, 15, "middle", FG[tone], weight=700))
        c.add(text(x, 158, "squawk " + code, 12, "middle", FG[tone], cls="num"))
    c.add(rect(20, 200, 600, 140, "surface-2", None, rx=10))
    c.add(text(36, 226, "Where to find them in flight: ERSA EMERG, the pink pages", 14, "start", "fg", weight=700))
    items = ["distress and urgency calls (MAYDAY, PAN PAN)", "transponder emergency codes", "radio failure procedures",
             "interception procedures and signals", "light signals", "ditching, survival and the SAR system"]
    for i, s in enumerate(items):
        x = 40 + (i % 2) * 330
        y = 252 + (i // 2) * 24
        c.add(circle(x, y - 4, 3, "fg-muted", None))
        c.add(text(x + 10, y, s, 12, "start", "fg-muted"))
    c.add(text(36, 328, "AIP GEN 3.6 and ENR 1.14 hold the fuller text. Carry a current ERSA.", 11.5, "start", "fg-faint"))
    return c


@chart
def sartime_timeline() -> Canvas:
    c = Canvas("How a SARTIME works", "A timeline. Before flight you nominate a SARTIME in UTC, by flight plan, the NAIPS SARTIME form, or "
               "phone or radio to Flight Information, with a sensible margin after your planned arrival. If delayed, extend it by radio "
               "or phone before it expires. On landing, cancel it at once. If it is not cancelled or amended by that time, the search and "
               "rescue system begins the alerting phases: attempts to contact you, then a communications search, then a physical search "
               "by AMSA's Joint Rescue Coordination Centre.", height=404, prefix="sar")
    Y = 150
    c.add(line(30, Y, 610, Y, "fg-muted", MAIN))
    c.add(arrow(600, Y, 618, Y, "fg-muted", MAIN))
    c.add(text(612, Y + 22, "time (UTC)", 11, "end", "fg-faint"))
    marks = [(90, "Nominate", ["flight plan, NAIPS form,", "or phone or radio to", "Flight Information"], "fg"),
             (210, "Depart", [], "fg"),
             (340, "Planned arrival", ["land: cancel at once"], "ok"),
             (480, "SARTIME", ["not cancelled or", "amended by now?"], "bad")]
    for x, title, lines, tone in marks:
        col_ = EDGE[tone] if tone != "fg" else "fg"
        c.add(circle(x, Y, 8 if tone != "fg" else 6, col_, "surface", 2))
        c.add(text(x, Y - 20, title, 14, "middle", FG[tone] if tone != "fg" else "fg", weight=700))
        c.add(multiline(x, Y + 26, lines, 11.5, "middle", FG[tone] if tone != "fg" else "fg-muted", 1.3))
    c.add(plane_side(283, Y - 50, 0.4, "fg"))
    # margin between planned arrival and SARTIME
    c.add(rect(340, 64, 140, 20, "ok-soft", None, rx=4))
    c.add(text(410, 78, "a sensible margin", 11.5, "middle", "ok-fg", weight=600))
    c.add(line(340, 86, 340, Y - 38, "ok", THIN, dash=DASH))
    c.add(line(480, 86, 480, Y - 38, "bad", THIN, dash=DASH))
    c.add(text(410, 40, "delayed? extend it by radio or phone before it expires", 12, "middle", "warn-fg", weight=600))
    # the escalation
    c.add(text(30, 246, "SARTIME passes uncancelled: the SAR system assumes you are in trouble", 13.5, "start", "fg", weight=700))
    steps = [("1", ["Attempts to", "contact you"], []), ("2", ["Communications", "search"], []),
             ("3", ["Physical", "search"], ["by AMSA's Joint Rescue", "Coordination Centre"])]
    for i, (n, title, sub) in enumerate(steps):
        x, y = 30 + i * 200, 266
        c.add(rect(x, y, 180, 90, "bad-soft", "bad", SECOND if i < 2 else MAIN + 1, rx=8))
        c.add(circle(x + 24, y + 28, 12, "bad", None))
        c.add(num(x + 24, y + 32, n, 12, "middle", "surface", weight=700))
        c.add(multiline(x + 44, y + 22, title, 13, "start", "bad-fg", 1.3, weight=700))
        c.add(multiline(x + 44, y + 64, sub, 11, "start", "bad-fg", 1.3))
        if i < 2:
            c.add(arrow(x + 182, y + 45, x + 198, y + 45, "bad", SECOND))
    c.add(text(30, 390, "Or, for a private VFR flight, leave a flight note with a responsible person who will contact SAR.", 11, "start", "fg-muted"))
    return c


@chart
def accident_incident_reporting() -> Canvas:
    c = Canvas("Accident, incident and what to report", "A decision chart. An accident is an occurrence in which a person is killed or "
               "seriously injured, the aircraft has serious damage or structural failure, or it is missing or inaccessible. Accidents, "
               "serious incidents and the listed serious events are immediately reportable: phone the ATSB as soon as practicable on "
               "1800 011 034, then a written report within 72 hours. Other incidents that affect or could affect safety are routine "
               "reportable: a written report within 72 hours. Reports go to the ATSB, not CASA.", height=470, prefix="air")
    c.add(rect(170, 18, 300, 46, "surface-2", "line-strong", SECOND, rx=10))
    c.add(text(320, 38, "An occurrence", 14, "middle", "fg", weight=700))
    c.add(text(320, 55, "associated with operating an aircraft", 11, "middle", "fg-muted"))
    c.add(arrow(270, 64, 168, 96, "fg-muted", SECOND))
    c.add(arrow(370, 64, 472, 96, "fg-muted", SECOND))
    # left: accident or serious incident
    c.add(rect(20, 100, 296, 196, "bad-soft", "bad", MAIN, rx=10))
    c.add(text(36, 126, "Accident", 16, "start", "bad-fg", weight=700))
    for i, s in enumerate(["a person killed or seriously injured", "serious damage or structural failure", "aircraft missing or inaccessible"]):
        c.add(circle(42, 148 + i * 20, 3, "bad", None))
        c.add(text(52, 152 + i * 20, s, 12, "start", "bad-fg"))
    c.add(line(36, 214, 300, 214, "bad", THIN, dash=DASH))
    c.add(text(36, 236, "or a serious incident", 14, "start", "bad-fg", weight=700))
    c.add(multiline(36, 256, ["an accident nearly occurred: near collision,", "runway incursion, fuel exhaustion"], 12, "start", "bad-fg", 1.35))
    # right: incident
    c.add(rect(324, 100, 296, 196, "warn-soft", "warn", SECOND, rx=10))
    c.add(text(340, 126, "Incident", 16, "start", "warn-fg", weight=700))
    c.add(multiline(340, 150, ["any other occurrence that affects or", "could affect safety, for example:"], 12, "start", "warn-fg", 1.35))
    for i, s in enumerate(["engine failure, then a safe landing", "airspace infringement", "bird strike"]):
        c.add(circle(346, 196 + i * 20, 3, "warn", None))
        c.add(text(356, 200 + i * 20, s, 12, "start", "warn-fg"))
    # what to do
    c.add(arrow(168, 296, 168, 318, "bad", SECOND))
    c.add(arrow(472, 296, 472, 318, "warn", SECOND))
    c.add(rect(20, 322, 296, 92, "surface", "bad", MAIN, rx=10))
    c.add(text(36, 346, "Immediately reportable", 14, "start", "bad-fg", weight=700))
    c.add(text(36, 368, "phone the ATSB as soon as practicable:", 12, "start", "fg"))
    c.add(num(36, 388, "1800 011 034", 15, "start", "bad", weight=700))
    c.add(text(160, 388, "then written in 72 h", 12, "start", "fg"))
    c.add(rect(324, 322, 296, 92, "surface", "warn", SECOND, rx=10))
    c.add(text(340, 346, "Routine reportable", 14, "start", "warn-fg", weight=700))
    c.add(text(340, 368, "written report to the ATSB", 12, "start", "fg"))
    c.add(num(340, 390, "within 72 hours", 15, "start", "warn", weight=700))
    c.add(text(320, 440, "Damage limited to the engine, propeller, wheels, tyres, brakes, fairings, small dents or punctures", 11, "middle", "fg-muted"))
    c.add(text(320, 456, "does not by itself make it an accident. Reports go to the ATSB, not CASA.", 11, "middle", "fg-muted"))
    return c
