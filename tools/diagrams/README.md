# tools/diagrams: how the visuals are made

| Script | Does | Run |
|---|---|---|
| `svg.py` | Toolkit: `Canvas`, `Chart`, primitives (`text`, `arrow`, `path`, …), shared characters (`plane_side`, `plane_top`, `plane_rear`, `aerofoil`, `runway`) | imported |
| `charts.py`, `figures.py` | One function per generated diagram, decorated with `@chart`; the function name with hyphens is the slug | `python -m tools.diagrams.build [slug…]` writes `content/diagrams/<slug>.svg` |
| `sketch.mjs` | Rough.js pass: `tools/diagrams/schematics/<slug>.svg` with `class="sketch"` shapes → hand-drawn look in `content/diagrams/<slug>.svg` | `npm run sketch` |
| `render.mjs` | PNG renders (light and dark, 2×) of every diagram and widget picture into `.renders/` for review | `node tools/diagrams/render.mjs [--out DIR] [slug…]` |
| `../vendor.mjs` | Copies KaTeX, Alpine, Three.js and fonts into `app/static` | `npm run vendor` |

Hand-authored diagrams (no generator, no sketch source) live directly in `content/diagrams/` and are edited in place.
Whatever the route, the result must pass `python -m app.seed.check_content` and the style guide in
`content/diagrams/README.md`, and must be referenced from a note.

## Writing a generated diagram

```python
@chart
def forces_in_a_climb() -> Canvas:
    c = Canvas("Forces in a steady climb", "Lift, weight, thrust and drag on a climbing aeroplane…", height=360, prefix="fic")
    c.add(plane_side(300, 200, 2.2, pitch=12))
    c.add(arrow(300, 180, 260, 60, "brand", label="Lift"))
    return c
```

- Pick a 2–4 letter `prefix`; any CSS class or keyframe in `c.style(...)` must start with it.
- `Chart(c, x=(x0, x1), y=(y0, y1), box=(left, top, right, bottom), xlabel=…, ylabel=…, xticks=[…], yticks=[…])`
  maps data to the canvas: `ch.axes()`, `ch.curve(points, "brand", label=…)`, `ch.point(x, y, "bad", label=…)`,
  `ch.guide(x, y)`, `ch.band(x0, x1, "bad")`, `ch.callout(x, y, dx, dy, ["line 1", "line 2"])`. `sample(fn, x0, x1)`
  evaluates a function.
- Animation: `c.style()` with `@keyframes`, one moving thing per diagram. Rotation about a point: wrap the
  element in `group(..., transform="translate(x y)")` and animate the inner group so the origin is local.
- Render and look at it before you call it done: `node tools/diagrams/render.mjs <slug>` then open
  `.renders/<slug>.light.png` and `.dark.png`. Check: nothing clipped, no text across strokes, numbers match the note.

## Writing a sketch schematic

Author clean SVG in `tools/diagrams/schematics/<slug>.svg` following the style guide. Add `class="sketch"` to the
shapes that should look hand-drawn (boxes, pipes, tanks, organs; not text, arrows or anything with numbers).
Optional per-shape attributes: `data-fill-style="hachure|solid|zigzag|cross-hatch|dots"`, `data-roughness="1.5"`,
`data-hachure-gap="8"`. Run `npm run sketch`; commit both the schematic and the generated file.
