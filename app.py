"""Local demo server. Binds to 127.0.0.1 and stores nothing and logs no question text."""
import json
import pathlib
from http.server import BaseHTTPRequestHandler, HTTPServer

from palimpsest.gate import gate, warm
from palimpsest.retrieve import load, top_k

PORT = 8080
PASSAGES = load("corpus")
CACHE = {}
STATIC = pathlib.Path("static")
ALLOWED_HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
MAX_BODY = 4000


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # privacy: no request logging
        pass

    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff")
        self.send_header("content-security-policy", "default-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code, msg):
        self._send(code, json.dumps({"error": msg}).encode())

    def _host_ok(self):
        return self.headers.get("host", "") in ALLOWED_HOSTS

    def do_GET(self):
        if not self._host_ok():
            return self._err(403, "bad host")
        path = self.path.split("?", 1)[0]
        name = {"/": "index.html"}.get(path, path.lstrip("/"))
        f = (STATIC / name).resolve()
        if STATIC.resolve() in f.parents and f.is_file():
            ctype = "text/css" if f.suffix == ".css" else "application/javascript" if f.suffix == ".js" else "text/html; charset=utf-8"
            return self._send(200, f.read_bytes(), ctype)
        self._err(404, "not found")

    def do_POST(self):
        if not self._host_ok():
            return self._err(403, "bad host")
        if self.path != "/api/ask":
            return self._err(404, "not found")
        if not self.headers.get("content-type", "").startswith("application/json"):
            return self._err(415, "send application/json")
        try:
            n = int(self.headers.get("content-length", 0))
        except ValueError:
            return self._err(400, "bad length")
        if n > MAX_BODY:
            return self._err(413, "request too large")
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, UnicodeDecodeError):
            return self._err(400, "bad json")
        q = body.get("q") if isinstance(body, dict) else None
        if not isinstance(q, str) or not q.strip():
            return self._err(400, "q must be a non empty string")
        q = q[:500]
        try:
            got = top_k(q, PASSAGES)
            kept, verdicts = gate(q, got, cache=CACHE)
            out = {"retrieved": [p.pid for p in got], "kept": [p.pid for p in kept],
                   "texts": {p.pid: p.text for p in got},
                   "verdicts": [v.__dict__ for v in verdicts]}
            self._send(200, json.dumps(out).encode())
        except Exception as e:
            self._err(502, str(e))


if __name__ == "__main__":
    warm(PASSAGES, CACHE, log=lambda m: print(m, flush=True))
    print(f"Palimpsest on http://127.0.0.1:{PORT} (decider expected at STRANDS_DECIDER_URL or 127.0.0.1:8000)")
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()
