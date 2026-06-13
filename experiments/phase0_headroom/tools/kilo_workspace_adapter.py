from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from llm_endpoint_proxy import DUMMY_API_KEY_ENV, LLMEndpointProxy, sanitized_child_env

MODEL = "gpt-5.4-mini"
PROVIDER = "openai-compatible"


def base_url_with_v1(raw: str) -> str:
    base = raw.rstrip("/")
    return base if base.endswith("/v1") else f"{base}/v1"


def write_kilo_config(config_root: Path, base_url: str, model: str = MODEL) -> Path:
    kilo_dir = config_root / "kilo"
    kilo_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "$schema": "https://app.kilo.ai/config.json",
        "model": f"{PROVIDER}/{model}",
        "enabled_providers": [PROVIDER],
        "permission": {"*": "allow"},
        "provider": {
            PROVIDER: {
                "options": {
                    "apiKey": f"{{env:{DUMMY_API_KEY_ENV}}}",
                    "baseURL": base_url,
                    "timeout": 60000,
                },
                "models": {
                    model: {
                        "name": f"{model} Workspace Agent",
                        "id": model,
                        "tool_call": True,
                        "reasoning": True,
                        "temperature": False,
                        "limit": {
                            "context": 400000,
                            "output": 4096,
                        },
                    }
                },
            }
        },
    }
    path = kilo_dir / "kilo.jsonc"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def build_prompt(completion_mode: str = "current") -> str:
    lines = [
        "Read the attached task statement.",
        "Inspect the repository in the current workspace.",
        "Modify only implementation files needed for the requested behavior.",
        "Do not edit tests, hidden verifier files, generated caches, or files outside the workspace.",
    ]
    if completion_mode == "strict-final":
        lines.extend(
            [
                "Do not ask follow-up questions.",
                "Do not show suggestions after editing.",
                "After edits are complete, provide one brief final answer and terminate.",
            ]
        )
    else:
        lines.append("Leave the final answer brief. The evaluation harness will capture git diff after you finish.")
    return "\n".join(lines)


def build_kilo_command(workspace: Path, statement_file: Path, timeout_seconds: int, completion_mode: str = "current", model: str = MODEL) -> list[str]:
    del timeout_seconds
    return [
        "kilo",
        "run",
        build_prompt(completion_mode),
        "--pure",
        "--auto",
        "--format",
        "json",
        "--dir",
        str(workspace),
        "--file",
        str(statement_file),
        "--model",
        f"{PROVIDER}/{model}",
    ]


def run_child(command: list[str], workspace: Path, env: dict[str, str], timeout_seconds: int) -> int:
    def kill_process_tree(process: subprocess.Popen[str]) -> None:
        try:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return

    start = time.monotonic()
    try:
        process = subprocess.Popen(
            command,
            cwd=workspace,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name != "nt",
        )
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        kill_process_tree(process)
        stdout, stderr = process.communicate()
        sys.stdout.write(stdout or "")
        sys.stderr.write(stderr or "")
        sys.stderr.write(f"\nKilo workspace adapter timed out after {timeout_seconds}s\n")
        return 124
    sys.stdout.write(stdout or "")
    sys.stderr.write(stderr or "")
    sys.stderr.write(f"\nKilo workspace adapter duration_seconds={time.monotonic() - start:.3f}\n")
    return process.returncode or 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Kilo CLI as a workspace ACUT adapter.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--statement-file", required=True)
    parser.add_argument("--raw-dir", default=None)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--completion-mode", choices=["current", "strict-final"], default="current")
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()

    base = os.environ.get("LLM_BASE_URL")
    key = os.environ.get("LLM_API_KEY")
    if not base or not key:
        sys.stderr.write("LLM_BASE_URL and LLM_API_KEY are required\n")
        return 2

    workspace = Path(args.workspace).resolve()
    statement_file = Path(args.statement_file).resolve()
    temp_parent = Path(args.raw_dir).resolve() if args.raw_dir else None
    if temp_parent:
        temp_parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="kilo-home-", dir=temp_parent) as temp_root_name:
        temp_root = Path(temp_root_name)
        config_root = temp_root / "config"
        with LLMEndpointProxy(base, key) as proxy:
            write_kilo_config(config_root, proxy.base_url, model=args.model)
            env = sanitized_child_env(
                {
                    "HOME": str(temp_root / "home"),
                    "XDG_CONFIG_HOME": str(config_root),
                    "XDG_DATA_HOME": str(temp_root / "data"),
                    "XDG_CACHE_HOME": str(temp_root / "cache"),
                    "XDG_STATE_HOME": str(temp_root / "state"),
                }
            )
            command = build_kilo_command(workspace, statement_file, args.timeout, completion_mode=args.completion_mode, model=args.model)
            return run_child(command, workspace, env, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
