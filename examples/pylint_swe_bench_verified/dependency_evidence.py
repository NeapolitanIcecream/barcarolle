"""Deterministic protocol-only dependency evidence for the Pylint adapter."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import PurePosixPath
from typing import Mapping, Sequence
import hashlib

from barcarolle.records import (
    SourceEventRecord,
    ValidationResult,
    canonical_data,
    canonical_digest,
    record_with_digest,
)
from barcarolle.workspace import CapturedDiff


DEPENDENCY_PROTOCOL_VERSION = "pylint_trusted_patch_path_components_v1"
RELATION_TYPE = "trusted_reference_patch_path_overlap"


@dataclass(frozen=True)
class PatchFootprint:
    source_event_id: str
    reference_patch_digest: str
    changed_paths: tuple[str, ...]


@dataclass(frozen=True)
class DependencyRelation:
    relation_id: str
    left_source_event_id: str
    right_source_event_id: str
    relation_type: str
    overlapping_paths: tuple[str, ...]
    left_reference_patch_digest: str
    right_reference_patch_digest: str


@dataclass(frozen=True)
class PylintDependencyEvidence:
    protocol_version: str
    repository_id: str
    patch_footprints: tuple[PatchFootprint, ...]
    relations: tuple[DependencyRelation, ...]
    cluster_by_source_event_id: Mapping[str, str]
    dependency_evidence_digest: str


def build_dependency_evidence(
    repository_id: str,
    reference_patches: Mapping[str, CapturedDiff],
) -> PylintDependencyEvidence:
    """Derive path-overlap edges and connected components from trusted patches.

    ``reference_patches`` is keyed by the already-derived SourceEvent ID. Patch
    text is read only to derive changed paths and is not persisted.
    """
    if not repository_id:
        raise ValueError("repository_id must be a nonempty string")
    if not reference_patches:
        raise ValueError("reference_patches must not be empty")
    footprints: list[PatchFootprint] = []
    for source_event_id, patch in sorted(reference_patches.items()):
        if not source_event_id:
            raise ValueError("reference_patches contains an empty SourceEvent ID")
        actual_digest = hashlib.sha256(patch.diff_text.encode("utf-8")).hexdigest()
        if actual_digest != patch.diff_digest:
            raise ValueError(f"reference patch digest changed: {source_event_id}")
        footprints.append(
            PatchFootprint(
                source_event_id=source_event_id,
                reference_patch_digest=patch.diff_digest,
                changed_paths=changed_paths_from_patch(patch.diff_text),
            )
        )
    relations = _relations_from_footprints(tuple(footprints))
    clusters = _clusters_from_relations(
        repository_id,
        tuple(footprint.source_event_id for footprint in footprints),
        relations,
    )
    evidence = record_with_digest(
        PylintDependencyEvidence(
            protocol_version=DEPENDENCY_PROTOCOL_VERSION,
            repository_id=repository_id,
            patch_footprints=tuple(footprints),
            relations=relations,
            cluster_by_source_event_id=clusters,
            dependency_evidence_digest="",
        ),
        "dependency_evidence_digest",
    )
    validation = validate_dependency_evidence(evidence)
    if not validation.ok:
        raise ValueError(
            "derived dependency evidence is invalid: " + "; ".join(validation.errors)
        )
    return evidence


def validate_dependency_evidence(
    evidence: PylintDependencyEvidence,
) -> ValidationResult:
    errors: list[str] = []
    if evidence.protocol_version != DEPENDENCY_PROTOCOL_VERSION:
        errors.append("dependency protocol version is unsupported")
    if not evidence.repository_id:
        errors.append("dependency repository_id is required")
    footprints = evidence.patch_footprints
    source_event_ids = tuple(footprint.source_event_id for footprint in footprints)
    if not footprints:
        errors.append("dependency patch footprints must not be empty")
    if source_event_ids != tuple(sorted(source_event_ids)):
        errors.append("dependency patch footprints must be sorted")
    if len(source_event_ids) != len(set(source_event_ids)):
        errors.append("dependency patch footprints contain duplicate SourceEvents")
    for footprint in footprints:
        if not footprint.source_event_id or not footprint.reference_patch_digest:
            errors.append("dependency patch footprint is incomplete")
        if not footprint.changed_paths or footprint.changed_paths != tuple(
            sorted(set(footprint.changed_paths))
        ):
            errors.append(
                f"dependency patch paths are invalid: {footprint.source_event_id}"
            )
    expected_relations = _relations_from_footprints(footprints)
    if evidence.relations != expected_relations:
        errors.append("dependency relations do not match patch footprints")
    expected_clusters = _clusters_from_relations(
        evidence.repository_id,
        source_event_ids,
        expected_relations,
    )
    if dict(evidence.cluster_by_source_event_id) != expected_clusters:
        errors.append("dependency clusters do not match connected components")
    payload = canonical_data(evidence)
    if isinstance(payload, dict):
        payload.pop("dependency_evidence_digest", None)
    if evidence.dependency_evidence_digest != canonical_digest(payload):
        errors.append("dependency_evidence_digest does not match evidence")
    return ValidationResult.fail(errors) if errors else ValidationResult.pass_()


def validate_dependency_evidence_against_patches(
    evidence: PylintDependencyEvidence,
    reference_patches: Mapping[str, CapturedDiff],
) -> ValidationResult:
    try:
        expected = build_dependency_evidence(
            evidence.repository_id,
            reference_patches,
        )
    except ValueError as exc:
        return ValidationResult.fail((str(exc),))
    if evidence != expected:
        return ValidationResult.fail(
            ("dependency evidence does not replay from reference patches",)
        )
    return ValidationResult.pass_()


def validate_source_event_clusters(
    evidence: PylintDependencyEvidence,
    source_events: Sequence[SourceEventRecord],
) -> ValidationResult:
    errors: list[str] = []
    event_by_id = {event.source_event_id: event for event in source_events}
    if len(event_by_id) != len(source_events):
        errors.append("source events contain duplicate identities")
    if set(event_by_id) != set(evidence.cluster_by_source_event_id):
        errors.append("dependency evidence does not cover the SourceEvent frame")
    for source_event_id, cluster_id in evidence.cluster_by_source_event_id.items():
        event = event_by_id.get(source_event_id)
        if event is None:
            continue
        if event.repository_id != evidence.repository_id:
            errors.append("dependency evidence repository does not match SourceEvent")
        if event.dependency_cluster_id != cluster_id:
            errors.append(
                f"SourceEvent dependency cluster does not replay: {source_event_id}"
            )
    return ValidationResult.fail(errors) if errors else ValidationResult.pass_()


def changed_paths_from_patch(patch_text: str) -> tuple[str, ...]:
    paths: set[str] = set()
    for line in patch_text.splitlines():
        if not line.startswith("diff --git a/"):
            continue
        _, separator, right = line.removeprefix("diff --git a/").partition(" b/")
        if not separator or not right:
            raise ValueError("reference patch has an unsupported diff header")
        path = PurePosixPath(right)
        if (
            path.is_absolute()
            or right != path.as_posix()
            or any(part in {"", ".", ".."} for part in path.parts)
            or "\\" in right
        ):
            raise ValueError("reference patch path is not repository-relative")
        paths.add(right)
    if not paths:
        raise ValueError("reference patch contains no changed paths")
    return tuple(sorted(paths))


def _relations_from_footprints(
    footprints: Sequence[PatchFootprint],
) -> tuple[DependencyRelation, ...]:
    relations: list[DependencyRelation] = []
    for left, right in combinations(footprints, 2):
        overlap = tuple(sorted(set(left.changed_paths) & set(right.changed_paths)))
        if not overlap:
            continue
        relation_payload = {
            "protocol_version": DEPENDENCY_PROTOCOL_VERSION,
            "relation_type": RELATION_TYPE,
            "left_source_event_id": left.source_event_id,
            "right_source_event_id": right.source_event_id,
            "overlapping_paths": overlap,
            "left_reference_patch_digest": left.reference_patch_digest,
            "right_reference_patch_digest": right.reference_patch_digest,
        }
        relations.append(
            DependencyRelation(
                relation_id=f"dependency_relation_{canonical_digest(relation_payload)}",
                left_source_event_id=left.source_event_id,
                right_source_event_id=right.source_event_id,
                relation_type=RELATION_TYPE,
                overlapping_paths=overlap,
                left_reference_patch_digest=left.reference_patch_digest,
                right_reference_patch_digest=right.reference_patch_digest,
            )
        )
    return tuple(relations)


def _clusters_from_relations(
    repository_id: str,
    source_event_ids: Sequence[str],
    relations: Sequence[DependencyRelation],
) -> dict[str, str]:
    parent = {source_event_id: source_event_id for source_event_id in source_event_ids}

    def find(source_event_id: str) -> str:
        root = source_event_id
        while parent[root] != root:
            root = parent[root]
        while parent[source_event_id] != source_event_id:
            next_id = parent[source_event_id]
            parent[source_event_id] = root
            source_event_id = next_id
        return root

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        earlier, later = sorted((left_root, right_root))
        parent[later] = earlier

    for relation in relations:
        union(relation.left_source_event_id, relation.right_source_event_id)
    members_by_root: dict[str, list[str]] = {}
    for source_event_id in sorted(source_event_ids):
        members_by_root.setdefault(find(source_event_id), []).append(source_event_id)
    cluster_by_source_event_id: dict[str, str] = {}
    for members in members_by_root.values():
        ordered_members = tuple(sorted(members))
        cluster_id = "dependency_cluster_" + canonical_digest(
            {
                "protocol_version": DEPENDENCY_PROTOCOL_VERSION,
                "repository_id": repository_id,
                "source_event_ids": ordered_members,
            }
        )
        for source_event_id in ordered_members:
            cluster_by_source_event_id[source_event_id] = cluster_id
    return dict(sorted(cluster_by_source_event_id.items()))
