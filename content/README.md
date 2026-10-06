# Content files

Everything the app teaches lives here as plain text. Edit with any editor and restart the container; the loader upserts by id and never touches your progress.

## Syllabus (generated, do not hand-edit)
`syllabus/schedule3.json` is produced from the official Part 61 MOS Schedule 3 text by
`python -m app.seed.parse_schedule3 content/sources/part61-mos-schedule3.txt content/syllabus/schedule3.json`.
Ids are the official codes: unit `RBKA`, subtopic `RBKA 3.6`, knowledge element `RBKA 3.6.2`.

## Exams
`exams.json`: duration, pass mark, simulator question count and per-unit weightings for RPLA and PPLA.

## Notes: `notes/<UNIT>/<n.n>-<slug>.md`
One Markdown file per subtopic, written as a **lesson** that teaches the subtopic (the full authoring brief, with
the structure, prose rules and exemplars, is `LESSONS.md`). YAML frontmatter:
```
---
subtopic: RBKA 3.6            # required, must match a subtopic id
title: Stalling, spinning and spiral dives
references: ["Part 61 MOS Schedule 3, unit RBKA 3.6", "VFRG"]
# minutes: 45                 # optional override; otherwise study time is estimated from the lesson's length
---
```
Structure, in order: `## What the exam expects (UNIT n.n)` listing every knowledge element by number (hard rule,
`check_content` fails without it); `## Why this matters`; one `##` section per element or coherent group that
explains from first principles with a visual at the paragraph it illustrates; `## Bringing it together` where a
scenario helps; `## Key points`; a closing `!!! tip "Exam tip"`. Do not write `[TOC]`: the page builds an "In this
lesson" list from the h2 headings.

Callouts and reveal boxes (the only types with styling; the lint flags others):

| Markdown | Use |
|---|---|
| `!!! example "Worked example"` | step-by-step calculation, units shown, maths in KaTeX (`$...$`, `$$...$$`) |
| `!!! warning "Common trap"` | the misconception or exam distractor |
| `!!! tip "Exam tip"` | how the exam asks it |
| `??? check "Check yourself: ..."` | self-check question; the answer inside stays hidden until tapped (3 to 6 per lesson) |
| `??? solution "Show the solution"` | hidden solution to a second worked example the reader tries first |

Cite the source document for every regulatory number so it can be checked against the current AIP, Part 91 MOS
or VFRG. Tables and standard Markdown are supported. `python -m app.seed.lint_lessons` reports lessons that fall
short of the standard (length, self-checks, worked examples, headings, visuals); `--strict` makes it fail.

## Questions: `questions/<UNIT>.yaml` or `questions/<UNIT>-<topic>.yaml`
The part before the first `-` is the unit code, so a unit can be split over several files (e.g. `BAKC-engines.yaml`, `BAKC-aerodynamics.yaml`). Ids must be unique across files: use a letter prefix per file, e.g. `BAKC-E001` for engines, `BAKC-A001` for aerodynamics. A list of questions. Two kinds:
```
- id: RBKA-001                 # unique, UNIT-NNN
  kind: mcq
  elements: ["RBKA 3.6.1"]     # knowledge element codes this tests (first one sets the subtopic)
  stem: "..."
  options: ["...", "...", "...", "..."]   # exactly 4
  answer: 1                    # index of the correct option, 0-3
  explanation: "..."           # why the answer is right and the others wrong
  references: ["RBKA 3.6"]
  difficulty: 2                # 1 easy, 2 medium, 3 hard

- id: RBKA-002
  kind: numeric                # whole-number entry, like the real exam
  elements: ["RBKA 3.6.2"]
  stem: "..."
  answer: 68
  tolerance: 1                 # accepted +/- range
  unit: kt
  workbook_page: 10            # optional, page in the CASA workbook the question uses
  explanation: "..."
```
Questions are original study material, never copied from CASA exams.

## Flashcards: `cards/<UNIT>.yaml` or `cards/<UNIT>-<topic>.yaml`
Same file naming and id rule as questions (card ids like `BAKC-EC001`).
```
- id: RBKA-C001
  elements: ["RBKA 3.6.1"]
  front: "..."
  back: "..."
```

## Equations: `equations.yaml`
The equation sheet (`/equations`) and the formula boxes on lessons. One file: a `topics` list (sheet order) and an
`equations` list. The YAML owns the links to lessons, so lessons carry no markers.
```
topics:
  - {id: aerodynamics, label: Aerodynamics}
equations:
  - id: stall-speed-in-turn          # lower-case slug, unique, at most 40 chars; anchor /equations#eq-<id>
    name: Stall speed in a level turn
    topic: aerodynamics              # a topic id above
    latex: 'V_{s,\text{turn}} = V_{s,\text{level}} \sqrt{n}'   # KaTeX, no $ delimiters; single-quote it
    symbols:                         # sym is KaTeX too; unit optional
      - {sym: 'V_{s,\text{turn}}', meaning: stall speed in the turn, unit: kt}
    when: "Markdown, with $...$ inline maths: when the formula is the one to reach for."
    rule_of_thumb: "30° adds 7%, 45° adds 19%, 60° adds 41%."    # optional
    exams: [RPLA]                    # RPLA and/or PPLA
    lessons: ["RBKA 3.5", "RBKA 3.6"]                              # subtopic ids, first = primary lesson
    tags: [bank, load factor, stall]                               # optional, for the filter and search
    see_also: [load-factor-bank]                                   # optional, other equation ids
```
In double-quoted YAML strings (`when`, `rule_of_thumb`) a backslash is written twice: `"$n = 1/\\cos\\theta$"`.
Every figure must match the lessons it links to (regulatory figures cite their clause and keep the "verify" flag).
`exams` must agree with `exams.json`: each claimed exam needs a linked lesson in one of its units, and no linked
lesson may sit outside the claimed exams. `python -m app.seed.check_content` checks ids, fields, lesson links, exam
consistency and LaTeX balance; add `--katex` (or run `npm run katex-check`) to render every formula with the
vendored KaTeX. The table is rebuilt from this file on every start.

## Reference pages: `reference/*.md`
Standalone Markdown pages (permitted materials, exam-day checklist, sources). Rendered as-is.

## Visuals: `diagrams/<slug>.svg` and `widgets/<slug>.html`
Notes reference them as images: `![Caption](diagram:slug "What to notice")` or `![Caption](widget:slug)`. At seed time the
file is inlined into the note as a `<figure>`; a missing file renders a placeholder and a warning. Diagrams are
token-coloured SVG (they follow dark mode), widgets are Alpine.js components; some are Three.js explorers. The style
guide and lint rules are in `diagrams/README.md`; `python -m app.seed.check_content` enforces them. Charts and sketch
diagrams are generated by `tools/diagrams/` (see `tools/diagrams/README.md`); hand-authored diagrams are edited in place.

## CASA workbook pages: `workbook:<figure>`
`![Which envelope does the exam use?](workbook:fig9 "What to notice: ...")` shows a page of the CASA RPL, PPL & CPL
(Aeroplane) Workbook (CC BY 4.0) with its credit line and a link to the PDF page. Figure ids (`fig3`, `fig9`,
`charlie-index-units`, ...) are listed in `app/seed/workbook.py`; the page images in `app/static/workbook/` are
rendered by `python -m tools.workbook.render` (needs `brew install poppler webp`). A question with
`workbook_page: 15` shows the same page in the quiz (open) and in mock exams (folded). Describe only what is printed
on the page in captions, and work chart answers on the real page.
