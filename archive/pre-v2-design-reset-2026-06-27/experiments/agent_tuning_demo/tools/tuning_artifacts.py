from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


ARTIFACT_SCHEMA_VERSION = "barcarolle.agent_tuning_demo.tuning_artifact.v1"
INJECTION_RECORD_SCHEMA_VERSION = "barcarolle.agent_tuning_demo.artifact_injection_record.v1"
ALLOWED_ARTIFACT_TYPES = {"agents_md_appendix", "skill_md", "kilo_rule", "policy_snippet"}
ALLOWED_TARGET_AGENTS = {"codex_workspace", "kilo_workspace", "any_workspace_agent"}
ALLOWED_WRITE_MODES = {"create_or_replace", "append"}
ALLOWED_CLEANUP_POLICIES = {"workspace_discarded_after_run", "delete_before_verifier_replay", "manual_local_only"}


class ArtifactValidationError(ValueError):
    """Raised when a tuning artifact or injection record violates Phase 1 boundaries."""


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ArtifactValidationError(f"{key} must be a non-empty string")
    return value


def _require_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ArtifactValidationError(f"{key} must be a boolean")
    return value


def safe_workspace_path(raw_path: str) -> PurePosixPath:
    if "\\" in raw_path:
        raise ArtifactValidationError(f"workspace path must use POSIX separators: {raw_path}")
    path = PurePosixPath(raw_path)
    if path.is_absolute() or not path.parts:
        raise ArtifactValidationError(f"workspace path must be relative: {raw_path}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ArtifactValidationError(f"workspace path contains unsafe segment: {raw_path}")
    return path


def _normalized_for_hash(artifact: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(artifact)
    normalized.pop("hash", None)
    normalized["changed_files"] = sorted(str(path) for path in normalized.get("changed_files", []))
    normalized["files"] = sorted(
        [
            {
                "content": str(item.get("content", "")),
                "workspace_relative_path": str(item.get("workspace_relative_path", "")),
                "write_mode": str(item.get("write_mode") or "create_or_replace"),
            }
            for item in normalized.get("files", [])
        ],
        key=lambda item: (item["workspace_relative_path"], item["write_mode"], item["content"]),
    )
    return normalized


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def artifact_hash(artifact: dict[str, Any]) -> str:
    digest = hashlib.sha256(canonical_json_bytes(_normalized_for_hash(artifact))).hexdigest()
    return f"sha256:{digest}"


def validate_artifact(artifact: dict[str, Any], *, allow_holdout_derived: bool = False) -> None:
    if artifact.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise ArtifactValidationError("unsupported artifact schema_version")

    _require_string(artifact, "artifact_id")
    artifact_type = _require_string(artifact, "artifact_type")
    if artifact_type not in ALLOWED_ARTIFACT_TYPES:
        raise ArtifactValidationError(f"unsupported artifact_type: {artifact_type}")

    target_agent = _require_string(artifact, "target_agent")
    if target_agent not in ALLOWED_TARGET_AGENTS:
        raise ArtifactValidationError(f"unsupported target_agent: {target_agent}")

    changed_files = artifact.get("changed_files")
    if not isinstance(changed_files, list) or not changed_files:
        raise ArtifactValidationError("changed_files must be a non-empty list")
    safe_changed = [str(safe_workspace_path(str(path))) for path in changed_files]
    if len(set(safe_changed)) != len(safe_changed):
        raise ArtifactValidationError("changed_files must be unique")

    files = artifact.get("files")
    if not isinstance(files, list) or not files:
        raise ArtifactValidationError("files must be a non-empty list")
    file_paths: list[str] = []
    for item in files:
        if not isinstance(item, dict):
            raise ArtifactValidationError("each file entry must be an object")
        file_path = str(safe_workspace_path(_require_string(item, "workspace_relative_path")))
        _require_string(item, "content")
        write_mode = str(item.get("write_mode") or "create_or_replace")
        if write_mode not in ALLOWED_WRITE_MODES:
            raise ArtifactValidationError(f"unsupported write_mode: {write_mode}")
        file_paths.append(file_path)

    if sorted(safe_changed) != sorted(set(file_paths)):
        raise ArtifactValidationError("changed_files must match files.workspace_relative_path")

    for key in ["intended_effect", "rollback_plan", "optimizer_source"]:
        _require_string(artifact, key)
    _require_bool(artifact, "visible_to_optimizer")
    holdout_derived = _require_bool(artifact, "holdout_derived")
    if holdout_derived and not allow_holdout_derived:
        raise ArtifactValidationError("holdout-derived artifacts are not injectable by default")

    expected = artifact_hash(artifact)
    declared = _require_string(artifact, "hash")
    if declared != expected:
        raise ArtifactValidationError(f"artifact hash mismatch: declared {declared}, expected {expected}")


def with_computed_hash(artifact: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(artifact)
    normalized["hash"] = artifact_hash(normalized)
    return normalized


def validate_injection_record(record: dict[str, Any]) -> None:
    if record.get("schema_version") != INJECTION_RECORD_SCHEMA_VERSION:
        raise ArtifactValidationError("unsupported injection record schema_version")
    for key in ["run_id", "artifact_id", "artifact_hash", "target_agent", "surface", "injected_at", "cleanup_policy"]:
        _require_string(record, key)
    if record["target_agent"] not in ALLOWED_TARGET_AGENTS:
        raise ArtifactValidationError(f"unsupported target_agent: {record['target_agent']}")
    if record["cleanup_policy"] not in ALLOWED_CLEANUP_POLICIES:
        raise ArtifactValidationError(f"unsupported cleanup_policy: {record['cleanup_policy']}")
    paths = record.get("workspace_relative_paths")
    if not isinstance(paths, list) or not paths:
        raise ArtifactValidationError("workspace_relative_paths must be a non-empty list")
    safe_paths = [str(safe_workspace_path(str(path))) for path in paths]
    if len(set(safe_paths)) != len(safe_paths):
        raise ArtifactValidationError("workspace_relative_paths must be unique")


def materialize_artifact(
    workspace: Path,
    artifact: dict[str, Any],
    *,
    run_id: str,
    surface: str,
    cleanup_policy: str = "workspace_discarded_after_run",
    injected_at: str | None = None,
) -> dict[str, Any]:
    validate_artifact(artifact)
    if cleanup_policy not in ALLOWED_CLEANUP_POLICIES:
        raise ArtifactValidationError(f"unsupported cleanup_policy: {cleanup_policy}")

    workspace = workspace.resolve()
    written_paths: list[str] = []
    for item in artifact["files"]:
        rel_path = str(safe_workspace_path(str(item["workspace_relative_path"])))
        destination = workspace / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = str(item["content"])
        write_mode = str(item.get("write_mode") or "create_or_replace")
        if write_mode == "append" and destination.exists():
            existing = destination.read_text(encoding="utf-8")
            separator = "" if not existing or existing.endswith("\n") else "\n"
            destination.write_text(f"{existing}{separator}{content}", encoding="utf-8")
        else:
            destination.write_text(content, encoding="utf-8")
        written_paths.append(rel_path)

    record = {
        "schema_version": INJECTION_RECORD_SCHEMA_VERSION,
        "run_id": run_id,
        "artifact_id": artifact["artifact_id"],
        "artifact_hash": artifact["hash"],
        "target_agent": artifact["target_agent"],
        "surface": surface,
        "workspace_relative_paths": sorted(written_paths),
        "injected_at": injected_at or iso_now(),
        "cleanup_policy": cleanup_policy,
    }
    validate_injection_record(record)
    return record


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ArtifactValidationError(f"expected JSON object in {path}")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize a sanitized Agent tuning artifact into a workspace.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--surface", required=True)
    parser.add_argument("--record-out", required=True)
    parser.add_argument("--cleanup-policy", default="workspace_discarded_after_run", choices=sorted(ALLOWED_CLEANUP_POLICIES))
    args = parser.parse_args(argv)

    artifact = _load_json(Path(args.artifact))
    record = materialize_artifact(
        Path(args.workspace),
        artifact,
        run_id=args.run_id,
        surface=args.surface,
        cleanup_policy=args.cleanup_policy,
    )
    record_path = Path(args.record_out)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
