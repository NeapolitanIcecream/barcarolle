#!/usr/bin/env python3
"""Aggregate repository-local Selector contrasts without flattening Origins."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import ceil, fsum, isfinite
import random
from typing import Any, Mapping, Sequence

from barcarolle.records import canonical_digest


@dataclass(frozen=True)
class ContrastRow:
    selector_id: str
    portfolio: str
    repository_id: str
    repository_cluster_id: str
    origin_id: str
    difference: float


def summarize_contrasts(
    rows: Sequence[ContrastRow],
    *,
    bootstrap_seed: int,
    bootstrap_resamples: int,
) -> Mapping[str, Any]:
    """Summarize candidate-minus-full-history loss at repository level."""
    if not rows:
        raise ValueError("at least one contrast row is required")
    if isinstance(bootstrap_seed, bool) or not isinstance(bootstrap_seed, int):
        raise ValueError("bootstrap_seed must be an integer")
    if (
        isinstance(bootstrap_resamples, bool)
        or not isinstance(bootstrap_resamples, int)
        or bootstrap_resamples <= 0
    ):
        raise ValueError("bootstrap_resamples must be a positive integer")

    selector_ids = {_required_text(row.selector_id, "selector_id") for row in rows}
    portfolios = {_required_text(row.portfolio, "portfolio") for row in rows}
    if len(selector_ids) != 1 or len(portfolios) != 1:
        raise ValueError("contrast rows must use one Selector and portfolio")

    differences_by_repository: dict[str, list[float]] = defaultdict(list)
    cluster_by_repository: dict[str, str] = {}
    seen_origins: set[tuple[str, str]] = set()
    for row in rows:
        repository_id = _required_text(row.repository_id, "repository_id")
        cluster_id = _required_text(
            row.repository_cluster_id,
            "repository_cluster_id",
        )
        origin_id = _required_text(row.origin_id, "origin_id")
        difference = float(row.difference)
        if not isfinite(difference) or not -1.0 <= difference <= 1.0:
            raise ValueError("difference must be finite and in [-1, 1]")
        origin_key = (repository_id, origin_id)
        if origin_key in seen_origins:
            raise ValueError("duplicate repository Origin contrast")
        seen_origins.add(origin_key)
        existing_cluster = cluster_by_repository.setdefault(repository_id, cluster_id)
        if existing_cluster != cluster_id:
            raise ValueError("one repository cannot use multiple clusters")
        differences_by_repository[repository_id].append(difference)

    repository_rows = tuple(
        {
            "repository_id": repository_id,
            "repository_cluster_id": cluster_by_repository[repository_id],
            "origin_count": len(differences_by_repository[repository_id]),
            "mean_difference": _mean(differences_by_repository[repository_id]),
            "favorable": _mean(differences_by_repository[repository_id]) < 0.0,
        }
        for repository_id in sorted(differences_by_repository)
    )
    repository_differences = tuple(
        float(row["mean_difference"]) for row in repository_rows
    )
    macro_difference = _mean(repository_differences)
    cluster_ids = tuple(
        sorted({str(row["repository_cluster_id"]) for row in repository_rows})
    )
    repository_values_by_cluster = {
        cluster_id: tuple(
            float(row["mean_difference"])
            for row in repository_rows
            if row["repository_cluster_id"] == cluster_id
        )
        for cluster_id in cluster_ids
    }
    bootstrap_interval = _cluster_bootstrap_interval(
        repository_values_by_cluster,
        seed=bootstrap_seed,
        resamples=bootstrap_resamples,
    )
    leave_one_out = tuple(
        {
            "omitted_repository_cluster_id": cluster_id,
            "remaining_repository_count": sum(
                len(values)
                for other_cluster, values in repository_values_by_cluster.items()
                if other_cluster != cluster_id
            ),
            "macro_repository_difference": _mean(
                tuple(
                    value
                    for other_cluster, values in repository_values_by_cluster.items()
                    if other_cluster != cluster_id
                    for value in values
                )
            ),
        }
        for cluster_id in cluster_ids
        if len(cluster_ids) > 1
    )

    summary: dict[str, Any] = {
        "schema_version": "barcarolle_multi_repository_summary_v1",
        "selector_id": next(iter(selector_ids)),
        "portfolio": next(iter(portfolios)),
        "origin_count": len(rows),
        "repository_count": len(repository_rows),
        "repository_cluster_count": len(cluster_ids),
        "macro_repository_difference": macro_difference,
        "origin_weighted_difference": _mean(tuple(row.difference for row in rows)),
        "favorable_repository_count": sum(
            bool(row["favorable"]) for row in repository_rows
        ),
        "upper_quartile_repository_difference": _nearest_rank_quantile(
            repository_differences,
            0.75,
        ),
        "repository_rows": repository_rows,
        "repository_cluster_interval_95": bootstrap_interval,
        "bootstrap_seed": bootstrap_seed,
        "bootstrap_resamples": bootstrap_resamples,
        "leave_one_cluster_out": leave_one_out,
        "leave_one_cluster_out_has_nonnegative_difference": any(
            float(row["macro_repository_difference"]) >= 0.0
            for row in leave_one_out
        ),
    }
    summary["summary_digest"] = canonical_digest(summary)
    return summary


def _cluster_bootstrap_interval(
    values_by_cluster: Mapping[str, Sequence[float]],
    *,
    seed: int,
    resamples: int,
) -> tuple[float, float] | None:
    cluster_ids = tuple(sorted(values_by_cluster))
    if len(cluster_ids) < 2:
        return None
    generator = random.Random(seed)
    draws = []
    for _ in range(resamples):
        sampled_clusters = generator.choices(cluster_ids, k=len(cluster_ids))
        sampled_repository_values = tuple(
            value
            for cluster_id in sampled_clusters
            for value in values_by_cluster[cluster_id]
        )
        draws.append(_mean(sampled_repository_values))
    draws.sort()
    return (
        _empirical_quantile(draws, 0.025),
        _empirical_quantile(draws, 0.975),
    )


def _nearest_rank_quantile(values: Sequence[float], probability: float) -> float:
    if not values or not 0.0 < probability <= 1.0:
        raise ValueError("quantile input is invalid")
    ordered = sorted(values)
    return ordered[ceil(probability * len(ordered)) - 1]


def _empirical_quantile(values: Sequence[float], probability: float) -> float:
    if not values or not 0.0 <= probability <= 1.0:
        raise ValueError("empirical quantile input is invalid")
    index = round(probability * (len(values) - 1))
    return values[index]


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires at least one value")
    return fsum(values) / len(values)


def _required_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a nonempty string")
    return value
