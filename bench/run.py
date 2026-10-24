"""Compare SupersessionGate (Decider 2B, local) with Nova Lite given the same pair and the same four labels.
Needs: decider server running, AWS credentials, BEDROCK_MODEL_ID. Prints accuracy, wrong-version rate, abstain rate, latency."""
import json
import os
import statistics
import time

from bench.cases import C
from palimpsest.gate import Passage, judge_pair


def gold_set(g, a, b):
    return {"A": [a.pid], "B": [b.pid], "both": [a.pid, b.pid], "abstain": [a.pid, b.pid]}[g]


def run_gate(rows, ask=None):
    out = []
    for q, ta, tb, g in rows:
        a, b = Passage.parse("A", ta), Passage.parse("B", tb)
        t = time.time()
        v = judge_pair(q, a, b, **({'ask': ask} if ask else {}))
        out.append((g, "abstain" if v.status == "conflict" else ("both" if len(v.keep) == 2 else v.keep[0]), (time.time() - t) * 1000))
    return out


def run_llm(rows):
    import boto3
    br = boto3.client("bedrock-runtime")
    out = []
    for q, ta, tb, g in rows:
        prompt = (f"Question: {q}\n\nPassage A:\n{ta}\n\nPassage B:\n{tb}\n\n"
                  "Which passage states the rule in force? Reply with one word: A, B, both, or abstain (if the passages cannot be ordered).")
        t = time.time()
        r = br.converse(modelId=os.environ["BEDROCK_MODEL_ID"], messages=[{"role": "user", "content": [{"text": prompt}]}])
        w = r["output"]["message"]["content"][0]["text"].strip().split()[0].strip(".").lower()
        out.append((g, {"a": "A", "b": "B"}.get(w, w), (time.time() - t) * 1000))
    return out


def score(name, res):
    n = len(res)
    acc = sum(g == p for g, p, _ in res) / n
    wrong = sum(g in ("A", "B") and p in ("A", "B") and p != g for g, p, _ in res) / n
    stale = sum(g == "abstain" and p in ("A", "B") for g, p, _ in res) / max(1, sum(g == "abstain" for g, _, _ in res))
    print(f"{name}: n={n} accuracy={acc:.2f} wrong_version={wrong:.2f} guessed_when_should_abstain={stale:.2f} median_ms={statistics.median(m for *_, m in res):.0f}")


if __name__ == "__main__":
    score("gate+decider", run_gate(C))
    if os.environ.get("BEDROCK_MODEL_ID"):
        score("nova-lite alone", run_llm(C))
