from __future__ import annotations

from email.message import Message
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import cast

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import AgentRecord, ResultRecord  # noqa: E402
from examples.experiment_ledger import write_json  # noqa: E402
from examples.model_agent_study import study  # noqa: E402


def test_committed_study_plan_is_self_digested_and_budget_partitioned() -> None:
    plan = study._load_plan(study.DEFAULT_PLAN)
    budget = plan["budget"]
    assert isinstance(budget, dict)
    assert budget["total_usd"] == 300.0
    assert (
        budget["calibration_authority_usd"]
        + budget["main_and_repeat_authority_usd"]
        + budget["unallocated_reserve_usd"]
        == budget["total_usd"]
    )
    calibration = plan["calibration"]
    assert isinstance(calibration, dict)
    campaigns = calibration["campaigns"]
    assert isinstance(campaigns, list)
    assert sum(item["maximum_estimated_cost_usd"] for item in campaigns) == 90.0


def test_committed_amendment_is_self_digested_and_reallocates_budget() -> None:
    plan = study._load_plan(study.DEFAULT_PLAN)
    amendment = study._load_amendment(study.DEFAULT_AMENDMENT, plan)

    assert amendment["base_study_plan_digest"] == plan["study_plan_digest"]
    assert amendment["budget"]["protocol_canary_authority_usd"] == 6.0
    assert len(amendment["canaries"]) == 2


def test_decision_amendment_freezes_one_connected_replacement_panel() -> None:
    plan = study._load_plan(study.DEFAULT_PLAN)
    decision = study._load_decision_amendment(
        study.DEFAULT_DECISION_AMENDMENT,
        plan,
    )

    assert decision["previous_amendment_digest"] == study._load_amendment(
        study.DEFAULT_AMENDMENT,
        plan,
    )["amendment_digest"]
    assert decision["canary_eligible_agent_keys"] == ["gpt-5.4-mini-high"]
    assert len(decision["replacement_calibration_campaigns"]) == 1
    assert decision["control_agent_key"] == "gpt-5.6-terra-high"


def test_study_agent_homes_are_distinct_for_same_effort(tmp_path: Path) -> None:
    first = _agent("first-high", "model-a")
    second = _agent("second-high", "model-b")

    first_command = study._agent_command(tmp_path, first)
    second_command = study._agent_command(tmp_path, second)

    first_home = next(
        item for item in first_command if item.startswith("BARCAROLLE_CODEX_HOME=")
    )
    second_home = next(
        item for item in second_command if item.startswith("BARCAROLLE_CODEX_HOME=")
    )
    assert first_home != second_home
    assert first_command[1] == "BARCAROLLE_CODEX_MODEL=model-a"
    assert second_command[1] == "BARCAROLLE_CODEX_MODEL=model-b"


def test_global_quota_guard_reserves_the_full_per_call_limit() -> None:
    plan = study._load_plan(study.DEFAULT_PLAN)
    campaign = study._calibration_campaign_config(
        plan,
        "model-calibration-frontier-2026-07-25",
    )
    budget = plan["budget"]
    assert isinstance(budget, dict)
    maximum = budget["quota_maximum_total_used"]
    assert isinstance(maximum, int)
    reserve = int(campaign["maximum_estimated_cost_per_call_usd"] * 500000)

    study._require_global_quota_guard(
        plan,
        {
            "total_granted": 1_500_000_000,
            "total_used": maximum - reserve,
            "total_available": 1_500_000_000 - maximum + reserve,
        },
        campaign,
    )
    with pytest.raises(RuntimeError, match="cannot cover"):
        study._require_global_quota_guard(
            plan,
            {
                "total_granted": 1_500_000_000,
                "total_used": maximum - reserve + 1,
                "total_available": 1_500_000_000 - maximum + reserve - 1,
            },
            campaign,
        )


def test_quota_checkpoint_uses_live_balance_once_per_six_cells(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "study"
    output.mkdir()
    ledger = {
        "gateway_accounting": {
            "baseline_total_used": 1000,
            "baseline_total_available": 9000,
            "latest_live_total_used": 1150,
            "latest_live_observed_at": "2026-07-25T00:00:00Z",
        },
        "entries": [
            {
                "gateway_quota_before": 1100,
                "gateway_quota_after": None,
            },
            {
                "gateway_quota_before": 1100,
                "gateway_quota_after": 1150,
            },
        ],
    }
    write_json(output / study.STUDY_LEDGER_NAME, ledger)
    paths = study.StudyPaths(
        plan_path=study.DEFAULT_PLAN,
        study_output=output,
        pilot_output=tmp_path / "pilot",
    )
    live = {
        "total_granted": 10_000,
        "total_used": 1200,
        "total_available": 8800,
    }
    monkeypatch.setattr(study, "_gateway_quota", lambda: live)
    monkeypatch.setattr(study, "_utc_now", lambda: "2026-07-25T00:10:00Z")

    observed_live, live_source, live_at = study._quota_checkpoint_for_cell(paths, 12)
    observed_cached, cached_source, cached_at = study._quota_checkpoint_for_cell(
        paths,
        13,
    )

    assert observed_live == live
    assert live_source == "live_six_cell_checkpoint"
    assert live_at == "2026-07-25T00:10:00Z"
    assert observed_cached == {
        "total_granted": 10_000,
        "total_used": 1150,
        "total_available": 8850,
    }
    assert cached_source == "cached_between_six_cell_checkpoints"
    assert cached_at == "2026-07-25T00:00:00Z"


def test_quota_checkpoint_reuses_a_recent_live_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "study"
    output.mkdir()
    write_json(
        output / study.STUDY_LEDGER_NAME,
        {
            "gateway_accounting": {
                "baseline_total_used": 1000,
                "baseline_total_available": 9000,
                "latest_live_total_used": 1200,
                "latest_live_observed_at": "2026-07-25T00:00:00Z",
            },
            "entries": [],
        },
    )
    paths = study.StudyPaths(
        plan_path=study.DEFAULT_PLAN,
        study_output=output,
        pilot_output=tmp_path / "pilot",
    )
    monkeypatch.setattr(study, "_utc_now", lambda: "2026-07-25T00:04:59Z")
    monkeypatch.setattr(
        study,
        "_gateway_quota",
        lambda: pytest.fail("recent live quota should be reused"),
    )

    observed, source, observed_at = study._quota_checkpoint_for_cell(paths, 0)

    assert observed["total_used"] == 1200
    assert source == "recent_live_checkpoint_reuse"
    assert observed_at == "2026-07-25T00:00:00Z"


def test_pending_receipt_must_close_before_the_next_six_cell_block(
    tmp_path: Path,
) -> None:
    output = tmp_path / "study"
    output.mkdir()
    write_json(
        output / study.STUDY_LEDGER_NAME,
        {
            "gateway_accounting": {},
            "entries": [
                {
                    "campaign_id": "campaign-a",
                    "sequence_index": 4,
                    "gateway_log_receipt": None,
                }
            ],
        },
    )
    paths = study.StudyPaths(
        plan_path=study.DEFAULT_PLAN,
        study_output=output,
        pilot_output=tmp_path / "pilot",
    )

    study._require_no_overdue_campaign_receipts(paths, "campaign-a", 5)
    with pytest.raises(RuntimeError, match="prior campaign block"):
        study._require_no_overdue_campaign_receipts(paths, "campaign-a", 6)


def test_non_scoreable_result_stops_a_paid_campaign() -> None:
    invalid = cast(
        ResultRecord,
        SimpleNamespace(
            result_id="result-invalid",
            scoreable_state="agent_invalid",
        ),
    )

    with pytest.raises(RuntimeError, match="result-invalid"):
        study._require_scoreable_results((invalid,), "campaign-a")


def test_main_selection_keeps_performance_then_seeks_disagreement() -> None:
    rows = {
        "best": _agent_row(7, 5.0, "a"),
        "same": _agent_row(7, 6.0, "a"),
        "diverse": _agent_row(6, 6.0, "b"),
        "weak": _agent_row(3, 1.0, "c"),
    }
    outcomes = {
        ("best", "t1"): "pass",
        ("best", "t2"): "pass",
        ("same", "t1"): "pass",
        ("same", "t2"): "pass",
        ("diverse", "t1"): "fail",
        ("diverse", "t2"): "pass",
        ("weak", "t1"): "fail",
        ("weak", "t2"): "fail",
    }

    assert study._select_main_agents({}, rows, outcomes) == ("best", "diverse")


def test_cluster_bootstrap_and_exact_mcnemar_are_deterministic() -> None:
    first = study._cluster_bootstrap_interval(
        {"cluster-a": (0.0, 0.0), "cluster-b": (1.0,)},
        seed=7,
        iterations=200,
    )
    second = study._cluster_bootstrap_interval(
        {"cluster-b": (1.0,), "cluster-a": (0.0, 0.0)},
        seed=7,
        iterations=200,
    )

    assert first == second
    assert 0.0 <= first["lower"] <= first["upper"] <= 1.0
    assert study._mcnemar_exact_two_sided(0, 0) == 1.0
    assert study._mcnemar_exact_two_sided(4, 0) == 0.125


def test_resource_ledger_separates_call_windows_from_global_movement(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / "resource-ledger.json"
    ledger = {
        "gateway_accounting": {"baseline_total_used": 1000},
    }
    write_json(ledger_path, ledger)
    entries = [
        {
            "action": "execute frozen benchmark campaign cell",
            "estimated_cost_usd": 0.1,
            "gateway_quota_delta": 10,
            "gateway_log_quota_points": 8,
        },
        {
            "action": "execute frozen benchmark campaign cell",
            "estimated_cost_usd": 0.2,
            "gateway_quota_delta": 20,
            "gateway_log_quota_points": 19,
        },
    ]

    study._write_study_resource_ledger(
        ledger_path,
        ledger,
        entries,
        points_per_usd=500_000,
        latest_gateway_total_used=1100,
    )

    observed = study._load_json(ledger_path)
    totals = {item["resource"]: item["amount"] for item in observed["totals"]}
    assert totals["observed_gateway_attributed_quota"] == 27
    assert totals["gateway_balance_window_delta_sum"] == 30
    assert totals["observed_gateway_global_total_used_movement"] == 100


def test_gateway_log_receipt_requires_exact_result_token_totals() -> None:
    result = cast(
        ResultRecord,
        SimpleNamespace(
            started_at="2026-07-25T00:00:00Z",
            finished_at="2026-07-25T00:00:10Z",
            cache_identity=SimpleNamespace(requested_model_id="model-a"),
            usage={"input_tokens": 30, "output_tokens": 7},
            scoreable_state="scoreable",
        ),
    )
    rows = (
        _gateway_row(1784937602, "model-a", 20, 5, 11, "request-a"),
        _gateway_row(1784937607, "model-a", 10, 2, 13, "request-b"),
        _gateway_row(1784937605, "model-b", 999, 999, 999, "other-model"),
    )

    receipt = study._gateway_log_receipt(result, rows)

    assert receipt["success_log_count"] == 2
    assert receipt["prompt_tokens"] == 30
    assert receipt["completion_tokens"] == 7
    assert receipt["quota_points"] == 24
    assert receipt["result_usage_match"] is True

    with pytest.raises(RuntimeError, match="do not exactly reconcile"):
        study._gateway_log_receipt(result, rows[:1])


def test_gateway_log_receipt_waits_for_all_result_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = cast(
        ResultRecord,
        SimpleNamespace(
            started_at="2026-07-25T00:00:00Z",
            finished_at="2026-07-25T00:00:10Z",
            cache_identity=SimpleNamespace(requested_model_id="model-a"),
            usage={"input_tokens": 30, "output_tokens": 7},
            scoreable_state="scoreable",
        ),
    )
    partial = (_gateway_row(1784937602, "model-a", 20, 5, 11, "request-a"),)
    complete = partial + (
        _gateway_row(1784937607, "model-a", 10, 2, 13, "request-b"),
    )
    observations = iter((partial, complete))
    sleeps: list[int] = []
    monkeypatch.setattr(study, "_gateway_token_logs", lambda: next(observations))
    monkeypatch.setattr(study.time, "sleep", sleeps.append)

    receipt = study._eventual_gateway_log_receipt(result, attempts=2)

    assert receipt["quota_points"] == 24
    assert sleeps == [1]


def test_gateway_metadata_rate_limit_fails_after_one_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def rate_limited(*_args: object, **_kwargs: object) -> None:
        nonlocal calls
        calls += 1
        headers = Message()
        headers["Retry-After"] = "1200"
        raise study.urllib.error.HTTPError(
            "https://proxy.invalid/api/log/token",
            429,
            "rate limited",
            headers,
            None,
        )

    monkeypatch.setenv("LLM_BASE_URL", "https://proxy.invalid/v1")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr(study.urllib.request, "urlopen", rate_limited)
    monkeypatch.setattr(
        study.time,
        "sleep",
        lambda _seconds: pytest.fail("a fixed-window 429 must not be polled"),
    )

    with pytest.raises(RuntimeError, match="retry after 1200 seconds"):
        study._gateway_json("/api/log/token")
    assert calls == 1


def test_gateway_token_log_credential_stays_out_of_the_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths: list[str] = []

    def gateway_json(path: str) -> dict[str, object]:
        paths.append(path)
        return {"success": True, "data": []}

    monkeypatch.setenv("LLM_API_KEY", "secret-query-unsafe-key")
    monkeypatch.setattr(study, "_gateway_json", gateway_json)

    assert study._gateway_token_logs() == ()
    assert paths == ["/api/log/token"]


def test_campaign_receipt_checkpoint_reconciles_one_snapshot_for_the_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "study"
    output.mkdir()
    write_json(
        output / study.STUDY_LEDGER_NAME,
        {
            "gateway_accounting": {
                "baseline_total_used": 1000,
                "latest_live_total_used": 1200,
                "quota_points_per_usd": 500_000,
            },
            "entries": [
                {
                    "action": "execute frozen benchmark campaign cell",
                    "campaign_id": "campaign-a",
                    "sequence_index": sequence_index,
                    "result_id": result_id,
                    "estimated_cost_usd": 0.1,
                    "gateway_log_receipt": None,
                }
                for sequence_index, result_id in enumerate(("result-a", "result-b"))
            ],
        },
    )
    paths = study.StudyPaths(
        plan_path=study.DEFAULT_PLAN,
        study_output=output,
        pilot_output=tmp_path / "pilot",
    )
    results = (
        _result_stub(
            "result-a",
            "2026-07-25T00:00:00Z",
            "2026-07-25T00:00:04Z",
            20,
            5,
        ),
        _result_stub(
            "result-b",
            "2026-07-25T00:00:05Z",
            "2026-07-25T00:00:10Z",
            30,
            7,
        ),
    )
    context = cast(
        study.ReplicateCampaignContext,
        SimpleNamespace(
            schedule=SimpleNamespace(campaign_id="campaign-a"),
            result_store=SimpleNamespace(path=tmp_path / "results.jsonl"),
        ),
    )
    rows = (
        _gateway_row(1784937602, "model-a", 20, 5, 11, "request-a"),
        _gateway_row(1784937607, "model-a", 30, 7, 13, "request-b"),
    )
    token_log_calls = 0

    def token_logs() -> tuple[dict[str, object], ...]:
        nonlocal token_log_calls
        token_log_calls += 1
        return rows

    monkeypatch.setattr(study, "load_jsonl_records", lambda *_args: results)
    monkeypatch.setattr(study, "_gateway_token_logs", token_logs)

    receipt = study._reconcile_campaign_pending_receipts(
        paths,
        study._load_plan(study.DEFAULT_PLAN),
        context,
        "result-b",
    )

    assert receipt["quota_points"] == 13
    assert token_log_calls == 1
    ledger = study._load_json(output / study.STUDY_LEDGER_NAME)
    assert [
        entry["gateway_log_receipt_status"] for entry in ledger["entries"]
    ] == ["exact", "exact"]


def _agent(agent_id: str, model: str) -> AgentRecord:
    return AgentRecord(
        agent_id=agent_id,
        agent_manifest_digest=f"manifest-{agent_id}",
        requested_model_id=model,
        model_snapshot_id=None,
        model_resolution_scope_id="campaign",
        model_resolution_scope_started_at="2026-07-25T00:00:00Z",
        model_resolution_scope_ended_at="2026-08-01T00:00:00Z",
        harness_digest="harness",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="retrieval",
        skills_digest="skills",
        network_policy_digest="network",
        adapter_digest="adapter",
    )


def _agent_row(passes: int, cost: float, provider: str) -> dict[str, object]:
    return {
        "scoreable_count": 12,
        "result_count": 12,
        "base_pass_count": passes,
        "repriced_estimated_cost_usd": cost,
        "attributed_gateway_cost_usd": cost,
        "provider_family": provider,
    }


def _gateway_row(
    created_at: int,
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    quota: int,
    request_id: str,
) -> dict[str, object]:
    return {
        "type": 2,
        "created_at": created_at,
        "model_name": model_name,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "quota": quota,
        "request_id": request_id,
    }


def _result_stub(
    result_id: str,
    started_at: str,
    finished_at: str,
    input_tokens: int,
    output_tokens: int,
) -> ResultRecord:
    return cast(
        ResultRecord,
        SimpleNamespace(
            result_id=result_id,
            started_at=started_at,
            finished_at=finished_at,
            cache_identity=SimpleNamespace(requested_model_id="model-a"),
            usage={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            scoreable_state="scoreable",
        ),
    )
