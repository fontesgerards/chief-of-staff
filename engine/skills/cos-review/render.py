"""Render collected decision cards into one self-contained dashboard-<date>.html.

Editorial review desk: a top tab bar (To review / Queued / Working / Done +
right-aligned Prompts & sources) with live counts, cards grouped under topic
headers, each card an eyebrow (SOURCE · DATE) + serif headline + context +
What happened + editable draft + Why this is in the sweep, and a persistent
bottom feedback bar ("Talking to: <scope>", Broader/Narrower, input, Send).

Zero external/network dependencies — CSS + JS inlined, card data embedded as a
JSON island painted by client JS (all escaping via textContent/value). Decisions
and notes accumulate in page; Export downloads decisions-<date>.jsonl; a live
write-back server (if present) also receives each one. The dashboard NEVER sends:
a send/approve is just a row in the JSONL the ingest phase reads.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_lib import collect_cards  # noqa: E402


_CSS = """
:root {
  color-scheme: light dark;
  --paper:#f4f2ed; --surface:#fffdf9; --ink:#1d1b16; --muted:#6f6a60;
  --faint:#8a857a; --line:#e7e3d9; --line-strong:#d8d3c6;
  --accent:#4b51c4; --accent-soft:#e7e7fb;
  --focus:#9a6b2f; --focus-bg:#f3e6cf; --danger:#b23b30; --ok:#3f7d4e;
  /* scope hues: narrow -> wide */
  --scope-card:#4b51c4; --scope-topic:#0e8c86; --scope-all:#b0772b;
  --scope:var(--accent);
  --serif: "Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
  --sans: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,sans-serif;
  --mono: ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark) {
  :root { --paper:#17160f; --surface:#201e17; --ink:#ece8df; --muted:#9b958a;
    --faint:#7c766b; --line:#322f27; --line-strong:#403c32;
    --accent:#9aa0ff; --accent-soft:#23233a; --focus:#d9b27a; --focus-bg:#2c2417;
    --scope-card:#9aa0ff; --scope-topic:#4fd1c5; --scope-all:#e0a558; }
}
body.scope-card  { --scope:var(--scope-card); }
body.scope-topic { --scope:var(--scope-topic); }
body.scope-all   { --scope:var(--scope-all); }
* { box-sizing:border-box; }
html,body { margin:0; }
body { background:var(--paper); color:var(--ink); font-family:var(--sans);
  font-size:15px; line-height:1.6; -webkit-font-smoothing:antialiased;
  padding-bottom:128px; }
.eyebrow { font-size:11px; letter-spacing:.11em; text-transform:uppercase;
  color:var(--faint); font-weight:600; }

/* Tabs */
header { position:sticky; top:0; z-index:20; background:color-mix(in srgb,var(--paper) 88%,transparent);
  backdrop-filter:saturate(1.2) blur(8px); border-bottom:1px solid var(--line); }
nav { max-width:880px; margin:0 auto; padding:0 28px; display:flex; align-items:stretch; gap:26px; }
.tab { appearance:none; border:0; background:none; font:inherit; cursor:pointer;
  padding:18px 2px 15px; color:var(--muted); border-bottom:2px solid transparent;
  display:flex; align-items:center; gap:8px; margin-bottom:-1px; transition:color .15s; }
.tab:hover { color:var(--ink); }
.tab[aria-selected="true"] { color:var(--ink); border-bottom-color:var(--ink); }
.tab .count { font-size:12px; color:var(--faint); font-variant-numeric:tabular-nums; }
.tab.right { margin-left:auto; color:var(--faint); }
.tab:focus-visible { outline:2px solid var(--accent); outline-offset:3px; border-radius:4px; }

main { max-width:880px; margin:0 auto; padding:28px; }
.topic { margin:34px 0 14px; display:flex; align-items:baseline; gap:12px; }
.topic:first-child { margin-top:8px; }
.topic h2 { font:inherit; font-size:12px; letter-spacing:.13em; text-transform:uppercase;
  color:var(--muted); font-weight:700; margin:0; }
.topic .rule { flex:1; height:1px; background:var(--line); }

/* Card */
.card { position:relative; background:var(--surface); border:1px solid var(--line);
  border-left:3px solid var(--line-strong); border-radius:12px;
  padding:24px 30px 22px; margin:0 0 16px; cursor:default;
  box-shadow:0 1px 2px rgba(20,18,12,.03); transition:border-color .15s, transform .15s, opacity .25s;
  opacity:0; transform:translateY(6px); }
.card.in { opacity:1; transform:none; }
.card.scoped { border-left-color:var(--scope);
  background:color-mix(in srgb, var(--scope) 5%, var(--surface)); }
.card.talking { border-left-color:var(--scope); border-left-width:4px;
  background:color-mix(in srgb, var(--scope) 9%, var(--surface)); }
.card.decided { opacity:.5; }
.card h3 { font-family:var(--serif); font-weight:600; font-size:25px; line-height:1.2;
  letter-spacing:-.01em; margin:7px 0 10px; }
.card .lede { font-size:16px; color:var(--ink); margin:0 0 18px; }
.label { margin:18px 0 7px; }
.block { color:var(--ink); margin:0; }
.muted { color:var(--muted); }
details.full { margin:14px 0 0; }
details.full summary { cursor:pointer; font-size:13px; color:var(--muted); list-style:none; }
details.full summary::-webkit-details-marker { display:none; }
details.full summary::before { content:"›"; display:inline-block; margin-right:7px;
  transition:transform .15s; }
details.full[open] summary::before { transform:rotate(90deg); }
details.full pre { margin-top:10px; }
textarea { width:100%; font-family:var(--mono); font-size:13.5px; line-height:1.6;
  background:var(--paper); border:1px solid var(--line-strong); border-radius:9px;
  padding:13px 14px; color:var(--ink); resize:vertical; min-height:96px; }
textarea:focus { outline:2px solid var(--accent); outline-offset:1px; border-color:transparent; }
pre.diff { font-family:var(--mono); font-size:13px; line-height:1.55; white-space:pre-wrap;
  word-break:break-word; background:var(--paper); border:1px solid var(--line);
  border-radius:9px; padding:13px 14px; margin:0; }
ul.why { margin:4px 0 0; padding-left:18px; }
ul.why li { margin:4px 0; }
.feedback-label { color:var(--focus); }
.notes { margin-top:6px; border-left:2px solid var(--focus); padding-left:13px; }
.note { display:flex; gap:8px; margin:6px 0; }
.note-mark { color:var(--focus); font-weight:700; }
.note-text { white-space:pre-wrap; word-break:break-word; }
.awaiting { margin-top:9px; font-size:12.5px; color:var(--focus); font-style:italic; }
.actions { display:flex; gap:9px; margin-top:18px; align-items:center; flex-wrap:wrap; }
button.act { font:inherit; font-size:14px; padding:7px 15px; border-radius:8px;
  border:1px solid var(--line-strong); background:var(--surface); color:var(--ink); cursor:pointer;
  transition:background .12s, border-color .12s; }
button.act:hover { border-color:var(--ink); }
button.act.primary { background:var(--accent); border-color:var(--accent); color:#fff; }
button.act.primary:hover { filter:brightness(1.06); }
button.act.danger { color:var(--danger); border-color:transparent; }
button.act.danger:hover { border-color:var(--danger); }
.decided-tag { font-size:13px; color:var(--ok); margin-left:auto; }
.badge { font-size:11px; letter-spacing:.04em; padding:2px 8px; border-radius:6px;
  background:var(--line); color:var(--muted); }
.badge.irreversible { background:var(--danger); color:#fff; }
.empty { text-align:center; color:var(--muted); padding:80px 0; font-size:16px; }
.empty .big { font-family:var(--serif); font-size:24px; color:var(--ink); display:block; margin-bottom:6px; }
.sources p { max-width:60ch; color:var(--muted); }
.sources code { font-family:var(--mono); font-size:13px; background:var(--paper);
  border:1px solid var(--line); border-radius:5px; padding:1px 6px; }

/* Feedback bar */
.bar { position:fixed; left:0; right:0; bottom:0; z-index:30;
  background:color-mix(in srgb,var(--surface) 94%,transparent);
  backdrop-filter:blur(10px) saturate(1.2); border-top:1px solid var(--line-strong); }
.bar .inner { max-width:880px; margin:0 auto; padding:11px 28px 12px; }
.bar .row1 { display:flex; align-items:center; gap:12px; font-size:12.5px; color:var(--muted);
  margin-bottom:9px; }
.bar .talking { color:var(--muted); }
.bar .scopepill { font-weight:600; color:var(--scope);
  background:color-mix(in srgb, var(--scope) 15%, transparent);
  padding:2px 10px; border-radius:999px; max-width:54ch; overflow:hidden; text-overflow:ellipsis;
  white-space:nowrap; transition:color .15s, background .15s; }
.bar .scopectl .lbl { color:var(--scope); }
.bar .scopectl { margin-left:auto; display:flex; align-items:center; gap:6px; }
.bar .scopectl .lbl { letter-spacing:.1em; text-transform:uppercase; font-size:11px; }
.bar .sbtn { font:inherit; font-size:12px; border:1px solid var(--line-strong); background:none;
  color:var(--muted); border-radius:7px; padding:3px 9px; cursor:pointer; }
.bar .sbtn:hover { color:var(--ink); border-color:var(--ink); }
.bar .sbtn:disabled { opacity:.32; cursor:default; }
.bar .sbtn:disabled:hover { color:var(--muted); border-color:var(--line-strong); }
.bar .row2 { display:flex; gap:10px; align-items:flex-end; }
.bar input { flex:1; font:inherit; font-size:15px; background:var(--paper);
  border:1px solid var(--line-strong); border-radius:10px; padding:11px 14px; color:var(--ink);
  box-shadow:inset 3px 0 0 var(--scope); transition:box-shadow .15s; }
.bar input:focus { outline:2px solid var(--scope); outline-offset:1px; border-color:transparent; }
.bar .send { font:inherit; font-weight:600; background:var(--ink); color:var(--paper);
  border:0; border-radius:10px; padding:11px 20px; cursor:pointer; }
.bar .send:hover { filter:brightness(1.15); }
.bar .hint { margin-top:7px; font-size:11.5px; color:var(--faint); }
.bar kbd { font-family:var(--mono); font-size:11px; background:var(--paper);
  border:1px solid var(--line); border-radius:4px; padding:0 4px; }
.export { position:fixed; top:13px; right:24px; z-index:25; }
.export button { font:inherit; font-size:13px; background:var(--surface); color:var(--ink);
  border:1px solid var(--line-strong); border-radius:8px; padding:6px 13px; cursor:pointer; }
.banner { font-size:11px; padding:2px 9px; border-radius:999px; }
.banner.live { background:var(--ok); color:#fff; }
"""

_JS = r"""
const CARDS = window.__CARDS__ || [];
const DATE = window.__DATE__;
const TABS = [["review","To review"],["feedback","Feedback"],["queued","Queued"],
  ["working","Working"],["done","Done"]];
const decisions = {};
const sessionNotes = {};          // card_id -> [note text] added this session
function effectiveTab(card) { return sessionNotes[card.card_id] ? "feedback" : card.tab; }
let activeTab = (TABS.find(([k]) => CARDS.some(c => c.tab === k)) || TABS[0])[0];
let talkingId = null;          // focused card id, or null
let scope = "card";            // card | topic | all
const SCOPES = ["card","topic","all"];

function el(t, cls, txt) { const e = document.createElement(t); if (cls) e.className = cls;
  if (txt != null) e.textContent = txt; return e; }
function cardsIn(tab) { return CARDS.filter(c => effectiveTab(c) === tab); }
function byId(id) { return CARDS.find(c => c.card_id === id); }

function record(target, decision, opts) {
  const d = Object.assign({ card_id: target, decision, ts: new Date().toISOString() }, opts || {});
  decisions[target + ":" + decision + ":" + (d.ts)] = d;   // notes are additive; actions overwrite below
  if (decision !== "note") { // one action per card — keep the latest
    Object.keys(decisions).forEach(k => { if (decisions[k].card_id === target
      && decisions[k].decision !== "note" && decisions[k] !== d) delete decisions[k]; });
  }
  if (window.__REVIEW_POST__) fetch(window.__REVIEW_POST__, { method:"POST",
    headers:{"Content-Type":"application/json"}, body: JSON.stringify(d) }).catch(()=>{});
  return d;
}

/* --- card rendering --- */
function renderCard(card) {
  const wrap = el("article", "card"); wrap.dataset.id = card.card_id;
  wrap.onclick = (e) => { if (e.target.closest("button,textarea,a,summary")) return;
    setTalking(card.card_id); };

  const eye = el("div", "eyebrow");
  eye.append(document.createTextNode(card.source_label + (card.date ? "  ·  " + card.date : "")));
  wrap.append(eye);
  wrap.append(el("h3", null, card.title));

  const f = card.fields || {};
  if (f.context) wrap.append(el("p", "lede", f.context));

  if (f.what_happened) {
    wrap.append(el("div", "eyebrow label", "What happened"));
    wrap.append(el("p", "block", f.what_happened));
  }
  if (f.full_source) {
    const det = el("details", "full");
    det.append(el("summary", null, "Read full source"));
    det.append(el("pre", "diff", f.full_source));
    wrap.append(det);
  }

  let editable = null;
  if (card.kind === "memory") {
    wrap.append(el("div", "eyebrow label", "Proposed memory change"));
    wrap.append(el("pre", "diff", f.diff || ""));     // RAW diff, never summarized
  } else if (card.kind === "outbound") {
    wrap.append(el("div", "eyebrow label", "Draft"));
    editable = el("textarea"); editable.value = f.draft || ""; wrap.append(editable);
  } else if (card.kind === "question" && card.decisions.includes("answer")) {
    wrap.append(el("div", "eyebrow label", "Your answer"));
    editable = el("textarea"); editable.placeholder = "type your answer…"; wrap.append(editable);
  }

  if (Array.isArray(f.why) && f.why.length) {
    wrap.append(el("div", "eyebrow label", "Why this is in the sweep"));
    const ul = el("ul", "why"); f.why.forEach(w => ul.append(el("li", null, w))); wrap.append(ul);
  }

  // feedback the principal has left — durable (from the proposal) + this session
  const notes = (f.notes || []).concat(sessionNotes[card.card_id] || []);
  if (notes.length) {
    wrap.append(el("div", "eyebrow label feedback-label", "Your feedback"));
    const box = el("div", "notes");
    notes.forEach(n => { const row = el("div", "note"); row.append(el("span", "note-mark", "›"));
      row.append(el("span", "note-text", n)); box.append(row); });
    if (effectiveTab(card) === "feedback")
      box.append(el("div", "awaiting", "Awaiting the agent's revision on the next sweep."));
    wrap.append(box);
  }

  if (card.decisions.length && effectiveTab(card) !== "feedback") {  // feedback cards await the agent
    const actions = el("div", "actions");
    if (f.reversibility) actions.append(el("span",
      "badge" + (f.reversibility === "irreversible" ? " irreversible" : ""), f.reversibility));
    const tag = el("span", "decided-tag");
    const VERB = { send:["Send","primary",1], edit:["Save edit","",1], reject:["Reject","danger",0],
      approve:["Approve","primary",0], answer:["Answer","primary",1], dismiss:["Dismiss","danger",0] };
    function decide(v, withText) {
      record(card.card_id, v, withText && editable ? { text: editable.value } : null);
      wrap.classList.add("decided"); tag.textContent = "✓ " + v;
    }
    card.decisions.forEach(v => { const [label, cls, wt] = VERB[v] || [v,"",0];
      const b = el("button", "act " + cls, label); b.onclick = () => decide(v, wt); actions.append(b); });
    actions.append(tag);
    wrap.append(actions);
  }
  return wrap;
}

function renderSources() {
  const box = el("div", "sources");
  box.append(el("h3", null, "Prompts & sources"));
  const p = el("p", null);
  p.append(document.createTextNode("This board is rendered from your queue — pending outbound "
    + "proposals, open questions, and staged Tier-2 memory diffs. Triage here; the outbound gate "
    + "and your autonomy dial still govern any actual send. Operating rules live in "));
  p.append(el("code", null, "instance/config.md")); p.append(document.createTextNode(" and "));
  p.append(el("code", null, "instance/memory/procedural/")); p.append(document.createTextNode("."));
  box.append(p);
  return box;
}

/* --- board + tabs --- */
function renderBoard() {
  const main = document.getElementById("main"); main.replaceChildren();
  if (activeTab === "sources") { main.append(renderSources()); return; }
  const cards = cardsIn(activeTab);
  if (!cards.length) {
    const e = el("div", "empty");
    e.append(el("span", "big", activeTab === "review" ? "Nothing to review." : "Nothing here."));
    e.append(document.createTextNode(activeTab === "review" ? "Inbox zero — you're clear."
      : "Cards land here as they move through the board."));
    main.append(e);
    talkingId = null; scope = "all"; syncTalking(); return;
  }
  let lastTopic = null;
  cards.forEach((card, i) => {
    if (card.topic !== lastTopic) {
      lastTopic = card.topic;
      const t = el("div", "topic"); t.append(el("h2", null, card.topic)); t.append(el("div","rule"));
      main.append(t);
    }
    const node = renderCard(card); main.append(node);
    requestAnimationFrame(() => setTimeout(() => node.classList.add("in"), 20 + i * 35));
  });
  if (!talkingId && cards.length) setTalking(cards[0].card_id, true);
  else syncTalking();
}

function renderTabs() {
  const nav = document.getElementById("nav"); nav.replaceChildren();
  TABS.forEach(([key, label]) => {
    const b = el("button", "tab"); b.setAttribute("role","tab");
    b.setAttribute("aria-selected", String(key === activeTab));
    b.append(el("span", null, label));
    b.append(el("span", "count", String(cardsIn(key).length)));
    b.onclick = () => { activeTab = key; talkingId = null; renderTabs(); renderBoard(); };
    nav.append(b);
  });
  const s = el("button", "tab right"); s.setAttribute("role","tab");
  s.setAttribute("aria-selected", String(activeTab === "sources"));
  s.append(el("span", null, "Prompts & sources"));
  s.onclick = () => { activeTab = "sources"; renderTabs(); renderBoard(); };
  nav.append(s);
}

/* --- feedback bar: talking-to + scope --- */
function setTalking(id, silent) {
  talkingId = id; scope = "card";
  document.querySelectorAll(".card").forEach(c =>
    c.classList.toggle("talking", c.dataset.id === id));
  syncTalking();
  if (!silent) { const node = document.querySelector('.card[data-id="'+id+'"]');
    if (node) node.scrollIntoView({ block:"nearest", behavior:"smooth" }); }
}
function syncTalking() {
  const pill = document.getElementById("scopepill");
  const card = byId(talkingId);
  const tabLabel = (TABS.find(([k]) => k === activeTab) || [,activeTab])[1];
  if (!card || scope === "all") pill.textContent = "Everything in " + tabLabel;
  else if (scope === "topic") pill.textContent = card.topic + " — " + cardsIn(activeTab)
    .filter(c => c.topic === card.topic).length + " items";
  else pill.textContent = card.title;
  applyScopeHighlight(card);
  updateScopeButtons();
}
function inScopeIds(card) {
  const cards = cardsIn(activeTab);
  if (!card || scope === "all") return new Set(cards.map(c => c.card_id));
  if (scope === "topic") return new Set(cards.filter(c => c.topic === card.topic).map(c => c.card_id));
  return new Set([card.card_id]);
}
function applyScopeHighlight(card) {
  document.body.classList.remove("scope-card", "scope-topic", "scope-all");
  document.body.classList.add("scope-" + scope);
  const ids = inScopeIds(card);
  document.querySelectorAll(".card").forEach(el => {
    el.classList.toggle("scoped", ids.has(el.dataset.id));
    el.classList.toggle("talking", el.dataset.id === talkingId);   // the focused item
  });
}
function updateScopeButtons() {
  const hasCard = !!byId(talkingId);
  const i = SCOPES.indexOf(scope);
  document.getElementById("broader").disabled = i >= SCOPES.length - 1;   // already widest
  document.getElementById("narrower").disabled = i <= 0 || !hasCard;      // already narrowest / nothing to narrow to
}
function moveScope(dir) { // dir +1 broader, -1 narrower
  const i = SCOPES.indexOf(scope);
  scope = SCOPES[Math.max(0, Math.min(SCOPES.length - 1, i + dir))]; syncTalking();
}
function moveItem(dir) {
  const cards = cardsIn(activeTab); if (!cards.length) return;
  let i = cards.findIndex(c => c.card_id === talkingId);
  i = Math.max(0, Math.min(cards.length - 1, (i < 0 ? 0 : i) + dir));
  setTalking(cards[i].card_id);
}
function sendNote() {
  const input = document.getElementById("note"); const text = input.value.trim();
  if (!text) return;
  const card = byId(talkingId);
  let target = "all:" + activeTab;
  if (card && scope === "card") target = card.card_id;
  else if (card && scope === "topic") target = "topic:" + card.topic;
  record(target, "note", { text, scope, tab: activeTab });
  // attach to every in-scope card so the feedback shows on it and it moves to Feedback
  const ids = card ? inScopeIds(card) : new Set();
  ids.forEach(id => { (sessionNotes[id] = sessionNotes[id] || []).push(text); });
  input.value = "";
  if (ids.size) { renderTabs(); renderBoard(); }
  flash(input, "feedback added ✓");
}
function flash(input, msg) { const ph = input.placeholder; input.placeholder = msg;
  setTimeout(() => input.placeholder = ph, 1100); }

function exportDecisions() {
  const lines = Object.values(decisions).map(d => JSON.stringify(d)).join("\n");
  const blob = new Blob([lines + "\n"], { type:"application/x-ndjson" });
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
  a.download = "decisions-" + DATE + ".jsonl"; a.click();
}

window.addEventListener("DOMContentLoaded", () => {
  renderTabs(); renderBoard();
  document.getElementById("export").onclick = exportDecisions;
  document.getElementById("broader").onclick = () => moveScope(1);
  document.getElementById("narrower").onclick = () => moveScope(-1);
  document.getElementById("send").onclick = sendNote;
  const done = document.getElementById("done");
  if (done) done.onclick = () => fetch(window.__REVIEW_POST_DONE__, {method:"POST"}).catch(()=>{});
  const input = document.getElementById("note");
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); sendNote(); return; }
    const empty = input.value.length === 0;
    if (empty && (e.key === "ArrowUp" || e.key === "ArrowDown")) {
      e.preventDefault();
      if (e.metaKey || e.ctrlKey) moveScope(e.key === "ArrowUp" ? 1 : -1);
      else moveItem(e.key === "ArrowDown" ? 1 : -1);
    }
  });
  input.focus();
});
"""


def render(instance_dir, date, *, server_post=None, server_done=None):
    cards = [c.to_dict() for c in collect_cards(instance_dir)]
    island = json.dumps(cards, ensure_ascii=False).replace("</", "<\\/")
    live = server_post is not None
    banner = '<span class="banner live">live — clicks saved</span>' if live else ""
    post_js = (f'window.__REVIEW_POST__ = {json.dumps(server_post)};\n'
               f'window.__REVIEW_POST_DONE__ = {json.dumps(server_done)};\n') if live else ""
    done_btn = '<button id="done" class="act">Done</button>' if live else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Decision dashboard — {date}</title>
<style>{_CSS}</style></head>
<body>
<div class="export"><button id="export">Export decisions</button>{done_btn}{banner}</div>
<header><nav id="nav" role="tablist"></nav></header>
<main id="main"></main>
<div class="bar">
  <div class="inner">
    <div class="row1">
      <span class="talking">Talking to</span>
      <span class="scopepill" id="scopepill">—</span>
      <span class="scopectl">
        <span class="lbl">Scope</span>
        <button class="sbtn" id="broader">↑ Broader</button>
        <button class="sbtn" id="narrower">↓ Narrower</button>
      </span>
    </div>
    <div class="row2">
      <input id="note" type="text" placeholder="Tell the agent what to notice, change, or do…"
             autocomplete="off">
      <button class="send" id="send">Send</button>
    </div>
    <div class="hint"><kbd>↑</kbd><kbd>↓</kbd> move between items when empty ·
      <kbd>⌘↑</kbd><kbd>⌘↓</kbd> change scope · <kbd>Enter</kbd> send ·
      click a card to talk to it</div>
  </div>
</div>
<script>
window.__DATE__ = {json.dumps(date)};
window.__CARDS__ = {island};
{post_js}{_JS}
</script>
</body></html>
"""


def write(instance_dir, date, *, server_post=None, server_done=None):
    html = render(instance_dir, date, server_post=server_post, server_done=server_done)
    out_dir = Path(instance_dir) / "queue" / "review"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"dashboard-{date}.html"
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="render the decision dashboard")
    ap.add_argument("instance_dir")
    ap.add_argument("date")
    args = ap.parse_args()
    print(write(args.instance_dir, args.date))
