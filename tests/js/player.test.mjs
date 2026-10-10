// The narration player (app/static/player.js) under jsdom: a classic script evaluated into a fresh window per test,
// with a fake Audio (no media in jsdom), a recording fetch and sendBeacon (npm run test:js).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const SOURCE = readFileSync(new URL("../../app/static/player.js", import.meta.url), "utf8");

function lesson(sid, extra = {}) {
  const [unit, number] = sid.split(" ");
  return {
    sid, title: `Lesson ${sid}`, unit, src: `/media/audio/${unit}/${number}.mp3?v=abc`, duration: 600,
    chapters: [{ id: "top", title: "Introduction", t: 0 }, { id: "why", title: "Why this matters", t: 30 },
               { id: "key", title: "Key points", t: 500 }],
    lesson_url: `/lessons/${unit}/${number}`, watch_url: `/lessons/${unit}/${number}/watch`,
    position: 0, completed: false, ...extra,
  };
}

/** A window with player.js loaded. `storage` is put in localStorage first; `queue` is what /listen/queue returns. */
function setup({ storage = {}, queue = [], body = "" } = {}) {
  const dom = new JSDOM(`<!doctype html><html><body>${body}</body></html>`, { url: "http://localhost/", runScripts: "outside-only" });
  const w = dom.window;
  const audios = [];

  class FakeAudio extends w.EventTarget {
    constructor() {
      super();
      Object.assign(this, { src: "", currentTime: 0, duration: NaN, paused: true, playbackRate: 1, defaultPlaybackRate: 1,
                            preload: "", plays: 0, loads: 0 });
      audios.push(this);
    }
    play() { this.plays++; this.paused = false; this.fire("play"); return Promise.resolve(); }
    pause() { if (!this.paused) { this.paused = true; this.fire("pause"); } }
    load() { this.loads++; }
    removeAttribute(name) { if (name === "src") this.src = ""; }
    fire(type) { this.dispatchEvent(new w.Event(type)); }
  }
  w.Audio = FakeAudio;

  const fetches = [];
  w.fetch = (url, opts = {}) => {
    fetches.push({ url, ...opts });
    const json = String(url).startsWith("/listen/queue") ? queue : {};
    return Promise.resolve({ ok: true, json: () => Promise.resolve(json) });
  };
  const beacons = [];
  Object.defineProperty(w.navigator, "sendBeacon", { configurable: true, value: (url, data) => { beacons.push({ url, data }); return true; } });

  for (const [k, v] of Object.entries(storage)) w.localStorage.setItem(k, v);
  w.eval(SOURCE);
  const P = w.CasaPlayer;
  assert.equal(audios.length, 1, "one Audio for the session");
  return { w, P, audio: audios[0], fetches, beacons };
}

const tick = () => new Promise((r) => setTimeout(r, 0));
// Arrays from the window realm fail deepStrictEqual against node arrays (different prototypes).
const sids = (list) => Array.from(list, (d) => d.sid);
const posts = (fetches) => fetches.filter((f) => f.url === "/listen/progress");

test("load() starts from a media fragment a little before the saved position", () => {
  const { P, audio } = setup();
  P.load(lesson("RFRC 2.3", { position: 100 }));
  assert.equal(audio.src, "/media/audio/RFRC/2.3.mp3?v=abc#t=97.0");
  assert.equal(P.current().sid, "RFRC 2.3");
  assert.equal(audio.plays, 0, "no autoplay unless asked");

  const other = setup();
  other.P.load(lesson("RFRC 2.3", { position: 4 }));      // 5 s or less: from the top
  assert.equal(other.audio.src, "/media/audio/RFRC/2.3.mp3?v=abc");
});

test("autoplay calls play(), and loading the same lesson again just plays", () => {
  const { P, audio } = setup();
  P.load(lesson("RFRC 2.3"), { autoplay: true });
  assert.equal(audio.plays, 1);
  assert.equal(audio.paused, false);
  audio.pause();
  P.load(lesson("RFRC 2.3"), { autoplay: true });
  assert.equal(audio.plays, 2);
  assert.equal(audio.src, "/media/audio/RFRC/2.3.mp3?v=abc");
});

test("without a queue, the rest of the exam is fetched", async () => {
  const { P, fetches } = setup({ queue: [lesson("RFRC 2.3"), lesson("RFRC 2.5"), lesson("RMTC 1.1")] });
  P.load(lesson("RFRC 2.3"));
  assert.equal(fetches[0].url, "/listen/queue?scope=exam&start=RFRC%202.3");
  await tick();
  assert.deepEqual(sids(P.queue()), ["RFRC 2.5", "RMTC 1.1"]);
});

test("chapter(1) and chapter(-1) seek to chapter starts; previous restarts the chapter when more than 4 s in", () => {
  const { P, audio } = setup();
  P.load(lesson("RFRC 2.3"));
  audio.currentTime = 35;                // 5 s into "Why this matters"
  P.chapter(1);
  assert.equal(audio.currentTime, 500);
  audio.currentTime = 35;
  P.chapter(-1);
  assert.equal(audio.currentTime, 30, "restart the current chapter");
  audio.currentTime = 32;                // near its start: go to the previous one
  P.chapter(-1);
  assert.equal(audio.currentTime, 0);
  P.chapter(-1);                         // at the first chapter: stays at 0
  assert.equal(audio.currentTime, 0);
});

test("ended advances to the next queued lesson and plays it", () => {
  const { P, audio, fetches } = setup();
  const q = [lesson("RFRC 2.3"), lesson("RFRC 2.5"), lesson("RMTC 1.1")];
  P.load(q[0], { autoplay: true, queue: q.slice(1) });
  assert.equal(fetches.length, 0, "a given queue is not fetched");
  audio.currentTime = 599.5;
  audio.paused = true;
  audio.fire("ended");
  assert.equal(P.current().sid, "RFRC 2.5");
  assert.equal(audio.src, "/media/audio/RFRC/2.5.mp3?v=abc");
  assert.equal(audio.plays, 2);
  assert.deepEqual(sids(P.queue()), ["RMTC 1.1"]);
  assert.deepEqual(JSON.parse(posts(fetches)[0].body), { sid: "RFRC 2.3", position: 599.5, duration: 600 });
});

test("next chapter from the last chapter moves on to the next lesson", () => {
  const { P, audio } = setup();
  P.load(lesson("RFRC 2.3"), { queue: [lesson("RFRC 2.5")] });
  audio.currentTime = 550;
  P.chapter(1);
  assert.equal(P.current().sid, "RFRC 2.5");
});

test("progress is POSTed as JSON on pause, and beaconed on pagehide", () => {
  const { w, P, audio, fetches, beacons } = setup();
  P.load(lesson("RFRC 2.3"), { autoplay: true, queue: [] });
  audio.currentTime = 123.4;
  audio.pause();
  const [post] = posts(fetches);
  assert.equal(post.method, "POST");
  assert.equal(post.headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(post.body), { sid: "RFRC 2.3", position: 123.4, duration: 600 });
  // The place is also kept locally, so a full page load comes back to it.
  const saved = JSON.parse(w.localStorage.getItem("listen:current"));
  assert.equal(saved.lesson.position, 123.4);

  w.dispatchEvent(new w.Event("pagehide"));
  assert.equal(beacons.length, 1);
  assert.equal(beacons[0].url, "/listen/progress");
});

test("nothing is saved before playback has started", () => {
  const { P, audio, fetches } = setup();
  P.load(lesson("RFRC 2.3"), { autoplay: true, queue: [] });
  audio.pause();                          // currentTime is still 0
  assert.equal(posts(fetches).length, 0);
});

test("the speed cycles and persists to localStorage", () => {
  const { w, P, audio } = setup();
  P.load(lesson("RFRC 2.3"), { queue: [] });
  const btn = w.document.createElement("button");
  btn.setAttribute("data-player", "speed");
  w.document.body.appendChild(btn);
  btn.click();
  assert.equal(audio.playbackRate, 1.1);
  btn.click();
  assert.equal(audio.playbackRate, 1.25);
  assert.equal(audio.defaultPlaybackRate, 1.25);
  assert.equal(w.localStorage.getItem("listen:speed"), "1.25");
  for (let i = 0; i < 5; i++) btn.click();  // 1.5, 1.75, 2, then round to 0.8 and 1
  assert.equal(audio.playbackRate, 1);

  const next = setup({ storage: { "listen:speed": "1.5" } });
  next.P.load(lesson("RFRC 2.3"), { queue: [] });
  assert.equal(next.audio.playbackRate, 1.5);
  assert.equal(next.audio.defaultPlaybackRate, 1.5);
});

test("the speed menu sets the chosen speed, marks it, and closes", () => {
  const options = ["0.8", "1", "1.25", "1.5"].map((v) =>
    `<button data-player="speed" data-speed="${v}" aria-checked="false">${v}×</button>`).join("");
  const { w, P, audio } = setup({ body: `<div data-miniplayer hidden><details class="mp-menu" open>
    <details data-speed-menu open><summary><span data-speed-label>1×</span></summary>${options}</details>
    </details></div><p id="outside">x</p>` });
  w.document.dispatchEvent(new w.Event("DOMContentLoaded"));   // bindMini, as htmx.onLoad would
  P.load(lesson("RFRC 2.3"), { queue: [] });
  const menu = w.document.querySelector("[data-speed-menu]"), outer = w.document.querySelector(".mp-menu");
  w.document.querySelector('[data-speed="1.5"]').click();
  assert.equal(audio.playbackRate, 1.5);
  assert.equal(w.localStorage.getItem("listen:speed"), "1.5");
  assert.equal(menu.open, false, "choosing a speed closes the speed menu");
  assert.equal(outer.open, true, "but not the player menu it sits in");
  assert.equal(w.document.querySelector("[data-speed-label]").textContent, "1.5×");
  const checked = Array.from(w.document.querySelectorAll("[data-speed]"), (b) => b.getAttribute("aria-checked"));
  assert.deepEqual(checked, ["false", "false", "false", "true"]);

  menu.open = true;
  w.document.getElementById("outside").click();
  assert.equal(menu.open, false, "a click outside closes open menus");
  assert.equal(outer.open, false);
  outer.open = true;
  w.document.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Escape" }));
  assert.equal(outer.open, false, "Escape closes them too");
});

test("stop() clears the lesson, the queue and the stored place", () => {
  const { w, P, audio } = setup();
  P.load(lesson("RFRC 2.3"), { autoplay: true, queue: [lesson("RFRC 2.5")] });
  assert.ok(w.localStorage.getItem("listen:current"));
  P.stop();
  assert.equal(P.current(), null);
  assert.equal(P.queue().length, 0);
  assert.equal(audio.paused, true);
  assert.equal(audio.src, "");
  assert.equal(audio.loads, 1);
  assert.equal(w.localStorage.getItem("listen:current"), null);
});

test("after a full page load the stored lesson comes back paused", () => {
  const stored = JSON.stringify({ lesson: lesson("RFRC 2.3", { position: 200 }), queue: [lesson("RFRC 2.5")] });
  const { P, audio } = setup({ storage: { "listen:current": stored } });
  assert.equal(P.current().sid, "RFRC 2.3");
  assert.equal(audio.src, "/media/audio/RFRC/2.3.mp3?v=abc#t=197.0");
  assert.equal(audio.plays, 0);
  assert.deepEqual(sids(P.queue()), ["RFRC 2.5"]);
});

test("clicking a [data-listen] button loads and plays that lesson with its queue", () => {
  const { w, P, audio } = setup({ body: '<button type="button" id="play"><span id="inner">Play unit</span></button>' });
  const btn = w.document.getElementById("play");
  btn.setAttribute("data-listen", JSON.stringify(lesson("RFRC 2.3")));
  btn.setAttribute("data-listen-queue", JSON.stringify([lesson("RFRC 2.3"), lesson("RFRC 2.5")]));
  const ev = new w.MouseEvent("click", { bubbles: true, cancelable: true });
  w.document.getElementById("inner").dispatchEvent(ev);   // a tap on the label inside the button
  assert.equal(P.current().sid, "RFRC 2.3");
  assert.equal(audio.plays, 1);
  assert.deepEqual(sids(P.queue()), ["RFRC 2.5"], "the started lesson is dropped from its queue");
  assert.equal(ev.defaultPrevented, true);

  const toggle = w.document.createElement("button");
  toggle.setAttribute("data-player", "toggle");
  w.document.body.appendChild(toggle);
  toggle.click();
  assert.equal(audio.paused, true);
  toggle.click();
  assert.equal(audio.paused, false);
});

test("on a lesson's page, Listen and play start from the passage the reader is on (follow.js's spot)", () => {
  const { w, P, audio } = setup({ body: '<button type="button" id="listen"></button><button type="button" id="toggle" data-player="toggle"></button>' });
  const asked = [];
  let spot = 120;
  w.CasaFollow = { spot: (sid, t) => { asked.push([sid, t]); return spot; } };
  const listen = w.document.getElementById("listen");
  listen.setAttribute("data-listen", JSON.stringify(lesson("RFRC 2.3", { position: 300 })));
  listen.setAttribute("data-listen-paused", "");
  listen.click();
  assert.deepEqual(asked[0], ["RFRC 2.3", 300], "asked against the place it would resume from");
  assert.equal(audio.src, "/media/audio/RFRC/2.3.mp3?v=abc#t=120.0", "starts at the spot, not 3 s before it");
  assert.equal(audio.plays, 0);

  // Paused and loaded: play jumps to where the reader has scrolled to, then plays.
  audio.duration = 600; audio.currentTime = 130;
  spot = 400;
  w.document.getElementById("toggle").click();
  assert.equal(audio.currentTime, 400);
  assert.equal(audio.paused, false);
  // Playing: the toggle only pauses.
  w.document.getElementById("toggle").click();
  assert.equal(audio.currentTime, 400);
  assert.equal(audio.paused, true);
  // No spot (the passage being read is on screen, or another page): resume where it was.
  spot = null;
  w.document.getElementById("toggle").click();
  assert.equal(audio.currentTime, 400);

  P.stop();
  P.load(lesson("RFRC 2.3", { position: 300 }), { at: 0 });
  assert.equal(audio.src, "/media/audio/RFRC/2.3.mp3?v=abc", "a spot at the very start needs no fragment");
});

test("on a lesson's page the player is the lesson bar's flyout, opened and closed by its Listen button", () => {
  const desc = JSON.stringify(lesson("RFRC 2.3")).replace(/"/g, "&quot;");
  const { w, P, audio } = setup({ body: `<div data-miniplayer data-floater="player" hidden><button data-player="collapse" hidden>fold</button></div>
    <div data-lesson-bar><button type="button" id="dock" data-listen="${desc}" data-listen-paused data-player-dock title="Listen"></button></div>` });
  w.document.dispatchEvent(new w.Event("DOMContentLoaded"));
  const html = w.document.documentElement, mini = w.document.querySelector("[data-miniplayer]"),
        fold = w.document.querySelector("[data-player='collapse']"), dock = w.document.getElementById("dock"),
        bar = w.document.querySelector("[data-lesson-bar]");
  assert.equal(mini.parentElement, bar, "the player moves into the lesson bar");
  assert.ok(!mini.hasAttribute("data-floater") && mini.hasAttribute("data-no-drag"), "it no longer drags on its own");
  assert.equal(fold.hidden, false);

  dock.click();
  assert.equal(mini.hidden, false, "Listen loads the lesson and opens the flyout");
  assert.equal(audio.plays, 0);
  assert.ok(!html.hasAttribute("data-player-open"), "no room kept at the bottom for a flyout");
  assert.ok(html.hasAttribute("data-player-docked"));
  assert.equal(dock.getAttribute("aria-expanded"), "true");
  assert.equal(dock.title, "Hide the player");

  dock.click();
  assert.equal(mini.hidden, true, "a second tap closes it");
  assert.equal(w.localStorage.getItem("player:collapsed"), "1");
  assert.equal(dock.getAttribute("aria-expanded"), "false");
  assert.equal(dock.title, "Show the player");

  audio.duration = 600; audio.currentTime = 150;
  P.toggle();
  audio.fire("timeupdate");
  assert.equal(bar.style.getPropertyValue("--p"), "25.00%", "the bar carries the progress for the ring");
  assert.ok(html.hasAttribute("data-player-playing"));

  dock.click();
  assert.equal(mini.hidden, false, "and a tap opens it again");
  assert.equal(audio.paused, false, "without touching playback");
  assert.equal(audio.currentTime, 150);
  assert.equal(w.localStorage.getItem("player:collapsed"), null);

  fold.click();
  assert.equal(mini.hidden, true, "the fold button closes it too");

  P.stop();
  assert.ok(!dock.hasAttribute("aria-expanded"));
  assert.equal(dock.title, "Listen");
  assert.ok(!html.hasAttribute("data-player-docked"));
});

test("a closed player stays a bar where there is no lesson bar, and starting a lesson opens it", () => {
  const { w, P } = setup({ storage: { "player:collapsed": "1" },
                           body: '<div data-miniplayer hidden><button data-player="collapse">fold</button></div><button type="button" id="play"></button>' });
  w.document.dispatchEvent(new w.Event("DOMContentLoaded"));
  P.load(lesson("RFRC 2.3"), { queue: [] });
  const mini = w.document.querySelector("[data-miniplayer]");
  assert.equal(mini.hidden, false);
  assert.ok(w.document.documentElement.hasAttribute("data-player-open"));
  assert.equal(w.document.querySelector("[data-player='collapse']").hidden, true);

  const play = w.document.getElementById("play");
  play.setAttribute("data-listen", JSON.stringify(lesson("RFRC 2.4")));
  play.click();
  assert.equal(w.localStorage.getItem("player:collapsed"), null, "starting a lesson opens the player");
});
