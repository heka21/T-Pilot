"""Write every generated diagram into content/diagrams/. Idempotent.

    python -m tools.diagrams.build [slug ...]

Generators live in tools/diagrams/charts.py and figures.py (shared exemplars) and one module per unit in
tools/diagrams/units/ (for example units/bakc_engines.py); every module is imported so its @chart functions register.
"""
from __future__ import annotations

import importlib
import pkgutil
import sys

from tools.diagrams import charts, figures, units  # noqa: F401 (registers generators)
from tools.diagrams.charts import CHARTS
from tools.diagrams.svg import DIAGRAMS

for mod in pkgutil.iter_modules(units.__path__):
    importlib.import_module(f"tools.diagrams.units.{mod.name}")


def main(argv: list[str]) -> int:
    wanted = set(argv) or set(CHARTS)
    unknown = wanted - set(CHARTS)
    if unknown:
        print("unknown:", *sorted(unknown))
        return 1
    for slug in sorted(wanted):
        path = CHARTS[slug]().write(slug, DIAGRAMS)
        print(path.relative_to(DIAGRAMS.parents[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
