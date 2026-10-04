"""Small shared helpers."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC timestamp (SQLite DateTime columns are naive)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
