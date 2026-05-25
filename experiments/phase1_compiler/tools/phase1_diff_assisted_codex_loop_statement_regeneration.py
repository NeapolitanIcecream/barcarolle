from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load

import phase1_diff_assisted_statement_regeneration as dryrun


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_diff_assisted_codex_loop_statement_regeneration.yaml"
SCHEMA_VERSION = "barcarolle.phase1_diff_assisted_codex_loop_statement_regeneration.v1"
MODES = {
    "packets",
    "workflow",
    "copy-generator-output",
    "copy-reviewer-output",
    "qa",
    "screen",
    "decide",
}

FORBIDDEN_PACKET_KEYS = {
    "adapter_outcomes",
    "historical_paid_context",
    "hidden_verifier",
    "paid_outcome",
    "policy_violation",
    "raw_diff",
    "scoreable_cell",
    "solver_trace",
    "terminal_status",
}
FORBIDDEN_TEXT_PATTERNS = {
    "diff --git": "raw_diff_marker",
    "\n@@": "raw_diff_hunk_marker",
    "verified_pass": "paid_terminal_status",
    "verified_fail": "paid_terminal_status",
    "hidden verifier": "hidden_verifier_marker",
}
DETERMINISTIC_OVERRIDE_MARKERS = {
    "BEHAVIOR_OVERRIDES",
    "deterministic behavior override",
    "deterministic_generation_override",
    "deterministic reviewer rules",
}
TARGET_COMMIT_PATTERN = re.compile(r"\b[0-9a-f]{40}\b")
REVIEW_STATUSES = {"pass", "revise", "reject"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def config_path(raw: str | Path) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else REPO_ROOT / path


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected diff-assisted Codex loop config schema_version")
    config["_path"] = str(path)
    return config


def artifact_path(config: dict[str, Any], key: str) -> Path:
    return config_path(str(config["source_artifacts"][key]))


def output_path(config: dict[str, Any], key: str) -> Path:
    return config_path(str(config["output_paths"][key]))


def workflow_dir(config: dict[str, Any]) -> Path:
    return config_path(str(config["generation_review"]["workflow_dir"]))


def stable_generated_at(config: dict[str, Any]) -> str:
    preflight = output_path(config, "preflight")
    if preflight.exists():
        return str(read_json(preflight).get("generated_at") or config.get("created_at") or utc_now())
    return str(config.get("created_at") or utc_now())


def recursive_forbidden_findings(value: Any, *, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            item_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_PACKET_KEYS:
                findings.append(f"forbidden_key:{item_path}")
            findings.extend(recursive_forbidden_findings(item, path=item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(recursive_forbidden_findings(item, path=f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        for marker, reason in FORBIDDEN_TEXT_PATTERNS.items():
            if marker in lowered:
                findings.append(f"{reason}:{path}")
    return findings


def validate_packet_payload(payload: dict[str, Any]) -> None:
    findings = recursive_forbidden_findings(payload)
    if findings:
        raise ValueError("candidate packets contain forbidden material: " + ", ".join(sorted(findings)[:20]))
    for packet in payload.get("packets", []):
        encoded = json.dumps(packet, sort_keys=True)
        if TARGET_COMMIT_PATTERN.search(encoded):
            raise ValueError(f"candidate packet exposes target commit hash: {packet.get('task_id')}")


def load_source_contexts(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("boltons_source_context", "attrs_source_context"):
        rows.extend(dryrun.read_jsonl(artifact_path(config, key)))
    return dryrun.row_by_task(rows)


def load_certified_tasks(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("boltons_certified_tasks", "attrs_certified_tasks"):
        rows.extend(dryrun.read_jsonl(artifact_path(config, key)))
    return dryrun.row_by_task(rows)


def build_codex_loop_candidate_packet(
    *,
    config: dict[str, Any],
    candidate: dict[str, Any],
    certified: dict[str, Any] | None,
    source_context: dict[str, Any] | None,
) -> dict[str, Any]:
    packet = dryrun.build_candidate_packet(
        config=config,
        candidate=candidate,
        certified=certified,
        source_context=source_context,
    )
    packet["schema_version"] = "barcarolle.phase1.diff_assisted_codex_loop_candidate_packet.v1"
    packet["real_codex_loop_required"] = True
    packet["deterministic_generation_allowed"] = False
    packet["deterministic_review_allowed"] = False
    packet["historical_paid_outcomes_included"] = False
    packet["raw_target_diff_included"] = False
    return packet


def build_candidate_packets(config: dict[str, Any]) -> dict[str, Any]:
    inventory = read_json(artifact_path(config, "statement_hardened_inventory"))
    certified_by_task = load_certified_tasks(config)
    context_by_task = load_source_contexts(config)
    packets = [
        build_codex_loop_candidate_packet(
            config=config,
            candidate=candidate,
            certified=certified_by_task.get(str(candidate.get("task_id"))),
            source_context=context_by_task.get(str(candidate.get("task_id"))),
        )
        for candidate in inventory.get("candidates", [])
    ]
    payload = {
        "schema_version": "barcarolle.phase1.diff_assisted_codex_loop_candidate_packets.v1",
        "generated_at": stable_generated_at(config),
        "candidate_count": len(packets),
        "source_inventory_digest": f"sha256:{digest_text(json.dumps(inventory, sort_keys=True))}",
        "real_codex_loop_required": True,
        "deterministic_generation_review_fallback_allowed": False,
        "raw_target_diffs_committed": False,
        "hidden_verifier_material_included": False,
        "historical_paid_outcomes_included": False,
        "packets": packets,
    }
    validate_packet_payload(payload)
    return payload


def write_candidate_packets(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_candidate_packets(config)
    write_json(output_path(config, "candidate_packets"), payload)
    return payload


def endpoint_host() -> str:
    from urllib.parse import urlparse

    return urlparse(os.environ.get("LLM_BASE_URL", "")).hostname or ""


def build_generation_plan(config: dict[str, Any]) -> dict[str, Any]:
    packets_payload = read_json(output_path(config, "candidate_packets"))
    packets = packets_payload.get("packets", [])
    ordered = sorted(
        packets,
        key=lambda packet: (
            not packet.get("old_statement_quality", {}).get("body_summary_hit_old_cap"),
            str(packet.get("repo_id")),
            str(packet.get("task_id")),
        ),
    )
    return {
        "schema_version": "barcarolle.phase1.diff_assisted_codex_loop_generation_plan.v1",
        "generated_at": stable_generated_at(config),
        "candidate_count": len(ordered),
        "task_order": [packet["task_id"] for packet in ordered],
        "execution_mode": "external_codex_cli_generator_reviewer_loop",
        "generator_tmux_session": str(config["generation_review"]["generator_tmux_session"]),
        "reviewer_tmux_session": str(config["generation_review"]["reviewer_tmux_session"]),
        "required_model": str(config["policy"]["required_codex_model"]),
        "required_reasoning_effort": str(config["policy"]["required_reasoning_effort"]),
        "endpoint_env_vars_present": {
            "LLM_BASE_URL": bool(os.environ.get("LLM_BASE_URL")),
            "LLM_API_KEY": bool(os.environ.get("LLM_API_KEY")),
        },
        "endpoint_base_url_host": endpoint_host(),
        "max_iterations_per_batch": int(config["generation_review"]["max_iterations_per_batch"]),
        "paid_llm_generation_review_conditionally_enabled": True,
        "paid_acut_calls_made": False,
        "paid_solver_cells_run": False,
        "deterministic_generation_review_fallback_allowed": False,
        "raw_prompts_or_completions_committed": False,
        "raw_target_diffs_committed": False,
        "prioritization": "old 240-character cap candidates first, then repo and task id",
    }


def generator_prompt_text(config: dict[str, Any]) -> str:
    candidate_path = output_path(config, "candidate_packets").relative_to(REPO_ROOT)
    output_rel = workflow_dir(config).relative_to(REPO_ROOT) / "generator" / "output" / "generated_statements.jsonl"
    process_rel = workflow_dir(config).relative_to(REPO_ROOT) / "generator" / "process.md"
    return f"""# External Codex CLI Generator

You are the real external Codex CLI generator session for the corrected Phase 1 diff-assisted statement regeneration run.

Work in `/Users/chenmohan/gits/barcarolle`. Do not commit. Do not push. Do not run solver ACUT cells.

Read only this sanitized candidate packet file for generation input:

`{candidate_path}`

Write one JSONL row per packet to:

`{output_rel}`

Update this process file before and after work:

`{process_rel}`

Required output row shape:

```json
{{"task_id":"...","statement":"...","statement_digest":"sha256:...","generation_notes":"...","used_diff_summary":true,"contains_raw_diff":false,"contains_paid_outcome":false}}
```

Rules:

- Generate solver-facing statements from public context plus diff summaries and digests in the packets.
- Do not copy previous `phase1_diff_assisted_statement_*` regenerated statements or deterministic dry-run output.
- Do not use deterministic behavior overrides, local rule-based statement generation, or old reviewer verdicts.
- Do not include raw diff hunks, `diff --git`, exact patch recipes, raw test assertions, target commit hashes, hidden verifier material, paid outcomes, or terminal statuses.
- Target 1500-2500 characters per statement, soft maximum 4000 characters, and never substring-truncate.
- Include problem summary, behavior details, expected behavior, editable implementation paths, non-editable test paths, verifier metadata, and scope boundaries.
- Set `statement_digest` to `sha256:` plus the SHA-256 digest of the exact statement string.
- Set `status: delivered` in the process file only after the JSONL output is complete.

Process file format:

```text
status: delivered
updated: <UTC timestamp>
summary: Generated <N> statements as a real external Codex CLI generator session.
artifacts:
  - {output_rel}
verification:
  - row count and statement digest check performed
```
"""


def reviewer_prompt_text(config: dict[str, Any]) -> str:
    packet_rel = output_path(config, "candidate_packets").relative_to(REPO_ROOT)
    statements_rel = output_path(config, "generated_statements").relative_to(REPO_ROOT)
    review_rel = workflow_dir(config).relative_to(REPO_ROOT) / "reviewer" / "output" / "statement_reviews.json"
    process_rel = workflow_dir(config).relative_to(REPO_ROOT) / "reviewer" / "process.md"
    handoff_rel = workflow_dir(config).relative_to(REPO_ROOT) / "reviewer" / "review-to-generator.md"
    return f"""# External Codex CLI Reviewer

You are the real external Codex CLI reviewer session for the corrected Phase 1 diff-assisted statement regeneration run.

Work in `/Users/chenmohan/gits/barcarolle`. Do not commit. Do not push. Do not edit generated statements.

Read:

- Sanitized candidate packets: `{packet_rel}`
- Generated statement JSONL copied from the generator session: `{statements_rel}`

Write review verdicts to:

`{review_rel}`

Update this process file before and after work:

`{process_rel}`

Also write a concise handoff summary to:

`{handoff_rel}`

Each review row must use this shape:

```json
{{"task_id":"...","status":"pass","leakage_pass":true,"sufficiency_pass":true,"faithfulness_pass":true,"scope_pass":true,"formatting_pass":true,"reasons":["..."],"required_revision":"","statement_digest":"sha256:..."}}
```

Top-level output must include:

```json
{{"schema_version":"barcarolle.phase1.diff_assisted_codex_loop_statement_reviews.v1","generated_at":"...","candidate_count":0,"review_counts":{{}},"paid_llm_calls_made":true,"paid_acut_calls_made":false,"reviews":[]}}
```

Review checks:

- Leakage: no gold patch text, no raw diff hunks, no `diff --git`, no exact implementation recipe, no hidden verifier content, no raw test assertions, no paid outcome/status, no target commit hash.
- Sufficiency: problem summary, expected public behavior, reproduction or behavior description, closed code fences, no mid-sentence truncation, and enough detail to attempt without hidden tests.
- Faithfulness: statement must be consistent with public context and diff summary.
- Scope: editable paths must be implementation-only; tests are non-editable metadata.
- Formatting: target 1500-2500 characters, soft max 4000, required sections present.

Return `pass`, `revise`, or `reject`. A `pass` row must have all five boolean checks true. Do not create replacement statements.

Set `status: delivered` in the process file only after every generated statement has exactly one review verdict.
"""


def run_script_text(role: str, config: dict[str, Any]) -> str:
    wf_rel = workflow_dir(config).relative_to(REPO_ROOT)
    session_name = str(config["generation_review"][f"{role}_tmux_session"])
    prompt = wf_rel / role / "prompt.md"
    process = wf_rel / role / "process.md"
    log = wf_rel / role / "cli.log"
    return f"""#!/usr/bin/env bash
set -euo pipefail
cd /Users/chenmohan/gits/barcarolle

WORKFLOW="{wf_rel}"
PROCESS="{process}"
LOG="{log}"

timestamp() {{
  date -u +%Y-%m-%dT%H:%M:%SZ
}}

if ! {{ test -n "${{LLM_BASE_URL:-}}" && test -n "${{LLM_API_KEY:-}}"; }}; then
  test -f ~/.zshrc && source ~/.zshrc >/dev/null 2>&1 || true
fi

if ! {{ test -n "${{LLM_BASE_URL:-}}" && test -n "${{LLM_API_KEY:-}}"; }}; then
  cat > "$PROCESS" <<EOF
status: blocked
updated: $(timestamp)
summary: Required LLM_BASE_URL or LLM_API_KEY was missing before the external Codex CLI {role} call.
session: {session_name}
EOF
  exit 2
fi

mkdir -p "$WORKFLOW/{role}/output"
cat > "$PROCESS" <<EOF
status: working
updated: $(timestamp)
summary: External Codex CLI {role} wrapper started with required endpoint environment present.
session: {session_name}
EOF

set +e
codex exec \\
  --ignore-user-config \\
  -C /Users/chenmohan/gits/barcarolle \\
  -m gpt-5.5 \\
  -c 'model="gpt-5.5"' \\
  -c 'model_provider="barcarolle_llm"' \\
  -c 'model_providers.barcarolle_llm.name="Barcarolle LLM Endpoint"' \\
  -c "model_providers.barcarolle_llm.base_url=\\"${{LLM_BASE_URL}}\\"" \\
  -c 'model_providers.barcarolle_llm.wire_api="responses"' \\
  -c 'model_providers.barcarolle_llm.env_key="LLM_API_KEY"' \\
  -c 'model_reasoning_effort="xhigh"' \\
  --dangerously-bypass-approvals-and-sandbox \\
  - < "{prompt}" \\
  > "$LOG" \\
  2>&1
rc=$?
set -e

if [ "$rc" -ne 0 ]; then
  cat > "$PROCESS" <<EOF
status: blocked
updated: $(timestamp)
summary: External Codex CLI {role} exited non-zero. Raw log is intentionally ignored and not committed.
session: {session_name}
exit_code: $rc
EOF
  exit "$rc"
fi

if ! grep -q '^status: delivered' "$PROCESS"; then
  cat >> "$PROCESS" <<EOF
wrapper_status: blocked_after_cli_return
wrapper_updated: $(timestamp)
wrapper_summary: Codex CLI returned zero but the {role} process file did not report delivered.
EOF
  exit 3
fi
"""


def pending_process_text(role: str) -> str:
    return f"""status: pending
updated: {utc_now()}
summary: Waiting for external Codex CLI {role} session to start.
"""


def coordinator_text(config: dict[str, Any]) -> str:
    return f"""# Phase 1 Diff-Assisted Statement Regeneration Codex Loop

Status: pending.

Runbook: `docs/experiments/phase-1-diff-assisted-statement-regeneration-runbook.md`.

This workflow is the corrected external Codex CLI generator/reviewer loop. Deterministic helpers may build packets, validate schemas, run leakage checks, and screen reviewed statements. They must not generate final statements or reviewer verdicts.

## Sessions

- Generator tmux session: `{config['generation_review']['generator_tmux_session']}`.
- Reviewer tmux session: `{config['generation_review']['reviewer_tmux_session']}`.

## Coordination Contract

- Check `generator/process.md` and `reviewer/process.md`; do not read CLI logs for normal coordination.
- Start reviewer only after the generator process reports `status: delivered` and the sanitized generated statements have been copied to `experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_generated_statements.jsonl`.
- Raw logs are ignored and must not be committed.
"""


def write_workflow_files(config: dict[str, Any]) -> dict[str, Any]:
    wf = workflow_dir(config)
    write_text(wf / "coordinator.md", coordinator_text(config))
    write_text(wf / "generator" / "prompt.md", generator_prompt_text(config))
    write_text(wf / "generator" / "process.md", pending_process_text("generator"))
    write_text(wf / "generator" / "run_generator.sh", run_script_text("generator", config))
    write_text(wf / "reviewer" / "prompt.md", reviewer_prompt_text(config))
    write_text(wf / "reviewer" / "process.md", pending_process_text("reviewer"))
    write_text(wf / "reviewer" / "review-to-generator.md", "status: pending\n")
    write_text(wf / "reviewer" / "run_reviewer.sh", run_script_text("reviewer", config))
    for path in (wf / "generator" / "run_generator.sh", wf / "reviewer" / "run_reviewer.sh"):
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    plan = build_generation_plan(config)
    write_json(output_path(config, "generation_plan"), plan)
    return plan


def status_from_process(path: Path) -> str:
    if not path.exists():
        return "missing"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("status:"):
            return line.split(":", 1)[1].strip()
    return "missing"


def statement_digest(statement: str) -> str:
    return f"sha256:{digest_text(statement)}"


def validate_generated_statement_rows(rows: list[dict[str, Any]], packet_count: int) -> None:
    if len(rows) != packet_count:
        raise ValueError(f"generated statement row count mismatch: expected {packet_count}, got {len(rows)}")
    seen: set[str] = set()
    for row in rows:
        task_id = str(row.get("task_id") or "")
        if not task_id or task_id in seen:
            raise ValueError(f"missing or duplicate generated statement task_id: {task_id}")
        seen.add(task_id)
        statement = str(row.get("statement") or "")
        if not statement:
            raise ValueError(f"generated statement is empty: {task_id}")
        if row.get("statement_digest") != statement_digest(statement):
            raise ValueError(f"generated statement digest mismatch: {task_id}")
        if row.get("used_diff_summary") is not True:
            raise ValueError(f"generated statement did not record diff-summary use: {task_id}")
        if row.get("contains_raw_diff") is not False:
            raise ValueError(f"generated statement records raw diff inclusion: {task_id}")
        if row.get("contains_paid_outcome") is not False:
            raise ValueError(f"generated statement records paid outcome inclusion: {task_id}")
        encoded = json.dumps(row, sort_keys=True)
        for marker in DETERMINISTIC_OVERRIDE_MARKERS:
            if marker.lower() in encoded.lower():
                raise ValueError(f"generated statement row mentions deterministic override marker: {task_id}")


def session_proof_base(config: dict[str, Any]) -> dict[str, Any]:
    proof_path = output_path(config, "session_proof")
    if proof_path.exists():
        return read_json(proof_path)
    return {
        "schema_version": "barcarolle.phase1.diff_assisted_codex_loop_session_proof.v1",
        "generated_at": stable_generated_at(config),
        "endpoint_base_url_host": endpoint_host(),
        "model_provider": "barcarolle_llm",
        "model_provider_env_key": "LLM_API_KEY",
        "required_model": "gpt-5.5",
        "required_reasoning_effort": "xhigh",
        "real_generator_codex_cli_session_started": False,
        "real_reviewer_codex_cli_session_started": False,
        "generator_process_file_present": False,
        "reviewer_process_file_present": False,
        "raw_cli_logs_committed": False,
        "paid_acut_solver_cells_run": False,
        "historical_paid_outcomes_used_for_generation_or_review": False,
        "sessions": [],
    }


def write_session_proof_report(config: dict[str, Any], proof: dict[str, Any]) -> None:
    lines = [
        "# Phase 1 Diff-Assisted Codex Loop Session Proof",
        "",
        f"Generated: `{proof['generated_at']}`.",
        "",
        f"- Endpoint host: `{proof.get('endpoint_base_url_host', '')}`.",
        f"- Model provider: `{proof.get('model_provider')}` using env key `{proof.get('model_provider_env_key')}`.",
        f"- Generator session started: `{proof['real_generator_codex_cli_session_started']}`.",
        f"- Reviewer session started: `{proof['real_reviewer_codex_cli_session_started']}`.",
        f"- Generator process file present: `{proof['generator_process_file_present']}`.",
        f"- Reviewer process file present: `{proof['reviewer_process_file_present']}`.",
        f"- Raw CLI logs committed: `{proof['raw_cli_logs_committed']}`.",
        f"- Paid ACUT solver cells run: `{proof['paid_acut_solver_cells_run']}`.",
        "",
        "## Sessions",
        "",
    ]
    for session in proof.get("sessions", []):
        lines.extend(
            [
                f"### {session['role']}",
                "",
                f"- tmux session: `{session['tmux_session']}`.",
                f"- command shape: `{session['command_shape']}`.",
                f"- started at: `{session.get('started_at', '')}`.",
                f"- ended at: `{session.get('ended_at', '')}`.",
                f"- process status: `{session.get('process_status', '')}`.",
                f"- output row count: `{session.get('output_row_count', 0)}`.",
                "",
            ]
        )
    write_text(output_path(config, "session_proof_report"), "\n".join(lines))


def copy_generator_output(config: dict[str, Any]) -> dict[str, Any]:
    wf = workflow_dir(config)
    source = wf / "generator" / "output" / "generated_statements.jsonl"
    process = wf / "generator" / "process.md"
    if status_from_process(process) != "delivered":
        raise ValueError("generator process did not report status: delivered")
    packets = read_json(output_path(config, "candidate_packets"))
    rows = read_jsonl(source)
    validate_generated_statement_rows(rows, int(packets["candidate_count"]))
    write_jsonl(output_path(config, "generated_statements"), rows)
    proof = session_proof_base(config)
    proof["real_generator_codex_cli_session_started"] = True
    proof["generator_process_file_present"] = process.exists()
    proof["generator_output_not_deterministic_override"] = True
    proof["sessions"] = [
        session for session in proof.get("sessions", []) if session.get("role") != "generator"
    ] + [
        {
            "role": "generator",
            "tmux_session": str(config["generation_review"]["generator_tmux_session"]),
            "command_shape": "tmux new-session -> run_generator.sh -> codex exec with barcarolle_llm env_key LLM_API_KEY",
            "started_at": stable_generated_at(config),
            "ended_at": utc_now(),
            "process_status": "delivered",
            "process_file": str(process.relative_to(REPO_ROOT)),
            "output_row_count": len(rows),
            "output_path": str(output_path(config, "generated_statements").relative_to(REPO_ROOT)),
        }
    ]
    write_json(output_path(config, "session_proof"), proof)
    write_session_proof_report(config, proof)
    return proof


def validate_review_payload(payload: dict[str, Any], generated_rows: list[dict[str, Any]]) -> None:
    reviews = payload.get("reviews", [])
    if len(reviews) != len(generated_rows):
        raise ValueError(f"review row count mismatch: expected {len(generated_rows)}, got {len(reviews)}")
    generated_by_task = {row["task_id"]: row for row in generated_rows}
    seen: set[str] = set()
    for review in reviews:
        task_id = str(review.get("task_id") or "")
        if task_id not in generated_by_task or task_id in seen:
            raise ValueError(f"missing or duplicate review task_id: {task_id}")
        seen.add(task_id)
        status = str(review.get("status") or "")
        if status not in REVIEW_STATUSES:
            raise ValueError(f"invalid review status for {task_id}: {status}")
        for key in ("leakage_pass", "sufficiency_pass", "faithfulness_pass", "scope_pass", "formatting_pass"):
            if not isinstance(review.get(key), bool):
                raise ValueError(f"review boolean check missing for {task_id}: {key}")
        if status == "pass" and not all(
            review.get(key) is True
            for key in ("leakage_pass", "sufficiency_pass", "faithfulness_pass", "scope_pass", "formatting_pass")
        ):
            raise ValueError(f"pass review has failing boolean check: {task_id}")
        if review.get("statement_digest") != generated_by_task[task_id].get("statement_digest"):
            raise ValueError(f"review statement digest mismatch: {task_id}")
        encoded = json.dumps(review, sort_keys=True).lower()
        for marker, reason in FORBIDDEN_TEXT_PATTERNS.items():
            if marker in encoded:
                raise ValueError(f"review contains forbidden text {reason}: {task_id}")


def normalize_review_payload(payload: dict[str, Any]) -> dict[str, Any]:
    reviews = payload.get("reviews", [])
    counts = dict(sorted(Counter(str(review.get("status")) for review in reviews).items()))
    normalized = dict(payload)
    normalized["schema_version"] = "barcarolle.phase1.diff_assisted_codex_loop_statement_reviews.v1"
    normalized["generated_at"] = str(payload.get("generated_at") or utc_now())
    normalized["candidate_count"] = len(reviews)
    normalized["review_counts"] = counts
    normalized["paid_llm_calls_made"] = True
    normalized["paid_acut_calls_made"] = False
    normalized["raw_prompts_or_completions_committed"] = False
    normalized["reviews"] = reviews
    return normalized


def render_statement_reviews_markdown(reviews: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Diff-Assisted Codex Loop Statement Reviews",
        "",
        f"Generated: `{reviews['generated_at']}`.",
        "",
        f"- Candidate statements reviewed: `{reviews['candidate_count']}`.",
        f"- Review counts: `{reviews['review_counts']}`.",
        f"- Deterministic QA counts: `{reviews.get('deterministic_qa_counts', {})}`.",
        f"- Paid LLM calls made: `{reviews.get('paid_llm_calls_made')}`.",
        "- Paid ACUT calls made: `false`.",
        "- Raw prompts or completions committed: `false`.",
        "",
        "## Verdicts",
        "",
    ]
    for review in reviews["reviews"]:
        lines.extend(
            [
                f"### {review['task_id']}",
                "",
                f"- Status: `{review['status']}`.",
                f"- Checks: `{{'leakage_pass': {review['leakage_pass']}, 'sufficiency_pass': {review['sufficiency_pass']}, 'faithfulness_pass': {review['faithfulness_pass']}, 'scope_pass': {review['scope_pass']}, 'formatting_pass': {review['formatting_pass']}}}`.",
                f"- Deterministic QA: `{review.get('deterministic_qa', {}).get('status', 'not_run')}`.",
                f"- Reasons: `{review.get('reasons', [])}`.",
                f"- Required revision: `{review.get('required_revision', '')}`.",
                "",
            ]
        )
    return "\n".join(lines)


def copy_reviewer_output(config: dict[str, Any]) -> dict[str, Any]:
    wf = workflow_dir(config)
    source = wf / "reviewer" / "output" / "statement_reviews.json"
    process = wf / "reviewer" / "process.md"
    if status_from_process(process) != "delivered":
        raise ValueError("reviewer process did not report status: delivered")
    generated = read_jsonl(output_path(config, "generated_statements"))
    payload = normalize_review_payload(read_json(source))
    validate_review_payload(payload, generated)
    write_json(output_path(config, "statement_reviews"), payload)
    write_text(output_path(config, "statement_reviews_report"), render_statement_reviews_markdown(payload))
    proof = session_proof_base(config)
    proof["real_reviewer_codex_cli_session_started"] = True
    proof["reviewer_process_file_present"] = process.exists()
    proof["reviewer_output_not_deterministic_rules_only"] = True
    proof["sessions"] = [
        session for session in proof.get("sessions", []) if session.get("role") != "reviewer"
    ] + [
        {
            "role": "reviewer",
            "tmux_session": str(config["generation_review"]["reviewer_tmux_session"]),
            "command_shape": "tmux new-session -> run_reviewer.sh -> codex exec with barcarolle_llm env_key LLM_API_KEY",
            "started_at": stable_generated_at(config),
            "ended_at": utc_now(),
            "process_status": "delivered",
            "process_file": str(process.relative_to(REPO_ROOT)),
            "output_row_count": len(payload["reviews"]),
            "output_path": str(output_path(config, "statement_reviews").relative_to(REPO_ROOT)),
        }
    ]
    write_json(output_path(config, "session_proof"), proof)
    write_session_proof_report(config, proof)
    return payload


def deterministic_qa_row(packet: dict[str, Any], statement: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    legacy_review = {
        "final_status": review.get("status"),
        "statement_digest": review.get("statement_digest"),
    }
    qa = dryrun.deterministic_statement_qa(packet, statement, legacy_review)
    if review.get("status") != "pass" and qa["status"] == "pass":
        qa["status"] = "reject"
        qa["reasons"] = sorted(set(qa["reasons"] + [f"review_status:{review.get('status')}"]))
    return qa


def apply_deterministic_qa(config: dict[str, Any]) -> dict[str, Any]:
    packets = read_json(output_path(config, "candidate_packets"))["packets"]
    packet_by_task = {packet["task_id"]: packet for packet in packets}
    statements = read_jsonl(output_path(config, "generated_statements"))
    statement_by_task = {row["task_id"]: row for row in statements}
    reviews = read_json(output_path(config, "statement_reviews"))
    qa_rows: list[dict[str, Any]] = []
    updated_reviews: list[dict[str, Any]] = []
    for review in reviews["reviews"]:
        task_id = review["task_id"]
        qa = deterministic_qa_row(packet_by_task[task_id], statement_by_task[task_id], review)
        qa_rows.append({"task_id": task_id, **qa})
        review = dict(review)
        review["deterministic_qa"] = qa
        updated_reviews.append(review)
    qa_payload = {
        "schema_version": "barcarolle.phase1.diff_assisted_codex_loop_deterministic_qa.v1",
        "generated_at": utc_now(),
        "candidate_count": len(qa_rows),
        "qa_counts": dict(sorted(Counter(row["status"] for row in qa_rows).items())),
        "deterministic_qa_guardrail_only": True,
        "deterministic_qa_created_pass_without_reviewer_pass": False,
        "paid_acut_calls_made": False,
        "rows": qa_rows,
    }
    reviews["reviews"] = updated_reviews
    reviews["deterministic_qa_counts"] = qa_payload["qa_counts"]
    write_json(output_path(config, "deterministic_qa"), qa_payload)
    write_json(output_path(config, "statement_reviews"), reviews)
    write_text(output_path(config, "statement_reviews_report"), render_statement_reviews_markdown(reviews))
    return qa_payload


def regenerated_candidate_records(config: dict[str, Any]) -> list[dict[str, Any]]:
    inventory = read_json(artifact_path(config, "statement_hardened_inventory"))
    reviews = read_json(output_path(config, "statement_reviews"))
    statements = read_jsonl(output_path(config, "generated_statements"))
    review_by_task = {row["task_id"]: row for row in reviews["reviews"]}
    statement_by_task = {row["task_id"]: row for row in statements}
    records: list[dict[str, Any]] = []
    for candidate in inventory.get("candidates", []):
        task_id = str(candidate["task_id"])
        review = review_by_task.get(task_id, {})
        qa = review.get("deterministic_qa") or {}
        eligible_after = review.get("status") == "pass" and qa.get("status") == "pass"
        reasons: list[str] = []
        if review.get("status") != "pass":
            reasons.append(f"real_reviewer_status:{review.get('status', 'missing')}")
        if qa.get("status") != "pass":
            reasons.append(f"deterministic_qa_status:{qa.get('status', 'missing')}")
        records.append(
            {
                "task_id": task_id,
                "repo_id": str(candidate["repo_id"]),
                "task_time": str(candidate.get("task_time") or ""),
                "release_split_eligibility": [str(split) for split in candidate.get("release_split_eligibility", [])],
                "eligible_before_regeneration": bool(candidate.get("selection_eligible_without_paid_outcome")),
                "eligible_after_codex_loop_regeneration": eligible_after,
                "statement_digest": statement_by_task.get(task_id, {}).get("statement_digest", ""),
                "real_reviewer_status": review.get("status", "missing"),
                "deterministic_qa_status": qa.get("status", "missing"),
                "old_statement_quality_gate": str(candidate.get("statement_quality_gate") or ""),
                "old_statement_quality_risk_reasons": [str(reason) for reason in candidate.get("statement_quality_risk_reasons", [])],
                "rejection_reasons_after_codex_loop_regeneration": reasons,
            }
        )
    return records


def select_by_repo_split(records: list[dict[str, Any]], *, repos: list[str], splits: list[str], per_split: int) -> dict[str, list[str]]:
    selected = {f"{repo}/{split}": [] for repo in repos for split in splits}
    for record in sorted(records, key=lambda row: (row["task_time"], row["task_id"])):
        if not record["eligible_after_codex_loop_regeneration"]:
            continue
        repo = record["repo_id"]
        if repo not in repos:
            continue
        for split in record["release_split_eligibility"]:
            key = f"{repo}/{split}"
            if key in selected and len(selected[key]) < per_split:
                selected[key].append(record["task_id"])
    return selected


def build_statement_screen(config: dict[str, Any]) -> dict[str, Any]:
    old_screen = read_json(artifact_path(config, "statement_hardened_screen"))
    records = regenerated_candidate_records(config)
    repos = [str(repo) for repo in config["selection"]["preferred_repos"]]
    splits = [str(split) for split in config["selection"]["preferred_splits"]]
    per_split = int(config["selection"]["tasks_per_repo_split"])
    selected = select_by_repo_split(records, repos=repos, splits=splits, per_split=per_split)
    selected_counts = {key: len(value) for key, value in sorted(selected.items())}
    missing = {
        key: [f"needed {per_split}, found {count} eligible Codex-reviewed regenerated statements without using paid outcomes"]
        for key, count in selected_counts.items()
        if count < per_split
    }
    review_counts = Counter(record["real_reviewer_status"] for record in records)
    qa_counts = Counter(record["deterministic_qa_status"] for record in records)
    eligible_before = int(old_screen.get("summary", {}).get("eligible_candidate_count") or sum(1 for row in records if row["eligible_before_regeneration"]))
    eligible_after = sum(1 for row in records if row["eligible_after_codex_loop_regeneration"])
    return {
        "schema_version": "barcarolle.phase1.diff_assisted_codex_loop_statement_screen.v1",
        "generated_at": utc_now(),
        "candidate_count": len(records),
        "regenerated_statement_count": len(records),
        "real_reviewer_counts": dict(sorted(review_counts.items())),
        "deterministic_qa_counts": dict(sorted(qa_counts.items())),
        "eligible_count_before_regeneration": eligible_before,
        "eligible_count_after_codex_loop_regeneration": eligible_after,
        "selected_task_ids_by_repo_split": selected,
        "selected_counts_by_repo_split": selected_counts,
        "remaining_missing_supply": missing,
        "true_supply_holes": {key: value for key, value in missing.items() if key == "boltons/H_future"},
        "real_reviewer_failures_separated": True,
        "deterministic_qa_failures_separated": True,
        "old_candidates_recovered_by_real_codex_loop": eligible_after > eligible_before,
        "full_statement_hardened_release_recovered": not missing,
        "replacement_supply_still_needed": bool(missing),
        "paid_outcome_used_for_selection": False,
        "paid_acut_calls_made": False,
        "paid_solver_cells_run": False,
        "candidate_screens": records,
    }


def render_statement_screen_markdown(screen: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Diff-Assisted Codex Loop Statement Screen",
        "",
        f"Generated: `{screen['generated_at']}`.",
        "",
        f"- Candidate count: `{screen['candidate_count']}`.",
        f"- Regenerated statement count: `{screen['regenerated_statement_count']}`.",
        f"- Real reviewer counts: `{screen['real_reviewer_counts']}`.",
        f"- Deterministic QA counts: `{screen['deterministic_qa_counts']}`.",
        f"- Eligible before regeneration: `{screen['eligible_count_before_regeneration']}`.",
        f"- Eligible after Codex loop regeneration: `{screen['eligible_count_after_codex_loop_regeneration']}`.",
        f"- Selected counts by repo/split: `{screen['selected_counts_by_repo_split']}`.",
        f"- Remaining missing supply: `{screen['remaining_missing_supply']}`.",
        f"- Replacement supply still needed: `{screen['replacement_supply_still_needed']}`.",
        "",
        "The screen uses only statements with real reviewer `pass` and deterministic QA `pass`. It does not use paid outcomes for selection.",
        "",
    ]
    if "boltons/H_future" in screen["remaining_missing_supply"]:
        lines.extend(
            [
                "## Remaining True Supply Hole",
                "",
                "The old inventory still contains no eligible `boltons/H_future` supply after Codex-reviewed regeneration.",
                "",
            ]
        )
    return "\n".join(lines)


def write_statement_screen(config: dict[str, Any]) -> dict[str, Any]:
    screen = build_statement_screen(config)
    write_json(output_path(config, "statement_screen"), screen)
    write_text(output_path(config, "statement_screen_report"), render_statement_screen_markdown(screen))
    return screen


def build_recovery_decision(config: dict[str, Any]) -> dict[str, Any]:
    proof = read_json(output_path(config, "session_proof"))
    screen = read_json(output_path(config, "statement_screen"))
    loop_completed = all(
        [
            proof.get("real_generator_codex_cli_session_started"),
            proof.get("real_reviewer_codex_cli_session_started"),
            proof.get("generator_process_file_present"),
            proof.get("reviewer_process_file_present"),
            proof.get("generator_output_not_deterministic_override"),
            proof.get("reviewer_output_not_deterministic_rules_only"),
        ]
    )
    if not loop_completed:
        primary = "blocked_real_codex_loop_not_completed"
    elif screen["full_statement_hardened_release_recovered"]:
        primary = "old_candidate_pool_recovered_retry_preregistration"
    elif screen["eligible_count_after_codex_loop_regeneration"] > screen["eligible_count_before_regeneration"]:
        primary = "partial_recovery_mine_targeted_replacement_supply"
    else:
        primary = "regeneration_failed_old_pool_not_recoverable"
    next_runbook = (
        "docs/experiments/phase-1-statement-hardened-preregistration-after-codex-loop-runbook.md"
        if primary == "old_candidate_pool_recovered_retry_preregistration"
        else "docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md"
    )
    return {
        "schema_version": "barcarolle.phase1.diff_assisted_codex_loop_recovery_decision.v1",
        "generated_at": utc_now(),
        "primary_decision": primary,
        "real_codex_generator_reviewer_loop_completed": loop_completed,
        "real_generator_session_completed": bool(proof.get("real_generator_codex_cli_session_started")),
        "real_reviewer_session_completed": bool(proof.get("real_reviewer_codex_cli_session_started")),
        "old_candidate_pool_recovered": "full" if primary.startswith("old_candidate_pool") else "partial" if primary.startswith("partial") else False,
        "replacement_supply_still_needed": bool(screen["remaining_missing_supply"]),
        "decision_basis": {
            "candidate_count": screen["candidate_count"],
            "real_reviewer_counts": screen["real_reviewer_counts"],
            "deterministic_qa_counts": screen["deterministic_qa_counts"],
            "eligible_count_before_regeneration": screen["eligible_count_before_regeneration"],
            "eligible_count_after_codex_loop_regeneration": screen["eligible_count_after_codex_loop_regeneration"],
            "selected_counts_by_repo_split": screen["selected_counts_by_repo_split"],
            "remaining_missing_supply": screen["remaining_missing_supply"],
        },
        "next_runbook_path": next_runbook,
        "paid_validation_completed": False,
        "paid_acut_calls_made": False,
        "paid_solver_cells_run": False,
        "historical_paid_outcomes_used_for_generation_or_review": False,
        "predictive_validity_established": False,
        "generated_statement_is_scoreable_result": False,
        "old_paid_result_repaired": False,
    }


def render_recovery_decision_markdown(decision: dict[str, Any]) -> str:
    basis = decision["decision_basis"]
    return f"""# Phase 1 Diff-Assisted Codex Loop Recovery Decision

Generated: `{decision['generated_at']}`.

## Decision

- Primary decision: `{decision['primary_decision']}`.
- Real Codex generator/reviewer loop completed: `{decision['real_codex_generator_reviewer_loop_completed']}`.
- Old candidate pool recovered: `{decision['old_candidate_pool_recovered']}`.
- Replacement supply still needed: `{decision['replacement_supply_still_needed']}`.
- Next runbook: `{decision['next_runbook_path']}`.

## Basis

- Candidate count: `{basis['candidate_count']}`.
- Real reviewer counts: `{basis['real_reviewer_counts']}`.
- Deterministic QA counts: `{basis['deterministic_qa_counts']}`.
- Eligible before regeneration: `{basis['eligible_count_before_regeneration']}`.
- Eligible after Codex loop regeneration: `{basis['eligible_count_after_codex_loop_regeneration']}`.
- Selected counts by repo/split: `{basis['selected_counts_by_repo_split']}`.
- Remaining missing supply: `{basis['remaining_missing_supply']}`.

## Boundary

This decision is based on a real external Codex CLI generator/reviewer loop plus deterministic QA guardrails. It does not claim predictive validity, paid validation, repaired historical paid results, or scoreable results from generated statements.
"""


def write_recovery_decision(config: dict[str, Any]) -> dict[str, Any]:
    decision = build_recovery_decision(config)
    write_json(output_path(config, "recovery_decision"), decision)
    write_text(output_path(config, "recovery_decision_report"), render_recovery_decision_markdown(decision))
    return decision


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build corrected Phase 1 diff-assisted Codex loop artifacts.")
    parser.add_argument("mode", choices=sorted(MODES))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if args.mode == "packets":
        write_candidate_packets(config)
    elif args.mode == "workflow":
        write_workflow_files(config)
    elif args.mode == "copy-generator-output":
        copy_generator_output(config)
    elif args.mode == "copy-reviewer-output":
        copy_reviewer_output(config)
    elif args.mode == "qa":
        apply_deterministic_qa(config)
    elif args.mode == "screen":
        write_statement_screen(config)
    elif args.mode == "decide":
        write_recovery_decision(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
