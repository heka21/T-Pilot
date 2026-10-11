// Widget helpers (app/static/viz.js) under jsdom with the vendored Alpine: the widget() and timeline() components
// keep getters live, presets apply by name, Reset restores the starting values, and the clock steps (npm run test:js).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const ALPINE = readFileSync(new URL("../../app/static/vendor/alpine.min.js", import.meta.url), "utf8");
const VIZ = readFileSync(new URL("../../app/static/viz.js", import.meta.url), "utf8");
const settle = () => new Promise((r) => setTimeout(r, 30));

async function mount(html) {
  const dom = new JSDOM(`<!doctype html><body>${html}<script>${VIZ}</script><script>${ALPINE}</script></body>`,
    { runScripts: "dangerously", pretendToBeVisual: true });
  await settle();
  const el = dom.window.document.querySelector("[x-data]");
  return { dom, el, data: el && dom.window.Alpine.$data(el) };
}

test("widget(): getters stay live and render", async () => {
  const { el, data } = await mount(`<div x-data="widget({ v: 50, get double() { return this.v * 2 } })"><span x-text="double"></span></div>`);
  assert.equal(el.querySelector("span").textContent, "100");
  data.v = 60;
  await settle();
  assert.equal(el.querySelector("span").textContent, "120");
});

test("widget(): presets by name, and reset restores the starting values", async () => {
  const { data } = await mount(`<div x-data="widget({ v: 50, w: [1, 2], presets: { steep: { v: 70 } } })"></div>`);
  data.preset("steep");
  assert.equal(data.v, 70);
  assert.equal(data.active, "steep");
  data.w.push(3);
  data.reset();
  assert.equal(data.v, 50);
  assert.deepEqual([...data.w], [1, 2]);
  assert.equal(data.active, null);
  data.preset({ v: 55 }); // the older widgets' object form
  assert.equal(data.v, 55);
});

test("widget(): the author's own init still runs", async () => {
  const { data } = await mount(`<div x-data="widget({ v: 1, ran: false, init() { this.ran = true } })"></div>`);
  assert.equal(data.ran, true);
});

test("$viz helpers", async () => {
  const { el } = await mount(`<div x-data="widget({})"><i x-text="$viz.fmt(12500)"></i><b x-text="dir(60)"></b><u x-text="hhmm(-30)"></u></div>`);
  assert.equal(el.querySelector("i").textContent, "12,500");
  assert.equal(el.querySelector("b").textContent, "060");
  assert.equal(el.querySelector("u").textContent, "2330");
});

test("CasaViz.fn: conversions", async () => {
  const { dom } = await mount(`<div></div>`);
  const fn = dom.window.CasaViz.fn;
  assert.equal(fn.windTo(270), 90);
  assert.equal(fn.isaTemp(5000), 5);
  assert.equal(JSON.stringify(fn.utc(6 * 60)), JSON.stringify({ min: 22 * 60, day: -1 }));
  assert.equal(fn.fmt(-0.04, 1), "0.0");
  assert.equal(fn.sign(-4), "−4");
  assert.equal(fn.seg(5, 0, 10), 0.5);
  assert.equal(fn.trk(0), "000");
  assert.equal(fn.trk(-5), "355");
  assert.equal(fn.addDays("2026-02-27", 2), "2026-03-01");
  assert.equal(fn.daysBetween("2026-07-01", "2026-09-29"), 90);
  assert.equal(fn.fmtDate("2026-10-07"), "Wed 7 Oct");
});

test("timeline(): steps, seek, presets with t, reset", async () => {
  const { data } = await mount(`<div x-data="timeline({ grad: 12, duration: 10,
      steps: [{ at: 0, label: 'Dawn' }, { at: 0.5, label: 'Noon' }],
      presets: { noon: { t: 0.6, grad: 4 } } })"></div>`);
  assert.equal(data.t, 0);
  assert.equal(data.stepLabel, "Dawn");
  data.seek(0.7);
  assert.equal(data.step, 1);
  data.prev();
  assert.equal(data.t, 0.5);
  data.prev();
  assert.equal(data.t, 0);
  data.next();
  assert.equal(data.stepLabel, "Noon");
  data.preset("noon");
  assert.equal(data.t, 0.6);
  assert.equal(data.grad, 4);
  data.reset();
  assert.equal(data.t, 0);
  assert.equal(data.grad, 12);
  assert.equal(data.playing, false);
});

test("timeline(): plays forward and stops at the end when not looping", async () => {
  const { data } = await mount(`<div x-data="timeline({ duration: 0.1, loop: false })"></div>`);
  data.play();
  assert.equal(data.playing, true);
  await new Promise((r) => setTimeout(r, 400));
  assert.equal(data.t, 1);
  assert.equal(data.playing, false);
});

test("timeline(): steps may be a getter of the widget's own state", async () => {
  const { data } = await mount(`<div x-data="timeline({ k: 0.2, get steps() { return [{ at: this.k, label: 'A' }] } })"></div>`);
  data.next();
  assert.equal(data.t, 0.2);
  data.k = 0.4;
  data.next();
  assert.equal(data.t, 0.4);
});

test("CasaViz.drive applies a preset and plays", async () => {
  const { dom, el, data } = await mount(`<figure><div x-data="timeline({ duration: 100, presets: { mid: { t: 0.5 } } })"></div></figure>`);
  assert.equal(dom.window.CasaViz.drive(el.parentElement, { preset: "mid", play: true }), true);
  assert.equal(data.t >= 0.5, true);
  assert.equal(data.playing, true);
  data.pause();
});

test("CasaViz.drive resets a widget cued without a preset", async () => {
  const { dom, el, data } = await mount(`<figure><div x-data="widget({ h: 1000, presets: { high: { h: 5000 } } })"></div></figure>`);
  data.preset("high");
  assert.equal(data.h, 5000);
  dom.window.CasaViz.drive(el.parentElement, { reset: true });
  assert.equal(data.h, 1000);
  assert.equal(data.active, null);
});

test("timeline(): a steps getter may use the helpers (it is not read before Alpine starts)", async () => {
  const { data } = await mount(`<div x-data="timeline({ get steps() { return [{ at: this.lerp(0, 1, 0.3), label: 'A' }] } })"></div>`);
  data.next();
  assert.equal(data.t, 0.3);
});
