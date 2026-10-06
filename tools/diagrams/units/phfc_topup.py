"""PHFC (human factors) top-up diagrams, second wave. One @chart function per diagram; the hyphenated name is the slug.
Numbers and medical statements come from content/notes/PHFC/; change the note first, then the diagram."""
from __future__ import annotations

import math
import random

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, arc_path, arrow, callout, circle, ellipse, fmt, group, line, multiline,
                                num, path, plane_rear, plane_side, plane_top, polygon, rect, sample, smooth_path, text)
from tools.diagrams.units.phfc import FG, SOFT, card


def hhmm(v: float) -> str:
    return f"{int(round(v)) % 24:02d}00"


# ---------------------------------------------------------------- 2.2 health and fitness
@chart
def blood_alcohol_curve_and_hangover() -> Canvas:
    c = Canvas("Blood alcohol and the hangover after a heavy night",
               "The wedding example from the note: ten standard drinks, the last at midnight. Blood alcohol rises while drinking and for 30 to 90 "
               "minutes after the last drink, while the drinks are absorbed, then falls at a fixed rate of about one standard drink an hour, reaching "
               "about zero around 1000. The 8-hour rule expires at 0800 with alcohol still in the blood. The hangover starts as blood alcohol falls and "
               "continues after it reaches zero, for 24 hours or more after heavy drinking. The curve's height is illustrative.",
               height=420, prefix="bac")
    ch = Chart(c, (18, 40), (0, 10), box=(56, 74, 612, 330), xlabel="Time of day (wedding night and next morning)",
               ylabel="Blood alcohol (shape only)", xticks=[18, 22, 26, 30, 34, 38], yticks=[], xfmt=hhmm)
    c.add(ch.band(19, 24, "warn", 0.14))
    c.add(ch.band(30, 40, "bad", 0.08))
    c.add(ch.axes())
    c.add(text(ch.px(21.5), ch.py(9.5), "drinking:", 12, "middle", "warn-fg", weight=600))
    c.add(text(ch.px(21.5), ch.py(9.5) + 15, "10 drinks", 12, "middle", "warn-fg"))

    # rise: absorption lags the drinking, peak about an hour after the last drink; then a straight fall to zero at 1000
    def rise(t: float) -> float:
        u = (t - 19) / 6
        return 8 * (1 - (1 - u) ** 2.2) if u < 1 else 8

    pts = sample(rise, 19, 25, 30) + [(34, 0)]
    c.add(ch.area(pts[:-1], "brand", 0.10))
    c.add(path(f"M{fmt(ch.px(25))} {fmt(ch.py(8))} L{fmt(ch.px(34))} {fmt(ch.py(0))} L{fmt(ch.px(25))} {fmt(ch.py(0))} Z", None, "brand", 0, fill_opacity=0.10))
    c.add(ch.curve(pts[:-1], "brand", MAIN))
    c.add(ch.curve([(25, 8), (34, 0)], "brand", MAIN, smooth=False))
    c.add(ch.curve([(34, 0), (40, 0)], "brand", SECOND, smooth=False, dash=DASH))
    # last drink and peak
    c.add(ch.vline(24, "warn", DASH, y_to=8.6))
    c.add(text(ch.px(24) - 7, ch.py(4.6), "last drink 0000", 12, "middle", "warn-fg", weight=600, rotate=-90))
    c.add(ch.point(25, 8, "brand", 5))
    c.add(text(ch.px(25) + 10, ch.py(8) - 10, "peak 30 to 90 min after", 12, "start", "brand", weight=600))
    c.add(text(ch.px(25) + 10, ch.py(8) + 6, "the last drink: still absorbing", 12, "start", "brand"))
    c.add(ch.callout(28.6, 4.8, 34, -10, ["falls at a fixed rate:", "about 1 standard drink an hour", "(nothing speeds it up)"], "fg", 12))
    # 0.02 line
    y02 = 0.7
    c.add(line(ch.left, ch.py(y02), ch.right, ch.py(y02), "warn", SECOND, dash=DASH))
    c.add(text(ch.left + 6, ch.py(y02) - 6, "0.02 g per 100 mL limit", 12, "start", "warn-fg", weight=600))
    # 8 hours
    c.add(ch.vline(32, "bad", None, y_to=6.2))
    c.add(text(ch.px(32), ch.py(6.2) - 22, "0800: 8 hours,", 12, "middle", "bad", weight=700))
    c.add(text(ch.px(32), ch.py(6.2) - 7, "alcohol still in the blood", 12, "middle", "bad"))
    c.add(ch.point(34, 0, "brand", 5))
    c.add(text(ch.px(34) + 8, ch.py(0) - 48, "about 1000:", 12, "start", "brand", weight=700))
    c.add(text(ch.px(34) + 8, ch.py(0) - 33, "near zero", 12, "start", "brand"))
    # hangover bar across the top of the hangover band
    yh = 52
    c.add(rect(ch.px(30), yh - 14, ch.right - ch.px(30) - 34, 26, "bad-soft", "bad", SECOND, rx=6))
    c.add(text(ch.px(30) + 10, yh + 4, "hangover: 24 h or more", 13, "start", "bad-fg", weight=700))
    c.add(arrow(ch.right - 28, yh - 1, ch.right, yh - 1, "bad", MAIN))
    c.add(text(ch.px(30) - 6, yh + 4, "starts as alcohol falls", 12, "end", "bad-fg"))
    c.add(text(320, 392, "Zero blood alcohol is not fitness: the hangover outlasts the alcohol.", 13, "middle", "fg", weight=600))
    c.add(text(320, 410, "Take the later of the 8-hour time and the liver time, then allow for the hangover.", 12, "middle", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.4 atmospheric pressure changes
@chart
def trapped_gas_body_map() -> Canvas:
    c = Canvas("Where trapped gas hurts, and when",
               "A head and torso with the four places gas is trapped. Ears (middle ear) and sinuses hurt on the descent: their air contracts and "
               "must get back in through a narrow passage that a cold or hay fever can block. Gut and teeth hurt on the climb: their gas expands "
               "inside a space it cannot leave quickly.", height=440, prefix="tgb")
    cx = 320
    # torso and head
    c.add(path(f"M{cx - 110} 440 C{cx - 110} 330 {cx - 100} 262 {cx - 46} 246 L{cx - 24} 226 L{cx + 24} 226 L{cx + 46} 246 "
               f"C{cx + 100} 262 {cx + 110} 330 {cx + 110} 440 Z", "fg", "surface-2", MAIN))
    c.add(ellipse(cx, 130, 62, 78, "surface", "fg", MAIN))
    # ears
    for s in (-1, 1):
        c.add(ellipse(cx + s * 64, 136, 12, 22, "surface", "fg", MAIN))
    # eyes, nose, mouth
    for s in (-1, 1):
        c.add(ellipse(cx + s * 24, 120, 9, 5, "surface", "fg", SECOND))
    c.add(path(f"M{cx} 124 L{cx - 7} 152 L{cx + 5} 154", "fg", None, SECOND))
    c.add(path(f"M{cx - 20} 176 Q{cx} 186 {cx + 20} 176", "fg", None, SECOND))
    # sinuses (frontal above the eyes, maxillary in the cheeks): descent colour
    c.add(ellipse(cx, 92, 22, 9, "bad-soft", "bad", SECOND))
    for s in (-1, 1):
        c.add(ellipse(cx + s * 30, 148, 12, 10, "bad-soft", "bad", SECOND))
    # middle ear spot
    c.add(circle(cx - 64, 136, 6, "bad-soft", "bad", SECOND))
    # tooth with a gas bubble: climb colour
    c.add(path(f"M{cx + 14} 170 l10 0 l-1 12 l-3 -4 l-3 4 Z", "warn", "warn-soft", SECOND))
    # gut
    gut = smooth_path([(cx - 50, 330), (cx + 40, 322), (cx + 50, 350), (cx - 40, 356), (cx - 50, 384), (cx + 46, 388), (cx + 40, 414), (cx - 30, 418)])
    c.add(path(gut, "warn", None, 9))
    c.add(path(gut, "warn-soft", None, 5))
    for bx, by in ((cx + 18, 326), (cx - 16, 357), (cx + 24, 389)):
        c.add(circle(bx, by, 4, "surface", "warn", THIN))

    # left: descent
    def tag(x: float, y: float, px: float, py: float, color: str, head: str, body: list[str], anchor: str) -> None:
        c.add(line(px, py, x + (-10 if anchor == "start" else 10), y - 4, "fg-muted", THIN))
        c.add(circle(px, py, 2.5, color, None))
        c.add(text(x, y, head, 14, anchor, FG[color], weight=700))
        c.add(multiline(x, y + 17, body, 12, anchor, "fg-muted", 1.3))

    c.add(rect(16, 14, 196, 58, "bad-soft", "bad", SECOND, rx=10))
    c.add(arrow(36, 26, 36, 60, "bad", MAIN))
    c.add(text(52, 38, "Hurt on the", 13, "start", "bad-fg"))
    c.add(text(52, 58, "DESCENT", 17, "start", "bad-fg", weight=800))
    tag(206, 116, cx - 22, 92, "bad", "Sinuses", ["air must get back in;", "a cold blocks the opening"], "end")
    tag(206, 186, cx - 70, 136, "bad", "Ears (middle ear)", ["air must climb back up", "the eustachian tube"], "end")
    c.add(rect(428, 14, 196, 58, "warn-soft", "warn", SECOND, rx=10))
    c.add(arrow(448, 60, 448, 26, "warn", MAIN))
    c.add(text(464, 38, "Hurt on the", 13, "start", "warn-fg"))
    c.add(text(464, 58, "CLIMB", 17, "start", "warn-fg", weight=800))
    tag(434, 186, cx + 22, 178, "warn", "Teeth", ["gas under a poor filling", "presses on the nerve"], "start")
    tag(462, 318, cx + 52, 350, "warn", "Gut", ["gas expands: bloating,", "cramps, can press on", "the diaphragm"], "start")
    # fixes
    c.add(multiline(16, 330, ["Fix: climb back, equalise", "(swallow, yawn, Valsalva),", "then descend more slowly"], 12, "start", "bad-fg", 1.35, weight=600))
    c.add(multiline(462, 400, ["Fix: stop climbing or", "descend, let the gas out"], 12, "start", "warn-fg", 1.35, weight=600))
    return c


@chart
def nitrogen_bubbles_after_diving() -> Canvas:
    c = Canvas("Why flying after diving causes the bends",
               "Three panels. At depth the diver breathes air at two, three or more times sea-level pressure and extra nitrogen dissolves in the blood "
               "and tissues. Back at the surface the extra nitrogen leaves slowly, over many hours. Flying soon after lowers the pressure again, like "
               "opening a soft-drink bottle a second time, and the nitrogen comes out as bubbles: decompression sickness, possible from about 5,000 "
               "to 8,000 ft cabin altitude. Wait at least 12 hours after a no-decompression dive and at least 24 hours after decompression stops or "
               "multiple dives.", height=420, prefix="nbd")
    c.style(".nbd-bub{animation:nbd-grow 3s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
            "@keyframes nbd-grow{0%,15%{transform:scale(.35)}60%,100%{transform:scale(1)}}")
    PW, PH = 196, 300
    heads = [("1  At depth", "air at 2, 3 or more × pressure"), ("2  Back on the surface", "extra leaves over many hours"),
             ("3  Flying soon after", "pressure falls again")]
    rnd = random.Random(7)
    for i, (h, sub) in enumerate(heads):
        x, y = 16 + i * (PW + 10), 14
        c.add(rect(x, y, PW, PH, "surface", "line-strong", SECOND, rx=10))
        c.add(text(x + 12, y + 22, h, 14, "start", "fg", weight=700))
        c.add(text(x + 12, y + 40, sub, 11, "start", "fg-muted"))
        # scene strip
        sy = y + 52
        if i == 0:
            c.add(rect(x + 8, sy, PW - 16, 74, "sky-soft", None, rx=6))
            c.add(line(x + 8, sy + 10, x + PW - 8, sy + 10, "sky-fg", SECOND))
            c.add(text(x + PW - 14, sy + 66, "every 10 m: +1 atmosphere", 11, "end", "sky-fg"))
            # diver: simple body with tank
            dx, dy = x + 60, sy + 40
            c.add(ellipse(dx, dy, 26, 7, "surface", "fg", SECOND))
            c.add(circle(dx + 32, dy - 2, 7, "surface", "fg", SECOND))
            c.add(rect(dx - 16, dy - 15, 26, 8, "fg-muted", None, rx=3))
            for k in range(3):
                c.add(circle(dx + 42 + k * 4, dy - 12 - k * 11, 2.5 + k, None, "sky-fg", THIN))
        elif i == 1:
            c.add(rect(x + 8, sy, PW - 16, 74, "surface-2", None, rx=6))
            c.add(rect(x + 8, sy + 52, PW - 16, 22, "sky-soft", None, rx=0))
            c.add(text(x + PW / 2, sy + 30, "sea-level pressure", 12, "middle", "fg-muted"))
            c.add(text(x + PW / 2, sy + 68, "boat ride home, a rest", 11, "middle", "sky-fg"))
        else:
            c.add(rect(x + 8, sy, PW - 16, 74, "sky-soft", None, rx=6))
            c.add(plane_side(x + 120, sy + 32, 1.1, pitch=6, gear=False))     # CG 21 units ahead of mid-length
            c.add(text(x + PW / 2, sy + 68, "from about 5,000 to 8,000 ft", 11, "middle", "sky-fg"))
        # magnified tissue
        tx, ty, r = x + PW / 2, y + 200, 50
        c.add(circle(tx, ty, r, "info-soft", "info", SECOND))
        c.add(text(tx, ty - r - 7, "blood and tissues", 11, "middle", "fg-muted"))
        n = [30, 22, 10][i]
        for _ in range(n):
            a, rr = rnd.uniform(0, 2 * math.pi), r * math.sqrt(rnd.uniform(0, 0.8))
            c.add(circle(tx + rr * math.cos(a), ty + rr * math.sin(a), 2.6, "brand", None))
        if i == 1:
            for a in (-40, 30, 150, 210):
                ax, ay = tx + (r - 4) * math.cos(math.radians(a)), ty + (r - 4) * math.sin(math.radians(a))
                bx, by = tx + (r + 14) * math.cos(math.radians(a)), ty + (r + 14) * math.sin(math.radians(a))
                c.add(arrow(ax, ay, bx, by, "brand", SECOND))
        if i == 2:
            for bx, by, br in ((tx - 18, ty - 10, 12), (tx + 20, ty + 8, 9), (tx - 4, ty + 26, 7), (tx + 16, ty - 26, 6)):
                c.add(circle(bx, by, br, "surface", "bad", MAIN, cls="nbd-bub"))
        foot = [["extra nitrogen", "dissolves, no bubbles"], ["still more than normal:", "it leaves slowly"],
                ["nitrogen comes out", "as bubbles: the bends"]][i]
        c.add(multiline(x + PW / 2, y + 268, foot, 12, "middle", "bad" if i == 2 else "brand", 1.3, weight=600))
    c.add(circle(30, 336, 4, "brand", None))
    c.add(text(40, 340, "dissolved nitrogen", 12, "start", "fg-muted"))
    c.add(circle(178, 336, 7, "surface", "bad", MAIN))
    c.add(text(192, 340, "bubble: joint pain, itching, chokes, tingling, collapse", 12, "start", "fg-muted"))
    c.add(rect(16, 356, 608, 52, "ok-soft", "ok", SECOND, rx=10))
    c.add(text(320, 377, "Wait at least 12 h after a dive with no decompression stops;", 13, "middle", "ok-fg", weight=700))
    c.add(text(320, 396, "at least 24 h after decompression stops or several days of dives. Snorkelling: no wait.", 12, "middle", "ok-fg"))
    return c


# ---------------------------------------------------------------- 2.7 vision, disorientation, illusions
def canal(cx: float, cy: float, bend: float, canal_turn: str | None, fluid: str | None) -> str:
    """Horizontal semicircular canal seen from above: a fluid ring with the ampulla and cupula at the top.
    bend: cupula deflection in px (negative = to the left). canal_turn / fluid: 'cw', 'ccw' or None for the arc arrows."""
    R0, R1 = 44, 62
    out = [circle(cx, cy, (R0 + R1) / 2, None, "sky-soft", R1 - R0)]
    out.append(circle(cx, cy, R1, None, "fg", SECOND))
    out.append(circle(cx, cy, R0, "surface", "fg", SECOND))
    # ampulla bulge at the top
    out.append(ellipse(cx, cy - (R0 + R1) / 2, 20, 15, "sky-soft", "fg", SECOND))
    out.append(rect(cx - 19, cy - (R0 + R1) / 2 - 7, 38, 14, "sky-soft", None))
    # cupula: a flap from the outer wall of the ampulla towards the inner wall
    top, bot = cy - (R0 + R1) / 2 - 15, cy - R0 + 1
    out.append(path(f"M{fmt(cx - 4)} {fmt(top)} Q{fmt(cx - 4 + bend * 0.2)} {fmt((top + bot) / 2)} {fmt(cx + bend)} {fmt(bot)} "
                    f"L{fmt(cx + 4 + bend)} {fmt(bot)} Q{fmt(cx + 4 + bend * 0.2)} {fmt((top + bot) / 2)} {fmt(cx + 4)} {fmt(top)} Z", "brand", "brand", SECOND))
    if canal_turn:
        a0, a1 = (200, 300) if canal_turn == "cw" else (300, 200)
        out.append(path(arc_path(cx, cy, R1 + 16, a0 - 140, a1 - 140), "fg-muted", None, MAIN, arrow_end=True))
    if fluid:
        a0, a1 = (60, 120) if fluid == "cw" else (120, 60)
        out.append(path(arc_path(cx, cy, (R0 + R1) / 2, a0, a1), "brand", None, MAIN, arrow_end=True))
    return "".join(out)


@chart
def semicircular_canal_fluid_lag() -> Canvas:
    c = Canvas("Why the canals miss a steady turn",
               "The horizontal semicircular canal seen from above, in three moments of a turn to the right. When rotation starts, the canal turns but "
               "the fluid lags and bends the cupula: you feel the turn. In a steady turn, after about 10 to 20 seconds, the fluid has caught up and the "
               "cupula is upright: the sensation has gone. When the rotation stops, the fluid runs on and bends the cupula the other way: you feel a "
               "turn in the opposite direction. A graph below compares the actual rate of turn with what is felt.", height=520, prefix="scf")
    PW, PH = 196, 286
    panels = [("1  Rotation starts", -12, "cw", "ccw", ["canal turns, fluid lags", "and bends the cupula"], "feels: turning right", "ok"),
              ("2  Steady turn", 0, "cw", None, ["after 10 to 20 s the fluid", "catches up: cupula upright"], "feels: no turn at all", "bad"),
              ("3  Rotation stops", 12, None, "cw", ["canal stops, fluid runs on,", "cupula bends the other way"], "feels: turning left", "bad")]
    for i, (h, bend, ct, fl, body, feel, fc) in enumerate(panels):
        x, y = 16 + i * (PW + 10), 14
        c.add(rect(x, y, PW, PH, "surface", "line-strong", SECOND, rx=10))
        c.add(text(x + 12, y + 22, h, 14, "start", "fg", weight=700))
        c.add(canal(x + PW / 2, y + 128, bend, ct, fl))
        if ct:
            c.add(text(x + PW - 10, y + 52, "head", 11, "end", "fg-muted"))
            c.add(text(x + PW - 10, y + 66, "turning", 11, "end", "fg-muted"))
        else:
            c.add(text(x + PW - 10, y + 52, "head", 11, "end", "fg-muted"))
            c.add(text(x + PW - 10, y + 66, "stopped", 11, "end", "fg-muted"))
        c.add(multiline(x + PW / 2, y + 226, body, 12, "middle", "fg-muted", 1.3))
        c.add(text(x + PW / 2, y + 270, feel, 13, "middle", FG[fc], weight=700))
    c.add(text(30, 76, "cupula", 12, "start", "brand", weight=600))
    c.add(line(72, 78, 16 + PW / 2 - 8, 14 + 128 - 48, "fg-muted", THIN))
    # timeline: actual rate of turn vs felt
    ch = Chart(c, (0, 60), (-1.2, 1.4), box=(70, 330, 610, 470), xlabel="Time (seconds)", xticks=[0, 10, 20, 30, 40, 50], yticks=[0], grid=False)
    c.add(ch.axes())
    c.add(text(18, 400, "Rate of turn", 13, "middle", "fg-muted", weight=600, rotate=-90))
    c.add(ch.curve([(0, 0), (2, 0), (2, 1), (40, 1), (40, 0), (60, 0)], "fg-muted", MAIN, smooth=False))
    c.add(text(ch.px(30), ch.py(1) - 8, "actual turn", 12, "middle", "fg-muted", weight=600))
    felt = [(0, 0), (2, 0)] + [(t, math.exp(-(t - 2) / 6)) for t in [2 + k * 0.5 for k in range(77)]]
    felt += [(40, -math.exp(0)), ] + [(t, -math.exp(-(t - 40) / 6)) for t in [40 + k * 0.5 for k in range(1, 41)]]
    c.add(ch.curve(felt[:80], "brand", MAIN, smooth=False))
    c.add(ch.curve([(40, felt[79][1]), (40, -1)] + felt[80:], "brand", MAIN, smooth=False))
    c.add(text(ch.px(9), ch.py(0.65), "felt: fades in 10 to 20 s", 12, "start", "brand", weight=600))
    c.add(text(ch.px(43), ch.py(-1.05), "felt: a turn the other way", 12, "start", "brand", weight=600))
    return c


@chart
def somatogravic_resultant_vector() -> Canvas:
    c = Canvas("Somatogravic illusion: acceleration feels like pitch-up",
               "On a dark take-off the aeroplane accelerates forward. The otoliths feel gravity straight down plus the backward lag of the crystals "
               "from the forward acceleration, and report only their sum: a total force tilted backwards. With no horizon the brain takes that "
               "tilted force as 'down' and feels a nose-up pitch: tan theta = a / g, so a quarter of g feels like about 14 degrees nose-up. The "
               "pilot who pushes forward flies into the ground.", height=400, prefix="sgv")
    # left: vector diagram at the otoliths
    c.add(text(16, 28, "What the otoliths feel", 15, "start", "fg", weight=700))
    ox, oy, G = 200, 76, 220
    a = G / 4
    c.add(circle(ox, oy, 8, "surface", "fg", MAIN))
    c.add(arrow(ox, oy + 10, ox, oy + G, "fg", MAIN))
    c.add(text(ox + 10, oy + G * 0.55, "gravity, 1 g", 13, "start", "fg", weight=600))
    c.add(text(ox + 10, oy + G * 0.55 + 16, "straight down", 12, "start", "fg-muted"))
    c.add(arrow(ox - 10, oy, ox - a, oy, "info", MAIN))
    c.add(multiline(ox - a - 8, oy - 22, ["crystals lag back:", "acceleration ¼ g"], 12, "end", "info-fg", 1.3, weight=600))
    c.add(line(ox - a, oy, ox - a, oy + G, "line-strong", THIN, dash=DASH))
    c.add(line(ox, oy + G, ox - a, oy + G, "line-strong", THIN, dash=DASH))
    k = (G - 12) / math.hypot(a, G)
    c.add(arrow(ox - 6, oy + 8, ox - a * k, oy + G * k, "brand", 2.5))
    c.add(multiline(ox - a - 10, oy + G * 0.75, ["the sum: felt", "as \"down\""], 13, "end", "brand", 1.3, weight=700))
    th = math.degrees(math.atan(0.25))
    c.add(path(arc_path(ox, oy, 70, 90, 90 + th), "brand", None, SECOND))
    c.add(text(ox - 10, oy + 92, "θ", 14, "middle", "brand", weight=700))
    c.add(text(16, 360, "tan θ = a ÷ g = 0.25, so θ ≈ 14°", 14, "start", "fg", weight=700, cls="num"))
    c.add(text(16, 382, "Deceleration does the reverse: it feels nose-down.", 12, "start", "fg-muted"))
    # right: actual vs felt
    x0 = 330
    c.add(rect(x0, 40, 294, 140, "surface", "line-strong", SECOND, rx=10))
    c.add(text(x0 + 12, 62, "Actual: accelerating, shallow climb", 13, "start", "fg", weight=700))
    c.add(line(x0 + 12, 158, x0 + 282, 158, "fg-muted", SECOND))
    c.add(plane_side(x0 + 180, 124, 1.15, pitch=5, gear=False))
    c.add(arrow(x0 + 20, 92, x0 + 80, 92, "info", SECOND))
    c.add(text(x0 + 20, 110, "accelerating", 11, "start", "info-fg"))
    c.add(rect(x0, 196, 294, 140, "info-soft", "info", SECOND, rx=10))
    c.add(text(x0 + 12, 218, "Felt, with no horizon: steep nose-up", 13, "start", "info-fg", weight=700))
    c.add(plane_side(x0 + 180, 280, 1.15, pitch=5 + th, color="info", gear=False))
    c.add(line(x0 + 80, 280 + 100 * math.tan(math.radians(5)), x0 + 230, 280 - 50 * math.tan(math.radians(5)), "info", THIN, dash=DASH))
    c.add(text(x0 + 236, 286, "+14°", 13, "start", "info-fg", weight=700, cls="num"))
    c.add(rect(x0, 344, 294, 46, "bad-soft", "bad", SECOND, rx=10))
    c.add(text(x0 + 147, 364, "Pushing forward to \"fix\" it flies into", 13, "middle", "bad-fg", weight=700))
    c.add(text(x0 + 147, 381, "the ground. Believe the attitude indicator.", 12, "middle", "bad-fg"))
    return c


@chart
def black_hole_approach_profile() -> Canvas:
    c = Canvas("Black hole approach: the path that sags",
               "Side view of a night approach over dark country to a lit runway. The normal glidepath is a straight slope to the threshold. With only "
               "the runway lights to judge by, the pilot keeps the runway's shape in the windscreen the same, and the path that does that is a curve "
               "that sags below the glidepath, low and shallow, meeting the dark scrub short of the threshold. The pilot feels high all the way down. "
               "The fix is to fly the numbers: the PAPI, a planned height against distance profile and the altimeter.", height=380, prefix="bha")
    gy, tx, fx = 300, 470, 604
    sx, sy = 40, 140
    # night sky, dark ground and scrub
    c.add(rect(16, 14, 608, gy - 14, "surface-2", None, rx=10))
    c.add(rect(16, gy, 608, 30, "tarmac", None))
    scrub = [(330, gy), (342, gy - 10), (356, gy - 6), (372, gy - 14), (388, gy - 8), (404, gy - 15), (420, gy - 9), (436, gy - 13), (450, gy - 4), (458, gy)]
    c.add(polygon(scrub, "tarmac", None))
    c.add(text(24, gy + 20, "dark bush or water: no lights, no texture", 12, "start", "paint"))
    # runway and its lights
    c.add(line(tx, gy, fx, gy, "paint", 4, cap="butt"))
    for k in range(9):
        c.add(circle(tx + 4 + k * 16, gy - 4, 2.6, "warn", None))
    c.add(text((tx + fx) / 2, gy + 20, "lit runway", 12, "middle", "paint", weight=600))
    # normal glidepath
    c.add(line(sx, sy, tx, gy, "ok", MAIN, dash="7 5"))
    c.add(text(296, 196, "normal glidepath", 13, "start", "ok-fg", weight=700))
    c.add(text(296, 212, "(what the PAPI shows)", 12, "start", "ok-fg"))
    c.add(text(608, 36, "night", 13, "end", "fg-muted", weight=600))
    # constant-picture path: arc of the circle through the start, the threshold and the far end of the runway
    xc = (tx + fx) / 2
    yc = ((sx - xc) ** 2 + sy ** 2 - (tx - xc) ** 2 - gy ** 2) / (2 * (sy - gy))
    R = math.hypot(tx - xc, gy - yc)

    def arc_y(x: float) -> float:
        return yc + math.sqrt(R * R - (x - xc) ** 2)

    hit = next(x for x in range(380, 460) if arc_y(x) >= gy - 14 - (0 if x < 404 else 0))
    pts = [(x, arc_y(x)) for x in range(sx, hit + 1, 6)]
    c.add(path(smooth_path(pts), "bad", None, 2.5))
    c.add(circle(hit, arc_y(hit), 5, "bad", "surface", 1.5))
    c.add(text(hit, gy + 20, "lands short", 12, "middle", "paint", weight=700))
    c.add(text(56, 262, "black hole path:", 13, "start", "bad", weight=700))
    c.add(text(56, 278, "low and shallow", 13, "start", "bad", weight=700))
    # the same runway picture at three points
    for px in (100, 180, 260):
        py = arc_y(px)
        bx, by = px - 30, 30
        c.add(line(px, py - 6, px, by + 48, "fg-muted", THIN, dash=DASH))
        c.add(circle(px, py, 3.5, "bad", None))
        c.add(rect(bx, by, 60, 46, "tarmac", "line-strong", SECOND, rx=4))
        c.add(polygon([(bx + 20, by + 40), (bx + 40, by + 40), (bx + 34, by + 12), (bx + 26, by + 12)], None, "warn", SECOND))
    c.add(text(380, 46, "the same runway picture", 13, "start", "fg", weight=700))
    c.add(text(380, 62, "all the way down:", 13, "start", "fg", weight=700))
    c.add(text(380, 78, "you feel high, so you", 12, "start", "fg-muted"))
    c.add(text(380, 93, "never correct", 12, "start", "fg-muted"))
    c.add(rect(16, 338, 608, 34, "ok-soft", "ok", SECOND, rx=8))
    c.add(text(320, 360, "Fly the numbers, not the picture: PAPI, planned height v distance, altimeter.", 13, "middle", "ok-fg", weight=700))
    return c


@chart
def constant_bearing_collision() -> Canvas:
    c = Canvas("A collision course does not move on the windscreen",
               "Plan view of two aircraft on converging tracks, shown at equal time intervals. The line of sight between them stays parallel to "
               "itself: a constant relative bearing. From the cockpit the other aircraft stays fixed on the windscreen and only grows, slowly at "
               "first and then very fast, so peripheral vision, which hunts for movement, does not notice it.", height=400, prefix="cbc")
    c.add(rect(16, 14, 380, 372, "surface", "line-strong", SECOND, rx=10))
    c.add(text(28, 36, "From above: equal time steps", 14, "start", "fg", weight=700))
    P = (340, 330)
    you0, oth0 = (60, 330), (270, 70)
    n = 5

    def pos(p0: tuple[float, float], t: float) -> tuple[float, float]:
        return p0[0] + (P[0] - p0[0]) * t / n, p0[1] + (P[1] - p0[1]) * t / n

    c.add(line(*you0, *P, "line-strong", THIN, dash=DASH))
    c.add(line(*oth0, *P, "line-strong", THIN, dash=DASH))
    ux, uy = (P[0] - oth0[0]) / math.dist(oth0, P), (P[1] - oth0[1]) / math.dist(oth0, P)
    for t in range(0, 5):                       # sight lines nose to nose (plan-view spinner 21 units ahead of the CG)
        a, b = pos(you0, t), pos(oth0, t)
        c.add(line(a[0] + 7, a[1], b[0] + 7 * ux, b[1] + 7 * uy, "brand", SECOND, dash=None if t == 0 else DASH, opacity=1 - t * 0.12))
    for t in range(0, 5):
        a, b = pos(you0, t), pos(oth0, t)
        c.add(plane_top(*a, 0.32, heading=90))
        c.add(plane_top(*b, 0.32, heading=math.degrees(math.atan2(P[0] - oth0[0], -(P[1] - oth0[1]))), color="bad"))
        c.add(num(a[0], a[1] + 26, str(t + 1), 11, "middle", "fg-muted"))
        c.add(num(b[0] + 18, b[1] + 4, str(t + 1), 11, "start", "bad"))
    c.add(circle(*P, 7, "bad-soft", "bad", MAIN))
    c.add(text(P[0], P[1] + 28, "collision", 12, "middle", "bad", weight=700))
    c.add(text(60, 306, "you", 13, "middle", "fg", weight=700))
    c.add(text(oth0[0] - 22, oth0[1] + 4, "other", 13, "end", "bad", weight=700))
    c.add(multiline(160, 152, ["lines of sight stay", "parallel: a constant", "relative bearing"], 12, "end", "brand", 1.3, weight=600))
    # windscreen view
    x0 = 408
    c.add(text(x0, 36, "From your seat", 14, "start", "fg", weight=700))
    c.add(path(f"M{x0} 70 Q{x0 + 108} 52 {x0 + 216} 70 L{x0 + 210} 210 L{x0 + 6} 210 Z", "fg", "sky-soft", MAIN))
    c.add(line(x0 + 108, 61, x0 + 108, 210, "fg", 4))
    ox, oy = x0 + 56, 160
    c.add(line(x0 + 6, 160, ox - 40, 160, "fg-muted", THIN, dash=DASH))
    c.add(line(ox + 40, 160, x0 + 210, 160, "fg-muted", THIN, dash=DASH))
    c.add(text(x0 + 204, 176, "horizon", 11, "end", "fg-muted"))
    for k, sc in enumerate((0.7, 0.45, 0.25)):
        c.add(plane_rear(ox, oy, sc, color="bad", fill="bad-soft" if k == 0 else "surface"))
    c.add(text(x0 + 16, 192, "same spot,", 11, "start", "bad", weight=600))
    c.add(text(x0 + 16, 205, "just bigger", 11, "start", "bad", weight=600))
    c.add(multiline(x0, 236, ["It stays in the same spot", "and just grows, then", "\"blossoms\" in the last", "few seconds."], 13, "start", "fg", 1.35, weight=600))
    c.add(multiline(x0, 318, ["No movement means your", "peripheral vision ignores it.", "Traffic sliding across the", "screen will pass ahead or behind."], 12, "start", "fg-muted", 1.35))
    return c


# ---------------------------------------------------------------- 2.10 toxic hazards
def haemoglobin(cx: float, cy: float, sites: list[str]) -> str:
    """A haemoglobin molecule as a soft blob with four binding sites; each site 'O2', 'CO' or ''."""
    out = [path(smooth_path([(cx - 70, cy), (cx - 50, cy - 46), (cx, cy - 56), (cx + 52, cy - 44), (cx + 72, cy), (cx + 48, cy + 48),
                              (cx, cy + 56), (cx - 52, cy + 44)], closed=True), "fg", "surface-2", MAIN)]
    out.append(text(cx, cy + 5, "haemoglobin", 12, "middle", "fg-muted", weight=600))
    for (dx, dy), s in zip(((-44, -30), (44, -30), (-44, 30), (44, 30)), sites):
        x, y = cx + dx, cy + dy
        if s in ("O2", "CO"):
            colr = "ok" if s == "O2" else "bad"
            out += [rect(x - 17, y - 10, 34, 20, SOFT[colr], colr, SECOND, rx=10),
                    text(x, y + 4, "O₂" if s == "O2" else "CO", 12, "middle", FG[colr], weight=800)]
        else:
            out.append(circle(x, y, 7, "surface", "line-strong", SECOND, dash="3 2"))
    return "".join(out)


@chart
def carboxyhaemoglobin_binding() -> Canvas:
    c = Canvas("Carbon monoxide takes oxygen's seats",
               "Two panels. In clean air each haemoglobin molecule's oxygen sites carry oxygen. With a little carbon monoxide in the cabin air, CO "
               "binds to the same sites about 200 to 250 times more readily than oxygen, so a small amount of CO takes over a large share of the "
               "haemoglobin, forming carboxyhaemoglobin. The lungs have their full share of oxygen but the blood cannot carry it: anaemic hypoxia. "
               "CO lets go only slowly, over many hours.", height=404, prefix="cob")
    PW = 298
    for i, (head, sub, air, sites, foot, fc) in enumerate([
            ("Clean air", "every site carries oxygen", ["O2"] * 9, ["O2", "O2", "O2", "O2"], "blood fully loaded", "ok"),
            ("A little CO in the cabin", "the air still has its full share of oxygen", ["O2"] * 8 + ["CO"], ["CO", "O2", "CO", "CO"],
             "most seats taken by CO", "bad")]):
        x = 16 + i * (PW + 12)
        c.add(rect(x, 14, PW, 282, "surface", "line-strong" if i == 0 else "bad", SECOND, rx=10))
        c.add(text(x + 14, 38, head, 15, "start", "fg", weight=700))
        c.add(text(x + 14, 56, sub, 12, "start", "fg-muted"))
        # air: a strip of molecules
        c.add(rect(x + 12, 68, PW - 24, 50, "sky-soft", None, rx=8))
        c.add(text(x + 20, 84, "air in the lungs", 11, "start", "sky-fg"))
        for k, m in enumerate(air):
            mx, my = x + 34 + k * 28, 102
            colr = ("ok", "ok-soft") if m == "O2" else ("bad", "bad-soft")
            c.add(circle(mx - 4, my, 5, colr[1], colr[0], THIN))
            c.add(circle(mx + 4, my, 5, colr[1], colr[0], THIN))
        c.add(arrow(x + PW / 2, 124, x + PW / 2, 148, "fg-muted", SECOND))
        c.add(haemoglobin(x + PW / 2, 210, sites))
        c.add(text(x + PW / 2, 286, foot, 13, "middle", FG[fc], weight=700))
    # the grip comparison
    y = 318
    c.add(text(16, y, "How readily each one binds to haemoglobin (to scale)", 13, "start", "fg", weight=700))
    c.add(rect(100, y + 10, 2.1, 14, "ok", None))
    c.add(text(92, y + 22, "oxygen", 12, "end", "ok-fg", weight=600))
    c.add(text(110, y + 22, "× 1", 12, "start", "ok-fg", weight=600, cls="num"))
    c.add(rect(100, y + 32, 472, 14, "bad-soft", "bad", SECOND, rx=3))
    c.add(text(92, y + 44, "CO", 12, "end", "bad", weight=700))
    c.add(text(336, y + 44, "about × 200 to 250", 12, "middle", "bad-fg", weight=700, cls="num"))
    c.add(text(16, y + 72, "Every seat CO takes cannot carry oxygen, and CO lets go only over many hours: anaemic hypoxia.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.11 the atmosphere
@chart
def isa_temperature_profile() -> Canvas:
    c = Canvas("The ISA temperature profile",
               "International Standard Atmosphere temperature against altitude: +15 degrees at sea level, falling about 2 degrees per 1,000 ft to "
               "about -56.5 degrees at the tropopause, about 36,000 ft, then constant above it. Worked example: -1 degree at 8,000 ft.",
               height=400, prefix="isa")
    ch = Chart(c, (-70, 50), (0, 46000), box=(84, 24, 600, 340), xlabel="ISA temperature (°C)", ylabel="Altitude (ft)",
               xticks=[-60, -40, -20, 0, 20, 40], yticks=[0, 10000, 20000, 30000, 40000], yfmt=lambda v: f"{int(v):,}",
               xfmt=lambda v: (f"+{int(v)}" if v > 0 else f"−{-int(v)}") if v else "0")
    c.add(ch.axes())
    # stratosphere shading above the tropopause
    c.add(rect(ch.left, ch.top, ch.right - ch.left, ch.py(36000) - ch.top, "info", None, fill_opacity=0.07))
    c.add(ch.hline(36000, "info", DASH))
    c.add(text(ch.right - 6, ch.py(36000) - 8, "tropopause, about 36,000 ft", 12, "end", "info-fg", weight=600))
    c.add(text(ch.right - 6, ch.py(36000) - 24, "above it: constant", 12, "end", "info-fg"))
    c.add(ch.curve([(15, 0), (-56.5, 36000), (-56.5, 46000)], "brand", 2.5, smooth=False))
    c.add(ch.point(15, 0, "brand", 5))
    c.add(text(ch.px(15) + 10, ch.py(0) - 10, "+15 °C at sea level", 13, "start", "brand", weight=700))
    c.add(ch.point(-1, 8000, "brand", 4.5))
    c.add(ch.guide(-1, 8000))
    c.add(text(ch.px(-1) + 26, ch.py(8000) + 18, "8,000 ft: 15 − 16 = −1 °C", 12, "start", "fg", cls="num"))
    c.add(ch.point(-5, 10000, "brand", 4.5))
    c.add(text(ch.px(-5) + 10, ch.py(10000) - 6, "10,000 ft: −5 °C", 12, "start", "fg", cls="num"))
    c.add(ch.point(-56.5, 36000, "brand", 5))
    c.add(text(ch.px(-56.5) + 10, ch.py(36000) - 10, "about −56.5 °C", 13, "start", "brand", weight=700))
    c.add(ch.callout(-21, 18000, 40, 0, ["falls about 2 °C", "per 1,000 ft"], "brand", 13))
    c.add(text(320, 392, "T(ISA) = 15 − 2 × (altitude in ft ÷ 1,000)", 13, "middle", "fg-muted", cls="num"))
    return c


# ---------------------------------------------------------------- 2.12 hypoxia
@chart
def hypoxia_stages_by_altitude() -> Canvas:
    c = Canvas("The four stages of hypoxia by cabin altitude",
               "Approximate cabin altitude bands: indifferent from sea level to 10,000 ft, with night vision reduced from about 5,000 ft; compensatory "
               "from 10,000 to 15,000 ft, breathing and heart rate up, drowsiness, poor judgement and reduced coordination after some time; "
               "disturbance from 15,000 to 20,000 ft, clear impairment with poor judgement, memory and coordination, cyanosis, tunnel vision and "
               "euphoria; critical above 20,000 ft, rapid mental and physical incapacity, then unconsciousness. Heights vary with the person and the day.",
               height=440, prefix="hsa")
    base, k = 410, 14.0  # y at sea level, px per 1,000 ft

    def Y(kft: float) -> float:
        return base - kft * k

    bands = [(0, 10, "ok", "Indifferent", ["Body unbothered: haemoglobin stays nearly fully loaded.", "Night vision reduced from about 5,000 ft; little else."]),
             (10, 15, "warn", "Compensatory", ["Breathing and heart rate increase to keep up; after some", "time drowsiness, poor judgement, reduced coordination."]),
             (15, 20, "bad", "Disturbance", ["Clear impairment: judgement, memory, coordination;", "cyanosis, tunnel vision, euphoria."]),
             (20, 27, "bad", "Critical", ["Rapid mental and physical incapacity,", "then unconsciousness."])]
    x0, x1 = 112, 624
    for lo, hi, colr, name, body in bands:
        y0, y1 = Y(hi), Y(lo)
        if name == "Critical":
            c.add(rect(x0, y0, x1 - x0, y1 - y0, "bad", "bad", SECOND, rx=0, fill_opacity=0.28))
        else:
            c.add(rect(x0, y0, x1 - x0, y1 - y0, SOFT[colr], colr, SECOND))
        mid = (y0 + y1) / 2
        c.add(text(x0 + 14, mid - 10 if name != "Indifferent" else y0 + 26, name, 15, "start", FG[colr], weight=800))
        c.add(multiline(x0 + 14, (mid + 10) if name != "Indifferent" else y0 + 46, body, 12, "start", FG[colr], 1.3))
    # altitude scale
    c.add(line(100, Y(0), 100, Y(27) - 6, "fg-muted", SECOND, arrow_end=True))
    for ft in (0, 5, 10, 15, 20, 25):
        c.add(line(94, Y(ft), 100, Y(ft), "fg-muted", SECOND))
        c.add(num(90, Y(ft) + 4, f"{ft * 1000:,}" if ft else "SL", 12, "end", "fg-muted"))
    c.add(text(16, 20, "Cabin altitude (ft, approx.)", 12, "start", "fg-muted", weight=600))
    # night-vision marker at 5,000 ft
    c.add(line(x0, Y(5), x1, Y(5), "ok", THIN, dash=DASH))
    c.add(text(x1 - 10, Y(5) + 18, "about 5,000 ft: night vision starts to fade", 12, "end", "ok-fg", weight=600))
    c.add(text(x0 + 14, Y(1.6), "Insidious: each stage creeps in while you feel fine.", 13, "start", "ok-fg", italic=True, weight=600))
    c.add(plane_side(x1 - 46, Y(2), 0.65, pitch=12, color="ok", fill="ok-soft"))
    return c


# ---------------------------------------------------------------- 2.13 human factors
@chart
def information_processing_model() -> Canvas:
    c = Canvas("How the brain turns the senses into action",
               "The information-processing model: senses with a short-lived sensory store, attention as a limited single channel, perception "
               "against experience and expectation, the mental model (situational awareness), decision and action, with feedback through the "
               "senses. Short-term memory holds about 7 plus or minus 2 items for 15 to 30 seconds; long-term memory is large but recall can fail "
               "under stress. Errors can enter at every stage.", height=440, prefix="ipm")
    stages = [("Senses", ["eyes, ears,", "balance, touch"], "sensory store:", "a fraction of a second", "info"),
              ("Attention", ["single channel:", "one demanding", "task at a time"], None, None, "warn"),
              ("Perception", ["compared with", "experience and", "expectation"], None, None, "brand"),
              ("Decision", ["choose what", "to do"], None, None, "brand"),
              ("Action", ["act on the", "controls, radio"], None, None, "brand")]
    W_, gap, y, h = 108, 17, 120, 104
    xs = [16 + i * (W_ + gap) for i in range(5)]
    for i, (name, body, s1, s2, colr) in enumerate(stages):
        x = xs[i]
        c.add(rect(x, y, W_, h, SOFT[colr], colr, MAIN, rx=10))
        c.add(text(x + W_ / 2, y + 24, name, 15, "middle", FG[colr], weight=800))
        c.add(multiline(x + W_ / 2, y + 46, body, 12, "middle", FG[colr], 1.3))
        if i < 4:
            c.add(arrow(x + W_ + 2, y + h / 2, x + W_ + gap - 2, y + h / 2, "fg", MAIN))
    # attention as a funnel: many cues in, few through
    c.add(multiline(xs[1] + W_ / 2, y + h + 20, ["many cues in,", "few get through"], 11, "middle", "warn-fg", 1.3, weight=600))
    c.add(text(xs[0] + W_ / 2, y + h + 20, "sensory store:", 11, "middle", "info-fg", weight=600))
    c.add(text(xs[0] + W_ / 2, y + h + 34, "held for a fraction", 11, "middle", "info-fg"))
    c.add(text(xs[0] + W_ / 2, y + h + 48, "of a second, most fades", 11, "middle", "info-fg"))
    # mental model across perception and decision
    mx0, mx1 = xs[2], xs[3] + W_
    c.add(rect(mx0, 30, mx1 - mx0, 58, "surface-2", "brand", MAIN, rx=10))
    c.add(text((mx0 + mx1) / 2, 52, "Mental model", 14, "middle", "brand", weight=800))
    c.add(text((mx0 + mx1) / 2, 72, "= situational awareness", 12, "middle", "fg-muted"))
    c.add(arrow(xs[2] + W_ / 2, y - 2, xs[2] + W_ / 2, 90, "brand", SECOND, both=True))
    c.add(arrow(xs[3] + W_ / 2, 90, xs[3] + W_ / 2, y - 2, "brand", SECOND))
    # feedback loop over the top
    fy = 16
    c.add(path(f"M{xs[4] + W_ / 2} {y - 2} L{xs[4] + W_ / 2} {fy} L{xs[0] + W_ / 2} {fy} L{xs[0] + W_ / 2} {y - 4}", "ok", None, MAIN, arrow_end=True))
    c.add(text(xs[1] + W_ / 2, fy + 18, "feedback: monitor", 12, "middle", "ok-fg", weight=600))
    c.add(text(xs[1] + W_ / 2, fy + 32, "the result", 12, "middle", "ok-fg", weight=600))
    # memory
    my = 296
    mx = xs[1]
    c.add(rect(mx, my, xs[4] + W_ - mx, 44, "info-soft", "info", SECOND, rx=8))
    c.add(text(mx + 12, my + 19, "Short-term (working) memory: about 7 ± 2 items for 15 to 30 s", 12, "start", "info-fg", weight=700))
    c.add(text(mx + 12, my + 35, "an interruption wipes it: write clearances down", 12, "start", "info-fg"))
    c.add(rect(mx, my + 52, xs[4] + W_ - mx, 44, "surface-2", "line-strong", SECOND, rx=8))
    c.add(text(mx + 12, my + 71, "Long-term memory: large and durable", 12, "start", "fg", weight=700))
    c.add(text(mx + 12, my + 87, "but recall depends on cues and can fail under stress", 12, "start", "fg-muted"))
    for xx in (xs[2] + W_ / 2, xs[3] + W_ / 2):
        c.add(line(xx, y + h + 2, xx, my - 2, "info", SECOND, dash=DASH))
    # where errors enter
    ey = 412
    c.add(text(16, ey - 2, "Errors enter at every stage:", 12, "start", "bad", weight=700))
    errs = ["cue not sensed", "attention elsewhere", "cue misperceived", "poor decision", "badly executed"]
    for i, e in enumerate(errs):
        c.add(text(xs[i] + W_ / 2, ey + 18, e, 11, "middle", "bad", weight=600))
    return c


# ---------------------------------------------------------------- 2.14 first aid and survival
@chart
def ground_to_air_survival_codes() -> Canvas:
    c = Canvas("Ground-to-air signal codes",
               "Five symbols survivors lay out on the ground for search aircraft, as shown in the ERSA: V means require assistance, X means require "
               "medical assistance, N means no, Y means yes, and an arrow means proceeding in this direction. Make them large and contrasting: rocks "
               "on red sand, dark branches on a pale claypan, or trenches whose shadows show. Lay an arrow only if you really do leave, pointing the "
               "way you have gone.", height=364, prefix="gas")
    codes = [("V", "Require", "assistance"), ("X", "Require", "medical", "assistance"), ("N", "No"), ("Y", "Yes"), ("→", "Proceeding in", "this direction")]
    W_, gap = 112, 12
    for i, item in enumerate(codes):
        sym, lines_ = item[0], list(item[1:])
        x, y = 16 + i * (W_ + gap), 18
        hi = sym in ("V", "X")
        c.add(rect(x, y, W_, 196, "warn-soft", "brand" if hi else "line-strong", MAIN if hi else SECOND, rx=10))
        cx, cy = x + W_ / 2, y + 78
        st = dict(color="fg", width=9)
        if sym == "V":
            c.add(polyline_thick([(cx - 30, cy - 40), (cx, cy + 40), (cx + 30, cy - 40)], **st))
        elif sym == "X":
            c.add(polyline_thick([(cx - 30, cy - 40), (cx + 30, cy + 40)]), polyline_thick([(cx + 30, cy - 40), (cx - 30, cy + 40)]))
        elif sym == "N":
            c.add(polyline_thick([(cx - 28, cy + 40), (cx - 28, cy - 40), (cx + 28, cy + 40), (cx + 28, cy - 40)], **st))
        elif sym == "Y":
            c.add(polyline_thick([(cx - 30, cy - 40), (cx, cy), (cx + 30, cy - 40)], **st), polyline_thick([(cx, cy + 10), (cx, cy + 40)]))
        else:
            c.add(polyline_thick([(cx - 38, cy), (cx + 24, cy)]), polyline_thick([(cx + 8, cy - 24), (cx + 34, cy), (cx + 8, cy + 24)], **st))
        c.add(multiline(cx, y + 146, lines_, 13, "middle", "brand" if hi else "fg", 1.3, weight=700))
    c.add(text(16 + W_ + gap / 2, 238, "have V and X by heart", 12, "middle", "brand", weight=600))
    # how to lay them
    y = 256
    c.add(rect(16, y, 608, 92, "surface-2", "line-strong", SECOND, rx=10))
    c.add(text(30, y + 24, "Make them large and contrasting", 14, "start", "fg", weight=700))
    c.add(multiline(30, y + 46, ["rocks on red sand, dark branches on a pale claypan,", "or trenches dug so their shadows show;",
                                 "each line as long and wide as the materials allow"], 12, "start", "fg-muted", 1.4))
    c.add(text(610, y + 24, "The arrow: only if you really leave", 13, "end", "bad", weight=700))
    c.add(multiline(610, y + 46, ["and it points the way you have gone.", "Otherwise stay with the aircraft."], 12, "end", "fg-muted", 1.4))
    return c


def polyline_thick(points: list[tuple[float, float]], color: str = "fg", width: float = 9) -> str:
    """A stroke laid out in rocks: small stones every few px along the polyline."""
    rnd = random.Random(len(points) * 31 + int(points[0][0]))
    out = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / 10))
        for k in range(n + 1):
            t = k / n
            r = 5.2 + rnd.uniform(-0.8, 0.8)
            out.append(ellipse(x0 + (x1 - x0) * t + rnd.uniform(-1, 1), y0 + (y1 - y0) * t + rnd.uniform(-1, 1), r, r * 0.85, "fg-muted", "fg", THIN))
    return "".join(out)


# ---------------------------------------------------------------- 2.1 basic health
@chart
def pilot_health_factors_map() -> Canvas:
    c = Canvas("The pilot as a system",
               "Five parts of the pilot, like the systems of an aeroplane, and the health factors that attack each one. Fuel (food and water): "
               "skipped meals, heavy meals, dehydration, food poisoning. Oxygen delivery: coronary risk factors, smoking, blood donation. "
               "Structure: injuries, pregnancy, ageing. Sensors: colds and hay fever blocking ears and sinuses, migraine aura, ageing eyes and ears. "
               "Processor (the brain): alcohol, medication, anxiety, depression, fears, headache. Factors that can cause sudden incapacitation, "
               "such as a heart attack, food poisoning, a migraine or a faint, are marked.", height=486, prefix="phm")
    c.add(text(320, 30, "Which part does each factor degrade, and could it fail suddenly?", 15, "middle", "fg", weight=700))

    def sudden(x: float, y: float, w: float, label: str) -> None:
        c.add(rect(x, y - 14, w, 22, "bad-soft", "bad", SECOND, rx=11))
        c.add(circle(x + 12, y - 3, 7, "bad", None))
        c.add(text(x + 12, y + 1.5, "!", 11, "middle", "surface", weight=800))
        c.add(text(x + 26, y + 1, label, 12, "start", "bad-fg", weight=700))

    W_, H_ = 196, 190
    cards = [
        ("Fuel", "food and water", [("skipped meal: low sugar", 0), ("heavy meal: drowsy", 0), ("dehydration", 0), ("food poisoning", 1)]),
        ("Oxygen delivery", "heart, lungs, blood", [("coronary risk factors:", 0), ("smoking, cholesterol,", 2),
                                                    ("obesity, heredity", 2), ("heart attack", 1), ("blood donation", 0)]),
        ("Structure", "can you reach and push?", [("injury: full rudder and", 0), ("brakes still possible?", 2), ("pregnancy: reach, belts", 0),
                                                  ("ageing: slower reactions", 0)]),
        ("Sensors", "eyes, ears, balance", [("cold, hay fever: ears", 0), ("and sinuses block", 2), ("migraine aura", 1),
                                           ("ageing: near focus,", 0), ("high-pitch hearing", 2)]),
        ("Processor", "the brain", [("alcohol, hangover", 0), ("medication, even OTC", 0), ("anxiety, depression,", 0),
                                    ("fears, headache", 2), ("a faint", 1)]),
    ]
    pos = [(16, 50), (222, 50), (428, 50), (16, 250), (222, 250)]
    for (name, sub, items), (x, y) in zip(cards, pos):
        c.add(rect(x, y, W_, H_, "surface", "line-strong", SECOND, rx=10))
        c.add(text(x + 14, y + 26, name, 16, "start", "brand", weight=800))
        c.add(text(x + 14, y + 44, sub, 12, "start", "fg-muted"))
        yy = y + 70
        for label, sud in items:
            if sud == 1:
                sudden(x + 10, yy, W_ - 20, label)
            elif sud == 2:
                c.add(text(x + 26, yy - 6, label, 12, "start", "fg"))
                yy -= 6
            else:
                c.add(circle(x + 18, yy - 4, 2.5, "fg-muted", None))
                c.add(text(x + 26, yy, label, 12, "start", "fg"))
            yy += 25
    x, y = 428, 250
    c.add(rect(x, y, W_, H_, "surface-2", "line-strong", SECOND, rx=10))
    c.add(text(x + 14, y + 26, "Two kinds of failure", 14, "start", "fg", weight=700))
    c.add(text(x + 14, y + 52, "Subtle impairment", 13, "start", "fg", weight=700))
    c.add(multiline(x + 14, y + 70, ["you fly worse and may", "not notice it"], 12, "start", "fg-muted", 1.3))
    sudden(x + 10, y + 114, W_ - 20, "Sudden")
    c.add(multiline(x + 14, y + 142, ["incapacitation in seconds:", "usually fatal flying solo"], 12, "start", "fg-muted", 1.3))
    c.add(rect(16, 448, 608, 32, "ok-soft", "ok", SECOND, rx=8))
    c.add(text(320, 469, "Most of the medical standard exists to screen out the sudden kind.", 13, "middle", "ok-fg", weight=700))
    return c


# ---------------------------------------------------------------- 2.3 hyperventilation
@chart
def hyperventilation_vicious_circle() -> Canvas:
    c = Canvas("Hyperventilation feeds on itself",
               "A loop: anxiety makes you breathe faster or deeper; over-breathing blows off carbon dioxide; low CO2 narrows the brain's blood "
               "vessels, makes haemoglobin hold on to its oxygen and makes nerves irritable; that brings dizziness, tingling and spasm; the alarming "
               "symptoms make you more anxious. Break the circle by recognising it, slowing the breathing to one breath every 4 to 5 seconds and "
               "talking out loud; at altitude use oxygen or descend. Do not take deep breaths.", height=372, prefix="hvc")
    c.style(".hvc-orbit{animation:hvc-spin 8s linear infinite}@keyframes hvc-spin{to{transform:rotate(360deg)}}")
    cx, cy, R = 208, 206, 122
    # the loop track and the travelling dot
    c.add(circle(cx, cy, R, None, "line-strong", 6))
    for a0, a1 in ((-46, -18), (18, 46), (134, 162), (198, 226)):
        c.add(path(arc_path(cx, cy, R, a0, a1), "bad", None, 3, arrow_end=True))
    c.add(group(group(circle(R * math.cos(math.radians(-32)), R * math.sin(math.radians(-32)), 7, "bad", "surface", 2), cls="hvc-orbit"), transform=f"translate({cx} {cy})"))
    nodes = [(cx, cy - R, "Anxiety", ["stress, fear, a first solo"], "warn"),
             (cx + R, cy, "Over-breathing", ["faster or deeper", "than you need"], "warn"),
             (cx, cy + R, "CO₂ falls", ["brain vessels narrow,", "haemoglobin grips O₂"], "bad"),
             (cx - R, cy, "Symptoms", ["dizzy, tingling,", "spasm: alarming"], "bad")]
    for x, y, head, body, colr in nodes:
        w, h = 140, 62
        c.add(rect(x - w / 2, y - h / 2, w, h, SOFT[colr], colr, MAIN, rx=10))
        c.add(text(x, y - h / 2 + 20, head, 14, "middle", FG[colr], weight=800))
        c.add(multiline(x, y - h / 2 + 37, body, 11, "middle", FG[colr], 1.3))
    c.add(multiline(cx, cy - 4, ["builds over", "a minute or so"], 12, "middle", "fg-muted", 1.3))
    # breakers
    x = 410
    c.add(rect(x, 24, 214, 262, "ok-soft", "ok", SECOND, rx=10))
    c.add(text(x + 14, 48, "Break the circle", 15, "start", "ok-fg", weight=800))
    steps = [("1", ["Recognise it: name it", "and the panic eases"]), ("2", ["Slow down: one breath", "every 4 to 5 seconds"]),
             ("3", ["Talk out loud: speech", "forces slow breathing"]), ("4", ["At altitude: oxygen or", "descend: it may be hypoxia"])]
    yy = 76
    for n, body in steps:
        c.add(circle(x + 24, yy + 2, 11, "surface", "ok", SECOND))
        c.add(text(x + 24, yy + 7, n, 13, "middle", "ok-fg", weight=800, cls="num"))
        c.add(multiline(x + 44, yy + 2, body, 12, "start", "ok-fg", 1.3))
        yy += 56
    c.add(rect(x, 298, 214, 52, "bad-soft", "bad", SECOND, rx=10))
    c.add(text(x + 14, 320, "Not: \"take deep breaths\"", 13, "start", "bad-fg", weight=800))
    c.add(text(x + 14, 338, "it blows off more CO₂", 12, "start", "bad-fg"))
    return c


# ---------------------------------------------------------------- 2.5 the ear
@chart
def speech_masking_by_cabin_noise() -> Canvas:
    c = Canvas("Cabin noise masks the consonants",
               "A sketch of sound level against pitch. Steady engine and airflow noise covers the whole range. Vowels are louder and lower, so they "
               "stand above the noise and you hear that someone spoke. Consonants such as s, t, f, th and k are quiet and high-pitched, so the noise "
               "drowns them and similar words blur. Noise-induced hearing loss starts around 4,000 Hz, in the same band. Turning the volume up "
               "raises the noise as well; a better headset seal lowers the noise at the ear.", height=394, prefix="smn")
    lg = math.log2
    ch = Chart(c, (lg(125), lg(8000)), (0, 10), box=(70, 30, 610, 300), xlabel="Pitch (frequency, Hz)", ylabel="Sound level (sketch)",
               xticks=[lg(f) for f in (125, 250, 500, 1000, 2000, 4000, 8000)], yticks=[],
               xfmt=lambda v: {7: "125", 8: "250", 9: "500", 10: "1,000", 11: "2,000", 12: "4,000", 13: "8,000"}[round(v)])
    c.add(ch.band(lg(2000), lg(8000), "bad", 0.06))
    c.add(ch.axes())
    noise = [(lg(125), 8.2), (lg(250), 8.0), (lg(500), 7.2), (lg(1000), 6.3), (lg(2000), 5.6), (lg(4000), 5.0), (lg(8000), 4.4)]
    c.add(ch.area(noise, "fg-muted", 0.22))
    c.add(ch.curve(noise, "fg-muted", MAIN))
    c.add(text(ch.px(lg(140)), ch.py(1.2), "steady cabin noise: engine, propeller, airflow", 13, "start", "fg-muted", weight=700))
    vow = [(lg(200), 6), (lg(320), 8.4), (lg(500), 9.3), (lg(800), 8.6), (lg(1250), 6)]
    c.add(ch.area(vow, "ok", 0.25, baseline=6))
    c.add(ch.curve(vow, "ok", MAIN))
    c.add(text(ch.px(lg(500)), ch.py(9.3) - 10, "vowels: loud and low, heard", 13, "middle", "ok-fg", weight=700))
    con = [(lg(2000), 2.0), (lg(2800), 3.6), (lg(4000), 4.2), (lg(5600), 3.6), (lg(8000), 2.0)]
    c.add(ch.area(con, "bad", 0.2, baseline=2))
    c.add(ch.curve(con, "bad", MAIN, dash=DASH))
    c.add(multiline(ch.px(lg(1900)), ch.py(3.6), ["consonants s, t, f, th, k:", "quiet and high, drowned"], 13, "end", "bad", 1.3, weight=700))
    c.add(ch.vline(lg(4000), "bad", DASH, y_to=10))
    c.add(text(ch.px(lg(4000)) - 6, ch.py(10) + 12, "4,000 Hz: hearing", 11, "end", "bad"))
    c.add(text(ch.px(lg(4000)) - 6, ch.py(10) + 26, "loss starts here", 11, "end", "bad"))
    c.add(text(320, 364, "\"Five\" or \"nine\"? The consonants decide, and they are the first sounds lost.", 13, "middle", "fg", weight=600))
    c.add(text(320, 383, "Volume up raises the noise too; a better seal or ANR lowers the noise at the ear.", 12, "middle", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.6 hearing protection
@chart
def passive_vs_anr_attenuation_by_frequency() -> Canvas:
    c = Canvas("Passive and ANR protection cover different pitches",
               "A sketch of noise reduction against pitch. A passive headset's shell and seal block high-frequency hiss and whine well but let much "
               "of the low-frequency engine and propeller drone through. ANR electronics cancel the low-frequency drone and do little at high "
               "frequency. Together they cover the whole range; both depend on an unbroken ear seal.", height=386, prefix="anr")
    ch = Chart(c, (0, 10), (0, 10), box=(70, 30, 610, 290), xlabel="Pitch of the noise", ylabel="Noise reduction (sketch)", xticks=[], yticks=[])
    c.add(ch.band(0, 3.2, "warn", 0.08))
    c.add(ch.axes())
    c.add(text(ch.px(1.6), ch.py(9.6), "engine and", 12, "middle", "warn-fg", weight=600))
    c.add(text(ch.px(1.6), ch.py(9.6) + 15, "propeller drone", 12, "middle", "warn-fg", weight=600))
    c.add(text(ch.left, ch.bottom + 18, "low", 12, "start", "fg-muted"))
    c.add(text(ch.right, ch.bottom + 18, "high", 12, "end", "fg-muted"))

    def passive(x: float) -> float:
        return 1.5 + 6.5 / (1 + math.exp(-(x - 4.2) * 1.1))

    def anr(x: float) -> float:
        return 4.2 * math.exp(-((x - 1.4) / 1.9) ** 2) if x < 6.5 else 0.0

    P = sample(passive, 0, 10, 60)
    T = sample(lambda x: passive(x) + anr(x), 0, 10, 60)
    c.add(ch.area(T, "brand", 0.10))
    c.add(ch.curve(P, "info", MAIN, dash=DASH))
    c.add(ch.curve(T, "brand", 2.5))
    c.add(text(ch.px(6.2), ch.py(passive(6.2)) + 22, "passive shell and seal alone", 13, "start", "info-fg", weight=700))
    c.add(text(ch.px(1.5), ch.py(passive(1.5) + anr(1.5)) - 14, "with ANR added", 13, "middle", "brand", weight=700))
    for x in (0.9, 1.6, 2.3):
        c.add(arrow(ch.px(x), ch.py(passive(x)) - 4, ch.px(x), ch.py(passive(x) + anr(x)) + 6, "brand", SECOND))
    c.add(text(ch.px(0.25), ch.py(0.95), "ANR cancels the", 12, "start", "brand", weight=600))
    c.add(text(ch.px(0.25), ch.py(0.95) + 15, "low-frequency drone", 12, "start", "brand", weight=600))
    c.add(text(ch.px(9.6), ch.py(9.2), "hiss and whine: the shell", 12, "end", "info-fg"))
    c.add(text(ch.px(9.6), ch.py(9.2) + 15, "blocks them already", 12, "end", "info-fg"))
    c.add(rect(16, 340, 608, 34, "bad-soft", "bad", SECOND, rx=8))
    c.add(text(320, 362, "Both need an unbroken ear seal: a gap lets noise in at every pitch.", 13, "middle", "bad-fg", weight=700))
    return c


def ear_canal(x: float, y: float, depth: float, color: str = "fg") -> str:
    """Cross-section of the ear canal from the outer ear (left) to the eardrum (right); a foam plug pushed in by `depth` (0..1)."""
    out = [path(f"M{x} {y - 34} C{x + 20} {y - 34} {x + 24} {y - 14} {x + 44} {y - 14} C{x + 80} {y - 14} {x + 96} {y - 22} {x + 120} {y - 18}",
                "fg", None, SECOND),
           path(f"M{x} {y + 34} C{x + 20} {y + 34} {x + 24} {y + 14} {x + 44} {y + 14} C{x + 80} {y + 14} {x + 96} {y + 6} {x + 120} {y + 10}",
                "fg", None, SECOND),
           line(x + 120, y - 20, x + 120, y + 12, "info", 3)]
    px = x + 6 + depth * 64
    out.append(rect(px - 22, y - 13, 48, 26, "warn-soft", "warn", SECOND, rx=9))
    return "".join(out)


@chart
def earplug_insertion() -> Canvas:
    c = Canvas("Fitting a foam earplug",
               "Three steps and the result. Roll the foam plug into a thin cylinder. Pull the top of the ear up and back to straighten the canal. "
               "Push the plug well in and hold it while it expands to fill the canal. A plug pushed well in seals and protects; a plug resting in "
               "the outer canal, half sticking out, protects very little.", height=340, prefix="epi")
    PW = 196
    heads = ["1  Roll it thin", "2  Ear up and back", "3  Push in and hold"]
    for i, h in enumerate(heads):
        x = 16 + i * (PW + 10)
        c.add(rect(x, 14, PW, 196, "surface", "line-strong", SECOND, rx=10))
        c.add(text(x + 12, 36, h, 14, "start", "fg", weight=700))
    # 1 roll: fat plug -> thin plug
    x = 16
    c.add(rect(x + 26, 70, 40, 56, "warn-soft", "warn", SECOND, rx=12))
    c.add(arrow(x + 76, 98, x + 112, 98, "fg-muted", SECOND))
    c.add(rect(x + 126, 76, 20, 44, "warn-soft", "warn", SECOND, rx=8))
    c.add(multiline(x + PW / 2, 166, ["between finger and thumb", "into a thin cylinder"], 12, "middle", "fg-muted", 1.3))
    # 2 ear: head in side view facing left, the ear pulled up and back
    x = 16 + PW + 10
    hx, hy = x + 100, 124
    c.add(path(f"M{hx - 44} {hy + 56} C{hx - 50} {hy + 30} {hx - 66} {hy + 20} {hx - 58} {hy + 4} L{hx - 66} {hy - 4} C{hx - 60} {hy - 50} {hx - 20} {hy - 66} "
               f"{hx + 14} {hy - 62} C{hx + 60} {hy - 58} {hx + 74} {hy - 10} {hx + 62} {hy + 26} C{hx + 56} {hy + 44} {hx + 44} {hy + 56} {hx + 40} {hy + 60}",
               "fg", "surface-2", MAIN))
    ex, ey = hx + 18, hy + 4
    c.add(path(f"M{ex - 8} {ey - 22} C{ex + 14} {ey - 30} {ex + 22} {ey - 6} {ex + 10} {ey + 6} C{ex + 4} {ey + 14} {ex + 8} {ey + 24} {ex - 2} {ey + 26}",
               "fg", None, MAIN))
    c.add(circle(ex - 2, ey + 2, 4, "fg", None))
    c.add(arrow(ex + 8, ey - 28, ex + 38, ey - 52, "brand", MAIN))
    c.add(text(hx - 62, hy - 30, "face", 11, "end", "fg-muted"))
    c.add(multiline(x + PW / 2, 200, ["straightens the canal"], 12, "middle", "fg-muted", 1.3))
    # 3 push in and hold, it expands
    x = 16 + 2 * (PW + 10)
    c.add(ear_canal(x + 34, 104, 0.9))
    for dy in (-20, 20):
        c.add(arrow(x + 34 + 6 + 0.9 * 64, 104 + dy * 0.2, x + 34 + 6 + 0.9 * 64, 104 + dy * 0.75, "warn", SECOND))
    c.add(text(x + 154, 80, "eardrum", 11, "start", "info"))
    c.add(multiline(x + PW / 2, 166, ["hold it in while", "it expands to seal"], 12, "middle", "fg-muted", 1.3))
    # results
    y = 222
    c.add(rect(16, y, 301, 104, "ok-soft", "ok", SECOND, rx=10))
    c.add(text(30, y + 22, "Well in: seals, good protection", 13, "start", "ok-fg", weight=700))
    c.add(ear_canal(60, y + 64, 0.9))
    c.add(rect(323, y, 301, 104, "bad-soft", "bad", SECOND, rx=10))
    c.add(text(337, y + 22, "Resting half out: little protection", 13, "start", "bad-fg", weight=700))
    c.add(ear_canal(380, y + 64, -0.08))
    c.add(text(520, y + 70, "refit it", 12, "start", "bad-fg", weight=600))
    c.add(text(200, y + 70, "check you still hear", 11, "start", "ok-fg"))
    c.add(text(200, y + 84, "radio and stall horn", 11, "start", "ok-fg"))
    return c


# ---------------------------------------------------------------- 2.8 motion sickness
@chart
def motion_sickness_progression() -> Canvas:
    c = Canvas("How motion sickness progresses",
               "Six stages in order: loss of interest and a vague unease, going quiet; yawning and increased saliva; pallor; cold sweating; nausea; "
               "vomiting. Performance falls well before vomiting: concentration and motivation drop in the first stages, so the early signs are the "
               "time to act.", height=380, prefix="msp")
    stages = [("1", "Unease", ["no interest,", "goes quiet"]), ("2", "Yawning", ["more saliva"]), ("3", "Pallor", ["face goes pale"]),
              ("4", "Cold sweat", ["often feels", "warm"]), ("5", "Nausea", []), ("6", "Vomiting", [])]
    W_, gap = 94, 9
    for i, (n, name, body) in enumerate(stages):
        x = 16 + i * (W_ + gap)
        y = 150 + i * 22
        colr = "warn" if i < 3 else "bad"
        c.add(rect(x, y, W_, 330 - y, SOFT[colr], colr, SECOND, rx=8))
        c.add(circle(x + 18, y + 20, 11, "surface", colr, SECOND))
        c.add(text(x + 18, y + 25, n, 13, "middle", FG[colr], weight=800, cls="num"))
        c.add(text(x + 8, y + 52, name, 13, "start", FG[colr], weight=700))
        c.add(multiline(x + 8, y + 70, body, 11, "start", FG[colr], 1.3))
    # performance line falls early
    xs = [16 + i * (W_ + gap) + W_ / 2 for i in range(6)]
    perf = [96, 104, 116, 124, 128, 130]
    pts = [(xs[0] - 40, 50)] + list(zip(xs, perf))
    c.add(path(smooth_path([(16, 50), (xs[0], 62), (xs[1], 92), (xs[2], 112), (xs[3], 122), (xs[4], 127), (xs[5], 130)]), "brand", None, 2.5))
    c.add(text(16, 40, "Your flying: concentration, lookout, accuracy", 13, "start", "brand", weight=700))
    c.add(text(xs[3], 110, "already poor long before stage 6", 12, "start", "brand"))
    # act-early bracket
    c.add(rect(16, 338, 3 * W_ + 2 * gap, 32, "ok-soft", "ok", SECOND, rx=8))
    c.add(text(16 + (3 * W_ + 2 * gap) / 2, 359, "Act here: air, horizon, head still", 13, "middle", "ok-fg", weight=700))
    c.add(text(16 + 3 * (W_ + gap) + 8, 359, "Later: flying already degraded", 13, "start", "bad", weight=700))
    return c


# ---------------------------------------------------------------- 2.9 acceleration
def seated_pilot(x: float, y: float, pooled: float = 0.0) -> str:
    """Seated pilot in side view facing right; (x, y) is the heart. pooled (0..1) shades blood pooled in the legs and lower body."""
    out = [path(f"M{x - 34} {y - 30} L{x - 40} {y + 70} L{x + 50} {y + 74} L{x + 56} {y + 140}", "line-strong", None, 5)]  # seat
    out.append(path(f"M{x - 22} {y - 46} C{x - 30} {y} {x - 28} {y + 40} {x - 22} {y + 62} L{x + 50} {y + 62} L{x + 60} {y + 124} L{x + 74} {y + 124} "
                    f"L{x + 66} {y + 52} L{x + 4} {y + 48} C{x + 10} {y + 10} {x + 18} {y - 30} {x + 6} {y - 46} Z", "fg", "surface-2", MAIN))
    out.append(circle(x - 6, y - 74, 26, "surface-2", "fg", MAIN))
    if pooled:
        out.append(path(f"M{x + 6} {y + 50} L{x + 64} {y + 54} L{x + 72} {y + 122} L{x + 62} {y + 122} L{x + 52} {y + 64} L{x - 20} {y + 62} Z",
                        None, "bad", 0, fill_opacity=0.25 + 0.45 * pooled))
    return "".join(out)


@chart
def g_blood_column() -> Canvas:
    c = Canvas("Why g starves the brain of blood",
               "Two seated pilots. The brain is about 30 cm above the heart, and the heart must push blood up that column. The pressure needed is "
               "rho times n g times h, so it rises in direct proportion to the load factor: at 3 g the column weighs three times as much. Under "
               "positive g blood also pools in the legs and lower body, so less returns to the heart. Reflexes that raise heart rate and tighten "
               "vessels take several seconds, so a sudden onset is worse.", height=400, prefix="gbc")
    for i, (n, label, colr) in enumerate([(1, "1 g: straight and level", "ok"), (3, "3 g: steep turn or pull-up", "bad")]):
        x0 = 16 + i * 310
        c.add(rect(x0, 14, 298, 300, "surface", "line-strong", SECOND, rx=10))
        c.add(text(x0 + 14, 38, label, 14, "start", "fg", weight=700))
        hx, hy = x0 + 64, 170
        c.add(seated_pilot(hx, hy, pooled=0 if n == 1 else 1))
        c.add(circle(hx - 4, hy, 7, "bad", None))  # heart
        c.add(circle(hx + 8, hy - 78, 4, "fg", None))  # eye
        # blood column from heart to eye level
        bx = hx + 70
        c.add(line(bx - 8, hy, bx + 8, hy, "fg-muted", SECOND))
        c.add(line(bx - 8, hy - 78, bx + 8, hy - 78, "fg-muted", SECOND))
        c.add(line(hx + 4, hy, bx - 10, hy, "line-strong", THIN, dash=DASH))
        c.add(line(hx + 14, hy - 78, bx - 10, hy - 78, "line-strong", THIN, dash=DASH))
        c.add(rect(bx - 5, hy - 76, 10, 74, "bad", None, fill_opacity=0.25 if n == 1 else 0.65))
        c.add(text(bx + 12, hy - 34, "30 cm", 12, "start", "fg-muted", cls="num"))
        # weight arrows on the column
        for k in range(n):
            ax = bx + 56 + k * 18
            c.add(arrow(ax, hy - 70, ax, hy - 26, colr, MAIN))
        c.add(text(bx + 56 + (n - 1) * 9, hy - 6, f"{n}×", 15, "middle", FG[colr], weight=800, cls="num"))
        c.add(text(bx + 56 + (n - 1) * 9, hy + 10, "weight", 11, "middle", FG[colr]))
        c.add(multiline(x0 + 154, 236, ["the heart pushes" if n == 1 else "3 times the pressure", "blood up the column" if n == 1 else "just to reach eye", "" if n == 1 else "level: grey-out may begin"],
                        11, "start", FG[colr], 1.35, weight=600))
        if n == 3:
            c.add(text(hx + 80, hy + 120, "blood pools in", 11, "start", "bad", weight=600))
            c.add(text(hx + 80, hy + 134, "the legs", 11, "start", "bad", weight=600))
    c.add(text(320, 342, "Δp = ρ (n g) h: the pressure needed grows in proportion to the g.", 14, "middle", "fg", weight=700, cls="num"))
    c.add(text(320, 364, "Reflexes raise the heart rate and tighten vessels, but take several seconds:", 12, "middle", "fg-muted"))
    c.add(text(320, 381, "a slow build-up of g is tolerated better than a sudden one.", 12, "middle", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.11 respiration and circulation
@chart
def respiration_and_circulation() -> Canvas:
    c = Canvas("From the air to your cells: two loops",
               "The diaphragm draws air into the lungs' alveoli. Oxygen diffuses across the thin wall into the blood and carbon dioxide diffuses out. "
               "Haemoglobin in the red cells carries the oxygen. The heart is two pumps: the right side pumps oxygen-poor blood through the lungs, "
               "the left side pumps oxygen-rich blood through the arteries to the body's tissues, where oxygen leaves the blood and carbon dioxide "
               "enters it; the blood returns through the veins.", height=470, prefix="rac")
    # lungs
    lx, ly = 320, 92
    c.add(rect(lx - 150, ly - 56, 300, 112, "sky-soft", "sky-fg", SECOND, rx=40))
    c.add(text(lx, ly - 34, "Lungs: millions of alveoli", 14, "middle", "sky-fg", weight=700))
    # one alveolus with its capillary
    ax, ay = lx - 60, ly + 10
    c.add(circle(ax, ay, 26, "surface", "sky-fg", SECOND))
    c.add(text(ax, ay + 4, "air", 11, "middle", "sky-fg"))
    c.add(path(f"M{ax + 30} {ay + 26} C{ax + 40} {ay - 10} {ax + 60} {ay - 26} {ax + 120} {ay - 26}", "bad", None, 6))
    c.add(path(f"M{ax - 30} {ay + 30} C{ax + 4} {ay + 34} {ax + 22} {ay + 30} {ax + 30} {ay + 26}", "info", None, 6))
    c.add(arrow(ax + 18, ay - 6, ax + 38, ay - 14, "ok", SECOND))
    c.add(text(ax + 52, ay - 2, "O₂ in", 12, "start", "ok-fg", weight=700))
    c.add(arrow(ax + 12, ay + 30, ax + 4, ay + 14, "fg-muted", SECOND))
    c.add(text(ax + 74, ay + 22, "CO₂ out: diffusion,", 11, "start", "fg-muted"))
    c.add(text(ax + 74, ay + 36, "high to low pressure", 11, "start", "fg-muted"))
    # diaphragm
    c.add(path(f"M{lx - 100} {ly + 72} Q{lx} {ly + 52} {lx + 100} {ly + 72}", "fg-muted", None, 3))
    c.add(text(lx, ly + 90, "diaphragm draws air in", 11, "middle", "fg-muted"))
    # heart
    hx, hy = 320, 252
    c.add(rect(hx - 96, hy - 40, 90, 80, "info-soft", "info", MAIN, rx=14))
    c.add(rect(hx + 6, hy - 40, 90, 80, "bad-soft", "bad", MAIN, rx=14))
    c.add(text(hx - 51, hy - 6, "Right side", 13, "middle", "info-fg", weight=700))
    c.add(text(hx - 51, hy + 12, "to the lungs", 11, "middle", "info-fg"))
    c.add(text(hx + 51, hy - 6, "Left side", 13, "middle", "bad-fg", weight=700))
    c.add(text(hx + 51, hy + 12, "to the body", 11, "middle", "bad-fg"))
    c.add(text(hx, hy + 58, "Heart: two pumps", 13, "middle", "fg", weight=700))
    # tissues
    tx, ty = 320, 404
    c.add(rect(tx - 150, ty - 34, 300, 68, "surface-2", "line-strong", SECOND, rx=14))
    c.add(text(tx, ty - 10, "Body tissues: brain, eyes, muscles", 13, "middle", "fg", weight=700))
    c.add(text(tx, ty + 10, "O₂ leaves the blood, cells make CO₂", 12, "middle", "fg-muted"))
    # loops: oxygen-poor (info) and oxygen-rich (bad)
    c.add(path(f"M{hx - 70} {hy - 42} C{hx - 120} {hy - 90} {lx - 200} {ly + 40} {lx - 152} {ly + 16}", "info", None, 3, arrow_end=True))
    c.add(path(f"M{lx + 152} {ly + 16} C{lx + 200} {ly + 40} {hx + 120} {hy - 90} {hx + 70} {hy - 42}", "bad", None, 3, arrow_end=True))
    c.add(path(f"M{hx + 98} {hy + 10} C{hx + 230} {hy + 20} {tx + 230} {ty} {tx + 152} {ty}", "bad", None, 3, arrow_end=True))
    c.add(path(f"M{tx - 152} {ty} C{tx - 230} {ty} {hx - 230} {hy + 20} {hx - 98} {hy + 10}", "info", None, 3, arrow_end=True))
    c.add(text(hx + 136, hy - 70, "oxygen-rich", 12, "start", "bad", weight=700))
    c.add(text(hx + 236, hy + 80, "arteries", 12, "start", "bad", weight=700))
    c.add(text(hx - 136, hy - 70, "oxygen-poor", 12, "end", "info-fg", weight=700))
    c.add(text(hx - 236, hy + 80, "veins", 12, "end", "info-fg", weight=700))
    c.add(text(16, 460, "Haemoglobin in the red cells carries almost all the oxygen.", 12, "start", "fg-muted"))
    return c


@chart
def oxygen_saturation_curve() -> Canvas:
    c = Canvas("Haemoglobin is forgiving, then it isn't",
               "A qualitative sketch of how fully haemoglobin is loaded with oxygen against cabin altitude. Near sea level it stays almost fully "
               "loaded, so 5,000 or 8,000 ft make little difference to the oxygen the blood carries. Somewhere above about 10,000 ft its grip weakens "
               "and saturation falls away steeply: the symptoms of hypoxia begin, and the supplemental oxygen rules start at about that height.",
               height=380, prefix="osc")
    ch = Chart(c, (0, 25000), (0, 10), box=(80, 40, 610, 300), xlabel="Cabin altitude (ft)", ylabel="Haemoglobin loading (sketch)",
               xticks=[0, 5000, 10000, 15000, 20000, 25000], yticks=[], xfmt=lambda v: f"{int(v):,}")

    def sat(ft: float) -> float:
        return 9.4 - 0.25 * ft / 10000 - 6.2 / (1 + math.exp(-(ft - 16500) / 2600)) + 6.2 / (1 + math.exp(16500 / 2600))

    c.add(ch.band(0, 10000, "ok", 0.08))
    c.add(ch.band(10000, 25000, "bad", 0.06))
    c.add(ch.axes())
    c.add(text(ch.left - 8, ch.py(9.6) + 4, "full", 12, "end", "fg-muted"))
    c.add(text(ch.left - 8, ch.py(1) + 4, "low", 12, "end", "fg-muted"))
    pts = sample(sat, 0, 25000, 80)
    c.add(ch.curve(pts, "brand", 2.5))
    for ft, lab in ((0, "sea level"), (5000, "5,000"), (8000, "8,000")):
        c.add(ch.point(ft, sat(ft), "brand", 4.5))
    c.add(text(ch.px(4000), ch.py(sat(4000)) + 30, "flat: 5,000 or 8,000 ft makes", 12, "middle", "ok-fg", weight=600))
    c.add(text(ch.px(4000), ch.py(sat(4000)) + 46, "little difference to the blood", 12, "middle", "ok-fg", weight=600))
    c.add(ch.vline(10000, "bad", DASH))
    c.add(text(ch.px(10000) + 8, ch.py(9.9), "about 10,000 ft and above:", 12, "start", "bad", weight=700))
    c.add(text(ch.px(10000) + 8, ch.py(9.9) + 15, "the grip weakens", 12, "start", "bad", weight=700))
    c.add(ch.callout(19000, sat(19000), 24, -24, ["steep fall:", "hypoxia symptoms"], "bad", 12))
    c.add(text(345, 352, "Why the oxygen rules start at about 10,000 ft, and why night vision (more sensitive still)", 12, "middle", "fg-muted"))
    c.add(text(345, 368, "fades from about 5,000 ft.", 12, "middle", "fg-muted"))
    return c
