// Copies the front-end libraries the app needs from node_modules into app/static so the app stays
// fully offline. Run with `npm run vendor` after `npm install`; the copied files are committed, so
// Docker builds never need Node. Rough.js is build-time only (tools/diagrams/sketch.mjs) and is not copied.
import { cpSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname;
const nm = join(root, "node_modules");
const vendor = join(root, "app/static/vendor");
const fonts = join(root, "app/static/fonts");

rmSync(vendor, { recursive: true, force: true });
rmSync(fonts, { recursive: true, force: true });
mkdirSync(join(vendor, "katex/fonts"), { recursive: true });
mkdirSync(join(vendor, "three/addons/controls"), { recursive: true });
mkdirSync(fonts, { recursive: true });

const copy = (from, to) => cpSync(join(nm, from), join(to.startsWith("/") ? to : join(vendor, to)), { force: true });

// KaTeX: CSS, renderer, auto-render contrib and the woff2 fonts only (the CSS lists woff2 first, so
// browsers never request the woff or ttf fallbacks).
copy("katex/dist/katex.min.css", "katex/katex.min.css");
copy("katex/dist/katex.min.js", "katex/katex.min.js");
copy("katex/dist/contrib/auto-render.min.js", "katex/auto-render.min.js");
for (const f of readdirSync(join(nm, "katex/dist/fonts")).filter((f) => f.endsWith(".woff2"))) {
  copy(`katex/dist/fonts/${f}`, `katex/fonts/${f}`);
}

// Alpine.js (CDN build registers window.Alpine and starts itself).
copy("alpinejs/dist/cdn.min.js", "alpine.min.js");

// Three.js ES modules. OrbitControls imports from "three", resolved by the import map in base.html.
copy("three/build/three.module.js", "three/three.module.js");
copy("three/build/three.core.js", "three/three.core.js");
copy("three/examples/jsm/controls/OrbitControls.js", "three/addons/controls/OrbitControls.js");

// Variable fonts: Latin and Latin Extended subsets of Inter (upright and italic) and JetBrains Mono.
for (const f of [
  "inter/files/inter-latin-wght-normal.woff2",
  "inter/files/inter-latin-wght-italic.woff2",
  "inter/files/inter-latin-ext-wght-normal.woff2",
  "jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2",
]) copy(`@fontsource-variable/${f}`, join(fonts, f.split("/").pop()));

const versions = Object.fromEntries(
  ["katex", "alpinejs", "three", "@fontsource-variable/inter", "@fontsource-variable/jetbrains-mono"].map((p) => [
    p, JSON.parse(readFileSync(join(nm, p, "package.json"), "utf8")).version,
  ]),
);
writeFileSync(join(vendor, "VERSIONS.json"), JSON.stringify(versions, null, 2) + "\n");
console.log("vendored", versions);
