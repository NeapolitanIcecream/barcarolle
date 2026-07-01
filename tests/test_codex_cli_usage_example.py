from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("examples/harnesses/codex-cli/extract-usage.py")


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


def _run_helper(stdin: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
