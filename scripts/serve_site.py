#!/usr/bin/env python3
"""Preview the Pages overlay; optionally proxy the two live-check endpoints.

The proxy binds to loopback, never logs bodies, and forwards no browser cookies.
Without --proxy-api, this remains a static, network-free preview.
"""

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "docs"
COPIED = {"index.html", "styles.css", "script.js", "data", "img"}


def output_path(url, root=ROOT):
    """Resolve a served URL against the same overlay as the Pages copy step."""
    path = unquote(urlsplit(url).path).lstrip("/")
    if not path or path.endswith("/"):
        path += "index.html"
    if ".." in Path(path).parts:
        raise ValueError("Path escapes the output tree")
    first = path.split("/", 1)[0]
    target = root / "site" / path if first in COPIED else root / path
    # Match Pages extensionless HTML routes without changing the preview root.
    html = target.with_name(target.name + ".html")
    return html if not target.exists() and html.is_file() else target


def proxy_origin(value):
    url = urlsplit(value)
    if (url.scheme != "https" or not url.hostname or url.username or url.password
            or url.path not in ("", "/") or url.query or url.fragment):
        raise argparse.ArgumentTypeError("--proxy-api requires an HTTPS origin without credentials or a path")
    return f"https://{url.netloc}"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        # In particular, never redirect a password-bearing POST to another host.
        return None


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def translate_path(self, path):
        try:
            return str(output_path(path, self.server.docs_root))
        except ValueError:
            return str(self.server.docs_root / "__invalid_path__")

    def do_GET(self):
        if not self.proxy_request():
            super().do_GET()

    def do_HEAD(self):
        if not self.proxy_request():
            super().do_HEAD()

    def do_POST(self):
        if not self.proxy_request():
            self.send_error(405)

    def proxy_request(self):
        path = urlsplit(self.path)
        if path.path not in ("/api/budget", "/api/history", "/api/check", "/api/check-example", "/api/compare"):
            return False
        origin = self.server.proxy_api
        if not origin:
            self.send_error(404)
            return True
        allowed = ("GET", "HEAD") if path.path in ("/api/budget", "/api/history") else ("POST",)
        if self.command not in allowed or (path.query and path.path != "/api/history"):
            self.send_error(405)
            return True
        local = f"http://127.0.0.1:{self.server.server_port}"
        if self.headers.get("Origin", local) != local:
            self.send_error(403)
            return True
        body = None
        if self.command == "POST":
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if (not 0 < length <= 16384 or self.headers.get("Transfer-Encoding")
                    or self.headers.get_content_type() != "application/json"):
                self.close_connection = True
                self.send_error(400)
                return True
            with self.server.check_lock:
                if self.server.check_count >= self.server.max_checks:
                    self.close_connection = True
                    self.send_error(429, "Local take limit reached")
                    return True
                self.server.check_count += 1  # Includes failed and partial attempts.
            body = self.rfile.read(length)
        request = Request(origin + path.path + (f"?{path.query}" if path.query else ""), data=body, method=self.command,
                          headers={"Origin": origin, "Content-Type": "application/json",
                                   "Accept": "application/json",
                                   # Cloudflare's browser integrity check (error 1010) rejects the
                                   # urllib default agent; identify as the recording browser instead.
                                   "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                                 "AppleWebKit/537.36 (KHTML, like Gecko) "
                                                 "Chrome/131.0.0.0 Safari/537.36 live-check-preview"})
        try:
            response = build_opener(NoRedirect()).open(request, timeout=40)
        except HTTPError as error:
            response = error
        except (URLError, TimeoutError, OSError):
            self.send_error(502, "Live-check upstream unavailable")
            return True
        with response:
            payload = response.read(2 * 1024 * 1024 + 1)
            if len(payload) > 2 * 1024 * 1024 or 300 <= response.code < 400:
                self.send_error(502, "Invalid upstream response")
                return True
            self.send_response(response.code)
            self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload)
        return True

    def end_headers(self):
        config = self.server.docs_root / "_headers"
        if config.is_file():
            for line in config.read_text().splitlines():
                if line.startswith("  ") and ":" in line:
                    name, value = line.strip().split(":", 1)
                    # Browsers ignore HSTS on the local HTTP preview.
                    self.send_header(name, value.strip())
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        page = self.server.docs_root / "404.html"
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--docs-root", type=Path, default=ROOT, help="Optional committed-main docs snapshot")
    parser.add_argument("--proxy-api", type=proxy_origin)
    parser.add_argument("--max-checks", type=int, choices=range(1, 4), default=3,
                        help="Hard limit on forwarded checks, including failures (no retries)")
    args = parser.parse_args()
    class Server(ThreadingHTTPServer):
        request_queue_size = 128

    server = Server(("127.0.0.1", args.port), Handler)
    server.docs_root = args.docs_root.resolve()
    server.proxy_api = args.proxy_api
    server.max_checks = args.max_checks
    server.check_count = 0
    server.check_lock = threading.Lock()
    print(f"Preview: http://127.0.0.1:{server.server_port}/ (Pages overlay, no SPA fallback)", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
