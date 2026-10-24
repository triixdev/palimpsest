"""Thin client for a locally served Strands Decider 2B (/v1/systemone).

Request shape: {"state": str, "questions": {name: {"type": "noul"|"choice"|"score", "instructions": str, "criteria": ...}}}
"""
import json
import os
import urllib.request

BASE = os.environ.get("STRANDS_DECIDER_URL", "http://127.0.0.1:8000")


class DeciderError(RuntimeError):
    pass


def ask(state, questions, base=None, timeout=60):
    url = (base or BASE).rstrip("/") + "/v1/systemone"
    if not url.startswith(("http://", "https://")):
        raise DeciderError("decider url must start with http:// or https://")
    body = json.dumps({"state": state, "questions": questions}).encode()
    req = urllib.request.Request(url, data=body, headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310 (scheme checked above)
            data = json.load(r)
        return data["answers"], data.get("latency_ms") or 0.0
    except Exception as e:  # server not started or network down or bad reply
        raise DeciderError(f"decider unreachable or bad reply: {e}") from e
