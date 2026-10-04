"""Diagram and widget references in notes (app/seed/visuals.py) and their lint rules."""
from __future__ import annotations

import logging
from pathlib import Path

from app.seed.loader import render_markdown
from app.seed import workbook
from app.seed.visuals import find_refs, lint_svg, lint_widget, visual_path

GOOD_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360" role="img" data-prefix="t">
<title>Test</title><style>.t-a{animation:t-spin 2s linear infinite}@keyframes t-spin{to{transform:rotate(360deg)}}</style>
<defs><marker id="arrow"><path fill="var(--color-fg)" d="M0 0L6 3L0 6z"/></marker></defs>
<line x1="0" y1="0" x2="100" y2="100" stroke="var(--color-brand)" marker-end="url(#arrow)"/>
<text x="10" y="20" font-size="13" fill="var(--color-fg)">hello</text></svg>"""
GOOD_WIDGET = """<div class="widget" x-data="{ bank: 30 }"><p x-text="bank"></p>
<p class="widget-notice"><strong>What to notice.</strong> Load factor doubles at 60°.</p></div>"""


def make_content(tmp_path: Path) -> Path:
    (tmp_path / "diagrams").mkdir()
    (tmp_path / "widgets").mkdir()
    (tmp_path / "diagrams" / "good.svg").write_text('<?xml version="1.0"?>\n' + GOOD_SVG, encoding="utf-8")
    (tmp_path / "widgets" / "bank.html").write_text(GOOD_WIDGET, encoding="utf-8")
    return tmp_path


def test_diagram_ref_inlines_svg_in_figure(tmp_path: Path) -> None:
    html = render_markdown("Before.\n\n![Why it turns](diagram:good \"Lift tilts\")\n\nAfter.", make_content(tmp_path))
    assert '<figure class="visual visual-diagram" data-visual="diagram:good">' in html
    assert "<svg" in html and "<?xml" not in html
    assert "<figcaption>Why it turns<span class=\"visual-notice\">Lift tilts</span></figcaption>" in html
    assert "<p><figure" not in html and "<p>Before.</p>" in html and "<p>After.</p>" in html
    # ids are prefixed with the slug so two diagrams can both define "arrow"
    assert 'id="good-arrow"' in html and "url(#good-arrow)" in html


def test_widget_ref_inlines_html(tmp_path: Path) -> None:
    html = render_markdown("![Try it](widget:bank)", make_content(tmp_path))
    assert '<figure class="visual visual-widget" data-visual="widget:bank">' in html
    assert 'x-data="{ bank: 30 }"' in html
    assert "<figcaption>Try it</figcaption>" in html


def test_unknown_slug_is_placeholder_not_error(tmp_path: Path, caplog) -> None:
    with caplog.at_level(logging.WARNING):
        html = render_markdown("![Soon](diagram:not-there)", make_content(tmp_path))
    assert 'class="visual visual-missing"' in html and "not-there" in html
    assert "not found" in caplog.text


def test_ordinary_images_untouched(tmp_path: Path) -> None:
    html = render_markdown("![](https://example.com/x.png)", make_content(tmp_path))
    assert "<img" in html and "https://example.com/x.png" in html and "<figure" not in html


def test_find_refs() -> None:
    body = "![a](diagram:one) text ![b](widget:two \"notice\") ![c](http://x/y.png) ![d](workbook:fig9)"
    assert find_refs(body) == [("diagram", "one"), ("widget", "two"), ("workbook", "fig9")]


def test_workbook_ref_shows_page_image_with_credit(tmp_path: Path) -> None:
    html = render_markdown("![Which envelope?](workbook:fig9 \"Aft limit 3,004 mm\")", make_content(tmp_path))
    assert '<figure class="visual visual-workbook" data-visual="workbook:fig9">' in html
    assert 'src="/static/workbook/p15.webp"' in html
    assert "rpl-ppl-cpl-aeroplane-workbook.pdf#page=15" in html and "CC BY 4.0" in html
    assert "<figcaption>Which envelope?<span class=\"visual-notice\">Aft limit 3,004 mm</span></figcaption>" in html


def test_workbook_pages_rendered_for_every_figure() -> None:
    missing = [slug for slug in workbook.FIGURES if not visual_path(Path("content"), "workbook", slug).is_file()]
    assert not missing, f"run python -m tools.workbook.render; missing pages for {missing}"


def test_unknown_workbook_figure_is_placeholder(tmp_path: Path) -> None:
    html = render_markdown("![Soon](workbook:fig99)", make_content(tmp_path))
    assert 'class="visual visual-missing"' in html


def test_lint_svg_passes_good_file(tmp_path: Path) -> None:
    make_content(tmp_path)
    assert lint_svg(tmp_path / "diagrams" / "good.svg") == []


def test_lint_svg_catches_problems(tmp_path: Path) -> None:
    bad = tmp_path / "bad-one.svg"
    bad.write_text('<svg xmlns="http://www.w3.org/2000/svg" role="img"><rect fill="#ff0000"/>'
                   '<text font-size="9">x</text><style>.oops{} @keyframes spin{}</style></svg>', encoding="utf-8")
    problems = lint_svg(bad)
    joined = "\n".join(problems)
    assert "viewBox" in joined
    assert "<title>" in joined
    assert "#ff0000" in joined or "tokens only" in joined
    assert "below 11px" in joined
    assert '"bad-one-"' in joined


def test_lint_widget(tmp_path: Path) -> None:
    make_content(tmp_path)
    assert lint_widget(tmp_path / "widgets" / "bank.html") == []
    bad = tmp_path / "widgets" / "bad.html"
    bad.write_text('<div><script src="https://cdn.example/x.js"></script></div>', encoding="utf-8")
    joined = "\n".join(lint_widget(bad))
    assert "x-data" in joined and "network" in joined and "What to notice" in joined
