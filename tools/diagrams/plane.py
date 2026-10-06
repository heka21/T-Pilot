"""Print one of the shared aeroplane silhouettes as SVG markup, for pasting into a hand-written widget or diagram.

    python -m tools.diagrams.plane side|top|rear|airliner [--scale S] [--x X] [--y Y] [--pitch P] [--bank B] [--heading H]
                                   [--color TOKEN] [--fill TOKEN] [--no-gear] [--no-prop] [--cls CLASS]

The output is exactly what the generators get from tools/diagrams/svg.py (plane_side, plane_top, plane_rear,
airliner_rear): one <g> with the CG (fuselage centre for the airliner) at (--x, --y), colours as var(--color-TOKEN).
Wrap it in your own <g :transform="..."> to move or rotate it with Alpine; keep the pasted <g> as it is so the
widget stays in step with the diagrams. Re-run and re-paste when the silhouettes change.

    python -m tools.diagrams.plane rear --scale 1.5              # bank-angle.html
    python -m tools.diagrams.plane side --scale 0.5 --y -7 --color brand
"""
from __future__ import annotations

import argparse
import sys

from tools.diagrams.svg import airliner_rear, plane_rear, plane_side, plane_top

# which options each view accepts (beyond scale, x, y, color, fill, cls)
EXTRA = {"side": {"pitch", "no_gear", "no_prop"}, "top": {"heading"}, "rear": {"bank"}, "airliner": set()}
FLAGS = {"pitch": "--pitch", "no_gear": "--no-gear", "no_prop": "--no-prop", "heading": "--heading", "bank": "--bank"}


def parse(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m tools.diagrams.plane", description="Print a shared aeroplane silhouette as an SVG <g>.")
    p.add_argument("view", choices=sorted(EXTRA), help="side (from the left, nose right), top (plan view), rear (from behind), airliner (twin-jet from behind)")
    p.add_argument("--scale", type=float, default=1.0, help="1 = about 100 units long or across (default 1)")
    p.add_argument("--x", type=float, default=0.0, help="CG x (default 0)")
    p.add_argument("--y", type=float, default=0.0, help="CG y (default 0)")
    p.add_argument("--pitch", type=float, default=None, help="side: nose-up degrees")
    p.add_argument("--bank", type=float, default=None, help="rear: degrees, positive = left wing down")
    p.add_argument("--heading", type=float, default=None, help="top: degrees, 0 = up the page, 90 = right (default 90)")
    p.add_argument("--color", default="fg", help="outline colour token (default fg)")
    p.add_argument("--fill", default="surface", help="fill colour token (default surface)")
    p.add_argument("--no-gear", dest="no_gear", action="store_true", help="side: leave the wheels off")
    p.add_argument("--no-prop", dest="no_prop", action="store_true", help="side: leave the propeller off")
    p.add_argument("--cls", default=None, help="class attribute on the <g>")
    a = p.parse_args(argv)
    for opt, flag in FLAGS.items():
        used = getattr(a, opt) not in (None, False)
        if used and opt not in EXTRA[a.view]:
            p.error(f"{flag} does not apply to the {a.view} view")
    return a


def markup(a: argparse.Namespace) -> str:
    common = dict(color=a.color, fill=a.fill, cls=a.cls)
    if a.view == "side":
        return plane_side(a.x, a.y, a.scale, pitch=a.pitch or 0, prop=not a.no_prop, gear=not a.no_gear, **common)
    if a.view == "top":
        return plane_top(a.x, a.y, a.scale, heading=90 if a.heading is None else a.heading, **common)
    if a.view == "rear":
        return plane_rear(a.x, a.y, a.scale, bank=a.bank or 0, **common)
    return airliner_rear(a.x, a.y, a.scale, **common)


def main(argv: list[str]) -> int:
    print(markup(parse(argv)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
