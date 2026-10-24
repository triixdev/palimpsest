"""Strands agent with one retrieval tool whose output has already passed the SupersessionGate.

BEDROCK_MODEL_ID is your region's Nova Lite model or inference profile id.
Run with --dry-run to see exactly what would be sent to Bedrock without calling it.
"""
import os
import sys

from .gate import gate, warm
from .retrieve import load, top_k

PASSAGES = load(os.environ.get("PALIMPSEST_CORPUS", "corpus"))
CACHE = {}


def render(kept, verdicts):
    conflict = any(v.status == "conflict" for v in verdicts)
    head = "SOURCES CONFLICT. Say so and show both. Do not pick one.\n" if conflict else ""
    amends = {v.amends: v.base for v in verdicts if v.amends}
    tag = lambda p: f"[{p.pid}] (AMENDMENT to [{amends[p.pid]}], apply it on top of that rule) " if p.pid in amends else f"[{p.pid}] "
    return head + "\n\n".join(tag(p) + p.text for p in kept)


def search_policies(question: str) -> str:
    """Find the policy passages that answer a question. Superseded passages are already removed."""
    kept, verdicts = gate(question, top_k(question, PASSAGES), cache=CACHE)
    return render(kept, verdicts)


def build():
    from strands import Agent, tool
    from strands.models import BedrockModel

    region = os.environ.get("AWS_REGION")
    model = BedrockModel(model_id=os.environ["BEDROCK_MODEL_ID"], **({"region_name": region} if region else {}))
    return Agent(
        model=model,
        tools=[tool(search_policies)],
        system_prompt=("Answer only from search_policies results and cite passage ids in brackets. "
                       "If the tool says sources conflict, report both and ask a person to confirm."),
    )


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    warm(PASSAGES, CACHE)
    agent = None if dry else build()
    while True:
        q = input("Question (blank to stop): ").strip()
        if not q:
            break
        if dry:
            print("--- what Bedrock would receive ---\n" + search_policies(q) + "\n")
        else:
            print(agent(q))
