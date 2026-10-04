"""RBKA (aeroplane aerodynamics and performance) diagrams. Numbers come from content/notes/RBKA/*.md."""
from __future__ import annotations

import math

from tools.diagrams.charts import chart, cl_curve
from tools.diagrams.svg import (DASH, MAIN, SECOND, THIN, Canvas, Chart, aerofoil, angle_mark, arc_path, arrow, badge, callout, circle, ellipse, fmt,
                                group, line, multiline, num, path, plane_rear, plane_side, plane_top, polygon, polyline, rect, runway, sample,
                                smooth_path, text)


# ---------------------------------------------------------------- 2.1 piston engine
@chart
def carburettor_heat_decision() -> Canvas:
    c = Canvas("Carburettor heat: ice or no ice?", "Two RPM traces after full carburettor heat is applied. With ice present (the note's example) "
               "the RPM, already crept from 2400 to 2300, falls to 2200, the engine runs rough briefly, the RPM rises to 2350 as the ice melts, "
               "and on returning to cold it settles at 2400, higher than before. With no ice the RPM drops slightly, stays there, and returns "
               "to the original value on cold.", height=470, prefix="chd")
    c.add(text(20, 28, "Apply FULL carb heat and watch the tachometer", 16, "start", "fg", weight=700))

    def panel(top: float, title: str, colour: str, pts, heat_on: float, heat_off: float, notes):
        ch = Chart(c, (0, 60), (2150, 2450), box=(80, top, 610, top + 140), ylabel=None, yticks=[2200, 2300, 2400], xticks=[], grid=True)
        c.add(rect(ch.px(heat_on), top, ch.px(heat_off) - ch.px(heat_on), 140, "warn-soft", None))
        c.add(text(ch.px(heat_off) - 8, top + 132, "carb heat ON", 11, "end", "warn-fg", weight=600))
        c.add(ch.axes(arrows=False))
        c.add(text(80, top - 12, title, 14, "start", colour, weight=700))
        c.add(text(26, top + 74, "RPM", 12, "middle", "fg-muted", weight=600, rotate=-90))
        c.add(path("M" + " L".join(f"{fmt(ch.px(x))} {fmt(ch.py(y))}" for x, y in pts), colour, None, MAIN))
        for x, y, dx, dy, lines, col_ in notes:
            c.add(ch.callout(x, y, dx, dy, lines, col_, 12))
        return ch

    # ice present: the note's worked example
    ice = [(0, 2400), (4, 2385), (8, 2340), (12, 2300), (13, 2300), (14.5, 2200), (16, 2215), (17, 2190), (18, 2225), (19, 2195), (20, 2230), (21, 2205),
           (23, 2260), (27, 2330), (30, 2350), (45, 2350), (47, 2400), (60, 2400)]
    panel(70, "Ice present", "brand", ice, 13, 46, [
        (6, 2365, 20, -28, ["RPM creeps 2400 → 2300", "(ice forming)"], "fg"),
        (14.5, 2200, -22, 0, ["drops", "to 2200"], "fg"),
        (19, 2225, 60, -8, ["runs rough: melted", "ice passing through"], "fg"),
        (36, 2350, 0, -32, ["rises to 2350", "as the ice melts"], "fg"),
        (52, 2400, -4, 36, ["cold: 2400,", "HIGHER than before"], "brand")])
    # no ice
    clean = [(0, 2300), (13, 2300), (14.5, 2265), (45, 2265), (47, 2300), (60, 2300)]
    panel(280, "No ice", "info", clean, 13, 46, [
        (24, 2265, 0, -34, ["drops slightly", "and stays there"], "fg"),
        (52, 2300, -4, -40, ["cold: back to", "the original value"], "info")])
    c.add(text(345, 446, "time →", 12, "middle", "fg-muted"))
    c.add(text(20, 462, "Rough running when heat goes on means it is working: leave it on. Use full heat, not partial.", 12, "start", "fg-muted"))
    return c


@chart
def leaning_by_rpm() -> Canvas:
    c = Canvas("Leaning by RPM with a fixed-pitch propeller", "As the mixture is leaned in cruise the RPM rises from 2350 to a peak of 2400, then falls to "
               "2370 and the engine roughens. The pilot enriches back to the peak and then slightly richer, as the note's worked example describes.",
               height=394, prefix="lbr")

    def rpm(m: float) -> float:
        return 2400 - 50 * ((m - 0.6) / 0.6) ** 2 if m <= 0.6 else 2400 - 30 * ((m - 0.6) / 0.2) ** 2

    ch = Chart(c, (0, 1), (2320, 2420), box=(80, 50, 600, 300), xlabel="Mixture control: full rich  →  lean", ylabel="RPM",
               yticks=[2350, 2370, 2400], xticks=[])
    c.add(ch.band(0.78, 1, "bad", 0.10))
    c.add(ch.axes())
    c.add(text(ch.px(0.89), ch.py(2414), "too lean:", 12, "middle", "bad", weight=600))
    c.add(text(ch.px(0.89), ch.py(2414) + 15, "rough, power loss", 12, "middle", "bad"))
    pts = sample(rpm, 0, 0.9, 60)
    c.add(ch.curve(pts, "brand", MAIN))
    c.add(ch.point(0, 2350, "fg", 5))
    c.add(ch.callout(0, 2350, 40, 26, ["1  Full rich in cruise: 2350"], "fg", 12))
    c.add(ch.point(0.6, 2400, "brand", 5))
    c.add(ch.callout(0.6, 2400, -10, -26, ["2  Lean slowly: RPM rises to a peak, 2400"], "brand", 12))
    c.add(ch.point(0.8, 2370, "bad", 5))
    c.add(ch.callout(0.8, 2370, 30, -40, ["3  Falls to 2370,", "engine rough"], "bad", 12))
    c.add(ch.point(0.55, 2399.3, "ok", 6))
    c.add(ch.callout(0.55, 2399.3, -6, 84, ["4  Enrich back to the peak,", "then a little richer (POH)"], "ok", 12))
    c.add(arrow(ch.px(0.1), ch.py(2368) - 22, ch.px(0.4), ch.py(2396) - 22, "fg-muted", SECOND))
    c.add(text((ch.px(0.1) + ch.px(0.4)) / 2 - 12, (ch.py(2368) + ch.py(2396)) / 2 - 30, "leaning", 12, "end", "fg-muted"))
    c.add(multiline(20, 362, ["Climbing makes the mixture richer (less air, same fuel): lean in the cruise, enrich in the",
                              "descent, full rich before landing. Re-lean after any big change of power or altitude."], 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 3.1 lift and drag
def _aoa_for_cl(cl: float) -> float:
    lo, hi = -2.0, 16.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if cl_curve(mid) < cl:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


@chart
def best_ld_and_critical_angle_speeds() -> Canvas:
    c = Canvas("Two angles of attack, two speeds, at two weights", "Angle of attack needed for level flight against airspeed, at maximum weight and at a "
               "lighter weight. The best lift/drag angle of about 4 degrees gives the best glide speed: 70 knots at maximum weight, about 63 knots "
               "lighter. The critical angle of about 16 degrees gives the stall speed, which is also lower when lighter. The angles stay the same.",
               height=360, prefix="bls")
    k_heavy, k_light = 0.6 * 70 ** 2, 0.6 * 63 ** 2          # CL = k / V^2, calibrated on the note's 70 and 63 kt at 4 degrees
    vs_h, vs_l = math.sqrt(k_heavy / 1.5), math.sqrt(k_light / 1.5)
    ch = Chart(c, (34, 100), (0, 20), box=(80, 40, 520, 310), xlabel="Indicated airspeed (kt)", ylabel="Angle of attack for level flight",
               xticks=[63, 70], yticks=[4, 16], yfmt=lambda v: f"{int(v)}°")
    c.add(ch.axes())
    c.add(ch.hline(16, "bad", DASH))
    c.add(ch.hline(4, "ok", DASH))
    c.add(text(ch.right, ch.py(16) - 8, "critical angle ≈ 16°  →  stall speed", 13, "end", "bad", weight=600))
    c.add(multiline(ch.left + 10, ch.py(4) + 20, ["best L/D ≈ 4°", "→ best glide speed"], 12, "start", "ok-fg", weight=600))
    for k, vs, colour, lab, dy in ((k_heavy, vs_h, "brand", "max weight", 0), (k_light, vs_l, "info", "lighter", 4)):
        pts = [(v, _aoa_for_cl(k / v ** 2)) for v in [vs + (96 - vs) * i / 60 for i in range(61)]]
        c.add(ch.curve(pts, colour, MAIN))
        c.add(text(ch.px(96) + 8, ch.py(pts[-1][1]) + dy, lab, 13, "start", colour, weight=600))
        c.add(ch.point(vs, 16, colour, 5))
    vb_h, vb_l = 70, 63
    c.add(ch.guide(vb_h, 4), ch.guide(vb_l, 4))
    c.add(ch.point(vb_h, 4, "brand", 5.5), ch.point(vb_l, 4, "info", 5.5))
    c.add(ch.callout(vs_h, 16, 26, 40, ["stall speed,", "maximum weight"], "brand", 12))
    c.add(ch.callout(vs_l, 16, -2, 66, ["stall speed,", "lighter"], "info", 12))
    c.add(rect(296, 100, 224, 64, "brand-soft", None, rx=8))
    c.add(multiline(308, 122, ["Lighter: each angle comes at a", "lower IAS. Best glide 70 kt →", "about 63 kt. Angles unchanged."], 12, "start", "brand-fg"))
    return c


def _cl_flap(a: float) -> float:
    """Flap-down lift curve: shifted up (more camber), CL max about 1.9 at a slightly lower critical angle."""
    if a <= 10.5:
        return 0.1 * (a + 6)
    if a <= 14.5:
        t = (a - 10.5) / 4
        return 1.65 + 0.25 * (1 - (1 - t) ** 2)
    return 1.9 - 0.07 * (a - 14.5) ** 1.35


@chart
def flap_effect_on_lift_curve() -> Canvas:
    c = Canvas("What flap does to the lift curve", "Lift coefficient against angle of attack with flap up and flap down. With flap down the curve is higher at "
               "every angle, the maximum lift coefficient is higher so the stall speed is lower, the same lift comes at a smaller angle of attack so "
               "the nose attitude is lower, and the critical angle is slightly lower. Drag also increases.", height=400, prefix="fel")
    ch = Chart(c, (-6, 21), (0, 2.2), box=(70, 40, 470, 330), xlabel="Angle of attack (degrees)", ylabel="Lift coefficient  CL",
               xticks=[-4, 0, 4, 8, 12, 16, 20], yticks=[0.5, 1.0, 1.5, 2.0], xfmt=lambda v: f"{int(v)}°")
    c.add(ch.axes())
    clean = sample(cl_curve, -2, 20, 80)
    flap = sample(_cl_flap, -5.5, 19, 80)
    c.add(ch.curve(clean, "fg-muted", MAIN))
    c.add(ch.curve(flap, "brand", MAIN))
    c.add(text(ch.px(17.5), ch.py(1.18), "flap up", 13, "middle", "fg-muted", weight=600))
    c.add(text(ch.px(14.5), ch.py(1.9) - 12, "flap down", 13, "middle", "brand", weight=700))
    c.add(ch.point(16, 1.5, "fg-muted", 4.5), ch.point(14.5, 1.9, "brand", 5))
    # same CL at a smaller angle
    a_clean, a_flap = 8, 4
    c.add(ch.hline(1.0, "fg-faint", DASH, x_to=a_clean))
    c.add(line(ch.px(a_flap), ch.py(1.0), ch.px(a_flap), ch.bottom, "brand", THIN, DASH))
    c.add(line(ch.px(a_clean), ch.py(1.0), ch.px(a_clean), ch.bottom, "fg-muted", THIN, DASH))
    c.add(arrow(ch.px(a_clean) - 3, ch.py(0.3), ch.px(a_flap) + 3, ch.py(0.3), "brand", SECOND))
    c.add(text(ch.px(6), ch.py(0.3) + 18, "smaller angle", 11, "middle", "brand"))
    # side panel: the effects
    x0 = 488
    items = [("Lift at the same angle", "more", "brand-fg"), ("CL max", "higher", "brand-fg"), ("Stall speed", "lower", "ok-fg"),
             ("Same lift comes at", "a smaller angle", "brand-fg"), ("so the nose attitude is", "lower", "brand-fg"), ("Critical angle", "slightly lower", "fg-muted"),
             ("Drag", "more", "bad")]
    c.add(rect(x0, 40, 144, 300, "surface-2", None, rx=8))
    c.add(text(x0 + 12, 62, "Flap down:", 14, "start", "fg", weight=700))
    for i, (head, val, colour) in enumerate(items):
        y = 86 + i * 36
        c.add(text(x0 + 12, y, head, 11, "start", "fg-muted"))
        c.add(text(x0 + 12, y + 15, val, 13, "start", colour, weight=600))
    c.add(text(x0 + 12, 362, "Small flap: big lift gain.", 11, "start", "fg-muted"))
    c.add(text(x0 + 12, 377, "Full flap: mostly drag.", 11, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 3.2 flight controls
def _ailerons_top(left: str, right: str) -> str:
    """Aileron patches for plane_top local coordinates (heading 90: left wing is up the page, at negative y)."""
    return (rect(-9, -47, 5, 18, left, "fg", 1, transform=None) + rect(-9, 29, 5, 18, right, "fg", 1))


@chart
def adverse_yaw() -> Canvas:
    c = Canvas("Adverse aileron yaw and how rudder fixes it", "Plan view, aeroplane flying left to right and rolling right. Top: with aileron alone, the "
               "down-going aileron on the rising left wing makes more induced drag, so the nose yaws left, away from the turn. Bottom: right rudder "
               "applied with the right aileron pushes the tail left and the nose right, so the nose follows the turn and the ball stays centred.",
               height=470, prefix="ady")
    for top, step in ((0, 1), (236, 2)):
        X, Y = 196, top + 122
        c.add(rect(12, top + 14, 616, 214, "surface-2" if step == 1 else "ok-soft", None, rx=10, fill_opacity=0.5 if step == 2 else None))
        # intended turn to the right (down the page)
        c.add(path(f"M{X + 60} {Y} Q{X + 160} {Y} {X + 200} {Y + 40}", "fg-faint", None, THIN, dash=DASH, arrow_end=True))
        c.add(text(X + 208, Y + 48, "turn wanted", 11, "start", "fg-faint"))
        rud = "" if step == 1 else path("M-34 0 L-44 6", "brand", None, 3)
        c.add(group(plane_top(0, 0, 1, 90, "fg", "surface"), _ailerons_top("brand-soft", "info-soft"), rud,
                    transform=f"translate({X} {Y}) scale(1.5)"))
        c.add(text(X - 14, Y - 84, "left wing rising: aileron DOWN", 11, "middle", "brand", weight=600))
        c.add(text(X - 14, Y + 94, "right wing: aileron UP", 11, "middle", "info", weight=600))
        # drag at the tips: more on the rising wing
        c.add(arrow(X - 16, Y - 57, X - 86, Y - 57, "bad", MAIN))
        c.add(text(X - 100, Y - 53, "more drag", 12, "end", "bad", weight=600))
        c.add(arrow(X - 16, Y + 57, X - 44, Y + 57, "fg-muted", SECOND))
        c.add(text(X - 50, Y + 61, "less", 11, "end", "fg-muted"))
        if step == 1:
            c.add(path(arc_path(X, Y, 78, -4, -34), "bad", None, MAIN, arrow_end=True))
            c.add(text(X + 70, Y - 62, "nose yaws LEFT", 13, "start", "bad", weight=700))
            heading = "1 · Aileron alone, rolling right"
            lines = ["The down-going aileron gives the", "rising left wing more lift and more", "induced drag. The drag pulls that", "wing back: the nose swings away", "from the turn. This is adverse yaw."]
            colour = "bad"
        else:
            c.add(arrow(X - 66, Y + 16, X - 66, Y - 18, "brand", MAIN))
            c.add(text(X - 74, Y + 30, "rudder force", 11, "end", "brand", weight=600))
            c.add(path(arc_path(X, Y, 78, 4, 34), "ok", None, MAIN, arrow_end=True))
            c.add(text(X + 56, Y + 76, "nose follows the turn", 13, "start", "ok-fg", weight=700))
            heading = "2 · Add rudder the same way"
            lines = ["Rudder the same way as the aileron", "pushes the tail left and the nose", "right, cancelling the adverse yaw:", "a coordinated roll, ball centred."]
            colour = "ok-fg"
        c.add(text(402, top + 44, heading, 14, "start", colour, weight=700))
        c.add(multiline(402, top + 68, lines, 12, "start", "fg"))
    return c


@chart
def trim_tab() -> Canvas:
    c = Canvas("How a trim tab holds the elevator", "Side view of the tailplane, elevator and trim tab with the airflow from the left. For nose-up trim the tab is "
               "deflected down; the air pushes up on it, and that force holds the elevator trailing edge up without any force from the pilot.",
               height=320, prefix="tt")
    HX, HY = 320, 130
    el_ang, tab_ang, el_len, tab_len = 12, 26, 140, 62
    # airflow
    for y in (70, 110, 160, 196):
        c.add(arrow(26, y, 86, y, "sky-fg", SECOND))
    c.add(text(26, 56, "airflow", 12, "start", "sky-fg"))
    # tailplane (fixed)
    c.add(path(f"M100 {HY} C110 {HY - 16} 160 {HY - 16} {HX - 4} {HY - 8} L{HX - 4} {HY + 8} C160 {HY + 14} 110 {HY + 14} 100 {HY} Z", "fg", "surface-2", MAIN))
    c.add(text(200, HY + 40, "tailplane (fixed)", 12, "middle", "fg-muted"))
    tab = group(path(f"M0 -3.5 L{tab_len} -1.5 L{tab_len} 1.5 L0 3.5 Z", "brand", "brand-soft", MAIN), transform=f"translate({el_len} 0) rotate({tab_ang})")
    elev = group(path(f"M0 -8 C20 -9 60 -7 {el_len} -3 L{el_len} 3 C60 7 20 9 0 8 Z", "fg", "surface", MAIN), tab, transform=f"translate({HX} {HY}) rotate({-el_ang})")
    c.add(elev)
    c.add(circle(HX, HY, 4, "fg", None))
    c.add(text(HX - 4, HY + 30, "hinge", 11, "middle", "fg-muted"))
    r = math.radians
    tex, tey = HX + el_len * math.cos(r(el_ang)), HY - el_len * math.sin(r(el_ang))
    tcx, tcy = tex + tab_len * 0.6 * math.cos(r(tab_ang - el_ang)), tey + tab_len * 0.6 * math.sin(r(tab_ang - el_ang))
    # neutral elevator position for reference
    c.add(line(HX, HY, HX + el_len + tab_len, HY, "fg-faint", THIN, DASH))
    c.add(text(HX + 60, HY + 18, "neutral", 11, "middle", "fg-faint"))
    # air force on the tab, pushing it (and the elevator trailing edge) up
    c.add(arrow(tcx, tcy + 60, tcx, tcy + 9, "brand", MAIN))
    c.add(multiline(tcx + 10, tcy + 40, ["air pushes", "up on the tab"], 12, "start", "brand", weight=600))
    # moment about the hinge
    c.add(path(arc_path(HX, HY, 92, 4, -24), "brand", None, SECOND, arrow_end=True))
    c.add(text(HX + 70, HY - 64, "elevator held UP", 13, "end", "fg", weight=700))
    c.add(text(tex + 22, tey - 2, "tab DOWN", 13, "start", "brand", weight=700))
    # the chain, as a strip at the bottom
    steps = ["Trim nose-up", "Tab down", "Air holds elevator up", "Tail down, nose up", "No stick force"]
    x = 20
    for i, s in enumerate(steps):
        w = len(s) * 6.0 + 16
        c.add(rect(x, 248, w, 28, "brand-soft" if i in (1, 2) else "surface-2", None, rx=6))
        c.add(text(x + w / 2, 266, s, 11, "middle", "brand-fg" if i in (1, 2) else "fg", weight=600))
        if i < len(steps) - 1:
            c.add(line(x + w + 3, 262, x + w + 13, 262, "fg-muted", SECOND, arrow_end=True))
        x += w + 18
    c.add(text(20, 304, "The tab always moves opposite to the elevator. Attitude first, then trim the pressure away.", 12, "start", "fg-muted"))
    return c


@chart
def control_effectiveness_vs_airspeed() -> Canvas:
    c = Canvas("Control effectiveness with airspeed and power", "A grid rating the elevator, rudder and ailerons in three cases. Low airspeed with "
               "power off: all three weak and sloppy. Low airspeed with high power: the slipstream over the tail makes the elevator and rudder "
               "effective, the ailerons, outside the slipstream, stay weak. High airspeed: all three effective and heavier.",
               height=300, prefix="cea")
    cols = [("Low IAS, power off", "glide, flare"), ("Low IAS, high power", "take-off, go-around"), ("High IAS", "cruise, descent")]
    rows = ["Elevator", "Rudder", "Ailerons"]
    levels = [[1, 2, 3], [1, 2, 3], [1, 1, 3]]
    notes = [["weak, sloppy", "good: in the slipstream", "strong, heavy"], ["weak, sloppy", "good: in the slipstream", "strong, heavy"],
             ["weak, sloppy", "weak: outside it", "strong, heavy"]]
    X0, CW, Y0, RH = 120, 170, 76, 62
    for j, (h, sub) in enumerate(cols):
        cx = X0 + j * CW + CW / 2
        c.add(text(cx, 30, h, 14, "middle", "fg", weight=700))
        c.add(text(cx, 48, sub, 12, "middle", "fg-muted"))
    for i, r in enumerate(rows):
        y = Y0 + i * RH
        c.add(rect(20, y, 600, RH - 8, "surface-2", None, rx=8))
        c.add(text(32, y + RH / 2, r, 14, "start", "fg", weight=600))
        for j in range(3):
            lv = levels[i][j]
            colour = "brand" if lv > 1 else "warn"
            bx = X0 + j * CW + 34
            for k in range(3):
                c.add(rect(bx + k * 24, y + 10, 20, 14, colour if k < lv else "surface", colour if k < lv else "line-strong", 1, rx=3))
            c.add(text(bx, y + 42, notes[i][j], 11, "start", "brand-fg" if lv > 1 else "warn-fg", weight=600))
    c.add(multiline(20, 276, ["Control force comes from dynamic pressure (½ρV²): faster means more effective and heavier.",
                              "The slipstream flows over the tail, not the ailerons: power helps the elevator and rudder only."], 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 3.3 climbing
@chart
def vx_vs_vy() -> Canvas:
    c = Canvas("Vx or Vy?", "Two climbs from the same point. At Vx (best angle) the path is steeper, gaining the most height per distance, so it clears "
               "a nearby obstacle. At Vy (best rate) the path is flatter but the aeroplane goes faster, gaining the most height per minute: the "
               "one-minute and two-minute marks are higher on the Vy path.", height=380, prefix="vxy")
    GY, X0 = 320, 50
    sx, sy = 165, 0.11                                    # px per NM, px per ft (schematic)
    vx, rx, vyy, ry = 55, 700, 75, 760                   # schematic: Vx slower with a steeper gradient, Vy faster with a higher rate
    c.add(path(f"M20 {GY} L620 {GY} L620 {GY + 18} L20 {GY + 18} Z", None, "surface-2"))
    c.add(line(20, GY, 620, GY, "fg-muted", SECOND))

    def pt(minutes, v, roc):
        return X0 + v / 60 * minutes * sx, GY - roc * minutes * sy

    # obstacle: Vx clears it, Vy does not
    OX = X0 + 160
    OH = 73
    c.add(path(f"M{OX - 14} {GY} L{OX} {GY - OH} L{OX + 14} {GY} Z", "fg-muted", "ok-soft", SECOND))
    c.add(text(OX, GY + 14, "obstacle", 11, "middle", "fg-muted"))
    for v, roc, colour, name, tmax, pitch in ((vx, rx, "brand", "Vx", 2.5, 14), (vyy, ry, "info", "Vy", 2.3, 10)):
        end = pt(tmax, v, roc)
        c.add(line(X0, GY, *end, colour, MAIN))
        for m in (1, 2):
            x, y = pt(m, v, roc)
            c.add(circle(x, y, 5, colour, "surface", 1.5))
            c.add(num(x + (-10 if name == "Vx" else 10), y + (-6 if name == "Vx" else 18), f"{m} min", 11, "end" if name == "Vx" else "start", colour))
        c.add(plane_side(end[0] + 10, end[1] - 4, 0.4, colour, pitch=pitch, gear=False))
        c.add(text(end[0] + 36, end[1] + 4, name, 14, "start", colour, weight=700))
    c.add(circle(X0, GY, 4, "fg", None))
    c.add(callout(OX + 2, GY - 0.405 * 160 + 3, OX + 60, GY - 26, ["Vy path passes", "too low here"], "bad", 12))
    # labels
    c.add(rect(20, 18, 286, 70, "brand-soft", None, rx=8))
    c.add(text(32, 40, "Vx · best ANGLE", 14, "start", "brand-fg", weight=700))
    c.add(multiline(32, 58, ["most height per distance: obstacle clearance", "slower; uses the maximum excess thrust"], 12, "start", "brand-fg"))
    c.add(rect(334, 18, 286, 70, "info-soft", None, rx=8))
    c.add(text(346, 40, "Vy · best RATE", 14, "start", "info-fg", weight=700))
    c.add(multiline(346, 58, ["most height per minute: fastest to altitude", "faster; uses the maximum excess power"], 12, "start", "info-fg"))
    c.add(text(620, GY + 36, "Same minute marks: Vy is higher on time, Vx is higher over the same distance.", 12, "end", "fg-muted"))
    c.add(text(620, GY + 52, "Schematic, not to scale.", 11, "end", "fg-faint"))
    return c


@chart
def climb_gradient_and_wind() -> Canvas:
    c = Canvas("Wind changes the climb angle, not the rate", "Height against distance over the ground for a climb at 500 feet per minute and 70 knots TAS: "
               "429 feet per nautical mile in still air, 545 with a 15 knot headwind (groundspeed 55 knots) and 353 with a 15 knot tailwind "
               "(groundspeed 85 knots). The vertical speed indicator shows 500 feet per minute in all three.", height=380, prefix="cgw")
    ch = Chart(c, (0, 3.2), (0, 1800), box=(80, 30, 470, 310), xlabel="Distance over the ground (NM)", ylabel="Height gained (ft)",
               xticks=[0, 1, 2, 3], yticks=[0, 500, 1000, 1500])
    c.add(ch.axes())
    cases = [(545, "info", "15 kt headwind, GS 55 kt", "545 ft/NM"), (429, "brand", "still air, GS 70 kt", "429 ft/NM"), (353, "warn", "15 kt tailwind, GS 85 kt", "353 ft/NM")]
    for g, colour, lab, val in cases:
        xe = 3.0
        c.add(ch.curve([(0, 0), (xe, g * xe)], colour, MAIN, smooth=False))
        c.add(ch.point(1, g, colour, 5))
        c.add(num(ch.px(xe) + 10, ch.py(g * xe) + 2, val, 13, "start", colour, weight=700))
        c.add(text(ch.px(xe) + 10, ch.py(g * xe) + 18, lab, 11, "start", colour))
    c.add(ch.guide(1, 545, "fg-faint"))
    c.add(text(ch.px(1) + 8, ch.py(150), "after 1 NM", 11, "start", "fg-faint"))
    # the sum, in the empty corner
    c.add(rect(96, 38, 200, 108, "surface-2", None, rx=8))
    c.add(text(108, 60, "500 fpm at 70 kt TAS", 12, "start", "fg", weight=600))
    c.add(text(108, 78, "ft per NM = ROC × 60 ÷ GS", 12, "start", "fg", weight=600))
    c.add(multiline(108, 102, ["500 × 60 ÷ 55 = 545", "500 × 60 ÷ 70 = 429", "500 × 60 ÷ 85 = 353"], 12, "start", "fg-muted", leading=1.5, cls="num"))
    c.add(text(20, 368, "The VSI shows 500 fpm in all three: wind changes the path over the ground, not the rate of climb.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 3.4 descents
@chart
def forces_in_a_glide() -> Canvas:
    c = Canvas("Forces in a steady glide", "An aeroplane gliding down a straight path with no thrust. Lift acts perpendicular to the flight path, drag acts "
               "back along it, and weight acts vertically down. Lift and drag together make a resultant that is exactly equal and opposite to "
               "the weight. The glide angle between the path and the horizon is the angle whose tangent is drag over lift, so the flattest glide "
               "is at the best lift/drag ratio.", height=420, prefix="fig")
    g = 14                                    # glide angle, exaggerated for clarity (a 9:1 glide is about 6 degrees)
    r = math.radians(g)
    CX, CY, W = 280, 196, 150
    L, D = W * math.cos(r), W * math.sin(r)
    t = math.tan(r)
    # flight path and horizon
    x0, x1 = 30, 620
    c.add(line(x0, CY - (CX - x0) * t, x1, CY + (x1 - CX) * t, "sky-fg", SECOND, DASH))
    c.add(text(40, CY - (CX - 40) * t - 12, "flight path = relative airflow", 12, "start", "sky-fg", rotate=g))
    PX = 430
    PY = CY + (PX - CX) * t
    c.add(line(PX, PY, 620, PY, "fg-faint", THIN, DASH))
    c.add(text(620, PY - 8, "horizontal", 11, "end", "fg-faint"))
    c.add(angle_mark(PX, PY, 110, 0, g, None, "fg-muted"))
    c.add(text(PX + 118, PY + 110 * math.tan(r / 2) + 10, "glide angle", 12, "start", "fg-muted", weight=600))
    c.add(plane_side(CX, CY, 1.0, "fg-muted", pitch=-g + 3, gear=False))
    # vectors from the CG
    lx, ly = CX + L * math.sin(r), CY - L * math.cos(r)
    ddx, ddy = CX - D * math.cos(r), CY - D * math.sin(r)
    c.add(line(lx, ly, CX, CY - W, "fg-faint", THIN, DASH))
    c.add(line(ddx, ddy, CX, CY - W, "fg-faint", THIN, DASH))
    c.add(arrow(CX, CY - 4, CX, CY - W, "ok", MAIN, dash="6 4"))
    c.add(arrow(CX, CY, lx, ly, "brand", 2.5))
    c.add(text(lx + 10, ly + 8, "Lift", 15, "start", "brand", weight=700))
    c.add(text(lx + 10, ly + 24, "perpendicular to the path", 11, "start", "brand"))
    c.add(arrow(CX, CY, ddx, ddy, "info", 2.5))
    c.add(text(ddx - 4, ddy + 30, "Drag", 15, "end", "info", weight=700))
    c.add(text(ddx - 4, ddy + 46, "back along the path", 11, "end", "info"))
    c.add(arrow(CX, CY, CX, CY + W, "fg", 2.5))
    c.add(text(CX - 10, CY + W - 6, "Weight", 15, "end", "fg", weight=700))
    c.add(text(CX - 10, CY - W + 4, "lift + drag together", 12, "end", "ok-fg", weight=600))
    c.add(text(CX - 10, CY - W + 20, "= weight, straight up", 12, "end", "ok-fg"))
    # no thrust box
    c.add(rect(340, 310, 284, 96, "surface-2", None, rx=8))
    c.add(text(352, 332, "No thrust", 14, "start", "fg", weight=700))
    c.add(multiline(352, 352, ["Weight pulls the aeroplane down the path:", "it does the job thrust did. Flattest glide", "at best L/D: distance = height × L/D."],
                    12, "start", "fg-muted", leading=1.35))
    c.add(text(20, 410, "Angle exaggerated: a 9 : 1 glide is about 6°.", 11, "start", "fg-faint"))
    return c


@chart
def powered_descent_vs_glide() -> Canvas:
    c = Canvas("Power and flap in a descent at constant IAS", "Three descents from the same point, all at the same indicated airspeed. With power "
               "added the path is shallower, the rate of descent lower and the nose higher. The glide with power off is in the middle. With flap "
               "lowered the path is steeper, the rate of descent higher and the nose noticeably lower.", height=340, prefix="pdg")
    SX, SY = 40, 60
    cases = [(3, "ok", "Power added", ["shallower, lower rate", "of descent, nose HIGHER"], 3, 0.72),
             (11, "brand", "Glide, power off", ["the reference"], -4, 0.72),
             (22, "warn", "More flap", ["steeper, higher rate of", "descent, nose much LOWER"], -16, 0.72)]
    for ang, colour, head, lines, pitch, f in cases:
        r = math.radians(ang)
        L = 390
        ex, ey = SX + L * math.cos(r), SY + L * math.sin(r)
        c.add(line(SX, SY, ex, ey, colour, MAIN))
        px, py = SX + f * L * math.cos(r), SY + f * L * math.sin(r)
        c.add(plane_side(px, py, 0.7, colour, pitch=pitch, gear=False))
        c.add(text(ex + 10, ey + 4, head, 14, "start", f"{colour}-fg" if colour != "brand" else "brand", weight=700))
        c.add(multiline(ex + 10, ey + 21, lines, 11, "start", "fg-muted"))
    c.add(circle(SX, SY, 4, "fg", None))
    c.add(text(SX - 6, SY - 14, "same point, same IAS", 12, "start", "fg-muted"))
    c.add(rect(20, 260, 300, 42, "surface-2", None, rx=8))
    c.add(text(32, 278, "On approach: power controls the rate of", 12, "start", "fg"))
    c.add(text(32, 294, "descent, attitude controls the airspeed.", 12, "start", "fg"))
    c.add(text(620, 326, "Schematic angles. Too low? Add power, not back pressure.", 11, "end", "fg-faint"))
    return c


# ---------------------------------------------------------------- 3.5 turning
@chart
def slip_and_skid_ball() -> Canvas:
    c = Canvas("Slip, balanced or skid: read the ball", "Three balance indicators in a left turn. Slipping: the ball sits to the inside of the "
               "turn (left, the low wing) because there is too much bank or too little rudder; step on the left rudder. Balanced: ball centred. "
               "Skidding: the ball sits to the outside (right, the high wing) because there is too much rudder; step on the right rudder.",
               height=350, prefix="sas")
    panels = [(-1, "Slip", "bad", ["too much bank for the rate", "of yaw: too little rudder"], "step on the LEFT rudder"),
              (0, "Balanced", "ok", ["rate of yaw matches the", "bank: no slip or skid"], "hold it there"),
              (1, "Skid", "bad", ["too much rudder", "for the bank"], "step on the RIGHT rudder")]
    for i, (side, head, colour, why, fix) in enumerate(panels):
        cx = 110 + i * 210
        c.add(rect(cx - 98, 14, 196, 322, "surface-2" if side else "ok-soft", None, rx=10, fill_opacity=None if side else 0.6))
        c.add(text(cx, 42, head, 17, "middle", "bad" if side else "ok-fg", weight=700))
        c.add(plane_rear(cx, 96, 0.9, 20))
        c.add(text(cx, 140, "left turn, seen from behind", 11, "middle", "fg-faint"))
        # inclinometer: curved tube with two reference wires
        R, TY = 150, 50
        tube_c = (cx, TY)
        c.add(path(arc_path(cx, TY, R + 11, 62, 118), "fg", None, 1.5))
        c.add(path(arc_path(cx, TY, R - 11, 62, 118), "fg", None, 1.5))
        for a in (62, 118):
            x1, y1 = cx + (R - 11) * math.cos(math.radians(a)), TY + (R - 11) * math.sin(math.radians(a))
            x2, y2 = cx + (R + 11) * math.cos(math.radians(a)), TY + (R + 11) * math.sin(math.radians(a))
            c.add(line(x1, y1, x2, y2, "fg", 1.5))
        for a in (85, 95):
            x1, y1 = cx + (R - 13) * math.cos(math.radians(a)), TY + (R - 13) * math.sin(math.radians(a))
            x2, y2 = cx + (R + 13) * math.cos(math.radians(a)), TY + (R + 13) * math.sin(math.radians(a))
            c.add(line(x1, y1, x2, y2, "fg-muted", 1.5))
        ba = 90 - side * 15                      # inside of a left turn is the reader's left (larger screen angle)
        bx, by = cx + R * math.cos(math.radians(ba)), TY + R * math.sin(math.radians(ba))
        c.add(circle(bx, by, 9, "bad" if side else "ok", "fg", 1.5))
        del tube_c
        c.add(text(cx - 66, 232, "inside", 11, "middle", "fg-faint"), text(cx + 66, 232, "outside", 11, "middle", "fg-faint"))
        c.add(multiline(cx, 264, why, 12, "middle", "fg"))
        c.add(badge(cx, 312, fix, "bad" if side else "ok", 11))
    return c


@chart
def category_load_limits() -> Canvas:
    c = Canvas("Limit and ultimate load factors by category", "Bars for the normal, utility and aerobatic categories. The limit load factors are "
               "plus 3.8, 4.4 and 6 g; beyond the limit the structure may bend permanently, and beyond the ultimate load, normally 1.5 times the "
               "limit (5.7, 6.6 and 9 g), it may fail. A level turn at 60 degrees of bank pulls 2 g and at 75 degrees about 3.86 g.",
               height=330, prefix="cll")
    ch = Chart(c, (0, 10), (0, 3), box=(120, 50, 600, 250), xlabel="Positive load factor (g)", xticks=[0, 2, 4, 6, 8, 10], yticks=[], grid=False)
    for t in (2, 4, 6, 8, 10):
        c.add(line(ch.px(t), ch.top - 10, ch.px(t), ch.bottom, "line", THIN))
    rows = [("Normal", 3.8), ("Utility", 4.4), ("Aerobatic", 6.0)]
    for b, n_, lab in ((60, 2.0, "60° turn: 2 g"), (75, 3.86, "75°: 3.86 g")):
        X = ch.px(n_)
        c.add(line(X, 56, X, 250, "info", SECOND, DASH))
        c.add(text(X + (-4 if b == 60 else 4), 46, lab, 11, "end" if b == 60 else "start", "info", weight=600))
    for i, (name, lim) in enumerate(rows):
        y = 70 + i * 60
        ult = lim * 1.5
        c.add(text(110, y + 17, name, 14, "end", "fg", weight=600))
        c.add(rect(ch.px(0), y, ch.px(lim) - ch.px(0), 26, "brand", None, rx=3))
        c.add(rect(ch.px(lim), y, ch.px(ult) - ch.px(lim), 26, "warn-soft", "warn", 1, rx=3))
        c.add(num(ch.px(0) + 10, y + 18, f"limit +{fmt(lim)} g", 13, "start", "on-brand", weight=700))
        c.add(num(ch.px(ult) + 6, y + 18, f"{fmt(round(ult, 1))} ultimate", 12, "start", "warn-fg", weight=600))
    c.add(ch.axes(arrows=False))
    c.add(rect(120, 290, 14, 12, "brand", None, rx=2))
    c.add(text(140, 300, "up to limit: no permanent damage", 12, "start", "fg-muted"))
    c.add(rect(360, 290, 14, 12, "warn-soft", "warn", 1, rx=2))
    c.add(text(380, 300, "limit to ultimate (1.5 × limit): bends", 12, "start", "fg-muted"))
    c.add(text(380, 316, "beyond ultimate: may fail", 12, "start", "bad"))
    return c


# ---------------------------------------------------------------- 3.6 stalling, spinning and spiral dives
def _upper_surface(n: int = 24, lift: float = 7.0, t0: float = 0.0, t1: float = 1.0) -> list[tuple[float, float]]:
    """Points just above the aerofoil() upper surface in its local units (100 long, quarter chord at x=0)."""
    p = [(0, 0), (8, -14), (40, -16), (100, -2)]
    out = []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        x = (1 - t) ** 3 * p[0][0] + 3 * (1 - t) ** 2 * t * p[1][0] + 3 * (1 - t) * t ** 2 * p[2][0] + t ** 3 * p[3][0]
        y = (1 - t) ** 3 * p[0][1] + 3 * (1 - t) ** 2 * t * p[1][1] + 3 * (1 - t) * t ** 2 * p[2][1] + t ** 3 * p[3][1]
        out.append((x - 25, y - lift))
    return out


def _eddy(x: float, y: float, r: float, colour: str = "bad") -> str:
    return path(arc_path(x, y, r, 200, 470), colour, None, SECOND, arrow_end=True)


@chart
def stall_sequence() -> Canvas:
    c = Canvas("Approaching the stall", "Three wing sections at increasing angle of attack: airflow attached over the whole upper surface, airflow starting "
               "to separate near the trailing edge, and the stall past the critical angle with the flow separated and turbulent. Below, the "
               "warning signs in the usual order: low and decreasing airspeed with a high nose attitude, sloppy controls and a quieter airflow note, "
               "the stall warning 5 to 10 knots above the stall, buffet, then the stall itself: a nose drop or wing drop and a high rate of descent.",
               height=420, prefix="sts")
    stages = [(4, "Attached", "smooth flow, full lift", "ok", 1.0), (12, "Separating", "flow breaks away at the rear", "warn", 0.62),
              (18, "Stalled", "past the critical angle", "bad", 0.12)]
    for i, (a, head, sub, colour, sep) in enumerate(stages):
        cx, cy, chord = 110 + i * 210, 130, 130
        s_ = chord / 100
        c.add(text(cx, 34, head, 16, "middle", f"{colour}-fg" if colour != "bad" else "bad", weight=700))
        c.add(text(cx, 52, sub, 11, "middle", "fg-muted"))
        for y in (92, 112):
            c.add(arrow(cx - 98, y, cx - 74, y, "sky-fg", SECOND))
        inner = [path("M0 0 C8 -14 40 -16 100 -2 C60 4 20 8 0 0 Z", "fg", "surface", MAIN / s_, transform="translate(-25 0)")]
        flow = _upper_surface(24, 7, 0.0, sep if sep < 1 else 1.0)
        inner.append(path(smooth_path(flow), "sky-fg", None, SECOND / s_, arrow_end=sep >= 1))
        under = [(x, -y * 0.25 + 10) for x, y in _upper_surface(12, 0)]
        inner.append(path(smooth_path([(-25, 9), (20, 10), (75, 6)]), "sky-fg", None, SECOND / s_, arrow_end=True))
        del under
        if sep < 1:
            # broken-away flow leaves the surface and carries on; eddies fill the gap above the rear of the wing
            lx, ly = flow[-1]
            dep = math.radians(-8 if sep > 0.5 else -15)
            fx = 92
            fy = ly + (fx - lx) * math.tan(dep)
            inner.append(path(f"M{fmt(lx)} {fmt(ly)} L{fmt(fx)} {fmt(fy)}", "sky-fg", None, SECOND / s_, dash="4 3", arrow_end=True))
            spots = [(55, -12, 5), (72, -10, 4.5)] if sep > 0.5 else [(12, -22, 4.5), (36, -22, 5.5), (60, -18, 6), (80, -14, 5)]
            for ex, ey, er in spots:
                inner.append(_eddy(ex, ey, er, colour))
        c.add(group(*inner, transform=f"translate({cx} {cy}) rotate({-a}) scale({fmt(s_)})"))
        c.add(num(cx, cy + 50, f"{a}°", 13, "middle", colour if colour != "ok" else "ok-fg", weight=700))
        c.add(text(cx, cy + 66, "angle of attack", 11, "middle", "fg-faint"))
    # timeline of the symptoms
    c.add(arrow(20, 238, 620, 238, "fg-muted", SECOND))
    c.add(text(20, 228, "angle of attack rising, airspeed falling →", 12, "start", "fg-muted", weight=600))
    steps = [("1", ["Low, decreasing", "airspeed; nose", "high in level flight"], "surface-2", "fg"),
             ("2", ["Controls sloppy,", "quieter airflow", "note"], "surface-2", "fg"),
             ("3", ["Stall warning", "horn or light,", "5–10 kt above"], "warn-soft", "warn-fg"),
             ("4", ["Buffet: turbulent", "air hits the", "tailplane"], "warn-soft", "warn-fg"),
             ("!", ["STALL: nose drop", "or wing drop, high", "rate of descent"], "bad-soft", "bad-fg")]
    for i, (n_, lines, fill, fg) in enumerate(steps):
        x = 20 + i * 122
        c.add(rect(x, 254, 112, 84, fill, None, rx=8))
        c.add(circle(x + 16, 272, 10, "surface", fg, 1.5))
        c.add(text(x + 16, 276, n_, 12, "middle", fg, weight=700))
        c.add(multiline(x + 8, 300, lines, 11, "start", fg))
    c.add(text(20, 370, "The stall is about angle of attack, not speed: it can happen at any airspeed and any attitude.", 12, "start", "fg-muted"))
    c.add(text(20, 388, "The cure: ease forward to lower the angle of attack until the buffet stops, then power, then roll level.", 12, "start", "fg-muted"))
    return c


def _asi(x: float, y: float, frac: float, colour: str, trend: str) -> str:
    """Mini airspeed indicator: needle at frac of the scale (0 = low)."""
    a = math.radians(135 + frac * 270)
    out = circle(x, y, 30, "surface", "fg", 1.5)
    out += path(arc_path(x, y, 25, 135, 405), "line-strong", None, 3)
    out += line(x, y, x + 22 * math.cos(a), y + 22 * math.sin(a), colour, 2.5)
    out += circle(x, y, 3, "fg", None)
    out += text(x, y + 46, trend, 12, "middle", colour, weight=700)
    return out


@chart
def spin_vs_spiral_dive() -> Canvas:
    c = Canvas("Spin or spiral dive?", "Side-by-side comparison. Spin: both wings stalled, airspeed low and roughly steady, rate of descent high; recover "
               "with throttle closed, ailerons neutral, full opposite rudder, control column forward until the rotation stops, then centralise "
               "the rudder and ease out. Spiral dive: wings not stalled, airspeed high and increasing, rate of descent very high; recover with "
               "throttle closed, roll level with aileron and coordinated rudder, ease out gently, then restore power.", height=450, prefix="svs")
    cols = [(170, "Spin", "bad", "Stalled", 0.12, "low, steady", "High",
             ["1  Throttle closed", "2  Ailerons neutral", "3  Full opposite rudder", "4  Stick centrally forward", "    until the rotation stops", "5  Centralise rudder, ease out"]),
            (470, "Spiral dive", "warn", "Not stalled", 0.82, "high, rising ↑", "Very high",
             ["1  Throttle closed", "2  Roll wings level with", "    aileron + coordinated rudder", "3  Ease out of the dive gently", "4  Power back on once the", "    speed is under control"])]
    for cx, head, colour, wings, frac, trend, rod, steps in cols:
        fg = "bad" if colour == "bad" else "warn-fg"
        c.add(rect(cx - 145, 14, 290, 410, f"{colour}-soft", None, rx=10, fill_opacity=0.45))
        c.add(text(cx, 44, head, 18, "middle", fg, weight=700))
        # picture: steep nose-down aeroplane with rotation
        c.add(plane_side(cx - 50, 100, 0.55, "fg", pitch=-60 if head == "Spin" else -35, gear=False))
        c.add(path(arc_path(cx - 50, 100, 34, 200, 340), colour, None, SECOND, arrow_end=True))
        c.add(_asi(cx + 70, 96, frac, colour if colour == "bad" else "warn", trend))
        c.add(text(cx + 70, 56, "ASI", 11, "middle", "fg-faint"))
        rows = [("Wings", wings), ("Airspeed", trend.replace(" ↑", "")), ("Rate of descent", rod)]
        for j, (k, v) in enumerate(rows):
            y = 182 + j * 34
            c.add(line(cx - 130, y - 16, cx + 130, y - 16, "line", THIN))
            c.add(text(cx - 130, y + 2, k, 13, "start", "fg-muted"))
            c.add(text(cx + 130, y + 2, v, 14, "end", fg, weight=700))
        c.add(line(cx - 130, 268, cx + 130, 268, "line", THIN))
        c.add(text(cx - 130, 292, "Recovery", 14, "start", "fg", weight=700))
        for j, st in enumerate(steps):
            indent = st.startswith("    ")
            c.add(text(cx - 130 + (16 if indent or st[0].isdigit() else 0), 316 + j * 18, st.strip()[3:] if st[0].isdigit() else st.strip(), 12, "start", "fg"))
            if st[0].isdigit():
                c.add(num(cx - 130, 316 + j * 18, st[0], 12, "start", fg, weight=700))
    c.add(text(320, 442, "Check the POH: its procedure overrides any generic one.", 11, "middle", "fg-faint"))
    c.add(badge(320, 160, "VS", "surface", 12))
    return c


def _wing_section(x: float, y: float, chord: float, angle: float, flap: float, colour: str) -> str:
    s_ = chord / 100
    te_x, te_y = 75, -2
    fx, fy = te_x + 22 * math.cos(math.radians(flap)), te_y + 22 * math.sin(math.radians(flap))
    return group(path("M0 0 C8 -14 40 -16 100 -2 C60 4 20 8 0 0 Z", colour, "surface", MAIN / s_, transform="translate(-25 0)"),
                 line(te_x - 4, te_y + 1, fx, fy, colour, 3 / s_), transform=f"translate({fmt(x)} {fmt(y)}) rotate({fmt(-angle)}) scale({fmt(s_)})")


@chart
def wing_drop_and_recovery() -> Canvas:
    c = Canvas("A wing drops near the stall: aileron or rudder?", "Left: using aileron to pick up a dropped wing near the stall lowers that wing's "
               "aileron, raising its angle of attack past the critical angle; the wing stalls further and drops more, and the extra drag yaws the "
               "aeroplane towards a spin. Right: keep the wings level with rudder near the stall, unstall first by easing the control column "
               "forward, then level the wings with aileron once the wing is flying.", height=390, prefix="wdr")
    for i, (head, colour, ok) in enumerate((("Aileron to lift the low wing", "bad", False), ("Rudder, unstall, then aileron", "ok", True))):
        cx = 165 + i * 310
        c.add(rect(cx - 150, 14, 300, 362, f"{colour}-soft", None, rx=10, fill_opacity=0.45))
        c.add(text(cx, 42, head, 15, "middle", "bad" if not ok else "ok-fg", weight=700))
        c.add(plane_rear(cx, 104, 1.2, 14))
        c.add(arrow(cx - 136, 200, cx - 96, 200, "sky-fg", SECOND))
        c.add(text(cx - 136, 190, "airflow", 11, "start", "sky-fg"))
        c.add(text(cx - 64, 146, "dropped wing", 11, "middle", "fg-muted"))
        if not ok:
            c.add(_wing_section(cx - 20, 202, 110, 15, 42, "bad"))
            c.add(text(cx, 246, "aileron DOWN on the low wing:", 12, "middle", "bad", weight=600))
            c.add(text(cx, 262, "angle of attack goes past critical", 12, "middle", "bad"))
            c.add(multiline(cx - 134, 296, ["→ that wing stalls further and drops more", "→ its extra drag yaws the aeroplane", "→ a spin can start"], 12, "start", "fg"))
        else:
            c.add(text(cx + 64, 146, "level it with rudder", 11, "middle", "ok-fg", weight=600))
            c.add(_wing_section(cx - 20, 202, 110, 8, 0, "ok"))
            c.add(text(cx, 246, "stick forward: angle below critical", 12, "middle", "ok-fg", weight=600))
            for j, (n_, st) in enumerate((("1", "Ease forward until the buffet stops"), ("2", "Full power, straight with rudder"), ("3", "Level the wings with aileron"),
                                          ("", "once the wing is unstalled"), ("4", "Climb away, minimum height loss"))):
                if n_:
                    c.add(num(cx - 134, 282 + j * 18, n_, 12, "start", "ok-fg", weight=700))
                c.add(text(cx - 118, 282 + j * 18, st, 12, "start", "fg"))
    return c


# ---------------------------------------------------------------- 3.7 taxi, take-off and landing
def _stick_box(x: float, y: float, dx: int, dy: int, colour: str) -> str:
    """Control column position seen from above: dx -1 left / +1 right, dy -1 forward / +1 back / 0 neutral."""
    out = rect(x - 18, y - 18, 36, 36, "surface", "line-strong", 1, rx=6)
    out += line(x, y - 14, x, y + 14, "line", THIN) + line(x - 14, y, x + 14, y, "line", THIN)
    out += circle(x + dx * 10, y + dy * 10, 6, colour, None)
    return out


@chart
def crosswind_taxi_control_positions() -> Canvas:
    c = Canvas("Taxiing in a strong wind: where to hold the controls", "Plan view of a tricycle aeroplane taxiing to the right with the four wind "
               "quadrants. Wind from ahead: aileron into the wind (upwind aileron up), elevator neutral. Wind from behind: aileron away from the "
               "wind (upwind aileron down) and elevator forward: dive away from the wind.", height=448, prefix="ctp")
    CX, CY = 320, 220
    c.add(rect(CX, 40, 300, 360, "ok-soft", None, rx=10, fill_opacity=0.35))
    c.add(rect(20, 40, 300, 360, "warn-soft", None, rx=10, fill_opacity=0.35))
    c.add(line(CX, 40, CX, 400, "line-strong", THIN, DASH), line(20, CY, 620, CY, "line-strong", THIN, DASH))
    c.add(text(470, 30, "wind from AHEAD", 13, "middle", "ok-fg", weight=700))
    c.add(text(170, 30, "wind from BEHIND", 13, "middle", "warn-fg", weight=700))
    c.add(plane_top(CX, CY, 0.9, 90))
    c.add(text(CX + 50, CY + 18, "taxiing →", 11, "start", "fg-faint"))
    quads = [  # (x, y, wind arrow from, to, stick dx, dy, lines)
        (470, 140, (590, 56), (550, 88), -1, 0, ["Wind from ahead-left:", "stick LEFT (into wind),", "elevator neutral"], "ok"),
        (470, 300, (590, 384), (550, 352), 1, 0, ["Wind from ahead-right:", "stick RIGHT (into wind),", "elevator neutral"], "ok"),
        (170, 140, (50, 56), (90, 88), 1, -1, ["Wind from behind-left:", "stick RIGHT (away) and", "FORWARD"], "warn"),
        (170, 300, (50, 384), (90, 352), -1, -1, ["Wind from behind-right:", "stick LEFT (away) and", "FORWARD"], "warn")]
    for x, y, a0, a1, sdx, sdy, lines, colour in quads:
        c.add(arrow(*a0, *a1, "sky-fg", MAIN))
        c.add(_stick_box(x - 90, y, sdx, sdy, "brand"))
        c.add(multiline(x - 60, y - 12, lines, 12, "start", f"{colour}-fg"))
    c.add(text(20, 422, "Headwind: climb into it (upwind aileron up). Tailwind: dive away from it (upwind aileron down, stick forward).", 11, "start", "fg-muted"))
    c.add(text(20, 438, "Square = control column seen from above; top = forward. Pilot's left is up the page.", 11, "start", "fg-faint"))
    return c


@chart
def crosswind_takeoff_and_landing() -> Canvas:
    c = Canvas("Crosswind take-off and landing", "Left: seen from behind on the take-off roll with the wind from the left, the wind tends to lift the upwind "
               "wing and the fin weathercocks the nose into wind; hold full aileron into wind at the start and reduce it as speed builds, and keep "
               "straight with rudder. Right: on approach, either crab (heading into wind, tracking down the centreline, straightened with rudder "
               "just before touchdown) or wing-down (upwind wing lowered, opposite rudder keeps the nose straight; low-wing aeroplanes have less "
               "tip and flap clearance).", height=430, prefix="cwt")
    # left panel: take-off roll, rear view
    c.add(rect(12, 14, 300, 404, "surface-2", None, rx=10))
    c.add(text(162, 42, "Take-off roll", 16, "middle", "fg", weight=700))
    c.add(text(162, 60, "seen from behind, wind from the left", 11, "middle", "fg-muted"))
    for y in (110, 140, 170):
        c.add(arrow(26, y, 66, y, "sky-fg", MAIN))
    c.add(text(26, 98, "wind", 12, "start", "sky-fg", weight=600))
    c.add(plane_rear(176, 170, 1.7, 0))
    c.add(line(80, 214, 280, 214, "fg-muted", SECOND))
    c.add(arrow(104, 158, 104, 116, "bad", MAIN))
    c.add(text(110, 106, "wind lifts the upwind wing", 12, "start", "bad", weight=600))
    c.add(rect(92, 168, 16, 6, "brand", None))
    c.add(text(100, 236, "left aileron UP (stick left)", 12, "start", "brand", weight=600))
    c.add(line(100, 176, 100, 222, "brand", THIN))
    c.add(multiline(24, 284, ["Full aileron INTO wind at the start", "(stick towards the wind), less as", "speed builds; rudder keeps you straight", "against weathercocking (nose into wind)."], 12, "start", "fg", leading=1.4))
    c.add(multiline(24, 370, ["High-wing aeroplanes: stronger lifting", "tendency, the wing is high and exposed."], 11, "start", "fg-muted", leading=1.4))
    # right panel: approach
    c.add(rect(326, 14, 302, 404, "surface-2", None, rx=10))
    c.add(text(477, 42, "On approach", 16, "middle", "fg", weight=700))
    c.add(runway(540, 196, 150, 26, None))
    c.add(line(340, 196, 462, 196, "fg-faint", THIN, DASH))
    for y in (80, 110):
        c.add(arrow(600, y - 20, 600, y + 4, "sky-fg", MAIN))
    c.add(text(588, 76, "wind", 12, "end", "sky-fg", weight=600))
    c.add(plane_top(390, 196, 0.42, 66))
    c.add(arrow(410, 196, 460, 196, "brand", SECOND))
    c.add(text(340, 170, "Crab: nose into wind,", 12, "start", "brand", weight=700))
    c.add(text(340, 232, "track down the centreline;", 12, "start", "fg"))
    c.add(text(340, 248, "rudder straightens it before touchdown", 12, "start", "fg"))
    c.add(plane_rear(392, 318, 0.9, 12))
    c.add(text(392, 356, "upwind (left) wing low", 11, "middle", "fg-muted"))
    c.add(text(462, 300, "Wing-down:", 12, "start", "brand", weight=700))
    c.add(multiline(462, 316, ["upwind wing lowered,", "opposite rudder keeps", "the nose straight"], 12, "start", "fg"))
    c.add(text(340, 384, "Low-wing aeroplanes: less wing-tip and", 11, "start", "bad"))
    c.add(text(340, 398, "flap clearance with the wing down.", 11, "start", "bad"))
    return c


@chart
def wind_shear_on_approach() -> Canvas:
    c = Canvas("Wind gradient on approach", "Side view of an approach into a strong headwind that decreases near the ground. As the headwind falls away, "
               "inertia keeps the groundspeed so the indicated airspeed drops; the aeroplane sinks below the approach path and undershoots, with "
               "no change in attitude or power. Add a speed margin in strong winds and be ready with power.", height=400, prefix="wsa")
    GY = 330
    k = (GY - 70) / (500 - 70)                      # planned path: (70, 70) to touchdown at x 500
    py = lambda x: 70 + (x - 70) * k
    path_d = f"M70 70 L300 {py(300):.1f} C350 {py(350) + 6:.1f} 392 {GY - 26} 432 {GY}"
    c.style(f"""
.wsa-plane{{offset-path:path("{path_d}");offset-rotate:0deg;animation:wsa-fly 6s ease-in infinite}}
@keyframes wsa-fly{{0%{{offset-distance:0%;opacity:0}}8%{{opacity:1}}88%{{opacity:1}}100%{{offset-distance:100%;opacity:0}}}}
.wsa-static{{display:none}}
@supports not (offset-path: path("M0 0")){{.wsa-plane{{display:none}}.wsa-static{{display:inline}}}}
""")
    c.add(path(f"M20 {GY} L620 {GY} L620 {GY + 16} L20 {GY + 16} Z", None, "surface-2"))
    c.add(line(20, GY, 620, GY, "fg-muted", SECOND))
    c.add(rect(480, GY - 3, 140, 6, "fg-muted", None))
    c.add(text(550, GY - 12, "runway", 11, "middle", "fg-muted"))
    for y, ln in ((110, 90), (150, 80), (190, 66), (230, 46), (270, 26), (306, 12)):
        c.add(arrow(620, y, 620 - ln, y, "sky-fg", SECOND))
    c.add(multiline(616, 40, ["headwind, weaker", "near the ground", "(wind gradient)"], 11, "end", "sky-fg", leading=1.25))
    c.add(rect(296, 150, 150, GY - 150, "warn-soft", None, fill_opacity=0.5))
    c.add(text(371, 168, "headwind falls away", 12, "middle", "warn-fg", weight=600))
    c.add(path(path_d, "bad", None, MAIN))
    c.add(line(70, 70, 500, GY, "ok", SECOND, DASH))
    c.add(text(84, 60, "planned approach path", 12, "start", "ok-fg", weight=600))
    c.add(multiline(380, 300, ["sinks below the", "path: UNDERSHOOT"], 12, "end", "bad", weight=700))
    c.add(badge(170, 230, "IAS steady", "ok", 12))
    c.add(badge(371, 196, "IAS falls ↓", "bad", 12))
    c.add(multiline(30, 266, ["Inertia keeps the groundspeed, so", "the airspeed drops; the aeroplane", "sinks with no change in attitude", "or power."], 11, "start", "fg-muted"))
    c.add(rect(20, 360, 600, 34, "brand-soft", None, rx=8))
    c.add(text(32, 382, "Strong, gusty wind: add a speed margin (often half the gust factor) and be ready with power.", 12, "start", "brand-fg"))
    c.add(group(plane_side(0, 0, 0.42, "fg", pitch=-3, gear=True), cls="wsa-plane"))
    c.add(group(plane_side(300, py(300) - 6, 0.42, "fg", pitch=-3, gear=True), cls="wsa-static"))
    return c


# ---------------------------------------------------------------- 3.8 structural damage
@chart
def v_n_diagram() -> Canvas:
    c = Canvas("The flight envelope (V-n diagram)", "Load factor against airspeed for a normal category aeroplane with a 52 knot stall speed. The "
               "stall curve rises with the square of the speed and meets the +3.8 g limit at the manoeuvring speed VA, about 101 knots. Below VA "
               "a full control movement stalls the wing before the limit load is reached; above VA it can overstress the structure. The negative "
               "limit is -1.52 g. VNO marks the end of normal operation and VNE the never-exceed speed.", height=440, prefix="vnd")
    VS, VA = 52, 52 * math.sqrt(3.8)
    VNO, VNE, VSN = 128, 160, 64          # schematic positions (no figures in the note); VSN: negative 1 g stall speed
    ch = Chart(c, (0, 176), (-2.4, 5.2), box=(70, 30, 600, 370), xlabel="Indicated airspeed (kt)", ylabel="Load factor  n (g)",
               xticks=[52, round(VA)], yticks=[-1.52, -1, 0, 1, 2, 3.8], yfmt=lambda v: (f"+{fmt(v)}" if v > 0 else fmt(v)), grid=False)
    # regions
    pos = [(v, (v / VS) ** 2) for v in [VS + (VA - VS) * i / 40 for i in range(41)]]
    vneg = VSN * math.sqrt(1.52)
    neg = [(v, -(v / VSN) ** 2) for v in [VSN + (vneg - VSN) * i / 30 for i in range(31)]]
    env = [ch.pt(VS, 1)] + [ch.pt(*p) for p in pos] + [ch.pt(VNE, 3.8), ch.pt(VNE, 0), ch.pt(VNE, -1.52), ch.pt(vneg, -1.52)] + \
          [ch.pt(*p) for p in reversed(neg)] + [ch.pt(VSN, -1), ch.pt(VSN, 0), ch.pt(VS, 0)]
    c.add(polygon(env, "ok", None, fill_opacity=0.12))
    c.add(rect(ch.px(VNO), ch.py(3.8), ch.px(VNE) - ch.px(VNO), ch.py(-1.52) - ch.py(3.8), "warn-soft", None))
    c.add(rect(ch.px(VNE), ch.top, ch.right - ch.px(VNE), ch.bottom - ch.top, "bad", None, fill_opacity=0.10))
    c.add(rect(ch.px(VA), ch.top, ch.px(VNE) - ch.px(VA), ch.py(3.8) - ch.top, "bad", None, fill_opacity=0.10))
    c.add(ch.axes())
    c.add(line(ch.left, ch.py(0), ch.right, ch.py(0), "fg-muted", THIN))
    c.add(line(ch.left, ch.py(1), ch.right, ch.py(1), "line-strong", THIN, DASH))
    c.add(text(ch.left + 6, ch.py(1) - 6, "level flight, 1 g", 11, "start", "fg-faint"))
    # boundaries
    c.add(ch.curve(pos, "brand", MAIN))
    c.add(ch.curve(neg, "brand", SECOND))
    c.add(line(ch.px(VA), ch.py(3.8), ch.px(VNE), ch.py(3.8), "bad", MAIN))
    c.add(line(ch.px(vneg), ch.py(-1.52), ch.px(VNE), ch.py(-1.52), "bad", MAIN))
    c.add(line(ch.px(VNE), ch.py(3.8), ch.px(VNE), ch.py(-1.52), "bad", MAIN))
    c.add(ch.vline(VNO, "warn", DASH, y_to=3.8))
    c.add(ch.point(VA, 3.8, "brand", 5.5))
    c.add(text(ch.px(VA) - 8, ch.py(3.8) - 10, "VA ≈ 101 kt", 13, "end", "brand", weight=700))
    c.add(text(ch.px(VNO) - 6, ch.py(-2.15), "VNO", 13, "end", "warn-fg", weight=700))
    c.add(text(ch.px(VNE) + 4, ch.py(-2.15), "VNE", 13, "start", "bad", weight=700))
    c.add(text((ch.px(VNO) + ch.px(VNE)) / 2, ch.py(3.8) - 30, "structural damage", 13, "middle", "bad", weight=700))
    c.add(text((ch.px(VNO) + ch.px(VNE)) / 2, ch.py(3.8) - 14, "+3.8 g limit load", 12, "middle", "bad"))
    c.add(text(ch.px(110), ch.py(-1.52) + 18, "−1.52 g limit", 12, "middle", "bad"))
    c.add(text(ch.px(30), ch.py(2.6), "stalled:", 12, "middle", "brand", weight=700))
    c.add(text(ch.px(30), ch.py(2.6) + 16, "the wing can't", 11, "middle", "brand"))
    c.add(text(ch.px(30), ch.py(2.6) + 30, "make more lift", 11, "middle", "brand"))
    c.add(text(ch.px(VS) - 6, ch.py(1) + 16, "Vs 52 kt", 11, "end", "brand"))
    # the two pulls
    c.add(arrow(ch.px(74), ch.py(1), ch.px(74), ch.py((74 / VS) ** 2) + 6, "ok", MAIN))
    c.add(multiline(ch.px(74), ch.py(0.72), ["below VA: a full", "pull stalls first"], 11, "middle", "ok-fg", weight=600))
    c.add(arrow(ch.px(110), ch.py(1), ch.px(110), ch.py(4.7), "bad", MAIN))
    c.add(multiline(ch.px(110), ch.py(0.72), ["above VA: limit", "load before stall"], 11, "middle", "bad", weight=600))
    c.add(text(600, 434, "VNO and VNE positions schematic; stall speed and VA from the note's example.", 11, "end", "fg-faint"))
    return c


@chart
def controllability_check() -> Canvas:
    c = Canvas("Controllability check after damage", "A speed scale from the note's worked example. After a bird strike dents the left wing, at "
               "3000 ft in the landing configuration full right aileron is needed at 65 knots to stop a roll to the left. The normal approach "
               "speed is 65 knots, so the approach is flown at about 75 to 80 knots.", height=236, prefix="cc")
    x0, x1 = 60, 600
    vmin, vmax = 50, 95
    px = lambda v: x0 + (v - vmin) / (vmax - vmin) * (x1 - x0)
    Y = 130
    c.add(rect(x0, Y - 16, px(65) - x0, 32, "bad-soft", None))
    c.add(rect(px(65), Y - 16, px(75) - px(65), 32, "warn-soft", None))
    c.add(rect(px(75), Y - 16, px(80) - px(75), 32, "ok", None))
    c.add(rect(px(80), Y - 16, x1 - px(80), 32, "ok-soft", None))
    c.add(rect(x0, Y - 16, x1 - x0, 32, None, "fg-muted", 1, rx=3))
    for v in range(50, 96, 5):
        c.add(line(px(v), Y + 16, px(v), Y + 24, "fg-muted", THIN))
        c.add(num(px(v), Y + 38, str(v), 11, "middle", "fg-muted"))
    c.add(text((x0 + x1) / 2, Y + 58, "indicated airspeed (kt), landing flap set, at 3000 ft", 12, "middle", "fg-muted"))
    c.add(line(px(65), Y - 30, px(65), Y + 16, "bad", MAIN))
    c.add(multiline(px(65) - 8, 40, ["65 kt: full right aileron to", "stop the roll = minimum safe", "speed (also the normal approach)"], 11, "end", "bad", weight=600))
    c.add(line(px(65), 74, px(65), Y - 30, "bad", THIN))
    c.add(multiline(px(77.5), 40, ["Plan the approach", "at 75 to 80 kt"], 13, "middle", "ok-fg", weight=700))
    c.add(line(px(77.5), 64, px(77.5), Y - 18, "ok", THIN))
    c.add(text(px(70), Y + 5, "no margin", 11, "middle", "warn-fg", weight=600))
    c.add(text(px(57.5), Y + 5, "control runs out", 11, "middle", "bad-fg", weight=600))
    c.add(text(x0, 222, "Fly faster than normal, gentle bank, longest runway; do not trust the stall warning.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 4.1 take-off and landing performance
@chart
def runway_slope_and_surface_effects() -> Canvas:
    c = Canvas("Slope and surface: what they do to the distances", "A table of the effect of runway slope and surface on take-off distance, "
               "landing distance and take-off climb. Uphill: take-off longer, landing shorter, climb reduced relative to rising ground. Downhill: "
               "take-off shorter, landing longer, climb unchanged with terrain falling away. Wet sealed: little change for take-off, landing "
               "longer. Wet grass: both longer. Slush or waterlogged: both greatly longer, climb unchanged but starting later.", height=400, prefix="rss")
    cols = ["Take-off distance", "Landing distance", "Take-off climb"]
    rows = [("Uphill", "slope_up", [("longer", "bad", 1), ("shorter", "ok", -1), ("reduced vs rising ground", "warn", 0)]),
            ("Downhill", "slope_down", [("shorter", "ok", -1), ("longer", "bad", 1), ("unchanged, terrain falls away", "fg", 0)]),
            ("Wet sealed", "wet", [("little change", "fg", 0), ("longer", "bad", 1), ("unchanged", "fg", 0)]),
            ("Wet grass", "grass", [("longer", "bad", 1), ("longer", "bad", 1), ("unchanged", "fg", 0)]),
            ("Slush", "slush", [("MUCH longer", "bad", 2), ("MUCH longer", "bad", 2), ("unchanged, starts later", "fg", 0)])]
    X = [150, 290, 430]
    for j, h in enumerate(cols):
        c.add(text(X[j] + 64, 32, h, 13, "middle", "fg", weight=700))
    for i, (name, icon, cells) in enumerate(rows):
        y = 48 + i * 64
        c.add(rect(16, y, 608, 56, "surface-2", None, rx=8))
        c.add(text(70, y + 33, name, 13, "start", "fg", weight=600))
        ix, iy = 40, y + 36
        if icon == "slope_up":
            c.add(path(f"M{ix - 18} {iy} L{ix + 18} {iy - 12}", "fg", None, MAIN), arrow(ix - 12, iy - 10, ix + 4, iy - 15, "brand", SECOND))
        elif icon == "slope_down":
            c.add(path(f"M{ix - 18} {iy - 12} L{ix + 18} {iy}", "fg", None, MAIN), arrow(ix - 12, iy - 15, ix + 4, iy - 10, "brand", SECOND))
        else:
            c.add(line(ix - 18, iy - 4, ix + 18, iy - 4, "fg", MAIN))
            if icon in ("wet", "slush"):
                for k in range(3 if icon == "wet" else 5):
                    c.add(ellipse(ix - 12 + k * (12 if icon == "wet" else 6), iy - 9, 4, 2, "sky-soft", "sky-fg", 1))
            if icon == "grass":
                for k in range(5):
                    c.add(line(ix - 14 + k * 7, iy - 4, ix - 12 + k * 7, iy - 11, "ok", 1.5))
        for j, (txt, colour, dirn) in enumerate(cells):
            cx = X[j] + 64
            if dirn:
                sym = "▲▲" if dirn == 2 else ("▲" if dirn > 0 else "▼")
                c.add(text(cx, y + 26, sym, 14, "middle", colour if colour != "fg" else "fg-muted", weight=700))
                c.add(text(cx, y + 45, txt, 12, "middle", f"{colour}-fg" if colour in ("ok", "warn", "bad") else "fg", weight=600))
            else:
                words = txt.split(", ")
                c.add(multiline(cx, y + 26 if len(words) > 1 else y + 33, words, 11, "middle", f"{colour}-fg" if colour in ("ok", "warn", "bad") else "fg-muted"))
    c.add(text(16, 386, "Slope works opposite ways for take-off and landing; wet and slush are bad for both, slush the worst.", 12, "start", "fg-muted"))
    return c


@chart
def runway_slope_take_off_and_landing() -> Canvas:
    c = Canvas("Uphill or downhill?", "Two side views of a sloping runway. Taking off uphill, part of the thrust climbs the slope, so the run is "
               "longer: a 2 percent upslope can add around 10 percent to the take-off distance. Landing uphill, the slope helps the aeroplane "
               "slow down, so the landing roll is shorter. With light wind, land uphill and take off downhill.", height=330, prefix="rst")
    for i, (head, sub, colour, up_takeoff) in enumerate((("Take off uphill", "longer run: about +10% for a 2% upslope", "bad", True),
                                                          ("Land uphill", "shorter roll: the slope helps you stop", "ok", False))):
        x0 = 16 + i * 312
        c.add(rect(x0, 14, 296, 260, f"{colour}-soft", None, rx=10, fill_opacity=0.4))
        c.add(text(x0 + 148, 42, head, 16, "middle", "bad" if colour == "bad" else "ok-fg", weight=700))
        c.add(text(x0 + 148, 60, sub, 11, "middle", "fg-muted"))
        g0, g1 = (x0 + 20, 220), (x0 + 276, 180)
        c.add(path(f"M{g0[0]} {g0[1]} L{g1[0]} {g1[1]} L{g1[0]} 262 L{g0[0]} 262 Z", None, "surface-2"))
        c.add(line(*g0, *g1, "fg-muted", MAIN))
        ang = math.degrees(math.atan2(g0[1] - g1[1], g1[0] - g0[0]))
        gy = lambda x: g0[1] - (x - g0[0]) * (g0[1] - g1[1]) / (g1[0] - g0[0])
        if up_takeoff:
            c.add(plane_side(x0 + 90, gy(x0 + 90) - 9, 0.6, "fg", pitch=ang))
            c.add(arrow(x0 + 128, 186, x0 + 220, 172, "brand", MAIN))
            c.add(text(x0 + 176, 160, "accelerates slowly", 11, "middle", "brand", weight=600))
        else:
            c.add(plane_side(x0 + 190, gy(x0 + 190) - 9, 0.6, "fg", pitch=ang))
            c.add(path(arc_path(x0 + 120, 120, 80, 150, 100), "fg-faint", None, THIN, dash=DASH, arrow_end=True))
            c.add(arrow(x0 + 150, gy(x0 + 150) - 14, x0 + 110, gy(x0 + 110) - 14, "ok", MAIN))
            c.add(text(x0 + 130, gy(x0 + 130) + 24, "slope slows you", 11, "middle", "ok-fg", weight=600))
    c.add(text(16, 300, "Light wind: land uphill, take off downhill. A downhill landing with a tailwind is the classic overrun.", 12, "start", "fg-muted"))
    c.add(text(16, 318, "Wind usually wins over slope unless the slope is steep: use the chart's slope correction.", 12, "start", "fg-muted"))
    return c


# ---------------------------------------------------------------- 4.2 aircraft limitations
@chart
def flap_speeds_vfo_vfe() -> Canvas:
    c = Canvas("VFO and VFE on the speed scale", "A speed scale showing the white arc from VSO, the full-flap stall speed at maximum weight, up to "
               "VFE, the maximum speed with flap extended. On some aeroplanes VFO, the maximum speed for moving the flap, is lower than VFE: "
               "slow to VFO before selecting flap, then VFE is the limit for flying with it out.", height=250, prefix="fsv")
    x0, x1, Y = 40, 600, 120
    VSO, VFO, VFE, VNO, VNE = 100, 220, 350, 470, 560
    c.add(rect(x0, Y - 14, x1 - x0, 28, "surface-2", "line-strong", 1, rx=4))
    c.add(rect(VSO, Y - 14, VFE - VSO, 12, "surface", "fg", 1.5))
    c.add(text((VSO + VFE) / 2, Y - 22, "white arc: flap range", 12, "middle", "fg", weight=600))
    c.add(rect(VNO, Y + 2, VNE - VNO, 12, "warn", None))
    c.add(rect(VSO + 40, Y + 2, VNO - VSO - 40, 12, "ok", None))
    c.add(line(VNE, Y - 16, VNE, Y + 16, "bad", 3))
    c.add(text((VNO + VNE) / 2, Y - 22, "yellow arc", 11, "middle", "warn-fg"))
    c.add(text(VNE, Y + 32, "VNE", 11, "middle", "bad", weight=600))
    for x, lab, colour, dy in ((VSO, "VSO", "fg", 0), (VFO, "VFO", "brand", 0), (VFE, "VFE", "fg", 0)):
        c.add(line(x, Y - (14 if lab == "VFO" else 30), x, Y + 40, colour, MAIN if lab != "VSO" else SECOND))
        c.add(text(x, Y + 56, lab, 14, "middle", colour, weight=700))
    c.add(multiline(VSO, Y + 74, ["full-flap stall,", "max weight"], 11, "middle", "fg-muted"))
    c.add(multiline(VFO, Y + 74, ["max speed to", "MOVE the flap"], 11, "middle", "brand"))
    c.add(multiline(VFE, Y + 74, ["max speed with", "flap EXTENDED"], 11, "middle", "fg"))
    c.add(rect(x0, 30, 360, 46, "brand-soft", None, rx=8))
    c.add(text(x0 + 12, 50, "Slow to VFO, select the flap, then you may", 12, "start", "brand-fg", weight=600))
    c.add(text(x0 + 12, 66, "fly up to VFE with it out. Often VFO = VFE.", 12, "start", "brand-fg", weight=600))
    c.add(text(x0, 236, "Schematic scale. Never select flap in the yellow arc; many POHs give a higher VFE for the first stage.", 11, "start", "fg-faint"))
    return c
