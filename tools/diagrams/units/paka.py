"""PAKA (PPL aeroplane general knowledge) diagrams. Numbers come from content/notes/PAKA/*.md."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, angle_mark, arc_path, arrow, badge, callout, circle, fmt, group, line,
                                multiline, num, path, polygon, polyline, rect, smooth_path, text)


# ---------------------------------------------------------------- 3.1 take-off and landing performance
@chart
def stacked_performance_factors() -> Canvas:
    c = Canvas("Performance penalties multiply", "Take-off distance as a percentage of the chart's level, nil-wind figure. A 2 percent upslope adds "
               "about 10 percent: 110. A tailwind of 10 percent of the lift-off speed then adds about 20 percent of that already longer distance, "
               "22 more, for 132, not 130. Density height and a wet grass surface multiply the result again by amounts read from the POH.",
               height=420, prefix="spf")
    c.add(text(20, 30, "Each correction multiplies the distance the previous one produced", 16, "start", "fg", weight=700))
    ch = Chart(c, (0, 170), (0, 4), box=(220, 60, 610, 320), xlabel="Take-off distance, % of the level, nil-wind chart figure",
               xticks=[0, 50, 100, 150], yticks=[], grid=True)
    c.add(ch.axes(arrows=False))
    rows = [(3.5, "Chart figure", "level, nil wind"), (2.5, "+ 2% upslope", "rule of thumb ≈ +10%"),
            (1.5, "+ tailwind", "10% of lift-off speed ≈ +20%"), (0.5, "+ density height", "+ wet grass")]
    h = 34
    for y, lab, sub in rows:
        c.add(text(20, ch.py(y) - 2, lab, 14, "start", "fg", weight=600))
        c.add(text(20, ch.py(y) + 15, sub, 12, "start", "fg-muted"))

    def bar(y: float, x0: float, x1: float, fill: str, stroke: str, dash: str | None = None) -> str:
        return rect(ch.px(x0), ch.py(y) - h / 2, ch.px(x1) - ch.px(x0), h, fill, stroke, SECOND, dash=dash)

    # row 1: baseline
    c.add(bar(3.5, 0, 100, "surface-2", "fg-muted"))
    c.add(num(ch.px(100) + 8, ch.py(3.5) + 5, "100", 14, "start", "fg", weight=600))
    # row 2: upslope
    c.add(bar(2.5, 0, 100, "surface-2", "fg-muted"), bar(2.5, 100, 110, "warn-soft", "warn"))
    c.add(num(ch.px(110) + 8, ch.py(2.5) + 5, "110", 14, "start", "fg", weight=600))
    c.add(num(ch.px(110) + 44, ch.py(2.5) + 5, "100 × 1.10", 12, "start", "fg-muted"))
    # row 3: tailwind on top of upslope
    c.add(bar(1.5, 0, 100, "surface-2", "fg-muted"), bar(1.5, 100, 110, "warn-soft", "warn"), bar(1.5, 110, 132, "bad-soft", "bad"))
    c.add(num(ch.px(132) + 8, ch.py(1.5) + 5, "132", 15, "start", "bad", weight=700))
    c.add(num(ch.px(132) + 44, ch.py(1.5) + 5, "110 × 1.20", 12, "start", "fg-muted"))
    c.add(line(ch.px(130), ch.py(1.5) - h / 2 - 8, ch.px(130), ch.py(1.5) + h / 2 + 8, "fg", SECOND, DASH))
    c.add(line(ch.px(121), ch.py(1.5) - h / 2, ch.px(121), ch.py(2), "bad", THIN))
    c.add(text(ch.px(121) - 6, ch.py(2) + 4, "tailwind: 20% of 110 = 22, not 20", 12, "end", "bad", weight=600))
    c.add(text(ch.px(130), ch.py(1.5) + h / 2 + 22, "adding would say 130", 12, "middle", "fg-muted"))
    # row 4: the factors the POH supplies, open-ended
    c.add(bar(0.5, 0, 132, "surface-2", "fg-muted"))
    c.add(bar(0.5, 132, 166, "bad-soft", "bad", DASH))
    c.add(text((ch.px(132) + ch.px(166)) / 2, ch.py(0.5) + 5, "× ? × ?", 13, "middle", "bad", weight=700))
    c.add(multiline(ch.left + 10, ch.py(0.5) - 4, ["132 × the POH chart's density height and", "grass corrections: grows further"], 12, "start", "fg"))
    c.add(multiline(20, 390, ["Two 10% penalties are 1.1 × 1.1 = 1.21: 21%, not 20%.",
                              "The rules of thumb are approximate; the POH figures govern."], 12, "start", "fg-muted"))
    return c


@chart
def weight_limits_lowest() -> Canvas:
    c = Canvas("Which weight limit governs today", "The lesson's illustrative aeroplane: structural MTOW 1,150 kg, today's climb weight limit 1,120 kg, "
               "runway-limited weight 1,180 kg, landing-limited take-off weight 1,170 kg (MLW 1,100 plus 70 kg of fuel burn). The lowest, the climb "
               "limit of 1,120 kg, governs. A loading sheet of 1,140 kg is 20 kg over it.", height=400, prefix="wll")
    c.add(text(20, 30, "You may take off at the LOWEST of four limits", 16, "start", "fg", weight=700))
    ch = Chart(c, (1080, 1200), (0, 4), box=(250, 60, 610, 300), xlabel="Take-off weight (kg)",
               xticks=[1100, 1120, 1140, 1160, 1180, 1200], yticks=[], grid=True, xfmt=lambda v: f"{int(v):,}")
    c.add(ch.band(1120, 1200, "bad", 0.07))
    c.add(ch.axes(arrows=False))
    rows = [(3.5, "Structural MTOW", "airframe strength, fixed", 1150, "fg"),
            (2.5, "Climb weight limit", "today's pressure height and temp", 1120, "brand"),
            (1.5, "Runway-limited weight", "take-off chart, this runway", 1180, "fg"),
            (0.5, "Landing-limited weight", "MLW 1,100 + 70 kg fuel burn", 1170, "fg")]
    for y, lab, sub, w, colour in rows:
        Y = ch.py(y)
        c.add(text(20, Y - 2, lab, 14, "start", colour if colour == "brand" else "fg", weight=700 if colour == "brand" else 600))
        c.add(text(20, Y + 15, sub, 12, "start", "fg-muted"))
        c.add(line(ch.left, Y, ch.px(w), Y, colour if colour == "brand" else "line-strong", 6 if colour == "brand" else 4, cap="butt"))
        c.add(circle(ch.px(w), Y, 7, colour if colour == "brand" else "surface", colour if colour == "brand" else "fg", MAIN))
        if colour == "brand":
            c.add(num(ch.px(w), Y - 14, f"{w:,}", 14, "middle", colour, weight=700))
        else:
            c.add(num(ch.px(w) + 12, Y + 5, f"{w:,}", 14, "start", colour))
    X = ch.px(1140)
    c.add(line(X, ch.top - 6, X, ch.bottom, "bad", MAIN, DASH))
    c.add(text(X + 6, ch.top - 10, "loading sheet 1,140 kg", 12, "start", "bad", weight=600))
    c.add(arrow(ch.px(1120) + 2, ch.py(2.5) + 24, X - 2, ch.py(2.5) + 24, "bad", SECOND, both=True))
    c.add(text(X + 8, ch.py(2.5) + 29, "20 kg too heavy", 13, "start", "bad", weight=700))
    c.add(multiline(20, 364, ["The runway and the structure would allow more, but today the aeroplane could not make the",
                              "required climb gradient any heavier: offload 20 kg or wait for cooler air. (Illustrative figures.)"], 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 2.2 stall warning and autopilot
_UPPER = ((0, 0), (8, -14), (40, -16), (100, -2))
_LOWER = ((100, -2), (60, 4), (20, 8), (0, 0))
_AEROFOIL_D = "M0 0 C8 -14 40 -16 100 -2 C60 4 20 8 0 0 Z"


def _bez(p, t: float) -> tuple[float, float]:
    u = 1 - t
    return (u ** 3 * p[0][0] + 3 * u * u * t * p[1][0] + 3 * u * t * t * p[2][0] + t ** 3 * p[3][0],
            u ** 3 * p[0][1] + 3 * u * u * t * p[1][1] + 3 * u * t * t * p[2][1] + t ** 3 * p[3][1])


class _Foil:
    """Aerofoil with its nose at (x, y), leading edge on the left, pitched nose-up by `angle` degrees; maps local units (0..100) to the canvas."""

    def __init__(self, x: float, y: float, chord: float, angle: float):
        self.x, self.y, self.k, self.a = x, y, chord / 100, math.radians(angle)

    def pt(self, lx: float, ly: float) -> tuple[float, float]:
        # nose-up: the trailing edge (local +x) goes DOWN on screen, so rotate clockwise by angle
        X, Y = lx * self.k, ly * self.k
        ca, sa = math.cos(self.a), math.sin(self.a)
        return self.x + X * ca - Y * sa, self.y + X * sa + Y * ca

    def lower(self, t: float) -> tuple[float, float]:
        return self.pt(*_bez(_LOWER, t))

    def upper(self, t: float) -> tuple[float, float]:
        return self.pt(*_bez(_UPPER, t))

    def lower_frame(self, t: float) -> tuple[tuple[float, float], tuple[float, float]]:
        """Outward normal and the aft-pointing tangent of the lower surface at t (screen units)."""
        x0, y0 = self.lower(t - 0.01)
        x1, y1 = self.lower(t + 0.01)
        tx, ty = x0 - x1, y0 - y1  # t increases towards the nose, so aft is x0 - x1
        d = math.hypot(tx, ty) or 1
        tx, ty = tx / d, ty / d
        return (-ty, tx), (tx, ty)

    def draw(self, colour: str = "fg", fill: str = "surface") -> str:
        return path(_AEROFOIL_D, colour, fill, MAIN / self.k, transform=f"translate({fmt(self.x)} {fmt(self.y)}) rotate({fmt(math.degrees(self.a))}) scale({fmt(self.k)})")


def _flow_to_stag(foil: _Foil, t_stag: float, x_left: float) -> str:
    """Dividing streamline arriving horizontally at the stagnation point, plus the stagnation dot."""
    sx, sy = foil.lower(t_stag)
    return line(x_left, sy, sx - 8, sy, "sky-fg", SECOND, arrow_end=True) + circle(sx, sy, 4.5, "brand", "surface", 1.5)


def _round_nose(foil: _Foil, t_stag: float, colour: str, width: float, off: float = 7) -> str:
    """Air that leaves the stagnation point forwards, round the nose and onto the upper surface."""
    pts = [foil.lower(t) for t in [t_stag + (1 - t_stag) * i / 8 for i in range(1, 8)]] + [foil.upper(t) for t in (0.0, 0.04, 0.09, 0.15, 0.22)]
    out = []
    for i, (x, y) in enumerate(pts):
        xa, ya = pts[max(0, i - 1)]
        xb, yb = pts[min(len(pts) - 1, i + 1)]
        tx, ty = xb - xa, yb - ya
        d = math.hypot(tx, ty) or 1
        out.append((x + ty / d * off, y - tx / d * off))
    return path(smooth_path(out), colour, None, width, arrow_end=True)


@chart
def stall_warning_reed_and_vane() -> Canvas:
    c = Canvas("How the reed and vane stall warnings sense the stall", "Leading edge of a wing at a normal angle of attack and near the critical "
               "angle. As the angle increases the stagnation point, where the oncoming air stops against the wing, moves down and back under "
               "the leading edge and fast, low-pressure air whips round the nose. Reed type: the suction over the opening draws air through a "
               "reed horn in the cabin, no electrical power needed. Vane type: the vane is pushed up by air flowing forward round the leading "
               "edge, closing a microswitch that sounds a horn or lights a light; it needs the master switch on.", height=500, prefix="swr")
    c.add(text(170, 30, "Reed (pneumatic)", 16, "middle", "fg", weight=700))
    c.add(text(170, 48, "no electrical power needed", 12, "middle", "ok-fg"))
    c.add(text(490, 30, "Vane (electric)", 16, "middle", "fg", weight=700))
    c.add(text(490, 48, "needs the master switch ON", 12, "middle", "warn-fg"))
    c.add(line(320, 62, 320, 470, "line", THIN))
    c.add(line(20, 266, 620, 266, "line", THIN))
    rows = [(62, 3, 0.985, False, "Normal angle of attack", "stagnation point at the nose"),
            (266, 15, 0.82, True, "Near the critical angle", "stagnation point moves down and back")]
    for top, ang, t_stag, high, title, sub in rows:
        for col_x, kind in ((0, "reed"), (320, "vane")):
            foil = _Foil(col_x + 74, top + 72, 230, ang)
            c.add(text(col_x + 20, top + 22, title, 13, "start", "bad" if high else "fg", weight=700))
            c.add(text(col_x + 20, top + 38, sub, 12, "start", "fg-muted"))
            c.add(foil.draw())
            c.add(_flow_to_stag(foil, t_stag, col_x + 16))
            if high:
                c.add(_round_nose(foil, t_stag, "brand", MAIN))
            if kind == "reed":
                sx, sy = foil.lower(t_stag)
                c.add(line(sx - 3, sy + 5, col_x + 46, sy + 24, "fg-muted", THIN))
                c.add(text(col_x + 20, sy + 38, "stagnation point", 12, "start", "brand", weight=600))
            if kind == "reed":
                ox, oy = foil.lower(0.965)
                hx, hy = col_x + 200, top + 156
                ix, iy = foil.pt(36, -4)
                tube = [(hx, hy - 14), (ix, iy), (ox + 4, oy - 1)]
                c.add(rect(hx - 17, hy - 14, 34, 20, "surface-2", "fg", SECOND, rx=4))
                c.add(text(hx - 24, hy - 6, "reed horn", 12, "end", "fg-muted"))
                c.add(text(hx - 24, hy + 8, "in the cabin", 12, "end", "fg-muted"))
                if high:
                    c.add(polyline(tube, "brand", MAIN, arrow_end=True))
                    for r in (8, 14, 20):
                        c.add(path(arc_path(hx + 18, hy - 4, r, -40, 40), "bad", None, SECOND))
                    c.add(text(hx + 22, hy - 30, "WAIL", 13, "middle", "bad", weight=700))
                    c.add(multiline(col_x + 20, top + 186, ["low pressure at the opening sucks", "air through the reed: it sounds"], 12, "start", "brand", weight=600))
                else:
                    c.add(polyline(tube, "fg-muted", SECOND, DASH))
                    c.add(text(hx + 24, hy, "silent", 12, "start", "fg-muted"))
                    c.add(multiline(col_x + 20, top + 186, ["opening near the stagnation point:", "no suction, no sound"], 12, "start", "fg-muted"))
                c.add(circle(ox, oy, 3.5, "surface", "fg", 1.5))
            else:
                vx, vy = foil.lower(0.9)
                (nx, ny), (ax, ay) = foil.lower_frame(0.9)
                k = -1.4 if high else 0.9
                dx, dy = nx + k * ax, ny + k * ay
                d = math.hypot(dx, dy)
                L = 16
                c.add(line(vx, vy, vx + L * dx / d, vy + L * dy / d, "bad" if high else "fg", 3.5))
                c.add(circle(vx, vy, 2.5, "fg", None))
                lx, ly = col_x + 200, top + 156
                c.add(circle(lx, ly - 4, 10, "bad" if high else "surface-2", "fg", SECOND))
                c.add(text(lx - 16, ly, "horn or light", 12, "end", "fg-muted"))
                c.add(text(lx + 16, ly, "ON" if high else "off", 12, "start", "bad" if high else "fg-muted", weight=700 if high else None))
                if high:
                    c.add(multiline(col_x + 20, top + 186, ["air flowing forward round the nose", "lifts the vane: microswitch closes"], 12, "start", "brand", weight=600))
                else:
                    # local flow aft along the lower surface, below the vane
                    bx, by = foil.lower(0.8)
                    c.add(arrow(vx + nx * 26 - ax * 6, vy + ny * 26 - ay * 6, bx + nx * 26 + ax * 14, by + ny * 26 + ay * 14, "sky-fg", SECOND))
                    c.add(multiline(col_x + 20, top + 186, ["air flowing back along the lower", "surface holds the vane down"], 12, "start", "fg-muted"))
    c.add(text(320, 494, "Both trigger about 5 to 10 kt above the stall in level flight, at an angle of attack, not at a fixed speed.", 12, "middle", "fg-muted"))
    return c


def _box(x: float, y: float, w: float, h: float, title: str, lines: list[str], colour: str = "fg") -> str:
    fill = f"{colour}-soft" if colour in ("brand", "ok", "warn", "bad", "info") else "surface-2"
    out = rect(x, y, w, h, fill, colour if colour != "fg" else "fg-muted", SECOND, rx=8)
    out += text(x + w / 2, y + 22, title, 14, "middle", f"{colour}-fg" if colour in ("brand", "ok", "warn", "bad", "info") else "fg", weight=700)
    out += multiline(x + w / 2, y + 41, lines, 12, "middle", "fg-muted")
    return out


@chart
def autopilot_control_loop() -> Canvas:
    c = Canvas("The parts of an autopilot", "Sensors (attitude gyro, turn coordinator or AHRS, heading indicator, VOR or GNSS) tell the computer what the "
               "aeroplane is doing; the mode controller tells it what to hold (ROL, HDG, NAV, PIT, ALT, VS). The computer works out the correction "
               "and the servos, electric motors driving the control cables through slip clutches, move the ailerons, elevator and sometimes the trim. "
               "The aeroplane responds and the sensors see the result, closing the loop. No mode moves the throttle.", height=430, prefix="apl")
    # mode controller
    c.add(rect(190, 20, 260, 92, "surface-2", "fg-muted", SECOND, rx=8))
    c.add(text(320, 42, "Mode controller", 14, "middle", "fg", weight=700))
    c.add(text(320, 59, "what you ask it to hold", 12, "middle", "fg-muted"))
    for i, m in enumerate(("ROL", "HDG", "NAV", "PIT", "ALT", "VS")):
        c.add(badge(222 + i * 39, 88, m, "info", 11))
    # three main blocks
    c.add(_box(20, 150, 170, 112, "Sensors", ["attitude gyro, turn", "coordinator or AHRS,", "heading indicator,", "VOR or GNSS"]))
    c.add(_box(235, 160, 170, 92, "Computer", ["compares what is", "happening with what", "you selected"], "brand"))
    c.add(_box(450, 150, 170, 112, "Servos", ["electric motors on", "the control cables:", "ailerons, elevator,", "sometimes the trim"]))
    c.add(arrow(320, 114, 320, 156, "info", MAIN))
    c.add(arrow(192, 206, 231, 206, "fg", MAIN))
    c.add(arrow(407, 206, 446, 206, "brand", MAIN))
    # clutch note on the servo
    c.add(rect(452, 270, 166, 24, "warn-soft", None, rx=6))
    c.add(text(535, 286, "drives via a slip clutch", 12, "middle", "warn-fg", weight=600))
    # aeroplane and the loop
    from tools.diagrams.svg import plane_side
    c.add(plane_side(320, 350, 1.3))
    c.add(path("M535 296 C535 340 470 352 400 352", "brand", None, MAIN, arrow_end=True))
    c.add(text(470, 372, "controls move", 12, "start", "brand", weight=600))
    c.add(path("M240 352 C170 352 105 340 105 268", "fg", None, MAIN, arrow_end=True))
    c.add(text(170, 372, "aeroplane responds,", 12, "end", "fg", weight=600))
    c.add(text(170, 386, "sensors see the result", 12, "end", "fg", weight=600))
    c.add(rect(20, 398, 600, 26, "bad-soft", None, rx=6))
    c.add(text(320, 415, "No part of the loop moves the throttle: in ALT or VS you manage the airspeed.", 12, "middle", "bad-fg", weight=600))
    return c


@chart
def autopilot_overpowering_trim() -> Canvas:
    c = Canvas("Fighting an auto-trim autopilot", "Three traces against time. The autopilot holds altitude. The pilot pulls back on the control column "
               "against the servo, and the auto-trim runs nose-down to relieve the servo load. The pilot pulls harder and the trim runs further. "
               "Pitch hardly changes while the servo holds. At disconnect the full nose-down trim and the pilot's pull are suddenly unopposed "
               "by the servo and the aeroplane pitches sharply, possibly towards the ground.", height=460, prefix="apt")
    c.add(text(20, 28, "Pull against it and it trims against you", 16, "start", "fg", weight=700))
    L, R = 150, 610
    t_dis = 0.78

    def tx(t: float) -> float:
        return L + t * (R - L)

    panels = [(52, "Your pull on", "the column", "info"), (172, "Auto-trim", "position", "warn"), (292, "Pitch", "attitude", "fg")]
    for top, a, b, colour in panels:
        c.add(line(L, top + 90, R, top + 90, "fg-muted", SECOND, cap="butt"))
        c.add(line(L, top, L, top + 90, "fg-muted", SECOND, cap="butt"))
        c.add(text(20, top + 40, a, 13, "start", colour if colour != "fg" else "fg", weight=700))
        c.add(text(20, top + 56, b, 13, "start", colour if colour != "fg" else "fg", weight=700))
    c.add(rect(tx(t_dis), 44, R - tx(t_dis), 346, "bad", None, fill_opacity=0.08))
    c.add(line(tx(t_dis), 44, tx(t_dis), 392, "bad", SECOND, DASH))
    c.add(text(tx(t_dis) + 6, 410, "disconnect", 13, "start", "bad", weight=700))
    # pull: zero, ramps up in two steps, held to disconnect
    top = 52
    pull = [(0, 0.05), (0.12, 0.05), (0.2, 0.35), (0.38, 0.4), (0.48, 0.7), (0.62, 0.78), (t_dis, 0.8)]
    c.add(polyline([(tx(t), top + 90 - v * 80) for t, v in pull], "info", MAIN))
    c.add(text(tx(0.2) + 8, top + 90 - 0.35 * 80 + 22, "you pull", 12, "start", "info", weight=600))
    c.add(text(tx(0.48) + 8, top + 12, "you pull harder", 12, "start", "info", weight=600))
    c.add(polyline([(tx(t_dis), top + 90 - 0.8 * 80), (tx(t_dis) + 14, top + 90 - 0.8 * 80)], "info", MAIN, DASH))
    # trim: neutral then runs nose-down after each pull
    top = 172
    c.add(text(L - 8, top + 14, "nose up", 11, "end", "fg-faint"))
    c.add(text(L - 8, top + 86, "nose down", 11, "end", "fg-faint"))
    c.add(line(L, top + 30, R, top + 30, "line", THIN, DASH))
    trim = [(0, 30), (0.24, 30), (0.34, 52), (0.5, 54), (0.62, 78), (t_dis, 82), (1, 82)]
    c.add(polyline([(tx(t), top + v) for t, v in trim], "warn", MAIN))
    c.add(text(tx(0.35) + 6, top + 48, "trims nose-down", 12, "start", "warn-fg", weight=600))
    c.add(text(tx(0.55) - 4, top + 80, "and further", 12, "end", "warn-fg", weight=600))
    c.add(text(tx(t_dis) + 8, top + 52, "still wound", 12, "start", "warn-fg", weight=600))
    c.add(text(tx(t_dis) + 8, top + 66, "nose-down", 12, "start", "warn-fg", weight=600))
    # pitch: held by the servo, then a sharp upset
    top = 292
    c.add(line(L, top + 30, R, top + 30, "line", THIN, DASH))
    pitch = [(0, 30), (0.2, 28), (0.3, 30), (0.48, 27), (0.58, 30), (t_dis, 30)]
    c.add(polyline([(tx(t), top + v) for t, v in pitch], "ok", MAIN))
    c.add(text(tx(0.05), top + 18, "servo holds the attitude: it all feels normal", 12, "start", "ok-fg", weight=600))
    c.add(path(f"M{fmt(tx(t_dis))} {top + 30} C{fmt(tx(t_dis) + 20)} {top + 32} {fmt(tx(t_dis) + 26)} {top + 70} {fmt(tx(t_dis) + 44)} {top + 86}", "bad", None, 3))
    c.add(multiline(tx(t_dis) + 50, top + 52, ["sharp pitch", "upset"], 12, "start", "bad", weight=700))
    c.add(text(L, 410, "time →", 12, "start", "fg-muted"))
    c.add(rect(20, 424, 600, 28, "ok-soft", None, rx=6))
    c.add(text(320, 443, "Unexpected behaviour? A/P DISC first, hold on firmly, then fly and retrim by hand.", 12, "middle", "ok-fg", weight=600))
    return c


# ---------------------------------------------------------------- 2.1 propellers
def _blade_section(cx: float, cy: float, chord: float, blade_angle: float, colour: str = "fg", fill: str = "surface") -> str:
    """Blade section centred on (cx, cy), moving to the right (rotation) and up the page (forward): leading edge on the right,
    camber facing forward (up), chord at blade_angle above the plane of rotation."""
    a = math.radians(blade_angle)
    foil = _Foil(-chord / 2 * math.cos(a), -chord / 2 * math.sin(a), chord, blade_angle)
    return group(foil.draw(colour, fill), transform=f"translate({fmt(cx)} {fmt(cy)}) scale(-1 1)")


@chart
def propeller_blade_twist() -> Canvas:
    c = Canvas("Why a propeller blade is twisted", "Three sections of one blade at the same forward speed, 80 knots. Near the hub the section moves "
               "round slowly, so its helical path is steep and the blade angle is large. Three-quarters out it moves round at about 345 knots at "
               "2,400 RPM: helix angle 13 degrees, blade angle 21 degrees, angle of attack 8. Near the tip it moves fastest, the helical path is "
               "flattest and the blade angle smallest. The twist keeps each section at a sensible angle of attack.", height=470, prefix="pbt")
    c.add(text(20, 28, "Faster round towards the tip, so less blade angle", 16, "start", "fg", weight=700))
    c.add(text(20, 48, "Each section moves right (round) and up the page (forward, 80 kt). Coloured line: the helical path.", 12, "start", "fg-muted"))
    V, k = 80, 0.4
    rows = [(140, "Near the hub", ["slow round, steep path", "large blade angle"], 153, None),
            (270, "Three-quarters out", ["345 kt at 2,400 RPM", "21° − 13° = 8°"], 345, (21, 13)),
            (400, "Near the tip", ["fast round, flat path", "small blade angle"], 460, None)]
    for y, title, sub, u, nums in rows:
        phi = math.degrees(math.atan(V / u))
        theta = phi + 8
        cx = 270
        c.add(text(20, y - 14, title, 14, "start", "fg", weight=700))
        c.add(multiline(20, y + 4, sub, 12, "start", "brand" if nums else "fg-muted", weight=600 if nums else None))
        # plane of rotation, helical path and chord through the section centre
        c.add(line(cx - 90, y, cx + 120, y, "line-strong", THIN, DASH))
        hp = math.radians(phi)
        th = math.radians(theta)
        c.add(line(cx - 70 * math.cos(hp), y + 70 * math.sin(hp), cx + 125 * math.cos(hp), y - 125 * math.sin(hp), "info", SECOND))
        c.add(line(cx - 60 * math.cos(th), y + 60 * math.sin(th), cx + 125 * math.cos(th), y - 125 * math.sin(th), "fg", THIN))
        c.add(_blade_section(cx, y, 92, theta))
        c.add(path(arc_path(cx, y, 112, -theta, -phi), "brand", None, 3))
        c.add(text(cx + 128 * math.cos(math.radians((theta + phi) / 2)) + 4, y - 128 * math.sin(math.radians((theta + phi) / 2)) + 5, "AoA", 12, "start", "brand", weight=700))
        # velocity triangle
        x0 = 410
        c.add(arrow(x0, y + 20, x0 + u * k, y + 20, "fg-muted", SECOND))
        c.add(arrow(x0 + u * k, y + 20, x0 + u * k, y + 20 - V * k, "fg-muted", SECOND))
        c.add(line(x0, y + 20, x0 + u * k, y + 20 - V * k, "info", MAIN))
        c.add(text(x0, y + 38, "round" + (": 345 kt" if nums else ""), 12, "start", "fg-muted"))
        c.add(text(x0 + u * k + 6, y + 20 - V * k / 2 + 4, "80 kt", 12, "start", "fg-muted"))
        c.add(path(arc_path(x0, y + 20, 36, -phi, 0), "info", None, SECOND))
        if nums:
            c.add(text(x0 - 6, y + 24, "13°", 12, "end", "info", weight=600))
    c.add(text(320, 458, "Sight along a blade on the pre-flight: steep near the hub, nearly flat at the tip.", 12, "middle", "fg-muted"))
    return c


@chart
def constant_speed_governor() -> Canvas:
    c = Canvas("How a constant-speed governor holds the RPM", "Schematic of a governor reacting to a rise in RPM as the aeroplane speeds up in "
               "a descent. 1: the engine-driven flyweights swing outwards. 2: they lift the pilot valve against the speeder spring, whose force "
               "the propeller lever sets. 3: oil, boosted by the governor pump, flows to the piston in the propeller hub. 4: the blades turn to a "
               "coarser angle, the angle of attack and the load are restored and the RPM returns to the setting.", height=450, prefix="csg")
    c.add(text(20, 28, "RPM starts to rise: the governor coarsens the blades", 16, "start", "fg", weight=700))
    # governor body
    c.add(rect(60, 60, 250, 330, "surface-2", "fg-muted", SECOND, rx=12))
    c.add(text(74, 82, "Governor", 14, "start", "fg", weight=700))
    X = 185
    # propeller lever and speeder spring
    c.add(line(X, 96, X, 110, "fg", MAIN))
    c.add(rect(X - 30, 92, 60, 8, "fg-muted", None, rx=2))
    zig = [(X, 110)] + [(X + (12 if i % 2 else -12), 116 + i * 7) for i in range(7)] + [(X, 168)]
    c.add(polyline(zig, "fg", MAIN))
    c.add(text(X + 26, 146, "speeder", 12, "start", "fg"))
    c.add(text(X + 26, 160, "spring", 12, "start", "fg"))
    c.add(multiline(74, 112, ["propeller", "lever sets", "the force"], 12, "start", "info", weight=600))
    # pilot valve: sleeve, spool lifted
    c.add(rect(X - 18, 168, 36, 92, "surface", "fg", SECOND, rx=3))
    c.add(rect(X - 14, 172, 28, 14, "brand-soft", "brand", SECOND))
    c.add(rect(X - 14, 214, 28, 14, "brand-soft", "brand", SECOND))
    c.add(line(X, 186, X, 270, "brand", 3))
    c.add(arrow(X - 30, 222, X - 30, 194, "brand", MAIN))
    c.add(text(X - 36, 206, "valve", 12, "end", "brand", weight=600))
    c.add(text(X - 36, 220, "lifts", 12, "end", "brand", weight=600))
    # flyweights, swung outwards
    c.add(rect(X - 60, 300, 120, 10, "fg-muted", None, rx=2))
    c.add(line(X, 310, X, 384, "fg", 4))
    for sgn in (-1, 1):
        px, py = X + sgn * 40, 300
        wx, wy = X + sgn * 62, 252
        c.add(line(px, py, wx, wy, "fg", 3))
        c.add(line(px, py, X + sgn * 6, 272, "fg", 3))
        c.add(circle(wx, wy, 11, "brand", "fg", SECOND))
        c.add(circle(px, py, 3, "fg", None))
        c.add(arrow(wx + sgn * 14, wy + 4, wx + sgn * 30, wy - 2, "brand", SECOND))
    c.add(text(X, 404, "driven by the engine: faster RPM, further out", 12, "middle", "fg-muted"))
    # oil: pump in, line to the hub
    c.add(text(74, 360, "engine oil,", 12, "start", "fg-muted"))
    c.add(text(74, 374, "pump boosts it", 12, "start", "fg-muted"))
    c.add(polyline([(100, 340), (100, 236), (X - 18, 236)], "warn", MAIN, arrow_end=True))
    c.add(polyline([(X + 18, 200), (450, 200), (450, 160)], "warn", 3, arrow_end=True))
    c.add(text(330, 192, "oil to the hub", 12, "middle", "warn-fg", weight=600))
    # propeller hub with piston and a blade turning coarser
    c.add(rect(400, 70, 120, 84, "surface-2", "fg", SECOND, rx=8))
    c.add(rect(414, 96, 60, 34, "warn-soft", "warn", SECOND))
    c.add(rect(474, 92, 10, 42, "fg-muted", None))
    c.add(arrow(440, 113, 470, 113, "warn", MAIN))
    c.add(text(460, 86, "hub piston", 12, "middle", "fg"))
    c.add(_blade_section(560, 230, 90, 32, "brand", "brand-soft"))
    c.add(_blade_section(560, 230, 90, 18, "fg-muted", "none"))
    c.add(path(arc_path(560, 230, 60, -14, -30), "brand", None, MAIN, arrow_end=True))
    c.add(text(560, 290, "blade turns", 12, "middle", "brand", weight=700))
    c.add(text(560, 304, "coarser", 12, "middle", "brand", weight=700))
    c.add(line(484, 113, 545, 205, "fg-muted", SECOND, DASH))
    # numbered sequence
    steps = ["1  RPM rises: flyweights swing out", "2  they lift the pilot valve against the spring", "3  oil flows to the hub piston",
             "4  blades go coarser: angle of attack and load restored, RPM back to the setting"]
    c.add(multiline(330, 330, steps[:3], 12, "start", "fg", leading=1.5))
    c.add(rect(20, 414, 600, 28, "brand-soft", None, rx=6))
    c.add(text(320, 433, steps[3], 12, "middle", "brand-fg", weight=600))
    return c
