"""Reference pages rendered from content/reference/*.md."""
from __future__ import annotations

import os
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.seed.loader import render_markdown, split_frontmatter
from app.templating import templates

router = APIRouter(prefix="/reference", tags=["reference"])

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def reference_dir() -> Path:
    return Path(os.environ.get("CONTENT_DIR", "content")) / "reference"


def load_page(path: Path) -> dict:
    meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    return {"slug": path.stem, "title": meta.get("title") or path.stem.replace("-", " ").capitalize(),
            "summary": meta.get("summary", ""), "order": meta.get("order", 99), "body": body}


def list_pages() -> list[dict]:
    pages = [load_page(p) for p in sorted(reference_dir().glob("*.md"))]
    return sorted(pages, key=lambda p: (p["order"], p["title"]))


@router.get("", response_class=HTMLResponse)
def reference_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "reference_index.html", {"pages": list_pages()})


@router.get("/{slug}", response_class=HTMLResponse)
def reference_page(slug: str, request: Request) -> HTMLResponse:
    path = reference_dir() / f"{slug}.md"
    if not SLUG_RE.match(slug) or not path.is_file():
        raise HTTPException(status_code=404, detail="Reference page not found")
    page = load_page(path)
    page["html"] = render_markdown(page["body"], reference_dir().parent)
    return templates.TemplateResponse(request, "reference.html", {"page": page, "pages": list_pages()})
