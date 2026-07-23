from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import hashlib
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import SourceEventRecord  # noqa: E402
from barcarolle.workspace import CapturedDiff  # noqa: E402
from examples.pylint_swe_bench_verified.dependency_evidence import (  # noqa: E402
    RELATION_TYPE,
    build_dependency_evidence,
    changed_paths_from_patch,
    validate_dependency_evidence,
    validate_dependency_evidence_against_patches,
    validate_source_event_clusters,
)


def test_dependency_evidence_derives_exact_edges_and_transitive_components() -> None:
    patches = {
        "event-a": _patch("pylint/a.py"),
        "event-b": _patch("pylint/a.py", "pylint/b.py"),
        "event-c": _patch("pylint/b.py"),
        "event-d": _patch("pylint/d.py"),
    }

    evidence = build_dependency_evidence("pylint-dev/pylint", patches)
    reordered = build_dependency_evidence(
        "pylint-dev/pylint", dict(reversed(tuple(patches.items())))
    )

    assert evidence == reordered
    assert validate_dependency_evidence(evidence).ok
    assert validate_dependency_evidence_against_patches(evidence, patches).ok
    assert len(evidence.relations) == 2
    assert all(
        relation.relation_type == RELATION_TYPE for relation in evidence.relations
    )
    assert {
        (
            relation.left_source_event_id,
            relation.right_source_event_id,
            relation.overlapping_paths,
        )
        for relation in evidence.relations
    } == {
        ("event-a", "event-b", ("pylint/a.py",)),
        ("event-b", "event-c", ("pylint/b.py",)),
    }
    clusters = evidence.cluster_by_source_event_id
    assert clusters["event-a"] == clusters["event-b"] == clusters["event-c"]
    assert clusters["event-d"] != clusters["event-a"]


def test_dependency_evidence_rejects_tampering_and_patch_drift() -> None:
    patches = {
        "event-a": _patch("pylint/a.py"),
        "event-b": _patch("pylint/a.py"),
    }
    evidence = build_dependency_evidence("pylint-dev/pylint", patches)
    footprint = replace(
        evidence.patch_footprints[0],
        changed_paths=("pylint/other.py",),
    )
    tampered = replace(
        evidence,
        patch_footprints=(footprint, *evidence.patch_footprints[1:]),
    )

    assert not validate_dependency_evidence(tampered).ok
    changed_patches = {**patches, "event-a": _patch("pylint/other.py")}
    assert not validate_dependency_evidence_against_patches(
        evidence, changed_patches
    ).ok


def test_dependency_evidence_replays_source_event_clusters() -> None:
    patches = {
        "event-a": _patch("pylint/a.py"),
        "event-b": _patch("pylint/a.py"),
    }
    evidence = build_dependency_evidence("pylint-dev/pylint", patches)
    source_events = tuple(
        _source_event(source_event_id, cluster_id)
        for source_event_id, cluster_id in evidence.cluster_by_source_event_id.items()
    )

    assert validate_source_event_clusters(evidence, source_events).ok
    changed = (
        replace(source_events[0], dependency_cluster_id="unrelated"),
        *source_events[1:],
    )
    assert not validate_source_event_clusters(evidence, changed).ok


@pytest.mark.parametrize(
    "patch_text",
    (
        "",
        "--- a/pylint/a.py\n+++ b/pylint/a.py\n",
        "diff --git a/../escape.py b/../escape.py\n",
        "diff --git a/pylint/a.py /absolute.py\n",
    ),
)
def test_dependency_patch_paths_fail_closed(patch_text: str) -> None:
    with pytest.raises(ValueError, match="reference patch"):
        changed_paths_from_patch(patch_text)


def test_dependency_evidence_rejects_changed_patch_digest() -> None:
    patch = _patch("pylint/a.py")
    corrupt = replace(patch, diff_digest="corrupt")

    with pytest.raises(ValueError, match="patch digest changed"):
        build_dependency_evidence("pylint-dev/pylint", {"event": corrupt})


def _patch(*paths: str) -> CapturedDiff:
    text = "".join(
        f"diff --git a/{path} b/{path}\n"
        f"--- a/{path}\n"
        f"+++ b/{path}\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
        for path in paths
    )
    return CapturedDiff(
        diff_text=text,
        diff_digest=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def _source_event(source_event_id: str, cluster_id: str) -> SourceEventRecord:
    return SourceEventRecord(
        source_event_id=source_event_id,
        repository_id="pylint-dev/pylint",
        source_family="swe_bench_verified",
        source_ref=source_event_id,
        source_resolved_at="2026-01-01T00:00:00Z",
        task_material_available_at="2026-01-01T00:00:00Z",
        check_material_available_at="2026-01-01T00:00:00Z",
        label_mature_at="2026-01-01T00:00:00Z",
        candidate_id=f"candidate-{source_event_id}",
        task_id=f"task-{source_event_id}",
        check_id=f"check-{source_event_id}",
        disposition="accepted",
        rejection_stage=None,
        rejection_reasons=(),
        dependency_cluster_id=cluster_id,
        sampling_stratum="medium",
        source_event_digest="not-needed-for-cluster-replay",
    )
