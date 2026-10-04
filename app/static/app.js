/* Shared page behaviour: drawer, maths rendering and widget hooks that must also run after HTMX
   boosted navigations (hx-boost swaps <body>, so DOMContentLoaded fires only once per session). */
(function () {
  "use strict";

  // Mobile drawer. Delegated so it survives body swaps without re-binding.
  function setDrawer(open) {
    var sidebar = document.getElementById("sidebar"), backdrop = document.getElementById("drawer-backdrop");
    if (!sidebar || !backdrop) return;
    sidebar.classList.toggle("-translate-x-full", !open);
    backdrop.classList.toggle("hidden", !open);
    document.querySelectorAll("[data-drawer-open]").forEach(function (b) { b.setAttribute("aria-expanded", String(open)); });
  }
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-drawer-open]")) setDrawer(true);
    else if (e.target.closest("[data-drawer-close]")) setDrawer(false);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") setDrawer(false);
    // "/" jumps to the top-bar search box, unless the user is already typing.
    if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey) return;
    var t = e.target, tag = t && t.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (t && t.isContentEditable)) return;
    var box = document.querySelector("[data-global-search]");
    if (!box) return;
    box.focus(); box.select(); e.preventDefault();
  });

  // Top-bar search: suggestions dropdown (filled by HTMX from /search/suggest), arrow keys, Enter, Escape, clear.
  function suggestOptions(form) { return Array.prototype.slice.call(form.querySelectorAll(".suggest-item, .suggest-all")); }
  function setActive(form, index) {
    var opts = suggestOptions(form), input = form.querySelector("[data-global-search]");
    opts.forEach(function (o, i) { o.classList.toggle("is-active", i === index); o.setAttribute("aria-selected", String(i === index)); });
    if (opts[index]) { opts[index].scrollIntoView({ block: "nearest" }); input.setAttribute("aria-activedescendant", opts[index].id); }
    else input.removeAttribute("aria-activedescendant");
  }
  function syncExpanded(form) {
    var input = form.querySelector("[data-global-search]"), panel = form.querySelector(".suggest-panel");
    if (input && panel) input.setAttribute("aria-expanded", String(panel.childElementCount > 0 && !form.classList.contains("is-dismissed")));
  }
  document.addEventListener("keydown", function (e) {
    var input = e.target.closest && e.target.closest("[data-global-search]");
    var form = input && input.closest("[data-topsearch]");
    if (!form || !form.querySelector(".suggest-panel")) return;
    var opts = suggestOptions(form), current = opts.findIndex(function (o) { return o.classList.contains("is-active"); });
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!opts.length) return;
      form.classList.remove("is-dismissed");
      var step = e.key === "ArrowDown" ? 1 : -1;
      setActive(form, current < 0 ? (step > 0 ? 0 : opts.length - 1) : (current + step + opts.length) % opts.length);
      syncExpanded(form); e.preventDefault();
    } else if (e.key === "Enter" && current >= 0 && !form.classList.contains("is-dismissed")) {
      opts[current].click(); e.preventDefault();
    } else if (e.key === "Escape") {
      if (!form.classList.contains("is-dismissed") && form.querySelector(".suggest-panel").childElementCount) form.classList.add("is-dismissed");
      else input.blur();
      setActive(form, -1); syncExpanded(form);
    }
  });
  document.addEventListener("input", function (e) {
    var form = e.target.closest && e.target.closest("[data-topsearch]");
    if (!form) return;
    form.classList.remove("is-dismissed");
    if (!e.target.value.trim()) { var panel = form.querySelector(".suggest-panel"); if (panel) panel.innerHTML = ""; syncExpanded(form); }
  });
  // Keep focus in the box when a suggestion is pressed, so the panel does not close before the click lands (Safari).
  document.addEventListener("mousedown", function (e) {
    if (e.target.closest && e.target.closest(".suggest-panel, .topsearch-clear")) e.preventDefault();
  });
  document.addEventListener("click", function (e) {
    var clear = e.target.closest && e.target.closest("[data-search-clear]");
    if (!clear) return;
    var input = clear.closest("[data-topsearch]").querySelector("[data-global-search]");
    input.value = "";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.focus();
  });
  document.addEventListener("htmx:afterSwap", function (e) {
    if (e.target.id !== "search-suggest") return;
    var form = e.target.closest("[data-topsearch]");
    // A slow reply for an older query can land after the box was cleared.
    if (!form.querySelector("[data-global-search]").value.trim()) e.target.innerHTML = "";
    setActive(form, -1); syncExpanded(form);
  });

  // KaTeX: render $...$ / $$...$$ (emitted by the server as \( \) and \[ \]) inside notes and widgets.
  function renderMaths(root) {
    if (typeof renderMathInElement !== "function") return;
    root.querySelectorAll(".note-body, .visual-widget, .question-stem, .explanation, .flashcard, [data-maths]").forEach(function (el) {
      if (el.dataset.mathsDone) return;
      el.dataset.mathsDone = "1";
      renderMathInElement(el, {
        delimiters: [
          { left: "\\[", right: "\\]", display: true },
          { left: "\\(", right: "\\)", display: false },
          { left: "$$", right: "$$", display: true },
        ],
        throwOnError: false,
        strict: "ignore",
      });
    });
  }

  // Widgets that need code beyond Alpine register here: window.CasaWidgets.register(name, mountFn).
  // mountFn(el) is called once for every element with data-widget="name" present now or swapped in later.
  var mounts = {};
  window.CasaWidgets = {
    register: function (name, mount) { mounts[name] = mount; mountAll(document); },
    mountAll: mountAll,
  };
  function mountAll(root) {
    root.querySelectorAll("[data-widget]").forEach(function (el) {
      var name = el.dataset.widget, fn = mounts[name];
      if (!fn || el.dataset.widgetMounted) return;
      el.dataset.widgetMounted = "1";
      try { fn(el); } catch (err) { console.error("widget " + name + " failed", err); }
    });
  }

  // Colour theme: system -> light -> dark -> system. The choice lives in localStorage and <html data-theme>,
  // which survives hx-boost body swaps; base.html applies it before first paint.
  var THEMES = ["system", "light", "dark"], THEME_LABELS = { system: "follow system", light: "light", dark: "dark" };
  var themeMetas = null;
  function applyTheme(theme) {
    var root = document.documentElement;
    if (theme === "light" || theme === "dark") root.dataset.theme = theme; else delete root.dataset.theme;
    // The browser chrome colour follows the forced theme too.
    themeMetas = themeMetas || Array.prototype.map.call(document.querySelectorAll('meta[name="theme-color"]'),
      function (m) { return { el: m, media: m.getAttribute("media"), content: m.content }; });
    var forced = { light: "#f4f6fc", dark: "#080d1c" }[theme];
    themeMetas.forEach(function (m) {
      if (forced) { m.el.removeAttribute("media"); m.el.content = forced; }
      else { m.el.setAttribute("media", m.media); m.el.content = m.content; }
    });
    document.querySelectorAll("[data-theme-toggle]").forEach(function (b) { b.setAttribute("aria-label", "Colour theme: " + THEME_LABELS[theme]); });
  }
  function currentTheme() { return document.documentElement.dataset.theme || "system"; }
  document.addEventListener("click", function (e) {
    if (!e.target.closest || !e.target.closest("[data-theme-toggle]")) return;
    var next = THEMES[(THEMES.indexOf(currentTheme()) + 1) % THEMES.length];
    try { if (next === "system") localStorage.removeItem("theme"); else localStorage.setItem("theme", next); } catch (err) {}
    applyTheme(next);
    document.dispatchEvent(new CustomEvent("casa:themechange", { detail: { theme: next } }));
  });

  // Celebrations: an element with data-celebrate ("big" or "small") throws confetti once when it appears.
  // Skipped under reduced motion. Colours come from the theme tokens.
  function celebrate(origin, big) {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    var cs = getComputedStyle(document.documentElement);
    var colours = ["brand", "brand-2", "ok", "warn", "accent", "info"].map(function (k) { return cs.getPropertyValue("--color-" + k).trim(); });
    var canvas = document.createElement("canvas"), ctx = canvas.getContext("2d"), dpr = window.devicePixelRatio || 1;
    if (!ctx) return;
    canvas.className = "confetti";
    canvas.width = innerWidth * dpr; canvas.height = innerHeight * dpr;
    document.body.appendChild(canvas);
    ctx.scale(dpr, dpr);
    var r = origin ? origin.getBoundingClientRect() : null;
    var ox = r ? r.left + r.width / 2 : innerWidth / 2, oy = r ? r.top + Math.min(r.height / 2, 80) : innerHeight / 3;
    var n = big ? 140 : 46, parts = [];
    for (var i = 0; i < n; i++) {
      var a = -Math.PI / 2 + (Math.random() - 0.5) * (big ? 2.4 : 1.8), v = (big ? 9 : 6) * (0.5 + Math.random());
      parts.push({ x: ox, y: oy, vx: Math.cos(a) * v, vy: Math.sin(a) * v, w: 5 + Math.random() * 5, h: 7 + Math.random() * 7,
                   rot: Math.random() * 6.28, vr: (Math.random() - 0.5) * 0.3, c: colours[i % colours.length] });
    }
    var start = performance.now(), life = big ? 2200 : 1400;
    (function frame(now) {
      var t = now - start;
      ctx.clearRect(0, 0, innerWidth, innerHeight);
      ctx.globalAlpha = Math.max(0, 1 - Math.max(0, t - life * 0.6) / (life * 0.4));
      parts.forEach(function (p) {
        p.vy += 0.22; p.vx *= 0.99; p.x += p.vx; p.y += p.vy; p.rot += p.vr;
        ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.fillStyle = p.c;
        ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h * Math.abs(Math.cos(p.rot * 2))); ctx.restore();
      });
      if (t < life) requestAnimationFrame(frame); else canvas.remove();
    })(start);
  }
  window.CasaCelebrate = celebrate;
  function celebrateIn(root) {
    var els = root.matches && root.matches("[data-celebrate]") ? [root] : [];
    els = els.concat(Array.prototype.slice.call(root.querySelectorAll("[data-celebrate]")));
    els.forEach(function (el) {
      if (el.dataset.celebrated) return;
      el.dataset.celebrated = "1";
      setTimeout(function () { celebrate(el, el.dataset.celebrate === "big"); }, 150);
    });
  }

  function init(root) { renderMaths(root); mountAll(root); celebrateIn(root); applyTheme(currentTheme()); }
  document.addEventListener("DOMContentLoaded", function () { init(document); });
  // Deferred scripts (KaTeX) may finish after DOMContentLoaded listeners were queued; run once more on load.
  window.addEventListener("load", function () { init(document); });
  if (window.htmx) htmx.onLoad(function (el) { init(el.nodeType === 1 ? el : document); });
})();
