from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXP_REL = Path("experiments/phase0_headroom")
BASE_PREFIX = "codex_kilo_workspace"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def phase0_root(root: Path) -> Path:
    candidate = root / EXP_REL
    return candidate if candidate.exists() else root


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_score_table(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def raw_path(exp: Path, row: dict[str, Any], name: str) -> Path | None:
    rel = row.get("raw_artifacts", {}).get(name)
    return exp / rel if rel else None


def solver_workspace_from_patch(exp: Path, patch_path: Path | None) -> Path | None:
    if patch_path is None:
        return None
    try:
        rel = patch_path.relative_to(exp)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) < 7 or parts[:3] != ("results", "raw", "workspace_acut"):
        return None
    return exp / "workspaces" / "workspace_acut" / Path(*parts[3:-1]) / "solver"


def git_diff_paths(workspace: Path | None) -> list[str]:
    if workspace is None or not (workspace / ".git").exists():
        return []
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def kilo_stdout_events(stdout_path: Path | None) -> dict[str, Any]:
    events: list[str] = []
    has_step_finish_stop = False
    if stdout_path is None or not stdout_path.exists():
        return {"last_10_event_types": [], "has_step_finish_stop": False}
    for line in stdout_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type")
        if isinstance(event_type, str):
            events.append(event_type)
        part = event.get("part") if isinstance(event.get("part"), dict) else {}
        if event_type == "step_finish" and part.get("reason") == "stop":
            has_step_finish_stop = True
    return {"last_10_event_types": events[-10:], "has_step_finish_stop": has_step_finish_stop}


def kilo_log_indicators(raw_dir: Path | None) -> dict[str, bool]:
    text = ""
    if raw_dir and raw_dir.exists():
        for path in raw_dir.rglob("data/kilo/log/*.log"):
            text += path.read_text(encoding="utf-8", errors="replace")
    return {
        "has_suggestion_shown": "suggestion.shown" in text,
        "has_session_idle": "session.idle" in text,
    }


def path_is_noneditable(path: str) -> bool:
    return path.startswith("tests/") or "/tests/" in path


def statement_policy_facts(workspace: Path | None, rejected_paths: list[str]) -> dict[str, Any]:
    statement_path = workspace / ".barcarolle" / "statement.md" if workspace else None
    text = statement_path.read_text(encoding="utf-8", errors="replace") if statement_path and statement_path.exists() else ""
    return {
        "statement_found": bool(text),
        "statement_has_editable_paths_section": "## Editable Paths" in text,
        "statement_has_noneditable_paths_section": "## Non-Editable Paths" in text,
        "statement_mentions_rejected_paths": [path for path in rejected_paths if path in text],
        "statement_mentions_tests_path": "tests/" in text or "/tests/" in text,
    }


def diagnose(root: Path) -> dict[str, Any]:
    exp = phase0_root(root)
    score_rows = read_score_table(exp / "results" / f"{BASE_PREFIX}_score_table.csv")
    submissions = {row["run_id"]: row for row in read_jsonl(exp / "results" / f"{BASE_PREFIX}_submissions.jsonl")}
    verifiers = {row["run_id"]: row for row in read_jsonl(exp / "results" / f"{BASE_PREFIX}_verifier_results.jsonl")}
    costs = {row["run_id"]: row for row in read_jsonl(exp / "results" / f"{BASE_PREFIX}_cost_ledger.jsonl")}

    kilo_errors: list[dict[str, Any]] = []
    policy_violations: list[dict[str, Any]] = []

    for score in score_rows:
        run_id = ""
        for candidate, submission in submissions.items():
            if submission.get("adapter_id") == score.get("adapter_id") and submission.get("task_id") == score.get("task_id"):
                run_id = candidate
                break
        submission = submissions.get(run_id, {})
        verifier = verifiers.get(run_id, {})
        cost = costs.get(run_id, {})
        patch_path = raw_path(exp, submission, "patch")
        stdout_path = raw_path(exp, submission, "stdout")
        raw_dir = patch_path.parent if patch_path else None
        workspace = solver_workspace_from_patch(exp, patch_path)

        if score.get("adapter_id") == "kilo_workspace" and score.get("terminal_status") == "acut_harness_error":
            patch_bytes = patch_path.stat().st_size if patch_path and patch_path.exists() else 0
            stdout_facts = kilo_stdout_events(stdout_path)
            log_facts = kilo_log_indicators(raw_dir)
            exit_code = submission.get("acut_exit_code", verifier.get("acut_exit_code"))
            elapsed = cost.get("latency_seconds", submission.get("latency_seconds"))
            adapter_timeout = exit_code == 124 or (isinstance(elapsed, (int, float)) and elapsed >= 899)
            changed = git_diff_paths(workspace)
            if adapter_timeout and patch_bytes > 0:
                classification = "adapter_timeout_nonempty_diff_nonexit"
            elif adapter_timeout:
                classification = "adapter_timeout_empty_or_uncaptured_diff"
            else:
                classification = "non_timeout_acut_harness_error"
            kilo_errors.append(
                {
                    "task_id": score.get("task_id"),
                    "split": score.get("split"),
                    "run_id": run_id,
                    "acut_exit_code": exit_code,
                    "adapter_timeout": adapter_timeout,
                    "elapsed_seconds": elapsed,
                    "submission_patch_non_empty": patch_bytes > 0,
                    "submission_patch_bytes": patch_bytes,
                    "changed_paths_from_solver_workspace": changed,
                    "kilo_stdout_last_10_event_types": stdout_facts["last_10_event_types"],
                    "kilo_stdout_has_step_finish_stop": stdout_facts["has_step_finish_stop"],
                    "kilo_log_has_suggestion_shown": log_facts["has_suggestion_shown"],
                    "kilo_log_has_session_idle": log_facts["has_session_idle"],
                    "classification": classification,
                }
            )

        if score.get("terminal_status") == "policy_violation":
            rejected = list(verifier.get("changed_paths") or [])
            policy_violations.append(
                {
                    "task_id": score.get("task_id"),
                    "split": score.get("split"),
                    "adapter_id": score.get("adapter_id"),
                    "harness_name": score.get("harness_name"),
                    "run_id": run_id,
                    "harness_error": verifier.get("harness_error"),
                    "rejected_paths": rejected,
                    "rejected_path_classes": ["test" if path_is_noneditable(path) else "out_of_scope" for path in rejected],
                    **statement_policy_facts(workspace, rejected),
                }
            )

    kilo_counts = Counter(row["classification"] for row in kilo_errors)
    policy_counts = Counter(row.get("harness_error") or "unknown" for row in policy_violations)
    return {
        "schema_version": "barcarolle.kilo_completion_policy_diagnosis.v1",
        "generated_at": iso_now(),
        "source_result_prefix": BASE_PREFIX,
        "kilo_acut_harness_error_count": len(kilo_errors),
        "kilo_acut_harness_error_classification_counts": dict(sorted(kilo_counts.items())),
        "kilo_acut_harness_errors": kilo_errors,
        "policy_violation_count": len(policy_violations),
        "policy_violation_harness_error_counts": dict(sorted(policy_counts.items())),
        "policy_violations": policy_violations,
        "statement_policy_findings": {
            "policy_rejects_test_edits": True,
            "current_statements_have_explicit_editable_paths_section": all(
                row["statement_has_editable_paths_section"] for row in policy_violations
            )
            if policy_violations
            else False,
            "policy_violations_with_test_path_mentions": sum(1 for row in policy_violations if row["statement_mentions_tests_path"]),
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Kilo Completion And Policy Diagnosis",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "## Kilo Completion",
        "",
        f"- Kilo ACUT harness errors: `{payload['kilo_acut_harness_error_count']}`.",
        f"- Classifications: `{payload['kilo_acut_harness_error_classification_counts']}`.",
        "",
    ]
    for row in payload["kilo_acut_harness_errors"]:
        lines.extend(
            [
                f"- `{row['task_id']}` `{row['split']}`: `{row['classification']}`; "
                f"exit `{row['acut_exit_code']}`, elapsed `{row['elapsed_seconds']}`, "
                f"patch non-empty `{row['submission_patch_non_empty']}`, "
                f"changed paths `{row['changed_paths_from_solver_workspace']}`, "
                f"stdout tail events `{row['kilo_stdout_last_10_event_types']}`, "
                f"log idle `{row['kilo_log_has_session_idle']}`, "
                f"log suggestion `{row['kilo_log_has_suggestion_shown']}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Policy Rejections",
            "",
            f"- Policy violations: `{payload['policy_violation_count']}`.",
            f"- Harness error counts: `{payload['policy_violation_harness_error_counts']}`.",
            "",
        ]
    )
    for row in payload["policy_violations"]:
        lines.append(
            f"- `{row['adapter_id']}` `{row['task_id']}` `{row['split']}`: "
            f"`{row['harness_error']}` rejected `{row['rejected_paths']}`; "
            f"statement mentions rejected paths `{row['statement_mentions_rejected_paths']}`; "
            f"statement mentions tests path `{row['statement_mentions_tests_path']}`; "
            f"editable section `{row['statement_has_editable_paths_section']}`."
        )
    lines.extend(
        [
            "",
            "## Finding",
            "",
            "The Kilo failures are dominated by adapter timeouts with non-empty workspace diffs, not endpoint proof failures. The completed matrix also used solver-visible statements without explicit editable/non-editable sections, while the benchmark policy still rejected test edits and out-of-scope edits.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Kilo completion and policy failures from completed workspace ACUT artifacts.")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    exp = phase0_root(root)
    payload = diagnose(root)
    write_json(exp / "results" / "kilo_completion_policy_diagnosis.json", payload)
    write_text(exp / "reports" / "kilo_completion_policy_diagnosis.md", render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
