"""Visuals in notes: inline SVG diagrams and HTML widgets referenced with image syntax.

    ![Why does stall speed rise in a turn?](diagram:stall-speed-vs-bank "What to notice: ...")
    ![Explore bank angle, load factor and stall speed](widget:bank-angle)

At render time the Markdown extension replaces the <img> with

    <figure class="visual visual-diagram"> ...content/diagrams/<slug>.svg... <figcaption>caption</figcaption></figure>
    <figure class="visual visual-widget">  ...content/widgets/<slug>.html...  <figcaption>caption</figcaption></figure>

The optional image title becomes a "What to notice" line under the caption. An unknown slug logs a warning
and renders a dashed placeholder figure instead of failing the seed. SVG ids are prefixed with the slug so
the same marker or gradient id can be used in every diagram without clashing on one page.

The lint functions are shared by `python -m app.seed.check_content`; the rules are in content/diagrams/README.md.
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from markdown import Extension, Markdown
from markdown.treeprocessors import Treeprocessor
import xml.etree.ElementTree as etree

log = logging.getLogger(__name__)

REF_RE = re.compile(r"!\[[^\]]*\]\((diagram|widget):([a-z0-9][a-z0-9-]*)(?:\s+\"[^\"]*\")?\)")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
XML_PROLOG_RE = re.compile(r"^\s*<\?xml[^>]*\?>\s*", re.S)
SVG_NS = "http://www.w3.org/2000/svg"
MAX_SVG_BYTES = 40_000
MAX_WIDGET_BYTES = 80_000
MIN_FONT_PX = 11
ALLOWED_PAINT = {"none", "currentColor", "inherit", "transparent", "context-stroke", "context-fill"}
PAINT_ATTRS = ("fill", "stroke", "stop-color", "color", "flood-color", "lighting-color")
HEX_RE = re.compile(r"(?<![\w#])#[0-9a-fA-F]{3,8}\b")
FONT_SIZE_RE = re.compile(r"font-size\s*[:=]\s*\"?(\d+(?:\.\d+)?)(px)?")


def visual_path(content_dir: Path, kind: str, slug: str) -> Path:
    return Path(content_dir) / ("diagrams" if kind == "diagram" else "widgets") / f"{slug}.{'svg' if kind == 'diagram' else 'html'}"


def find_refs(markdown_text: str) -> list[tuple[str, str]]:
    """All (kind, slug) references in a note body, in document order."""
    return [(m.group(1), m.group(2)) for m in REF_RE.finditer(markdown_text)]


def _prefix_ids(svg: str, slug: str) -> str:
    ids = set(re.findall(r'\bid="([^"]+)"', svg))
    if not ids:
        return svg
    alt = "|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True))
    svg = re.sub(rf'\bid="({alt})"', lambda m: f'id="{slug}-{m.group(1)}"', svg)
    svg = re.sub(rf'url\(#({alt})\)', lambda m: f'url(#{slug}-{m.group(1)})', svg)
    svg = re.sub(rf'(xlink:)?href="#({alt})"', lambda m: f'{m.group(1) or ""}href="#{slug}-{m.group(2)}"', svg)
    return svg


def load_visual(content_dir: Path, kind: str, slug: str) -> str | None:
    path = visual_path(content_dir, kind, slug)
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    if kind == "diagram":
        text = _prefix_ids(XML_PROLOG_RE.sub("", text), slug)
    return text.strip()


class VisualsTreeprocessor(Treeprocessor):
    def __init__(self, md: Markdown, content_dir: Path):
        super().__init__(md)
        self.content_dir = Path(content_dir)

    def run(self, root: etree.Element) -> None:
        parents = {child: parent for parent in root.iter() for child in parent}
        for img in list(root.iter("img")):
            src = img.get("src", "")
            kind, sep, slug = src.partition(":")
            if kind not in ("diagram", "widget") or not sep or not SLUG_RE.match(slug):
                continue
            figure = self._figure(kind, slug, img.get("alt", ""), img.get("title"))
            parent = parents[img]
            alone = (parent.tag == "p" and len(parent) == 1 and not (parent.text or "").strip()
                     and not (img.tail or "").strip() and parent in parents)
            if alone:
                grand = parents[parent]
                idx = list(grand).index(parent)
                figure.tail = parent.tail
                grand.remove(parent)
                grand.insert(idx, figure)
            else:
                idx = list(parent).index(img)
                figure.tail = img.tail
                parent.remove(img)
                parent.insert(idx, figure)

    def _figure(self, kind: str, slug: str, caption: str, notice: str | None) -> etree.Element:
        html = load_visual(self.content_dir, kind, slug)
        if html is None:
            log.warning("visual %s:%s not found under %s", kind, slug, self.content_dir)
            figure = etree.Element("figure", {"class": "visual visual-missing", "data-visual": f"{kind}:{slug}"})
            p = etree.SubElement(figure, "p")
            p.text = f"Visual not available yet: {kind} “{slug}”"
        else:
            figure = etree.Element("figure", {"class": f"visual visual-{kind}", "data-visual": f"{kind}:{slug}"})
            figure.text = self.md.htmlStash.store(html)
        if caption or notice:
            cap = etree.SubElement(figure, "figcaption")
            cap.text = caption
            if notice:
                n = etree.SubElement(cap, "span", {"class": "visual-notice"})
                n.text = notice
        return figure


class VisualsExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {"content_dir": ["content", "Directory holding diagrams/ and widgets/"]}
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Markdown) -> None:
        md.treeprocessors.register(VisualsTreeprocessor(md, Path(self.getConfig("content_dir"))), "visuals", 15)


def makeExtension(**kwargs) -> VisualsExtension:  # noqa: N802 (python-markdown entry point name)
    return VisualsExtension(**kwargs)


# ---------------------------------------------------------------- lint (shared with check_content)
def _style_blocks(svg_text: str) -> list[str]:
    return re.findall(r"<style[^>]*>(.*?)</style>", svg_text, re.S)


def lint_svg(path: Path) -> list[str]:
    """Return problems with a diagram file; empty list when it passes."""
    problems: list[str] = []
    slug = path.stem
    if not SLUG_RE.match(slug):
        problems.append("file name must be a lowercase slug (a-z, 0-9, hyphen)")
    raw = path.read_bytes()
    if len(raw) > MAX_SVG_BYTES:
        problems.append(f"file is {len(raw) // 1000} KB; keep diagrams under {MAX_SVG_BYTES // 1000} KB")
    text = raw.decode("utf-8", errors="replace")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return problems + [f"not well-formed XML: {e}"]
    if root.tag != f"{{{SVG_NS}}}svg":
        return problems + ['root element must be <svg xmlns="http://www.w3.org/2000/svg">']
    if not root.get("viewBox"):
        problems.append("root <svg> needs a viewBox (normally 0 0 640 360)")
    if root.get("role") != "img":
        problems.append('root <svg> needs role="img"')
    if root.find(f"{{{SVG_NS}}}title") is None:
        problems.append("needs a <title> as the first child of <svg>")
    for tag in ("image", "script", "foreignObject"):
        if root.find(f".//{{{SVG_NS}}}{tag}") is not None:
            problems.append(f"<{tag}> is not allowed in diagrams")
    for el in root.iter():
        for attr in PAINT_ATTRS:
            v = el.get(attr)
            if v and not _paint_ok(v):
                problems.append(f"<{el.tag.split('}')[1]} {attr}=\"{v}\">: use var(--color-…) tokens only")
        style = el.get("style", "")
        for prop, v in re.findall(r"(fill|stroke|stop-color|color)\s*:\s*([^;]+)", style):
            if not _paint_ok(v.strip()):
                problems.append(f"style {prop}: {v.strip()}: use var(--color-…) tokens only")
    for m in HEX_RE.finditer(text):
        problems.append(f"hard-coded colour {m.group(0)}: use var(--color-…) tokens only")
        break
    for size, _px in FONT_SIZE_RE.findall(text):
        if float(size) < MIN_FONT_PX:
            problems.append(f"font-size {size} is below {MIN_FONT_PX}px")
            break
    prefix = root.get("data-prefix") or slug
    for block in _style_blocks(text):
        if re.search(r"#[A-Za-z_]", block):
            problems.append("<style> must not use #id selectors (ids are prefixed when inlined); use classes")
        for cls in set(re.findall(r"\.([A-Za-z_][\w-]*)", block)):
            if not cls.startswith(prefix + "-"):
                problems.append(f"<style> class .{cls} must start with \"{prefix}-\" so it cannot clash with another diagram on the page")
                break
        for name in set(re.findall(r"@keyframes\s+([\w-]+)", block)):
            if not name.startswith(prefix + "-"):
                problems.append(f"@keyframes {name} must start with \"{prefix}-\"")
                break
        if "animation" in block and "prefers-reduced-motion" not in block and "@keyframes" in block:
            pass  # the app stylesheet disables .visual animations under reduced motion
    return problems


def _paint_ok(v: str) -> bool:
    v = v.strip()
    return v in ALLOWED_PAINT or v.startswith("var(--color-") or v.startswith("url(#") or v.startswith("color-mix(")


def lint_widget(path: Path, static_dir: Path | None = None) -> list[str]:
    """Return problems with a widget file; empty list when it passes."""
    problems: list[str] = []
    if not SLUG_RE.match(path.stem):
        problems.append("file name must be a lowercase slug (a-z, 0-9, hyphen)")
    raw = path.read_bytes()
    if len(raw) > MAX_WIDGET_BYTES:
        problems.append(f"file is {len(raw) // 1000} KB; keep widgets under {MAX_WIDGET_BYTES // 1000} KB")
    text = raw.decode("utf-8", errors="replace")
    if "x-data" not in text and "data-widget" not in text:
        problems.append("widget needs an Alpine x-data root or a data-widget=\"name\" root")
    if re.search(r"(src|href)=\"https?://", text):
        problems.append("widgets must not load anything from the network")
    for m in HEX_RE.finditer(re.sub(r"<script.*?</script>", "", text, flags=re.S)):
        problems.append(f"hard-coded colour {m.group(0)}: use var(--color-…) tokens or theme classes")
        break
    if "widget-notice" not in text and "What to notice" not in text:
        problems.append("widget needs a 'What to notice' line (class widget-notice)")
    for name in re.findall(r'data-widget="([^"]+)"', text):
        if static_dir is not None:
            registered = any(f'register("{name}"' in p.read_text(encoding="utf-8") or f"register('{name}'" in p.read_text(encoding="utf-8")
                             for p in Path(static_dir).glob("*.js"))
            if not registered:
                problems.append(f'data-widget="{name}" is not registered in app/static/*.js (CasaWidgets.register)')
    return problems
