"""Listening scripts: the spoken version of each lesson, in content/audio/<UNIT>/<same file name as the lesson>.md.

A script is written for the ear (the brief is content/AUDIO.md). The lesson it narrates is never changed; the script
records the lesson's hash in `source_sha` so check_content can say when the lesson moved on without it.

    ---
    subtopic: RFRC 2.3
    source_sha: 3f9c0a1b2c4d          # lesson_sha() of the lesson file the script was written from
    ---
    Opening words before the first heading form the "Introduction" chapter.

    ## Why this matters               # a chapter: the title must be one of the lesson's h2 headings
    One paragraph per idea. Sentences are captions in watch mode.

    [[diagram:vmc-minima-by-airspace]]   # watch mode shows this visual from the next sentence on
    [[pause 4]]                          # silence, in seconds (thinking time after a question)

    Below {10,000 ft|ten thousand feet}  # {as written|as spoken}: captions show the left, the voice says the right

Everything here is plain parsing with no audio dependencies, so check_content and the app can use it; the synthesis
lives in tools/audio/build.py.
"""
from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from markdown.extensions.toc import slugify

from app.seed.loader import split_frontmatter

SCRIPTS_DIR = "audio"
LEXICON_FILE = "audio/lexicon.yaml"
INTRO_ID = "top"
INTRO_TITLE = "Introduction"

CHAPTER_RE = re.compile(r"^##\s+(.+?)\s*$")
DIRECTIVE_RE = re.compile(r"^\[\[\s*(?:(diagram|widget|workbook):([a-z0-9][a-z0-9-]*)|pause\s+(\d+(?:\.\d+)?))\s*\]\]$")
OVERRIDE_RE = re.compile(r"\{([^{}|]+)\|([^{}]+)\}")
# A sentence ends at . ! or ? (and any closing quote or bracket) followed by space and a capital, digit or override.
SENTENCE_RE = re.compile(r"(?<=[.!?])[\"”’)]?\s+(?=[\"“(]?[A-Z0-9{])")
NUMBER_RE = re.compile(r"(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.,])\d+(?:\.\d+)?")


@dataclass
class Speech:
    raw: str            # the sentence as it is in the script, overrides and all
    caption: str        # as written (overrides show their left side)
    spoken: str         # what the voice says (overrides' right side, the rest through the lexicon)
    para_end: bool = False


@dataclass
class Pause:
    seconds: float


@dataclass
class Cue:
    kind: str
    slug: str


@dataclass
class Chapter:
    title: str
    id: str
    items: list[Speech | Pause | Cue] = field(default_factory=list)


@dataclass
class Script:
    path: Path
    subtopic: str
    source_sha: str
    text: str
    chapters: list[Chapter]
    unknown: set[str]   # capitalised tokens the lexicon does not know (spelled out letter by letter)

    @property
    def sha(self) -> str:
        """Hash of what the narration is made of (spoken text, captions, pauses, cues, chapters), not of the file:
        a lexicon change re-renders only the scripts whose speech it actually changes."""
        parts = []
        for c in self.chapters:
            parts.append(f"#{c.id}|{c.title}")
            for i in c.items:
                parts.append(f"S{i.spoken}|{i.caption}|{i.para_end}" if isinstance(i, Speech)
                             else f"P{i.seconds}" if isinstance(i, Pause) else f"C{i.kind}:{i.slug}")
        return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:12]

    def speeches(self) -> list[Speech]:
        return [i for c in self.chapters for i in c.items if isinstance(i, Speech)]

    def cues(self) -> list[Cue]:
        return [i for c in self.chapters for i in c.items if isinstance(i, Cue)]

    def words(self) -> int:
        return sum(len(s.caption.split()) for s in self.speeches())


def lesson_sha(lesson_text: str) -> str:
    return hashlib.sha256(lesson_text.encode()).hexdigest()[:12]


def plain_title(title: str) -> str:
    """An h2 as text: 'V<sub>FE</sub>' -> 'VFE', which is what the toc extension slugifies and what the player shows."""
    return html.unescape(re.sub(r"<[^>]+>", "", title)).strip()


def chapter_id(title: str) -> str:
    """The id the `toc` extension gives an h2 with this text, so a chapter can link to the lesson's heading."""
    return slugify(plain_title(title), "-")


def lesson_path_for(script_path: Path, content_dir: Path) -> Path:
    """content/audio/RFRC/2.3-x.md -> content/notes/RFRC/2.3-x.md"""
    rel = Path(script_path).resolve().relative_to((Path(content_dir) / SCRIPTS_DIR).resolve())
    return Path(content_dir) / "notes" / rel


def script_paths(content_dir: Path) -> list[Path]:
    return sorted((Path(content_dir) / SCRIPTS_DIR).glob("*/*.md"))


# ---------------------------------------------------------------- lexicon and spoken normalisation
@dataclass
class Lexicon:
    """content/audio/lexicon.yaml. `words`: capitalised tokens and how to say them (null = spell the letters);
    `units`: abbreviations said in full after a number."""
    words: dict[str, str | None]
    units: dict[str, str]

    @classmethod
    def load(cls, content_dir: Path) -> Lexicon:
        data = yaml.safe_load((Path(content_dir) / LEXICON_FILE).read_text(encoding="utf-8")) or {}
        words = {k: v if v is None else LETTER_A_RE.sub("eigh", str(v)) for k, v in (data.get("words") or {}).items()}
        return cls(words=words, units=data.get("units") or {})


SYMBOLS = [("°C", " degrees Celsius"), ("°F", " degrees Fahrenheit"), ("°", " degrees"), ("%", " percent"),
           ("×", " times "), ("≈", " about "), ("≥", " at least "), ("≤", " at most "), ("±", " plus or minus "),
           ("→", " to "), ("&", " and "), ("½", " a half"), ("¼", " a quarter")]
DIGIT_WORDS = "zero one two three four five six seven eight nine".split()
TOKEN_RE = re.compile(r"\b([A-Z][A-Za-z0-9]*?[A-Z0-9]|V[a-z]{1,2}[0-9]?)(s?)\b")
CODED_RE = re.compile(r"([A-Z]{1,6})(\d{1,3})")
FLIGHT_LEVEL_RE = re.compile(r"\bFL ?(\d{2,3})\b")
# espeak sometimes reads a decimal mid-sentence as two sentences ("3,412.5" -> "three thousand four hundred twelve.
# five", "0.02" -> "zero. zero two"), so every decimal gets its "point" in words. Not dotted section numbers (2.3.1).
DECIMAL_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d+)\.(\d+)(?!\d|\.\d)")
LEADING_ZERO_RE = re.compile(r"(?<![\d.,])0\d{2}(?!\d|[.,]\d)")
RANGE_RE = re.compile(r"(\d)\s?[–—-]\s?(\d)")


def digits(s: str) -> str:
    return " ".join(DIGIT_WORDS[int(d)] for d in s if d.isdigit())


def spell(token: str) -> str:
    return " ".join("eigh" if c == "A" else c for c in token)


def _unit_re(units: dict[str, str]) -> re.Pattern:
    alts = "|".join(re.escape(u) for u in sorted(units, key=len, reverse=True))
    return re.compile(rf"(\d)\s?({alts})(?![\w/])")


SINGULAR = {"feet": "foot", "metres": "metre", "knots": "knot", "litres": "litre", "hours": "hour", "minutes": "minute"}


def _unit_words(words: str, m: re.Match) -> str:
    """'1 ft' is one foot: singular when the number before the unit is exactly 1."""
    start = m.start(1)
    one = m.string[start] == "1" and (start == 0 or not (m.string[start - 1].isdigit() or m.string[start - 1] in ",."))
    if not one:
        return words
    # The first plural word: "feet per minute" -> "foot per minute", "nautical miles" -> "nautical mile".
    parts = words.split(" ")
    for i, w in enumerate(parts):
        if w in SINGULAR or w.endswith("s"):
            parts[i] = SINGULAR.get(w, w[:-1])
            break
    return " ".join(parts)


def normalise(text: str, lexicon: Lexicon, unknown: set[str] | None = None) -> str:
    """Plain text as the voice should say it: units after numbers in full, flight levels and leading-zero tracks
    digit by digit, symbols in words, capitalised tokens from the lexicon (or spelled out and reported)."""
    text = re.sub(r"[*_`]+", "", text)
    text = FLIGHT_LEVEL_RE.sub(lambda m: f"flight level {digits(m.group(1))}", text)
    text = LEADING_ZERO_RE.sub(lambda m: digits(m.group(0)), text)
    text = RANGE_RE.sub(r"\1 to \2", text)
    if lexicon.units:
        text = _unit_re(lexicon.units).sub(lambda m: f"{m.group(1)} {_unit_words(lexicon.units[m.group(2)], m)}", text)
    text = DECIMAL_RE.sub(lambda m: f"{int(m.group(1).replace(',', '')):,} point {digits(m.group(2))}", text)   # 1,942: not a year
    for key in (k for k in lexicon.words if not k.isalnum()):   # ADS-B: the token pattern stops at the hyphen
        text = re.sub(rf"\b{re.escape(key)}\b", lexicon.words[key] or spell(re.sub(r"\W", "", key)), text)
    for sym, words in SYMBOLS:
        text = text.replace(sym, words)

    def token(m: re.Match) -> str:
        word, plural = m.group(1), m.group(2)
        if word in lexicon.words:
            said = lexicon.words[word]
        elif word + plural in lexicon.words:
            word, plural = word + plural, ""
            said = lexicon.words[word]
        elif word.isupper() and word.isalpha() and len(word) <= 8:
            if unknown is not None:
                unknown.add(word)
            said = None
        elif code := CODED_RE.fullmatch(word):         # PROB30, TAF3, H24: the letters as a token, then the number
            letters, number = code.groups()
            said = letters if len(letters) == 1 else token(TOKEN_RE.fullmatch(letters))
            return f"{said} {number}{plural}"
        else:
            return m.group(0)
        if said is None:
            return spell(word) + ("'s" if plural else "")
        return said + plural

    text = TOKEN_RE.sub(token, text)
    return re.sub(r"\s{2,}", " ", text).strip()


def spoken_and_caption(text: str, lexicon: Lexicon, unknown: set[str] | None = None) -> tuple[str, str]:
    """Apply {written|spoken} overrides: captions keep the written side, the voice gets the spoken side verbatim
    and everything outside overrides goes through normalise()."""
    caption, spoken, pos = [], [], 0
    for m in OVERRIDE_RE.finditer(text):
        caption += [text[pos:m.start()], m.group(1)]
        spoken += [normalise(text[pos:m.start()], lexicon, unknown), m.group(2)]
        pos = m.end()
    caption.append(text[pos:])
    spoken.append(normalise(text[pos:], lexicon, unknown))
    clean = lambda parts: re.sub(r"\s+([.,;:!?])", r"\1", " ".join(p.strip() for p in parts if p.strip())).strip()
    return letter_a(clean(spoken)), re.sub(r"[*_`]+", "", "".join(caption)).strip()


LETTER_A_RE = re.compile(r"\bA\b(?!-\w)")


def letter_a(text: str) -> str:
    """The voice reads a lone "A" as the article "uh", even in "A G L" or "Class A", but says "eigh" as the letter.
    A capital A mid-sentence is the letter; one starting a sentence is the article (spell() and the lexicon already
    turn the letter into "eigh" there)."""
    def fix(m: re.Match) -> str:
        before = text[:m.start()].rstrip()
        return "A" if not before or before[-1] in ".!?:\"“(—" else "eigh"
    return LETTER_A_RE.sub(fix, text)


def sentences(paragraph: str) -> list[str]:
    return [s.strip() for s in SENTENCE_RE.split(paragraph) if s.strip()]


# ---------------------------------------------------------------- parsing
def parse(path: Path, lexicon: Lexicon, text: str | None = None) -> Script:
    text = Path(path).read_text(encoding="utf-8") if text is None else text
    meta, body = split_frontmatter(text)
    chapters = [Chapter(INTRO_TITLE, INTRO_ID)]
    unknown: set[str] = set()
    paragraph: list[str] = []

    def flush() -> None:
        if not paragraph:
            return
        parts = sentences(" ".join(paragraph))
        for n, s in enumerate(parts):
            spoken, caption = spoken_and_caption(s, lexicon, unknown)
            chapters[-1].items.append(Speech(s, caption, spoken, para_end=n == len(parts) - 1))
        paragraph.clear()

    for raw in body.splitlines():
        line = raw.strip()
        if m := CHAPTER_RE.match(line):
            flush()
            chapters.append(Chapter(plain_title(m.group(1)), chapter_id(m.group(1))))
        elif m := DIRECTIVE_RE.match(line):
            flush()
            if m.group(3):
                chapters[-1].items.append(Pause(float(m.group(3))))
            else:
                chapters[-1].items.append(Cue(m.group(1), m.group(2)))
        elif not line:
            flush()
        else:
            paragraph.append(line)
    flush()
    if not chapters[0].items:
        chapters.pop(0)
    return Script(Path(path), str(meta.get("subtopic") or ""), str(meta.get("source_sha") or ""), text, chapters, unknown)


# ---------------------------------------------------------------- checks (used by app.seed.check_content)
BARE_4_DIGITS_RE = re.compile(r"(?<![\d,.])\d{4}(?![\d,.]\d)")
FREQUENCY_RE = re.compile(r"(?<![\d,.])\d{3}\.\d+")
RUNWAY_RE = re.compile(r"(?<![\w])\d{2}[LRC]\b")
CLOCK_RE = re.compile(r"\d:\d")
MARKUP_RE = re.compile(r"[$\\|#<>\[\]]|!\[")


def numbers(text: str) -> set[str]:
    """Numbers written in digits, commas removed: '1,500 ft' -> {'1500'}. LaTeX thousands separators count too
    ('1{,}020' in a lesson's maths is 1020)."""
    text = text.replace("{,}", ",").replace("\\,", ",")
    return {n.replace(",", "") for n in NUMBER_RE.findall(text)}


def speech_issues(raw: str) -> list[str]:
    """Things outside overrides in a script sentence that the voice would say wrongly: clock times, QNH values and
    frequencies read as quantities, runway designators, leftover Markdown or LaTeX."""
    outside = OVERRIDE_RE.sub(" ", raw)
    issues = []
    for rx, what in ((BARE_4_DIGITS_RE, "4-digit number (time, QNH, year?)"), (FREQUENCY_RE, "frequency"),
                     (RUNWAY_RE, "runway designator"), (CLOCK_RE, "clock time or ratio"), (MARKUP_RE, "markup")):
        for m in rx.finditer(outside):
            issues.append(f"{what} {m.group(0)!r} needs a {{written|spoken}} override")
    return issues
