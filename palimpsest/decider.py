"""Thin client for a locally served Strands Decider 2B (/v1/systemone).

Request shape confirmed from the LiteLLM provider docs and the strands-decider README:
{"state": str, "questions": {name: {"type": "noul"|"choice"|"score", "instructions": str, "criteria": ...}}}
"""
import json
import os
import urllib.request

BASE = os.environ.get("STRANDS_DECIDER_URL", "http://127.0.0.1:8000")


class DeciderError(RuntimeError):
    pass


def ask(state, questions, base=None, timeout=60):
    body = json.dumps({"state": state, "questions": questions}).encode()
    req = urllib.request.Request(
        (base or BASE).rstrip("/") + "/v1/systemone",
        data=body,
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
    except Exception as e:  # server not started, network down, bad JSON
        raise DeciderError(f"decider unreachable: {e}") from e
    return data["answers"], data.get("latency_ms")
