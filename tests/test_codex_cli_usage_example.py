from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("examples/harnesses/codex-cli/extract-usage.py")
HARNESS = Path("examples/harnesses/codex-cli/run-agent.zsh").resolve()


def test_codex_usage_helper_reads_codex_turn_completed_usage() -> None:
    payload = "\n".join(
        [
            json.dumps({"type": "message", "text": "done"}),
            json.dumps(
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 12,
                        "cached_input_tokens": 7,
                        "output_tokens": 3,
                    },
                }
            ),
        ]
    )

    completed = _run_helper(payload)

    assert json.loads(completed.stdout) == {
        "cached_input_tokens": 7,
        "input_tokens": 12,
        "output_tokens": 3,
        "uncached_input_tokens": 5,
    }
    assert completed.stderr == ""


def test_codex_usage_helper_ignores_usage_aliases_and_unrelated_nested_objects() -> None:
    payload = "\n".join(
        [
            json.dumps({"usage": {"prompt_tokens": 5, "completion_tokens": 7}}),
            json.dumps({"type": "response", "response": {"usage": {"input_tokens": 12}}}),
        ]
    )

    completed = _run_helper(payload)

    assert json.loads(completed.stdout) == {}


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
        "printf '%s\\n' \"$@\" > .barcarolle/test-codex-argv.txt\n"
        "printf 'CODEX_HOME=%s\\nOPENAI_API_KEY=%s\\nOPENAI_BASE_URL=%s\\nOPENAI_MODEL=%s\\nLLM_API_KEY=%s\\nLLM_BASE_URL=%s\\n' \"${CODEX_HOME-unset}\" \"${OPENAI_API_KEY-unset}\" \"${OPENAI_BASE_URL-unset}\" \"${OPENAI_MODEL-unset}\" \"${LLM_API_KEY-unset}\" \"${LLM_BASE_URL-unset}\" > .barcarolle/test-codex-env.txt\n"
        "cat >/dev/null\n"
        "printf '%s\\n' '{\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":12,\"cached_input_tokens\":7,\"output_tokens\":3}}'\n",
        encoding="utf-8",
    )
    fake_codex.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "OPENAI_BASE_URL": "https://example.invalid/v1",
        "OPENAI_API_KEY": "test-only",
        "OPENAI_MODEL": "ambient-model",
        "LLM_BASE_URL": "https://ambient.invalid/v1",
        "LLM_API_KEY": "ambient-only",
        "BARCAROLLE_CODEX_MODEL": "test-model",
        "BARCAROLLE_CODEX_REASONING_EFFORT": "low",
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
        "type": "turn.completed",
        "usage": {"cached_input_tokens": 7, "input_tokens": 12, "output_tokens": 3},
    }
    assert json.loads((reserved / "usage.json").read_text(encoding="utf-8")) == {
        "cached_input_tokens": 7,
        "input_tokens": 12,
        "output_tokens": 3,
        "uncached_input_tokens": 5,
    }
    assert not (reserved / "codex-events.jsonl").exists()
    argv = (reserved / "test-codex-argv.txt").read_text(encoding="utf-8")
    assert 'model_provider="barcarolle_openai"' in argv
    assert 'model_providers.barcarolle_openai.base_url="https://example.invalid/v1"' in argv
    assert 'model_providers.barcarolle_openai.env_key="OPENAI_API_KEY"' in argv
    assert 'model_providers.barcarolle_openai.wire_api="responses"' in argv
    assert "model_providers.barcarolle_openai.request_max_retries=0" in argv
    assert "model_providers.barcarolle_openai.stream_max_retries=0" in argv
    assert 'shell_environment_policy.exclude=["OPENAI_API_KEY","OPENAI_BASE_URL"]' in argv
    assert 'model_reasoning_effort="low"' in argv
    argv_lines = argv.splitlines()
    assert "--ignore-user-config" in argv_lines
    assert "--strict-config" in argv_lines
    assert "--ephemeral" in argv_lines
    assert argv_lines[argv_lines.index("--disable") + 1] == "plugins"
    assert argv_lines[argv_lines.index("--disable", argv_lines.index("--disable") + 1) + 1] == "multi_agent"
    assert argv_lines[argv_lines.index("--model") + 1] == "test-model"
    assert "ambient-model" not in argv
    assert "test-only" not in argv
    assert (reserved / "test-codex-env.txt").read_text(encoding="utf-8") == (
        f"CODEX_HOME={tmp_path / 'codex-home'}\n"
        "OPENAI_API_KEY=test-only\n"
        "OPENAI_BASE_URL=https://example.invalid/v1\n"
        "OPENAI_MODEL=unset\n"
        "LLM_API_KEY=unset\n"
        "LLM_BASE_URL=unset\n"
    )


def test_codex_harness_requires_authorized_openai_environment(tmp_path: Path) -> None:
    reserved = tmp_path / ".barcarolle"
    reserved.mkdir()
    (reserved / "TASK.md").write_text("Fix the parser.\n", encoding="utf-8")
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"OPENAI_API_KEY", "OPENAI_BASE_URL", "LLM_API_KEY", "LLM_BASE_URL"}
    }
    env["HOME"] = str(tmp_path / "empty-home")
    env["BARCAROLLE_CODEX_HOME"] = str(tmp_path / "codex-home")

    completed = subprocess.run(
        [str(HARNESS)],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 65
    assert "OPENAI_BASE_URL is required" in completed.stderr


def test_codex_harness_restores_isolated_home_after_sourcing_zshrc(tmp_path: Path) -> None:
    reserved = tmp_path / ".barcarolle"
    reserved.mkdir()
    (reserved / "TASK.md").write_text("Fix the parser.\n", encoding="utf-8")
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / ".zshrc").write_text(
        "export OPENAI_BASE_URL=https://example.invalid/v1\n"
        "export OPENAI_API_KEY=test-only\n"
        "export CODEX_HOME=/tmp/ambient-codex-home\n",
        encoding="utf-8",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_codex = fake_bin / "codex"
    fake_codex.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$CODEX_HOME\" > .barcarolle/test-codex-home.txt\n"
        "cat >/dev/null\n"
        "printf '%s\\n' '{\"type\":\"turn.completed\",\"usage\":{}}'\n",
        encoding="utf-8",
    )
    fake_codex.chmod(0o755)
    isolated_home = tmp_path / "isolated-codex-home"
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"OPENAI_API_KEY", "OPENAI_BASE_URL"}
    }
    env.update(
        {
            "HOME": str(fake_home),
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "BARCAROLLE_CODEX_HOME": str(isolated_home),
        }
    )

    subprocess.run(
        [str(HARNESS)],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert (reserved / "test-codex-home.txt").read_text(encoding="utf-8") == (
        f"{isolated_home}\n"
    )


def test_codex_harness_rejects_unknown_reasoning_effort(tmp_path: Path) -> None:
    reserved = tmp_path / ".barcarolle"
    reserved.mkdir()
    (reserved / "TASK.md").write_text("Fix the parser.\n", encoding="utf-8")
    env = {
        **os.environ,
        "OPENAI_BASE_URL": "https://example.invalid/v1",
        "OPENAI_API_KEY": "test-only",
        "BARCAROLLE_CODEX_HOME": str(tmp_path / "codex-home"),
        "BARCAROLLE_CODEX_REASONING_EFFORT": "maximum",
    }

    completed = subprocess.run(
        [str(HARNESS)],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 64
    assert "must be none, low, medium, high, or xhigh" in completed.stderr


def _run_helper(stdin: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
