/* Student annotations on a lesson: text highlights, typed notes and Apple Pencil ink (over the lesson and on a
   sketch pad). Loaded as a module on every page; it does nothing until a lesson mounts the widgets
   (data-widget="lesson-annotations" | "lesson-notes" | "lesson-sketch", see note.html and the panel partials).

   Anchoring. Lesson HTML is regenerated at every start, so a highlight is stored as a W3C TextQuoteSelector
   (exact + prefix/suffix) with a TextPositionSelector fast path, computed over a "text map" of the article that
   skips figures, widgets and maths wrappers (.arithmatex). KaTeX only replaces the inside of those wrappers, so
   the map is identical before and after maths rendering. Ink over the lesson is anchored to the top-level block
   (paragraph, figure, table …) it was drawn on, with points as fractions of that block's box, so it stays on
   its paragraph when the column reflows. The sketch pad uses absolute units in a fixed 1000 × 1400 page.

   Everything here is exported for tests/js/anchor.test.mjs; the browser only needs the side effects at the end. */
import { getStroke } from "perfect-freehand";

/* ------------------------------------------------------------------ text map and selectors */
export const EXCLUDE = "figure.visual, .visual-widget, .widget, .arithmatex, .katex, script, style, noscript, template, .ink-layer, .hl-bar, .hl-popover";
const CONTEXT = 32;

/** Flattened text of `root` (minus excluded subtrees) with the text nodes that make it up. */
export function textMap(root) {
  const nodes = [];
  let text = "";
  const doc = root.ownerDocument;
  const walker = doc.createTreeWalker(root, 4 /* SHOW_TEXT */, {
    acceptNode(n) {
      const p = n.parentElement;
      if (!p) return 2;
      const ex = p.closest(EXCLUDE);
      return ex && root.contains(ex) ? 2 /* REJECT */ : 1 /* ACCEPT */;
    },
  });
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const start = text.length;
    text += n.data;
    nodes.push({ node: n, start, end: text.length });
  }
  return { text, nodes };
}

/** Map offset in the flattened text to the text node that holds it. `end` picks the node ending there. */
export function offsetToPoint(map, offset, end = false) {
  const { nodes } = map;
  let lo = 0, hi = nodes.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1, e = nodes[mid];
    if (offset < e.start) hi = mid - 1;
    else if (offset > e.end || (offset === e.end && !end && mid < nodes.length - 1)) lo = mid + 1;
    else return { node: e.node, offset: offset - e.start };
  }
  if (!nodes.length) return null;
  const last = nodes[nodes.length - 1];
  return { node: last.node, offset: Math.max(0, Math.min(last.node.data.length, offset - last.start)) };
}

/** Map a DOM point (node, offset) to a flattened-text offset, or -1 when it falls in an excluded subtree. */
export function pointToOffset(map, node, offset) {
  if (node.nodeType === 3) {
    const e = map.nodes.find((x) => x.node === node);
    return e ? e.start + Math.min(offset, node.data.length) : -1;
  }
  // Element: the offset counts children; the point is just before child[offset] (or at the end).
  const child = node.childNodes[offset];
  if (child) {
    for (const e of map.nodes) if (child === e.node || child.contains(e.node)) return e.start;
    // No text inside the child: the first mapped node after it in document order.
    for (const e of map.nodes) if (child.compareDocumentPosition(e.node) & 4 /* FOLLOWING */) return e.start;
    return map.text.length;
  }
  for (let i = map.nodes.length - 1; i >= 0; i--) if (node.contains(map.nodes[i].node)) return map.nodes[i].end;
  for (const e of map.nodes) if (node.compareDocumentPosition(e.node) & 4) return e.start;
  return map.text.length;
}

/** Stable-ish id of the top-level block holding a node: "<index>:<tag>:<first words>". */
export function blockOf(root, node) {
  let el = node.nodeType === 1 ? node : node.parentElement;
  while (el && el.parentElement !== root) el = el.parentElement;
  return el;
}
export function blockFingerprint(el) {
  const words = (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 30).toLowerCase().replace(/[^a-z0-9 ]+/g, "").trim().replace(/ /g, "-");
  return `${el.tagName.toLowerCase()}:${words}`;
}
export function blockId(root, el) {
  const i = Array.prototype.indexOf.call(root.children, el);
  return `${i}:${blockFingerprint(el)}`.slice(0, 80);
}

/** Describe a DOM Range inside root as a selector, or null when it does not cover article text. */
export function describeRange(root, range, map = textMap(root)) {
  const start = pointToOffset(map, range.startContainer, range.startOffset);
  const end = pointToOffset(map, range.endContainer, range.endOffset);
  if (start < 0 || end < 0 || end <= start) return null;
  const exact = map.text.slice(start, end);
  if (!exact.trim()) return null;
  const block = blockOf(root, range.startContainer);
  return {
    exact, start, end,
    prefix: map.text.slice(Math.max(0, start - CONTEXT), start),
    suffix: map.text.slice(end, end + CONTEXT),
    block_id: block ? blockId(root, block) : null,
  };
}

function contextScore(text, at, len, sel) {
  const pre = text.slice(Math.max(0, at - CONTEXT), at), suf = text.slice(at + len, at + len + CONTEXT);
  let s = 0;
  for (let i = 1; i <= Math.min(pre.length, sel.prefix.length); i++) { if (pre[pre.length - i] === sel.prefix[sel.prefix.length - i]) s++; else break; }
  for (let i = 0; i < Math.min(suf.length, sel.suffix.length); i++) { if (suf[i] === sel.suffix[i]) s++; else break; }
  return s;
}

/** Find the selector's text again: exact position, then every exact match ranked by context, then a
    whitespace-normalised search. Returns {start, end} offsets in the map, or null. */
export function resolveSelector(map, sel) {
  const { text } = map, exact = sel.exact || "";
  if (!exact) return null;
  if (typeof sel.start === "number" && text.slice(sel.start, sel.start + exact.length) === exact) return { start: sel.start, end: sel.start + exact.length };
  const hits = [];
  for (let i = text.indexOf(exact); i >= 0; i = text.indexOf(exact, i + 1)) hits.push(i);
  if (hits.length) {
    let best = hits[0], bestScore = -1;
    for (const h of hits) {
      const s = contextScore(text, h, exact.length, sel) * 1000 - (typeof sel.start === "number" ? Math.abs(h - sel.start) / 1000 : 0);
      if (s > bestScore) { bestScore = s; best = h; }
    }
    return { start: best, end: best + exact.length };
  }
  // Whitespace may have changed (a rewrapped paragraph): compare with runs of whitespace collapsed.
  const norm = [], idx = [];
  let lastSpace = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i], sp = /\s/.test(ch);
    if (sp && lastSpace) continue;
    norm.push(sp ? " " : ch); idx.push(i); lastSpace = sp;
  }
  const ntext = norm.join(""), nexact = exact.replace(/\s+/g, " ").trim();
  if (!nexact) return null;
  const at = ntext.indexOf(nexact);
  if (at < 0) return null;
  return { start: idx[at], end: idx[at + nexact.length - 1] + 1 };
}

/** Wrap the text between offsets in <mark class="hl hl-<colour>" data-hl="id">, never crossing element boundaries. */
export function applyHighlight(root, offsets, h, map = textMap(root)) {
  const doc = root.ownerDocument, marks = [];
  const segs = [];
  for (const e of map.nodes) {
    if (e.end <= offsets.start || e.start >= offsets.end) continue;
    segs.push({ node: e.node, from: Math.max(0, offsets.start - e.start), to: Math.min(e.node.data.length, offsets.end - e.start) });
  }
  for (const s of segs) {
    if (s.to <= s.from) continue;
    let n = s.node;
    if (s.from > 0) n = n.splitText(s.from);
    if (s.to - s.from < n.data.length) n.splitText(s.to - s.from);
    if (!n.data.trim() && segs.length > 1) continue;   // whitespace-only slivers between elements
    const mark = doc.createElement("mark");
    mark.className = `hl hl-${h.colour}`;
    mark.dataset.hl = String(h.id);
    if (h.comment) mark.title = h.comment;
    n.parentNode.insertBefore(mark, n);
    mark.appendChild(n);
    marks.push(mark);
  }
  return marks;
}

export function removeHighlight(root, id) {
  root.querySelectorAll(`mark.hl[data-hl="${id}"]`).forEach((m) => {
    const parent = m.parentNode;
    while (m.firstChild) parent.insertBefore(m.firstChild, m);
    parent.removeChild(m);
    parent.normalize();
  });
}

export function recolourHighlight(root, id, colour, comment) {
  root.querySelectorAll(`mark.hl[data-hl="${id}"]`).forEach((m) => {
    m.className = `hl hl-${colour}`;
    if (comment) m.title = comment; else m.removeAttribute("title");
  });
}

/** Text of the nearest h2 before a node (for the highlight list). */
export function headingBefore(root, node) {
  let el = node.nodeType === 1 ? node : node.parentElement;
  while (el && el.parentElement !== root) el = el.parentElement;
  for (; el; el = el.previousElementSibling) if (/^H[23]$/.test(el.tagName)) return el.textContent.trim();
  return "";
}

/* ------------------------------------------------------------------ ink geometry */
const INK_OPTIONS = { size: 4, thinning: 0.55, smoothing: 0.5, streamline: 0.45, last: true };

/** Outline polygon (perfect-freehand) → SVG path with quadratic joins. */
export function outlinePath(points, size, hasPressure) {
  if (!points.length) return "";
  const poly = getStroke(points, { ...INK_OPTIONS, size, simulatePressure: !hasPressure });
  if (!poly.length) return "";
  const n = poly.length;
  let d = `M${poly[0][0].toFixed(1)} ${poly[0][1].toFixed(1)}`;
  for (let i = 0; i < n; i++) {
    const [x0, y0] = poly[i], [x1, y1] = poly[(i + 1) % n];
    d += ` Q${x0.toFixed(1)} ${y0.toFixed(1)} ${((x0 + x1) / 2).toFixed(1)} ${((y0 + y1) / 2).toFixed(1)}`;
  }
  return d + " Z";
}

/** Drop points closer than `tol` to the previous kept point (pressure kept from the dropped run's max). */
export function simplify(points, tol = 0.75) {
  if (points.length < 3) return points;
  const out = [points[0]];
  for (let i = 1; i < points.length - 1; i++) {
    const last = out[out.length - 1], p = points[i];
    if (Math.hypot(p[0] - last[0], p[1] - last[1]) < tol) { last[2] = Math.max(last[2], p[2]); continue; }
    out.push(p.slice());
  }
  out.push(points[points.length - 1]);
  return out;
}

/** Distance from (x, y) to a polyline, early-out when below `limit`. */
export function hitStroke(pts, x, y, limit) {
  if (pts.length === 1) return Math.hypot(pts[0][0] - x, pts[0][1] - y) <= limit;
  for (let i = 1; i < pts.length; i++) {
    const [ax, ay] = pts[i - 1], [bx, by] = pts[i];
    const dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy;
    const t = l2 ? Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / l2)) : 0;
    if (Math.hypot(ax + t * dx - x, ay + t * dy - y) <= limit) return true;
  }
  return false;
}

/** Which pointers draw. Overlay: a pen draws when "pen draws" is armed; fingers scroll; mouse and finger draw
    only in explicit draw mode. The sketch pad draws with pen and mouse always, finger only in draw mode. */
export function shouldDraw(ev, policy) {
  if (!policy.tool || policy.tool === "none") return null;
  const type = ev.pointerType || "mouse";
  const want = policy.tool === "erase" ? "erase" : "draw";
  if (type === "pen") return policy.penDraws === false ? null : want;
  if (type === "touch") return policy.drawMode ? want : null;
  if (policy.sketch) return want;             // mouse on the pad
  return policy.drawMode ? want : null;       // mouse over the lesson
}

const INK_COLOURS = ["ink-1", "ink-2", "ink-3", "ink-4"];
let strokeSeq = 0;
export function newStrokeId() { return `${Date.now().toString(36)}-${(strokeSeq++).toString(36)}`; }

/* ------------------------------------------------------------------ InkSurface: pointer events → strokes → SVG */
export class InkSurface {
  /** opts: { host, svg, policy(), toSurface(clientX, clientY) → [x, y], unitScale() → surface units per CSS px,
      encode(ptsSurface, colour, width, hasPressure) → stored stroke | null, decode(stroke) → surface pts | null,
      onChange(), onOrphans(count) } */
  constructor(opts) {
    Object.assign(this, { strokes: [], undoStack: [], redoStack: [], live: null, hasPressure: false, orphans: 0 }, opts);
    this.colour = INK_COLOURS[0];
    this.width = 3;
    this.svg.classList.add("ink-layer");
    this.layer = this.svg.ownerDocument.createElementNS("http://www.w3.org/2000/svg", "g");
    this.liveEl = this.svg.ownerDocument.createElementNS("http://www.w3.org/2000/svg", "path");
    this.liveEl.setAttribute("class", "ink-live");
    this.svg.append(this.layer, this.liveEl);
    this._down = this._down.bind(this); this._move = this._move.bind(this); this._up = this._up.bind(this);
    this._touch = this._touch.bind(this);
    this.host.addEventListener("pointerdown", this._down, true);
    this.host.addEventListener("pointermove", this._move, true);
    this.host.addEventListener("pointerup", this._up, true);
    this.host.addEventListener("pointercancel", this._up, true);
    // Safari gives the Pencil touch events that scroll the page; touch-action cannot tell a stylus from a finger.
    this.host.addEventListener("touchstart", this._touch, { passive: false, capture: true });
    this.host.addEventListener("touchmove", this._touch, { passive: false, capture: true });
  }
  destroy() {
    this.host.removeEventListener("pointerdown", this._down, true);
    this.host.removeEventListener("pointermove", this._move, true);
    this.host.removeEventListener("pointerup", this._up, true);
    this.host.removeEventListener("pointercancel", this._up, true);
    this.host.removeEventListener("touchstart", this._touch, true);
    this.host.removeEventListener("touchmove", this._touch, true);
    this.layer.remove(); this.liveEl.remove();
  }
  load(strokes) { this.strokes = (strokes || []).map((s) => ({ ...s })); this.undoStack = []; this.redoStack = []; this.render(); }
  get canUndo() { return this.undoStack.length > 0; }
  get canRedo() { return this.redoStack.length > 0; }

  _touch(ev) {
    const touches = Array.from(ev.changedTouches || []);
    if (!touches.length || !touches.every((t) => t.touchType === "stylus")) return;
    const p = this.policy();
    if (p.tool && p.tool !== "none" && p.penDraws !== false) ev.preventDefault();
  }
  _down(ev) {
    if (this.live || ev.button > 0) return;
    const mode = shouldDraw(ev, this.policy());
    if (!mode) return;
    ev.preventDefault(); ev.stopPropagation();
    const sel = this.host.ownerDocument.getSelection && this.host.ownerDocument.getSelection();
    if (sel && !sel.isCollapsed) sel.removeAllRanges();
    this.host.classList.add("is-drawing");
    try { this.host.setPointerCapture(ev.pointerId); } catch (e) {}
    this.live = { id: ev.pointerId, mode, pts: [], pressure: ev.pressure > 0 && ev.pressure !== 0.5, erased: new Set() };
    this._add(ev);
    if (mode === "erase") this._eraseAt(ev);
  }
  _move(ev) {
    if (!this.live || ev.pointerId !== this.live.id) return;
    ev.preventDefault(); ev.stopPropagation();
    const events = ev.getCoalescedEvents ? ev.getCoalescedEvents() : [ev];
    for (const e of events.length ? events : [ev]) this._add(e);
    if (this.live.mode === "erase") this._eraseAt(ev);
    else this._scheduleLive();
  }
  _up(ev) {
    if (!this.live || ev.pointerId !== this.live.id) return;
    ev.preventDefault(); ev.stopPropagation();
    if (ev.type === "pointerup") this._add(ev);
    try { this.host.releasePointerCapture(ev.pointerId); } catch (e) {}
    this.host.classList.remove("is-drawing");
    const live = this.live;
    this.live = null;
    this.liveEl.removeAttribute("d");
    if (live.mode === "draw" && this._isTap(live, ev)) return;
    if (live.mode === "draw") {
      const pts = simplify(live.pts, 0.6 * this.unitScale());
      const stroke = this.encode(pts, this.colour, this.width * this.unitScale(), live.pressure);
      if (stroke) { stroke.id = stroke.id || newStrokeId(); this.strokes.push(stroke); this.undoStack.push({ type: "add", stroke }); this.redoStack = []; this.render(); this.onChange && this.onChange(); }
    } else if (live.erased.size) {
      this.redoStack = [];
      this.onChange && this.onChange();
    }
  }
  /** A tap (no movement) on something interactive under the layer clicks it rather than leaving a dot. */
  _isTap(live, ev) {
    if (live.pts.length > 6) return false;
    const xs = live.pts.map((p) => p[0]), ys = live.pts.map((p) => p[1]);
    if ((Math.max(...xs) - Math.min(...xs) + Math.max(...ys) - Math.min(...ys)) > 4 * this.unitScale()) return false;
    const doc = this.host.ownerDocument;
    const under = doc.elementsFromPoint ? doc.elementsFromPoint(ev.clientX, ev.clientY) : [doc.elementFromPoint(ev.clientX, ev.clientY)];
    const target = under.map((el) => el && el.closest && el.closest("a, button, summary, input, select, textarea, label, [role=button], mark.hl")).find(Boolean);
    if (!target || !this.host.contains(target)) return false;
    if (target.matches("input[type=range]")) return false;   // a slider needs a drag: let the dot go instead
    setTimeout(() => { if (target.matches("input, select, textarea")) target.focus(); else target.click(); }, 0);
    return true;
  }
  _add(ev) {
    const [x, y] = this.toSurface(ev.clientX, ev.clientY);
    if (ev.pressure > 0 && ev.pressure !== 0.5) this.live.pressure = true;
    this.live.pts.push([x, y, ev.pressure > 0 ? ev.pressure : 0.5]);
  }
  _scheduleLive() {
    if (this._raf) return;
    this._raf = requestAnimationFrame(() => {
      this._raf = 0;
      if (!this.live) return;
      this.liveEl.setAttribute("d", outlinePath(this.live.pts, this.width * this.unitScale(), this.live.pressure));
      this.liveEl.setAttribute("fill", `var(--color-${this.colour})`);
    });
  }
  _eraseAt(ev) {
    const [x, y] = this.toSurface(ev.clientX, ev.clientY), limit = 9 * this.unitScale();
    for (let i = this.strokes.length - 1; i >= 0; i--) {
      const s = this.strokes[i], pts = this._decoded.get(s.id);
      if (!pts || !hitStroke(pts, x, y, Math.max(limit, (s.w || 3) / 2 + limit / 2))) continue;
      this.strokes.splice(i, 1);
      this.live.erased.add(s.id);
      this.undoStack.push({ type: "remove", stroke: s, index: i });
      this.render();
    }
  }
  undo() {
    const op = this.undoStack.pop();
    if (!op) return;
    if (op.type === "add") this.strokes = this.strokes.filter((s) => s !== op.stroke);
    else this.strokes.splice(Math.min(op.index, this.strokes.length), 0, op.stroke);
    this.redoStack.push(op);
    this.render(); this.onChange && this.onChange();
  }
  redo() {
    const op = this.redoStack.pop();
    if (!op) return;
    if (op.type === "add") this.strokes.push(op.stroke);
    else this.strokes = this.strokes.filter((s) => s !== op.stroke);
    this.undoStack.push(op);
    this.render(); this.onChange && this.onChange();
  }
  clear() {
    if (!this.strokes.length) return;
    const removed = this.strokes.slice();
    removed.forEach((s, i) => this.undoStack.push({ type: "remove", stroke: s, index: i }));
    this.strokes = []; this.redoStack = [];
    this.render(); this.onChange && this.onChange();
  }
  /** Redraw every stroke (after load, edits, or a relayout that moved the anchor blocks). */
  render() {
    this._decoded = new Map();
    let orphans = 0;
    const frag = this.svg.ownerDocument.createDocumentFragment();
    for (const s of this.strokes) {
      const pts = this.decode(s);
      if (!pts || !pts.length) { orphans++; continue; }
      this._decoded.set(s.id, pts);
      const path = this.svg.ownerDocument.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", outlinePath(pts, s.w || 3, pts.some((p) => p[2] !== 0.5)));
      path.setAttribute("fill", `var(--color-${INK_COLOURS.includes(s.c) ? s.c : "ink-1"})`);
      path.dataset.stroke = s.id;
      frag.appendChild(path);
    }
    this.layer.replaceChildren(frag);
    if (orphans !== this.orphans) { this.orphans = orphans; this.onOrphans && this.onOrphans(orphans); }
  }
}

/* ------------------------------------------------------------------ Saver: debounce, flush on navigation, retry */
export class Saver {
  constructor(send, { delay = 1200, onStatus } = {}) {
    this.send = send; this.delay = delay; this.onStatus = onStatus || (() => {});
    this.timer = 0; this.dirty = false; this.inflight = null; this.retries = 0;
  }
  mark() {
    this.dirty = true; this.onStatus("unsaved");
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.flush(), this.delay);
  }
  async flush() {
    clearTimeout(this.timer);
    if (!this.dirty) return this.inflight;
    if (this.inflight) { await this.inflight.catch(() => {}); return this.flush(); }
    this.dirty = false;
    this.onStatus("saving");
    this.inflight = this.send().then(() => {
      this.retries = 0; this.onStatus(this.dirty ? "unsaved" : "saved");
    }, (err) => {
      console.warn("annotation save failed", err);
      this.dirty = true; this.onStatus("error");
      if (this.retries++ < 3) this.timer = setTimeout(() => this.flush(), 1500 * this.retries);
    }).finally(() => { this.inflight = null; });
    return this.inflight;
  }
}

async function postJSON(url, body, method = "POST") {
  const payload = JSON.stringify(body);
  const r = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: payload, keepalive: payload.length < 60000 });
  if (!r.ok) throw new Error(`${method} ${url}: ${r.status}`);
  return r.status === 204 ? null : r.json();
}

/* ------------------------------------------------------------------ per-lesson controller */
const PREFS_KEY = "ink:prefs";
function loadPrefs() { try { return JSON.parse(localStorage.getItem(PREFS_KEY) || "{}") || {}; } catch (e) { return {}; } }
function savePrefs(p) { try { localStorage.setItem(PREFS_KEY, JSON.stringify(p)); } catch (e) {} }

const lessons = new Map();   // sid → Lesson

class Lesson {
  constructor(sid, bundle) {
    this.sid = sid;
    this.bundle = bundle || { note: "", highlights: [], ink: { lesson: { rev: 0, strokes: [] }, sketch: [] } };
    this.base = `/annotations/${encodeURIComponent(sid)}`;
    this.prefs = { tool: "pen", colour: "ink-1", width: 3, penDraws: true, drawMode: false, ...loadPrefs() };
    this.listeners = new Set();
    this.article = null;
  }
  emit(what) { this.listeners.forEach((fn) => { try { fn(what); } catch (e) { console.error(e); } }); }
  setPref(k, v) { this.prefs[k] = v; savePrefs({ tool: this.prefs.tool, colour: this.prefs.colour, width: this.prefs.width, penDraws: this.prefs.penDraws }); this.emit("prefs"); }
  destroy() { this.ink && this.ink.destroy(); this.sketch && this.sketch.destroy(); this.emit("destroy"); }
  async flushAll() { await Promise.all([this.inkSaver, this.noteSaver, this.sketchSaver].filter(Boolean).map((s) => s.flush().catch(() => {}))); }

  /* ---- highlights */
  async addHighlight(selector, colour) {
    const h = await postJSON(`${this.base}/highlights`, { ...selector, colour });
    this.bundle.highlights.push(h);
    this.placeHighlight(h);
    this.emit("highlights");
    return h;
  }
  async updateHighlight(id, patch) {
    const h = await postJSON(`/annotations/highlights/${id}`, patch, "PATCH");
    const i = this.bundle.highlights.findIndex((x) => x.id === id);
    if (i >= 0) this.bundle.highlights[i] = h;
    if (this.article) recolourHighlight(this.article, id, h.colour, h.comment);
    this.emit("highlights");
    return h;
  }
  async deleteHighlight(id) {
    await postJSON(`/annotations/highlights/${id}`, null, "DELETE").catch((e) => { if (!/404/.test(e.message)) throw e; });
    this.bundle.highlights = this.bundle.highlights.filter((x) => x.id !== id);
    if (this.article) removeHighlight(this.article, id);
    this.emit("highlights");
  }
  placeHighlight(h) {
    if (!this.article) return false;
    const map = textMap(this.article);
    const offsets = resolveSelector(map, h);
    if (!offsets) {
      if (!h.orphaned) { h.orphaned = true; postJSON(`/annotations/highlights/${h.id}`, { orphaned: true }, "PATCH").catch(() => {}); }
      return false;
    }
    const start = offsetToPoint(map, offsets.start);
    h.section = start ? headingBefore(this.article, start.node) : "";
    applyHighlight(this.article, offsets, h, map);
    if (h.orphaned) { h.orphaned = false; postJSON(`/annotations/highlights/${h.id}`, { orphaned: false }, "PATCH").catch(() => {}); }
    return true;
  }
  placeAllHighlights() {
    if (!this.article) return;
    this.article.querySelectorAll("mark.hl").forEach((m) => removeHighlight(this.article, m.dataset.hl));
    // Earlier offsets first so later ones are not shifted by marks (marks keep the text map intact anyway).
    for (const h of this.bundle.highlights.slice().sort((a, b) => a.start - b.start)) this.placeHighlight(h);
    this.emit("highlights");
  }
}

function lessonFor(sid, bundle) {
  let l = lessons.get(sid);
  if (!l) { l = new Lesson(sid, bundle); lessons.set(sid, l); }
  else if (bundle) l.bundle = bundle;
  return l;
}
function readBundle(el) {
  const script = el.querySelector("script[data-annotations]") || document.querySelector("script[data-annotations]");
  if (!script) return null;
  try { return JSON.parse(script.textContent); } catch (e) { return null; }
}

/* ------------------------------------------------------------------ widget: ink over the lesson + highlights */
const SVG_NS = "http://www.w3.org/2000/svg";
function svgEl(tag, attrs = {}) { const e = document.createElementNS(SVG_NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }
function h(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const k in attrs) {
    if (k === "class") e.className = attrs[k];
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), attrs[k]);
    else if (attrs[k] != null) e.setAttribute(k, attrs[k]);
  }
  for (const c of children.flat()) if (c != null) e.append(c);
  return e;
}
const HL_COLOURS = ["yellow", "green", "pink", "blue"];

function mountLessonAnnotations(host) {
  const sid = host.dataset.sid;
  const article = host.querySelector("[data-lesson-article]") || host.querySelector("article");
  if (!sid || !article) return;
  const lesson = lessonFor(sid, readBundle(host));
  lesson.article = article;
  lesson.host = host;
  lesson.placeAllHighlights();

  /* ---- ink layer over the article, anchored per block */
  const svg = svgEl("svg", { "aria-hidden": "true" });
  host.appendChild(svg);
  const hostRect = () => host.getBoundingClientRect();
  let blocks = [];
  function indexBlocks() {
    const hr = hostRect();
    blocks = Array.from(article.children).map((el, i) => {
      const r = el.getBoundingClientRect();
      return { el, i, k: blockFingerprint(el), x: r.left - hr.left, y: r.top - hr.top, w: r.width, h: r.height };
    });
    svg.setAttribute("viewBox", `0 0 ${Math.max(1, hr.width)} ${Math.max(1, hr.height)}`);
    svg.setAttribute("width", hr.width); svg.setAttribute("height", hr.height);
  }
  function findBlock(ref) {
    if (!ref) return null;
    const exact = blocks[ref.i];
    if (exact && exact.k === ref.k) return exact;
    for (let d = 1; d <= 3; d++) for (const j of [ref.i - d, ref.i + d]) if (blocks[j] && blocks[j].k === ref.k) return blocks[j];
    return null;   // the lesson changed around this stroke: leave it out and count it
  }
  const ink = new InkSurface({
    host, svg,
    policy: () => ({ tool: lesson.prefs.tool, penDraws: lesson.prefs.penDraws, drawMode: lesson.prefs.drawMode }),
    toSurface: (cx, cy) => { const r = hostRect(); return [cx - r.left, cy - r.top]; },
    unitScale: () => 1,
    encode: (pts, colour, width, hasPressure) => {
      if (pts.length < 1) return null;
      const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
      const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
      let b = blocks.find((bl) => cy >= bl.y && cy < bl.y + bl.h && bl.h > 0);
      if (!b) { let best = Infinity; for (const bl of blocks) { const d = cy < bl.y ? bl.y - cy : cy - (bl.y + bl.h); if (bl.h > 0 && d < best) { best = d; b = bl; } } }
      if (!b) return null;
      const bw = Math.max(1, b.w), bh = Math.max(1, b.h);
      return { c: colour, w: Math.round(width * 10) / 10, blk: { i: b.i, k: b.k }, bw: Math.round(bw), bh: Math.round(bh),
               pts: pts.map((p) => [+((p[0] - b.x) / bw).toFixed(4), +((p[1] - b.y) / bh).toFixed(4), hasPressure ? +p[2].toFixed(2) : 0.5]) };
    },
    decode: (s) => {
      const b = findBlock(s.blk);
      if (!b) return null;
      return s.pts.map((p) => [b.x + p[0] * b.w, b.y + p[1] * b.h, p[2] == null ? 0.5 : p[2]]);
    },
    onChange: () => { lesson.inkSaver.mark(); lesson.emit("ink"); },
    onOrphans: (n) => { lesson.inkOrphans = n; lesson.emit("ink"); },
  });
  lesson.ink = ink;
  ink.colour = lesson.prefs.colour; ink.width = lesson.prefs.width;
  lesson.inkSaver = new Saver(async () => {
    const doc = lesson.bundle.ink.lesson;
    const r = await postJSON(`${lesson.base}/ink/lesson/0`, { rev: doc.rev || 0, strokes: ink.strokes });
    doc.rev = r.rev; doc.strokes = ink.strokes.slice();
  }, { onStatus: (s) => { lesson.inkStatus = s; lesson.emit("status"); } });
  indexBlocks();
  ink.load(lesson.bundle.ink.lesson.strokes);

  let relayoutRaf = 0;
  const relayout = () => { if (relayoutRaf) return; relayoutRaf = requestAnimationFrame(() => { relayoutRaf = 0; indexBlocks(); ink.render(); }); };
  const ro = new ResizeObserver(relayout);
  ro.observe(host); ro.observe(article);
  const mo = new MutationObserver(relayout);
  mo.observe(article, { childList: true, subtree: true, attributes: true, attributeFilter: ["open", "class", "style"] });
  window.addEventListener("resize", relayout);
  document.addEventListener("casa:fontsizechange", relayout);
  lesson.listeners.add((what) => { if (what === "destroy") { ro.disconnect(); mo.disconnect(); window.removeEventListener("resize", relayout); document.removeEventListener("casa:fontsizechange", relayout); } });

  /* ---- toolbar (server-rendered buttons: data-ink-tool, data-ink-colour, data-ink-width, data-ink-pen-mode,
          data-ink-draw-mode, data-ink-undo, data-ink-redo, data-ink-clear; .ink-status; .ink-orphans). It lives in
          the lesson bar's flyout, which the pen toggle opens and closes (remembered, "inkbar:open"); the toggle
          wears the current ink colour. */
  const bar = document.querySelector(".ink-toolbar");
  const lessonBar = bar && bar.closest("[data-lesson-bar]");
  const barToggle = lessonBar && lessonBar.querySelector("[data-lesson-bar-toggle]");
  function setBarOpen(open) {
    lessonBar.toggleAttribute("data-open", open);
    barToggle.setAttribute("aria-expanded", String(open));
    barToggle.title = open ? "Hide the pen tools" : "Show the pen tools";
    try { localStorage.setItem("inkbar:open", open ? "1" : "0"); } catch (e) {}
  }
  if (barToggle) {
    let saved = null;
    try { saved = localStorage.getItem("inkbar:open"); } catch (e) {}
    setBarOpen(saved === "1");
    barToggle.addEventListener("click", () => setBarOpen(!lessonBar.hasAttribute("data-open")));
  }
  function syncBar() {
    if (!bar) return;
    bar.hidden = false;
    host.dataset.inkTool = lesson.prefs.tool;
    if (lessonBar) lessonBar.style.setProperty("--ink", `var(--color-${lesson.prefs.colour})`);
    bar.querySelectorAll("[data-ink-tool]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.inkTool === lesson.prefs.tool)));
    bar.querySelectorAll("[data-ink-colour]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.inkColour === lesson.prefs.colour)));
    bar.querySelectorAll("[data-ink-width]").forEach((b) => b.setAttribute("aria-pressed", String(+b.dataset.inkWidth === +lesson.prefs.width)));
    bar.querySelectorAll("[data-ink-pen-mode]").forEach((b) => { b.setAttribute("aria-pressed", String(!lesson.prefs.penDraws)); });
    bar.querySelectorAll("[data-ink-draw-mode]").forEach((b) => b.setAttribute("aria-pressed", String(!!lesson.prefs.drawMode)));
    bar.querySelectorAll("[data-ink-undo]").forEach((b) => { b.disabled = !ink.canUndo; });
    bar.querySelectorAll("[data-ink-redo]").forEach((b) => { b.disabled = !ink.canRedo; });
    bar.querySelectorAll("[data-ink-clear]").forEach((b) => { b.disabled = !ink.strokes.length; });
    const status = bar.querySelector(".ink-status");
    if (status) {
      const s = lesson.inkStatus;
      status.textContent = s === "saving" ? "Saving…" : s === "unsaved" ? "Unsaved" : s === "error" ? "Not saved – retrying" : s === "saved" ? "Saved" : (ink.strokes.length ? `${ink.strokes.length} stroke${ink.strokes.length === 1 ? "" : "s"}` : "");
      status.dataset.state = s || "";
    }
    const orphans = bar.querySelector(".ink-orphans");
    if (orphans) { orphans.hidden = !lesson.inkOrphans; orphans.textContent = lesson.inkOrphans ? `${lesson.inkOrphans} stroke${lesson.inkOrphans === 1 ? "" : "s"} could not be placed (the lesson text changed)` : ""; }
  }
  if (bar) {
    bar.addEventListener("click", (e) => {
      const b = e.target.closest("button"); if (!b) return;
      if (b.dataset.inkTool) lesson.setPref("tool", b.dataset.inkTool === lesson.prefs.tool && b.dataset.inkTool !== "none" ? "none" : b.dataset.inkTool);
      else if (b.dataset.inkColour) { lesson.setPref("colour", b.dataset.inkColour); if (lesson.prefs.tool === "erase" || lesson.prefs.tool === "none") lesson.setPref("tool", "pen"); }
      else if (b.dataset.inkWidth) lesson.setPref("width", +b.dataset.inkWidth);
      else if ("inkPenMode" in b.dataset) lesson.setPref("penDraws", !lesson.prefs.penDraws);
      else if ("inkDrawMode" in b.dataset) lesson.setPref("drawMode", !lesson.prefs.drawMode);
      else if ("inkUndo" in b.dataset) ink.undo();
      else if ("inkRedo" in b.dataset) ink.redo();
      else if ("inkClear" in b.dataset) { if (confirm("Remove every pen stroke on this lesson?")) ink.clear(); }
    });
  }
  lesson.listeners.add((what) => {
    if (what === "prefs") { ink.colour = lesson.prefs.colour; ink.width = lesson.prefs.width; }
    if (what !== "highlights") syncBar();
  });
  syncBar();

  /* ---- highlight bar on selection, popover on an existing mark */
  let hlBar = null, popover = null;
  const closeBar = () => { if (hlBar) { hlBar.remove(); hlBar = null; } };
  const closePopover = () => { if (popover) { popover.remove(); popover = null; } };
  function selectionInArticle() {
    const sel = document.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) return null;
    const range = sel.getRangeAt(0);
    if (!article.contains(range.commonAncestorContainer)) return null;
    if (range.commonAncestorContainer.nodeType === 1 && range.commonAncestorContainer.closest(EXCLUDE) && article.contains(range.commonAncestorContainer.closest(EXCLUDE))) return null;
    return range;
  }
  function place(el, rect) {
    const hr = hostRect();
    el.style.left = `${Math.max(8, Math.min(hr.width - el.offsetWidth - 8, rect.left - hr.left + rect.width / 2 - el.offsetWidth / 2))}px`;
    const above = rect.top - hr.top - el.offsetHeight - 10;
    el.style.top = `${above > 0 ? above : rect.bottom - hr.top + 10}px`;
  }
  function showBar() {
    closeBar();
    const range = selectionInArticle();
    if (!range) return;
    const selector = describeRange(article, range);
    if (!selector) return;
    hlBar = h("div", { class: "hl-bar", role: "toolbar", "aria-label": "Highlight" },
      HL_COLOURS.map((c) => h("button", { type: "button", class: `hl-swatch hl-swatch-${c}`, "aria-label": `Highlight ${c}`, onclick: async () => {
        closeBar(); document.getSelection().removeAllRanges();
        try { await lesson.addHighlight(selector, c); } catch (e) { console.error(e); }
      } })),
      h("button", { type: "button", class: "hl-bar-note", onclick: async () => {
        closeBar(); document.getSelection().removeAllRanges();
        try { const hl = await lesson.addHighlight(selector, "yellow"); const m = article.querySelector(`mark.hl[data-hl="${hl.id}"]`); if (m) showPopover(m, true); } catch (e) { console.error(e); }
      } }, "+ note"));
    hlBar.addEventListener("pointerdown", (e) => e.preventDefault());   // keep the selection
    host.appendChild(hlBar);
    place(hlBar, range.getBoundingClientRect());
  }
  function showPopover(mark, focusComment) {
    closePopover(); closeBar();
    const id = +mark.dataset.hl, hl = lesson.bundle.highlights.find((x) => x.id === id);
    if (!hl) return;
    const comment = h("textarea", { class: "hl-comment", rows: "2", placeholder: "Add a note to this highlight…", "aria-label": "Highlight note" });
    comment.value = hl.comment || "";
    let saveTimer = 0;
    const saveComment = () => { clearTimeout(saveTimer); if (comment.value !== (hl.comment || "")) lesson.updateHighlight(id, { comment: comment.value }).catch(console.error); };
    comment.addEventListener("input", () => { clearTimeout(saveTimer); saveTimer = setTimeout(saveComment, 800); });
    comment.addEventListener("blur", saveComment);
    popover = h("div", { class: "hl-popover", role: "dialog", "aria-label": "Highlight" },
      h("div", { class: "hl-popover-row" },
        HL_COLOURS.map((c) => h("button", { type: "button", class: `hl-swatch hl-swatch-${c}`, "aria-pressed": String(c === hl.colour), "aria-label": c,
          onclick: () => { lesson.updateHighlight(id, { colour: c }).then(() => popover && popover.querySelectorAll(".hl-swatch").forEach((b) => b.setAttribute("aria-pressed", String(b.classList.contains(`hl-swatch-${c}`))))).catch(console.error); } })),
        h("button", { type: "button", class: "hl-popover-delete", onclick: () => { closePopover(); lesson.deleteHighlight(id).catch(console.error); } }, "Remove"),
        h("button", { type: "button", class: "hl-popover-close", "aria-label": "Close", onclick: closePopover }, "×")),
      comment);
    host.appendChild(popover);
    place(popover, mark.getBoundingClientRect());
    if (focusComment) comment.focus();
  }
  host.addEventListener("click", (e) => {
    const mark = e.target.closest && e.target.closest("mark.hl");
    if (mark && article.contains(mark) && !host.classList.contains("is-drawing")) { e.preventDefault(); showPopover(mark); }
    else if (popover && !popover.contains(e.target)) closePopover();
  });
  const onSelection = () => {
    if (!lesson.article || lesson.article !== article) return;
    clearTimeout(lesson._selTimer);
    lesson._selTimer = setTimeout(() => { if (selectionInArticle()) showBar(); else closeBar(); }, 180);
  };
  const onKey = (e) => {
    if (e.key === "Escape") { closeBar(); closePopover(); }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "z" && !/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) && !e.target.isContentEditable) {
      if (e.shiftKey) ink.redo(); else ink.undo();
      e.preventDefault();
    }
  };
  document.addEventListener("selectionchange", onSelection);
  document.addEventListener("keydown", onKey);
  lesson.listeners.add((what) => {
    if (what === "destroy") { closeBar(); closePopover(); document.removeEventListener("selectionchange", onSelection); document.removeEventListener("keydown", onKey); }
  });
  lesson.emit("highlights");
}

/* ------------------------------------------------------------------ widget: typed note + highlight list (panel) */
function mountLessonNotes(el) {
  const sid = el.dataset.sid || (el.closest("[data-sid]") || {}).dataset?.sid || document.querySelector("[data-widget='lesson-annotations']")?.dataset.sid;
  if (!sid) return;
  const lesson = lessonFor(sid, lessons.has(sid) ? null : readBundle(el));
  const editor = el.querySelector(".notes-editor"), status = el.querySelector(".notes-saved"), list = el.querySelector(".hl-list"), empty = el.querySelector(".hl-empty");
  if (editor) {
    if (!editor.value && lesson.bundle.note) editor.value = lesson.bundle.note;
    lesson.noteSaver = lesson.noteSaver || new Saver(async () => {
      const r = await postJSON(`${lesson.base}/note`, { text: editor.value });
      lesson.bundle.note = editor.value; lesson.bundle.note_updated_at = r.updated_at;
    }, { onStatus: (s) => { if (!status) return; status.dataset.state = s; status.textContent = s === "saving" ? "Saving…" : s === "unsaved" ? "Unsaved changes" : s === "error" ? "Not saved – retrying" : "Saved"; } });
    editor.addEventListener("input", () => lesson.noteSaver.mark());
    editor.addEventListener("blur", () => lesson.noteSaver.flush());
    const grow = () => { editor.style.height = "auto"; editor.style.height = `${Math.min(600, Math.max(140, editor.scrollHeight + 2))}px`; };
    editor.addEventListener("input", grow); grow();
  }
  function renderList() {
    if (!list) return;
    const hls = lesson.bundle.highlights;
    list.replaceChildren(...hls.map((hl) => h("li", { class: `hl-item${hl.orphaned ? " is-orphaned" : ""}`, "data-hl-id": hl.id },
      h("button", { type: "button", class: "hl-item-quote", onclick: () => {
        const m = lesson.article && lesson.article.querySelector(`mark.hl[data-hl="${hl.id}"]`);
        if (!m) return;
        window.CasaPanel && window.CasaPanel.close && window.CasaPanel.close();
        m.scrollIntoView({ block: "center", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
        lesson.article.querySelectorAll("mark.hl.is-flash").forEach((x) => x.classList.remove("is-flash"));
        lesson.article.querySelectorAll(`mark.hl[data-hl="${hl.id}"]`).forEach((x) => { x.classList.add("is-flash"); setTimeout(() => x.classList.remove("is-flash"), 1600); });
      } },
        h("span", { class: `hl-dot hl-dot-${hl.colour}`, "aria-hidden": "true" }),
        h("span", { class: "hl-item-text" }, hl.exact.length > 140 ? `${hl.exact.slice(0, 140)}…` : hl.exact)),
      hl.section ? h("span", { class: "hl-item-section" }, hl.section) : null,
      hl.orphaned ? h("span", { class: "hl-item-orphan" }, "The lesson text changed; this highlight could not be placed.") : null,
      hl.comment ? h("p", { class: "hl-item-comment" }, hl.comment) : null,
      h("button", { type: "button", class: "hl-item-delete", "aria-label": "Remove highlight", onclick: () => lesson.deleteHighlight(hl.id).catch(console.error) }, "Remove"))));
    if (empty) empty.hidden = hls.length > 0;
    const count = el.querySelector(".hl-count");
    if (count) count.textContent = hls.length ? String(hls.length) : "";
  }
  lesson.listeners.add((what) => { if (what === "highlights") renderList(); });
  renderList();
}

/* ------------------------------------------------------------------ widget: sketch pad (panel) — see _panel_sketch.html */
export const SKETCH_W = 1000, SKETCH_H = 1400;
function mountLessonSketch(el) {
  const sid = el.dataset.sid || document.querySelector("[data-widget='lesson-annotations']")?.dataset.sid;
  if (!sid) return;
  const lesson = lessonFor(sid, lessons.has(sid) ? null : readBundle(el));
  const pages = () => lesson.bundle.ink.sketch || (lesson.bundle.ink.sketch = []);
  const pageDoc = (n) => { let d = pages().find((p) => p.page === n); if (!d) { d = { kind: "sketch", page: n, rev: 0, strokes: [] }; pages().push(d); pages().sort((a, b) => a.page - b.page); } return d; };
  const state = { page: 0 };
  const preview = el.querySelector(".sketch-preview"), dialog = el.querySelector("dialog.sketch-dialog"), pageSvg = el.querySelector(".sketch-page svg, svg.sketch-page");
  const pager = el.querySelector(".sketch-pager"), labels = el.querySelectorAll("[data-sketch-page-label]");
  if (!pageSvg) return;
  pageSvg.setAttribute("viewBox", `0 0 ${SKETCH_W} ${SKETCH_H}`);
  const toSurface = (cx, cy) => { const r = pageSvg.getBoundingClientRect(); return [(cx - r.left) / r.width * SKETCH_W, (cy - r.top) / r.height * SKETCH_H]; };
  const unitScale = () => SKETCH_W / Math.max(1, pageSvg.getBoundingClientRect().width);
  const ink = new InkSurface({
    host: pageSvg.parentElement, svg: pageSvg,
    policy: () => ({ tool: lesson.prefs.sketchTool || "pen", penDraws: true, drawMode: !!lesson.prefs.sketchFinger, sketch: true }),
    toSurface, unitScale,
    encode: (pts, colour, width, hasPressure) => ({ c: colour, w: Math.round(width * 10) / 10, pts: pts.map((p) => [Math.round(p[0] * 10) / 10, Math.round(p[1] * 10) / 10, hasPressure ? +p[2].toFixed(2) : 0.5]) }),
    decode: (s) => s.pts.map((p) => [p[0], p[1], p[2] == null ? 0.5 : p[2]]),
    onChange: () => { lesson.sketchSaver.mark(); syncSketch(); },
  });
  lesson.sketch = ink;
  ink.colour = lesson.prefs.colour; ink.width = lesson.prefs.width;
  lesson.sketchSaver = new Saver(async () => {
    const doc = pageDoc(state.page);
    const r = await postJSON(`${lesson.base}/ink/sketch/${state.page}`, { rev: doc.rev || 0, strokes: ink.strokes });
    doc.rev = r.rev; doc.strokes = ink.strokes.slice();
    if (!doc.strokes.length) lesson.bundle.ink.sketch = pages().filter((p) => p.strokes.length || p.page === state.page);
  }, { onStatus: (s) => { lesson.sketchStatus = s; syncSketch(); } });
  async function showPage(n) {
    await lesson.sketchSaver.flush().catch(() => {});
    state.page = Math.max(0, Math.min(99, n));
    ink.load(pageDoc(state.page).strokes);
    syncSketch();
  }
  function renderPreview() {
    if (!preview) return;
    preview.setAttribute("viewBox", `0 0 ${SKETCH_W} ${SKETCH_H}`);
    preview.replaceChildren(...ink.strokes.map((s) => svgEl("path", { d: outlinePath(ink._decoded.get(s.id) || [], s.w || 3, true), fill: `var(--color-${s.c || "ink-1"})` })));
    preview.classList.toggle("is-empty", !ink.strokes.length);
  }
  function syncSketch() {
    renderPreview();
    const saved = pages().filter((p) => p.strokes.length).map((p) => p.page);
    const last = Math.max(state.page, saved.length ? Math.max(...saved) : 0);
    labels.forEach((l) => { l.textContent = `Page ${state.page + 1} of ${last + 1}`; });
    el.querySelectorAll("[data-sketch-prev]").forEach((b) => { b.disabled = state.page === 0; });
    el.querySelectorAll("[data-sketch-undo]").forEach((b) => { b.disabled = !ink.canUndo; });
    el.querySelectorAll("[data-sketch-redo]").forEach((b) => { b.disabled = !ink.canRedo; });
    el.querySelectorAll("[data-sketch-clear]").forEach((b) => { b.disabled = !ink.strokes.length; });
    el.querySelectorAll("[data-sketch-tool]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.sketchTool === (lesson.prefs.sketchTool || "pen"))));
    el.querySelectorAll("[data-sketch-colour]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.sketchColour === lesson.prefs.colour)));
    el.querySelectorAll("[data-sketch-width]").forEach((b) => b.setAttribute("aria-pressed", String(+b.dataset.sketchWidth === +lesson.prefs.width)));
    el.querySelectorAll("[data-sketch-finger]").forEach((b) => b.setAttribute("aria-pressed", String(!!lesson.prefs.sketchFinger)));
    const status = el.querySelector(".sketch-status");
    if (status) { const s = lesson.sketchStatus; status.dataset.state = s || ""; status.textContent = s === "saving" ? "Saving…" : s === "unsaved" ? "Unsaved" : s === "error" ? "Not saved – retrying" : s === "saved" ? "Saved" : ""; }
    if (pager) pager.hidden = false;
  }
  el.addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    if ("sketchOpen" in b.dataset && dialog) { dialog.showModal(); requestAnimationFrame(() => ink.render()); }
    else if ("sketchClose" in b.dataset && dialog) { lesson.sketchSaver.flush(); dialog.close(); }
    else if ("sketchPrev" in b.dataset) showPage(state.page - 1);
    else if ("sketchNext" in b.dataset) showPage(state.page + 1);
    else if ("sketchUndo" in b.dataset) ink.undo();
    else if ("sketchRedo" in b.dataset) ink.redo();
    else if ("sketchClear" in b.dataset) { if (confirm("Clear this page?")) ink.clear(); }
    else if (b.dataset.sketchTool) { lesson.prefs.sketchTool = b.dataset.sketchTool; syncSketch(); }
    else if (b.dataset.sketchColour) { lesson.setPref("colour", b.dataset.sketchColour); lesson.prefs.sketchTool = "pen"; }
    else if (b.dataset.sketchWidth) lesson.setPref("width", +b.dataset.sketchWidth);
    else if ("sketchFinger" in b.dataset) { lesson.prefs.sketchFinger = !lesson.prefs.sketchFinger; syncSketch(); }
  });
  if (dialog) {
    dialog.addEventListener("close", () => { lesson.sketchSaver.flush(); renderPreview(); });
    dialog.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "z") { if (e.shiftKey) ink.redo(); else ink.undo(); e.preventDefault(); e.stopPropagation(); }
    });
    new ResizeObserver(() => ink.render()).observe(pageSvg);
  }
  lesson.listeners.add((what) => { if (what === "prefs") { ink.colour = lesson.prefs.colour; ink.width = lesson.prefs.width; syncSketch(); } });
  const first = pages().find((p) => p.strokes.length);
  state.page = first ? first.page : 0;
  ink.load(pageDoc(state.page).strokes);
  syncSketch();
}

/* ------------------------------------------------------------------ wiring */
function flushAll() { return Promise.all(Array.from(lessons.values()).map((l) => l.flushAll())); }
if (typeof window !== "undefined" && typeof document !== "undefined") {
  const register = () => {
    if (!window.CasaWidgets) return false;
    window.CasaWidgets.register("lesson-annotations", mountLessonAnnotations);
    window.CasaWidgets.register("lesson-notes", mountLessonNotes);
    window.CasaWidgets.register("lesson-sketch", mountLessonSketch);
    return true;
  };
  if (!register()) document.addEventListener("DOMContentLoaded", register, { once: true });
  // Boosted navigation swaps the whole body: save first, then drop the instances for the page that is leaving.
  document.addEventListener("htmx:beforeRequest", (e) => { if (e.detail && e.detail.boosted) flushAll(); });
  document.addEventListener("htmx:beforeSwap", (e) => {
    if (e.target !== document.body) return;
    lessons.forEach((l) => l.destroy()); lessons.clear();
  });
  window.addEventListener("pagehide", () => { flushAll(); });
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") flushAll(); });
  window.CasaAnnotations = { lessons, flushAll };
}
