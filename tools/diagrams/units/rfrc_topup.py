"""RFRC top-up visuals (second wave). Every number, rule and name comes from the notes in content/notes/RFRC/; where a
note hedges, the diagram hedges. Helpers are reused from units/rfrc.py (not edited)."""
from __future__ import annotations

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, arrow, circle, fmt, group, line, multiline, num, path, plane_top,
                                rect, runway, text)
from tools.diagrams.units.rfrc import EDGE, FG, SOFT, icon

def raw_rect(x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None, width: float = 0, rx: float = 0,
             opacity: float | None = None) -> str:
    st = f' stroke="{stroke}" stroke-width="{fmt(width)}"' if stroke else ""
    op = f' fill-opacity="{fmt(opacity)}"' if opacity is not None else ""
    return f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" rx="{fmt(rx)}" fill="{fill}"{op}{st}/>'


def raw_text(x: float, y: float, s: str, size: float, fill: str, anchor: str = "middle", weight: int = 700) -> str:
    return (f'<text x="{fmt(x)}" y="{fmt(y)}" font-size="{fmt(size)}" text-anchor="{anchor}" font-weight="{weight}" '
            f'fill="{fill}">{s}</text>')


def nbadge(x: float, y: float, n: str, tone: str = "brand") -> str:
    """Numbered disc used to key a picture to a list."""
    return circle(x, y, 10, "fg-muted" if tone == "fg" else EDGE[tone], "surface", 1.5) + num(x, y + 4.5, n, 12, "middle", "surface", weight=700)


def person(x: float, y: float, color: str = "fg-muted") -> str:
    """Tiny standing person in plan-ish view (head and shoulders)."""
    return circle(x, y - 9, 5, color, None) + path(f"M{fmt(x - 8)} {fmt(y + 8)} Q{fmt(x)} {fmt(y - 6)} {fmt(x + 8)} {fmt(y + 8)} Z", color, color, THIN)


# ================================================================ 2.2 Licence and medical limits stack
@chart
def tighter_limit_applies() -> Canvas:
    c = Canvas("The licence limit and the medical limit stack", "Two worked comparisons. Maximum take-off weight: a Basic Class 2 medical "
               "would allow piston aircraft up to 8,618 kg, but the RPL allows only 1,500 kg, so 1,500 kg applies. Passengers: a four-seat "
               "aeroplane has three passenger seats and the RPL allows passengers, but a RAMPC allows no more than 1 passenger, so 1 applies. "
               "You are bound by whichever limit is tighter.", height=400, prefix="tla")
    c.add(text(320, 30, "Licence, medical, aeroplane: the tightest limit is the one you fly to", 15, "middle", "fg", weight=700))
    # ---------- weight scale
    c.add(text(20, 66, "Maximum take-off weight: RPL holder with a Basic Class 2", 13.5, "start", "fg", weight=700))
    X0, X1, KG = 150, 610, 9000
    sx = lambda kg: X0 + (X1 - X0) * kg / KG  # noqa: E731
    rows = [("Basic Class 2", 8618, "8,618 kg", "info", 92), ("RPL licence", 1500, "1,500 kg", "brand", 128)]
    for label, kg, s, tone, y in rows:
        c.add(text(X0 - 12, y + 5, label, 12.5, "end", FG[tone], weight=600))
        c.add(rect(X0, y - 9, sx(kg) - X0, 18, SOFT[tone], EDGE[tone], SECOND, rx=4))
        if kg > 4000:
            c.add(num(sx(kg) - 10, y + 5, s, 12.5, "end", FG[tone], weight=700))
        else:
            c.add(num(sx(kg) + 8, y + 5, s, 12.5, "start", FG[tone], weight=700))
    for kg in (0, 3000, 6000, 9000):
        c.add(line(sx(kg), 146, sx(kg), 152, "line-strong", THIN))
        c.add(num(sx(kg), 166, f"{kg:,}", 11, "middle", "fg-faint"))
    c.add(line(X0, 146, X1, 146, "line-strong", THIN))
    c.add(line(sx(1500), 76, sx(1500), 146, "brand", MAIN, dash=DASH))
    c.add(text(X1, 186, "kg", 11, "end", "fg-faint"))
    c.add(rect(20, 176, 380, 26, "brand-soft", None, rx=13))
    c.add(text(34, 194, "You may fly up to 1,500 kg MTOW: the licence wins", 12.5, "start", "brand-fg", weight=700))
    # ---------- passengers
    c.add(line(20, 222, 620, 222, "line", THIN))
    c.add(text(20, 250, "Passengers: RPL holder with a RAMPC in a four-seat aeroplane", 13.5, "start", "fg", weight=700))
    cards = [("Aeroplane", "4 seats: pilot + 3", "fg"), ("RPL licence", "passengers allowed", "fg"), ("RAMPC medical", "no more than 1", "brand")]
    for i, (t, s, tone) in enumerate(cards):
        x = 20 + i * 128
        c.add(rect(x, 266, 122, 52, SOFT[tone], EDGE[tone], SECOND, rx=8))
        c.add(text(x + 61, 287, t, 12.5, "middle", FG[tone], weight=700))
        c.add(text(x + 61, 306, s, 11, "middle", FG[tone] if tone != "fg" else "fg-muted"))
    # cabin seen from above: 2 x 2 seats
    cx, cy = 520, 314
    c.add(rect(cx - 70, cy - 52, 140, 104, "surface-2", "line-strong", SECOND, rx=22))
    seats = [(cx - 28, cy - 24, "P"), (cx + 28, cy - 24, "1"), (cx - 28, cy + 24, "x"), (cx + 28, cy + 24, "x")]
    for x, y, k in seats:
        if k == "P":
            c.add(rect(x - 18, y - 16, 36, 32, "surface", "fg", SECOND, rx=6), text(x, y + 5, "pilot", 11, "middle", "fg", weight=600))
        elif k == "1":
            c.add(rect(x - 18, y - 16, 36, 32, "brand-soft", "brand", MAIN, rx=6), num(x, y + 5, "1", 14, "middle", "brand-fg", weight=700))
        else:
            c.add(rect(x - 18, y - 16, 36, 32, "surface", "line-strong", SECOND, rx=6, dash=DASH))
            c.add(line(x - 9, y - 9, x + 9, y + 9, "bad", MAIN), line(x - 9, y + 9, x + 9, y - 9, "bad", MAIN))
    c.add(rect(20, 334, 380, 26, "brand-soft", None, rx=13))
    c.add(text(34, 352, "1 passenger, whatever the seats: the medical wins", 12.5, "start", "brand-fg", weight=700))
    c.add(text(320, 388, "Check each limit (licence, medical, aeroplane) and fly to the tightest.", 12, "middle", "fg-muted"))
    return c


# ================================================================ 2.4 Refuelling and pre-flight
@chart
def refuelling_safety_zone() -> Canvas:
    c = Canvas("Refuelling: what must be true before fuel flows", "Plan view of an aeroplane being refuelled from a bowser inside a "
               "refuelling zone. Keyed to a list: 1 no smoking or naked flames; 2 engines stopped; 3 aircraft and bowser bonded (earthed) "
               "with a lead so static equalises through the wire, not as a spark at the nozzle; 4 a fire extinguisher at hand; 5 passengers "
               "off the aircraft, or supervised as the rules allow; 6 no radar or HF transmissions. Afterwards: caps secured and a fuel "
               "drain check for water and the correct fuel.", height=430, prefix="rsz")
    c.add(text(20, 28, "Every rule removes one way to ignite the fuel vapour", 15, "start", "fg", weight=700))
    # refuelling zone
    ZX0, ZY0, ZX1, ZY1 = 36, 46, 372, 384
    c.add(rect(ZX0, ZY0, ZX1 - ZX0, ZY1 - ZY0, "warn-soft", "warn", MAIN, rx=18, dash="8 5"))
    c.add(text(ZX0 + 14, ZY1 - 12, "refuelling zone", 12, "start", "warn-fg", weight=700))
    # aeroplane, nose right, engine stopped (prop drawn still)
    PX, PY, S = 176, 196, 1.7
    c.add(plane_top(PX, PY, S, 90, "fg", "surface"))
    # bowser
    BX, BY = 232, 306
    c.add(rect(BX, BY, 92, 44, "surface-2", "fg", MAIN, rx=6))
    c.add(rect(BX + 92, BY + 6, 6, 32, "fg-muted", None, rx=2))
    c.add(text(BX + 46, BY + 27, "bowser", 12, "middle", "fg", weight=600))
    # hose to the lower wing filler
    FX, FY = PX - 2, PY + 30 * S
    c.add(circle(FX, FY, 4, "surface", "fg", SECOND))
    c.add(path(f"M{BX} {BY + 16} C{BX - 40} {BY + 14} {FX + 30} {FY + 40} {FX + 4} {FY + 3}", "fg-muted", None, 4))
    c.add(text(FX - 8, FY + 50, "hose", 11, "end", "fg-muted"))
    # bonding lead (the focal element)
    TX, TY = PX + 30 * S, PY + 6 * S
    LX0 = BX + 70
    c.add(path(f"M{LX0} {BY} C{LX0} {BY - 50} {TX + 40} {TY + 30} {TX + 2} {TY + 2}", "brand", None, MAIN))
    c.add(circle(TX, TY, 4, "brand", None), circle(LX0, BY, 4, "brand", None))
    c.add(text(LX0 + 8, BY - 30, "bonding", 12, "start", "brand-fg", weight=700))
    c.add(text(LX0 + 8, BY - 16, "lead", 12, "start", "brand-fg", weight=700))
    # extinguisher
    c.add(icon("extinguisher", 330, 118, "bad"))
    # no smoking sign
    c.add(icon("smoke", 84, 86, "fg-muted"))
    # no transmitting: a handheld radio crossed out
    RX, RY = 84, 300
    c.add(rect(RX - 8, RY - 12, 16, 26, None, "fg-muted", 2, rx=3), line(RX + 4, RY - 12, RX + 4, RY - 22, "fg-muted", 2))
    c.add(circle(RX, RY, 18, None, "bad", 2.5), line(RX - 13, RY - 13, RX + 13, RY + 13, "bad", 2.5))
    # passengers stepping out of the zone
    c.add(person(86, 196), person(66, 214))
    c.add(arrow(54, 194, 22, 194, "fg-muted", SECOND))
    # number badges in the picture
    c.add(nbadge(112, 70, "1", "fg"), nbadge(PX + 43 * S + 14, PY - 22, "2", "fg"), nbadge(LX0 - 16, BY - 34, "3", "brand"),
          nbadge(354, 96, "4", "fg"), nbadge(96, 236, "5", "fg"), nbadge(112, 284, "6", "fg"))
    c.add(text(PX + 43 * S + 28, PY - 18, "prop still", 11, "start", "fg-muted"))
    # list
    LX = 384
    items = [("1", "No smoking or naked flames", ["no ignition source"], "fg"),
             ("2", "Engines stopped", ["no hot exhaust or ignition spark"], "fg"),
             ("3", "Aircraft and bowser bonded", ["static flows through the wire,", "not as a spark at the nozzle"], "brand"),
             ("4", "Fire extinguisher at hand", [], "fg"),
             ("5", "Passengers off the aircraft", ["or supervised as the rules allow"], "fg"),
             ("6", "No radar or HF transmissions", ["they can induce a spark"], "fg")]
    y = 66
    for n, title, lines, tone in items:
        c.add(nbadge(LX + 10, y - 4, n, tone))
        c.add(text(LX + 26, y, title, 12.5, "start", "brand-fg" if tone == "brand" else "fg", weight=700))
        c.add(multiline(LX + 26, y + 16, lines, 11.5, "start", "brand-fg" if tone == "brand" else "fg-muted", 1.3))
        y += 30 + 15 * len(lines)
    c.add(rect(20, 396, 600, 28, "ok-soft", None, rx=14))
    c.add(text(320, 415, "Afterwards: caps secured, then a fuel drain check for water and the correct fuel", 12.5, "middle", "ok-fg", weight=700))
    return c


@chart
def preflight_legal_checks() -> Canvas:
    c = Canvas("The walk-around items the law requires", "Plan view of the aeroplane with eight numbered items: 1 locking devices "
               "removed (control and gust locks, pitot cover, engine blanks); 2 doors and hatches secured; 3 tank caps fitted and secure; "
               "4 frost, ice and snow removed from wings, tail and control surfaces; 5 flight controls full, free and correct; "
               "6 instruments checked; 7 the empty control seat's harness secured before solo; 8 fuel drained at each drain point for "
               "water and contamination, at the first flight of the day and after refuelling, once the fuel has settled.",
               height=404, prefix="plc")
    c.add(text(320, 28, "Behind the checklist: eight items the law requires", 15, "middle", "fg", weight=700))
    PX, PY, S = 336, 214, 2.3
    P = lambda u, v: (PX + u * S, PY + v * S)  # noqa: E731
    # frost on the wings and tail (soft hatch area behind the picture)
    c.add(plane_top(PX, PY, S, 90, "fg", "surface"))
    # pitot tube on the left (upper) wing
    px, py = P(7, -36)
    c.add(line(px, py, px + 16, py, "brand", 3))
    # doors
    for v in (-5.2, 5.2):
        a, b = P(10, v), P(24, v)
        c.add(line(a[0], a[1], b[0], b[1], "brand", 3.5))
    # tank caps
    for v in (-24, 24):
        x, y = P(-1, v)
        c.add(circle(x, y, 4.5, "surface", "brand", MAIN))
    # drains (underside, shown dashed) at each tank and the engine
    for u, v in ((6, -18), (6, 18), (32, 0)):
        x, y = P(u, v)
        c.add(circle(x, y, 4.5, "ok-soft", "ok", SECOND, dash="2 2"))
    # control surfaces: ailerons and elevator outlined in brand
    for sgn in (-1, 1):
        a, b = P(-6, sgn * 30), P(-6, sgn * 49)
        c.add(line(a[0], a[1], b[0], b[1], "brand", 3.5))
        a, b = P(-33, sgn * 4), P(-33, sgn * 17)
        c.add(line(a[0], a[1], b[0], b[1], "brand", 3.5))
    # badges
    marks = [("1", P(7, -36), (16, -14)), ("2", P(17, -5), (0, -22)), ("3", P(-1, -24), (-18, -8)), ("4", P(-30, 17), (-12, 14)),
             ("5", P(-6, 44), (-18, 4)), ("6", P(26, -2), (8, -30)), ("7", P(16, 3), (0, 20)), ("8", P(6, 18), (18, 8))]
    for n, (x, y), (dx, dy) in marks:
        c.add(line(x, y, x + dx, y + dy, "fg-muted", THIN))
        c.add(circle(x + dx, y + dy, 10, "brand", "surface", 1.5), num(x + dx, y + dy + 4.5, n, 12, "middle", "surface", weight=700))
    # lists
    left = [("1", "Locks and covers off", ["control and gust locks,", "pitot cover, engine blanks"]),
            ("2", "Doors and hatches secured", ["an open door distracts"]),
            ("3", "Tank caps secure", ["or fuel siphons out"]),
            ("4", "Frost, ice, snow removed", ["even thin frost cuts lift"])]
    right = [("5", "Controls full, free", ["and correct movement"]),
             ("6", "Instruments checked", ["altimeter, gyros,", "ASI reading zero"]),
             ("7", "Empty seat harness", ["secured before solo"]),
             ("8", "Fuel drains sampled", ["at each drain point, first", "flight of the day and after", "refuelling, once settled"])]
    for col_x, items in ((20, left), (448, right)):
        y = 70
        for n, title, lines in items:
            c.add(circle(col_x + 10, y - 4, 10, "brand", "surface", 1.5), num(col_x + 10, y + 0.5, n, 12, "middle", "surface", weight=700))
            c.add(text(col_x + 26, y, title, 12.5, "start", "fg", weight=700))
            c.add(multiline(col_x + 26, y + 16, lines, 11.5, "start", "fg-muted", 1.3))
            y += 34 + 15 * len(lines)
    c.add(circle(170, 384, 4.5, "ok-soft", "ok", SECOND, dash="2 2"))
    c.add(text(180, 388, "drain points (underneath)", 11.5, "start", "fg-muted"))
    c.add(line(350, 384, 370, 384, "brand", 3.5))
    c.add(text(378, 388, "items to check", 11.5, "start", "fg-muted"))
    return c


# ================================================================ 2.5 Aerodromes
@chart
def movement_area_plan() -> Canvas:
    c = Canvas("Movement area, manoeuvring area and apron", "Plan of a small aerodrome. The runway and the taxiways are shaded as the "
               "manoeuvring area; the apron, where aircraft park, load and refuel, is shaded separately; a dashed line around both marks "
               "the movement area. The grass, buildings and road outside are not part of the movement area. Below: movement area equals "
               "manoeuvring area (runways and taxiways) plus apron.", height=420, prefix="map")
    c.add(rect(16, 16, 608, 300, "ok-soft", None, rx=12))  # grass
    c.add(text(30, 40, "grass: not movement area", 11.5, "start", "ok-fg", weight=600))
    # surfaces with halos: manoeuvring (brand) and apron (info); halos grouped so overlaps do not darken
    RY, TY = 92, 176
    halo = 9
    TW = 14
    man = [(60, RY - 15, 520, 30), (100, TY - TW / 2, 440, TW), (100, RY, TW, TY - RY), (526, RY, TW, TY - RY), (313, RY, TW, TY - RY)]
    c.add(group(*[rect(x - halo, y - halo, w + 2 * halo, h + 2 * halo, "brand", None, rx=6) for x, y, w, h in man], opacity=0.28))
    APX, APY, APW, APH = 250, TY + TW / 2, 140, 66
    c.add(group(rect(APX - halo, APY, APW + 2 * halo, APH + halo, "info", None, rx=6), opacity=0.6))
    # movement area outline
    d = (f"M{60 - 18} {RY - 15 - 18} H{580 + 18} V{TY + TW / 2 + 18} H{APX + APW + 18} V{APY + APH + 18} H{APX - 18} "
         f"V{TY + TW / 2 + 18} H{60 - 18} Z")
    c.add(path(d, "fg", None, MAIN, dash="7 5"))
    # tarmac
    c.add(rect(60, RY - 15, 520, 30, "tarmac", None, rx=1))
    for j in range(4):
        for x0 in (64, 562):
            c.add(rect(x0, RY - 12 + j * 7, 14, 4, "paint", None))
    c.add(num(96, RY, "06", 15, "middle", "paint", weight=700, baseline="central", rotate=90))
    c.add(num(544, RY, "24", 15, "middle", "paint", weight=700, baseline="central", rotate=-90))
    for x in range(118, 520, 26):
        c.add(rect(x, RY - 1.2, 14, 2.4, "paint", None))
    for x, y, w, h in man[1:]:
        c.add(rect(x, y, w, h, "tarmac", None))
    c.add(line(100 + TW / 2, TY, 526 + TW / 2, TY, "warn", 1.5))
    for x in (100, 526, 313):
        c.add(line(x + TW / 2, RY + 15, x + TW / 2, TY, "warn", 1.5))
    c.add(rect(APX, APY, APW, APH, "tarmac", None, rx=2))
    for x in (278, 320, 362):
        c.add(plane_top(x, APY + 36, 0.34, 0, "paint", "tarmac"))
    # buildings and road
    c.add(rect(250, 266, 70, 30, "surface-2", "line-strong", SECOND, rx=2), rect(330, 270, 60, 26, "surface-2", "line-strong", SECOND, rx=2))
    c.add(line(16, 304, 624, 304, "line-strong", 6, cap="butt"))
    c.add(text(236, 276, "buildings, road:", 11.5, "end", "fg-muted", weight=600))
    c.add(text(236, 291, "not movement area", 11.5, "end", "fg-muted", weight=600))
    # labels on the picture
    c.add(text(580, 52, "runway", 12.5, "end", "brand-fg", weight=700))
    c.add(text(212, 134, "taxiway", 12.5, "middle", "brand-fg", weight=700))
    c.add(arrow(212, 142, 212, TY - 10, "brand", SECOND))
    c.add(text(426, 140, "grass inside: not", 11.5, "middle", "ok-fg"))
    c.add(text(426, 155, "movement area", 11.5, "middle", "ok-fg"))
    c.add(text(APX + APW + 26, APY + 44, "apron", 13, "start", "info-fg", weight=700))
    c.add(text(598, 226, "movement area", 12.5, "end", "fg", weight=700))
    c.add(text(598, 242, "(dashed line)", 11, "end", "fg-muted"))
    # equation
    EY = 336
    c.add(rect(20, EY, 170, 66, "surface", "fg", MAIN, rx=10, dash="7 5"))
    c.add(text(105, EY + 28, "Movement area", 14, "middle", "fg", weight=700))
    c.add(text(105, EY + 48, "take-off, landing, taxiing", 11.5, "middle", "fg-muted"))
    c.add(text(206, EY + 39, "=", 22, "middle", "fg", weight=700))
    c.add(rect(222, EY, 210, 66, "brand-soft", "brand", SECOND, rx=10))
    c.add(text(327, EY + 28, "Manoeuvring area", 14, "middle", "brand-fg", weight=700))
    c.add(text(327, EY + 48, "runways + taxiways", 11.5, "middle", "brand-fg"))
    c.add(text(448, EY + 39, "+", 22, "middle", "fg", weight=700))
    c.add(rect(464, EY, 156, 66, "info-soft", "info", SECOND, rx=10))
    c.add(text(542, EY + 28, "Apron", 14, "middle", "info-fg", weight=700))
    c.add(text(542, EY + 48, "park, load, refuel", 11.5, "middle", "info-fg"))
    return c


def sign(x: float, y: float, w: float, h: float, kind: str, label: str, size: float = 15) -> str:
    """Taxiway sign face centred on (x, y). The token set has no theme-stable red, yellow or black, so each face is a token
    fill with a soft overlay that keeps it legible in both themes: mandatory = red with light letters, location = dark with
    yellow letters and border, direction = yellow with dark letters."""
    x0, y0 = x - w / 2, y - h / 2
    ty = y + size * 0.36

    def light_yellow_text() -> str:  # paint lifted with a warn wash: pale yellow in both themes
        return raw_text(x, ty, label, size, "var(--color-paint)") + raw_text(x, ty, label, size, "var(--color-warn)").replace("<text ", '<text fill-opacity="0.35" ')

    if kind == "mandatory":
        face = raw_rect(x0, y0, w, h, "var(--color-bad)", "var(--color-fg)", 1, 3) + raw_rect(x0, y0, w, h, "var(--color-bad-soft)", None, 0, 3, 0.35)
        letters = raw_text(x, ty, label, size, "var(--color-paint)")
    elif kind == "location":
        face = (raw_rect(x0, y0, w, h, "var(--color-tarmac)", "var(--color-fg)", 1, 3) +
                raw_rect(x0 + 3, y0 + 3, w - 6, h - 6, "none", "var(--color-paint)", 1.5, 2) +
                raw_rect(x0 + 3, y0 + 3, w - 6, h - 6, "none", "var(--color-warn)", 1.5, 2).replace("<rect ", '<rect stroke-opacity="0.35" '))
        letters = light_yellow_text()
    else:
        face = raw_rect(x0, y0, w, h, "var(--color-paint)", "var(--color-fg)", 1, 3) + raw_rect(x0, y0, w, h, "var(--color-warn)", None, 0, 3, 0.35)
        letters = raw_text(x, ty, label, size, "var(--color-tarmac)")
    return face + letters


@chart
def taxiway_signs() -> Canvas:
    c = Canvas("Taxiway signs: red is mandatory, yellow informs", "Left: plan view of taxiway A leading up to runway 24R, with a junction "
               "to taxiway B. Beside the taxiway before the junction stand a location sign (A, yellow letters on black: the taxiway you "
               "are on) and a direction sign (B with an arrow, black letters on yellow: which way to go). Beside the runway holding "
               "position marking, two solid then two dashed yellow lines, stands a mandatory sign 24R in white letters on red: stop on "
               "the solid side and do not pass without permission. Right: the three signs explained.", height=440, prefix="tws")
    c.add(text(20, 28, "Red: you must not pass. Yellow: where you are and where to go.", 15, "start", "fg", weight=700))
    # ---------- plan view (left)
    c.add(rect(16, 44, 300, 380, "ok-soft", None, rx=10))
    RY = 82
    c.add(rect(16, RY - 22, 300, 44, "tarmac", None))
    for x in range(30, 310, 34):
        c.add(rect(x, RY - 1.5, 18, 3, "paint", None))
    c.add(text(300, RY - 28, "runway 24R", 11.5, "end", "fg", weight=600))
    TXC, TW = 150, 34
    c.add(rect(TXC - TW / 2, RY + 22, TW, 402 - RY, "tarmac", None))
    JY = 330
    c.add(rect(TXC, JY - TW / 2, 316 - TXC, TW, "tarmac", None))
    c.add(line(TXC, RY + 22, TXC, 424, "warn", 2))
    c.add(path(f"M{TXC} {JY + 30} Q{TXC} {JY} {TXC + 30} {JY} H316", "warn", None, 2))
    # holding position marking: dashed nearer the runway, solid facing the approaching aircraft
    HY = 150
    for dy, dash in ((0, "5 3"), (6, "5 3"), (14, None), (20, None)):
        c.add(line(TXC - TW / 2, HY + dy, TXC + TW / 2, HY + dy, "warn", 2.5, dash=dash, cap="butt"))
    c.add(plane_top(TXC, 222, 0.42, 0, "fg", "surface"))
    # signs beside the taxiway (left side, as seen by the pilot)
    c.add(line(TXC - TW / 2 - 6, HY + 10, 96, HY + 10, "fg-muted", THIN))
    c.add(sign(70, HY + 10, 48, 26, "mandatory", "24R", 14))
    c.add(text(70, HY + 40, "holding position", 11, "middle", "bad-fg", weight=600))
    c.add(sign(56, JY - 46, 30, 26, "location", "A", 14))
    c.add(sign(100, JY - 46, 46, 26, "direction", "B →", 14))
    c.add(text(78, JY - 16, "before the", 11, "middle", "fg-muted"))
    c.add(text(78, JY - 3, "junction", 11, "middle", "fg-muted"))
    c.add(text(TXC + 24, 400, "taxiway A", 11.5, "start", "fg", weight=600))
    c.add(text(300, JY + 32, "taxiway B", 11.5, "end", "fg", weight=600))
    c.add(text(TXC + 26, HY + 4, "dashed", 11, "start", "fg-muted"))
    c.add(text(TXC + 26, HY + 24, "solid: hold here", 11, "start", "warn-fg", weight=700))
    # ---------- explanations (right)
    X, W = 332, 288
    tiles = [("mandatory", "24R", 56, "bad", "Mandatory: white on red", ["runway holding position (also NO ENTRY).", "Stop at the solid lines; do not pass", "without permission (a clearance at a", "controlled aerodrome)."]),
             ("location", "A", 36, "fg", "Location: yellow on black", ["the taxiway you are on now."]),
             ("direction", "B →", 56, "fg", "Direction: black on yellow", ["which way to taxiway B (or to a", "runway): information, not a stop."])]
    y = 48
    for kind, label, sw, tone, head, lines in tiles:
        h = 50 + 16 * len(lines)
        c.add(rect(X, y, W, h, SOFT[tone], EDGE[tone], SECOND, rx=10))
        c.add(sign(X + 16 + sw / 2, y + 24, sw, 28, kind, label, 15))
        c.add(text(X + 28 + sw, y + 29, head, 13, "start", FG[tone], weight=700))
        c.add(multiline(X + 14, y + 62, lines, 12, "start", FG[tone] if tone != "fg" else "fg-muted", 1.33))
        y += h + 12
    c.add(multiline(X + 4, y + 14, ["The signs are drawn close to the real colours,", "softened slightly to read in light and dark."], 11, "start", "fg-faint", 1.3))
    return c


# ================================================================ 2.6 Airspace
@chart
def prd_areas_entry() -> Canvas:
    c = Canvas("Prohibited, restricted and danger areas: may you go in?", "Three panels. Prohibited area: may not be entered at all; the "
               "track stops at the boundary. Restricted area: treated like controlled airspace; when active you need the controlling "
               "authority's clearance to enter, without one stay out. Danger area: a hazardous activity such as parachuting or gunnery; "
               "you may enter, but knowing the risk is your responsibility. Below: hours of activity are in ERSA PRD and AIP ENR 5.1 "
               "(H24, HJ, specified UTC times, or by NOTAM), and a NOTAM can activate, deactivate or change an area.", height=380, prefix="prd")
    c.add(text(320, 28, "Three kinds of area, three answers", 15, "middle", "fg", weight=700))
    panels = [("P", "Prohibited", "bad", "No entry, ever", ["may not be entered", "at all"]),
              ("R", "Restricted", "warn", "Clearance when active", ["like controlled airspace:", "no clearance, stay out"]),
              ("D", "Danger", "info", "May enter: your risk", ["parachuting, gunnery…", "know what is going on"])]
    W, G = 192, 12
    for i, (letter, name, tone, verdict, lines) in enumerate(panels):
        x = 20 + i * (W + G)
        c.add(rect(x, 44, W, 262, "surface", "line", SECOND, rx=10))
        c.add(text(x + W / 2, 70, f"{name} area", 15, "middle", FG[tone], weight=700))
        # the area
        ax, ay, r = x + W / 2 + 20, 140, 46
        c.add(circle(ax, ay, r, SOFT[tone], EDGE[tone], MAIN, dash=None if letter != "D" else DASH))
        c.add(text(ax, ay + 9, letter, 26, "middle", FG[tone], weight=700))
        # the track
        y0 = ay
        if letter == "P":
            c.add(arrow(x + 12, y0, ax - r - 8, y0, "fg", MAIN))
            c.add(line(ax - r - 4, y0 - 12, ax - r - 4, y0 + 12, "bad", 3))
        elif letter == "R":
            c.add(arrow(x + 12, y0, ax - r - 8, y0, "fg", MAIN))
            c.add(path(f"M{ax - r - 8} {y0} Q{ax - r + 10} {y0 - 2} {ax} {y0 + 24} T{ax + r + 14} {y0 + 30}", "fg", None, MAIN, dash=DASH, arrow_end=True))
            c.add(text(ax, ay + 66, "only with a clearance", 11, "middle", "warn-fg", weight=600))
        else:
            c.add(arrow(x + 12, y0 + 22, x + W - 10, y0 + 22, "fg", MAIN))
        c.add(rect(x + 12, 214, W - 24, 28, SOFT[tone], None, rx=14))
        c.add(text(x + W / 2, 232.5, verdict, 12, "middle", FG[tone], weight=700))
        c.add(multiline(x + W / 2, 264, lines, 12, "middle", "fg-muted", 1.35))
    c.add(rect(20, 318, 600, 52, "sky-soft", None, rx=10))
    c.add(text(36, 339, "When is it active?", 13, "start", "sky-fg", weight=700))
    c.add(text(180, 339, "ERSA PRD and AIP ENR 5.1: H24, HJ, specified UTC times, or by NOTAM.", 11.5, "start", "sky-fg"))
    c.add(text(36, 358, "A NOTAM can activate, deactivate or change an area; temporary restricted areas come by NOTAM.", 11.5, "start", "sky-fg"))
    return c
