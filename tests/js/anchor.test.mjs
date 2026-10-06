// Pure anchoring and ink helpers from app/static/annotations.js, run under jsdom (npm run test:js).
import { test } from "node:test";
import assert from "node:assert/strict";
import { JSDOM } from "jsdom";

import {
  textMap, describeRange, resolveSelector, applyHighlight, removeHighlight, shouldDraw, hitStroke,
} from "../../app/static/annotations.js";

function article(html) {
  const dom = new JSDOM(`<!doctype html><body><article>${html}</article></body>`);
  return dom.window.document.querySelector("article");
}

/** A Range over the `nth` occurrence of `phrase` inside a single text node under root. */
function rangeOver(root, phrase, nth = 0) {
  const doc = root.ownerDocument;
  const walker = doc.createTreeWalker(root, 4);
  let seen = 0;
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    for (let at = n.data.indexOf(phrase); at >= 0; at = n.data.indexOf(phrase, at + 1)) {
      if (seen++ === nth) {
        const r = doc.createRange();
        r.setStart(n, at);
        r.setEnd(n, at + phrase.length);
        return r;
      }
    }
  }
  throw new Error(`phrase not found: ${phrase}`);
}

const LESSON = `
  <h2>Angle of attack</h2>
  <p>The wing stalls at the critical angle of attack, about 16 degrees for a light aircraft.</p>
  <p>Lift is <span class="arithmatex">\\(L = C_L \\tfrac12 \\rho V^2 S\\)</span> so it grows with speed squared.</p>
  <figure class="visual"><svg><text>Diagram label</text></svg><figcaption>Figure caption text</figcaption></figure>
  <p>In a turn the stall speed rises with load factor.</p>`;

test("textMap skips figures and maths wrappers", () => {
  const root = article(LESSON);
  const { text } = textMap(root);
  assert.ok(text.includes("critical angle of attack"));
  assert.ok(text.includes("so it grows with speed squared"));
  assert.ok(!text.includes("Diagram label"));
  assert.ok(!text.includes("Figure caption"));
  assert.ok(!text.includes("C_L"));
});

test("describeRange and resolveSelector round-trip", () => {
  const root = article(LESSON);
  const sel = describeRange(root, rangeOver(root, "critical angle of attack"));
  assert.equal(sel.exact, "critical angle of attack");
  assert.ok(sel.prefix.endsWith("stalls at the "));
  assert.ok(sel.suffix.startsWith(", about 16"));
  assert.match(sel.block_id, /^1:p:/);
  const map = textMap(root);
  assert.deepEqual(resolveSelector(map, sel), { start: sel.start, end: sel.end });
  assert.equal(map.text.slice(sel.start, sel.end), sel.exact);
});

test("the quote still resolves when text is inserted before it", () => {
  const before = article(LESSON);
  const sel = describeRange(before, rangeOver(before, "load factor"));
  const after = article(`<p>A brand new opening paragraph was added to this lesson.</p>${LESSON}`);
  const map = textMap(after);
  assert.notEqual(map.text.slice(sel.start, sel.end), sel.exact, "position fast path should miss");
  const got = resolveSelector(map, sel);
  assert.ok(got);
  assert.equal(map.text.slice(got.start, got.end), "load factor");
  assert.ok(got.start > sel.start);
});

test("a repeated phrase resolves to the occurrence with matching context", () => {
  const html = `<p>The stall speed is shown on the airspeed indicator.</p>
    <p>Flap lowers the stall speed by raising the maximum lift coefficient.</p>
    <p>In a turn the stall speed rises with load factor.</p>`;
  const before = article(html);
  const sel = describeRange(before, rangeOver(before, "stall speed", 2));
  const after = article(`<p>Some new words.</p>${html}`);
  const map = textMap(after);
  const got = resolveSelector(map, sel);
  assert.equal(got.start, map.text.lastIndexOf("stall speed"));
  // And the first occurrence picks the first.
  const sel0 = describeRange(before, rangeOver(before, "stall speed", 0));
  assert.equal(resolveSelector(map, sel0).start, map.text.indexOf("stall speed"));
});

test("deleted text does not resolve", () => {
  const before = article(LESSON);
  const sel = describeRange(before, rangeOver(before, "load factor"));
  const after = article(LESSON.replace("with load factor", "in a turn"));
  assert.equal(resolveSelector(textMap(after), sel), null);
});

test("applyHighlight marks across a <strong> boundary and removeHighlight restores the text", () => {
  const root = article(`<p>The <strong>critical angle</strong> of attack is fixed.</p>`);
  const original = root.innerHTML;
  const map = textMap(root);
  const start = map.text.indexOf("angle of");
  const marks = applyHighlight(root, { start, end: start + "angle of".length }, { id: 7, colour: "green", comment: "check" });
  assert.equal(marks.length, 2);
  for (const m of marks) {
    assert.equal(m.dataset.hl, "7");
    assert.equal(m.className, "hl hl-green");
    assert.equal(m.title, "check");
  }
  assert.equal(marks[0].parentElement.tagName, "STRONG");
  assert.equal(marks[0].textContent, "angle");
  assert.equal(marks[1].textContent, " of");
  assert.equal(textMap(root).text, map.text, "marks do not change the text map");
  removeHighlight(root, 7);
  assert.equal(root.querySelectorAll("mark").length, 0);
  assert.equal(root.innerHTML, original);
});

test("the text map is identical before and after KaTeX renders", () => {
  const root = article(LESSON);
  const before = textMap(root).text;
  const sel = describeRange(root, rangeOver(root, "speed squared"));
  root.querySelector(".arithmatex").innerHTML =
    `<span class="katex"><span class="katex-mathml"><math><mi>L</mi><mo>=</mo></math></span><span class="katex-html">L = C</span></span>`;
  const map = textMap(root);
  assert.equal(map.text, before);
  assert.deepEqual(resolveSelector(map, sel), { start: sel.start, end: sel.end });
});

test("shouldDraw: pen draws when armed, fingers scroll, mouse draws on the sketch pad", () => {
  const pen = { pointerType: "pen" }, touch = { pointerType: "touch" }, mouse = { pointerType: "mouse" };
  const overlay = { tool: "pen", penDraws: true, drawMode: false };
  assert.equal(shouldDraw(pen, overlay), "draw");
  assert.equal(shouldDraw(touch, overlay), null);
  assert.equal(shouldDraw(mouse, overlay), null);
  assert.equal(shouldDraw(pen, { ...overlay, penDraws: false }), null, "Pen selects");
  assert.equal(shouldDraw(touch, { ...overlay, drawMode: true }), "draw", "Finger draws");
  assert.equal(shouldDraw(mouse, { ...overlay, drawMode: true }), "draw");
  assert.equal(shouldDraw(pen, { ...overlay, tool: "erase" }), "erase");
  assert.equal(shouldDraw(pen, { ...overlay, tool: "none" }), null);
  const sketch = { tool: "pen", penDraws: true, drawMode: false, sketch: true };
  assert.equal(shouldDraw(mouse, sketch), "draw");
  assert.equal(shouldDraw(pen, sketch), "draw");
  assert.equal(shouldDraw(touch, sketch), null);
  assert.equal(shouldDraw(touch, { ...sketch, drawMode: true }), "draw");
});

test("hitStroke hits near the polyline and misses away from it", () => {
  const pts = [[0, 0, 0.5], [100, 0, 0.5], [100, 100, 0.5]];
  assert.equal(hitStroke(pts, 50, 3, 5), true);
  assert.equal(hitStroke(pts, 104, 60, 5), true);
  assert.equal(hitStroke(pts, 50, 20, 5), false);
  assert.equal(hitStroke(pts, 120, 120, 5), false);
  assert.equal(hitStroke([[10, 10, 0.5]], 12, 12, 5), true);
  assert.equal(hitStroke([[10, 10, 0.5]], 20, 20, 5), false);
});
