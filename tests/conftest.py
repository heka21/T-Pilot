"""Point the app at a throwaway SQLite DB before anything from app/ is imported."""
from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

_TMP_DIR = tempfile.mkdtemp(prefix="casa-theory-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DIR}/test.db"
os.environ.setdefault("CONTENT_DIR", str(Path(__file__).resolve().parent.parent / "content"))
# Narrations (app/services/audio.py, the /media mount) come from a throwaway directory: tests never see or touch media/.
os.environ.setdefault("MEDIA_DIR", f"{_TMP_DIR}/media")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def session() -> Iterator[Session]:
    with SessionLocal() as s:
        yield s
