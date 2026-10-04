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


def test_flag_roundtrip(client: TestClient) -> None:
    r = client.post("/flags", data={"kind": "other", "ref": "dashboard", "message": "Typo in the stall speed note"})
    assert r.status_code == 200
    assert "Thanks, noted." in r.text

    r = client.get("/flags")
    assert r.status_code == 200
    assert "Typo in the stall speed note" in r.text
