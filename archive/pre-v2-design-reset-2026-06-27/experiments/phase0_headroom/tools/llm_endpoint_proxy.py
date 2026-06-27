from __future__ import annotations

import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterable


DUMMY_API_KEY_ENV = "BARCAROLLE_LLM_PROXY_API_KEY"
DUMMY_API_KEY_VALUE = "barcarolle-local-proxy-key"
DEFAULT_UPSTREAM_TIMEOUT_SECONDS = 3600

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

SECRET_ENV_NAMES = {
    "LLM_API_KEY",
    "LLM_BASE_URL",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
}


def base_url_with_v1(raw: str) -> str:
    base = raw.rstrip("/")
    return base if base.endswith("/v1") else f"{base}/v1"


def sanitized_child_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    keep_prefixes = ("PATH", "HOME", "SHELL", "TMPDIR", "TEMP", "TMP", "LANG", "LC_", "USER", "LOGNAME")
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in SECRET_ENV_NAMES and (key in keep_prefixes or key.startswith("LC_") or key.startswith("XDG_"))
    }
    env[DUMMY_API_KEY_ENV] = DUMMY_API_KEY_VALUE
    if extra:
        env.update(extra)
    for name in SECRET_ENV_NAMES:
        env.pop(name, None)
    return env


def _forward_headers(headers: Iterable[tuple[str, str]], api_key: str) -> dict[str, str]:
    forwarded: dict[str, str] = {}
    for key, value in headers:
        lowered = key.lower()
        if lowered in HOP_BY_HOP_HEADERS or lowered in {"host", "authorization", "accept-encoding"}:
            continue
        forwarded[key] = value
    forwarded["Authorization"] = f"Bearer {api_key}"
    return forwarded


def _upstream_url(upstream_base_url: str, child_path: str) -> str:
    parsed = urllib.parse.urlsplit(child_path)
    path = parsed.path
    if path == "/v1":
        suffix = ""
    elif path.startswith("/v1/"):
        suffix = path[len("/v1") :]
    else:
        suffix = path
    rebuilt = urllib.parse.urlunsplit(("", "", suffix or "/", parsed.query, ""))
    return upstream_base_url.rstrip("/") + rebuilt


class _ProxyHandler(BaseHTTPRequestHandler):
    server: "LLMEndpointProxyServer"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        self._proxy()

    def do_POST(self) -> None:
        self._proxy()

    def do_DELETE(self) -> None:
        self._proxy()

    def do_OPTIONS(self) -> None:
        self._proxy()

    def _proxy(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        url = _upstream_url(self.server.upstream_base_url, self.path)
        request = urllib.request.Request(
            url,
            data=body,
            headers=_forward_headers(self.headers.items(), self.server.api_key),
            method=self.command,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.server.upstream_timeout_seconds) as response:
                payload = response.read()
                self.send_response(response.status)
                self._copy_response_headers(response.headers.items(), len(payload))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            self._copy_response_headers(exc.headers.items(), len(payload))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as exc:
            message = f"local LLM endpoint proxy failed: {type(exc).__name__}".encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)

    def _copy_response_headers(self, headers: Iterable[tuple[str, str]], payload_length: int) -> None:
        wrote_length = False
        for key, value in headers:
            lowered = key.lower()
            if lowered in HOP_BY_HOP_HEADERS:
                continue
            if lowered == "content-length":
                wrote_length = True
                self.send_header(key, str(payload_length))
            else:
                self.send_header(key, value)
        if not wrote_length:
            self.send_header("Content-Length", str(payload_length))


class LLMEndpointProxyServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], upstream_base_url: str, api_key: str, upstream_timeout_seconds: int):
        super().__init__(server_address, _ProxyHandler)
        self.upstream_base_url = base_url_with_v1(upstream_base_url)
        self.api_key = api_key
        self.upstream_timeout_seconds = upstream_timeout_seconds


class LLMEndpointProxy:
    def __init__(self, upstream_base_url: str, api_key: str, upstream_timeout_seconds: int = DEFAULT_UPSTREAM_TIMEOUT_SECONDS):
        self._server = LLMEndpointProxyServer(("127.0.0.1", 0), upstream_base_url, api_key, upstream_timeout_seconds)
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}/v1"

    def start(self) -> "LLMEndpointProxy":
        self._thread = threading.Thread(target=self._server.serve_forever, name="barcarolle-llm-endpoint-proxy", daemon=True)
        self._thread.start()
        return self

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._thread:
            self._thread.join(timeout=5)

    def __enter__(self) -> "LLMEndpointProxy":
        return self.start()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
