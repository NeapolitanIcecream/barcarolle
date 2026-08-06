#!/usr/bin/env python3
"""Replay the two frozen ALG-007 semantic rules across local repositories."""

from __future__ import annotations

# The extraction environment owns the optional parquet dependency.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
from dataclasses import dataclass, field
import hashlib
import json
from math import fsum, isfinite, sqrt
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.multi_repository_study.aggregate import (  # noqa: E402
    ContrastRow,
    summarize_contrasts,
)
from examples.multi_repository_study.public_replay import (  # noqa: E402
    TaskMetadata,
    build_repository_origins,
    future_pass_rate_mae,
    load_dataset_tasks,
    load_portfolio,
    load_public_outcomes,
    load_public_panel_plan,
    random_calibration,
)


HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "semantic-plan.json"
DEFAULT_PUBLIC_PLAN = HERE / "public-panel-plan.json"
DEFAULT_PORTFOLIO = HERE / "portfolio.json"
DEFAULT_PUBLIC_RESULTS = HERE / "public-panel-results.json"
DEFAULT_OUTPUT = HERE / "semantic-results.json"


@dataclass
class SimilarityIndex:
    vectors: Mapping[str, tuple[float, ...]]
    _cache: dict[tuple[str, str], float] = field(default_factory=dict)

    def similarity(self, left: str, right: str) -> float:
        key = (left, right) if left <= right else (right, left)
        if key not in self._cache:
            left_vector = self.vectors.get(left)
            right_vector = self.vectors.get(right)
            if left_vector is None or right_vector is None:
                raise ValueError("semantic index does not cover a Task")
            if len(left_vector) != len(right_vector):
                raise ValueError("semantic vectors have inconsistent dimensions")
            self._cache[key] = fsum(
                left_value * right_value
                for left_value, right_value in zip(
                    left_vector,
                    right_vector,
                    strict=True,
                )
            )
        return self._cache[key]


def load_semantic_plan(path: Path = DEFAULT_PLAN) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("semantic plan must be a JSON object")
    if payload.get("schema_version") != "barcarolle_multi_repository_semantic_plan_v1":
        raise ValueError("semantic plan schema is unsupported")
    digest = payload.get("semantic_plan_digest")
    expected = canonical_digest(
        {key: value for key, value in payload.items() if key != "semantic_plan_digest"}
    )
    if digest != expected:
        raise ValueError("semantic plan digest does not match")
    return payload


def load_embedding_artifact(
    path: Path,
    plan: Mapping[str, object],
    task_ids: Sequence[str],
) -> tuple[Mapping[str, tuple[float, ...]], Mapping[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("embedding artifact must be an object")
    digest = payload.pop("embedding_artifact_digest", None)
    if canonical_digest(payload) != digest:
        raise ValueError("embedding artifact digest does not match")
    if payload.get("schema_version") != "barcarolle_local_task_embeddings_v1":
        raise ValueError("embedding artifact schema is unsupported")
    if payload.get("semantic_plan_digest") != plan.get("semantic_plan_digest"):
        raise ValueError("embedding artifact does not bind the semantic plan")
    embedding_plan = _mapping(plan, "embedding")
    model = _mapping(payload, "model")
    for key in ("model_id", "model_revision", "sentence_transformers_version"):
        if model.get(key) != embedding_plan.get(key):
            raise ValueError(f"embedding artifact does not bind {key}")
    items = payload.get("items")
    if (
        not isinstance(items, Sequence)
        or isinstance(items, str)
        or any(not isinstance(item, Mapping) for item in items)
    ):
        raise ValueError("embedding items must be an array of objects")
    observed_ids = tuple(item.get("task_id") for item in items)
    if observed_ids != tuple(task_ids):
        raise ValueError("embedding artifact does not match Task order")
    dimensions = payload.get("dimensions")
    if isinstance(dimensions, bool) or not isinstance(dimensions, int) or dimensions <= 0:
        raise ValueError("embedding dimensions must be positive")
    vectors = {}
    for item in items:
        task_id = item.get("task_id")
        vector = item.get("embedding")
        if (
            not isinstance(task_id, str)
            or not task_id
            or not isinstance(vector, Sequence)
            or isinstance(vector, str)
            or len(vector) != dimensions
        ):
            raise ValueError("embedding item is malformed")
        normalized = tuple(_finite_number(value, "embedding value") for value in vector)
        norm = sqrt(fsum(value * value for value in normalized))
        if abs(norm - 1.0) > 1e-4:
            raise ValueError("embedding vector is not L2 normalized")
        vectors[task_id] = normalized
    manifest = {
        key: value for key, value in payload.items() if key != "items"
    }
    manifest["embedding_artifact_digest"] = digest
    manifest["vector_values_digest"] = canonical_digest(
        tuple((task_id, vectors[task_id]) for task_id in task_ids)
    )
    return vectors, manifest


def select_centroid_recent(
    history_ids: Sequence[str],
    vectors: Mapping[str, Sequence[float]],
    *,
    recent_window: int,
    budget: int,
) -> tuple[str, ...]:
    normalized = _validated_vectors(history_ids, vectors)
    return _centroid_recent(
        tuple(history_ids),
        SimilarityIndex(normalized),
        recent_window,
        budget,
    )


def select_facility_recent(
    history_ids: Sequence[str],
    vectors: Mapping[str, Sequence[float]],
    *,
    recent_window: int,
    budget: int,
) -> tuple[str, ...]:
    normalized = _validated_vectors(history_ids, vectors)
    return _facility_recent(
        tuple(history_ids),
        SimilarityIndex(normalized),
        recent_window,
        budget,
    )


def _centroid_recent(
    history_ids: tuple[str, ...],
    index: SimilarityIndex,
    recent_window: int,
    budget: int,
) -> tuple[str, ...]:
    _validate_selection_shape(history_ids, recent_window, budget)
    recent = history_ids[-min(recent_window, len(history_ids)) :]
    target_similarities = {
        candidate: _mean(
            tuple(index.similarity(item, candidate) for item in recent)
        )
        for candidate in history_ids
    }
    position = {task_id: offset for offset, task_id in enumerate(history_ids)}
    selected: list[str] = []
    for round_index in range(budget):
        selected.append(
            max(
                (task_id for task_id in history_ids if task_id not in selected),
                key=lambda task_id: (
                    target_similarities[task_id]
                    - (
                        _mean(
                            tuple(
                                index.similarity(task_id, other)
                                for other in selected
                            )
                        )
                        * round_index
                        / (round_index + 1)
                        if selected
                        else 0.0
                    ),
                    -position[task_id],
                ),
            )
        )

    def objective(items: Sequence[str]) -> float:
        return (
            fsum(index.similarity(left, right) for left in items for right in items)
            / (budget * budget)
            - 2.0 * _mean(
                tuple(target_similarities[task_id] for task_id in items)
            )
        )

    current = objective(selected)
    for _ in range(20):
        replacement: tuple[int, str] | None = None
        best = current
        selected_set = set(selected)
        for selected_position in range(len(selected)):
            for new_task_id in history_ids:
                if new_task_id in selected_set:
                    continue
                candidate = selected.copy()
                candidate[selected_position] = new_task_id
                value = objective(candidate)
                if value < best - 1e-12:
                    best = value
                    replacement = selected_position, new_task_id
        if replacement is None:
            break
        selected[replacement[0]] = replacement[1]
        current = best
    return tuple(selected)


def _facility_recent(
    history_ids: tuple[str, ...],
    index: SimilarityIndex,
    recent_window: int,
    budget: int,
) -> tuple[str, ...]:
    _validate_selection_shape(history_ids, recent_window, budget)
    target = history_ids[-min(recent_window, len(history_ids)) :]
    position = {task_id: offset for offset, task_id in enumerate(history_ids)}
    selected: list[str] = []
    best_similarities = [-2.0] * len(target)
    for _ in range(budget):
        def gain(candidate: str) -> float:
            return fsum(
                max(current, index.similarity(target_item, candidate)) - current
                for current, target_item in zip(
                    best_similarities,
                    target,
                    strict=True,
                )
            )

        chosen = max(
            (task_id for task_id in history_ids if task_id not in selected),
            key=lambda task_id: (gain(task_id), -position[task_id]),
        )
        selected.append(chosen)
        best_similarities = [
            max(current, index.similarity(target_item, chosen))
            for current, target_item in zip(
                best_similarities,
                target,
                strict=True,
            )
        ]
    return tuple(selected)


def run_semantic_replay(
    tasks: Sequence[TaskMetadata],
    outcomes_by_agent: Mapping[str, Mapping[str, int]],
    vectors: Mapping[str, tuple[float, ...]],
    embedding_manifest: Mapping[str, object],
    semantic_plan: Mapping[str, object],
    public_plan: Mapping[str, object],
    portfolio: Mapping[str, object],
) -> Mapping[str, Any]:
    source = _mapping(semantic_plan, "source_results")
    if source.get("public_panel_plan_digest") != public_plan.get(
        "public_panel_plan_digest"
    ):
        raise ValueError("semantic plan does not bind the public panel plan")
    if source.get("portfolio_digest") != portfolio.get("portfolio_digest"):
        raise ValueError("semantic plan does not bind the portfolio")
    task_ids = tuple(task.instance_id for task in tasks)
    if set(vectors) != set(task_ids):
        raise ValueError("semantic vectors must cover the exact Task denominator")
    if any(set(outcomes) != set(task_ids) for outcomes in outcomes_by_agent.values()):
        raise ValueError("every Agent must cover the exact Task denominator")
    rolling = _mapping(public_plan, "rolling_origin")
    origins_by_repository = build_repository_origins(
        tasks,
        minimum_initial_history_tasks=_positive_integer(
            rolling,
            "minimum_initial_history_tasks",
        ),
        future_block_tasks=_positive_integer(rolling, "future_block_tasks"),
    )
    budget = _positive_integer(rolling, "selection_budget_task_checks")
    selection_plan = _mapping(semantic_plan, "selection")
    if _positive_integer(selection_plan, "budget_tasks") != budget:
        raise ValueError("semantic budget does not match public replay")
    recent_window = _positive_integer(selection_plan, "recent_window_tasks")
    selector_ids = tuple(
        _required_string(row, "selector_id")
        for row in _mapping_sequence(selection_plan, "candidates")
    )
    if selector_ids != ("centroid_recent_15", "facility_recent_15"):
        raise ValueError("semantic candidate set does not match implementation")
    plan_portfolio = _mapping(semantic_plan, "portfolio")
    repositories = {
        "wide": _unique_strings(
            plan_portfolio.get("wide_repository_ids"),
            "wide repositories",
        ),
        "deep": _unique_strings(
            plan_portfolio.get("deep_repository_ids"),
            "deep repositories",
        ),
    }
    cluster_by_repository = {
        _required_string(row, "repository_id"): _required_string(
            row,
            "repository_cluster_id",
        )
        for row in _mapping_sequence(portfolio, "repositories")
    }
    index = SimilarityIndex(vectors)
    rows_by_selector: dict[str, list[ContrastRow]] = {
        selector_id: [] for selector_id in selector_ids
    }
    semantic_distance_rows: dict[str, dict[str, list[float]]] = {
        selector_id: {} for selector_id in (*selector_ids, "full_history")
    }
    membership_digests: dict[str, dict[str, str]] = {
        selector_id: {} for selector_id in selector_ids
    }
    for repository_id in repositories["wide"]:
        origins = origins_by_repository.get(repository_id)
        if not origins or repository_id not in cluster_by_repository:
            raise ValueError(f"semantic repository is not replayable: {repository_id}")
        for origin in origins:
            history_ids = tuple(task.instance_id for task in origin.history)
            future_ids = tuple(task.instance_id for task in origin.future)
            baseline = future_pass_rate_mae(
                history_ids,
                future_ids,
                outcomes_by_agent,
            )
            semantic_distance_rows["full_history"].setdefault(
                repository_id,
                [],
            ).append(_centroid_distance(history_ids, future_ids, index))
            selected_by_rule = {
                "centroid_recent_15": _centroid_recent(
                    history_ids,
                    index,
                    recent_window,
                    budget,
                ),
                "facility_recent_15": _facility_recent(
                    history_ids,
                    index,
                    recent_window,
                    budget,
                ),
            }
            for selector_id, selected_ids in selected_by_rule.items():
                rows_by_selector[selector_id].append(
                    ContrastRow(
                        selector_id=selector_id,
                        portfolio="wide",
                        repository_id=repository_id,
                        repository_cluster_id=cluster_by_repository[repository_id],
                        origin_id=origin.origin_id,
                        difference=(
                            future_pass_rate_mae(
                                selected_ids,
                                future_ids,
                                outcomes_by_agent,
                            )
                            - baseline
                        ),
                    )
                )
                membership_digests[selector_id][origin.origin_id] = canonical_digest(
                    selected_ids
                )
                semantic_distance_rows[selector_id].setdefault(
                    repository_id,
                    [],
                ).append(_centroid_distance(selected_ids, future_ids, index))

    aggregation = _mapping(public_plan, "aggregation")
    bootstrap_seed = _integer(aggregation, "bootstrap_seed")
    bootstrap_resamples = _positive_integer(aggregation, "bootstrap_resamples")
    summaries = {
        portfolio_name: {
            selector_id: summarize_contrasts(
                tuple(
                    _with_portfolio(row, portfolio_name)
                    for row in rows
                    if row.repository_id in repository_ids
                ),
                bootstrap_seed=bootstrap_seed,
                bootstrap_resamples=bootstrap_resamples,
            )
            for selector_id, rows in rows_by_selector.items()
        }
        for portfolio_name, repository_ids in (
            ("wide", set(repositories["wide"])),
            ("deep", set(repositories["deep"])),
        )
    }
    random_config = _mapping(public_plan, "random_calibration")
    random_reports = {
        portfolio_name: random_calibration(
            repository_ids,
            origins_by_repository,
            outcomes_by_agent,
            budget=budget,
            draws=_positive_integer(random_config, "draws"),
            seed=_integer(random_config, "seed"),
            observed_summaries=summaries[portfolio_name],
        )
        for portfolio_name, repository_ids in repositories.items()
    }
    alignment = {
        selector_id: {
            "wide_macro_repository_centroid_distance": _mean(
                tuple(
                    _mean(tuple(values))
                    for repository_id, values in by_repository.items()
                    if repository_id in repositories["wide"]
                )
            ),
            "deep_macro_repository_centroid_distance": _mean(
                tuple(
                    _mean(tuple(values))
                    for repository_id, values in by_repository.items()
                    if repository_id in repositories["deep"]
                )
            ),
        }
        for selector_id, by_repository in semantic_distance_rows.items()
    }
    nomination = _nominate(summaries, random_reports)
    result: dict[str, Any] = {
        "schema_version": "barcarolle_multi_repository_semantic_results_v1",
        "study_id": semantic_plan.get("study_id"),
        "epistemic_status": semantic_plan.get("epistemic_status"),
        "semantic_plan_digest": semantic_plan.get("semantic_plan_digest"),
        "public_panel_results_digest": source.get("public_panel_results_digest"),
        "portfolio_digest": portfolio.get("portfolio_digest"),
        "embedding_manifest": embedding_manifest,
        "task_count": len(tasks),
        "agent_count": len(outcomes_by_agent),
        "origin_counts": {
            repository_id: len(origins_by_repository[repository_id])
            for repository_id in repositories["wide"]
        },
        "summaries": summaries,
        "random_calibration": random_reports,
        "semantic_alignment_diagnostic": {
            "rows": alignment,
            "interpretation": (
                "Lower selected-to-future text-centroid distance is descriptive "
                "and does not enter nomination."
            ),
        },
        "selection_membership_digests": {
            selector_id: canonical_digest(tuple(sorted(rows.items())))
            for selector_id, rows in membership_digests.items()
        },
        "nomination": nomination,
        "claim_boundary": (
            "The Agent outcomes were open before this fixed-route replication. "
            "Results can retire or nominate ALG-007 for an independent test, "
            "but cannot confirm it or promote a Runner default."
        ),
    }
    result["semantic_results_digest"] = canonical_digest(result)
    return result


def _centroid_distance(
    left: Sequence[str],
    right: Sequence[str],
    index: SimilarityIndex,
) -> float:
    if not left or not right:
        raise ValueError("centroid distance requires nonempty Task sets")
    dot = fsum(index.similarity(a, b) for a in left for b in right)
    left_norm = fsum(index.similarity(a, b) for a in left for b in left)
    right_norm = fsum(index.similarity(a, b) for a in right for b in right)
    denominator = sqrt(left_norm * right_norm)
    if denominator <= 0.0:
        raise ValueError("embedding centroid has no positive norm")
    cosine = dot / denominator
    return 1.0 - max(-1.0, min(1.0, cosine))


def _nominate(
    summaries: Mapping[str, Mapping[str, Mapping[str, Any]]],
    random_reports: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    assessments = {}
    for selector_id in ("centroid_recent_15", "facility_recent_15"):
        wide = summaries["wide"][selector_id]
        deep = summaries["deep"][selector_id]
        random_position = _bounded_number(
            _mapping(
                _mapping(
                    _mapping(random_reports, "wide"),
                    "candidate_positions",
                ),
                selector_id,
            )["candidate_better_than_random_midrank"],
            "candidate random midrank",
        )
        requirements = {
            "wide_at_most_minus_0_01": (
                float(wide["macro_repository_difference"]) <= -0.01
            ),
            "at_least_five_favorable_repositories": (
                int(wide["favorable_repository_count"]) >= 5
            ),
            "every_leave_one_repository_out_favorable": not bool(
                wide["leave_one_cluster_out_has_nonnegative_difference"]
            ),
            "deep_direction_favorable": (
                float(deep["macro_repository_difference"]) < 0.0
            ),
            "better_than_at_least_75_percent_random": random_position >= 0.75,
        }
        assessments[selector_id] = {
            "requirements": requirements,
            "all_requirements_met": all(requirements.values()),
        }
    eligible = tuple(
        selector_id
        for selector_id, assessment in assessments.items()
        if assessment["all_requirements_met"]
    )
    nominated = (
        min(
            eligible,
            key=lambda selector_id: (
                float(
                    summaries["wide"][selector_id][
                        "macro_repository_difference"
                    ]
                ),
                selector_id,
            ),
        )
        if eligible
        else None
    )
    return {
        "status": (
            "freeze_fixed_semantic_route_for_independent_validation"
            if nominated is not None
            else "retire_fixed_alg_007_on_current_source_family"
        ),
        "nominated_selector_id": nominated,
        "candidate_assessments": assessments,
        "production_promotion_allowed": False,
    }


def _validated_vectors(
    task_ids: Sequence[str],
    vectors: Mapping[str, Sequence[float]],
) -> Mapping[str, tuple[float, ...]]:
    tasks = tuple(task_ids)
    if not tasks or len(tasks) != len(set(tasks)):
        raise ValueError("semantic history must be nonempty and unique")
    result = {}
    dimensions = None
    for task_id in tasks:
        vector = vectors.get(task_id)
        if not isinstance(vector, Sequence) or isinstance(vector, str) or not vector:
            raise ValueError("semantic vector is missing")
        normalized = tuple(_finite_number(value, "semantic value") for value in vector)
        if dimensions is None:
            dimensions = len(normalized)
        if len(normalized) != dimensions:
            raise ValueError("semantic dimensions are inconsistent")
        result[task_id] = normalized
    return result


def _validate_selection_shape(
    history_ids: Sequence[str],
    recent_window: int,
    budget: int,
) -> None:
    if (
        not history_ids
        or len(history_ids) != len(set(history_ids))
        or recent_window <= 0
        or budget <= 0
        or budget > len(history_ids)
    ):
        raise ValueError("semantic selection shape is invalid")


def _with_portfolio(row: ContrastRow, portfolio: str) -> ContrastRow:
    return ContrastRow(
        selector_id=row.selector_id,
        portfolio=portfolio,
        repository_id=row.repository_id,
        repository_cluster_id=row.repository_cluster_id,
        origin_id=row.origin_id,
        difference=row.difference,
    )


def _mapping(value: Mapping[str, object], key: str) -> Mapping[str, object]:
    item = value.get(key)
    if not isinstance(item, Mapping):
        raise ValueError(f"{key} must be an object")
    return item


def _mapping_sequence(
    value: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, object], ...]:
    item = value.get(key)
    if (
        not isinstance(item, Sequence)
        or isinstance(item, str)
        or any(not isinstance(row, Mapping) for row in item)
    ):
        raise ValueError(f"{key} must be an array of objects")
    return tuple(item)


def _required_string(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a nonempty string")
    return item


def _unique_strings(value: object, name: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{name} must be a nonempty string array")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise ValueError(f"{name} must be unique")
    return result


def _integer(value: Mapping[str, object], key: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int):
        raise ValueError(f"{key} must be an integer")
    return item


def _positive_integer(value: Mapping[str, object], key: str) -> int:
    item = _integer(value, key)
    if item <= 0:
        raise ValueError(f"{key} must be a positive integer")
    return item


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _bounded_number(value: object, name: str) -> float:
    result = _finite_number(value, name)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return result


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires values")
    return fsum(values) / len(values)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--public-plan", type=Path, default=DEFAULT_PUBLIC_PLAN)
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)
    parser.add_argument(
        "--public-results",
        type=Path,
        default=DEFAULT_PUBLIC_RESULTS,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    semantic_plan = load_semantic_plan(args.plan)
    public_plan = load_public_panel_plan(args.public_plan)
    portfolio = load_portfolio(args.portfolio)
    source = _mapping(public_plan, "task_source")
    if _file_sha256(args.dataset) != _required_string(source, "dataset_sha256"):
        raise RuntimeError("dataset digest does not match the public plan")
    public_results = json.loads(args.public_results.read_text(encoding="utf-8"))
    if not isinstance(public_results, dict):
        raise ValueError("public results must be an object")
    observed_public_digest = public_results.pop("public_panel_results_digest", None)
    if (
        canonical_digest(public_results) != observed_public_digest
        or observed_public_digest
        != _mapping(semantic_plan, "source_results").get(
            "public_panel_results_digest"
        )
    ):
        raise ValueError("semantic plan does not bind valid public results")
    tasks = load_dataset_tasks(args.dataset)
    outcomes, _ = load_public_outcomes(
        args.result_dir,
        public_plan,
        tuple(task.instance_id for task in tasks),
    )
    vectors, embedding_manifest = load_embedding_artifact(
        args.embeddings,
        semantic_plan,
        tuple(task.instance_id for task in tasks),
    )
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite semantic replay: {args.output}")
    result = run_semantic_replay(
        tasks,
        outcomes,
        vectors,
        embedding_manifest,
        semantic_plan,
        public_plan,
        portfolio,
    )
    args.output.write_text(canonical_json(result) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "nomination": result["nomination"],
                "semantic_results_digest": result["semantic_results_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
