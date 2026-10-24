const $ = (s) => document.querySelector(s);
const out = $("#out");

function show() {
  const id = (location.hash || "#demo").slice(1);
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== id));
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

function render(d) {
  const dropped = {}; const roles = {}; let conflictIds = new Set();
  d.verdicts.forEach((v) => {
    v.dropped.forEach((x) => (dropped[x] = v));
    if (v.amends) { roles[v.base] = "base rule, still applies"; roles[v.amends] = "amendment, applies on top of the base rule"; }
    if (v.status === "conflict") v.keep.forEach((x) => conflictIds.add(x));
  });
  const nodes = d.retrieved.map((id) => {
    const state = dropped[id] ? "gone" : conflictIds.has(id) ? "conflict" : "";
    const row = el("div", "row " + state);
    const h = el("h3", "", id);
    const note = roles[id] ? roles[id] : dropped[id] ? "out of date, withheld from the answering model" : state === "conflict" ? "conflicts with another source, a person must confirm" : "in force";
    h.append(el("span", "tag", "  " + note));
    row.append(h, el("p", "", d.texts[id]));
    return row;
  });
  const box = el("div", "verdict");
  if (!d.verdicts.length) box.append(el("p", "", "No two retrieved passages overlap, so nothing needed ordering."));
  d.verdicts.forEach((v) => {
    const how = v.via === "code" ? "settled by code from an explicit reference" : v.via === "decider" ? "judged by Decider 2B" : "Decider 2B checked against stated dates";
    const conf = v.via === "code" ? "" : ", confidence " + Number(v.confidence).toFixed(2) + ", " + Math.round(v.latency_ms / 1000) + " s of model time, checked once at startup";
    box.append(el("p", "", (v.status === "conflict" ? "Needs a person: " : "Decided: ") + v.reason + ". " + how + conf + "."));
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
