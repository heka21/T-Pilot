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
- Widgets in `content/widgets/<slug>.html` (Alpine only; no Three.js, no `data-widget`, no scripts).
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
- Reuse the shared characters (`plane_side`, `plane_top`, `plane_rear`, `aerofoil`, `runway`) so the same aeroplane
  appears everywhere. Charts: direct labels on the curves, units in axis titles, highlighted exam values with
  callouts, no legends unless unavoidable.
- Keep each file under the size limits (40 KB SVG, 80 KB widget). Diagram width is always 640; make it taller if
  needed.

## Report back

For each slug: kind (generated / sketch / hand SVG / widget), the note and section it sits in, and "reviewed light
and dark: pass". Then: formulas converted to KaTeX (which notes), anything you could not do or
that the toolkit lacked, and any note content you believe is wrong. Do not commit.
