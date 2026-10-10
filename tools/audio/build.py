"""Narrate the listening scripts in content/audio/ to media/audio/<UNIT>/<n.n>.mp3 plus a .json of timings. Idempotent:
a lesson is rebuilt only when what it says changed (its script, or a lexicon entry it uses), or the voice or speed.

    python -m tools.audio.build                      # every script
    python -m tools.audio.build RFRC "RBKA 3.5"      # units or subtopics
    python -m tools.audio.build --jobs 3             # lessons in parallel (each process gets cores/jobs threads)
    python -m tools.audio.build --sample             # the same passage in each candidate voice, to choose one
    python -m tools.audio.build --say "the METAR and the TAF"    # one line, with the phonemes, to check a word

Needs the [audio] extra (uv pip install -e ".[audio]") and the Kokoro model files, which are downloaded once into
~/.cache/casa-audio (about 350 MB). Kokoro runs on the CPU at roughly 5x real time, so the full set of lessons takes
hours: run it in the background, it resumes where it stopped.

The .json beside each .mp3 is what the app reads (app/services/audio.py): duration, chapters (ids match the lesson's
h2 ids), visual cues for watch mode and one caption per sentence, all in seconds.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from app.seed.narration import (
    Cue, Lexicon, Pause, Script, Speech, lesson_path_for, parse, script_paths, spoken_and_caption,
)

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"
OUT = Path(os.environ.get("MEDIA_DIR", ROOT / "media")) / "audio"
MODELS = Path.home() / ".cache" / "casa-audio"
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
MODEL_FILES = ("kokoro-v1.0.onnx", "voices-v1.0.bin")

VOICE = "af_heart"
SPEED = 1.0
SAMPLE_VOICES = ("af_heart", "af_bella", "bf_emma", "bm_george")
BITRATE = 48            # kbps, constant bit rate so browsers seek exactly; mono 24 kHz speech
SENTENCE_GAP = 0.3      # seconds of silence between sentences, paragraphs and before a chapter
PARAGRAPH_GAP = 0.75
CHAPTER_GAP = 1.5
FORMAT_VERSION = 1      # bump to rebuild everything when the output format or the gaps change

SAMPLE_TEXT = (
    "This is R F R C 2.3, conditions of flight. Picture yourself climbing out of Jandakot on a clear morning. "
    "Below 10,000 feet in Class G you need 5,000 metres of visibility, and 1,500 metres horizontally and 1,000 feet "
    "vertically from cloud. Before you descend, set the Q N H, and check the mee-tar and the taff for your destination. "
    "Here is a question to think about. Two aeroplanes are converging at the same level. Which one gives way? "
    "The one that has the other on its right.")


def ensure_models() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    for name in MODEL_FILES:
        dest = MODELS / name
        if not dest.is_file():
            print(f"downloading {name} to {MODELS} ...", flush=True)
            urllib.request.urlretrieve(MODEL_URL + name, dest.with_suffix(".part"))
            dest.with_suffix(".part").rename(dest)


_kokoro = None


def kokoro(threads: int = 0):
    """One Kokoro per process. threads=0 lets onnxruntime use every core."""
    global _kokoro
    if _kokoro is None:
        import onnxruntime as ort
        from kokoro_onnx import Kokoro
        opts = ort.SessionOptions()
        if threads:
            opts.intra_op_num_threads = threads
        session = ort.InferenceSession(str(MODELS / MODEL_FILES[0]), sess_options=opts, providers=["CPUExecutionProvider"])
        _kokoro = Kokoro.from_session(session, str(MODELS / MODEL_FILES[1]))
    return _kokoro


def lang_of(voice: str) -> str:
    return "en-gb" if voice.startswith("b") else "en-us"


def synth(text: str, voice: str, speed: float) -> tuple[np.ndarray, int]:
    audio, rate = kokoro().create(text, voice=voice, speed=speed, lang=lang_of(voice), trim=True)
    return audio, rate


def encode_mp3(audio: np.ndarray, rate: int) -> bytes:
    import lameenc
    enc = lameenc.Encoder()
    enc.set_bit_rate(BITRATE)
    enc.set_in_sample_rate(rate)
    enc.set_channels(1)
    enc.set_quality(2)
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
    return bytes(enc.encode(pcm) + enc.flush())


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    tmp.replace(path)


def out_paths(subtopic: str) -> tuple[Path, Path]:
    unit, number = subtopic.split()
    return OUT / unit / f"{number}.mp3", OUT / unit / f"{number}.json"


def stamp(script: Script, voice: str, speed: float) -> dict:
    """What a rendered lesson was made from; any difference means rebuild. script.sha covers the lexicon's effect."""
    return {"version": FORMAT_VERSION, "script_sha": script.sha, "voice": voice, "speed": speed}


def up_to_date(script: Script, voice: str, speed: float) -> bool:
    mp3, meta = out_paths(script.subtopic)
    if not (mp3.is_file() and meta.is_file()):
        return False
    try:
        old = json.loads(meta.read_text())
    except ValueError:
        return False
    return all(old.get(k) == v for k, v in stamp(script, voice, speed).items())


def narrate(script: Script, voice: str, speed: float, say=synth) -> tuple[np.ndarray, dict]:
    """The whole lesson as one signal plus its timings. `say(text, voice, speed) -> (samples, rate)` is injectable
    so the timing logic can be tested without a model."""
    parts: list[np.ndarray] = []
    rate = 24000
    n = 0   # samples so far

    def silence(seconds: float) -> None:
        nonlocal n
        k = int(round(seconds * rate))
        parts.append(np.zeros(k, dtype=np.float32))
        n += k

    chapters, cues, captions = [], [], []
    for ci, chapter in enumerate(script.chapters):
        if ci:
            silence(CHAPTER_GAP)
        chapters.append({"id": chapter.id, "title": chapter.title, "t": round(n / rate, 2)})
        for item in chapter.items:
            if isinstance(item, Cue):
                cues.append({"kind": item.kind, "slug": item.slug, "t": round(n / rate, 2)})
            elif isinstance(item, Pause):
                silence(item.seconds)
            elif isinstance(item, Speech):
                audio, rate = say(item.spoken, voice, speed)
                captions.append({"t": round(n / rate, 2), "text": item.caption})
                parts.append(audio.astype(np.float32))
                n += len(audio)
                silence(PARAGRAPH_GAP if item.para_end else SENTENCE_GAP)
    signal = np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)
    meta = {"subtopic": script.subtopic, "script": str(script.path.relative_to(ROOT)) if script.path.is_absolute() else str(script.path),
            "duration": round(n / rate, 2), "words": script.words(), "chapters": chapters, "cues": cues, "captions": captions}
    return signal, meta


def build_one(path: str, voice: str, speed: float, threads: int) -> tuple[str, float, float]:
    """Narrate one script and write its .mp3 and .json. Returns (subtopic, audio seconds, wall seconds)."""
    kokoro(threads)
    script = parse(Path(path), Lexicon.load(CONTENT))
    t0 = time.time()
    signal, meta = narrate(script, voice, speed)
    mp3, meta_path = out_paths(script.subtopic)
    write_atomic(mp3, encode_mp3(signal, 24000))
    write_atomic(meta_path, json.dumps({**stamp(script, voice, speed), **meta}, ensure_ascii=False, indent=1).encode())
    return script.subtopic, meta["duration"], time.time() - t0


def selected(args: list[str], lexicon: Lexicon) -> list[Script]:
    scripts = [parse(p, lexicon) for p in script_paths(CONTENT)]
    if not args:
        return scripts
    return [s for s in scripts if s.subtopic in args or s.subtopic.split()[0] in args]


def hms(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("only", nargs="*", help="unit codes or subtopic ids (default: all)")
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--speed", type=float, default=SPEED)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--force", action="store_true", help="rebuild even when up to date")
    ap.add_argument("--sample", action="store_true", help=f"render a sample passage in {', '.join(SAMPLE_VOICES)}")
    ap.add_argument("--say", metavar="TEXT", help="narrate one line to media/audio/say.mp3 and print its phonemes")
    args = ap.parse_args(argv)
    ensure_models()
    lexicon = Lexicon.load(CONTENT)

    if args.say:
        spoken, _ = spoken_and_caption(args.say, lexicon)
        from kokoro_onnx.tokenizer import Tokenizer
        print(spoken)
        print(Tokenizer().phonemize(spoken, lang_of(args.voice)))
        audio, rate = synth(spoken, args.voice, args.speed)
        write_atomic(OUT / "say.mp3", encode_mp3(audio, rate))
        print((OUT / "say.mp3").relative_to(ROOT.parent) if OUT.is_relative_to(ROOT.parent) else OUT / "say.mp3")
        return 0

    if args.sample:
        for voice in SAMPLE_VOICES:
            audio, rate = synth(SAMPLE_TEXT, voice, args.speed)
            dest = OUT / "samples" / f"{voice}.mp3"
            write_atomic(dest, encode_mp3(audio, rate))
            print(dest, hms(len(audio) / rate))
        return 0

    scripts = selected(args.only, lexicon)
    if args.only and not scripts:
        print(f"no listening scripts match {args.only}")
        return 1
    todo = [s for s in scripts if args.force or not up_to_date(s, args.voice, args.speed)]
    for s in scripts:
        if s.unknown:
            print(f"{s.path.relative_to(ROOT)}: spelled out, not in the lexicon: {', '.join(sorted(s.unknown))}")
    print(f"{len(todo)} of {len(scripts)} lessons to narrate with {args.voice} at {args.speed}x", flush=True)
    if not todo:
        return 0
    threads = max(1, (os.cpu_count() or 1) // args.jobs) if args.jobs > 1 else 0
    total_audio = total_wall = 0.0
    started = time.time()
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(build_one, str(s.path), args.voice, args.speed, threads) for s in todo]
        for done, fut in enumerate(as_completed(futures), 1):
            subtopic, audio_s, wall_s = fut.result()
            total_audio += audio_s
            total_wall = time.time() - started
            print(f"[{done}/{len(todo)}] {subtopic:10} {hms(audio_s):>8} of audio in {hms(wall_s)} "
                  f"(overall {total_audio / max(total_wall, 1e-9):.1f}x real time)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
