from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("examples/harnesses/codex-cli/extract-usage.py")
HARNESS = Path("examples/harnesses/codex-cli/run-agent.zsh").resolve()


def test_codex_usage_helper_normalizes_nested_usage_event() -> None:
    payload = "\n".join(
        [
            json.dumps({"type": "message", "text": "done"}),
            json.dumps({"type": "response", "response": {"usage": {"input_tokens": 12, "output_tokens": 3}}}),
        ]
    )

    completed = _run_helper(payload)

    assert json.loads(completed.stdout) == {"input_tokens": 12, "output_tokens": 3, "total_tokens": 15}
    assert completed.stderr == ""


def test_codex_usage_helper_accepts_prompt_and_completion_token_names() -> None:
    payload = json.dumps({"usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12}})

    completed = _run_helper(payload)

    assert json.loads(completed.stdout) == {"input_tokens": 5, "output_tokens": 7, "total_tokens": 12}


def test_codex_usage_helper_returns_empty_mapping_when_usage_is_absent() -> None:
    completed = _run_helper(json.dumps({"type": "agent_message", "message": "no token event"}))

    assert json.loads(completed.stdout) == {}
    assert "No usage event found" in completed.stderr


def test_codex_harness_writes_usage_for_workspace_runner(tmp_path: Path) -> None:
    reserved = tmp_path / ".barcarolle"
    reserved.mkdir()
    (reserved / "TASK.md").write_text("Fix the parser.\n", encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_codex = fake_bin / "codex"
    fake_codex.write_text(
        "#!/bin/sh\n"
        "cat >/dev/null\n"
        "printf '%s\\n' '{\"type\":\"response\",\"usage\":{\"input_tokens\":12,\"output_tokens\":3}}'\n",
        encoding="utf-8",
    )
    fake_codex.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "LLM_BASE_URL": "https://example.invalid/v1",
        "LLM_API_KEY": "test-only",
        "BARCAROLLE_CODEX_HOME": str(tmp_path / "codex-home"),
    }

    completed = subprocess.run(
        [str(HARNESS)],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert json.loads(completed.stdout) == {
        "type": "response",
        "usage": {"input_tokens": 12, "output_tokens": 3},
    }
    assert json.loads((reserved / "usage.json").read_text(encoding="utf-8")) == {
        "input_tokens": 12,
        "output_tokens": 3,
        "total_tokens": 15,
    }
    assert not (reserved / "codex-events.jsonl").exists()


def _run_helper(stdin: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
