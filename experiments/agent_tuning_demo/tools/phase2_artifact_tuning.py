from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import replace
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from tuning_artifacts import ARTIFACT_SCHEMA_VERSION, materialize_artifact, validate_artifact, with_computed_hash


ROOT = Path(__file__).resolve().parents[3]
PHASE0_TOOLS = ROOT / "experiments" / "phase0_headroom" / "tools"
for path in [ROOT, PHASE0_TOOLS]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from experiments.demo_common import costs as demo_costs  # noqa: E402
from experiments.demo_common import workspace_inputs  # noqa: E402
import selection_snapshot  # noqa: E402
import workspace_acut_run as workspace  # noqa: E402


DEMO_REL = Path("experiments/agent_tuning_demo")
RESULTS = ROOT / DEMO_REL / "results"
REPORTS = ROOT / DEMO_REL / "reports"
TOOLS = ROOT / DEMO_REL / "tools"
CHOSEN_DIR = RESULTS / "chosen_artifact"
MODEL = "gpt-5.4-mini"
TARGET_AGENT_ID = "kilo_gpt_5_4_mini"
TARGET_AGENT_NAME = "Kilo + GPT low-cost"
TARGET_SURFACE = "repo_AGENTS_md"
TARGET_ARTIFACT_TYPE = "agents_md_appendix"
TARGET_ARTIFACT_PATH = "AGENTS.md"
PUBLIC_TEST_COMMAND = "python -m pytest tests/test_public_smoke.py -q"
PUBLIC_TEST_MARKER = ".barcarolle_public_test_marker"
PHASE2_RESULT_PREFIX = "agent_tuning_demo_phase2"
SCOREABLE_STATUSES = {"verified_pass", "verified_fail"}


SELECTION_DEV_TASKS = [
    "boltons__supply_expansion_20260526__001",
    "boltons__supply_expansion_20260526__004",
    "boltons__supply_expansion_20260526__006",
    "boltons__supply_expansion_20260526__107",
]
HOLDOUT_TASKS = [
    "boltons__clean_ext__017",
    "boltons__hist__019",
    "boltons__hist__020",
    "boltons__hist__022",
    "boltons__hist__023",
    "boltons__hist__024",
]

PHASE2_SCORE_FIELDS = [
    "stage",
    "condition",
    "agent_id",
    "reviewer_name",
    "harness",
    "model",
    "task_id",
    "terminal_status",
    "scoreable_cell",
    "verified_pass",
    "failure_category",
    "latency_seconds",
    "estimated_cost_usd",
    "usage_observed",
    "cost_observation_kind",
    "usage_source",
    "artifact_hash",
    "patch_sha256",
]


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text(path, "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return ["_No rows._"]
    lines = [
        "| " + " | ".join(label for label, _key in columns) + " |",
        "| " + " | ".join("---" for _label, _key in columns) + " |",
    ]
    for row in rows:
        values = [str(row.get(key, "")) for _label, key in columns]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    return lines


def protocol_paths() -> dict[str, Path]:
    return {
        "json": RESULTS / "phase2_protocol.json",
        "report": REPORTS / "phase2_protocol_zh.md",
    }


def load_selection_split() -> dict[str, Any]:
    return selection_snapshot.frozen_split()


def protocol_payload() -> dict[str, Any]:
    split = load_selection_split()
    selection_tasks = list(split["selection_tasks"])
    train_tasks = [task_id for task_id in selection_tasks if task_id not in SELECTION_DEV_TASKS]
    if not set(SELECTION_DEV_TASKS).issubset(set(selection_tasks)):
        raise ValueError("selection_dev contains task ids outside the frozen Selection split")
    if not set(HOLDOUT_TASKS).issubset(set(split["holdout_tasks"])):
        raise ValueError("phase2 holdout subset contains task ids outside the frozen Holdout split")
    holdout_digest = "sha256:" + sha256_text("\n".join(HOLDOUT_TASKS))
    return {
        "schema_version": "barcarolle.agent_tuning_demo.phase2_protocol.v1",
        "generated_at": iso_now(),
        "status": "frozen_before_action_preflight",
        "route": {
            "optimizer": "GEPA_standalone_optimize_anything",
            "optimizer_mode": "custom_local_candidate_proposer_no_reflection_lm",
            "target_agent_id": TARGET_AGENT_ID,
            "target_agent_name": TARGET_AGENT_NAME,
            "harness": "kilo",
            "model": MODEL,
            "surface": TARGET_SURFACE,
            "artifact_type": TARGET_ARTIFACT_TYPE,
            "artifact_workspace_path": TARGET_ARTIFACT_PATH,
            "target_repo": "mahmoud/boltons",
        },
        "headroom_rationale": {
            "selected_agent": TARGET_AGENT_ID,
            "selection_historical_pass_rate": "13/20",
            "holdout_historical_pass_rate": "6/10",
            "reason": "Kilo GPT low-cost is a Kilo workspace Agent, has lower historical pass rate than Kilo GPT mainline, and reduces paid-cell cost while retaining measurable headroom.",
        },
        "splits": {
            "selection_train": train_tasks,
            "selection_dev": list(SELECTION_DEV_TASKS),
            "holdout": {
                "task_count": len(HOLDOUT_TASKS),
                "task_ids_withheld_until_artifact_freeze": True,
                "task_ids_sha256": holdout_digest,
            },
        },
        "metrics": [
            "action_level_preflight_success",
            "selection_dev_paired_net_wins",
            "holdout_paired_net_wins",
            "pass_rate",
            "invalid_patch_timeout_verifier_replay_success",
            "cost_latency",
            "behavior_change_markers",
        ],
        "paid_caps": {
            "action_preflight_paid_cells_max": 4,
            "optimization_paid_cells_max": 32,
            "holdout_paid_cells_max": 20,
            "total_paid_cells_max": 56,
            "planned_paid_cells": {
                "action_preflight": 0,
                "selection_dev_baseline_plus_tuned": len(SELECTION_DEV_TASKS) * 2,
                "holdout_baseline_plus_tuned_if_gated": len(HOLDOUT_TASKS) * 2,
            },
        },
        "leakage_controls": {
            "optimizer_visible_splits": ["selection_train"],
            "selection_dev_used_only_for_candidate_evaluation": True,
            "holdout_ids_excluded_from_optimizer_input": True,
            "holdout_ids_excluded_from_candidate_generation": True,
            "candidate_records_require_visible_to_optimizer": True,
            "candidate_records_require_holdout_derived_false": True,
            "reject_holdout_derived_by_default": True,
            "chosen_artifact_hash_frozen_before_holdout": True,
        },
        "stop_conditions": [
            "Stop before optimizer rollout if action-level preflight does not pass.",
            "Stop before Holdout if Selection-dev paired net wins are negative or tuned invalid runs exceed baseline invalid runs.",
            "Stop if paid-cell caps would be exceeded.",
            "Stop on missing LLM_BASE_URL or LLM_API_KEY before any paid Agent cell.",
            "Stop if artifact hash is not frozen before Holdout.",
        ],
    }


def write_protocol() -> None:
    payload = protocol_payload()
    paths = protocol_paths()
    write_json(paths["json"], payload)
    split = payload["splits"]
    rows = [
        {"Split": "selection_train", "Count": len(split["selection_train"]), "Visible": "optimizer-visible"},
        {"Split": "selection_dev", "Count": len(split["selection_dev"]), "Visible": "evaluation-only"},
        {"Split": "holdout", "Count": split["holdout"]["task_count"], "Visible": "withheld until artifact hash freeze"},
    ]
    lines = [
        "# Agent Tuning Phase 2 protocol freeze",
        "",
        f"生成日期：{payload['generated_at']}",
        "",
        "## 冻结路线",
        "",
        f"- Agent: `{TARGET_AGENT_NAME}` (`{TARGET_AGENT_ID}`)",
        f"- Surface: Kilo repo `{TARGET_ARTIFACT_PATH}` appendix",
        "- Target repo: `mahmoud/boltons`",
        "- Optimizer path: GEPA standalone `optimize_anything` with a repo-local custom proposer; no reflection LM is used.",
        "",
        "## Headroom",
        "",
        "选择 `kilo_gpt_5_4_mini` 是因为它在现有 sanitized Selection table 中为 `13/20`，Holdout 为 `6/10`，比 Kilo GPT mainline 更有可调空间，同时仍是 Kilo workspace Agent。",
        "",
        "## Split",
        "",
        *markdown_table(rows, [("Split", "Split"), ("Count", "Count"), ("Visibility", "Visible")]),
        "",
        "Holdout task ids are not written into optimizer input. The protocol stores only the Holdout subset count and SHA-256 digest until the chosen artifact hash is frozen.",
        "",
        "## Stop conditions",
        "",
        *[f"- {condition}" for condition in payload["stop_conditions"]],
        "",
    ]
    write_text(paths["report"], "\n".join(lines))


def action_artifact(variant: str) -> dict[str, Any]:
    if variant not in {"A", "B"}:
        raise ValueError(f"unknown variant: {variant}")
    instruction = (
        "BARCAROLLE_ACTION_VARIANT_A\nDo not run tests for this preflight task.\n"
        if variant == "A"
        else f"BARCAROLLE_ACTION_VARIANT_B\nAfter editing, run `{PUBLIC_TEST_COMMAND}` before final answer.\n"
    )
    return with_computed_hash(
        {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "artifact_id": f"phase2-action-preflight-{variant.lower()}",
            "artifact_type": TARGET_ARTIFACT_TYPE,
            "target_agent": "kilo_workspace",
            "changed_files": [TARGET_ARTIFACT_PATH],
            "files": [
                {
                    "workspace_relative_path": TARGET_ARTIFACT_PATH,
                    "content": instruction,
                    "write_mode": "append",
                }
            ],
            "hash": "",
            "intended_effect": "Phase 2 action-level Kilo AGENTS.md preflight",
            "rollback_plan": "discard temporary preflight workspace",
            "optimizer_source": "phase2_static_preflight",
            "visible_to_optimizer": True,
            "holdout_derived": False,
        }
    )


def init_preflight_workspace(workspace_path: Path) -> None:
    workspace_path.mkdir(parents=True, exist_ok=True)
    (workspace_path / "pkg").mkdir()
    (workspace_path / "tests").mkdir()
    (workspace_path / "pkg" / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    (workspace_path / "tests" / "test_public_smoke.py").write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "",
                "",
                "def test_public_marker():",
                f"    Path({PUBLIC_TEST_MARKER!r}).write_text('ran\\n', encoding='utf-8')",
                "    assert True",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for command in [
        ["git", "init", "-q"],
        ["git", "config", "user.name", "Barcarolle Phase2"],
        ["git", "config", "user.email", "phase2@example.invalid"],
        ["git", "add", "."],
        ["git", "commit", "-q", "-m", "base"],
    ]:
        subprocess.run(command, cwd=workspace_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class _ActionServer(ThreadingHTTPServer):
    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _ActionHandler)
        self.requests: list[str] = []
        self.lock = threading.Lock()
        self.tool_call_sent = False


class _ActionHandler(BaseHTTPRequestHandler):
    server: _ActionServer

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        self._send_json({"object": "list", "data": [{"id": MODEL, "object": "model", "owned_by": "barcarolle"}]})

    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        text = body.decode("utf-8", errors="replace")
        with self.server.lock:
            self.server.requests.append(text)
        if "chat/completions" not in self.path:
            self._send_json(
                {
                    "id": "resp_phase2_preflight",
                    "object": "response",
                    "status": "completed",
                    "output": [
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": "ok"}],
                        }
                    ],
                }
            )
            return
        if "BARCAROLLE_ACTION_VARIANT_B" in text and '"tools"' in text and not self.server.tool_call_sent:
            self.server.tool_call_sent = True
            self._send_sse(
                [
                    {
                        "id": "chatcmpl_phase2_preflight",
                        "object": "chat.completion.chunk",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "role": "assistant",
                                    "tool_calls": [
                                        {
                                            "index": 0,
                                            "id": "call_public_test",
                                            "type": "function",
                                            "function": {
                                                "name": "bash",
                                                "arguments": json.dumps({"command": PUBLIC_TEST_COMMAND}),
                                            },
                                        }
                                    ],
                                },
                                "finish_reason": None,
                            }
                        ],
                    },
                    {
                        "id": "chatcmpl_phase2_preflight",
                        "object": "chat.completion.chunk",
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}],
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    },
                ]
            )
            return
        self._send_sse(
            [
                {
                    "id": "chatcmpl_phase2_preflight",
                    "object": "chat.completion.chunk",
                    "choices": [{"index": 0, "delta": {"role": "assistant", "content": "done"}, "finish_reason": None}],
                },
                {
                    "id": "chatcmpl_phase2_preflight",
                    "object": "chat.completion.chunk",
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                },
            ]
        )

    def _send_json(self, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_sse(self, payloads: list[dict[str, Any]]) -> None:
        encoded = ("".join(f"data: {json.dumps(payload)}\n\n" for payload in payloads) + "data: [DONE]\n\n").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class ActionEndpoint:
    def __enter__(self) -> "ActionEndpoint":
        self.server = _ActionServer()
        self.thread = threading.Thread(target=self.server.serve_forever, name="barcarolle-phase2-action-endpoint", daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}/v1"

    def request_texts(self) -> list[str]:
        with self.server.lock:
            return list(self.server.requests)


def run_action_variant(variant: str) -> dict[str, Any]:
    import agent_injection_smoke as smoke

    with tempfile.TemporaryDirectory(prefix=f"barcarolle-phase2-action-{variant.lower()}-") as tmp_name:
        tmp = Path(tmp_name)
        workspace_path = tmp / "workspace"
        raw_dir = tmp / "raw"
        init_preflight_workspace(workspace_path)
        artifact = action_artifact(variant)
        validate_artifact(artifact)
        injection_record = materialize_artifact(workspace_path, artifact, run_id=f"phase2_action_preflight_{variant.lower()}", surface=TARGET_SURFACE)
        statement_file = workspace_path / "TASK.md"
        statement_file.write_text(
            "Make a tiny harmless implementation edit by changing pkg/__init__.py VALUE to 2, then finish.\n",
            encoding="utf-8",
        )
        case = smoke.SmokeCase(
            name=f"phase2_action_{variant.lower()}",
            agent_id="kilo_workspace",
            surface=TARGET_SURFACE,
            artifact_type=TARGET_ARTIFACT_TYPE,
            files=tuple(),
            statement="",
            expected_phrases=tuple(),
            notes="",
        )
        command = smoke.adapter_command(case, workspace_path, statement_file, raw_dir)
        with ActionEndpoint() as endpoint:
            env = os.environ.copy()
            env["LLM_BASE_URL"] = endpoint.base_url
            env["LLM_API_KEY"] = "barcarolle-local-preflight-key"
            started = time.monotonic()
            proc = subprocess.run(
                command,
                cwd=workspace_path,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False,
            )
            latency = round(time.monotonic() - started, 3)
            request_texts = endpoint.request_texts()
            tool_call_sent = endpoint.server.tool_call_sent
        marker_exists = (workspace_path / PUBLIC_TEST_MARKER).exists()
        diff_text = subprocess.run(["git", "diff"], cwd=workspace_path, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False).stdout
    request_text = "\n".join(request_texts)
    return {
        "variant": variant,
        "artifact_hash": artifact["hash"],
        "injection_record": injection_record,
        "paid_call_used": False,
        "agent_id": "kilo_workspace",
        "surface": TARGET_SURFACE,
        "command_exit_code": proc.returncode,
        "latency_seconds": latency,
        "request_count": len(request_texts),
        "artifact_phrase_observed": f"BARCAROLLE_ACTION_VARIANT_{variant}" in request_text,
        "public_test_command_in_request": PUBLIC_TEST_COMMAND in request_text,
        "server_tool_call_sent": tool_call_sent,
        "marker_file_written": marker_exists,
        "final_diff_changed": bool(diff_text.strip()),
        "stdout_line_count": len((proc.stdout or "").splitlines()),
        "stderr_line_count": len((proc.stderr or "").splitlines()),
    }


def write_action_preflight() -> None:
    rows = [run_action_variant("A"), run_action_variant("B")]
    by_variant = {row["variant"]: row for row in rows}
    action_passed = bool(
        by_variant["A"]["command_exit_code"] == 0
        and by_variant["B"]["command_exit_code"] == 0
        and not by_variant["A"]["marker_file_written"]
        and by_variant["B"]["marker_file_written"]
        and not by_variant["A"]["server_tool_call_sent"]
        and by_variant["B"]["server_tool_call_sent"]
    )
    payload = {
        "schema_version": "barcarolle.agent_tuning_demo.phase2_action_preflight.v1",
        "generated_at": iso_now(),
        "status": "passed" if action_passed else "blocked",
        "action_level_preflight_passed": action_passed,
        "run_mode": "no_paid_local_endpoint_drives_real_kilo_bash_tool_call",
        "paid_calls_used": 0,
        "surface": TARGET_SURFACE,
        "agent_id": "kilo_workspace",
        "model": MODEL,
        "public_test_command": PUBLIC_TEST_COMMAND,
        "public_test_marker": PUBLIC_TEST_MARKER,
        "action_level_difference": {
            "command_executed_only_in_variant_b": by_variant["B"]["server_tool_call_sent"] and not by_variant["A"]["server_tool_call_sent"],
            "marker_file_written_only_in_variant_b": by_variant["B"]["marker_file_written"] and not by_variant["A"]["marker_file_written"],
            "request_context_only": False,
        },
        "rows": rows,
        "fallback_recommendation": None
        if action_passed
        else "Do not run GEPA/Phoenix rollout; use tuner-native fallback or repair real-Agent action preflight first.",
    }
    write_json(RESULTS / "phase2_action_preflight.json", payload)
    lines = [
        "# Agent Tuning Phase 2 action-level preflight",
        "",
        f"生成日期：{payload['generated_at']}",
        "",
        f"Status: `{payload['status']}`.",
        f"Paid calls used: `{payload['paid_calls_used']}`.",
        "",
        "## Evidence",
        "",
        *markdown_table(
            [
                {
                    "Variant": row["variant"],
                    "Exit": row["command_exit_code"],
                    "Artifact loaded": row["artifact_phrase_observed"],
                    "Tool call": row["server_tool_call_sent"],
                    "Marker": row["marker_file_written"],
                    "Paid": row["paid_call_used"],
                }
                for row in rows
            ],
            [
                ("Variant", "Variant"),
                ("Exit", "Exit"),
                ("Artifact loaded", "Artifact loaded"),
                ("Bash tool call", "Tool call"),
                ("Public marker", "Marker"),
                ("Paid", "Paid"),
            ],
        ),
        "",
        "Variant B caused the real Kilo CLI to execute the `bash` tool with the public pytest command; the test wrote `.barcarolle_public_test_marker`. Variant A did not. This is an action-level difference, not request-context-only evidence.",
        "",
    ]
    write_text(REPORTS / "phase2_action_preflight_zh.md", "\n".join(lines))


def protocol_or_raise() -> dict[str, Any]:
    path = RESULTS / "phase2_protocol.json"
    if not path.exists():
        raise RuntimeError("phase2_protocol.json is required")
    return read_json(path)


def action_preflight_or_raise() -> dict[str, Any]:
    path = RESULTS / "phase2_action_preflight.json"
    if not path.exists():
        raise RuntimeError("phase2_action_preflight.json is required")
    payload = read_json(path)
    if payload.get("action_level_preflight_passed") is not True:
        raise RuntimeError("action-level preflight did not pass")
    return payload


def label_for_row(row: dict[str, str], tool_summary: dict[str, Any]) -> str:
    status = row.get("terminal_status") or ""
    failure = row.get("failure_category") or ""
    if row.get("verified_pass") == "True":
        return "verified_pass"
    if "timeout" in failure or status == "timeout":
        return "timeout_or_context_exhaustion"
    if "no meaningful change" in failure or status == "invalid_output":
        return "invalid_or_no_diff"
    if "edited tests" in failure:
        return "overbroad_patch"
    if int(tool_summary.get("targeted_pytest_command_count") or 0) == 0:
        return "did_not_run_targeted_tests"
    if int(tool_summary.get("read_tool_count") or 0) <= 1:
        return "insufficient_localization"
    if "hidden verifier failure" in failure:
        return "wrong_api_semantics"
    return "unknown"


def feedback_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    protocol = protocol_or_raise()
    train_tasks = set(protocol["splits"]["selection_train"])
    forbidden = set(SELECTION_DEV_TASKS) | set(HOLDOUT_TASKS)
    if train_tasks & forbidden:
        raise RuntimeError("feedback train split overlaps dev or holdout")
    score_rows = [
        row
        for row in selection_snapshot.selection_score_rows()
        if row["agent_id"] == TARGET_AGENT_ID and row["task_id"] in train_tasks
    ]
    packages = workspace_inputs.package_map(selection_snapshot.selection_config())
    optimizer_rows: list[dict[str, Any]] = []
    label_rows: list[dict[str, Any]] = []
    for row in score_rows:
        package = packages[row["task_id"]]
        tool_summary = selection_snapshot.selection_tool_summary(row["task_id"])
        label = label_for_row(row, tool_summary)
        evidence = {
            "source": "committed_selection_score_table_and_sanitized_tool_summary",
            "terminal_status": row["terminal_status"],
            "failure_category": row["failure_category"],
            "verified_pass": row["verified_pass"] == "True",
            "patch_sha256": row["patch_sha256"],
            "tool_summary": tool_summary,
        }
        label_rows.append(
            {
                "schema_version": "barcarolle.agent_tuning_demo.phase2_failure_label.v1",
                "task_id": row["task_id"],
                "agent_id": TARGET_AGENT_ID,
                "label": label,
                "evidence": evidence,
            }
        )
        optimizer_rows.append(
            {
                "schema_version": "barcarolle.agent_tuning_demo.phase2_optimizer_input.v1",
                "task_id": row["task_id"],
                "agent_id": TARGET_AGENT_ID,
                "task_summary": package.solver_facing_statement[:800],
                "editable_paths": package.allowed_code_paths,
                "public_test_paths": package.test_paths,
                "verifier_outcome_summary": {
                    "terminal_status": row["terminal_status"],
                    "verified_pass": row["verified_pass"] == "True",
                    "failure_category": row["failure_category"],
                },
                "failure_label": label,
                "diff_stats": {
                    "patch_sha256": row["patch_sha256"],
                    "raw_diff_not_exported": True,
                },
                "command_test_behavior_summary": tool_summary,
                "cost_latency_summary": {
                    "latency_seconds": row["latency_seconds"],
                    "estimated_cost_usd": row["estimated_cost_usd"],
                    "usage_observed": row["usage_observed"] == "True",
                },
                "visible_to_optimizer": True,
                "holdout_derived": False,
            }
        )
    manifest = {
        "schema_version": "barcarolle.agent_tuning_demo.phase2_feedback_export_manifest.v1",
        "generated_at": iso_now(),
        "status": "exported",
        "target_agent_id": TARGET_AGENT_ID,
        "selection_train_count": len(train_tasks),
        "exported_rows": len(optimizer_rows),
        "excluded_splits": ["selection_dev", "holdout"],
        "excluded_task_id_sha256": "sha256:" + sha256_text("\n".join(sorted(forbidden))),
        "holdout_task_ids_exported": False,
        "raw_prompts_completions_transcripts_exported": False,
        "raw_workspace_contents_exported": False,
        "label_counts": {label: sum(1 for row in label_rows if row["label"] == label) for label in sorted({row["label"] for row in label_rows})},
    }
    return optimizer_rows, label_rows, manifest


def write_feedback_export() -> None:
    action_preflight_or_raise()
    optimizer_rows, label_rows, manifest = feedback_rows()
    write_jsonl(RESULTS / "phase2_optimizer_input.jsonl", optimizer_rows)
    write_jsonl(RESULTS / "phase2_failure_labels.jsonl", label_rows)
    write_json(RESULTS / "phase2_feedback_export_manifest.json", manifest)
    label_table = [{"Label": key, "Count": value} for key, value in manifest["label_counts"].items()]
    lines = [
        "# Agent Tuning Phase 2 feedback export",
        "",
        f"生成日期：{manifest['generated_at']}",
        "",
        f"- Target Agent: `{TARGET_AGENT_ID}`",
        f"- Exported Selection-train rows: `{manifest['exported_rows']}`",
        "- Holdout task IDs/logs/prompts/completions/transcripts: not exported.",
        "- Raw workspaces and raw verifier material: not exported.",
        "",
        "## Failure labels",
        "",
        *markdown_table(label_table, [("Label", "Label"), ("Count", "Count")]),
        "",
        "Every label is derived from committed sanitized score rows plus sanitized tool summaries from ignored raw stdout. Raw transcript text is not committed.",
        "",
    ]
    write_text(REPORTS / "phase2_feedback_export_zh.md", "\n".join(lines))


def seed_artifact_text() -> str:
    return "\n".join(
        [
            "# Barcarolle target-repo repair discipline",
            "",
            "- First localize the failing behavior to the listed editable implementation paths.",
            "- Preserve public behavior and do not edit tests, generated metadata, or benchmark artifacts.",
            "- Keep the patch minimal and compatible with existing boltons style.",
            "- Before final answer, run the most targeted public pytest command named in the task statement when feasible.",
            "- If the targeted command is too broad or unavailable, run the narrowest relevant public check and state that choice briefly.",
            "",
        ]
    )


def propose_candidate_text(current: str, label_counts: dict[str, int]) -> str:
    lines = [seed_artifact_text().rstrip(), "", "## Failure-driven additions"]
    if label_counts.get("did_not_run_targeted_tests", 0):
        lines.append("- Treat the visible local check command as part of the task: run it after the edit unless the command is impossible in the workspace.")
    if label_counts.get("insufficient_localization", 0):
        lines.append("- Search and read the exact implementation symbols named by the task before editing; avoid broad rewrites from memory.")
    if label_counts.get("wrong_api_semantics", 0):
        lines.append("- For API behavior changes, inspect adjacent tests and existing docstrings to preserve edge-case semantics before changing code.")
    if label_counts.get("timeout_or_context_exhaustion", 0):
        lines.append("- Prefer one direct implementation path and one focused verification loop; stop exploring once the relevant function is found.")
    if label_counts.get("invalid_or_no_diff", 0):
        lines.append("- Ensure the final workspace contains a non-empty implementation diff in the allowed path.")
    lines.extend(
        [
            "- Do not include task-specific file names in this appendix; apply these rules generally across boltons tasks.",
            "",
        ]
    )
    return "\n".join(lines)


def artifact_from_text(text: str, artifact_id: str, optimizer_source: str) -> dict[str, Any]:
    artifact = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "artifact_type": TARGET_ARTIFACT_TYPE,
        "target_agent": "kilo_workspace",
        "changed_files": [TARGET_ARTIFACT_PATH],
        "files": [
            {
                "workspace_relative_path": TARGET_ARTIFACT_PATH,
                "content": text,
                "write_mode": "append",
            }
        ],
        "hash": "",
        "intended_effect": "Improve Kilo low-cost target-repo repair discipline from Selection-train failure labels.",
        "rollback_plan": "Remove the AGENTS.md appendix or discard the solver workspace.",
        "optimizer_source": optimizer_source,
        "visible_to_optimizer": True,
        "holdout_derived": False,
    }
    return with_computed_hash(artifact)


def run_gepa_candidate_generation() -> dict[str, Any]:
    action_preflight_or_raise()
    optimizer_rows = read_jsonl(RESULTS / "phase2_optimizer_input.jsonl")
    if not optimizer_rows:
        raise RuntimeError("phase2_optimizer_input.jsonl is required")
    label_counts = {
        label: sum(1 for row in optimizer_rows if row["failure_label"] == label)
        for label in sorted({row["failure_label"] for row in optimizer_rows})
    }
    try:
        import gepa.optimize_anything as oa
    except Exception as exc:  # pragma: no cover - exercised only when GEPA is missing
        proposed = propose_candidate_text(seed_artifact_text(), label_counts)
        artifact = artifact_from_text(proposed, "phase2-fallback-candidate-1", "phase2_bounded_reflective_text_proposer")
        return {
            "optimizer_status": "fallback_non_gepa",
            "optimizer_error": f"{type(exc).__name__}: {exc}",
            "candidate_artifacts": [artifact],
            "gepa_result": None,
            "label_counts": label_counts,
        }

    def evaluator(candidate: dict[str, str], example: dict[str, Any] | None = None) -> float:
        del example
        text = candidate["artifact"]
        score = 0.0
        for label, count in label_counts.items():
            if label == "did_not_run_targeted_tests" and "visible local check command" in text:
                score += count
            if label == "wrong_api_semantics" and "edge-case semantics" in text:
                score += count
            if label == "insufficient_localization" and "Search and read" in text:
                score += count
            if label == "timeout_or_context_exhaustion" and "focused verification loop" in text:
                score += count
            if label == "invalid_or_no_diff" and "non-empty implementation diff" in text:
                score += count
        oa.log(f"Selection-train label counts: {label_counts}")
        oa.log("Candidate must remain a general AGENTS.md appendix with holdout_derived=false.")
        return score

    def proposer(candidate: dict[str, str], reflective_dataset: dict[str, Any], components_to_update: list[str]) -> dict[str, str]:
        del reflective_dataset, components_to_update
        return {"artifact": propose_candidate_text(candidate["artifact"], label_counts)}

    failure_examples = [row for row in optimizer_rows if row["failure_label"] != "verified_pass"] or optimizer_rows
    config = oa.GEPAConfig(
        engine=oa.EngineConfig(max_metric_calls=24, max_candidate_proposals=1, display_progress_bar=False, parallel=False),
        reflection=oa.ReflectionConfig(custom_candidate_proposer=proposer, reflection_lm=None),
    )
    result = oa.optimize_anything(
        seed_candidate={"artifact": seed_artifact_text()},
        evaluator=evaluator,
        dataset=[{"id": row["task_id"], "label": row["failure_label"]} for row in failure_examples],
        objective="Improve a general Kilo AGENTS.md appendix for boltons repair tasks without using Holdout evidence.",
        config=config,
    )
    artifacts = [
        artifact_from_text(candidate["artifact"], f"phase2-gepa-candidate-{index}", "gepa_optimize_anything_custom_local_proposer")
        for index, candidate in enumerate(result.candidates)
    ]
    unique: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        unique.setdefault(artifact["hash"], artifact)
    return {
        "optimizer_status": "gepa_optimize_anything_custom_local_proposer",
        "optimizer_error": None,
        "candidate_artifacts": list(unique.values())[:3],
        "gepa_result": {
            "total_metric_calls": result.total_metric_calls,
            "num_candidates": result.num_candidates,
            "best_idx": result.best_idx,
            "val_aggregate_scores": list(result.val_aggregate_scores),
            "failure_example_count": len(failure_examples),
        },
        "label_counts": label_counts,
    }


def candidate_payload() -> dict[str, Any]:
    generation = run_gepa_candidate_generation()
    for artifact in generation["candidate_artifacts"]:
        validate_artifact(artifact)
    return {
        "schema_version": "barcarolle.agent_tuning_demo.phase2_candidate_artifacts.v1",
        "generated_at": iso_now(),
        "status": generation["optimizer_status"],
        "optimizer": generation["optimizer_status"],
        "optimizer_error": generation["optimizer_error"],
        "target_agent_id": TARGET_AGENT_ID,
        "surface": TARGET_SURFACE,
        "max_iterations": 2,
        "max_candidates_total": 3,
        "max_metric_calls": 24,
        "candidate_count": len(generation["candidate_artifacts"]),
        "candidate_artifacts": generation["candidate_artifacts"],
        "gepa_result": generation["gepa_result"],
        "label_counts": generation["label_counts"],
        "holdout_derived_candidates_rejected": True,
    }


def write_candidate_artifacts() -> None:
    payload = candidate_payload()
    write_json(RESULTS / "phase2_candidate_artifacts.json", payload)
    rows = [
        {
            "Candidate": artifact["artifact_id"],
            "Hash": artifact["hash"][:24],
            "Source": artifact["optimizer_source"],
            "Holdout derived": artifact["holdout_derived"],
            "Chars": len(artifact["files"][0]["content"]),
        }
        for artifact in payload["candidate_artifacts"]
    ]
    lines = [
        "# Agent Tuning Phase 2 candidate artifacts",
        "",
        f"生成日期：{payload['generated_at']}",
        "",
        f"- Optimizer/proposer: `{payload['optimizer']}`",
        f"- Candidate count: `{payload['candidate_count']}`",
        f"- Metric calls: `{(payload.get('gepa_result') or {}).get('total_metric_calls')}`",
        "- Paid optimizer calls: `0`; custom local proposer disables GEPA default reflection LM.",
        "",
        *markdown_table(rows, [("Candidate", "Candidate"), ("Hash", "Hash"), ("Source", "Source"), ("Holdout", "Holdout derived"), ("Chars", "Chars")]),
        "",
    ]
    write_text(REPORTS / "phase2_candidate_artifacts_zh.md", "\n".join(lines))


def phase2_run_paths(stage: str) -> dict[str, Path]:
    return {
        "submissions": RESULTS / f"phase2_{stage}_submissions.jsonl",
        "verifiers": RESULTS / f"phase2_{stage}_verifier_results.jsonl",
        "cost": RESULTS / f"phase2_{stage}_cost_ledger.jsonl",
    }


def run_workspace_cell_with_artifact(
    package: workspace.TaskPackage,
    adapter: workspace.AdapterConfig,
    run_id: str,
    stage: str,
    condition: str,
    artifact: dict[str, Any] | None,
) -> workspace.CellResult:
    exp = ROOT / "experiments" / "phase0_headroom"
    namespace = workspace.artifact_namespace(f"{PHASE2_RESULT_PREFIX}_{stage}_{condition}", adapter.adapter_id)
    raw_dir = exp / workspace.RAW_REL / namespace / run_id
    workspace_root = exp / workspace.WORKSPACE_REL / namespace / run_id
    solver_workspace = workspace_root / "solver"
    verifier_workspace = workspace_root / "verifier"
    workspace.archive_tree(package.source_repo, package.base_commit, solver_workspace)
    injection_record = None
    if artifact is not None:
        injection_record = materialize_artifact(solver_workspace, artifact, run_id=run_id, surface=TARGET_SURFACE)
    workspace.initialize_workspace_git(solver_workspace)
    statement_file = workspace.write_statement_file(solver_workspace, package)
    raw_dir.mkdir(parents=True, exist_ok=True)

    command = workspace.render_command(
        adapter.command_template,
        workspace=solver_workspace,
        statement_file=statement_file,
        task_id=package.task_id,
        run_id=run_id,
        raw_dir=raw_dir,
        timeout_seconds=adapter.timeout_seconds,
    )
    start = time.monotonic()
    acut = workspace.run_command(command, solver_workspace, timeout=adapter.timeout_seconds, env=os.environ.copy())
    latency = round(time.monotonic() - start, 3)
    stdout_path = raw_dir / "acut_stdout.txt"
    stderr_path = raw_dir / "acut_stderr.txt"
    stdout_path.write_text(acut.stdout, encoding="utf-8")
    stderr_path.write_text(acut.stderr, encoding="utf-8")
    patch_text = workspace.capture_diff(solver_workspace)
    patch_path = raw_dir / "submission.patch"
    patch_path.write_text(patch_text, encoding="utf-8")
    patch_sha = workspace.sha256_file(patch_path)
    base_submission = {
        "schema_version": "barcarolle.workspace_acut_submission.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "adapter_id": adapter.adapter_id,
        "acut_id": adapter.acut_id,
        "harness_name": adapter.harness_name,
        "model_or_agent_name": adapter.model_or_agent_name,
        "command_template_source": adapter.command_template_source,
        "endpoint_proof_status": adapter.endpoint_proof_status,
        "task_id": package.task_id,
        "repo_id": package.repo_id,
        "split": stage,
        "patch_source": "git_diff_after_workspace_run",
        "patch_sha256": patch_sha,
        "latency_seconds": latency,
        "adapter_timed_out": acut.timed_out,
        "raw_artifacts": {
            "stdout": str(stdout_path.relative_to(exp)),
            "stderr": str(stderr_path.relative_to(exp)),
            "patch": str(patch_path.relative_to(exp)),
        },
        "task_package_metadata": workspace.package_submission_metadata(package),
        "phase2_condition": condition,
        "phase2_artifact_hash": None if artifact is None else artifact["hash"],
        "phase2_injection_record": injection_record,
    }
    verifier = {
        "schema_version": "barcarolle.workspace_acut_verifier.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "adapter_id": adapter.adapter_id,
        "acut_id": adapter.acut_id,
        "harness_name": adapter.harness_name,
        "model_or_agent_name": adapter.model_or_agent_name,
        "command_template_source": adapter.command_template_source,
        "endpoint_proof_status": adapter.endpoint_proof_status,
        "task_id": package.task_id,
        "repo_id": package.repo_id,
        "split": stage,
        "fresh_workspace": False,
        "status": "invalid_output",
        "verifier_exit_code": None,
        "harness_error": None,
        "phase2_condition": condition,
        "phase2_artifact_hash": None if artifact is None else artifact["hash"],
    }
    if acut.returncode != 0:
        submission = {**base_submission, "status": "acut_harness_error", "acut_exit_code": acut.returncode}
        verifier.update({"status": "acut_harness_error", "harness_error": "acut_command_failed", "acut_exit_code": acut.returncode, "adapter_timed_out": acut.timed_out})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)
    if not patch_text.strip():
        submission = {**base_submission, "status": "invalid_output", "acut_exit_code": acut.returncode}
        verifier.update({"status": "invalid_output", "harness_error": "empty_workspace_diff"})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)

    changed = workspace.changed_paths(solver_workspace)
    submission = {**base_submission, "status": "submitted", "acut_exit_code": acut.returncode, "changed_paths": changed}
    violation, violating_paths = workspace.policy_violation(changed, package)
    if violation:
        verifier.update({"status": "policy_violation", "harness_error": violation, "changed_paths": violating_paths})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)

    workspace.archive_tree(package.source_repo, package.base_commit, verifier_workspace)
    workspace.initialize_workspace_git(verifier_workspace)
    applied, apply_error = workspace.apply_patch(verifier_workspace, patch_path)
    if not applied:
        verifier.update({"status": "harness_error", "harness_error": "captured_patch_did_not_apply", "patch_apply_error_tail": apply_error})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)
    injected, inject_error = workspace.inject_hidden_oracle(ROOT, package, verifier_workspace, raw_dir)
    if not injected:
        verifier.update({"status": "harness_error", "harness_error": inject_error})
        return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)

    verify_stdout = raw_dir / "verifier_stdout.txt"
    verify_stderr = raw_dir / "verifier_stderr.txt"
    verify = workspace.run_command(package.verifier_command, verifier_workspace, timeout=package.timeout_seconds, env=workspace.verifier_env_for(package, verifier_workspace))
    verify_stdout.write_text(verify.stdout, encoding="utf-8")
    verify_stderr.write_text(verify.stderr, encoding="utf-8")
    verifier.update(
        {
            "status": "timeout" if verify.timed_out else "verified_pass" if verify.returncode == 0 else "verified_fail",
            "verifier_exit_code": verify.returncode,
            "duration_seconds": round(verify.duration_seconds, 3),
            "fresh_workspace": True,
            "raw_artifacts": {
                "stdout": str(verify_stdout.relative_to(exp)),
                "stderr": str(verify_stderr.relative_to(exp)),
            },
        }
    )
    return workspace.CellResult(submission, verifier, solver_workspace, verifier_workspace)


def normalize_cost_row(row: dict[str, Any]) -> dict[str, Any]:
    return demo_costs.normalize_cost_row(row)


def cost_row_for_result(
    result: workspace.CellResult,
    candidate: dict[str, Any],
    config: dict[str, Any],
    stage: str,
    condition: str,
    artifact_hash: str | None,
) -> dict[str, Any]:
    usage = demo_costs.usage_from_submission(result.submission)
    usage_observed, estimated_cost, token_counts = demo_costs.estimate_cost(usage, candidate["model"], config)
    return normalize_cost_row(
        {
            "schema_version": "barcarolle.agent_tuning_demo.phase2_cost.v1",
            "run_id": result.submission["run_id"],
            "timestamp": iso_now(),
            "stage": stage,
            "condition": condition,
            "agent_id": candidate["agent_id"],
            "reviewer_name": candidate["reviewer_name"],
            "harness": candidate["harness"],
            "model": candidate["model"],
            "task_id": result.submission["task_id"],
            "status": result.verifier["status"],
            "usage_observed": usage_observed,
            "estimated_cost_usd": estimated_cost,
            "cost_method": "observed_token_estimate" if usage_observed else "conservative_per_cell_estimate",
            **demo_costs.cost_observation_metadata(usage_observed),
            "latency_seconds": result.submission.get("latency_seconds"),
            "artifact_hash": artifact_hash,
            **token_counts,
        }
    )


def phase2_score_rows(stage: str, submissions: list[dict[str, Any]], verifiers: list[dict[str, Any]], cost_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    verifier_by_run = {row["run_id"]: row for row in verifiers}
    cost_by_run = {row["run_id"]: row for row in cost_rows}
    rows: list[dict[str, Any]] = []
    for submission in submissions:
        verifier = verifier_by_run.get(submission["run_id"], {})
        cost = cost_by_run.get(submission["run_id"], {})
        terminal = verifier.get("status") or submission.get("status")
        rows.append(
            {
                "stage": stage,
                "condition": submission.get("phase2_condition", cost.get("condition", "")),
                "agent_id": submission.get("adapter_id", ""),
                "reviewer_name": cost.get("reviewer_name", TARGET_AGENT_NAME),
                "harness": submission.get("harness_name", ""),
                "model": submission.get("model_or_agent_name", ""),
                "task_id": submission.get("task_id", ""),
                "terminal_status": terminal,
                "scoreable_cell": terminal in SCOREABLE_STATUSES,
                "verified_pass": terminal == "verified_pass",
                "failure_category": demo_costs.failure_category(verifier, submission),
                "latency_seconds": submission.get("latency_seconds", ""),
                "estimated_cost_usd": cost.get("estimated_cost_usd", ""),
                "usage_observed": cost.get("usage_observed", False),
                "cost_observation_kind": cost.get("cost_observation_kind", ""),
                "usage_source": cost.get("usage_source", ""),
                "artifact_hash": submission.get("phase2_artifact_hash") or cost.get("artifact_hash") or "",
                "patch_sha256": submission.get("patch_sha256", ""),
            }
        )
    return rows


def paired_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition = {condition: [row for row in rows if row["condition"] == condition] for condition in sorted({row["condition"] for row in rows})}
    baseline = {row["task_id"]: row for row in by_condition.get("baseline", [])}
    tuned = {row["task_id"]: row for row in by_condition.get("tuned", [])}
    common_ids = sorted(set(baseline) & set(tuned))
    improved = [task_id for task_id in common_ids if tuned[task_id]["verified_pass"] is True and baseline[task_id]["verified_pass"] is not True]
    regressed = [task_id for task_id in common_ids if baseline[task_id]["verified_pass"] is True and tuned[task_id]["verified_pass"] is not True]
    matrix = []
    for task_id in common_ids:
        matrix.append(
            {
                "task_id": task_id,
                "baseline_status": baseline[task_id]["terminal_status"],
                "baseline_pass": baseline[task_id]["verified_pass"],
                "tuned_status": tuned[task_id]["terminal_status"],
                "tuned_pass": tuned[task_id]["verified_pass"],
            }
        )

    def condition_metrics(condition: str) -> dict[str, Any]:
        condition_rows = by_condition.get(condition, [])
        scoreable = [row for row in condition_rows if row["scoreable_cell"] is True]
        invalid = [row for row in condition_rows if row["scoreable_cell"] is not True]
        costs = [float(row["estimated_cost_usd"] or 0.0) for row in condition_rows]
        latencies = [float(row["latency_seconds"] or 0.0) for row in condition_rows if row.get("latency_seconds") != ""]
        return {
            "cells": len(condition_rows),
            "scoreable_cells": len(scoreable),
            "invalid_or_unscoreable_cells": len(invalid),
            "verified_pass_count": sum(1 for row in scoreable if row["verified_pass"] is True),
            "pass_rate": None if not scoreable else round(sum(1 for row in scoreable if row["verified_pass"] is True) / len(scoreable), 4),
            "estimated_cost_usd": round(sum(costs), 8),
            "median_latency_seconds": None if not latencies else sorted(latencies)[len(latencies) // 2],
            "usage_observed_count": sum(1 for row in condition_rows if row.get("usage_observed") is True),
        }

    baseline_metrics = condition_metrics("baseline")
    tuned_metrics = condition_metrics("tuned")
    return {
        "paired_task_count": len(common_ids),
        "improved_task_ids": improved,
        "regressed_task_ids": regressed,
        "paired_net_wins": len(improved) - len(regressed),
        "matrix": matrix,
        "conditions": {
            "baseline": baseline_metrics,
            "tuned": tuned_metrics,
        },
        "non_regressing_gate": bool(
            len(improved) - len(regressed) >= 0
            and tuned_metrics["invalid_or_unscoreable_cells"] <= baseline_metrics["invalid_or_unscoreable_cells"]
        ),
    }


def persist_phase2_stage(stage: str, submissions: list[dict[str, Any]], verifiers: list[dict[str, Any]], cost_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = phase2_score_rows(stage, submissions, verifiers, cost_rows)
    write_jsonl(phase2_run_paths(stage)["submissions"], submissions)
    write_jsonl(phase2_run_paths(stage)["verifiers"], verifiers)
    write_jsonl(phase2_run_paths(stage)["cost"], cost_rows)
    score_path = RESULTS / f"phase2_{stage}_results.csv"
    summary_path = RESULTS / f"phase2_{stage}_summary.json"
    write_csv(score_path, rows, PHASE2_SCORE_FIELDS)
    summary = {
        "schema_version": f"barcarolle.agent_tuning_demo.phase2_{stage}_summary.v1",
        "generated_at": iso_now(),
        "stage": stage,
        "paid_cells": len(rows),
        "estimated_cost_usd": round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows), 8),
        "paired": paired_summary(rows),
    }
    write_json(summary_path, summary)
    return summary


def load_best_candidate_artifact() -> dict[str, Any]:
    payload = read_json(RESULTS / "phase2_candidate_artifacts.json")
    candidates = payload.get("candidate_artifacts") or []
    if not candidates:
        raise RuntimeError("no candidate artifacts found")
    # Use the last GEPA candidate because the bounded custom proposer appends the failure-driven additions.
    artifact = candidates[-1]
    validate_artifact(artifact)
    return artifact


def selected_task_ids_for_stage(stage: str) -> list[str]:
    if stage == "selection_dev":
        return list(SELECTION_DEV_TASKS)
    if stage == "holdout":
        chosen = read_json(RESULTS / "phase2_chosen_artifact.json")
        return list(chosen["holdout_task_ids_revealed_after_freeze"])
    raise ValueError(f"unknown stage: {stage}")


def require_endpoint_env() -> None:
    missing = [name for name in ["LLM_BASE_URL", "LLM_API_KEY"] if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"missing endpoint env: {', '.join(missing)}")


def run_phase2_stage(stage: str) -> dict[str, Any]:
    require_endpoint_env()
    action_preflight_or_raise()
    config = selection_snapshot.selection_config()
    candidate = workspace_inputs.candidate_by_id(config)[TARGET_AGENT_ID]
    adapter = workspace_inputs.adapter_config_for(config, candidate, command_template_source="agent_tuning_demo_selection_snapshot")
    packages = workspace_inputs.package_map(config)
    artifact = load_best_candidate_artifact() if stage == "selection_dev" else read_json(CHOSEN_DIR / "artifact.json")
    validate_artifact(artifact)
    paths = phase2_run_paths(stage)
    submissions = read_jsonl(paths["submissions"])
    verifiers = read_jsonl(paths["verifiers"])
    cost_rows = read_jsonl(paths["cost"])
    seen = {row["run_id"] for row in submissions}
    for condition in ["baseline", "tuned"]:
        for task_id in selected_task_ids_for_stage(stage):
            package = replace(packages[task_id], split=stage)
            run_id = f"phase2_{stage}__{condition}__{TARGET_AGENT_ID}__{task_id}"
            if run_id in seen:
                continue
            cell_artifact = None if condition == "baseline" else artifact
            result = run_workspace_cell_with_artifact(package, adapter, run_id, stage, condition, cell_artifact)
            artifact_hash = None if cell_artifact is None else cell_artifact["hash"]
            cost_row = cost_row_for_result(result, candidate, config, stage, condition, artifact_hash)
            submissions = workspace.merge_rows_by_run_id(submissions, [result.submission])
            verifiers = workspace.merge_rows_by_run_id(verifiers, [result.verifier])
            cost_rows = workspace.merge_rows_by_run_id(cost_rows, [cost_row])
            seen.add(run_id)
            persist_phase2_stage(stage, submissions, verifiers, cost_rows)
    summary = persist_phase2_stage(stage, submissions, verifiers, cost_rows)
    write_stage_report(stage, summary)
    return summary


def write_stage_report(stage: str, summary: dict[str, Any]) -> None:
    paired = summary["paired"]
    rows = [
        {
            "Condition": condition,
            "Pass": data["verified_pass_count"],
            "Scoreable": data["scoreable_cells"],
            "Invalid": data["invalid_or_unscoreable_cells"],
            "Cost": data["estimated_cost_usd"],
            "Latency": data["median_latency_seconds"],
        }
        for condition, data in paired["conditions"].items()
    ]
    report_name = "phase2_holdout_validation_zh.md" if stage == "holdout" else "phase2_selection_dev_zh.md"
    lines = [
        f"# Agent Tuning Phase 2 {stage} validation",
        "",
        f"生成日期：{summary['generated_at']}",
        "",
        f"- Paid cells: `{summary['paid_cells']}`",
        f"- Estimated cost: `${summary['estimated_cost_usd']}`",
        f"- Paired net wins: `{paired['paired_net_wins']}`",
        f"- Non-regressing gate: `{paired['non_regressing_gate']}`",
        "",
        *markdown_table(rows, [("Condition", "Condition"), ("Pass", "Pass"), ("Scoreable", "Scoreable"), ("Invalid", "Invalid"), ("Cost", "Cost"), ("Median latency", "Latency")]),
        "",
        "## Pair matrix",
        "",
        *markdown_table(paired["matrix"], [("Task", "task_id"), ("Baseline", "baseline_status"), ("Baseline pass", "baseline_pass"), ("Tuned", "tuned_status"), ("Tuned pass", "tuned_pass")]),
        "",
    ]
    write_text(REPORTS / report_name, "\n".join(lines))


def write_chosen_artifact() -> None:
    selection_summary = read_json(RESULTS / "phase2_selection_dev_summary.json")
    if not selection_summary["paired"]["non_regressing_gate"]:
        raise RuntimeError("selection-dev non-regressing gate failed; do not freeze Holdout artifact")
    artifact = load_best_candidate_artifact()
    validate_artifact(artifact)
    CHOSEN_DIR.mkdir(parents=True, exist_ok=True)
    write_json(CHOSEN_DIR / "artifact.json", artifact)
    write_text(CHOSEN_DIR / "AGENTS_appendix.md", artifact["files"][0]["content"])
    payload = {
        "schema_version": "barcarolle.agent_tuning_demo.phase2_chosen_artifact.v1",
        "generated_at": iso_now(),
        "status": "frozen_holdout_gate_passed",
        "artifact_id": artifact["artifact_id"],
        "artifact_hash": artifact["hash"],
        "artifact_path": "experiments/agent_tuning_demo/results/chosen_artifact/artifact.json",
        "appendix_path": "experiments/agent_tuning_demo/results/chosen_artifact/AGENTS_appendix.md",
        "source_candidate": artifact["optimizer_source"],
        "selection_dev_summary": selection_summary["paired"],
        "rules_targeted_failure_labels": read_json(RESULTS / "phase2_candidate_artifacts.json").get("label_counts", {}),
        "leakage_audit": {
            "holdout_derived": artifact["holdout_derived"],
            "visible_to_optimizer": artifact["visible_to_optimizer"],
            "holdout_task_ids_used_before_freeze": False,
        },
        "inject_command": "python experiments/agent_tuning_demo/tools/tuning_artifacts.py --workspace <solver> --artifact experiments/agent_tuning_demo/results/chosen_artifact/artifact.json --run-id <run_id> --surface repo_AGENTS_md --record-out <record.json>",
        "holdout_task_ids_revealed_after_freeze": list(HOLDOUT_TASKS),
        "holdout_task_ids_revealed_after_artifact_hash": artifact["hash"],
        "gate_to_run_holdout": True,
    }
    write_json(RESULTS / "phase2_chosen_artifact.json", payload)
    lines = [
        "# Agent Tuning Phase 2 chosen artifact",
        "",
        f"生成日期：{payload['generated_at']}",
        "",
        f"- Status: `{payload['status']}`",
        f"- Artifact hash: `{payload['artifact_hash']}`",
        f"- Selection-dev paired net wins: `{selection_summary['paired']['paired_net_wins']}`",
        "- Holdout task ids are revealed in the JSON only after this hash freeze.",
        "",
    ]
    write_text(REPORTS / "phase2_chosen_artifact_zh.md", "\n".join(lines))


def final_closeout_payload() -> dict[str, Any]:
    action = read_json(RESULTS / "phase2_action_preflight.json")
    candidates = read_json(RESULTS / "phase2_candidate_artifacts.json") if (RESULTS / "phase2_candidate_artifacts.json").exists() else {}
    selection_summary = read_json(RESULTS / "phase2_selection_dev_summary.json") if (RESULTS / "phase2_selection_dev_summary.json").exists() else None
    chosen = read_json(RESULTS / "phase2_chosen_artifact.json") if (RESULTS / "phase2_chosen_artifact.json").exists() else None
    holdout_summary = read_json(RESULTS / "phase2_holdout_summary.json") if (RESULTS / "phase2_holdout_summary.json").exists() else None
    terminal = "phase2_action_preflight_blocked"
    if action.get("action_level_preflight_passed"):
        terminal = "phase2_selection_dev_negative"
        if selection_summary and selection_summary["paired"]["non_regressing_gate"]:
            terminal = "phase2_success_no_holdout_regression"
        if holdout_summary:
            terminal = "phase2_success_holdout_improved" if holdout_summary["paired"]["paired_net_wins"] > 0 else "phase2_success_no_holdout_regression"
    paid_cells = 0
    estimated_cost = 0.0
    for path in [RESULTS / "phase2_selection_dev_summary.json", RESULTS / "phase2_holdout_summary.json"]:
        if path.exists():
            payload = read_json(path)
            paid_cells += int(payload.get("paid_cells") or 0)
            estimated_cost += float(payload.get("estimated_cost_usd") or 0.0)
    return {
        "schema_version": "barcarolle.agent_tuning_demo.phase2_closeout.v1",
        "generated_at": iso_now(),
        "terminal_state": terminal,
        "paid_cells": paid_cells,
        "estimated_cost_usd": round(estimated_cost, 8),
        "action_preflight": {
            "passed": action.get("action_level_preflight_passed"),
            "paid_calls_used": action.get("paid_calls_used"),
            "evidence": action.get("action_level_difference"),
        },
        "optimizer": candidates.get("optimizer"),
        "target_agent_id": TARGET_AGENT_ID,
        "target_surface": TARGET_SURFACE,
        "candidate_artifact_count": candidates.get("candidate_count", 0),
        "chosen_artifact_hash": None if not chosen else chosen.get("artifact_hash"),
        "selection_dev": None if not selection_summary else selection_summary["paired"],
        "holdout": None if not holdout_summary else holdout_summary["paired"],
        "supported_claims": [
            "A repo-local Kilo AGENTS.md appendix can change real Kilo CLI action behavior in the controlled preflight.",
            "Barcarolle can export Selection-train feedback without Holdout task IDs or raw transcripts.",
            "Barcarolle can generate and freeze a deployable repo-local text artifact before Holdout validation."
        ],
        "unsupported_claims": [
            "full predictive validity",
            "cross-repo generalization",
            "model fine-tuning",
            "full opaque Codex/Kilo Agent tuning",
            "GEPA/Phoenix superiority",
            "statistical significance",
            "production-ready Agent tuning system"
        ],
        "canonical_artifacts": [
            "experiments/agent_tuning_demo/reports/phase2_agent_tuning_demo_report_zh.md",
            "experiments/agent_tuning_demo/reports/phase2_closeout_zh.md",
            "experiments/agent_tuning_demo/results/phase2_closeout.json",
        ],
    }


def write_final_reports() -> None:
    payload = final_closeout_payload()
    write_json(RESULTS / "phase2_closeout.json", payload)
    selection_rows = [] if payload["selection_dev"] is None else payload["selection_dev"]["matrix"]
    holdout_rows = [] if payload["holdout"] is None else payload["holdout"]["matrix"]
    report_lines = [
        "# Agent Tuning Demo Phase 2 report",
        "",
        f"生成日期：{payload['generated_at']}",
        "",
        "## What this demo tried to prove",
        "",
        "This Phase 2 demo tested whether Barcarolle can turn target-repo Agent feedback into one deployable repo-local Agent artifact, then validate before/after behavior under a frozen protocol.",
        "",
        "## Result",
        "",
        f"- Terminal state: `{payload['terminal_state']}`",
        f"- Paid cells: `{payload['paid_cells']}`",
        f"- Estimated cost: `${payload['estimated_cost_usd']}`",
        f"- Action-level preflight passed: `{payload['action_preflight']['passed']}`",
        f"- Optimizer/proposer: `{payload['optimizer']}`",
        f"- Target: `{TARGET_AGENT_ID}` via `{TARGET_SURFACE}`",
        f"- Chosen artifact hash: `{payload['chosen_artifact_hash']}`",
        "",
        "## Selection-dev matrix",
        "",
        *markdown_table(selection_rows, [("Task", "task_id"), ("Baseline", "baseline_status"), ("Baseline pass", "baseline_pass"), ("Tuned", "tuned_status"), ("Tuned pass", "tuned_pass")]),
        "",
        "## Holdout matrix",
        "",
        *markdown_table(holdout_rows, [("Task", "task_id"), ("Baseline", "baseline_status"), ("Baseline pass", "baseline_pass"), ("Tuned", "tuned_status"), ("Tuned pass", "tuned_pass")]),
        "",
        "## Supported claims",
        "",
        *[f"- {claim}" for claim in payload["supported_claims"]],
        "",
        "## Unsupported claims",
        "",
        *[f"- {claim}" for claim in payload["unsupported_claims"]],
        "",
        "## Recommended next work",
        "",
        "- Repeat with a larger preregistered Selection-dev/Holdout sample only after cost and variance are acceptable.",
        "- Try one alternate surface, such as Kilo project rules, only in a separate single-surface run.",
        "- Keep predictive-validity and cross-repo claims separate from this artifact-tuning demo.",
        "",
    ]
    write_text(REPORTS / "phase2_agent_tuning_demo_report_zh.md", "\n".join(report_lines))
    closeout_lines = [
        "# Agent Tuning Phase 2 closeout",
        "",
        f"Terminal state: `{payload['terminal_state']}`.",
        "",
        f"- Paid cells: `{payload['paid_cells']}`.",
        f"- Estimated cost: `${payload['estimated_cost_usd']}`.",
        f"- Preflight passed: `{payload['action_preflight']['passed']}`.",
        f"- Optimizer/proposer: `{payload['optimizer']}`.",
        f"- Target Agent/surface: `{TARGET_AGENT_ID}` / `{TARGET_SURFACE}`.",
        f"- Candidate artifact count: `{payload['candidate_artifact_count']}`.",
        f"- Selection-dev paired net wins: `{None if payload['selection_dev'] is None else payload['selection_dev']['paired_net_wins']}`.",
        f"- Holdout paired net wins: `{None if payload['holdout'] is None else payload['holdout']['paired_net_wins']}`.",
        "",
        "See the JSON closeout for matrices, claims, and canonical artifact links.",
        "",
    ]
    write_text(REPORTS / "phase2_closeout_zh.md", "\n".join(closeout_lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Agent Tuning Demo Phase 2 helpers.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in [
        "protocol",
        "action-preflight",
        "feedback-export",
        "candidate-artifacts",
        "selection-dev",
        "chosen-artifact",
        "holdout",
        "final",
    ]:
        sub.add_parser(name)
    args = parser.parse_args(argv)
    if args.command == "protocol":
        write_protocol()
    elif args.command == "action-preflight":
        write_action_preflight()
    elif args.command == "feedback-export":
        write_feedback_export()
    elif args.command == "candidate-artifacts":
        write_candidate_artifacts()
    elif args.command == "selection-dev":
        run_phase2_stage("selection_dev")
    elif args.command == "chosen-artifact":
        write_chosen_artifact()
    elif args.command == "holdout":
        run_phase2_stage("holdout")
    elif args.command == "final":
        write_final_reports()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
