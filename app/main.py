"""FastAPI application factory."""
from __future__ import annotations

import importlib
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import SessionLocal, init_db
from app.seed.loader import seed_all
from app.services import search

log = logging.getLogger("app")

STATIC_DIR = Path(__file__).parent / "static"
ROUTER_MODULES = ["dashboard", "syllabus", "notes", "quiz", "exam", "cards", "planner", "progress", "reference", "search", "annotations", "equations", "mistakes", "diagnostic"]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    content_dir = Path(os.environ.get("CONTENT_DIR", "content"))
    with SessionLocal() as session:
        summary = seed_all(session, content_dir)
    search.reset()
    log.info("Seeded content from %s: %s", content_dir, summary)
    yield


def include_routers(app: FastAPI) -> None:
    for name in ROUTER_MODULES:
        module_name = f"app.routers.{name}"
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            log.warning("Skipping router %s: %s", module_name, exc)
            continue
        router = getattr(module, "router", None)
        if router is not None:
            app.include_router(router)


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    app = FastAPI(title="CASA Theory", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    include_routers(app)
    return app


app = create_app()
