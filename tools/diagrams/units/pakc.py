"""PAKC (aeronautical knowledge: radio) diagrams. Every call, number and order comes from content/notes/PAKC/*.md;
where a note hedges, the diagram hedges."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, arrow, circle, fmt, group, line, multiline, num, path, plane_side,
                                polygon, polyline, rect, sample, text)

SOFT = {"brand": "brand-soft", "ok": "ok-soft", "warn": "warn-soft", "bad": "bad-soft", "info": "info-soft", "sky": "sky-soft", "fg": "surface-2"}
FG = {"brand": "brand-fg", "ok": "ok-fg", "warn": "warn-fg", "bad": "bad-fg", "info": "info-fg", "sky": "sky-fg", "fg": "fg"}
EDGE = {"brand": "brand", "ok": "ok", "warn": "warn", "bad": "bad", "info": "info", "sky": "sky-fg", "fg": "line-strong"}


def card(x: float, y: float, w: float, h: float, title: str | None, lines: list[str], tone: str = "fg", size: float = 12,
         title_size: float = 14, leading: float = 1.35, pad: float = 12, anchor: str = "start", dash: str | None = None) -> str:
    """Rounded panel with a bold title and body lines in the tone's ink."""
    out = rect(x, y, w, h, SOFT[tone], EDGE[tone], SECOND, rx=8, dash=dash)
    tx = x + pad if anchor == "start" else x + w / 2
    yy = y + pad + title_size * 0.85
    if title:
        out += text(tx, yy, title, title_size, anchor, FG[tone], weight=700)
        yy += title_size * 0.5 + size * 1.05
    else:
        yy = y + pad + size * 0.9
    out += multiline(tx, yy, lines, size, anchor, FG[tone] if tone != "fg" else "fg-muted", leading)
    return out


def pill(x: float, y: float, w: float, h: float, s: str, tone: str = "brand", size: float = 13) -> str:
    """Rounded label of fixed width centred on (x, y)."""
    return rect(x - w / 2, y - h / 2, w, h, SOFT[tone], EDGE[tone], THIN, rx=h / 2) + text(x, y + size * 0.36, s, size, "middle", FG[tone], weight=700)


def small_plane(x: float, y: float, scale: float) -> str:
    """The shared side-view aeroplane with its strokes kept thin when drawn small or large."""
    k = 1 / scale
    return (plane_side(x, y, scale).replace('stroke-width="2"', f'stroke-width="{fmt(2 * k * 0.9)}"')
            .replace('stroke-width="1.25"', f'stroke-width="{fmt(1.25 * k * 0.9)}"').replace('stroke-width="1"', f'stroke-width="{fmt(k * 0.9)}"'))


def wave(x0: float, x1: float, yc: float, cycles: float, amp, color: str, width: float = SECOND, per: int = 12, phase: float = 0) -> str:
    """Sine wave from x0 to x1 about yc; amp is a number or a function of t in [0, 1]."""
    n = max(8, int(cycles * per))
    pts = []
    for i in range(n + 1):
        t = i / n
        a = amp(t) if callable(amp) else amp
        pts.append((x0 + (x1 - x0) * t, yc - a * math.sin(2 * math.pi * cycles * t + phase)))
    return polyline(pts, color, width)


# ================================================================ 3.4 the CTAF broadcast
def _call_rows(c: Canvas, top: float, rh: float, rows, cols: dict, prefix: str, focal: set[int]) -> None:
    """Numbered rows: item name, the words spoken (in a chip) and why the item is there. A highlight steps down the rows."""
    for i, (label, words, why) in enumerate(rows):
        y = top + i * rh
        tone = "brand" if i in focal else "fg"
        mid = y + (rh - 8) / 2
        c.add(circle(cols["num"], mid, 11, SOFT[tone], EDGE[tone], THIN))
        c.add(num(cols["num"], mid + 4.5, str(i + 1) if cols.get("start", 1) == 1 else (str(i) if i else "×3"), 12 if cols.get("start", 1) == 1 or i else 11, "middle", FG[tone], weight=700))
        labels = label if isinstance(label, list) else [label]
        c.add(multiline(cols["name"], mid + 4.5 - (len(labels) - 1) * 8.5, labels, 13, "start", FG[tone] if tone != "fg" else "fg", weight=700))
        c.add(rect(cols["chip"], y, cols["chip_w"], rh - 8, SOFT[tone], EDGE[tone], THIN, rx=8))
        ws = words if isinstance(words, list) else [words]
        c.add(multiline(cols["chip"] + 12, mid + 4.5 - (len(ws) - 1) * 8, ws, 12.5, "start", FG[tone] if tone != "fg" else "fg", italic=True))
        c.add(multiline(cols["why"], mid + 4 - (len(why) - 1) * 8, why, 12, "start", "fg-muted", 1.3))
    # reading highlight: steps down one row at a time while the call is "spoken"
    n = len(rows)
    c.style(f".{prefix}-read{{animation:{prefix}-read {n}s steps({n},end) infinite}}\n"
            f"@keyframes {prefix}-read{{from{{transform:translateY(0)}}to{{transform:translateY({fmt(n * rh)}px)}}}}")
    c.add(rect(cols["hl_x"], top - 4, 640 - 12 - cols["hl_x"], rh, None, "brand", MAIN, rx=10, cls=f"{prefix}-read"))


@chart
def ctaf_broadcast_anatomy() -> Canvas:
    rows = [
        ("Location", "Northam", ["which aerodrome the call", "is about"]),
        ("Traffic", "traffic,", ["addressed to all aircraft,", "not to one station"]),
        ("Type", "Cessna 172", ["what to look for, and", "how fast it will be"]),
        ("Call-sign", "Alpha Bravo Charlie,", ["who you are"]),
        ("Position", "10 miles south,", ["where you are"]),
        ("Level", "2,500,", ["how high you are"]),
        ("Intentions", "inbound, estimate circuit at 25,", ["what you will do next: the", "part others plan around"]),
        ("Location", "Northam.", ["a late listener learns which", "aerodrome: 126.7 is shared"]),
    ]
    rh, top = 46, 84
    h = top + len(rows) * rh + 44
    c = Canvas("One CTAF broadcast, eight items in a fixed order", "The inbound call from the lesson, Northam traffic, Cessna 172 Alpha Bravo "
               "Charlie, 10 miles south, 2,500, inbound, estimate circuit at 25, Northam, split into its eight items: location, traffic, type, "
               "call-sign, position, level, intentions, location. Each item has a reason beside it. The aerodrome name is said first and last "
               "because many aerodromes share one frequency, often 126.7, and a pilot who tunes in late still hears the last word.",
               height=h, prefix="cba")
    c.add(text(20, 30, "One broadcast, eight items, always in this order", 16, "start", "fg", weight=700))
    c.add(text(20, 50, "The inbound call by 10 nm at Northam (CTAF)", 12, "start", "fg-muted"))
    cols = {"num": 58, "name": 78, "chip": 172, "chip_w": 236, "why": 422, "hl_x": 42}
    c.add(text(cols["name"], top - 12, "Item", 12, "start", "fg-faint", weight=600))
    c.add(text(cols["chip"], top - 12, "What you say", 12, "start", "fg-faint", weight=600))
    c.add(text(cols["why"], top - 12, "Why it is there", 12, "start", "fg-faint", weight=600))
    _call_rows(c, top, rh, rows, cols, "cba", {0, 7})
    # bracket: the aerodrome name opens and closes the call
    y1, y2 = top + (rh - 8) / 2, top + 7 * rh + (rh - 8) / 2
    c.add(path(f"M40 {fmt(y1)} L28 {fmt(y1)} L28 {fmt(y2)} L40 {fmt(y2)}", "brand", None, MAIN))
    c.add(text(18, (y1 + y2) / 2, "the aerodrome name brackets the call", 12, "middle", "brand-fg", weight=600, rotate=-90))
    c.add(text(20, h - 16, "Plan it, listen first, say it once in this order, then release the PTT and listen again.", 12, "start", "fg-muted"))
    return c


# ================================================================ 3.5 responsibilities
@chart
def secrecy_use_vs_spread() -> Canvas:
    c = Canvas("Secrecy: use it for safety, never spread it", "You may and should listen. A message not addressed to you may be used for the "
               "safety purpose it was sent for: acting on broadcasts to all stations, avoiding traffic you hear about, and relaying a distress "
               "call that has not been answered. You may not divulge it to anyone, publish it, use it for personal gain, or record and broadcast "
               "or post it.", height=420, prefix="suv")
    c.add(text(320, 30, "You may hear it. What you do with it is the rule.", 16, "middle", "fg", weight=700))
    # the listener
    cx, cy = 320, 78
    c.add(circle(cx, cy, 22, "surface-2", "fg", MAIN))
    c.add(path(f"M{cx - 9} {cy - 8} L{cx - 3} {cy - 8} L{cx + 5} {cy - 15} L{cx + 5} {cy + 15} L{cx - 3} {cy + 8} L{cx - 9} {cy + 8} Z", "fg", "surface", SECOND))
    c.add(path(f"M{cx + 10} {cy - 7} Q{cx + 15} {cy} {cx + 10} {cy + 7}", "fg", None, SECOND))
    c.add(text(cx + 36, cy - 4, "A message on the frequency", 13, "start", "fg", weight=600))
    c.add(text(cx + 36, cy + 13, "that was not addressed to you", 12, "start", "fg-muted"))
    c.add(text(cx - 36, cy - 4, "Listening is expected:", 12, "end", "ok-fg", weight=600))
    c.add(text(cx - 36, cy + 13, "keep a listening watch", 12, "end", "ok-fg"))
    # two branches
    c.add(arrow(cx - 14, cy + 22, 170, 142, "ok", MAIN))
    c.add(arrow(cx + 14, cy + 22, 470, 142, "bad", MAIN))
    c.add(text(226, 112, "USE", 13, "end", "ok-fg", weight=700))
    c.add(text(414, 112, "SPREAD", 13, "start", "bad-fg", weight=700))
    # the line
    c.add(line(320, 132, 320, 330, "line-strong", SECOND, DASH))
    c.add(card(20, 150, 286, 180, "Use it for safety", [], "ok"))
    items_ok = [("Act on broadcasts to all stations:", "“Northam traffic …” is for you"),
                ("Avoid traffic you hear cleared", "into your area"),
                ("Relay a distress call that the", "station addressed has not answered")]
    for i, (a, b) in enumerate(items_ok):
        y = 196 + i * 44
        c.add(path(f"M34 {y - 4} L39 {y + 1} L48 {y - 9}", "ok", None, MAIN))
        c.add(text(58, y, a, 12.5, "start", "ok-fg", weight=600))
        c.add(text(58, y + 16, b, 12, "start", "ok-fg"))
    c.add(card(334, 150, 286, 180, "Spread it beyond the frequency", [], "bad"))
    items_bad = [("Divulge", "tell anyone at all"), ("Publish", "put it out to the public"),
                 ("Profit", "use it for personal gain"), ("Record and post", "or broadcast it")]
    for i, (a, b) in enumerate(items_bad):
        y = 196 + i * 34
        c.add(line(348, y - 9, 358, y + 1, "bad", MAIN), line(358, y - 9, 348, y + 1, "bad", MAIN))
        c.add(text(368, y, a, 12.5, "start", "bad-fg", weight=700))
        c.add(text(368, y + 16, b, 12, "start", "bad-fg"))
    c.add(text(163, 346, "allowed, often required", 12, "middle", "ok-fg", weight=600))
    c.add(text(477, 346, "not allowed", 12, "middle", "bad-fg", weight=600))
    c.add(rect(20, 362, 600, 44, "surface-2", None, rx=8))
    c.add(text(34, 380, "The infringement you overheard: use its traffic information while you fly;", 12, "start", "fg"))
    c.add(text(34, 397, "after landing, say nothing about it and post nothing.", 12, "start", "fg"))
    return c


@chart
def unauthorised_transmission_filter() -> Canvas:
    gates = [
        ("Necessary?", "“Thanks for the heads-up, mate”", "chat, jokes, thanks, repeated radio checks"),
        ("Clean language?", "Profane, obscene or offensive words", "the band reaches every receiver in range"),
        ("True?", "False or misleading; a false MAYDAY", "or PAN PAN is an offence"),
        ("Identified?", "“Northam traffic, turning base 23”", "no call-sign: which of three aircraft?"),
        ("Right frequency?", "Fuel truck request on CTAF or 121.5", "CTAF is for traffic, 121.5 for emergencies"),
        ("Approved radio?", "Unapproved or modified set", "can drift off frequency or interfere"),
    ]
    top, rh = 92, 62
    h = top + len(gates) * rh + 70
    c = Canvas("May I make this call?", "A call must pass six gates before you press the PTT: is it necessary, in clean language, true, "
               "identified with your call-sign, on the right frequency for its purpose, and from an approved radio? Failing any gate makes "
               "it an unauthorised transmission; the examples come from the lesson's worked example. A call that passes every gate is made "
               "once, short and in standard words.", height=h, prefix="utf")
    c.add(text(20, 30, "May I make this call? Every gate must say yes", 16, "start", "fg", weight=700))
    c.add(pill(150, 64, 220, 30, "About to press the PTT", "fg", 13))
    gx, gw, gh = 40, 220, 42
    for i, (q, ex, why) in enumerate(gates):
        y = top + i * rh
        c.add(arrow(150, y - (rh - gh) + 6 if i else 79, 150, y - 2, "ok", SECOND))
        if i:
            c.add(text(158, y - 10, "yes", 11, "start", "ok-fg", weight=600))
        c.add(rect(gx, y, gw, gh, "brand-soft", "brand", SECOND, rx=10))
        c.add(num(gx + 18, y + 26, str(i + 1), 13, "middle", "brand-fg", weight=700))
        c.add(text(gx + 36, y + 26, q, 14, "start", "brand-fg", weight=700))
        c.add(arrow(gx + gw + 4, y + gh / 2, 324, y + gh / 2, "bad", SECOND))
        c.add(text(292, y + gh / 2 - 7, "no", 11, "middle", "bad-fg", weight=600))
        c.add(rect(330, y - 2, 290, gh + 4, "bad-soft", "bad", THIN, rx=8))
        c.add(text(342, y + 16, ex, 12.5, "start", "bad-fg", weight=600))
        c.add(text(342, y + 33, why, 11.5, "start", "bad-fg"))
    yend = top + len(gates) * rh
    c.add(arrow(150, yend - (rh - gh) + 6, 150, yend + 8, "ok", SECOND))
    c.add(text(158, yend - 10, "yes to all", 11, "start", "ok-fg", weight=600))
    c.add(rect(20, yend + 10, 260, 36, "ok-soft", "ok", SECOND, rx=18))
    c.add(text(150, yend + 33, "Transmit: once, short, standard", 13, "middle", "ok-fg", weight=700))
    c.add(text(330 + 145, yend + 26, "Any “no” makes it an", 12.5, "middle", "bad-fg", weight=600))
    c.add(text(330 + 145, yend + 43, "unauthorised transmission", 12.5, "middle", "bad-fg", weight=600))
    return c


# ================================================================ 3.6 radio system components
def _block(x: float, y: float, w: float, h: float, title: str, sub: list[str], tone: str, letter: str | None = None) -> str:
    out = rect(x, y, w, h, SOFT[tone], EDGE[tone], SECOND, rx=8)
    out += text(x + 10, y + 18, title, 13, "start", FG[tone], weight=700)
    out += multiline(x + 10, y + 34, sub, 11.5, "start", FG[tone] if tone != "fg" else "fg-muted", 1.3)
    return out


@chart
def radio_system_block_diagram() -> Canvas:
    c = Canvas("How your voice reaches the tower", "Block diagram of a light-aircraft radio installation. Power: the battery and the alternator "
               "feed the main bus through the master switch; the avionics master feeds the avionics bus, and each radio has its own circuit "
               "breaker. Transmit path: microphone and press-to-talk switch, transmitter, antenna. Receive path: antenna, receiver with "
               "squelch, headset or speaker. The transmitter and receiver share one box, the COM transceiver, and one antenna.",
               height=480, prefix="rsb")
    c.add(text(20, 28, "Eight links: power, then voice out and voice back", 16, "start", "fg", weight=700))
    # power chain
    c.add(_block(20, 48, 116, 44, "Battery", ["start, reserve"], "fg", "a"))
    c.add(_block(20, 102, 116, 44, "Alternator", ["carries the load"], "fg", "a"))
    c.add(_block(168, 74, 92, 46, "Master", ["switch"], "fg", "a"))
    c.add(line(136, 70, 152, 70, "fg-muted", SECOND), line(136, 124, 152, 124, "fg-muted", SECOND), line(152, 70, 152, 124, "fg-muted", SECOND))
    c.add(arrow(152, 97, 166, 97, "fg-muted", SECOND))
    c.add(rect(280, 56, 8, 84, "fg-muted", None, rx=2))
    c.add(text(284, 152, "main bus", 11.5, "middle", "fg-muted"))
    c.add(arrow(260, 97, 278, 97, "fg-muted", SECOND))
    c.add(_block(300, 74, 140, 46, "Avionics master", ["spike protection"], "brand", "b"))
    c.add(arrow(288, 97, 298, 97, "fg-muted", SECOND))
    c.add(rect(456, 56, 8, 84, "fg-muted", None, rx=2))
    c.add(text(460, 152, "avionics bus", 11.5, "middle", "fg-muted"))
    c.add(arrow(440, 97, 454, 97, "fg-muted", SECOND))
    c.add(_block(482, 74, 138, 46, "COM 1 breaker", ["pops on overload"], "fg", "c"))
    c.add(arrow(464, 97, 480, 97, "fg-muted", SECOND))
    c.add(polyline([(549, 120), (549, 172), (335, 172), (335, 194)], "fg-muted", SECOND, arrow_end=True))
    c.add(text(560, 160, "power", 11.5, "start", "fg-muted"))
    # the transceiver
    c.add(rect(196, 196, 278, 222, "surface", "line-strong", SECOND, rx=10, dash=DASH))
    c.add(text(335, 214, "COM radio (transceiver)", 12, "middle", "fg-muted", weight=600))
    c.add(_block(214, 226, 242, 62, "Transmitter", ["carrier on the selected frequency,", "amplitude-modulated by your voice"], "brand", "e"))
    c.add(_block(214, 326, 242, 76, "Receiver", ["selects, amplifies, demodulates;", "squelch mutes the hiss when", "no signal is present"], "info", "f"))
    # microphone and headset
    c.add(_block(20, 226, 150, 62, "Microphone + PTT", ["voice → audio; PTT", "keys the transmitter"], "fg", "d"))
    c.add(arrow(170, 257, 212, 257, "brand", MAIN))
    c.add(_block(20, 334, 150, 62, "Headset / speaker", ["audio → sound;", "speaker is the back-up"], "fg", "h"))
    c.add(arrow(212, 364, 172, 364, "info", MAIN))
    # antenna
    ax = 552
    c.add(line(ax, 300, ax, 228, "fg", MAIN))
    c.add(polygon([(ax - 4, 300), (ax + 4, 300), (ax + 2, 226), (ax - 2, 226)], "fg", "fg", THIN))
    c.add(arrow(456, 257, ax - 6, 257, "brand", MAIN))
    c.add(polyline([(ax, 300), (ax, 364), (460, 364)], "info", MAIN, arrow_end=True))
    c.add(_block(496, 380, 124, 74, "Antenna", ["radiates and", "collects; one for", "TX and RX"], "fg", "g"))
    c.add(line(ax, 300, ax, 380, "fg", MAIN))
    # radio waves leaving the antenna (the one moving thing)
    arcs = "".join(path(f"M{ax + 10 + 10 * k} {228 - 8 - 6 * k} Q{ax + 18 + 12 * k} 228 {ax + 10 + 10 * k} {228 + 8 + 6 * k}", "brand", None, SECOND)
                   for k in range(3))
    c.style(".rsb-wave{animation:rsb-wave 2s ease-in-out infinite}\n@keyframes rsb-wave{0%{opacity:.15}50%{opacity:1}100%{opacity:.15}}")
    c.add(group(arcs, cls="rsb-wave"))
    c.add(text(632, 282, "to and from", 11.5, "end", "fg-muted"))
    c.add(text(632, 296, "the tower", 11.5, "end", "fg-muted"))
    # legend
    for x, tone, s in ((20, "brand", "transmit path"), (150, "info", "receive path"), (270, "fg-muted", "power")):
        c.add(line(x, 448, x + 28, 448, tone, MAIN), text(x + 36, 452, s, 12, "start", "fg-muted"))
    c.add(text(20, 472, "Any broken link sounds the same from the seat: silence.", 11.5, "start", "fg-faint"))
    return c


@chart
def am_modulation() -> Canvas:
    c = Canvas("How your voice rides on the carrier", "Three traces. The audio from the microphone is a slow wave. The transmitter's carrier "
               "is a steady radio-frequency wave on the selected frequency, for example 118.1 MHz. Amplitude modulation varies the carrier's "
               "strength in step with the audio while its frequency stays fixed; the outline of the result is the voice. Below, two stations "
               "transmitting at once on the same frequency: the two carriers clash and an AM receiver produces a squeal or garble, so listeners "
               "know a call was blocked.", height=500, prefix="amm")
    c.add(text(20, 28, "Amplitude modulation: the voice changes the carrier's strength", 16, "start", "fg", weight=700))
    x0, x1 = 196, 616
    audio = lambda t: math.sin(2 * math.pi * 2 * t)

    def label(y: float, title: str, sub: list[str], tone: str) -> None:
        c.add(text(20, y - 6, title, 13.5, "start", tone, weight=700))
        c.add(multiline(20, y + 11, sub, 11.5, "start", "fg-muted", 1.3))

    # 1 audio
    y1 = 82
    c.add(line(x0, y1, x1, y1, "line", THIN))
    c.add(wave(x0, x1, y1, 2, 26, "info", MAIN, per=40))
    label(y1, "Audio", ["your voice from the", "microphone: slow"], "info-fg")
    # 2 carrier
    y2 = 182
    c.add(line(x0, y2, x1, y2, "line", THIN))
    c.add(wave(x0, x1, y2, 26, 26, "fg-muted", SECOND, per=10))
    label(y2, "Carrier", ["steady radio wave,", "e.g. 118.1 MHz"], "fg")
    # 3 AM
    y3 = 300
    env = lambda t: 26 + 18 * audio(t)
    c.add(line(x0, y3, x1, y3, "line", THIN))
    c.add(wave(x0, x1, y3, 26, env, "brand", SECOND, per=10))
    up = [(x0 + (x1 - x0) * t, y3 - env(t)) for t in [i / 80 for i in range(81)]]
    dn = [(x, 2 * y3 - y) for x, y in up]
    c.add(polyline(up, "info", SECOND, dash=DASH), polyline(dn, "info", SECOND, dash=DASH))
    label(y3, "AM signal", ["strength follows the", "voice; frequency", "stays fixed"], "brand")
    c.add(text(x1, y3 - 52, "outline = your voice", 12, "end", "info-fg", weight=600))
    # the transmitter combines 1 and 2
    c.add(text(176, 236, "transmitter modulates", 11.5, "end", "fg-faint", italic=True))
    c.add(arrow(186, 246, 186, 262, "fg-faint", SECOND))
    # divider
    c.add(line(20, 362, 620, 362, "line-strong", THIN, DASH))
    # 4 two stations
    y4 = 428
    pts = []
    n = 320
    for i in range(n + 1):
        t = i / n
        v = 15 * math.sin(2 * math.pi * 24 * t) + 15 * math.sin(2 * math.pi * 27 * t + 0.6)
        pts.append((x0 + (x1 - x0) * t, y4 - v))
    c.add(line(x0, y4, x1, y4, "line", THIN))
    c.add(polyline(pts, "bad", SECOND))
    label(y4 - 14, "Two at once", ["two pilots press the", "PTT together: the", "carriers clash"], "bad-fg")
    c.add(text(x1, 482, "heard as a squeal or garble: the blocked call announces itself", 12, "end", "bad-fg", weight=600))
    return c


@chart
def aircraft_antenna_locations() -> Canvas:
    c = Canvas("Where the antennas are, and which is which", "Side view of a light aeroplane. A COM antenna, a blade or whip about 60 cm "
               "long (a quarter wavelength), sits on top of the fuselage, with a second COM antenna underneath, one per COM radio. The V-shaped "
               "cat's whisker NAV antenna for the VOR and ILS receivers is on the fin. Short UHF stubs underneath serve the transponder and DME.",
               height=400, prefix="aal")
    c.add(text(20, 28, "Match each antenna to its job on the walk-around", 16, "start", "fg", weight=700))
    s, X0, Y0 = 5, 425, 195
    P = lambda x, y: (X0 + s * x, Y0 + s * y)
    c.add(small_plane(X0, Y0, s))
    # COM 1 blade on the top of the fuselage, behind the wing and rear window
    bx, by = P(-31, -0.3)
    c.add(polygon([(bx - 6, by + 1), (bx + 6, by + 1), (bx - 8, by - 30), (bx - 15, by - 30)], "brand", "brand-soft", MAIN))
    # COM 2 whip under the rear fuselage (belly line)
    wx, wy = P(-28, 10.3)
    c.add(line(wx, wy, wx - 14, wy + 36, "brand", MAIN))
    # NAV cat's whisker on top of the fin (y -14.5)
    nx, ny = P(-69, -14.5)
    c.add(line(nx, ny, nx + 36, ny - 10, "info", MAIN), line(nx, ny, nx + 36, ny + 8, "info", MAIN))
    # transponder and DME stubs on the belly between the wheels
    for xx in (1, 7):
        sx, sy = P(xx, 12.7)
        c.add(line(sx, sy, sx, sy + 14, "warn", MAIN), circle(sx, sy + 16, 2.5, "warn", None))
    # callouts
    c.add(line(bx - 10, by - 32, 420, 70, "fg-muted", THIN))
    c.add(text(426, 66, "COM antenna: blade or whip", 13, "start", "brand-fg", weight=700))
    c.add(text(426, 83, "quarter-wave, about 60 cm", 12.5, "start", "brand-fg"))
    c.add(line(nx + 1, ny - 3, 139, 76, "fg-muted", THIN))
    c.add(text(20, 52, "NAV (VOR and ILS): V-shaped", 13, "start", "info-fg", weight=700))
    c.add(text(20, 69, "“cat's whisker” on the fin", 12.5, "start", "info-fg"))
    c.add(line(wx - 14, wy + 36, 150, 318, "fg-muted", THIN))
    c.add(text(20, 334, "Second COM antenna", 13, "start", "brand-fg", weight=700))
    c.add(text(20, 351, "one per COM radio", 12.5, "start", "brand-fg"))
    tx, ty = P(4, 12.7)
    c.add(line(tx, ty + 20, 470, 318, "fg-muted", THIN))
    c.add(text(620, 334, "Transponder and DME:", 13, "end", "warn-fg", weight=700))
    c.add(text(620, 351, "short UHF stubs underneath", 12.5, "end", "warn-fg"))
    c.add(text(320, 386, "Check each one: cracks, bends, a loose base or a missing whip all cut the range.", 12, "middle", "fg-muted"))
    return c


# ================================================================ 3.7 distress and urgency
@chart
def distress_message_anatomy() -> Canvas:
    rows = [
        (["Signal"], "MAYDAY MAYDAY MAYDAY", ["recognised through noise;", "clears the frequency"]),
        (["Station", "addressed"], "Melbourne Centre,", ["who you are calling; skip", "it if unknown or no time"]),
        (["Call-sign", "and type"], ["Cessna 172 Alpha Bravo Charlie,", "Alpha Bravo Charlie (×3)"], ["who you are; the type tells", "searchers what to look for"]),
        (["Nature of the", "emergency"], "engine failure,", ["what kind of help", "is needed"]),
        (["Intentions"], "forced landing in a paddock,", ["what you will do (in a forced", "landing: where you will be)"]),
        (["Position,", "level, heading"], ["8 miles north-east of Northam,", "passing 2,000, heading 230,"], ["narrows the search area"]),
        (["Other useful", "information"], "two POB.", ["POB, endurance, colour:", "useful, least essential"]),
    ]
    rh, top = 52, 84
    h = top + len(rows) * rh + 58
    c = Canvas("What goes in a MAYDAY, in order", "The lesson's engine-failure MAYDAY near Northam split into its parts in the AIP order: the signal "
               "MAYDAY three times, then the station addressed (Melbourne Centre), call-sign and type, nature of the emergency (engine failure), "
               "intentions (forced landing in a paddock), position, level and heading (8 miles north-east of Northam, passing 2,000, heading "
               "230), and other useful information (two POB). The most essential items come first in case the call is cut short. A PAN PAN "
               "message uses the same order.", height=h, prefix="dma")
    c.add(text(20, 30, "MAYDAY: who, what, what next, where, the rest", 16, "start", "fg", weight=700))
    c.add(text(20, 50, "Engine failure near Northam, on the Melbourne Centre frequency", 12, "start", "fg-muted"))
    cols = {"num": 52, "name": 72, "chip": 190, "chip_w": 240, "why": 442, "hl_x": 38, "start": 0}
    c.add(text(cols["name"], top - 12, "Item", 12, "start", "fg-faint", weight=600))
    c.add(text(cols["chip"], top - 12, "What you say", 12, "start", "fg-faint", weight=600))
    c.add(text(cols["why"], top - 12, "Why it is there", 12, "start", "fg-faint", weight=600))
    _call_rows(c, top, rh, rows, cols, "dma", {0})
    # most essential first
    c.add(arrow(22, top + 6, 22, top + len(rows) * rh - 14, "fg-muted", SECOND))
    c.add(text(14, top + len(rows) * rh / 2, "most essential first", 11.5, "middle", "fg-muted", weight=600, rotate=-90))
    y = top + len(rows) * rh + 10
    c.add(rect(20, y, 600, 40, "surface-2", None, rx=8))
    c.add(text(32, y + 17, "Then squawk 7700, fly the aeroplane, and activate the ELT as the landing becomes certain.", 12, "start", "fg"))
    c.add(text(32, y + 33, "A PAN PAN, PAN PAN, PAN PAN message uses exactly the same order.", 12, "start", "fg-muted"))
    return c


@chart
def mayday_or_pan_decision() -> Canvas:
    c = Canvas("MAYDAY or PAN PAN?", "One test separates the two calls: is the aircraft threatened by grave and imminent danger, requiring "
               "immediate assistance? Yes: distress, MAYDAY three times, absolute priority, squawk 7700; examples engine failure with a "
               "forced landing, fire or structural failure, pilot incapacitated with no other pilot, lost with fuel nearly exhausted. No, but "
               "a safety concern for the aircraft or someone on board or in sight: urgency, PAN PAN three times, priority over all except "
               "distress; examples a rough engine still producing power, lost with fuel to spare, alternator failure, sick passenger, bird "
               "strike with the aircraft controllable. Upgrade a PAN if it worsens; cancel a MAYDAY when the danger is over.",
               height=490, prefix="mpd")
    c.add(text(320, 28, "Do I need help now, or do people need to know?", 16, "middle", "fg", weight=700))
    c.add(pill(320, 60, 340, 30, "Something is wrong: fly the aeroplane first", "fg", 12.5))
    c.add(arrow(320, 76, 320, 96, "fg-muted", SECOND))
    c.add(rect(150, 98, 340, 62, "brand-soft", "brand", MAIN, rx=12))
    c.add(text(320, 122, "Grave and imminent danger,", 14, "middle", "brand-fg", weight=700))
    c.add(text(320, 142, "needing immediate assistance?", 14, "middle", "brand-fg", weight=700))
    c.add(path("M150 129 L100 129 L100 186", "bad", None, MAIN, arrow_end=True))
    c.add(text(124, 120, "YES", 12.5, "middle", "bad-fg", weight=700))
    c.add(path("M490 129 L540 129 L540 186", "warn", None, MAIN, arrow_end=True))
    c.add(text(516, 120, "NO", 12.5, "middle", "warn-fg", weight=700))
    cw, top = 290, 190
    for x, tone, head, sub, foot in ((20, "bad", "MAYDAY MAYDAY MAYDAY", "Distress: help now", "absolute priority · squawk 7700"),
                                     (330, "warn", "PAN PAN, PAN PAN, PAN PAN", "Urgency: no immediate help needed",
                                      "priority over all except distress")):
        c.add(rect(x, top, cw, 230, SOFT[tone], EDGE[tone], MAIN, rx=10))
        c.add(text(x + 14, top + 26, head, 15, "start", FG[tone], weight=700))
        c.add(text(x + 14, top + 46, sub, 12, "start", FG[tone]))
        c.add(line(x + 14, top + 58, x + cw - 14, top + 58, EDGE[tone], THIN))
        c.add(text(x + 14, top + 216, foot, 12, "start", FG[tone], weight=600))
    pairs = [("Engine failure, forced landing", "Rough engine, still giving power"),
             ("Lost, fuel nearly exhausted", "Lost, fuel to spare"),
             ("Fire or structural failure", "Alternator failure"),
             ("Pilot incapacitated, no other pilot", "Sick passenger"),
             (None, "Bird strike, still controllable")]
    for i, (a, b) in enumerate(pairs):
        y = top + 82 + i * 24
        if a:
            c.add(circle(38, y - 4, 3, "bad", None), text(48, y, a, 12.5, "start", "bad-fg"))
        c.add(circle(348, y - 4, 3, "warn", None), text(358, y, b, 12.5, "start", "warn-fg"))
        if i < 2:
            c.add(text(320, y, "↔", 13, "middle", "fg-muted"))
    c.add(text(330 + 14, top + 196, "also for an aircraft or vessel in sight", 11.5, "start", "warn-fg", italic=True))
    # upgrade and cancel
    c.add(path(f"M{330 + 60} {top + 232} Q320 {top + 272} {20 + cw - 60} {top + 232}", "bad", None, MAIN, arrow_end=True))
    c.add(text(320, top + 284, "gets worse? upgrade to MAYDAY on the same frequency · danger over? cancel distress", 12, "middle", "fg-muted", weight=600))
    return c


# ================================================================ 3.10 radio waves
EC, ER = (320, 1500), 1220                    # earth centre and radius for the curved-earth scenes
IONO_LO, IONO_HI = ER + 170, ER + 200


def _on(r: float, x: float) -> tuple[float, float]:
    """Point at horizontal position x on the circle of radius r about the earth centre."""
    return x, EC[1] - math.sqrt(r * r - (x - EC[0]) ** 2)


def _band(r0: float, r1: float, x0: float = 0, x1: float = 640) -> str:
    top = [_on(r1, x0 + (x1 - x0) * i / 40) for i in range(41)]
    bot = [_on(r0, x1 - (x1 - x0) * i / 40) for i in range(41)]
    return "M" + " L".join(f"{fmt(x)} {fmt(y)}" for x, y in top + bot) + " Z"


@chart
def radio_propagation_paths() -> Canvas:
    c = Canvas("Three paths for a radio wave", "A transmitter on the curved earth. The ground wave (LF and MF) hugs the surface and fades with "
               "distance, further over sea than over land: this is how NDBs are received. The sky wave (HF) is refracted back down by the "
               "ionosphere, about 60 to 400 km up, and reaches the ground far away, hop after hop. The space wave (VHF and UHF) travels in a "
               "straight line: it reaches an aircraft in line of sight, and a wave aimed upwards passes through the ionosphere into space.",
               height=390, prefix="rpp")
    c.add(path(_band(IONO_LO, IONO_HI), None, "sky-soft", 0))
    c.add(path(_band(IONO_LO, IONO_LO + 0.01), "sky-fg", None, THIN, DASH))
    c.add(text(382, 101, "ionosphere, 60 to 400 km up", 12, "middle", "sky-fg", weight=600))
    c.add(path(_band(ER - 300, ER), "line-strong", "surface-2", SECOND))
    tx = 150
    gx, gy = _on(ER, tx)
    top = (tx, gy - 30)
    c.add(line(tx, gy, tx, gy - 30, "fg", MAIN), polygon([(tx - 9, gy), (tx + 9, gy), (tx, gy - 18)], None, "fg", SECOND))
    # ground wave: fading dashes along the surface
    for i in range(10):
        xa, xb = tx + 12 + i * 16, tx + 22 + i * 16
        (x1_, y1_), (x2_, y2_) = _on(ER + 7, xa), _on(ER + 7, xb)
        c.add(line(x1_, y1_, x2_, y2_, "info", MAIN, opacity=fmt(1 - i * 0.09)))
    c.add(text(tx + 6, gy + 26, "Ground wave (LF, MF): follows the curve and fades;", 12.5, "start", "info-fg", weight=700))
    c.add(text(tx + 6, gy + 43, "further over sea than land. How NDBs are received.", 12, "start", "info-fg"))
    # sky wave hops
    hops = [top, _on(IONO_LO + 10, 262), _on(ER, 372), _on(IONO_LO + 10, 482), _on(ER, 592)]
    d = f"M{fmt(hops[0][0])} {fmt(hops[0][1])}"
    for a, b in zip(hops[1:], hops[2:] + [None]):
        d += f" L{fmt(a[0])} {fmt(a[1])}"
    d += f" L{fmt(hops[-1][0])} {fmt(hops[-1][1])}"
    c.add(path(d, "brand-soft", None, 4))
    c.style(".rpp-sig{stroke-dasharray:14 10;animation:rpp-sig 1.5s linear infinite}\n@keyframes rpp-sig{from{stroke-dashoffset:48}to{stroke-dashoffset:0}}")
    c.add(path(d, "brand", None, MAIN, cls="rpp-sig"))
    for p in (hops[2], hops[4]):
        c.add(circle(p[0], p[1], 4, "brand", "surface", 1.5))
    c.add(text(620, 40, "Sky wave (HF): bent back down by the", 12.5, "end", "brand", weight=700))
    c.add(text(620, 57, "ionosphere; hop after hop, thousands of km", 12, "end", "brand"))
    # space wave: to an aircraft in line of sight, and up through the ionosphere
    c.add(small_plane(84, 226, 0.6))
    c.add(arrow(top[0] - 6, top[1] - 3, 104, 232, "fg", SECOND))
    c.add(arrow(top[0] - 2, top[1] - 6, 112, 76, "fg", SECOND))
    c.add(text(20, 40, "Space wave (VHF, UHF): straight", 12.5, "start", "fg", weight=700))
    c.add(text(20, 57, "line, line of sight; passes through", 12, "start", "fg"))
    c.add(text(20, 72, "the ionosphere into space", 12, "start", "fg"))
    c.add(text(620, 376, "Not to scale. Which path dominates depends on the frequency.", 11.5, "end", "fg-muted"))
    return c


@chart
def hf_skip_zone() -> Canvas:
    c = Canvas("The HF skip zone", "An HF transmitter on the left. Its ground wave is heard by an aircraft 30 km away but fades out. Waves sent up "
               "too steeply pass through the ionosphere; shallower ones are bent back and return to earth far away, where an aircraft 1,500 km "
               "out hears the sky wave. Between the two, an aircraft 150 km away hears nothing: it is in the skip zone, too far for the ground "
               "wave and too close for the sky wave. Not to scale.", height=400, prefix="hsz")
    G = 290
    c.add(rect(0, 70, 640, 30, "sky-soft", None))
    c.add(line(0, 100, 640, 100, "sky-fg", THIN, DASH))
    c.add(text(630, 90, "ionosphere", 12, "end", "sky-fg", weight=600))
    c.add(rect(0, G, 640, 110, "surface-2", None))
    c.add(line(0, G, 640, G, "line-strong", SECOND))
    tx = 50
    c.add(line(tx, G, tx, G - 30, "fg", MAIN), polygon([(tx - 9, G), (tx + 9, G), (tx, G - 18)], None, "fg", SECOND))
    top = (tx, G - 30)
    # steep rays escape
    for ex in (118, 160):
        c.add(arrow(top[0] + 2, top[1] - 4, ex, 30, "fg-faint", SECOND, dash=DASH))
    c.add(text(176, 34, "too steep: passes through", 12, "start", "fg-muted"))
    # shallower rays refract back
    for apex, land in ((228, 400), (330, 600)):
        c.add(polyline([(top[0] + 4, top[1] - 2), (apex, 102), (land, G)], "brand", MAIN, arrow_end=True))
    # ground wave
    for i in range(8):
        c.add(line(tx + 14 + i * 14, G - 6, tx + 22 + i * 14, G - 6, "info", MAIN, opacity=fmt(1 - i * 0.11)))
    # zones
    zones = [(0, 170, "ok", "heard: ground wave"), (170, 400, "bad", "skip zone: nothing heard"), (400, 640, "ok", "heard: sky wave")]
    for x0, x1, tone, s in zones:
        c.add(rect(x0, G + 8, x1 - x0, 30, SOFT[tone], None))
        c.add(text((x0 + x1) / 2, G + 28, s, 12.5, "middle", FG[tone], weight=700))
    for x, d, s, tone in ((120, "30 km", "hears it", "ok-fg"), (290, "150 km", "silent", "bad-fg"), (520, "1,500 km", "hears it", "ok-fg")):
        c.add(small_plane(x + 10.5, 266, 0.5))          # CG 21 units ahead of mid-length
        c.add(num(x - 4, G + 58, d, 12.5, "end", "fg", weight=700))
        c.add(text(x + 4, G + 58, s, 12, "start", tone, weight=600))
    c.add(multiline(20, G + 86, ["Too far for the ground wave, too close for the sky wave.",
                                 "The first sky wave lands where the skip zone ends. Not to scale."], 12, "start", "fg-muted"))
    return c


@chart
def vhf_line_of_sight_range() -> Canvas:
    c = Canvas("VHF range against height", "Line-of-sight range to a station at sea level, range in nautical miles about 1.23 times the square "
               "root of the height in feet. 1,500 ft gives about 48 nm and 5,000 ft about 87 nm. Four times the height, 1,500 to 6,000 ft, only "
               "doubles the range, from 48 to about 95 nm. Terrain, transmitter power and antenna shielding often make the real range less.",
               height=400, prefix="vlr")
    rng = lambda hft: 1.23 * math.sqrt(hft)
    ch = Chart(c, (0, 10000), (0, 140), box=(80, 40, 600, 330), xlabel="Aircraft height (ft)", ylabel="Range to a sea-level station (nm)",
               xticks=[0, 1500, 5000, 6000, 10000], yticks=[0, 25, 50, 75, 100, 125], xfmt=lambda v: f"{int(v):,}")
    c.add(ch.axes())
    c.add(ch.area(sample(rng, 0, 10000, 80), "brand", 0.08))
    c.add(ch.curve(sample(rng, 0, 10000, 80), "brand", MAIN))
    c.add(text(ch.px(10000) - 4, ch.py(rng(10000)) - 12, "range ≈ 1.23 × √height", 13, "end", "brand", weight=700))
    # x4 height, x2 range
    c.add(line(ch.px(1500), ch.py(rng(1500)), ch.px(6000), ch.py(rng(1500)), "fg-muted", SECOND, DASH, arrow_end=True))
    c.add(text((ch.px(1500) + ch.px(6000)) / 2 + 30, ch.py(rng(1500)) - 9, "4 × the height", 12.5, "middle", "fg", weight=600))
    c.add(line(ch.px(6000), ch.py(rng(1500)), ch.px(6000), ch.py(rng(6000)) + 6, "info", SECOND, DASH, arrow_end=True))
    c.add(text(ch.px(6000) + 10, (ch.py(rng(1500)) + ch.py(rng(6000))) / 2 + 4, "only 2 × the range", 12.5, "start", "info-fg", weight=700))
    for hft, lab, dx, dy, anchor in ((5000, "5,000 ft: 87 nm", -8, -12, "end"), (6000, "6,000 ft: about 95 nm", 10, 18, "start")):
        c.add(ch.point(hft, rng(hft), "brand", 5, lab, dx=dx, dy=dy, anchor=anchor))
    px_, py_ = ch.pt(1500, rng(1500))
    c.add(ch.point(1500, rng(1500), "brand", 5))
    c.add(text(px_ + 4, py_ + 22, "1,500 ft: 48 nm", 13, "start", "brand", weight=600, cls="num"))
    # inset: a higher aeroplane sees a further radio horizon
    ix, iy, iw, ih = 432, 196, 168, 96
    c.add(rect(ix, iy, iw, ih, "surface", "line", THIN, rx=8))
    ecx, ecy, er = ix + iw / 2, iy + 330, 260
    xa, xb = ix + 8, ix + iw - 8
    ya, yb = ecy - math.sqrt(er * er - (xa - ecx) ** 2), ecy - math.sqrt(er * er - (xb - ecx) ** 2)
    c.add(path(f"M{fmt(xa)} {fmt(ya)} A{er} {er} 0 0 1 {fmt(xb)} {fmt(yb)}", "line-strong", None, SECOND))
    th = math.radians(-74)                      # tangent point on the arc, right of the top
    tx_, ty_ = ecx + er * math.cos(th), ecy + er * math.sin(th)
    dx_, dy_ = -math.sin(th), math.cos(th)      # tangent direction
    k = -118
    pxp, pyp = tx_ + k * dx_, ty_ + k * dy_
    c.add(line(pxp, pyp, tx_, ty_, "brand", SECOND, DASH))
    c.add(circle(tx_, ty_, 3, "brand", None))
    c.add(small_plane(pxp - 7, pyp - 3, 0.32))
    c.add(text(ix + iw - 10, iy + 18, "line of sight to", 11.5, "end", "fg-muted"))
    c.add(text(ix + iw - 10, iy + 32, "the radio horizon", 11.5, "end", "fg-muted"))
    c.add(text(ch.right, ch.bottom - 10, "Terrain and low power often make it less.", 11.5, "end", "fg-muted"))
    return c


@chart
def frequency_band_ladder() -> Canvas:
    rows = [
        ("UHF", "300 MHz to 3 GHz", "λ 1 m to 10 cm", 6, ["DME, GNSS, ILS glideslope,", "transponder (1,030/1,090 MHz)"], "Line of sight", "ok"),
        ("VHF", "30 to 300 MHz", "λ 10 m to 1 m", 3, ["COM 118 to 137 MHz,", "VOR and ILS 108 to 118 MHz"], "Line of sight", "ok"),
        ("HF", "3 to 30 MHz", "λ 100 m to 10 m", 1.5, ["Long-range voice: oceanic and", "remote (about 2.8 to 22 MHz)"], "Sky wave", "brand"),
        ("MF", "300 kHz to 3 MHz", "λ 1 km to 100 m", 0.75, ["NDBs (with LF, roughly", "190 to 1,750 kHz)"], "Ground wave", "info"),
    ]
    top, rh = 62, 86
    h = top + len(rows) * rh + 52
    c = Canvas("The four aviation bands", "From the top: UHF, 300 MHz to 3 GHz, wavelength 1 m to 10 cm, DME, transponder, GNSS and the ILS "
               "glideslope, line of sight. VHF, 30 to 300 MHz, 10 m to 1 m, COM 118 to 137 MHz and VOR and ILS 108 to 118 MHz, line of sight. "
               "HF, 3 to 30 MHz, 100 m to 10 m, long-range voice in oceanic and remote areas, sky wave. MF, 300 kHz to 3 MHz, 1 km to 100 m, "
               "NDBs, ground wave. Each band is ten times the one below; higher frequencies behave more like light.", height=h, prefix="fbl")
    c.add(text(20, 28, "Each band ten times higher: shorter waves, straighter paths", 16, "start", "fg", weight=700))
    c.add(text(96, 50, "Frequency, wavelength", 11.5, "start", "fg-faint", weight=600))
    c.add(text(262, 50, "Wave (not to scale)", 11.5, "start", "fg-faint", weight=600))
    c.add(text(398, 50, "Aviation use and path", 11.5, "start", "fg-faint", weight=600))
    for i, (band, f, lam, cyc, use, prop, tone) in enumerate(rows):
        y = top + i * rh
        c.add(rect(20, y, 600, rh - 8, "surface-2" if i % 2 == 0 else "surface", "line", THIN, rx=8))
        c.add(text(56, y + rh / 2 + 2, band, 20, "middle", FG[tone] if tone != "ok" else "ok-fg", weight=700))
        c.add(num(96, y + 30, f, 12.5, "start", "fg", weight=600))
        c.add(num(96, y + 50, lam, 12, "start", "fg-muted"))
        c.add(line(262, y + rh / 2 - 4, 382, y + rh / 2 - 4, "line", THIN))
        c.add(wave(262, 382, y + rh / 2 - 4, cyc, 18, EDGE[tone], MAIN, per=24))
        c.add(multiline(398, y + 22, use, 12, "start", "fg", 1.3))
        c.add(pill(398 + 54, y + 60, 108, 22, prop, tone, 12))
    # direction arrow
    c.add(arrow(240, top + len(rows) * rh - 20, 240, top + 6, "fg-muted", SECOND))
    c.add(text(232, top + len(rows) * rh / 2 - 4, "higher frequency", 11.5, "middle", "fg-muted", weight=600, rotate=-90))
    y = top + len(rows) * rh + 8
    c.add(text(20, y + 10, "Wavelength (m) = 300 ÷ frequency (MHz). Lower bands reach further but need big antennas;", 12, "start", "fg-muted"))
    c.add(text(20, y + 27, "higher bands need tiny antennas but behave like light and stop at the horizon.", 12, "start", "fg-muted"))
    return c


# ================================================================ 3.3 fault finding
def _brace(x0: float, x1: float, y: float, up: bool, color: str) -> str:
    """Square bracket spanning x0..x1 with its tips pointing towards the chain (down if up=True)."""
    d = 8 if up else -8
    return path(f"M{fmt(x0)} {fmt(y + d)} L{fmt(x0)} {fmt(y)} L{fmt(x1)} {fmt(y)} L{fmt(x1)} {fmt(y + d)}", color, None, MAIN)


@chart
def squelch_hiss_test() -> Canvas:
    c = Canvas("The hiss test", "The receive chain runs from the other station, through range and terrain and the frequency set in the active "
               "window, to the receiver, the audio panel and the headset, with power, the circuit breaker and the volume feeding the radio. "
               "Open the squelch. Hiss but no stations: the receiver, audio panel and headset work, so the fault is in front of the radio: "
               "the wrong frequency, out of range or behind terrain, or nobody talking. No hiss at all: the fault is between the radio and "
               "your ear: power, breaker, volume, audio panel selection or the headset and its plugs.", height=390, prefix="sht")
    c.add(text(20, 28, "Open the squelch: the hiss splits the chain in two", 16, "start", "fg", weight=700))
    cy, bh = 170, 52
    top = cy - bh / 2

    def box(x: float, w: float, title: str, sub: str | None, tone: str = "fg") -> None:
        c.add(rect(x, top, w, bh, SOFT[tone], EDGE[tone], SECOND, rx=8))
        c.add(text(x + w / 2, cy - (2 if sub else -4), title, 13, "middle", FG[tone], weight=700))
        if sub:
            c.add(text(x + w / 2, cy + 14, sub, 11.5, "middle", FG[tone] if tone != "fg" else "fg-muted"))

    box(20, 84, "Other", "station")
    for k in range(3):
        c.add(path(f"M{112 + 14 * k} {cy - 10} Q{120 + 14 * k} {cy} {112 + 14 * k} {cy + 10}", "fg-muted", None, SECOND))
    c.add(text(140, cy + 32, "range,", 11.5, "middle", "fg-muted"))
    c.add(text(140, cy + 46, "terrain", 11.5, "middle", "fg-muted"))
    box(170, 96, "Frequency", "active window?")
    box(290, 92, "Receiver", "squelch open", "brand")
    box(406, 96, "Audio panel", "selections")
    box(526, 94, "Headset", "plugs → you")
    for x0, x1 in ((266, 288), (382, 404), (502, 524)):
        c.add(arrow(x0, cy, x1, cy, "fg-muted", SECOND))
    c.add(rect(290, 236, 212, 34, "surface-2", "line-strong", THIN, rx=8))
    c.add(text(396, 258, "Power, breaker, volume", 12.5, "middle", "fg", weight=600))
    c.add(arrow(336, 236, 336, top + bh + 2, "fg-muted", SECOND))
    # if hiss
    c.add(_brace(290, 620, 100, True, "ok"))
    c.add(text(455, 90, "Hiss heard: all of this works", 13, "middle", "ok-fg", weight=700))
    c.add(_brace(20, 266, 100, True, "warn"))
    c.add(text(143, 72, "so the fault is out here: wrong", 12, "middle", "warn-fg", weight=600))
    c.add(text(143, 88, "frequency, range, nobody talking", 12, "middle", "warn-fg", weight=600))
    # if no hiss
    c.add(_brace(290, 620, 290, False, "bad"))
    c.add(text(455, 312, "No hiss: the fault is in here", 13, "middle", "bad-fg", weight=700))
    c.add(text(455, 330, "power, breaker, volume, audio panel, plugs", 12, "middle", "bad-fg"))
    c.add(rect(20, 286, 246, 64, "surface-2", None, rx=8))
    c.add(multiline(32, 306, ["One action halves the search.", "Then try the speaker, a spare", "headset or COM 2."], 12, "start", "fg-muted"))
    c.add(text(20, 378, "Hiss is the noise of an empty channel: proof that the receiver and audio path are alive.", 12, "start", "fg-faint"))
    return c


# ================================================================ 3.9 radiotelephone controls
@chart
def com_radio_active_standby() -> Canvas:
    c = Canvas("The COM radio face", "A typical COM radio. The display shows the active frequency, 126.700, which the radio transmits and "
               "receives on, and the standby frequency, 120.025, a scratch pad. The concentric knobs change only the standby: the outer knob "
               "whole megahertz, the inner knob kilohertz. The flip-flop button swaps standby and active. The volume knob is often the on/off "
               "switch, and pulling it opens the squelch to test for hiss. A TX indicator lights while the transmitter is keyed; lit with no "
               "PTT pressed means a stuck microphone.", height=414, prefix="cfa")
    c.add(text(20, 28, "Dial in standby, flip to active, talk on active only", 16, "start", "fg", weight=700))
    Y = 58                                             # vertical offset of the radio
    c.add(rect(30, 56 + Y, 580, 132, "surface-2", "fg", MAIN, rx=14))
    c.add(circle(92, 122 + Y, 30, "surface", "fg", MAIN), line(92, 98 + Y, 92, 110 + Y, "fg", MAIN))
    c.add(text(92, 168 + Y, "VOL · PULL SQ", 11, "middle", "fg-muted", weight=600))
    c.add(rect(150, 78 + Y, 300, 88, "surface", "line-strong", SECOND, rx=6))
    c.add(text(166, 98 + Y, "ACTIVE", 11, "start", "brand", weight=700))
    c.add(num(166, 140 + Y, "126.700", 26, "start", "brand", weight=700))
    c.add(text(436, 98 + Y, "STBY", 11, "end", "fg-muted", weight=700))
    c.add(num(436, 140 + Y, "120.025", 20, "end", "fg-muted"))
    c.add(text(166, 158 + Y, "TX", 11, "start", "fg-faint", weight=700))
    c.style(".cfa-ff{animation:cfa-ff 3s ease-in-out infinite}\n@keyframes cfa-ff{0%,60%,100%{opacity:.3}75%{opacity:1}}")
    c.add(rect(466, 104 + Y, 40, 36, "brand-soft", "brand", SECOND, rx=6))
    c.add(text(486, 128 + Y, "⇄", 18, "middle", "brand-fg", weight=700))
    c.add(group(path(f"M420 {74 + Y} Q300 {50 + Y} 190 {74 + Y}", "brand", None, SECOND, arrow_end=True), cls="cfa-ff"))
    c.add(circle(556, 122 + Y, 32, "surface", "fg", MAIN), circle(556, 122 + Y, 17, "surface-2", "fg", MAIN), line(556, 106 + Y, 556, 113 + Y, "fg", SECOND))
    c.add(text(556, 176 + Y, "MHz · kHz", 11, "middle", "fg-muted", weight=600))

    def note(x: float, y: float, px: float, py: float, lx: float, ly: float, title: str, body: list[str], tone: str = "fg") -> None:
        c.add(line(px, py, lx, ly, "fg-muted", THIN), circle(px, py, 2.5, "fg-muted", None))
        c.add(text(x, y, title, 13, "start", FG[tone] if tone != "fg" else "fg", weight=700))
        c.add(multiline(x, y + 17, body, 12, "start", "fg-muted", 1.3))
    note(20, 64, 80, 94 + Y, 60, 106, "Volume and squelch", ["often the on/off switch; pull:", "hiss = receiver and audio work"])
    note(416, 64, 486, 104 + Y, 480, 106, "Flip-flop", ["swaps standby and active; a long", "press often gives 121.5 (POH)"], "brand")
    note(150, 286, 230, 146 + Y, 200, 270, "Active", ["you transmit and receive", "on this one only"], "brand")
    note(350, 286, 400, 146 + Y, 380, 270, "Standby", ["a scratch pad: the knobs", "change only this window"])
    note(20, 366, 172, 158 + Y, 60, 350, "TX light", ["lit while keyed; lit with", "no PTT pressed = stuck mic"])
    note(470, 366, 588, 122 + Y, 560, 350, "Frequency knobs", ["outer: whole MHz", "inner: kHz"])
    return c
