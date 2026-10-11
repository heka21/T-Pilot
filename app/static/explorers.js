/* Three.js explorers for the notes. Loaded as a module on every page but only imports Three.js when a
   <div data-widget="explorer" data-explorer="…"> is present. Each explorer builds the shared procedural
   aeroplane (makePlane) and wires the sliders/buttons found inside the widget (data-param, data-out,
   data-action). Colours come from the CSS tokens so the scene follows the theme. */

const EXPLORERS = {};
let threePromise = null;
function loadThree() {
  threePromise ||= Promise.all([import("three"), import("three/addons/controls/OrbitControls.js")])
    .then(([THREE, { OrbitControls }]) => ({ THREE, OrbitControls }));
  return threePromise;
}

export function themeColours() {
  const cs = getComputedStyle(document.documentElement);
  const get = (k) => cs.getPropertyValue(`--color-${k}`).trim();
  return {
    fg: get("fg"), fgMuted: get("fg-muted"), fgFaint: get("fg-faint"), line: get("line"), lineStrong: get("line-strong"),
    surface: get("surface"), surface2: get("surface-2"), brand: get("brand"), brandSoft: get("brand-soft"), info: get("info"), ok: get("ok"),
    warn: get("warn"), bad: get("bad"), skySoft: get("sky-soft"), skyFg: get("sky-fg"), tarmac: get("tarmac"), paint: get("paint"),
    dark: document.documentElement.dataset.theme ? document.documentElement.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches,
  };
}

/* ------------------------------------------------------------------ the aeroplane
   A Cessna 152 at its real size in metres (7.3 m long, 10.2 m span, 2.6 m tall), CG at the origin, the same
   shape as the SVG silhouettes in tools/diagrams/svg.py: short blunt cowl, cabin glass just above a long, nearly
   level tail cone, high strut-braced wing on the roof, big swept fin, tricycle gear (ground at y = -1.43).
   Axes: +X nose, +Y up, +Z right wing. Parts with hinges are Groups whose rotation is set by the explorers
   (aileronL/R, elevator: rotation.z about the hinge; rudder: rotation.y about its raked hinge; prop: rotation.x).
   The wing's chord plane is y = WING_Y (used for the chord line); its leading edge is at x = WING_LE. */
export const WING_Y = 0.58;
export const WING_LE = 0.45;
export function makePlane(THREE, c) {
  const body = new THREE.MeshStandardMaterial({ color: c.dark ? c.fgMuted : c.surface, roughness: 0.55, metalness: 0.05 });
  const edge = new THREE.MeshStandardMaterial({ color: c.fg, roughness: 0.6 });
  const control = new THREE.MeshStandardMaterial({ color: c.brand, roughness: 0.5 });
  const glass = new THREE.MeshStandardMaterial({ color: c.skyFg, roughness: 0.2, transparent: true, opacity: 0.55 });
  const plane = new THREE.Group();
  const parts = { materials: { body, edge, control, glass } };

  const slab = (w, h, d, mat) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  const planform = (pts, thickness, mat) => {    // pts in (x, z); extruded thickness along y
    const shape = new THREE.Shape(pts.map(([x, z]) => new THREE.Vector2(x, z)));
    const geo = new THREE.ExtrudeGeometry(shape, { depth: thickness, bevelEnabled: false });
    geo.rotateX(Math.PI / 2);            // shape plane (x, y=z) -> (x, z), depth along -y
    geo.translate(0, thickness / 2, 0);
    return new THREE.Mesh(geo, mat);
  };
  const profileXY = (pts, thickness, mat) => {   // pts in (x, y), extruded symmetrically along z (fin, rudder, windows)
    const shape = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, y)));
    const geo = new THREE.ExtrudeGeometry(shape, { depth: thickness, bevelEnabled: false });
    geo.translate(0, 0, -thickness / 2);
    return new THREE.Mesh(geo, mat);
  };
  const strut = (from, to, radius, mat) => {
    const a = new THREE.Vector3(...from), b = new THREE.Vector3(...to), d = b.clone().sub(a);
    const m = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, d.length(), 8), mat);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.clone().normalize());
    m.position.copy(a).addScaledVector(d, 0.5);
    return m;
  };
  // fuselage lofted through boxy rounded sections: [x, half-width at the belly, half-width at the top, belly y, top y]
  const loft = (stations, mat, n = 28) => {
    const pos = [], idx = [];
    for (const [x, wb, wt, yb, yt] of stations) {
      for (let k = 0; k < n; k++) {
        const t = (2 * Math.PI * k) / n, ct = Math.cos(t), st = Math.sin(t);
        const u = Math.sign(ct) * Math.abs(ct) ** 0.5, v = Math.sign(st) * Math.abs(st) ** 0.5;   // squircle
        pos.push(x, (yb + yt) / 2 + v * (yt - yb) / 2, u * (wb + (wt - wb) * (v + 1) / 2));
      }
    }
    for (let s = 0; s < stations.length - 1; s++) {
      for (let k = 0; k < n; k++) {
        const a = s * n + k, b = s * n + (k + 1) % n, c2 = a + n, d = b + n;
        idx.push(a, c2, b, b, c2, d);
      }
    }
    for (const [s, flip] of [[0, false], [stations.length - 1, true]]) {   // flat caps (the spinner and rudder cover them)
      const centre = pos.length / 3, [x, , , yb, yt] = stations[s];
      pos.push(x, (yb + yt) / 2, 0);
      for (let k = 0; k < n; k++) {
        const a = s * n + k, b = s * n + (k + 1) % n;
        flip ? idx.push(centre, b, a) : idx.push(centre, a, b);
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    geo.setIndex(idx);
    geo.computeVertexNormals();
    return new THREE.Mesh(geo, mat);
  };
  // a control surface that turns about a hinge: the Group sits on the hinge, the explorers rotate it
  const hinged = (mesh, x, y, z, name) => {
    const g = new THREE.Group();
    g.position.set(x, y, z);
    g.add(mesh);
    plane.add(g);
    parts[name] = g;
    return g;
  };

  // fuselage: cowl from the spinner back to the firewall (x 0.85), windscreen up to the roof, cabin under the wing,
  // the rear window sloping down behind it, then the tail cone with a level top and a rising belly
  plane.add(loft([
    [2.00, 0.22, 0.24, -0.45, 0.00],
    [1.90, 0.36, 0.38, -0.58, 0.02],
    [1.60, 0.45, 0.46, -0.74, 0.03],
    [1.20, 0.49, 0.48, -0.85, 0.03],
    [0.75, 0.52, 0.50, -0.93, 0.03],
    [0.40, 0.52, 0.49, -0.94, 0.50],
    [-0.60, 0.52, 0.49, -0.94, 0.50],
    [-1.29, 0.50, 0.46, -0.87, 0.50],
    [-1.91, 0.42, 0.36, -0.78, 0.03],
    [-3.00, 0.29, 0.24, -0.64, 0.01],
    [-4.00, 0.18, 0.14, -0.51, -0.01],
    [-4.85, 0.08, 0.06, -0.41, -0.04],
  ], body));
  // glass: windscreen, door and rear side windows on both sides, the rear window behind the wing
  const windscreen = slab(0.6, 0.02, 0.92, glass);     // raked from the cowl top (0.75, 0.03) to the roof (0.40, 0.50)
  windscreen.position.set(0.59, 0.28, 0);
  windscreen.rotation.z = Math.atan2(0.47, -0.35);
  plane.add(windscreen);
  for (const side of [-1, 1]) {
    const door = profileXY([[0.3, 0.07], [0.3, 0.41], [-0.41, 0.41], [-0.41, 0.07]], 0.02, glass);
    const rear = profileXY([[-0.5, 0.07], [-0.5, 0.41], [-1.13, 0.41], [-0.93, 0.07]], 0.02, glass);
    door.position.z = rear.position.z = side * 0.515;
    plane.add(door, rear);
  }
  const rearWindow = slab(0.7, 0.02, 0.6, glass);     // sloping from the roof (-1.29, 0.50) down to the tail cone (-1.91, 0.03)
  rearWindow.position.set(-1.58, 0.3, 0);
  rearWindow.rotation.z = Math.atan2(0.47, 0.62);
  plane.add(rearWindow);

  // high wing on the roof: constant chord to 2.45 m out, then tapering to rounded tips; the trailing edge is cut
  // back to the hinge line where the flaps and ailerons sit
  const HINGE = -0.87, TE = -1.2;
  const wing = planform([[WING_LE, -2.45], [-0.07, -5.0], [-0.25, -5.1], [-1.05, -5.1], [TE, -5.0], [TE, -4.62], [HINGE, -4.62],
    [HINGE, 4.62], [TE, 4.62], [TE, 5.0], [-1.05, 5.1], [-0.25, 5.1], [-0.07, 5.0], [WING_LE, 2.45]], 0.16, body);
  wing.position.y = WING_Y;
  plane.add(wing);
  const surface = (chord, span, mat) => { const m = slab(chord, 0.07, span, mat); m.position.x = -chord / 2; return m; };
  hinged(surface(0.33, 2.0, control), HINGE, WING_Y, -3.6, "aileronL");
  hinged(surface(0.33, 2.0, control), HINGE, WING_Y, 3.6, "aileronR");
  hinged(surface(0.33, 2.0, body), HINGE, WING_Y, -1.56, "flapL");
  hinged(surface(0.33, 2.0, body), HINGE, WING_Y, 1.56, "flapR");
  // wing struts: lower fuselage to the wing underside 2.45 m out
  plane.add(strut([0.18, -0.76, -0.5], [-0.04, WING_Y - 0.08, -2.45], 0.035, edge));
  plane.add(strut([0.18, -0.76, 0.5], [-0.04, WING_Y - 0.08, 2.45], 0.035, edge));

  // tailplane at the bottom of the tail cone and the elevator behind it
  const tail = planform([[-3.83, -0.2], [-4.21, -1.7], [-4.68, -1.7], [-4.68, 1.7], [-4.21, 1.7], [-3.83, 0.2]], 0.07, body);
  tail.position.y = -0.32;
  plane.add(tail);
  hinged(surface(0.5, 3.4, control), -4.68, -0.32, 0, "elevator");

  // swept fin with its dorsal fillet, and the rudder on a raked hinge (rotation.y turns it about that hinge)
  plane.add(profileXY([[-2.79, -0.02], [-3.6, 0.07], [-4.08, 0.29], [-4.89, 1.07], [-4.96, 1.05], [-4.54, -0.3], [-4.3, -0.06]], 0.09, body));
  const HB = [-4.54, -0.35], HT = [-4.96, 1.0], tilt = Math.atan2(HB[0] - HT[0], HT[1] - HB[1]);
  const rudder = new THREE.Group();
  rudder.position.set(HB[0], HB[1], 0);
  rudder.rotation.order = "ZYX";
  rudder.rotation.z = tilt;
  const rudderMesh = profileXY([[0, 0], [HT[0] - HB[0], HT[1] - HB[1]], [-5.24 - HB[0], 1.07 - HB[1]], [-4.96 - HB[0], -0.38 - HB[1]]], 0.06, control);
  rudderMesh.rotation.z = -tilt;
  rudder.add(rudderMesh);
  plane.add(rudder);
  parts.rudder = rudder;

  // propeller and spinner
  const prop = new THREE.Group();
  prop.position.set(1.98, -0.19, 0);
  prop.add(slab(0.05, 1.75, 0.13, edge));
  const spinner = new THREE.Mesh(new THREE.ConeGeometry(0.17, 0.32, 20), edge);
  spinner.rotation.z = -Math.PI / 2;
  spinner.position.x = 0.14;
  prop.add(spinner);
  plane.add(prop);
  parts.prop = prop;

  // tricycle undercarriage: nose oleo under the cowl, spring-steel mains splayed from the belly just aft of the CG
  const wheel = (x, y, z, r, w) => {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, w, 20), edge);
    m.rotation.x = Math.PI / 2;
    m.position.set(x, y, z);
    plane.add(m);
  };
  wheel(-0.55, -1.18, -1.15, 0.25, 0.15);
  wheel(-0.55, -1.18, 1.15, 0.25, 0.15);
  wheel(1.1, -1.25, 0, 0.18, 0.12);
  plane.add(strut([1.0, -0.8, 0], [1.1, -1.25, 0], 0.04, edge));
  plane.add(strut([-0.25, -0.9, -0.4], [-0.55, -1.18, -1.06], 0.04, edge));
  plane.add(strut([-0.25, -0.9, 0.4], [-0.55, -1.18, 1.06], 0.04, edge));
  parts.group = plane;
  return parts;
}

/* ------------------------------------------------------------------ labels and axes */
function makeLabel(THREE, text, colour, size = 0.9) {
  const canvas = document.createElement("canvas");
  canvas.width = 512; canvas.height = 128;
  const ctx = canvas.getContext("2d");
  ctx.font = "600 56px 'Inter Variable', system-ui, sans-serif";
  ctx.fillStyle = colour;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, 256, 64);
  const tex = new THREE.CanvasTexture(canvas);
  tex.anisotropy = 4;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
  sprite.scale.set(size * 4, size, 1);
  sprite.renderOrder = 10;
  return sprite;
}

function makeAxis(THREE, dir, length, colour, label) {
  const g = new THREE.Group();
  const d = new THREE.Vector3(...dir).normalize();
  const geo = new THREE.BufferGeometry().setFromPoints([d.clone().multiplyScalar(-length), d.clone().multiplyScalar(length)]);
  g.add(new THREE.Line(geo, new THREE.LineDashedMaterial({ color: colour, dashSize: 0.3, gapSize: 0.15 })));
  g.children[0].computeLineDistances();
  g.add(new THREE.ArrowHelper(d, d.clone().multiplyScalar(length), 0.8, colour, 0.4, 0.2));
  const sprite = makeLabel(THREE, label, colour);
  sprite.position.copy(d.clone().multiplyScalar(length + 1.4));
  g.add(sprite);
  return g;
}

/* ------------------------------------------------------------------ scene plumbing shared by all explorers */
function createStage(THREE, OrbitControls, el, { camera: camPos = [-8.5, 4.5, -8.5] } = {}) {
  const holder = el.querySelector("[data-canvas]") || el;
  holder.textContent = "";
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "low-power" });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  holder.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 16 / 10, 0.1, 200);
  camera.position.set(...camPos);
  const view = el._casaView; // kept across a re-theme so the reader's camera angle survives
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.enablePan = false;
  controls.minDistance = 6;
  controls.maxDistance = 30;
  controls.target.set(0, 0, 0);
  if (view) { camera.position.fromArray(view.pos); controls.target.fromArray(view.target); }
  const c = themeColours();
  const hemi = new THREE.HemisphereLight(0xffffff, 0x8899aa, c.dark ? 1.4 : 1.1);
  const sun = new THREE.DirectionalLight(0xffffff, c.dark ? 1.6 : 1.4);
  sun.position.set(5, 10, -4);
  scene.add(hemi, sun);

  function resize() {
    const w = holder.clientWidth || 640, h = holder.clientHeight || w * 0.625;
    renderer.setSize(w, h, false);
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  resize();
  const ro = new ResizeObserver(resize);
  ro.observe(holder);

  let visible = true, running = false, tick = null, disposed = false;
  const io = new IntersectionObserver((entries) => { visible = entries[0].isIntersecting; if (visible) start(); }, { threshold: 0.05 });
  io.observe(holder);
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  function frame(t) {
    if (disposed || !visible || !holder.isConnected) { running = false; return; }
    controls.update();
    tick && tick(t / 1000, reduced.matches);
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  function start() { if (!running && !disposed) { running = true; requestAnimationFrame(frame); } }
  function dispose() {
    disposed = true;
    ro.disconnect();
    io.disconnect();
    el._casaView = { pos: camera.position.toArray(), target: controls.target.toArray() };
    controls.dispose();
    renderer.dispose();
    renderer.forceContextLoss();
  }
  start();
  el._casaStage = { dispose };
  return { renderer, scene, camera, controls, colours: c, holder, onTick(fn) { tick = fn; }, start, dispose };
}

function wireControls(el, params, onChange) {
  const outs = {};
  el.querySelectorAll("[data-out]").forEach((o) => { outs[o.dataset.out] = o; });
  const inputs = el.querySelectorAll("[data-param]");
  const defaults = {};
  inputs.forEach((inp) => {
    const k = inp.dataset.param;
    // the first mount records the authored value; a re-mount (theme change) keeps it for Reset
    if (inp.dataset.default === undefined) inp.dataset.default = inp.type === "checkbox" ? String(inp.checked) : inp.value;
    defaults[k] = inp.type === "checkbox" ? inp.dataset.default === "true" : Number(inp.dataset.default);
    params[k] = inp.type === "checkbox" ? inp.checked : Number(inp.value);
    inp.addEventListener("input", () => { params[k] = inp.type === "checkbox" ? inp.checked : Number(inp.value); onChange(params, outs); });
    inp.addEventListener("change", () => { params[k] = inp.type === "checkbox" ? inp.checked : Number(inp.value); onChange(params, outs); });
  });
  el.querySelectorAll("[data-action='reset']").forEach((b) => b.addEventListener("click", () => {
    inputs.forEach((inp) => { const k = inp.dataset.param; if (inp.type === "checkbox") inp.checked = defaults[k]; else inp.value = defaults[k]; params[k] = defaults[k]; });
    onChange(params, outs);
  }));
  el.querySelectorAll("[data-set]").forEach((b) => b.addEventListener("click", () => {
    for (const [k, v] of Object.entries(JSON.parse(b.dataset.set))) {
      params[k] = v;
      const inp = el.querySelector(`[data-param='${k}']`);
      if (inp) { if (inp.type === "checkbox") inp.checked = v; else inp.value = v; }
    }
    onChange(params, outs);
  }));
  onChange(params, outs);
  return outs;
}

const deg = (r) => `${Math.round(r * 180 / Math.PI)}°`;
const lerp = (a, b, t) => a + (b - a) * t;

/* ------------------------------------------------------------------ explorer: axes and controls (RBKA 3.2) */
EXPLORERS.axes = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el);
  const c = stage.colours;
  const plane = makePlane(THREE, c);
  const rig = new THREE.Group();        // rotated by the control inputs; the plane sits inside
  rig.add(plane.group);
  stage.scene.add(rig);
  const axes = new THREE.Group();
  axes.add(makeAxis(THREE, [1, 0, 0], 6.5, c.brand, "Longitudinal · roll"));
  axes.add(makeAxis(THREE, [0, 0, 1], 6.5, c.info, "Lateral · pitch"));
  axes.add(makeAxis(THREE, [0, 1, 0], 4.5, c.ok, "Normal · yaw"));
  rig.add(axes);
  const grid = new THREE.GridHelper(30, 15, c.line, c.line);
  grid.position.y = -4;
  stage.scene.add(grid);

  const params = {};
  const target = { roll: 0, pitch: 0, yaw: 0 };
  const MAX = 0.44;   // 25 degrees of surface travel
  wireControls(el, params, (p, outs) => {
    target.roll = p.aileron * 0.6;
    target.pitch = p.elevator * 0.45;
    target.yaw = -p.rudder * 0.45 + (p.adverseYaw ? p.aileron * 0.18 : 0);
    axes.visible = !!p.axes;
    plane.aileronR.rotation.z = -p.aileron * MAX;   // stick right: right aileron up, left aileron down
    plane.aileronL.rotation.z = p.aileron * MAX;
    plane.elevator.rotation.z = -p.elevator * MAX;  // stick back: elevator up
    plane.rudder.rotation.y = p.rudder * MAX;       // right pedal: rudder right
    const word = (v, neg, pos) => Math.abs(v) < 0.05 ? "neutral" : `${v > 0 ? pos : neg} ${Math.round(Math.abs(v) * 25)}°`;
    outs.aileron && (outs.aileron.textContent = word(p.aileron, "stick left", "stick right"));
    outs.elevator && (outs.elevator.textContent = word(p.elevator, "stick forward", "stick back"));
    outs.rudder && (outs.rudder.textContent = word(p.rudder, "left pedal", "right pedal"));
    outs.effect && (outs.effect.textContent = describe(p));
  });
  function describe(p) {
    const bits = [];
    if (Math.abs(p.aileron) >= 0.05) bits.push(`rolls ${p.aileron > 0 ? "right" : "left"} about the longitudinal axis` + (p.adverseYaw ? `, nose yaws ${p.aileron > 0 ? "left" : "right"} (adverse yaw)` : ""));
    if (Math.abs(p.elevator) >= 0.05) bits.push(`pitches nose ${p.elevator > 0 ? "up" : "down"} about the lateral axis`);
    if (Math.abs(p.rudder) >= 0.05) bits.push(`yaws nose ${p.rudder > 0 ? "right" : "left"} about the normal axis`);
    return bits.length ? "The aeroplane " + bits.join("; ") + "." : "Controls neutral: straight and level.";
  }
  const cur = { roll: 0, pitch: 0, yaw: 0 };
  stage.onTick((t, reduced) => {
    const k = reduced ? 1 : 0.08;
    cur.roll = lerp(cur.roll, target.roll, k); cur.pitch = lerp(cur.pitch, target.pitch, k); cur.yaw = lerp(cur.yaw, target.yaw, k);
    rig.rotation.set(0, 0, 0);
    rig.rotateY(cur.yaw); rig.rotateZ(cur.pitch); rig.rotateX(cur.roll);
    if (!reduced) plane.prop.rotation.x = t * 14;
    const outs = el.querySelectorAll("[data-out]");
    outs.forEach((o) => {
      if (o.dataset.out === "roll") o.textContent = deg(cur.roll);
      if (o.dataset.out === "pitch") o.textContent = deg(cur.pitch);
      if (o.dataset.out === "yaw") o.textContent = deg(-cur.yaw);
    });
  });
};

/* ------------------------------------------------------------------ explorer: attitude, flight path and angle of attack (RBKA 3.1, 3.6) */
EXPLORERS.attitude = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [2, 2.5, 16] });
  const c = stage.colours;
  const plane = makePlane(THREE, c);
  plane.group.position.set(0, 0, 0);
  const rig = new THREE.Group();
  rig.add(plane.group);
  stage.scene.add(rig);
  const horizon = new THREE.GridHelper(40, 20, c.line, c.line);
  horizon.position.y = -3.2;
  stage.scene.add(horizon);
  const horizonLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-20, 0, -0.01), new THREE.Vector3(20, 0, -0.01)]),
    new THREE.LineDashedMaterial({ color: c.fgFaint, dashSize: 0.5, gapSize: 0.3 }));
  horizonLine.computeLineDistances();
  stage.scene.add(horizonLine);
  const hLabel = makeLabel(THREE, "horizon", c.fgFaint, 0.7);
  hLabel.position.set(-9, 0.5, 0);
  stage.scene.add(hLabel);

  // flight path: a long line through the CG, and the velocity arrow along it
  const pathGroup = new THREE.Group();
  const pathLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-30, 0, 0), new THREE.Vector3(30, 0, 0)]),
    new THREE.LineDashedMaterial({ color: c.ok, dashSize: 0.6, gapSize: 0.3 }));
  pathLine.computeLineDistances();
  pathGroup.add(pathLine);
  const vel = new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(4.5, 0, 0), 3.5, c.ok, 0.7, 0.35);
  pathGroup.add(vel);
  const pathLabel = makeLabel(THREE, "flight path", c.ok, 0.8);
  pathLabel.position.set(9.5, 0.9, 0);
  pathGroup.add(pathLabel);
  // relative airflow: comes from ahead, opposite to the flight path
  const raf = new THREE.ArrowHelper(new THREE.Vector3(-1, 0, 0), new THREE.Vector3(12, 1.6, 0), 4.5, c.skyFg, 0.7, 0.35);
  pathGroup.add(raf);
  const rafLabel = makeLabel(THREE, "relative airflow", c.skyFg, 0.8);
  rafLabel.position.set(10.5, 2.6, 0);
  pathGroup.add(rafLabel);
  stage.scene.add(pathGroup);

  // chord line of the wing (through the aeroplane, body-fixed)
  const chord = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-5, WING_Y, 0), new THREE.Vector3(8, WING_Y, 0)]),
    new THREE.LineDashedMaterial({ color: c.brand, dashSize: 0.4, gapSize: 0.25 }));
  chord.computeLineDistances();
  plane.group.add(chord);
  const chordLabel = makeLabel(THREE, "chord line · attitude", c.brand, 0.8);
  chordLabel.position.set(8.5, WING_Y + 0.7, 0);
  plane.group.add(chordLabel);

  // streamers over the wing: attached when flying, detached and fluttering when stalled
  const streamers = [];
  const streamerMat = new THREE.LineBasicMaterial({ color: c.skyFg });
  for (let i = 0; i < 5; i++) {
    const pts = Array.from({ length: 8 }, () => new THREE.Vector3());
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), streamerMat);
    line.userData.z = -4 + i * 2;
    streamers.push(line);
    stage.scene.add(line);
  }

  const params = {};
  const state = { theta: 3, gamma: 0 };
  const aoaLabel = makeLabel(THREE, "", c.fg, 0.9);
  aoaLabel.position.set(-7, -1.6, 0);
  stage.scene.add(aoaLabel);
  function aoaText(a) {
    const canvas = aoaLabel.material.map.image;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = "700 56px 'Inter Variable', system-ui, sans-serif";
    ctx.fillStyle = a >= 16 ? c.bad : a >= 13 ? c.warn : c.fg;
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(`angle of attack ${a.toFixed(0)}°${a >= 16 ? "  STALLED" : ""}`, canvas.width / 2, canvas.height / 2);
    aoaLabel.material.map.needsUpdate = true;
  }
  wireControls(el, params, (p, outs) => {
    state.theta = p.attitude; state.gamma = p.flightPath;
    const aoa = p.attitude - p.flightPath;
    outs.attitude && (outs.attitude.textContent = `${p.attitude.toFixed(0)}° ${p.attitude >= 0 ? "nose up" : "nose down"}`);
    outs.flightPath && (outs.flightPath.textContent = `${p.flightPath.toFixed(0)}° ${p.flightPath > 0 ? "climbing" : p.flightPath < 0 ? "descending" : "level"}`);
    if (outs.aoa) {
      outs.aoa.textContent = `${aoa.toFixed(0)}°`;
      const box = outs.aoa.closest(".widget-readout");
      if (box) { box.classList.toggle("bad", aoa >= 16); box.classList.toggle("warn", aoa >= 13 && aoa < 16); }
    }
    el.querySelectorAll("[data-flag='stalled']").forEach((f) => { f.style.display = aoa >= 16 ? "" : "none"; });
    el.querySelectorAll("[data-flag='near']").forEach((f) => { f.style.display = aoa >= 13 && aoa < 16 ? "" : "none"; });
    aoaText(aoa);
  });
  const rad = (d) => d * Math.PI / 180;
  stage.onTick((t, reduced) => {
    rig.rotation.z = rad(state.theta);
    pathGroup.rotation.z = rad(state.gamma);
    if (!reduced) plane.prop.rotation.x = t * 14;
    const aoa = state.theta - state.gamma;
    const stalled = aoa >= 16;
    const dir = new THREE.Vector3(Math.cos(rad(state.gamma)), Math.sin(rad(state.gamma)), 0); // along the flight path
    const up = new THREE.Vector3(-Math.sin(rad(state.theta)), Math.cos(rad(state.theta)), 0);  // body up
    const fwd = new THREE.Vector3(Math.cos(rad(state.theta)), Math.sin(rad(state.theta)), 0);  // body forward
    for (const s of streamers) {
      const pos = s.geometry.attributes.position;
      const z = s.userData.z;
      const start = new THREE.Vector3().addScaledVector(fwd, WING_LE).addScaledVector(up, WING_Y + 0.1).setZ(z);
      for (let i = 0; i < 8; i++) {
        const f = i / 7;
        const p = start.clone().addScaledVector(dir, -f * 2.6);
        if (stalled) {
          const flutter = reduced ? 0.6 : 0.6 + 0.35 * Math.sin(t * 9 + i * 1.3 + z);
          p.addScaledVector(up, f * f * 1.6 * flutter).addScaledVector(dir, -f * 0.6);
        } else {
          p.addScaledVector(up, -f * 0.05 + 0.02 * Math.sin(t * 6 + i + z) * (reduced ? 0 : 1));
        }
        pos.setXYZ(i, p.x, p.y, p.z);
      }
      pos.needsUpdate = true;
      s.material.color.set(stalled ? c.bad : c.skyFg);
    }
  });
};

/* ------------------------------------------------------------------ explorer: the balanced turn (RBKA 3.5) */
EXPLORERS.turn = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [-15, 4, 0.01] });
  const c = stage.colours;
  const plane = makePlane(THREE, c);
  const rig = new THREE.Group();
  rig.add(plane.group);
  stage.scene.add(rig);
  const ground = new THREE.GridHelper(60, 30, c.line, c.line);
  ground.position.y = -6;
  stage.scene.add(ground);
  const horizonLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, -25), new THREE.Vector3(0, 0, 25)]),
    new THREE.LineDashedMaterial({ color: c.fgFaint, dashSize: 0.5, gapSize: 0.3 }));
  horizonLine.computeLineDistances();
  stage.scene.add(horizonLine);

  // vectors at the CG, drawn in the plane behind the aeroplane (x = -0.5 so they are not hidden by the fuselage)
  const vec = (colour) => new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), new THREE.Vector3(-0.5, 0, 0), 1, colour, 0.6, 0.3);
  const lift = vec(c.brand), weight = vec(c.info), vert = vec(c.ok), horiz = vec(c.warn);
  weight.setDirection(new THREE.Vector3(0, -1, 0));
  stage.scene.add(lift, weight, vert, horiz);
  const liftLabel = makeLabel(THREE, "Lift", c.brand, 0.9), weightLabel = makeLabel(THREE, "Weight", c.info, 0.9);
  const vertLabel = makeLabel(THREE, "vertical = weight", c.ok, 0.75), horizLabel = makeLabel(THREE, "turning force", c.warn, 0.75);
  stage.scene.add(liftLabel, weightLabel, vertLabel, horizLabel);
  const dash = (colour) => { const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]), new THREE.LineDashedMaterial({ color: colour, dashSize: 0.3, gapSize: 0.2 })); stage.scene.add(l); return l; };
  const d1 = dash(c.lineStrong), d2 = dash(c.lineStrong);
  const W = 4; // weight arrow length

  const params = {};
  const state = { bank: 30, ball: 0 };
  wireControls(el, params, (p, outs) => {
    state.bank = p.bank; state.ball = p.ball || 0;
    const n = 1 / Math.cos(p.bank * Math.PI / 180);
    const vs = p.vs || 52;
    const tas = (p.tas || 100) * 0.5144;
    const omega = 9.81 * Math.tan(p.bank * Math.PI / 180) / tas;           // rad/s
    const radius = p.bank > 0 ? tas * tas / (9.81 * Math.tan(p.bank * Math.PI / 180)) : Infinity;
    outs.bank && (outs.bank.textContent = `${p.bank.toFixed(0)}°`);
    outs.vs && (outs.vs.textContent = `${vs} kt`);
    outs.tas && (outs.tas.textContent = `${p.tas || 100} kt`);
    if (outs.n) {
      outs.n.textContent = `${n.toFixed(2)} g`;
      const box = outs.n.closest(".widget-readout");
      box && box.classList.toggle("bad", n > 3.8);
      box && box.classList.toggle("warn", n > 3.0 && n <= 3.8);
    }
    el.querySelectorAll("[data-flag='over']").forEach((f) => { f.style.display = n > 3.8 ? "" : "none"; });
    outs.vsTurn && (outs.vsTurn.textContent = `${Math.round(vs * Math.sqrt(n))} kt  (+${Math.round((Math.sqrt(n) - 1) * 100)}%)`);
    outs.rate && (outs.rate.textContent = p.bank > 0 ? `${(omega * 180 / Math.PI).toFixed(1)}°/s · ${Math.round(360 / (omega * 180 / Math.PI))} s per circle` : "0°/s (straight)");
    outs.radius && (outs.radius.textContent = isFinite(radius) ? `${Math.round(radius)} m` : "–");
    outs.ballText && (outs.ballText.textContent = Math.abs(state.ball) < 0.1 ? "balanced: ball centred" : state.ball > 0 ? "skid: ball out to the high wing, add aileron or less rudder" : "slip: ball in to the low wing, more rudder ('step on the ball')");
    const ball = el.querySelector("[data-out='ball']");
    if (ball) ball.setAttribute("cx", String(160 + state.ball * 60));
  });
  const cur = { bank: 30 };
  stage.onTick((t, reduced) => {
    cur.bank = lerp(cur.bank, state.bank, reduced ? 1 : 0.1);
    const phi = cur.bank * Math.PI / 180;
    rig.rotation.x = phi;                                  // right wing down = right turn
    if (!reduced) {
      plane.prop.rotation.x = t * 14;
      ground.rotation.y = -t * 0.08 * Math.tan(phi);       // the world turns faster under a steeper bank
    }
    const n = 1 / Math.cos(phi);
    const upBody = new THREE.Vector3(0, Math.cos(phi), Math.sin(phi)); // tilts towards the right (+z) wing-down side
    const origin = new THREE.Vector3(-0.5, 0, 0);
    lift.position.copy(origin); lift.setDirection(upBody); lift.setLength(W * n, 0.6, 0.3);
    weight.position.copy(origin); weight.setLength(W, 0.6, 0.3);
    vert.position.copy(origin); vert.setDirection(new THREE.Vector3(0, 1, 0)); vert.setLength(W, 0.5, 0.25); vert.visible = cur.bank > 1;
    horiz.position.copy(origin); horiz.setDirection(new THREE.Vector3(0, 0, 1)); horiz.setLength(Math.max(0.01, W * Math.tan(phi)), 0.5, 0.25); horiz.visible = cur.bank > 3;
    const tip = origin.clone().addScaledVector(upBody, W * n);
    liftLabel.position.copy(tip).add(new THREE.Vector3(0, 0.8, 0));
    weightLabel.position.set(-0.5, -W - 0.8, 0);
    vertLabel.position.set(-0.5, W + 0.6, -2.2); vertLabel.visible = cur.bank > 8;
    horizLabel.position.set(-0.5, -0.7, W * Math.tan(phi) / 2); horizLabel.visible = cur.bank > 12;
    d1.geometry.setFromPoints([tip, new THREE.Vector3(-0.5, W, 0)]); d1.computeLineDistances();
    d2.geometry.setFromPoints([tip, new THREE.Vector3(-0.5, 0, W * Math.tan(phi))]); d2.computeLineDistances();
  });
};

/* ------------------------------------------------------------------ explorer: the circuit in 3D (RFRC 2.5) */
/* Circuit geometry in a canonical frame: take-off along +x, left-hand circuit on the -z side (the pilot's left),
   circuit height H. Returns {points, legs} where legs are fractions of the path length where each leg ends. */
export function circuitPath(THREE, leftHand = true, dir = 1, H = 10) {
  const zf = (leftHand ? 1 : -1) * dir;
  const P = (x, y, z) => new THREE.Vector3(x * dir, y, z * zf);
  const pts = [];
  const arc = (cx, cz, a0, a1, y0, y1, n = 8) => {
    for (let i = 1; i <= n; i++) {
      const a = (a0 + (a1 - a0) * i / n) * Math.PI / 180;
      pts.push(P(cx + 8 * Math.cos(a), y0 + (y1 - y0) * i / n, cz + 8 * Math.sin(a)));
    }
  };
  pts.push(P(-10, 0, 0), P(0, 0, 0), P(12, 0, 0));          // ground roll and lift-off
  pts.push(P(19, H * 0.25, 0), P(26, H * 0.5, 0));          // upwind climb: 500 ft at the first turn
  arc(26, -8, 90, 0, H * 0.5, H * 0.65);                    // left turn onto crosswind
  pts.push(P(34, H * 0.85, -22));                           // crosswind, still climbing
  arc(26, -22, 0, -90, H * 0.85, H);                        // onto downwind at circuit height
  pts.push(P(10, H, -30), P(-10, H, -30), P(-26, H, -30));  // downwind
  arc(-26, -22, -90, -180, H, H * 0.8);                     // onto base, descending
  pts.push(P(-34, H * 0.5, -8));                            // base
  arc(-26, -8, 180, 90, H * 0.5, H * 0.3);                  // onto final
  pts.push(P(-18, H * 0.15, 0), P(-10, 0, 0));              // final to touchdown
  // leg end fractions from the segment lengths (ground roll 22 + climb 14, arcs 12.57, crosswind 14, downwind 52, base 14, final 16)
  const total = 36 + 4 * 12.57 + 14 + 52 + 14 + 16;
  const legs = { upwind: (36 + 6.3) / total, crosswind: (36 + 12.57 + 14 + 6.3) / total, downwind: (36 + 2 * 12.57 + 14 + 52 + 6.3) / total, base: (36 + 3 * 12.57 + 14 + 52 + 14 + 6.3) / total };
  return { points: pts, legs, P };
}

EXPLORERS.circuit = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [-30, 26, 38] });
  stage.controls.maxDistance = 90;
  stage.controls.minDistance = 10;
  const c = stage.colours;
  const ground = new THREE.GridHelper(120, 24, c.line, c.line);
  ground.position.y = -0.02;
  stage.scene.add(ground);
  const runway = new THREE.Mesh(new THREE.BoxGeometry(30, 0.1, 3), new THREE.MeshStandardMaterial({ color: c.fgMuted, roughness: 0.9 }));
  stage.scene.add(runway);
  const centreline = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-12, 0.08, 0), new THREE.Vector3(12, 0.08, 0)]),
    new THREE.LineDashedMaterial({ color: c.surface, dashSize: 1.2, gapSize: 1.2 }));
  centreline.computeLineDistances();
  stage.scene.add(centreline);
  const sock = new THREE.Group();
  sock.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 4, 8), new THREE.MeshStandardMaterial({ color: c.fg })), { position: new THREE.Vector3(0, 2, 0) }));
  const cone = new THREE.Mesh(new THREE.ConeGeometry(0.5, 2.2, 10), new THREE.MeshStandardMaterial({ color: c.warn }));
  sock.add(cone);
  sock.position.set(0, 0, 6);
  stage.scene.add(sock);

  const plane = makePlane(THREE, c);
  plane.group.scale.setScalar(0.45);
  stage.scene.add(plane.group);

  const H = 10;
  const curveLine = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineDashedMaterial({ color: c.brand, dashSize: 1.5, gapSize: 0.8 }));
  stage.scene.add(curveLine);
  const labels = {};
  for (const [name, colour] of [["Upwind", c.brand], ["Crosswind", c.brand], ["Downwind", c.brand], ["Base", c.brand], ["Final", c.brand], ["Dead side", c.fgMuted], ["wind", c.skyFg]]) {
    labels[name] = makeLabel(THREE, name, colour, 1.6);
    stage.scene.add(labels[name]);
  }
  const wind = new THREE.ArrowHelper(new THREE.Vector3(-1, 0, 0), new THREE.Vector3(0, 0, 0), 8, c.skyFg, 2, 1);
  stage.scene.add(wind);

  let curve = null, legs = null;
  const params = {};
  const state = { progress: 0, speed: 1, leftHand: true, dir: 1, playing: true };
  function rebuild() {
    const built = circuitPath(THREE, state.leftHand, state.dir, H);
    legs = built.legs;
    curve = new THREE.CatmullRomCurve3(built.points, false, "centripetal", 0.5);
    curveLine.geometry.dispose();
    curveLine.geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(400));
    curveLine.computeLineDistances();
    const P = built.P;
    labels.Upwind.position.copy(P(20, 4.5, 3));
    labels.Crosswind.position.copy(P(37, H * 0.8 + 1.5, -15));
    labels.Downwind.position.copy(P(0, H + 2, -30));
    labels.Base.position.copy(P(-37, H * 0.6 + 1.5, -15));
    labels.Final.position.copy(P(-20, 3.5, 3));
    labels["Dead side"].position.copy(P(0, 1.5, 18));
    wind.position.copy(P(16, 6, 12));
    wind.setDirection(new THREE.Vector3(-state.dir, 0, 0));
    labels.wind.position.copy(P(16, 8.5, 12));
    cone.rotation.z = state.dir > 0 ? Math.PI / 2 : -Math.PI / 2;   // the sock streams downwind, away from the take-off direction
    cone.position.set(-1.1 * state.dir, 3.9, 0);
  }
  rebuild();
  const legName = (u) => u < legs.upwind ? "upwind" : u < legs.crosswind ? "crosswind" : u < legs.downwind ? "downwind" : u < legs.base ? "base" : "final";
  wireControls(el, params, (p, outs) => {
    const lh = !p.rightHand, d = p.runway06 ? -1 : 1;
    if (lh !== state.leftHand || d !== state.dir) { state.leftHand = lh; state.dir = d; rebuild(); }
    state.speed = p.speed || 1;
    outs.runway && (outs.runway.textContent = d > 0 ? "runway 24: take-off and landing heading 240°" : "runway 06: take-off and landing heading 060°");
    outs.circuit && (outs.circuit.textContent = lh ? "left-hand (standard): all turns to the left" : "right-hand: only where ERSA says so");
  });
  el.querySelectorAll("[data-action='play']").forEach((b) => b.addEventListener("click", () => { state.playing = !state.playing; b.textContent = state.playing ? "Pause" : "Play"; }));
  let last = null;
  stage.onTick((t, reduced) => {
    if (last === null) last = t;
    const dt = Math.min(0.1, t - last); last = t;
    if (state.playing) state.progress = (state.progress + dt * state.speed / 45) % 1;
    const u = state.progress;
    const pos = curve.getPointAt(u), tan = curve.getTangentAt(u);
    pos.y = Math.max(0, pos.y);                        // the spline may dip a little below the runway before lift-off
    plane.group.position.copy(pos);
    const yaw = Math.atan2(-tan.z, tan.x), pitch = pos.y > 0.05 ? Math.asin(Math.max(-1, Math.min(1, tan.y))) : 0;
    const ahead = curve.getTangentAt(Math.min(1, u + 0.015));
    const turn = Math.atan2(Math.sin(Math.atan2(-ahead.z, ahead.x) - yaw), Math.cos(Math.atan2(-ahead.z, ahead.x) - yaw));
    plane.group.rotation.set(0, 0, 0);
    plane.group.rotateY(yaw); plane.group.rotateZ(pitch); plane.group.rotateX(-turn * 5);   // bank into the turn (visual only)
    if (!reduced) plane.prop.rotation.x = t * 14;
    el.querySelectorAll("[data-out]").forEach((o) => {
      if (o.dataset.out === "leg") o.textContent = legName(u);
      if (o.dataset.out === "height") o.textContent = `${Math.round(pos.y / H * 1000 / 50) * 50} ft above aerodrome level`;
    });
  });
};

/* ------------------------------------------------------------------ shared bits for the scene explorers below */
function dashedLine(THREE, pts, colour, dash = 0.6, gap = 0.3) {
  const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineDashedMaterial({ color: colour, dashSize: dash, gapSize: gap }));
  l.computeLineDistances();
  return l;
}
function solidLine(THREE, pts, colour) {
  return new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: colour }));
}
function glassMat(THREE, colour, opacity) {
  return new THREE.MeshStandardMaterial({ color: colour, transparent: true, opacity, roughness: 0.85, depthWrite: false, side: THREE.DoubleSide });
}
function v3(THREE, ...pts) { return pts.map(([x, y, z]) => new THREE.Vector3(x, y, z)); }
function setText(outs, key, text, cls) {
  const o = outs[key];
  if (!o) return;
  o.textContent = text;
  const box = o.closest(".widget-readout");
  if (box) { box.classList.remove("ok", "warn", "bad"); if (cls) box.classList.add(cls); }
}
function playButton(el, state) {
  el.querySelectorAll("[data-action='play']").forEach((b) => b.addEventListener("click", () => { state.playing = !state.playing; b.textContent = state.playing ? "Pause" : "Play"; }));
}
/* a runway lying along x, centred on the origin, with its dashed centreline */
function makeRunway(THREE, c, length, width) {
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.BoxGeometry(length, width * 0.04, width), new THREE.MeshStandardMaterial({ color: c.tarmac, roughness: 0.95 })));
  g.add(dashedLine(THREE, v3(THREE, [-length * 0.4, width * 0.03, 0], [length * 0.4, width * 0.03, 0]), c.paint, length * 0.03, length * 0.03));
  return g;
}
/* the twin-jet heavy of the wake pictures (tools/diagrams/svg.py airliner_rear, 100 units = the span): nose +x, gear up */
function makeHeavy(THREE, c, span = 60) {
  const s = span / 100;
  const body = new THREE.MeshStandardMaterial({ color: c.dark ? c.fgMuted : c.surface, roughness: 0.5 });
  const edge = new THREE.MeshStandardMaterial({ color: c.fg, roughness: 0.6 });
  const g = new THREE.Group();
  const fuse = new THREE.Mesh(new THREE.CapsuleGeometry(10 * s, 110 * s, 4, 16), body);
  fuse.rotation.z = Math.PI / 2;
  g.add(fuse);
  const wingShape = new THREE.Shape([[25, 10], [-10, 50], [-22, 50], [-20, 10], [-20, -10], [-22, -50], [-10, -50], [25, -10]].map(([x, z]) => new THREE.Vector2(x * s, z * s)));
  const wing = new THREE.Mesh(new THREE.ExtrudeGeometry(wingShape, { depth: 2.5 * s, bevelEnabled: false }), body);
  wing.rotation.x = Math.PI / 2;
  wing.position.y = -4 * s;
  g.add(wing);
  for (const z of [-29, 29]) {
    const eng = new THREE.Mesh(new THREE.CylinderGeometry(4.5 * s, 4.5 * s, 14 * s, 12), edge);
    eng.rotation.z = Math.PI / 2;
    eng.position.set(5 * s, -8.5 * s, z * s);
    g.add(eng);
  }
  const finShape = new THREE.Shape([[-45, 10], [-62, 44], [-66, 44], [-66, 10]].map(([x, y]) => new THREE.Vector2(x * s, y * s)));
  g.add(new THREE.Mesh(new THREE.ExtrudeGeometry(finShape, { depth: 2 * s, bevelEnabled: false }), body));
  const tailShape = new THREE.Shape([[-50, 2], [-62, 18], [-66, 18], [-66, -18], [-62, -18], [-50, -2]].map(([x, z]) => new THREE.Vector2(x * s, z * s)));
  const tail = new THREE.Mesh(new THREE.ExtrudeGeometry(tailShape, { depth: 1.5 * s, bevelEnabled: false }), body);
  tail.rotation.x = Math.PI / 2;
  tail.position.y = 8 * s;
  g.add(tail);
  return g;
}
/* aerodrome scenery shared by the circuit-type explorers: grid, runway, windsock, a wind arrow */
function makeAerodrome(THREE, c, scene) {
  const ground = new THREE.GridHelper(120, 24, c.line, c.line);
  ground.position.y = -0.02;
  scene.add(ground);
  scene.add(makeRunway(THREE, c, 30, 3));
  const sock = new THREE.Group();
  sock.add(Object.assign(new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 4, 8), new THREE.MeshStandardMaterial({ color: c.fg })), { position: new THREE.Vector3(0, 2, 0) }));
  const cone = new THREE.Mesh(new THREE.ConeGeometry(0.5, 2.2, 10), new THREE.MeshStandardMaterial({ color: c.warn }));
  sock.add(cone);
  sock.position.set(0, 0, 6);
  scene.add(sock);
  const wind = new THREE.ArrowHelper(new THREE.Vector3(-1, 0, 0), new THREE.Vector3(0, 0, 0), 8, c.skyFg, 2, 1);
  scene.add(wind);
  return { ground, cone, wind };
}
const FT_PER_M = 3.2808;

/* ------------------------------------------------------------------ explorer: Perth airspace in 3D (RFRC 2.6)
   Schematic model: 1 unit = 1 km across and 1 unit = 1,000 ft up (heights exaggerated about 3x so the steps read).
   Perth's Class C control zone from the surface, then steps whose lower limits rise with distance (the lesson's and the
   cross-section diagram's "C LL 1500 / 2500 / 4500" labels), Class E beyond with LL 8500, Jandakot's Class D zone from
   the surface tucked under the first step, and a restricted area to the north-east (RAAF Pearce). Ring radii, the D
   zone's upper limit and the R area's limits are schematic: the real figures are on the VTC and in ERSA. +x east, +z south. */
export function airspaceModel(towerOpen = true) {
  const rings = [
    { cls: "C", label: "C · SFC", name: "Perth Class C control zone from the surface", rIn: 0, rOut: 7, lower: 0, upper: 12.5 },
    { cls: "C", label: "C LL 1500", name: "Class C step, lower limit 1,500 ft", rIn: 7, rOut: 14, lower: 1.5, upper: 12.5 },
    { cls: "C", label: "C LL 2500", name: "Class C step, lower limit 2,500 ft", rIn: 14, rOut: 24, lower: 2.5, upper: 12.5 },
    { cls: "C", label: "C LL 4500", name: "Class C step, lower limit 4,500 ft", rIn: 24, rOut: 38, lower: 4.5, upper: 12.5 },
    { cls: "E", label: "E LL 8500", name: "Class E, lower limit 8,500 ft", rIn: 38, rOut: 62, lower: 8.5, upper: 12.5 },
  ];
  const jandakot = { x: -8, z: 11, r: 5, lower: 0, upper: 1.5, open: towerOpen };
  const restricted = { x: -6, z: -32, half: 7, lower: 0, upper: 5 };
  const places = [["Perth city", -10, -1], ["Perth Airport", 0, 0], ["Jandakot", -8, 11], ["Rottnest", -40, 10], ["RAAF Pearce", -6, -32], ["Fremantle", -20, 10]];
  const track = [[-8, 11], [-16, 22], [-28, 24], [-38, 18], [-42, 8], [-36, -6], [-26, -22], [-10, -32]];   // Jandakot, south-west to the coast, Rottnest, north, then east to the Pearce restricted area
  return { rings, jandakot, restricted, places, track };
}
/* which airspace a point (x, z, altitude in ft) is in; returns {code, text, cls, lower} with cls ok/warn/bad for the readout */
export function airspaceAt(model, x, z, altFt) {
  const r = Math.hypot(x, z), alt = altFt / 1000;
  const j = model.jandakot, R = model.restricted;
  const ring = model.rings.find((g) => r >= g.rIn && r < g.rOut) || model.rings[model.rings.length - 1];
  const stepText = (g) => `${g.cls} LL ${Math.round(g.lower * 1000).toLocaleString("en-AU")} ft`;
  if (Math.abs(x - R.x) <= R.half && Math.abs(z - R.z) <= R.half && alt < R.upper) {
    return { code: "R", lower: R.upper, cls: "bad", text: "Restricted area: if it is active (ERSA PRD, NOTAM) you need the controlling authority's clearance; without one, stay out" };
  }
  if (Math.hypot(x - j.x, z - j.z) <= j.r && alt < j.upper) {
    return j.open
      ? { code: "D", lower: j.upper, cls: "warn", text: "Jandakot Class D (tower open): clearance required; the tower controls the circuit" }
      : { code: "G", lower: j.upper, cls: "ok", text: `Jandakot outside tower hours: Class G, CTAF procedures, no clearance (the ${stepText(ring)} step still sits above)` };
  }
  if (ring.lower === 0) return { code: "C", lower: 0, cls: "bad", text: "Inside Perth's Class C control zone, which starts at the surface: a clearance is required" };
  if (alt >= ring.lower) {
    return ring.cls === "C"
      ? { code: "C", lower: ring.lower, cls: "bad", text: `Inside Class C (${stepText(ring)}): clearance required; without one this is an airspace infringement` }
      : { code: "E", lower: ring.lower, cls: "warn", text: `Inside Class E (${stepText(ring)}): controlled for IFR; VFR needs no clearance but a transponder, a radio and the VMC minima` };
  }
  const margin = Math.round((ring.lower - alt) * 1000);
  return { code: "G", lower: ring.lower, cls: margin < 500 ? "warn" : "ok", margin, text: `Class G under the ${stepText(ring)} step: ${margin.toLocaleString("en-AU")} ft below it, no clearance needed` };
}

EXPLORERS.airspace = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [-60, 42, 70] });
  stage.controls.maxDistance = 170;
  stage.controls.minDistance = 12;
  if (!el._casaView) stage.controls.target.set(-14, 2, 2);
  stage.camera.far = 600;
  stage.camera.updateProjectionMatrix();
  const c = stage.colours;
  const scene = stage.scene;

  // ground: land east of a straight schematic coastline, sea to the west, a faint grid
  const land = new THREE.Mesh(new THREE.PlaneGeometry(100, 130), new THREE.MeshStandardMaterial({ color: c.surface2, roughness: 1 }));
  land.rotation.x = -Math.PI / 2; land.position.set(16, -0.05, 0);
  const sea = new THREE.Mesh(new THREE.PlaneGeometry(40, 130), new THREE.MeshStandardMaterial({ color: c.skySoft, roughness: 1 }));
  sea.rotation.x = -Math.PI / 2; sea.position.set(-54, -0.05, 0);
  scene.add(land, sea);
  const grid = new THREE.GridHelper(140, 14, c.line, c.line);
  grid.position.set(-4, -0.02, 0);
  scene.add(grid);
  const rott = new THREE.Mesh(new THREE.CylinderGeometry(2.2, 2.2, 0.1, 16), new THREE.MeshStandardMaterial({ color: c.surface2, roughness: 1 }));
  rott.position.set(-40, -0.02, 10);
  scene.add(rott);

  const blocks = new THREE.Group();
  scene.add(blocks);
  const colourFor = { C: c.brand, D: c.info, E: c.skyFg, R: c.bad };
  const ringPrism = (rIn, rOut, y0, y1, colour, opacity) => {
    const shape = new THREE.Shape();
    shape.absarc(0, 0, rOut, 0, Math.PI * 2, false);
    if (rIn > 0) { const hole = new THREE.Path(); hole.absarc(0, 0, rIn, 0, Math.PI * 2, true); shape.holes.push(hole); }
    const geo = new THREE.ExtrudeGeometry(shape, { depth: y1 - y0, bevelEnabled: false, curveSegments: 48 });
    geo.rotateX(-Math.PI / 2);
    geo.translate(0, y0, 0);
    const m = new THREE.Mesh(geo, glassMat(THREE, colour, opacity));
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 20), new THREE.LineBasicMaterial({ color: colour, transparent: true, opacity: 0.6 }));
    m.add(edges);
    return m;
  };
  const model0 = airspaceModel(true);
  for (const g of model0.rings) {
    blocks.add(ringPrism(g.rIn, g.rOut, g.lower, g.upper, colourFor[g.cls], g.cls === "C" ? 0.16 : 0.1));
    const lbl = makeLabel(THREE, g.label, colourFor[g.cls], 2.6);
    const ang = -0.95;   // labels along the south-west edge of each ring, where the camera starts
    const rr = g.rIn === 0 ? 0 : (g.rIn + g.rOut) / 2;
    lbl.position.set(rr * Math.cos(ang) * -1, g.lower + 0.9, rr * Math.sin(ang) * -1);
    if (g.rIn === 0) lbl.position.set(0, g.upper + 1, 0);
    blocks.add(lbl);
  }
  // Jandakot Class D: a cylinder from the surface up to its published upper limit (schematic height), under the first step
  const j = model0.jandakot;
  const dGeo = new THREE.CylinderGeometry(j.r, j.r, j.upper, 32);
  const dZone = new THREE.Mesh(dGeo, glassMat(THREE, c.info, 0.3));
  dZone.position.set(j.x, j.upper / 2, j.z);
  const dEdges = new THREE.LineSegments(new THREE.EdgesGeometry(dGeo, 20), new THREE.LineBasicMaterial({ color: c.info }));
  dZone.add(dEdges);
  scene.add(dZone);
  const dLabel = makeLabel(THREE, "Jandakot Class D · SFC to its published upper limit", c.info, 2.4);
  dLabel.position.set(j.x, j.upper + 1.2, j.z + 3);
  scene.add(dLabel);
  // the restricted area: a box, filled when active
  const R = model0.restricted;
  const rGeo = new THREE.BoxGeometry(R.half * 2, R.upper, R.half * 2);
  const rZone = new THREE.Mesh(rGeo, glassMat(THREE, c.bad, 0.25));
  rZone.position.set(R.x, R.upper / 2, R.z);
  rZone.add(new THREE.LineSegments(new THREE.EdgesGeometry(rGeo), new THREE.LineBasicMaterial({ color: c.bad })));
  scene.add(rZone);
  const rLabel = makeLabel(THREE, "R area · active per ERSA / NOTAM", c.bad, 2.4);
  rLabel.position.set(R.x, R.upper + 1.2, R.z + 3);
  scene.add(rLabel);
  for (const [name, x, z] of model0.places) {
    const s = makeLabel(THREE, name, c.fgMuted, 2);
    s.position.set(x, 0.6, z + 1.5);
    scene.add(s);
    const dot = new THREE.Mesh(new THREE.SphereGeometry(0.35, 10, 8), new THREE.MeshStandardMaterial({ color: c.fg }));
    dot.position.set(x, 0.1, z);
    scene.add(dot);
  }
  const heights = makeLabel(THREE, "1 square = 10 km · heights exaggerated (1,000 ft per unit)", c.fgFaint, 2.2);
  heights.position.set(-20, 0.5, 48);
  scene.add(heights);

  // the track and the aeroplane
  const trackCurve = new THREE.CatmullRomCurve3(model0.track.map(([x, z]) => new THREE.Vector3(x, 0, z)), false, "catmullrom", 0.5);
  const trackLine = dashedLine(THREE, trackCurve.getPoints(120), c.ok, 1, 0.6);
  scene.add(trackLine);
  const shadow = solidLine(THREE, v3(THREE, [0, 0, 0], [0, 1, 0]), c.fgFaint);
  scene.add(shadow);
  const plane = makePlane(THREE, c);
  plane.group.scale.setScalar(0.5);
  scene.add(plane.group);

  const params = {};
  const state = { progress: 0.15, alt: 1500, playing: true, open: true, active: true, model: model0 };
  playButton(el, state);
  wireControls(el, params, (p, outs) => {
    state.alt = p.altitude;
    state.open = !!p.towerOpen;
    state.active = !!p.rActive;
    if (p.position !== undefined) state.progress = p.position;
    state.model = airspaceModel(state.open);
    dZone.material.opacity = state.open ? 0.3 : 0.05;
    dEdges.material.color.set(state.open ? c.info : c.fgFaint);
    rZone.material.opacity = state.active ? 0.25 : 0.04;
    trackLine.position.y = state.alt / 1000;
    setText(outs, "altitude", `${p.altitude.toLocaleString("en-AU")} ft`);
    setText(outs, "tower", state.open ? "tower open: Class D, clearance required" : "tower closed: Class G, CTAF aerodrome");
    setText(outs, "rArea", state.active ? "active: a clearance is required to enter" : "inactive today: no clearance needed");
  });
  let last = null;
  stage.onTick((t, reduced) => {
    if (last === null) last = t;
    const dt = Math.min(0.1, t - last); last = t;
    if (state.playing && !reduced) state.progress = (state.progress + dt / 40) % 1;
    const u = state.progress;
    const pos = trackCurve.getPointAt(u), tan = trackCurve.getTangentAt(u);
    pos.y = state.alt / 1000;
    plane.group.position.copy(pos);
    plane.group.rotation.set(0, Math.atan2(-tan.z, tan.x), 0);
    shadow.geometry.setFromPoints([new THREE.Vector3(pos.x, 0, pos.z), pos]);
    if (!reduced) plane.prop.rotation.x = t * 14;
    const here = airspaceAt(state.model, pos.x, pos.z, state.alt);
    const active = here.code === "R" ? state.active : true;
    const outs = {};
    el.querySelectorAll("[data-out]").forEach((o) => { outs[o.dataset.out] = o; });
    if (here.code === "R" && !active) setText(outs, "here", `Restricted area, inactive today: you may fly through (chart for where, ERSA for when, NOTAM for today)`, "ok");
    else setText(outs, "here", here.text, here.cls);
    setText(outs, "class", here.code === "R" ? (active ? "R (active)" : "R (inactive)") : `Class ${here.code}`, here.code === "R" && !active ? "ok" : here.cls);
    const positionOut = el.querySelector("[data-param='position']");
    if (positionOut && state.playing) positionOut.value = String(u.toFixed(3));
  });
};

/* ------------------------------------------------------------------ explorer: the overhead join (RFRC 2.5)
   Same canonical frame as circuitPath (take-off along +x, left-hand circuit on -z, dead side on +z, circuit height H).
   Arrive over the aerodrome above circuit height (the lesson gives no figure: the model uses 1.5 H, that is 500 ft above
   a 1,000 ft circuit), cross midfield to the dead side, make a descending turn there to circuit height, cross the upwind
   end heading in the crosswind direction, join crosswind, then downwind, base and final as circuitPath does. */
export function overheadJoinPath(THREE, leftHand = true, dir = 1, H = 10) {
  const zf = (leftHand ? 1 : -1) * dir;
  const P = (x, y, z) => new THREE.Vector3(x * dir, y, z * zf);
  const pts = [], marks = {};
  const arc = (cx, cz, a0, a1, y0, y1, r = 8, n = 8) => {
    for (let i = 1; i <= n; i++) {
      const a = (a0 + (a1 - a0) * i / n) * Math.PI / 180;
      pts.push(P(cx + r * Math.cos(a), y0 + (y1 - y0) * i / n, cz + r * Math.sin(a)));
    }
  };
  const OH = H * 1.5;
  pts.push(P(0, OH, -52), P(0, OH, -34), P(0, OH, -16), P(0, OH, 0));   // inbound over the circuit side, overhead midfield
  marks.overhead = pts.length - 1;
  pts.push(P(0, OH, 8));
  arc(18, 14, 180, 0, OH, H, 18, 12);                                   // the descending turn on the dead side, out to the upwind end
  marks.deadside = pts.length - 1;
  pts.push(P(36, H, 2), P(36, H, -22));                                 // across the upwind end at circuit height: crosswind
  arc(28, -22, 0, -90, H, H);
  marks.crosswind = pts.length - 1;
  pts.push(P(10, H, -30), P(-10, H, -30), P(-26, H, -30));              // downwind, base and final as circuitPath flies them
  marks.downwind = pts.length - 1;
  arc(-26, -22, -90, -180, H, H * 0.8);
  pts.push(P(-34, H * 0.5, -8));                                        // base
  marks.base = pts.length - 1;
  arc(-26, -8, 180, 90, H * 0.5, H * 0.3, 8, 8);
  pts.push(P(-18, H * 0.15, 0), P(-10, 0, 0));
  // leg end fractions from the polyline length
  const cum = [0];
  for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + pts[i].distanceTo(pts[i - 1]));
  const total = cum[cum.length - 1];
  const legs = {};
  for (const [k, i] of Object.entries(marks)) legs[k] = cum[i] / total;
  return { points: pts, legs, P, overheadHeight: OH };
}

EXPLORERS.overhead = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [-34, 30, 44] });
  stage.controls.maxDistance = 100;
  stage.controls.minDistance = 10;
  const c = stage.colours;
  const { cone, wind } = makeAerodrome(THREE, c, stage.scene);
  const plane = makePlane(THREE, c);
  plane.group.scale.setScalar(0.45);
  stage.scene.add(plane.group);
  const H = 10;
  const joinLine = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineDashedMaterial({ color: c.brand, dashSize: 1.5, gapSize: 0.8 }));
  const circuitLine = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineDashedMaterial({ color: c.fgMuted, dashSize: 1.2, gapSize: 1 }));
  stage.scene.add(joinLine, circuitLine);
  const sheet = new THREE.Mesh(new THREE.PlaneGeometry(90, 70), glassMat(THREE, c.skyFg, 0.07));   // circuit height, so the descent reads
  sheet.rotation.x = -Math.PI / 2; sheet.position.y = H;
  stage.scene.add(sheet);
  const labels = {};
  for (const [name, colour] of [["1 · overhead, above circuit height", c.brand], ["2 · descend on the dead side", c.brand], ["3 · cross the upwind end, join crosswind", c.brand], ["4 · downwind at circuit height", c.brand], ["Dead side", c.fgMuted], ["Circuit side", c.fgMuted], ["wind", c.skyFg], ["circuit height 1,000 ft", c.skyFg]]) {
    labels[name] = makeLabel(THREE, name, colour, 1.8);
    stage.scene.add(labels[name]);
  }
  let curve = null, legs = null;
  const params = {};
  const state = { progress: 0, speed: 1, leftHand: true, dir: 1, playing: true };
  function rebuild() {
    const built = overheadJoinPath(THREE, state.leftHand, state.dir, H);
    legs = built.legs;
    curve = new THREE.CatmullRomCurve3(built.points, false, "centripetal", 0.5);
    joinLine.geometry.dispose();
    joinLine.geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(400));
    joinLine.computeLineDistances();
    const cp = new THREE.CatmullRomCurve3(circuitPath(THREE, state.leftHand, state.dir, H).points, false, "centripetal", 0.5);
    circuitLine.geometry.dispose();
    circuitLine.geometry = new THREE.BufferGeometry().setFromPoints(cp.getPoints(300));
    circuitLine.computeLineDistances();
    const P = built.P;
    labels["1 · overhead, above circuit height"].position.copy(P(0, built.overheadHeight + 2.5, -4));
    labels["2 · descend on the dead side"].position.copy(P(18, H * 1.3 + 2, 38));
    labels["3 · cross the upwind end, join crosswind"].position.copy(P(40, H + 2.5, -8));
    labels["4 · downwind at circuit height"].position.copy(P(-8, H + 2.5, -32));
    labels["Dead side"].position.copy(P(0, 1.5, 22));
    labels["Circuit side"].position.copy(P(0, 1.5, -18));
    labels["circuit height 1,000 ft"].position.copy(P(-40, H + 1, 20));
    wind.position.copy(P(16, 6, 12));
    wind.setDirection(new THREE.Vector3(-state.dir, 0, 0));
    labels.wind.position.copy(P(16, 8.5, 12));
    cone.rotation.z = state.dir > 0 ? Math.PI / 2 : -Math.PI / 2;
    cone.position.set(-1.1 * state.dir, 3.9, 0);
  }
  rebuild();
  const phase = (u) => u < legs.overhead ? "inbound overhead, above circuit height" : u < legs.deadside ? "descending turn on the dead side" : u < legs.crosswind ? "crossing the upwind end: crosswind at circuit height" : u < legs.downwind ? "downwind, circuit height" : u < legs.base ? "base, descending" : "final";
  wireControls(el, params, (p, outs) => {
    const lh = !p.rightHand, d = p.runway06 ? -1 : 1;
    if (lh !== state.leftHand || d !== state.dir) { state.leftHand = lh; state.dir = d; rebuild(); }
    state.speed = p.speed || 1;
    setText(outs, "runway", d > 0 ? "runway 24: landing heading 240°" : "runway 06: landing heading 060°");
    setText(outs, "deadside", lh ? "left-hand circuit: dead side to the right of the runway, looking along the landing direction" : "right-hand circuit (ERSA): dead side to the left, looking along the landing direction");
  });
  playButton(el, state);
  let last = null;
  stage.onTick((t, reduced) => {
    if (last === null) last = t;
    const dt = Math.min(0.1, t - last); last = t;
    if (state.playing && !reduced) state.progress = (state.progress + dt * state.speed / 50) % 1;
    const u = state.progress;
    const pos = curve.getPointAt(u), tan = curve.getTangentAt(u);
    pos.y = Math.max(0, pos.y);
    plane.group.position.copy(pos);
    const yaw = Math.atan2(-tan.z, tan.x), pitch = pos.y > 0.05 ? Math.asin(Math.max(-1, Math.min(1, tan.y))) : 0;
    const ahead = curve.getTangentAt(Math.min(1, u + 0.015));
    const turn = Math.atan2(Math.sin(Math.atan2(-ahead.z, ahead.x) - yaw), Math.cos(Math.atan2(-ahead.z, ahead.x) - yaw));
    plane.group.rotation.set(0, 0, 0);
    plane.group.rotateY(yaw); plane.group.rotateZ(pitch); plane.group.rotateX(-turn * 5);
    if (!reduced) plane.prop.rotation.x = t * 14;
    el.querySelectorAll("[data-out]").forEach((o) => {
      if (o.dataset.out === "phase") o.textContent = phase(u);
      if (o.dataset.out === "height") o.textContent = `${Math.round(pos.y / H * 1000 / 50) * 50} ft above aerodrome level`;
    });
  });
};

/* ------------------------------------------------------------------ explorer: spin or spiral dive (RBKA 3.6)
   Position and attitude of the aeroplane t seconds into each manoeuvre, in metres (the aeroplane is real size).
   Spin: autorotation about a near-vertical axis of small radius, one turn every 3 s, nose well down, the airspeed low
   and steady at about the book stall speed. Spiral dive: a steep descending turn of large radius, wings flying, the
   airspeed and the load factor building with time. Heading is the direction of travel around the axis (radians, about +y);
   bank and pitch in degrees; ias in knots; g the load factor; rod the rate of descent in ft/min. */
export function spinSpiralState(mode, t, vs = 50) {
  const spin = mode === "spin";
  if (spin) {
    const period = 3, radius = 4, descent = 25;             // m, m/s (about 5,000 ft/min: "high")
    const a = (t / period) * Math.PI * 2;
    return { x: radius * Math.cos(a), z: -radius * Math.sin(a), y: -descent * t, heading: a + Math.PI / 2, bank: 35, pitch: -55,
      ias: vs + 3 * Math.sin(t * 2), g: 1.2, rod: Math.round(descent * FT_PER_M * 60 / 100) * 100, stalled: true };
  }
  const ias = Math.min(190, 90 + 7 * t);                     // high and increasing fast
  const bankDeg = Math.min(80, 50 + 2.2 * t);
  const g = Math.min(5, 1 / Math.cos(bankDeg * Math.PI / 180) * (0.85 + 0.02 * t));
  const tas = ias * 0.5144;
  const omega = 9.81 * Math.tan(bankDeg * Math.PI / 180) / tas;   // rad/s
  const radius = tas * tas / (9.81 * Math.tan(bankDeg * Math.PI / 180)) / 4;   // the real radius is 4x this: compressed so the turn reads in the picture
  const a = omega * t * 0.8;
  const descent = 20 + 2.5 * t;                               // m/s, very high and growing
  return { x: radius * Math.cos(a) - radius, z: -radius * Math.sin(a), y: -(20 * t + 1.25 * t * t), heading: a + Math.PI / 2, bank: bankDeg, pitch: -30 - t,
    ias, g, rod: Math.round(descent * FT_PER_M * 60 / 100) * 100, stalled: false, radius };
}

EXPLORERS.spinspiral = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [-22, 9, 20] });
  stage.controls.maxDistance = 70;
  stage.controls.minDistance = 8;
  const c = stage.colours;
  const scene = stage.scene;
  const world = new THREE.Group();        // everything fixed to the air mass; it moves so the aeroplane stays in view
  scene.add(world);
  const plane = makePlane(THREE, c);
  scene.add(plane.group);
  const ground = new THREE.GridHelper(600, 30, c.line, c.line);
  world.add(ground);
  const horizon = dashedLine(THREE, v3(THREE, [-60, 0, 0], [60, 0, 0]), c.fgFaint, 1, 0.6);
  scene.add(horizon);
  const axis = dashedLine(THREE, v3(THREE, [0, -200, 0], [0, 40, 0]), c.fgFaint, 1.5, 1);
  world.add(axis);
  const TRAIL = 220;
  const trailGeo = new THREE.BufferGeometry().setFromPoints(Array.from({ length: TRAIL }, () => new THREE.Vector3()));
  const trail = new THREE.Line(trailGeo, new THREE.LineBasicMaterial({ color: c.brand }));
  world.add(trail);
  const trailPts = [];
  const aoaLabel = makeLabel(THREE, "", c.fg, 1.1);
  aoaLabel.position.set(0, 4.5, 0);
  scene.add(aoaLabel);
  function labelText(text, colour) {
    const canvas = aoaLabel.material.map.image, ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = "700 56px 'Inter Variable', system-ui, sans-serif";
    ctx.fillStyle = colour; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(text, canvas.width / 2, canvas.height / 2);
    aoaLabel.material.map.needsUpdate = true;
  }
  // streamers over the wing: attached when flying, broken away when stalled (as the attitude explorer draws them)
  const streamers = [];
  const streamerMat = new THREE.LineBasicMaterial({ color: c.skyFg });
  for (let i = 0; i < 4; i++) {
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 6 }, () => new THREE.Vector3())), streamerMat);
    line.userData.z = -3.5 + i * 2.3;
    streamers.push(line);
    plane.group.add(line);
  }

  const params = {};
  const state = { mode: "spin", t: 0, playing: true, recover: false, recoverT: 0, vs: 50 };
  const LOOP = { spin: 12, spiral: 14 };
  const RECOVERY = {
    spin: ["1 Throttle closed", "2 Ailerons neutral", "3 Full opposite rudder", "4 Control column centrally forward until the rotation stops", "5 Centralise the rudder, ease out of the dive"],
    spiral: ["1 Throttle closed", "2 Roll the wings level with aileron and coordinated rudder", "3 Ease out of the dive gently, load factor down", "4 Restore power once the speed is under control"],
  };
  let outsRef = {};
  wireControls(el, params, (p, outs) => {
    outsRef = outs;
    const mode = p.spiral ? "spiral" : "spin";
    if (mode !== state.mode) { state.mode = mode; state.t = 0; trailPts.length = 0; state.recover = false; }
    const rec = !!p.recover;
    if (rec !== state.recover) { state.recover = rec; state.recoverT = 0; }
    state.vs = p.vs || 50;
    setText(outs, "mode", mode === "spin" ? "SPIN: both wings stalled, autorotation" : "SPIRAL DIVE: wings flying, not stalled");
    setText(outs, "vs", `${state.vs} kt`);
    const list = el.querySelector("[data-out='recovery']");
    if (list) list.innerHTML = RECOVERY[mode].map((s) => `<li>${s}</li>`).join("");
    setText(outs, "tc", mode === "spin" ? "rotation to the left; the turn coordinator cannot tell a spin from a spiral" : "turn to the left; the turn coordinator cannot tell a spin from a spiral");
  });
  playButton(el, state);
  let last = null;
  const rad = (d) => d * Math.PI / 180;
  stage.onTick((t, reduced) => {
    if (last === null) last = t;
    const dt = Math.min(0.1, t - last); last = t;
    if (state.playing) {
      const step = reduced ? dt * 0.35 : dt;    // reduced motion: the manoeuvre plays slowly rather than not at all
      if (state.recover) state.recoverT = Math.min(6, state.recoverT + step);
      else { state.t += step; if (state.t > LOOP[state.mode]) { state.t = 0; trailPts.length = 0; } }
    }
    const s = spinSpiralState(state.mode, state.t, state.vs);
    const k = Math.min(1, state.recoverT / 4);     // recovery blend: 0 in the manoeuvre, 1 straight and level-ish
    const bank = lerp(s.bank, 0, k), pitch = lerp(s.pitch, state.mode === "spin" ? -10 : -5, k);
    const ias = state.mode === "spin" ? lerp(s.ias, 75, k) : lerp(s.ias, 100, k);
    const g = state.mode === "spin" ? lerp(s.g, 1.3, k) : lerp(s.g, 1.6, Math.min(1, k * 1.5));
    const rod = Math.round(lerp(s.rod, 500, k) / 100) * 100;
    const stalled = s.stalled && k < 0.5;
    const heading = s.heading;
    // the aeroplane stays near the origin; the air mass (grid, trail, axis) moves around it
    const pos = new THREE.Vector3(s.x, s.y, s.z);
    world.position.set(-pos.x, -pos.y, -pos.z);
    plane.group.rotation.set(0, 0, 0);
    plane.group.rotateY(heading); plane.group.rotateZ(rad(pitch)); plane.group.rotateX(rad(bank));
    if (state.mode === "spin" && !state.recover) { plane.rudder.rotation.y = 0.3; plane.elevator.rotation.z = 0.35; plane.aileronL.rotation.z = plane.aileronR.rotation.z = 0; }
    else if (state.recover && state.mode === "spin") { plane.rudder.rotation.y = -0.4 * (1 - k); plane.elevator.rotation.z = -0.35 * (1 - k); }
    else if (state.recover) { plane.rudder.rotation.y = 0; plane.elevator.rotation.z = -0.15 * k; plane.aileronL.rotation.z = 0.4 * (1 - k); plane.aileronR.rotation.z = -0.4 * (1 - k); }
    else { plane.rudder.rotation.y = 0; plane.elevator.rotation.z = 0.2; plane.aileronL.rotation.z = plane.aileronR.rotation.z = 0; }
    if (!reduced) plane.prop.rotation.x = t * (state.recover ? 8 : 14);
    if (state.playing && (trailPts.length === 0 || trailPts[trailPts.length - 1].distanceTo(pos) > 0.6)) { trailPts.push(pos.clone()); if (trailPts.length > TRAIL) trailPts.shift(); }
    const attr = trailGeo.attributes.position;
    for (let i = 0; i < TRAIL; i++) { const p = trailPts[Math.min(i, trailPts.length - 1)] || pos; attr.setXYZ(i, p.x, p.y, p.z); }
    attr.needsUpdate = true;
    trailGeo.setDrawRange(0, Math.max(1, trailPts.length));
    // streamers
    for (const sl of streamers) {
      const a = sl.geometry.attributes.position, z = sl.userData.z;
      for (let i = 0; i < 6; i++) {
        const f = i / 5;
        let x = WING_LE - f * 2.4, y = WING_Y + 0.1;
        if (stalled) y += f * f * 1.4 * (reduced ? 0.7 : 0.7 + 0.3 * Math.sin(t * 9 + i + z));
        else y += (reduced ? 0 : 0.03 * Math.sin(t * 6 + i + z));
        a.setXYZ(i, x, y, z);
      }
      a.needsUpdate = true;
      sl.material.color.set(stalled ? c.bad : c.skyFg);
    }
    labelText(stalled ? "STALLED · autorotation" : state.recover ? "recovering" : "flying · speed building", stalled ? c.bad : state.recover ? c.ok : c.warn);
    const trend = state.recover ? "" : state.mode === "spin" ? " · low, steady" : " · high, rising";
    setText(outsRef, "ias", `${Math.round(ias)} kt${trend}`, state.mode === "spin" ? "warn" : ias > 140 ? "bad" : "warn");
    setText(outsRef, "g", `${g.toFixed(1)} g${state.recover ? "" : state.mode === "spin" ? " · low" : " · high, building"}`, g >= 3.8 ? "bad" : g > 2.5 ? "warn" : "ok");
    el.querySelectorAll("[data-flag='overstress']").forEach((f) => { f.style.display = g >= 3.8 ? "" : "none"; });
    setText(outsRef, "rod", `${rod.toLocaleString("en-AU")} ft/min${state.recover ? "" : state.mode === "spin" ? " · high" : " · very high"}`);
    setText(outsRef, "wings", stalled ? "stalled: push to unstall" : state.recover ? "flying" : "flying: do not push, roll level then ease out", stalled ? "bad" : "ok");
    setText(outsRef, "clock", `${state.recover ? "recovery " + state.recoverT.toFixed(1) : state.t.toFixed(1)} s`);
  });
};

/* ------------------------------------------------------------------ explorer: wake vortices behind a heavy (BAKC 4.4)
   1 unit = 10 m. The heavy rotates at x = 0 at t = 0 (about a third of the way along a 2,000 m runway), climbs at 7°
   at 150 kt. Each wing-tip vortex is shed at the tip and then, as the lesson says: it sinks at a few hundred feet per
   minute (400 ft/min here) and levels off 500 to 1,000 ft below the generating aircraft's path (750 ft here); near
   the ground it stops sinking a short height above the surface (half the heavy's span here) and spreads outward at a
   few knots (2 kt here); the whole pair drifts with the wind; and it decays with time, faster in turbulent air. Your
   path lifts off 400 m before the heavy's rotation point, climbs at the same angle (so it stays above the heavy's path)
   and turns away upwind. Crosswind positive = from the right (+z), blowing the wake towards -z. */
export function wakeField(t, crosswindKt = 0, { turbulent = false, span = 6 } = {}) {
  const V = 7.7, CLIMB = Math.tan(7 * Math.PI / 180), SINK = 0.2, LEVEL = 23, FLOOR = span / 2, SPREAD = 0.103, SHED = 0.4 * span;   // spread 2 kt: the lesson's light-crosswind example
  const drift = -0.0514 * crosswindKt;      // u/s, with the wind
  const heavy = { x: V * t, y: V * t * CLIMB, pitch: 7 };
  const vortices = [];
  for (let s = 0; s <= t; s += 1) {
    const age = t - s, xs = V * s, ys = xs * CLIMB;
    const y = Math.max(ys - SINK * age, Math.min(ys, FLOOR), ys - LEVEL);
    const atFloor = ys < FLOOR ? age : Math.max(0, age - (ys - FLOOR) / SINK);
    const spread = (y <= FLOOR + 1e-6 ? SPREAD * atFloor : 0);
    const strength = Math.exp(-age / (turbulent ? 40 : 150));
    vortices.push({ age, x: xs, pathY: ys, y, zL: -SHED - spread + drift * age, zR: SHED + spread + drift * age, strength, inGroundEffect: y <= FLOOR + 1e-6 });
  }
  const side = crosswindKt < 0 ? -1 : 1;    // turn away towards the upwind side
  const you = (tt) => { const x = -40 + 3.3 * tt; return { x, y: Math.max(0, (x + 40) * CLIMB), z: side * 0.004 * Math.max(0, x - 40) ** 2 }; };
  return { heavy, vortices, you: you(t), youPath: Array.from({ length: 41 }, (_, i) => you(i)), runway: { x0: -67, x1: 133, halfWidth: 3 }, spreadKt: 2, sinkFtMin: 400 };
}

EXPLORERS.wake = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [-70, 40, 80] });
  stage.controls.maxDistance = 320;
  stage.controls.minDistance = 10;
  if (!el._casaView) stage.controls.target.set(40, 6, 0);
  stage.camera.far = 1000;
  stage.camera.updateProjectionMatrix();
  const c = stage.colours;
  const scene = stage.scene;
  const grid = new THREE.GridHelper(600, 30, c.line, c.line);
  grid.position.set(100, -0.05, 0);
  scene.add(grid);
  const rw = makeRunway(THREE, c, 200, 6);
  rw.position.x = 33;
  scene.add(rw);
  const heavy = makeHeavy(THREE, c, 6);
  scene.add(heavy);
  const plane = makePlane(THREE, c);
  plane.group.scale.setScalar(0.15);       // 1 unit = 10 m, so the real-size C152 is 0.73 units long; drawn 1.5x
  scene.add(plane.group);
  const heavyPath = dashedLine(THREE, v3(THREE, [0, 0, 0], [320, 320 * Math.tan(7 * Math.PI / 180), 0]), c.fgMuted, 2, 1.5);
  scene.add(heavyPath);
  const youPath = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineDashedMaterial({ color: c.ok, dashSize: 2, gapSize: 1 }));
  scene.add(youPath);
  const vortexMat = new THREE.LineBasicMaterial({ color: c.bad, transparent: true, opacity: 0.85 });
  const coreL = new THREE.Line(new THREE.BufferGeometry(), vortexMat), coreR = new THREE.Line(new THREE.BufferGeometry(), vortexMat);
  scene.add(coreL, coreR);
  // pinwheels every 5 s along each core show the sense of rotation: left clockwise, right anticlockwise, seen from behind
  const wheels = [];
  const spokeMat = new THREE.MeshStandardMaterial({ color: c.bad, transparent: true, opacity: 0.9 });
  for (let i = 0; i < 18; i++) {
    const g = new THREE.Group();
    for (let k = 0; k < 3; k++) { const m = new THREE.Mesh(new THREE.BoxGeometry(0.12, 2.2, 0.12), spokeMat); m.rotation.x = k * Math.PI / 3; g.add(m); }
    g.visible = false;
    wheels.push(g);
    scene.add(g);
  }
  const labels = {};
  for (const [k, txt, colour] of [["rot", "heavy's rotation point: its wake starts here", c.fgMuted], ["path", "its climb path", c.fgMuted], ["you", "you: lift off before its rotation point, climb above its path, turn upwind", c.ok], ["wind", "wind", c.skyFg], ["up", "upwind vortex", c.bad], ["down", "downwind vortex", c.bad]]) {
    labels[k] = makeLabel(THREE, txt, colour, 3.2);
    scene.add(labels[k]);
  }
  labels.rot.position.set(0, 2.5, 8);
  labels.path.position.set(150, 150 * Math.tan(7 * Math.PI / 180) + 3, 0);
  const marker = new THREE.Mesh(new THREE.ConeGeometry(0.8, 2, 10), new THREE.MeshStandardMaterial({ color: c.fgMuted }));
  marker.position.set(0, 1, 4.5);
  scene.add(marker);
  const wind = new THREE.ArrowHelper(new THREE.Vector3(0, 0, -1), new THREE.Vector3(-30, 6, 14), 14, c.skyFg, 4, 2);
  scene.add(wind);

  const params = {};
  const state = { t: 0, playing: true, xw: 0, turbulent: false, speed: 1 };
  let outsRef = {};
  wireControls(el, params, (p, outs) => {
    outsRef = outs;
    state.xw = p.crosswind || 0;
    state.turbulent = !!p.turbulent;
    state.speed = p.speed || 1;
    if (p.time !== undefined && !state.playing) state.t = p.time;
    wind.visible = Math.abs(state.xw) > 0.2;
    wind.setDirection(new THREE.Vector3(0, 0, state.xw > 0 ? -1 : 1));
    wind.position.set(-30, 6, state.xw > 0 ? 16 : -16);
    labels.wind.position.set(-30, 10, state.xw > 0 ? 16 : -16);
    labels.wind.visible = wind.visible;
    setText(outs, "xw", Math.abs(state.xw) < 0.2 ? "calm: still air" : `${Math.abs(state.xw).toFixed(0)} kt from the ${state.xw > 0 ? "right" : "left"}`);
    setText(outs, "air", state.turbulent ? "gusty, turbulent air: vortices mixed and broken up sooner" : "calm, stable air: vortices strongest and longest-lived (several minutes)", state.turbulent ? "ok" : "warn");
    const f = wakeField(0, state.xw);
    youPath.geometry.dispose();
    youPath.geometry = new THREE.BufferGeometry().setFromPoints(f.youPath.map((q) => new THREE.Vector3(q.x, q.y, q.z)));
    youPath.computeLineDistances();
  });
  playButton(el, state);
  let last = null;
  stage.onTick((t, reduced) => {
    if (last === null) last = t;
    const dt = Math.min(0.1, t - last); last = t;
    if (state.playing && !reduced) { state.t += dt * state.speed; if (state.t > 40) state.t = 0; const inp = el.querySelector("[data-param='time']"); if (inp) inp.value = String(state.t.toFixed(1)); }
    const f = wakeField(state.t, state.xw, { turbulent: state.turbulent });
    heavy.position.set(f.heavy.x, f.heavy.y + 0.9, 0);
    heavy.rotation.z = state.t > 0 ? 7 * Math.PI / 180 : 0;
    plane.group.position.set(f.you.x, f.you.y + 0.2, f.you.z);
    plane.group.rotation.set(0, -Math.atan2(0.008 * Math.max(0, f.you.x - 40) * (state.xw < 0 ? -1 : 1), 1), f.you.y > 0 ? 7 * Math.PI / 180 : 0);
    if (!reduced) plane.prop.rotation.x = t * 14;
    const L = f.vortices.map((v) => new THREE.Vector3(v.x, v.y, v.zL)), R = f.vortices.map((v) => new THREE.Vector3(v.x, v.y, v.zR));
    if (L.length >= 2) {
      coreL.geometry.dispose(); coreL.geometry = new THREE.BufferGeometry().setFromPoints(L);
      coreR.geometry.dispose(); coreR.geometry = new THREE.BufferGeometry().setFromPoints(R);
      coreL.visible = coreR.visible = true;
    } else coreL.visible = coreR.visible = false;
    let w = 0;
    for (let i = 0; i < f.vortices.length && w < wheels.length; i += 5) {
      const v = f.vortices[i];
      for (const [z, sense] of [[v.zL, 1], [v.zR, -1]]) {
        const g = wheels[w++];
        g.visible = true;
        g.position.set(v.x, v.y, z);
        g.scale.setScalar(0.4 + 0.8 * v.strength);
        g.rotation.x = reduced ? 0 : sense * t * 4;
      }
    }
    for (; w < wheels.length; w++) wheels[w].visible = false;
    const first = f.vortices[0];
    const up = state.xw < 0 ? first.zL : first.zR, down = state.xw < 0 ? first.zR : first.zL;
    labels.up.position.set(first.x, first.y + 2.5, up);
    labels.down.position.set(first.x, first.y + 2.5, down);
    labels.up.visible = labels.down.visible = Math.abs(state.xw) > 0.2 && state.t > 2;
    labels.you.position.set(f.you.x, f.you.y + 3, f.you.z);
    setText(outsRef, "time", `${state.t.toFixed(0)} s after the heavy rotated`);
    setText(outsRef, "heavy", `${Math.round(f.heavy.y * 10 * FT_PER_M / 10) * 10} ft, ${Math.round(f.heavy.x * 10 / 100) * 100} m past rotation`);
    const upM = Math.abs(up) * 10, overRunway = Math.abs(up) <= f.runway.halfWidth;
    setText(outsRef, "vortex", Math.abs(state.xw) < 0.2
      ? `both spread outward at a few knots: ${Math.round(Math.abs(first.zR) * 10)} m from the centreline after ${state.t.toFixed(0)} s`
      : overRunway ? `upwind vortex ${Math.round(upM)} m from the centreline: OVER THE RUNWAY` : `upwind vortex ${Math.round(upM)} m out, ${Math.round(upM - f.runway.halfWidth * 10)} m beyond the runway edge`,
      Math.abs(state.xw) < 0.2 ? "warn" : overRunway ? "bad" : "ok");
    el.querySelectorAll("[data-flag='parked']").forEach((fl) => { fl.style.display = overRunway && Math.abs(state.xw) >= 0.2 && state.t > 5 ? "" : "none"; });
    const oldest = f.vortices[Math.min(f.vortices.length - 1, 15)];
    setText(outsRef, "sink", oldest.inGroundEffect ? `in ground effect: stops sinking about ${Math.round(3 * 10 * FT_PER_M / 10) * 10} ft up and spreads sideways` : `sunk ${Math.round((oldest.pathY - oldest.y) * 10 * FT_PER_M / 10) * 10} ft below its path at 400 ft/min; levels off 500 to 1,000 ft below`);
    setText(outsRef, "strength", `${Math.round(first.strength * 100)}% of its strength ${first.age.toFixed(0)} s on (${state.turbulent ? "decaying fast" : "slow decay in calm air"})`, first.strength > 0.6 ? "bad" : first.strength > 0.3 ? "warn" : "ok");
  });
};

/* ------------------------------------------------------------------ explorer: crosswind landing (RBKA 3.7)
   Metres. Final approach at 3° from 900 m out to the aiming point at x = 0, then the roll-out. The wind is across
   the runway from the right (+z) unless fromLeft; the ground track is the centreline (z = 0) with either method.
   Crab: heading into wind by the crab angle asin(crosswind / TAS), wings level, then at the flare rudder yaws the
   nose straight and aileron stops the drift. Wing-down: nose on the runway heading, upwind wing lowered (bank drawn
   equal to the crab angle: illustrative), opposite rudder, touching down on the upwind main wheel first. */
export function crosswindApproach(method, xwKt, tasKt, u, fromLeft = false) {
  const side = fromLeft ? -1 : 1;
  const x = -900 + u * 1020;                                   // -900 m out to 120 m of roll-out
  const slope = Math.tan(3 * Math.PI / 180);
  const y = x < -60 ? -x * slope : x < 0 ? 3.14 * (x / -60) ** 2 : 0;
  const crab = Math.asin(Math.min(0.95, xwKt / tasKt));       // radians
  const flare = Math.max(0, Math.min(1, (x + 60) / 60));      // 0 before the flare, 1 at touchdown
  const rolling = x >= 0 ? Math.min(1, x / 120) : 0;
  let heading, bank, phase;
  if (method === "crab") {
    heading = crab * (1 - flare);                              // kick off the drift: nose straight by touchdown
    bank = crab * 0.4 * flare * (1 - rolling);                 // aileron into wind as the nose comes straight
    phase = x < -60 ? "crabbed: nose into wind, wings level, tracking the centreline" : x < 0 ? "flare: rudder yaws the nose straight, aileron stops the drift" : "rolling: aileron into wind, more as you slow";
  } else {
    heading = 0;
    bank = crab * (1 - rolling * 0.7);
    phase = x < -60 ? "wing-down: upwind wing low, opposite rudder keeps the nose straight" : x < 0 ? "touching down on the upwind main wheel first" : "rolling: upwind wing still low, more aileron as you slow";
  }
  const ghostZ = -side * (xwKt * 0.5144) * ((x + 900) / (tasKt * 0.5144));   // where no correction would take you
  return { x, y, z: 0, heading: heading * side, bank: bank * side, crabDeg: crab * 180 / Math.PI, phase, ghostZ, flare, rolling };
}

EXPLORERS.crosswind = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [-170, 70, 160] });
  stage.controls.maxDistance = 500;
  stage.controls.minDistance = 12;
  if (!el._casaView) stage.controls.target.set(-150, 20, 0);
  stage.camera.far = 3000;
  stage.camera.updateProjectionMatrix();
  const c = stage.colours;
  const scene = stage.scene;
  const grid = new THREE.GridHelper(1600, 32, c.line, c.line);
  grid.position.set(-300, -0.1, 0);
  scene.add(grid);
  const rw = makeRunway(THREE, c, 700, 30);
  rw.position.x = 250;
  scene.add(rw);
  const extended = dashedLine(THREE, v3(THREE, [-950, 0.1, 0], [-100, 0.1, 0]), c.paint, 10, 10);
  scene.add(extended);
  const glide = dashedLine(THREE, v3(THREE, [-900, 900 * Math.tan(3 * Math.PI / 180), 0], [0, 0, 0]), c.ok, 8, 5);
  scene.add(glide);
  const ghost = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineDashedMaterial({ color: c.bad, dashSize: 8, gapSize: 6 }));
  scene.add(ghost);
  const plane = makePlane(THREE, c);
  plane.group.scale.setScalar(2.5);        // drawn 2.5x so it reads from 300 m away
  scene.add(plane.group);
  const wind = new THREE.ArrowHelper(new THREE.Vector3(0, 0, -1), new THREE.Vector3(-400, 30, 90), 70, c.skyFg, 18, 9);
  scene.add(wind);
  const labels = {};
  for (const [k, txt, colour] of [["wind", "wind", c.skyFg], ["track", "ground track: the centreline", c.ok], ["ghost", "no correction: blown downwind", c.bad], ["aim", "aiming point", c.paint]]) {
    labels[k] = makeLabel(THREE, txt, colour, 18);
    scene.add(labels[k]);
  }
  labels.track.position.set(-520, 32, -40);
  labels.aim.position.set(0, 8, 30);
  const headingLine = solidLine(THREE, v3(THREE, [0, 0, 0], [60, 0, 0]), c.brand);
  plane.group.add(headingLine);
  headingLine.scale.setScalar(1 / 2.5);
  const nose = makeLabel(THREE, "heading", c.brand, 14);
  scene.add(nose);

  const params = {};
  const state = { u: 0, playing: true, xw: 10, tas: 65, method: "crab", fromLeft: false, poh: 12 };
  let outsRef = {};
  wireControls(el, params, (p, outs) => {
    outsRef = outs;
    state.xw = p.crosswind; state.tas = p.tas || 65; state.method = p.wingDown ? "wingdown" : "crab"; state.fromLeft = !!p.fromLeft; state.poh = p.poh || 12;
    if (p.position !== undefined && !state.playing) state.u = p.position;
    const side = state.fromLeft ? -1 : 1;
    wind.setDirection(new THREE.Vector3(0, 0, -side));
    wind.position.set(-400, 30, side * 90);
    labels.wind.position.set(-400, 40, side * 90);
    wind.visible = labels.wind.visible = state.xw > 0.2;
    const a = crosswindApproach(state.method, state.xw, state.tas, 0, state.fromLeft);
    const pts = Array.from({ length: 30 }, (_, i) => { const q = crosswindApproach(state.method, state.xw, state.tas, i / 29 * 0.88, state.fromLeft); return new THREE.Vector3(q.x, q.y, q.ghostZ); });
    ghost.geometry.dispose(); ghost.geometry = new THREE.BufferGeometry().setFromPoints(pts); ghost.computeLineDistances();
    ghost.visible = labels.ghost.visible = state.xw > 0.2;
    const end = pts[pts.length - 1];
    labels.ghost.position.set(end.x, end.y + 12, end.z);
    setText(outs, "xw", `${state.xw.toFixed(0)} kt from the ${state.fromLeft ? "left" : "right"}`);
    setText(outs, "tas", `${state.tas} kt`);
    setText(outs, "crab", `${a.crabDeg.toFixed(0)}° into wind`);
    const hdg = 240 + Math.round(a.crabDeg) * side;
    setText(outs, "heading", state.method === "crab" ? `heading ${String((hdg + 360) % 360).padStart(3, "0")}°, track 240° (runway 24)` : `heading 240° = track 240°; ${a.crabDeg.toFixed(0)}° of bank into wind`);
    setText(outs, "poh", state.xw > state.poh ? `${state.xw.toFixed(0)} kt is above your POH's ${state.poh} kt demonstrated crosswind: pick another runway or wait` : `${state.xw.toFixed(0)} kt is within your POH's ${state.poh} kt demonstrated crosswind`, state.xw > state.poh ? "bad" : state.xw > state.poh * 0.8 ? "warn" : "ok");
    setText(outs, "method", state.method === "crab" ? "crab: wings level, nose into wind; straighten with rudder just before touchdown" : "wing-down (sideslip): upwind wing low, opposite rudder; upwind main wheel touches first");
  });
  playButton(el, state);
  let last = null;
  stage.onTick((t, reduced) => {
    if (last === null) last = t;
    const dt = Math.min(0.1, t - last); last = t;
    if (state.playing && !reduced) { state.u += dt / 18; if (state.u > 1.05) state.u = 0; const inp = el.querySelector("[data-param='position']"); if (inp) inp.value = String(Math.min(1, state.u).toFixed(3)); }
    const a = crosswindApproach(state.method, state.xw, state.tas, Math.min(1, state.u), state.fromLeft);
    plane.group.position.set(a.x, a.y + 1.43 * 2.5, a.z);
    plane.group.rotation.set(0, 0, 0);
    plane.group.rotateY(-a.heading);
    plane.group.rotateZ(a.y > 0.5 ? -3 * Math.PI / 180 + (a.flare * 6 * Math.PI / 180) : 0);
    plane.group.rotateX(a.bank);
    const sideSign = state.fromLeft ? -1 : 1;
    plane.aileronR.rotation.z = -a.bank * 1.5;
    plane.aileronL.rotation.z = a.bank * 1.5;
    plane.rudder.rotation.y = state.method === "wingdown" ? -sideSign * 0.25 : (a.flare > 0 && a.flare < 1 ? -sideSign * 0.3 : 0);   // opposite rudder: left pedal when the wind is from the right
    if (!reduced) plane.prop.rotation.x = t * 12;
    nose.position.set(a.x + 70 * Math.cos(a.heading), a.y + 6, a.z + 70 * Math.sin(a.heading));
    nose.visible = state.xw > 0.2 && a.rolling === 0;
    setText(outsRef, "phase", a.phase);
    setText(outsRef, "where", a.x < 0 ? `${Math.round(-a.x)} m from the aiming point, ${Math.round(a.y * FT_PER_M)} ft up` : `rolling, ${Math.round(a.x)} m past the aiming point`);
  });
};

/* ------------------------------------------------------------------ explorer: GNSS trilateration (GNSSC 2.1)
   1 unit = 1,000 km. The Earth is a sphere of radius 6.37, the receiver sits on top of it, the satellites orbit at
   20,200 km above the surface (26.57 from the centre), in the directions (azimuth, elevation) listed. Each satellite's
   range sphere is centred on it with the pseudorange as its radius: the true range plus the receiver's clock error,
   the same for every satellite (the lesson's "every range wrong by the same amount"), plus an extra error for a faulty
   satellite. Returns the satellites, the circle where spheres 1 and 2 meet, the two points where sphere 3 cuts it, and
   what the receiver can conclude with n satellites (the lesson's 3 / 4 / 5 / 6 rules). */
export function gnssGeometry(n, { clockError = false, bunched = false, faulty = false } = {}) {
  const RE = 6.37, ORBIT = 26.57;
  const receiver = [0, RE, 0];
  const dirs = bunched ? [[70, 40], [95, 55], [60, 62], [110, 38], [85, 48], [75, 70]] : [[40, 50], [150, 35], [250, 60], [330, 30], [90, 72], [200, 20]];
  const err = clockError ? 2.2 : 0;
  const sats = dirs.slice(0, Math.max(0, Math.min(6, n))).map(([az, el], i) => {
    const a = az * Math.PI / 180, e = el * Math.PI / 180;
    const d = [Math.cos(e) * Math.sin(a), Math.sin(e), -Math.cos(e) * Math.cos(a)];
    const rd = RE * d[1];
    const s = -rd + Math.sqrt(rd * rd + ORBIT * ORBIT - RE * RE);     // true range from the receiver
    const pos = receiver.map((r, k) => r + s * d[k]);
    const fault = faulty && i === 4 ? 1.6 : 0;
    return { id: i + 1, az, el, pos, trueRange: s, range: s + err + fault, faulty: fault > 0 };
  });
  const sub = (a, b) => a.map((v, i) => v - b[i]), len = (a) => Math.hypot(...a), scale = (a, k) => a.map((v) => v * k), add = (a, b) => a.map((v, i) => v + b[i]);
  const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
  let circle = null, points = null;
  if (sats.length >= 2) {
    const c1 = sats[0].pos, c2 = sats[1].pos, r1 = sats[0].range, r2 = sats[1].range;
    const dv = sub(c2, c1), d = len(dv), nrm = scale(dv, 1 / d);
    const a = (r1 * r1 - r2 * r2 + d * d) / (2 * d), h2 = r1 * r1 - a * a;
    if (h2 > 0) circle = { centre: add(c1, scale(nrm, a)), normal: nrm, radius: Math.sqrt(h2) };
  }
  if (sats.length >= 3 && !clockError) {
    const c1 = sats[0].pos, c2 = sats[1].pos, c3 = sats[2].pos;
    const u = sub(c2, c1), v = sub(c3, c1);
    const m = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    const mn = scale(m, 1 / len(m));
    const k = dot(sub(receiver, c1), mn);
    const mirror = sub(receiver, scale(mn, 2 * k));
    points = { fix: receiver, discarded: mirror, discardedWhere: len(mirror) < RE ? "deep inside the Earth" : "far out in space" };
  }
  const nn = sats.length;
  let status;
  if (nn === 0) status = "no satellites: no ranges, no position";
  else if (nn === 1) status = "one range: you are somewhere on a sphere around that satellite";
  else if (nn === 2) status = "two spheres meet in a circle";
  else if (nn === 3) status = clockError ? "three pseudoranges, all too long by the receiver's clock error: the spheres miss; many receivers fall back to a 2D fix" : "three spheres cut the circle at two points; one is deep in the Earth or out in space and is discarded";
  else if (nn === 4) status = "four satellites: three for position, one for the receiver's clock: a 3D fix";
  else if (nn === 5) status = faulty ? "RAIM: the four-satellite solutions disagree: a satellite is faulty, the receiver warns you (fault detection)" : "five satellites: RAIM compares the four-satellite solutions; they agree, the fix is checked";
  else status = faulty ? "six satellites: RAIM finds that satellite 5 is the culprit and excludes it, and keeps navigating (fault detection and exclusion)" : "six satellites: RAIM can detect a faulty satellite and exclude it (FDE)";
  return { receiver, earthRadius: RE, sats, circle, points, status, solvedClock: nn >= 4, raim: nn >= 5, fde: nn >= 6 };
}

EXPLORERS.gnss = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [-40, 40, 60] });
  stage.controls.maxDistance = 150;
  stage.controls.minDistance = 15;
  if (!el._casaView) stage.controls.target.set(0, 12, 0);
  stage.camera.far = 600;
  stage.camera.updateProjectionMatrix();
  const c = stage.colours;
  const scene = stage.scene;
  const earth = new THREE.Mesh(new THREE.SphereGeometry(6.37, 40, 28), new THREE.MeshStandardMaterial({ color: c.skySoft, roughness: 0.9 }));
  scene.add(earth);
  const earthGrid = new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.SphereGeometry(6.38, 18, 12)), new THREE.LineBasicMaterial({ color: c.skyFg, transparent: true, opacity: 0.25 }));
  scene.add(earthGrid);
  const you = new THREE.Mesh(new THREE.SphereGeometry(0.5, 12, 10), new THREE.MeshStandardMaterial({ color: c.brand }));
  you.position.set(0, 6.37, 0);
  scene.add(you);
  const youLabel = makeLabel(THREE, "receiver: you", c.brand, 3.5);
  youLabel.position.set(0, 9, 3);
  scene.add(youLabel);
  const scaleLabel = makeLabel(THREE, "to scale: satellites 20,200 km up", c.fgFaint, 3.5);
  scaleLabel.position.set(0, -10, 0);
  scene.add(scaleLabel);
  const satGroup = new THREE.Group();
  scene.add(satGroup);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(1, 0.12, 8, 64), new THREE.MeshStandardMaterial({ color: c.brand }));
  ring.visible = false;
  scene.add(ring);
  const fixDot = new THREE.Mesh(new THREE.SphereGeometry(0.7, 12, 10), new THREE.MeshStandardMaterial({ color: c.ok }));
  const badDot = new THREE.Mesh(new THREE.SphereGeometry(0.7, 12, 10), new THREE.MeshStandardMaterial({ color: c.fgMuted }));
  fixDot.visible = badDot.visible = false;
  scene.add(fixDot, badDot);
  const discardLabel = makeLabel(THREE, "", c.fgMuted, 3.2);
  scene.add(discardLabel);
  const missLabel = makeLabel(THREE, "pseudoranges too long: the spheres miss you", c.bad, 3.4);
  missLabel.position.set(0, 12, -6);
  missLabel.visible = false;
  scene.add(missLabel);

  const params = {};
  let built = [];
  function rebuild(p) {
    for (const o of built) { satGroup.remove(o); o.traverse?.((m) => { m.geometry?.dispose(); }); }
    built = [];
    const g = gnssGeometry(p.sats, { clockError: !!p.clockError && p.sats < 4, bunched: !!p.bunched, faulty: !!p.faulty });
    for (const s of g.sats) {
      const excluded = g.fde && s.faulty;
      const colour = s.faulty ? c.bad : g.solvedClock ? c.ok : p.clockError ? c.warn : c.info;
      const sat = new THREE.Group();
      const body = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshStandardMaterial({ color: c.fg }));
      const panels = new THREE.Mesh(new THREE.BoxGeometry(4.5, 0.1, 1.2), new THREE.MeshStandardMaterial({ color: colour }));
      sat.add(body, panels);
      sat.position.set(...s.pos);
      sat.lookAt(0, 0, 0);
      const sphere = new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.SphereGeometry(s.range, 14, 10)), new THREE.LineBasicMaterial({ color: colour, transparent: true, opacity: excluded ? 0.06 : 0.22 }));
      sphere.position.set(...s.pos);
      const lbl = makeLabel(THREE, `satellite ${s.id}${s.faulty ? (excluded ? ": faulty, excluded" : ": faulty") : ""}`, colour, 3.2);
      lbl.position.set(s.pos[0], s.pos[1] + 2.5, s.pos[2]);
      const ray = dashedLine(THREE, v3(THREE, [0, 6.37, 0], s.pos), colour, 0.6, 0.5);
      ray.material.transparent = true; ray.material.opacity = excluded ? 0.2 : 0.7;
      satGroup.add(sat, sphere, lbl, ray);
      built.push(sat, sphere, lbl, ray);
    }
    if (g.circle) {
      ring.visible = true;
      ring.geometry.dispose();
      ring.geometry = new THREE.TorusGeometry(g.circle.radius, 0.12, 8, 96);
      ring.position.set(...g.circle.centre);
      ring.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), new THREE.Vector3(...g.circle.normal));
    } else ring.visible = false;
    if (g.points) {
      fixDot.visible = badDot.visible = true;
      badDot.position.set(...g.points.discarded);
      discardLabel.position.set(g.points.discarded[0], g.points.discarded[1] + 2.5, g.points.discarded[2]);
      const canvas = discardLabel.material.map.image, ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.font = "600 56px 'Inter Variable', system-ui, sans-serif"; ctx.fillStyle = c.fgMuted; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(`other point: ${g.points.discardedWhere}, discarded`, 256, 64);
      discardLabel.material.map.needsUpdate = true;
      discardLabel.visible = true;
      fixDot.position.set(0, 6.37, 0);
    } else { fixDot.visible = badDot.visible = discardLabel.visible = false; }
    missLabel.visible = !!p.clockError && p.sats >= 2 && p.sats < 4;
    return g;
  }
  wireControls(el, params, (p, outs) => {
    const g = rebuild(p);
    setText(outs, "sats", `${g.sats.length} in view`);
    setText(outs, "status", g.status, g.sats.length < 4 ? "warn" : (p.faulty && g.sats.length === 5) ? "bad" : "ok");
    setText(outs, "fix", g.sats.length < 3 ? "no fix" : g.sats.length === 3 ? (p.clockError ? "2D fix at best (height assumed)" : "3D geometry, but the clock is unsolved") : "3D fix: latitude, longitude, height, clock");
    setText(outs, "raim", g.sats.length < 5 ? "RAIM not available: nothing is checking the position" : g.sats.length === 5 ? (p.faulty ? "fault detected: warning, revert to other navigation" : "fault detection available: solutions agree") : (p.faulty ? "faulty satellite excluded (FDE): navigation continues" : "fault detection and exclusion available"), g.sats.length < 5 ? "warn" : p.faulty && g.sats.length === 5 ? "bad" : "ok");
    setText(outs, "dop", p.bunched ? "satellites bunched in one part of the sky: spheres cross at shallow angles, every range error magnified (high DOP)" : "satellites spread across the sky: spheres cross cleanly, errors stay small (low DOP)", p.bunched ? "bad" : "ok");
  });
  stage.onTick((t, reduced) => {
    if (!reduced) satGroup.rotation.y = Math.sin(t * 0.1) * 0.03;
  });
};

/* ------------------------------------------------------------------ explorer: the ten cloud genera by height (PMTC 2.3)
   1 unit = 1,000 ft up; across, the sky is an arbitrary 70 units wide. The bands are the lesson's: high above about
   20,000 ft (ice crystals), middle about 6,500 to 20,000 ft, low below about 6,500 ft, plus Cu and Cb with a low base
   and great vertical extent, the Cb anvil at the tropopause (36,090 ft in the ISA, PMTC 2.1). Base and top heights of
   each genus are representative within its band, not figures from the lesson. */
export function cloudBands() {
  return [
    { name: "Low", from: 0, to: 6.5, note: "below about 6,500 ft" },
    { name: "Middle", from: 6.5, to: 20, note: "about 6,500 to 20,000 ft; water droplets, often supercooled" },
    { name: "High", from: 20, to: 36, note: "above about 20,000 ft; ice crystals" },
  ];
}
export function cloudGenera() {
  return [
    { id: 1, abbr: "Ci", name: "Cirrus", band: "High", form: "wisp", x: -20, z: -8, base: 29, top: 30.5, look: "white wisps, streaks and hooks of ice crystals (mares' tails)", weather: "no precipitation, no icing; thickening into cirrostratus often heralds a warm front or a jet stream" },
    { id: 2, abbr: "Cc", name: "Cirrocumulus", band: "High", form: "ripples", x: 4, z: -14, base: 26.5, top: 27.5, look: "small white ripples or grains, no shading", weather: "none; at most light turbulence" },
    { id: 3, abbr: "Cs", name: "Cirrostratus", band: "High", form: "veil", x: 22, z: 2, base: 24.5, top: 25.5, look: "a thin white veil; its ice crystals bend sunlight into a halo round the sun or moon", weather: "none; increasing Ci then Cs often heralds a warm front" },
    { id: 4, abbr: "Ac", name: "Altocumulus", band: "Middle", form: "ripples", x: -22, z: 6, base: 12, top: 13.5, look: "grey-white rolls or patches, larger than Cc and shaded", weather: "usually dry, light bumps, light icing; Ac castellanus (turrets) in the morning warns of afternoon thunderstorms" },
    { id: 5, abbr: "As", name: "Altostratus", band: "Middle", form: "sheet", x: 6, z: 12, base: 10, top: 13, look: "a grey or bluish sheet, the sun seen as through ground glass, no halo", weather: "light continuous rain, light to moderate icing; thickening and lowering As means a front approaching" },
    { id: 6, abbr: "Ns", name: "Nimbostratus", band: "Middle", form: "slab", x: 24, z: -16, base: 2, top: 12, look: "thick, dark, featureless layer; classed as middle cloud but its base often lowers to near the ground", weather: "continuous moderate to heavy rain, moderate to severe icing, poor visibility, ragged St fractus beneath" },
    { id: 7, abbr: "Sc", name: "Stratocumulus", band: "Low", form: "lumps", x: -6, z: -2, base: 3, top: 4.5, look: "a grey layer of lumps, rolls or patches, often with blue sky between", weather: "light drizzle or light showers, light icing, bumpy below; usually fair" },
    { id: 8, abbr: "St", name: "Stratus", band: "Low", form: "sheet", x: -26, z: 18, base: 0.6, top: 1.4, look: "a uniform grey layer with a very low base; hill fog where it touches high ground", weather: "drizzle, smooth air, very low base, hills in cloud, poor visibility" },
    { id: 9, abbr: "Cu", name: "Cumulus", band: "Low base, great vertical extent", form: "heap", x: 10, z: -4, base: 3.2, top: 6.5, look: "separate heaps with flat bases and cauliflower tops; TCu when towering", weather: "fair-weather Cu none; large Cu showers, moderate turbulence below and in it; good visibility outside showers" },
    { id: 10, abbr: "Cb", name: "Cumulonimbus", band: "Low base, great vertical extent", form: "tower", x: 24, z: 16, base: 3.2, top: 36, look: "a huge tower to the tropopause, spreading into a flat anvil top", weather: "heavy showers, hail, thunderstorms, severe icing and turbulence, lightning, microbursts, squalls, gust fronts" },
  ];
}

EXPLORERS.clouds = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [-55, 30, 80] });
  stage.controls.maxDistance = 200;
  stage.controls.minDistance = 10;
  if (!el._casaView) stage.controls.target.set(0, 14, 0);
  stage.camera.far = 800;
  stage.camera.updateProjectionMatrix();
  const c = stage.colours;
  const scene = stage.scene;
  const sky = new THREE.Mesh(new THREE.SphereGeometry(300, 24, 16), new THREE.MeshBasicMaterial({ color: c.skySoft, side: THREE.BackSide }));
  scene.add(sky);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshStandardMaterial({ color: c.surface2, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2; ground.position.y = -0.05;
  scene.add(ground);
  const grid = new THREE.GridHelper(120, 12, c.line, c.line);
  scene.add(grid);
  const hill = new THREE.Mesh(new THREE.ConeGeometry(9, 1.2, 24), new THREE.MeshStandardMaterial({ color: c.surface2, roughness: 1 }));
  hill.position.set(-26, 0.6, 18);
  scene.add(hill);
  // band boundaries at 6,500 and 20,000 ft, and the tropopause
  for (const [h, label] of [[6.5, "6,500 ft"], [20, "20,000 ft"], [36, "tropopause (36,090 ft ISA)"]]) {
    const sheet = new THREE.Mesh(new THREE.PlaneGeometry(90, 70), glassMat(THREE, c.skyFg, 0.08));
    sheet.rotation.x = -Math.PI / 2; sheet.position.y = h;
    scene.add(sheet);
    const edge = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(90, 70)), new THREE.LineBasicMaterial({ color: c.skyFg, transparent: true, opacity: 0.5 }));
    edge.rotation.x = -Math.PI / 2; edge.position.y = h;
    scene.add(edge);
    const l = makeLabel(THREE, label, c.skyFg, 3.2);
    l.position.set(-46, h + 1.2, 36);
    scene.add(l);
  }
  for (const [name, y, note] of [["Low", 3, "below about 6,500 ft"], ["Middle", 13, "about 6,500 to 20,000 ft"], ["High", 28, "above about 20,000 ft: ice crystals"]]) {
    const l = makeLabel(THREE, `${name}: ${note}`, c.fgMuted, 3.6);
    l.position.set(-44, y, -36);
    scene.add(l);
  }
  // the sun, with the halo that cirrostratus makes
  const sun = new THREE.Mesh(new THREE.SphereGeometry(1.6, 16, 12), new THREE.MeshBasicMaterial({ color: c.warn }));
  sun.position.set(30, 44, -10);
  scene.add(sun);
  const halo = new THREE.Mesh(new THREE.TorusGeometry(5, 0.18, 8, 48), new THREE.MeshBasicMaterial({ color: c.warn, transparent: true, opacity: 0.7 }));
  halo.position.copy(sun.position);
  halo.lookAt(0, 6, 0);
  halo.visible = false;
  scene.add(halo);

  const cloudColour = c.dark ? c.fgMuted : c.surface, darkCloud = c.dark ? c.fgFaint : c.lineStrong;
  const clouds = {};
  const seeded = (n) => { let s = n * 9301 + 49297; return () => { s = (s * 9301 + 49297) % 233280; return s / 233280; }; };
  for (const g of cloudGenera()) {
    const grp = new THREE.Group();
    const mat = new THREE.MeshStandardMaterial({ color: g.form === "slab" || g.form === "tower" ? darkCloud : cloudColour, roughness: 0.95, transparent: true, opacity: 1 });
    const rnd = seeded(g.id);
    const blob = (x, y, z, r, sy = 1, sx = 1, sz = 1) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 10, 8), mat); m.position.set(x, y, z); m.scale.set(sx, sy, sz); grp.add(m); };
    const h = g.top - g.base;
    if (g.form === "heap") { for (let i = 0; i < 7; i++) blob((rnd() - 0.5) * 8, g.base + rnd() * h * 0.8 + 0.8, (rnd() - 0.5) * 6, 1.4 + rnd() * 1.2); blob(0, g.base + 0.5, 0, 4, 0.25, 1, 0.8); }
    else if (g.form === "tower") {
      for (let i = 0; i < 14; i++) blob((rnd() - 0.5) * 7, g.base + 1 + i * (h - 4) / 14, (rnd() - 0.5) * 6, 2.2 + rnd() * 1.4);
      blob(0, g.base + 0.6, 0, 4.5, 0.25, 1, 0.9);
      const anvil = new THREE.Mesh(new THREE.CylinderGeometry(9, 4, 2.2, 20), mat); anvil.position.set(2, g.top - 1.4, 0); grp.add(anvil);
    }
    else if (g.form === "lumps") { for (let i = 0; i < 12; i++) blob((rnd() - 0.5) * 18, g.base + 0.6 + rnd() * (h - 1), (rnd() - 0.5) * 12, 1.2 + rnd(), 0.7, 1.4, 1.2); }
    else if (g.form === "ripples") { for (let i = 0; i < 24; i++) blob((rnd() - 0.5) * 18, g.base + 0.4 + rnd() * (h - 0.8), (rnd() - 0.5) * 12, 0.5 + rnd() * 0.5, 0.5, 1.6, 1.1); }
    else if (g.form === "sheet") { blob(0, g.base + h / 2, 0, 1, h / 2, 10, 7); }
    else if (g.form === "slab") { blob(0, g.base + h / 2, 0, 1, h / 2, 11, 8); }
    else if (g.form === "veil") { blob(0, g.base + h / 2, 0, 1, h / 3, 14, 10); mat.opacity = 0.6; }
    else if (g.form === "wisp") { for (let i = 0; i < 6; i++) { const w = new THREE.Mesh(new THREE.BoxGeometry(6 + rnd() * 6, 0.25, 0.6), mat); w.position.set((rnd() - 0.5) * 16, g.base + rnd() * h, (rnd() - 0.5) * 10); w.rotation.y = (rnd() - 0.5) * 0.8; w.rotation.z = 0.15; grp.add(w); } }
    grp.position.set(g.x, 0, g.z);
    grp.userData = { genus: g, baseOpacity: mat.opacity, mat };
    const lbl = makeLabel(THREE, `${g.name} ${g.abbr}`, c.fg, 2.8);
    lbl.position.set(0, g.top + 1.6, 0);
    grp.add(lbl);
    grp.userData.label = lbl;
    scene.add(grp);
    clouds[g.id] = grp;
  }
  const plane = makePlane(THREE, c);
  plane.group.scale.setScalar(0.35);
  plane.group.position.set(-10, 3, 8);
  scene.add(plane.group);
  const planeLabel = makeLabel(THREE, "C152 cruising at 3,000 ft (drawn 100x)", c.fgMuted, 2.6);
  planeLabel.position.set(-10, 5.2, 8);
  scene.add(planeLabel);

  const params = {};
  const genera = cloudGenera();
  wireControls(el, params, (p, outs) => {
    const sel = p.genus || 0;
    for (const grp of Object.values(clouds)) {
      const on = sel === 0 || grp.userData.genus.id === sel;
      grp.userData.mat.opacity = on ? grp.userData.baseOpacity : 0.18;
      grp.userData.mat.emissive = new THREE.Color(on && sel !== 0 ? c.brand : 0x000000);
      grp.userData.mat.emissiveIntensity = on && sel !== 0 ? 0.35 : 0;
      grp.userData.label.material.opacity = on ? 1 : 0.3;
    }
    halo.visible = sel === 3;
    plane.group.visible = planeLabel.visible = !!p.showPlane;
    const g = genera.find((x) => x.id === sel);
    setText(outs, "genus", g ? `${g.name} (${g.abbr})` : "all ten genera");
    setText(outs, "band", g ? `${g.band}${g.band === "High" ? ": above about 20,000 ft, ice crystals" : g.band === "Middle" ? ": about 6,500 to 20,000 ft" : g.band === "Low" ? ": below about 6,500 ft" : ": base low, tops to great height"}` : "low below 6,500 ft, middle 6,500 to 20,000 ft, high above 20,000 ft");
    setText(outs, "look", g ? g.look : "pick a genus to read its look and weather");
    setText(outs, "weather", g ? g.weather : "layer cloud: stable air, steady precipitation; heap cloud: unstable air, showers and bumps", g && (g.abbr === "Cb" || g.abbr === "Ns") ? "bad" : g && (g.abbr === "Cu" || g.abbr === "St" || g.abbr === "As") ? "warn" : "ok");
    setText(outs, "report", g ? (g.abbr === "Cb" ? "named in a TAF or METAR as CB (for example SCT050CB)" : g.abbr === "Cu" ? "only named in a TAF or METAR when towering: TCU" : "not named in a TAF or METAR: only its amount (oktas) and base") : "only CB and TCU are named in a TAF or METAR");
  });
  stage.onTick((t, reduced) => {
    if (!reduced) { plane.prop.rotation.x = t * 14; for (const grp of Object.values(clouds)) grp.position.x = grp.userData.genus.x + Math.sin(t * 0.15 + grp.userData.genus.id) * 0.6; }
  });
};

/* ------------------------------------------------------------------ explorer: minimum heights (RFRC 2.3)
   1 unit = 100 m across and up. A town (populous area) in the middle, open country either side; obstacles in metres.
   The rule, as RFRC 2.3 states it: over a populous area, not below 1,000 ft above the highest obstacle within a 600 m
   radius of the aircraft; anywhere else, not below 500 ft above the highest feature or obstacle within a 300 m radius
   of the point directly below the aircraft. */
export function minimumHeightWorld() {
  const obstacles = [];
  const rnd = (() => { let s = 7; return () => { s = (s * 9301 + 49297) % 233280; return s / 233280; }; })();
  for (let i = 0; i < 26; i++) obstacles.push({ kind: "building", x: -7 + (i % 9) * 1.75 + rnd() * 0.4, z: -3 + Math.floor(i / 9) * 2.6 + rnd() * 0.6, h: 10 + rnd() * 30, w: 1.1 });
  obstacles.push({ kind: "tower", name: "100 m tower", x: 5.5, z: 1, h: 100, w: 0.5 });
  obstacles.push({ kind: "tree", x: 14, z: -2, h: 15, w: 0.8 }, { kind: "tree", x: 17, z: 2.5, h: 15, w: 0.8 }, { kind: "tree", x: -18, z: -2, h: 15, w: 0.8 }, { kind: "tree", x: -14, z: 3, h: 15, w: 0.8 });
  obstacles.push({ kind: "hill", name: "60 m hill", x: 23, z: 0, h: 60, w: 5 });
  obstacles.push({ kind: "mast", name: "40 m mast", x: -22, z: 1.5, h: 40, w: 0.3 });
  return { obstacles, populous: [-8.5, 10.5], ground: 0 };
}
export function minimumHeightAt(world, x, z = 0) {
  const populous = x >= world.populous[0] && x <= world.populous[1];
  const radiusM = populous ? 600 : 300, aboveFt = populous ? 1000 : 500;
  let highest = { h: 0, kind: "the surface", name: "flat ground" };
  for (const o of world.obstacles) {
    const edge = o.kind === "hill" ? Math.max(0, Math.hypot(x - o.x, z - o.z) - o.w * 0.6) : Math.hypot(x - o.x, z - o.z);
    if (edge * 100 <= radiusM && o.h > highest.h) highest = o;
  }
  const floorFt = Math.round(highest.h * FT_PER_M + aboveFt);
  return { populous, radiusM, aboveFt, highest, floorFt, rule: populous
    ? "populous area: not below 1,000 ft above the highest obstacle within a 600 m radius of the aircraft"
    : "anywhere else: not below 500 ft above the highest feature or obstacle within a 300 m radius of the point directly below the aircraft" };
}

EXPLORERS.minheights = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [-26, 16, 34] });
  stage.controls.maxDistance = 120;
  stage.controls.minDistance = 6;
  if (!el._casaView) stage.controls.target.set(0, 3, 0);
  stage.camera.far = 500;
  stage.camera.updateProjectionMatrix();
  const c = stage.colours;
  const scene = stage.scene;
  const world = minimumHeightWorld();
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(120, 60), new THREE.MeshStandardMaterial({ color: c.surface2, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2; ground.position.y = -0.03;
  scene.add(ground);
  scene.add(new THREE.GridHelper(120, 24, c.line, c.line));
  const town = new THREE.Mesh(new THREE.PlaneGeometry(world.populous[1] - world.populous[0], 14), glassMat(THREE, c.warn, 0.12));
  town.rotation.x = -Math.PI / 2; town.position.set((world.populous[0] + world.populous[1]) / 2, 0.01, 0);
  scene.add(town);
  const bMat = new THREE.MeshStandardMaterial({ color: c.dark ? c.fgFaint : c.lineStrong, roughness: 0.9 });
  const meshes = [];
  for (const o of world.obstacles) {
    let m;
    const h = o.h / 100;
    if (o.kind === "building" || o.kind === "tower" || o.kind === "mast") { m = new THREE.Mesh(new THREE.BoxGeometry(o.w, h, o.w), bMat.clone()); m.position.set(o.x, h / 2, o.z); }
    else if (o.kind === "tree") { m = new THREE.Mesh(new THREE.ConeGeometry(o.w / 2, h, 8), new THREE.MeshStandardMaterial({ color: c.ok, roughness: 1 })); m.position.set(o.x, h / 2, o.z); }
    else { m = new THREE.Mesh(new THREE.ConeGeometry(o.w, h, 20), bMat.clone()); m.position.set(o.x, h / 2, o.z); }
    m.userData.obstacle = o;
    scene.add(m);
    meshes.push(m);
  }
  for (const [txt, x, z, colour] of [["populous area (town)", 1, 8.5, c.warn], ["open country", 20, 8.5, c.fgMuted], ["open country", -18, 8.5, c.fgMuted], ["100 m tower", 5.5, 1, c.fg], ["60 m hill", 23, 0, c.fg], ["40 m mast", -22, 1.5, c.fg]]) {
    const l = makeLabel(THREE, txt, colour, 1.6);
    const o = world.obstacles.find((q) => q.name === txt);
    l.position.set(x, o ? o.h / 100 + 0.8 : 0.6, z);
    scene.add(l);
  }
  // the floor you must stay above, along the track z = 0
  const floorPts = [];
  for (let x = -30; x <= 30; x += 0.25) floorPts.push(new THREE.Vector3(x, minimumHeightAt(world, x, 0).floorFt / FT_PER_M / 100, 0));
  const floorLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints(floorPts), new THREE.LineBasicMaterial({ color: c.bad }));
  scene.add(floorLine);
  const floorLabel = makeLabel(THREE, "the floor along this track: 1,000 ft above the highest obstacle within 600 m over the town, 500 ft within 300 m elsewhere", c.bad, 2);
  floorLabel.position.set(0, minimumHeightAt(world, 0, 0).floorFt / FT_PER_M / 100 + 1.5, 0);
  scene.add(floorLabel);
  const cyl = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, 48, 1, true), glassMat(THREE, c.brand, 0.12));
  const disc = new THREE.Mesh(new THREE.CircleGeometry(1, 48), glassMat(THREE, c.brand, 0.25));
  disc.rotation.x = -Math.PI / 2;
  const floorDisc = new THREE.Mesh(new THREE.CircleGeometry(1, 48), glassMat(THREE, c.bad, 0.3));
  floorDisc.rotation.x = -Math.PI / 2;
  scene.add(cyl, disc, floorDisc);
  const radiusLabel = makeLabel(THREE, "", c.brand, 1.8);
  scene.add(radiusLabel);
  const plane = makePlane(THREE, c);
  plane.group.scale.setScalar(0.12);      // the real C152 would be 0.07 units long; drawn about 12x
  scene.add(plane.group);
  const drop = dashedLine(THREE, v3(THREE, [0, 0, 0], [0, 1, 0]), c.fgMuted, 0.3, 0.2);
  scene.add(drop);
  function label(sprite, text, colour) {
    const canvas = sprite.material.map.image, ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = "600 56px 'Inter Variable', system-ui, sans-serif"; ctx.fillStyle = colour; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(text, 256, 64);
    sprite.material.map.needsUpdate = true;
  }

  const params = {};
  const state = { x: 0, alt: 1200 };
  wireControls(el, params, (p, outs) => {
    state.x = p.x; state.alt = p.altitude;
    const r = minimumHeightAt(world, state.x, 0);
    const R = r.radiusM / 100, y = state.alt / FT_PER_M / 100, fy = r.floorFt / FT_PER_M / 100;
    cyl.scale.set(R, y, R); cyl.position.set(state.x, y / 2, 0);
    disc.scale.set(R, R, 1); disc.position.set(state.x, 0.02, 0);
    floorDisc.scale.set(R, R, 1); floorDisc.position.set(state.x, fy, 0);
    floorDisc.material.color.set(state.alt >= r.floorFt ? c.ok : c.bad);
    plane.group.position.set(state.x, y, 0);
    drop.geometry.setFromPoints([new THREE.Vector3(state.x, 0, 0), new THREE.Vector3(state.x, y, 0)]); drop.computeLineDistances();
    radiusLabel.position.set(state.x, 0.6, R + 1.2);
    label(radiusLabel, `${r.radiusM} m radius`, c.brand);
    for (const m of meshes) { const o = m.userData.obstacle; const hot = o === r.highest; m.material.emissive = new THREE.Color(hot ? c.bad : 0x000000); m.material.emissiveIntensity = hot ? 0.6 : 0; }
    const legal = state.alt >= r.floorFt;
    setText(outs, "where", r.populous ? "over a populous area (the town)" : "over open country", r.populous ? "warn" : "ok");
    setText(outs, "rule", r.rule);
    setText(outs, "highest", r.highest.h > 0 ? `${r.highest.name || r.highest.kind}: ${Math.round(r.highest.h)} m (${Math.round(r.highest.h * FT_PER_M)} ft) within ${r.radiusM} m` : `nothing within ${r.radiusM} m: the surface`);
    setText(outs, "floor", `${r.floorFt.toLocaleString("en-AU")} ft above the ground datum (${r.aboveFt.toLocaleString("en-AU")} ft + the obstacle)`);
    setText(outs, "alt", `${state.alt.toLocaleString("en-AU")} ft: ${legal ? `${(state.alt - r.floorFt).toLocaleString("en-AU")} ft above the floor` : `${(r.floorFt - state.alt).toLocaleString("en-AU")} ft BELOW the minimum`}`, legal ? "ok" : "bad");
    el.querySelectorAll("[data-flag='low']").forEach((f) => { f.style.display = legal ? "none" : ""; });
  });
  stage.onTick((t, reduced) => { if (!reduced) plane.prop.rotation.x = t * 14; });
};

/* ------------------------------------------------------------------ explorer: the gyroscope (BAKC 3.5)
   Rigidity: the spinning rotor's axis holds its direction while the case (the aeroplane) rolls and pitches around it on
   its gimbals. Precession: a force on the rim acts 90° further round in the direction of rotation. Rim angles are
   measured from the nose (+x) towards the right wing (+z); spin "clockwise" means clockwise seen from above. */
export function precessionResponse(pushAtDeg, clockwiseFromAbove = true) {
  const response = ((pushAtDeg + (clockwiseFromAbove ? 90 : -90)) % 360 + 360) % 360;
  const where = (a) => a === 0 ? "the front" : a === 90 ? "the right side" : a === 180 ? "the back" : a === 270 ? "the left side" : `${a}° round`;
  return { pushAt: pushAtDeg, responseAt: response, text: `a push down at ${where(pushAtDeg)} tilts the rotor as if pushed at ${where(response)}: 90° on, in the direction of rotation` };
}

EXPLORERS.gyro = function ({ THREE, OrbitControls }, el) {
  const stage = createStage(THREE, OrbitControls, el, { camera: [7, 5, 9] });
  stage.controls.maxDistance = 25;
  stage.controls.minDistance = 4;
  const c = stage.colours;
  const scene = stage.scene;
  const metal = new THREE.MeshStandardMaterial({ color: c.dark ? c.fgMuted : c.lineStrong, roughness: 0.4, metalness: 0.3 });
  const brand = new THREE.MeshStandardMaterial({ color: c.brand, roughness: 0.5 });
  // the case: a wireframe box with the aeroplane symbol, rolled and pitched by the sliders
  const caseGroup = new THREE.Group();
  caseGroup.rotation.order = "XZY";
  scene.add(caseGroup);
  caseGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(5.6, 4.4, 5.6)), new THREE.LineBasicMaterial({ color: c.fgMuted })));
  const plane = makePlane(THREE, c);
  plane.group.scale.setScalar(0.42);
  plane.group.position.set(0, -3.2, 0);
  caseGroup.add(plane.group);
  const caseLabel = makeLabel(THREE, "the aeroplane and the instrument case", c.fgMuted, 1.3);
  caseLabel.position.set(0, 2.9, 0);
  caseGroup.add(caseLabel);
  // outer gimbal (pivots on the case's longitudinal axis), inner gimbal (pivots on the outer's lateral axis), rotor inside
  const outer = new THREE.Group();
  caseGroup.add(outer);
  const outerRing = new THREE.Mesh(new THREE.TorusGeometry(2.4, 0.07, 8, 48), metal);
  outerRing.rotation.y = Math.PI / 2;      // ring in the y-z plane, its pivot along x
  outer.add(outerRing);
  for (const s of [-1, 1]) { const pin = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.5, 8), metal); pin.rotation.z = Math.PI / 2; pin.position.x = s * 2.6; outer.add(pin); }
  const inner = new THREE.Group();
  outer.add(inner);
  const innerRing = new THREE.Mesh(new THREE.TorusGeometry(1.9, 0.07, 8, 48), metal);
  inner.add(innerRing);                    // ring in the x-y plane, its pivot along z
  for (const s of [-1, 1]) { const pin = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.5, 8), metal); pin.rotation.x = Math.PI / 2; pin.position.z = s * 2.1; inner.add(pin); }
  const rotorTilt = new THREE.Group();     // precession tilts this
  inner.add(rotorTilt);
  const rotor = new THREE.Group();
  rotorTilt.add(rotor);
  const disc = new THREE.Mesh(new THREE.CylinderGeometry(1.4, 1.4, 0.35, 40), metal);
  rotor.add(disc);
  for (let k = 0; k < 4; k++) { const spoke = new THREE.Mesh(new THREE.BoxGeometry(2.7, 0.4, 0.12), brand); spoke.rotation.y = k * Math.PI / 4; rotor.add(spoke); }
  const axle = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 4.2, 10), brand);
  rotorTilt.add(axle);
  const axisLine = dashedLine(THREE, v3(THREE, [0, -5, 0], [0, 5, 0]), c.brand, 0.3, 0.2);
  rotorTilt.add(axisLine);
  const axisLabel = makeLabel(THREE, "spin axis: rigid in space", c.brand, 1.2);
  axisLabel.position.set(0, 5.6, 0);
  rotorTilt.add(axisLabel);
  const spinArrow = new THREE.Mesh(new THREE.ConeGeometry(0.16, 0.4, 10), brand);
  spinArrow.position.set(1.6, 0, 0);
  rotor.add(spinArrow);
  const push = new THREE.ArrowHelper(new THREE.Vector3(0, -1, 0), new THREE.Vector3(1.4, 1.6, 0), 1.3, c.warn, 0.45, 0.25);
  const acts = new THREE.ArrowHelper(new THREE.Vector3(0, -1, 0), new THREE.Vector3(0, 1.6, 1.4), 1.3, c.bad, 0.45, 0.25);
  push.visible = acts.visible = false;
  inner.add(push, acts);
  const pushLabel = makeLabel(THREE, "push here", c.warn, 1.1), actsLabel = makeLabel(THREE, "it acts here: 90° on", c.bad, 1.1);
  pushLabel.visible = actsLabel.visible = false;
  inner.add(pushLabel, actsLabel);
  // a heading card for the DI drift idea: an index on the case against a ring on the rotor assembly
  const card = new THREE.Mesh(new THREE.TorusGeometry(3.2, 0.03, 6, 72), new THREE.MeshBasicMaterial({ color: c.fgFaint }));
  card.rotation.x = Math.PI / 2; card.position.y = -2.2;
  scene.add(card);
  const north = makeLabel(THREE, "N", c.fg, 0.9);
  north.position.set(0, -2.1, -3.4);
  scene.add(north);
  const lubber = new THREE.Mesh(new THREE.ConeGeometry(0.15, 0.4, 8), new THREE.MeshStandardMaterial({ color: c.fg }));
  lubber.rotation.x = -Math.PI / 2; lubber.position.set(0, -2.2, -2.7);
  caseGroup.add(lubber);
  const driftLabel = makeLabel(THREE, "", c.fgMuted, 1.3);
  driftLabel.position.set(0, -2.9, 3.4);
  scene.add(driftLabel);
  function setLabel(sprite, text, colour) {
    const canvas = sprite.material.map.image, ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = "600 56px 'Inter Variable', system-ui, sans-serif"; ctx.fillStyle = colour; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(text, 256, 64);
    sprite.material.map.needsUpdate = true;
  }

  const params = {};
  const state = { roll: 0, pitch: 0, push: false, pushAt: 0, cw: true, minutes: 0, tilt: 0 };
  wireControls(el, params, (p, outs) => {
    state.roll = p.roll; state.pitch = p.pitch; state.push = !!p.push; state.pushAt = p.pushAt || 0; state.cw = !p.reverse; state.minutes = p.minutes || 0;
    const r = precessionResponse(state.pushAt, state.cw);
    const a = state.pushAt * Math.PI / 180, b = r.responseAt * Math.PI / 180;
    push.position.set(1.4 * Math.cos(a), 1.6, 1.4 * Math.sin(a));
    pushLabel.position.set(2.2 * Math.cos(a), 2.3, 2.2 * Math.sin(a));
    acts.position.set(1.4 * Math.cos(b), 1.6, 1.4 * Math.sin(b));
    actsLabel.position.set(2.4 * Math.cos(b), 2.3, 2.4 * Math.sin(b));
    push.visible = pushLabel.visible = acts.visible = actsLabel.visible = state.push;
    spinArrow.rotation.z = state.cw ? -Math.PI / 2 : Math.PI / 2;
    setText(outs, "attitude", `roll ${state.roll}°, pitch ${state.pitch}°: the case moves, the rotor axis does not`);
    setText(outs, "precession", state.push ? r.text : "push on the rim to see precession");
    setText(outs, "spin", state.cw ? "clockwise seen from above" : "anticlockwise seen from above");
    const driftDeg = Math.round(state.minutes * 0.4);   // illustrative rate: the lesson gives none
    setText(outs, "drift", state.minutes === 0 ? "just set to the compass" : `${state.minutes} min since set: the DI reads ${driftDeg}° off (friction and the Earth's rotation)`, state.minutes > 15 ? "bad" : state.minutes > 10 ? "warn" : "ok");
    el.querySelectorAll("[data-flag='reset']").forEach((f) => { f.style.display = state.minutes >= 10 ? "" : "none"; });
    setLabel(driftLabel, state.minutes === 0 ? "heading card: set to the compass" : `heading card: ${driftDeg}° of drift after ${state.minutes} min`, state.minutes > 15 ? c.bad : c.fgMuted);
    card.rotation.y = -driftDeg * Math.PI / 180;
    north.position.set(3.4 * Math.sin(driftDeg * Math.PI / 180), -2.1, -3.4 * Math.cos(driftDeg * Math.PI / 180));
  });
  const rad = (d) => d * Math.PI / 180;
  stage.onTick((t, reduced) => {
    caseGroup.rotation.x = rad(state.roll);
    caseGroup.rotation.z = rad(state.pitch);
    outer.rotation.z = -rad(state.pitch);           // the gimbals turn so the rotor axis stays put (rigidity)
    inner.rotation.x = -rad(state.roll);
    state.tilt = lerp(state.tilt, state.push ? rad(18) : 0, reduced ? 1 : 0.08);
    const b = precessionResponse(state.pushAt, state.cw).responseAt * Math.PI / 180;
    const P = new THREE.Vector3(Math.cos(b), 0, Math.sin(b));
    rotorTilt.quaternion.setFromAxisAngle(P.clone().cross(new THREE.Vector3(0, 1, 0)).normalize(), -state.tilt);
    if (!reduced) rotor.rotation.y += (state.cw ? -1 : 1) * 0.12;
  });
};

/* ------------------------------------------------------------------ mounting */
function mount(el) {
  const name = el.dataset.explorer;
  const holder = el.querySelector("[data-canvas]") || el;
  const canvasTest = document.createElement("canvas");
  const gl = canvasTest.getContext("webgl2") || canvasTest.getContext("webgl");
  if (!gl) {
    holder.innerHTML = '<p class="widget-fallback">This 3D view needs WebGL, which your browser has turned off. The diagrams and lesson text above cover the same points.</p>';
    return;
  }
  if (!EXPLORERS[name]) { console.warn("unknown explorer", name); return; }
  loadThree().then((three) => EXPLORERS[name](three, el)).catch((err) => {
    console.error("explorer failed", err);
    holder.innerHTML = '<p class="widget-fallback">The 3D view could not start.</p>';
  });
}

/* The scenes take their colours from the CSS tokens when built, so a theme change rebuilds them. The controls
   are swapped for clean copies (keeping their values) so the new scene's listeners are the only ones. */
function remount(el) {
  if (el._casaStage) el._casaStage.dispose();
  el._casaStage = null;
  el.querySelectorAll("[data-param], [data-action], [data-set]").forEach((n) => {
    const copy = n.cloneNode(true);
    if (n.type === "checkbox") copy.checked = n.checked;
    else if (n.tagName === "INPUT") copy.value = n.value;
    n.replaceWith(copy);
  });
  mount(el);
}
function retheme() {
  document.querySelectorAll("[data-widget='explorer'][data-widget-mounted]").forEach((el) => { if (el._casaStage) remount(el); });
}

if (typeof window !== "undefined") {
  document.addEventListener("casa:themechange", retheme);
  matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", () => { if (!document.documentElement.dataset.theme) retheme(); });
  if (window.CasaWidgets) window.CasaWidgets.register("explorer", mount);
  else document.addEventListener("DOMContentLoaded", () => window.CasaWidgets && window.CasaWidgets.register("explorer", mount));
}
