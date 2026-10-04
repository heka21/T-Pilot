"""Global search: service scoring and the /search page (full and HTMX partial)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.services import search as svc
from tests._db import fresh_session


def test_index_covers_every_kind() -> None:
    session = fresh_session()
    kinds = {e.kind for e in svc.build_index(session, "content")}
    assert kinds == set(svc.KINDS)


def test_search_stall_finds_note_and_elements() -> None:
    session = fresh_session()
    res = svc.search(session, "stall", "content")
    by_kind = {g["kind"]: g for g in res["groups"]}
    assert "note" in by_kind and "element" in by_kind and "question" in by_kind
    titles = [h.entry.title for h in by_kind["note"]["hits"]]
    assert any("Stall" in t for t in titles)
    assert "<mark>" in by_kind["note"]["hits"][0].snippet  # body hit is highlighted; title-only hits have plain snippets


def test_exact_code_ranks_first() -> None:
    session = fresh_session()
    res = svc.search(session, "RBKA 3.6", "content")
    sub = next(g for g in res["groups"] if g["kind"] == "subtopic")
    assert sub["hits"][0].entry.code == "RBKA 3.6"
    assert sub["hits"][0].entry.url == "/syllabus/subtopic/RBKA/3.6"
    el = next(g for g in res["groups"] if g["kind"] == "element")
    assert el["hits"][0].entry.url.startswith("/syllabus/subtopic/RBKA/3.6#el-")


def test_all_terms_required_and_kind_filter() -> None:
    session = fresh_session()
    assert svc.search(session, "stall zzzqqq", "content")["total"] == 0
    only_cards = svc.search(session, "stall", "content", kind="card")
    assert only_cards["total"] > 0 and {g["kind"] for g in only_cards["groups"]} == {"card"}


def test_snippet_is_escaped() -> None:
    assert svc.highlight("a < b & stall", ["stall"]) == "a &lt; b &amp; <mark>stall</mark>"


def test_search_page(client: TestClient) -> None:
    r = client.get("/search")
    assert r.status_code == 200
    assert "What you can find" in r.text
    r = client.get("/search", params={"q": "stall"})
    assert r.status_code == 200
    assert "<mark>" in r.text and "/notes/RBKA/3.6" in r.text
    assert 'value="stall"' in r.text  # both the page box and the sidebar box echo the query


def test_search_partial_and_no_results(client: TestClient) -> None:
    r = client.get("/search", params={"q": "stall"}, headers={"HX-Request": "true", "HX-Target": "search-results"})
    assert r.status_code == 200
    assert "<html" not in r.text and "search-hit" in r.text
    r = client.get("/search", params={"q": "zzzqqqxxx"})
    assert "Nothing matches" in r.text
    assert client.get("/search", params={"q": "stall", "kind": "bogus"}).status_code == 200


def test_top_bar_has_search_box(client: TestClient) -> None:
    r = client.get("/")
    assert 'data-global-search' in r.text and 'action="/search"' in r.text
    assert 'hx-get="/search/suggest"' in r.text and 'id="search-suggest"' in r.text
    # On the search page the same box drives the results instead of the dropdown.
    r = client.get("/search", params={"q": "stall"})
    assert 'hx-target="#search-results"' in r.text and 'id="search-suggest"' not in r.text


def test_suggest_ranks_across_kinds() -> None:
    session = fresh_session()
    res = svc.suggest(session, "stall", "content")
    kinds = [h.kind for h in res["hits"]]
    assert 0 < len(kinds) <= svc.SUGGEST_LIMIT
    assert all(kinds.count(k) <= svc.SUGGEST_PER_KIND[k] for k in kinds)
    assert any(h.entry.url == "/notes/RBKA/3.6" for h in res["hits"])
    assert res["total"] >= len(kinds)


def test_suggest_endpoint(client: TestClient) -> None:
    r = client.get("/search/suggest", params={"q": "stall"})
    assert r.status_code == 200 and "<html" not in r.text
    assert "suggest-item" in r.text and "<mark>" in r.text and "See all" in r.text
    assert client.get("/search/suggest", params={"q": ""}).text.strip() == ""
    assert "Nothing matches" in client.get("/search/suggest", params={"q": "zzzqqqxxx"}).text
