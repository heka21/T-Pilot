// Checks the 3D explorers' geometry without a browser: imports the module in Node, builds the circuit path,
// and renders a plan view and side profile to .renders/_circuit-path.png for a look.
import * as THREE from "../../app/static/vendor/three/three.module.js";
import { circuitPath } from "../../app/static/explorers.js";
import { renderPng, tokens } from "../diagrams/render.mjs";
import { writeFileSync, mkdirSync } from "node:fs";

const t = tokens();
mkdirSync(".renders", { recursive: true });
let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 520" font-family="sans-serif" font-size="12">`;
const panels = [[true, 1, "left-hand, runway 24 (take off to +x)"], [true, -1, "left-hand, runway 06"], [false, 1, "right-hand, runway 24"]];
panels.forEach(([lh, dir, title], i) => {
  const { points, legs } = circuitPath(THREE, lh, dir, 10);
  const curve = new THREE.CatmullRomCurve3(points, false, "centripetal", 0.5);
  const pts = curve.getPoints(300);
  const ox = 20 + (i % 2) * 320, oy = 20 + Math.floor(i / 2) * 250;
  const X = (x) => ox + 150 + x * 3.2, Z = (z) => oy + 110 + z * 3.2;
  svg += `<text x="${ox}" y="${oy + 12}" fill="${t.light.fg}" font-weight="600">${title}</text>`;
  svg += `<rect x="${X(-15)}" y="${Z(-1.5)}" width="${30 * 3.2}" height="${3 * 3.2}" fill="${t.light["fg-muted"]}"/>`;
  svg += `<polyline points="${pts.map((p) => `${X(p.x).toFixed(1)},${Z(p.z).toFixed(1)}`).join(" ")}" fill="none" stroke="${t.light.brand}" stroke-width="1.5"/>`;
  // arrows every 10% to show direction, colour by leg
  for (let k = 0.05; k < 1; k += 0.1) {
    const p = curve.getPointAt(k), d = curve.getTangentAt(k);
    const leg = k < legs.upwind ? "upwind" : k < legs.crosswind ? "crosswind" : k < legs.downwind ? "downwind" : k < legs.base ? "base" : "final";
    svg += `<circle cx="${X(p.x)}" cy="${Z(p.z)}" r="3" fill="${t.light.bad}"/><text x="${X(p.x) + 5}" y="${Z(p.z) - 4}" fill="${t.light["fg-muted"]}" font-size="9">${leg} ${Math.round(p.y * 100)}ft</text>`;
    svg += `<line x1="${X(p.x)}" y1="${Z(p.z)}" x2="${X(p.x + d.x * 4)}" y2="${Z(p.z + d.z * 4)}" stroke="${t.light.bad}" stroke-width="1.5"/>`;
  }
  svg += `<text x="${X(0)}" y="${Z(20)}" fill="${t.light["fg-faint"]}" font-size="10" text-anchor="middle">+z is the aeroplane's right when flying +x; screen down = +z</text>`;
});
// side profile of the canonical circuit (height vs path fraction)
{
  const { points } = circuitPath(THREE, true, 1, 10);
  const curve = new THREE.CatmullRomCurve3(points, false, "centripetal", 0.5);
  const ox = 340, oy = 300;
  svg += `<text x="${ox}" y="${oy}" fill="${t.light.fg}" font-weight="600">height profile along the path</text>`;
  const pts = Array.from({ length: 200 }, (_, i) => { const u = i / 199; const p = curve.getPointAt(u); return `${ox + u * 280},${oy + 180 - p.y * 15}`; });
  svg += `<polyline points="${pts.join(" ")}" fill="none" stroke="${t.light.ok}" stroke-width="1.5"/><line x1="${ox}" y1="${oy + 180}" x2="${ox + 280}" y2="${oy + 180}" stroke="${t.light.fg}"/>`;
}
svg += "</svg>";
writeFileSync(".renders/_circuit-path.png", renderPng(svg, t.light, t.light.surface));
console.log("wrote .renders/_circuit-path.png");
