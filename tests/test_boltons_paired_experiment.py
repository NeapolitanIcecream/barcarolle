from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import Any, cast

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest  # noqa: E402
from barcarolle.result_store import compute_cost  # noqa: E402
from examples.boltons_regression import paired_experiment  # noqa: E402


def test_paired_agents_bind_exact_model_and_reasoning_effort(
    tmp_path: Path,
) -> None:
    agents, commands = paired_experiment._agents(
        tmp_path,
        cli_version="codex-cli-test",
        endpoint_digest="endpoint-digest",
    )

    assert tuple(agent.requested_model_id for agent in agents) == (
        "gpt-5.4-mini",
        "gpt-5.4-mini",
    )
    assert all(agent.model_snapshot_id is None for agent in agents)
    assert all(
        agent.model_resolution_scope_id == paired_experiment.MODEL_RESOLUTION_SCOPE_ID
        for agent in agents
    )
    assert tuple(paired_experiment._agent_effort(agent) for agent in agents) == (
        "low",
        "high",
    )
    assert agents[0].agent_manifest_digest != agents[1].agent_manifest_digest
    for agent in agents:
        command = commands[agent.agent_id]
        assert f"BARCAROLLE_CODEX_MODEL={agent.requested_model_id}" in command
        assert (
            "BARCAROLLE_CODEX_REASONING_EFFORT="
            f"{paired_experiment._agent_effort(agent)}"
        ) in command
        assert agent.harness_digest == canonical_digest({"agent_command": command})


def test_official_mini_pricing_requires_all_three_measured_token_fields() -> None:
    usage = {
        "uncached_input_tokens": 1_000_000,
        "cached_input_tokens": 1_000_000,
        "output_tokens": 1_000_000,
        "input_tokens": 2_000_000,
    }

    cost = compute_cost(usage, paired_experiment.SCORING_CONFIG)

    assert cost["total_cost"] == pytest.approx(5.325)
    assert paired_experiment._priced_usage(usage) == {
        "uncached_input_tokens": 1_000_000,
        "cached_input_tokens": 1_000_000,
        "output_tokens": 1_000_000,
    }
    with pytest.raises(RuntimeError, match="cached_input_tokens is required"):
        paired_experiment._priced_usage(
            {"uncached_input_tokens": 1, "output_tokens": 1}
        )
    with pytest.raises(RuntimeError, match="cached plus uncached"):
        paired_experiment._priced_usage(
            {
                "input_tokens": 99,
                "uncached_input_tokens": 1,
                "cached_input_tokens": 2,
                "output_tokens": 1,
            }
        )


def test_resource_ledger_uses_append_only_reservation_and_completion_events(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "resource-ledger.json"
    initial = {
        "authorization": {
            "budget_usd": 300.0,
            "credential_variables": ["OPENAI_API_KEY", "OPENAI_BASE_URL"],
        },
        "calls": [],
        "limits": {"maximum_paid_calls": 10},
        "spent_usd": 0.0,
        "remaining_usd": 300.0,
    }
    paired_experiment._write_json(snapshot, initial)
    events_path = paired_experiment._ledger_events_path(snapshot)
    paired_experiment._append_ledger_event(
        events_path,
        {
            "event_type": "reservation",
            "call_id": "cell-01",
            "state": "started",
            "agent_id": "agent-low",
        },
    )
    started = paired_experiment._load_ledger(snapshot)
    paired_experiment._append_ledger_event(
        events_path,
        {
            "event_type": "completion",
            "call_id": "cell-01",
            "state": "completed",
            "estimated_cost_usd": 1.25,
        },
    )

    completed = paired_experiment._load_ledger(snapshot)

    started_calls = started["calls"]
    completed_calls = completed["calls"]
    assert isinstance(started_calls, list) and isinstance(started_calls[0], dict)
    assert isinstance(completed_calls, list) and isinstance(completed_calls[0], dict)
    assert started_calls[0]["state"] == "started"
    assert completed_calls[0]["state"] == "completed"
    assert completed["spent_usd"] == pytest.approx(1.25)
    assert completed["remaining_usd"] == pytest.approx(298.75)
    assert tuple(
        json.loads(line)["event_type"]
        for line in events_path.read_text(encoding="utf-8").splitlines()
    ) == ("reservation", "completion")


def test_paired_cli_exposes_explicit_single_cell_stages() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "examples/boltons_regression/paired_experiment.py",
            "--help",
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert "at most one" in completed.stdout
    assert "--canary" in completed.stdout
    assert "--next-cell" in completed.stdout
    assert "--fit-mixture" in completed.stdout
    assert "--evaluate" in completed.stdout
    assert "--all" not in completed.stdout


def test_non_scoreable_historical_cell_stops_expansion_after_recovery() -> None:
    with pytest.raises(RuntimeError, match="expansion is stopped"):
        paired_experiment._ensure_historical_calls_scoreable(
            (
                {
                    "call_id": "cell-01",
                    "state": "completed",
                    "scoreable_state": "agent_invalid",
                },
            )
        )

    paired_experiment._ensure_historical_calls_scoreable(
        (
            {
                "call_id": "cell-01",
                "state": "completed",
                "scoreable_state": "scoreable",
            },
        )
    )


@pytest.mark.parametrize(
    ("origin_two_frozen", "expected_next"),
    ((False, "--fit-mixture"), (True, "--evaluate")),
)
def test_next_cell_stops_at_each_frozen_selection_boundary(
    monkeypatch: pytest.MonkeyPatch,
    origin_two_frozen: bool,
    expected_next: str,
) -> None:
    context = cast(
        paired_experiment.ExperimentContext,
        SimpleNamespace(
            tasks=(),
            checks={},
            agents=(),
            workspace_config=None,
            runtime_config=None,
            result_store=None,
        ),
    )
    monkeypatch.setattr(paired_experiment, "_reconcile_ledger", lambda _: {})
    monkeypatch.setattr(paired_experiment, "freeze_origin_one", lambda _: {})
    monkeypatch.setattr(
        paired_experiment,
        "_load_origin_one",
        lambda _: ((), object(), ()),
    )
    monkeypatch.setattr(
        paired_experiment, "_origin_two_is_frozen", lambda _: origin_two_frozen
    )
    monkeypatch.setattr(
        paired_experiment,
        "_load_origin_two",
        lambda _: (object(), object(), ()),
    )
    monkeypatch.setattr(paired_experiment, "_required_refs", lambda *args: ())
    monkeypatch.setattr(
        paired_experiment,
        "find_missing_results",
        lambda *args, **kwargs: (),
    )
    monkeypatch.setattr(paired_experiment, "_paid_result_count", lambda _: 0)

    summary = paired_experiment.run_next_cell(context, canary=False)

    assert cast(dict[str, Any], summary)["next"] == expected_next


def test_fake_codex_runs_both_frozen_origins_without_paid_network(
    tmp_path: Path,
) -> None:
    configured_target = os.environ.get("BARCAROLLE_BOLTONS_REPO")
    if configured_target is None:
        pytest.skip(
            "set BARCAROLLE_BOLTONS_REPO to run the real-target fake-Codex test"
        )
    output_dir = tmp_path / "paired"
    output_dir.mkdir()
    ledger = {
        "authorization": {
            "approved_at": "2026-07-15",
            "budget_usd": 300.0,
            "credential_variables": ["OPENAI_API_KEY", "OPENAI_BASE_URL"],
            "scope": "test",
        },
        "calls": [],
        "limits": {
            "maximum_paid_calls": 10,
            "maximum_estimated_cost_usd": 300.0,
            "retry_policy": "none",
        },
        "pricing": {
            "models": {
                "gpt-5.4-mini": {
                    "input_usd_per_token": 0.75 / 1_000_000,
                    "cached_input_usd_per_token": 0.075 / 1_000_000,
                    "output_usd_per_token": 4.5 / 1_000_000,
                }
            }
        },
        "spent_usd": 0.0,
        "remaining_usd": 300.0,
    }
    (output_dir / "resource-ledger.json").write_text(
        json.dumps(ledger), encoding="utf-8"
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_codex = fake_bin / "codex"
    fake_codex.write_text(
        "#!/bin/sh\n"
        'if [ "${1:-}" = "--version" ]; then\n'
        "  printf '%s\\n' 'codex-cli 0.test'\n"
        "  exit 0\n"
        "fi\n"
        "cat >/dev/null\n"
        'printf \'%s\\n\' \'{"type":"turn.completed","usage":'
        '{"input_tokens":12,"cached_input_tokens":2,'
        '"output_tokens":3}}\'\n',
        encoding="utf-8",
    )
    fake_codex.chmod(0o755)
    environment = {
        **os.environ,
        "OPENAI_BASE_URL": "https://no-network.invalid/v1",
        "OPENAI_API_KEY": "test-only",
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
    }

    def run_stage(stage: str) -> dict[str, Any]:
        completed = subprocess.run(
            [
                sys.executable,
                "examples/boltons_regression/paired_experiment.py",
                "--target-repo",
                configured_target,
                "--output-dir",
                str(output_dir),
                stage,
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        value = json.loads(completed.stdout)
        assert isinstance(value, dict)
        return value

    run_stage("--prepare-only")
    run_stage("--freeze-origin-one")
    run_stage("--canary")
    for _ in range(7):
        run_stage("--next-cell")
    fitted = run_stage("--fit-mixture")
    assert fitted["paid_call_count"] == 8
    assert (output_dir / "records/paired-mixture-selector.jsonl").exists()
    run_stage("--next-cell")
    run_stage("--next-cell")
    summary = run_stage("--evaluate")

    snapshot = json.loads(
        (output_dir / "resource-ledger.json").read_text(encoding="utf-8")
    )
    metrics = json.loads(
        (output_dir / "paired-metrics.json").read_text(encoding="utf-8")
    )
    assert summary["paid_agent_result_count"] == 10
    assert summary["predictive_validity_claim"]["supported"] is False
    assert len(snapshot["calls"]) == 10
    assert all(call["state"] == "completed" for call in snapshot["calls"])
    assert len(metrics["rows"]) == 42
