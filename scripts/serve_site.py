#!/usr/bin/env python3
"""Preview the Cloudflare Pages output, including _headers and real 404s.

No build, credentials, or network requests. Usage: python3 scripts/serve_site.py
"""

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "docs"
COPIED = {"index.html", "styles.css", "script.js", "data", "img"}


def output_path(url):
    """Resolve a served URL against the same overlay as the Pages copy step."""
    path = unquote(urlsplit(url).path).lstrip("/")
    if not path or path.endswith("/"):
        path += "index.html"
    if ".." in Path(path).parts:
        raise ValueError("Path escapes the output tree")
    first = path.split("/", 1)[0]
    target = ROOT / "site" / path if first in COPIED else ROOT / path
    # Pages serves HTML without its final .html suffix, including index.zh.
    # Resolve only an existing file; unknown routes still receive a real 404.
    html = target.with_name(target.name + ".html")
    return html if not target.exists() and html.is_file() else target


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def translate_path(self, path):
        try:
            return str(output_path(path))
        except ValueError:
            return str(ROOT / "__invalid_path__")

    def end_headers(self):
        config = ROOT / "_headers"
        if config.is_file():
            for line in config.read_text().splitlines():
                if line.startswith("  ") and ":" in line:
                    name, value = line.strip().split(":", 1)
                    # Browsers ignore HSTS on the local HTTP preview.
                    self.send_header(name, value.strip())
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        page = ROOT / "404.html"
        if code != 404 or not page.is_file():
            return super().send_error(code, message, explain)
        body = page.read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def log_message(self, *_args):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    class Server(ThreadingHTTPServer):
        request_queue_size = 128

    server = Server(("127.0.0.1", args.port), Handler)
    print(f"Preview: http://127.0.0.1:{args.port}/ (Pages overlay, no SPA fallback)", flush=True)
    server.serve_forever()
