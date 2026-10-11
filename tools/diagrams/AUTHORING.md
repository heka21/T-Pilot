# Authoring visuals for a unit: the brief

You are adding diagrams, charts, animations and widgets to the notes of one syllabus unit. The reader is a student
pilot studying for a CASA theory exam who learns best visually. Every visual must be **correct, legible in light and
dark mode, intuitive, and a little bit fun**. Read, in this order, before writing anything:

1. `content/diagrams/README.md`: the style guide (lint-enforced).
2. `tools/diagrams/README.md`: the toolkit and scripts.
3. The exemplars, which set the bar: `tools/diagrams/charts.py` (`cl_vs_angle_of_attack`, `stall_speed_vs_bank`),
   `tools/diagrams/figures.py` (`four_stroke_cycle` animated, `wake_turbulence_vortices` animated, `circuit_pattern`
   with a motion-path aeroplane, `airspace_cross_section`), `tools/diagrams/schematics/dual-ignition-system.svg`
   (Rough.js sketch register), `content/widgets/bank-angle.html` and `content/widgets/weight-and-balance.html` (Alpine).
4. The unit's notes in `content/notes/<UNIT>/`, and `python -m app.seed.show_elements UNIT n.n` for the MOS wording.

## What you may change

- Your own generator module `tools/diagrams/units/<unit>_<part>.py` (create it; `@chart` functions register by name,
  hyphenated name = slug). Never edit `charts.py`, `figures.py` or `svg.py`.
- Hand-drawn schematics in `tools/diagrams/schematics/<slug>.svg` (then `npm run sketch`), or plain hand-authored
  SVG straight into `content/diagrams/<slug>.svg` when no sketch look is wanted.
- Widgets in `content/widgets/<slug>.html` (Alpine only, using the `widget()` or `timeline()` components from
  `app/static/viz.js`; no Three.js, no `data-widget`, no scripts). See "Interactive widgets and timelines" below.
- The unit's notes: insert references, convert real formulas to KaTeX (`$...$`, `$$...$$`). Never edit `minutes`
  (reading time is computed at seed time; delete the key if a note still has one).
- Nothing under `app/`, no CSS, no templates, no tests, no `package.json`. If the toolkit lacks something you need,
  work around it and list it in your report.

## Workflow for every visual

1. Decide the one question it answers. That question is the caption. If you need "and", make two visuals.
2. Build it. Generated: `.venv/bin/python -m tools.diagrams.build <slug>`. Sketch: `npm run sketch`.
3. Render it: `node tools/diagrams/render.mjs <slug>` and **look at** `.renders/<slug>.light.png` and `.dark.png`
   with the Read tool. Fix clipped text, overlaps, text across strokes, unreadable soft fills. Render again. Do not
   skip this: every exemplar needed two or three rounds.
4. Lint: `.venv/bin/python -m app.seed.check_content` must print no PROBLEM lines for your files (it also fails on
   files nothing references, so reference everything you create).
5. Reference it in the note at the paragraph it illustrates, never before or inside the "What the exam expects"
   list and never inside a `??? check` answer: `![Question the visual answers?](diagram:slug "What to notice: the
   one insight the exam wants.")` or `widget:slug`. Reading time is computed from the note at seed time.
6. Widgets: `node tools/widgets/smoke.mjs content/widgets/<slug>.html <input-id>=<value> …` must print the readouts
   with no WARN/ERR lines; check the numbers by hand against the note's worked example.

## Interactive widgets and timelines

Since the 2026-10-10 visualisation push (`tools/diagrams/VIZ-INVENTORY.md`), every new widget uses one of two
Alpine components from `app/static/viz.js` (loaded on every page before Alpine):

- `x-data="widget({ ... })"`: sliders, toggles, readouts. Exemplars: `taf-arrival-check.html` (a planning tool that
  reproduces the lessons' worked examples) and `drag-curve-explorer.html` (a chart computed from a formula).
- `x-data="timeline({ ... })"`: a process that plays out over time, with a clock `t` running 0 → 1 over `duration`
  seconds, a play button, a scrubber, step buttons and a caption. Exemplar: `sea-breeze-day.html`. Use it for
  anything the lesson describes as a sequence (a day, a storm's life, ice building, an encounter on final, SAR
  phases). Drive the picture from getters of `t`: `this.at(a, b)` is the clock's progress through [a, b] (0..1),
  `this.eased(a, b)` the same smoothed, `steps: [{ at, label }]` the key moments (a getter is fine), and a
  `caption` getter the sentence for the current moment (shown in `.widget-caption`). Copy the timeline bar, step
  buttons and caption markup from the exemplar. Use `loop: false` when the story has an end.

Both give you, inside expressions and getters (as `this.x` or bare `x`): `fmt(n, dp)` (thousands separators),
`sign`, `dir(deg)` ("060"), `clamp`, `lerp`, `seg`, `ease`, `scale`, `pol(cx, cy, r, bearing)` (compass bearing to
{x, y}), `windTo(from)`, `isaTemp(ft)` (2 °C per 1,000 ft), `hhmm(min)`, `hmm(min)`, `utc(wstMin)` and
`path([[x, y], ...])` (an SVG path through points), `trk(deg)` ("000" for north; `dir` gives "360"), dates as
`"YYYY-MM-DD"` strings with `addDays`, `daysBetween` and `fmtDate(iso, year?)`, and `drag($event, (p) => { ... })`
for dragging on an SVG (`@pointerdown`, `p` in viewBox units; add `style="touch-action: none"` to the dragged
element and always offer a slider for the same value). Getters stay live (do not spread objects into `x-data`).

**Named presets (required).** Every widget has a `presets: { name: { key: value, ... } }` object and its preset
buttons call `preset('name')` (aria-pressed: `active === 'name'`). Name each preset after what it shows
(`front-at-jandakot`, `va-at-mtow`, `geraldton-inter`). Watch mode will drive widgets by these names from the
narration script, so they must exist and each must reproduce something the lesson says. A timeline preset may set
`t` (and `play: true`). `reset()` restores the starting values automatically.

**Explanations.** `.widget-caption` (a live sentence under the picture) works in plain widgets too: use a
`caption` getter whenever the reader needs to be told why the picture changed.

**Styling.** Use the `.widget-*` classes; Tailwind utilities in widget files (e.g. `size-5`, `sm:col-span-2`) work
because `app/static/src/app.css` scans `content/widgets`, but they only exist after the lead runs `npm run css`, so
list any new utility you use in your report.

**One concept, one control.** Each slider or toggle changes one thing the exam asks about; readouts name the
answer the exam wants, with units, and turn `ok`/`warn`/`bad` at the thresholds the lesson gives.

**Numbers.** The widget computes from the lesson's formula or table, and its presets reproduce the lesson's worked
examples exactly (the smoke test prints them; compare by hand). Regulatory figures come only from the lesson. When
a model is illustrative (timings of a sea breeze, the shape of a curve), say so in the `.widget-notice`.

**Keep what exists.** Never remove, rename or move an existing diagram or widget reference: audio scripts cue them
and `check_content` fails on unreferenced files. Put the new widget beside the related diagram, asking a
different question (the diagram explains, the widget lets the reader try it).

**SVG inside widgets.** No `<template x-for>` or `<template x-if>` inside `<svg>` (jsdom and some browsers cannot
clone them): write repeated elements out, and hide optional ones with `:opacity` (or `:display`) bindings rather
than `x-show`, which can stop updating on SVG elements after a reset and a preset (seen in jsdom and the PNG
renders). Never leave an empty `stroke-dasharray=""`: resvg then drops the text drawn after it. Labels
that must cross a line get a halo: `paint-order="stroke" stroke="var(--color-surface)" stroke-width="4"
stroke-linejoin="round"`. Night and darkness: fade a `--color-sky-soft` daylight tint and add stars and a moon;
never darken with `--color-fg` (it is light in dark mode).

**Checks for every widget:**
- `node tools/widgets/smoke.mjs content/widgets/<slug>.html --presets` (add `--frames 5` for a timeline) prints
  the readouts at the defaults, at each preset and through the clock, with no WARN/ERR/PROBLEM lines. It also
  checks that preset keys exist and that every `preset('x')` in the markup is defined.
- `node tools/diagrams/render.mjs --presets <slug>` writes `.renders/widget-<slug>.light/dark.png`, one per preset
  (`@<name>`) and, for a timeline, `@0`, `@0.5` and `@1`. Look at them with the Read tool in light and dark:
  clipped or overlapping labels, text across lines, things off the stage. Arrowheads render dark in these PNGs
  (resvg has no `context-stroke`); in the browser they take the line colour.

## Rules that are easy to get wrong

- Colours only via `var(--color-…)` tokens (see the style guide table); the thing being explained in brand colour,
  everything else quieter. No hex, no `white`/`black`. Minimum font size 11.
- Numbers on a visual must match the note. Regulatory numbers (heights, distances, minima, codes) come from the
  note; if the note hedges, the visual hedges ("about"). Never invent a figure.
- Conventions: aeroplane flies left to right; lift perpendicular to relative airflow, weight vertical, thrust along
  the longitudinal axis; Southern Hemisphere rotation (anticlockwise round a high, clockwise round a low); knots and
  feet, except runway lengths and visibility in metres and kilometres.
- CSS classes and `@keyframes` inside an SVG must start with the diagram's `data-prefix`; no `#id` selectors; one
  moving element per diagram; loops of 2 to 8 s.
- Alpine widgets: no `<template x-for>` inside `<svg>` (write the repeated elements out). Unique marker ids per
  widget (`<prefix>-arrow`). Readouts in `.widget-readout` with `bad`/`warn`/`ok` classes and a `.widget-flag` when a
  threshold is crossed. Presets for the exam's favourite values, a Reset button, a `.widget-notice` line starting
  `<strong>What to notice.</strong>`, one or two `.widget-try` prompts with the answer worked out.
- KaTeX: only for real maths (formulas, worked calculations); leave ordinary prose and tables alone. Escape
  backslashes correctly inside Python strings if you generate Markdown.
- Reuse the shared characters (`plane_side`, `plane_top`, `plane_rear`, `airliner_rear`, `aerofoil`, `runway`) so the
  same aeroplane appears everywhere. The aeroplane is a Cessna 152 (high wing on the cabin roof, mains just behind the
  CG): lift arrows start at the wing (local y ≈ −8), wheels touch at local y 19.5 (side) or 13.5 (rear), and the
  exact geometry is in `content/diagrams/README.md` → Recurring characters. In a widget, paste the output of
  `python -m tools.diagrams.plane` instead of drawing an aeroplane by hand. Charts: direct labels on the curves, units in axis titles, highlighted exam values with
  callouts, no legends unless unavoidable.
- Keep each file under the size limits (40 KB SVG, 80 KB widget). Diagram width is always 640; make it taller if
  needed.

## Report back

For each slug: kind (generated / sketch / hand SVG / widget), the note and section it sits in, and "reviewed light
and dark: pass". Then: formulas converted to KaTeX (which notes), anything you could not do or
that the toolkit lacked, and any note content you believe is wrong. Do not commit.
