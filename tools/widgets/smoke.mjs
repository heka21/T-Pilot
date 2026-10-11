// Smoke-tests an Alpine widget without a browser: loads it into jsdom with app/static/viz.js and the vendored Alpine,
// prints the readouts at the defaults, then applies the command-line changes in order and prints again.
//   node tools/widgets/smoke.mjs content/widgets/bank-angle.html ba-bank=60 ba-vs=50
//   node tools/widgets/smoke.mjs content/widgets/sea-breeze-day.html t=0.5        (timeline clock, 0..1)
//   node tools/widgets/smoke.mjs content/widgets/x.html preset=calm-morning step=2  (named preset, timeline step)
//   --presets   also apply every named preset in turn (after a reset) and print the readouts for each
//   --frames N  also print a timeline at N evenly spaced points from t=0 to t=1
// Any Alpine expression error shows up as WARN/ERR lines; so do presets that set keys the widget does not have,
// preset('name') calls in the markup with no such preset, and steps out of order. The exit code is 1 if any.
import { JSDOM, VirtualConsole } from "jsdom";
import { readFileSync } from "node:fs";

const root = new URL("../..", import.meta.url).pathname;
const args = process.argv.slice(2);
const flag = (name) => { const i = args.indexOf(name); if (i < 0) return false; args.splice(i, 1); return true; };
const optN = (name) => { const i = args.indexOf(name); if (i < 0) return 0; return Number(args.splice(i, 2)[1]); };
const allPresets = flag("--presets");
const frames = optN("--frames");
const [file, ...changes] = args;
const alpine = readFileSync(`${root}/app/static/vendor/alpine.min.js`, "utf8");
const viz = readFileSync(`${root}/app/static/viz.js`, "utf8");
const widget = readFileSync(file, "utf8");
let problems = 0;
const problem = (msg) => { problems++; console.error("PROBLEM", msg); };
const vc = new VirtualConsole();
vc.on("error", (e) => { problems++; console.error("ERR ", e); });
vc.on("warn", (w) => { problems++; console.error("WARN", String(w).split("\n")[0]); });
vc.on("jsdomError", (e) => { problems++; console.error("JSDOM", e.message); });
const dom = new JSDOM(`<!doctype html><html><body>${widget}<script>${viz}</script><script>${alpine}</script></body></html>`,
  { runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc });
const { document: doc, Event } = dom.window;
const tick = () => new Promise((r) => setTimeout(r, 60));
await tick();

const rootEl = doc.querySelector("[x-data]");
const data = rootEl && dom.window.Alpine.$data(rootEl);
const isTimeline = !!(data && typeof data.play === "function" && "t" in data);
const presets = (data && data.presets) || {};

// static checks on presets and steps
if (data) {
  for (const [name, vals] of Object.entries(presets)) {
    for (const k of Object.keys(vals)) if (k !== "play" && !(k in data)) problem(`preset "${name}" sets "${k}", which the widget does not have`);
  }
  for (const m of widget.matchAll(/preset\('([^']+)'\)/g)) if (!presets[m[1]]) problem(`markup calls preset('${m[1]}') but there is no such preset`);
  const steps = data.steps || [];
  steps.forEach((s, i) => { if (i && s.at < steps[i - 1].at) problem(`steps out of order at "${s.label}"`); });
}

function dump(label) {
  console.log(label);
  if (isTimeline) console.log(`  t = ${data.t.toFixed(3)}${data.stepLabel ? "  step: " + data.stepLabel : ""}`);
  for (const r of doc.querySelectorAll(".widget-readout")) {
    if (r.style.display === "none") continue;
    const k = r.querySelector("dt, .widget-label")?.textContent.trim();
    const vEl = r.querySelector("dd, .widget-value");
    const v = vEl && [...vEl.childNodes].filter((n) => !(n.style && n.style.display === "none")).map((n) => n.textContent).join(" ").replace(/\s+/g, " ").trim();
    const state = r.className.replace("widget-readout", "").trim();
    console.log(`  ${k} = ${v}${state ? "  [" + state + "]" : ""}`);
  }
  for (const c of doc.querySelectorAll(".widget-caption")) if (c.style.display !== "none") console.log(`  caption: ${c.textContent.trim()}`);
  for (const o of doc.querySelectorAll("output")) console.log(`  output ${o.getAttribute("for") || ""}: ${o.textContent.trim()}`);
  const svgText = [...doc.querySelectorAll("svg text")].filter((t) => !t.closest("[style*='display: none']"))
    .map((t) => t.textContent.trim()).filter(Boolean);
  if (svgText.length) console.log("  svg text:", svgText.join(" | "));
}

async function apply(kv) {
  const i = kv.indexOf("=");
  const id = kv.slice(0, i), v = kv.slice(i + 1);
  const el = doc.getElementById(id);
  if (el) {
    if (el.type === "checkbox") el.checked = v === "1" || v === "true";
    else el.value = v;
    el.dispatchEvent(new Event(el.tagName === "SELECT" || el.type === "checkbox" ? "change" : "input", { bubbles: true }));
  } else if (data && id === "t" && isTimeline) data.seek(Number(v));
  else if (data && id === "step" && isTimeline) data.goStep(Number(v));
  else if (data && id === "preset") { if (!presets[v]) problem(`no preset "${v}"`); else data.preset(v); }
  else problem(`no element with id ${id} (and not t=, step= or preset=)`);
  await tick();
}

dump("defaults");
if (changes.length) {
  for (const kv of changes) await apply(kv);
  dump("after " + changes.join(" "));
}
if (allPresets) {
  for (const name of Object.keys(presets)) {
    data.reset(); await tick();
    data.preset(name); await tick();
    if (isTimeline) data.pause();
    dump(`preset ${name}`);
  }
}
if (frames && isTimeline) {
  data.reset(); await tick();
  for (let k = 0; k < frames; k++) {
    data.seek(frames === 1 ? 0 : k / (frames - 1)); await tick();
    dump(`frame ${k + 1}/${frames}`);
  }
}
process.exit(problems ? 1 : 0);
