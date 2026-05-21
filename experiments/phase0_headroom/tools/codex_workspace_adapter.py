from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


MODEL = "gpt-5.4-mini"
PROVIDER = "llm_endpoint"


def base_url_with_v1(raw: str) -> str:
    base = raw.rstrip("/")
    return base if base.endswith("/v1") else f"{base}/v1"


def build_prompt(statement_file: Path) -> str:
    return "\n".join(
        [
            f"Read the task statement at {statement_file}.",
            "Inspect the repository in the current workspace.",
            "Modify only implementation files needed for the requested behavior.",
            "Do not edit tests, hidden verifier files, generated caches, or files outside the workspace.",
            "Leave the final answer brief. The evaluation harness will capture git diff after you finish.",
        ]
    )


def build_codex_command(workspace: Path, statement_file: Path, base_url: str, timeout_seconds: int) -> list[str]:
    del timeout_seconds
    return [
        "codex",
        "exec",
        "--ignore-user-config",
        "--ephemeral",
        "--json",
        "--cd",
        str(workspace),
        "--sandbox",
        "workspace-write",
        "--model",
        MODEL,
        "-c",
        f'model_provider="{PROVIDER}"',
        "-c",
        f'model_providers.{PROVIDER}.name="LLM endpoint"',
        "-c",
        f'model_providers.{PROVIDER}.base_url="{base_url}"',
        "-c",
        f'model_providers.{PROVIDER}.env_key="LLM_API_KEY"',
        "-c",
        f'model_providers.{PROVIDER}.wire_api="responses"',
        "-c",
        f"model_providers.{PROVIDER}.supports_websockets=false",
        "-c",
        'approval_policy="never"',
        build_prompt(statement_file),
    ]


def run_child(command: list[str], workspace: Path, env: dict[str, str], timeout_seconds: int) -> int:
    start = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=workspace,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        sys.stdout.write(exc.stdout or "")
        sys.stderr.write(exc.stderr or "")
        sys.stderr.write(f"\nCodex workspace adapter timed out after {timeout_seconds}s\n")
        return 124
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    sys.stderr.write(f"\nCodex workspace adapter duration_seconds={time.monotonic() - start:.3f}\n")
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Codex CLI as a workspace ACUT adapter.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--statement-file", required=True)
    parser.add_argument("--raw-dir", default=None)
    parser.add_argument("--timeout", type=int, default=900)
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

    with tempfile.TemporaryDirectory(prefix="codex-home-", dir=temp_parent) as codex_home:
        env = os.environ.copy()
        env["CODEX_HOME"] = codex_home
        env["LLM_API_KEY"] = key
        command = build_codex_command(workspace, statement_file, base_url_with_v1(base), args.timeout)
        return run_child(command, workspace, env, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
