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

  function init(root) { renderMaths(root); mountAll(root); }
  document.addEventListener("DOMContentLoaded", function () { init(document); });
  // Deferred scripts (KaTeX) may finish after DOMContentLoaded listeners were queued; run once more on load.
  window.addEventListener("load", function () { init(document); });
  if (window.htmx) htmx.onLoad(function (el) { init(el.nodeType === 1 ? el : document); });
})();
