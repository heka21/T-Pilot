// Smoke-tests an Alpine widget without a browser: loads it into jsdom with the vendored Alpine, prints the
// readouts at the defaults, then applies "id=value" slider changes from the command line and prints again.
//   node tools/widgets/smoke.mjs content/widgets/bank-angle.html ba-bank=60 ba-vs=50
// Any Alpine expression error shows up as WARN/ERR lines; the exit code is 1 if there were any.
import { JSDOM, VirtualConsole } from "jsdom";
import { readFileSync } from "node:fs";

const root = new URL("../..", import.meta.url).pathname;
const [file, ...changes] = process.argv.slice(2);
const alpine = readFileSync(`${root}/app/static/vendor/alpine.min.js`, "utf8");
const widget = readFileSync(file, "utf8");
let problems = 0;
const vc = new VirtualConsole();
vc.on("error", (e) => { problems++; console.error("ERR ", e); });
vc.on("warn", (w) => { problems++; console.error("WARN", String(w).split("\n")[0]); });
vc.on("jsdomError", (e) => { problems++; console.error("JSDOM", e.message); });
const dom = new JSDOM(`<!doctype html><html><body>${widget}<script>${alpine}</script></body></html>`,
  { runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc });
const { document: doc, Event } = dom.window;
const tick = () => new Promise((r) => setTimeout(r, 60));
await tick();

function dump(label) {
  console.log(label);
  for (const r of doc.querySelectorAll(".widget-readout")) {
    const k = r.querySelector("dt, .widget-label")?.textContent.trim();
    const vEl = r.querySelector("dd, .widget-value");
    const v = vEl && [...vEl.childNodes].filter((n) => !(n.style && n.style.display === "none")).map((n) => n.textContent).join(" ").replace(/\s+/g, " ").trim();
    const state = r.className.replace("widget-readout", "").trim();
    console.log(`  ${k} = ${v}${state ? "  [" + state + "]" : ""}`);
  }
  for (const o of doc.querySelectorAll("output")) console.log(`  output ${o.getAttribute("for") || ""}: ${o.textContent.trim()}`);
  const svgText = [...doc.querySelectorAll("svg text")].map((t) => t.textContent.trim()).filter(Boolean);
  if (svgText.length) console.log("  svg text:", svgText.join(" | "));
}
dump("defaults");
if (changes.length) {
  for (const kv of changes) {
    const [id, v] = kv.split("=");
    const el = doc.getElementById(id);
    if (!el) { problems++; console.error(`no element with id ${id}`); continue; }
    el.value = v;
    el.dispatchEvent(new Event(el.tagName === "SELECT" ? "change" : "input", { bubbles: true }));
  }
  await tick();
  dump("after " + changes.join(" "));
}
process.exit(problems ? 1 : 0);
