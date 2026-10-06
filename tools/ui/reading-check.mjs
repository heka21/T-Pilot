// Loads app/static/app.js into a jsdom window and checks the reading helpers that do not need layout:
// CasaReading.fraction, the text-size buttons and the lesson panel tabs. Run: npm run test:ui
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { JSDOM } from "jsdom";

const appJs = readFileSync(fileURLToPath(new URL("../../app/static/app.js", import.meta.url)), "utf8");
const html = `<!doctype html><html><body>
  <div id="text-size-menu" popover>${["s", "m", "l", "xl", "xxl"].map((s) => `<button type="button" data-font-size="${s}" aria-pressed="false">A</button>`).join("")}</div>
  <aside class="lesson-panel" data-lesson-panel>
    <div role="tablist">${["contents", "notes", "sketch"].map((t) => `<button type="button" role="tab" data-panel-tab-btn="${t}" aria-selected="false">${t}</button>`).join("")}</div>
    ${["contents", "notes", "sketch"].map((t) => `<div data-panel-tab="${t}" hidden></div>`).join("")}
  </aside>
  <div class="lesson-panel-backdrop" data-panel-close></div>
  <button type="button" data-panel-open aria-expanded="false">Notes</button>
</body></html>`;
const dom = new JSDOM(html, { runScripts: "outside-only", url: "http://localhost/lessons/X/1.1" });
const { window } = dom;
window.eval(appJs);
window.document.dispatchEvent(new window.Event("DOMContentLoaded"));

let failures = 0;
function check(name, ok) {
  console.log(`${ok ? "ok  " : "FAIL"} ${name}`);
  if (!ok) failures++;
}

const f = window.CasaReading.fraction;
// Viewport 800 px, top bar bottom edge at 64 px, article 2000 px tall: span = 2000 - (800 - 64) = 1264.
check("fraction 0 when the article top is at the top bar", f({ top: 64, bottom: 2064, height: 2000 }, 800, 64) === 0);
check("fraction 0.5 half way", f({ top: 64 - 632, bottom: 2064 - 632, height: 2000 }, 800, 64) === 0.5);
check("fraction 1 once the bottom is in view", f({ top: -1300, bottom: 700, height: 2000 }, 800, 64) === 1);

const doc = window.document;
doc.querySelector('button[data-font-size="xl"]').click();
check("text size xl sets <html data-font-size>", doc.documentElement.dataset.fontSize === "xl");
check("text size xl is pressed", doc.querySelector('button[data-font-size="xl"]').getAttribute("aria-pressed") === "true"
  && doc.querySelector('button[data-font-size="m"]').getAttribute("aria-pressed") === "false");
check("text size stored", window.localStorage.getItem("fontsize") === "xl");
doc.querySelector('button[data-font-size="m"]').click();
check("text size m clears the attribute and storage", !("fontSize" in doc.documentElement.dataset) && window.localStorage.getItem("fontsize") === null);

check("panel starts on contents", !doc.querySelector('[data-panel-tab="contents"]').hidden && doc.querySelector('[data-panel-tab="notes"]').hidden);
window.CasaPanel.setTab("notes");
check("CasaPanel.setTab shows notes", !doc.querySelector('[data-panel-tab="notes"]').hidden && doc.querySelector('[data-panel-tab="contents"]').hidden
  && doc.querySelector('[data-panel-tab-btn="notes"]').getAttribute("aria-selected") === "true");
doc.querySelector("[data-panel-open]").click();
check("open adds .is-open", doc.querySelector("[data-lesson-panel]").classList.contains("is-open")
  && doc.querySelector("[data-panel-open]").getAttribute("aria-expanded") === "true");
doc.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
check("Escape closes the panel", !doc.querySelector("[data-lesson-panel]").classList.contains("is-open"));

window.close();
if (failures) { console.error(`${failures} check(s) failed`); process.exit(1); }
console.log("reading-check: all passed");
