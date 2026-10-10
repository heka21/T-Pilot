// Follow along (app/static/follow.js) under jsdom: matching the narration's captions to lesson blocks, and the
// toggle marking the block being read. The player is a stub that records subscribers (npm run test:js).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const SOURCE = readFileSync(new URL("../../app/static/follow.js", import.meta.url), "utf8");

const ARTICLE = `
<h2 id="why">Why this matters</h2>
<p>Most training aeroplanes drive a fixed-pitch propeller. The tachometer needle does not stay where you put it.</p>
<p>Nothing has broken. The propeller is doing exactly what its geometry says it must.</p>
<h2 id="blade">A propeller blade is a rotating wing</h2>
<p>Cut a blade across and you see an aerofoil section with a chord line. The angle between the chord line and the plane of rotation is the blade angle.</p>
<figure class="visual visual-diagram" data-visual="diagram:propeller-blade-twist"><svg></svg><figcaption>Three sections of one blade: near the hub the helical path is steep.</figcaption></figure>
<ul><li><p>Reduce power first, then raise the nose to slow down.</p></li></ul>
<details class="check"><summary>Check yourself: what happens to the angle of attack as the aeroplane accelerates?</summary><p>It decreases, because the helix angle grows.</p></details>`;

const TIMELINE = {
  chapters: [{ id: "top", title: "Introduction", t: 0 }, { id: "why", title: "Why this matters", t: 5 },
             { id: "blade", title: "A propeller blade is a rotating wing", t: 30 }],
  cues: [{ kind: "diagram", slug: "propeller-blade-twist", t: 50 }],
  captions: [
    { t: 0, text: "This is PAKA 2.1, Propellers." },
    { t: 5, text: "Most training aeroplanes drive a fixed-pitch propeller." },
    { t: 10, text: "In one of them, the tachometer needle does not stay where you put it." },
    { t: 15, text: "So, then." },
    { t: 20, text: "Nothing has broken." },
    { t: 25, text: "The propeller is doing exactly what its geometry says it must." },
    { t: 30, text: "Cut a blade across, and you see an aerofoil section." },
    { t: 40, text: "The angle between the chord line and the plane of rotation is the blade angle." },
    { t: 50, text: "Picture three sections of one blade, side by side." },
    { t: 55, text: "Near the hub, the helical path is steep." },
    { t: 60, text: "First, reduce power. Then raise the nose." },
    { t: 70, text: "Question. What happens to the angle of attack as the aeroplane accelerates?" },
    { t: 75, text: "It decreases, because the helix angle grows." },
  ],
};

function setup({ follow = null, sid = "PAKA 2.1", highlights = false, listen = false } = {}) {
  const desc = { sid: "PAKA 2.1", src: "/media/audio/PAKA/2.1.mp3?v=abcaf_heart" };
  const body = `${listen ? `<button data-listen='${JSON.stringify(desc)}'></button>` : ""}
    <div data-sid="${sid}"><article data-lesson-article>${ARTICLE}</article></div>
    <button data-player="follow" aria-pressed="false"></button>`;
  const dom = new JSDOM(`<!doctype html><html><body>${body}</body></html>`, { url: "http://localhost/", runScripts: "outside-only" });
  const w = dom.window;
  if (follow !== null) w.localStorage.setItem("listen:follow", follow);
  if (highlights) {
    w.CSS = { highlights: new Map() };
    w.Highlight = function (range) { this.range = range; };
    w.eval("var CSS = window.CSS, Highlight = window.Highlight;");
  }
  const fetches = [];
  w.fetch = (url) => { fetches.push(url); return Promise.resolve({ ok: true, json: () => Promise.resolve(TIMELINE) }); };
  w.scrollTo = () => {};
  w.matchMedia = () => ({ matches: false });
  const subs = [];
  const lesson = { sid: "PAKA 2.1", src: "/media/audio/PAKA/2.1.mp3?v=abcaf_heart" };
  w.CasaPlayer = { subscribe: (el, fn) => subs.push(fn), audio: { currentTime: 0, paused: false }, current: () => lesson };
  w.eval(SOURCE);
  w.document.dispatchEvent(new w.Event("DOMContentLoaded"));
  const emit = (time, extra = {}) => subs.forEach((fn) => fn({ type: "time", lesson, time, paused: false, ...extra }));
  return { w, doc: w.document, F: w.CasaFollow, emit, fetches };
}

const tick = () => new Promise((r) => setTimeout(r, 0));
const reading = (doc) => [...doc.querySelectorAll("[data-reading]")].map((el) => el.textContent.trim().slice(0, 18));

test("each caption lands on the block it paraphrases, in reading order", () => {
  const { doc, F } = setup();
  const m = F.align(TIMELINE, doc.querySelector("article"));
  const text = (i) => (m.at[i] == null ? null : m.blocks[m.at[i]].textContent.trim().slice(0, 18));
  assert.equal(text(0), null, "the introduction has no block before the first h2");
  assert.equal(text(1), "Most training aero");
  assert.equal(text(2), "Most training aero");
  assert.equal(text(3), "Most training aero", "a sentence with no match stays where it was");
  assert.equal(text(4), "Nothing has broken");
  assert.equal(text(6), "Cut a blade across");
  assert.equal(text(7), "Cut a blade across");
  assert.equal(m.blocks[m.at[8]].tagName, "FIGURE", "the sentences after a visual's cue go to the visual");
  assert.equal(m.blocks[m.at[9]].tagName, "FIGURE");
  assert.equal(text(10), "Reduce power first", "a list item is matched through its paragraph");
  assert.equal(m.blocks[m.at[11]].tagName, "SUMMARY");
  assert.equal(text(12), "It decreases, beca");
});

test("off by default; the toggle turns it on, is remembered, and marks every toggle button", () => {
  const { doc, F, w } = setup();
  assert.equal(F.enabled(), false);
  doc.querySelector('[data-player="follow"]').click();
  assert.equal(F.enabled(), true);
  assert.equal(w.localStorage.getItem("listen:follow"), "1");
  assert.equal(doc.querySelector('[data-player="follow"]').getAttribute("aria-pressed"), "true");
});

test("when on, the block being read is marked, and only on the lesson that is playing", async () => {
  const { doc, emit, fetches } = setup({ follow: "1" });
  emit(0);
  await tick();
  assert.deepEqual(fetches, ["/media/audio/PAKA/2.1.json?v=abcaf_heart"], "the timeline sits beside the mp3");
  emit(21);
  assert.deepEqual(reading(doc), ["Nothing has broken"]);
  emit(41);
  assert.deepEqual(reading(doc), ["Cut a blade across"]);
  // A paragraph inside a closed "Check yourself" box marks its summary, where it can be seen.
  emit(76);
  assert.deepEqual(reading(doc), ["Check yourself: wh"]);
  doc.querySelector("details").open = true;
  emit(71); emit(76);
  assert.deepEqual(reading(doc), ["It decreases, beca"]);

  const other = setup({ follow: "1", sid: "RFRC 2.3" });
  other.emit(0); await tick(); other.emit(21);
  assert.deepEqual(reading(other.doc), [], "another lesson's page is left alone");
});

test("turning it off clears the mark", async () => {
  const { doc, emit, F } = setup({ follow: "1" });
  emit(0); await tick(); emit(21);
  assert.equal(reading(doc).length, 1);
  F.set(false);
  assert.deepEqual(reading(doc), []);
  emit(41);
  assert.deepEqual(reading(doc), [], "stays off while playing");
});

test("the sentence in the block closest to the caption is highlighted where the browser supports it", async () => {
  const { emit, w } = setup({ follow: "1", highlights: true });
  emit(0); await tick(); emit(41);
  const hl = w.CSS.highlights.get("casa-reading");
  assert.ok(hl, "a highlight is set");
  assert.equal(hl.range.toString(), "The angle between the chord line and the plane of rotation is the blade angle.");
  emit(31);
  assert.equal(w.CSS.highlights.get("casa-reading").range.toString(), "Cut a blade across and you see an aerofoil section with a chord line.");
});

// Lays the article's blocks out 100 px apart, `scroll` px up the window (jsdom has no layout); anything else,
// like a paragraph in a closed box, has no box.
function layout(w, scroll) {
  const blocks = ["Most training", "Nothing has", "Cut a blade", "FIGURE", "Reduce power", "Check yourself"];
  w.Element.prototype.getBoundingClientRect = function () {
    const i = blocks.findIndex((b) => (b === "FIGURE" ? this.tagName === "FIGURE" : this.matches("p, summary") && this.textContent.trim().startsWith(b)));
    if (i < 0) return { top: 0, bottom: 0, left: 0, right: 0, width: 0, height: 0 };
    const top = 200 + 100 * i - scroll;
    return { top, bottom: top + 100, left: 0, right: 600, width: 600, height: 100 };
  };
}

test("spot(): where Listen starts for a reader scrolled into the lesson", async () => {
  const { w, F, fetches } = setup({ listen: true });
  assert.equal(F.spot("PAKA 2.1", 0), null, "nothing before the timeline is in");
  await tick();
  assert.deepEqual(fetches, ["/media/audio/PAKA/2.1.json?v=abcaf_heart"], "fetched when the page opens, before any playing");
  layout(w, 0);
  assert.equal(F.spot("PAKA 2.1", 0), null, "still at the start: resume as before");
  layout(w, 350);    // "Cut a blade across" is at the top of the window
  assert.equal(F.spot("PAKA 2.1", 0), 29.8, "its first sentence, a moment early");
  assert.equal(F.spot("RFRC 2.3", 0), null, "only for this page's lesson");
  layout(w, 250);    // "Nothing has broken" is still showing at the top
  assert.equal(F.spot("PAKA 2.1", 21), null, "the passage it would resume on is on screen: resume there");
  layout(w, 650);    // past "Reduce power": the closed check box is next, read from its question
  assert.equal(F.spot("PAKA 2.1", 21), 69.8);
});
