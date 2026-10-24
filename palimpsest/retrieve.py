"""Small stdlib retriever (term overlap). Swap in embeddings or a Bedrock Knowledge Base without touching the gate."""
import math
import pathlib
import re

from .gate import STOP, Passage


def load(folder):
    return [Passage.parse(p.stem, p.read_text(encoding="utf-8")) for p in sorted(pathlib.Path(folder).glob("*.txt"))]


def top_k(q, passages, k=4):
    toks = lambda t: [w for w in re.findall(r"[a-z]{3,}", t.lower()) if w not in STOP]
    df = {}
    for p in passages:
        for t in set(toks(p.text)):
            df[t] = df.get(t, 0) + 1
    n = len(passages)

    def score(p):
        words = toks(p.text)
        return sum(words.count(t) * math.log(1 + n / df.get(t, n)) for t in set(toks(q)))

    ranked = sorted(((score(p), p) for p in passages), key=lambda x: -x[0])
    top = ranked[0][0] if ranked else 0
    return [p for s, p in ranked[:k] if s > 0 and s >= 0.5 * top]
