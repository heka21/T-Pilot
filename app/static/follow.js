/* Follow along: while a lesson's narration plays on that lesson's page, highlight the passage being read and keep
   it in view. Toggled from the mini player (data-player="follow"), remembered in localStorage "listen:follow".

   The listening scripts are rewritten for the ear (content/AUDIO.md), so the spoken sentences are not the lesson's
   text. Each caption in the build's timeline (media/audio/<UNIT>/<n.n>.json) is matched to a block of the lesson
   (paragraph, list item, figure, equation...) inside the chapter's h2 section, by the share of the caption's
   distinctive words the block contains, with the blocks in reading order (a dynamic programme per chapter, so a
   sentence with no clear match stays on the block before it). A visual cue pulls the sentences after it onto
   that figure. Inside the block, the closest sentence is marked too where the CSS Custom Highlight API exists.

   The same match lets Listen start where the reader is: spot(sid, t) gives the time of the first sentence on the
   block at the top of the screen (player.js asks for it on Listen and on play), so the timeline is fetched as soon
   as a narrated lesson's page opens rather than when its audio first plays.

   window.CasaFollow = {enabled(), set(on), align(timeline, article), sentence(block, text) -> Range,
                        spot(sid, t) -> seconds or null} */
(function () {
  "use strict";

  var KEY = "listen:follow";
  var HIGHLIGHT = "casa-reading";
  var BLOCKS = "p, li, h3, h4, figure, tr, dt, dd, div.arithmatex, summary";
  var JUMP = 0.04;           // cost of moving on to a later block, so a weak match does not move the highlight
  var CUE_BONUS = 0.6;       // for the sentences just after a visual's cue, on that visual
  var CUE_SPAN = 3;          // sentences after a cue that get the bonus
  var SENTENCE_MIN = 0.3;    // weakest match that still marks a sentence inside the block
  var HANDS_OFF = 8000;      // ms after the reader scrolls before following resumes

  function stored() { try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; } }
  var on = stored();

  // ------------------------------------------------------------ matching
  var STOP = {};
  ("a an and are as at be but by can do does for from has have he her his how i if in into is it its it's just let's " +
   "more most no not now of on one or so than that the their them then there these they this those to too up us was " +
   "we what when where which while who why will with you your you'll you're also only very just here same each").split(" ")
    .forEach(function (w) { STOP[w] = 1; });

  function tokens(text) {
    var out = [];
    (String(text).toLowerCase().replace(/[’']/g, "'").match(/[a-z0-9][a-z0-9']*/g) || []).forEach(function (w) {
      w = w.replace(/'s$/, "");
      if (STOP[w] || (w.length < 2 && !/\d/.test(w))) return;
      if (w.length > 4 && /[^s]s$/.test(w)) w = w.slice(0, -1);    // blades ~ blade
      out.push(w);
    });
    return out;
  }
  function bag(text) { var b = {}; tokens(text).forEach(function (w) { b[w] = 1; }); return b; }

  // Share of the caption's word weight found in the block (0..1).
  function similarity(cap, block, idf) {
    var total = 0, hit = 0;
    for (var w in cap) { var x = idf(w); total += x; if (block[w]) hit += x; }
    return total ? hit / total : 0;
  }

  // The text a block is matched on: a figure by its caption and title, not by a widget's controls.
  function blockText(el) {
    if (el.tagName === "FIGURE") {
      var cap = el.querySelector("figcaption"), img = el.querySelector("[alt], [title], [aria-label]");
      return [cap && cap.textContent, img && (img.getAttribute("alt") || img.getAttribute("title") || img.getAttribute("aria-label")),
              (el.getAttribute("data-visual") || "").replace(/^[a-z]+:/, "").replace(/-/g, " ")].join(" ");
    }
    return el.textContent;
  }

  // The leaf blocks of the article, in order, grouped by the h2 they sit under ("top" before the first h2).
  function sections(article) {
    var all = Array.prototype.slice.call(article.querySelectorAll(BLOCKS + ", h2"));
    var out = { top: [] }, current = out.top;
    all.forEach(function (el) {
      if (el.tagName === "H2") { current = out[el.id] = []; return; }
      for (var p = el.parentElement; p && p !== article; p = p.parentElement) if (p.tagName === "FIGURE") return;
      // A list item or cell that wraps paragraphs is matched through them, unless it has text of its own.
      if (el.tagName !== "FIGURE" && el.querySelector(BLOCKS)) {
        var own = Array.prototype.some.call(el.childNodes, function (n) { return n.nodeType === 3 && n.textContent.trim().length > 20; });
        if (!own) return;
      }
      if (!el.textContent.trim()) return;
      current.push(el);
    });
    return out;
  }

  /* For each caption, the block it is matched to (null where none): {blocks: [el...], at: [index into blocks]}.
     timeline: {chapters: [{id, t}], captions: [{t, text}], cues: [{kind, slug, t}]}. */
  function align(timeline, article) {
    var caps = timeline.captions || [], chs = timeline.chapters || [], cues = timeline.cues || [];
    var secs = sections(article), blocks = [], at = new Array(caps.length).fill(null);
    var docs = {}, nDocs = 0;
    var bags = new Map();
    Object.keys(secs).forEach(function (id) {
      secs[id].forEach(function (el) {
        var b = bag(blockText(el)); bags.set(el, b); nDocs++;
        for (var w in b) docs[w] = (docs[w] || 0) + 1;
      });
    });
    function idf(w) { return Math.log(1 + nDocs / (1 + (docs[w] || 0))); }

    // Captions just after a cue lean towards that visual.
    var bonus = new Array(caps.length);
    cues.forEach(function (c) {
      var k = 0;
      while (k < caps.length && caps[k].t < c.t - 0.05) k++;
      for (var j = k; j < Math.min(caps.length, k + CUE_SPAN); j++) bonus[j] = c.kind + ":" + c.slug;
    });

    chs.forEach(function (ch, ci) {
      var list = secs[ch.id] || [];
      var end = ci + 1 < chs.length ? chs[ci + 1].t : Infinity;
      var idx = [];
      caps.forEach(function (c, k) { if (c.t >= ch.t - 0.05 && c.t < end - 0.05) idx.push(k); });
      if (!list.length || !idx.length) return;
      var m = list.length, base = blocks.length;
      Array.prototype.push.apply(blocks, list);
      var keys = list.map(function (el) { return el.getAttribute("data-visual"); });
      // score[i][j]: best total with caption i on block j; blocks never go backwards.
      var prev = null, from = [];
      idx.forEach(function (k, i) {
        var cap = bag(caps[k].text), row = new Array(m), back = new Array(m);
        var best = -Infinity, bestJ = 0;
        for (var j = 0; j < m; j++) {
          var s = similarity(cap, bags.get(list[j]), idf) + (bonus[k] && keys[j] === bonus[k] ? CUE_BONUS : 0);
          if (!prev) { row[j] = s - (j ? JUMP : 0); back[j] = -1; continue; }
          if (j > 0 && prev[j - 1] > best) { best = prev[j - 1]; bestJ = j - 1; }
          var stay = prev[j], move = best - JUMP;
          // On a tie, move late: the highlight changes when the matching sentence starts.
          if (stay > move + 1e-9) { row[j] = stay + s; back[j] = j; } else { row[j] = move + s; back[j] = bestJ; }
        }
        from.push(back); prev = row;
      });
      var j = 0;
      for (var q = 1; q < m; q++) if (prev[q] > prev[j]) j = q;
      for (var i = idx.length - 1; i >= 0; i--) { at[idx[i]] = base + j; if (i) j = from[i][j]; }
    });
    return { blocks: blocks, at: at };
  }

  // ------------------------------------------------------------ marking the page
  var supportsHighlight = typeof CSS !== "undefined" && CSS.highlights && typeof Highlight === "function";

  // The range of the sentence in `el` that best matches `text`, or null.
  function sentenceRange(el, text) {
    if (!supportsHighlight || el.tagName === "FIGURE") return null;
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), nodes = [], full = "", n;
    while ((n = walker.nextNode())) {
      if (n.parentElement && n.parentElement.closest(".katex-mathml, script, style")) continue;
      nodes.push({ node: n, start: full.length }); full += n.textContent;
    }
    // Sentences, and clauses after a semicolon or colon: the scripts split long lesson sentences into short ones.
    var re = /[.!?]+["')\]]*(?=\s)|[;:](?=\s)/g, m, cap = bag(text), best = null, bestScore = SENTENCE_MIN;
    var parts = [], from = 0;
    function part(a, b) { if (full.slice(a, b).trim()) parts.push({ start: a, end: b, text: full.slice(a, b) }); }
    while ((m = re.exec(full))) { part(from, m.index + m[0].length); from = m.index + m[0].length; }
    part(from, full.length);
    if (parts.length < 2) return null;
    var docs = {}; parts.forEach(function (p) { p.bag = bag(p.text); for (var w in p.bag) docs[w] = (docs[w] || 0) + 1; });
    var idf = function (w) { return Math.log(1 + parts.length / (1 + (docs[w] || 0))) + 0.2; };
    parts.forEach(function (p) { var s = similarity(cap, p.bag, idf); if (s > bestScore) { bestScore = s; best = p; } });
    if (!best) return null;
    while (/\s/.test(full[best.start]) && best.start < best.end) best.start++;
    function point(off, isEnd) {
      for (var i = nodes.length - 1; i >= 0; i--) {
        if (nodes[i].start < off || (!isEnd && nodes[i].start === off)) return { node: nodes[i].node, offset: Math.min(off - nodes[i].start, nodes[i].node.length) };
      }
      return { node: nodes[0].node, offset: 0 };
    }
    var a = point(best.start, false), b = point(best.end, true), r = document.createRange();
    try { r.setStart(a.node, a.offset); r.setEnd(b.node, b.offset); } catch (e) { return null; }
    return r;
  }

  var page = null;   // {sid, article, map, timeline, current: el, cap}
  var cache = {};    // sid -> timeline promise
  var handsOffUntil = 0;

  function timelineFor(lesson) {
    if (!cache[lesson.sid]) {
      var url = lesson.src.replace(/\.mp3(\?|#|$)/, ".json$1");
      cache[lesson.sid] = fetch(url).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { delete cache[lesson.sid]; return null; });
    }
    return cache[lesson.sid];
  }

  function clear() {
    if (page && page.current) page.current.removeAttribute("data-reading");
    if (page) { page.current = null; page.cap = -1; }
    if (supportsHighlight) CSS.highlights.delete(HIGHLIGHT);
  }

  function capIndex(caps, t) {
    var lo = 0, hi = caps.length - 1, ans = -1;
    while (lo <= hi) { var mid = (lo + hi) >> 1; if (caps[mid].t <= t + 0.05) { ans = mid; lo = mid + 1; } else hi = mid - 1; }
    return ans;
  }

  // What to mark for a block: a paragraph inside a closed "Check yourself" box marks the box's summary.
  function visible(el) {
    var d = el.closest("details:not([open])");
    return d ? (d.querySelector("summary") || d) : el;
  }

  // The part of the window the reader sees text in: below the top bar and above the mini player.
  function viewport() {
    var vh = window.innerHeight;
    var bar = document.querySelector(".topbar"), top = bar ? bar.getBoundingClientRect().bottom : 0;
    var player = document.querySelector("[data-miniplayer]:not([hidden])");
    var bottom = player ? Math.min(vh, player.getBoundingClientRect().top) : vh;
    if (player && player.getBoundingClientRect().top < vh / 2) bottom = vh;     // dragged to the top: it is not in the way
    return { top: top, bottom: bottom };
  }

  function keepInView(el, smooth) {
    if (Date.now() < handsOffUntil) return;
    var r = el.getBoundingClientRect(), v = viewport(), top = v.top, bottom = v.bottom;
    if (r.top >= top + 16 && r.bottom <= bottom - 16) return;
    var y = window.scrollY + r.top - top - Math.max(24, (bottom - top) * 0.2);
    window.scrollTo({ top: Math.max(0, y), behavior: smooth && !matchMedia("(prefers-reduced-motion: reduce)").matches ? "smooth" : "auto" });
  }

  function update(s) {
    if (!page || !page.map || !on || !s.lesson || s.lesson.sid !== page.sid) { clear(); return; }
    var k = capIndex(page.timeline.captions || [], s.time);
    if (k === page.cap) return;
    page.cap = k;
    var i = k >= 0 ? page.map.at[k] : null, el = i == null ? null : visible(page.map.blocks[i]);
    if (el !== page.current) {
      if (page.current) page.current.removeAttribute("data-reading");
      if (el) el.setAttribute("data-reading", "");
      page.current = el;
      if (el && !s.paused) keepInView(el, true);
    }
    if (supportsHighlight) {
      var range = el && el === page.map.blocks[i] ? sentenceRange(el, page.timeline.captions[k].text) : null;
      if (range) CSS.highlights.set(HIGHLIGHT, new Highlight(range)); else CSS.highlights.delete(HIGHLIGHT);
    }
  }

  function bind(root) {
    var article = document.querySelector("[data-lesson-article]");
    var host = article && article.closest("[data-sid]");
    if (!article || !host || !window.CasaPlayer) { if (page && !page.article.isConnected) { clear(); page = null; } return; }
    if (page && page.article === article) return;
    if (page) clear();
    page = { sid: host.getAttribute("data-sid"), article: article, map: null, timeline: null, current: null, cap: -1 };
    var mine = page, last = null;
    function fetchFor(lesson) {
      if (mine.loading) return;
      mine.loading = true;
      timelineFor(lesson).then(function (tl) {
        if (!tl || page !== mine || mine.timeline) return;      // no timeline: leave this page alone
        mine.loading = false;
        mine.timeline = tl; mine.map = align(tl, article);
        if (last) update(last);
      });
    }
    // Ready before the first tap on Listen, which has to start the sound synchronously (iOS).
    var desc = lessonOnPage(mine.sid);
    if (desc) fetchFor(desc);
    window.CasaPlayer.subscribe(article, function (s) {
      last = s;
      if (page !== mine) return;
      if (!s.lesson || s.lesson.sid !== mine.sid) { clear(); return; }
      if (!mine.timeline) { fetchFor(s.lesson); return; }
      if (s.type === "play") handsOffUntil = 0;
      update(s);
      if (s.type === "play" && on && mine.current) keepInView(mine.current, true);
    });
  }

  // The lesson descriptor on a Listen button of this page (note.html), if the lesson is narrated.
  function lessonOnPage(sid) {
    var b = document.querySelector("[data-listen]"), d;
    try { d = b && JSON.parse(b.getAttribute("data-listen")); } catch (e) { return null; }
    return d && d.sid === sid && d.src ? d : null;
  }

  // Where to start the narration of `sid` for a reader looking at its page: the first sentence on the block at the
  // top of the screen. null (keep the place `t` it would resume from) off that page, before the timeline is in,
  // while the reader is still at the start, or when the block being read at `t` is on screen.
  function spot(sid, t) {
    if (!page || page.sid !== sid || !page.map || !page.article.isConnected) return null;
    var caps = page.timeline.captions || [], map = page.map, v = viewport();
    var line = v.top + Math.min(80, (v.bottom - v.top) * 0.15);
    function onScreen(el) {
      var r = el.getBoundingClientRect();
      return (r.width || r.height) && r.bottom > v.top && r.top < v.bottom;
    }
    var k = capIndex(caps, t || 0), now = k >= 0 && map.at[k] != null ? visible(map.blocks[map.at[k]]) : null;
    if (now && onScreen(now)) return null;
    // The first block not yet scrolled past the reading line (one in a closed box counts as its summary).
    var at = -1;
    for (var i = 0; i < map.blocks.length; i++) {
      var r = visible(map.blocks[i]).getBoundingClientRect();
      if ((r.width || r.height) && r.bottom > line) { at = i; break; }
    }
    if (at <= 0) return null;
    // Its first sentence, or the next one narrated after it.
    for (var c = 0; c < caps.length; c++) if (map.at[c] != null && map.at[c] >= at) return Math.max(0, caps[c].t - 0.2);
    return null;
  }

  // A reader scrolling the page themselves pauses the scrolling (not the highlight) for a while; pressing play, or
  // any player control (a chapter, back, forward), brings it back.
  function handsOff() { handsOffUntil = Date.now() + HANDS_OFF; }
  window.addEventListener("wheel", handsOff, { passive: true });
  window.addEventListener("touchmove", handsOff, { passive: true });
  window.addEventListener("keydown", function (e) { if (/^(Arrow|Page|Home|End| )/.test(e.key) && !e.target.closest("input, textarea, [contenteditable]")) handsOff(); });

  function mark(root) {
    (root || document).querySelectorAll('[data-player="follow"]').forEach(function (b) { b.setAttribute("aria-pressed", String(on)); });
  }
  function set(value) {
    on = !!value;
    try { localStorage.setItem(KEY, on ? "1" : "0"); } catch (e) {}
    mark(document);
    handsOffUntil = 0;
    if (!on) clear();
    else if (page && window.CasaPlayer) {
      page.cap = -2;
      var a = window.CasaPlayer.audio, l = window.CasaPlayer.current();
      if (l) update({ lesson: l, time: a.currentTime || 0, paused: a.paused });
      if (page.current) keepInView(page.current, true);
    }
  }

  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-player]");
    if (!b) return;
    handsOffUntil = 0;
    if (b.getAttribute("data-player") !== "follow") return;
    e.preventDefault();
    set(!on);
  });

  function init(root) { mark(root.querySelectorAll ? root : document); bind(root); }
  if (window.htmx) htmx.onLoad(function (el) { init(el.nodeType === 1 ? el : document); });
  else document.addEventListener("DOMContentLoaded", function () { init(document); });

  window.CasaFollow = { enabled: function () { return on; }, set: set, align: align, sentence: sentenceRange, spot: spot };
})();
