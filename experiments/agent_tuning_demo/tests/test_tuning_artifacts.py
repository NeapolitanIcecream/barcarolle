from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import tuning_artifacts as artifacts  # noqa: E402


def sample_artifact() -> dict[str, object]:
    artifact: dict[str, object] = {
        "schema_version": artifacts.ARTIFACT_SCHEMA_VERSION,
        "artifact_id": "codex-agents-smoke-v1",
        "artifact_type": "agents_md_appendix",
        "target_agent": "codex_workspace",
        "changed_files": ["AGENTS.md"],
        "files": [
            {
                "workspace_relative_path": "AGENTS.md",
                "content": "BARCAROLLE_INJECTION_ACTIVE\n",
                "write_mode": "append",
            }
        ],
        "hash": "",
        "intended_effect": "prove Codex can receive repo instructions",
        "rollback_plan": "discard the solver workspace after the run",
        "optimizer_source": "phase1_static_smoke",
        "visible_to_optimizer": True,
        "holdout_derived": False,
    }
    return artifacts.with_computed_hash(artifact)


def test_with_computed_hash_is_deterministic() -> None:
    left = sample_artifact()
    right = sample_artifact()

    assert left["hash"] == right["hash"]
    assert str(left["hash"]).startswith("sha256:")
    artifacts.validate_artifact(left)


def test_materialize_artifact_appends_and_returns_sanitized_record(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")
    artifact = sample_artifact()

    record = artifacts.materialize_artifact(
        tmp_path,
        artifact,
        run_id="phase1__codex__agents",
        surface="repo_AGENTS_md",
        injected_at="2026-06-14T00:00:00+00:00",
    )

    assert "BARCAROLLE_INJECTION_ACTIVE" in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert record == {
        "schema_version": artifacts.INJECTION_RECORD_SCHEMA_VERSION,
        "run_id": "phase1__codex__agents",
        "artifact_id": "codex-agents-smoke-v1",
        "artifact_hash": artifact["hash"],
        "target_agent": "codex_workspace",
        "surface": "repo_AGENTS_md",
        "workspace_relative_paths": ["AGENTS.md"],
        "injected_at": "2026-06-14T00:00:00+00:00",
        "cleanup_policy": "workspace_discarded_after_run",
    }
    artifacts.validate_injection_record(record)


def test_rejects_unsafe_workspace_paths(tmp_path: Path) -> None:
    artifact = sample_artifact()
    artifact["changed_files"] = ["../AGENTS.md"]
    artifact["files"] = [
        {
            "workspace_relative_path": "../AGENTS.md",
            "content": "bad",
        }
    ]
    artifact = artifacts.with_computed_hash(artifact)

    with pytest.raises(artifacts.ArtifactValidationError, match="unsafe segment"):
        artifacts.materialize_artifact(tmp_path, artifact, run_id="bad", surface="repo_AGENTS_md")


def test_rejects_holdout_derived_artifacts_by_default() -> None:
    artifact = sample_artifact()
    artifact["holdout_derived"] = True
    artifact = artifacts.with_computed_hash(artifact)

    with pytest.raises(artifacts.ArtifactValidationError, match="holdout-derived"):
        artifacts.validate_artifact(artifact)


def test_schema_files_are_json_objects() -> None:
    for rel_path in [
        "experiments/agent_tuning_demo/schemas/tuning_artifact.schema.json",
        "experiments/agent_tuning_demo/schemas/artifact_injection_record.schema.json",
    ]:
        payload = json.loads((ROOT / rel_path).read_text(encoding="utf-8"))
        assert payload["type"] == "object"
        assert payload["required"]
