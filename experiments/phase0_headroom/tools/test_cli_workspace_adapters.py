from __future__ import annotations

from pathlib import Path

import codex_workspace_adapter
import kilo_workspace_adapter
import workspace_acut_run


def test_codex_command_uses_custom_responses_provider_without_secret() -> None:
    command = codex_workspace_adapter.build_codex_command(
        workspace=Path("/tmp/workspace"),
        statement_file=Path("/tmp/workspace/.barcarolle/statement.md"),
        base_url="https://endpoint.example/v1",
        timeout_seconds=900,
    )

    rendered = " ".join(command)

    assert command[:2] == ["codex", "exec"]
    assert "--ignore-user-config" in command
    assert "--ephemeral" in command
    assert "--json" in command
    assert "--cd" in command
    assert "/tmp/workspace" in command
    assert 'model_provider="llm_endpoint"' in command
    assert 'model_providers.llm_endpoint.env_key="LLM_API_KEY"' in command
    assert "supports_websockets=false" in rendered
    assert "LLM_API_KEY=" not in rendered


def test_kilo_config_uses_env_key_and_openai_compatible_model(tmp_path: Path) -> None:
    config_path = kilo_workspace_adapter.write_kilo_config(tmp_path, "https://endpoint.example/v1")
    text = config_path.read_text(encoding="utf-8")

    assert config_path == tmp_path / "kilo" / "kilo.jsonc"
    assert '"model": "openai-compatible/gpt-5.4-mini"' in text
    assert '"apiKey": "{env:LLM_API_KEY}"' in text
    assert '"baseURL": "https://endpoint.example/v1"' in text
    assert "SECRET" not in text


def test_kilo_command_delivers_statement_file_and_workspace() -> None:
    command = kilo_workspace_adapter.build_kilo_command(
        workspace=Path("/tmp/workspace"),
        statement_file=Path("/tmp/workspace/.barcarolle/statement.md"),
        timeout_seconds=900,
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
    assert "openai-compatible/gpt-5.4-mini" in command
    assert "LLM_API_KEY=" not in rendered


def test_kilo_strict_final_mode_tells_cli_to_finalize_and_exit() -> None:
    command = kilo_workspace_adapter.build_kilo_command(
        workspace=Path("/tmp/workspace"),
        statement_file=Path("/tmp/workspace/.barcarolle/statement.md"),
        timeout_seconds=300,
        completion_mode="strict-final",
    )

    prompt = command[2]

    assert "provide one brief final answer and terminate" in prompt
    assert "Do not ask follow-up questions" in prompt
    assert "Do not show suggestions after editing" in prompt
    assert "--auto" in command
    assert "LLM_API_KEY=" not in " ".join(command)


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
