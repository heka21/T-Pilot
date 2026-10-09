"""End-to-end page flows for quiz, mock exam, flashcards and planner."""
import re
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models import Card


def test_quiz_flow(client: TestClient) -> None:
    assert client.get("/quiz").status_code == 200
    r = client.get("/quiz?subtopic=RBKA+3.6&weak=1")
    assert r.status_code == 200 and "RBKA 3.6" in r.text

    r = client.post("/quiz/start", data={"units": ["RBKA"], "count": "5"}, follow_redirects=False)
    assert r.status_code == 303
    url = r.headers["location"]
    r = client.get(url)
    assert r.status_code == 200 and "Question 1 of 5" in r.text
    for position in range(5):
        r = client.post(f"{url}/answer", data={"position": position, "given": "1"})
        assert r.status_code == 200
        assert "Correct." in r.text or "Incorrect." in r.text
    assert "See results" in r.text
    r = client.get(f"{url}/result")
    assert r.status_code == 200
    assert re.search(r'class="score-big">\d+%', r.text)
    assert "Quiz the weak areas again" in r.text


def test_quiz_with_no_questions_shows_error(client: TestClient) -> None:
    r = client.post("/quiz/start", data={"units": ["ZZZZ"], "count": "5"})
    assert r.status_code == 422 and "No questions match" in r.text


def test_exam_flow(client: TestClient) -> None:
    r = client.get("/exam")
    assert r.status_code == 200 and "RPLA" in r.text
    r = client.post("/exam/start", data={"exam_code": "RPLA"}, follow_redirects=False)
    assert r.status_code == 303
    url = r.headers["location"]
    r = client.get(url)
    assert r.status_code == 200 and 'id="exam-timer"' in r.text
    r = client.post(f"{url}/answer", data={"position": 0, "given": "1"})
    assert r.status_code == 200
    assert "Correct." not in r.text and "Incorrect." not in r.text  # no feedback during the exam
    r = client.post(f"{url}/flag/0")
    assert r.status_code == 200 and "Flagged for review" in r.text
    r = client.post(f"{url}/submit", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == f"{url}/result"
    r = client.get(f"{url}/result")
    assert r.status_code == 200
    assert "Knowledge Deficiency Report" in r.text
    # a submitted exam can't be resumed
    assert client.get(url, follow_redirects=False).status_code == 303


def test_cards_flow(client: TestClient) -> None:
    """Exam format: four shuffled options, check, explanation, then a grade that depends on the pick."""
    assert client.get("/cards").status_code == 200
    r = client.get("/cards/review?unit=RMTC")
    assert r.status_code == 200 and "Check answer" in r.text
    card_id = re.search(r"/cards/([^/\"?]+)/answer", r.text).group(1)
    order = re.search(r'name="order" value="([0-9,]+)"', r.text).group(1)
    assert sorted(order.split(",")) == ["0", "1", "2", "3"]
    shown = [int(v) for v in re.findall(r'name="given" value="(\d)"', r.text)]
    assert shown == [int(x) for x in order.split(",")]

    with SessionLocal() as s:
        answer = s.get(Card, card_id).answer
    wrong = (answer + 1) % 4
    r = client.post(f"/cards/{card_id}/answer", data={"given": wrong, "order": order, "unit": "RMTC"})
    assert r.status_code == 200 and "Incorrect." in r.text and "Explanation" in r.text
    assert 'hx-vals=\'{"grade": 0}\'' in r.text and "Knew it" not in r.text
    # the correct option's letter follows the display order
    assert f"Correct answer: <strong>{'ABCD'[order.split(',').index(str(answer))]}." in r.text

    r = client.post(f"/cards/{card_id}/answer", data={"given": answer, "order": order, "unit": "RMTC"})
    assert r.status_code == 200 and "Correct." in r.text and "Knew it" in r.text
    assert client.post(f"/cards/{card_id}/answer", data={"given": 7, "order": order}).status_code == 422

    r = client.post(f"/cards/{card_id}/grade", data={"grade": "2", "unit": "RMTC"})
    assert r.status_code == 200
    assert "Check answer" in r.text or "Done for today" in r.text


def test_planner_flow(client: TestClient) -> None:
    r = client.get("/planner")
    assert r.status_code == 200 and 'action="/planner/generate"' in r.text

    today = date.today()
    bad = {"start_date": today.isoformat(), "rpla_exam_date": today.isoformat(), "ppla_exam_date": today.isoformat(),
           "study_weekdays": ["0"], "minutes_per_session": "60", "revision_days_before_exam": "4"}
    r = client.post("/planner/generate", data=bad)
    assert r.status_code == 422 and "must be after the start date" in r.text

    good = {"start_date": today.isoformat(), "rpla_exam_date": (today + timedelta(days=33)).isoformat(),
            "ppla_exam_date": (today + timedelta(days=56)).isoformat(), "study_weekdays": [str(i) for i in range(7)],
            "minutes_per_session": "90", "revision_days_before_exam": "4"}
    r = client.post("/planner/generate", data=good, follow_redirects=False)
    assert r.status_code == 303
    r = client.get("/planner")
    assert r.status_code == 200 and "Flashcards due today" in r.text
    item_id = re.search(r"/planner/item/(\d+)/toggle", r.text).group(1)
    r = client.post(f"/planner/item/{item_id}/toggle", headers={"HX-Request": "true"})
    assert r.status_code == 200 and "plan-item" in r.text
    r = client.post("/planner/replan", follow_redirects=False)
    assert r.status_code in (200, 303)
    assert client.get("/planner").status_code == 200
