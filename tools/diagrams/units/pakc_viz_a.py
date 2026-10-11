"""PAKC 2.1 to 3.4: diagrams added in the 2026-10-10 visualisation push (Phase 1b, slice A).
Figures and phraseology come from content/notes/PAKC/; change the note first, then the diagram."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import DASH, MAIN, SECOND, THIN, Canvas, arrow, circle, group, line, multiline, path, plane_side, polyline, rect, smooth_path, text
from tools.diagrams.units.pakc import EDGE, FG, SOFT
from tools.diagrams.units.phfc import card, pill


# ---------------------------------------------------------------- 2.2 supercharging
@chart
def centrifugal_compressor() -> Canvas:
    c = Canvas("How a centrifugal compressor squeezes the air",
               "A centrifugal compressor seen face on. Air enters at the hub of the spinning impeller, is flung outwards by its curved "
               "vanes and leaves the rim fast. The snail-shaped housing around the rim gradually widens, so the air slows down and its "
               "speed is turned into pressure before it leaves for the engine. Three gauges along the path show the speed low then high "
               "then low again, while the pressure rises at the rim and rises further in the widening housing. The faster the impeller "
               "spins, the more it squeezes. The gear-driven supercharger spins it from the crankshaft, the turbocharger from an exhaust "
               "turbine on the same shaft.", height=480, prefix="ccw")
    c.style(".ccw-spin{animation:ccw-spin 2.4s linear infinite}@keyframes ccw-spin{to{transform:rotate(360deg)}}")
    cx, cy = 200, 236
    c.add(text(320, 28, "Fling it out, then slow it down: speed becomes pressure", 16, "middle", "fg", weight=700))
    # the volute: a spiral widening clockwise from the tongue (top) round to the outlet duct running right
    r0, r1 = 92, 146
    pts = []
    for a in range(-90, 271, 6):
        r = r0 + (r1 - r0) * (a + 90) / 360
        pts.append((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))))
    duct_end = 470
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f} " + " ".join(f"L{x:.1f} {y:.1f}" for x, y in pts[1:])
    d += f" L{duct_end} {cy - r1:.1f} L{duct_end} {cy - r0:.1f} Z"
    c.add(path(d, "fg", "sky-soft", MAIN))
    # impeller chamber
    c.add(circle(cx, cy, 80, "surface", "line-strong", SECOND))
    # the spinning impeller: hub and backward-curved vanes
    vanes = []
    for i in range(8):
        a = i * 45
        p = []
        for k in range(6):
            rr = 18 + k * 10
            aa = math.radians(a - k * 7)
            p.append((rr * math.cos(aa), rr * math.sin(aa)))
        vanes.append(path(smooth_path(p), "brand", None, 3))
    imp = group(circle(0, 0, 72, "brand-soft", "brand", SECOND), *vanes, circle(0, 0, 17, "surface", "brand", MAIN), circle(0, 0, 4, "brand", None))
    c.add(group(group(imp, cls="ccw-spin"), transform=f"translate({cx} {cy})"))
    # air in at the hub (towards the reader)
    c.add(line(cx - 8, cy + 10, cx - 70, cy + 150, "fg-muted", THIN))
    c.add(multiline(cx - 74, cy + 168, ["Air in at the hub (towards you)"], 13, "middle", "fg", weight=600))
    c.add(text(cx - 74, cy + 186, "impeller: tens of thousands of RPM", 12, "middle", "fg-faint"))
    # flung outwards: an arrow along a vane, outside the wheel
    c.add(arrow(cx + 40, cy + 40, cx + 70, cy + 70, "brand"))
    c.add(line(cx + 76, cy + 76, cx + 100, cy + 104, "fg-muted", THIN))
    c.add(multiline(cx + 104, cy + 118, ["Flung outwards by the vanes:", "leaves the rim fast"], 13, "start", "brand-fg"))
    # round the volute and out
    c.add(arrow(cx - 101, cy - 37, cx - 62, cy - 88, "fg-muted", SECOND))
    c.add(multiline(16, 70, ["Housing widens:", "the air slows down"], 13, "start", "fg-muted"))
    c.add(arrow(duct_end - 120, cy - (r0 + r1) / 2, duct_end + 26, cy - (r0 + r1) / 2, "brand", MAIN))
    c.add(multiline(duct_end + 34, cy - (r0 + r1) / 2 - 8, ["To the", "engine"], 13, "start", "brand-fg", weight=600))
    # gauges along the path: speed and pressure, qualitative
    gx, gy = 424, 190
    stations = [("Hub", 0.25, 0.25), ("Rim", 0.95, 0.55), ("Outlet", 0.3, 0.95)]
    c.add(text(gx + 86, gy - 14, "Along the path (not to scale)", 13, "middle", "fg-muted", weight=600))
    for i, (name, spd, prs) in enumerate(stations):
        x = gx + i * 66
        h = 92
        c.add(rect(x, gy, 14, h, "surface-2", "line-strong", THIN, rx=3))
        c.add(rect(x, gy + h * (1 - spd), 14, h * spd, "info", None, rx=3))
        c.add(rect(x + 20, gy, 14, h, "surface-2", "line-strong", THIN, rx=3))
        c.add(rect(x + 20, gy + h * (1 - prs), 14, h * prs, "brand", None, rx=3))
        c.add(text(x + 17, gy + h + 18, name, 13, "middle", "fg", weight=600))
    c.add(rect(gx, gy + 122, 12, 12, "info", None, rx=2))
    c.add(text(gx + 18, gy + 132, "speed", 13, "start", "info"))
    c.add(rect(gx + 80, gy + 122, 12, 12, "brand", None, rx=2))
    c.add(text(gx + 98, gy + 132, "pressure", 13, "start", "brand-fg"))
    c.add(multiline(320, 452, ["Spin it faster and it squeezes harder. Gear-driven supercharger: spun by the crankshaft.",
                               "Turbocharger: spun by an exhaust turbine on the same shaft."], 12, "middle", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.3 flight instruments
@chart
def alternate_static_cabin() -> Canvas:
    c = Canvas("Why the instruments read high on the alternate static source",
               "A Cessna seen from the side in flight. Air flowing fast over the cabin lowers the pressure outside the doors and windows, "
               "and the cabin leaks towards it, so cabin pressure is slightly lower than true static. The normal static vent on the "
               "fuselage side is blocked. The alternate static valve under the panel lets the instruments take their static pressure from "
               "the cabin instead. Lower static pressure looks to the instruments like more height and more speed: the altimeter reads "
               "slightly high, the airspeed indicator reads slightly high, and the vertical speed indicator shows a brief climb when you "
               "select it, then settles. The POH gives the corrections.", height=420, prefix="asc")
    c.add(text(320, 28, "Alternate static: cabin air is a little below true static", 16, "middle", "fg", weight=700))
    s, X, Y = 2.6, 380, 168
    # streamlines bunching over the cabin: fast flow, lower pressure
    for i, off in enumerate((0, 13, 26)):
        pts = [(40, 92 + off), (240, 94 + off), (330, 104 + off * 0.45), (380, 106 + off * 0.42), (450, 102 + off * 0.5), (600, 92 + off)]
        c.add(path(smooth_path(pts), "sky-fg", None, SECOND, opacity=0.8))
    c.add(arrow(580, 92, 616, 92, "sky-fg", SECOND))
    c.add(text(40, 74, "Air speeds up over the cabin, so the pressure outside the doors and windows drops a little", 13, "start", "sky-fg"))
    # the cabin tinted: the focal pressure
    cab = (f"M{X + 10.2 * s} {Y - 0.4 * s} L{X + 5.5 * s} {Y - 6.1 * s} L{X - 17.5 * s} {Y - 6.1 * s} L{X - 26 * s} {Y - 0.4 * s} "
           f"L{X - 8 * s} {Y + 12.8 * s} L{X + 10 * s} {Y + 12.6 * s} Z")
    c.add(plane_side(X, Y, s, "fg", prop=True, gear=True))
    c.add(path(cab, None, "brand", fill_opacity=0.18))
    # cabin leaking outwards through the door seals
    c.add(arrow(X - 4, Y + 4, X - 4, Y - 30, "brand", SECOND))
    c.add(arrow(X - 30, Y + 6, X - 52, Y - 22, "brand", SECOND))
    c.add(line(X + 2, Y - 30, X + 76, Y - 30, "fg-muted", THIN))
    c.add(text(X + 82, Y - 26, "cabin air leaks out", 12, "start", "brand-fg", weight=600))
    # static vent (blocked) on the rear fuselage
    vx, vy = X - 40 * s, Y + 2.5 * s
    c.add(circle(vx, vy, 5, "bad-soft", "bad", MAIN))
    c.add(line(vx - 4, vy - 4, vx + 4, vy + 4, "bad", SECOND), line(vx - 4, vy + 4, vx + 4, vy - 4, "bad", SECOND))
    c.add(line(vx, vy + 8, vx - 30, vy + 54, "fg-muted", THIN))
    c.add(multiline(vx - 34, vy + 70, ["Static vent blocked", "(ice, insects, a wasp's nest)"], 12, "middle", "bad-fg"))
    # alternate static valve under the panel
    ax, ay = X + 6 * s, Y + 7 * s
    c.add(circle(ax, ay, 5, "brand", "surface", SECOND))
    c.add(line(ax + 4, ay + 4, ax + 46, ay + 54, "fg-muted", THIN))
    c.add(multiline(ax + 50, ay + 66, ["Alternate static valve", "under the panel: cabin air"], 12, "start", "brand-fg", weight=600))
    # what the instruments do
    y0 = 304
    c.add(text(320, y0 - 10, "Lower static pressure looks like more height and more speed", 13, "middle", "fg", weight=600))
    w = 192
    items = [("Altimeter", ["reads slightly high"]), ("Airspeed indicator", ["reads slightly high"]), ("VSI", ["brief climb when", "selected, then settles"])]
    for i, (name, lines) in enumerate(items):
        x = 24 + i * (w + 12)
        c.add(card(x, y0, w, 74, "brand", name, lines, 13, 14))
        c.add(arrow(x + w - 18, y0 + 62, x + w - 18, y0 + 30, "brand", MAIN))
    c.add(text(320, 404, "Usable but less accurate: the POH gives the corrections.", 12, "middle", "fg-muted"))
    return c


# ---------------------------------------------------------------- 3.1 operation of radio systems
@chart
def readability_scale() -> Canvas:
    c = Canvas("The readability scale",
               "The readability scale from AIP GEN 3.4, used to answer a radio check. Each grade shows the request 'radio check one two "
               "four decimal three' as the other station hears it. 1 unreadable: nothing but noise. 2 readable now and then: a word "
               "here and there. 3 readable but with difficulty: all the words come through the noise, with effort. 4 readable. 5 "
               "perfectly readable. Grades 4 and 5 are fine; anything below 4 is worth investigating on the ground before you leave: "
               "the microphone position, the plugs and the other COM radio.", height=388, prefix="rds")
    c.add(text(320, 28, "Readability 1 to 5: how well were you heard?", 16, "middle", "fg", weight=700))
    words = ["radio", "check", "one", "two", "four", "decimal", "three"]
    shown = {1: [], 2: [1, 6], 3: [0, 1, 2, 3, 4, 5, 6], 4: [0, 1, 2, 3, 4, 5, 6], 5: [0, 1, 2, 3, 4, 5, 6]}
    noise = {1: 1.0, 2: 0.8, 3: 0.5, 4: 0.12, 5: 0.0}
    meaning = {1: "Unreadable", 2: "Readable now and then", 3: "Readable but with difficulty", 4: "Readable", 5: "Perfectly readable"}
    tone = {1: "bad", 2: "bad", 3: "warn", 4: "ok", 5: "ok"}
    widths = [len(w_) * 7.4 for w_ in words]
    gap = (606 - 312 - sum(widths)) / (len(words) - 1)
    x_words, x = [], 312.0
    for w_ in widths:
        x_words.append(x)
        x += w_ + gap
    for i, g in enumerate((1, 2, 3, 4, 5)):
        y = 56 + i * 58
        t = tone[g]
        c.add(rect(20, y, 600, 48, SOFT[t] if g in (1, 3, 5) else "surface", t if g == 3 else "line", SECOND if g == 3 else THIN, rx=10))
        c.add(circle(48, y + 24, 16, t, None))
        c.add(text(48, y + 30, str(g), 17, "middle", "surface", weight=700))
        c.add(text(74, y + 29, meaning[g], 14, "start", FG[t] if g == 3 else "fg", weight=600))
        # the words that get through (a dash where a word is lost) above a strip of noise whose size falls with the grade
        for k, w_ in enumerate(words):
            if k in shown[g]:
                c.add(text(x_words[k], y + 22, w_, 12, "start", "fg", weight=600 if g == 5 else None, opacity=0.6 if g == 3 else None))
            else:
                c.add(line(x_words[k] + 2, y + 18, x_words[k] + widths[k] - 2, y + 18, "fg-faint", SECOND, dash="2 4"))
        amp = 5 * noise[g]
        if amp > 0:
            zz = [(312 + k * 4, y + 36 + (amp if k % 2 else -amp)) for k in range(74)]
            c.add(path("M" + " L".join(f"{px:.0f} {py:.1f}" for px, py in zz), "fg-faint", None, THIN))
        else:
            c.add(line(312, y + 36, 606, y + 36, "fg-faint", THIN))
    c.add(text(312, 50, "what the station hears, and the noise under it", 12, "start", "fg-faint"))
    c.add(text(320, 360, "Below 4 on the apron? Check the microphone position, the plugs and the other COM before you go.", 12, "middle", "fg-muted"))
    c.add(text(320, 378, "Exam favourite: 3 is readable but with difficulty; 5 is perfectly readable.", 12, "middle", "brand-fg", weight=600))
    return c


@chart
def establishing_contact() -> Canvas:
    c = Canvas("Establishing two-way contact",
               "A sequence between you and Melbourne Centre. First call: the station you are calling, your call-sign, and request: "
               "'Melbourne Centre, Cessna 152 Alpha Bravo Charlie, request traffic', short so that the controller is ready before the "
               "details. Then wait for the reply. No reply: wait at least about 10 seconds before calling again, and check the "
               "frequency, the volume, the MIC selector and range. Centre answers using your call-sign. You give the rest of the message. "
               "Centre's reply includes an item that must be read back, such as a QNH. You read it back and end with your call-sign: "
               "'QNH one zero one niner, Alpha Bravo Charlie', which catches both your mishearing and the controller's slip.",
               height=460, prefix="ecx")
    c.add(text(320, 28, "Making contact: short first call, wait, then the message", 16, "middle", "fg", weight=700))
    yx, cxl = 80, 548
    c.add(pill(yx - 56, 46, 112, 28, "brand", "You", 14))
    c.add(pill(cxl - 82, 46, 164, 28, "info", "Melbourne Centre", 13))
    c.add(line(yx, 78, yx, 430, "line-strong", SECOND, dash="4 3"))
    c.add(line(cxl, 78, cxl, 430, "line-strong", SECOND, dash="4 3"))

    def msg(y: float, frm: str, words: list[str], note: list[str] | None, colour: str) -> None:
        x1, x2 = (yx, cxl) if frm == "you" else (cxl, yx)
        c.add(arrow(x1 + (6 if frm == "you" else -6), y, x2 + (-8 if frm == "you" else 8), y, colour, MAIN))
        c.add(multiline((yx + cxl) / 2, y - 8 - 15 * (len(words) - 1), words, 13, "middle", FG.get(colour, "fg"), 1.15, weight=600))
        if note:
            c.add(multiline(cxl + 14 if frm == "you" else yx - 14, y - 3, note, 12, "start" if frm == "you" else "end", "fg-muted", 1.25))

    msg(116, "you", ["“Melbourne Centre, Cessna 152 Alpha Bravo Charlie,", "request traffic”"], None, "brand")
    c.add(text((yx + cxl) / 2, 134, "station, call-sign, request: short, so they are ready before the details", 12, "middle", "fg-muted"))
    # wait / no reply loop
    c.add(rect(120, 150, 388, 54, "warn-soft", "warn", SECOND, rx=10))
    c.add(text((yx + cxl) / 2, 172, "Wait for the reply. Nothing after about 10 s?", 13, "middle", "warn-fg", weight=600))
    c.add(text((yx + cxl) / 2, 192, "Check frequency, volume, MIC selector, range; call again", 12, "middle", "warn-fg"))
    msg(236, "centre", ["Centre answers, calling you by call-sign"], None, "info")
    msg(286, "you", ["The rest of the message"], None, "brand")
    msg(344, "centre", ["… an item to read back, e.g. “QNH one zero one niner”"], None, "info")
    msg(402, "you", ["Readback: “QNH one zero one niner, Alpha Bravo Charlie”"], None, "brand")
    c.add(multiline(cxl - 4, 424, ["ends with your call-sign"], 12, "end", "brand-fg"))
    c.add(text(320, 452, "The readback is a two-way check: it catches your mishearing and the controller's slip.", 12, "middle", "fg-muted"))
    return c


# ---------------------------------------------------------------- 3.2 pre-flight radio test and 3.3 fault finding
def _ink(tone: str) -> str:
    return FG[tone] if tone != "fg" else "fg"


# ================================================================ 3.2 the audio panel: talk on one, listen to many
def _key(x: float, y: float, w: float, s: str, tone: str | None) -> str:
    """One audio-panel push button, lit in a tone or dark."""
    if tone:
        return rect(x, y, w, 22, SOFT[tone], EDGE[tone], SECOND, rx=5) + text(x + w / 2, y + 15, s, 11, "middle", FG[tone], weight=700)
    return rect(x, y, w, 22, "surface", "line-strong", THIN, rx=5) + text(x + w / 2, y + 15, s, 11, "middle", "fg-faint", weight=600)


def _pilot(cx: float, cy: float) -> str:
    """Head and shoulders with a headset and boom microphone; the mic sits at (cx - 9, cy + 15)."""
    out = path(f"M{cx - 30} {cy + 44} Q{cx - 28} {cy + 22} {cx} {cy + 21} Q{cx + 28} {cy + 22} {cx + 30} {cy + 44}", "fg-muted", "surface-2", SECOND)
    out += circle(cx, cy, 15, "surface", "fg", SECOND)
    out += path(f"M{cx - 17} {cy - 2} Q{cx - 17} {cy - 24} {cx} {cy - 24} Q{cx + 17} {cy - 24} {cx + 17} {cy - 2}", "fg", None, MAIN)
    out += rect(cx - 22, cy - 8, 8, 16, "fg-muted", "fg", THIN, rx=3) + rect(cx + 14, cy - 8, 8, 16, "fg-muted", "fg", THIN, rx=3)
    out += path(f"M{cx - 18} {cy + 6} Q{cx - 19} {cy + 15} {cx - 11} {cy + 15}", "fg", None, SECOND) + circle(cx - 9, cy + 15, 3, "fg", None)
    return out


def _radio(x: float, y: float, w: float, name: str, freq: str, tx: str | None) -> str:
    out = rect(x, y, w, 50, "surface", "fg", SECOND, rx=7)
    out += text(x + 12, y + 21, name, 13, "start", "fg", weight=700)
    out += text(x + 12, y + 39, freq, 12, "start", "fg-muted")
    if tx:
        out += rect(x + w - 36, y + 9, 26, 16, tx, None, rx=4) + text(x + w - 23, y + 21, "TX", 11, "middle", "surface", weight=700)
    else:
        out += rect(x + w - 36, y + 9, 26, 16, "surface", "line-strong", THIN, rx=4) + text(x + w - 23, y + 21, "TX", 11, "middle", "fg-faint", weight=600)
    return out


@chart
def audio_panel_mic_receive() -> Canvas:
    c = Canvas("Talk on one radio, listen to several", "Two audio panel set-ups side by side. The MIC selector connects the microphone and "
               "press-to-talk switch to one transmitter only, COM 1 or COM 2. The receive buttons (COM 1, COM 2, NAV, ADF, marker) each add "
               "a radio to the headset. Left, set correctly: MIC on COM 1, which is tuned to the CTAF, with COM 1 and COM 2 both selected to "
               "receive, so you call on the CTAF and also monitor the area frequency on COM 2. Right, the classic trap: the CTAF is on COM 2 "
               "and heard clearly, but the MIC selector is on COM 1, tuned to the area frequency, so every call goes out on the wrong "
               "frequency and nobody answers. Hearing a frequency proves nothing about where you transmit; the TX light on the radio that "
               "is transmitting confirms it during the test call.", height=514, prefix="apm")
    c.add(text(20, 28, "MIC picks one transmitter; receive buttons add what you hear", 16, "start", "fg", weight=700))
    setups = [
        (20, "ok", "✓  Set up right", ("CTAF", "Area (Centre)"), "COM 1", {"COM 1", "COM 2"},
         ["Calls go out on the CTAF; you hear", "it, and monitor the area on COM 2:", "you talk on a radio you hear."]),
        (330, "bad", "✗  The classic trap", ("Area (Centre)", "CTAF"), "COM 1", {"COM 2"},
         ["You hear the CTAF clearly, but every", "call goes out on the area frequency:", "nobody answers."]),
    ]
    for x0, tone, head, freqs, mic, rx, result in setups:
        w = 290
        c.add(text(x0, 62, head, 14, "start", FG[tone], weight=700))
        # the audio panel face
        c.add(rect(x0, 74, w, 104, "surface-2", "fg", SECOND, rx=9))
        c.add(text(x0 + 12, 104, "MIC", 12, "start", "fg", weight=700), text(x0 + 12, 138, "RX", 12, "start", "fg", weight=700))
        for i, name in enumerate(("COM 1", "COM 2")):
            c.add(_key(x0 + 50 + i * 50, 88, 44, name, "brand" if name == mic else None))
        c.add(text(x0 + 154, 103, "← one only", 12, "start", "brand-fg", weight=600))
        for i, name in enumerate(("COM 1", "COM 2", "NAV", "ADF", "MKR")):
            c.add(_key(x0 + 50 + i * 47, 122, 44, name, "info" if name in rx else None))
        c.add(text(x0 + 50, 165, "↑ each lit button adds a radio", 12, "start", "info-fg", weight=600))
        # the two radios
        mic_tone = "brand" if tone == "ok" else "bad"
        boxes = {"COM 1": x0, "COM 2": x0 + 152}
        for name, bx in boxes.items():
            c.add(_radio(bx, 200, 138, name, freqs[0] if name == "COM 1" else freqs[1], mic_tone if name == mic else None))
        # routing: the transmit line from the boom mic, a receive line from each selected radio into an ear cup
        pcx, pcy = x0 + 145, 320
        if "COM 1" in rx:
            c.add(polyline([(x0 + 104, 252), (x0 + 104, pcy), (pcx - 26, pcy)], "info", SECOND, arrow_end=True))
        if "COM 2" in rx:
            c.add(polyline([(x0 + 186, 252), (x0 + 186, pcy), (pcx + 26, pcy)], "info", SECOND, arrow_end=True))
        assert mic == "COM 1"
        c.add(polyline([(pcx - 12, pcy + 15), (x0 + 50, pcy + 15), (x0 + 50, 255)], mic_tone, MAIN + 0.5, arrow_end=True))
        c.add(_pilot(pcx, pcy))
        c.add(rect(x0, 380, w, 72, SOFT[tone], EDGE[tone], SECOND, rx=8))
        c.add(multiline(x0 + 12, 403, result, 12.5, "start", FG[tone], 1.35, weight=600))
    # legend
    c.add(line(20, 474, 48, 474, "brand", MAIN + 0.5), text(56, 478, "your calls (MIC)", 12, "start", "fg-muted"))
    c.add(line(180, 474, 208, 474, "info", SECOND), text(216, 478, "what you hear (RX)", 12, "start", "fg-muted"))
    c.add(text(20, 502, "Hearing proves nothing about where you transmit: the TX light on your test call confirms it.", 12, "start", "fg-faint"))
    return c


# ================================================================ 3.2 the avionics master and the bus voltage
@chart
def avionics_master_start() -> Canvas:
    c = Canvas("When the avionics master goes on and off", "A qualitative trace of the electrical bus voltage from before start to "
               "shutdown, with the avionics master switch below it. Before start the avionics master is off. While the starter cranks it "
               "draws a very large current and pulls the voltage down; when it disengages the voltage can surge. Once the alternator is "
               "charging (ammeter or voltmeter, no low-voltage light) the system settles, and only then does the avionics master go on and "
               "the radios self-test. At the end of the flight the avionics master goes off before the engine is shut down, for the same "
               "reason. The dip and the surge are what the off periods keep away from the solid-state avionics. Levels are illustrative.",
               height=446, prefix="avm")
    c.add(text(20, 28, "Avionics off through start and shutdown, on once settled", 16, "start", "fg", weight=700))
    b = [48, 112, 204, 262, 362, 492, 556, 620]          # phase boundaries
    top, bot = 62, 206
    BAT, CHG, DIP, SURGE = 150, 126, 196, 70
    # danger windows behind the trace
    c.add(rect(b[1], top, b[3] - b[1], bot - top, "bad-soft", None))
    c.add(rect(b[6], top, b[7] - b[6], bot - top, "bad-soft", None))
    for x in b[1:-1]:
        c.add(line(x, top, x, bot, "line", THIN, DASH))
    # axes
    c.add(line(b[0], bot, b[7] + 8, bot, "fg-muted", SECOND, arrow_end=True, cap="butt"))
    c.add(line(b[0], bot, b[0], top - 8, "fg-muted", SECOND, arrow_end=True, cap="butt"))
    c.add(text(28, (top + bot) / 2, "bus voltage", 13, "middle", "fg-muted", weight=600, rotate=-90))
    c.add(text(b[7] - 4, bot - 8, "time →", 12, "end", "fg-muted"))
    # the trace
    crank = [(b[1] + 4 + 6 * k, DIP - 8 + (5 if k % 2 else -3)) for k in range(12)]
    pts = [(b[0], BAT), (b[1] - 6, BAT), (b[1] + 2, DIP - 10)] + crank[1:]
    pts += [(b[2] - 4, DIP - 6), (b[2] + 4, SURGE), (b[2] + 14, CHG + 16), (b[2] + 26, CHG - 8), (b[2] + 40, CHG + 4), (b[3], CHG)]
    pts += [(b[6] - 4, CHG), (b[6] + 8, BAT + 10), (b[6] + 18, BAT - 6), (b[6] + 30, BAT + 3), (b[6] + 42, BAT), (b[7], BAT)]
    c.add(polyline(pts, "fg", MAIN))
    c.add(text(156, 112, "heavy load:", 12, "middle", "bad-fg", weight=600), text(156, 127, "voltage dips", 12, "middle", "bad-fg", weight=600))
    c.add(text(b[2] + 14, 78, "voltage surge", 12, "start", "bad-fg", weight=600))
    c.add(text(424, CHG - 12, "taxi · flight · taxi", 12, "middle", "fg-faint"))
    # the avionics master
    y = 224
    c.add(rect(b[0], y, b[4] - b[0], 30, "surface-2", "line-strong", SECOND, rx=6))
    c.add(text((b[0] + b[4]) / 2, y + 20, "AVIONICS MASTER OFF: radios isolated", 12.5, "middle", "fg", weight=700))
    c.add(rect(b[4], y - 3, b[5] - b[4], 36, "brand-soft", "brand", MAIN, rx=6))
    c.add(text((b[4] + b[5]) / 2, y + 20, "AVIONICS ON", 13, "middle", "brand-fg", weight=700))
    c.add(rect(b[5], y, b[7] - b[5], 30, "surface-2", "line-strong", SECOND, rx=6))
    c.add(text((b[5] + b[7]) / 2, y + 20, "OFF", 12.5, "middle", "fg", weight=700))
    # the steps
    steps = [
        (["Before start:", "avionics OFF"], "fg"),
        (["Starter", "cranking"], "bad"),
        (["Starter", "disengages"], "bad"),
        (["Alternator", "charging:", "ammeter or", "voltmeter, no", "low-volts light"], "fg"),
        (["Avionics ON;", "each radio on,", "watch its", "self-test"], "brand"),
        (["Avionics", "OFF"], "fg"),
        (["Engine", "shutdown"], "bad"),
    ]
    for i, (lines, tone) in enumerate(steps):
        cx = (b[i] + b[i + 1]) / 2
        c.add(circle(cx, 284, 11, SOFT[tone], EDGE[tone], THIN), text(cx, 288.5, str(i + 1), 12, "middle", _ink(tone), weight=700, cls="num"))
        c.add(multiline(cx, 314, lines, 11.5, "middle", _ink(tone) if i in (0, 4, 5) else "fg-muted", 1.3, weight=600 if i in (0, 4, 5) else None))
    c.add(rect(20, 392, 600, 1, "line", None))
    c.add(text(20, 414, "Shaded: the dip and the surges that the OFF periods keep away from the solid-state avionics.", 12, "start", "fg-faint"))
    c.add(text(20, 431, "Levels illustrative: the shape matters, not the numbers.", 12, "start", "fg-faint"))
    return c


# ================================================================ 3.2 the VOX threshold
def _noise(t: float) -> float:
    return 29 + 2.5 * math.sin(1.7 * t) + 1.8 * math.sin(4.3 * t + 1) + 1.2 * math.sin(9.1 * t + 2)


BURSTS = [(10, 32, 72, 0.76), (44, 62, 50, 0.92), (72, 93, 70, 0.78)]   # start, end, peak, first-word factor


def _speech(t: float) -> float:
    for a, e, peak, first in BURSTS:
        if a <= t <= e:
            win = min(1.0, (t - a) / 1.5, (e - t) / 1.5)
            u = t - a
            mod = 0.86 + 0.08 * math.sin(2 * math.pi * u / 3.4 + 1.2) + 0.06 * math.sin(2 * math.pi * u / 1.3)
            return peak * win * mod * (first if t < a + 4.5 else 1.0)
    return 0.0


def _level(t: float) -> float:
    return max(_noise(t), _speech(t))


def _open(th: float, hang: float = 3.0) -> list[tuple[float, float]]:
    """Stretches of time the intercom is open for a threshold, with a short hang time bridging gaps between syllables."""
    spans: list[list[float]] = []
    t = 0.0
    while t <= 100:
        if _level(t) > th:
            if spans and t - spans[-1][1] <= hang:
                spans[-1][1] = t
            else:
                spans.append([t, t])
        t += 0.1
    return [(a, e) for a, e in spans]


@chart
def vox_threshold() -> Canvas:
    LOW, RIGHT, HIGH = 22, 42, 59
    c = Canvas("Where the VOX threshold should sit", "Sound level at an intercom microphone against time: steady engine noise, with three "
               "bursts of speech above it, the middle one a quiet passenger. Three threshold settings and when each opens the intercom. Too "
               "low, below the engine noise: the engine holds the intercom open and every headset fills with roar. Right, above the engine "
               "but below normal speech: the intercom opens for every speaker and stays shut for the engine. Too high: the first word of each "
               "sentence is lost before the microphone opens, and the quiet speaker never opens it. VOX works the intercom only; only the "
               "press-to-talk switch transmits. Levels are illustrative.", height=470, prefix="vxt")
    c.add(text(20, 28, "Set VOX above the engine, below normal speech", 16, "start", "fg", weight=700))
    L, R, T, B = 86, 452, 56, 226

    def px(t: float) -> float:
        return L + t / 100 * (R - L)

    def py(v: float) -> float:
        return B - v / 90 * (B - T)
    # axes
    c.add(line(L, B, R + 8, B, "fg-muted", SECOND, arrow_end=True, cap="butt"), line(L, B, L, T - 8, "fg-muted", SECOND, arrow_end=True, cap="butt"))
    c.add(text(64, (T + B) / 2, "sound at the mic", 13, "middle", "fg-muted", weight=600, rotate=-90))
    c.add(text(R, B + 18, "time →", 12, "end", "fg-muted"))
    # the trace, engine band shaded
    n = 400
    pts = [(px(100 * i / n), py(_level(100 * i / n))) for i in range(n + 1)]
    c.add(rect(L + 1, py(34.5), R - L - 1, py(23.5) - py(34.5), "surface-2", None))
    c.add(polyline(pts, "fg-muted", THIN + 0.25))
    c.add(text(px(34), py(LOW) + 16, "↑ engine noise, always there", 11.5, "start", "fg-muted"))
    for (a, e, peak, _), who in zip(BURSTS, ("pilot", "quiet passenger", "pilot")):
        c.add(text(px((a + e) / 2), py(82), who, 12, "middle", "fg-muted", weight=600))
    # thresholds
    for v, tone, name, sub in ((HIGH, "warn", "Too high", "clips words"), (RIGHT, "brand", "Right", "above engine, below speech"), (LOW, "bad", "Too low", "engine opens it")):
        c.add(line(L, py(v), R, py(v), tone, MAIN if tone == "brand" else SECOND, None if tone == "brand" else "6 4"))
        c.add(text(R + 14, py(v) - 2, name, 13, "start", FG[tone], weight=700))
        c.add(text(R + 14, py(v) + 13, sub, 11, "start", FG[tone]))
    # when the intercom is open, per setting
    rows = [(LOW, "bad", "Too low", "roar in every headset"), (RIGHT, "brand", "Right", "opens for every speaker"),
            (HIGH, "warn", "Too high", "words lost")]
    c.add(text(L, 260, "Intercom open:", 12, "start", "fg-muted", weight=700))
    for k, (th, tone, name, verdict) in enumerate(rows):
        y = 274 + k * 34
        c.add(text(L - 10, y + 13, name, 12.5, "end", FG[tone], weight=700))
        c.add(rect(L, y, R - L, 18, "surface-2", None, rx=4))
        for a, e in _open(th):
            c.add(rect(px(a), y, max(3, px(e) - px(a)), 18, SOFT[tone], EDGE[tone], THIN, rx=4))
        c.add(text(R + 14, y + 13, verdict, 12, "start", FG[tone]))
    # the too-high row: mark the clipped first word and the missing quiet speaker
    y = 274 + 2 * 34
    for (a, *_), (o, _e) in zip((BURSTS[0], BURSTS[2]), (_open(HIGH)[0], _open(HIGH)[-1])):
        c.add(rect(px(a), y, px(o) - px(a), 18, "bad-soft", "bad", THIN, rx=3, dash="3 2"))
    c.add(rect(px(BURSTS[1][0]), y, px(BURSTS[1][1]) - px(BURSTS[1][0]), 18, None, "bad", THIN, rx=4, dash="3 2"))
    c.add(text(px(BURSTS[1][0]) - 2, y + 32, "↑ quiet voice never opens it", 11, "start", "bad-fg", weight=600))
    c.add(text(px(BURSTS[0][0]) - 2, y + 32, "↑ first word lost", 11, "start", "bad-fg", weight=600))
    # the PTT note
    c.add(rect(20, 400, 600, 50, "info-soft", "info", SECOND, rx=8))
    c.add(text(34, 421, "VOX works the intercom only.", 13, "start", "info-fg", weight=700))
    c.add(text(34, 439, "Only the press-to-talk switch transmits: talking loudly never puts you on the radio.", 12, "start", "info-fg"))
    c.add(text(620, 464, "Levels illustrative; set it with the engine running.", 11, "end", "fg-faint"))
    return c


# ================================================================ 3.3 a popped breaker
def _breaker(cx: float, base: float, popped: bool) -> str:
    """Side view of a push-button breaker in the panel: body behind the panel line, cap in front; popped shows the collar."""
    out = rect(cx - 18, base, 36, 40, "surface-2", "line-strong", SECOND, rx=3)           # body behind the panel
    out += line(cx - 60, base, cx + 60, base, "fg", MAIN)                                    # the panel face
    rise = 26 if popped else 0
    if popped:
        out += rect(cx - 9, base - rise, 18, rise, "surface", "warn", SECOND)              # exposed collar
        for k in range(3):
            out += line(cx - 9, base - 6 - 7 * k, cx + 9, base - 6 - 7 * k, "warn", THIN)
    fill, edge = ("warn-soft", "warn") if popped else ("surface-2", "fg")
    out += rect(cx - 17, base - rise - 16, 34, 16, fill, edge, MAIN, rx=5)                  # the cap
    return out


@chart
def breaker_reset_once() -> Canvas:
    c = Canvas("A popped circuit breaker: reset once", "Left, a push-button circuit breaker drawn side on: pushed in, the cap sits flush on "
               "the panel; popped, it stands out and shows its collar. Right, the flow when a radio breaker pops: reset it once. If it "
               "holds, carry on and watch it; a single trip may be a momentary spike. If it pops again, leave it out: there is a real "
               "overload or short, and holding it in or resetting it again and again can start an electrical fire. Treat the radio as "
               "failed and write it up.", height=442, prefix="brs")
    c.add(text(20, 28, "A popped breaker gets one reset, never two", 16, "start", "fg", weight=700))
    # the breaker itself
    c.add(rect(20, 48, 172, 356, "surface", "line-strong", THIN, rx=10))
    c.add(text(106, 74, "Pushed in", 13, "middle", "fg", weight=700))
    c.add(_breaker(106, 122, False))
    c.add(text(106, 184, "cap flush on the", 12, "middle", "fg-muted"), text(106, 199, "panel: circuit live", 12, "middle", "fg-muted"))
    c.add(line(36, 216, 176, 216, "line", THIN))
    c.add(text(106, 240, "Popped", 13, "middle", "warn-fg", weight=700))
    c.add(arrow(106, 250, 106, 270, "brand", MAIN))
    c.add(text(113, 265, "reset once", 12, "start", "brand-fg", weight=700))
    c.add(_breaker(106, 318, True))
    c.add(text(106, 376, "stands out, collar", 12, "middle", "warn-fg"), text(106, 391, "showing: circuit off", 12, "middle", "warn-fg"))
    # the flow
    fx = 216

    def box(x: float, y: float, w: float, h: float, tone: str, title: str, lines: list[str], width: float = SECOND) -> None:
        c.add(rect(x, y, w, h, SOFT[tone], EDGE[tone], width, rx=9))
        c.add(text(x + 14, y + 23, title, 14, "start", _ink(tone), weight=700))
        c.add(multiline(x + 14, y + 42, lines, 12, "start", FG[tone] if tone != "fg" else "fg-muted", 1.35))

    box(fx, 48, 404, 54, "warn", "A radio breaker pops", ["the commonest cause of a radio that has gone dark on its own"])
    c.add(arrow(fx + 202, 102, fx + 202, 114, "fg-muted", SECOND))
    c.add(rect(fx + 62, 116, 280, 54, "brand-soft", "brand", MAIN + 0.5, rx=10))
    c.add(text(fx + 202, 140, "Reset it ONCE", 16, "middle", "brand-fg", weight=700))
    c.add(text(fx + 202, 159, "push it back in, one time only", 12, "middle", "brand-fg"))
    # branches
    c.add(polyline([(fx + 140, 170), (fx + 100, 204)], "ok", SECOND, arrow_end=True))
    c.add(polyline([(fx + 264, 170), (fx + 304, 204)], "bad", SECOND, arrow_end=True))
    c.add(text(fx + 112, 188, "holds", 12.5, "end", "ok-fg", weight=700))
    c.add(text(fx + 292, 188, "pops again", 12.5, "start", "bad-fg", weight=700))
    box(fx, 208, 180, 96, "ok", "Carry on, watch it", ["A single trip may be", "a momentary spike,", "which one reset clears."])
    box(fx + 196, 208, 208, 196, "bad", "Leave it out", ["A real overload or short", "(a chafed wire on the", "airframe). Holding it in or", "resetting it again can", "start an electrical fire."], MAIN)
    c.add(line(fx + 210, 340, fx + 394, 340, "bad", THIN))
    c.add(text(fx + 210, 364, "Treat the radio as failed;", 12.5, "start", "bad-fg", weight=700))
    c.add(text(fx + 210, 383, "write it up.", 12.5, "start", "bad-fg", weight=700))
    c.add(text(20, 428, "A breaker opens itself when too much current flows, to stop the wiring overheating.", 12, "start", "fg-faint"))
    return c


# ================================================================ 3.3 when the fault cannot be cleared
@chart
def radio_failure_actions() -> Canvas:
    c = Canvas("When the radio fault will not clear", "The corrective actions in order, each with the reason for it. In the air: squawk 7600 "
               "if you were, or were about to be, talking to ATC, which tells a radar controller without a word that you have lost "
               "communications; follow the ERSA EMERG radio failure procedure, staying in VMC and landing at the most suitable aerodrome, "
               "so ATC can expect a known procedure rather than improvisation; transmit blind, prefixing calls with 'transmitting blind', "
               "because your transmitter may work even if your receiver does not. On the ground: report arrival, which stops a search being "
               "started; write the defect on the maintenance release, or it is a trap for the next pilot.", height=506, prefix="rfa")
    c.add(text(20, 28, "Stop fault-finding and cope: each action tells someone", 16, "start", "fg", weight=700))
    rows = [
        ("Squawk 7600", ["if you were, or were about", "to be, talking to ATC"], "radar controller",
         ["Says “lost communications”", "without a word"]),
        ("Follow ERSA EMERG", ["radio failure procedure:", "stay in VMC, land at the", "most suitable aerodrome"], "ATC and traffic",
         ["They expect a known", "procedure, not improvisation"]),
        ("Transmit blind", ["prefix your calls with", "“transmitting blind”"], "anyone listening",
         ["Your transmitter may work", "even if you hear nothing"]),
        ("Report arrival", ["once on the ground", "(if required)"], "search and rescue",
         ["Stops a search", "being started"]),
        ("Write it up", ["on the maintenance release:", "what failed, when, what tried"], "the next pilot",
         ["Otherwise it is a trap", "set for the next pilot"]),
    ]
    top, rh, gap = 76, 76, 34
    c.add(text(64, 58, "Action", 12, "start", "fg-faint", weight=700))
    c.add(text(290, 58, "Tells", 12, "start", "fg-faint", weight=700))
    c.add(text(446, 58, "Why", 12, "start", "fg-faint", weight=700))
    ys = [top + i * rh + (gap if i >= 3 else 0) for i in range(5)]
    # the spine: the order is the point
    c.add(line(36, ys[0] + 14, 36, ys[-1] + 14, "brand", MAIN + 1))
    for i, ((act, detail, who, why), y) in enumerate(zip(rows, ys)):
        c.add(circle(36, y + 14, 13, "brand", "surface", 2), text(36, y + 19, str(i + 1), 13, "middle", "surface", weight=700, cls="num"))
        c.add(text(64, y + 19, act, 15, "start", "fg", weight=700))
        c.add(multiline(64, y + 37, detail, 11.5, "start", "fg-muted", 1.3))
        c.add(arrow(250, y + 14, 282, y + 14, "info", SECOND))
        c.add(rect(288, y + 2, 142, 24, "info-soft", "info", THIN, rx=12), text(359, y + 18.5, who, 12, "middle", "info-fg", weight=700))
        c.add(multiline(446, y + 18, why, 12, "start", "fg-muted", 1.3))
    # in the air / on the ground split
    gy = ys[3] - gap / 2 - 6
    c.add(line(64, gy, 620, gy, "fg-muted", SECOND, DASH))
    c.add(rect(244, gy - 11, 176, 22, "surface", None))
    c.add(text(332, gy + 4.5, "landed: on the ground ↓", 12, "middle", "fg-muted", weight=700))
    c.add(text(620, gy - 9, "in the air ↑", 11, "end", "fg-faint"))
    c.add(text(20, 492, "Fly first throughout: stay in VMC and keep a good lookout.", 12, "start", "fg-faint"))
    return c
