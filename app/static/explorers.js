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
    warn: get("warn"), bad: get("bad"), skySoft: get("sky-soft"), skyFg: get("sky-fg"),
    dark: matchMedia("(prefers-color-scheme: dark)").matches,
  };
}

/* ------------------------------------------------------------------ the aeroplane
   Axes: +X nose, +Y up, +Z right wing. Length ~7.5, span 10. Parts with hinges are Groups whose rotation
   is set by the explorers (aileronL/R, elevator, rudder: rotation about the hinge; prop: rotation.x). */
export function makePlane(THREE, c) {
  const body = new THREE.MeshStandardMaterial({ color: c.dark ? c.fgMuted : c.surface, roughness: 0.55, metalness: 0.05 });
  const edge = new THREE.MeshStandardMaterial({ color: c.fg, roughness: 0.6 });
  const control = new THREE.MeshStandardMaterial({ color: c.brand, roughness: 0.5 });
  const glass = new THREE.MeshStandardMaterial({ color: c.skyFg, roughness: 0.2, transparent: true, opacity: 0.55 });
  const plane = new THREE.Group();
  const parts = { materials: { body, edge, control, glass } };

  // fuselage: lathe profile (radius, station), station measured along +X
  const profile = [[0.02, 3.3], [0.32, 2.7], [0.55, 1.7], [0.6, 0.6], [0.5, -0.8], [0.32, -2.3], [0.17, -3.7], [0.1, -4.3], [0.0, -4.35]]
    .map(([r, x]) => new THREE.Vector2(r, x));
  const fuselage = new THREE.Mesh(new THREE.LatheGeometry(profile, 32), body);
  fuselage.rotation.z = -Math.PI / 2;      // lathe axis Y -> +X
  plane.add(fuselage);

  const canopy = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2), glass);
  canopy.scale.set(1.0, 0.5, 0.52);
  canopy.position.set(0.9, 0.45, 0);
  plane.add(canopy);

  const slab = (w, h, d, mat) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  const planform = (pts, thickness, mat) => {    // pts in (x, z); extruded thickness along y
    const shape = new THREE.Shape(pts.map(([x, z]) => new THREE.Vector2(x, z)));
    const geo = new THREE.ExtrudeGeometry(shape, { depth: thickness, bevelEnabled: false });
    geo.rotateX(Math.PI / 2);            // shape plane (x, y=z) -> (x, z), depth along -y
    geo.translate(0, thickness / 2, 0);
    return new THREE.Mesh(geo, mat);
  };

  // wing (main part; trailing edge cut back 0.3 for flaps and ailerons)
  const wing = planform([[0.9, -0.55], [0.6, -5.0], [0.0, -5.0], [-0.3, -0.55], [-0.3, 0.55], [0.0, 5.0], [0.6, 5.0], [0.9, 0.55]], 0.11, body);
  wing.position.y = -0.3;
  plane.add(wing);
  const hinged = (mesh, x, y, z, name) => {
    const g = new THREE.Group();
    g.position.set(x, y, z);
    mesh.position.x = -0.16;
    g.add(mesh);
    plane.add(g);
    parts[name] = g;
    return g;
  };
  hinged(slab(0.34, 0.07, 1.75, control), -0.09, -0.3, -4.05, "aileronL");
  hinged(slab(0.34, 0.07, 1.75, control), -0.09, -0.3, 4.05, "aileronR");
  hinged(slab(0.34, 0.07, 2.2, body), -0.21, -0.3, -1.75, "flapL");
  hinged(slab(0.34, 0.07, 2.2, body), -0.21, -0.3, 1.75, "flapR");

  // tailplane and elevator
  const tail = planform([[-3.2, -0.15], [-3.55, -1.9], [-3.85, -1.9], [-3.9, -0.15], [-3.9, 0.15], [-3.85, 1.9], [-3.55, 1.9], [-3.2, 0.15]], 0.08, body);
  tail.position.y = 0.1;
  plane.add(tail);
  hinged(slab(0.34, 0.06, 3.7, control), -3.88, 0.1, 0, "elevator");

  // fin and rudder (shape in the x-y plane)
  const finShape = new THREE.Shape([[-2.9, 0.15], [-3.6, 1.55], [-3.95, 1.55], [-3.95, 0.15]].map(([x, y]) => new THREE.Vector2(x, y)));
  const finGeo = new THREE.ExtrudeGeometry(finShape, { depth: 0.08, bevelEnabled: false });
  finGeo.translate(0, 0, -0.04);
  plane.add(new THREE.Mesh(finGeo, body));
  const rudder = new THREE.Group();
  rudder.position.set(-3.95, 0.85, 0);
  const rudderMesh = slab(0.34, 1.35, 0.06, control);
  rudderMesh.position.x = -0.16;
  rudder.add(rudderMesh);
  plane.add(rudder);
  parts.rudder = rudder;

  // propeller and spinner
  const prop = new THREE.Group();
  prop.position.x = 3.32;
  const blade = slab(0.06, 2.1, 0.16, edge);
  prop.add(blade);
  const spinner = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.45, 16), edge);
  spinner.rotation.z = -Math.PI / 2;
  spinner.position.x = 0.2;
  prop.add(spinner);
  plane.add(prop);
  parts.prop = prop;

  // undercarriage
  const wheelGeo = new THREE.CylinderGeometry(0.24, 0.24, 0.14, 20);
  const legGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.6, 8);
  for (const [x, z] of [[0.3, -1.1], [0.3, 1.1], [2.3, 0]]) {
    const wheel = new THREE.Mesh(wheelGeo, edge);
    wheel.rotation.x = Math.PI / 2;
    wheel.position.set(x, -1.0, z);
    const leg = new THREE.Mesh(legGeo, edge);
    leg.position.set(x, -0.7, z * 0.9);
    plane.add(wheel, leg);
  }
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
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.enablePan = false;
  controls.minDistance = 6;
  controls.maxDistance = 30;
  controls.target.set(0, 0, 0);
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
  new ResizeObserver(resize).observe(holder);

  let visible = true, running = false, tick = null;
  new IntersectionObserver((entries) => { visible = entries[0].isIntersecting; if (visible) start(); }, { threshold: 0.05 }).observe(holder);
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  function frame(t) {
    if (!visible || !holder.isConnected) { running = false; return; }
    controls.update();
    tick && tick(t / 1000, reduced.matches);
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  function start() { if (!running) { running = true; requestAnimationFrame(frame); } }
  start();
  return { renderer, scene, camera, controls, colours: c, holder, onTick(fn) { tick = fn; }, start };
}

function wireControls(el, params, onChange) {
  const outs = {};
  el.querySelectorAll("[data-out]").forEach((o) => { outs[o.dataset.out] = o; });
  const inputs = el.querySelectorAll("[data-param]");
  const defaults = {};
  inputs.forEach((inp) => {
    const k = inp.dataset.param;
    defaults[k] = inp.type === "checkbox" ? inp.checked : Number(inp.value);
    params[k] = defaults[k];
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
  const chord = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-5, -0.3, 0), new THREE.Vector3(8, -0.3, 0)]),
    new THREE.LineDashedMaterial({ color: c.brand, dashSize: 0.4, gapSize: 0.25 }));
  chord.computeLineDistances();
  plane.group.add(chord);
  const chordLabel = makeLabel(THREE, "chord line · attitude", c.brand, 0.8);
  chordLabel.position.set(8.5, 0.4, 0);
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
      const start = new THREE.Vector3().addScaledVector(fwd, 0.75).addScaledVector(up, -0.12).setZ(z);
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

/* ------------------------------------------------------------------ mounting */
function mount(el) {
  const name = el.dataset.explorer;
  const holder = el.querySelector("[data-canvas]") || el;
  const canvasTest = document.createElement("canvas");
  const gl = canvasTest.getContext("webgl2") || canvasTest.getContext("webgl");
  if (!gl) {
    holder.innerHTML = '<p class="widget-fallback">This 3D view needs WebGL, which your browser has turned off. The diagrams and notes above cover the same points.</p>';
    return;
  }
  if (!EXPLORERS[name]) { console.warn("unknown explorer", name); return; }
  loadThree().then((three) => EXPLORERS[name](three, el)).catch((err) => {
    console.error("explorer failed", err);
    holder.innerHTML = '<p class="widget-fallback">The 3D view could not start.</p>';
  });
}

if (typeof window !== "undefined") {
  if (window.CasaWidgets) window.CasaWidgets.register("explorer", mount);
  else document.addEventListener("DOMContentLoaded", () => window.CasaWidgets && window.CasaWidgets.register("explorer", mount));
}
