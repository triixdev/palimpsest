"""Compare SupersessionGate (Decider 2B local) with Nova Lite on the same pair and the same four labels.
Needs the decider server running and AWS credentials and BEDROCK_MODEL_ID.
Prints accuracy and wrong version rate and lost passage rate and abstain rate and latency."""
import os
import statistics
import time

from bench.cases import C
from palimpsest.gate import Passage, judge_pair


def run_gate(rows, ask=None):
    out = []
    for q, ta, tb, g in rows:
        a, b = Passage.parse("A", ta), Passage.parse("B", tb)
        t = time.time()
        v = judge_pair(q, a, b, **({"ask": ask} if ask else {}))
        pred = "abstain" if v.status == "conflict" else ("both" if len(v.keep) == 2 else v.keep[0])
        out.append((g, pred, (time.time() - t) * 1000))
    return out


def run_llm(rows):
    import boto3
    br = boto3.client("bedrock-runtime")
    out = []
    for q, ta, tb, g in rows:
        prompt = (f"Question: {q}\n\nPassage A:\n{ta}\n\nPassage B:\n{tb}\n\n"
                  "Which passage states the rule in force? Reply with one word: A or B or both or abstain (if the passages cannot be ordered).")
        t = time.time()
        r = br.converse(modelId=os.environ["BEDROCK_MODEL_ID"],
                        messages=[{"role": "user", "content": [{"text": prompt}]}],
                        inferenceConfig={"temperature": 0, "maxTokens": 10})
        text = r["output"]["message"]["content"][0]["text"].strip()
        w = (text.split() or [""])[0].strip(".,:;!*").lower()
        out.append((g, {"a": "A", "b": "B"}.get(w, w), (time.time() - t) * 1000))
    return out


def score(name, res):
    n = len(res)
    acc = sum(g == p for g, p, _ in res) / n
    wrong = sum(g in ("A", "B") and p in ("A", "B") and p != g for g, p, _ in res) / n
    lost = sum(g == "both" and p in ("A", "B") for g, p, _ in res) / n
    stale = sum(g == "abstain" and p in ("A", "B", "both") for g, p, _ in res) / max(1, sum(g == "abstain" for g, _, _ in res))
    print(f"{name}: n={n} accuracy={acc:.2f} wrong_version={wrong:.2f} lost_needed_passage={lost:.2f} guessed_when_should_abstain={stale:.2f} median_ms={statistics.median(m for *_, m in res):.0f}")


if __name__ == "__main__":
    score("gate+decider", run_gate(C))
    if os.environ.get("BEDROCK_MODEL_ID"):
        score("nova-lite alone", run_llm(C))
