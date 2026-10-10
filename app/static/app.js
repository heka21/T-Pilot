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
  function drawerOpen() {
    var backdrop = document.getElementById("drawer-backdrop");
    return !!backdrop && !backdrop.classList.contains("hidden");
  }
  document.addEventListener("keydown", function (e) {
    // Escape closes the drawer if it is open, else the lesson panel's bottom sheet.
    if (e.key === "Escape") { if (drawerOpen()) setDrawer(false); else closePanel(); }
    // "/" jumps to the page's own filter box if it has one, else the top-bar search box, unless the user is already typing.
    if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey) return;
    var t = e.target, tag = t && t.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (t && t.isContentEditable)) return;
    var box = document.querySelector("[data-filter-q]") || document.querySelector("[data-global-search]");
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

  // Lessons page filter: words (all must match a card's code or titles), exam and status, applied in the page.
  // The URL keeps the filter (replaceState), so Back from a lesson returns to the same list.
  function filterValues(box) {
    var exam = box.querySelector("input[name=exam]:checked"), status = box.querySelector("input[name=status]:checked");
    return { q: box.querySelector("[data-filter-q]").value.trim(), exam: exam ? exam.value : "", status: status ? status.value : "" };
  }
  function applyLessonFilter(box) {
    var f = filterValues(box), words = f.q.toLowerCase().split(/\s+/).filter(Boolean), shown = 0;
    box.querySelectorAll("[data-unit-section]").forEach(function (sec) {
      var inExam = !f.exam || sec.dataset.exams.split(" ").indexOf(f.exam) >= 0, n = 0;
      sec.querySelectorAll("[data-lesson]").forEach(function (li) {
        var text = li.dataset.text;
        var ok = inExam && (!f.status || li.dataset.status === f.status) && words.every(function (w) { return text.indexOf(w) >= 0; });
        li.hidden = !ok;
        if (ok) n++;
      });
      var missing = sec.querySelector("[data-missing]");
      if (missing) {
        var m = missing.querySelectorAll("[data-lesson]:not([hidden])").length;
        missing.hidden = m === 0;
        if (words.length || f.status) missing.open = m > 0;
      }
      sec.hidden = n === 0;
      var link = box.querySelector('[data-unit-link="' + sec.dataset.unitSection + '"]');
      if (link) {
        link.hidden = !inExam;
        link.classList.toggle("is-empty", n === 0);
        link.querySelector("[data-unit-count]").textContent = n;
      }
      shown += n;
    });
    var total = +box.dataset.total, filtered = !!(f.q || f.exam || f.status);
    box.querySelector("[data-filter-count]").textContent = (filtered ? shown + " of " + total : total) + " lessons";
    box.querySelector("[data-filter-reset]").hidden = !filtered;
    box.querySelector("[data-filter-empty]").hidden = shown > 0;
    box.querySelector("[data-filter-search-link]").href = "/search" + (f.q ? "?q=" + encodeURIComponent(f.q) : "");
    var url = new URL(location.href);
    ["q", "exam", "status"].forEach(function (k) { if (f[k]) url.searchParams.set(k, f[k]); else url.searchParams.delete(k); });
    if (url.href !== location.href) history.replaceState(history.state, "", url);
  }
  function setLessonFilter(box, q, exam, status) {
    box.querySelector("[data-filter-q]").value = q;
    [["exam", exam], ["status", status]].forEach(function (pair) {
      var radio = box.querySelector("input[name=" + pair[0] + "][value='" + pair[1] + "']") || box.querySelector("input[name=" + pair[0] + "][value='']");
      radio.checked = true;
    });
    applyLessonFilter(box);
  }
  function initLessonFilter(root) {
    var box = root.querySelector && root.querySelector("[data-lesson-filter]");
    if (!box) return;
    var p = new URLSearchParams(location.search);  // an HTMX history restore can bring back stale input values
    setLessonFilter(box, p.get("q") || "", p.get("exam") || "", p.get("status") || "");
  }
  document.addEventListener("input", function (e) {
    var box = e.target.closest && e.target.closest("[data-lesson-filter]");
    if (box && e.target.matches("[data-filter-q]")) applyLessonFilter(box);
  });
  document.addEventListener("change", function (e) {
    var box = e.target.closest && e.target.closest("[data-lesson-filter]");
    if (box && e.target.matches("input[type=radio]")) applyLessonFilter(box);
  });
  document.addEventListener("click", function (e) {
    var box = e.target.closest && e.target.closest("[data-lesson-filter]");
    if (!box) return;
    if (e.target.closest("[data-filter-clear-q]")) {
      var f = filterValues(box);
      setLessonFilter(box, "", f.exam, f.status);
      box.querySelector("[data-filter-q]").focus();
    } else if (e.target.closest("[data-filter-reset]")) {
      setLessonFilter(box, "", "", "");
    } else {
      var link = e.target.closest("[data-unit-link]");
      if (link && link.classList.contains("is-empty")) e.preventDefault();
    }
  });
  document.addEventListener("keydown", function (e) {
    var input = e.target.closest && e.target.closest("[data-filter-q]");
    if (!input) return;
    var box = input.closest("[data-lesson-filter]");
    if (!box) return;   // other pages (the equation sheet) mark their filter box so "/" focuses it, and handle keys themselves
    if (e.key === "Enter") {
      // Enter opens the first match, so "bakc 2.1" + Enter goes straight to that lesson.
      var first = box.querySelector("[data-unit-section]:not([hidden]) [data-lesson]:not([hidden]) a");
      if (first) first.click();
      e.preventDefault();
    } else if (e.key === "Escape") {
      if (input.value) { var f = filterValues(box); setLessonFilter(box, "", f.exam, f.status); } else input.blur();
    }
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

  // Desktop sidebar: full width or an icon rail. Same storage pattern as the theme: <html data-sidebar>, set before
  // first paint by base.html. The server always renders the button as expanded, so its labels are synced here.
  function sidebarCollapsed() { return document.documentElement.dataset.sidebar === "collapsed"; }
  function syncSidebarToggle() {
    var collapsed = sidebarCollapsed(), label = collapsed ? "Expand sidebar" : "Collapse sidebar";
    document.querySelectorAll("[data-sidebar-toggle]").forEach(function (b) {
      b.setAttribute("aria-expanded", String(!collapsed));
      b.title = label + " ( [ )";
      var span = b.querySelector("span"); if (span) span.textContent = label;
    });
  }
  function toggleSidebar() {
    var collapsed = !sidebarCollapsed();
    if (collapsed) document.documentElement.dataset.sidebar = "collapsed"; else delete document.documentElement.dataset.sidebar;
    try { if (collapsed) localStorage.setItem("sidebar", "collapsed"); else localStorage.removeItem("sidebar"); } catch (err) {}
    syncSidebarToggle();
    // Charts and 3D views size themselves on window resize; the content width changes without one.
    setTimeout(function () { window.dispatchEvent(new Event("resize")); }, 220);
  }
  document.addEventListener("click", function (e) {
    if (e.target.closest && e.target.closest("[data-sidebar-toggle]")) toggleSidebar();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "[" || e.ctrlKey || e.metaKey || e.altKey || !window.matchMedia("(min-width: 64rem)").matches) return;
    var t = e.target, tag = t && t.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (t && t.isContentEditable)) return;
    toggleSidebar(); e.preventDefault();
  });

  // Reader's text size: s, m (default), l, xl, xxl. Same storage pattern as the theme: localStorage "fontsize" and
  // <html data-font-size> (absent = m), applied before first paint by base.html. CSS scales `content-scaled` regions.
  var FONT_SIZES = ["s", "m", "l", "xl", "xxl"];
  function applyFontSize(size) {
    if (FONT_SIZES.indexOf(size) < 0) size = "m";
    if (size === "m") delete document.documentElement.dataset.fontSize; else document.documentElement.dataset.fontSize = size;
    // button[...] because <html data-font-size> matches the bare attribute selector too.
    document.querySelectorAll("button[data-font-size]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.fontSize === size)); });
  }
  function currentFontSize() { return document.documentElement.dataset.fontSize || "m"; }
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest("button[data-font-size]");
    if (!btn) return;
    var size = btn.dataset.fontSize;
    try { if (size === "m") localStorage.removeItem("fontsize"); else localStorage.setItem("fontsize", size); } catch (err) {}
    applyFontSize(size);
    var menu = btn.closest("[popover]");
    if (menu && menu.hidePopover) { try { menu.hidePopover(); } catch (err) {} }
    document.dispatchEvent(new CustomEvent("casa:fontsizechange", { detail: { size: size } }));
    // Charts and 3D views size themselves on window resize; the diagram caps change with the text size.
    setTimeout(function () { window.dispatchEvent(new Event("resize")); }, 220);
  });

  // Lesson tools panel (note.html): Contents / Notes / Sketch tabs. On wide screens it docks beside the article
  // (CSS `docked:` variant) and the lesson bar's Notes button switches it to Notes; otherwise it is a bottom sheet
  // opened by that button, closed by the close button, the backdrop, Escape or following a section link. The
  // chosen tab is remembered ("panel:tab").
  var PANEL_TABS = ["contents", "notes", "sketch"];
  function lessonPanel() { return document.querySelector("[data-lesson-panel]"); }
  function panelDocked(panel) { return !!panel && getComputedStyle(panel).position === "sticky"; }
  function setPanelTab(name, focus) {
    var panel = lessonPanel();
    if (!panel || PANEL_TABS.indexOf(name) < 0) return;
    panel.querySelectorAll("[data-panel-tab-btn]").forEach(function (b) {
      var on = b.dataset.panelTabBtn === name;
      b.setAttribute("aria-selected", String(on));
      b.tabIndex = on ? 0 : -1;
      if (on && focus) b.focus();
    });
    panel.querySelectorAll("[data-panel-tab]").forEach(function (p) { p.hidden = p.dataset.panelTab !== name; });
    try { localStorage.setItem("panel:tab", name); } catch (err) {}
  }
  function setPanelOpen(open) {
    var panel = lessonPanel();
    if (!panel) return;
    var wasOpen = panel.classList.contains("is-open");
    panel.classList.toggle("is-open", open);
    document.querySelectorAll(".lesson-panel-backdrop").forEach(function (b) { b.classList.toggle("is-open", open); });
    document.querySelectorAll("[data-panel-open]").forEach(function (b) { b.setAttribute("aria-expanded", String(open)); });
    if (open && !wasOpen && !panelDocked(panel)) {
      var tab = panel.querySelector('[data-panel-tab-btn][aria-selected="true"]');
      if (tab) tab.focus({ preventScroll: true });
    } else if (!open && wasOpen && panel.contains(document.activeElement)) {
      var fab = document.querySelector("[data-panel-open]");
      if (fab) fab.focus({ preventScroll: true });
    }
  }
  function openPanel() { setPanelOpen(true); }
  function closePanel() { setPanelOpen(false); }
  function savedPanelTab() {
    try { var t = localStorage.getItem("panel:tab"); return PANEL_TABS.indexOf(t) >= 0 ? t : "contents"; } catch (err) { return "contents"; }
  }
  function syncPanel() {
    var panel = lessonPanel();
    if (!panel || panel.dataset.panelSynced) return;   // once per page (a body swap brings a fresh panel)
    panel.dataset.panelSynced = "1";
    setPanelTab(savedPanelTab());
    closePanel();
  }
  document.addEventListener("click", function (e) {
    if (!e.target.closest) return;
    var t;
    if ((t = e.target.closest("[data-panel-tab-btn]"))) setPanelTab(t.dataset.panelTabBtn);
    else if (e.target.closest("[data-panel-open]")) { if (panelDocked(lessonPanel())) setPanelTab("notes"); else openPanel(); }
    else if (e.target.closest("[data-panel-close]")) closePanel();
    else if ((t = e.target.closest("[data-lesson-panel] [data-toc-link]")) && !panelDocked(lessonPanel())) closePanel();
  });
  document.addEventListener("keydown", function (e) {
    var btn = e.target.closest && e.target.closest("[data-panel-tab-btn]");
    if (!btn) return;
    var tabs = Array.prototype.slice.call(btn.closest("[role=tablist]").querySelectorAll("[data-panel-tab-btn]"));
    var i = tabs.indexOf(btn), next = -1;
    if (e.key === "ArrowRight") next = (i + 1) % tabs.length;
    else if (e.key === "ArrowLeft") next = (i - 1 + tabs.length) % tabs.length;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = tabs.length - 1;
    if (next < 0) return;
    setPanelTab(tabs[next].dataset.panelTabBtn, true);
    e.preventDefault();
  });
  window.CasaPanel = { open: openPanel, close: closePanel, setTab: function (name) { setPanelTab(name); } };

  // Floaters: the lesson bar (note.html) and the mini player (base.html), which the reader drags anywhere.
  // [data-floater="<name>"] is the element; a drag starts on a [data-drag-handle] inside it (the whole lesson bar,
  // the player's grip and title), never on [data-no-drag] parts or form fields, and a [data-floater-grip] also
  // takes arrow keys. The spot is kept as fractions of the free space ("<name>:pos") so it survives rotation and
  // resizes; until moved a floater sits where CSS parks it (the lesson bar beside the docked panel). Each is
  // kept below the top bar (and the lesson bar above the mini player when that is low
  // on the screen); data-side / data-vside say which way its flyouts should open, towards the middle, and --room
  // how wide they can be.
  var FLOAT_GAP = 8, FLOAT_STEP = 16;
  function savedFloatPos(el) {
    try { var p = JSON.parse(localStorage.getItem(el.dataset.floater + ":pos") || "null"); return p && isFinite(p.x) && isFinite(p.y) ? p : null; } catch (err) { return null; }
  }
  function moveFloater(el, x, y) {
    var w = el.offsetWidth, h = el.offsetHeight, vw = document.documentElement.clientWidth, vh = window.innerHeight;
    var topbar = document.querySelector(".topbar"), top = Math.max(FLOAT_GAP, (topbar ? topbar.getBoundingClientRect().bottom : 0) + FLOAT_GAP);
    x = Math.max(FLOAT_GAP, Math.min(vw - w - FLOAT_GAP, x));
    var bottom = vh - FLOAT_GAP;
    document.querySelectorAll("[data-miniplayer]").forEach(function (o) {
      if (o === el || el.contains(o)) return;   // the player as the lesson bar's flyout
      var r = o.getBoundingClientRect();
      if (r.height && r.top > vh / 2 && r.left < x + w && r.right > x) bottom = Math.min(bottom, r.top - FLOAT_GAP);
    });
    y = Math.max(top, Math.min(bottom - h, y));
    el.style.left = x + "px"; el.style.top = y + "px"; el.style.right = "auto"; el.style.bottom = "auto";
    el.dataset.side = x + w / 2 > vw / 2 ? "left" : "right";
    el.dataset.vside = y + h / 2 > vh / 2 ? "up" : "down";
    el.style.setProperty("--room", (x + w / 2 > vw / 2 ? x : vw - x - w) + "px");   // width free on the flyout side
  }
  function placeFloater(el) {
    if (!el.getClientRects().length) return;   // hidden (the player with nothing loaded)
    var pos = savedFloatPos(el), vw = document.documentElement.clientWidth, vh = window.innerHeight;
    if (pos) { moveFloater(el, pos.x * (vw - el.offsetWidth), pos.y * (vh - el.offsetHeight)); return; }
    el.style.left = el.style.top = el.style.right = el.style.bottom = "";
    var r = el.getBoundingClientRect(), panel = lessonPanel();
    var x = el.hasAttribute("data-lesson-bar") && panelDocked(panel) ? panel.getBoundingClientRect().left - r.width - 3 * FLOAT_GAP / 2 : r.left;
    moveFloater(el, x, r.top);
  }
  // The player first, so the lesson bar is placed against where it now sits.
  function placeFloaters() {
    document.querySelectorAll("[data-miniplayer][data-floater]").forEach(placeFloater);
    document.querySelectorAll("[data-floater]:not([data-miniplayer])").forEach(placeFloater);
  }
  function saveFloatPos(el) {
    var r = el.getBoundingClientRect(), vw = document.documentElement.clientWidth, vh = window.innerHeight;
    try { localStorage.setItem(el.dataset.floater + ":pos", JSON.stringify({ x: r.left / Math.max(1, vw - r.width), y: r.top / Math.max(1, vh - r.height) })); } catch (err) {}
  }
  var floatDrag = null;
  document.addEventListener("pointerdown", function (e) {
    var handle = e.target.closest && e.target.closest("[data-drag-handle]");
    var el = handle && handle.closest("[data-floater]");
    if (!el || e.target.closest("[data-no-drag], input, select, textarea") || e.button > 0) return;
    var r = el.getBoundingClientRect();
    floatDrag = { el: el, id: e.pointerId, sx: e.clientX, sy: e.clientY, x: r.left, y: r.top, moved: false };
  });
  document.addEventListener("pointermove", function (e) {
    var d = floatDrag;
    if (!d || e.pointerId !== d.id) return;
    var dx = e.clientX - d.sx, dy = e.clientY - d.sy;
    if (!d.moved) {
      if (Math.abs(dx) + Math.abs(dy) < 6) return;   // a tap on a button, not a drag
      d.moved = true;
      d.el.classList.add("is-dragging");
      try { d.el.setPointerCapture(e.pointerId); } catch (err) {}
    }
    moveFloater(d.el, d.x + dx, d.y + dy);
    e.preventDefault();
  });
  function endFloatDrag(e) {
    var d = floatDrag;
    if (!d || e.pointerId !== d.id) return;
    floatDrag = null;
    if (!d.moved) return;
    d.el.classList.remove("is-dragging");
    saveFloatPos(d.el);
    // The click that ends a drag is not a press of the button under it.
    function swallow(ev) { ev.stopPropagation(); ev.preventDefault(); }
    window.addEventListener("click", swallow, { capture: true, once: true });
    setTimeout(function () { window.removeEventListener("click", swallow, true); }, 0);
  }
  document.addEventListener("pointerup", endFloatDrag);
  document.addEventListener("pointercancel", endFloatDrag);
  document.addEventListener("keydown", function (e) {
    var grip = e.target.closest && e.target.closest("[data-floater-grip]");
    var step = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key];
    if (!grip || !step) return;
    var el = grip.closest("[data-floater]"), r = el.getBoundingClientRect(), n = e.shiftKey ? 4 * FLOAT_STEP : FLOAT_STEP;
    moveFloater(el, r.left + step[0] * n, r.top + step[1] * n);
    saveFloatPos(el);
    e.preventDefault();
  });
  // A [data-floater-collapse] button folds its floater down to just itself (data-collapsed, kept as
  // "<name>:collapsed"), keeping the floater's bottom edge where it was so the button stays under the finger.
  function setFloaterCollapsed(el, collapsed) {
    var btn = el.querySelector("[data-floater-collapse]");
    el.toggleAttribute("data-collapsed", collapsed);
    btn.setAttribute("aria-expanded", String(!collapsed));
    btn.title = collapsed ? "Show the lesson tools" : "Collapse the lesson bar";
  }
  function collapseKey(el) { return el.dataset.floater + ":collapsed"; }
  function restoreCollapsed(root) {
    root.querySelectorAll("[data-floater-collapse]").forEach(function (btn) {
      var el = btn.closest("[data-floater]"), saved = null;
      try { saved = localStorage.getItem(collapseKey(el)); } catch (err) {}
      setFloaterCollapsed(el, saved === "1");
    });
  }
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest("[data-floater-collapse]");
    if (!btn) return;
    var el = btn.closest("[data-floater]"), r = el.getBoundingClientRect(), collapsed = !el.hasAttribute("data-collapsed");
    setFloaterCollapsed(el, collapsed);
    try { localStorage.setItem(collapseKey(el), collapsed ? "1" : "0"); } catch (err) {}
    if (savedFloatPos(el)) { moveFloater(el, r.right - el.offsetWidth, r.bottom - el.offsetHeight); saveFloatPos(el); }
    else placeFloater(el);
  });
  window.addEventListener("resize", placeFloaters);
  // The mini player showing or hiding changes the room at the bottom (player.js sets html[data-player-open]).
  new MutationObserver(placeFloaters).observe(document.documentElement, { attributes: true, attributeFilter: ["data-player-open"] });

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

  // Reading progress. The page's [data-read-target] (a lesson or reference article) drives a bar in the top bar
  // ([data-read-progress], --p = fraction read), percentage readouts ([data-read-pct]) and the current section
  // (aria-current on [data-toc-link] entries, in every copy of the section list). Progress is saved per path in
  // localStorage ("read:<path>") so a long lesson can be resumed. Everything is recomputed on scroll, resize and
  // whenever the article or page changes height (details opening, KaTeX, widgets, text-size changes).
  var reading = { target: null, observer: null, sections: [], threshold: 0, dirty: true, raf: 0, saveAt: 0, saved: null };
  function readFraction(rect, viewportHeight, barBottom) {
    // 0 until the article's top reaches the bottom edge of the top bar; 1 once its bottom is in view.
    if (rect.height <= 0) return 0;
    if (rect.bottom <= viewportHeight) return 1;
    var span = rect.height - (viewportHeight - barBottom);
    if (span <= 0) return 0;
    return Math.min(1, Math.max(0, (barBottom - rect.top) / span));
  }
  function readingKey() { return "read:" + location.pathname; }
  function savedReading() {
    try { var raw = localStorage.getItem(readingKey()); return raw ? JSON.parse(raw) : null; } catch (err) { return null; }
  }
  function rebuildSections(target, rect) {
    var cs = getComputedStyle(document.documentElement), first = target.querySelector("h2[id]");
    var padding = parseFloat(cs.scrollPaddingTop) || 0, margin = first ? (parseFloat(getComputedStyle(first).scrollMarginTop) || 0) : 0;
    reading.threshold = padding + margin + 2;   // where a heading lands after a section-list jump
    reading.sections = Array.prototype.map.call(target.querySelectorAll("h2[id]"), function (h) {
      return { id: h.id, top: h.getBoundingClientRect().top - rect.top };
    });
    reading.dirty = false;
  }
  function updateReading() {
    reading.raf = 0;
    var target = reading.target;
    if (!target || !target.isConnected) return;
    var rect = target.getBoundingClientRect(), vh = window.innerHeight;
    var bar = document.querySelector(".topbar"), barBottom = bar ? bar.getBoundingClientRect().bottom : 0;
    var p = readFraction(rect, vh, barBottom), pct = Math.round(p * 100);
    document.querySelectorAll("[data-read-progress]").forEach(function (el) {
      el.hidden = false; el.style.setProperty("--p", p.toFixed(4)); el.setAttribute("aria-valuenow", String(pct));
    });
    document.querySelectorAll("[data-read-pct]").forEach(function (el) { el.hidden = false; el.textContent = pct + "%"; });
    if (reading.dirty) rebuildSections(target, rect);
    var current = null;
    for (var i = 0; i < reading.sections.length; i++) {
      if (rect.top + reading.sections[i].top <= reading.threshold) current = reading.sections[i].id; else break;
    }
    if (p >= 1 && reading.sections.length) current = reading.sections[reading.sections.length - 1].id;
    document.querySelectorAll("[data-toc-link]").forEach(function (a) {
      if (a.dataset.tocLink === current) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
    });
    var now = Date.now();
    if (p > 0 && now - reading.saveAt > 1000) {
      reading.saveAt = now;
      try { localStorage.setItem(readingKey(), JSON.stringify({ p: Math.round(p * 1000) / 1000, t: now })); } catch (err) {}
    }
    document.dispatchEvent(new CustomEvent("casa:reading", { detail: { fraction: p, section: current } }));
  }
  function scheduleReading() { if (!reading.raf && reading.target) reading.raf = requestAnimationFrame(updateReading); }
  function markReadingDirty() { reading.dirty = true; scheduleReading(); }
  function initReading() {
    var target = document.querySelector("[data-read-target]");
    if (target !== reading.target) {
      if (reading.observer) { reading.observer.disconnect(); reading.observer = null; }
      reading.target = target;
      reading.saveAt = 0;
      reading.saved = target ? savedReading() : null;
      if (target && "ResizeObserver" in window) {
        // The article's own height (details, images, maths, widgets) and the page's (anything above it).
        reading.observer = new ResizeObserver(markReadingDirty);
        reading.observer.observe(target);
        reading.observer.observe(document.body);
      }
    }
    if (!target) {
      document.querySelectorAll("[data-read-progress], [data-read-pct]").forEach(function (el) { el.hidden = true; });
      return;
    }
    markReadingDirty();
  }
  window.addEventListener("scroll", scheduleReading, { passive: true });
  window.addEventListener("resize", markReadingDirty);
  document.addEventListener("casa:fontsizechange", markReadingDirty);
  window.CasaReading = {
    fraction: readFraction,
    saved: savedReading,
    // The saved position when a page is opened fresh (used by the resume pill): null when nothing useful is stored.
    resumable: function () {
      var s = reading.saved;
      if (!s || typeof s.p !== "number" || typeof s.t !== "number") return null;
      if (s.p < 0.05 || s.p > 0.95 || Date.now() - s.t > 30 * 864e5) return null;
      return s;
    },
    scrollToFraction: function (p) {
      var target = reading.target;
      if (!target) return;
      var rect = target.getBoundingClientRect(), vh = window.innerHeight;
      var bar = document.querySelector(".topbar"), barBottom = bar ? bar.getBoundingClientRect().bottom : 0;
      var span = rect.height - (vh - barBottom);
      var y = window.scrollY + rect.top - barBottom + Math.max(0, span) * Math.min(1, Math.max(0, p));
      window.scrollTo({ top: y, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    },
  };

  // Resume pill: a page opened fresh (no #section, at the top) with a saved position part-way through offers to jump
  // back there. Offered once per article; gone on click, after 10 s, or once the reader scrolls 300 px. Never auto-scrolls.
  var PLAY_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3l14 9-14 9z"/></svg>';
  var resumeOfferedFor = null;
  function offerResume() {
    var target = document.querySelector("[data-read-target]");
    if (!target || target === resumeOfferedFor || !window.CasaReading) return;
    resumeOfferedFor = target;
    var saved = window.CasaReading.resumable();
    if (location.hash || window.scrollY >= 80 || !saved || document.querySelector(".read-resume")) return;
    var pill = document.createElement("button"), startY = window.scrollY, timer = 0;
    pill.type = "button";
    pill.className = "read-resume";
    pill.innerHTML = PLAY_ICON + "<span>Resume where you left off · " + Math.round(saved.p * 100) + "%</span>";
    function dismiss() {
      clearTimeout(timer);
      window.removeEventListener("scroll", onScroll);
      pill.remove();
    }
    function onScroll() { if (Math.abs(window.scrollY - startY) > 300) dismiss(); }
    pill.addEventListener("click", function () { dismiss(); window.CasaReading.scrollToFraction(saved.p); });
    window.addEventListener("scroll", onScroll, { passive: true });
    timer = setTimeout(dismiss, 10000);
    document.body.appendChild(pill);
  }

  function init(root) {
    renderMaths(root); mountAll(root); celebrateIn(root); initLessonFilter(root); applyTheme(currentTheme()); syncSidebarToggle();
    applyFontSize(currentFontSize()); syncPanel(); restoreCollapsed(root); placeFloaters();
    initReading();   // last, so maths and widgets have laid out
    offerResume();
  }
  document.addEventListener("DOMContentLoaded", function () { init(document); });
  // Deferred scripts (KaTeX) may finish after DOMContentLoaded listeners were queued; run once more on load.
  window.addEventListener("load", function () { init(document); });
  if (window.htmx) htmx.onLoad(function (el) { init(el.nodeType === 1 ? el : document); });
})();
