"""Study streak on the dashboard (services.progress.activity_streak)."""
from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import Progress, Subtopic
from app.services.progress import activity_streak
from tests._db import fresh_session

TODAY = date(2026, 10, 4)


def _utc_noon(d: date) -> datetime:
    """Local noon on day d as the naive UTC timestamp the app stores."""
    return datetime.combine(d, time(12)).astimezone(timezone.utc).replace(tzinfo=None)


@pytest.fixture(scope="module")
def seeded():
    return fresh_session()


@pytest.fixture
def s(seeded):
    yield seeded
    seeded.rollback()


def _studied(session, *days_ago: int, status: str = "studying") -> None:
    ids = session.scalars(select(Subtopic.id).order_by(Subtopic.position).limit(len(days_ago)))
    for sid, n in zip(ids, days_ago):
        session.add(Progress(subtopic_id=sid, status=status, updated_at=_utc_noon(TODAY - timedelta(days=n))))
    session.flush()


def test_no_activity(s) -> None:
    st = activity_streak(s, TODAY)
    assert st["current"] == 0 and not st["today"]
    assert len(st["week"]) == 7 and st["week"][-1]["today"] and not any(d["on"] for d in st["week"])


def test_streak_counts_back_from_today(s) -> None:
    _studied(s, 0, 1, 2, 4)
    st = activity_streak(s, TODAY)
    assert st["current"] == 3 and st["today"]
    assert [d["on"] for d in st["week"]] == [False, False, True, False, True, True, True]


def test_streak_kept_until_today_is_over(s) -> None:
    _studied(s, 1, 2)
    st = activity_streak(s, TODAY)
    assert st["current"] == 2 and not st["today"]


def test_not_started_rows_do_not_count(s) -> None:
    _studied(s, 0, status="not_started")
    assert activity_streak(s, TODAY)["current"] == 0
