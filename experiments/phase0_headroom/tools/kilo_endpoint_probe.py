from __future__ import annotations

import argparse
import contextlib
import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.parse
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


MODEL = "gpt-5.4-mini"
PROVIDER = "openai-compatible"


@dataclass
class ProbeResult:
    mode: str
    returncode: int
    duration_seconds: float
    stdout: str
    stderr: str
    requests: list[dict[str, Any]]
    temp_root: str


class RecordingHandler(BaseHTTPRequestHandler):
    server: "RecordingServer"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_body(self) -> bytes:
        length = int(self.headers.get("content-length") or 0)
        return self.rfile.read(length) if length else b""

    def _record(self, body: bytes) -> dict[str, Any]:
        auth = self.headers.get("authorization")
        parsed_body: Any = None
        with contextlib.suppress(json.JSONDecodeError):
            parsed_body = json.loads(body.decode("utf-8"))
        row = {
            "method": self.command,
            "path": urllib.parse.urlparse(self.path).path,
            "authorization_present": bool(auth),
            "authorization_matches_probe_key": auth == f"Bearer {self.server.expected_key}",
            "accept": self.headers.get("accept"),
            "content_type": self.headers.get("content-type"),
            "body_keys": sorted(parsed_body) if isinstance(parsed_body, dict) else None,
            "model": parsed_body.get("model") if isinstance(parsed_body, dict) else None,
            "stream": parsed_body.get("stream") if isinstance(parsed_body, dict) else None,
            "messages_count": len(parsed_body.get("messages", [])) if isinstance(parsed_body, dict) else None,
            "tools_count": len(parsed_body.get("tools", [])) if isinstance(parsed_body, dict) and isinstance(parsed_body.get("tools"), list) else 0,
        }
        self.server.records.put(row)
        return row

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self._record(b"")
        if urllib.parse.urlparse(self.path).path.endswith("/models"):
            self._send_json(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": MODEL,
                            "object": "model",
                            "created": 0,
                            "owned_by": "probe",
                        }
                    ],
                },
            )
            return
        self._send_json(404, {"error": {"message": "not found"}})

    def do_POST(self) -> None:
        body = self._read_body()
        row = self._record(body)
        path = urllib.parse.urlparse(self.path).path
        if not path.endswith("/chat/completions"):
            self._send_json(404, {"error": {"message": "not found"}})
            return
        if not row["authorization_matches_probe_key"]:
            self._send_json(401, {"error": {"message": "missing or wrong auth"}})
            return
        if row["stream"]:
            chunks = [
                {"id": "chatcmpl-probe", "object": "chat.completion.chunk", "created": 0, "model": MODEL, "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]},
                {"id": "chatcmpl-probe", "object": "chat.completion.chunk", "created": 0, "model": MODEL, "choices": [{"index": 0, "delta": {"content": "PONG"}, "finish_reason": None}]},
                {"id": "chatcmpl-probe", "object": "chat.completion.chunk", "created": 0, "model": MODEL, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
            ]
            payload = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks) + "data: [DONE]\n\n"
            data = payload.encode("utf-8")
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("cache-control", "no-cache")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._send_json(
            200,
            {
                "id": "chatcmpl-probe",
                "object": "chat.completion",
                "created": 0,
                "model": MODEL,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "PONG"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            },
        )


class RecordingServer(ThreadingHTTPServer):
    def __init__(self, expected_key: str):
        super().__init__(("127.0.0.1", 0), RecordingHandler)
        self.expected_key = expected_key
        self.records: queue.Queue[dict[str, Any]] = queue.Queue()


def base_url_with_v1(raw: str) -> str:
    base = raw.rstrip("/")
    return base if base.endswith("/v1") else f"{base}/v1"


def write_kilo_config(config_dir: Path, base_url: str, permission: dict[str, Any] | None = None) -> None:
    kilo_dir = config_dir / "kilo"
    kilo_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "$schema": "https://app.kilo.ai/config.json",
        "model": f"{PROVIDER}/{MODEL}",
        "enabled_providers": [PROVIDER],
        "permission": permission or {"*": "deny"},
        "provider": {
            PROVIDER: {
                "options": {
                    "apiKey": "{env:LLM_API_KEY}",
                    "baseURL": base_url,
                    "timeout": 60000,
                },
                "models": {
                    MODEL: {
                        "name": "GPT 5.4 Mini Endpoint Probe",
                        "id": MODEL,
                        "tool_call": True,
                        "reasoning": True,
                        "temperature": False,
                        "limit": {
                            "context": 400000,
                            "output": 1024,
                        },
                    }
                },
            }
        },
    }
    (kilo_dir / "kilo.jsonc").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_env(temp_root: Path, api_key: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(temp_root / "home"),
            "XDG_CONFIG_HOME": str(temp_root / "config"),
            "XDG_DATA_HOME": str(temp_root / "data"),
            "XDG_CACHE_HOME": str(temp_root / "cache"),
            "XDG_STATE_HOME": str(temp_root / "state"),
            "LLM_API_KEY": api_key,
        }
    )
    return env


def run_kilo(
    workspace: Path,
    env: dict[str, str],
    timeout: int,
    message: str,
    *,
    auto: bool = False,
    print_logs: bool = False,
) -> tuple[subprocess.CompletedProcess[str], float]:
    workspace.mkdir(parents=True, exist_ok=True)
    command = [
        shutil.which("kilo") or "kilo",
        "run",
        "--pure",
        "--format",
        "json",
        "--model",
        f"{PROVIDER}/{MODEL}",
        "--dir",
        str(workspace),
    ]
    if auto:
        command.append("--auto")
    if print_logs:
        command.extend(["--print-logs", "--log-level", "DEBUG"])
    command.append(message)
    start = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=workspace,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return completed, time.monotonic() - start


def collect_records(server: RecordingServer) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    while True:
        try:
            rows.append(server.records.get_nowait())
        except queue.Empty:
            return rows


def run_mock(timeout: int) -> ProbeResult:
    temp_root = Path(tempfile.mkdtemp(prefix="kilo-probe-mock-"))
    probe_key = "KILO_PROBE_MARKER_KEY"
    server = RecordingServer(probe_key)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_port}/v1"
        write_kilo_config(temp_root / "config", base_url)
        completed, duration = run_kilo(
            temp_root / "workspace",
            build_env(temp_root, probe_key),
            timeout,
            "Reply exactly PONG. Do not inspect files, run tools, or edit files.",
        )
        requests = collect_records(server)
        return ProbeResult("mock", completed.returncode, duration, completed.stdout, completed.stderr, requests, str(temp_root))
    finally:
        server.shutdown()
        server.server_close()


def run_live(timeout: int) -> ProbeResult:
    base = os.environ.get("LLM_BASE_URL")
    key = os.environ.get("LLM_API_KEY")
    if not base or not key:
        raise SystemExit("LLM_BASE_URL and LLM_API_KEY are required for live mode")
    temp_root = Path(tempfile.mkdtemp(prefix="kilo-probe-live-"))
    write_kilo_config(temp_root / "config", base_url_with_v1(base))
    completed, duration = run_kilo(
        temp_root / "workspace",
        build_env(temp_root, key),
        timeout,
        "Reply exactly PONG. Do not inspect files, run tools, or edit files.",
    )
    return ProbeResult("live", completed.returncode, duration, completed.stdout, completed.stderr, [], str(temp_root))


def run_workspace_live(timeout: int) -> ProbeResult:
    base = os.environ.get("LLM_BASE_URL")
    key = os.environ.get("LLM_API_KEY")
    if not base or not key:
        raise SystemExit("LLM_BASE_URL and LLM_API_KEY are required for workspace-live mode")
    temp_root = Path(tempfile.mkdtemp(prefix="kilo-probe-workspace-live-"))
    workspace = temp_root / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    target = workspace / "target.txt"
    target.write_text("before\n", encoding="utf-8")
    write_kilo_config(temp_root / "config", base_url_with_v1(base), permission={"*": "allow"})
    completed, duration = run_kilo(
        workspace,
        build_env(temp_root, key),
        timeout,
        "Edit target.txt so its entire content is exactly PONG followed by a newline. Do not modify any other file.",
        auto=True,
    )
    requests = [
        {
            "workspace_target_content": target.read_text(encoding="utf-8") if target.exists() else None,
            "workspace_files": sorted(path.name for path in workspace.iterdir()),
        }
    ]
    return ProbeResult("workspace-live", completed.returncode, duration, completed.stdout, completed.stderr, requests, str(temp_root))


def summarize(result: ProbeResult) -> dict[str, Any]:
    stdout_text = result.stdout.replace(result.temp_root, "<temp_root>")
    stderr_text = result.stderr.replace(result.temp_root, "<temp_root>")
    return {
        "mode": result.mode,
        "returncode": result.returncode,
        "duration_seconds": round(result.duration_seconds, 3),
        "stdout_contains_pong": "PONG" in stdout_text,
        "stderr_error_prefix": stderr_text[-1000:] if result.returncode else "",
        "stdout_prefix": stdout_text[:1200],
        "requests": result.requests,
        "temp_root": "<temp_root>",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run isolated Kilo endpoint probes.")
    parser.add_argument("--mode", choices=["mock", "live", "workspace-live"], required=True)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()

    if args.mode == "mock":
        result = run_mock(args.timeout)
    elif args.mode == "live":
        result = run_live(args.timeout)
    else:
        result = run_workspace_live(args.timeout)
    print(json.dumps(summarize(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
