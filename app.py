"""Local demo server. Binds to 127.0.0.1, stores nothing, logs no question text."""
import json
import pathlib
from http.server import BaseHTTPRequestHandler, HTTPServer

from palimpsest.gate import gate, warm
from palimpsest.retrieve import load, top_k

PASSAGES = load("corpus")
CACHE = {}
STATIC = pathlib.Path("static")


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # privacy: no request logging
        pass

    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("cache-control", "no-store")
        self.send_header("content-security-policy", "default-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        name = {"/": "index.html"}.get(self.path, self.path.lstrip("/"))
        f = (STATIC / name).resolve()
        if STATIC.resolve() in f.parents and f.is_file():
            ctype = "text/css" if f.suffix == ".css" else "application/javascript" if f.suffix == ".js" else "text/html; charset=utf-8"
            return self._send(200, f.read_bytes(), ctype)
        self._send(404, b"{}")

    def do_POST(self):
        if self.path != "/api/ask":
            return self._send(404, b"{}")
        n = min(int(self.headers.get("content-length", 0)), 2000)
        q = json.loads(self.rfile.read(n) or b"{}").get("q", "")[:500]
        try:
            got = top_k(q, PASSAGES)
            kept, verdicts = gate(q, got, cache=CACHE)
            out = {"retrieved": [p.pid for p in got], "kept": [p.pid for p in kept],
                   "texts": {p.pid: p.text for p in got},
                   "verdicts": [v.__dict__ for v in verdicts]}
            self._send(200, json.dumps(out).encode())
        except Exception as e:
            self._send(502, json.dumps({"error": str(e)}).encode())


if __name__ == "__main__":
    warm(PASSAGES, CACHE, log=lambda m: print(m, flush=True))
    print("Palimpsest on http://127.0.0.1:8080 (decider expected at STRANDS_DECIDER_URL or 127.0.0.1:8000)")
    HTTPServer(("127.0.0.1", 8080), H).serve_forever()
