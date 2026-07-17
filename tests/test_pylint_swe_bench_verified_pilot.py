from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import cast

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.pylint_swe_bench_verified import pilot  # noqa: E402


def test_fixed_task_sources_replace_the_uncertifiable_verified_instance() -> None:
    configured = pilot._task_source_by_instance()

    assert len(configured) == 10
    assert "pylint-dev__pylint-8898" not in configured
    assert configured["pylint-dev__pylint-5859"]["dataset_family"] == (
        "swe_bench_lite"
    )


def test_candidate_separates_task_source_time_from_check_time(
    tmp_path: Path,
) -> None:
    instance_id = "pylint-dev__pylint-4551"
    bundle = tmp_path / "hidden-checks" / instance_id
    bundle.mkdir(parents=True)
    (bundle / "spec.json").write_text("{}", encoding="utf-8")
    paths = pilot.PilotPaths(
        output_dir=tmp_path,
        target_repo=tmp_path / "target",
        dataset=tmp_path / "dataset",
        supplemental_dataset=tmp_path / "supplemental-dataset",
        harness_python=tmp_path / "python",
    )

    candidate = pilot._candidate(
        paths,
        {
            "instance_id": instance_id,
            "base_commit": "a" * 40,
            "problem_statement": "Fix the bug.",
            "difficulty": "<15 min fix",
        },
        {
            "instance_id": instance_id,
            "issue_url": "https://example.invalid/issues/1",
            "task_material_available_at": "2021-01-01T00:00:00Z",
            "check_material_available_at": "2021-02-01T00:00:00Z",
        },
        ("check",),
    )

    assert candidate.source_resolved_at == "2021-01-01T00:00:00Z"
    assert candidate.task_material_available_at == "2021-01-01T00:00:00Z"
    assert candidate.check_material_available_at == "2021-02-01T00:00:00Z"


def test_certification_counts_require_base_negative_and_reference_positive() -> None:
    base = {
        "tests": {
            "FAIL_TO_PASS": {"success_count": 0, "failure_count": 3},
            "PASS_TO_PASS": {"success_count": 5, "failure_count": 0},
        }
    }
    reference = {
        "tests": {
            "FAIL_TO_PASS": {"success_count": 3, "failure_count": 0},
            "PASS_TO_PASS": {"success_count": 5, "failure_count": 0},
        }
    }

    pilot._require_test_counts(base, 3, 5, reference=False)
    pilot._require_test_counts(reference, 3, 5, reference=True)

    with pytest.raises(RuntimeError, match="test counts differ"):
        pilot._require_test_counts(reference, 3, 5, reference=False)


def test_started_cell_without_exact_result_is_never_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_path = tmp_path / "resource-ledger.json"
    pilot._write_json(ledger_path, pilot._new_ledger())
    pilot._append_ledger_event(
        pilot._ledger_events_path(ledger_path),
        {
            "event_type": "reservation",
            "recorded_at": "2026-07-17T00:00:00Z",
            "call_id": "cell-01",
            "state": "started",
        },
    )
    context = cast(pilot.PilotContext, SimpleNamespace(ledger_path=ledger_path))
    monkeypatch.setattr(pilot, "_exact_result_for_call", lambda *_: None)

    with pytest.raises(RuntimeError, match="automatic retry is forbidden"):
        pilot._reconcile_ledger(context)


def test_started_cell_recovers_an_exact_scoreable_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_path = tmp_path / "resource-ledger.json"
    pilot._write_json(ledger_path, pilot._new_ledger())
    pilot._append_ledger_event(
        pilot._ledger_events_path(ledger_path),
        {
            "event_type": "reservation",
            "recorded_at": "2026-07-17T00:00:00Z",
            "call_id": "cell-01",
            "state": "started",
        },
    )
    result = SimpleNamespace(
        result_id="result-1",
        result_digest="digest-1",
        terminal_status="failed",
        scoreable_state="scoreable",
        outcome="fail",
        usage={
            "input_tokens": 10,
            "uncached_input_tokens": 8,
            "cached_input_tokens": 2,
            "output_tokens": 3,
        },
        cost={"total_cost": 0.01},
        pricing_version=pilot.PRICING_VERSION,
    )
    context = cast(pilot.PilotContext, SimpleNamespace(ledger_path=ledger_path))
    monkeypatch.setattr(pilot, "_exact_result_for_call", lambda *_: result)
    monkeypatch.setattr(pilot, "_paid_result_count", lambda _: 1)

    ledger = pilot._reconcile_ledger(context)

    calls = ledger["calls"]
    assert isinstance(calls, list)
    assert len(calls) == 1
    assert calls[0] == {
        **calls[0],
        "call_id": "cell-01",
        "state": "completed",
        "recovered_after_interruption": True,
        "result_id": "result-1",
        "result_digest": "digest-1",
        "terminal_status": "failed",
        "scoreable_state": "scoreable",
        "outcome": "fail",
        "usage": {
            "uncached_input_tokens": 8,
            "cached_input_tokens": 2,
            "output_tokens": 3,
        },
        "estimated_cost_usd": 0.01,
        "pricing_version": pilot.PRICING_VERSION,
    }


def test_pilot_cli_only_exposes_single_cell_paid_stages() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "examples/pylint_swe_bench_verified/pilot.py",
            "--help",
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert "at most one cell" in completed.stdout
    assert "--canary" in completed.stdout
    assert "--next-cell" in completed.stdout
    assert "--all" not in completed.stdout


def test_paid_check_rejects_a_stale_summary(tmp_path: Path) -> None:
    instance_id = "pylint-dev__pylint-4551"
    task_id = "task-1"
    diff_digest = "a" * 64
    summary_path = (
        tmp_path / "raw/checks" / instance_id / diff_digest / "summary.json"
    )
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(
        json.dumps(
            {
                "state": "scored",
                "instance_id": instance_id,
                "patch_digest": diff_digest,
                "resolved": False,
            }
        ),
        encoding="utf-8",
    )
    os.utime(summary_path, (1_577_836_800, 1_577_836_800))
    context = cast(
        pilot.PilotContext,
        SimpleNamespace(
            instance_by_task_id={task_id: instance_id},
            paths=SimpleNamespace(output_dir=tmp_path),
        ),
    )
    task = SimpleNamespace(task_id=task_id)
    workspace_run = SimpleNamespace(
        diff_digest=diff_digest,
        started_at="2026-07-17T00:00:00Z",
        check_outcome="fail",
    )

    with pytest.raises(RuntimeError, match="summary is stale"):
        pilot._require_paid_check_summary(context, task, workspace_run)  # type: ignore[arg-type]


def test_pilot_resource_ledger_pins_authorized_limits_and_official_rates() -> None:
    ledger = pilot._new_ledger()

    assert ledger["authorization"] == {
        "approved_at": "2026-07-17",
        "budget_usd": 30.0,
        "credential_variables": ["OPENAI_API_KEY", "OPENAI_BASE_URL"],
        "scope": "fixed 10-task x low/high SWE-bench Pylint pilot",
    }
    assert ledger["limits"] == {
        "maximum_estimated_cost_usd": 30.0,
        "maximum_paid_calls": 20,
        "retry_policy": {
            "cell_retries": 0,
            "codex_request_retries": "default",
            "codex_stream_retries": "default",
        },
    }
    pricing = cast(dict[str, object], ledger["pricing"])
    models = cast(dict[str, object], pricing["models"])
    rates = cast(dict[str, float], models["gpt-5.4-mini"])
    assert rates == {
        "input_usd_per_token": 0.75 / 1_000_000,
        "cached_input_usd_per_token": 0.075 / 1_000_000,
        "output_usd_per_token": 4.5 / 1_000_000,
    }
    assert json.dumps(ledger)
