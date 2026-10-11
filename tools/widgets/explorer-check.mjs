// Checks the 3D explorers' geometry without a browser: imports the module in Node, builds each explorer's pure
// geometry (circuit path, airspace model, overhead join, spin/spiral trajectories, wake field, crosswind approach,
// GNSS geometry, cloud bands, minimum-height floor, gyro precession) and renders plan views and side profiles to
// .renders/_<name>.png for a look with the Read tool.
//   node tools/widgets/explorer-check.mjs [name ...]      (default: all)
import * as THREE from "../../app/static/vendor/three/three.module.js";
import * as X from "../../app/static/explorers.js";
import { renderPng, tokens } from "../diagrams/render.mjs";
import { writeFileSync, mkdirSync } from "node:fs";

const t = tokens();
const T = t.light;
mkdirSync(".renders", { recursive: true });
const only = new Set(process.argv.slice(2));
const want = (name) => only.size === 0 || only.has(name);
const text = (x, y, s, opts = {}) => `<text x="${x}" y="${y}" fill="${opts.fill || T.fg}" font-size="${opts.size || 11}" ${opts.anchor ? `text-anchor="${opts.anchor}"` : ""} ${opts.weight ? `font-weight="${opts.weight}"` : ""}>${s}</text>`;
const poly = (pts, stroke, w = 1.5, extra = "") => `<polyline points="${pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ")}" fill="none" stroke="${stroke}" stroke-width="${w}" ${extra}/>`;
const write = (name, w, h, body) => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" font-family="sans-serif" font-size="12">${body}</svg>`;
  writeFileSync(`.renders/_${name}.png`, renderPng(svg, T, T.surface));
  console.log(`wrote .renders/_${name}.png`);
};

/* ---------------------------------------------------------------- circuit (existing) */
if (want("circuit-path")) {
  let svg = "";
  const panels = [[true, 1, "left-hand, runway 24 (take off to +x)"], [true, -1, "left-hand, runway 06"], [false, 1, "right-hand, runway 24"]];
  panels.forEach(([lh, dir, title], i) => {
    const { points, legs } = X.circuitPath(THREE, lh, dir, 10);
    const curve = new THREE.CatmullRomCurve3(points, false, "centripetal", 0.5);
    const pts = curve.getPoints(300);
    const ox = 20 + (i % 2) * 320, oy = 20 + Math.floor(i / 2) * 250;
    const Xc = (x) => ox + 150 + x * 3.2, Z = (z) => oy + 110 + z * 3.2;
    svg += text(ox, oy + 12, title, { weight: 600 });
    svg += `<rect x="${Xc(-15)}" y="${Z(-1.5)}" width="${30 * 3.2}" height="${3 * 3.2}" fill="${T["fg-muted"]}"/>`;
    svg += poly(pts.map((p) => [Xc(p.x), Z(p.z)]), T.brand);
    for (let k = 0.05; k < 1; k += 0.1) {
      const p = curve.getPointAt(k), d = curve.getTangentAt(k);
      const leg = k < legs.upwind ? "upwind" : k < legs.crosswind ? "crosswind" : k < legs.downwind ? "downwind" : k < legs.base ? "base" : "final";
      svg += `<circle cx="${Xc(p.x)}" cy="${Z(p.z)}" r="3" fill="${T.bad}"/>` + text(Xc(p.x) + 5, Z(p.z) - 4, `${leg} ${Math.round(p.y * 100)}ft`, { fill: T["fg-muted"], size: 9 });
      svg += `<line x1="${Xc(p.x)}" y1="${Z(p.z)}" x2="${Xc(p.x + d.x * 4)}" y2="${Z(p.z + d.z * 4)}" stroke="${T.bad}" stroke-width="1.5"/>`;
    }
    svg += text(Xc(0), Z(20), "+z is the aeroplane's right when flying +x; screen down = +z", { fill: T["fg-faint"], size: 10, anchor: "middle" });
  });
  {
    const { points } = X.circuitPath(THREE, true, 1, 10);
    const curve = new THREE.CatmullRomCurve3(points, false, "centripetal", 0.5);
    const ox = 340, oy = 300;
    svg += text(ox, oy, "height profile along the path", { weight: 600 });
    const pts = Array.from({ length: 200 }, (_, i) => { const u = i / 199; const p = curve.getPointAt(u); return [ox + u * 280, oy + 180 - p.y * 15]; });
    svg += poly(pts, T.ok) + `<line x1="${ox}" y1="${oy + 180}" x2="${ox + 280}" y2="${oy + 180}" stroke="${T.fg}"/>`;
  }
  write("circuit-path", 640, 520, svg);
}

/* ---------------------------------------------------------------- airspace: plan of the rings and a cross-section along the track */
if (want("airspace")) {
  const m = X.airspaceModel(true);
  let svg = text(20, 18, "airspace model: plan (1 unit = 1 km, +x east, +z south)", { weight: 600 });
  const ox = 330, oz = 200, S = 2.6;
  const Xc = (x) => ox + x * S, Z = (z) => oz + z * S;
  for (const g of [...m.rings].reverse()) {
    svg += `<circle cx="${Xc(0)}" cy="${Z(0)}" r="${g.rOut * S}" fill="${g.cls === "C" ? T.brand : T["sky-fg"]}" fill-opacity="0.12" stroke="${g.cls === "C" ? T.brand : T["sky-fg"]}"/>`;
    svg += text(Xc(0) + 4, Z(-g.rOut) + 12, g.label, { size: 10, fill: g.cls === "C" ? T.brand : T["sky-fg"] });
  }
  const j = m.jandakot, R = m.restricted;
  svg += `<circle cx="${Xc(j.x)}" cy="${Z(j.z)}" r="${j.r * S}" fill="${T.info}" fill-opacity="0.3" stroke="${T.info}"/>`;
  svg += `<rect x="${Xc(R.x - R.half)}" y="${Z(R.z - R.half)}" width="${2 * R.half * S}" height="${2 * R.half * S}" fill="${T.bad}" fill-opacity="0.25" stroke="${T.bad}"/>`;
  for (const [name, x, z] of m.places) svg += `<circle cx="${Xc(x)}" cy="${Z(z)}" r="2.5" fill="${T.fg}"/>` + text(Xc(x) + 4, Z(z) + 4, name, { size: 10 });
  const curve = new THREE.CatmullRomCurve3(m.track.map(([x, z]) => new THREE.Vector3(x, 0, z)), false, "catmullrom", 0.5);
  const tp = curve.getPoints(100);
  svg += poly(tp.map((p) => [Xc(p.x), Z(p.z)]), T.ok, 2, 'stroke-dasharray="4 3"');
  // cross-section along the track at three altitudes: which class is the aeroplane in?
  const oy = 420;
  svg += text(20, oy - 8, "along the track: lower limit of the controlled step overhead (ft) and the class at 1,500 / 3,000 / 5,000 ft", { weight: 600, size: 11 });
  const Y = (ft) => oy + 100 - ft / 100;
  const profile = [];
  for (let i = 0; i <= 100; i++) {
    const p = curve.getPointAt(i / 100);
    const here = X.airspaceAt(m, p.x, p.z, 0);
    profile.push([20 + i * 6, Y(here.lower * 1000)]);
  }
  svg += poly(profile, T.brand, 2);
  for (const [ft, colour] of [[1500, T.ok], [3000, T.warn], [5000, T.bad]]) {
    svg += `<line x1="20" y1="${Y(ft)}" x2="620" y2="${Y(ft)}" stroke="${colour}" stroke-dasharray="3 3"/>`;
    let runs = "";
    for (let i = 0; i <= 100; i += 10) { const p = curve.getPointAt(i / 100); runs += X.airspaceAt(m, p.x, p.z, ft).code + " "; }
    svg += text(22, Y(ft) - 3, `${ft} ft: ${runs}`, { size: 9, fill: colour });
  }
  svg += `<line x1="20" y1="${Y(0)}" x2="620" y2="${Y(0)}" stroke="${T.fg}"/>` + text(22, Y(0) + 12, "Jandakot → coast → Rottnest → north; tower open", { size: 9, fill: T["fg-muted"] });
  write("airspace", 640, 540, svg);
}

/* ---------------------------------------------------------------- overhead join: plan and profile */
if (want("overhead")) {
  let svg = "";
  const panels = [[true, 1, "left-hand, runway 24: join from overhead"], [false, 1, "right-hand, runway 24"]];
  panels.forEach(([lh, dir, title], i) => {
    const built = X.overheadJoinPath(THREE, lh, dir, 10);
    const curve = new THREE.CatmullRomCurve3(built.points, false, "centripetal", 0.5);
    const ox = 20 + i * 320, oy = 20;
    const Xc = (x) => ox + 150 + x * 2.6, Z = (z) => oy + 130 + z * 2.6;
    svg += text(ox, oy + 12, title, { weight: 600 });
    svg += `<rect x="${Xc(-15)}" y="${Z(-1.5)}" width="${30 * 2.6}" height="${3 * 2.6}" fill="${T["fg-muted"]}"/>`;
    svg += poly(curve.getPoints(300).map((p) => [Xc(p.x), Z(p.z)]), T.brand);
    const cp = new THREE.CatmullRomCurve3(X.circuitPath(THREE, lh, dir, 10).points, false, "centripetal", 0.5);
    svg += poly(cp.getPoints(300).map((p) => [Xc(p.x), Z(p.z)]), T["fg-faint"], 1, 'stroke-dasharray="3 3"');
    const legs = built.legs;
    for (let k = 0.03; k < 1; k += 0.08) {
      const p = curve.getPointAt(k), d = curve.getTangentAt(k);
      const leg = k < legs.overhead ? "overhead" : k < legs.deadside ? "dead side" : k < legs.crosswind ? "crosswind" : k < legs.downwind ? "downwind" : k < legs.base ? "base" : "final";
      svg += `<circle cx="${Xc(p.x)}" cy="${Z(p.z)}" r="2.5" fill="${T.bad}"/>` + text(Xc(p.x) + 4, Z(p.z) - 3, `${leg} ${Math.round(p.y * 100)}ft`, { fill: T["fg-muted"], size: 8 });
      svg += `<line x1="${Xc(p.x)}" y1="${Z(p.z)}" x2="${Xc(p.x + d.x * 4)}" y2="${Z(p.z + d.z * 4)}" stroke="${T.bad}" stroke-width="1.5"/>`;
    }
    svg += text(Xc(0), Z(40), "screen down = +z = dead side for a left-hand circuit", { fill: T["fg-faint"], size: 10, anchor: "middle" });
  });
  {
    const { points } = X.overheadJoinPath(THREE, true, 1, 10);
    const curve = new THREE.CatmullRomCurve3(points, false, "centripetal", 0.5);
    const ox = 20, oy = 290;
    svg += text(ox, oy, "height profile: 1,500 ft overhead, down to 1,000 ft on the dead side, level until base", { weight: 600 });
    const pts = Array.from({ length: 200 }, (_, i) => { const u = i / 199; const p = curve.getPointAt(u); return [ox + u * 600, oy + 180 - p.y * 10]; });
    svg += poly(pts, T.ok) + `<line x1="${ox}" y1="${oy + 180}" x2="${ox + 600}" y2="${oy + 180}" stroke="${T.fg}"/>`;
    for (const h of [10, 15]) svg += `<line x1="${ox}" y1="${oy + 180 - h * 10}" x2="${ox + 600}" y2="${oy + 180 - h * 10}" stroke="${T.line}" stroke-dasharray="3 3"/>` + text(ox + 2, oy + 177 - h * 10, `${h * 100} ft`, { size: 9, fill: T["fg-muted"] });
  }
  write("overhead", 640, 500, svg);
}

/* ---------------------------------------------------------------- spin vs spiral: plan, profile, ASI and g against time */
if (want("spinspiral")) {
  let svg = "";
  for (const [i, mode] of ["spin", "spiral"].entries()) {
    const ox = 20 + i * 320, oy = 20;
    svg += text(ox, oy + 12, `${mode}: plan (m) and height (m) over 12 s`, { weight: 600 });
    const S = mode === "spin" ? 12 : 0.5;
    const plan = [], prof = [], ias = [], gg = [];
    for (let k = 0; k <= 120; k++) {
      const s = X.spinSpiralState(mode, k / 10);
      plan.push([ox + 150 + s.x * S, oy + 110 - s.z * S]);
      prof.push([ox + k * 2.4, oy + 240 - s.y * 0.35]);
      ias.push([ox + k * 2.4, oy + 400 - s.ias * 1.2]);
      gg.push([ox + k * 2.4, oy + 400 - s.g * 40]);
    }
    svg += poly(plan, T.brand) + text(ox, oy + 30, `plan scale ${S} px/m; radius ${mode === "spin" ? "4 m" : Math.round(X.spinSpiralState(mode, 0).radius) + " m (compressed 4x)"}`, { size: 9, fill: T["fg-muted"] });
    svg += poly(prof, T.ok) + text(ox, oy + 232, "height lost: " + Math.round(-X.spinSpiralState(mode, 12).y) + " m in 12 s = " + X.spinSpiralState(mode, 12).rod + " ft/min", { size: 9, fill: T["fg-muted"] });
    svg += poly(ias, T.bad) + poly(gg, T.info) + text(ox, oy + 420, `ASI ${Math.round(X.spinSpiralState(mode, 0).ias)} → ${Math.round(X.spinSpiralState(mode, 12).ias)} kt (red); g ${X.spinSpiralState(mode, 0).g.toFixed(1)} → ${X.spinSpiralState(mode, 12).g.toFixed(1)} (blue); bank ${X.spinSpiralState(mode, 0).bank}° → ${X.spinSpiralState(mode, 12).bank.toFixed(0)}°`, { size: 9, fill: T["fg-muted"] });
  }
  write("spinspiral", 640, 460, svg);
}

/* ---------------------------------------------------------------- wake: plan and side view of the vortex pair at 10, 25 and 40 s, calm and 2 kt crosswind */
if (want("wake")) {
  let svg = "";
  const cases = [[0, "calm"], [2, "2 kt crosswind from the right (+z)"], [8, "8 kt crosswind from the right"]];
  cases.forEach(([xw, title], i) => {
    const oy = 20 + i * 165;
    svg += text(20, oy, `wake at 40 s, ${title}: plan (1 unit = 10 m; +z down the page)`, { weight: 600 });
    const Xc = (x) => 30 + x * 1.7, Z = (z) => oy + 70 + z * 4;
    const f = X.wakeField(40, xw);
    svg += `<rect x="${Xc(f.runway.x0)}" y="${Z(-f.runway.halfWidth)}" width="${(f.runway.x1 - f.runway.x0) * 1.7}" height="${2 * f.runway.halfWidth * 4}" fill="${T["fg-muted"]}" fill-opacity="0.35"/>`;
    svg += poly(f.vortices.map((v) => [Xc(v.x), Z(v.zL)]), T.bad) + poly(f.vortices.map((v) => [Xc(v.x), Z(v.zR)]), T.bad);
    svg += poly(f.youPath.map((q) => [Xc(q.x), Z(q.z)]), T.ok, 1.5, 'stroke-dasharray="4 3"');
    svg += `<circle cx="${Xc(f.heavy.x)}" cy="${Z(0)}" r="3" fill="${T.fg}"/>` + text(Xc(f.heavy.x) - 60, Z(0) - 6, `heavy ${Math.round(f.heavy.y * 10)} m up`, { size: 9 });
    const v0 = f.vortices[0], v20 = f.vortices[20], v39 = f.vortices[39];
    svg += text(20, oy + 12, `at the rotation point after 40 s: left ${Math.round(v0.zL * 10)} m, right ${Math.round(v0.zR * 10)} m from the centreline (runway edge ±${f.runway.halfWidth * 10} m), strength ${Math.round(v0.strength * 100)}%`, { size: 9, fill: T["fg-muted"] });
    svg += text(20, oy + 24, `shed 20 s ago at x=${Math.round(v20.x * 10)} m, path ${Math.round(v20.pathY * 10)} m: now ${Math.round(v20.y * 10)} m up (sunk ${Math.round((v20.pathY - v20.y) * 10 * 3.28)} ft); shed 1 s ago: path ${Math.round(v39.pathY * 10)} m, now ${Math.round(v39.y * 10)} m`, { size: 9, fill: T["fg-muted"] });
    svg += text(20, oy + 36, `you at 40 s: x=${Math.round(f.you.x * 10)} m, ${Math.round(f.you.y * 10)} m up, z=${Math.round(f.you.z * 10)} m (upwind side); heavy's path there: ${Math.round((f.you.x) * Math.tan(7 * Math.PI / 180) * 10)} m`, { size: 9, fill: T.ok });
  });
  // side view
  {
    const oy = 520;
    svg += text(20, oy, "side view at 40 s (calm): heavy's path, vortex cores, your path", { weight: 600 });
    const Xc = (x) => 30 + x * 1.7, Y = (y) => oy + 90 - y * 2;
    const f = X.wakeField(40, 0);
    svg += `<line x1="${Xc(-67)}" y1="${Y(0)}" x2="${Xc(133)}" y2="${Y(0)}" stroke="${T.fg}" stroke-width="3"/>`;
    svg += poly(f.vortices.map((v) => [Xc(v.x), Y(v.pathY)]), T["fg-muted"], 1, 'stroke-dasharray="3 3"');
    svg += poly(f.vortices.map((v) => [Xc(v.x), Y(v.y)]), T.bad);
    svg += poly(f.youPath.map((q) => [Xc(q.x), Y(q.y)]), T.ok, 1.5, 'stroke-dasharray="4 3"');
  }
  write("wake", 640, 640, svg);
}

/* ---------------------------------------------------------------- crosswind: plan of track, heading and the no-correction ghost; bank/heading along the approach */
if (want("crosswind")) {
  let svg = "";
  [["crab", 10], ["wingdown", 10], ["crab", 20]].forEach(([method, xw], i) => {
    const oy = 20 + i * 150;
    svg += text(20, oy, `${method}, ${xw} kt crosswind from the right (+z, down the page), TAS 65 kt: plan`, { weight: 600 });
    const Xc = (x) => 30 + (x + 900) * 0.55, Z = (z) => oy + 60 + z * 0.55;
    svg += `<rect x="${Xc(-100)}" y="${Z(-15)}" width="${600 * 0.55}" height="${30 * 0.55}" fill="${T["fg-muted"]}" fill-opacity="0.35"/>`;
    const pts = [], ghost = [];
    for (let k = 0; k <= 40; k++) {
      const a = X.crosswindApproach(method, xw, 65, k / 40);
      pts.push([Xc(a.x), Z(a.z)]); ghost.push([Xc(a.x), Z(a.ghostZ)]);
      if (k % 5 === 0) {
        const L = 25;
        svg += `<line x1="${Xc(a.x)}" y1="${Z(a.z)}" x2="${Xc(a.x) + L * Math.cos(a.heading)}" y2="${Z(a.z) + L * Math.sin(a.heading)}" stroke="${T.brand}" stroke-width="2"/>`;
        svg += text(Xc(a.x), Z(a.z) + 22, `h${(a.heading * 180 / Math.PI).toFixed(0)}° b${(a.bank * 180 / Math.PI).toFixed(0)}° ${Math.round(a.y)}m`, { size: 7, fill: T["fg-muted"] });
      }
    }
    svg += poly(pts, T.ok, 2) + poly(ghost, T.bad, 1, 'stroke-dasharray="4 3"');
    const a0 = X.crosswindApproach(method, xw, 65, 0);
    svg += text(20, oy + 12, `crab angle ${a0.crabDeg.toFixed(1)}°; no-correction drift at the threshold ${Math.round(-X.crosswindApproach(method, xw, 65, 0.88).ghostZ)} m downwind`, { size: 9, fill: T["fg-muted"] });
  });
  write("crosswind", 640, 470, svg);
}

/* ---------------------------------------------------------------- gnss: side elevation of the range spheres, and the status for 1..6 satellites */
if (want("gnss")) {
  let svg = "";
  [[3, false, false, false, "3 satellites, perfect clock"], [3, true, false, false, "3 satellites, receiver clock wrong"], [5, false, false, true, "5 satellites, one faulty"], [6, false, true, false, "6 satellites bunched (high DOP)"]].forEach(([n, ce, bu, fa, title], i) => {
    const ox = 20 + (i % 2) * 310, oy = 20 + Math.floor(i / 2) * 230;
    const g = X.gnssGeometry(n, { clockError: ce, bunched: bu, faulty: fa });
    svg += text(ox, oy, title, { weight: 600 });
    const Xc = (x) => ox + 150 + x * 3.4, Y = (y) => oy + 170 - y * 3.4;
    svg += `<circle cx="${Xc(0)}" cy="${Y(0)}" r="${g.earthRadius * 3.4}" fill="${T["sky-soft"]}" stroke="${T["sky-fg"]}"/>`;
    for (const s of g.sats) {
      const colour = s.faulty ? T.bad : ce ? T.warn : T.info;
      svg += `<circle cx="${Xc(s.pos[0])}" cy="${Y(s.pos[1])}" r="${s.range * 3.4}" fill="none" stroke="${colour}" stroke-opacity="0.6"/>`;
      svg += `<circle cx="${Xc(s.pos[0])}" cy="${Y(s.pos[1])}" r="3" fill="${colour}"/>` + text(Xc(s.pos[0]) + 4, Y(s.pos[1]) - 4, `${s.id} r=${s.range.toFixed(1)} (true ${s.trueRange.toFixed(1)})`, { size: 7, fill: colour });
    }
    svg += `<circle cx="${Xc(0)}" cy="${Y(g.earthRadius)}" r="3" fill="${T.brand}"/>`;
    if (g.points) svg += `<circle cx="${Xc(g.points.discarded[0])}" cy="${Y(g.points.discarded[1])}" r="3" fill="${T["fg-muted"]}"/>` + text(Xc(g.points.discarded[0]) + 4, Y(g.points.discarded[1]), g.points.discardedWhere, { size: 8, fill: T["fg-muted"] });
    svg += text(ox, oy + 215, g.status.slice(0, 95), { size: 8, fill: T["fg-muted"] });
  });
  svg += text(20, 500, "projection: x and y only (z dropped), so sphere circles may look off; the numbers are what matter", { size: 9, fill: T["fg-faint"] });
  write("gnss", 640, 520, svg);
}

/* ---------------------------------------------------------------- clouds: elevation of the bands and each genus's base and top */
if (want("clouds")) {
  let svg = text(20, 18, "cloud genera: base and top (1,000 ft units) against the lesson's bands", { weight: 600 });
  const Y = (kft) => 420 - kft * 10.5;
  for (const b of X.cloudBands()) {
    svg += `<rect x="60" y="${Y(b.to)}" width="560" height="${(b.to - b.from) * 10.5}" fill="${T["sky-soft"]}" fill-opacity="${b.name === "High" ? 0.6 : b.name === "Middle" ? 0.4 : 0.2}" stroke="${T["sky-fg"]}"/>`;
    svg += text(64, Y(b.to) + 12, `${b.name}: ${b.note}`, { size: 10, fill: T["sky-fg"] });
  }
  X.cloudGenera().forEach((g, i) => {
    const x = 80 + i * 54;
    svg += `<rect x="${x}" y="${Y(g.top)}" width="40" height="${Math.max(2, (g.top - g.base) * 10.5)}" fill="${g.form === "tower" || g.form === "slab" ? T["fg-muted"] : T.surface}" stroke="${T.fg}"/>`;
    svg += text(x + 20, Y(g.top) - 4, g.abbr, { size: 10, anchor: "middle", weight: 600 }) + text(x + 20, Y(g.base) + 11, `${g.base}-${g.top}`, { size: 8, anchor: "middle", fill: T["fg-muted"] });
  });
  for (const h of [0, 6.5, 20, 36]) svg += text(22, Y(h) + 4, `${h * 1000}`, { size: 9, fill: T["fg-muted"] });
  write("clouds", 640, 440, svg);
}

/* ---------------------------------------------------------------- minimum heights: side view of the town and country with the floor profile */
if (want("minheights")) {
  const w = X.minimumHeightWorld();
  let svg = text(20, 18, "minimum-height floor along the track (1 unit = 100 m); 1,000 ft above the highest obstacle within 600 m over the town, 500 ft within 300 m elsewhere", { weight: 600, size: 10 });
  const Xc = (x) => 320 + x * 9.5, Y = (m) => 330 - m * 0.45;
  svg += `<rect x="${Xc(w.populous[0])}" y="${Y(0)}" width="${(w.populous[1] - w.populous[0]) * 9.5}" height="14" fill="${T.warn}" fill-opacity="0.4"/>` + text(Xc(0), Y(0) + 26, "populous area", { size: 9, anchor: "middle", fill: T.warn });
  for (const o of w.obstacles) svg += `<rect x="${Xc(o.x) - o.w * 4}" y="${Y(o.h)}" width="${Math.max(2, o.w * 8)}" height="${o.h * 0.45}" fill="${o.kind === "tree" ? T.ok : T["fg-muted"]}"/>`;
  const pts = [];
  for (let x = -30; x <= 30; x += 0.25) pts.push([Xc(x), Y(X.minimumHeightAt(w, x).floorFt / 3.2808)]);
  svg += poly(pts, T.bad, 2);
  for (const x of [-25, -22, -14, -8, 0, 5.5, 8, 12, 16, 23, 28]) { const r = X.minimumHeightAt(w, x); svg += text(Xc(x), Y(r.floorFt / 3.2808) - 6, `${r.floorFt}`, { size: 8, anchor: "middle", fill: T.bad }); }
  for (const m of [0, 152, 305, 457]) svg += `<line x1="20" y1="${Y(m)}" x2="620" y2="${Y(m)}" stroke="${T.line}" stroke-dasharray="3 3"/>` + text(22, Y(m) - 2, `${Math.round(m * 3.2808)} ft`, { size: 8, fill: T["fg-faint"] });
  const probes = [[0, "town centre"], [5.5, "under the tower"], [9, "350 m from the tower, in town"], [12, "country, 650 m from the tower"], [23, "over the hill"], [-22, "over the mast"]];
  probes.forEach(([x, label], i) => { const r = X.minimumHeightAt(w, x); svg += text(20, 360 + i * 12, `x=${x}: ${label}: ${r.populous ? "populous" : "elsewhere"}, highest ${r.highest.name || r.highest.kind} ${Math.round(r.highest.h)} m → floor ${r.floorFt} ft`, { size: 9, fill: T["fg-muted"] }); });
  write("minheights", 640, 440, svg);
}

/* ---------------------------------------------------------------- gyro: precession response table */
if (want("gyro")) {
  let svg = text(20, 18, "precession: where a push acts (plan view, nose up the page, +z right)", { weight: 600 });
  [[0, true], [90, true], [180, true], [270, true], [0, false], [90, false]].forEach(([at, cw], i) => {
    const r = X.precessionResponse(at, cw);
    const cx = 80 + (i % 3) * 200, cy = 110 + Math.floor(i / 3) * 170;
    svg += `<circle cx="${cx}" cy="${cy}" r="45" fill="none" stroke="${T.fg}"/>`;
    const pt = (deg, rr) => [cx + rr * Math.sin(deg * Math.PI / 180), cy - rr * Math.cos(deg * Math.PI / 180)];   // 0° = nose (up the page), 90° = right wing
    const [px, py] = pt(r.pushAt, 45), [qx, qy] = pt(r.responseAt, 45);
    svg += `<circle cx="${px}" cy="${py}" r="5" fill="${T.warn}"/><circle cx="${qx}" cy="${qy}" r="5" fill="${T.bad}"/>`;
    svg += text(cx, cy - 60, `${cw ? "clockwise" : "anticlockwise"} from above`, { size: 9, anchor: "middle" }) + text(cx, cy + 66, `push ${r.pushAt}° → acts ${r.responseAt}°`, { size: 9, anchor: "middle", fill: T["fg-muted"] });
  });
  svg += text(20, 420, "The lesson: a push acts 90° further round, in the direction of rotation. Clockwise from above: nose (0°) → right wing (90°).", { size: 10, fill: T["fg-muted"] });
  write("gyro", 640, 440, svg);
}
