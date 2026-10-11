"""RFRC and RMTC diagrams from the 2026-10-10 visualisation push. Every figure and rule comes from the notes in
content/notes/RFRC/ and content/notes/RMTC/; sample entries (dates, registrations) are placeholders."""
from __future__ import annotations

from tools.diagrams.charts import chart
from tools.diagrams.svg import SECOND, THIN, Canvas, multiline, rect, text

SOFT = {"brand": "brand-soft", "info": "info-soft", "ok": "ok-soft", "warn": "warn-soft", "fg": "surface-2"}
INK = {"brand": "brand-fg", "info": "info-fg", "ok": "ok-fg", "warn": "warn-fg", "fg": "fg"}
EDGE = {"brand": "brand", "info": "info", "ok": "ok", "warn": "warn", "fg": "line-strong"}


# ================================================================ RFRC 2.1 Documentation
@chart
def logbook_entry_anatomy() -> Canvas:
    c = Canvas("What a logbook entry must show",
               "One logbook entry for a one-hour solo flight of circuits and steep turns at Jandakot, split into the six questions "
               "someone checking your experience would ask: when (the date), in what (aircraft type and registration), who was in "
               "charge (the pilot in command and your role), where (departure and arrival, or the route), how long and of what kind "
               "(flight time split day and night, single or multi-engine, dual, solo and in command, with instrument and simulator time), "
               "and what was signed off (the nature of the flight and any flight test, flight review or endorsement). Each card gives the "
               "reason the column exists. A footer contrasts the logbook, which tracks the pilot, with the maintenance release, which "
               "tracks the aircraft.", height=484, prefix="lea")
    c.add(text(320, 28, "One flight, six questions: what each logbook entry shows", 16, "middle", "fg", weight=700))
    c.add(text(320, 48, "the lesson's Sunday at Jandakot: 1.0 hour of circuits and steep turns, flown solo in command", 12, "middle", "fg-muted"))
    cards = [
        ("When?", "date", "Sunday (today)", ["write it as soon as", "practicable, normally", "the same day"], "fg"),
        ("In what?", "type and registration", "C152  VH-XXX", ["endorsements and class", "ratings depend on what", "you actually flew"], "fg"),
        ("Who was in charge?", "pilot in command, your role", "SELF  in command", ["your role: in command,", "dual, or in command", "under supervision"], "fg"),
        ("Where?", "departure, arrival or route", "Jandakot – Jandakot", ["proves your cross-", "country time is real"], "fg"),
        ("How long, what kind?", "day/night, SE/ME, dual/solo", "1.0 day SE command", ["licences need a minimum", "of dual and of solo; a", "night rating, night hours"], "brand"),
        ("Signed off?", "nature of flight, any test", "circuits, steep turns", ["proves your flight", "review and endorsements", "were signed off"], "fg"),
    ]
    W, H, gx, gy, x0, y0 = 196, 156, 14, 14, 13, 66
    for i, (q, col_name, entry, why, tone) in enumerate(cards):
        x = x0 + (i % 3) * (W + gx)
        y = y0 + (i // 3) * (H + gy)
        c.add(rect(x, y, W, H, SOFT[tone], EDGE[tone], SECOND if tone == "fg" else 2, rx=10))
        c.add(text(x + 12, y + 24, q, 15, "start", INK[tone], weight=700))
        c.add(text(x + 12, y + 44, col_name, 12, "start", "fg-muted"))
        # the entry itself, as written in the logbook
        c.add(rect(x + 10, y + 54, W - 20, 30, "surface", "line-strong", THIN, rx=6))
        c.add(text(x + W / 2, y + 74, entry, 12.5, "middle", "fg", weight=600, cls="num"))
        c.add(multiline(x + 12, y + 104, why, 12, "start", "fg-muted", leading=1.3))
    fy = y0 + 2 * H + gy + 16
    c.add(rect(13, fy, 304, 46, "brand-soft", "brand", SECOND, rx=10))
    c.add(text(165, fy + 20, "Logbook: tracks you", 14, "middle", "brand-fg", weight=700))
    c.add(text(165, fy + 37, "evidence of your experience", 12, "middle", "brand-fg"))
    c.add(rect(323, fy, 304, 46, "surface-2", "line-strong", SECOND, rx=10))
    c.add(text(475, fy + 20, "Maintenance release: the aircraft", 14, "middle", "fg", weight=700))
    c.add(text(475, fy + 37, "its hours in service, its defects", 12, "middle", "fg-muted"))
    c.add(text(320, fy + 66, "Falsifying a logbook is an offence: someone else relies on it.", 12, "middle", "fg-muted"))
    return c
