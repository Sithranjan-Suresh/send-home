"use strict";
/* Sendhome frontend: no framework, no build step. All state lives in one object and
   nothing is stored in the browser. Model text is only ever inserted with textContent. */

const SAMPLES = [
  { id: "pneumonia", label: "Pneumonia" },
  { id: "heart_failure", label: "Heart failure" },
  { id: "appendectomy", label: "Appendectomy" },
];
const QUESTION_CHIPS = ["When do I see my doctor?", "Can I take ibuprofen too?"];

let MSG = {
  refusal: "That isn't in your paperwork — ask your nurse.",
  dose_missing: "Dose not listed — confirm with your nurse.",
  quote_not_found: "Couldn't verify — confirm with your nurse.",
  number_mismatch: "Numbers here don't match the source — confirm with your nurse.",
  ambiguous_match: "This wording appears more than once — showing the first match.",
  max_chars: 8000,
};

const state = {
  text: "",
  analysis: null,
  grades: null,
  message: null,
  translation: null,
  language: "en",
  qa: [],
  highlights: [],
  loading: null, // "analyze" | "translate" | "ask" | null
  error: null,
};

/* ---------- tiny DOM helper (text only, never HTML) ---------- */
function h(tag, props, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "text") el.textContent = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
}
const $ = (id) => document.getElementById(id);

/* ---------- API ---------- */
async function api(path, body) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 90000);
  try {
    const r = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctl.signal,
    });
    let data = null;
    try { data = await r.json(); } catch (_) { /* non-JSON error page */ }
    if (!r.ok) throw new Error((data && data.message) || "Something went wrong. Please try again.");
    return data;
  } catch (e) {
    if (e.name === "AbortError") throw new Error("That took too long. Please try again.");
    if (e instanceof TypeError) throw new Error("Couldn't reach the server. Check your connection and try again.");
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

/* ---------- render ---------- */
function render() {
  renderInput();
  renderStatus();
  const has = !!(state.analysis && state.analysis.is_discharge_doc);
  $("results").hidden = !has;
  if (has) {
    renderResults();
    renderSource();
  }
}

function renderInput() {
  const pane = $("input-pane");
  const busy = state.loading === "analyze";
  const over = state.text.length > MSG.max_chars;
  // Keep the textarea element (and caret) alive across re-renders.
  let ta = $("sheet");
  if (!ta) {
    ta = h("textarea", {
      id: "sheet",
      "aria-label": "Discharge sheet text",
      placeholder: "Paste the text of a discharge sheet here, or pick a sample below.",
      oninput: (e) => {
        state.text = e.target.value;
        if (state.analysis || state.message) { resetResults(); state.message = null; render(); } else updateCount();
      },
    });
    pane.replaceChildren(
      h("div", { class: "card" },
        h("h2", { id: "in-h" }, "Your discharge sheet"),
        h("p", { class: "lead" }, "Pick a synthetic sample or paste text. We'll turn it into a plan and show where every line came from."),
        h("div", { class: "row", id: "sample-row" }),
        h("div", { style: "margin:12px 0" }, ta),
        h("div", { class: "row between" },
          h("span", { id: "count", class: "count" }),
          h("div", { class: "row" },
            h("button", { id: "go", class: "primary", onclick: onAnalyze }, "Make it clear"),
            h("button", { id: "reset", class: "link", onclick: onReset }, "Start over"),
          ))));
  }
  if (ta.value !== state.text) ta.value = state.text;
  const row = $("sample-row");
  if (!row.children.length) {
    row.append(h("span", { class: "small" }, "Use a sample:"));
    for (const s of SAMPLES) row.append(h("button", { onclick: () => loadSample(s.id) }, s.label));
  }
  for (const b of row.querySelectorAll("button")) b.disabled = busy;
  const go = $("go");
  go.disabled = busy || over;
  go.textContent = busy ? "Reading your paperwork…" : "Make it clear";
  updateCount();
}

function updateCount() {
  const c = $("count");
  if (!c) return;
  const n = state.text.length;
  const over = n > MSG.max_chars;
  c.textContent = over
    ? `${n.toLocaleString()} / ${MSG.max_chars.toLocaleString()} characters — too long. Please shorten it.`
    : `${n.toLocaleString()} / ${MSG.max_chars.toLocaleString()} characters`;
  c.className = "count" + (over ? " over" : "");
  const go = $("go");
  if (go) go.disabled = state.loading === "analyze" || over;
}

function renderStatus() {
  const box = $("status");
  box.replaceChildren();
  if (state.loading === "analyze") {
    box.append(h("div", { class: "msg info" }, h("span", { class: "spinner" }), "Reading your paperwork and checking every line against it… this can take up to 15 seconds."));
  } else if (state.error) {
    box.append(h("div", { class: "msg error", role: "alert" }, state.error));
  } else if (state.message) {
    box.append(h("div", { class: "msg info" }, state.message));
  }
}

function flagBadges(item, opts = {}) {
  const out = [];
  for (const f of item.flags || []) {
    if (f === "dose_missing" && opts.skipDose) continue;
    if (MSG[f]) out.push(h("span", { class: "badge" }, "⚠ " + MSG[f]));
  }
  return out.length ? h("div", { class: "flags" }, out) : null;
}

function sourceBtn(item) {
  if (!item.span) return null;
  return h("button", { class: "link", onclick: () => showSource([item.span]), "aria-label": "Show source sentence in your paperwork" }, "Show source");
}

function renderResults() {
  const a = state.analysis;
  const g = state.grades || {};
  const pane = $("result-pane");

  const grade = h("div", { class: "grade", title: "Approximate Flesch–Kincaid grade, computed locally" },
    "Reading level (approx.): ",
    g.original != null ? h("span", {}, "original grade ", h("b", {}, String(g.original))) : null,
    g.plain != null ? h("span", {}, " → plain grade ", h("b", {}, String(g.plain))) : null);

  const summary = h("section", { class: "card" }, h("h2", {}, "In plain words"),
    a.summary.map((s) => h("div", { class: "item" }, h("p", {}, s.text), flagBadges(s), sourceBtn(s))));

  const medsCard = h("section", { class: "card" }, h("h2", {}, "Your medicines"),
    a.medications.length ? medTable(a.medications) : h("p", { class: "lead" }, "No medicines were found in this sheet."));

  const call = a.red_flags.filter((r) => r.urgency !== "er");
  const er = a.red_flags.filter((r) => r.urgency === "er");
  const flagsCard = h("section", { class: "card" }, h("h2", {}, "When to get help"),
    redGroup("call", "☎ Call your care team if…", call),
    redGroup("er", "✚ Go to the ER or call 911 if…", er));

  const fuCard = h("section", { class: "card" }, h("h2", {}, "Follow-up visits"),
    a.follow_ups.length
      ? a.follow_ups.map((f) => h("div", { class: "item" },
          h("p", {}, h("b", {}, f.what), " — ",
            f.when ? f.when : h("span", { class: "missing" }, "Time not listed — confirm with your nurse.")),
          flagBadges(f), sourceBtn(f)))
      : h("p", { class: "lead" }, "No follow-up visits were found."));

  pane.replaceChildren(
    h("div", { class: "row between", style: "margin-top:16px" }, grade),
    summary, medsCard, flagsCard, fuCard, translateCard(), askCard());
}

function medCells(m) {
  const dose = m.dose ? m.dose : h("span", { class: "missing" }, MSG.dose_missing);
  const other = (v) => v || h("span", { class: "small" }, "Not listed");
  return { dose, schedule: other(m.schedule), purpose: other(m.purpose) };
}

function medTable(meds) {
  const table = h("table", { class: "meds-table" },
    h("thead", {}, h("tr", {}, ["Medicine", "Dose", "When", "Why", ""].map((t) => h("th", {}, t)))),
    h("tbody", {}, meds.map((m) => {
      const c = medCells(m);
      return h("tr", {},
        h("td", {}, h("b", {}, m.name), flagBadges(m, { skipDose: true })),
        h("td", {}, c.dose), h("td", {}, c.schedule), h("td", {}, c.purpose),
        h("td", {}, sourceBtn(m)));
    })));
  const cards = h("div", { class: "meds" }, meds.map((m) => {
    const c = medCells(m);
    return h("div", { class: "med" },
      h("div", { class: "name" }, m.name),
      h("dl", {}, h("dt", {}, "Dose"), h("dd", {}, c.dose), h("dt", {}, "When"), h("dd", {}, c.schedule),
        h("dt", {}, "Why"), h("dd", {}, c.purpose)),
      flagBadges(m, { skipDose: true }), sourceBtn(m));
  }));
  return h("div", {}, table, cards);
}

function redGroup(kind, title, items) {
  if (!items.length) return null;
  return h("div", { class: "group " + kind }, h("h3", {}, title),
    h("ul", {}, items.map((r) => h("li", {}, h("span", {}, r.text), flagBadges(r), sourceBtn(r)))));
}

/* ---------- source viewer + highlighting ---------- */
function renderSource() {
  const pane = $("source-pane");
  const text = state.text;
  const spans = state.highlights
    .filter((s) => s && s.start >= 0 && s.end <= text.length && s.start < s.end)
    .sort((a, b) => a.start - b.start);
  const body = h("div", { class: "src-text", id: "src-text", tabindex: "0" });
  let pos = 0;
  for (const s of spans) {
    if (s.start < pos) continue; // skip overlaps
    body.append(document.createTextNode(text.slice(pos, s.start)));
    body.append(h("mark", { class: "pulse" }, text.slice(s.start, s.end)));
    pos = s.end;
  }
  body.append(document.createTextNode(text.slice(pos)));
  pane.replaceChildren(h("div", { class: "card" },
    h("h2", { id: "src-h" }, "Your original paperwork"),
    h("p", { class: "small" }, "Click “Show source” on any line to see where it came from."),
    body));
}

function showSource(spans) {
  state.highlights = spans;
  renderSource();
  const mark = document.querySelector("#src-text mark");
  if (mark) mark.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
}

/* ---------- translate ---------- */
function translateCard() {
  const sel = h("select", { id: "lang", "aria-label": "Language", onchange: onLanguage },
    h("option", { value: "en" }, "English"), h("option", { value: "es" }, "Español (Spanish)"));
  sel.value = state.language;
  const card = h("section", { class: "card" }, h("h2", {}, "Another language"),
    h("div", { class: "row" }, h("label", { for: "lang" }, "Show this plan in: "), sel));
  if (state.loading === "translate") {
    card.append(h("div", { class: "msg info" }, h("span", { class: "spinner" }), "Translating, then translating back to English so you can check…"));
  } else if (state.language !== "en" && state.translation) {
    const t = state.translation;
    if (t.warnings.length) {
      card.append(h("div", { class: "msg error", role: "alert" },
        h("b", {}, "Check these before relying on the translation:"), h("ul", {}, t.warnings.map((w) => h("li", {}, w)))));
    }
    card.append(h("p", { class: "small" }, t.disclaimer),
      h("div", { class: "cols" },
        h("div", { class: "col", lang: state.language }, h("h3", {}, "Español"), renderTranslated(t.translated)),
        h("div", { class: "col" }, h("h3", {}, "Back to English (check)"), renderTranslated(t.back_translation))));
  }
  return card;
}

function renderTranslated(d) {
  const el = h("div", {});
  const list = (title, items) => items.length ? [h("b", {}, title), h("ul", {}, items.map((i) => h("li", {}, i)))] : [];
  el.append(...list("Summary", (d.summary || []).map(String)));
  el.append(...list("Medicines", (d.medications || []).map((m) =>
    [m.name, m.dose, m.schedule, m.purpose].filter(Boolean).join(" — "))));
  el.append(...list("Get help", (d.red_flags || []).map((r) => (r.urgency === "er" ? "✚ " : "☎ ") + r.text)));
  el.append(...list("Follow-ups", (d.follow_ups || []).map((f) => [f.what, f.when].filter(Boolean).join(" — "))));
  return el;
}

async function onLanguage(e) {
  state.language = e.target.value;
  state.error = null;
  if (state.language === "en") return render();
  if (state.translation && state.translation.language === state.language) return render();
  state.loading = "translate";
  render();
  try {
    const res = await api("/api/translate", { analysis: state.analysis, language: state.language });
    state.translation = { ...res, language: state.language };
  } catch (err) {
    state.error = err.message;
    state.language = "en";
  }
  state.loading = null;
  render();
}

/* ---------- ask ---------- */
function askCard() {
  const input = h("input", { type: "text", id: "q", maxlength: "300", "aria-label": "Your question", placeholder: "Ask about your paperwork…",
    onkeydown: (e) => { if (e.key === "Enter") onAsk(e.target.value); } });
  const busy = state.loading === "ask";
  const card = h("section", { class: "card" }, h("h2", {}, "Ask a question"),
    h("p", { class: "lead" }, "Answers come only from your paperwork. If it isn't there, we'll say so."),
    h("div", { class: "row" }, input,
      h("button", { class: "primary", disabled: busy, onclick: () => onAsk($("q").value) }, busy ? "Checking…" : "Ask")),
    h("div", { class: "chips" }, QUESTION_CHIPS.map((q) => h("button", { disabled: busy, onclick: () => onAsk(q) }, q))));
  const qa = h("div", { class: "qa", "aria-live": "polite" });
  for (const item of state.qa) {
    qa.append(h("div", { class: "q" }, "You: " + item.q),
      h("div", { class: "a" + (item.in_document ? "" : " refusal") },
        item.answer,
        item.spans.length ? h("div", {}, h("button", { class: "link", onclick: () => showSource(item.spans) }, "Show source")) : null));
  }
  card.append(qa);
  return card;
}

async function onAsk(question) {
  question = (question || "").trim();
  if (!question || state.loading) return;
  state.loading = "ask";
  state.error = null;
  render();
  try {
    const r = await api("/api/ask", { text: state.text, question });
    state.qa.push({ q: question, in_document: r.in_document, answer: r.answer || MSG.refusal, spans: r.spans || [] });
    if (r.in_document && r.spans.length) state.highlights = r.spans;
  } catch (err) {
    state.error = err.message;
  }
  state.loading = null;
  render();
  if (state.highlights.length && state.qa.length && state.qa[state.qa.length - 1].in_document) showSource(state.highlights);
}

/* ---------- actions ---------- */
async function loadSample(id) {
  try {
    const r = await fetch(`/samples/${id}.txt`);
    if (!r.ok) throw new Error();
    state.text = (await r.text()).replace(/\r\n/g, "\n");
    resetResults();
    state.error = null;
  } catch (_) {
    state.error = "Couldn't load that sample. Please try again.";
  }
  render();
}

function resetResults() {
  state.analysis = null; state.grades = null; state.message = null; state.translation = null;
  state.language = "en"; state.qa = []; state.highlights = [];
}

async function onAnalyze() {
  if (state.loading) return;
  const text = state.text;
  if (!text.trim()) {
    state.error = "Paste or pick a discharge sheet first.";
    return render();
  }
  if (text.length > MSG.max_chars) return render();
  resetResults();
  state.error = null;
  state.loading = "analyze";
  render();
  try {
    const r = await api("/api/analyze", { text });
    state.message = r.message || null;
    if (r.analysis && r.analysis.is_discharge_doc) {
      state.analysis = r.analysis;
      state.grades = r.grades;
    }
  } catch (err) {
    state.error = err.message;
  }
  state.loading = null;
  render();
  if (state.analysis) $("result-pane").scrollIntoView({ behavior: "smooth", block: "start" });
}

function onReset() {
  state.text = "";
  resetResults();
  state.error = null;
  state.loading = null;
  render();
  $("sheet").focus();
}

/* ---------- start ---------- */
(async function init() {
  try {
    const r = await fetch("/api/messages");
    if (r.ok) {
      const m = await r.json();
      MSG = { ...MSG, refusal: m.refusal, dose_missing: m.dose_missing, quote_not_found: m.quote_not_found,
              number_mismatch: m.number_mismatch, max_chars: m.max_chars };
    }
  } catch (_) { /* keep built-in defaults */ }
  render();
})();
