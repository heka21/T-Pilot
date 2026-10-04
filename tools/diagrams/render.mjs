// Renders diagrams and widgets to PNG for visual review (no browser in the dev container).
//   node tools/diagrams/render.mjs [--out DIR] [--scale 2] [slug ...]
// Default: every content/diagrams/*.svg and the <svg> inside every content/widgets/*.html, light and dark,
// into .renders/<slug>.light.png and .renders/<slug>.dark.png. Token colours come from app/static/src/app.css.
import { Resvg } from "@resvg/resvg-js";
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";

const root = new URL("../..", import.meta.url).pathname;
const args = process.argv.slice(2);
const opt = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args.splice(i, 2)[1] : dflt; };
const outDir = opt("--out", join(root, ".renders"));
const scale = Number(opt("--scale", "2"));
const only = new Set(args);

export function tokens() {
  const css = readFileSync(join(root, "app/static/src/app.css"), "utf8");
  const light = {}, dark = {};
  // Dark values live in the `:root { @variant dark { ... } }` block, after the light @theme tokens.
  const darkStart = css.search(/^\s*@variant dark \{/m);
  for (const m of css.matchAll(/--color-([a-z0-9-]+):\s*(#[0-9a-fA-F]{3,8})/g)) {
    (m.index < darkStart ? light : dark)[m[1]] = m[2];
  }
  return { light, dark: { ...light, ...dark } };
}

export function substitute(svg, theme) {
  let out = svg.replace(/var\(--color-([a-z0-9-]+)\)/g, (_, k) => theme[k] ?? "#ff00ff");
  // resvg ignores orient="auto-start-reverse"; plain auto renders marker-end heads correctly (marker-start heads will point the wrong way in previews only).
  out = out.replace(/orient="auto-start-reverse"/g, 'orient="auto"');
  // resvg has no context-stroke; make arrowheads foreground-coloured per use by inlining the shaft colour.
  out = out.replace(/<marker id="([^"]+)"([^>]*)>(.*?)<\/marker>/gs, (m, id, a, inner) =>
    `<marker id="${id}"${a}>${inner.replace(/context-stroke/g, theme.fg)}</marker>`);
  // Simple per-colour arrowheads: for lines whose stroke is a different colour, duplicate the marker.
  const colours = new Set([...out.matchAll(/stroke="(#[0-9a-fA-F]{3,8})"[^>]*marker-(?:end|start)="url\(#([^)]+)\)"/g)].map((m) => m[1]));
  for (const c of colours) {
    const id = "arrow-" + c.slice(1);
    const marker = out.match(/<marker id="arrow"[^>]*>.*?<\/marker>/s);
    if (!marker) break;
    out = out.replace("</defs>", marker[0].replace('id="arrow"', `id="${id}"`).replace(new RegExp(theme.fg, "g"), c) + "</defs>");
    out = out.replace(new RegExp(`(stroke="${c}"[^>]*marker-(?:end|start)=")url\\(#arrow\\)`, "g"), `$1url(#${id})`);
  }
  return out;
}

function fonts() {
  const dir = join(root, "app/static/fonts");
  return readdirSync(dir).filter((f) => f.endsWith(".woff2")).map((f) => join(dir, f));
}

export function renderPng(svg, theme, bg) {
  const body = substitute(svg, theme);
  const r = new Resvg(body, {
    fitTo: { mode: "zoom", value: scale },
    background: bg,
    font: { fontFiles: fonts(), loadSystemFonts: true, defaultFontFamily: "Inter Variable", monospaceFamily: "JetBrains Mono Variable", sansSerifFamily: "Inter Variable" },
  });
  return r.render().asPng();
}

async function widgetSvg(html) {
  // Static preview of a widget: let Alpine evaluate the bindings in jsdom, then take the first <svg>.
  try {
    const { JSDOM, VirtualConsole } = await import("jsdom");
    const alpine = readFileSync(join(root, "app/static/vendor/alpine.min.js"), "utf8");
    const vc = new VirtualConsole();
    const dom = new JSDOM(`<!doctype html><html><body>${html}<script>${alpine}</script></body></html>`, { runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc });
    await new Promise((r) => setTimeout(r, 80));
    const svg = dom.window.document.querySelector("svg");
    if (!svg) return null;
    svg.querySelectorAll("[style*='display: none']").forEach((n) => n.remove());
    svg.querySelectorAll("template").forEach((n) => n.remove());
    let out = svg.outerHTML.replace(/\s(?::|x-|@)[\w.:-]+="[^"]*"/g, "");
    if (!/xmlns=/.test(out)) out = out.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"');
    return out;
  } catch (e) {
    console.error("widget preview failed:", e.message);
    return null;
  }
}

export async function renderAll() {
  const t = tokens();
  mkdirSync(outDir, { recursive: true });
  const jobs = [];
  for (const f of readdirSync(join(root, "content/diagrams")).filter((f) => f.endsWith(".svg"))) {
    const slug = basename(f, ".svg");
    if (only.size && !only.has(slug)) continue;
    jobs.push([slug, readFileSync(join(root, "content/diagrams", f), "utf8")]);
  }
  for (const f of readdirSync(join(root, "content/widgets")).filter((f) => f.endsWith(".html"))) {
    const slug = basename(f, ".html");
    if (only.size && !only.has(slug)) continue;
    const svg = await widgetSvg(readFileSync(join(root, "content/widgets", f), "utf8"));
    if (svg) jobs.push(["widget-" + slug, svg]);
  }
  for (const [slug, svg] of jobs) {
    for (const [name, theme, bg] of [["light", t.light, t.light.surface], ["dark", t.dark, t.dark.surface]]) {
      try {
        writeFileSync(join(outDir, `${slug}.${name}.png`), renderPng(svg, theme, bg));
      } catch (e) {
        console.error(`${slug} (${name}): ${e.message}`);
      }
    }
    console.log(slug);
  }
  console.log(`${jobs.length} visual(s) rendered to ${outDir}`);
}

if (process.argv[1] && import.meta.url.endsWith(basename(process.argv[1]))) renderAll();
