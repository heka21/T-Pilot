// Renders the procedural Three.js aeroplane (makePlane) offline as a wireframe projection from three views,
// so its proportions can be checked without WebGL. Output: .renders/_plane-3d.png
import * as THREE from "../../app/static/vendor/three/three.module.js";
import { makePlane } from "../../app/static/explorers.js";
import { renderPng, tokens } from "../diagrams/render.mjs";
import { writeFileSync, mkdirSync } from "node:fs";

const t = tokens();
const colours = { fg: t.light.fg, fgMuted: t.light["fg-muted"], surface: t.light.surface, brand: t.light.brand, skyFg: t.light["sky-fg"], dark: false };
const parts = makePlane(THREE, colours);
parts.aileronR.rotation.z = -0.4; parts.aileronL.rotation.z = 0.4; parts.elevator.rotation.z = -0.4; parts.rudder.rotation.y = 0.4;
parts.group.updateMatrixWorld(true);
const edgesByMesh = [];
parts.group.traverse((o) => {
  if (!o.isMesh) return;
  const eg = new THREE.EdgesGeometry(o.geometry, 25);
  const pos = eg.attributes.position;
  const pts = [];
  for (let i = 0; i < pos.count; i++) pts.push(new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld));
  edgesByMesh.push({ pts, colour: o.material.color.getStyle() });
});
let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480">`;
const views = [["side (from +z, nose right)", (p) => [p.x, -p.y], 20, 20], ["top (from +y, nose right, +z down)", (p) => [p.x, p.z], 20, 250], ["rear (from -x, +z right)", (p) => [p.z, -p.y], 340, 20]];
for (const [title, proj, ox, oy] of views) {
  svg += `<text x="${ox}" y="${oy + 12}" font-size="12" fill="${t.light.fg}">${title}</text>`;
  for (const { pts, colour } of edgesByMesh) {
    for (let i = 0; i < pts.length; i += 2) {
      const [x1, y1] = proj(pts[i]), [x2, y2] = proj(pts[i + 1]);
      svg += `<line x1="${(ox + 150 + x1 * 24).toFixed(1)}" y1="${(oy + 120 + y1 * 24).toFixed(1)}" x2="${(ox + 150 + x2 * 24).toFixed(1)}" y2="${(oy + 120 + y2 * 24).toFixed(1)}" stroke="${colour === "rgb(255,255,255)" ? t.light["fg-muted"] : colour}" stroke-width="0.8"/>`;
    }
  }
}
svg += "</svg>";
mkdirSync(".renders", { recursive: true });
writeFileSync(".renders/_plane-3d.png", renderPng(svg, t.light, t.light.surface));
console.log("wrote .renders/_plane-3d.png");
