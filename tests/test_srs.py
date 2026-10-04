from datetime import date, timedelta

from app.models import CardReview
from app.services.srs import schedule, grade_card, due_cards
from tests._db import fresh_session

D = date(2026, 10, 5)


def test_good_sequence_grows_intervals():
    r = CardReview(card_id="x")
    schedule(r, 2, D)
    assert (r.interval_days, r.repetitions, r.due) == (1, 1, D + timedelta(days=1))
    schedule(r, 2, D + timedelta(days=1))
    assert r.interval_days == 6
    schedule(r, 2, D + timedelta(days=7))
    assert r.interval_days == round(6 * r.ease) and r.interval_days > 6


def test_again_resets_and_counts_lapse():
    r = CardReview(card_id="x", ease=2.5, interval_days=10, repetitions=3)
    schedule(r, 0, D)
    assert (r.interval_days, r.repetitions, r.lapses, r.due) == (0, 0, 1, D)
    assert r.ease < 2.5


def test_ease_floor():
    r = CardReview(card_id="x", ease=1.3)
    for _ in range(5):
        schedule(r, 0, D)
    assert r.ease == 1.3


def test_due_cards_new_then_reviewed():
    s = fresh_session()
    cards = due_cards(s, D, unit_codes=["RMTC"])
    assert [c.id for c in cards][:3] == ["RMTC-C001", "RMTC-C002", "RMTC-C003"]
    grade_card(s, "RMTC-C001", 3, D)  # easy -> due in a day or more
    assert [c.id for c in due_cards(s, D, unit_codes=["RMTC"])][:2] == ["RMTC-C002", "RMTC-C003"]
    grade_card(s, "RMTC-C002", 0, D)  # again -> still due today, listed first
    assert [c.id for c in due_cards(s, D, unit_codes=["RMTC"])][0] == "RMTC-C002"
