/* Lesson narration player (see app/services/audio.py and content/AUDIO.md).

   One Audio object for the whole session, never attached to the DOM: hx-boost swaps <body> on every navigation,
   and a media element removed from the document pauses, so the sound lives here and the page only holds controls
   that re-bind after each swap. A full page load stops playback, but the place is saved on the server every few
   seconds and the player comes back paused where it was.

   window.CasaPlayer = {load(lesson, {autoplay, queue}), toggle(), seek(t), skip(dt), chapter(+1|-1), stop(),
                        current(), subscribe(el, fn)}

   lesson: the descriptor from services.audio.descriptor (sid, title, unit, src, duration, chapters, position, ...).
   The lock screen, CarPlay and headphone buttons work through the Media Session API. */
(function () {
  "use strict";

  var SPEEDS = [0.8, 1, 1.1, 1.25, 1.5, 1.75, 2];
  var SAVE_EVERY = 10000;   // ms between progress reports while playing
  var BACK = 15, FORWARD = 30;
  var STORE = "listen:current";

  var audio = new Audio();
  audio.preload = "metadata";
  var lesson = null;          // descriptor of what is loaded
  var queue = [];             // descriptors to play after it
  var lastSaved = 0;
  var listeners = [];         // [{el, fn}]: dropped once el leaves the document

  function store(key, value) { try { if (value === undefined) localStorage.removeItem(key); else localStorage.setItem(key, value); } catch (e) {} }
  function stored(key) { try { return localStorage.getItem(key); } catch (e) { return null; } }

  var speed = parseFloat(stored("listen:speed")) || 1;

  function fmt(t) {
    t = Math.max(0, Math.floor(t || 0));
    var h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = t % 60;
    return (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(s).padStart(2, "0");
  }

  function chapterIndex(t) {
    var chs = (lesson && lesson.chapters) || [], i = 0;
    for (var k = 0; k < chs.length; k++) if (chs[k].t <= t + 0.25) i = k;
    return i;
  }

  // ------------------------------------------------------------ events for the page (mini player, watch mode)
  function emit(type) {
    var detail = { type: type, lesson: lesson, time: audio.currentTime, duration: audio.duration || (lesson && lesson.duration) || 0,
                   paused: audio.paused, speed: speed };
    listeners = listeners.filter(function (l) { return l.el.isConnected; });
    listeners.forEach(function (l) { try { l.fn(detail); } catch (e) { console.error(e); } });
  }

  function subscribe(el, fn) {
    listeners.push({ el: el, fn: fn });
    fn({ type: "init", lesson: lesson, time: audio.currentTime, duration: audio.duration || (lesson && lesson.duration) || 0,
         paused: audio.paused, speed: speed });
  }

  // ------------------------------------------------------------ progress on the server
  function payload() {
    return JSON.stringify({ sid: lesson.sid, position: audio.currentTime || 0, duration: audio.duration || lesson.duration || 0 });
  }
  function save(beacon) {
    if (!lesson || !(audio.currentTime > 0)) return;
    lastSaved = Date.now();
    lesson.position = audio.currentTime;
    store(STORE, JSON.stringify({ lesson: lesson, queue: queue }));
    if (beacon && navigator.sendBeacon) {
      navigator.sendBeacon("/listen/progress", new Blob([payload()], { type: "application/json" }));
      return;
    }
    fetch("/listen/progress", { method: "POST", headers: { "Content-Type": "application/json" }, body: payload(), keepalive: true })
      .catch(function () {});
  }

  // ------------------------------------------------------------ loading and the queue
  function fetchQueue(sid) {
    return fetch("/listen/queue?scope=exam&start=" + encodeURIComponent(sid))
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (list) { if (lesson && lesson.sid === sid) queue = list.filter(function (d) { return d.sid !== sid; }); })
      .catch(function () {});
  }

  function load(next, opts) {
    opts = opts || {};
    if (!next || !next.src) return;
    if (lesson && lesson.sid === next.sid) {        // already loaded: just play, with the new queue if one came
      if (opts.queue) {
        queue = opts.queue.filter(function (d) { return d.sid !== next.sid; });
        store(STORE, JSON.stringify({ lesson: lesson, queue: queue }));
      }
      if (opts.autoplay) audio.play().catch(function () {});
      return;
    }
    if (lesson) save();
    lesson = next;
    var start = next.position > 5 ? next.position - 3 : 0;
    // A media fragment sets the start before metadata loads (setting currentTime that early is ignored on iOS).
    audio.src = next.src + (start ? "#t=" + start.toFixed(1) : "");
    audio.defaultPlaybackRate = speed;
    audio.playbackRate = speed;
    if (opts.queue) queue = opts.queue.filter(function (d) { return d.sid !== next.sid; });
    else { queue = []; fetchQueue(next.sid); }
    store(STORE, JSON.stringify({ lesson: lesson, queue: queue }));
    // play() must run in the same tick as the tap for iOS to allow it; everything above is synchronous.
    if (opts.autoplay) audio.play().catch(function () {});
    setMetadata();
    emit("load");
  }

  function advance() {
    var next = queue.shift();
    if (next) { lesson = null; load(next, { autoplay: true, queue: queue.slice() }); }
    else emit("end");
  }

  function stop() {
    save();
    audio.pause();
    audio.removeAttribute("src");
    audio.load();
    lesson = null; queue = [];
    store(STORE);
    if ("mediaSession" in navigator) navigator.mediaSession.metadata = null;
    emit("stop");
  }

  function toggle() { if (!lesson) return; if (audio.paused) audio.play().catch(function () {}); else audio.pause(); }
  function seek(t) {
    if (!lesson) return;
    var d = audio.duration || lesson.duration || 0;
    audio.currentTime = Math.max(0, Math.min(d ? d - 0.5 : t, t));
    emit("time");
  }
  function skip(dt) { seek((audio.currentTime || 0) + dt); }
  function chapter(step) {
    if (!lesson || !lesson.chapters || !lesson.chapters.length) return;
    var i = chapterIndex(audio.currentTime);
    // "Previous" restarts the current chapter unless you are already near its start.
    if (step < 0 && audio.currentTime - lesson.chapters[i].t > 4) step = 0;
    var j = i + step;
    if (j >= lesson.chapters.length) { advance(); return; }
    seek(lesson.chapters[Math.max(0, j)].t);
  }
  function setSpeed(s) {
    speed = s;
    audio.playbackRate = s;
    audio.defaultPlaybackRate = s;
    store("listen:speed", String(s));
    positionState();
    emit("speed");
  }
  function cycleSpeed() { setSpeed(SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length] || 1); }

  // ------------------------------------------------------------ lock screen, CarPlay, headphones
  function setMetadata() {
    if (!("mediaSession" in navigator) || !lesson) return;
    var ch = lesson.chapters && lesson.chapters[chapterIndex(audio.currentTime)];
    try {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: lesson.title,
        artist: lesson.sid + (ch ? " · " + ch.title : ""),
        album: "CASA Theory",
        artwork: [{ src: "/static/listen-art.png", sizes: "512x512", type: "image/png" }]
      });
    } catch (e) {}
  }
  function positionState() {
    if (!("mediaSession" in navigator) || !navigator.mediaSession.setPositionState || !lesson) return;
    var d = audio.duration;
    if (!(d > 0) || !isFinite(d)) return;
    try { navigator.mediaSession.setPositionState({ duration: d, playbackRate: audio.playbackRate, position: Math.min(audio.currentTime, d) }); } catch (e) {}
  }
  if ("mediaSession" in navigator) {
    var actions = {
      play: function () { audio.play().catch(function () {}); },
      pause: function () { audio.pause(); },
      seekbackward: function (e) { skip(-((e && e.seekOffset) || BACK)); },
      seekforward: function (e) { skip((e && e.seekOffset) || FORWARD); },
      seekto: function (e) { if (e && e.seekTime != null) seek(e.seekTime); },
      previoustrack: function () { chapter(-1); },
      nexttrack: function () { chapter(1); },
      stop: function () { audio.pause(); }
    };
    Object.keys(actions).forEach(function (a) { try { navigator.mediaSession.setActionHandler(a, actions[a]); } catch (e) {} });
  }

  // ------------------------------------------------------------ audio element events
  var lastChapter = -1;
  audio.addEventListener("timeupdate", function () {
    if (!lesson) return;
    var i = chapterIndex(audio.currentTime);
    if (i !== lastChapter) { lastChapter = i; setMetadata(); }
    if (!audio.paused && Date.now() - lastSaved > SAVE_EVERY) save();
    emit("time");
  });
  audio.addEventListener("loadedmetadata", function () { positionState(); emit("time"); });
  audio.addEventListener("play", function () {
    if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "playing";
    positionState();
    emit("play");
  });
  audio.addEventListener("pause", function () {
    if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "paused";
    save();
    emit("pause");
  });
  audio.addEventListener("seeked", function () { positionState(); save(); });
  audio.addEventListener("ended", function () { save(); advance(); });
  audio.addEventListener("error", function () { emit("error"); });
  window.addEventListener("pagehide", function () { if (lesson) save(true); });

  // After a full page load, come back paused where we were.
  try {
    var saved = JSON.parse(stored(STORE) || "null");
    if (saved && saved.lesson && saved.lesson.src) load(saved.lesson, { queue: saved.queue || [] });
  } catch (e) {}

  // ------------------------------------------------------------ page controls (delegated: they survive body swaps)
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-listen], [data-player]");
    if (!b) return;
    if (b.hasAttribute("data-listen")) {
      // A lesson's Listen or Watch button: start it now, inside the tap (iOS), then let a Watch link navigate.
      // data-listen-paused (the lesson bar's Listen) only loads it into the mini player, paused.
      var desc;
      try { desc = JSON.parse(b.getAttribute("data-listen")); } catch (err) { return; }
      var q = b.getAttribute("data-listen-queue");
      load(desc, { autoplay: !b.hasAttribute("data-listen-paused"), queue: q ? JSON.parse(q) : undefined });
      if (b.tagName !== "A") e.preventDefault();
      return;
    }
    var act = b.getAttribute("data-player");
    if (act === "toggle") toggle();
    else if (act === "back") skip(-BACK);
    else if (act === "forward") skip(FORWARD);
    else if (act === "prev") chapter(-1);
    else if (act === "next") chapter(1);
    else if (act === "speed") {
      var v = parseFloat(b.getAttribute("data-speed"));
      if (v) setSpeed(v); else cycleSpeed();
      var menu = b.closest("[data-speed-menu]");
      if (menu) menu.open = false;
    }
    else if (act === "stop") stop();
    else if (act === "chapter") seek(parseFloat(b.getAttribute("data-t")) || 0);
    else return;
    e.preventDefault();
  });

  // Speed menus (_player.html): the label shows the current speed and the menu marks it.
  function markSpeed(root, s) {
    root.querySelectorAll("[data-speed-label]").forEach(function (el) { el.textContent = (s % 1 ? s : s.toFixed(0)) + "×"; });
    root.querySelectorAll("[data-speed]").forEach(function (el) {
      el.setAttribute("aria-checked", String(parseFloat(el.getAttribute("data-speed")) === s));
    });
  }
  // An open player menu closes on a click outside it or on Escape.
  function closeMenus(except) {
    document.querySelectorAll("details[data-speed-menu][open], details.mp-menu[open]").forEach(function (d) {
      if (!except || !d.contains(except)) d.open = false;
    });
  }
  document.addEventListener("click", function (e) { closeMenus(e.target); }, true);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeMenus(null); });

  // The mini player in base.html: shown whenever something is loaded, except on the Watch page (it has its own).
  function bindMini(root) {
    var mini = root.querySelector ? root.querySelector("[data-miniplayer]") : null;
    if (!mini && root.matches && root.matches("[data-miniplayer]")) mini = root;
    if (!mini) return;
    var title = mini.querySelector("[data-mp-title]"), sub = mini.querySelector("[data-mp-sub]"),
        bar = mini.querySelector("[data-mp-bar]"), time = mini.querySelector("[data-mp-time]"),
        chList = mini.querySelector("[data-mp-chapters]"),
        lessonLink = mini.querySelector("[data-mp-lesson]"), watchLink = mini.querySelector("[data-mp-watch]"),
        scrub = mini.querySelector("[data-mp-scrub]");
    var shownSid = null, lastCh = -1, lastSpeed = null;
    if (scrub) {
      scrub.addEventListener("input", function () { var d = audio.duration || (lesson && lesson.duration) || 0; seek(d * scrub.value / 1000); });
    }
    subscribe(mini, function (s) {
      var onWatch = !!document.querySelector("[data-watch-page]");
      mini.hidden = !s.lesson || onWatch;
      document.documentElement.toggleAttribute("data-player-open", !mini.hidden);
      if (!s.lesson) return;
      mini.toggleAttribute("data-playing", !s.paused);
      if (shownSid !== s.lesson.sid) {
        shownSid = s.lesson.sid; lastCh = -1;
        if (title) title.textContent = s.lesson.title;
        if (lessonLink) lessonLink.href = s.lesson.lesson_url;
        if (watchLink) watchLink.href = s.lesson.watch_url;
        if (chList) {
          chList.textContent = "";
          (s.lesson.chapters || []).forEach(function (c, i) {
            var li = document.createElement("li"), btn = document.createElement("button");
            btn.type = "button"; btn.className = "mp-chapter"; btn.setAttribute("data-player", "chapter"); btn.setAttribute("data-t", c.t);
            btn.innerHTML = "<span></span><time></time>";
            btn.firstChild.textContent = c.title; btn.lastChild.textContent = fmt(c.t);
            li.appendChild(btn); chList.appendChild(li);
          });
        }
      }
      var ci = chapterIndex(s.time);
      if (ci !== lastCh) {
        lastCh = ci;
        var ch = s.lesson.chapters && s.lesson.chapters[ci];
        if (sub) sub.textContent = s.lesson.sid + (ch ? " · " + ch.title : "");
        if (chList) Array.prototype.forEach.call(chList.children, function (li, i) { li.toggleAttribute("data-current", i === ci); });
      }
      var d = s.duration || 0;
      if (bar) bar.style.setProperty("--p", d ? (100 * s.time / d).toFixed(2) + "%" : "0%");
      if (scrub && document.activeElement !== scrub) scrub.value = d ? Math.round(1000 * s.time / d) : 0;
      if (time) time.textContent = fmt(s.time) + " / " + fmt(d);
      if (s.speed !== lastSpeed) { lastSpeed = s.speed; markSpeed(mini, s.speed); }
    });
  }

  // Watch mode (watch.html): the visual whose cue was last passed, the chapter title between cues, and the caption.
  function bindWatch(root) {
    var page = root.querySelector ? root.querySelector("[data-watch-page]") : null;
    if (!page) return;
    var desc = JSON.parse(page.querySelector("[data-watch-lesson]").textContent);
    var tl = JSON.parse(page.querySelector("[data-watch-timeline]").textContent);
    var visuals = {};
    page.querySelectorAll("[data-visual-key]").forEach(function (v) { visuals[v.getAttribute("data-visual-key")] = v; });
    var card = page.querySelector("[data-watch-card]"), cardTitle = page.querySelector("[data-watch-chapter]"),
        caption = page.querySelector("[data-watch-caption]"), bar = page.querySelector("[data-watch-bar]"),
        time = page.querySelector("[data-watch-time]"), cover = page.querySelector("[data-watch-start]"),
        scrub = page.querySelector("[data-watch-scrub]");
    if (!lesson || lesson.sid !== desc.sid) load(desc, { autoplay: false });
    if (scrub) scrub.addEventListener("input", function () { seek((audio.duration || desc.duration || 0) * scrub.value / 1000); });

    function lastBefore(list, t) {   // index of the last item with item.t <= t (lists are sorted by t)
      var lo = 0, hi = list.length - 1, ans = -1;
      while (lo <= hi) { var mid = (lo + hi) >> 1; if (list[mid].t <= t + 0.05) { ans = mid; lo = mid + 1; } else hi = mid - 1; }
      return ans;
    }
    var shown = null, lastCap = -2, lastChap = -2, wake = null, lastSpeed = null;
    function wakeLock(on) {
      if (on && !wake && navigator.wakeLock) navigator.wakeLock.request("screen").then(function (w) { wake = w; w.addEventListener("release", function () { wake = null; }); }).catch(function () {});
      if (!on && wake) { wake.release().catch(function () {}); wake = null; }
    }
    subscribe(page, function (s) {
      if (!s.lesson || s.lesson.sid !== desc.sid) {
        // The queue moved on to the next lesson: follow it.
        // A boosted link click keeps this document (and the sound) and pushes history like any other navigation.
        if (s.lesson && s.type === "load" && window.htmx) {
          var a = document.createElement("a");
          a.href = s.lesson.watch_url; a.hidden = true;
          page.appendChild(a); htmx.process(a); a.click();
        }
        return;
      }
      page.toggleAttribute("data-playing", !s.paused);
      if (cover) cover.hidden = !s.paused;
      wakeLock(!s.paused);
      var t = s.time;
      var ci = lastBefore(tl.chapters, t), chapterStart = ci >= 0 ? tl.chapters[ci].t : 0;
      var cu = lastBefore(tl.cues, t);
      var key = cu >= 0 && tl.cues[cu].t >= chapterStart ? tl.cues[cu].kind + ":" + tl.cues[cu].slug : null;
      if (!visuals[key]) key = null;
      if (key !== shown) {
        if (shown && visuals[shown]) visuals[shown].hidden = true;
        if (key) visuals[key].hidden = false;
        shown = key;
        if (card) card.hidden = !!key;
      }
      if (ci !== lastChap) {
        lastChap = ci;
        if (cardTitle) cardTitle.textContent = ci >= 0 ? tl.chapters[ci].title : desc.title;
        page.querySelectorAll("[data-watch-chapter-title]").forEach(function (el) { el.textContent = ci >= 0 ? tl.chapters[ci].title : ""; });
      }
      var cap = lastBefore(tl.captions, t);
      if (cap !== lastCap) { lastCap = cap; if (caption) caption.textContent = cap >= 0 ? tl.captions[cap].text : ""; }
      var d = s.duration || desc.duration || 0;
      if (bar) bar.style.setProperty("--p", d ? (100 * t / d).toFixed(2) + "%" : "0%");
      if (scrub && document.activeElement !== scrub) scrub.value = d ? Math.round(1000 * t / d) : 0;
      if (time) time.textContent = fmt(t) + " / " + fmt(d);
      if (s.speed !== lastSpeed) { lastSpeed = s.speed; markSpeed(page, s.speed); }
    });
    page.addEventListener("click", function (e) {
      if (e.target.closest("[data-watch-fullscreen]")) {
        if (document.fullscreenElement) document.exitFullscreen().catch(function () {});
        else if (page.requestFullscreen) page.requestFullscreen().catch(function () {});
      }
    });
  }

  function init(root) { bindMini(root); bindWatch(root); }
  if (window.htmx) htmx.onLoad(function (el) { init(el.nodeType === 1 ? el : document); });
  else document.addEventListener("DOMContentLoaded", function () { init(document); });

  window.CasaPlayer = {
    load: load, toggle: toggle, seek: seek, skip: skip, chapter: chapter, stop: stop, setSpeed: setSpeed,
    subscribe: subscribe, current: function () { return lesson; }, queue: function () { return queue.slice(); },
    audio: audio, fmt: fmt
  };
})();
