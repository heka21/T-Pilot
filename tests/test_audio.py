"""Lesson narration: script parsing and spoken normalisation (app.seed.narration), the build's timings
(tools.audio.build.narrate with a fake voice), check_content's script checks, services.audio and the routes.

Narrations are fake .mp3/.json pairs written into MEDIA_DIR, which conftest points at a temp directory."""
from __future__ import annotations

import json
import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import ListenProgress, Subtopic
from app.seed import check_content, narration
from app.seed.narration import Cue, Pause, Speech
from app.services import audio
from tests._db import fresh_session
from tools.audio import build

ROOT = Path(__file__).resolve().parent.parent
LEX = narration.Lexicon.load(ROOT / "content")
RATE = 24000

SCRIPT = """---
subtopic: X 1.1
source_sha: abc123
---
This is X 1.1, a test. Tune 121.5 if you are lost.

## Why this matters
First, set {1013 hPa|ten thirteen hectopascals} on the subscale. Then climb.

[[diagram:right-of-way-rules]]
[[pause 2.5]]
Picture the ZQX beacon.

## Key points
Last one!
"""


def parse(text: str = SCRIPT) -> narration.Script:
    return narration.parse(Path("x.md"), LEX, text=text)


# ---------------------------------------------------------------- parser
def test_chapters_and_ids() -> None:
    s = parse()
    assert [(c.title, c.id) for c in s.chapters] == [
        ("Introduction", "top"), ("Why this matters", "why-this-matters"), ("Key points", "key-points")]
    assert s.subtopic == "X 1.1" and s.source_sha == "abc123"
    # No words before the first heading: no Introduction chapter.
    assert [c.id for c in parse("---\nsubtopic: X 1.1\n---\n## Key points\nHello there.\n").chapters] == ["key-points"]
    assert narration.chapter_id("Altimetry below 10,000 ft") == "altimetry-below-10000-ft"


def test_items_speech_pause_cue_and_para_end() -> None:
    intro, why, key = parse().chapters
    assert [type(i) for i in intro.items] == [Speech, Speech]
    assert [i.para_end for i in intro.items] == [False, True]
    assert [type(i) for i in why.items] == [Speech, Speech, Cue, Pause, Speech]
    assert [i.para_end for i in why.items if isinstance(i, Speech)] == [False, True, True]
    cue, pause = why.items[2], why.items[3]
    assert (cue.kind, cue.slug) == ("diagram", "right-of-way-rules")
    assert pause.seconds == 2.5
    assert key.items[0].caption == "Last one!" and key.items[0].para_end
    assert parse().cues() == [cue]


def test_sentence_splitting_keeps_decimals() -> None:
    intro = parse().chapters[0]
    assert [i.caption for i in intro.items] == ["This is X 1.1, a test.", "Tune 121.5 if you are lost."]
    assert narration.sentences("Call on 121.5 now. Then 3.5 nm out! Is it? {1013|Ten thirteen} it is.") == [
        "Call on 121.5 now.", "Then 3.5 nm out!", "Is it?", "{1013|Ten thirteen} it is."]


def test_override_caption_left_spoken_right_verbatim() -> None:
    first = parse().chapters[1].items[0]
    assert first.raw == "First, set {1013 hPa|ten thirteen hectopascals} on the subscale."
    assert first.caption == "First, set 1013 hPa on the subscale."
    assert first.spoken == "First, set ten thirteen hectopascals on the subscale."
    # The spoken side is not normalised (no lexicon, no units); the text around it is.
    spoken, caption = narration.spoken_and_caption("At {FL110|FL110 ft} check the QNH.", LEX)
    assert spoken == "At FL110 ft check the Q N H."
    assert caption == "At FL110 check the QNH."


def test_unknown_capitals_are_reported() -> None:
    s = parse()
    assert s.unknown == {"ZQX"}
    assert s.chapters[1].items[-1].spoken == "Picture the Z Q X beacon."


# ---------------------------------------------------------------- normaliser
@pytest.mark.parametrize(("text", "said"), [
    ("1,500 ft", "1,500 feet"),
    ("1 ft", "1 foot"),
    ("21 ft", "21 feet"),
    ("1 kt", "1 knot"),
    ("10 kt", "10 knots"),
    ("1 nm", "1 nautical mile"),
    ("2 nm", "2 nautical miles"),
    ("1 fpm", "1 foot per minute"),
    ("500 ft/min", "500 feet per minute"),
    ("1.5 nm", "1 point five nautical miles"),
    ("0.02 hPa", "0 point zero two hectopascals"),
    ("reads 3,412.5 hours", "reads 3,412 point five hours"),
    ("at 1942.6 hours", "at 1,942 point six hours"),
    ("section 2.3.1", "section 2.3.1"),
    ("the TAF3 and H24", "the taff 3 and H 24"),
    ("DRSABCD", "D R S eigh B C D"),
    ("1,500 ft AGL", "1,500 feet eigh G L"),
    ("FL110", "flight level one one zero"),
    ("track 095", "track zero nine five"),
    ("1,095 ft", "1,095 feet"),
    ("the METAR and the TAF", "the mee-tar and the taff"),
    ("check the NOTAMs", "check the no-tams"),
    ("set the QNH", "set the Q N H"),
    ("ADS-B out", "eigh D S B out"),
    ("15°C", "15 degrees Celsius"),
    ("10–20 kt", "10 to 20 knots"),
])
def test_normalise(text: str, said: str) -> None:
    assert narration.normalise(text, LEX) == said


@pytest.mark.parametrize(("text", "said"), [
    ("A pilot in Class A airspace.", "A pilot in Class eigh airspace."),
    ("A VFR pilot.", "A V F R pilot."),
    ("Fly at {Va|V A} or below.", "Fly at V eigh or below."),
    ("Plan B: a {RA1|R A one} area.", "Plan B: a R eigh one area."),
])
def test_letter_a(text: str, said: str) -> None:
    """espeak says a lone capital A as the article "uh"; the letter has to be written "eigh"."""
    assert narration.spoken_and_caption(text, LEX)[0] == said


# ---------------------------------------------------------------- speech_issues and numbers
@pytest.mark.parametrize(("raw", "what"), [
    ("Set 1013 on the subscale.", "4-digit number"),
    ("Call on 118.1 now.", "frequency"),
    ("Land on 06L.", "runway designator"),
    ("Depart at 10:30.", "clock time"),
    ("The formula $L$ is here.", "markup"),
    ("See [the chart].", "markup"),
])
def test_speech_issues_flagged_outside_overrides(raw: str, what: str) -> None:
    issues = narration.speech_issues(raw)
    assert issues and issues[0].startswith(what)


def test_speech_issues_ignore_overrides_and_ordinary_numbers() -> None:
    assert narration.speech_issues(
        "Set {1013|ten thirteen}, call {118.1|one one eight decimal one}, land {06L|zero six left} at {10:30|ten thirty}.") == []
    assert narration.speech_issues("Climb to 1,500 ft at 3.5 nm, then 10,000 ft and 121 kt.") == []


def test_numbers() -> None:
    assert narration.numbers("1,500 ft and 0.02") == {"1500", "0.02"}
    assert narration.numbers("1{,}020 kg") == {"1020"}
    assert narration.numbers("RFRC 2.3: 10,000 ft") == {"2.3", "10000"}


# ---------------------------------------------------------------- tools.audio.build.narrate
def fake_say(text: str, voice: str, speed: float) -> tuple[np.ndarray, int]:
    return np.zeros(len(text), dtype=np.float32), RATE


def test_narrate_timings() -> None:
    script = parse()
    signal, meta = build.narrate(script, "af_heart", 1.0, say=fake_say)
    sp = script.speeches()
    gap = lambda s: int(round((build.PARAGRAPH_GAP if s.para_end else build.SENTENCE_GAP) * RATE))
    # Introduction: two sentences, then the chapter gap before "Why this matters".
    intro = sum(len(s.spoken) + gap(s) for s in sp[:2])
    chapters = meta["chapters"]
    assert [c["id"] for c in chapters] == ["top", "why-this-matters", "key-points"]
    assert chapters[0]["t"] == 0
    assert chapters[1]["t"] == round((intro + build.CHAPTER_GAP * RATE) / RATE, 2)
    # The cue fires when the pause before the next sentence starts; that sentence starts 2.5 s later.
    (cue,) = meta["cues"]
    assert cue == {"kind": "diagram", "slug": "right-of-way-rules", "t": cue["t"]}
    captions = meta["captions"]
    after = next(c for c in captions if c["text"] == "Picture the ZQX beacon.")
    assert after["t"] == pytest.approx(cue["t"] + 2.5, abs=0.011)
    # The same script without the pause: the cue's t is the next caption's t, and 2.5 s (60000 samples) shorter.
    nopause, meta2 = build.narrate(parse(SCRIPT.replace("[[pause 2.5]]\n", "")), "af_heart", 1.0, say=fake_say)
    after2 = next(c for c in meta2["captions"] if c["text"] == "Picture the ZQX beacon.")
    assert meta2["cues"][0]["t"] == after2["t"]
    assert len(signal) - len(nopause) == int(2.5 * RATE)
    # Total: every sentence, its gap, two chapter gaps and the pause.
    total = sum(len(s.spoken) + gap(s) for s in sp) + 2 * int(build.CHAPTER_GAP * RATE) + int(2.5 * RATE)
    assert len(signal) == total
    assert meta["duration"] == round(total / RATE, 2)
    assert [c["text"] for c in captions] == [s.caption for s in sp]
    assert captions == sorted(captions, key=lambda c: c["t"])


# ---------------------------------------------------------------- check_content.check_audio
LESSON = """---
subtopic: X 1.1
title: A test lesson
---
Intro text with 1,500 ft and 3 nm. Set 1013 hPa.

## Why this matters
More text.

![Right of way](diagram:thing)

## Key points
- Fly at 500 ft.
"""

GOOD_SCRIPT = """---
subtopic: X 1.1
source_sha: {sha}
---
This is a test at 1,500 ft.

## Why this matters
[[diagram:thing]]
Squawk 7,700 in an emergency, at {{1013|ten thirteen}}.

## Key points
Fly at 500 ft.
"""


@pytest.fixture
def fake_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "notes" / "X").mkdir(parents=True)
    (tmp_path / "audio" / "X").mkdir(parents=True)
    (tmp_path / "diagrams").mkdir()
    (tmp_path / "notes" / "X" / "1.1-a.md").write_text(LESSON, encoding="utf-8")
    (tmp_path / "audio" / "lexicon.yaml").write_text("words:\n  QNH: ~\nunits:\n  ft: feet\n  nm: nautical miles\n", encoding="utf-8")
    (tmp_path / "diagrams" / "thing.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><title>Thing</title><desc>Squawk 7,700 in an emergency.</desc></svg>',
        encoding="utf-8")
    monkeypatch.setattr(check_content, "CONTENT", tmp_path)
    return tmp_path


def run_check(content: Path, script: str) -> tuple[list[str], list[str]]:
    (content / "audio" / "X" / "1.1-a.md").write_text(script, encoding="utf-8")
    problems: list[str] = []
    warnings: list[str] = []
    assert check_content.check_audio({}, problems, warnings) == 1
    return problems, warnings


def test_check_audio_clean_script(fake_content: Path) -> None:
    sha = narration.lesson_sha(LESSON)
    problems, warnings = run_check(fake_content, GOOD_SCRIPT.format(sha=sha))
    assert problems == []
    # Only the length warning (a test script is far below 2,000 words). 7,700 is only in the diagram's <desc>.
    assert len(warnings) == 1 and "words (aim for" in warnings[0], warnings


def test_check_audio_problems_and_warnings(fake_content: Path) -> None:
    bad = (GOOD_SCRIPT.format(sha="000000000000")
           .replace("## Key points", "## Key point")                 # not a lesson heading
           .replace("[[diagram:thing]]", "[[diagram:thing]]\n[[diagram:nope]]")   # not embedded in the lesson
           .replace("{1013|ten thirteen}", "1013")                   # needs an override
           .replace("Fly at 500 ft.", "Fly at 500 ft, or 42 ft."))  # 42 is not in the lesson
    problems, warnings = run_check(fake_content, bad)
    text = "\n".join(problems)
    assert "chapter 'Key point' is not a heading of the lesson" in text
    assert "cue diagram:nope is not a visual this lesson embeds" in text
    assert "4-digit number (time, QNH, year?) '1013' needs a {written|spoken} override" in text
    assert len(problems) == 3, problems
    assert any("the lesson has changed since the script was written" in w for w in warnings)
    extra = next(w for w in warnings if "numbers not in the lesson" in w)
    assert extra.endswith("numbers not in the lesson: 42")
    assert "7700" not in extra
    assert any("lesson sections with no chapter: Key points" in w for w in warnings)


# ---------------------------------------------------------------- services.audio and routes: fake narrations
NARRATED = ["RFRC 2.1", "RFRC 2.3", "RFRC 2.5", "PFRA 2.1"]   # RFRC 2.2 and 2.4 are not narrated
DURATION = 600.0
MP3_BYTES = bytes(range(256)) * 8


def fake_meta(sid: str) -> dict:
    return {"version": 1, "script_sha": "abcdef123456", "voice": "af_heart", "speed": 1.0, "subtopic": sid,
            "duration": DURATION,
            "chapters": [{"id": "top", "title": "Introduction", "t": 0.0},
                         {"id": "why-this-matters", "title": "Why this matters", "t": 30.0},
                         {"id": "key-points", "title": "Key points", "t": 500.0}],
            "cues": [{"kind": "diagram", "slug": "right-of-way-rules", "t": 40.0}],
            "captions": [{"t": 0.0, "text": "Hello."}, {"t": 40.0, "text": "Picture this </script> scene."}]}


def write_narration(sid: str, data: dict | None = None) -> None:
    unit, number = sid.split()
    base = audio.media_dir() / "audio" / unit
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{number}.mp3").write_bytes(MP3_BYTES)
    (base / f"{number}.json").write_text(json.dumps(data or fake_meta(sid)), encoding="utf-8")


@pytest.fixture
def media() -> Iterator[Path]:
    root = audio.media_dir()
    assert "casa-theory-test-" in str(root), "MEDIA_DIR must be the test temp dir (conftest)"
    for sid in NARRATED:
        write_narration(sid)
    yield root
    shutil.rmtree(root / "audio", ignore_errors=True)
    audio._cache.clear()


@pytest.fixture(scope="module")
def db() -> Iterator[Session]:
    s = fresh_session()
    yield s
    s.close()


@pytest.fixture
def svc(db: Session, media: Path) -> Iterator[Session]:
    yield db
    db.execute(delete(ListenProgress))
    db.commit()


def test_meta_cached_by_mtime_and_none_when_missing(media: Path) -> None:
    first = audio.meta("RFRC 2.3")
    assert first is not None and first["duration"] == DURATION
    assert audio.meta("RFRC 2.3") is first
    path = media / "audio" / "RFRC" / "2.3.json"
    path.write_text(json.dumps({**fake_meta("RFRC 2.3"), "duration": 61.0}), encoding="utf-8")
    st = path.stat()
    os.utime(path, (st.st_atime, st.st_mtime + 5))
    assert audio.meta("RFRC 2.3")["duration"] == 61.0
    assert audio.meta("RFRC 2.2") is None
    (media / "audio" / "RFRC" / "2.5.mp3").unlink()       # a .json without its .mp3 is not a narration
    assert audio.meta("RFRC 2.5") is None
    assert audio.available() == {"RFRC 2.1", "RFRC 2.3", "PFRA 2.1"}


def test_save_progress_completes_near_the_end_and_keeps_the_tick(svc: Session) -> None:
    row = audio.save_progress(svc, "RFRC 2.3", 100, DURATION)
    assert row.completed_at is None and not audio.finished(row)
    row = audio.save_progress(svc, "RFRC 2.3", DURATION - audio.COMPLETE_WITHIN + 1, DURATION)
    assert row.completed_at is not None and audio.finished(row)
    done_at = row.completed_at
    sub = svc.get(Subtopic, "RFRC 2.3")
    d = audio.for_subtopic(svc, sub)
    assert d["completed"] and d["position"] == 0          # finished: the next play starts from the top
    row = audio.save_progress(svc, "RFRC 2.3", 12.34, DURATION)   # played again
    assert row.completed_at == done_at
    d = audio.for_subtopic(svc, sub)
    assert d["completed"] and d["position"] == 12.3
    with pytest.raises(KeyError):
        audio.save_progress(svc, "XXXX 9.9", 1, 2)


def test_descriptor(svc: Session) -> None:
    d = audio.for_subtopic(svc, svc.get(Subtopic, "RFRC 2.3"))
    assert d["sid"] == "RFRC 2.3" and d["unit"] == "RFRC"
    assert d["src"] == "/media/audio/RFRC/2.3.mp3?v=abcdef123456af_heart"
    assert d["lesson_url"] == "/lessons/RFRC/2.3" and d["watch_url"] == "/lessons/RFRC/2.3/watch"
    assert d["duration"] == DURATION and len(d["chapters"]) == 3
    assert d["position"] == 0 and d["completed"] is False
    assert audio.for_subtopic(svc, svc.get(Subtopic, "RFRC 2.2")) is None


def test_queue_order_and_scope(svc: Session) -> None:
    ids = lambda scope, start="RFRC 2.3": [d["sid"] for d in audio.queue(svc, start, scope)]
    assert ids("unit") == ["RFRC 2.3", "RFRC 2.5"]
    assert ids("unit", "RFRC 2.1") == ["RFRC 2.1", "RFRC 2.3", "RFRC 2.5"]
    assert ids("exam") == ["RFRC 2.3", "RFRC 2.5"]            # PFRA is PPLA only
    assert ids("exam", "PFRA 2.1") == ["PFRA 2.1"]
    rfrc, pfra = svc.get(Subtopic, "RFRC 2.3"), svc.get(Subtopic, "PFRA 2.1")
    assert ids("all") == (["RFRC 2.3", "RFRC 2.5", "PFRA 2.1"] if pfra.position > rfrc.position else ["RFRC 2.3", "RFRC 2.5"])
    assert ids("unit", "RFRC 2.2") == ["RFRC 2.3", "RFRC 2.5"]   # the start need not be narrated itself
    assert audio.queue(svc, "XXXX 1.1") == []


def test_last_played(svc: Session) -> None:
    assert audio.last_played(svc) is None
    audio.save_progress(svc, "RFRC 2.1", 3, DURATION)          # under 5 s: not worth a Continue
    assert audio.last_played(svc) is None
    audio.save_progress(svc, "RFRC 2.3", 200, DURATION)
    audio.save_progress(svc, "RFRC 2.1", 50, DURATION)
    assert audio.last_played(svc)["sid"] == "RFRC 2.1"
    assert audio.last_played(svc)["position"] == 50
    audio.save_progress(svc, "RFRC 2.1", DURATION, DURATION)   # finished: nothing to continue
    assert audio.last_played(svc) is None


def test_unit_summaries(svc: Session) -> None:
    audio.save_progress(svc, "RFRC 2.1", DURATION, DURATION)
    groups = {g["unit"].code: g for g in audio.unit_summaries(svc)}
    rfrc = groups["RFRC"]
    assert [d["sid"] for d in rfrc["lessons"]] == ["RFRC 2.1", "RFRC 2.3", "RFRC 2.5"]
    assert rfrc["missing"] == 4 and rfrc["seconds"] == 3 * DURATION and rfrc["heard"] == 1
    assert rfrc["exams"] == ["RPLA"] and groups["PFRA"]["exams"] == ["PPLA"]
    assert groups["PHFC"]["exams"] == ["RPLA", "PPLA"] and groups["PHFC"]["lessons"] == []


# ---------------------------------------------------------------- routes
@pytest.fixture
def listen_client(client: TestClient, session: Session) -> Iterator[TestClient]:
    yield client
    session.execute(delete(ListenProgress))
    session.commit()


def test_listen_page_without_narrations(listen_client: TestClient) -> None:
    r = listen_client.get("/listen")
    assert r.status_code == 200
    assert "No lessons are narrated yet" in r.text
    assert "python -m tools.audio.build" in r.text
    assert "data-listen=" not in r.text


def test_listen_page_with_narrations(listen_client: TestClient, media: Path) -> None:
    r = listen_client.get("/listen")
    assert r.status_code == 200
    assert "4 of " in r.text and "40 min of listening" in r.text
    assert "Play all RPLA" in r.text and "Play all PPLA" in r.text
    assert "Play unit" in r.text and "Conditions of flight" in r.text
    assert "data-listen-resume" not in r.text
    assert "4 lessons not narrated yet" in r.text                     # RFRC
    assert 'data-listen="{&#34;' in r.text                              # JSON escaped in the attribute
    listen_client.post("/listen/progress", json={"sid": "RFRC 2.3", "position": 720 / 2, "duration": DURATION})
    r = listen_client.get("/listen")
    assert "data-listen-resume" in r.text and "Continue listening" in r.text
    assert "RFRC 2.3 · Why this matters" in r.text
    assert "6 min in" in r.text


def test_listen_queue_route(listen_client: TestClient, media: Path) -> None:
    r = listen_client.get("/listen/queue", params={"start": "RFRC 2.3", "scope": "unit"})
    assert r.status_code == 200 and [d["sid"] for d in r.json()] == ["RFRC 2.3", "RFRC 2.5"]
    assert listen_client.get("/listen/queue", params={"start": "RFRC 2.3", "scope": "planet"}).status_code == 400


def test_listen_progress_route(listen_client: TestClient, media: Path) -> None:
    r = listen_client.post("/listen/progress", json={"sid": "RFRC 2.3", "position": 595, "duration": DURATION})
    assert r.status_code == 200 and r.json() == {"sid": "RFRC 2.3", "position": 595, "completed": True}
    assert listen_client.post("/listen/progress", json={"sid": "XXXX 9.9", "position": 1, "duration": 2}).status_code == 404


def test_watch_page(listen_client: TestClient, media: Path) -> None:
    r = listen_client.get("/lessons/RFRC/2.3/watch")
    assert r.status_code == 200
    assert 'data-visual-key="diagram:right-of-way-rules"' in r.text
    assert "data-watch-page" in r.text
    assert "</script> scene" not in r.text and "<\\/script> scene" in r.text   # the caption cannot close the <script>
    assert listen_client.get("/lessons/RFRC/2.2/watch").status_code == 404


def test_lesson_page_listen_buttons_only_when_narrated(listen_client: TestClient, media: Path) -> None:
    r = listen_client.get("/lessons/RFRC/2.3")
    assert r.status_code == 200 and "data-listen=" in r.text and "/lessons/RFRC/2.3/watch" in r.text
    r = listen_client.get("/lessons/RFRC/2.2")
    assert r.status_code == 200 and "data-listen=" not in r.text


def test_media_range_request(listen_client: TestClient, media: Path) -> None:
    r = listen_client.get("/media/audio/RFRC/2.3.mp3", headers={"Range": "bytes=10-19"})
    assert r.status_code == 206
    assert r.content == MP3_BYTES[10:20]
    assert r.headers["content-range"] == f"bytes 10-19/{len(MP3_BYTES)}"
