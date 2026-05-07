"""Click specialist context-pack loading for prompt construction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from _common import ToolError


PACK_MARKER = "CLICK_SPECIALIST_CONTEXT_PACK_V1"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def disabled_evidence(reason: str) -> dict[str, Any]:
    return {
        "enabled": False,
        "expected_for_acut": False,
        "reason": reason,
        "pack_id": None,
        "pack_hash": None,
        "marker": None,
        "manifest_path": None,
        "context_prompt_path": None,
        "context_prompt_sha256": None,
        "context_prompt_char_count": 0,
        "section_ids": [],
        "section_markers_present_in_context": {},
        "content_recorded": False,
        "source_material_policy": {},
        "leakage_guards": {},
    }


def find_repo_root(reference: Path) -> Path:
    start = reference if reference.is_dir() else reference.parent
    for candidate in [start, *start.parents]:
        if (candidate / "experiments" / "core_narrative").exists() and (
            (candidate / ".git").exists() or (candidate / ".git").is_file()
        ):
            return candidate
    raise ToolError("could not locate experiment repository root", reference=str(reference))


def resolve_repo_path(raw_path: str, repo_root: Path, field: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = repo_root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ToolError(f"{field} must stay inside the experiment repository", path=raw_path) from exc
    return resolved


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ToolError("context pack manifest is not valid JSON", path=str(path)) from exc
    if not isinstance(data, dict):
        raise ToolError("context pack manifest root must be an object", path=str(path))
    return data


def specialist_context_config(acut: Mapping[str, Any]) -> tuple[bool, Mapping[str, Any] | None]:
    metadata = acut.get("metadata") if isinstance(acut.get("metadata"), dict) else {}
    specialist = metadata.get("specialist_context") if isinstance(metadata.get("specialist_context"), dict) else {}
    allowed = specialist.get("click_task_agnostic_context_allowed") is True
    context_pack = specialist.get("context_pack")
    if context_pack is not None and not isinstance(context_pack, dict):
        raise ToolError("metadata.specialist_context.context_pack must be an object when present")
    return allowed, context_pack


def load_click_specialist_context(acut: Mapping[str, Any], acut_path: str | Path) -> tuple[str, dict[str, Any]]:
    allowed, context_pack = specialist_context_config(acut)
    if not allowed:
        if context_pack is not None:
            raise ToolError("generic ACUT must not declare a Click specialist context pack")
        return "", disabled_evidence("acut does not allow click specialist context")
    if context_pack is None:
        raise ToolError("Click-specialist ACUT is missing metadata.specialist_context.context_pack")

    required = ["pack_id", "marker", "pack_hash", "manifest_path", "context_prompt_path", "section_ids"]
    missing = [key for key in required if key not in context_pack]
    if missing:
        raise ToolError("Click specialist context pack config is missing required fields", missing=missing)

    repo_root = find_repo_root(Path(acut_path).resolve())
    manifest_path = resolve_repo_path(str(context_pack["manifest_path"]), repo_root, "manifest_path")
    prompt_path = resolve_repo_path(str(context_pack["context_prompt_path"]), repo_root, "context_prompt_path")
    if not manifest_path.exists():
        raise ToolError("Click specialist context pack manifest does not exist", path=str(manifest_path))
    if not prompt_path.exists():
        raise ToolError("Click specialist context prompt does not exist", path=str(prompt_path))

    manifest = load_json(manifest_path)
    pack_id = str(context_pack["pack_id"])
    marker = str(context_pack["marker"])
    pack_hash = str(context_pack["pack_hash"])
    section_ids = [str(item) for item in context_pack["section_ids"]]

    if manifest.get("pack_id") != pack_id:
        raise ToolError("Click specialist context pack id mismatch")
    if manifest.get("marker") != marker:
        raise ToolError("Click specialist context marker mismatch")
    if manifest.get("pack_hash") != pack_hash:
        raise ToolError("Click specialist context pack hash mismatch")
    if marker != PACK_MARKER:
        raise ToolError("unexpected Click specialist context marker", marker=marker)
    manifest_sections = [str(item) for item in manifest.get("section_ids", [])]
    if manifest_sections != section_ids:
        raise ToolError("Click specialist context section id mismatch")

    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
    prompt_artifact = artifacts.get("context_prompt") if isinstance(artifacts.get("context_prompt"), dict) else {}
    expected_prompt_sha = prompt_artifact.get("sha256")
    actual_prompt_sha = sha256_file(prompt_path)
    if expected_prompt_sha != actual_prompt_sha:
        raise ToolError("Click specialist context prompt hash mismatch")

    prompt_text = prompt_path.read_text(encoding="utf-8")
    section_markers = {section_id: f"[CLICK_SECTION:{section_id}]" in prompt_text for section_id in section_ids}
    if marker not in prompt_text or not all(section_markers.values()):
        raise ToolError("Click specialist context prompt is missing required markers")

    leakage_guards = manifest.get("leakage_guards") if isinstance(manifest.get("leakage_guards"), dict) else {}
    source_policy = (
        manifest.get("source_material_policy") if isinstance(manifest.get("source_material_policy"), dict) else {}
    )
    evidence = {
        "enabled": True,
        "expected_for_acut": True,
        "pack_id": pack_id,
        "pack_hash": pack_hash,
        "marker": marker,
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "context_prompt_path": str(prompt_path),
        "context_prompt_sha256": actual_prompt_sha,
        "context_prompt_char_count": len(prompt_text),
        "section_ids": section_ids,
        "section_markers_present_in_context": section_markers,
        "content_recorded": False,
        "source_material_policy": {
            "public_committed_source_docs_tests_examples_only": bool(
                source_policy.get("public_committed_source_docs_tests_examples_only")
            ),
            "network_fetched_docs_used": bool(source_policy.get("network_fetched_docs_used")),
            "rbench_rwork_gold_patches_used": bool(source_policy.get("rbench_rwork_gold_patches_used")),
            "hidden_verifier_tests_used": bool(source_policy.get("hidden_verifier_tests_used")),
            "acut_outputs_or_failed_patches_used": bool(source_policy.get("acut_outputs_or_failed_patches_used")),
            "git_history_mining_used": bool(source_policy.get("git_history_mining_used")),
        },
        "leakage_guards": {
            "credential_values_recorded": bool(leakage_guards.get("credential_values_recorded")),
            "bearer_tokens_recorded": bool(leakage_guards.get("bearer_tokens_recorded")),
            "resolved_secrets_recorded": bool(leakage_guards.get("resolved_secrets_recorded")),
            "full_base_url_values_recorded": bool(leakage_guards.get("full_base_url_values_recorded")),
            "resolved_endpoint_values_recorded": bool(leakage_guards.get("resolved_endpoint_values_recorded")),
            "hostnames_recorded": bool(leakage_guards.get("hostnames_recorded")),
            "ip_addresses_recorded": bool(leakage_guards.get("ip_addresses_recorded")),
            "full_urls_recorded": bool(leakage_guards.get("full_urls_recorded")),
        },
    }
    return prompt_text, evidence


def prompt_injection_evidence(prompt: str, evidence: Mapping[str, Any]) -> dict[str, Any]:
    section_ids = [str(item) for item in evidence.get("section_ids", [])]
    marker = str(evidence.get("marker") or PACK_MARKER)
    pack_hash = evidence.get("pack_hash")
    prompt_sections = {section_id: f"[CLICK_SECTION:{section_id}]" in prompt for section_id in section_ids}
    prompt_evidence = dict(evidence)
    prompt_evidence["prompt_checks"] = {
        "marker_present": marker in prompt,
        "pack_id_present": bool(evidence.get("pack_id") and str(evidence["pack_id"]) in prompt),
        "pack_hash_present": bool(pack_hash and str(pack_hash) in prompt),
        "section_ids_present": prompt_sections,
        "all_expected_sections_present": all(prompt_sections.values()) if section_ids else False,
        "prompt_sha256": sha256_text(prompt),
        "prompt_char_count": len(prompt),
        "prompt_content_recorded": False,
    }
    if not evidence.get("enabled"):
        prompt_evidence["prompt_checks"]["marker_present"] = marker in prompt
        prompt_evidence["prompt_checks"]["pack_hash_present"] = False
        prompt_evidence["prompt_checks"]["all_expected_sections_present"] = False
    return prompt_evidence
