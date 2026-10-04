"""The CASA RPL, PPL & CPL (Aeroplane) Workbook v3.0a: which page holds which figure.

The workbook (app/static/rpl-ppl-cpl-aeroplane-workbook.pdf) is CC BY 4.0. Pages 4 to 21 are rendered to
app/static/workbook/pNN.webp by `python -m tools.workbook.render`. Notes show a page with

    ![Which chart does the exam use?](workbook:fig9 "What to notice: ...")

and a question with `workbook_page: 15` shows the same image in the quiz.
"""
from __future__ import annotations

PDF_URL = "/static/rpl-ppl-cpl-aeroplane-workbook.pdf"
ATTRIBUTION = "CASA RPL, PPL & CPL (Aeroplane) Workbook v3.0a, licensed CC BY 4.0"
FIRST_PAGE, LAST_PAGE = 4, 21

# id -> (page, title). Ids are what notes write after `workbook:`.
FIGURES: dict[str, tuple[int, str]] = {
    "fig1-2": (4, "Figs 1 and 2: aerodrome markers and markings"),
    "fig3": (5, "Fig 3: take-off weight chart"),
    "fig4": (6, "Fig 4: landing distance chart"),
    "fig5": (7, "Fig 5: take-off weight chart"),
    "fig6": (8, "Fig 6: landing chart"),
    "alpha-instructions": (9, "Loading system ALPHA: instructions"),
    "fig7": (10, "Fig 7: loading system ALPHA"),
    "bravo-instructions": (11, "Loading system BRAVO: instructions"),
    "fig8": (12, "Fig 8: loading system BRAVO"),
    "charlie-instructions": (13, "Loading system CHARLIE: instructions"),
    "charlie-index-units": (14, "Loading system CHARLIE: index units"),
    "fig9": (15, "Fig 9: loading system CHARLIE, CG envelope"),
    "echo-instructions": (16, "Loading system ECHO: instructions"),
    "echo-instructions-2": (17, "Loading system ECHO: instructions (continued)"),
    "fig10": (18, "Fig 10: loading system ECHO, index units"),
    "fig11": (19, "Fig 11: loading system ECHO, CG envelope"),
    "fig12": (20, "Fig 12: take-off weight chart, aircraft ECHO"),
    "fig13": (21, "Fig 13: landing weight chart, aircraft ECHO"),
}
PAGE_TITLES: dict[int, str] = {page: title for page, title in FIGURES.values()}


def image_url(page: int) -> str:
    return f"/static/workbook/p{page:02d}.webp"


def pdf_url(page: int) -> str:
    return f"{PDF_URL}#page={page}"
