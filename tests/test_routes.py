from fastapi.testclient import TestClient


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_dashboard(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "RPLA" in r.text
    assert "/static/htmx.min.js" in r.text

