"use strict";
/* Extra pages: Medicine schedule, Warning signs, Questions for your nurse, Report card.
   They are separate addresses (#/schedule ...) but share the one in-memory analysis from
   app.js, so nothing is stored. Everything shown is derived from the analysis (or, for the
   Report card, from the evaluation files committed in the repo). Model text goes in via
   textContent only. */

const ROUTES = [
  { id: "plan", hash: "#/", label: "Plan" },
  { id: "schedule", hash: "#/schedule", label: "Medicine schedule" },
  { id: "warnings", hash: "#/warnings", label: "Warning signs" },
  { id: "nurse", hash: "#/nurse", label: "Questions for your nurse" },
  { id: "report", hash: "#/report", label: "Report card" },
];

function currentRoute() {
  const hash = location.hash || "#/";
  const found = ROUTES.find((r) => r.hash === hash);
  return found ? found.id : "plan";
}

function renderNav(route) {
  const nav = $("nav");
  nav.replaceChildren(h("div", { class: "nav-pill" },
    h("a", { class: "brand", href: "#/", "aria-label": "Sendhome home" }, h("span", { class: "brand-mark", "aria-hidden": "true" }), h("span", {}, "Sendhome")),
    h("div", { class: "nav-links" },
      ROUTES.map((r) => h("a", { href: r.hash, "aria-current": r.id === route ? "page" : null, class: r.id === route ? "active" : "" }, r.label)))));
}

function hasPlan() {
  return !!(state.analysis && state.analysis.is_discharge_doc);
}

function needPlanCard() {
  return h("div", { class: "card" },
    h("h2", {}, "Analyze a sheet first"),
    h("p", { class: "lead" }, "This page is built from your plan. Pick a sample or paste a discharge sheet on the Plan page, press “Make it clear”, then come back here."),
    h("a", { class: "btnlink", href: "#/" }, "Go to the Plan page"));
}

function renderPage(route) {
  const page = $("page");
  if (route === "report") return renderReportPage(page);
  if (!hasPlan()) return page.replaceChildren(h("h2", { class: "page-title" }, routeLabel(route)), needPlanCard());
  if (route === "schedule") return page.replaceChildren(schedulePage(state.analysis));
  if (route === "warnings") return page.replaceChildren(warningsPage(state.analysis));
  if (route === "nurse") return page.replaceChildren(nursePage(state.analysis));
}

function routeLabel(id) {
  return ROUTES.find((r) => r.id === id).label;
}

function printBtn() {
  return h("button", { class: "noprint", onclick: () => window.print() }, "Print this page");
}

/* ======================= Medicine schedule ======================= */

const SLOTS = [
  { id: "morning", label: "Morning" },
  { id: "midday", label: "Midday" },
  { id: "evening", label: "Evening" },
  { id: "bedtime", label: "Bedtime" },
];

/* Read the schedule wording only; never invent a time the sheet doesn't support. */
function classifySchedule(sched) {
  const s = (sched || "").toLowerCase();
  if (!s.trim()) return { kind: "unclear" };
  if (/as needed|\bprn\b|when needed|if needed|only if|only when/.test(s)) return { kind: "asneeded" };
  const slots = new Set();
  const explicit = new Set();
  if (/morning|breakfast/.test(s)) explicit.add("morning");
  if (/noon|lunch|midday|afternoon/.test(s)) explicit.add("midday");
  if (/evening|dinner|supper/.test(s)) explicit.add("evening");
  if (/bedtime|at night|nightly|before bed/.test(s)) explicit.add("bedtime");
  let guessed = false;
  if (/(four|4) times|every 6 hours|\bqid\b/.test(s)) { ["morning", "midday", "evening", "bedtime"].forEach((x) => slots.add(x)); guessed = true; }
  else if (/(three|3) times|every 8 hours|\btid\b/.test(s)) { ["morning", "midday", "evening"].forEach((x) => slots.add(x)); guessed = true; }
  else if (/twice|two times|2 times|every 12 hours|\bbid\b/.test(s)) { ["morning", "evening"].forEach((x) => slots.add(x)); guessed = true; }
  if (explicit.size && !guessed) explicit.forEach((x) => slots.add(x));
  if (slots.size) return { kind: "slots", slots: [...slots], guessed };
  if (/once|daily|every day|a day|each day/.test(s)) return { kind: "once" };
  return { kind: "unclear" };
}

function schedMed(m) {
  const dose = m.dose ? m.dose : h("span", { class: "missing" }, MSG.dose_missing);
  return h("div", { class: "slot-item" },
    h("b", {}, m.name), h("div", {}, dose),
    m.schedule ? h("div", { class: "small" }, "Sheet says: “" + m.schedule + "”") : null,
    flagBadges(m, { skipDose: true }), sourceBtn(m));
}

function schedulePage(a) {
  const cols = Object.fromEntries(SLOTS.map((s) => [s.id, []]));
  const once = [], asneeded = [], unclear = [];
  let anyGuess = false;
  for (const m of a.medications) {
    const c = classifySchedule(m.schedule);
    if (c.kind === "slots") { c.slots.forEach((id) => cols[id].push(m)); anyGuess = anyGuess || c.guessed; }
    else if (c.kind === "once") once.push(m);
    else if (c.kind === "asneeded") asneeded.push(m);
    else unclear.push(m);
  }
  const box = (title, meds, note, cls) => h("section", { class: "card slot " + (cls || "") },
    h("h3", {}, title), note ? h("p", { class: "small" }, note) : null,
    meds.length ? meds.map(schedMed) : h("p", { class: "small" }, "Nothing here"));

  return h("div", {},
    h("div", { class: "row between" }, h("h2", { class: "page-title" }, "Medicine schedule"), printBtn()),
    h("p", { class: "lead" }, "Your medicines laid out across the day. Times are only suggestions based on the wording of your sheet"
      + (anyGuess ? " (for example “twice daily” is shown as morning and evening)" : "")
      + ". Confirm the exact times with your nurse."),
    h("div", { class: "slots" }, SLOTS.map((s) => box(s.label, cols[s.id]))),
    box("Once a day — your sheet gives no time", once, "Pick one time and take it at the same time each day.", "wide"),
    box("Only when needed", asneeded, "Take these only for the reason the sheet gives. Check the sheet for the daily limit.", "wide"),
    unclear.length ? box("Schedule unclear — ask your nurse", unclear, "We couldn't place these without guessing.", "wide warn") : null);
}

/* ======================= Warning signs card ======================= */

function warningsPage(a) {
  const call = a.red_flags.filter((r) => r.urgency !== "er");
  const er = a.red_flags.filter((r) => r.urgency === "er");
  const list = (items) => h("ul", { class: "big-list" }, items.map((r) => h("li", {}, h("span", {}, r.text), flagBadges(r), sourceBtn(r))));
  return h("div", {},
    h("div", { class: "row between" }, h("h2", { class: "page-title" }, "Warning signs"), printBtn()),
    h("p", { class: "lead" }, "Keep this where you can find it quickly. It only repeats what your own paperwork says."),
    er.length ? h("section", { class: "alert er" }, h("h3", {}, "✚ Go to the ER or call 911 if…"), list(er)) : null,
    call.length ? h("section", { class: "alert call" }, h("h3", {}, "☎ Call your care team if…"), list(call)) : null,
    !er.length && !call.length ? h("div", { class: "card" }, h("p", {}, "No warning signs were found in this sheet. If you are worried about how you feel, ask your nurse or call your care team.")) : null,
    h("p", { class: "small" }, "If you are ever unsure whether something is an emergency, treat it as one and call 911."));
}

/* ======================= Questions for your nurse ======================= */

function nurseItems(a) {
  const items = [];
  for (const m of a.medications) {
    const flags = m.flags || [];
    if (!m.dose || flags.includes("dose_missing")) items.push({ q: `What is the dose of ${m.name}?`, why: "Your sheet doesn't list a dose.", span: m.span });
    if (!m.schedule) items.push({ q: `When and how often should I take ${m.name}?`, why: "Your sheet doesn't say.", span: m.span });
    if (flags.includes("number_mismatch")) items.push({ q: `Can you confirm the dose and schedule for ${m.name}?`, why: "The numbers didn't match the source sentence.", span: m.span });
  }
  const groups = [["summary", "text"], ["medications", "name"], ["red_flags", "text"], ["follow_ups", "what"]];
  for (const [key, field] of groups) {
    for (const it of a[key]) {
      if ((it.flags || []).includes("quote_not_found")) items.push({ q: `Can you confirm: “${it[field]}”?`, why: "We couldn't find this in your paperwork.", span: null });
    }
  }
  for (const f of a.follow_ups) {
    if (!f.when) items.push({ q: `When is my appointment for: ${f.what}? Who schedules it?`, why: "Your sheet doesn't give a time.", span: f.span });
  }
  for (const qa of state.qa) {
    if (!qa.in_document) items.push({ q: qa.q, why: "You asked this and it isn't in your paperwork.", span: null });
  }
  return items;
}

function nursePage(a) {
  const items = nurseItems(a);
  const text = items.map((i, n) => `${n + 1}. ${i.q}`).join("\n");
  const copied = h("span", { class: "small", role: "status" });
  const copyBtn = h("button", { class: "noprint", onclick: async () => {
    try { await navigator.clipboard.writeText(text); copied.textContent = " Copied."; }
    catch (_) { copied.textContent = " Couldn't copy — select the text instead."; }
  } }, "Copy list");

  return h("div", {},
    h("div", { class: "row between" }, h("h2", { class: "page-title" }, "Questions for your nurse"), h("div", { class: "row" }, copyBtn, printBtn(), copied)),
    h("p", { class: "lead" }, "Everything Sendhome couldn't confirm, plus any question you asked that your paperwork doesn't answer, in one list to bring to your nurse or doctor."),
    items.length
      ? h("ol", { class: "nurse-list" }, items.map((i, n) => h("li", {},
          h("label", {}, h("input", { type: "checkbox", "aria-label": "Asked: " + i.q }), h("span", {}, h("b", {}, i.q), h("span", { class: "small block" }, i.why))),
          i.span ? h("button", { class: "link noprint", onclick: () => showSource([i.span]) }, "Show source") : null)))
      : h("div", { class: "card" }, h("p", {}, "Nothing was flagged in this sheet. You can always ask your nurse anything that worries you.")),
    h("p", { class: "small" }, "Checkmarks aren't saved. Print or copy the list if you need to keep it."));
}

/* ======================= Report card ======================= */

let reportCache = null;

async function renderReportPage(page) {
  page.replaceChildren(h("h2", { class: "page-title" }, "Report card"), h("div", { class: "msg info" }, h("span", { class: "spinner" }), "Loading…"));
  try {
    if (!reportCache) {
      const r = await fetch("/api/report");
      if (!r.ok) throw new Error();
      reportCache = await r.json();
    }
  } catch (_) {
    return page.replaceChildren(h("h2", { class: "page-title" }, "Report card"), h("div", { class: "msg error" }, "Couldn't load the report. Please try again."));
  }
  if (currentRoute() !== "report") return;
  page.replaceChildren(reportPage(reportCache));
}

function gradeBars(rows) {
  const max = 14;
  return h("div", { class: "bars", role: "img", "aria-label": "Reading grade before and after, per sheet" },
    rows.filter((r) => r.grade_original != null).map((r) => h("div", { class: "bar-row" },
      h("span", { class: "bar-label" }, r.sheet),
      h("div", { class: "bar-pair" },
        h("div", { class: "bar orig", style: `width:${(r.grade_original / max) * 100}%` }, h("span", {}, "original " + r.grade_original)),
        h("div", { class: "bar plain", style: `width:${(r.grade_plain / max) * 100}%` }, h("span", {}, "plain " + r.grade_plain))))));
}

function runTable(run) {
  return h("div", { class: "table-wrap" }, h("table", { class: "report-table" },
    h("thead", {}, h("tr", {}, ["Sheet", "Medicines found", "Dose correct", "Warning-sign keywords", "Follow-up keywords", "Items flagged", "Reading grade"].map((t) => h("th", {}, t)))),
    h("tbody", {}, run.rows.map((r) => h("tr", {}, [r.sheet, r.medicines, r.doses, r.red_flags, r.follow_ups, r.flagged, r.grade].map((c) => h("td", {}, c)))),
      run.total ? h("tr", { class: "total" }, [run.total.sheet, run.total.medicines, run.total.doses, run.total.red_flags, run.total.follow_ups, run.total.flagged, ""].map((c) => h("td", {}, c))) : null)));
}

function runBlock(run, open) {
  return h("details", { class: "card run", open: open ? true : null },
    h("summary", {}, run.name, run.total ? ` — medicines ${run.total.medicines}, doses ${run.total.doses}, warning signs ${run.total.red_flags}` : ""),
    run.header ? h("p", { class: "small" }, run.header.replace(/`/g, "")) : null,
    run.why ? h("p", { class: "small" }, run.why) : null,
    runTable(run),
    h("p", {}, run.misses.length ? h("b", {}, "Misses:") : h("b", {}, "Misses: none in this run.")),
    run.misses.length ? h("ul", {}, run.misses.map((m) => h("li", {}, m))) : null,
    run.qa ? h("p", {}, h("b", {}, "Grounded Q&A: "), run.qa) : null);
}

function reportPage(rep) {
  const first = rep.final[0];
  return h("div", {},
    h("h2", { class: "page-title" }, "Report card"),
    h("p", { class: "lead" }, "How Sendhome did on its own self-check, including the misses. " + rep.caveat),
    h("section", { class: "card" }, h("h3", {}, "Reading grade, before and after (approximate)"),
      first ? gradeBars(first.rows) : null,
      h("p", { class: "small" }, "Approximate Flesch–Kincaid grade, computed locally from the original sheet and the plain-language output. Drug names and clinical terms inflate it. Shown for the first final run; see the tables for the others.")),
    h("h3", { class: "sec" }, "Final runs (current prompts)"),
    rep.final.map((r, i) => runBlock(r, i === 0)),
    h("h3", { class: "sec" }, "Earlier runs we kept for transparency"),
    h("p", { class: "small" }, "These are from before two fixes. We kept them so the improvement is visible and nothing is hidden."),
    rep.earlier.map((r) => runBlock(r, false)),
    h("p", { class: "small" }, "Everything on this page is read from files committed in the repo (eval/). Nothing is computed from your text."));
}
