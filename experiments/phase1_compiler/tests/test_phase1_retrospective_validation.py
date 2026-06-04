from __future__ import annotations

import phase1_retrospective_validation as retro


def row(
    task_id: str,
    split: str = "B_real",
    terminal_status: str = "verified_pass",
    scoreable: str = "True",
    adapter_id: str = "codex_workspace",
    prefix: str = "codex_kilo_workspace_followup",
) -> dict[str, str]:
    return {
        "adapter_id": adapter_id,
        "acut_id": f"{adapter_id}_gpt",
        "harness_name": adapter_id.removesuffix("_workspace"),
        "model_or_agent_name": "gpt-5.4-mini",
        "task_id": task_id,
        "split": split,
        "attempt": "1",
        "submission_status": "submitted",
        "terminal_status": terminal_status,
        "verifier_exit_code": "0",
        "scoreable_cell": scoreable,
        "agent_failure": "False",
        "harness_error": "False",
        "source_result_prefix": prefix,
    }


def test_outcome_seen_rows_are_allowed_only_for_retrospective_evidence_level() -> None:
    assert retro.validate_evidence_level("outcome_seen_retrospective_locked") is None

    try:
        retro.validate_evidence_level("clean_future_holdout")
    except ValueError as exc:
        assert "outcome-seen" in str(exc)
    else:
        raise AssertionError("clean future holdout evidence should not accept outcome-seen rows")


def test_primary_filter_excludes_click_and_humanize_rows() -> None:
    rows = [
        row("toolz__hist__001"),
        row("click__hist__001"),
        row("humanize__hist__001"),
    ]

    filtered = retro.primary_eligible_rows(
        rows,
        primary_repos={"toolz"},
        excluded_repos={"click", "generic_comparators"},
        diagnostic_only_repos={"humanize"},
    )

    assert [item["task_id"] for item in filtered] == ["toolz__hist__001"]


def test_toolz_stability_repeat_is_diagnostic_only() -> None:
    prefix_roles = retro.prefix_roles(
        primary_prefixes={"toolz": ["codex_kilo_workspace_followup"]},
        diagnostic_prefixes=["codex_kilo_workspace_stability"],
    )

    assert prefix_roles["codex_kilo_workspace_followup"] == "primary_retrospective"
    assert prefix_roles["codex_kilo_workspace_stability"] == "diagnostic_dev"


def test_b_to_w_error_uses_scoreable_pass_rates() -> None:
    rows = [
        row("toolz__hist__001", split="B_real", terminal_status="verified_pass"),
        row("toolz__hist__002", split="B_real", terminal_status="verified_fail"),
        row("toolz__hist__004", split="W_real", terminal_status="verified_fail"),
    ]

    metrics = retro.repo_adapter_metrics(rows)

    assert metrics["B_real"]["scoreable_cell_count"] == 2
    assert metrics["B_real"]["pass_rate"] == 0.5
    assert metrics["W_real"]["pass_rate"] == 0.0
    assert metrics["absolute_error"] == 0.5


def test_non_scoreable_rows_do_not_enter_pass_rate_denominators() -> None:
    rows = [
        row("boltons__hist__024", split="W_real", terminal_status="invalid_output", scoreable="False"),
        row("boltons__hist__026", split="W_real", terminal_status="verified_pass", scoreable="True"),
    ]

    metrics = retro.repo_adapter_metrics(rows)

    assert metrics["W_real"]["cell_count"] == 2
    assert metrics["W_real"]["scoreable_cell_count"] == 1
    assert metrics["W_real"]["non_scoreable_count"] == 1
    assert metrics["W_real"]["pass_rate"] == 1.0


def test_metrics_payload_never_claims_predictive_validity() -> None:
    payload = retro.metrics_payload(
        plan={"included_rows": []},
        rows=[],
        cost_summary={"observed_or_conservative_estimated_cost_usd": 1.0},
    )

    assert payload["evidence_level"] == "outcome_seen_retrospective_locked"
    assert payload["clean_future_holdout"] is False
    assert payload["predictive_validity_established"] is False
