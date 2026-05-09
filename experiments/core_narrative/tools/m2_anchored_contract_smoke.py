#!/usr/bin/env python3
"""No-spend M2 anchored-contract scoreability smoke matrix.

This tool exercises the existing anchored-search-replace-json-v3 applicator on
small Click-shaped fixtures. It does not call a model or verifier. Optional
live-smoke evidence can be attached from a separately bounded batch run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json
from _llm_budget import llm_safe_subprocess_env
from run_task import write_safe_patch

import codex_nfl_experiment_runner as batch
import openclaw_direct_runner as direct


TOOL = "m2_anchored_contract_smoke"
CONTRACT = "anchored-search-replace-json-v3"
DEFAULT_RUN_PREFIX = "m2_anchored_contract_smoke_20260509"
DEFAULT_M2_SUMMARY = "experiments/core_narrative/results/m2_scoreability_summary_20260509.json"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2-summary", default=DEFAULT_M2_SUMMARY)
    parser.add_argument("--run-prefix", default=DEFAULT_RUN_PREFIX)
    parser.add_argument("--raw-root", default=str(batch.RAW_ROOT))
    parser.add_argument("--workspace-root", default=str(batch.WORKSPACES_ROOT))
    parser.add_argument("--live-smoke-batch", help="Optional bounded live anchored-contract batch JSON.")
    parser.add_argument("--live-smoke-blocker", help="Optional machine-readable live-smoke blocker JSON.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(list(argv))


def read_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ToolError("JSON root must be an object", path=str(path))
    return data


def count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key)
        label = str(value) if value is not None else "none"
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def fixture_definitions() -> list[dict[str, Any]]:
    repeated_core = (
        "def first():\n"
        "    rv = get_default()\n"
        "\n"
        "def second():\n"
        "    rv = get_default()\n"
    )
    return [
        {
            "fixture_id": "exact_anchored_search_text",
            "intent": "exact immediate anchor isolates repeated Click-shaped old text",
            "files": {"src/click/core.py": repeated_core},
            "context_paths": ["src/click/core.py"],
            "response": {
                "edits": [
                    {
                        "path": "src/click/core.py",
                        "before": "def first():\n",
                        "old": "    rv = get_default()\n",
                        "new": "    rv = get_default(ctx)\n",
                    }
                ]
            },
        },
        {
            "fixture_id": "ambiguous_anchor",
            "intent": "non-isolating immediate anchor is a model-output invalid submission",
            "files": {"src/click/core.py": "SECTION\nVALUE = 1\nSECTION\nVALUE = 1\n"},
            "context_paths": ["src/click/core.py"],
            "response": {
                "edits": [
                    {
                        "path": "src/click/core.py",
                        "before": "SECTION\n",
                        "old": "VALUE = 1\n",
                        "new": "VALUE = 2\n",
                    }
                ]
            },
        },
        {
            "fixture_id": "stale_anchor",
            "intent": "stale anchor beside otherwise unique old text is rejected with hashed diagnostics",
            "files": {"src/click/core.py": "def invoke():\n    value = get_default()\n"},
            "context_paths": ["src/click/core.py"],
            "response": {
                "edits": [
                    {
                        "path": "src/click/core.py",
                        "before": "def stale():\n",
                        "old": "    value = get_default()\n",
                        "new": "    value = get_default(ctx)\n",
                    }
                ]
            },
        },
        {
            "fixture_id": "redacted_source_text",
            "intent": "redacted source text can match raw source, but raw-URL patch artifacts stay blocked",
            "files": {"src/click/core.py": 'DOC = "http' + 's://example.invalid/private"\n'},
            "context_paths": ["src/click/core.py"],
            "response": {
                "edits": [
                    {
                        "path": "src/click/core.py",
                        "old": 'DOC = "<redacted:url>"\n',
                        "new": 'DOC = "offline"\n',
                    }
                ]
            },
        },
        {
            "fixture_id": "missing_raw_artifact",
            "intent": "missing raw response artifact remains machine-readable missing input",
            "files": {"src/click/core.py": "VALUE = 1\n"},
            "context_paths": ["src/click/core.py"],
            "response": None,
            "omit_raw_response_artifact": True,
        },
    ]


def remove_generated_path(path: Path, run_prefix: str, force: bool) -> None:
    if not path.exists():
        return
    if not force:
        raise ToolError("generated path already exists; pass --force to replace", path=str(path))
    if not path.name.startswith(run_prefix):
        raise ToolError("refusing to remove path outside run prefix", path=str(path), run_prefix=run_prefix)
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def run_capture(command: Sequence[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def init_workspace(root: Path, run_prefix: str, fixture: Mapping[str, Any], force: bool) -> Path:
    workspace = root / f"{run_prefix}__fixture__{fixture['fixture_id']}"
    remove_generated_path(workspace, run_prefix, force)
    workspace.mkdir(parents=True, exist_ok=True)
    for relative, text in (fixture.get("files") or {}).items():
        path = workspace / str(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(text), encoding="utf-8")
    run_capture(["git", "init", "-q"], cwd=workspace)
    run_capture(["git", "add", "."], cwd=workspace)
    commit = run_capture(
        ["git", "-c", "user.email=test@example.invalid", "-c", "user.name=Test", "commit", "-qm", "init"],
        cwd=workspace,
    )
    if commit.returncode != 0:
        raise ToolError("fixture workspace commit failed", fixture_id=fixture.get("fixture_id"), stderr=commit.stderr)
    return workspace


def write_fixture_artifacts(
    artifact_dir: Path,
    run_prefix: str,
    fixture: Mapping[str, Any],
    *,
    force: bool,
) -> dict[str, Any]:
    remove_generated_path(artifact_dir, run_prefix, force)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    prompt_snapshot = artifact_dir / "prompt_snapshot.json"
    write_json(
        prompt_snapshot,
        {
            "tool": TOOL,
            "output_contract": CONTRACT,
            "context_files": [{"path": path} for path in fixture.get("context_paths", [])],
            "fixture_id": fixture.get("fixture_id"),
            "content_recorded": False,
        },
    )
    raw_response = artifact_dir / "provider_response.redacted.json"
    if fixture.get("omit_raw_response_artifact") is True:
        return {"prompt_snapshot": str(prompt_snapshot), "raw_response_artifact": None}
    response_text = json.dumps(fixture.get("response"), sort_keys=True)
    write_json(raw_response, {"choices": [{"message": {"content": response_text}}], "usage": {"cost": 0}})
    return {"prompt_snapshot": str(prompt_snapshot), "raw_response_artifact": str(raw_response)}


def provider_text(path: str | None) -> str:
    if not path:
        return ""
    artifact = Path(path)
    if not artifact.exists() or not artifact.is_file():
        return ""
    data = read_json(artifact)
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, Mapping):
            message = first.get("message")
            if isinstance(message, Mapping) and isinstance(message.get("content"), str):
                return str(message["content"])
    return json.dumps(data, sort_keys=True)


def clean_replay_patch(fixture: Mapping[str, Any], patch_path: Path, workspace_root: Path, run_prefix: str, force: bool) -> dict[str, Any]:
    replay_fixture = dict(fixture)
    replay_fixture["fixture_id"] = f"{fixture['fixture_id']}__clean_replay"
    workspace = init_workspace(workspace_root, run_prefix, replay_fixture, force)
    resolved_patch = patch_path.resolve()
    check = run_capture(["git", "apply", "--check", str(resolved_patch)], cwd=workspace)
    if check.returncode != 0:
        return {"attempted": True, "success": False, "status": "git_apply_check_failed"}
    applied = run_capture(["git", "apply", str(resolved_patch)], cwd=workspace)
    return {
        "attempted": True,
        "success": applied.returncode == 0,
        "status": "applied_to_clean_workspace" if applied.returncode == 0 else "git_apply_failed",
        "workspace": str(workspace),
    }


def replay_fixture(
    fixture: Mapping[str, Any],
    *,
    args: argparse.Namespace,
    workspace_root: Path,
    raw_root: Path,
) -> dict[str, Any]:
    artifact_dir = raw_root / f"{args.run_prefix}__fixture__{fixture['fixture_id']}"
    workspace = init_workspace(workspace_root, args.run_prefix, fixture, bool(args.force))
    artifacts = write_fixture_artifacts(artifact_dir, args.run_prefix, fixture, force=bool(args.force))
    raw_response = artifacts.get("raw_response_artifact") if isinstance(artifacts.get("raw_response_artifact"), str) else None
    base = {
        "fixture_id": fixture.get("fixture_id"),
        "intent": fixture.get("intent"),
        "contract": CONTRACT,
        "workspace": str(workspace),
        "artifact_dir": str(artifact_dir),
        "context_paths": list(fixture.get("context_paths", [])),
        "prompt_snapshot": artifacts.get("prompt_snapshot"),
        "raw_response_artifact": raw_response,
        "model_call_made": False,
        "model_spend_usd": 0.0,
    }
    if raw_response is None:
        return {
            **base,
            "status": "missing_replay_input",
            "failure_owner": "infrastructure",
            "failure_class": "missing_raw_response_artifact",
            "patch_ready": False,
            "clean_replay": {"attempted": False, "success": False, "status": "not_attempted_missing_input"},
            "patch": None,
            "patch_artifact": None,
            "details": {"content_recorded": False},
        }

    text = provider_text(raw_response)
    try:
        patch_result = direct.apply_model_response(
            workspace,
            text,
            allowed_paths=list(fixture.get("context_paths", [])),
            output_contract=CONTRACT,
        )
        safe_env, _ = llm_safe_subprocess_env({})
        patch_path = artifact_dir / "submission.patch"
        patch_artifact = write_safe_patch(workspace, patch_path, safe_env)
        if patch_artifact.get("unsafe_content_detected") is True:
            return {
                **base,
                "status": "invalid_submission",
                "failure_owner": "model_output",
                "failure_class": "unsafe_generated_text",
                "patch_ready": False,
                "clean_replay": {"attempted": False, "success": False, "status": "not_attempted_unsafe_patch_artifact"},
                "patch": patch_result,
                "patch_artifact": patch_artifact,
                "details": {
                    "failure_class": "unsafe_generated_text",
                    "unsafe_content": patch_artifact.get("unsafe_content"),
                    "patch_result_before_patch_artifact": patch_result,
                    "content_recorded": False,
                },
            }
        patch_ready = bool(patch_artifact.get("written") and patch_artifact.get("size_bytes", 0) > 0)
        clean_replay = (
            clean_replay_patch(fixture, patch_path, workspace_root, args.run_prefix, bool(args.force))
            if patch_ready
            else {"attempted": False, "success": False, "status": "not_attempted_no_patch"}
        )
        return {
            **base,
            "status": "patch_ready" if patch_ready else "empty_patch",
            "failure_owner": "candidate_patch" if patch_ready else "model_output",
            "failure_class": None if patch_ready else "empty_generated_patch",
            "patch_ready": patch_ready,
            "clean_replay": clean_replay,
            "patch": patch_result,
            "patch_artifact": patch_artifact,
            "details": {"content_recorded": False},
        }
    except ToolError as exc:
        failure_class = exc.details.get("failure_class")
        return {
            **base,
            "status": "invalid_submission",
            "failure_owner": "model_output",
            "failure_class": failure_class if isinstance(failure_class, str) else "anchored_contract_error",
            "patch_ready": False,
            "clean_replay": {"attempted": False, "success": False, "status": "not_attempted_after_invalid_submission"},
            "patch": None,
            "patch_artifact": None,
            "error": str(exc),
            "details": exc.details,
        }


def aggregate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    denominator = len(rows)
    patch_ready_count = sum(1 for row in rows if row.get("patch_ready") is True)
    clean_success = sum(
        1
        for row in rows
        if isinstance(row.get("clean_replay"), Mapping) and row["clean_replay"].get("success") is True
    )
    return {
        "fixed_denominator": denominator,
        "status_counts": count_by(rows, "status"),
        "failure_owner_counts": count_by(rows, "failure_owner"),
        "failure_class_counts": count_by(rows, "failure_class"),
        "patch_ready_count": patch_ready_count,
        "patch_ready_coverage": rate(patch_ready_count, denominator),
        "clean_replay_success_count": clean_success,
        "clean_replay_success_rate": rate(clean_success, denominator),
    }


def diagnostic_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    exact_search_rows = 0
    ambiguous_anchor_rows = 0
    stale_anchor_rows = 0
    redacted_rows = 0
    missing_raw_rows = 0
    source_content_recorded = False
    for row in rows:
        details = row.get("details") if isinstance(row.get("details"), Mapping) else {}
        patch_result = row.get("patch") if isinstance(row.get("patch"), Mapping) else {}
        diagnostics = patch_result.get("edit_diagnostics") if isinstance(patch_result.get("edit_diagnostics"), list) else []
        applied_summaries = (
            patch_result.get("applied_edit_summaries")
            if isinstance(patch_result.get("applied_edit_summaries"), list)
            else []
        )
        if applied_summaries:
            exact_search_rows += 1
            source_content_recorded = source_content_recorded or any(
                isinstance(item, Mapping) and bool(item.get("content_recorded")) for item in applied_summaries
            )
        elif isinstance(details.get("search_text"), Mapping):
            exact_search_rows += 1
            source_content_recorded = source_content_recorded or bool(details.get("search_text", {}).get("content_recorded"))
        if details.get("diagnostic", {}).get("code") == "anchors_do_not_isolate_one_occurrence":
            ambiguous_anchor_rows += 1
        if details.get("diagnostic", {}).get("code") == "unique_old_anchor_mismatch":
            stale_anchor_rows += 1
        if any(
            isinstance(item, Mapping)
            and isinstance(item.get("diagnostic"), Mapping)
            and item["diagnostic"].get("code") == "redacted_source_text_matched_raw_source"
            for item in diagnostics
        ):
            redacted_rows += 1
        if row.get("failure_class") == "missing_raw_response_artifact":
            missing_raw_rows += 1
    return {
        "exact_search_text_diagnostic_rows": exact_search_rows,
        "ambiguous_anchor_diagnostic_rows": ambiguous_anchor_rows,
        "stale_anchor_diagnostic_rows": stale_anchor_rows,
        "redacted_source_text_diagnostic_rows": redacted_rows,
        "missing_raw_artifact_rows": missing_raw_rows,
        "source_content_recorded": source_content_recorded,
    }


def live_smoke_status(args: argparse.Namespace) -> dict[str, Any]:
    if args.live_smoke_batch and args.live_smoke_blocker:
        raise ToolError("choose only one of --live-smoke-batch or --live-smoke-blocker")
    if args.live_smoke_blocker:
        blocker = read_json(args.live_smoke_blocker)
        return {
            "status": "blocked",
            "path": args.live_smoke_blocker,
            "model_call_made": bool(blocker.get("model_call_made")),
            "blockers": blocker.get("blockers") if isinstance(blocker.get("blockers"), list) else [],
            "details": blocker,
        }
    if args.live_smoke_batch:
        batch_payload = read_json(args.live_smoke_batch)
        results = [item for item in batch_payload.get("results", []) if isinstance(item, Mapping)]
        failure_rows: list[dict[str, Any]] = []
        for item in results:
            runner_result = item.get("runner_result") if isinstance(item.get("runner_result"), Mapping) else {}
            details = runner_result.get("details") if isinstance(runner_result.get("details"), Mapping) else {}
            failure_class = item.get("failure_class") or details.get("failure_class")
            failure_owner = item.get("failure_owner")
            if failure_owner is None:
                failure_owner = batch.failure_owner_for_status(
                    item.get("status"),
                    {"failure_owner": failure_owner},
                    runner_result,
                )
            failure_rows.append({"failure_class": failure_class, "failure_owner": failure_owner})
        return {
            "status": "completed",
            "path": args.live_smoke_batch,
            "model_call_made": any(
                isinstance(item.get("runner_result"), Mapping)
                and item["runner_result"].get("model_call_made") is True
                for item in results
            ),
            "total": len(results),
            "status_counts": count_by(results, "status"),
            "failure_class_counts": count_by(failure_rows, "failure_class"),
            "failure_owner_counts": count_by(failure_rows, "failure_owner"),
            "submission_contract": batch_payload.get("submission_contract"),
        }
    return {
        "status": "not_run",
        "model_call_made": False,
        "blockers": ["live_smoke_not_attempted_in_this_artifact_generation"],
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    m2_summary = read_json(args.m2_summary)
    workspace_root = Path(args.workspace_root)
    raw_root = Path(args.raw_root)
    rows = [
        replay_fixture(fixture, args=args, workspace_root=workspace_root, raw_root=raw_root)
        for fixture in fixture_definitions()
    ]
    live_smoke = live_smoke_status(args)
    return {
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "inputs": {
            "m2_summary": args.m2_summary,
            "run_prefix": args.run_prefix,
            "raw_root": args.raw_root,
            "workspace_root": args.workspace_root,
            "live_smoke_batch": args.live_smoke_batch,
            "live_smoke_blocker": args.live_smoke_blocker,
            "force": bool(args.force),
            "output": args.output,
            "report": args.report,
        },
        "scope": {
            "contract": CONTRACT,
            "fixture_fixed_denominator": len(rows),
            "fixture_matrix_row_count": len(rows),
            "prior_m2_fixed_denominator": m2_summary.get("fixed_denominator"),
            "prior_m2_tasks": m2_summary.get("tasks"),
            "prior_m2_acuts": m2_summary.get("acuts"),
            "prior_m2_claim_status": m2_summary.get("claim_status"),
            "denominators_are_separate": True,
        },
        "method": {
            "fixture_model_calls": "none",
            "fixture_model_spend_usd": 0.0,
            "verifier_execution": "not_run",
            "runner_contract_schema": direct.output_contract_schema(CONTRACT),
            "claim_boundary": "anchored contract/applicator scoreability smoke only",
        },
        "fixture_summary": aggregate(rows),
        "diagnostic_summary": diagnostic_summary(rows),
        "matrix": rows,
        "live_smoke": live_smoke,
        "cost_model_call_flags": {
            "fixtures": {
                "model_call_made": False,
                "model_spend_usd": 0.0,
                "live_api_calls": False,
            },
            "live_smoke": {
                "model_call_made": bool(live_smoke.get("model_call_made")),
                "status": live_smoke.get("status"),
            },
        },
        "claim_status": "anchored_contract_smoke_not_m2_pass",
        "claim_boundaries": {
            "m2_passed": False,
            "ranking_reversal": False,
            "task_solving_improvement": False,
            "capability_uplift": False,
            "g_score_predictivity": False,
            "g0_g5": False,
            "license": False,
            "admission": False,
            "authorization": False,
            "verifier_or_task_success_measured": False,
        },
        "prohibited_claims": {
            "m2_passed": False,
            "ranking_reversal": False,
            "task_solving_improvement": False,
            "capability_uplift": False,
            "g_score_predictivity": False,
            "g0_g5": False,
            "license": False,
            "admission": False,
            "authorization": False,
        },
    }


def pct(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:.1f}%"
    return "n/a"


def write_report(payload: Mapping[str, Any], path: str) -> None:
    scope = payload.get("scope") if isinstance(payload.get("scope"), Mapping) else {}
    summary = payload.get("fixture_summary") if isinstance(payload.get("fixture_summary"), Mapping) else {}
    diagnostics = payload.get("diagnostic_summary") if isinstance(payload.get("diagnostic_summary"), Mapping) else {}
    live = payload.get("live_smoke") if isinstance(payload.get("live_smoke"), Mapping) else {}
    inputs = payload.get("inputs") if isinstance(payload.get("inputs"), Mapping) else {}
    lines = [
        "# M2 Anchored Contract Scoreability Smoke",
        "",
        "Date: 2026-05-09",
        "",
        "## Scope",
        "",
        f"- Contract: `{scope.get('contract')}`.",
        f"- Fixture denominator: `{scope.get('fixture_fixed_denominator')}`; prior M2 denominator: `{scope.get('prior_m2_fixed_denominator')}`.",
        "- Fixture replay made no model calls and ran no verifier.",
        "",
        "## Fixture Matrix",
        "",
        "| Fixture | Status | Owner | Class | Patch-ready | Clean replay | Intent |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in payload.get("matrix", []):
        if not isinstance(row, Mapping):
            continue
        clean = row.get("clean_replay") if isinstance(row.get("clean_replay"), Mapping) else {}
        lines.append(
            f"| `{row.get('fixture_id')}` | `{row.get('status')}` | `{row.get('failure_owner')}` | "
            f"`{row.get('failure_class')}` | `{row.get('patch_ready')}` | `{clean.get('status')}` | "
            f"{row.get('intent')} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Patch-ready coverage: {pct(summary.get('patch_ready_coverage'))} (`{summary.get('patch_ready_count')}` of `{summary.get('fixed_denominator')}`).",
            f"- Status counts: `{summary.get('status_counts')}`.",
            f"- Failure classes: `{summary.get('failure_class_counts')}`.",
            "",
            "## Diagnostics",
            "",
            f"- Exact search-text diagnostic rows: `{diagnostics.get('exact_search_text_diagnostic_rows')}`.",
            f"- Ambiguous-anchor diagnostic rows: `{diagnostics.get('ambiguous_anchor_diagnostic_rows')}`.",
            f"- Stale-anchor diagnostic rows: `{diagnostics.get('stale_anchor_diagnostic_rows')}`.",
            f"- Redacted-source diagnostic rows: `{diagnostics.get('redacted_source_text_diagnostic_rows')}`.",
            f"- Missing raw artifact rows: `{diagnostics.get('missing_raw_artifact_rows')}`.",
            f"- Source content recorded in diagnostics: `{diagnostics.get('source_content_recorded')}`.",
            "",
            "## Live Smoke",
            "",
            f"Status: `{live.get('status')}`. Model call made: `{live.get('model_call_made')}`. "
            f"Total cells: `{live.get('total')}`. Status counts: `{live.get('status_counts')}`. "
            f"Failure classes: `{live.get('failure_class_counts')}`. "
            f"Contract: `{live.get('submission_contract')}`.",
            "",
            "## Reproduction",
            "",
            "```bash",
            "PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_anchored_contract_smoke.py \\",
            f"  --m2-summary {inputs.get('m2_summary')} \\",
            f"  --run-prefix {inputs.get('run_prefix')} \\",
            f"  --raw-root {inputs.get('raw_root')} \\",
            f"  --workspace-root {inputs.get('workspace_root')} \\",
            *(
                [f"  --live-smoke-batch {inputs.get('live_smoke_batch')} \\"]
                if inputs.get("live_smoke_batch")
                else []
            ),
            *(
                [f"  --live-smoke-blocker {inputs.get('live_smoke_blocker')} \\"]
                if inputs.get("live_smoke_blocker")
                else []
            ),
            "  --force \\",
            f"  --output {inputs.get('output')} \\",
            f"  --report {inputs.get('report')}",
            "```",
            "",
            "## Claim Boundaries",
            "",
            "This report does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization. It only reports anchored-contract parser/applicator scoreability evidence and the separately attached bounded live-smoke status.",
        ]
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_payload(args)
        emit_json(payload, args.output)
        write_report(payload, args.report)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
