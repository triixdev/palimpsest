const $ = (s) => document.querySelector(s);
const out = $("#out");

function show() {
  const views = [...document.querySelectorAll(".view")];
  const want = (location.hash || "#demo").slice(1);
  const id = views.some((v) => v.id === want) ? want : "demo";
  views.forEach((v) => (v.hidden = v.id !== id));
}
addEventListener("hashchange", show); show();

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function skeleton() {
  out.replaceChildren(el("div", "sk"), el("div", "sk"), el("div", "sk"));
}

function fmt(ms) {
  const n = Number(ms) || 0;
  return n >= 1000 ? Math.round(n / 1000) + " s" : Math.round(n) + " ms";
}

function render(d) {
  const dropped = {}; const roles = {}; const conflictIds = new Set();
  d.verdicts.forEach((v) => {
    v.dropped.forEach((x) => (dropped[x] = v));
    if (v.amends) { roles[v.base] = "base rule that still applies"; roles[v.amends] = "amendment that applies on top of the base rule"; }
    if (v.status === "conflict") v.keep.forEach((x) => conflictIds.add(x));
  });
  const nodes = d.retrieved.map((id) => {
    const state = dropped[id] ? "gone" : conflictIds.has(id) ? "conflict" : "";
    const row = el("div", "row " + state);
    const h = el("h3", "", id);
    const note = roles[id] ? roles[id] : dropped[id] ? "out of date and withheld from the answering model" : state === "conflict" ? "conflicts with another source and a person must confirm" : "in force";
    h.append(el("span", "tag", "  " + note));
    row.append(h, el("p", "", d.texts[id]));
    return row;
  });
  const box = el("div", "verdict");
  if (!d.verdicts.length) box.append(el("p", "", "No two retrieved passages overlap so nothing needed ordering."));
  d.verdicts.forEach((v) => {
    const how = v.via === "code" ? "Settled by code from an explicit reference." : v.via === "decider" ? "Judged by Decider 2B." : "Decider 2B read it and code checked the dates.";
    const extra = v.via === "code" ? "" : (v.status === "conflict" ? "" : " Confidence " + Number(v.confidence).toFixed(2) + ".") + " Model time " + fmt(v.latency_ms) + ". Checked once at startup.";
    const p = el("p");
    p.append(el("strong", "", v.status === "conflict" ? "Needs a person" : "Decided"), " " + v.reason + ". " + how + extra);
    box.append(p);
  });
  out.replaceChildren(...nodes, box);
}

async function ask(q) {
  skeleton();
  try {
    const r = await fetch("/api/ask", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ q }) });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || "request failed");
    render(d);
  } catch (e) {
    out.replaceChildren(el("p", "err", "Could not reach the decision model. Start it with: strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8000 --device cpu. Detail: " + e.message));
  }
}

$("#ask").addEventListener("submit", (e) => { e.preventDefault(); ask($("#q").value); });
document.querySelectorAll(".samples button").forEach((b) => b.addEventListener("click", () => { $("#q").value = b.dataset.q; ask(b.dataset.q); }));
