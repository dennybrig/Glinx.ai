"""Local dashboard, bound to loopback; no file listing, uploads, or scan endpoint."""
import json
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PUBLIC_FILES = {"index.html", "styles.css", "app.js", "model.js", "demo.json", "favicon.svg", "memory.html", "memory.css", "memory.js", "memory-model.js", "memory-demo.json"}


def web_dir():
    packaged = Path(__file__).parent / "web"
    return packaged if (packaged / "index.html").exists() else Path(__file__).parent.parent / "dist"


def handler_for(payload, port, memory_payload=None):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get("Host") not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
                self.send_error(403)
                return
            path = urllib.parse.urlsplit(self.path).path.lstrip("/") or "index.html"
            if path == "initial.json":
                body, mime = json.dumps(payload).encode(), "application/json"
            elif path == "memory-demo.json" and memory_payload is not None:
                body, mime = json.dumps(memory_payload).encode(), "application/json"
            elif path in PUBLIC_FILES:
                body = (web_dir() / path).read_bytes()
                mime = {".js": "text/javascript", ".svg": "image/svg+xml"}.get(Path(path).suffix) or mimetypes.guess_type(path)[0] or "application/octet-stream"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", mime + ("; charset=utf-8" if mime != "image/svg+xml" else ""))
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; object-src 'none'")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass
    return Handler


def serve(report_path=None, port=8765):
    if not 1024 <= port <= 65535:
        raise ValueError("Choose a port from 1024 to 65535")
    path = Path(report_path) if report_path else web_dir() / "demo.json"
    if path.stat().st_size > 5_000_000:
        raise ValueError("Report exceeds 5 MB")
    payload = json.loads(path.read_text(encoding="utf-8"))
    with ThreadingHTTPServer(("127.0.0.1", port), handler_for(payload, port)) as server:
        print(f"Glinx dashboard: http://127.0.0.1:{port} (Ctrl+C to stop)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0
