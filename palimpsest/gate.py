"""SupersessionGate: decide which of two retrieved passages is in force.

Code settles what the documents state outright (explicit references and printed dates).
Decider 2B answers small yes or no reading questions about the pair.
Anything the evidence cannot settle is reported as a conflict and never guessed.
"""
import re
from dataclasses import dataclass, field

from . import decider

HIGH, LOW = 0.60, 0.45  # set from one real probe run (2 revising passages scored 0.67 and 0.82, the rest 0.37 or lower). Re-run palimpsest.probe on your own documents.
QUESTION = {"revises": {"type": "noul", "instructions": "Does this passage say it replaces or revises an earlier rule?"}}
PARTIAL = re.compile(r"all other|the rest|remain|stay|unchanged|only", re.I)
FILLER = {"revised", "amendment", "amended", "notice", "draft", "update", "updated"}
DATE = re.compile(r"(?:effective|issued|dated)[^0-9]{0,12}(\d{4}-\d{2}-\d{2})", re.I)
SUPERSEDES = re.compile(r"(?:supersedes|replaces|rescinds)\s+(?:circular|policy|notice)?\s*([A-Z]{1,5}-\d{1,4})", re.I)
STOP = set("""about after also and any are because been before being between both but can cannot does each for from have how into more must not only other over per such than that the their them then there these they this those under upon was were what when where which while who will with within without would your eastgate college""".split())


@dataclass
class Passage:
    pid: str
    text: str
    ref: str = ""
    date: str = ""

    @property
    def family(self):
        """Document family from the title line: same family means the same rulebook in another version."""
        line = next((l for l in self.text.splitlines() if l.strip() and not l.startswith("Ref:")), "")
        head = re.split(r"[.,]", line)[0].lower()
        return " ".join(w for w in head.split() if w not in FILLER)

    @classmethod
    def parse(cls, pid, raw):
        ref = re.search(r"^Ref:\s*(\S+)", raw, re.M)
        date = DATE.search(raw)
        return cls(pid, raw, ref.group(1) if ref else "", date.group(1) if date else "")


@dataclass
class Verdict:
    keep: list
    status: str  # decided | conflict
    reason: str
    confidence: float = 1.0
    via: str = "code"
    latency_ms: float = 0.0
    dropped: list = field(default_factory=list)
    base: str = ""       # set when one passage amends another that stays in force
    amends: str = ""


def revises(p, ask, cache):
    """One short Decider call per passage, cached. Returns (probability, ms)."""
    key = ("rev", p.pid)
    if key not in cache:
        ans, ms = ask(p.text, QUESTION)
        cache[key] = (float(ans["revises"]["noul"]), ms or 0.0)
    return cache[key]


def _amend(new, old, ms, p):
    if PARTIAL.search(new.text):
        return Verdict([old.pid, new.pid], "decided", f"{new.pid} amends {old.pid} and the rest of it stays", p, "decider+code", ms, base=old.pid, amends=new.pid)
    return Verdict([new.pid], "decided", f"{new.pid} says it revises the other", p, "decider+code", ms, [old.pid])


def judge_pair(q, a, b, ask=decider.ask, high=HIGH, low=LOW, cache=None):
    """q is accepted for symmetry with older callers. The verdict depends only on the pair."""
    cache = {} if cache is None else cache
    for new, old in ((a, b), (b, a)):  # 1. explicit reference, settled in code
        m = SUPERSEDES.search(new.text)
        if m and old.ref and m.group(1).upper() == old.ref.upper():
            return Verdict([new.pid], "decided", f"{new.pid} names {old.ref} as replaced", 1.0, "code", 0.0, [old.pid])
    (ra, ma), (rb, mb) = revises(a, ask, cache), revises(b, ask, cache)  # 2. what each passage says about itself
    ms = ma + mb
    rev = {a.pid: ra, b.pid: rb}
    if a.date and b.date and a.date != b.date:  # 3. printed dates order them
        new, old = (a, b) if a.date > b.date else (b, a)
        if rev[old.pid] >= high and rev[new.pid] < low:
            return Verdict([a.pid, b.pid], "conflict", "the older passage claims to revise the newer one", rev[old.pid], "decider+code", ms)
        if rev[new.pid] >= high:
            return _amend(new, old, ms, rev[new.pid])
        if a.family == b.family:
            return Verdict([new.pid], "decided", f"{new.pid} is the later version of the same document", 1 - max(ra, rb), "decider+code", ms, [old.pid])
        return Verdict([a.pid, b.pid], "conflict", "different documents and no sign that one replaces the other", 1 - max(ra, rb), "decider+code", ms)
    for new, old in ((b, a), (a, b)):  # 4. no usable dates: the wording decides
        if rev[new.pid] >= high and rev[old.pid] < low:
            return _amend(new, old, ms, rev[new.pid])
    return Verdict([a.pid, b.pid], "conflict", "no dates and no clear sign of which came first", max(ra, rb), "decider", ms)


def _words(t):
    return {w for w in re.findall(r"[a-z]{4,}", t.lower()) if w not in STOP}


def overlap(a, b, threshold=0.25):
    x, y = _words(a.text), _words(b.text)
    return len(x & y) / max(1, len(x | y)) >= threshold


def gate(q, passages, ask=decider.ask, cache=None):
    """Reduce a retrieved set to what the LLM may see. Returns (kept, verdicts)."""
    cache = {} if cache is None else cache
    kept = {p.pid: p for p in passages}
    verdicts = []
    for i, a in enumerate(passages):
        for b in passages[i + 1:]:
            if a.pid not in kept or b.pid not in kept or not overlap(a, b):
                continue
            key = tuple(sorted((a.pid, b.pid)))
            if key not in cache:
                cache[key] = judge_pair(q, a, b, ask, cache=cache)
            v = cache[key]
            verdicts.append(v)
            for d in v.dropped:
                kept.pop(d, None)
    return list(kept.values()), verdicts


def warm(passages, cache, ask=decider.ask, log=print):
    """Ask the model about each passage that has a look alike, once. Nothing is written to disk."""
    from itertools import combinations
    pairs = [(a, b) for a, b in combinations(passages, 2) if overlap(a, b)]
    for n, (a, b) in enumerate(pairs, 1):
        log(f"Checking pair {n} of {len(pairs)}: {a.pid} and {b.pid}")
        gate("", [a, b], ask=ask, cache=cache)
