// Loaded with `node --import ./tests/js/setup.mjs --test tests/js/` (npm run test:js). annotations.js imports the
// bare specifier "perfect-freehand", which the browser resolves through base.html's import map; map it to the
// vendored copy here so the tests exercise the same file.
import { registerHooks } from "node:module";

const target = new URL("../../app/static/vendor/perfect-freehand/index.js", import.meta.url).href;

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === "perfect-freehand") return { url: target, format: "module", shortCircuit: true };
    return nextResolve(specifier, context);
  },
});
