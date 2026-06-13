from __future__ import annotations

from pathlib import Path

import pytest

import codex_workspace_adapter
import kilo_workspace_adapter
import llm_endpoint_proxy
import workspace_acut_run


def test_codex_command_uses_custom_responses_provider_without_secret() -> None:
    command = codex_workspace_adapter.build_codex_command(
        workspace=Path("/tmp/workspace"),
        statement_file=Path("/tmp/workspace/.barcarolle/statement.md"),
        base_url="https://endpoint.example/v1",
        timeout_seconds=900,
        model="gpt-5.4",
    )

    rendered = " ".join(command)

    assert command[:2] == ["codex", "exec"]
    assert "--ignore-user-config" in command
    assert "--ephemeral" in command
    assert "--json" in command
    assert "--cd" in command
    assert "/tmp/workspace" in command
    assert 'model_provider="llm_endpoint"' in command
    assert "--model" in command
    assert "gpt-5.4" in command
    assert f'model_providers.llm_endpoint.env_key="{llm_endpoint_proxy.DUMMY_API_KEY_ENV}"' in command
    assert "supports_websockets=false" in rendered
    assert "LLM_API_KEY=" not in rendered


def test_kilo_config_uses_env_key_and_openai_compatible_model(tmp_path: Path) -> None:
    config_path = kilo_workspace_adapter.write_kilo_config(tmp_path, "https://endpoint.example/v1", model="claude-sonnet-4-6")
    text = config_path.read_text(encoding="utf-8")

    assert config_path == tmp_path / "kilo" / "kilo.jsonc"
    assert '"model": "openai-compatible/claude-sonnet-4-6"' in text
    assert f'"apiKey": "{{env:{llm_endpoint_proxy.DUMMY_API_KEY_ENV}}}"' in text
    assert '"baseURL": "https://endpoint.example/v1"' in text
    assert '"timeout": 3600000' in text
    assert "SECRET" not in text
    assert "LLM_API_KEY" not in text


def test_workspace_adapter_defaults_match_doubled_timeout_policy() -> None:
    assert codex_workspace_adapter.DEFAULT_TIMEOUT_SECONDS == 1800
    assert kilo_workspace_adapter.DEFAULT_TIMEOUT_SECONDS == 1800
    assert kilo_workspace_adapter.DEFAULT_UPSTREAM_TIMEOUT_SECONDS == 3600
    assert llm_endpoint_proxy.DEFAULT_UPSTREAM_TIMEOUT_SECONDS == 3600


def test_kilo_command_delivers_statement_file_and_workspace() -> None:
    command = kilo_workspace_adapter.build_kilo_command(
        workspace=Path("/tmp/workspace"),
        statement_file=Path("/tmp/workspace/.barcarolle/statement.md"),
        timeout_seconds=900,
        model="gpt-5.4",
    )

    rendered = " ".join(command)
    prompt_index = 2
    file_option_index = command.index("--file")

    assert command[:2] == ["kilo", "run"]
    assert command[prompt_index].startswith("Read the attached task statement.")
    assert prompt_index < file_option_index
    assert "--pure" in command
    assert "--auto" in command
    assert "--format" in command
    assert "--dir" in command
    assert "/tmp/workspace" in command
    assert "--file" in command
    assert "/tmp/workspace/.barcarolle/statement.md" in command
    assert command.count("--model") == 1
    assert "openai-compatible/gpt-5.4" in command
    assert "LLM_API_KEY=" not in rendered


def test_kilo_strict_final_mode_tells_cli_to_finalize_and_exit() -> None:
    command = kilo_workspace_adapter.build_kilo_command(
        workspace=Path("/tmp/workspace"),
        statement_file=Path("/tmp/workspace/.barcarolle/statement.md"),
        timeout_seconds=300,
        completion_mode="strict-final",
        model="gpt-5.4-mini",
    )

    prompt = command[2]

    assert "provide one brief final answer and terminate" in prompt
    assert "Do not ask follow-up questions" in prompt
    assert "Do not show suggestions after editing" in prompt
    assert "--auto" in command
    assert "LLM_API_KEY=" not in " ".join(command)


def test_sanitized_child_env_removes_endpoint_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "real-secret")
    monkeypatch.setenv("LLM_BASE_URL", "https://endpoint.example")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")
    monkeypatch.setenv("PATH", "/usr/bin")

    env = llm_endpoint_proxy.sanitized_child_env()

    assert env["PATH"] == "/usr/bin"
    assert env[llm_endpoint_proxy.DUMMY_API_KEY_ENV] == llm_endpoint_proxy.DUMMY_API_KEY_VALUE
    assert "LLM_API_KEY" not in env
    assert "LLM_BASE_URL" not in env
    assert "OPENAI_API_KEY" not in env


def test_proxy_rewrites_v1_paths_without_leaking_dummy_key() -> None:
    assert llm_endpoint_proxy._upstream_url("https://endpoint.example/v1", "/v1/models") == "https://endpoint.example/v1/models"
    assert llm_endpoint_proxy._upstream_url("https://endpoint.example/v1", "/v1/responses?x=1") == "https://endpoint.example/v1/responses?x=1"

    headers = llm_endpoint_proxy._forward_headers(
        [
            ("Authorization", "Bearer dummy"),
            ("Content-Type", "application/json"),
            ("Accept-Encoding", "gzip"),
        ],
        "real-secret",
    )

    assert headers["Authorization"] == "Bearer real-secret"
    assert headers["Content-Type"] == "application/json"
    assert "Accept-Encoding" not in headers


def test_merge_rows_by_run_id_replaces_existing_rows() -> None:
    merged = workspace_acut_run.merge_rows_by_run_id(
        [{"run_id": "a", "status": "old"}, {"run_id": "b", "status": "kept"}],
        [{"run_id": "a", "status": "new"}],
    )

    assert merged == [{"run_id": "a", "status": "new"}, {"run_id": "b", "status": "kept"}]


def test_existing_task_ids_for_adapter_selects_only_matching_adapter() -> None:
    task_ids = workspace_acut_run.existing_task_ids_for_adapter(
        [
            {"adapter_id": "codex_workspace", "task_id": "toolz__hist__002"},
            {"adapter_id": "kilo_workspace", "task_id": "toolz__hist__002"},
            {"adapter_id": "codex_workspace", "task_id": "click__rbench__001"},
        ],
        "codex_workspace",
    )

    assert task_ids == {"toolz__hist__002", "click__rbench__001"}
