from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from tuning_artifacts import ARTIFACT_SCHEMA_VERSION, materialize_artifact, with_computed_hash


ROOT = Path(__file__).resolve().parents[3]
PHASE0 = ROOT / "experiments" / "phase0_headroom"
CODEX_ADAPTER = PHASE0 / "tools" / "codex_workspace_adapter.py"
KILO_ADAPTER = PHASE0 / "tools" / "kilo_workspace_adapter.py"
MODEL = "gpt-5.4-mini"


@dataclass(frozen=True)
class SmokeCase:
    name: str
    agent_id: str
    surface: str
    artifact_type: str
    files: tuple[dict[str, str], ...]
    statement: str
    expected_phrases: tuple[str, ...]
    notes: str


class _CaptureServer(ThreadingHTTPServer):
    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _CaptureHandler)
        self.requests: list[dict[str, str]] = []
        self.lock = threading.Lock()


class _CaptureHandler(BaseHTTPRequestHandler):
    server: _CaptureServer

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        self._capture(None)
        if self.path.rstrip("/").endswith("/models"):
            self._send_json({"object": "list", "data": [{"id": MODEL, "object": "model", "owned_by": "barcarolle"}]})
            return
        self._send_json({"ok": True})

    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self._capture(body)
        text = body.decode("utf-8", errors="replace")
        wants_stream = '"stream":true' in text.replace(" ", "")
        if "chat/completions" in self.path:
            if wants_stream:
                self._send_sse(
                    [
                        {
                            "id": "chatcmpl_barcarolle_smoke",
                            "object": "chat.completion.chunk",
                            "choices": [{"index": 0, "delta": {"role": "assistant", "content": self._message_for(text)}, "finish_reason": None}],
                        },
                        {
                            "id": "chatcmpl_barcarolle_smoke",
                            "object": "chat.completion.chunk",
                            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                        },
                    ]
                )
            else:
                self._send_json(
                    {
                        "id": "chatcmpl_barcarolle_smoke",
                        "object": "chat.completion",
                        "model": MODEL,
                        "choices": [{"index": 0, "message": {"role": "assistant", "content": self._message_for(text)}, "finish_reason": "stop"}],
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    }
                )
            return

        if wants_stream:
            self._send_sse(
                [
                    {"type": "response.created", "response": {"id": "resp_barcarolle_smoke", "status": "in_progress"}},
                    {"type": "response.output_text.delta", "delta": self._message_for(text)},
                    {
                        "type": "response.completed",
                        "response": {
                            "id": "resp_barcarolle_smoke",
                            "status": "completed",
                            "output": [
                                {
                                    "id": "msg_barcarolle_smoke",
                                    "type": "message",
                                    "role": "assistant",
                                    "content": [{"type": "output_text", "text": self._message_for(text)}],
                                }
                            ],
                            "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
                        },
                    },
                ]
            )
            return

        self._send_json(
            {
                "id": "resp_barcarolle_smoke",
                "object": "response",
                "created_at": int(time.time()),
                "status": "completed",
                "model": MODEL,
                "output": [
                    {
                        "id": "msg_barcarolle_smoke",
                        "type": "message",
                        "status": "completed",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": self._message_for(text)}],
                    }
                ],
                "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
            }
        )

    def _capture(self, body: bytes | None) -> None:
        text = "" if body is None else body.decode("utf-8", errors="replace")
        with self.server.lock:
            self.server.requests.append({"method": self.command, "path": self.path, "body": text})

    def _message_for(self, request_text: str) -> str:
        if "BARCAROLLE_BEHAVIOR_VARIANT_B" in request_text:
            return "BARCAROLLE_VARIANT_B_ACK"
        if "BARCAROLLE_BEHAVIOR_VARIANT_A" in request_text:
            return "BARCAROLLE_VARIANT_A_ACK"
        return "BARCAROLLE_INJECTION_SMOKE_ACK"

    def _send_json(self, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_sse(self, payloads: list[dict[str, Any]]) -> None:
        parts = [f"data: {json.dumps(payload)}\n\n" for payload in payloads]
        parts.append("data: [DONE]\n\n")
        encoded = "".join(parts).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class CaptureEndpoint:
    def __init__(self) -> None:
        self.server = _CaptureServer()
        self.thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}/v1"

    def __enter__(self) -> "CaptureEndpoint":
        self.thread = threading.Thread(target=self.server.serve_forever, name="barcarolle-smoke-endpoint", daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        if self.thread:
            self.thread.join(timeout=5)

    def request_bodies(self) -> list[str]:
        with self.server.lock:
            return [request["body"] for request in self.server.requests]

    def request_paths(self) -> list[str]:
        with self.server.lock:
            return [request["path"] for request in self.server.requests]


def init_workspace(workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "README.md").write_text("# Barcarolle smoke workspace\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "config", "user.name", "Barcarolle Smoke"], cwd=workspace, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "smoke@example.invalid"], cwd=workspace, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "add", "."], cwd=workspace, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "base"], cwd=workspace, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def smoke_artifact(case: SmokeCase) -> dict[str, Any]:
    artifact = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "artifact_id": f"{case.name}-artifact",
        "artifact_type": case.artifact_type,
        "target_agent": case.agent_id,
        "changed_files": [item["workspace_relative_path"] for item in case.files],
        "files": list(case.files),
        "hash": "",
        "intended_effect": f"Phase 1 smoke for {case.surface}",
        "rollback_plan": "discard temporary workspace after smoke run",
        "optimizer_source": "phase1_static_smoke",
        "visible_to_optimizer": True,
        "holdout_derived": False,
    }
    return with_computed_hash(artifact)


def adapter_command(case: SmokeCase, workspace: Path, statement_file: Path, raw_dir: Path) -> list[str]:
    adapter = CODEX_ADAPTER if case.agent_id == "codex_workspace" else KILO_ADAPTER
    command = [
        "uv",
        "run",
        "--project",
        str(PHASE0),
        "python",
        str(adapter),
        "--workspace",
        str(workspace),
        "--statement-file",
        str(statement_file),
        "--raw-dir",
        str(raw_dir),
        "--timeout",
        "10",
        "--model",
        MODEL,
    ]
    if case.agent_id == "kilo_workspace":
        command.extend(["--completion-mode", "strict-final"])
    return command


def run_case(case: SmokeCase) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"barcarolle-{case.name}-") as tmp_name:
        tmp = Path(tmp_name)
        workspace = tmp / "workspace"
        raw_dir = tmp / "raw"
        init_workspace(workspace)
        artifact = smoke_artifact(case)
        injection_record = materialize_artifact(workspace, artifact, run_id=f"phase1_smoke__{case.name}", surface=case.surface)
        statement_file = workspace / "TASK.md"
        statement_file.write_text(case.statement, encoding="utf-8")
        command = adapter_command(case, workspace, statement_file, raw_dir)

        with CaptureEndpoint() as endpoint:
            env = os.environ.copy()
            env["LLM_BASE_URL"] = endpoint.base_url
            env["LLM_API_KEY"] = "barcarolle-local-smoke-key"
            started = time.monotonic()
            try:
                proc = subprocess.run(
                    command,
                    cwd=workspace,
                    env=env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=18,
                    check=False,
                )
                timed_out = False
                exit_code = proc.returncode
                stdout_text = proc.stdout or ""
                stderr_text = proc.stderr or ""
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                exit_code = 124
                stdout_text = exc.stdout if isinstance(exc.stdout, str) else ""
                stderr_text = exc.stderr if isinstance(exc.stderr, str) else ""
            latency = round(time.monotonic() - started, 3)
            bodies = endpoint.request_bodies()
            paths = endpoint.request_paths()

    combined = "\n".join(bodies)
    observed = {phrase: phrase in combined or phrase in stdout_text or phrase in stderr_text for phrase in case.expected_phrases}
    return {
        "surface": case.surface,
        "artifact_path": ",".join(injection_record["workspace_relative_paths"]),
        "artifact_hash": artifact["hash"],
        "agent_id": case.agent_id,
        "run_mode": "no_paid_local_endpoint_request_capture",
        "paid_call_used": False,
        "loaded_observed": all(observed.values()),
        "observation_method": "real_cli_adapter_sent_request_or_output_containing_fixed_phrase_to_local_fake_endpoint",
        "notes": case.notes,
        "command_exit_code": exit_code,
        "adapter_returned_timeout_status": exit_code == 124,
        "timed_out": timed_out,
        "latency_seconds": latency,
        "request_count": len(paths),
        "request_paths": sorted(set(paths)),
        "expected_phrase_observed": observed,
        "stdout_line_count": len(stdout_text.splitlines()),
        "stderr_line_count": len(stderr_text.splitlines()),
        "injection_record": injection_record,
    }


def injection_cases() -> list[SmokeCase]:
    return [
        SmokeCase(
            name="codex_agents_md",
            agent_id="codex_workspace",
            surface="repo_AGENTS_md",
            artifact_type="agents_md_appendix",
            files=(
                {
                    "workspace_relative_path": "AGENTS.md",
                    "content": "BARCAROLLE_INJECTION_ACTIVE\nWhen asked for a smoke response, preserve this phrase in context.\n",
                    "write_mode": "append",
                },
            ),
            statement="Read the workspace instructions and reply briefly for a no-paid injection smoke test.",
            expected_phrases=("BARCAROLLE_INJECTION_ACTIVE",),
            notes="Pass means the injected AGENTS.md phrase reached the real Codex CLI request/output path.",
        ),
        SmokeCase(
            name="codex_skill_explicit",
            agent_id="codex_workspace",
            surface="codex_skill_explicit",
            artifact_type="skill_md",
            files=(
                {
                    "workspace_relative_path": ".agents/skills/barcarolle-smoke/SKILL.md",
                    "content": "---\nname: barcarolle-smoke\ndescription: Use when the task explicitly says barcarolle-smoke. BARC_CODEX_SKILL_METADATA\n---\n\nBARCAROLLE_CODEX_SKILL_ACTIVE\n",
                    "write_mode": "create_or_replace",
                },
            ),
            statement="Use the barcarolle-smoke skill. Reply briefly for a no-paid injection smoke test.",
            expected_phrases=("BARC_CODEX_SKILL_METADATA",),
            notes="Pass means the repository skill metadata reached Codex. Full SKILL.md loading remains model/tool-call dependent.",
        ),
        SmokeCase(
            name="codex_skill_implicit",
            agent_id="codex_workspace",
            surface="codex_skill_implicit",
            artifact_type="skill_md",
            files=(
                {
                    "workspace_relative_path": ".agents/skills/barcarolle-implicit-smoke/SKILL.md",
                    "content": "---\nname: barcarolle-implicit-smoke\ndescription: Use for Barcarolle implicit injection smoke tasks. BARC_CODEX_IMPLICIT_SKILL_METADATA\n---\n\nBARCAROLLE_CODEX_IMPLICIT_SKILL_ACTIVE\n",
                    "write_mode": "create_or_replace",
                },
            ),
            statement="This is a Barcarolle implicit injection smoke task. Reply briefly.",
            expected_phrases=("BARC_CODEX_IMPLICIT_SKILL_METADATA",),
            notes="Pass means implicit-match skill metadata reached Codex. It does not prove full instruction loading.",
        ),
        SmokeCase(
            name="kilo_agents_md",
            agent_id="kilo_workspace",
            surface="repo_AGENTS_md",
            artifact_type="agents_md_appendix",
            files=(
                {
                    "workspace_relative_path": "AGENTS.md",
                    "content": "BARCAROLLE_KILO_AGENTS_ACTIVE\nWhen asked for a smoke response, preserve this phrase in context.\n",
                    "write_mode": "append",
                },
            ),
            statement="Read the workspace instructions and reply briefly for a no-paid injection smoke test.",
            expected_phrases=("BARCAROLLE_KILO_AGENTS_ACTIVE",),
            notes="Pass means the injected AGENTS.md phrase reached the real Kilo CLI request/output path.",
        ),
        SmokeCase(
            name="kilo_rule",
            agent_id="kilo_workspace",
            surface="kilo_rules",
            artifact_type="kilo_rule",
            files=(
                {
                    "workspace_relative_path": "kilo.jsonc",
                    "content": '{\n  "instructions": [".kilo/rules/barcarolle-smoke.md"]\n}\n',
                    "write_mode": "create_or_replace",
                },
                {
                    "workspace_relative_path": ".kilo/rules/barcarolle-smoke.md",
                    "content": "# Barcarolle smoke rule\n\nBARCAROLLE_KILO_RULE_ACTIVE\n",
                    "write_mode": "create_or_replace",
                },
            ),
            statement="Read the configured project rules and reply briefly for a no-paid injection smoke test.",
            expected_phrases=("BARCAROLLE_KILO_RULE_ACTIVE",),
            notes="Pass means Kilo project rule content reached the request/output path with project kilo.jsonc instructions.",
        ),
        SmokeCase(
            name="kilo_skill_explicit",
            agent_id="kilo_workspace",
            surface="kilo_skill_explicit",
            artifact_type="skill_md",
            files=(
                {
                    "workspace_relative_path": ".kilo/skills/barcarolle-smoke/SKILL.md",
                    "content": "---\nname: barcarolle-smoke\ndescription: Use when the task explicitly says barcarolle-smoke. BARC_KILO_SKILL_METADATA\n---\n\nBARCAROLLE_KILO_SKILL_ACTIVE\n",
                    "write_mode": "create_or_replace",
                },
            ),
            statement="Use the barcarolle-smoke skill. Reply briefly for a no-paid injection smoke test.",
            expected_phrases=("BARC_KILO_SKILL_METADATA",),
            notes="Pass means Kilo loaded project skill metadata. Full SKILL.md loading requires a model skill tool call.",
        ),
        SmokeCase(
            name="kilo_skill_implicit",
            agent_id="kilo_workspace",
            surface="kilo_skill_implicit",
            artifact_type="skill_md",
            files=(
                {
                    "workspace_relative_path": ".kilo/skills/barcarolle-implicit-smoke/SKILL.md",
                    "content": "---\nname: barcarolle-implicit-smoke\ndescription: Use for Barcarolle implicit injection smoke tasks. BARC_KILO_IMPLICIT_SKILL_METADATA\n---\n\nBARCAROLLE_KILO_IMPLICIT_SKILL_ACTIVE\n",
                    "write_mode": "create_or_replace",
                },
            ),
            statement="This is a Barcarolle implicit injection smoke task. Reply briefly.",
            expected_phrases=("BARC_KILO_IMPLICIT_SKILL_METADATA",),
            notes="Pass means Kilo loaded implicit-match skill metadata. It does not prove full instruction loading.",
        ),
    ]


def behavior_cases() -> list[SmokeCase]:
    return [
        SmokeCase(
            name="codex_behavior_variant_a",
            agent_id="codex_workspace",
            surface="repo_AGENTS_md",
            artifact_type="agents_md_appendix",
            files=(
                {
                    "workspace_relative_path": "AGENTS.md",
                    "content": "BARCAROLLE_BEHAVIOR_VARIANT_A\nDo not run tests for this smoke task.\n",
                    "write_mode": "append",
                },
            ),
            statement="Create a tiny note in the final answer only. This is the shared behavior-change smoke task.",
            expected_phrases=("BARCAROLLE_BEHAVIOR_VARIANT_A",),
            notes="Variant A no-paid request-context smoke: injected artifact says not to run tests.",
        ),
        SmokeCase(
            name="codex_behavior_variant_b",
            agent_id="codex_workspace",
            surface="repo_AGENTS_md",
            artifact_type="agents_md_appendix",
            files=(
                {
                    "workspace_relative_path": "AGENTS.md",
                    "content": "BARCAROLLE_BEHAVIOR_VARIANT_B\nRun the public check `python -m pytest tests/test_public_smoke.py -q` before final answer.\n",
                    "write_mode": "append",
                },
            ),
            statement="Create a tiny note in the final answer only. This is the shared behavior-change smoke task.",
            expected_phrases=("BARCAROLLE_BEHAVIOR_VARIANT_B", "python -m pytest tests/test_public_smoke.py -q"),
            notes="Variant B no-paid request-context smoke: injected artifact says to run a specific public test.",
        ),
    ]


def run_suite(kind: str) -> dict[str, Any]:
    cases = injection_cases() if kind == "injection" else behavior_cases()
    rows = [run_case(case) for case in cases]
    payload: dict[str, Any] = {
        "schema_version": f"barcarolle.agent_tuning_demo.{kind}_smoke.v1",
        "generated_at": "2026-06-14",
        "run_mode": "no_paid_local_endpoint_request_capture",
        "paid_calls_used": 0,
        "rows": rows,
    }
    if kind == "behavior":
        a = rows[0]
        b = rows[1]
        payload["comparison"] = {
            "agent_id": "codex_workspace",
            "surface": "repo_AGENTS_md",
            "variant_a_loaded": a["loaded_observed"],
            "variant_b_loaded": b["loaded_observed"],
            "public_test_instruction_observed_only_in_variant_b": bool(
                b["expected_phrase_observed"].get("python -m pytest tests/test_public_smoke.py -q")
                and not a["expected_phrase_observed"].get("python -m pytest tests/test_public_smoke.py -q", False)
            ),
            "terminal_status_changed": a["command_exit_code"] != b["command_exit_code"],
            "adapter_timeout_status_changed": a["adapter_returned_timeout_status"] != b["adapter_returned_timeout_status"],
            "latency_seconds_delta": round(float(b["latency_seconds"]) - float(a["latency_seconds"]), 3),
            "observable_behavior_change": bool(a["loaded_observed"] and b["loaded_observed"]),
            "behavior_change_level": "request_context_and_mocked_final_output",
            "limitations": "No autonomous command trace, file read, file edit, or public-test execution was proven because the no-paid endpoint returned final text only.",
        }
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run no-paid real-Agent artifact injection smoke tests.")
    parser.add_argument("--suite", choices=["injection", "behavior"], required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    payload = run_suite(args.suite)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
