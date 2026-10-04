"""Render the CASA workbook pages that hold figures to app/static/workbook/pNN.webp. Idempotent.

    python -m tools.workbook.render

Needs poppler's `pdftoppm` (brew install poppler) and `cwebp` (brew install webp). 150 dpi, lossless WebP:
sharp enough to read a chart line by line, about 75 KB a page.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from app.seed.workbook import FIRST_PAGE, LAST_PAGE

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "app" / "static" / "rpl-ppl-cpl-aeroplane-workbook.pdf"
OUT = ROOT / "app" / "static" / "workbook"
DPI = 150


def main() -> int:
    for tool in ("pdftoppm", "cwebp"):
        if not shutil.which(tool):
            print(f"{tool} not found: brew install poppler webp")
            return 1
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", str(DPI), "-png", "-f", str(FIRST_PAGE), "-l", str(LAST_PAGE), str(PDF),
                        f"{tmp}/p"], check=True)
        for png in sorted(Path(tmp).glob("p-*.png")):
            page = int(png.stem.split("-")[1])
            dest = OUT / f"p{page:02d}.webp"
            subprocess.run(["cwebp", "-quiet", "-lossless", "-z", "9", str(png), "-o", str(dest)], check=True)
            print(dest.relative_to(ROOT), f"{dest.stat().st_size // 1000} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
