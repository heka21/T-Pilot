"""PHFC (human factors) diagrams. One @chart function per diagram; the hyphenated name is the slug.
Numbers and medical statements come from content/notes/PHFC/; change the note first, then the diagram."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, arrow, badge, callout, circle, ellipse, fmt, group, line, multiline,
                                num, path, plane_rear, plane_side, polygon, polyline, rect, sample, smooth_path, text)

SOFT = {"brand": "brand-soft", "ok": "ok-soft", "warn": "warn-soft", "bad": "bad-soft", "info": "info-soft", "sky": "sky-soft"}
FG = {"brand": "brand-fg", "ok": "ok-fg", "warn": "warn-fg", "bad": "bad-fg", "info": "info-fg", "sky": "sky-fg"}


def card(x: float, y: float, w: float, h: float, color: str = "brand", heading: str | None = None, lines: list[str] | None = None,
         size: float = 12, head_size: float = 14, align: str = "start", stroke: bool = True, pad: float = 12, leading: float = 1.35) -> str:
    """Rounded soft panel with an optional bold heading and body lines in the matching -fg colour."""
    out = rect(x, y, w, h, SOFT.get(color, "surface-2"), color if stroke and color in SOFT else ("line-strong" if stroke else None), SECOND, rx=10)
    tx = x + pad if align == "start" else x + w / 2
    ty = y + pad + head_size * 0.8
    fg = FG.get(color, "fg")
    if heading:
        out += text(tx, ty, heading, head_size, align, fg, weight=700)
        ty += head_size * 0.6 + size * 0.95
    elif lines:
        ty = y + pad + size * 0.8
    if lines:
        out += multiline(tx, ty, lines, size, align, fg, leading)
    return out


def pill(x: float, y: float, w: float, h: float, color: str, label: str, size: float = 13, weight: int = 700) -> str:
    return rect(x, y, w, h, SOFT[color], color, SECOND, rx=h / 2) + text(x + w / 2, y + h / 2 + size * 0.35, label, size, "middle", FG[color], weight=weight)


# ---------------------------------------------------------------- 2.1 basic health
@chart
def im_safe_checklist() -> Canvas:
    c = Canvas("IMSAFE: am I fit for this flight?", "Six tiles for the IMSAFE self-check before every flight: Illness, Medication, Stress, Alcohol, "
               "Fatigue, Eating and hydration, each with the question to ask. A no to any of them means do not fly; the pilot in command decides.",
               height=420, prefix="ims")
    tiles = [
        ("I", "Illness", ["Unwell or injured?", "A head cold means ear", "and sinus block on descent."]),
        ("M", "Medication", ["Any medication, even", "over the counter, cleared", "with a DAME?"]),
        ("S", "Stress", ["Anxious, upset or", "preoccupied? It narrows", "attention and decisions."]),
        ("A", "Alcohol", ["8 hours bottle to throttle", "is the minimum. A hangover", "still impairs."]),
        ("F", "Fatigue", ["Excessively tired? A tired", "pilot is a poor judge", "of their own fatigue."]),
        ("E", "Eating", ["Eaten and drunk water?", "Skipped meals mean low", "blood sugar."]),
    ]
    c.add(text(320, 30, "Before every flight, ask yourself six questions", 16, "middle", "fg", weight=700))
    W_, H_, gx, gy, x0, y0 = 196, 150, 10, 12, 16, 50
    for i, (letter, word, body) in enumerate(tiles):
        col_, row = i % 3, i // 3
        x, y = x0 + col_ * (W_ + gx), y0 + row * (H_ + gy)
        c.add(rect(x, y, W_, H_, "surface", "line-strong", SECOND, rx=10))
        c.add(circle(x + 30, y + 32, 20, "brand-soft", "brand", MAIN))
        c.add(text(x + 30, y + 40, letter, 22, "middle", "brand-fg", weight=800))
        c.add(text(x + 60, y + 38, word, 16, "start", "fg", weight=700))
        # tick box: the fun bit, every box must be ticked
        c.add(rect(x + W_ - 30, y + H_ - 30, 18, 18, "surface", "ok", SECOND, rx=4))
        c.add(path(f"M{x + W_ - 26} {y + H_ - 21} l4 5 l8 -11", "ok", None, MAIN))
        c.add(multiline(x + 14, y + 76, body, 12, "start", "fg-muted", 1.4))
    c.add(rect(16, 378, 608, 34, "bad-soft", "bad", SECOND, rx=8))
    c.add(text(320, 400, "Any box you cannot tick: do not fly. You, the pilot in command, decide.", 14, "middle", "bad-fg", weight=700))
    return c


# ---------------------------------------------------------------- 2.2 health and fitness
@chart
def alcohol_and_blood_levels_timeline() -> Canvas:
    c = Canvas("Alcohol leaves at one drink an hour", "Worked example from the note: the 6th standard drink is finished at 2300. The liver removes about one "
               "standard drink an hour and nothing speeds it up, so blood alcohol is not near zero until about 0500. The 8-hour rule makes 0700 the "
               "earliest legal time to fly, and the hangover can last well beyond that.", height=400, prefix="alc")
    ch = Chart(c, (22, 33), (0, 7), box=(70, 60, 610, 300), xlabel="Time of day", ylabel="Standard drinks still in the body",
               xticks=[23, 25, 27, 29, 31, 33], yticks=[0, 1, 2, 3, 4, 5, 6], xfmt=lambda v: f"{int(v) % 24:02d}00")
    c.add(ch.band(22, 23, "warn", 0.12))
    c.add(ch.band(29, 33, "bad", 0.08))
    c.add(ch.axes())
    c.add(text(ch.px(22.5), ch.py(3.5), "drinking", 12, "middle", "warn-fg", weight=600, rotate=-90))
    pts = [(23, 6), (29, 0)]
    c.add(ch.area(pts, "brand", 0.10))
    c.add(ch.curve(pts, "brand", MAIN, smooth=False))
    c.add(ch.curve([(29, 0), (33, 0)], "brand", SECOND, smooth=False, dash=DASH))
    c.add(ch.point(23, 6, "brand", 5))
    c.add(text(ch.px(23) + 10, ch.py(6) - 8, "6th drink finished at 2300", 13, "start", "brand", weight=600))
    c.add(ch.callout(26, 3, 50, -40, ["−1 drink per hour, fixed:", "coffee, showers, exercise", "and sleep do not speed it up"], "fg", 12))
    # 0500 and 0700 markers
    c.add(ch.vline(29, "brand", DASH))
    c.add(ch.point(29, 0, "brand", 5))
    c.add(text(ch.px(29) + 8, ch.py(0.45), "0500: about zero", 12, "start", "brand", weight=600))
    c.add(ch.vline(31, "bad", None))
    c.add(text(ch.px(31) + 6, ch.py(3.7), "0700", 13, "start", "bad", weight=700, cls="num"))
    c.add(multiline(ch.px(31) + 6, ch.py(3.7) + 18, ["8 hours after the", "last drink: the", "earliest legal time"], 12, "start", "bad"))
    c.add(text(ch.px(32), ch.py(6.5), "hangover:", 12, "middle", "bad-fg", weight=600))
    c.add(text(ch.px(32), ch.py(6.5) + 15, "can last well", 12, "middle", "bad-fg"))
    c.add(text(ch.px(32), ch.py(6.5) + 30, "beyond 0700", 12, "middle", "bad-fg"))
    # the 8-hour bracket along the top
    y8 = 46
    c.add(line(ch.px(23), y8, ch.px(31), y8, "bad", SECOND))
    c.add(line(ch.px(23), y8 - 6, ch.px(23), y8 + 6, "bad", SECOND))
    c.add(line(ch.px(31), y8 - 6, ch.px(31), y8 + 6, "bad", SECOND))
    c.add(rect(ch.px(27) - 34, y8 - 10, 68, 20, "surface", None))
    c.add(text(ch.px(27), y8 + 5, "8 hours", 13, "middle", "bad", weight=700, cls="num"))
    c.add(text(320, 370, "The rules (CASR 91.520, Part 99): no alcohol within 8 hours; blood alcohol limit 0.02 g per 100 mL.", 12, "middle", "fg-muted"))
    c.add(text(320, 388, "Eight hours is a minimum, not a guarantee: after heavy drinking allow 24 hours or more.", 12, "middle", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.3 hyperventilation
@chart
def hyperventilation_vs_hypoxia() -> Canvas:
    c = Canvas("Hyperventilation or hypoxia?", "Side-by-side comparison. Hyperventilation is too little carbon dioxide from over-breathing, can happen at any "
               "altitude, comes on fairly rapidly with anxiety and brings tingling and muscle spasm. Hypoxia is too little oxygen reaching the tissues, "
               "mainly at altitude, is gradual and insidious and brings euphoria, poor judgement and cyanosis. Both share dizziness, tingling and visual "
               "disturbance. If unsure above about 10,000 feet with oxygen available, treat as hypoxia first.", height=470, prefix="hvh")
    L, R, w = 16, 332, 292
    # headings
    c.add(card(L, 14, w, 112, "brand", "Hyperventilation", ["Breathing faster or deeper than needed", "blows off CO2: blood vessels in the brain",
                                                           "narrow, the brain runs short of oxygen", "even though oxygen is breathed in"], 12, 16))
    c.add(card(R, 14, w, 112, "info", "Hypoxia", ["Too little oxygen reaches the tissues:", "low oxygen pressure at altitude,",
                                                 "or CO, alcohol, blood loss"], 12, 16))
    rows = [
        ("Where", ["Any altitude,", "even on the ground"], ["Mainly at altitude"]),
        ("Onset", ["Fairly rapid, often", "with anxiety"], ["Gradual and insidious,", "often unnoticed"]),
        ("Tell-tale signs", ["Tingling, muscle spasm,", "rapid breathing"], ["Euphoria, poor judgement,", "cyanosis (blue lips)"]),
    ]
    y = 140
    for label, a, b in rows:
        c.add(text(320, y + 4, label, 12, "middle", "fg-muted", weight=700))
        c.add(multiline(L + 12, y + 4, a, 13, "start", "fg", 1.3))
        c.add(multiline(R + w - 12, y + 4, b, 13, "end", "fg", 1.3))
        c.add(line(L, y + 30, R + w, y + 30, "line", THIN))
        y += 44
    # shared band
    y = 276
    c.add(rect(L, y, R + w - L, 40, "surface-2", "line-strong", SECOND, rx=8))
    c.add(text(320, y + 17, "Shared by both", 12, "middle", "fg-muted", weight=700))
    c.add(text(320, y + 33, "dizziness · tingling · visual disturbance (blurred or tunnel vision)", 13, "middle", "fg", weight=600))
    # fixes
    y = 330
    c.add(card(L, y, w, 70, "brand", "Fix", ["Slow the breathing: one breath", "every 4 to 5 s. Talk out loud."], 12, 14))
    c.add(card(R, y, w, 70, "info", "Fix", ["Oxygen on, or descend", "below 10,000 ft."], 12, 14))
    # decision rule
    y = 412
    c.add(rect(L, y, R + w - L, 46, "warn-soft", "warn", SECOND, rx=8))
    c.add(text(320, y + 19, "Not sure, above about 10,000 ft, oxygen on board? Treat it as hypoxia first:", 13, "middle", "warn-fg", weight=700))
    c.add(text(320, y + 37, "oxygen does a hyperventilating pilot no harm; wasting time of useful consciousness does.", 12, "middle", "warn-fg"))
    return c


# ---------------------------------------------------------------- 2.4 atmospheric pressure changes
def isa_pressure(ft: float) -> float:
    return 1013.25 * (1 - 6.8756e-6 * ft) ** 5.2559


@chart
def boyles_law_gas_expansion() -> Canvas:
    c = Canvas("Trapped gas expands as you climb", "Boyle's law: trapped gas volume against altitude. About 1.5 times the sea-level volume at 10,000 feet, about "
               "2 times at 18,000 feet where the pressure is half, about 2.7 times at 25,000 feet. Gut and teeth hurt on the climb as gas expands; ears "
               "and sinuses hurt on the descent when air cannot get back in.", height=400, prefix="bgl")
    ch = Chart(c, (0, 27000), (0.8, 3.0), box=(70, 40, 400, 330), xlabel="Altitude (ft)", ylabel="Gas volume × sea-level volume",
               xticks=[0, 10000, 18000, 25000], yticks=[1, 1.5, 2, 2.5], xfmt=lambda v: f"{int(v):,}", yfmt=lambda v: "×" + fmt(v))
    c.add(ch.axes())
    vol = lambda h: 1013.25 / isa_pressure(h)
    c.add(ch.area(sample(vol, 0, 26000, 60), "brand", 0.08, baseline=0.8))
    c.add(ch.curve(sample(vol, 0, 26000, 60), "brand", MAIN))
    for h, lab in ((0, "×1"), (10000, "×1.5"), (18000, "×2"), (25000, "×2.7")):
        if h:
            c.add(ch.guide(h, vol(h), "fg-faint"))
        c.add(ch.point(h, vol(h), "brand", 5))
        # a gas bubble whose area grows with the volume, sitting above the point
        X, Y = ch.pt(h, vol(h))
        r = 8 * math.sqrt(vol(h))
        bx, by = X - r - 10, Y - r - 14
        if h == 0:
            bx, by = X + 26, Y - r - 18
        c.add(circle(bx, by, r, "brand-soft", "brand", SECOND))
        c.add(num(bx, by - r - 6, lab, 13, "middle", "brand", weight=700))
    c.add(text(ch.px(18000) + 8, ch.py(1.88), "half the", 11, "start", "fg-muted"))
    c.add(text(ch.px(18000) + 8, ch.py(1.88) + 13, "pressure", 11, "start", "fg-muted"))
    c.add(text(ch.px(800), ch.py(2.85), "100 mL of gut gas at sea level", 12, "start", "fg", weight=600))
    c.add(text(ch.px(800), ch.py(2.85) + 16, "is about 200 mL at 18,000 ft", 12, "start", "fg"))
    # where it hurts
    x0, w = 424, 200
    c.add(card(x0, 40, w, 136, "warn", "Climb: gas expands", ["Gut: bloating and pain", "Teeth: under a poor filling", "Ears vent easily: a pop",
                                                             "Fix: stop climbing or", "descend, release the gas"], 12, 14))
    c.add(card(x0, 190, w, 140, "bad", "Descent: gas shrinks", ["Air must get back in.", "Ears and sinuses hurt if", "blocked by a cold or hay fever",
                                                               "Fix: climb back, equalise,", "descend more slowly"], 12, 14))
    return c


@chart
def ear_pressure_equalisation() -> Canvas:
    c = Canvas("Why ears block on descent, not on climb", "Two cross-sections of the ear. On the climb the air in the middle ear expands and vents easily "
               "down the eustachian tube to the throat. On the descent outside pressure pushes the eardrum in and air must get back up the tube, whose "
               "soft end stays closed; swollen by a cold it may not open at all: ear block. Fix: climb back, equalise, descend more slowly.",
               height=400, prefix="epe")

    def ear(ox: float, climb: bool) -> str:
        parts = []
        col_ = "warn" if climb else "bad"
        parts.append(rect(ox + 10, 70, 290, 200, "surface-2", None, rx=14))
        # ear canal (open to the outside on the left)
        parts.append(rect(ox + 10, 128, 92, 40, "sky-soft", None))
        parts.append(line(ox + 10, 128, ox + 102, 128, "fg", MAIN))
        parts.append(line(ox + 10, 168, ox + 102, 168, "fg", MAIN))
        # middle ear cavity
        parts.append(rect(ox + 112, 100, 110, 96, "sky-soft", "fg", MAIN, rx=16))
        # eustachian tube down to the throat
        tube = f"M{ox + 190} 196 C{ox + 200} 220 {ox + 222} 236 {ox + 250} 252"
        parts.append(path(tube, "fg", None, 14))
        parts.append(path(tube, "sky-soft", None, 9))
        parts.append(text(ox + 262, 262, "throat", 12, "start", "fg-muted"))
        parts.append(text(ox + 150, 214, "eustachian", 12, "end", "fg-muted"))
        parts.append(text(ox + 150, 228, "tube", 12, "end", "fg-muted"))
        # eardrum: bulges out on the climb, in on the descent
        bulge = -16 if climb else 16
        parts.append(rect(ox + 102, 120, 10, 56, "sky-soft", None))
        parts.append(path(f"M{ox + 107} 122 Q{ox + 107 + bulge} 148 {ox + 107} 174", col_, None, 3))
        parts.append(text(ox + 107, 112, "eardrum", 12, "middle", col_, weight=600))
        parts.append(text(ox + 167, 144, "middle ear", 12, "middle", "fg-muted"))
        parts.append(text(ox + 167, 158, "(air)", 12, "middle", "fg-muted"))
        parts.append(text(ox + 56, 186, "ear canal", 12, "middle", "fg-muted"))
        if climb:
            parts.append(arrow(ox + 224, 214, ox + 260, 240, "warn", MAIN))
            parts.append(text(ox + 155, 254, "air vents out easily", 12, "middle", "warn-fg", weight=600))
        else:
            parts.append(arrow(ox + 24, 148, ox + 86, 148, "bad", MAIN))
            parts.append(line(ox + 240, 238, ox + 258, 256, "bad", 3))
            parts.append(line(ox + 258, 238, ox + 240, 256, "bad", 3))
            parts.append(text(ox + 155, 254, "air can't get back in", 12, "middle", "bad-fg", weight=600))
        return "".join(parts)

    c.add(text(165, 34, "Climb: outside pressure falls", 15, "middle", "warn-fg", weight=700))
    c.add(text(165, 54, "middle-ear air expands", 12, "middle", "fg-muted"))
    c.add(ear(10, True))
    c.add(text(165, 290, "A \"pop\" every so often.", 13, "middle", "fg", weight=600))
    c.add(text(165, 308, "Rarely a problem.", 13, "middle", "fg"))
    c.add(text(485, 34, "Descent: outside pressure rises", 15, "middle", "bad-fg", weight=700))
    c.add(text(485, 54, "eardrum pushed in", 12, "middle", "fg-muted"))
    c.add(ear(330, False))
    c.add(text(485, 290, "Tube swollen by a cold: ear block,", 13, "middle", "bad-fg", weight=600))
    c.add(text(485, 308, "pain, poor hearing, burst eardrum", 13, "middle", "bad-fg"))
    c.add(rect(16, 332, 608, 54, "ok-soft", "ok", SECOND, rx=8))
    c.add(text(320, 354, "Equalise often on descent: swallow, yawn, Valsalva (pinch nose, gently blow).", 13, "middle", "ok-fg", weight=700))
    c.add(text(320, 374, "If it blocks: climb back to where it was comfortable, equalise, then descend more slowly.", 12, "middle", "ok-fg"))
    return c


# ---------------------------------------------------------------- 2.6 hearing protection
@chart
def noise_levels_and_hearing_damage() -> Canvas:
    c = Canvas("How long before noise damages hearing?", "Safe daily exposure time against sound level, from the guide in the note: 85 dB(A) averaged over "
               "8 hours risks permanent damage, and each 3 dB more halves the safe time: about 4 hours at 88, 2 at 91, 1 at 94, 30 minutes at 97 and "
               "15 minutes at 100 dB. A piston single's cabin is typically 85 to 100 dB. A headset that lowers the level at the ear buys time.",
               height=420, prefix="nhd")
    lg = lambda m: math.log2(m)
    ticks = [15, 30, 60, 120, 240, 480]
    labels = {15: "15 min", 30: "30 min", 60: "1 h", 120: "2 h", 240: "4 h", 480: "8 h"}
    ch = Chart(c, (82, 103), (lg(10), lg(640)), box=(80, 56, 600, 330), xlabel="Sound level at the ear, dB(A)", ylabel="Safe exposure per day",
               xticks=[85, 88, 91, 94, 97, 100], yticks=[lg(t) for t in ticks], yfmt=lambda v: labels[round(2 ** v)])
    c.add(ch.band(85, 100, "warn", 0.10))
    c.add(text(ch.px(92.5), 44, "typical piston single cabin: 85 to 100 dB", 12, "middle", "warn-fg", weight=600))
    c.add(line(ch.px(85), 50, ch.px(100), 50, "warn", SECOND))
    c.add(ch.axes())
    safe = lambda db: 480 / 2 ** ((db - 85) / 3)
    c.add(ch.curve([(83, lg(safe(83))), (102, lg(safe(102)))], "brand", MAIN, smooth=False))
    for db in (85, 88, 91, 94, 97, 100):
        c.add(ch.point(db, lg(safe(db)), "brand" if db < 100 else "bad", 4.5))
    c.add(ch.callout(85, lg(480), 40, -6, ["85 dB for 8 hours:", "the damage threshold"], "brand", 12))
    X, Y = ch.pt(100, lg(15))
    c.add(text(X - 12, Y + 22, "100 dB: about 15 min a day", 12, "end", "bad", weight=600))
    c.add(ch.callout(94, lg(60), 40, -90, ["each +3 dB", "halves the time"], "fg", 12))
    # a better headset lowers the level at the ear: the same flight moves left, to a much longer safe time
    X1, Y1 = ch.pt(97, lg(safe(97)))
    X2, Y2 = ch.pt(88, lg(safe(88)))
    c.add(line(X1 - 10, Y1 + 18, X2 + 4, Y2 + 22, "ok", MAIN, arrow_end=True))
    c.add(text(ch.px(85.6), ch.py(lg(40)), "A good headset seal,", 12, "start", "ok-fg", weight=600))
    c.add(text(ch.px(85.6), ch.py(lg(40)) + 15, "ANR or earplugs lower the", 12, "start", "ok-fg"))
    c.add(text(ch.px(85.6), ch.py(lg(40)) + 30, "level at the ear: more time", 12, "start", "ok-fg"))
    c.add(text(320, 392, "Noise-induced hearing loss is permanent, painless and cumulative.", 12, "middle", "fg-muted"))
    c.add(text(320, 410, "Turning the radio up adds sound energy at the eardrum; a better seal lets you keep it low.", 12, "middle", "fg-muted"))
    return c


@chart
def visual_illusions_panels() -> Canvas:
    c = Canvas("Landing illusions: what you think, what you do", "Six small panels. Black hole: dark ground before a lit runway makes you feel high, so "
               "you fly too low and land short. A narrow or long runway looks high: too low. A wide runway looks low: too high. An upsloping runway "
               "looks high: too low. A downsloping runway looks low: too high. A sloping cloud top is a false horizon: you bank to level with it. "
               "The fix is the PAPI or a planned descent profile, not the look of the lights.", height=560, prefix="vil")
    PW, PH = 196, 222

    def frame(i: int) -> tuple[float, float]:
        return 16 + (i % 3) * (PW + 10), 16 + (i // 3) * (PH + 12)

    def side(x: float, y: float, slope: float = 0, dark: bool = False, low: bool = True) -> str:
        """Side view: ground, a runway (sloping by `slope` px over its length), the correct path (dashed) and the flown path."""
        out = []
        gy = y + 150
        rx0, rx1 = x + 120, x + 186
        if dark:
            out.append(rect(x + 8, gy, rx0 - x - 8, 12, "fg-muted", None))
        out.append(line(x + 8, gy, rx0, gy, "fg-muted", SECOND))
        out.append(line(rx0, gy, rx1, gy - slope, "fg", 4))
        if dark:
            for k in range(4):
                out.append(circle(rx0 + 8 + k * 16, gy - slope * (8 + k * 16) / 66 - 6, 2.5, "warn", None))
        # correct approach to the threshold, dashed
        out.append(line(x + 20, gy - 70, rx0, gy, "ok", SECOND, dash=DASH))
        if low:
            out.append(path(f"M{x + 20} {gy - 70} Q{x + 44} {gy - 8} {rx0 - 26} {gy}", "bad", None, MAIN))
            out.append(circle(rx0 - 26, gy, 3.5, "bad", None))
        else:
            out.append(path(f"M{x + 20} {gy - 70} Q{x + 104} {gy - 68} {rx0 + 30} {gy - slope * 30 / 66}", "bad", None, MAIN))
            out.append(circle(rx0 + 30, gy - slope * 30 / 66, 3.5, "bad", None))
        return "".join(out)

    def view(cx: float, cy: float, near: float, far: float, depth: float, tilt: float = 0) -> str:
        """Pilot's-eye runway: a trapezoid near width, far width and apparent depth."""
        pts = [(cx - near / 2, cy), (cx + near / 2, cy), (cx + far / 2, cy - depth - tilt), (cx - far / 2, cy - depth - tilt)]
        return polygon(pts, "fg-muted", "fg", THIN) + line(cx, cy - 3, cx, cy - depth - tilt + 3, "surface", 1.5, dash="5 4")

    panels = [
        ("Black hole", "dark terrain or water, lit runway", "feels high", "too low, lands short", dict(dark=True, low=True), None),
        ("Narrow or long runway", "looks long and steep", "feels high", "too low", dict(low=True), (14, 6, 46)),
        ("Wide runway", "looks short and flat", "feels low", "too high", dict(low=False), (70, 26, 22)),
        ("Upsloping runway", "rises away from you", "feels high", "too low", dict(slope=16, low=True), None),
        ("Downsloping runway", "falls away from you", "feels low", "too high", dict(slope=-12, low=False), None),
    ]
    for i, (head, sub, feel, result, kw, trap) in enumerate(panels):
        x, y = frame(i)
        c.add(rect(x, y, PW, PH, "surface", "line-strong", SECOND, rx=10))
        c.add(text(x + 12, y + 22, head, 14, "start", "fg", weight=700))
        c.add(text(x + 12, y + 39, sub, 11, "start", "fg-muted"))
        if trap:
            c.add(view(x + 160, y + 100, *trap))
        c.add(side(x, y, **kw))
        c.add(text(x + 12, y + 186, feel, 12, "start", "fg-muted", weight=600))
        c.add(text(x + 12, y + 204, "→ " + result, 13, "start", "bad", weight=700))
    # false horizon: rear view, aircraft banked to match a sloping cloud top
    x, y = frame(5)
    c.add(rect(x, y, PW, PH, "surface", "line-strong", SECOND, rx=10))
    c.add(text(x + 12, y + 22, "False horizon", 14, "start", "fg", weight=700))
    c.add(text(x + 12, y + 39, "sloping cloud tops or terrain", 11, "start", "fg-muted"))
    c.add(path(f"M{x + 10} {y + 150} Q{x + 50} {y + 136} {x + 80} {y + 140} T{x + 186} {y + 106} L{x + 186} {y + 160} L{x + 10} {y + 160} Z", None, "surface-2"))
    c.add(path(f"M{x + 10} {y + 150} Q{x + 50} {y + 136} {x + 80} {y + 140} T{x + 186} {y + 106}", "fg-muted", None, SECOND))
    c.add(line(x + 10, y + 70, x + 186, y + 70, "ok", SECOND, dash=DASH))
    c.add(text(x + 184, y + 64, "true horizon", 11, "end", "ok-fg"))
    c.add(plane_rear(x + 98, y + 98, 0.9, bank=14, color="bad"))
    c.add(text(x + 150, y + 150, "cloud top", 11, "middle", "fg-muted"))
    c.add(text(x + 12, y + 186, "feels level with the cloud", 12, "start", "fg-muted", weight=600))
    c.add(text(x + 12, y + 204, "→ banked to match it", 13, "start", "bad", weight=700))
    # key and fix
    y = 492
    c.add(line(26, y, 50, y, "ok", SECOND, dash=DASH))
    c.add(text(56, y + 4, "correct approach", 12, "start", "fg-muted"))
    c.add(line(190, y, 214, y, "bad", MAIN))
    c.add(text(220, y + 4, "the path the illusion leads you to fly", 12, "start", "fg-muted"))
    c.add(rect(16, 508, 608, 40, "ok-soft", "ok", SECOND, rx=8))
    c.add(text(320, 533, "Fix: use the PAPI or a planned descent profile, not the look of the lights.", 13, "middle", "ok-fg", weight=700))
    return c


@chart
def vestibular_illusions() -> Canvas:
    c = Canvas("When your balance senses lie", "Four illusions. The leans: after a slow, unnoticed roll and a quick correction you feel banked the "
               "opposite way when level. Somatogravic: forward acceleration on a dark take-off feels like a nose-up pitch, and pushing forward flies "
               "into the ground. Graveyard spiral: the canals adapt to a sustained turn, the wings feel level, and pulling back tightens the spiral. "
               "Autokinetic: a single light stared at in darkness appears to move. In every case, believe the instruments.", height=526, prefix="vsi")
    PW, PH = 298, 204

    def box(i: int, head: str) -> tuple[float, float]:
        x, y = 16 + (i % 2) * (PW + 12), 14 + (i // 2) * (PH + 12)
        c.add(rect(x, y, PW, PH, "surface", "line-strong", SECOND, rx=10))
        c.add(text(x + 14, y + 24, head, 15, "start", "fg", weight=700))
        return x, y

    def foot(x: float, y: float, feel: str, danger: str) -> None:
        c.add(text(x + 14, y + PH - 32, "feels: " + feel, 12, "start", "info-fg", weight=600))
        c.add(text(x + 14, y + PH - 14, "danger: " + danger, 12, "start", "bad", weight=600))

    # 1 the leans: real attitude level (fg), felt attitude banked (info, dashed)
    x, y = box(0, "The leans")
    c.add(text(x + 14, y + 42, "slow roll, then a quick correction", 11, "start", "fg-muted"))
    c.add(line(x + 20, y + 112, x + 278, y + 112, "line-strong", THIN, dash=DASH))
    c.add(plane_rear(x + 82, y + 104, 1.0, bank=0))
    c.add(text(x + 82, y + 146, "actual", 12, "middle", "fg", weight=600))
    c.add(plane_rear(x + 216, y + 104, 1.0, bank=-18, color="info"))
    c.add(text(x + 216, y + 146, "felt", 12, "middle", "info-fg", weight=600))
    foot(x, y, "banked the opposite way", "leaning into a bank, a spiral")

    # 2 somatogravic: accelerating, level climb attitude shallow; felt as steep nose-up
    x, y = box(1, "Somatogravic (acceleration)")
    c.add(text(x + 14, y + 42, "dark take-off or go-around", 11, "start", "fg-muted"))
    gx = y + 126
    c.add(line(x + 14, gx, x + 284, gx, "fg-muted", SECOND))
    c.add(plane_side(x + 100, gx - 23, 0.85, pitch=8))           # CG 21 units ahead of mid-length
    c.add(text(x + 82, gx + 16, "actual", 12, "middle", "fg", weight=600))
    c.add(plane_side(x + 236, gx - 40, 0.85, pitch=30, color="info", gear=False))
    c.add(text(x + 220, gx + 16, "felt", 12, "middle", "info-fg", weight=600))
    c.add(arrow(x + 40, y + 60, x + 110, y + 60, "fg-muted", SECOND))
    c.add(text(x + 118, y + 64, "accelerating", 11, "start", "fg-muted"))
    foot(x, y, "a steep nose-up pitch", "pushing forward into the ground")

    # 3 graveyard spiral
    x, y = box(2, "Graveyard spiral")
    c.add(text(x + 14, y + 42, "inner ear adapts to a sustained turn", 11, "start", "fg-muted"))
    cx, cy = x + 92, y + 58
    pts = []
    for k in range(121):
        t = k / 120
        a = t * 3 * 2 * math.pi
        r = 52 * (1 - 0.45 * t)
        pts.append((cx + r * math.sin(a), cy + t * 86 + r * 0.28 * math.cos(a)))
    c.add(path(smooth_path(pts), "bad", None, SECOND, arrow_end=True))
    c.add(plane_rear(x + 220, y + 96, 0.9, bank=0, color="info"))
    c.add(text(x + 220, y + 130, "wings feel level", 11, "middle", "info-fg"))
    foot(x, y, "wings level; pulls back", "the pull tightens the spiral")

    # 4 autokinetic
    x, y = box(3, "Autokinetic")
    c.add(text(x + 14, y + 42, "staring at a single light in darkness", 11, "start", "fg-muted"))
    c.add(rect(x + 30, y + 56, PW - 60, 92, "surface-2", None, rx=8))
    c.add(circle(x + 150, y + 102, 4, "warn", None))
    c.add(path(f"M{x + 150} {y + 102} q20 -16 36 -4 t30 -18", "warn", None, SECOND, dash=DASH))
    c.add(circle(x + 216, y + 80, 3, "warn", None, opacity=0.5))
    c.add(text(x + 150, y + 136, "a star or a lone light", 11, "middle", "fg-muted"))
    foot(x, y, "the light drifts and moves", "chasing a star as if an aircraft")

    # trust the instruments
    y = 448
    c.add(rect(16, y, 608, 66, "ok-soft", "ok", SECOND, rx=10))
    # small attitude indicator
    ax, ay = 56, y + 30
    c.add(circle(ax, ay, 22, "sky-soft", "fg", SECOND))
    c.add(path(f"M{ax - 22} {ay} A22 22 0 0 0 {ax + 22} {ay} Z", None, "surface-2"))
    c.add(line(ax - 22, ay, ax + 22, ay, "fg", SECOND))
    c.add(line(ax - 12, ay, ax - 4, ay, "warn", 3))
    c.add(line(ax + 4, ay, ax + 12, ay, "warn", 3))
    c.add(text(92, y + 22, "Believe the instruments.", 14, "start", "ok-fg", weight=700))
    c.add(text(92, y + 40, "The attitude indicator will disagree with your senses, and the senses", 12, "start", "ok-fg"))
    c.add(text(92, y + 56, "feel completely convincing. Keep head movements small; don't stare at single lights.", 12, "start", "ok-fg"))
    return c


@chart
def motion_sickness_sensory_conflict() -> Canvas:
    c = Canvas("Why motion sickness happens", "Reading a chart in turbulence: the eyes report that you are still, the inner ear reports that you are moving. "
               "The brain receives two different pictures of motion and responds with sickness. Remedies: fresh air, eyes outside on the horizon, head "
               "still, take the controls. Pilots should not take anti-motion-sickness medication.", height=420, prefix="msc")
    c.add(text(16, 34, "Reading a chart in turbulence: two senses, two different stories", 15, "start", "fg", weight=700))
    # eye
    ex, ey = 90, 92
    c.add(path(f"M{ex - 40} {ey} Q{ex} {ey - 30} {ex + 40} {ey} Q{ex} {ey + 30} {ex - 40} {ey} Z", "fg", "surface", MAIN))
    c.add(circle(ex, ey, 12, "info-soft", "info", MAIN))
    c.add(circle(ex, ey, 5, "fg", None))
    c.add(card(150, 60, 190, 64, "info", "Eyes: \"still\"", ["head down on a chart,", "cabin moving with you"], 12, 14))
    # inner ear (semicircular canals)
    ix, iy = 90, 222
    for a in (0, 60, 120):
        c.add(ellipse(ix, iy - 8, 26, 12, None, "warn", MAIN, transform=f"rotate({a} {ix} {iy - 8})"))
    c.add(path(f"M{ix - 6} {iy + 6} q-14 20 4 26 q18 4 14 -14", "warn", None, MAIN))
    c.add(card(150, 192, 190, 64, "warn", "Inner ear: \"moving\"", ["turbulence, turns,", "accelerations"], 12, 14))
    # brain
    bx, by = 420, 160
    c.add(ellipse(bx, by, 44, 34, "bad-soft", "bad", MAIN))
    c.add(path(f"M{bx - 26} {by - 8} q10 -12 20 0 q10 12 20 0 M{bx - 30} {by + 10} q12 -10 24 0 q12 10 24 0", "bad", None, SECOND))
    c.add(arrow(342, 92, 386, 142, "info", MAIN))
    c.add(arrow(342, 224, 386, 180, "warn", MAIN))
    c.add(text(bx, by + 56, "Conflict", 15, "middle", "bad", weight=700))
    c.add(text(bx, by + 74, "two pictures of motion", 12, "middle", "bad-fg"))
    c.add(arrow(470, 160, 500, 160, "bad", MAIN))
    c.add(multiline(508, 128, ["unease, yawning,", "pallor, cold sweat,", "nausea, then", "vomiting"], 12, "start", "bad-fg", 1.35))
    c.add(text(508, 204, "performance falls", 11, "start", "fg-muted"))
    c.add(text(508, 218, "well before vomiting", 11, "start", "fg-muted"))
    # remedies
    y = 286
    c.add(text(16, y, "Make the senses agree:", 14, "start", "ok-fg", weight=700))
    rem = [("Fresh air", "vents open, keep cool"), ("Eyes outside", "on the horizon"), ("Head still", "move the eyes"),
           ("Take the controls", "you anticipate it")]
    for i, (h, s) in enumerate(rem):
        x = 16 + i * 154
        c.add(card(x, y + 12, 146, 58, "ok", h, [s], 11, 13))
    c.add(rect(16, 366, 608, 46, "bad-soft", "bad", SECOND, rx=8))
    c.add(text(320, 385, "Pilots: no anti-motion-sickness medication.", 13, "middle", "bad-fg", weight=700))
    c.add(text(320, 402, "Most cause drowsiness, blurred vision and slowed reactions. Passengers may take them.", 12, "middle", "bad-fg"))
    return c


@chart
def g_effects_on_vision() -> Canvas:
    c = Canvas("What rising g does to your vision", "The pilot's view at each stage. Negative g, about minus 2 to minus 3 g: blood to the head, red-out, "
               "uncomfortable to painful. Plus 1 g: normal. Plus 2 to 3 g: heaviness, grey-out may begin. Plus 3 to 4 g: grey-out and tunnel vision. "
               "Plus 4 to 5 g: black-out, still conscious. Plus 5 to 6 g and above: G-LOC, incapacitated for 15 to 30 seconds or more. Vision goes "
               "before consciousness. Approximate values for a relaxed, unprotected person.", height=384, prefix="gev")
    cols = [  # g label, colour, title, body, view
        ("−2 to −3 g", "bad", "Red-out", ["blood to the", "head: fullness,", "headache"], "red"),
        ("+1 g", "ok", "Normal", ["straight and", "level flight"], "normal"),
        ("+2 to +3 g", "warn", "Heaviness", ["hard to lift", "arms and head;", "grey-out may begin"], "normal"),
        ("+3 to +4 g", "warn", "Grey-out", ["colour fades,", "tunnel vision"], "tunnel"),
        ("+4 to +5 g", "bad", "Black-out", ["no vision but", "still conscious"], "black"),
        ("+5 to +6 g", "bad", "G-LOC", ["unconscious;", "15 to 30 s or", "more out of action"], "gloc"),
    ]
    xs = [66, 182, 280, 378, 476, 574]

    def window(cx: float, cy: float, kind: str) -> str:
        r = 36
        h = math.sqrt(r * r - 36)
        out = [circle(cx, cy, r, "sky-soft", None), path(f"M{fmt(cx - h)} {cy + 6} A{r} {r} 0 0 0 {fmt(cx + h)} {cy + 6} Z", None, "ok-soft"),
               line(cx - h, cy + 6, cx + h, cy + 6, "fg-muted", SECOND)]
        if kind == "red":
            out.append(circle(cx, cy, r, "bad", None, fill_opacity=0.5))
        elif kind == "tunnel":
            out.append(circle(cx, cy, r, "fg-muted", None, fill_opacity=0.45))
            out.append(path(f"M{cx - r} {cy} A{r} {r} 0 1 0 {cx + r} {cy} A{r} {r} 0 1 0 {cx - r} {cy} Z "
                            f"M{cx - 14} {cy} A14 14 0 1 1 {cx + 14} {cy} A14 14 0 1 1 {cx - 14} {cy} Z", None, "fg-muted"))
        elif kind in ("black", "gloc"):
            out.append(circle(cx, cy, r, "fg-muted", None))
        out.append(circle(cx, cy, r, None, "fg", MAIN))
        if kind == "gloc":
            out.append(text(cx, cy + 7, "Zz", 20, "middle", "surface", weight=800))
        return "".join(out)

    c.add(text(xs[0], 26, "Negative g", 13, "middle", "fg-muted", weight=700))
    c.add(text(xs[0], 42, "lifted out of the seat", 11, "middle", "fg-muted"))
    c.add(text((xs[1] + xs[5]) / 2, 26, "Positive g: pressed into the seat, blood drains to the legs", 13, "middle", "fg-muted", weight=700))
    c.add(line(xs[1] - 30, 42, xs[5] + 30, 42, "fg-muted", SECOND, arrow_end=True))
    c.add(line(124, 20, 124, 290, "line-strong", THIN, dash=DASH))
    for x, (g, col_, title, body, kind) in zip(xs, cols):
        c.add(window(x, 98, kind))
        c.add(text(x, 158, title, 14, "middle", FG[col_], weight=700))
        c.add(multiline(x, 177, body, 11, "middle", FG[col_], 1.3))
        c.add(rect(x - 46, 226, 92, 26, SOFT[col_], col_, SECOND, rx=13))
        c.add(num(x, 243, g, 11 if len(g) > 10 else 12, "middle", FG[col_], weight=700))
    c.add(text(xs[2], 272, "60° level turn = 2 g", 11, "middle", "fg-muted", cls="num"))
    c.add(text(xs[5], 270, "and above;", 11, "middle", "bad-fg"))
    c.add(text(xs[5], 284, "fatal near the ground", 11, "middle", "bad-fg"))
    c.add(rect(16, 300, 608, 52, "brand-soft", "brand", SECOND, rx=8))
    c.add(text(320, 322, "Vision goes before consciousness.", 14, "middle", "brand-fg", weight=700))
    c.add(text(320, 341, "Grey-out is not a warning to keep pulling: ease off immediately. Apply g gradually.", 12, "middle", "brand-fg"))
    c.add(text(624, 372, "approximate values for a relaxed, unprotected person", 11, "end", "fg-faint"))
    return c


@chart
def carbon_monoxide_cabin_heater() -> Canvas:
    c = Canvas("How carbon monoxide gets into the cabin", "Cutaway of a light aeroplane's nose, engine on the right. Cabin heat is fresh air warmed in "
               "a muff around the exhaust. A crack in the exhaust inside the muff puts exhaust gas, with its colourless, odourless carbon monoxide, "
               "straight into the cabin through the heater outlet at the pilot's feet. First actions: cabin heat off, fresh-air vents open, oxygen if "
               "carried, land as soon as possible.", height=450, prefix="coh")
    c.style(".coh-flow{stroke-dasharray:6 10;animation:coh-flow 2.4s linear infinite}@keyframes coh-flow{to{stroke-dashoffset:-64}}")
    X = lambda x: 640 - x  # drawn with the nose on the right, as the aeroplane flies left to right
    c.add(rect(X(330), 70, 290, 230, "surface-2", "line-strong", SECOND))
    c.add(text(X(60), 92, "Engine compartment", 13, "end", "fg-muted", weight=600))
    c.add(rect(40, 70, 270, 230, "surface", "line-strong", SECOND))
    c.add(text(52, 92, "Cabin", 13, "start", "fg-muted", weight=600))
    c.add(line(X(330), 60, X(330), 310, "fg", 4))
    c.add(text(X(330), 54, "firewall", 11, "middle", "fg-muted"))
    # engine
    c.add(rect(X(220), 104, 140, 56, "surface", "fg", MAIN, rx=8))
    c.add(text(X(150), 137, "engine", 13, "middle", "fg-muted"))
    # exhaust pipe
    ex = f"M{X(120)} 160 L{X(120)} 240 L{X(60)} 240 L{X(46)} 262"
    c.add(path(ex, "fg", None, 10))
    c.add(path(ex, "surface-2", None, 5))
    c.add(text(X(112), 176, "exhaust", 11, "start", "fg-muted"))
    # muff around the exhaust, fresh air in
    c.add(rect(X(138), 226, 66, 28, "warn-soft", "warn", MAIN, rx=6, fill_opacity=0.6))
    c.add(text(X(105), 286, "heater muff (shroud)", 12, "middle", "warn-fg", weight=600))
    c.add(text(X(105), 299, "around the exhaust", 11, "middle", "warn-fg"))
    c.add(arrow(X(36), 206, X(72), 228, "sky-fg", SECOND))
    c.add(text(X(28), 198, "fresh air in", 11, "end", "sky-fg"))
    # crack
    c.add(path(f"M{X(120) - 6} 228 l4 3 l-3 3 l5 4", "bad", None, MAIN))
    c.add(callout(X(120) - 4, 232, X(146), 196, ["crack in the exhaust", "inside the muff"], "bad", 12))
    # heater duct to the cabin outlet
    duct = f"M{X(138)} 240 L{X(230)} 240 Q{X(250)} 240 {X(250)} 260 L{X(250)} 270 Q{X(250)} 280 {X(270)} 280 L284 280"
    c.add(path(duct, "warn", None, 12, opacity=0.35))
    c.add(path(duct, "bad", None, 3, cls="coh-flow"))
    c.add(text(X(200), 232, "cabin heat duct", 11, "middle", "warn-fg"))
    # pilot in the seat, facing the engine (nose to the right)
    c.add(path("M178 176 L178 232 L226 232 M200 232 L200 296", "fg-muted", None, MAIN))
    c.add(circle(192, 150, 15, "surface", "fg", MAIN))
    c.add(path("M190 166 L196 222 L246 218 L262 262 M191 182 L236 194", "fg", None, MAIN))
    c.add(arrow(282, 280, 268, 268, "bad", MAIN))
    c.add(text(60, 262, "heater outlet", 11, "start", "bad-fg"))
    c.add(text(60, 275, "at your feet", 11, "start", "bad-fg"))
    c.add(rect(44, 100, 120, 50, "bad-soft", "bad", SECOND, rx=8))
    c.add(multiline(104, 120, ["CO: colourless,", "odourless, tasteless"], 12, "middle", "bad-fg", 1.35))
    # actions
    y = 318
    c.add(text(16, y + 14, "Suspect CO (headache, drowsiness soon after the heater goes on)? Act at once:", 13, "start", "fg", weight=700))
    acts = [("1", ["Cabin heat", "OFF"]), ("2", ["Fresh-air vents", "OPEN"]), ("3", ["Oxygen", "if carried"]), ("4", ["Land ASAP,", "see a doctor"])]
    for i, (n_, a) in enumerate(acts):
        x = 16 + i * 153
        c.add(rect(x, y + 26, 147, 48, "ok-soft", "ok", SECOND, rx=8))
        c.add(circle(x + 22, y + 50, 12, "ok", None))
        c.add(text(x + 22, y + 55, n_, 13, "middle", "surface", weight=800))
        c.add(multiline(x + 42, y + 46, a, 12, "start", "ok-fg", 1.3, weight=700))
    c.add(text(320, y + 100, "Prevent: a CO detector (an electronic alarm is better), exhaust and heater muff inspections, no smoking.", 12, "middle", "fg-muted"))
    c.add(text(320, y + 118, "An exhaust smell means CO is probably there too; no smell does not mean no CO.", 12, "middle", "fg-muted"))
    return c


@chart
def atmosphere_pressure_oxygen_vs_altitude() -> Canvas:
    c = Canvas("Pressure and oxygen partial pressure fall with height", "Total pressure and oxygen partial pressure against altitude. Total pressure "
               "1013 hPa at sea level, about 700 at 10,000 feet, about 500 (half) at 18,000 feet, about 375 at 25,000 and 250 at 34,000 feet. Oxygen "
               "stays about 21 percent of the air, so its partial pressure is 0.21 times the total: about 213 hPa at sea level, 147 at 10,000 feet and "
               "105 at 18,000 feet.", height=420, prefix="apo")
    ch = Chart(c, (0, 36000), (0, 1100), box=(70, 40, 470, 330), xlabel="Altitude (ft)", ylabel="Pressure (hPa)",
               xticks=[0, 10000, 18000, 25000, 34000], yticks=[0, 250, 500, 750, 1000], xfmt=lambda v: f"{int(v / 1000)}k" if v else "0")
    c.add(ch.band(10000, 36000, "warn", 0.06))
    c.add(ch.axes())
    tot = sample(isa_pressure, 0, 35000, 70)
    c.add(ch.area(tot, "info", 0.06))
    c.add(ch.curve(tot, "info", MAIN, label="Total pressure", label_at=10, label_dx=10, label_dy=-14))
    po2 = [(h, 0.21 * p) for h, p in tot]
    c.add(ch.area(po2, "brand", 0.15))
    c.add(ch.curve(po2, "brand", MAIN))
    c.add(text(ch.px(11000), ch.py(330), "Oxygen partial pressure", 13, "start", "brand", weight=600))
    c.add(text(ch.px(11000), ch.py(330) + 16, "PO2 = 0.21 × total", 12, "start", "brand", cls="num"))
    for h, p_, lab in ((0, 1013, "1013"), (10000, 700, "≈700"), (18000, 500, "≈500: half"), (25000, 375, "≈375"), (34000, 250, "≈250")):
        c.add(ch.point(h, p_, "info", 4.5))
        c.add(num(ch.px(h) + 8, ch.py(p_) - 8, lab, 12, "start", "info-fg", weight=600))
    for h, p_, lab in ((0, 213, "213"), (10000, 147, "147"), (18000, 105, "105")):
        c.add(ch.point(h, p_, "brand", 4.5))
        c.add(num(ch.px(h) + 8, ch.py(p_) - 8, lab, 12, "start", "brand", weight=700))
    c.add(ch.vline(10000, "warn", DASH))
    c.add(text(ch.px(10000) + 6, ch.py(1060), "above 10,000 ft:", 11, "start", "warn-fg", weight=600))
    c.add(text(ch.px(10000) + 6, ch.py(1060) + 13, "oxygen requirements (Part 91 MOS)", 11, "start", "warn-fg"))
    # the composition column: same mix at every height
    x0 = 494
    c.add(text(x0 + 64, 52, "Same mix, less air", 13, "middle", "fg", weight=700))
    for i, (h, lab) in enumerate(((0, "sea level"), (18000, "18,000 ft"))):
        x = x0 + i * 68
        top, bot = 70, 70 + 200
        fill_h = 200 * isa_pressure(h) / 1013.25
        c.add(rect(x + 8, bot - fill_h, 44, fill_h * 0.79, "info-soft", "info", THIN))
        c.add(rect(x + 8, bot - fill_h * 0.21, 44, fill_h * 0.21, "brand-soft", "brand", SECOND))
        c.add(rect(x + 8, top, 44, 200, None, "line-strong", THIN, dash=DASH))
        c.add(num(x + 30, bot - fill_h * 0.105 + 4, "21%", 11, "middle", "brand-fg", weight=700))
        c.add(num(x + 30, bot - fill_h * 0.6 + 4, "78%", 11, "middle", "info-fg"))
        c.add(text(x + 30, bot + 16, lab, 11, "middle", "fg-muted"))
    c.add(multiline(x0 + 64, 306, ["O2 is 21% of the air", "at both; the column", "is half as heavy"], 11, "middle", "fg-muted", 1.3))
    c.add(text(320, 392, "It is the partial pressure, not the percentage, that drives oxygen into the blood.", 12, "middle", "fg", weight=600))
    c.add(text(320, 410, "Nitrogen 78%, oxygen 21%, argon, CO2 and others 1%, at every height we fly.", 11, "middle", "fg-muted"))
    return c


@chart
def hypoxia_time_of_useful_consciousness() -> Canvas:
    c = Canvas("Time of useful consciousness shrinks with altitude", "Time of useful consciousness for a seated, resting person: 20 to 30 minutes at "
               "18,000 feet, 5 to 10 minutes at 22,000, 3 to 5 minutes at 25,000, 1 to 2 minutes at 30,000, 30 to 60 seconds at 35,000 and 15 to 20 "
               "seconds at 40,000 feet. Exercise, smoking, fatigue and a rapid decompression shorten it; rapid decompression roughly halves it.",
               height=400, prefix="tuc")
    lg = lambda sec: math.log10(sec)
    ticks = [15, 30, 60, 120, 300, 600, 1800]
    names = {15: "15 s", 30: "30 s", 60: "1 min", 120: "2 min", 300: "5 min", 600: "10 min", 1800: "30 min"}
    rows = [(18000, 1200, 1800, "20 to 30 min"), (22000, 300, 600, "5 to 10 min"), (25000, 180, 300, "3 to 5 min"), (30000, 60, 120, "1 to 2 min"),
            (35000, 30, 60, "30 to 60 s"), (40000, 15, 20, "15 to 20 s")]
    ch = Chart(c, (lg(10), lg(2600)), (0, 7), box=(110, 40, 610, 320), xlabel="Time of useful consciousness (log scale)", ylabel=None,
               xticks=[lg(t) for t in ticks], yticks=[], xfmt=lambda v: names[round(10 ** v)])
    c.add(ch.axes())
    for i, (alt, a, b, lab) in enumerate(rows):
        yv = 6.2 - i
        Y = ch.py(yv)
        c.add(num(ch.left - 10, Y + 4, f"{alt:,} ft", 12, "end", "fg", weight=600))
        c.add(rect(ch.px(lg(a)), Y - 9, max(ch.px(lg(b)) - ch.px(lg(a)), 6), 18, "brand", None, rx=4, fill_opacity=0.85))
        if alt == 25000:
            # rapid decompression at FL250: roughly half, 1.5 to 2.5 minutes
            c.add(rect(ch.px(lg(90)), Y + 12, ch.px(lg(150)) - ch.px(lg(90)), 14, "bad-soft", "bad", SECOND, rx=4))
        anchor_x = ch.px(lg(b)) + 8 if alt != 18000 else ch.px(lg(a)) - 8
        c.add(text(anchor_x, Y + 4, lab, 12, "start" if alt != 18000 else "end", "brand", weight=700))
    Y = ch.py(6.2 - 2)
    c.add(text(ch.px(lg(150)) + 8, Y + 23, "after rapid decompression: 1.5 to 2.5 min", 11, "start", "bad", weight=600))
    c.add(text(320, 372, "TUC ends well before unconsciousness: oxygen mask on first, then descend.", 12, "middle", "fg", weight=600))
    c.add(text(320, 390, "Shortened by exercise, smoking, fatigue and a rapid decompression (roughly halved).", 11, "middle", "fg-muted"))
    return c


@chart
def hypoxia_types_and_causes() -> Canvas:
    c = Canvas("Four ways to starve the brain of oxygen", "The oxygen chain from the air to the cells, with the four types of hypoxia where they break "
               "it. Hypoxic: low oxygen partial pressure in the lungs, from altitude. Anaemic: blood cannot carry enough oxygen, from carbon monoxide, "
               "smoking, blood donation or anaemia. Stagnant: blood not circulating well, from positive g, cold or shock. Histotoxic: cells cannot use "
               "the oxygen, from alcohol, some drugs or cyanide.", height=440, prefix="hyt")
    links = [("Air", "21% oxygen"), ("Lungs", "alveoli"), ("Blood", "haemoglobin"), ("Circulation", "heart pumps"), ("Cells", "brain, retina")]
    xs = [68, 194, 320, 446, 572]
    y = 70
    c.add(text(320, 28, "Oxygen's journey to the brain, and where each type of hypoxia breaks it", 14, "middle", "fg", weight=700))
    for i, ((h, sub), x) in enumerate(zip(links, xs)):
        c.add(rect(x - 52, y - 22, 104, 50, "surface-2", "line-strong", SECOND, rx=10))
        c.add(text(x, y, h, 14, "middle", "fg", weight=700))
        c.add(text(x, y + 17, sub, 11, "middle", "fg-muted"))
        if i < 4:
            c.add(arrow(x + 54, y + 3, xs[i + 1] - 54, y + 3, "brand", MAIN))
    types = [
        ("Hypoxic", "(altitude)", "low O2 pressure", ["altitude without", "oxygen; cabin", "decompression"], ["descend; oxygen", "above 10,000 ft"], xs[1]),
        ("Anaemic", "(hypaemic)", "blood can't carry it", ["carbon monoxide,", "smoking, blood", "donation, anaemia"], ["remove CO source;", "100% oxygen"], xs[2]),
        ("Stagnant", "", "poor circulation", ["positive g, cold,", "shock, sitting", "cramped"], ["limit g, keep", "warm, move limbs"], xs[3]),
        ("Histotoxic", "", "cells can't use it", ["alcohol, some", "drugs, cyanide"], ["prevent it: oxygen", "does little"], xs[4]),
    ]
    for i, (name, alt, what, causes, fix, bx) in enumerate(types):
        x = 16 + i * 153
        # break marker on the link of the chain it hits
        my = y + 28
        c.add(line(bx, my + 9, x + 73, 124, "bad", THIN, dash=DASH))
        c.add(circle(bx, my, 9, "bad", "surface", 1.5))
        c.add(line(bx - 4, my - 4, bx + 4, my + 4, "surface", 2))
        c.add(line(bx + 4, my - 4, bx - 4, my + 4, "surface", 2))
        c.add(rect(x, 124, 147, 206, "surface", "bad", SECOND, rx=10))
        c.add(text(x + 12, 146, name, 15, "start", "bad", weight=700))
        if alt:
            c.add(text(x + 12, 162, alt, 11, "start", "fg-muted"))
        c.add(text(x + 12, 184, what, 12, "start", "fg", weight=600))
        c.add(text(x + 12, 206, "Causes", 11, "start", "fg-muted", weight=700))
        c.add(multiline(x + 12, 222, causes, 11, "start", "fg", 1.35))
        c.add(text(x + 12, 280, "Combat it", 11, "start", "ok-fg", weight=700))
        c.add(multiline(x + 12, 296, fix, 11, "start", "ok-fg", 1.35))
    c.add(rect(16, 342, 608, 86, "warn-soft", "warn", SECOND, rx=10))
    c.add(text(32, 366, "Why it is insidious", 14, "start", "warn-fg", weight=700))
    c.add(text(32, 386, "Hypoxia brings euphoria, over-confidence, lack of self-criticism and a false sense of security.", 12, "start", "warn-fg"))
    c.add(text(32, 403, "The pilot feels fine, even good, while judgement, memory and arithmetic deteriorate.", 12, "start", "warn-fg"))
    c.add(text(32, 420, "Rely on altitude rules and oxygen, not on how you feel.", 12, "start", "warn-fg", weight=700))
    return c


@chart
def decision_making_decide() -> Canvas:
    c = Canvas("DECIDE: a loop, not a one-off", "The DECIDE model drawn as a cycle: Detect a change, Estimate its significance, Choose a safe outcome, "
               "Identify actions, Do it, Evaluate the result, and back to Detect. A dot travels round the loop.", height=470, prefix="dec")
    cx, cy, R = 320, 232, 140
    c.style(".dec-spin{animation:dec-spin 9s linear infinite}@keyframes dec-spin{to{transform:rotate(360deg)}}")
    c.add(circle(cx, cy, R, None, "brand-soft", 10))
    steps = [("D", "Detect", "a change"), ("E", "Estimate", "its significance"), ("C", "Choose", "a safe outcome"),
             ("I", "Identify", "the actions"), ("D", "Do", "it"), ("E", "Evaluate", "the result")]
    for i in range(6):
        a1, a2 = math.radians(-90 + i * 60 + 13), math.radians(-90 + (i + 1) * 60 - 13)
        c.add(path(arc_path_deg(cx, cy, R, a1, a2), "brand", None, MAIN, arrow_end=True))
    # the travelling dot: rotates about the centre (static at Detect where animation is off)
    c.add(group(group(circle(0, -R, 7, "warn", "surface", 2), cls="dec-spin"), transform=f"translate({cx} {cy})"))
    for i, (L_, word, sub) in enumerate(steps):
        a = math.radians(-90 + i * 60)
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        c.add(circle(x, y, 24, "brand-soft", "brand", MAIN))
        c.add(text(x, y + 8, L_, 22, "middle", "brand-fg", weight=800))
        if abs(math.cos(a)) < 0.2:
            ty = y - 36 if math.sin(a) < 0 else y + 46
            c.add(text(x - 4, ty, word, 15, "end", "fg", weight=700))
            c.add(text(x + 4, ty, sub, 13, "start", "fg-muted"))
            continue
        right = math.cos(a) > 0
        tx = x + 34 if right else x - 34
        anchor = "start" if right else "end"
        c.add(text(tx, y + 1, word, 15, anchor, "fg", weight=700))
        c.add(text(tx, y + 18, sub, 12, anchor, "fg-muted"))
    c.add(text(cx, cy - 12, "Aeronautical", 14, "middle", "fg-muted", weight=600))
    c.add(text(cx, cy + 6, "decision-making", 14, "middle", "fg-muted", weight=600))
    c.add(text(cx, cy + 26, "keep going round", 12, "middle", "fg-faint"))
    c.add(text(320, 454, "Also: PAVE for pre-flight risk, IMSAFE for personal fitness, personal minimums set on the ground.", 12, "middle", "fg-muted"))
    return c


def arc_path_deg(cx: float, cy: float, r: float, a0: float, a1: float) -> str:
    """Arc between two angles in radians (clockwise on screen)."""
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    return f"M{fmt(x0)} {fmt(y0)} A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x1)} {fmt(y1)}"


@chart
def stress_performance_curve() -> Canvas:
    c = Canvas("Arousal and performance: the inverted U", "Performance against arousal follows an inverted U (the Yerkes-Dodson curve): too little "
               "arousal gives boredom and inattention, a moderate level gives the best performance, too much gives anxiety, narrowed attention, poor "
               "memory and panic.", height=380, prefix="spc")
    ch = Chart(c, (0, 10), (0, 11.5), box=(70, 30, 610, 290), xlabel="Arousal (stress) →", ylabel="Performance →", grid=False)
    c.add(ch.band(0, 3, "info", 0.08))
    c.add(ch.band(3.6, 6.4, "ok", 0.12))
    c.add(ch.band(7, 10, "bad", 0.08))
    c.add(ch.axes())
    f = lambda x: 1 + 8 * math.exp(-((x - 5) / 2.4) ** 2)
    c.add(ch.curve(sample(f, 0.2, 9.8, 60), "brand", 3))
    c.add(ch.point(5, f(5), "brand", 6))
    c.add(text(ch.px(5), ch.py(10.8), "Best performance", 14, "middle", "ok-fg", weight=700))
    c.add(text(ch.px(5), ch.py(10.8) + 16, "moderate arousal", 12, "middle", "ok-fg"))
    c.add(text(ch.px(1.5), ch.py(5.6), "Too little", 14, "middle", "info-fg", weight=700))
    c.add(multiline(ch.px(1.5), ch.py(5.6) + 17, ["boredom,", "inattention,", "complacency"], 12, "middle", "info-fg"))
    c.add(text(ch.px(8.5), ch.py(5.6), "Too much", 14, "middle", "bad-fg", weight=700))
    c.add(multiline(ch.px(8.5), ch.py(5.6) + 17, ["anxiety, tunnelling,", "poor memory,", "panic"], 12, "middle", "bad-fg"))
    c.add(text(ch.px(1.5), ch.py(0.6), "long cruise leg", 11, "middle", "fg-muted"))
    c.add(text(ch.px(8.5), ch.py(0.6), "lost, bad weather, rough engine", 11, "middle", "fg-muted"))
    c.add(text(320, 344, "Manage stress: plan and prepare thoroughly, don't fly preoccupied, slow your breathing,", 12, "middle", "fg-muted"))
    c.add(text(320, 362, "keep fit, sleep and eat well, talk problems through.", 12, "middle", "fg-muted"))
    return c


@chart
def first_aid_drsabcd() -> Canvas:
    c = Canvas("DRSABCD: the first aid action plan", "Seven steps in order: Danger, Response, Send for help, Airway, Breathing, CPR (30 compressions "
               "to 2 breaths, about 100 to 120 compressions a minute), Defibrillation.", height=400, prefix="drs")
    steps = [("D", "Danger", ["fuel, fire, a running", "engine, power lines"], "bad"),
             ("R", "Response", ["conscious? talk", "and gently squeeze"], "warn"),
             ("S", "Send for help", ["000 (112 mobile);", "ELT or PLB if remote"], "warn"),
             ("A", "Airway", ["open and clear", "the airway"], "brand"),
             ("B", "Breathing", ["look, listen, feel", "for normal breathing"], "brand"),
             ("C", "CPR", ["30 compressions to", "2 breaths, about", "100 to 120 a minute"], "brand"),
             ("D", "Defibrillation", ["apply an AED", "if available"], "brand")]
    W_, H_ = 140, 124
    pos = [(16 + i * 154, 24) for i in range(4)] + [(93 + i * 154, 212) for i in range(3)]
    for i, ((L_, word, body, col_), (x, y)) in enumerate(zip(steps, pos)):
        c.add(rect(x, y, W_, H_, "surface", col_, MAIN, rx=12))
        c.add(circle(x + 28, y + 28, 18, SOFT[col_], col_, MAIN))
        c.add(text(x + 28, y + 35, L_, 20, "middle", FG[col_], weight=800))
        c.add(num(x + W_ - 14, y + 26, str(i + 1), 13, "end", "fg-faint", weight=700))
        c.add(text(x + 12, y + 68, word, 14, "start", "fg", weight=700))
        c.add(multiline(x + 12, y + 88, body, 11, "start", "fg-muted", 1.35))
    for i in (0, 1, 2, 4, 5):
        x, y = pos[i]
        c.add(arrow(x + W_ + 1, y + H_ / 2, x + 153, y + H_ / 2, "fg-muted", SECOND))
    x4, y4 = pos[3]
    x5, y5 = pos[4]
    c.add(path(f"M{x4 + W_ / 2} {y4 + H_ + 2} L{x4 + W_ / 2} {y4 + H_ + 24} L{x5 + W_ / 2} {y4 + H_ + 24} L{x5 + W_ / 2} {y5 - 2}", "fg-muted", None, SECOND, arrow_end=True))
    c.add(text(320, 368, "Unconscious but breathing: recovery position, airway clear. Bleeding: firm direct pressure.", 12, "middle", "fg-muted"))
    c.add(text(320, 386, "Burns: cool under clean running water for 20 minutes. Fractures: immobilise as found.", 12, "middle", "fg-muted"))
    return c


@chart
def survival_priorities() -> Canvas:
    c = Canvas("After a forced landing: survival priorities", "Priorities in order: protection (first aid, shelter), location (help rescuers find "
               "you), water, then food. Stay with the aircraft: it is easier to see than a person, gives shade, and the search follows your notified "
               "route. Activate the ELT or PLB, try 121.5 MHz, and lay out ground-to-air signals: V require assistance, X require medical assistance, "
               "N no, Y yes, an arrow for proceeding in this direction.", height=460, prefix="svp")
    pr = [("1", "Protection", "first aid, shelter, shade"), ("2", "Location", "ELT/PLB on, radio, signals"),
          ("3", "Water", "cut sweat loss; rest in shade"), ("4", "Food", "last: weeks without it")]
    c.add(text(16, 30, "In this order", 15, "start", "fg", weight=700))
    for i, (n_, h, s_) in enumerate(pr):
        y = 46 + i * 64
        w = 258 - i * 14
        col_ = "brand" if i < 2 else "info" if i == 2 else "surface"
        c.add(rect(16, y, w, 54, SOFT.get(col_, "surface-2"), col_ if col_ in SOFT else "line-strong", SECOND, rx=10))
        c.add(circle(42, y + 27, 15, col_ if col_ in SOFT else "fg-muted", None))
        c.add(text(42, y + 33, n_, 15, "middle", "surface", weight=800))
        c.add(text(66, y + 24, h, 14, "start", FG.get(col_, "fg"), weight=700))
        c.add(text(66, y + 42, s_, 11, "start", FG.get(col_, "fg-muted")))
    gx0, gy = 290, 250
    c.add(rect(gx0, 46, 334, 250, "warn-soft", None, rx=12, fill_opacity=0.5))
    c.add(circle(598, 70, 13, "warn", None, fill_opacity=0.8))
    c.add(path(f"M{gx0} {gy} Q{gx0 + 160} {gy - 10} {gx0 + 334} {gy} L{gx0 + 334} 296 L{gx0} 296 Z", None, "surface-2"))
    c.add(ellipse(442, gy - 4, 44, 5, "fg-faint", None, fill_opacity=0.35))   # the high wing's shade
    c.add(plane_side(450, gy - 29.5, 1.25))                                     # wheels (local y 19.5) on the ground at gy - 5
    c.add(text(440, gy + 26, "shade under the wing", 11, "middle", "fg-muted"))
    c.add(path(f"M{gx0 + 254} {gy - 2} L{gx0 + 274} {gy + 26} L{gx0 + 294} {gy - 2}", "bad", None, 5))
    c.add(text(gx0 + 274, gy + 40, "\"V\" laid out", 11, "middle", "bad"))
    c.add(text(gx0 + 16, 78, "Stay with the aircraft", 16, "start", "brand-fg", weight=700))
    c.add(multiline(gx0 + 16, 98, ["easier to see from the air than a person;", "gives shade; the search follows your", "notified route (SARTIME or flight plan)"], 11, "start", "fg"))
    c.add(path(f"M{gx0 + 26} {gy - 4} q-10 -20 4 -36 q14 -16 0 -36", "fg-muted", None, 3, opacity=0.7))
    c.add(path(f"M{gx0 + 18} {gy} l8 -12 l8 12 z", "warn", "warn", THIN))
    c.add(text(gx0 + 40, gy - 86, "smoke by day,", 11, "start", "fg-muted"))
    c.add(text(gx0 + 40, gy - 73, "flame by night", 11, "start", "fg-muted"))
    # signal codes
    y = 320
    c.add(text(16, y, "Ground-to-air signals (see ERSA): make them large and contrasting", 13, "start", "fg", weight=700))
    codes = [("V", ["require", "assistance"]), ("X", ["require medical", "assistance"]), ("N", ["no"]), ("Y", ["yes"]), ("→", ["proceeding in", "this direction"])]
    for i, (k, m) in enumerate(codes):
        x = 76 + i * 122
        c.add(rect(x - 16, y + 12, 32, 32, "surface-2", "line-strong", THIN, rx=6))
        c.add(text(x, y + 35, k, 18, "middle", "bad", weight=800))
        c.add(multiline(x, y + 60, m, 11, "middle", "fg-muted", 1.3))
    c.add(rect(16, 402, 608, 46, "bad-soft", "bad", SECOND, rx=8))
    c.add(text(320, 421, "Don't walk away from the aircraft. Don't ration water to the point of dehydration:", 12, "middle", "bad-fg", weight=600))
    c.add(text(320, 438, "drink what you need and reduce sweat loss. No alcohol, urine or seawater.", 12, "middle", "bad-fg"))
    return c


@chart
def tem_model() -> Canvas:
    c = Canvas("Threat and error management", "Threats (outside the pilot's control) and errors (the pilot's own actions or inactions) can each be managed, "
               "leaving the flight safe, or mismanaged, leading on: a mismanaged threat or error becomes an undesired aircraft state, the last stage "
               "before an incident or accident. Example: pre-landing flap not set, trapped by the pre-landing check; if not trapped, a fast, long "
               "approach that needs a go-around. Countermeasures: anticipate, recognise, recover.", height=480, prefix="tem")
    W_ = 176
    cols = [("Threats", "outside your control", ["weather, terrain, traffic,", "ATC changes, defects,", "passengers, time pressure"], "warn", 16),
            ("Errors", "your action or inaction", ["handling, procedural,", "communication; e.g. the", "landing flap not set"], "info", 232),
            ("Undesired aircraft state", "safety margins reduced", ["position, speed, attitude", "or configuration; e.g.", "fast and long on final"], "bad", 448)]
    for name, sub, ex, col_, x in cols:
        c.add(rect(x, 34, W_, 128, SOFT[col_], col_, MAIN, rx=12))
        c.add(text(x + W_ / 2, 58, name, 15 if len(name) < 14 else 12, "middle", FG[col_], weight=700))
        c.add(text(x + W_ / 2, 76, sub, 11, "middle", FG[col_]))
        c.add(multiline(x + 12, 104, ex, 11, "start", "fg", 1.4))
    for x in (16 + W_, 232 + W_):
        c.add(arrow(x + 3, 58, x + 37, 58, "bad", MAIN))
        c.add(text(x + 20, 24, "mismanaged", 11, "middle", "bad", weight=600))
    # managed / trapped / recovered: down to a safe flight
    for x, lab in ((16 + W_ / 2, "managed"), (232 + W_ / 2, "trapped"), (472, "recovered")):
        c.add(arrow(x, 164, x, 252, "ok", MAIN))
        c.add(text(x + 6 if x < 400 else x - 6, 212, lab, 11, "start" if x < 400 else "end", "ok-fg", weight=600))
    c.add(rect(16, 256, 508, 40, "ok-soft", "ok", SECOND, rx=10))
    c.add(text(270, 281, "Safe flight: safety margins kept or restored", 14, "middle", "ok-fg", weight=700))
    # mismanaged UAS
    c.add(arrow(580, 164, 580, 220, "bad", MAIN))
    c.add(text(574, 194, "mismanaged", 11, "end", "bad", weight=600))
    c.add(rect(536, 224, 88, 72, "bad", None, rx=10))
    c.add(multiline(580, 254, ["Incident or", "accident"], 13, "middle", "surface", 1.3, weight=700))
    # countermeasures
    y = 322
    c.add(text(16, y, "Single-pilot countermeasures, every flight", 14, "start", "fg", weight=700))
    cm = [("Anticipate", ["before each phase: what", "threats are ahead? Brief", "yourself out loud."]),
          ("Recognise", ["monitor and cross-check", "so threats, errors and", "UAS are spotted early"]),
          ("Recover", ["trap the error, manage", "the threat, get out of the", "UAS: go around, turn back"])]
    for i, (h, body) in enumerate(cm):
        c.add(card(16 + i * 210, y + 12, 188, 86, "brand", h, body, 11, 14))
    c.add(text(320, y + 122, "Tools: planning, briefings, checklists and SOPs, monitoring, workload management, personal minimums.", 11, "middle", "fg-muted"))
    c.add(text(320, y + 140, "In any undesired aircraft state: aviate, navigate, communicate.", 12, "middle", "fg", weight=600))
    return c


@chart
def anr_noise_cancelling() -> Canvas:
    c = Canvas("How a headset cuts engine noise", "Passive protection: the ear seal and shell block noise, but only if the seal is "
               "intact. Active noise reduction: a microphone hears the low-frequency engine and propeller drone and the electronics play an opposite "
               "sound wave, so the two cancel and much less reaches the ear.", height=360, prefix="anr")
    x0, x1 = 40, 380

    def wave(y: float, amp: float, flip: bool = False, n: int = 3) -> list[tuple[float, float]]:
        return [(x0 + (x1 - x0) * i / 120, y + (-1 if flip else 1) * amp * math.sin(2 * math.pi * n * i / 120)) for i in range(121)]

    c.add(text(16, 30, "Active noise reduction (ANR): best for the low-frequency drone", 14, "start", "fg", weight=700))
    c.add(path(smooth_path(wave(84, 26)), "warn", None, MAIN))
    c.add(text(x1 + 12, 80, "engine and propeller", 12, "start", "warn-fg", weight=600))
    c.add(text(x1 + 12, 95, "drone (low frequency)", 11, "start", "warn-fg"))
    c.add(text(200, 130, "+", 20, "middle", "fg-muted", weight=700))
    c.add(path(smooth_path(wave(172, 26, True)), "info", None, MAIN, dash="6 4"))
    c.add(text(x1 + 12, 168, "opposite wave from", 12, "start", "info-fg", weight=600))
    c.add(text(x1 + 12, 183, "the headset electronics", 11, "start", "info-fg"))
    c.add(text(200, 218, "=", 20, "middle", "fg-muted", weight=700))
    c.add(path(smooth_path(wave(250, 4)), "ok", None, MAIN))
    c.add(text(x1 + 12, 246, "much less noise", 12, "start", "ok-fg", weight=600))
    c.add(text(x1 + 12, 261, "at the eardrum", 11, "start", "ok-fg"))
    c.add(rect(16, 286, 608, 62, "surface-2", "line-strong", SECOND, rx=10))
    c.add(text(30, 308, "Passive protection (every headset, earplugs): the seal and shell block the noise.", 12, "start", "fg", weight=600))
    c.add(text(30, 326, "Cracked cushions, glasses arms, hair or a cap under the seal let it leak in.", 12, "start", "fg-muted"))
    c.add(text(30, 342, "A good seal or ANR lets you keep the radio volume low.", 12, "start", "fg-muted"))
    return c
