// Renders every equation's LaTeX with the vendored KaTeX (the same build the browser uses) and reports the ones
// that fail, so a typo never reaches the equation sheet as red error text.
//   python -m app.seed.equations --json | node tools/equations/katex-check.mjs     (npm run katex-check)
// Input on stdin: a JSON array of {id, latex}. Prints "id: message" per failure; exit code 1 if there were any.
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

const root = new URL("../..", import.meta.url).pathname;
const katex = createRequire(import.meta.url)(`${root}app/static/vendor/katex/katex.min.js`);

const items = JSON.parse(readFileSync(0, "utf8") || "[]");
let failures = 0;
for (const { id, latex } of items) {
  try {
    // strict "ignore" matches app.js renderMaths, so only real parse errors count.
    katex.renderToString(latex, { throwOnError: true, displayMode: true, strict: "ignore" });
  } catch (err) {
    failures++;
    console.log(`${id}: ${String(err.message || err).replace(/\s+/g, " ")}`);
  }
}
console.log(`katex-check: ${items.length} formulas, ${failures} failed`);
process.exit(failures ? 1 : 0);
