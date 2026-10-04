"""RMTC (meteorology) diagrams: local weather, forecasts and reports, significance of observations.
Numbers and names come from content/notes/RMTC/. Sea to the west is on the left (Western Australia)."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, badge, circle, fmt, group, line, multiline, num, path,
                                plane_side, polygon, polyline, rect, smooth_path, text)


# ---------------------------------------------------------------- local helpers
def canvas(*args, **kw) -> Canvas:
    """Canvas whose shared arrow marker uses orient="auto": no diagram here uses marker-start, and the PNG renderer
    (resvg) ignores "auto-start-reverse", drawing every head pointing right."""
    c = Canvas(*args, **kw)
    c.defs[0] = c.defs[0].replace('orient="auto-start-reverse"', 'orient="auto"')
    return c


def arrow(x1: float, y1: float, x2: float, y2: float, color: str = "brand", width: float = MAIN, dash: str | None = None, cls: str | None = None) -> str:
    """Straight arrow drawn as a <path> (marker orientation on <line> is unreliable in some renderers)."""
    return path(f"M{fmt(x1)} {fmt(y1)} L{fmt(x2)} {fmt(y2)}", color, None, width, dash, cls=cls, arrow_end=True)


def cumulus(x0: float, base: float, x1: float, tops: list[float], stroke: str = "fg-muted", fill: str = "surface", width: float = SECOND,
            cls: str | None = None, flat: bool = True) -> str:
    """Cumulus outline: a flat base from x0 to x1 and a row of rounded bumps whose peaks are at heights `tops` above the base."""
    n = len(tops)
    xs = [x0 + (x1 - x0) * (i + 0.5) / n for i in range(n)]
    pts = [(x0, base)] + [(x, base - t) for x, t in zip(xs, tops)] + [(x1, base)]
    d = f"M{fmt(pts[0][0])} {fmt(pts[0][1])}"
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        r = math.hypot(bx - ax, by - ay) * 0.62
        d += f" A{fmt(r)} {fmt(r)} 0 0 1 {fmt(bx)} {fmt(by)}"
    d += " Z" if flat else ""
    return path(d, stroke, fill, width, cls=cls)


def sun(x: float, y: float, r: float = 14, color: str = "warn") -> str:
    rays = "".join(line(x + (r + 5) * math.cos(a), y + (r + 5) * math.sin(a), x + (r + 12) * math.cos(a), y + (r + 12) * math.sin(a), color, SECOND)
                   for a in [i * math.pi / 4 for i in range(8)])
    return circle(x, y, r, f"{color}-soft", color, SECOND) + rays


def moon(x: float, y: float, r: float = 12) -> str:
    return path(f"M{fmt(x + r * 0.3)} {fmt(y - r)} A{r} {r} 0 1 0 {fmt(x + r * 0.3)} {fmt(y + r)} A{r * 0.8} {r * 0.8} 0 1 1 {fmt(x + r * 0.3)} {fmt(y - r)} Z",
                "fg-muted", "surface-2", SECOND)


def ground(points: list[tuple[float, float]], bottom: float, fill: str = "surface-2", stroke: str = "fg-muted") -> str:
    d = smooth_path(points) + f" L{fmt(points[-1][0])} {fmt(bottom)} L{fmt(points[0][0])} {fmt(bottom)} Z"
    return path(d, None, fill, 0) + path(smooth_path(points), stroke, None, SECOND)


def along(pts: list[tuple[float, float]], n: int = 24) -> list[tuple[float, float, float]]:
    """Resample a smooth Catmull-Rom curve through pts into n+1 (x, y, screen angle) samples by arc length."""
    ext = [pts[0]] + list(pts) + [pts[-1]]
    dense = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(20):
            t = k / 20
            t2, t3 = t * t, t * t * t
            dense.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    dense.append(pts[-1])
    cum = [0.0]
    for a, b in zip(dense, dense[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    out, j = [], 0
    for k in range(n + 1):
        target = cum[-1] * k / n
        while j < len(cum) - 2 and cum[j + 1] < target:
            j += 1
        a, b = dense[j], dense[j + 1]
        f = (target - cum[j]) / ((cum[j + 1] - cum[j]) or 1)
        x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        out.append((x, y, ang))
    return out


def mover(prefix: str, pts: list[tuple[float, float]], seconds: float, static_at: float, body_fn, n: int = 24, rotate: bool = True,
          fade: bool = True) -> tuple[str, str]:
    """One element moving along a smooth path with transform keyframes (no offset-path, so static renders stay sensible).
    body_fn(angle) returns the element drawn at the origin. static_at (0..1) picks where it sits when not animated.
    Returns (css, markup)."""
    samples = along(pts, n)
    si = round(static_at * n)
    sx, sy, sa = samples[si]
    frames = []
    for k, (x, y, a) in enumerate(samples):
        pct = 100 * k / n
        rot = f" rotate({fmt(a - sa)}deg)" if rotate else ""
        op = ";opacity:0" if fade and k in (0, n) else (";opacity:1" if fade else "")
        frames.append(f"{fmt(pct)}%{{transform:translate({fmt(x - sx)}px,{fmt(y - sy)}px){rot}{op}}}")
    css = (f".{prefix}-mv{{animation:{prefix}-mv {seconds}s linear infinite;transform-origin:0 0}}\n"
           f"@keyframes {prefix}-mv{{{''.join(frames)}}}")
    markup = group(group(body_fn(sa), cls=f"{prefix}-mv"), transform=f"translate({fmt(sx)} {fmt(sy)})")
    return css, markup


# ================================================================ RMTC 2.1 local weather
@chart
def thunderstorm_hazards() -> Canvas:
    c = canvas("Thunderstorm hazards and the stand-off distance",
               "Side view of a mature thunderstorm cell with an anvil top. Inside and near the cell: severe turbulence, hail, lightning, icing in "
               "the cloud and heavy rain. Beneath it a microburst downdraught hits the ground and spreads out as a gust front ahead of the storm, "
               "causing wind shear on take-off and landing. A light aeroplane stays at least 10 nm from a mature cell and never flies under the anvil.",
               height=440, prefix="ths")
    c.style(""".ths-flow{stroke-dasharray:7 7;animation:ths-flow 1s linear infinite}
@keyframes ths-flow{to{stroke-dashoffset:-14}}""")
    G = 372
    c.add(text(320, 28, "A mature thunderstorm cell", 16, "middle", "fg", weight=700))
    c.add(text(320, 46, "moisture + instability + a trigger that lifts the air", 12, "middle", "fg-muted"))
    # anvil and tower
    cell = ("M262 300 C248 300 240 284 248 268 C232 254 240 228 258 224 C250 200 262 176 282 176 C280 150 296 132 316 136 "
            "C318 116 330 100 344 96 L330 84 C360 78 470 74 600 86 C620 90 616 100 596 104 C540 112 470 114 420 118 "
            "C424 136 430 150 424 162 C446 170 450 196 438 210 C456 222 454 252 436 262 C444 280 432 300 414 300 Z")
    c.add(path(cell, "fg-muted", "surface-2", SECOND))
    c.add(text(520, 70, "anvil", 13, "middle", "fg-muted", weight=600))
    # under the anvil: a no-go zone
    c.add(path("M458 116 L596 105 L596 210 L458 210 Z", None, "bad", 0, fill_opacity=0.1))
    c.add(multiline(527, 150, ["never fly", "under the anvil"], 13, "middle", "bad", weight=600))
    # hazards inside
    c.add(text(340, 160, "severe turbulence", 13, "middle", "bad", weight=600))
    c.add(text(340, 176, "and icing in cloud", 12, "middle", "fg-muted"))
    for hx, hy in ((300, 200), (316, 214), (290, 222), (330, 230), (306, 236)):
        c.add(circle(hx, hy, 3.5, "surface", "info", SECOND))
    c.add(text(268, 214, "hail", 12, "end", "info", weight=600))
    c.add(polygon([(392, 188), (378, 214), (390, 214), (378, 244), (402, 206), (390, 206), (400, 188)], "warn-soft", "warn", SECOND))
    c.add(text(408, 236, "lightning", 12, "start", "warn-fg", weight=600))
    # rain shafts
    for x in (262, 278, 294):
        c.add(line(x, 306, x - 10, 360, "sky-fg", THIN, dash=DASH))
    c.add(text(248, 330, "heavy rain:", 12, "end", "sky-fg", weight=600))
    c.add(text(248, 345, "destroys visibility", 12, "end", "sky-fg"))
    # microburst downdraught and outflow
    MX = 350
    c.add(line(MX, 300, MX, 350, "bad", MAIN, cls="ths-flow"))
    c.add(path(f"M{MX} 352 Q{MX} 364 {MX + 24} 364 L{MX + 110} 364", "bad", None, MAIN, cls="ths-flow", arrow_end=True))
    c.add(path(f"M{MX} 352 Q{MX} 364 {MX - 24} 364 L{MX - 60} 364", "bad", None, MAIN, cls="ths-flow", arrow_end=True))
    c.add(path(f"M{MX + 112} 364 C{MX + 138} 362 {MX + 144} 336 {MX + 122} 330", "bad", None, SECOND, arrow_end=True))
    c.add(multiline(MX + 8, 318, ["microburst", "downdraught"], 12, "start", "bad", weight=600))
    c.add(multiline(MX + 160, 316, ["gust front:", "wind shear on", "take-off and", "landing"], 12, "start", "bad"))
    c.add(line(30, G, 610, G, "fg-muted", SECOND))
    # stand-off
    c.add(plane_side(70, 226, 0.42))
    c.add(arrow(170, 250, 104, 250, "brand", MAIN), arrow(170, 250, 238, 250, "brand", MAIN))
    c.add(text(170, 240, "at least 10 nm", 13, "middle", "brand", weight=700, cls="num"))
    c.add(text(170, 272, "from a mature cell,", 12, "middle", "brand-fg"))
    c.add(text(170, 287, "more from a severe one", 12, "middle", "brand-fg"))
    c.add(text(320, 400, "Never try to fly through a line of storms. Storms forecast for your arrival: land early or go elsewhere.", 12, "middle", "fg-muted"))
    c.add(text(320, 418, "Schematic; not to scale.", 11, "middle", "fg-faint"))
    return c


@chart
def low_cloud_and_rising_terrain() -> Canvas:
    c = canvas("Squeezed between low cloud and rising ground",
               "Side view: a VFR aeroplane flies inland under a cloud base that lowers ahead while the ground rises towards hills. The gap between "
               "cloud and terrain narrows until there is no room to stay clear of cloud and above the minimum height. The safe choice is to turn back "
               "early while there is still room; pressing on under the cloud (scud running) into rising ground is a leading cause of fatal VFR accidents.",
               height=400, prefix="lct")
    c.style(""".lct-base{animation:lct-lower 6s ease-in-out infinite alternate}
@keyframes lct-lower{from{transform:translateY(0)}to{transform:translateY(14px)}}""")
    c.add(text(320, 28, "Low cloud ahead, rising ground below", 16, "middle", "fg", weight=700))
    # cloud layer: base lowers from left to right (animated: the whole layer sinks a little)
    base = [(20, 96), (140, 104), (260, 124), (380, 160), (500, 196), (620, 214)]
    d = smooth_path(base) + " L620 44 L20 44 Z"
    c.add(group(path(d, "fg-muted", "surface-2", SECOND), cls="lct-base"))
    c.add(text(110, 76, "low stratus: the base is lowering ahead", 13, "start", "fg-muted", weight=600))
    # terrain rising to the right
    terrain = [(20, 340), (160, 336), (280, 320), (380, 286), (470, 246), (540, 222), (620, 210)]
    c.add(ground(terrain, 392))
    c.add(text(300, 356, "rising terrain", 13, "middle", "fg-muted", weight=600))
    c.add(line(150, 109, 150, 330, "fg-faint", THIN, dash=DASH))
    c.add(text(158, 300, "plenty of room here", 12, "start", "fg-muted"))
    # the safe choice: turn back early (brand)
    c.add(path("M100 232 L280 232 C330 232 340 200 318 188 C300 178 260 194 230 196 L130 196", "brand", None, MAIN, arrow_end=True))
    c.add(badge(230, 166, "turn back early", "brand", 13))
    c.add(text(200, 258, "while you can still see a way out", 12, "middle", "brand-fg"))
    c.add(plane_side(64, 232, 0.4))
    # pressing on: scud running into the squeeze (bad)
    c.add(path("M300 234 C380 236 450 226 500 218", "bad", None, MAIN, dash="7 5"))
    c.add(path("M502 206 L522 226 M522 206 L502 226", "bad", None, MAIN))
    c.add(multiline(424, 290, ["press on (scud running)", "and you are trapped", "between cloud and terrain"], 12, "start", "bad", weight=600))
    c.add(text(320, 384, "Turn back while there is room, not when the gap has closed.", 13, "middle", "fg", weight=600))
    return c


@chart
def radiation_fog_overnight() -> Canvas:
    c = canvas("How fog forms overnight and clears",
               "Four panels from evening to mid-morning. Evening: clear sky, calm, humid air. Overnight: the ground radiates its heat to the clear sky "
               "and the air touching it cools to its dew point. Dawn: fog lies in the river valleys and along the coast. Mid-morning: the sun heats "
               "the ground and the fog clears.", height=350, prefix="rfg")
    c.add(text(320, 28, "Fog on a still, clear, humid winter morning", 16, "middle", "fg", weight=700))
    W, top, Hp = 144, 52, 168
    panels = [("Evening", ["clear sky, calm wind,", "humid air"]),
              ("Overnight", ["the ground radiates heat;", "air touching it cools", "to its dew point"]),
              ("Dawn", ["fog in the valleys", "and along the coast"]),
              ("Mid-morning", ["the sun heats the", "ground; fog clears"])]
    for i, (head, lines) in enumerate(panels):
        x = 16 + i * (W + 12)
        night = i in (1, 2)
        gy = top + Hp
        c.add(rect(x, top, W, Hp, "surface-2" if night else "sky-soft", None, rx=8))
        if i == 2:  # fog bank drawn first so the ground hides its lower edge
            c.add(rect(x + 18, gy - 58, W - 36, 44, "brand-soft", "brand", SECOND, rx=14))
        g = [(x, gy - 46), (x + 36, gy - 44), (x + 60, gy - 22), (x + 84, gy - 22), (x + 108, gy - 44), (x + W, gy - 48)]
        c.add(path(smooth_path(g) + f" L{x + W} {gy} L{x} {gy} Z", "fg-muted", "surface", SECOND))
        if i == 0:
            c.add(sun(x + W - 30, gy - 70, 12, "warn"))
            c.add(text(x + 12, top + 26, "sunset", 12, "start", "fg-muted"))
        elif i == 1:
            c.add(moon(x + W - 30, top + 26, 11))
            for sx, sy in ((x + 20, top + 20), (x + 50, top + 34), (x + 84, top + 16)):
                c.add(circle(sx, sy, 1.8, "fg-muted", None))
            for wx in (x + 24, x + 72, x + 120):
                c.add(path(f"M{wx} {gy - 54} q-5 -7 0 -14 q5 -7 0 -14 q-5 -7 0 -14", "info", None, SECOND, arrow_end=True))
            c.add(text(x + W / 2, top + 64, "heat radiates away", 12, "middle", "info", weight=600))
        elif i == 2:
            c.add(sun(x + 26, top + 70, 9, "warn"))
            c.add(text(x + 72, gy - 32, "fog", 13, "middle", "brand-fg", weight=700))
        else:
            c.add(sun(x + W / 2, top + 40, 13, "warn"))
            for wx in (x + 30, x + 72, x + 114):
                c.add(arrow(wx, gy - 56, wx, gy - 86, "warn", SECOND))
        c.add(badge(x + W / 2, top + Hp + 22, head, "brand" if i == 2 else "neutral", 13))
        c.add(multiline(x + W / 2, top + Hp + 48, lines, 12, "middle", "fg-muted", leading=1.3))
        if i < 3:
            c.add(arrow(x + W + 1, top + Hp / 2, x + W + 11, top + Hp / 2, "fg-faint", SECOND))
    c.add(text(320, 338, "Common in the south-west's river valleys and along the coast; it usually clears by mid-morning.", 12, "middle", "fg-faint"))
    return c


@chart
def rotor_in_the_lee_of_the_scarp() -> Canvas:
    c = canvas("Mechanical turbulence in the lee of hills and buildings",
               "West-east cross-section near Perth in a strong easterly wind. The wind flows across the plateau, over the edge of the Darling Scarp "
               "and down onto the coastal plain, where it rolls into a rotor of tumbling, turbulent air on the lee (western) side of the scarp. "
               "On a smaller scale the same happens downwind of a hangar, buildings and trees.", height=406, prefix="mts")
    c.style(""".mts-spin{animation:mts-spin 3s linear infinite;transform-box:fill-box;transform-origin:center}
@keyframes mts-spin{to{transform:rotate(-360deg)}}""")
    c.add(text(320, 28, "A strong easterly over the Darling Scarp", 16, "middle", "fg", weight=700))
    G = 318
    terrain = [(20, G), (200, G - 2), (330, G - 4), (390, G - 20), (430, G - 78), (470, G - 112), (530, G - 120), (620, G - 122)]
    c.add(ground(terrain, 372))
    c.add(text(30, G + 20, "coastal plain (Perth)", 12, "start", "fg-muted", weight=600))
    c.add(text(560, 230, "plateau", 12, "middle", "fg-muted"))
    c.add(text(470, 290, "Darling Scarp", 13, "middle", "fg-muted", weight=600))
    c.add(text(28, 64, "W", 13, "start", "fg-faint", weight=700), text(612, 64, "E", 13, "end", "fg-faint", weight=700))
    # wind: easterly, blowing to the left
    c.add(arrow(600, 72, 470, 72, "sky-fg", MAIN))
    c.add(text(462, 76, "strong easterly wind", 13, "end", "sky-fg", weight=600))
    # streamlines: smooth over the plateau, dipping down the lee slope
    for pts in ([(620, 172), (520, 170), (470, 174), (420, 206), (370, 230), (300, 214), (220, 184), (120, 172), (40, 172)],
                [(620, 136), (520, 135), (460, 140), (400, 166), (340, 176), (260, 160), (160, 140), (40, 136)],
                [(620, 100), (500, 100), (420, 112), (340, 122), (240, 110), (140, 102), (40, 100)]):
        c.add(path(smooth_path(pts), "sky-fg", None, SECOND))
        c.add(arrow(76, pts[-1][1], 40, pts[-1][1], "sky-fg", SECOND))
    # rotor at the foot of the scarp (brand, spinning anticlockwise on screen: wind over the top to the left, back towards the hill underneath)
    RX, RY, R = 352, G - 46, 32
    rotor = (path(f"M{RX + R} {RY} A{R} {R} 0 0 0 {RX - R * 0.5} {RY - R * 0.87}", "brand", None, MAIN, arrow_end=True)
             + path(f"M{RX - R} {RY} A{R} {R} 0 0 0 {RX + R * 0.5} {RY + R * 0.87}", "brand", None, MAIN, arrow_end=True)
             + path(f"M{RX + 16} {RY} A16 16 0 0 0 {RX - 8} {RY - 14}", "brand", None, SECOND, arrow_end=True)
             + circle(RX, RY, R + 2, "none", None))
    c.add(group(rotor, cls="mts-spin"))
    c.add(multiline(RX - 46, RY - 14, ["rotor:", "violent turbulence", "on the lee side"], 13, "end", "brand", weight=600))
    # hangar with eddies on its lee side
    HX = 90
    c.add(rect(HX, G - 34, 50, 34, "surface", "fg-muted", SECOND))
    c.add(path(f"M{HX - 2} {G - 34} L{HX + 25} {G - 46} L{HX + 52} {G - 34}", "fg-muted", None, SECOND))
    for ex, ey, r in ((HX - 18, G - 22, 10), (HX - 46, G - 16, 8)):
        c.add(path(f"M{ex + r} {ey} A{r} {r} 0 1 0 {ex} {ey + r}", "brand", None, SECOND, arrow_end=True))
    c.add(text(30, G + 40, "smaller eddies downwind of hangars, buildings and trees", 12, "start", "fg-muted"))
    c.add(text(320, 394, "In strong winds, expect turbulence in the lee of anything the wind flows over.", 12, "middle", "fg-faint"))
    return c


# ================================================================ RMTC 2.2 forecasts and reports
CW = 9.6  # generous advance per character at size 14 (fits JetBrains Mono and the sans fallback)


def code_row(x: float, y: float, tokens: list[str], hi: set[int] = frozenset(), gap: float = 10, size: float = 14) -> tuple[str, list[tuple[float, float]]]:
    """A row of code groups, each in its own box, centred text (so alignment does not depend on the exact font).
    Returns markup and the (left, right) extent of each box. Indices in hi are drawn in brand colour."""
    out, spans = [], []
    for i, t in enumerate(tokens):
        w = len(t) * CW + 12
        b = i in hi
        out.append(rect(x, y - 15, w, 26, "brand-soft" if b else "surface", "brand" if b else "line-strong", THIN, rx=5))
        out.append(num(x + w / 2, y + 3, t, size, "middle", "brand-fg" if b else "fg", weight=700 if b else 600))
        spans.append((x, x + w))
        x += w + gap
    return "".join(out), spans


def tag(spans: list[tuple[float, float]], i: int, j: int, y_box: float, lines: list[str], above: bool, color: str = "fg", dist: float = 26) -> str:
    """Bracket from box i..j to a two-line label above or below the code row."""
    x0, x1 = spans[i][0], spans[j][1]
    cx = (x0 + x1) / 2
    if above:
        yb = y_box - 15
        out = path(f"M{x0 + 2} {yb - 4} L{x0 + 2} {yb - 8} L{x1 - 2} {yb - 8} L{x1 - 2} {yb - 4}", "fg-faint", None, THIN) if j > i else ""
        out += line(cx, yb - 4 - (4 if j > i else 0), cx, yb - dist + 6, "fg-faint", THIN)
        return out + multiline(cx, yb - dist - 16 * (len(lines) - 1), lines, 12, "middle", color, leading=1.3)
    yb = y_box + 11
    out = path(f"M{x0 + 2} {yb + 4} L{x0 + 2} {yb + 8} L{x1 - 2} {yb + 8} L{x1 - 2} {yb + 4}", "fg-faint", None, THIN) if j > i else ""
    out += line(cx, yb + 4 + (4 if j > i else 0), cx, yb + dist - 6, "fg-faint", THIN)
    return out + multiline(cx, yb + dist + 8, lines, 12, "middle", color, leading=1.3)


@chart
def taf_anatomy() -> Canvas:
    c = canvas("Anatomy of a TAF",
               "The Jandakot TAF from the note, group by group. TAF YPJT: aerodrome forecast for Jandakot. 030400Z: issued on the 3rd at 0400 UTC. "
               "0306/0318: valid 0600 to 1800 UTC on the 3rd. 12012KT: wind 120 degrees true at 12 knots. 9999: visibility 10 km or more. "
               "FEW030 SCT045: few cloud at 3,000 ft and scattered at 4,500 ft above the aerodrome. FM031000 09008KT CAVOK: from 1000 UTC a "
               "permanent change to wind 090 at 8 knots and CAVOK. TEMPO 0306/0309 4000 SHRA BKN020: between 0600 and 0900 UTC temporary spells "
               "of 4,000 m in showers of rain with broken cloud at 2,000 ft. T and Q: temperatures and QNH at 3-hourly intervals.",
               height=530, prefix="taf")
    c.add(text(320, 28, "Reading a TAF, group by group", 16, "middle", "fg", weight=700))
    c.add(text(320, 46, "the example from the note; all times UTC", 12, "middle", "fg-muted"))
    Y1 = 156
    row, sp = code_row(16, Y1, ["TAF", "YPJT", "030400Z", "0306/0318", "12012KT", "9999", "FEW030", "SCT045"])
    c.add(row)
    c.add(tag(sp, 0, 0, Y1, ["aerodrome", "forecast"], False))
    c.add(tag(sp, 1, 1, Y1, ["aerodrome", "(Jandakot)"], True))
    c.add(tag(sp, 3, 3, Y1, ["valid 0600 to", "1800 UTC on the 3rd"], True))
    c.add(tag(sp, 5, 5, Y1, ["visibility", "10 km or more"], True))
    c.add(tag(sp, 2, 2, Y1, ["issued on the 3rd", "at 0400 UTC"], False))
    c.add(tag(sp, 4, 4, Y1, ["wind 120° true", "at 12 kt"], False))
    c.add(tag(sp, 6, 7, Y1, ["cloud above the aerodrome:", "FEW 3,000 ft", "SCT 4,500 ft"], False))
    c.add(line(30, 246, 610, 246, "line", THIN))
    c.add(text(30, 268, "Change groups: what happens later in the period", 13, "start", "brand-fg", weight=700))
    # FM line
    Y2 = 298
    row, sp = code_row(40, Y2, ["FM031000", "09008KT", "CAVOK"], {0})
    c.add(row)
    c.add(text(sp[-1][1] + 14, Y2 + 4, "from 1000 UTC, a permanent change", 12, "start", "fg-muted"))
    c.add(text(40, Y2 + 30, "to wind 090° true at 8 kt and CAVOK: visibility 10 km or more, no cloud below 5,000 ft or the", 12, "start", "fg"))
    c.add(text(40, Y2 + 46, "highest minimum sector altitude, no cumulonimbus, no significant weather", 12, "start", "fg"))
    # TEMPO line
    Y3 = 388
    row, sp = code_row(40, Y3, ["TEMPO", "0306/0309", "4000", "SHRA", "BKN020"], {0})
    c.add(row)
    c.add(text(sp[-1][1] + 14, Y3 + 4, "spells of 30 to 60 minutes", 12, "start", "fg-muted"))
    c.add(text(40, Y3 + 30, "between 0600 and 0900 UTC: visibility 4,000 m in showers of rain, broken cloud (5 to 7 oktas)", 12, "start", "fg"))
    c.add(text(40, Y3 + 46, "at 2,000 ft above the aerodrome: BKN is a ceiling", 12, "start", "fg"))
    # T and Q line
    Y4 = 476
    row, sp = code_row(40, Y4, ["T", "24 22 19 17", "Q", "1016 1015 1013 1012"])
    c.add(row)
    c.add(text(40, Y4 + 32, "forecast temperatures, then forecast QNH, at 3-hourly intervals through the period", 12, "start", "fg"))
    return c


@chart
def taf_change_groups() -> Canvas:
    c = canvas("TAF change groups on a timeline",
               "Timeline of the example TAF from 0600 to 1800 UTC. The main conditions apply from 0600; FM031000 replaces them permanently from "
               "1000 UTC with wind 090 at 8 knots and CAVOK. TEMPO 0306/0309 adds spells of 4,000 m in showers with broken cloud at 2,000 ft, each "
               "lasting 30 to 60 minutes, between 0600 and 0900. Below, the other groups: BECMG is a gradual change over the period given, INTER "
               "means fluctuations of less than 30 minutes, PROB30 or PROB40 gives the probability of the condition.", height=448, prefix="tcg")
    c.add(text(320, 28, "When does each part of the TAF apply?", 16, "middle", "fg", weight=700))
    c.add(text(320, 46, "TAF YPJT 030400Z 0306/0318, times UTC on the 3rd", 12, "middle", "fg-muted"))
    L, R = 120, 610

    def X(h: float) -> float:
        return L + (h - 6) / 12 * (R - L)
    # axis
    AY = 214
    c.add(line(L, AY, R, AY, "fg-muted", SECOND, cap="butt"))
    for h in range(6, 19, 2):
        c.add(line(X(h), AY, X(h), AY + 5, "fg-muted", THIN))
        c.add(num(X(h), AY + 20, f"{h:02d}00", 12, "middle", "fg-muted"))
    for h in range(7, 18, 2):
        c.add(line(X(h), AY, X(h), AY + 3, "fg-faint", THIN))
    # main forecast row
    Y = 82
    c.add(text(L - 10, Y + 20, "main", 13, "end", "fg", weight=600))
    c.add(rect(X(6), Y, X(10) - X(6), 30, "surface-2", "line-strong", THIN, rx=4))
    c.add(num((X(6) + X(10)) / 2, Y + 20, "12012KT 9999", 12, "middle", "fg"))
    c.add(rect(X(10), Y, X(18) - X(10), 30, "brand-soft", "brand", SECOND, rx=4))
    c.add(num((X(10) + X(18)) / 2, Y + 20, "09008KT CAVOK", 13, "middle", "brand-fg", weight=700))
    c.add(line(X(10), Y - 14, X(10), Y + 30, "brand", SECOND, dash=DASH), line(X(10), AY - 8, X(10), AY + 5, "brand", MAIN))
    c.add(text(X(10) + 6, Y - 6, "FM031000: a permanent change from 1000", 12, "start", "brand-fg", weight=600))
    c.add(num((X(6) + X(10)) / 2, Y + 46, "FEW030 SCT045", 12, "middle", "fg-muted"))
    # TEMPO row
    Y = 150
    c.add(text(L - 10, Y + 20, "TEMPO", 13, "end", "warn-fg", weight=700))
    c.add(rect(X(6), Y, X(9) - X(6), 30, "warn-soft", "warn", THIN, rx=4, dash=DASH, fill_opacity=0.35))
    for h0 in (6.3, 7.4, 8.2):
        c.add(rect(X(h0), Y + 4, X(h0 + 0.7) - X(h0), 22, "warn-soft", "warn", SECOND, rx=3))
    c.add(text(X(9) + 10, Y + 12, "0306/0309: spells of 4000 SHRA BKN020,", 12, "start", "warn-fg"))
    c.add(text(X(9) + 10, Y + 28, "each lasting 30 to 60 minutes", 12, "start", "warn-fg", weight=600))
    # the other groups, not in this TAF
    c.add(line(30, 254, 610, 254, "line", THIN))
    c.add(text(30, 278, "Other groups you will meet (not in this TAF)", 13, "start", "fg", weight=700))
    cols = [(30, "BECMG", "a gradual change", "over the period given"),
            (230, "INTER", "fluctuations lasting", "less than 30 minutes"),
            (430, "PROB30 / PROB40", "the probability of the", "condition (30 or 40%)")]
    for x, head, l1, l2 in cols:
        c.add(rect(x, 292, 180, 82, "surface", "line", THIN, rx=6))
        c.add(text(x + 90, 312, head, 13, "middle", "fg", weight=700, cls="num"))
        bx, by = x + 20, 352
        if head == "BECMG":
            c.add(polyline([(bx, by), (bx + 40, by), (bx + 100, by - 22), (bx + 140, by - 22)], "info", MAIN))
            c.add(path(f"M{bx + 40} {by + 8} L{bx + 40} {by + 12} L{bx + 100} {by + 12} L{bx + 100} {by + 8}", "fg-faint", None, THIN))
        elif head == "INTER":
            pts = [(bx, by)]
            for k in range(4):
                s0 = bx + 12 + k * 34
                pts += [(s0, by), (s0, by - 22), (s0 + 10, by - 22), (s0 + 10, by)]
            pts.append((bx + 140, by))
            c.add(polyline(pts, "info", MAIN))
        else:
            c.add(rect(bx, by - 18, 140, 16, "surface-2", "line-strong", THIN, rx=3))
            c.add(rect(bx, by - 18, 140 * 0.3, 16, "info-soft", "info", SECOND, rx=3))
            c.add(num(bx + 50, by - 6, "30%", 11, "start", "info"))
        c.add(text(x + 90, 392, l1, 12, "middle", "fg-muted"))
        c.add(text(x + 90, 408, l2, 12, "middle", "fg-muted"))
    c.add(text(320, 436, "Check the main conditions and every change group against the VMC minima for the time of your flight.", 12, "middle", "fg-faint"))
    return c


@chart
def metar_anatomy() -> Canvas:
    c = canvas("Anatomy of a METAR",
               "A made-up METAR for Jandakot, group by group: METAR, a routine observation; YPJT, the aerodrome; 030430Z, observed on the 3rd at "
               "0430 UTC; 12012KT, wind 120 degrees true at 12 knots; 9999, visibility 10 km or more; FEW030, few cloud at 3,000 ft above the "
               "aerodrome; 24/18, temperature 24 and dew point 18; Q1016, QNH 1016. SPECI in place of METAR means a special observation triggered "
               "by a significant change; AUTO means an automatic station whose cloud and weather may be incomplete.", height=360, prefix="mta")
    c.add(text(320, 28, "Reading a METAR: what is actually happening", 16, "middle", "fg", weight=700))
    c.add(text(320, 46, "a made-up example in the format the note describes", 12, "middle", "fg-muted"))
    Y = 150
    row, sp = code_row(28, Y, ["METAR", "YPJT", "030430Z", "12012KT", "9999", "FEW030", "24/18", "Q1016"], {6, 7})
    c.add(row)
    c.add(tag(sp, 1, 1, Y, ["aerodrome", "(Jandakot)"], True))
    c.add(tag(sp, 3, 3, Y, ["wind 120° true", "at 12 kt"], True))
    c.add(tag(sp, 5, 5, Y, ["FEW at 3,000 ft", "above the aerodrome"], True))
    c.add(tag(sp, 7, 7, Y, ["QNH", "1016 hPa"], True, "brand-fg"))
    c.add(tag(sp, 0, 0, Y, ["routine", "observation"], False))
    c.add(tag(sp, 2, 2, Y, ["observed on the", "3rd at 0430 UTC"], False))
    c.add(tag(sp, 4, 4, Y, ["visibility", "10 km or more"], False))
    c.add(tag(sp, 6, 6, Y, ["temperature 24,", "dew point 18"], False, "brand-fg"))
    c.add(text(320, 246, "Same groups as a TAF, but observed values, plus temperature/dew point and QNH.", 12, "middle", "fg-muted"))
    cards = [("SPECI", ["in place of METAR:", "a special report after", "a significant change"]),
             ("AUTO", ["automatic station,", "no observer: cloud and", "weather may be incomplete"]),
             ("observed", ["not a forecast: use it", "to check the TAF is", "actually happening"])]
    for i, (head, lines) in enumerate(cards):
        x = 30 + i * 200
        c.add(rect(x, 262, 180, 86, "surface", "line", THIN, rx=6))
        c.add(text(x + 90, 282, head, 13, "middle", "fg", weight=700, cls="num" if head != "observed" else None))
        c.add(multiline(x + 90, 302, lines, 12, "middle", "fg-muted"))
    return c


@chart
def cloud_amounts_in_oktas() -> Canvas:
    c = canvas("Cloud amounts in oktas",
               "Cloud amount is measured in oktas, eighths of the sky. FEW is 1 to 2 oktas, SCT (scattered) 3 to 4, BKN (broken) 5 to 7 and OVC "
               "(overcast) 8. A BKN or OVC layer forms a ceiling.", height=250, prefix="okt")
    c.add(text(320, 28, "How much of the sky is covered? (eighths, or oktas)", 16, "middle", "fg", weight=700))
    groups = [("FEW", "few", 1, 2), ("SCT", "scattered", 3, 4), ("BKN", "broken", 5, 7), ("OVC", "overcast", 8, 8)]
    CY, R = 116, 38
    for i, (code, word, lo, hi) in enumerate(groups):
        cx = 92 + i * 152
        ceiling = code in ("BKN", "OVC")
        colr = "brand" if ceiling else "sky-fg"
        soft = "brand-soft" if ceiling else "sky-soft"
        c.add(circle(cx, CY, R, "surface", "line-strong", SECOND))
        for k in range(hi):
            a0, a1 = math.radians(-90 + 45 * k), math.radians(-90 + 45 * (k + 1))
            d = f"M{cx} {CY} L{fmt(cx + R * math.cos(a0))} {fmt(CY + R * math.sin(a0))} A{R} {R} 0 0 1 {fmt(cx + R * math.cos(a1))} {fmt(CY + R * math.sin(a1))} Z"
            c.add(path(d, colr, colr, THIN, fill_opacity=0.45) if k < lo else path(d, None, soft, 0))
        c.add(circle(cx, CY, R, "none", colr, MAIN))
        c.add(num(cx, CY + R + 26, code, 15, "middle", colr if ceiling else "fg", weight=700))
        c.add(text(cx, CY + R + 44, word, 12, "middle", "fg-muted"))
        c.add(num(cx, CY + R + 62, f"{lo} to {hi} oktas" if lo != hi else f"{hi} oktas", 12, "middle", "fg", weight=600))
    # ceiling bracket over BKN and OVC
    x0, x1 = 92 + 2 * 152 - 50, 92 + 3 * 152 + 50
    c.add(path(f"M{x0} 66 L{x0} 58 L{x1} 58 L{x1} 66", "brand", None, SECOND))
    c.add(text((x0 + x1) / 2, 50, "a ceiling", 13, "middle", "brand-fg", weight=700))
    c.add(text(320, 240, "Strong slices: the least cover for each code; faint slices: the rest of its range.", 11, "middle", "fg-faint"))
    return c


@chart
def cloud_height_datum() -> Canvas:
    c = canvas("Cloud heights: above sea level or above the aerodrome?",
               "The same cloud base measured two ways. In the GAF, cloud heights are above mean sea level (AMSL). In a TAF and a METAR, cloud "
               "heights are above the aerodrome. At an aerodrome above sea level the TAF figure is smaller than the GAF figure for the same base, "
               "by the aerodrome elevation.", height=392, prefix="chd")
    c.add(text(320, 28, "One cloud base, two reference levels", 16, "middle", "fg", weight=700))
    BASE, AD, MSL = 112, 250, 326
    for x0, x1, tops in ((40, 190, [22, 34, 26]), (250, 440, [26, 40, 30, 24]), (492, 612, [26, 20, 30])):
        c.add(cumulus(x0, BASE, x1, tops, "fg-muted", "surface-2"))
    c.add(line(30, BASE, 610, BASE, "fg-faint", THIN, dash=DASH))
    c.add(text(26, BASE + 18, "cloud base", 12, "start", "fg-muted"))
    # sea on the left, land rising to an aerodrome on high ground
    c.add(rect(20, MSL, 160, 30, "sky-soft", None))
    c.add(line(20, MSL, 620, MSL, "fg-faint", THIN, dash=DASH))
    c.add(text(26, MSL + 20, "mean sea level", 12, "start", "sky-fg", weight=600))
    land = [(180, MSL), (240, MSL - 10), (300, MSL - 40), (340, AD + 4), (380, AD), (560, AD), (620, AD + 4)]
    c.add(path(smooth_path(land) + f" L620 {MSL + 30} L180 {MSL + 30} Z", "fg-muted", "surface-2", SECOND))
    c.add(rect(400, AD - 4, 140, 6, "fg-muted", None, rx=1))
    c.add(text(470, AD + 22, "aerodrome", 12, "middle", "fg-muted", weight=600))
    # GAF: AMSL (info)
    GX = 130
    c.add(arrow(GX, MSL, GX, BASE + 2, "info", MAIN), arrow(GX, BASE, GX, MSL - 2, "info", MAIN))
    c.add(multiline(GX - 12, 190, ["GAF:", "above mean", "sea level"], 13, "end", "info", weight=600))
    # TAF, METAR: above aerodrome (brand)
    TX = 470
    c.add(arrow(TX, AD - 4, TX, BASE + 2, "brand", MAIN), arrow(TX, BASE, TX, AD - 6, "brand", MAIN))
    c.add(multiline(TX + 12, 168, ["TAF and METAR:", "above the", "aerodrome"], 13, "start", "brand", weight=600))
    c.add(num(TX - 12, 186, "FEW030", 13, "end", "brand-fg", weight=700))
    c.add(text(TX - 12, 202, "= 3,000 ft above", 12, "end", "brand-fg"))
    # elevation
    EX = 588
    c.add(arrow(EX, MSL, EX, AD + 6, "fg-muted", SECOND), arrow(EX, AD + 4, EX, MSL - 2, "fg-muted", SECOND))
    c.add(multiline(EX - 10, 286, ["aerodrome", "elevation"], 12, "end", "fg-muted"))
    c.add(text(320, 382, "GAF height of the base = TAF height + aerodrome elevation", 13, "middle", "fg", weight=600))
    return c


# ================================================================ RMTC 2.3 significance of observations
@chart
def visible_signs_of_thermals() -> Canvas:
    c = canvas("Signs of thermals you can see",
               "A hot afternoon over bare ground. Bubbles of warm air rise as thermals and build cumulus clouds with flat bases and growing tops; "
               "between the thermals the air sinks. A dust devil over the bare ground is a visible thermal, a narrow strong updraught with sharp "
               "wind changes around it. Smoke rising steadily then breaking up and birds soaring in circles also mark thermals.", height=400, prefix="vst")
    c.style(""".vst-rise{animation:vst-rise 4s ease-in infinite}
@keyframes vst-rise{0%{transform:translateY(0);opacity:0}20%{opacity:1}80%{opacity:1}100%{transform:translateY(-70px);opacity:0}}""")
    c.add(text(320, 28, "Reading thermals from the cockpit", 16, "middle", "fg", weight=700))
    G = 330
    BASE = 140
    c.add(sun(596, 52, 13, "warn"))
    # cumulus over the two thermals
    c.add(cumulus(70, BASE, 230, [30, 52, 40]))
    c.add(cumulus(350, BASE, 490, [34, 46, 28]))
    c.add(text(66, BASE + 18, "flat base", 12, "start", "fg-muted"))
    c.add(multiline(246, 74, ["cumulus: flat bases,", "growing tops"], 12, "start", "fg", weight=600))
    # thermals (brand): rising columns and bubbles (the bubbles move)
    for cx in (150, 420):
        c.add(path(f"M{cx - 34} {G - 4} C{cx - 24} {G - 90} {cx - 14} {BASE + 70} {cx - 30} {BASE + 10}", "brand", None, THIN, dash=DASH))
        c.add(path(f"M{cx + 34} {G - 4} C{cx + 24} {G - 90} {cx + 14} {BASE + 70} {cx + 30} {BASE + 10}", "brand", None, THIN, dash=DASH))
        c.add(arrow(cx, G - 40, cx, BASE + 30, "brand", MAIN))
    bubbles = "".join(circle(x, y, r, "brand-soft", "brand", SECOND) for x, y, r in ((136, 270, 8), (164, 236, 6), (410, 262, 7), (432, 220, 6), (150, 196, 5)))
    c.add(group(bubbles, cls="vst-rise"))
    c.add(text(150, G - 12, "thermal", 13, "middle", "brand", weight=700))
    c.add(text(420, G - 12, "thermal", 13, "middle", "brand", weight=700))
    # sink between
    for x in (266, 306):
        c.add(arrow(x, 150, x, 196, "info", SECOND))
    c.add(text(286, 216, "sink", 13, "middle", "info", weight=600))
    # birds circling over the left thermal
    for a in range(0, 360, 120):
        bx, by = 150 + 26 * math.cos(math.radians(a)), 60 + 9 * math.sin(math.radians(a))
        c.add(path(f"M{fmt(bx - 6)} {fmt(by - 3)} q3 3 6 0 q3 3 6 0", "fg", None, SECOND))
    c.add(path("M118 60 A32 11 0 1 0 182 60", "fg-faint", None, THIN, dash=DASH))
    c.add(text(110, 58, "soaring birds", 12, "end", "fg-muted"))
    # smoke rising then breaking up (right)
    c.add(rect(536, G - 16, 16, 16, "surface", "fg-muted", SECOND))
    c.add(path(f"M544 {G - 18} C541 {G - 50} 547 {G - 80} 544 {G - 120}", "fg-muted", None, MAIN))
    for d in (f"M538 {G - 134} q6 -8 14 -4", f"M548 {G - 152} q8 -2 10 -10", f"M530 {G - 160} q-4 -10 4 -16", f"M552 {G - 180} q6 -6 2 -14"):
        c.add(path(d, "fg-muted", None, SECOND))
    c.add(multiline(590, G - 110, ["smoke rises", "steadily, then", "breaks up"], 12, "middle", "fg-muted"))
    # ground: bare and hot on the left half
    c.add(rect(20, G, 600, 30, "surface-2", None))
    c.add(rect(20, G, 470, 8, "warn-soft", None))
    c.add(line(20, G, 620, G, "fg-muted", SECOND))
    c.add(text(250, G + 24, "hot, bare ground on a summer afternoon", 12, "middle", "warn-fg", weight=600))
    # dust devil
    DX = 286
    c.add(path(f"M{DX - 4} {G} C{DX - 8} {G - 20} {DX - 14} {G - 40} {DX - 20} {G - 56} L{DX + 20} {G - 56} C{DX + 14} {G - 40} {DX + 8} {G - 20} {DX + 4} {G} Z",
               "warn", "warn-soft", SECOND))
    for k in range(3):
        y = G - 14 - k * 16
        w = 8 + k * 5
        c.add(path(f"M{DX - w} {y} q{w} 5 {2 * w} 0", "warn", None, THIN))
    c.add(multiline(DX, G - 84, ["dust devil:", "a visible thermal"], 12, "middle", "warn-fg", weight=600))
    c.add(text(320, 388, "Avoid dust devils on take-off and landing: the wind changes sharply around them.", 12, "middle", "fg-faint"))
    return c


@chart
def wind_gradient_on_approach() -> Canvas:
    c = canvas("Descending through a wind gradient",
               "Left: the wind gradient. Friction slows the wind close to the ground, so the headwind is strongest a few hundred feet up and weakest "
               "at the surface. Right: an aeroplane on final into a strong headwind. As it descends the headwind decreases, the airspeed decays, the "
               "rate of descent increases and the aeroplane sinks below the intended approach path and undershoots unless the pilot adds power.",
               height=400, prefix="wga")
    G = 330
    c.add(text(320, 28, "Final approach into a strong headwind", 16, "middle", "fg", weight=700))
    # wind profile (info): arrows point to the left, the way the wind blows
    c.add(arrow(36, G, 36, 80, "fg-muted", SECOND))
    c.add(text(26, 205, "height", 12, "middle", "fg-muted", rotate=-90))
    for y, L in ((100, 110), (150, 104), (200, 92), (250, 72), (290, 46), (316, 22)):
        c.add(arrow(46 + L, y, 46, y, "info", MAIN))
    c.add(multiline(52, 354, ["headwind weakens", "near the ground"], 12, "start", "info", weight=600))
    # ground and runway
    c.add(line(20, G, 620, G, "fg-muted", SECOND))
    c.add(rect(520, G - 3, 100, 6, "fg-muted", None, rx=1))
    c.add(text(570, G + 20, "runway", 12, "middle", "fg-muted"))
    # intended path and the sagging path
    start = (196, 96)
    c.add(line(start[0], start[1], 530, G - 2, "ok", SECOND, dash="6 5"))
    c.add(text(512, 286, "intended path", 12, "start", "ok-fg", weight=600))
    sag = [start, (300, 170), (380, 236), (430, 284), (456, 312), (468, G - 2)]
    c.add(path(smooth_path(sag), "bad", None, MAIN))
    c.add(path("M466 320 L486 340 M486 320 L466 340", "bad", None, MAIN))
    c.add(text(460, 354, "undershoot", 12, "end", "bad", weight=600))
    # the cause-and-effect chain
    steps = ["headwind decreases as you descend", "airspeed decays", "rate of descent increases", "add power to hold the path"]
    for i, s in enumerate(steps):
        y = 70 + i * 24
        last = i == len(steps) - 1
        c.add(badge(356, y, str(i + 1), "brand" if last else "neutral", 12))
        c.add(text(372, y + 4, s, 13, "start", "brand" if last else "fg", weight=700 if last else 500))
    css, mv = mover("wga", sag, 6, 0.3, lambda a: plane_side(0, 0, 0.36, pitch=-3), rotate=False)
    c.style(css)
    c.add(mv)
    c.add(text(320, 390, "After take-off it works the other way: the headwind increases as you climb, giving a brief airspeed gain.", 11, "middle", "fg-faint"))
    return c


@chart
def microburst_encounter() -> Canvas:
    c = canvas("Flying through a microburst on approach",
               "Side view of a microburst beneath a thunderstorm: a strong downdraught hits the ground and spreads out in all directions. An aeroplane "
               "on approach first meets the outflow as a headwind (airspeed and lift up, it floats above the path), then the downdraught (it sinks), "
               "then the outflow as a tailwind (airspeed and lift down) with the ground close.", height=400, prefix="mbe")
    G = 340
    c.add(text(320, 28, "A microburst on final: headwind, downdraught, tailwind", 16, "middle", "fg", weight=700))
    # storm base
    c.add(path("M150 96 C160 70 200 62 230 70 C260 48 330 46 360 62 C400 46 470 56 490 84 C510 88 520 96 516 102 L150 102 Z", "fg-muted", "surface-2", SECOND))
    c.add(text(480, 64, "thunderstorm", 12, "start", "fg-muted"))
    # downdraught and outflow (info)
    MX = 330
    for dx in (-30, 0, 30):
        c.add(arrow(MX + dx, 110, MX + dx * 0.8, 240, "info", MAIN))
    c.add(path(f"M{MX - 20} 262 C{MX - 40} {G - 10} {MX - 80} {G - 12} {MX - 200} {G - 12}", "info", None, MAIN, arrow_end=True))
    c.add(path(f"M{MX + 20} 262 C{MX + 40} {G - 10} {MX + 80} {G - 12} {MX + 200} {G - 12}", "info", None, MAIN, arrow_end=True))
    c.add(line(20, G, 620, G, "fg-muted", SECOND))
    c.add(rect(540, G - 3, 80, 6, "fg-muted", None, rx=1))
    # glidepath and the flown path
    c.add(line(40, 150, 548, G - 4, "ok", SECOND, dash="6 5"))
    flown = [(40, 150), (120, 172), (190, 180), (250, 214), (330, 262), (400, 300), (450, 322), (480, G - 4)]
    c.add(path(smooth_path(flown), "bad", None, MAIN))
    # stages
    stages = [(150, 150, "1", ["headwind:", "airspeed and lift up,", "aeroplane floats high"]),
              (384, 150, "2", ["downdraught:", "it sinks"]),
              (440, 250, "3", ["tailwind: airspeed", "and lift down,", "ground close"])]
    for x, y, n, lines in stages:
        c.add(badge(x, y, n, "bad" if n == "3" else "neutral", 13))
    c.add(multiline(162, 132, stages[0][3], 12, "start", "fg"))
    c.add(multiline(398, 146, stages[1][3], 12, "start", "fg"))
    c.add(multiline(456, 246, stages[2][3], 12, "start", "bad", weight=600))
    c.add(path("M470 322 L490 342 M490 322 L470 342", "bad", None, MAIN))
    css, mv = mover("mbe", flown, 7, 0.15, lambda a: plane_side(0, 0, 0.34, pitch=-2), rotate=False)
    c.style(css)
    c.add(mv)
    c.add(text(320, 372, "The most dangerous shear of all: never take off or land through a thunderstorm gust front.", 12, "middle", "fg", weight=600))
    c.add(text(320, 390, "Dashed: the intended approach path.", 11, "middle", "fg-faint"))
    return c


@chart
def sea_breeze_front() -> Canvas:
    c = canvas("The sea breeze and its front",
               "Cross-section of the west coast on a warm afternoon, sea on the left. The land heats, warm air rises over it, and cool, moist sea air "
               "flows onshore underneath as the sea breeze, returning seaward aloft and sinking over the sea. Where the cool sea air meets the warm "
               "inland air it pushes in as a shallow wedge, the sea breeze front, marked by cumulus and wind shear. Moist sea air moving inland can also "
               "bring low cloud.", height=380, prefix="sbf")
    c.style(""".sbf-flow{stroke-dasharray:10 8;animation:sbf-flow 1.6s linear infinite}
@keyframes sbf-flow{to{stroke-dashoffset:-36}}""")
    G = 312
    c.add(text(320, 28, "Afternoon: the sea breeze pushes inland", 16, "middle", "fg", weight=700))
    c.add(sun(590, 60, 13, "warn"))
    # sea and land
    c.add(rect(20, G, 190, 40, "sky-soft", None))
    c.add(text(40, G + 26, "sea (cooler)", 12, "start", "sky-fg", weight=600))
    c.add(rect(210, G, 410, 40, "surface-2", None))
    c.add(rect(210, G, 410, 6, "warn-soft", None))
    c.add(line(20, G, 620, G, "fg-muted", SECOND))
    c.add(text(520, G + 26, "land (heated)", 12, "middle", "warn-fg", weight=600))
    c.add(text(28, 100, "W", 13, "start", "fg-faint", weight=700), text(612, 100, "E", 13, "end", "fg-faint", weight=700))
    # the cool sea air wedge, its nose is the front
    FX = 440
    c.add(path(f"M20 {G} L20 {G - 92} C200 {G - 96} 340 {G - 92} {FX - 30} {G - 72} C{FX} {G - 60} {FX + 10} {G - 30} {FX + 16} {G} Z", "sky-fg", "sky-soft", THIN,
               fill_opacity=0.6))
    c.add(text(140, G - 70, "cool, moist sea air", 13, "middle", "sky-fg", weight=600))
    # circulation cell (brand, the moving flow)
    cell = f"M60 {G - 26} L{FX - 30} {G - 26} C{FX + 30} {G - 30} {FX + 30} {G - 160} {FX - 20} {G - 186} L120 {G - 186} C50 {G - 180} 40 {G - 60} 60 {G - 26}"
    c.add(path(cell, "brand", None, MAIN, cls="sbf-flow"))
    c.add(arrow(250, G - 26, 290, G - 26, "brand", MAIN))
    c.add(arrow(260, G - 186, 220, G - 186, "brand", MAIN))
    c.add(arrow(FX + 15, G - 110, FX + 13, G - 130, "brand", MAIN))
    c.add(arrow(51, G - 124, 50, G - 100, "brand", MAIN))
    c.add(text(250, G - 8, "sea breeze: onshore at the surface", 13, "middle", "brand", weight=700))
    c.add(text(250, G - 196, "return flow aloft", 12, "middle", "brand-fg"))
    c.add(multiline(FX + 30, G - 150, ["warm air", "rises"], 12, "start", "brand-fg"))
    c.add(multiline(74, G - 150, ["sinks over", "the sea"], 12, "start", "brand-fg"))
    # cumulus over the front
    c.add(cumulus(FX - 50, 112, FX + 70, [22, 34, 26]))
    # the front and its shear
    c.add(path(f"M{FX + 16} {G} L{FX + 16} {G + 4}", "bad", None, MAIN))
    c.add(line(FX + 18, G - 40, FX + 70, G - 64, "fg-muted", THIN))
    c.add(multiline(FX + 76, G - 76, ["sea breeze front:", "wind shear and", "turbulence here"], 12, "start", "bad", weight=600))
    c.add(text(320, 372, "Converging sea breezes can trigger storms; the moist sea air can bring low cloud inland.", 12, "middle", "fg-faint"))
    return c
