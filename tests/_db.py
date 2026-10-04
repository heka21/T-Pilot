"""Self-contained in-memory database helper for service tests (independent of conftest fixtures)."""
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from app.db import Base, make_engine
from app.seed.loader import seed_all

CONTENT = Path(__file__).resolve().parent.parent / "content"


def fresh_session(seed: bool = True):
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    if seed:
        seed_all(session, CONTENT)
    return session
