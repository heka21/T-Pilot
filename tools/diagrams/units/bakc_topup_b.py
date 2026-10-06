"""BAKC top-up visuals for lessons 3.x, 5.x and 6.x: systems schematics, engine handling, instruments, charts and
documents, and the structural and balance limits. Numbers on every figure come from the note it sits in."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, arc_path, arrow, badge, callout, circle, ellipse, fmt, group,
                                line, multiline, num, path, plane_side, polygon, polyline, rect, sample, smooth_path, text)


# ---------------------------------------------------------------- helpers
def panel(x: float, y: float, w: float, h: float, fill: str = "surface-2", stroke: str | None = None) -> str:
    return rect(x, y, w, h, fill, stroke, THIN if stroke else MAIN, rx=10)


def box(x: float, y: float, w: float, h: float, label: str | list[str], colour: str = "fg", size: float = 13, sub: str | None = None) -> str:
    """Component box: soft fill in its colour, label centred."""
    fill = f"{colour}-soft" if colour in ("brand", "ok", "warn", "bad", "info") else "surface"
    tcol = f"{colour}-fg" if colour in ("brand", "ok", "warn", "bad", "info") else "fg"
    out = rect(x, y, w, h, fill, colour if colour != "fg" else "fg", SECOND, rx=8)
    lines = [label] if isinstance(label, str) else label
    n = len(lines) + (1 if sub else 0)
    y0 = y + h / 2 - (n - 1) * size * 0.65 + size * 0.35
    for i, s in enumerate(lines):
        out += text(x + w / 2, y0 + i * size * 1.3, s, size, "middle", tcol, weight=700)
    if sub:
        out += text(x + w / 2, y0 + len(lines) * size * 1.3, sub, 11, "middle", tcol)
    return out


def wire(points: list[tuple[float, float]], colour: str = "fg", width: float = MAIN, arrow_end: bool = False, dash: str | None = None) -> str:
    return polyline(points, colour, width, dash, arrow_end=arrow_end)


def breaker(x: float, y: float) -> str:
    """Circuit breaker symbol on a horizontal wire centred at (x, y)."""
    return (rect(x - 9, y - 6, 18, 12, "surface", "fg", SECOND, rx=3) + rect(x - 4, y - 12, 8, 6, "fg-muted", None, rx=1))


def earth(x: float, y: float, colour: str = "fg") -> str:
    """Earth (ground) symbol hanging below (x, y)."""
    return (line(x, y, x, y + 10, colour, SECOND) + line(x - 10, y + 10, x + 10, y + 10, colour, SECOND) +
            line(x - 6, y + 15, x + 6, y + 15, colour, SECOND) + line(x - 2, y + 20, x + 2, y + 20, colour, SECOND))


def heat(x: float, y: float, dx: float, dy: float, colour: str = "bad") -> str:
    """Wavy heat arrow from (x, y) towards (x+dx, y+dy)."""
    n = 3
    pts = []
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    for i in range(n * 4 + 1):
        t = i / (n * 4)
        w = math.sin(t * n * 2 * math.pi) * 3.5
        pts.append((x + dx * t + nx * w, y + dy * t + ny * w))
    return path(smooth_path(pts), colour, None, SECOND, arrow_end=True)


# ================================================================ BAKC 3.1 the piston engine
@chart
def electrical_system_schematic() -> Canvas:
    c = Canvas("How power flows in a light aeroplane's electrical system",
               "The belt-driven alternator feeds the bus bar in flight and recharges the battery. The battery, through the master switch "
               "and the ammeter, turns the starter and is the reserve if the alternator fails. Every service draws from the bus bar through "
               "its own circuit breaker, which cuts an overloaded circuit before the wiring overheats. The magnetos are not on this system.",
               height=420, prefix="ess")
    BX = 372  # bus bar x
    # ---- alternator
    c.add(rect(20, 36, 92, 64, "surface-2", "fg-muted", SECOND, rx=8), text(66, 64, "engine", 13, "middle", "fg-muted", weight=700),
          text(66, 82, "(drives belt)", 11, "middle", "fg-muted"))
    c.add(line(112, 52, 150, 52, "fg-muted", SECOND, DASH), line(112, 86, 150, 86, "fg-muted", SECOND, DASH))
    c.add(box(150, 36, 112, 64, "Alternator", "brand", 14, sub="power in flight"))
    c.add(wire([(262, 68), (BX - 9, 68)], "brand", 3, arrow_end=True))
    c.add(breaker(300, 68), text(300, 92, "ALT field", 11, "middle", "fg-muted"))
    # ---- battery
    c.add(rect(150, 196, 112, 72, "info-soft", "info", SECOND, rx=8))
    for i in range(4):
        x = 170 + i * 20
        c.add(line(x, 216, x, 248, "info", 2.5, cap="butt"), line(x + 8, 222, x + 8, 242, "info", 1.5, cap="butt"))
    c.add(text(206, 262, "Battery", 13, "middle", "info-fg", weight=700))
    # vent
    c.add(wire([(150, 206), (96, 206)], "fg-muted", SECOND, arrow_end=True))
    c.add(multiline(16, 228, ["battery vent:", "hydrogen and acid", "fumes overboard"], 11, "start", "fg-muted"))
    # master switch and ammeter
    c.add(wire([(262, 232), (272, 232)], "info", 3))
    c.add(circle(272, 232, 3, "info", None), line(272, 232, 292, 219, "info", 2.5), circle(296, 232, 3, "info", None))
    c.add(text(292, 254, "master", 11, "middle", "fg-muted", weight=600))
    c.add(wire([(296, 232), (310, 232)], "info", 3))
    c.add(circle(324, 232, 14, "surface", "fg", SECOND), text(324, 237, "A", 13, "middle", "fg", weight=700))
    c.add(wire([(338, 232), (BX - 7, 232)], "info", 3))
    c.add(multiline(330, 274, ["ammeter:", "charge or", "discharge"], 11, "middle", "info"))
    # starter
    c.add(wire([(206, 268), (206, 300)], "info", 3, arrow_end=True))
    c.add(text(214, 290, "start", 11, "start", "fg-muted"))
    c.add(box(136, 304, 140, 48, ["Starter motor"], "fg", 13, sub="big current, short bursts"))
    # ---- bus bar
    c.add(rect(BX - 7, 40, 14, 340, "brand", None, rx=3))
    c.add(text(BX, 400, "bus bar", 13, "middle", "brand", weight=700))
    services = ["radios", "transponder", "lights", "electric flaps", "electric fuel pump", "turn coordinator", "pitot heat"]
    for i, s in enumerate(services):
        y = 64 + i * 46
        c.add(line(BX + 7, y, 470, y, "fg", SECOND), breaker(420, y), arrow(470, y, 484, y, "fg", SECOND))
        c.add(text(492, y + 5, s, 13, "start", "fg"))
    c.add(text(420, 36, "breakers", 11, "middle", "fg-muted", weight=600))
    # footer notes
    c.add(multiline(412, 372, ["A breaker pops on overload:", "reset once, after it cools."], 11, "start", "fg-muted"))
    c.add(multiline(16, 386, ["Magnetos are not on this system:", "the engine runs with the master off."], 12, "start", "fg", weight=600))
    return c


@chart
def engine_lubrication_circuit() -> Canvas:
    c = Canvas("Where the oil goes",
               "A wet-sump lubrication circuit. The engine-driven pump draws oil from the sump and pushes it through the filter, with a "
               "pressure relief valve spilling the excess back to the sump when the oil is cold and thick. A thermostatic valve sends cold oil "
               "past the oil cooler and hot oil through it. Drilled galleries carry the oil to the bearings, the valve gear and the cylinder "
               "walls, and oil sprayed under the pistons picks up heat the cooling fins cannot reach. It drains back to the sump, and the cooler "
               "sheds the heat to the airflow.", height=440, prefix="elc")
    O, P = "brand", 2.5
    # sump
    c.add(path("M180 372 L620 372 L604 420 L196 420 Z", O, "brand-soft", MAIN))
    c.add(text(400, 402, "Sump (wet sump)", 14, "middle", "brand-fg", weight=700))
    # pump, drawing from the sump
    c.add(wire([(196, 404), (90, 404), (90, 342)], O, P, arrow_end=True))
    c.add(box(40, 292, 100, 46, ["Oil pump"], "brand", 13, sub="engine driven"))
    # relief valve back to the sump
    c.add(wire([(140, 315), (162, 315), (162, 330)], O, SECOND))
    c.add(rect(152, 330, 20, 16, "surface", "fg", SECOND, rx=3))
    c.add(wire([(162, 346), (162, 390), (188, 390)], O, SECOND, dash=DASH, arrow_end=True))
    c.add(multiline(180, 300, ["relief valve:", "spills excess", "when cold"], 11, "start", "fg-muted"))
    # filter
    c.add(wire([(90, 292), (90, 254)], O, P, arrow_end=True))
    c.add(box(40, 206, 100, 46, ["Filter"], "fg", 13, sub="catches particles"))
    # thermostatic valve, cooler and bypass
    c.add(wire([(90, 206), (90, 180)], O, P))
    c.add(circle(90, 172, 8, "surface", "fg", SECOND))
    c.add(multiline(78, 168, ["thermostatic", "valve"], 11, "end", "fg-muted"))
    c.add(wire([(90, 164), (90, 122)], O, P, arrow_end=True))
    c.add(text(96, 150, "hot", 12, "start", O, weight=600))
    c.add(wire([(98, 172), (160, 172), (160, 52)], O, SECOND))
    c.add(text(166, 118, "cold:", 12, "start", O, weight=600), text(166, 133, "bypass", 12, "start", O, weight=600))
    c.add(rect(40, 70, 100, 50, "info-soft", "info", SECOND, rx=6))
    for x in (52, 64, 116, 128):
        c.add(line(x, 76, x, 114, "info", THIN))
    c.add(text(90, 99, "cooler", 12, "middle", "info-fg", weight=700))
    c.add(wire([(90, 70), (90, 50), (600, 50)], O, P))
    for x in (54, 72):
        c.add(heat(x, 64, 0, -28, "info"))
    c.add(text(16, 24, "Oil cooler: heat out to the airflow", 12, "start", "info", weight=700))
    # galleries
    c.add(text(420, 36, "galleries: drilled passages", 12, "middle", "brand", weight=700))
    parts = [(270, "Crankshaft", "bearings"), (375, "Valve gear", "and camshaft"), (480, "Cylinder", "walls"), (585, "Piston", "underside spray")]
    for x, a_, b_ in parts:
        c.add(wire([(x, 50), (x, 116)], O, SECOND, arrow_end=True))
        c.add(rect(x - 48, 120, 96, 50, "surface", "fg", SECOND, rx=8))
        c.add(text(x, 141, a_, 12, "middle", "fg", weight=700), text(x, 158, b_, 11, "middle", "fg-muted"))
        c.add(wire([(x, 170), (x, 366)], O, SECOND, dash=DASH, arrow_end=True))
    c.add(multiline(427, 290, ["drains", "back to", "the sump"], 12, "middle", "brand", weight=600))
    # heat pickup
    c.add(heat(624, 184, -32, 28, "bad"), heat(309, 184, -32, 28, "bad"))
    c.add(multiline(577, 236, ["piston heat", "the fins", "cannot reach"], 11, "end", "bad"))
    c.add(multiline(278, 236, ["bearing", "heat"], 11, "start", "bad"))
    return c


def ice(x: float, y: float, s: float = 1.0) -> str:
    """Small lump of ice."""
    d = f"M{fmt(x - 7 * s)} {fmt(y)} L{fmt(x - 4 * s)} {fmt(y - 6 * s)} L{fmt(x + 1 * s)} {fmt(y - 4 * s)} L{fmt(x + 6 * s)} {fmt(y - 7 * s)} L{fmt(x + 8 * s)} {fmt(y)} Z"
    return path(d, "info", "surface", SECOND)


@chart
def carburettor_vs_injection() -> Canvas:
    c = Canvas("Why fuel injection does not get carburettor ice",
               "Left: in a carburettor the air speeds up through the venturi, its pressure and temperature drop, and fuel evaporating in it "
               "cools it further, upstream of the throttle butterfly, so ice can form in the venturi and at the butterfly. Right: fuel "
               "injection has no venturi; a pump and metering unit send fuel to a nozzle at each cylinder's inlet port, where it evaporates "
               "against hot metal, so the induction air is never chilled. The air intake of either can still collect impact ice.",
               height=380, prefix="cvi")
    Y = 170
    for k, ox in enumerate((12, 328)):
        carb = k == 0
        c.add(panel(ox, 16, 300, 324))
        c.add(text(ox + 150, 42, "Carburettor" if carb else "Fuel injection", 16, "middle", "fg", weight=700))
        # duct walls
        if carb:
            top = f"M{ox + 16} {Y - 22} L{ox + 62} {Y - 22} Q{ox + 92} {Y - 8} {ox + 122} {Y - 22} L{ox + 220} {Y - 22}"
            bot = f"M{ox + 16} {Y + 22} L{ox + 62} {Y + 22} Q{ox + 92} {Y + 8} {ox + 122} {Y + 22} L{ox + 220} {Y + 22}"
            c.add(rect(ox + 66, Y - 21, 108, 42, "info", None, fill_opacity=0.22))
        else:
            top = f"M{ox + 16} {Y - 22} L{ox + 220} {Y - 22}"
            bot = f"M{ox + 16} {Y + 22} L{ox + 220} {Y + 22}"
        c.add(path(top, "fg", None, MAIN), path(bot, "fg", None, MAIN))
        # cylinder head, hot
        c.add(rect(ox + 220, Y - 62, 66, 124, "warn-soft", "warn", MAIN, rx=8))
        c.add(multiline(ox + 253, Y + 30, ["hot", "cylinder"], 12, "middle", "warn-fg", weight=700))
        c.add(line(ox + 220, Y - 21, ox + 220, Y + 21, "warn-soft", 4, cap="butt"))
        c.add(arrow(ox + 22, Y, ox + 52, Y, "fg-muted", SECOND), text(ox + 22, Y - 30, "air in", 12, "start", "fg-muted"))
        bx = ox + 150 if carb else ox + 100
        c.add(line(bx - 5, Y - 14, bx + 5, Y + 14, "fg", 2.5), circle(bx, Y, 2.5, "fg", None))
        if carb:
            # float chamber and jet
            c.add(rect(ox + 66, 240, 52, 40, "surface", "fg", SECOND, rx=4), rect(ox + 68, 256, 48, 22, "brand-soft", None))
            c.add(text(ox + 92, 298, "float chamber", 11, "middle", "fg-muted"))
            c.add(polyline([(ox + 92, 258), (ox + 92, Y + 4)], "brand", MAIN))
            for dx, dy in ((4, -2), (12, -6), (18, 3), (26, -3), (34, 4)):
                c.add(circle(ox + 92 + dx, Y + dy, 1.8, "brand", None))
            c.add(ice(ox + 92, Y - 15, -0.9), ice(ox + 150, Y - 21, -1.0), ice(ox + 140, Y + 21, 1.0))
            c.add(text(ox + 120, 74, "venturi: pressure and", 12, "middle", "info", weight=600))
            c.add(text(ox + 120, 89, "temperature drop, and fuel", 12, "middle", "info", weight=600))
            c.add(text(ox + 120, 104, "evaporating cools the air", 12, "middle", "info", weight=600))
            c.add(multiline(ox + 136, 258, ["ice forms in the", "venturi and at", "the butterfly"], 12, "start", "bad", weight=700))
            c.add(line(ox + 146, 244, ox + 142, Y + 28, "bad", THIN))
            c.add(text(ox + 150, 324, "The cooling happens in the induction air.", 12, "middle", "fg", weight=600))
        else:
            c.add(text(bx, Y + 40, "throttle", 11, "middle", "fg-muted"))
            c.add(rect(ox + 40, 252, 110, 40, "brand-soft", "brand", SECOND, rx=6))
            c.add(multiline(ox + 95, 268, ["pump and", "metering unit"], 11, "middle", "brand-fg", weight=600))
            c.add(polyline([(ox + 150, 272), (ox + 206, 272), (ox + 206, Y + 22)], "brand", MAIN))
            c.add(polygon([(ox + 202, Y + 22), (ox + 210, Y + 22), (ox + 208, Y + 12), (ox + 204, Y + 12)], "brand", "brand", THIN))
            for dx, dy in ((2, 4), (8, -2), (12, 6), (6, 10)):
                c.add(circle(ox + 206 + dx, Y + dy, 1.8, "brand", None))
            c.add(text(ox + 194, 236, "nozzle at the", 11, "end", "brand", weight=600), text(ox + 194, 250, "inlet port", 11, "end", "brand", weight=600))
            c.add(text(ox + 120, 74, "no venturi: the air keeps", 12, "middle", "ok", weight=600))
            c.add(text(ox + 120, 89, "its temperature; fuel", 12, "middle", "ok", weight=600))
            c.add(text(ox + 120, 104, "evaporates on hot metal", 12, "middle", "ok", weight=600))
            c.add(text(ox + 150, 324, "No chilled air, no carburettor ice.", 12, "middle", "fg", weight=600))
    c.add(text(320, 364, "Either one: the air intake can still collect impact ice (alternate air).", 12, "middle", "fg-muted"))
    return c


# ================================================================ BAKC 3.2 fuels and oils
@chart
def misfuelling_defences() -> Canvas:
    c = Canvas("Layered checks against the wrong fuel",
               "Four overlapping checks, each with gaps: the placard at the filler, the bowser and delivery docket, the nozzle size, and your "
               "fuel sample after refuelling. A mistake that slips through the gaps in one is caught by the next; the sample is the last "
               "layer before the engine. Best of all, be there when the aeroplane is refuelled.", height=400, prefix="mfd")
    Y = 170
    layers = [("1", "Placard", ["grade beside", "each filler"]), ("2", "Bowser, docket", ["read it before", "you sign"]),
              ("3", "Nozzle size", ["jet nozzle too wide:", "a backstop only"]), ("4", "Your fuel sample", ["colour and smell", "after refuelling"])]
    xs = [130, 250, 370, 490]
    slices: list[str] = []
    labels: list[str] = []
    holes = {0: [(Y, 16), (110, 9), (236, 11)], 1: [(Y, 15), (96, 10), (222, 13)], 2: [(Y, 14), (124, 8), (250, 12)], 3: [(112, 12), (232, 10)]}
    for i, (n, name, sub) in enumerate(layers):
        x = xs[i]
        last = i == 3
        fill, stroke = ("ok-soft", "ok") if last else ("surface-2", "fg-muted")
        d = f"M{x - 18} 70 L{x + 26} 56 L{x + 26} 270 L{x - 18} 284 Z"
        for (hy, r) in holes[i]:
            rx_ = r * 0.7
            d += f" M{fmt(x + 4 - rx_)} {hy} a{fmt(rx_)} {r} 0 1 0 {fmt(2 * rx_)} 0 a{fmt(rx_)} {r} 0 1 0 {fmt(-2 * rx_)} 0 Z"
        slices.append(f'<path d="{d}" fill="var(--color-{fill})" fill-rule="evenodd" stroke="var(--color-{stroke})" stroke-width="{SECOND}" stroke-linejoin="round"/>')
        labels.append(badge(x + 4, 304, n, "ok" if last else "neutral", 12))
        labels.append(text(x + 4, 330, name, 13, "middle", "ok" if last else "fg", weight=700))
        labels.append(multiline(x + 4, 346, sub, 11, "middle", "fg-muted"))
    # the mistake
    c.add(text(20, Y - 24, "Wrong fuel", 13, "start", "bad", weight=700))
    c.add(line(20, Y, 476, Y, "bad", 2.5, arrow_end=True))
    c.add(*slices, *labels)
    c.add(line(478, Y - 12, 494, Y + 12, "bad", 3), line(494, Y - 12, 478, Y + 12, "bad", 3))
    c.add(text(546, Y - 4, "caught", 13, "start", "ok", weight=700), text(546, Y + 12, "on the", 13, "start", "ok", weight=700),
          text(546, Y + 28, "ground", 13, "start", "ok", weight=700))
    c.add(text(320, 32, "Each check has gaps; one missed check is caught by the next.", 13, "middle", "fg", weight=600))
    c.add(text(320, 388, "Best of all: be there, and watch which nozzle comes off the truck.", 12, "middle", "fg", weight=600))
    return c


# ================================================================ BAKC 3.3 engine handling
@chart
def shock_cooling_descent() -> Canvas:
    c = Canvas("Cylinder head temperature in a long descent",
               "Qualitative sketch, no scale. Cylinder head temperature against time from the top of descent to the circuit. Closing the "
               "throttle to idle for a long glide makes the CHT fall fast, because the engine makes little heat while the fast airflow "
               "removes a lot; the parts cool at different rates and the stresses can crack cylinders, and the engine ends up cold, rich and "
               "prone to fouling and carburettor ice. A descent with some power kept on, in stages, lets the CHT fall slowly and stay warm.",
               height=380, prefix="scd")
    ch = Chart(c, x=(0, 1), y=(0, 1), box=(64, 50, 600, 300), xlabel="Time in the descent", ylabel="Cylinder head temperature",
               xticks=[], yticks=[], grid=False)
    c.add(ch.axes())
    # too-cold region
    c.add(rect(ch.px(0), ch.py(0.3), ch.right - ch.left, ch.py(0) - ch.py(0.3), "info", None, fill_opacity=0.12))
    c.add(text(ch.right - 8, ch.py(0.06), "too cold: rich, fouling plugs, carburettor ice likely", 12, "end", "info", weight=600))
    # top of descent
    c.add(ch.vline(0.14, "fg-muted", DASH))
    c.add(text(ch.px(0.14) + 6, ch.top + 4, "top of descent", 12, "start", "fg-muted"))
    c.add(text(ch.px(0.07), ch.py(0.78), "cruise", 12, "middle", "fg-muted"))
    glide = [(0.14, 0.72), (0.2, 0.62), (0.27, 0.45), (0.36, 0.32), (0.48, 0.24), (0.7, 0.19), (1, 0.17)]
    staged = [(0.14, 0.72), (0.24, 0.68), (0.4, 0.645), (0.6, 0.61), (0.8, 0.585), (1, 0.57)]
    c.add(ch.curve([(0, 0.72), (0.14, 0.72)], "fg-muted", 2.5, smooth=False))
    c.add(ch.curve(staged, "ok", 2.5))
    c.add(ch.curve(glide, "bad", 2.5))
    c.add(text(ch.px(0.98), ch.py(0.68), "some power on, descending in stages", 13, "end", "ok", weight=700))
    c.add(text(ch.px(0.98), ch.py(0.17) - 10, "idle glide", 13, "end", "bad", weight=700))
    # steep section callout
    x, y = ch.pt(0.25, 0.5)
    c.add(callout(x, y, x + 60, y - 4, ["fast fall: parts cool at different rates,", "stresses that can crack cylinders"], "bad", 12))
    c.add(text(332, 364, "Qualitative: the shape matters, not the numbers. The POH gives the CHT limits.", 11, "middle", "fg-muted"))
    return c


def prop_front(cx: float, cy: float, r: float, colour: str, cls: str | None = None) -> str:
    blades = (path(f"M-5 -8 C-9 -{r * 0.5} -6 -{r} 0 -{r} C6 -{r} 9 -{r * 0.5} 5 -8 Z", colour, f"{colour}-soft" if colour in ("bad", "ok", "brand") else "surface", SECOND) +
              path(f"M-5 8 C-9 {r * 0.5} -6 {r} 0 {r} C6 {r} 9 {r * 0.5} 5 8 Z", colour, f"{colour}-soft" if colour in ("bad", "ok", "brand") else "surface", SECOND))
    inner = group(blades, circle(0, 0, 9, "surface", colour, SECOND), cls=cls)
    return group(inner, transform=f"translate({fmt(cx)} {fmt(cy)})")


@chart
def dead_cut_check() -> Canvas:
    c = Canvas("What the dead-cut check proves",
               "Left: with the switch at OFF, an intact P-lead connects the magneto to earth, it makes no spark and the engine falters: the "
               "switch works. Right: a broken P-lead leaves the magneto unearthed, it keeps sparking with the switch at OFF and the engine keeps "
               "running: the magneto is live and anyone who moves the propeller could start the engine.", height=380, prefix="dcc")
    c.style(".dcc-spin{transform-box:fill-box;transform-origin:center;animation:dcc-turn 1.2s linear infinite}"
            "@keyframes dcc-turn{to{transform:rotate(360deg)}}")
    for k, ox in enumerate((12, 328)):
        good = k == 0
        col_ = "ok" if good else "bad"
        c.add(panel(ox, 16, 300, 348))
        c.add(text(ox + 150, 42, "P-lead intact" if good else "P-lead broken", 16, "middle", "fg", weight=700))
        c.add(text(ox + 150, 62, "switch at OFF", 12, "middle", "fg-muted"))
        # magneto
        c.add(box(ox + 20, 150, 92, 52, ["Magneto"], "brand", 13))
        # switch
        c.add(rect(ox + 150, 86, 76, 36, "surface", "fg", SECOND, rx=6), text(ox + 188, 109, "OFF", 13, "middle", "fg", weight=700, cls="num"))
        c.add(text(ox + 188, 80, "ignition switch", 11, "middle", "fg-muted"))
        # P-lead
        if good:
            c.add(polyline([(ox + 66, 150), (ox + 66, 104), (ox + 150, 104)], "ok", 2.5))
            c.add(polyline([(ox + 188, 122), (ox + 188, 140)], "ok", 2.5), earth(ox + 188, 140, "ok"))
            c.add(text(ox + 74, 132, "P-lead", 12, "start", "ok", weight=700))
            c.add(text(ox + 206, 158, "earth", 11, "start", "ok"))
        else:
            c.add(polyline([(ox + 66, 150), (ox + 66, 104), (ox + 98, 104)], "bad", 2.5), polyline([(ox + 114, 104), (ox + 150, 104)], "fg-muted", 2.5))
            c.add(polyline([(ox + 98, 96), (ox + 102, 112)], "bad", 2), polyline([(ox + 110, 96), (ox + 114, 112)], "fg-muted", 2))
            c.add(polyline([(ox + 188, 122), (ox + 188, 140)], "fg-muted", 2.5), earth(ox + 188, 140, "fg-muted"))
            c.add(text(ox + 74, 132, "break", 12, "start", "bad", weight=700))
        # spark plug lead
        c.add(polyline([(ox + 66, 202), (ox + 66, 236), (ox + 120, 236)], "brand", SECOND))
        c.add(rect(ox + 120, 228, 30, 16, "surface", "fg", SECOND, rx=3), line(ox + 150, 236, ox + 160, 236, "fg", SECOND))
        c.add(text(ox + 135, 262, "plug", 11, "middle", "fg-muted"))
        if good:
            c.add(text(ox + 168, 240, "no spark", 12, "start", "ok", weight=600))
        else:
            c.add(path(f"M{ox + 164} 236 l6 -8 l2 6 l6 -8", "bad", None, MAIN), text(ox + 182, 232, "spark", 12, "start", "bad", weight=600))
        # propeller
        c.add(prop_front(ox + 256, 214, 32, "fg-muted" if good else "bad", None if good else "dcc-spin"))
        c.add(text(ox + 256, 266, "slows" if good else "keeps turning", 11, "middle", "fg-muted" if good else "bad", weight=600))
        # verdict
        lines = (["Engine falters: the switch earths", "this magneto. Back to BOTH,", "then stop it with the mixture."] if good else
                 ["Engine keeps running at OFF:", "the magneto is live. Report it;", "treat the propeller as live."])
        c.add(rect(ox + 14, 284, 272, 68, f"{col_}-soft", None, rx=8))
        c.add(multiline(ox + 150, 304, lines, 13, "middle", f"{col_}-fg", weight=600))
    return c


# ================================================================ BAKC 3.4 malfunctions
def fuel_gauge(cx: float, cy: float, r: float, angle: float, colour: str, cls: str | None = None) -> str:
    """Fuel pressure gauge: a half dial with a green arc; needle at `angle` degrees (0 = left, 180 = right)."""
    out = path(arc_path(cx, cy, r, 180, 360), "fg", "surface", SECOND)
    out += line(cx - r, cy, cx + r, cy, "fg", SECOND)
    out += path(arc_path(cx, cy, r - 7, 225, 315), "ok", None, 5)
    for a in range(180, 361, 30):
        x0, y0 = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
        x1, y1 = cx + (r - 5) * math.cos(math.radians(a)), cy + (r - 5) * math.sin(math.radians(a))
        out += line(x0, y0, x1, y1, "fg-muted", THIN)
    needle = group(line(0, 0, -(r - 12), 0, colour, 2.5), cls=cls)
    out += group(needle, transform=f"translate({fmt(cx)} {fmt(cy)}) rotate({fmt(angle)})")
    out += circle(cx, cy, 4, colour, None)
    return out


@chart
def vapour_lock() -> Canvas:
    c = Canvas("Vapour lock after a hot shutdown",
               "Left: after a hot engine is shut down, heat soaks into the fuel lines and pump with no cooling air, the fuel boils into "
               "vapour, and a pump built for liquid cannot move bubbles, so the fuel pressure flickers and the engine surges or will not start. "
               "Right: the electric booster pump raises the pressure in the lines, pushing the vapour through or collapsing it back into "
               "liquid, and the pressure steadies in the green.", height=380, prefix="vpl")
    c.style(".vpl-flick{transform-origin:0 0;animation:vpl-wobble 2.4s ease-in-out infinite}"
            "@keyframes vpl-wobble{0%{transform:rotate(0deg)}15%{transform:rotate(40deg)}30%{transform:rotate(-20deg)}"
            "48%{transform:rotate(30deg)}62%{transform:rotate(-10deg)}80%{transform:rotate(45deg)}100%{transform:rotate(0deg)}}")
    Y = 150
    for k, ox in enumerate((12, 328)):
        hot = k == 0
        c.add(panel(ox, 16, 300, 348))
        c.add(text(ox + 150, 42, "Hot restart: vapour in the lines" if hot else "Booster pump on: liquid again", 15, "middle", "fg", weight=700))
        # tank
        c.add(rect(ox + 16, 82, 50, 56, "surface", "fg", SECOND, rx=6), rect(ox + 18, 104, 46, 32, "brand-soft", None, rx=4))
        c.add(text(ox + 41, 76, "tank", 11, "middle", "fg-muted"))
        # booster pump
        bcol = "fg-muted" if hot else "brand"
        c.add(polyline([(ox + 41, 138), (ox + 41, Y), (ox + 86, Y)], "brand", 4))
        c.add(circle(ox + 98, Y, 12, "surface" if hot else "brand-soft", bcol, SECOND))
        c.add(text(ox + 98, Y + 30, "booster", 11, "middle", bcol, weight=600), text(ox + 98, Y + 43, "OFF" if hot else "ON", 11, "middle", bcol, weight=700))
        # line to engine pump
        c.add(line(ox + 110, Y, ox + 196, Y, "brand", 4, cap="butt"))
        c.add(circle(ox + 206, Y, 10, "surface", "fg", SECOND))
        c.add(text(ox + 206, Y + 28, "engine", 11, "middle", "fg-muted"), text(ox + 206, Y + 41, "pump", 11, "middle", "fg-muted"))
        c.add(line(ox + 216, Y, ox + 236, Y, "brand", 4, cap="butt"))
        # hot engine
        c.add(rect(ox + 236, 96, 52, 92, "warn-soft", "warn", SECOND, rx=8))
        c.add(multiline(ox + 262, 136, ["hot", "engine"], 11, "middle", "warn-fg", weight=700))
        if hot:
            for x in (ox + 128, ox + 148, ox + 170):
                c.add(heat(x + 12, 106, -10, 32, "bad"))
            c.add(text(ox + 156, 94, "heat soak, no cooling air", 11, "middle", "bad", weight=600))
            for x, r in ((ox + 122, 3), (ox + 136, 2.2), (ox + 150, 3.4), (ox + 166, 2.4), (ox + 180, 3), (ox + 225, 2.4)):
                c.add(circle(x, Y, r, "surface", "brand", THIN))
        else:
            c.add(arrow(ox + 116, Y - 16, ox + 190, Y - 16, "brand", SECOND))
            c.add(text(ox + 152, Y - 24, "pressure up, liquid flows", 11, "middle", "brand", weight=600))
        # gauge
        c.add(fuel_gauge(ox + 150, 266, 50, 50 if hot else 90, "bad" if hot else "ok", "vpl-flick" if hot else None))
        c.add(text(ox + 150, 296, "fuel pressure", 12, "middle", "fg-muted", weight=600))
        c.add(text(ox + 150, 322, "fluctuating: rough running," if hot else "steady in the green", 12, "middle", "bad" if hot else "ok", weight=700))
        c.add(text(ox + 150, 338, "surging, hard to start" if hot else "then the POH hot-start drill", 12, "middle", "bad" if hot else "ok", weight=700 if hot else 400))
    return c


# ================================================================ BAKC 3.5 flight instruments
def bellows(cx: float, cy: float, w: float, h: float, fill: str, stroke: str, folds: int = 3) -> str:
    """Corrugated capsule centred on (cx, cy)."""
    pts_r, pts_l = [], []
    for i in range(folds * 2 + 1):
        y = cy - h / 2 + h * i / (folds * 2)
        dx = w / 2 if i % 2 == 0 else w / 2 - 7
        pts_r.append((cx + dx, y))
        pts_l.append((cx - dx, y))
    pts = pts_r + list(reversed(pts_l))
    return polygon(pts, fill, stroke, SECOND)


def mini_dial(cx: float, cy: float, angle: float) -> str:
    out = circle(cx, cy, 22, "surface", "fg", SECOND)
    for a in range(-150, 151, 50):
        x0, y0 = cx + 22 * math.sin(math.radians(a)), cy - 22 * math.cos(math.radians(a))
        x1, y1 = cx + 17 * math.sin(math.radians(a)), cy - 17 * math.cos(math.radians(a))
        out += line(x0, y0, x1, y1, "fg-muted", THIN)
    out += line(cx, cy, cx + 16 * math.sin(math.radians(angle)), cy - 16 * math.cos(math.radians(angle)), "fg", MAIN)
    out += circle(cx, cy, 2.5, "fg", None)
    return out


@chart
def asi_altimeter_vsi_cutaways() -> Canvas:
    c = Canvas("Inside the three pressure instruments",
               "Airspeed indicator: pitot pressure inside a capsule, static pressure in the case around it, so the capsule moves with the "
               "difference, dynamic pressure. Altimeter: sealed, evacuated aneroid capsules in a case full of static pressure; as static "
               "pressure falls in a climb they expand. Vertical speed indicator: static pressure straight into the capsule and into the case "
               "only through a calibrated leak, so in a climb or descent the case lags and the pressure difference shows the rate.",
               height=410, prefix="pic")
    names = ["Airspeed indicator", "Altimeter", "Vertical speed indicator"]
    for k, ox in enumerate((12, 220, 428)):
        c.add(panel(ox, 16, 200, 378))
        c.add(text(ox + 100, 42, names[k], 14, "middle", "fg", weight=700))
        # case full of static pressure
        c.add(rect(ox + 22, 70, 156, 186, "info", None, rx=10, fill_opacity=0.14), rect(ox + 22, 70, 156, 186, None, "fg", MAIN, rx=10))
        c.add(multiline(ox + 30, 90, ["case:", "static"], 11, "start", "info", weight=600))
        c.add(mini_dial(ox + 100, 100, 40 if k != 2 else 30))
        c.add(line(ox + 100, 122, ox + 100, 150, "fg", SECOND))
        if k == 0:
            c.add(bellows(ox + 100, 178, 84, 52, "brand-soft", "brand"))
            c.add(text(ox + 100, 182, "pitot", 12, "middle", "brand-fg", weight=700))
            c.add(line(ox + 100, 204, ox + 100, 290, "brand", 3))
            c.add(line(ox + 150, 256, ox + 150, 290, "info", 3))
            c.add(text(ox + 100, 306, "pitot", 12, "middle", "brand", weight=700), text(ox + 150, 306, "static", 12, "middle", "info", weight=700))
            lines = ["Static acts inside and out", "and cancels: the capsule", "moves with pitot minus", "static, dynamic pressure."]
        elif k == 1:
            for i, y in enumerate((162, 186, 210)):
                c.add(bellows(ox + 100, y, 84, 20, "surface", "fg", 1))
            c.add(line(ox + 100, 150, ox + 100, 152, "fg", SECOND))
            c.add(text(ox + 100, 238, "sealed, evacuated", 11, "middle", "fg-muted", weight=600))
            c.add(arrow(ox + 40, 186, ox + 40, 156, "fg-muted", SECOND), arrow(ox + 40, 186, ox + 40, 216, "fg-muted", SECOND))
            c.add(line(ox + 150, 256, ox + 150, 290, "info", 3))
            c.add(text(ox + 150, 306, "static", 12, "middle", "info", weight=700))
            lines = ["Climb: static pressure", "falls, the capsules", "expand, the needles", "turn: a barometer."]
        else:
            c.add(bellows(ox + 100, 178, 84, 52, "info-soft", "info"))
            c.add(text(ox + 100, 182, "static", 12, "middle", "info-fg", weight=700))
            c.add(line(ox + 100, 204, ox + 100, 290, "info", 3))
            c.add(polyline([(ox + 100, 274), (ox + 150, 274), (ox + 150, 256)], "info", 3))
            c.add(polygon([(ox + 141, 268), (ox + 159, 268), (ox + 152, 262), (ox + 159, 256), (ox + 141, 256), (ox + 148, 262)], "warn", "warn", THIN))
            c.add(text(ox + 100, 306, "static", 12, "middle", "info", weight=700))
            c.add(multiline(ox + 141, 226, ["calibrated", "leak"], 11, "middle", "warn", weight=700))
            lines = ["The case fills only through", "a calibrated leak and lags:", "the difference shows the", "rate; it lags a few seconds."]
        c.add(multiline(ox + 100, 330, lines, 12, "middle", "fg"))
    return c


def into_page(x: float, y: float, colour: str, r: float = 9) -> str:
    """A force pointing into the page: circle with a cross."""
    d = r * 0.6
    return circle(x, y, r, "surface", colour, MAIN) + line(x - d, y - d, x + d, y + d, colour, MAIN) + line(x - d, y + d, x + d, y - d, colour, MAIN)


@chart
def gyro_rigidity_and_precession() -> Canvas:
    c = Canvas("The two properties of a gyro",
               "Left, rigidity in space: the aeroplane rolls around a spinning rotor, but the rotor's spin axis keeps pointing the same way, "
               "which is what the attitude and directional indicators use. Right, precession: push on the rim of a spinning rotor and it "
               "responds as if the push had been applied 90 degrees further round in the direction of rotation, which is what the turn "
               "coordinator uses.", height=360, prefix="grp")
    # ---- rigidity
    ox = 12
    c.add(panel(ox, 16, 300, 328))
    c.add(text(ox + 150, 42, "Rigidity in space", 16, "middle", "fg", weight=700))
    CX, CY = ox + 150, 180
    def rear(bank: float, colour: str, fill: str | None, dash: str | None = None) -> str:
        """The Cessna 152 from behind in absolute units, rolled by `bank` degrees (left wing down): high wing across the
        cabin roof, struts to the lower fuselage, low tailplane, fin, main wheels. The rotor sits in the cabin."""
        def rot(pts):
            a_ = math.radians(-bank)
            return [(CX + x * math.cos(a_) - y * math.sin(a_), CY + x * math.sin(a_) + y * math.cos(a_)) for x, y in pts]
        def shape(pts, closed: bool = True, width: float = SECOND) -> str:
            d = "M" + " L".join(f"{fmt(x)} {fmt(y)}" for x, y in rot(pts)) + (" Z" if closed else "")
            return path(d, colour, None if dash or not closed else fill, width, dash=dash)
        wing = [(-120, -52), (0, -49), (120, -52), (120, -44), (0, -41), (-120, -44)]
        struts = [[(-12, 14), (-66, -44)], [(12, 14), (66, -44)]]
        legs = [[(-9, 16), (-22, 28)], [(9, 16), (22, 28)]]
        cabin = [(-14, -37), (-10, -41), (10, -41), (14, -37), (14, 14), (10, 18), (-10, 18), (-14, 14)]
        tail = [(-36, 4), (36, 4), (36, 11), (-36, 11)]
        fin = [(-3, -41), (-1, -76), (5, -76), (6, -41)]
        out = shape(wing) + "".join(shape(s_, False) for s_ in struts + legs) + shape(cabin) + shape(tail) + shape(fin)
        for wx in (-22, 22):
            (x_, y_), = rot([(wx, 34)])
            out += circle(x_, y_, 7, None if dash else fill, colour, SECOND, dash=dash)
        return out
    c.add(rear(0, "fg-faint", None, DASH))
    c.add(rear(25, "fg-muted", "surface"))
    c.add(line(CX, CY - 78, CX, CY + 78, "brand", 2.5, dash="6 4"))
    c.add(ellipse(CX, CY, 34, 9, "brand-soft", "brand", MAIN))
    c.add(path(f"M{CX - 30} {CY + 14} Q{CX} {CY + 26} {CX + 30} {CY + 14}", "brand", None, SECOND, arrow_end=True))
    c.add(text(CX - 8, CY - 84, "spin axis stays put", 12, "end", "brand", weight=700))
    c.add(text(ox + 22, 290, "The aeroplane rolls 25° around the", 12, "start", "fg"))
    c.add(text(ox + 22, 306, "rotor; the rotor does not follow.", 12, "start", "fg"))
    c.add(text(ox + 22, 326, "Used by: attitude indicator, DI", 12, "start", "fg-muted", weight=600))
    # ---- precession
    ox = 328
    c.add(panel(ox, 16, 300, 328))
    c.add(text(ox + 150, 42, "Precession", 16, "middle", "fg", weight=700))
    CX, CY, R = ox + 140, 170, 76
    c.add(circle(CX, CY, R, "brand-soft", "brand", MAIN), circle(CX, CY, 6, "brand", None))
    c.add(path(arc_path(CX, CY, R + 16, 200, 250), "brand", None, SECOND, arrow_end=True))
    c.add(text(CX - R - 4, CY - R + 2, "spin", 12, "end", "brand", weight=600))
    # push at 12 o'clock, effect at 3 o'clock (clockwise rotation)
    c.add(into_page(CX, CY - R, "info"))
    c.add(into_page(CX + R, CY, "bad"))
    c.add(path(arc_path(CX, CY, R - 22, 275, 355), "fg-muted", None, SECOND, arrow_end=True))
    c.add(text(CX + 20, CY - 30, "90°", 13, "middle", "fg-muted", weight=700, cls="num"))
    c.add(text(CX + 16, CY - R - 14, "push here", 12, "start", "info", weight=700))
    c.add(multiline(CX + R + 14, CY - 6, ["it acts", "here"], 12, "start", "bad", weight=700))
    c.add(text(ox + 22, 290, "A push into the page at the top acts", 12, "start", "fg"))
    c.add(text(ox + 22, 306, "90° further round, the way it spins.", 12, "start", "fg"))
    c.add(text(ox + 22, 326, "Used by: turn coordinator", 12, "start", "fg-muted", weight=600))
    return c


@chart
def di_drift_and_reset() -> Canvas:
    c = Canvas("Why the directional indicator must be reset",
               "Qualitative sketch. The heading error of the directional indicator grows steadily with time, from friction in its bearings "
               "and gimbals and from the Earth turning beneath a gyro that holds a fixed direction in space. Resetting it to the magnetic "
               "compass about every 10 to 15 minutes, in straight and level flight, brings the error back to zero. Resetting during a turn "
               "copies the compass's turning error into the DI.", height=360, prefix="ddr")
    ch = Chart(c, x=(0, 50), y=(0, 1), box=(70, 50, 600, 270), xlabel="Time (minutes)", ylabel="DI heading error",
               xticks=[0, 15, 30, 45], yticks=[], grid=False)
    c.add(ch.axes())
    k = 0.024
    # sawtooth: reset at 15 and 30 (good); a reset in a turn at ~40 leaves an error
    segs = [((0, 0), (15, 15 * k)), ((15, 0), (30, 15 * k)), ((30, 0), (40, 10 * k))]
    for (a, b) in segs:
        c.add(ch.curve([a, b], "brand", 2.5, smooth=False))
    for t in (15, 30):
        c.add(line(ch.px(t), ch.py(15 * k), ch.px(t), ch.py(0), "ok", MAIN, DASH, arrow_end=True))
        c.add(ch.point(t, 0, "ok"))
    # bad reset in a turn
    e = 0.55
    c.add(line(ch.px(40), ch.py(10 * k), ch.px(40), ch.py(e) + 8, "bad", MAIN, DASH, arrow_end=True))
    c.add(ch.curve([(40, e), (50, e + 10 * k)], "bad", 2.5, smooth=False))
    c.add(ch.point(40, e, "bad"))
    c.add(text(ch.px(7), ch.py(0.42), "drift: friction and", 12, "middle", "brand", weight=600))
    c.add(text(ch.px(7), ch.py(0.42) + 15, "the Earth's rotation", 12, "middle", "brand", weight=600))
    c.add(multiline(ch.px(22.5), ch.py(0.75), ["reset to the compass,", "straight and level"], 12, "middle", "ok", weight=700))
    c.add(line(ch.px(17), ch.py(0.6), ch.px(15.5), ch.py(0.42), "ok", THIN), line(ch.px(28), ch.py(0.6), ch.px(29.5), ch.py(0.42), "ok", THIN))
    c.add(multiline(ch.px(42), ch.py(0.95), ["reset in a turn:", "the compass error", "is copied across"], 12, "middle", "bad", weight=700))
    c.add(text(335, 336, "About every 10 to 15 minutes, and before turning onto a new heading.", 12, "middle", "fg", weight=600))
    return c


# ================================================================ BAKC 5.1 charts
@chart
def chart_scale_comparison() -> Canvas:
    c = Canvas("Chart scale: detail against coverage",
               "Left: the same 10 kilometres on the ground is 1 centimetre on the 1:1,000,000 WAC, 2 centimetres on the 1:500,000 VNC and "
               "4 centimetres on the 1:250,000 VTC. Right: a sheet of the same size covers a quarter of the area at each step from WAC to VNC "
               "to VTC. The smaller the number after the colon, the larger the scale: more detail, less country.",
               height=400, prefix="csc")
    c.add(panel(12, 16, 300, 368), panel(324, 16, 304, 368))
    c.add(text(162, 44, "The same 10 km on each chart", 15, "middle", "fg", weight=700))
    CM = 52
    rows = [("WAC", "1:1,000,000", 1, "fg-muted", "1 cm = 10 km"), ("VNC", "1:500,000", 2, "info", "1 cm = 5 km"),
            ("VTC", "1:250,000", 4, "brand", "1 cm = 2.5 km")]
    for i, (name, scale, n, col_, rule) in enumerate(rows):
        y = 92 + i * 84
        c.add(text(32, y, name, 14, "start", col_ if col_ != "fg-muted" else "fg", weight=700), num(76, y, scale, 13, "start", "fg-muted"))
        c.add(rect(32, y + 14, n * CM, 16, f"{col_}-soft" if col_ != "fg-muted" else "surface", col_ if col_ != "fg-muted" else "fg", SECOND, rx=2))
        for j in range(1, n):
            c.add(line(32 + j * CM, y + 14, 32 + j * CM, y + 30, col_ if col_ != "fg-muted" else "fg", THIN))
        c.add(num(32 + n * CM + 10, y + 27, f"{n} cm", 13, "start", col_ if col_ != "fg-muted" else "fg", weight=700))
        c.add(num(32, y + 50, rule, 12, "start", "fg-muted"))
    c.add(multiline(32, 346, ["Longer on the paper: larger scale,", "more detail. (Bars drawn to ratio.)"], 12, "start", "fg", weight=600))
    # coverage
    c.add(text(476, 44, "What one sheet covers", 15, "middle", "fg", weight=700))
    c.add(text(476, 62, "(same-size sheet)", 11, "middle", "fg-muted"))
    CX, CY = 476, 216
    for side, name, col_ in ((240, "WAC", "fg-muted"), (120, "VNC", "info"), (60, "VTC", "brand")):
        fill = "surface" if col_ == "fg-muted" else f"{col_}-soft"
        c.add(rect(CX - side / 2, CY - side / 2, side, side, fill, col_ if col_ != "fg-muted" else "fg", SECOND, rx=2))
        c.add(text(CX - side / 2 + 6, CY - side / 2 + 16, name, 12, "start", col_ if col_ != "fg-muted" else "fg", weight=700))
    c.add(multiline(476, 356, ["Each step down in the number:", "twice the detail, a quarter of the area."], 12, "middle", "fg", weight=600))
    return c


# ================================================================ BAKC 5.2 documentation
@chart
def prd_listing_anatomy() -> Canvas:
    c = Canvas("Reading an ERSA PRD listing",
               "An illustrative restricted area listing, not a real area: R999 Example Range, surface to 5,000 ft, hours by NOTAM, "
               "controlling authority, conditional status RA2. The letter gives the kind of area: P prohibited, R restricted, D danger. "
               "Each field answers one planning question: am I inside it vertically, is it active, who do I ask, and can I plan through it.",
               height=420, prefix="pla")
    # the listing card
    X, Y, W = 16, 30, 290
    c.add(rect(X, Y, W, 230, "surface", "fg", MAIN, rx=8))
    c.add(rect(X, Y, W, 30, "surface-2", None, rx=8), rect(X, Y + 22, W, 8, "surface-2", None))
    c.add(text(X + W / 2, Y + 20, "ILLUSTRATIVE: NOT A REAL AREA", 11, "middle", "fg-muted", weight=700))
    rows = [("R999", "EXAMPLE RANGE", 62), ("Vertical limits", "SFC – 5000", 104), ("Hours", "NOTAM", 146), ("Controlling authority", "EXAMPLE ATC", 188),
            ("Conditional status", "RA2", 216)]
    rows = [(k, v, yy) for k, v, yy in rows]
    ys = [62, 100, 138, 176, 214]
    for i, ((k, v, _), yy) in enumerate(zip(rows, ys)):
        if i == 0:
            c.add(num(X + 14, Y + yy + 2, k, 18, "start", "brand", weight=700), num(X + 76, Y + yy + 2, v, 14, "start", "fg", weight=700))
        else:
            c.add(text(X + 14, Y + yy, k, 12, "start", "fg-muted"), num(X + 160, Y + yy, v, 13, "start", "fg", weight=700))
        if i < 4:
            c.add(line(X + 10, Y + yy + 16, X + W - 10, Y + yy + 16, "line", THIN))
    notes = [["R: restricted. 999: the number", "printed on the chart beside it"], ["Below 5,000 ft over the area,", "you are inside it"],
             ["Active when? H24, times in UTC,", "or activated by NOTAM"], ["Who can give a clearance,", "and how to contact them"],
             ["RA1 plan through; RA2 plan to", "avoid; RA3 no clearance at all"]]
    cols = ["brand", "fg", "fg", "fg", "warn"]
    for (yy, lines, col_) in zip(ys, notes, cols):
        y = Y + yy - 4
        c.add(line(X + W + 4, y, X + W + 20, y, "fg-muted", THIN), circle(X + W + 4, y, 2.5, "fg-muted", None))
        c.add(multiline(X + W + 26, y - 3, lines, 12, "start", col_, weight=600))
    # letter key
    ky = 284
    for i, (letter, name, rule, col_) in enumerate((("P", "Prohibited", "no flight at any time", "bad"), ("R", "Restricted", "only with a clearance", "warn"),
                                                    ("D", "Danger", "permitted, with a hazard", "info"))):
        x = 16 + i * 206
        c.add(rect(x, ky, 196, 58, f"{col_}-soft", None, rx=8))
        c.add(num(x + 14, ky + 38, letter, 26, "start", f"{col_}-fg", weight=700))
        c.add(text(x + 44, ky + 24, name, 13, "start", f"{col_}-fg", weight=700), text(x + 44, ky + 42, rule, 11, "start", f"{col_}-fg"))
    c.add(text(320, 370, "Chart: where it is and its limits. ERSA PRD: hours, authority, status. NOTAM: changes.", 12, "middle", "fg", weight=600))
    c.add(text(320, 392, "Read the real area's details from the current ERSA.", 11, "middle", "fg-muted"))
    return c


# ================================================================ BAKC 6.1 airworthiness
@chart
def maintenance_release_anatomy() -> Canvas:
    c = Canvas("Where to look on the maintenance release",
               "A schematic of the maintenance release, not a facsimile of the real form. Part 1, the release itself, gives the expiry date "
               "and the expiry time in service, whichever comes first, and any maintenance due within the period. Part 2 records defects and "
               "permissible unserviceabilities. Part 3 holds the daily inspection certifications. The four pre-flight questions: current in "
               "hours and date, daily certified today, no grounding defect, nothing due before you land.", height=520, prefix="mra")
    X, W = 16, 352
    c.add(rect(X, 16, W, 488, "surface", "fg", MAIN, rx=6))
    c.add(text(X + 14, 40, "MAINTENANCE RELEASE", 14, "start", "fg", weight=700), text(X + W - 14, 40, "VH-___", 13, "end", "fg-muted", weight=700, cls="num"))
    c.add(text(X + 14, 58, "Schematic, not a facsimile: real layouts differ", 11, "start", "fg-muted", italic=True))

    def section(y: float, h: float, title: str) -> None:
        c.add(rect(X + 10, y, W - 20, h, None, "line-strong", SECOND, rx=4))
        c.add(rect(X + 10, y, W - 20, 24, "surface-2", None, rx=4))
        c.add(text(X + 20, y + 17, title, 12, "start", "fg", weight=700))

    def field(x: float, y: float, w: float, label: str, colour: str | None = None) -> None:
        if colour:
            c.add(rect(x - 4, y - 14, w, 22, f"{colour}-soft", None, rx=3))
        c.add(text(x, y, label, 12, "start", f"{colour}-fg" if colour else "fg-muted"))
        c.add(line(x + len(label) * 6.6 + 6, y + 3, x + w - 12, y + 3, "fg-faint", THIN, "2 3"))

    # Part 1
    section(70, 168, "Part 1: the release")
    field(X + 22, 116, 150, "Issued: date")
    field(X + 184, 116, 150, "at hours")
    c.add(text(X + 22, 142, "Expires, whichever comes first:", 12, "start", "fg", weight=600))
    field(X + 22, 166, 150, "date", "brand")
    field(X + 184, 166, 150, "hours", "brand")
    c.add(text(X + 22, 194, "Maintenance due within the period:", 12, "start", "fg", weight=600))
    field(X + 22, 218, 312, "item, due at hours / by date", "warn")
    # Part 2
    section(250, 116, "Part 2: defects")
    cols = [X + 22, X + 162, X + 262]
    for x, h_ in zip(cols, ("Defect", "Endorsed", "Cleared / PU")):
        c.add(text(x, 294, h_, 11, "start", "fg-muted", weight=700))
    for y in (316, 340):
        c.add(line(X + 20, y, X + W - 20, y, "line", THIN))
    c.add(text(X + 22, 334, "cabin light u/s", 12, "start", "fg"), text(X + 162, 334, "engineer", 12, "start", "fg"), text(X + 262, 334, "PU", 12, "start", "ok", weight=700))
    c.add(text(X + 22, 358, "PU = permissible unserviceability", 11, "start", "fg-muted"))
    # Part 3
    section(378, 116, "Part 3: daily inspections")
    for x, h_ in zip((X + 22, X + 132, X + 252), ("Date", "Daily certified", "Hours")):
        c.add(text(x, 422, h_, 11, "start", "fg-muted", weight=700))
    c.add(line(X + 20, 430, X + W - 20, 430, "line", THIN))
    c.add(text(X + 22, 448, "yesterday", 12, "start", "fg-muted"), text(X + 132, 448, "signed", 12, "start", "fg-muted"))
    c.add(rect(X + 18, 458, W - 36, 24, "ok-soft", None, rx=3))
    c.add(text(X + 22, 475, "today", 12, "start", "ok-fg", weight=700), text(X + 132, 475, "signed?", 12, "start", "ok-fg", weight=700))
    # the four questions
    qx = 392
    qs = [(166, "1", "brand", ["Current in hours", "AND date?"], 166),
          (218, "4", "warn", ["Anything due before", "you land? Hours now", "+ flight time."], 236),
          (334, "3", "bad", ["A defect that grounds", "it? Uncleared: no go.", "A PU may add conditions."], 334),
          (475, "2", "ok", ["Daily certified", "for today?"], 466)]
    for y_field, n, col_, lines, ty in qs:
        c.add(line(X + W - 2, y_field - 4, qx + 6, ty - 4, "fg-muted", THIN))
        c.add(circle(qx + 16, ty - 4, 12, f"{col_}-soft", col_, SECOND), text(qx + 16, ty + 1, n, 13, "middle", f"{col_}-fg", weight=700, cls="num"))
        c.add(multiline(qx + 36, ty, lines, 12, "start", "fg", weight=600))
    c.add(multiline(qx, 50, ["Four questions", "before every flight"], 15, "start", "fg", weight=700))
    c.add(multiline(qx, 96, ["A no to 1 or 2, or a yes", "to 3 or 4: not serviceable", "for that flight."], 12, "start", "fg-muted"))
    return c


# ================================================================ BAKC 6.3 speed limitations
@chart
def va_vs_weight() -> Canvas:
    c = Canvas("Why VA is lower when the aeroplane is lighter",
               "Load factor against indicated airspeed. The stall curve at maximum weight, stall speed 52 kt, meets the +3.8 g limit at "
               "VA = 52 × √3.8 ≈ 101 kt. At 80 percent of maximum weight the aeroplane stalls at a lower speed, its stall curve sits to the "
               "left, and it meets +3.8 g at about 101 × √0.8 ≈ 90 kt. Between 90 and 101 kt a full pull stalls the heavy aeroplane first "
               "but can overstress the light one.", height=380, prefix="vaw")
    VS_H = 52.0
    VS_L = VS_H * math.sqrt(0.8)
    ch = Chart(c, x=(0, 140), y=(0, 5), box=(70, 40, 600, 300), xlabel="Indicated airspeed (kt)", ylabel="Load factor (g)",
               xticks=[0, 20, 40, 60, 80, 100, 120, 140], yticks=[0, 1, 2, 3, 4, 5])
    c.add(ch.axes())
    va_h, va_l = VS_H * math.sqrt(3.8), VS_L * math.sqrt(3.8)
    c.add(ch.band(va_l, va_h, "warn", 0.16))
    c.add(ch.hline(3.8, "bad", None))
    c.add(line(ch.px(0), ch.py(3.8), ch.px(140), ch.py(3.8), "bad", MAIN))
    c.add(text(ch.px(139), ch.py(3.8) - 8, "+3.8 g limit", 13, "end", "bad", weight=700))
    for vs, colour in ((VS_H, "info"), (VS_L, "brand")):
        va = vs * math.sqrt(3.8)
        c.add(ch.curve(sample(lambda v: (v / vs) ** 2, vs, va, 40), colour, 2.5))
        c.add(ch.curve(sample(lambda v: (v / vs) ** 2, va, vs * math.sqrt(5), 10), colour, SECOND, dash=DASH))
        c.add(ch.point(vs, 1, colour, r=3.5))
    c.add(line(ch.px(va_h), ch.py(3.8), ch.px(va_h), ch.py(0), "info", THIN, DASH), line(ch.px(va_l), ch.py(3.8), ch.px(va_l), ch.py(0), "brand", THIN, DASH))
    c.add(ch.point(va_h, 3.8, "info"), ch.point(va_l, 3.8, "brand"))
    c.add(badge(ch.px(va_h) + 26, ch.py(0) - 14, "101 kt", "info", 12), badge(ch.px(va_l) - 26, ch.py(0) - 14, "90 kt", "brand", 12))
    # curve labels
    c.add(multiline(ch.px(56), ch.py(0.72), ["maximum weight,", "VS 52 kt"], 12, "start", "info", weight=700))
    c.add(multiline(ch.px(34), ch.py(2.3), ["80% of", "maximum weight"], 12, "end", "brand", weight=700))
    c.add(line(ch.px(35), ch.py(2.15), ch.px(66), ch.py(2.05), "brand", THIN))
    c.add(multiline(ch.px(104), ch.py(2.7), ["90 to 101 kt:", "the heavy one", "stalls first; the", "light one can be", "overstressed"], 12, "start", "warn-fg", weight=600))
    c.add(text(335, 368, "VA = VS × √3.8 = 52 × 1.95 ≈ 101 kt;   lighter: 101 × √0.8 ≈ 90 kt", 13, "middle", "fg", weight=600, cls="num"))
    return c


# ================================================================ BAKC 6.4 weight and balance
@chart
def tail_download_cg() -> Canvas:
    c = Canvas("How CG position changes the tail's job",
               "Two side views. Forward CG: the CG is well ahead of the centre of lift, so the tail must push down hard; the wing must carry "
               "the weight plus that download, so it flies at a higher angle of attack and stalls at a higher speed, but the long distance to "
               "the tail makes it very stable. Aft CG: the CG is close to the centre of lift, the tail pushes down only lightly and the wing "
               "carries less, so the stall speed is lower, but the tail's leverage over the CG is short and the restoring moment weak: less "
               "stable, light and over-sensitive in pitch.", height=420, prefix="tdc")
    for k, oy in enumerate((16, 214)):
        fwd = k == 0
        c.add(panel(12, oy, 616, 190))
        c.add(text(616, oy + 26, "CG forward" if fwd else "CG aft", 16, "end", "fg", weight=700))
        PY = oy + 108
        c.add(plane_side(210, PY, 2.0, color="fg-faint", gear=False))
        CL = 212  # centre of lift, about a quarter of the way back from the wing's leading edge (local x 7.8, chord 28)
        CG = CL + (34 if fwd else 10)
        TAIL = 87  # mid tailplane (local x -61.5)
        W_ = 36
        td = 20 if fwd else 6
        # lift = weight + download, from the high wing (local y -10)
        L = W_ + td
        WY = PY - 20
        c.add(arrow(CL, WY, CL, WY - L, "brand", 2.5))
        c.add(text(CL - 8, WY - L + 10, "lift", 13, "end", "brand", weight=700))
        # weight from CG
        c.add(arrow(CG, PY + 6, CG, PY + 6 + W_, "fg", 2.5))
        c.add(circle(CG, PY, 6, "surface", "fg", MAIN), line(CG - 6, PY, CG + 6, PY, "fg", THIN), line(CG, PY - 6, CG, PY + 6, "fg", THIN))
        c.add(text(CG + 10, PY + 6 + W_ - 6, "weight", 13, "start", "fg", weight=700))
        # tail download
        c.add(arrow(TAIL, PY + 10, TAIL, PY + 10 + td * 1.4, "info", 2.5))
        c.add(text(TAIL - 8, PY + 10 + td * 1.4 + 12, "tail download", 12, "middle", "info", weight=700))
        # tail arm
        ya = PY + 54
        c.add(line(TAIL, ya, CG, ya, "info", THIN), line(TAIL, ya - 4, TAIL, ya + 4, "info", THIN), line(CG, ya - 4, CG, ya + 4, "info", THIN))
        c.add(text((TAIL + CG) / 2 + 10, ya + 16, "tail arm: " + ("long" if fwd else "shorter"), 11, "middle", "info", weight=600))
        c.add(text(330, oy + 38, "lift = weight + download", 12, "start", "brand", weight=600))
        c.add(text(330, oy + 54, "download " + ("large" if fwd else "small"), 12, "start", "info", weight=600))
        # verdict
        X = 330
        lines = (["Very stable, heavy in pitch", "Higher stall speed", "More trim drag", "May lack elevator to flare"] if fwd else
                 ["Less stable, light and twitchy", "Lower stall speed", "Easy to over-rotate", "Stall or spin recovery may fail"])
        cols = (["ok", "bad", "warn", "bad"] if fwd else ["bad", "ok", "warn", "bad"])
        for i, (s_, cc) in enumerate(zip(lines, cols)):
            c.add(circle(X + 4, oy + 96 + i * 22, 4, cc, None), text(X + 16, oy + 101 + i * 22, s_, 13, "start", "fg"))
    return c
