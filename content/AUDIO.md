# Writing a listening script: the authoring brief

Every lesson in `content/notes/` gets a **listening script** in `content/audio/`, with the same unit folder and file
name (`notes/RFRC/2.3-conditions-of-flight.md` → `audio/RFRC/2.3-conditions-of-flight.md`). The script is what the
narrator says. `python -m tools.audio.build` turns it into an MP3 with a natural voice. The app plays it from the
lesson page in two modes:
- **Listen:** audio only, with the screen off.
- **Watch:** each diagram appears full-screen as the narrator reaches it, with the sentence being spoken shown
  underneath as a caption.

**The listener** is the same student pilot as the lessons' reader, but now they are driving to work or on a
treadmill. They cannot see the screen, cannot scroll back, and cannot take notes. They may play at 1.25×. They
have heard the lesson's topic before, or they will read it later. The script has to teach by ear alone and still
make sense when the screen is in their pocket.

**The script never changes the lesson.** It retells the lesson in spoken form. Read, in this order, before
writing:

1. This brief.
2. The three exemplar scripts:
   - `audio/RFRC/2.3-conditions-of-flight.md` (rules and figures);
   - `audio/RBKA/3.5-turning.md` (concepts and formulas);
   - `audio/BAKC/6.2-take-off-and-landing-performance.md` (calculations and charts).

   Read each one next to its lesson to see what was kept, what changed, and how.
3. The lesson you are narrating, all of it, including every diagram it embeds. For each `diagram:slug`, read the
   `<desc>` in `content/diagrams/<slug>.svg`; that is your description of the picture.

## Fidelity: the hard rules

- **No new facts. No changed facts.** Every figure, limit, rule and definition comes from the lesson, worded so
  that it means exactly what the lesson says. You may round only where the lesson itself rounds.
- **If you think the lesson is wrong**, keep the lesson's wording and list the doubt in your report. Don't fix it
  in the script.
- **Write every figure in digits:** 1,500 ft, 5,000 m, 8 hours, 0.02. The check compares every number in the script
  with the numbers in the lesson and lists any that are missing from the lesson. Counting words are not figures:
  "two rules", "the third case".
- **Chapters:** keep every `##` section of the lesson, in the lesson's order, with the heading text copied
  exactly. Chapter titles must match the lesson's headings; that is how the app links a chapter to the lesson's
  "In this lesson" list, and how Watch mode titles each part.

## File format

```
---
subtopic: RFRC 2.3
source_sha: 3f9c0a1b2c4d
---
This is RFRC 2.3, Conditions of flight. ...

## What the exam expects (RFRC 2.3)
Spoken paragraph. Another sentence.

## Why this matters
...
[[diagram:vmc-minima-by-airspace]]
Picture a ladder of airspace ...

Question. How high must you be before the first turn after take-off?
[[pause 4]]
At least 500 ft above the aerodrome ...
```

- **`source_sha`:** the hash of the lesson file you narrated. `python -m app.seed.check_content --audio-sha
  RFRC/2.3-conditions-of-flight` prints it. When the lesson is edited later, the check reports the script as
  stale.
- **Opening (before the first `##`):** two or three sentences.
  - Say the unit and subtopic number, and the lesson title.
  - Say what the listener will be able to do by the end.
  - Tell them a few checks need a pause to think, if you include any.
  - Never state the length.
- **Paragraphs** are separated by blank lines. Each sentence becomes one caption, so sentences end with `.`, `?`
  or `!`.
- **`[[diagram:slug]]`, `[[widget:slug]]`, `[[workbook:fig3]]`:** on a line of their own.
  - Use only visuals this lesson embeds, at most once each, in the place the lesson puts them.
  - Watch mode shows the visual from the next sentence on, until the next cue or chapter. So put the cue
    immediately before the sentences that describe that visual, and describe it right after.
  - Cue every diagram the lesson embeds. Widgets and workbook figures too, unless the lesson only mentions them
    in passing.
- **`[[pause N]]`:** N seconds of silence. Use 4 after a "Check yourself" question, or 6 for one that needs a
  calculation.
- **`{written|spoken}`:** the caption shows the left side and the voice says the right side, word for word. Use it
  wherever the voice would otherwise read a number as a quantity:

  | What | Write |
  |---|---|
  | clock times | `{0700|oh seven hundred}`, `{1915|nineteen fifteen}` |
  | QNH and pressure settings | `{1013 hPa|ten thirteen hectopascals}` |
  | frequencies | `{121.5|one two one decimal five}` |
  | tracks, headings, wind directions | `{095|zero nine five} degrees`, `wind {270|two seven zero} at 15 knots` |
  | runways | `runway {24L|two four left}` |
  | ratios | `the {1 in 60|one in sixty} rule` |

  The check flags 4-digit numbers, frequencies, runways and colons that have no override. Flight levels (FL110)
  and leading-zero tracks (095) are read digit by digit automatically, but an override is never wrong.

## Writing for the ear

- **Use short sentences, mostly under 25 words.** Put the subject first. One idea per sentence.
- **Signpost constantly.** "There are three cases. The first is head-on." "So that is the rule for converging.
  Now overtaking." A listener cannot see the structure, so say it.
- **Repeat the figures that matter.** Give each figure when it comes up and again at the end of its section, in
  the same words. Repetition on the page is padding, but on audio it is how things stick.
- **No lists, tables, brackets or footnotes.**
  - A bullet list becomes "First … Second … And third …".
  - Brackets become a separate sentence, or are dropped.
  - A table becomes its pattern first, then its figures grouped by what is common, then the exception. For
    example: "Visibility is the same everywhere: 5,000 m. Distance from cloud is 1,500 m horizontally and 1,000 ft
    vertically in Class C, in Class E, and in Class G up high. There are two exceptions…". Never read a table row
    by row.
- **Don't refer to the page.** No "see the table", "as shown above", "below", "click". Say "picture …" or "imagine
  …". A Watch-mode viewer sees the diagram anyway; a listener has to be able to build it in their head.
- **Describe diagrams in spatial words.**
  - Say where things are: left and right, above and below, the order along a line, what is big and what is small.
  - Then give the point the diagram makes. That is its "what to notice" line, in spoken form.
  - Two to five sentences.
- **Say maths in words.** No LaTeX, no symbols. "Load factor equals one over the cosine of the bank angle." "At
  60 degrees of bank the cosine is a half, so the load factor is 2." For a worked example:
  - say the question;
  - invite the listener to pause and try it;
  - walk through the steps with the numbers rounded as the lesson rounds them;
  - give the answer twice: when you reach it, and again in one sentence at the end.
- **Acronyms:** write them as the lesson does (QNH, CTAF, METAR); the lexicon `audio/lexicon.yaml` decides how
  they are said. The first time an acronym appears, give its meaning in words, as a pilot would explain it.
  `check_content` lists capitalised words the lexicon does not know. Report the ones you need, with how they are
  said on the radio; do not edit the lexicon yourself.
- **Use plain spoken English.** No "e.g.", "i.e.", "etc.", "vs.", "approx.", and no `/` between words. "Either …
  or" instead of "and/or". Units can be abbreviated (ft, m, kt, nm, kg, hPa), because the narrator expands them.
- **Don't read out element numbers** ("2.3.1"). Say what the element is about.

### What the narrator handles, and what it doesn't

- **Decimals** (3,412.5 hours, 0.02 percent, 1.5 nm) are said with "point" automatically. Write the digits with no
  override, unless aviation says them differently (frequencies, QNH).
- **Codes ending in a number** (PROB30, TAF3, H24, RA1) are said as the code's letters from the lexicon, then the
  number as a quantity: "prob 30", "H 24". If the digits should be said one by one, use an override:
  `{R155|R one five five}`.
- **The letter A.** The voice says a lone "A" as "uh", so the narrator changes a capital A in the middle of a
  sentence to "eigh": Class A, the A in "V A". A spelled acronym (ATC, AGL) is handled wherever it appears. In an
  override that starts a sentence with the letter, write `eigh`.
- **am and pm:** write `{am|a.m.}` and `{pm|p.m.}`. "ay em" is read as "eye em". For a clock time, use the overrides
  in the table above.
- **Abbreviations in lower case** (dB, Hz, mmHg, rpm) are expanded only after a number. Elsewhere, write the word.
- **Headings with markup** such as "V<sub>FE</sub>" are copied verbatim. The player shows them as plain text.
- **The word ceiling is 5,000.** For a lesson over 4,500 words, aim at about 105 percent: describe diagrams in two
  or three sentences, and don't repeat a summary that a later section repeats.
- **Never mention "the brief" or "the note"** if a lesson does. Say "the lesson", or leave it out.

## Turning each part of the lesson into speech

| In the lesson | In the script |
|---|---|
| What the exam expects | One short paragraph: "The exam wants you to know six things", then each in a phrase. No numbers. |
| Why this matters | Keep it nearly whole. It is already spoken in tone. |
| Teaching sections | Keep the reasoning; it is the point. Cut what only works visually. Shorten a long list of conditions to the ones the exam tests, keeping every figure. |
| `!!! example "Worked example"` | "Let's work one." Set it up, "pause if you'd like to try it", then the steps and the answer. |
| `??? solution` | Same as a worked example. |
| `!!! warning "Common trap"` | "Here's a trap the exam likes to set." Then the trap and the way out. |
| `??? check "Check yourself"` | "Question." The question, then `[[pause 4]]`, then "The answer:" and the answer with its reason. Keep every check. |
| Bringing it together | Tell the scenario as a story, present tense. |
| Key points | "Let's recap." One or two sentences per point, every figure kept. |
| `!!! tip "Exam tip"` | Last. Then a one-line close: "That's the end of RFRC 2.3." |
| Links to other lessons | "You'll find that in the lesson on take-off and landing performance." |

**Length:** about as long as the lesson, usually 90 to 120 percent of it, and between 2,000 and 5,000 words. That is
13 to 30 minutes at the narrator's pace of about 160 words a minute. Tables turned into sentences and figures said
twice add words. Visual asides and cross-references are what go.

## Before you hand in

```
python -m app.seed.check_content --audio          # format, chapters, cues, numbers, overrides, lexicon
python -m tools.audio.build --say "a tricky sentence with QNH and {1013|ten thirteen}"   # hear one line
```

Fix every error. For each warning, either fix it or, if it is a number that is in the lesson in another form,
say so in your report. Your report lists:
- words per script;
- capitalised terms the lexicon lacks, with how they are said;
- any doubts about the lesson's facts.
