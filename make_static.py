"""Build docs/data.json for the GitHub Pages demo.

It runs the real gate and the real retriever. The only recorded part is the Decider 2B score for each passage.
Those scores and timings came from one real run of python -m palimpsest.probe on a CPU laptop.
To refresh them run the probe again and update RECORDED. Then run: python make_static.py
"""
import json
import pathlib

from palimpsest.gate import gate
from palimpsest.retrieve import load, top_k

RECORDED = {  # passage id: (revises probability, milliseconds)
    "hostel_a": (0.18, 26949), "hostel_b": (0.18, 29924), "lab_2025": (0.31, 31421),
    "leave_2022": (0.13, 29084), "leave_2025": (0.88, 29113), "library_2024": (0.17, 28560),
    "library_2026": (0.67, 28346), "refund_2023": (0.29, 30659), "refund_2026": (0.29, 30217),
}
QUESTIONS = [
    ("Casual leave", "How many days of casual leave can I take?"),
    ("Tuition refund", "How many days do I have to withdraw for a full tuition refund?"),
    ("Library fines", "What is the overdue charge for library books?"),
    ("Hostel gates", "What time do hostel gates close?"),
    ("Lab safety", "What do I need to wear in the chemistry lab?"),
]

passages = load("corpus")
by_text = {p.text: p.pid for p in passages}


def recorded_ask(state, questions):
    p, ms = RECORDED[by_text[state]]
    return {"revises": {"noul": p}}, float(ms)


cache, out = {}, []
for label, q in QUESTIONS:
    got = top_k(q, passages)
    kept, verdicts = gate(q, got, ask=recorded_ask, cache=cache)
    out.append({"label": label, "q": q, "retrieved": [p.pid for p in got], "kept": [p.pid for p in kept],
                "texts": {p.pid: p.text for p in got}, "verdicts": [v.__dict__ for v in verdicts]})
pathlib.Path("docs/data.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
for r in out:
    print(r["label"], "| retrieved", r["retrieved"], "| kept", r["kept"], "|", [v["status"] for v in r["verdicts"]])
