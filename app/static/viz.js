/* Shared helpers for lesson widgets (content/widgets/*.html). Loaded before Alpine, registers on alpine:init.

   x-data="widget({ ... })"    a plain interactive widget with named presets and a Reset that restores the
                               starting values. Getters and methods in the object work as in a bare x-data.
   x-data="timeline({ ... })"  the same plus a clock for processes that play out over time (a sea breeze through
                               the day, a thunderstorm's life). `t` runs 0 → 1 over `duration` seconds; bind the
                               picture to getters of `t`, e.g. get temp() { return this.lerp(18, 31, this.seg(0.2, 0.6)) }.

   Presets: `presets: { name: { key: value, ... } }`, applied with preset('name'). Watch mode applies them by name
   from cues in the narration script, so name them after what they show ("calm-morning", "va-at-mtow").
   A timeline preset may also hold `t` (and `play: true` to start playing from there).

   $viz (also window.CasaViz.fn): small maths and formatting helpers usable in any widget expression. */
(function () {
  "use strict";

  var fn = {
    clamp: function (x, lo, hi) { return Math.min(hi, Math.max(lo, x)); },
    lerp: function (a, b, f) { return a + (b - a) * f; },
    // progress of x through [a, b] as 0..1, clamped
    seg: function (x, a, b) { return b === a ? (x >= b ? 1 : 0) : Math.min(1, Math.max(0, (x - a) / (b - a))); },
    // smooth start and stop for 0..1
    ease: function (f) { f = Math.min(1, Math.max(0, f)); return f * f * (3 - 2 * f); },
    // linear map from domain [d0, d1] to range [r0, r1]
    scale: function (v, d0, d1, r0, r1) { return r0 + (v - d0) / (d1 - d0) * (r1 - r0); },
    // a number with thousands separators and dp decimals: fmt(12500) → "12,500", fmt(3.14159, 1) → "3.1"
    fmt: function (n, dp) {
      if (n == null || isNaN(n)) return "–";
      dp = dp || 0;
      var s = Math.abs(n).toFixed(dp).split(".");
      s[0] = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      return (n < 0 && Number(Math.abs(n).toFixed(dp)) !== 0 ? "−" : "") + s.join(".");
    },
    // signed with an explicit plus: sign(4) → "+4", sign(-4) → "−4"
    sign: function (n, dp) { return (n > 0 ? "+" : "") + fn.fmt(n, dp); },
    // three-digit direction: dir(60) → "060"
    dir: function (deg) { var d = ((Math.round(deg) % 360) + 360) % 360; return String(d === 0 ? 360 : d).padStart(3, "0"); },
    // point on a compass bearing (0 = up, clockwise) at radius r from (cx, cy); returns {x, y}
    pol: function (cx, cy, r, bearing) { var a = bearing * Math.PI / 180; return { x: cx + r * Math.sin(a), y: cy - r * Math.cos(a) }; },
    // wind is reported FROM a direction; arrows on a picture point where it blows TO
    windTo: function (from) { return ((from + 180) % 360 + 360) % 360; },
    // ISA temperature (°C) at a pressure height in feet, 2 °C per 1,000 ft (the exam's rounding of 1.98)
    isaTemp: function (ft) { return 15 - 2 * ft / 1000; },
    // minutes since midnight → "HHMM"; wraps past midnight
    hhmm: function (min) { min = ((Math.round(min) % 1440) + 1440) % 1440; return String(Math.floor(min / 60)).padStart(2, "0") + String(min % 60).padStart(2, "0"); },
    // minutes since midnight → "H:MM" for a duration
    hmm: function (min) { min = Math.max(0, Math.round(min)); return Math.floor(min / 60) + ":" + String(min % 60).padStart(2, "0"); },
    // WST minutes since midnight → UTC minutes and the day shift (-1, 0); WST is UTC+8 all year
    utc: function (wstMin) { var u = wstMin - 480; return { min: ((u % 1440) + 1440) % 1440, day: u < 0 ? -1 : 0 }; },
    // an SVG path "M x y L x y ..." through points [[x, y], ...]
    path: function (pts) { return pts.map(function (p, i) { return (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" "); },
    // a track or bearing as three digits with 000 for north: trk(0) → "000" (dir() gives "360", as for wind and heading)
    trk: function (deg) { var d = ((Math.round(deg) % 360) + 360) % 360; return String(d).padStart(3, "0"); },
    // dates as "YYYY-MM-DD" strings, in UTC so they never shift with the browser's zone
    addDays: function (iso, n) { var d = new Date(iso + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); },
    daysBetween: function (a, b) { return Math.round((Date.parse(b + "T00:00:00Z") - Date.parse(a + "T00:00:00Z")) / 86400000); },
    // "Tue 7 Oct" (with the year when asked)
    fmtDate: function (iso, year) {
      var d = new Date(iso + "T00:00:00Z");
      var s = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][d.getUTCDay()] + " " + d.getUTCDate() + " " +
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d.getUTCMonth()];
      return year ? s + " " + d.getUTCFullYear() : s;
    },
    // Dragging on an SVG: @pointerdown="drag($event, (p) => { x = p.x })" calls back with the pointer in the SVG's
    // own coordinates (viewBox units) on every move until release. Give the dragged element touch-action: none.
    drag: function (evt, cb) {
      var svg = evt.target.ownerSVGElement || evt.target.closest("svg");
      if (!svg || !svg.getScreenCTM) return;
      evt.preventDefault();
      function at(e) {
        var m = svg.getScreenCTM();
        if (!m) return;
        var pt = svg.createSVGPoint();
        pt.x = e.clientX; pt.y = e.clientY;
        var q = pt.matrixTransform(m.inverse());
        cb({ x: q.x, y: q.y });
      }
      function up() { window.removeEventListener("pointermove", at); window.removeEventListener("pointerup", up); window.removeEventListener("pointercancel", up); }
      window.addEventListener("pointermove", at);
      window.addEventListener("pointerup", up);
      window.addEventListener("pointercancel", up);
      at(evt);
    },
  };

  function reducedMotion() {
    return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  // Values that Reset restores: own data, not getters or functions.
  function snapshot(obj) {
    var out = {};
    Object.keys(obj).forEach(function (k) {
      var d = Object.getOwnPropertyDescriptor(obj, k);
      if (!d || d.get || typeof d.value === "function" || k === "presets" || k === "steps" || k.charAt(0) === "_") return;
      out[k] = JSON.parse(JSON.stringify(d.value === undefined ? null : d.value));
    });
    return out;
  }

  // Copy cfg onto base keeping getters as getters (a spread would freeze them into values).
  function merge(base, cfg) {
    var userInit = cfg.init, userDestroy = cfg.destroy;
    var own = Object.getOwnPropertyDescriptors(cfg);
    delete own.init; delete own.destroy;
    Object.defineProperties(base, own);
    base._userInit = userInit;
    base._userDestroy = userDestroy;
    return base;
  }

  function widget(cfg) {
    cfg = cfg || {};
    var start = null;
    var c = merge({
      presets: {},
      active: null, // name of the preset last applied, for aria-pressed on preset buttons
      init: function () {
        // from the raw object: Alpine calls init with `this` as a merged proxy that hides property descriptors
        start = snapshot(c);
        if (this._userInit) this._userInit.call(this);
      },
      destroy: function () { if (this._userDestroy) this._userDestroy.call(this); },
      // preset('name') or preset({ key: value }) (the older widgets' style)
      preset: function (p) {
        var vals = typeof p === "string" ? this.presets[p] : p;
        if (!vals) { console.warn("unknown preset", p); return; }
        var self = this;
        Object.keys(vals).forEach(function (k) { if (k !== "play") self[k] = vals[k]; });
        this.active = typeof p === "string" ? p : null;
        return vals;
      },
      reset: function () {
        var self = this;
        if (start) Object.keys(start).forEach(function (k) { self[k] = JSON.parse(JSON.stringify(start[k])); });
        this.active = null;
      },
    }, cfg);
    Object.keys(fn).forEach(function (k) { if (!(k in c)) c[k] = fn[k]; });
    return c;
  }

  function timeline(cfg) {
    cfg = cfg || {};
    var raf = 0, last = 0, observer = null, visible = true, wanted = false;
    var c = widget(cfg);
    // defaults for what the author left out; never read cfg's values here (a `steps` getter would run on the raw
    // config, before the helpers exist)
    var own = {
      t: 0,
      duration: 10, // seconds for 0 → 1 at speed 1
      speed: 1,
      loop: true,
      autoplay: false,
      playing: false,
      steps: [], // [{ at: 0..1, label: "Cumulus" }, ...] key moments, in order
    };
    Object.keys(own).forEach(function (k) {
      if (!Object.prototype.hasOwnProperty.call(cfg, k) || k === "playing") c[k] = own[k];
    });
    var widgetInit = c.init, widgetDestroy = c.destroy, widgetPreset = c.preset, widgetReset = c.reset;

    function frame(self, now) {
      if (!self.playing) return;
      var dt = last ? Math.min(0.1, (now - last) / 1000) : 0;
      last = now;
      var t = self.t + dt * self.speed / self.duration;
      if (t >= 1) {
        if (self.loop) t -= 1;
        else { t = 1; self.playing = false; wanted = false; }
      }
      self.t = t;
      if (self.playing) raf = requestAnimationFrame(function (n) { frame(self, n); });
    }
    function run(self) {
      cancelAnimationFrame(raf);
      last = 0;
      if (self.playing && visible) raf = requestAnimationFrame(function (n) { frame(self, n); });
    }

    c.init = function () {
      widgetInit.call(this);
      var self = this;
      if (typeof IntersectionObserver === "function" && this.$el) {
        observer = new IntersectionObserver(function (entries) {
          visible = entries[entries.length - 1].isIntersecting;
          if (visible && wanted) { self.playing = true; run(self); }
          else if (!visible && self.playing) { self.playing = false; cancelAnimationFrame(raf); }
        });
        observer.observe(this.$el);
      }
      if (this.autoplay && !reducedMotion()) this.play();
    };
    c.destroy = function () {
      cancelAnimationFrame(raf);
      if (observer) observer.disconnect();
      widgetDestroy.call(this);
    };
    c.play = function () {
      if (this.t >= 1 && !this.loop) this.t = 0;
      wanted = true;
      this.playing = true;
      run(this);
    };
    c.pause = function () { wanted = false; this.playing = false; cancelAnimationFrame(raf); };
    c.toggle = function () { if (this.playing) this.pause(); else this.play(); };
    c.seek = function (t) { this.t = fn.clamp(Number(t), 0, 1); };
    // index of the step the clock is in (the last step whose `at` has passed), -1 before the first
    Object.defineProperty(c, "step", { enumerable: true, configurable: true, get: function () {
      var i = -1;
      for (var k = 0; k < this.steps.length; k++) if (this.t + 1e-9 >= this.steps[k].at) i = k;
      return i;
    } });
    Object.defineProperty(c, "stepLabel", { enumerable: true, configurable: true, get: function () {
      var s = this.steps[this.step];
      return s ? s.label : "";
    } });
    c.goStep = function (i) {
      if (!this.steps.length) return;
      i = fn.clamp(i, 0, this.steps.length - 1);
      this.pause();
      this.t = this.steps[i].at;
    };
    c.next = function () { this.goStep(this.step + 1); };
    c.prev = function () {
      // back to the start of this step, or the previous one when already at its start
      var i = this.step;
      if (i >= 0 && this.t - this.steps[i].at < 0.01) i -= 1;
      this.goStep(Math.max(0, i));
    };
    c.preset = function (p) {
      this.pause();
      var vals = widgetPreset.call(this, p);
      if (vals && vals.play) this.play();
      return vals;
    };
    c.reset = function () { this.pause(); widgetReset.call(this); };
    // shorthand for getters: the clock's progress through [a, b], eased or not
    c.at = function (a, b) { return fn.seg(this.t, a, b); };
    c.eased = function (a, b) { return fn.ease(fn.seg(this.t, a, b)); };
    return c;
  }

  // Watch mode and tests drive a widget through this: drive(el, { preset: "name", play: true }), or { reset: true }
  function drive(el, opts) {
    var root = el && (el.matches && el.matches("[x-data]") ? el : el.querySelector && el.querySelector("[x-data]"));
    if (!root || !window.Alpine) return false;
    var data = window.Alpine.$data(root);
    if (!data) return false;
    if (opts.reset && typeof data.reset === "function") data.reset();
    if (opts.preset && typeof data.preset === "function") data.preset(opts.preset);
    if (opts.play && typeof data.play === "function") data.play();
    if (opts.pause && typeof data.pause === "function") data.pause();
    return true;
  }

  window.CasaViz = { fn: fn, widget: widget, timeline: timeline, drive: drive };

  document.addEventListener("alpine:init", function () {
    window.Alpine.data("widget", widget);
    window.Alpine.data("timeline", timeline);
    window.Alpine.magic("viz", function () { return fn; });
  });
})();
