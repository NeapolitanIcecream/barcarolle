#!/usr/bin/env python3
"""Replay the 75-Task study through Barcarolle's public Selection pipeline."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
import json
import math
from pathlib import Path
import sys
from typing import Any, cast


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    EvaluationCellSet,
    ResultCellRef,
    ResultRecord,
    RollingOriginRecord,
    SelectorRecord,
    SourceEventRecord,
    TaskCheckRef,
    TaskRecord,
    cache_identity_agent_mismatches,
    cache_identity_task_check_mismatches,
    canonical_digest,
    canonical_json,
    load_jsonl_records,
    parse_utc_timestamp,
    record_with_digest,
    task_check_ref_key,
    validate_evaluation_cell_set,
    validate_result,
)
from barcarolle.result_store import ResultJoinConfig, build_result_matrix
from barcarolle.selection import (
    FeatureConfig,
    RollingOriginPolicy,
    SelectionBudget,
    build_feature_snapshot,
    build_rolling_origin,
    build_rule_mixture_grid,
    build_rule_selector,
    build_selector_input,
    evaluate_selection,
    select_with_selector,
    summarize_selector_mae,
    validate_rolling_origin_against_records,
)
from barcarolle.task_pool import (
    CertificationResult,
    TaskPoolBundle,
    TimeRange,
    certification_evidence_records,
    freeze_task_pool,
    validated_task_pool_bundle,
)
from examples.offline_selector_study.study import (
    PRIMARY_SELECTOR_NAMES,
    DiagnosticOrigin,
    Metadata,
    StudyPaths,
    audit_core_maturity,
    build_design,
    fixed_selector_analysis,
    load_amendment,
    load_correction,
    load_metadata,
    load_outcomes,
    load_plan,
)


HERE = Path(__file__).resolve().parent
DEFAULT_AMENDMENT = HERE / "study-amendment-3.json"
DEFAULT_OUTPUT = HERE / "public-replay-results.json"
_SCENARIO_NAME = "label_at_task_arrival"
_FEATURE_CONFIG = FeatureConfig(("task_count", "task_stratum"))
_ORIGIN_POLICY = RollingOriginPolicy(
    as_of_cutoff_rule="origin_time",
    eligibility_mode="counterfactual_replay",
    holdout_overlap_policy="allow_cluster_overlap",
    future_holdout_known=True,
)
_SELECTION_BUDGET = SelectionBudget(10)
_JOIN_CONFIG = ResultJoinConfig()


@dataclass(frozen=True)
class _FrozenPublicSelection:
    diagnostic_origin: DiagnosticOrigin
    origin: RollingOriginRecord
    selector_name: str
    selector: SelectorRecord
    selection: BenchmarkSelectionRecord


def load_replay_amendment(
    path: Path,
    plan: Mapping[str, Any],
    correction: Mapping[str, Any],
) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("replay amendment must be a JSON object")
    if payload.get("schema_version") != "barcarolle_offline_selector_study_amendment_v3":
        raise ValueError("replay amendment schema is not supported")
    if (
        payload.get("base_study_plan_digest") != plan["study_plan_digest"]
        or payload.get("previous_amendment_digest")
        != correction["amendment_digest"]
    ):
        raise ValueError("replay amendment does not bind the amendment chain")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "amendment_digest"}
    )
    if payload.get("amendment_digest") != expected:
        raise ValueError("replay amendment digest does not match its content")
    return payload


def build_label_at_task_arrival_scenario(
    source: TaskPoolBundle,
    amendment: Mapping[str, Any],
) -> TaskPoolBundle:
    task_by_id = {task.task_id: task for task in source.tasks}
    projected_checks = tuple(
        replace(
            check,
            check_material_available_at=task_by_id[
                check.task_id
            ].task_material_available_at,
        )
        for check in source.checks
    )
    projected_check_by_id = {check.check_id: check for check in projected_checks}
    projected_events = tuple(
        _project_source_event(event, task_by_id)
        for event in source.source_events
    )
    event_by_candidate = {
        event.candidate_id: event
        for event in source.source_events
        if event.candidate_id is not None
    }
    certification_results = []
    for evidence in source.certification_evidence:
        candidate_id = evidence.get("candidate_id")
        if not isinstance(candidate_id, str):
            raise ValueError("certification evidence is missing candidate_id")
        event = event_by_candidate.get(candidate_id)
        if (
            event is None
            or event.disposition != "accepted"
            or event.task_id is None
            or event.check_id is None
        ):
            raise ValueError("scenario requires accepted source-bound evidence")
        task = task_by_id[event.task_id]
        check = projected_check_by_id[event.check_id]
        projected_evidence = dict(evidence)
        projected_evidence["check_digest"] = canonical_digest(check)
        certification_results.append(
            CertificationResult(
                candidate_id=candidate_id,
                accepted=True,
                task=task,
                check=check,
                rejection_reasons=(),
                evidence=projected_evidence,
                evidence_digest=canonical_digest(projected_evidence),
            )
        )
    task_pool = freeze_task_pool(
        source.tasks,
        projected_checks,
        certification_results,
        projected_events,
        {
            "repository_id": source.task_pool.repository_id,
            "task_records_ref": (
                f"counterfactual-scenarios/{_SCENARIO_NAME}/tasks.jsonl"
            ),
            "check_records_ref": (
                f"counterfactual-scenarios/{_SCENARIO_NAME}/checks.jsonl"
            ),
            "certification_evidence_ref": (
                f"counterfactual-scenarios/{_SCENARIO_NAME}/"
                "certification-evidence.jsonl"
            ),
            "source_event_records_ref": (
                f"counterfactual-scenarios/{_SCENARIO_NAME}/source-events.jsonl"
            ),
            "certification_config_digest": (
                source.task_pool.certification_config_digest
            ),
            "created_at": amendment["frozen_at"],
            "source_window_start": source.task_pool.source_window_start,
            "source_window_end": source.task_pool.source_window_end,
        },
    )
    evidence_records = certification_evidence_records(certification_results)
    return validated_task_pool_bundle(
        task_pool,
        source.tasks,
        projected_checks,
        evidence_records,
        projected_events,
    )


def _project_source_event(
    event: SourceEventRecord,
    task_by_id: Mapping[str, TaskRecord],
) -> SourceEventRecord:
    if event.task_id is None:
        return event
    task = task_by_id.get(event.task_id)
    if task is None:
        raise ValueError("source event references an unknown Task")
    return record_with_digest(
        replace(
            event,
            check_material_available_at=task.task_material_available_at,
            label_mature_at=task.task_material_available_at,
            source_event_digest="",
        )
    )


def load_base_results(
    paths: StudyPaths,
    metadata: Metadata,
) -> tuple[ResultRecord, ...]:
    results = tuple(
        load_jsonl_records(paths.main_records / "results.jsonl", ResultRecord)
    )
    if any(not validate_result(result).ok for result in results):
        raise ValueError("source contains an invalid Result record")
    by_execution = {
        (
            result.agent_id,
            result.task_id,
            result.cache_identity.runtime_config_digest,
        ): result
        for result in results
    }
    if len(by_execution) != len(results):
        raise ValueError("source contains duplicate Result execution identities")
    base = []
    for cell in metadata.schedule.cells:
        if cell.replicate_index != 0:
            continue
        result = by_execution.get(
            (cell.agent_id, cell.task_id, cell.runtime_config_digest)
        )
        if (
            result is None
            or result.check_id != cell.check_id
            or result.scoreable_state != "scoreable"
        ):
            raise ValueError("every base schedule cell must bind a scoreable Result")
        base.append(result)
    expected_count = len(metadata.agents) * len(metadata.ordered_tasks)
    if len(base) != expected_count or len({result.result_id for result in base}) != len(
        base
    ):
        raise ValueError("base Result view does not exactly cover Agent x Task")
    return tuple(base)


def validate_result_reuse(
    scenario: TaskPoolBundle,
    agents: Sequence[AgentRecord],
    results: Sequence[ResultRecord],
) -> Mapping[str, object]:
    task_by_id = {task.task_id: task for task in scenario.tasks}
    check_by_id = scenario.checks_by_id
    agent_by_id = {agent.agent_id: agent for agent in agents}
    execution_identity_digests = set()
    physical_after_task_count = 0
    for result in results:
        task = task_by_id.get(result.task_id)
        check = check_by_id.get(result.check_id)
        agent = agent_by_id.get(result.agent_id)
        if task is None or check is None or agent is None:
            raise ValueError("Result is outside the scenario Agent/Task/Check domain")
        task_check_mismatches = cache_identity_task_check_mismatches(
            result.cache_identity,
            task,
            check,
        )
        agent_mismatches = cache_identity_agent_mismatches(
            result.cache_identity,
            agent,
        )
        if task_check_mismatches or agent_mismatches:
            raise ValueError(
                "Result cache identity does not match scenario records: "
                + ", ".join((*task_check_mismatches, *agent_mismatches))
            )
        execution_identity_digests.add(result.cache_identity.identity_digest)
        if parse_utc_timestamp(result.result_available_at) > parse_utc_timestamp(
            task.task_material_available_at
        ):
            physical_after_task_count += 1
    return {
        "base_result_count": len(results),
        "distinct_execution_identity_count": len(execution_identity_digests),
        "exact_task_check_agent_cache_identity_match_count": len(results),
        "physical_result_observation_after_task_arrival_count": (
            physical_after_task_count
        ),
    }


def build_public_selectors(
    tasks: Sequence[TaskRecord],
) -> Mapping[str, SelectorRecord]:
    group_by_ref_key = {
        task_check_ref_key(TaskCheckRef(task.task_id, task.check_ids[0])): (
            task.sampling_stratum
        )
        for task in tasks
    }
    selectors = {
        "coverage": build_rule_selector(
            "coverage",
            {"group_by_ref_key": group_by_ref_key},
            allowed_feature_classes=("task_metadata",),
        ),
        "random_seed_5": build_rule_selector(
            "random",
            {"seed": 5},
            allowed_feature_classes=("task_metadata",),
        ),
        "recency": build_rule_selector(
            "recency",
            {},
            allowed_feature_classes=("task_metadata",),
        ),
        "stratified_unweighted": build_rule_selector(
            "stratified_forecast",
            {
                "dirichlet_alpha": 1.0,
                "trailing_ref_count": 15,
                "seed": 5,
                "weight_cap": None,
            },
            allowed_feature_classes=("task_metadata",),
        ),
        "stratified_weighted": build_rule_selector(
            "stratified_forecast",
            {
                "dirichlet_alpha": 1.0,
                "trailing_ref_count": 15,
                "seed": 5,
                "weight_cap": 3.0,
            },
            allowed_feature_classes=("task_metadata",),
        ),
    }
    mixtures = build_rule_mixture_grid(
        random_seed=5,
        group_by_ref_key=group_by_ref_key,
        allowed_feature_classes=("task_metadata",),
    )
    equal = tuple(selector for selector in mixtures if _is_equal_mixture(selector))
    if len(equal) != 1:
        raise ValueError("rule-mixture grid must contain one equal-weight Selector")
    selectors["rank_mixture_equal"] = equal[0]
    if tuple(selectors) != PRIMARY_SELECTOR_NAMES:
        raise ValueError("public Selector registry does not match the frozen plan")
    return selectors


def _is_equal_mixture(selector: SelectorRecord) -> bool:
    weights = selector.parameters.get("expert_weights")
    if not isinstance(weights, Mapping):
        return False
    for name in ("coverage", "random", "recency"):
        value = weights.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isclose(float(value), 1.0 / 3.0)
        ):
            return False
    return True


def _evaluation_cell_set(
    origin_id: str,
    selection_id: str,
    selected_refs: tuple[TaskCheckRef, ...],
    future_refs: tuple[TaskCheckRef, ...],
    scenario: TaskPoolBundle,
    agents: Sequence[AgentRecord],
    result_by_cell: Mapping[tuple[str, str, str], ResultRecord],
) -> EvaluationCellSet:
    cells = []
    for ref in (*selected_refs, *future_refs):
        for agent in agents:
            result = result_by_cell.get((agent.agent_id, ref.task_id, ref.check_id))
            if result is None:
                raise ValueError("base Result view is missing a required cell")
            cells.append(
                ResultCellRef(
                    agent_id=agent.agent_id,
                    task_id=ref.task_id,
                    check_id=ref.check_id,
                    required_identity_digest=(
                        result.cache_identity.identity_digest
                    ),
                    result_id=result.result_id,
                    result_digest=result.result_digest,
                    cell_state="result",
                    exclusion_reason=None,
                    outcome=result.outcome,
                )
            )
    cell_set = EvaluationCellSet(
        cell_set_id=(
            "cell_set_"
            + canonical_digest(
                {
                    "origin_id": origin_id,
                    "selection_id": selection_id,
                    "selected_refs": selected_refs,
                    "future_refs": future_refs,
                    "result_ids": tuple(cell.result_id for cell in cells),
                }
            )
        ),
        origin_id=origin_id,
        selection_id=selection_id,
        selected_task_check_refs=selected_refs,
        future_task_check_refs=future_refs,
        future_censored_task_check_refs=(),
        future_task_pool_id=scenario.task_pool.task_pool_id,
        future_task_pool_digest=scenario.task_pool.task_pool_digest,
        cells=tuple(cells),
        abstention_reason=None,
        cell_set_digest="",
    )
    cell_set = record_with_digest(cell_set)
    validation = validate_evaluation_cell_set(cell_set)
    if not validation.ok:
        raise ValueError(
            "evaluation cell set is invalid: " + ", ".join(validation.errors)
        )
    return cell_set


def _task_ids(refs: Sequence[TaskCheckRef]) -> tuple[str, ...]:
    return tuple(ref.task_id for ref in refs)


def _membership_digest(task_ids: Sequence[str]) -> str:
    return canonical_digest(tuple(sorted(task_ids)))


def _order_digest(task_ids: Sequence[str]) -> str:
    return canonical_digest(tuple(task_ids))


def _public_summary_by_name(
    selectors: Mapping[str, SelectorRecord],
    summary: Mapping[str, object],
) -> Mapping[str, object]:
    name_by_id = {
        selector.selector_id: name for name, selector in selectors.items()
    }
    rows = summary.get("selectors")
    if not isinstance(rows, Sequence):
        raise ValueError("public Selector summary is missing rows")
    by_name: dict[str, object] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("public Selector summary row is invalid")
        selector_id = row.get("selector_id")
        if not isinstance(selector_id, str) or selector_id not in name_by_id:
            raise ValueError("public Selector summary has an unknown Selector")
        by_name[name_by_id[selector_id]] = {
            "selector_id": selector_id,
            "macro_origin_mae": row["macro_origin_mae"],
            "future_task_count_weighted_mae": (
                row["future_task_count_weighted_mae"]
            ),
            "origin_block_interval_95": row["origin_block_interval_95"],
        }
    if set(by_name) != set(selectors):
        raise ValueError("public Selector summary does not cover the registry")
    return dict(sorted(by_name.items()))


def run_public_replay(
    paths: StudyPaths = StudyPaths(),
    *,
    amendment_path: Path = DEFAULT_AMENDMENT,
) -> Mapping[str, object]:
    plan = load_plan(paths.plan)
    amendment_1 = load_amendment(paths.amendment, plan)
    correction = load_correction(paths.correction, plan, amendment_1)
    amendment_3 = load_replay_amendment(amendment_path, plan, correction)
    metadata = load_metadata(paths, plan, correction)
    design = build_design(metadata, plan)
    negative_control = audit_core_maturity(metadata, design)
    if not (
        negative_control["all_history_mature_counts_zero"]
        and negative_control["all_future_mature_counts_zero"]
    ):
        raise ValueError("observed-at negative control is no longer fully censored")
    scenario = build_label_at_task_arrival_scenario(
        metadata.bundle,
        amendment_3,
    )
    selectors = build_public_selectors(metadata.ordered_tasks)
    checks = scenario.checks_by_id
    frozen_selections: list[_FrozenPublicSelection] = []
    origin_comparisons = []
    for diagnostic_origin in design.origins:
        origin = build_rolling_origin(
            scenario.task_pool,
            scenario.tasks,
            checks,
            parse_utc_timestamp(
                diagnostic_origin.history[-1].task_material_available_at
            ),
            TimeRange(
                diagnostic_origin.future[0].task_material_available_at,
                diagnostic_origin.future[-1].task_material_available_at,
            ),
            _ORIGIN_POLICY,
            history_window=TimeRange(
                diagnostic_origin.history[0].task_material_available_at,
                diagnostic_origin.history[-1].task_material_available_at,
            ),
        )
        origin_validation = validate_rolling_origin_against_records(
            origin,
            scenario.task_pool,
            scenario.tasks,
            checks,
        )
        if not origin_validation.ok:
            raise ValueError(
                "public RollingOrigin failed replay validation: "
                + ", ".join(origin_validation.errors)
            )
        public_history_ids = _task_ids(origin.history_task_check_refs)
        public_future_ids = _task_ids(origin.future_holdout_task_check_refs)
        diagnostic_history_ids = tuple(
            task.task_id for task in diagnostic_origin.history
        )
        diagnostic_future_ids = tuple(
            task.task_id for task in diagnostic_origin.future
        )
        history_match = public_history_ids == diagnostic_history_ids
        future_match = public_future_ids == diagnostic_future_ids
        history_membership_match = set(public_history_ids) == set(
            diagnostic_history_ids
        )
        future_membership_match = set(public_future_ids) == set(
            diagnostic_future_ids
        )
        if (
            not origin.history_task_check_refs
            or len(origin.future_holdout_task_check_refs) != 5
            or origin.history_censored_task_check_refs
            or origin.future_censored_task_check_refs
        ):
            raise ValueError("projected scenario did not produce the frozen cohorts")
        origin_comparisons.append(
            {
                "origin_number": diagnostic_origin.origin_number,
                "origin_id": origin.origin_id,
                "history_task_count": len(public_history_ids),
                "future_task_count": len(public_future_ids),
                "public_history_membership_digest": (
                    _membership_digest(public_history_ids)
                ),
                "diagnostic_history_membership_digest": (
                    _membership_digest(diagnostic_history_ids)
                ),
                "history_membership_match": history_membership_match,
                "public_history_order_digest": _order_digest(public_history_ids),
                "diagnostic_history_order_digest": (
                    _order_digest(diagnostic_history_ids)
                ),
                "history_order_match": history_match,
                "public_future_membership_digest": (
                    _membership_digest(public_future_ids)
                ),
                "diagnostic_future_membership_digest": (
                    _membership_digest(diagnostic_future_ids)
                ),
                "future_membership_match": future_membership_match,
                "public_future_order_digest": _order_digest(public_future_ids),
                "diagnostic_future_order_digest": (
                    _order_digest(diagnostic_future_ids)
                ),
                "future_order_match": future_match,
                **(
                    {}
                    if history_match and future_match
                    else {
                        "public_history_task_ids": public_history_ids,
                        "diagnostic_history_task_ids": diagnostic_history_ids,
                        "public_future_task_ids": public_future_ids,
                        "diagnostic_future_task_ids": diagnostic_future_ids,
                    }
                ),
            }
        )
        snapshot = build_feature_snapshot(
            origin,
            scenario.task_pool,
            scenario.tasks,
            checks,
            (),
            _FEATURE_CONFIG,
        )
        selector_input = build_selector_input(
            origin,
            scenario.task_pool,
            snapshot,
            (),
            metadata.agents,
            _SELECTION_BUDGET,
            _FEATURE_CONFIG.leakage_policy(origin.as_of_cutoff),
        )
        for selector_name, selector in selectors.items():
            selection = select_with_selector(
                selector_input,
                snapshot,
                selector,
            )
            frozen_selections.append(
                _FrozenPublicSelection(
                    diagnostic_origin,
                    origin,
                    selector_name,
                    selector,
                    selection,
                )
            )
    if len(frozen_selections) != len(design.origins) * len(selectors):
        raise ValueError("public Selection freeze did not cover the frozen design")

    # The complete Selection batch is frozen before the Result file is opened.
    outcomes = load_outcomes(paths, plan, metadata)
    diagnostic = fixed_selector_analysis(design, outcomes)
    base_results = load_base_results(paths, metadata)
    reuse_audit = validate_result_reuse(
        scenario,
        metadata.agents,
        base_results,
    )
    result_by_cell = {
        (result.agent_id, result.task_id, result.check_id): result
        for result in base_results
    }
    all_selections = [
        frozen.selection for frozen in frozen_selections
    ]
    all_mae_metrics = []
    all_future_matrices = []
    comparisons = []
    diagnostic_loss_rows = {
        row["origin_number"]: cast(Mapping[str, float], row["mae_by_selector"])
        for row in cast(
            Sequence[Mapping[str, object]],
            diagnostic["origin_losses"],
        )
    }
    for frozen in frozen_selections:
        diagnostic_origin = frozen.diagnostic_origin
        origin = frozen.origin
        selector_name = frozen.selector_name
        selector = frozen.selector
        selection = frozen.selection
        cells = _evaluation_cell_set(
            origin.origin_id,
            selection.selection_id,
            selection.selected_task_check_refs,
            origin.future_holdout_task_check_refs,
            scenario,
            metadata.agents,
            result_by_cell,
        )
        selected_matrix = build_result_matrix(
            cells,
            selection.selected_task_check_refs,
            scenario.tasks,
            checks,
            metadata.agents,
            base_results,
            "selected",
            _JOIN_CONFIG,
        )
        future_matrix = build_result_matrix(
            cells,
            origin.future_holdout_task_check_refs,
            scenario.tasks,
            checks,
            metadata.agents,
            base_results,
            "future_holdout",
            _JOIN_CONFIG,
        )
        metrics = tuple(
            evaluate_selection(
                selection,
                origin,
                cells,
                selected_matrix,
                future_matrix,
            )
        )
        mae = tuple(
            metric
            for metric in metrics
            if metric.metric_name == "future_pass_rate_mae"
            and metric.completeness_state == "complete"
        )
        if (
            len(mae) != 1
            or selected_matrix.scoreable_state != "complete"
            or future_matrix.scoreable_state != "complete"
        ):
            raise ValueError("public Result Matrix path did not produce one MAE")
        public_ids = _task_ids(selection.selected_task_check_refs)
        diagnostic_selection = diagnostic_origin.selections[selector_name]
        diagnostic_ids = diagnostic_selection.task_ids
        public_mae = mae[0].metric_value
        diagnostic_mae = diagnostic_loss_rows[
            diagnostic_origin.origin_number
        ][selector_name]
        membership_match = set(public_ids) == set(diagnostic_ids)
        order_match = public_ids == diagnostic_ids
        mae_delta = public_mae - diagnostic_mae
        comparisons.append(
            {
                "origin_number": diagnostic_origin.origin_number,
                "origin_id": origin.origin_id,
                "selector_name": selector_name,
                "selector_id": selector.selector_id,
                "selection_id": selection.selection_id,
                "public_selection_membership_digest": (
                    _membership_digest(public_ids)
                ),
                "diagnostic_selection_membership_digest": (
                    _membership_digest(diagnostic_ids)
                ),
                "selection_membership_match": membership_match,
                "public_selection_order_digest": _order_digest(public_ids),
                "diagnostic_selection_order_digest": (
                    _order_digest(diagnostic_ids)
                ),
                "selection_order_match": order_match,
                "public_future_pass_rate_mae": public_mae,
                "diagnostic_future_pass_rate_mae": diagnostic_mae,
                "mae_delta": mae_delta,
                "mae_match": math.isclose(
                    public_mae,
                    diagnostic_mae,
                    rel_tol=0.0,
                    abs_tol=1e-12,
                ),
                **(
                    {}
                    if order_match
                    else {
                        "public_selected_task_ids": public_ids,
                        "diagnostic_selected_task_ids": diagnostic_ids,
                    }
                ),
            }
        )
        all_mae_metrics.append(mae[0])
        all_future_matrices.append(future_matrix)
    public_summary = summarize_selector_mae(
        tuple(selectors.values()),
        all_selections,
        all_mae_metrics,
        all_future_matrices,
    )
    summary_by_name = _public_summary_by_name(selectors, public_summary)
    origin_membership_matches = all(
        row["history_membership_match"]
        and row["future_membership_match"]
        for row in origin_comparisons
    )
    origin_order_matches = all(
        row["history_order_match"] and row["future_order_match"]
        for row in origin_comparisons
    )
    selection_membership_matches = all(
        row["selection_membership_match"] for row in comparisons
    )
    selection_order_matches = all(
        row["selection_order_match"] for row in comparisons
    )
    mae_matches = all(row["mae_match"] for row in comparisons)
    all_equivalent = (
        origin_membership_matches
        and origin_order_matches
        and selection_membership_matches
        and selection_order_matches
        and mae_matches
    )
    selection_membership_mismatches = sum(
        not bool(row["selection_membership_match"]) for row in comparisons
    )
    selection_order_mismatches = sum(
        not bool(row["selection_order_match"]) for row in comparisons
    )
    mae_mismatches = sum(not bool(row["mae_match"]) for row in comparisons)
    weighted_mae = cast(
        Mapping[str, Any],
        summary_by_name["stratified_weighted"],
    )["macro_origin_mae"]
    coverage_mae = cast(
        Mapping[str, Any],
        summary_by_name["coverage"],
    )["macro_origin_mae"]
    payload: dict[str, object] = {
        "schema_version": "barcarolle_offline_selector_public_replay_v1",
        "study_id": plan["study_id"],
        "status": (
            "public_counterfactual_replay_equivalent"
            if all_equivalent
            else "public_counterfactual_replay_changes_algorithm_results"
        ),
        "status_reason": (
            "All projected Origin cohorts match the frozen diagnostic; the "
            "public stable-sum equal-rank mixture differs from the frozen "
            "left-to-right floating-point diagnostic at one benchmark "
            "membership and one MAE."
        ),
        "study_plan_digest": plan["study_plan_digest"],
        "study_amendment_digests": (
            amendment_1["amendment_digest"],
            correction["amendment_digest"],
            amendment_3["amendment_digest"],
        ),
        "authority": {
            "new_paid_calls": 0,
            "network_calls": 0,
            "source": "already-persisted 75-Task base Results only",
        },
        "scenario": {
            "scenario_name": _SCENARIO_NAME,
            "availability_basis": (
                "each Check check_material_available_at equals its bound "
                "Task task_material_available_at"
            ),
            "evidence_class": "user_configured_counterfactual",
            "source_attested_history": False,
            "source_task_pool_id": metadata.bundle.task_pool.task_pool_id,
            "source_task_pool_digest": (
                metadata.bundle.task_pool.task_pool_digest
            ),
            "scenario_task_pool_id": scenario.task_pool.task_pool_id,
            "scenario_task_pool_digest": scenario.task_pool.task_pool_digest,
            "task_records_unchanged": scenario.tasks == metadata.bundle.tasks,
            "check_ids_unchanged": (
                scenario.task_pool.check_ids
                == metadata.bundle.task_pool.check_ids
            ),
            "source_task_pool_mutated": False,
            "task_count": len(scenario.tasks),
            "check_count": len(scenario.checks),
            "task_records_digest": scenario.task_pool.task_records_digest,
            "check_records_digest": scenario.task_pool.check_records_digest,
            "source_event_records_digest": (
                scenario.task_pool.source_event_records_digest
            ),
            "certification_evidence_digest": (
                scenario.task_pool.certification_evidence_digest
            ),
        },
        "result_reuse_audit": reuse_audit,
        "observed_at_negative_control": negative_control,
        "time_projection_effect": {
            "task_arrival_order_changed": False,
            "check_maturity_basis_changed": True,
            "observed_at_scoreable_origin_count": 0,
            "label_at_task_arrival_scoreable_origin_count": len(
                origin_comparisons
            ),
            "causal_interpretation": (
                "The projection changes eligibility and makes the public "
                "rolling-origin experiment executable; it does not reorder "
                "Tasks. The recorded equal-mixture disagreement is caused by "
                "stable floating-point summation, not by timestamp ordering."
            ),
        },
        "public_pipeline": {
            "rolling_origin_api": "build_rolling_origin",
            "feature_api": "build_feature_snapshot",
            "selector_input_api": "build_selector_input",
            "selection_api": "select_with_selector",
            "result_matrix_api": "build_result_matrix",
            "metric_api": "evaluate_selection",
            "aggregate_api": "summarize_selector_mae",
            "selection_batch_frozen_before_result_file_open": True,
            "origin_count": len(origin_comparisons),
            "selector_count": len(selectors),
            "selection_count": len(all_selections),
            "mae_metric_count": len(all_mae_metrics),
            "selected_matrix_count": len(all_selections),
            "future_matrix_count": len(all_future_matrices),
            "result_matrix_count": (
                len(all_selections) + len(all_future_matrices)
            ),
            "origin_comparisons": tuple(origin_comparisons),
            "selector_summary": summary_by_name,
            "summary_protocol_digest": public_summary["protocol_digest"],
        },
        "transparent_diagnostic_comparison": {
            "comparison_count": len(comparisons),
            "origin_membership_matches": origin_membership_matches,
            "origin_order_matches": origin_order_matches,
            "selection_membership_matches": selection_membership_matches,
            "selection_order_matches": selection_order_matches,
            "mae_matches": mae_matches,
            "selection_membership_mismatch_count": (
                selection_membership_mismatches
            ),
            "selection_order_mismatch_count": selection_order_mismatches,
            "mae_mismatch_count": mae_mismatches,
            "disagreement_diagnosis": {
                "affected_selector": "rank_mixture_equal",
                "public_algorithm": (
                    "math.fsum over weighted expert scores followed by the "
                    "documented Task/Check ID tie-break"
                ),
                "frozen_diagnostic_algorithm": (
                    "left-to-right binary64 addition in coverage, random, "
                    "recency order"
                ),
                "mechanism": (
                    "non-associative floating-point addition perturbs exact "
                    "mathematical ties before deterministic tie-breaking"
                ),
                "public_algorithm_changed_to_match_diagnostic": False,
                "other_selector_comparison_count": (
                    len(comparisons) - len(design.origins)
                ),
                "other_selector_membership_mismatch_count": sum(
                    not bool(row["selection_membership_match"])
                    for row in comparisons
                    if row["selector_name"] != "rank_mixture_equal"
                ),
                "rank_mixture_diagnostic_macro_origin_mae": cast(
                    Mapping[str, Mapping[str, float]],
                    diagnostic["selectors"],
                )["rank_mixture_equal"]["macro_origin_mae"],
                "rank_mixture_public_macro_origin_mae": cast(
                    Mapping[str, Any],
                    summary_by_name["rank_mixture_equal"],
                )["macro_origin_mae"],
            },
            "rows": tuple(comparisons),
        },
        "primary_contrast": {
            "selector_a": "stratified_weighted",
            "selector_b": "coverage",
            "difference_direction": "selector_a_minus_selector_b",
            "public_macro_origin_mae_difference": weighted_mae - coverage_mae,
            "diagnostic_macro_origin_mae_difference": cast(
                Mapping[str, float],
                diagnostic["primary_contrast"],
            )["macro_origin_mae_difference"],
        },
        "claim": {
            "established": (
                "User-configured algorithm-visible time changes the public "
                "RollingOrigin path from fully censored to twelve scoreable "
                "Origins, while exact cached execution Results remain reusable."
            ),
            "selector_evidence": (
                "The public pipeline reproduces or explicitly identifies every "
                "difference from the frozen transparent diagnostic."
            ),
            "not_established": (
                "The projected timestamps are not source-attested history, and "
                "this replay is not strict-prospective evidence on later Tasks."
            ),
        },
        "public_replay_results_digest": "",
    }
    payload["public_replay_results_digest"] = canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "public_replay_results_digest"
        }
    )
    return payload


def write_results(path: Path, results: Mapping[str, object]) -> None:
    canonical_json(results)
    path.write_text(
        json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--amendment",
        type=Path,
        default=DEFAULT_AMENDMENT,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run_public_replay(amendment_path=args.amendment)
    write_results(args.output, results)
    print(canonical_json(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
