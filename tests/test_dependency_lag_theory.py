from __future__ import annotations

from datetime import UTC, datetime
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import Any, Mapping, cast

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest, canonical_json  # noqa: E402
from examples.dependency_lag_theory.study import (  # noqa: E402
    DependencySnapshot,
    DirectDependency,
    StatePoint,
    StateVector,
    binary_brier,
    build_state_index,
    classify_lag,
    dependency_declarations,
    dependency_state,
    load_addendum,
    load_plan,
    load_registry_manifest,
    load_task_identities,
    locked_direct_versions,
    normalize_pnpm_version,
    parse_strict_semver,
    patch_touches_root_dependency,
    read_dependency_snapshot,
    select_nearest_regime,
    state_distance,
    temporal_null_summary,
)

PLAN_PATH = REPOSITORY_ROOT / "examples/dependency_lag_theory/plan.json"
ADDENDUM_PATH = (
    REPOSITORY_ROOT / "examples/dependency_lag_theory/execution-addendum.json"
)


def test_frozen_plan_and_execution_addendum_digests_are_valid() -> None:
    plan = cast(dict[str, Any], load_plan(PLAN_PATH))
    addendum = load_addendum(ADDENDUM_PATH, plan=plan)

    assert plan["candidate"]["algorithm_id"] == "THY-003"
    assert plan["candidate"]["selection_budget"] == 10
    assert addendum["source_frame"]["task_count"] == 1420
    assert addendum["source_frame"]["origin_count"] == 119


def test_plan_and_addendum_reject_changes_without_new_digest(
    tmp_path: Path,
) -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    plan["candidate"]["selection_budget"] = 11
    changed_plan = tmp_path / "plan.json"
    changed_plan.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        load_plan(changed_plan)

    addendum = json.loads(ADDENDUM_PATH.read_text(encoding="utf-8"))
    addendum["uncertainty_and_null"]["temporal_null_rate"] = "changed"
    changed_addendum = tmp_path / "addendum.json"
    changed_addendum.write_text(json.dumps(addendum), encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        load_addendum(changed_addendum)


def test_identity_loader_does_not_read_reference_patch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parquet = tmp_path / "source.parquet"
    parquet.write_bytes(b"identity-only fixture")
    queries: list[str] = []

    class FakeConnection:
        rows: list[tuple[object, ...]]

        def execute(
            self,
            query: str,
            _parameters: object,
        ) -> FakeConnection:
            queries.append(query)
            assert "patch" not in query.casefold()
            if "count(*)" in query:
                self.rows = [("owner/repo", 1)]
            else:
                self.rows = [
                    (
                        "owner/repo",
                        "task-1",
                        "base-commit",
                        "2026-01-01 00:00:00",
                        "TypeScript",
                        None,
                    )
                ]
            return self

        def fetchall(self) -> list[tuple[object, ...]]:
            return self.rows

        def close(self) -> None:
            return None

    monkeypatch.setitem(
        sys.modules,
        "duckdb",
        SimpleNamespace(connect=lambda: FakeConnection()),
    )
    parent_plan = {
        "source": {
            "parquet": str(parquet),
            "parquet_sha256": hashlib.sha256(parquet.read_bytes()).hexdigest(),
            "parquet_size_bytes": parquet.stat().st_size,
            "selected_source_row_count": 1,
            "canonical_task_count": 1,
            "canonical_repository_count": 1,
            "frame_minimum_source_rows": 1,
            "source_alias_count": 1,
            "repositories": [
                {
                    "repository_id": "owner/repo",
                    "source_aliases": ["owner/repo"],
                    "expected_task_count": 1,
                }
            ],
        }
    }

    tasks, identity_digest = load_task_identities(parent_plan)

    assert len(queries) == 2
    assert len(tasks) == 1
    assert tasks[0].instance_id == "task-1"
    assert tasks[0].modules == ()
    assert identity_digest == canonical_digest(
        {
            "task-1": (
                {
                    "source_alias": "owner/repo",
                    "source_instance_id": "task-1",
                },
            )
        }
    )


def test_origin_variation_uses_normalized_rational_identity() -> None:
    cutoff = datetime(2026, 1, 2, tzinfo=UTC)
    one = DirectDependency("one", "production", "^1", "1.0.0")
    two = DirectDependency("two", "production", "^1", "1.0.0")
    points = (
        StatePoint(
            repository_id="owner/repo",
            kind="origin",
            state_id="origin-1",
            cutoff=cutoff,
            commit_id="one",
            snapshot=DependencySnapshot("one", "package-lock.json", (one,)),
        ),
        StatePoint(
            repository_id="owner/repo",
            kind="origin",
            state_id="origin-2",
            cutoff=cutoff,
            commit_id="two",
            snapshot=DependencySnapshot(
                "two",
                "package-lock.json",
                (one, two),
            ),
        ),
    )
    registry = {
        "one": {(1, 0, 0): datetime(2026, 1, 1, tzinfo=UTC)},
        "two": {(1, 0, 0): datetime(2026, 1, 1, tzinfo=UTC)},
    }

    *_, summary = build_state_index(points, registry)

    assert summary["distinct_origin_state_count_by_repository"] == {
        "owner/repo": 1
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("0.0.0", (0, 0, 0)),
        ("1.2.3", (1, 2, 3)),
        ("01.2.3", None),
        ("v1.2.3", None),
        ("1.2.3-alpha", None),
        ("1.2.3+build", None),
        ("1.2", None),
    ),
)
def test_strict_semver_boundary(
    value: str,
    expected: tuple[int, int, int] | None,
) -> None:
    assert parse_strict_semver(value) == expected


def test_pnpm_peer_context_normalization_is_exactly_bounded() -> None:
    assert normalize_pnpm_version("1.2.3") == "1.2.3"
    assert normalize_pnpm_version("1.2.3_rollup@4.0.0") == "1.2.3"
    assert normalize_pnpm_version("1.2.3(peer@2.0.0)") == "1.2.3"
    assert normalize_pnpm_version("workspace:1.2.3") is None
    assert normalize_pnpm_version("1.2.3-alpha(peer@2.0.0)") is None


def test_dependency_declarations_use_production_precedence() -> None:
    observed = dependency_declarations(
        {
            "dependencies": {"shared": "^1", "prod": "^2"},
            "devDependencies": {"shared": "^3", "dev": "^4"},
        }
    )

    assert observed == (
        ("prod", "production", "^2"),
        ("shared", "production", "^1"),
        ("dev", "development", "^4"),
    )


def test_npm_v1_v2_v3_direct_resolution_and_link_boundary() -> None:
    manifest = {
        "dependencies": {"@scope/a": "^1", "linked": "^2"},
        "devDependencies": {"dev": "^3"},
    }
    v1 = locked_direct_versions(
        manifest=manifest,
        lockfile="package-lock.json",
        lock_bytes=json.dumps(
            {
                "lockfileVersion": 1,
                "dependencies": {
                    "@scope/a": {"version": "1.2.3"},
                    "linked": {"version": "2.0.0"},
                    "dev": {"version": "3.0.1"},
                },
            }
        ).encode(),
    )
    assert [item.locked_version for item in v1] == ["1.2.3", "2.0.0", "3.0.1"]

    for lock_version in (2, 3):
        modern = locked_direct_versions(
            manifest=manifest,
            lockfile="npm-shrinkwrap.json",
            lock_bytes=json.dumps(
                {
                    "lockfileVersion": lock_version,
                    "packages": {
                        "node_modules/@scope/a": {"version": "1.2.4"},
                        "node_modules/linked": {
                            "version": "2.0.0",
                            "link": True,
                        },
                        "node_modules/dev": {"version": "3.0.2-alpha"},
                    },
                }
            ).encode(),
        )
        assert [item.locked_version for item in modern] == [
            "1.2.4",
            None,
            None,
        ]


def test_first_present_lockfile_never_falls_through(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    subprocess.run(("git", "init", "-q", "-b", "main", str(repository)), check=True)
    subprocess.run(
        ("git", "-C", str(repository), "config", "user.email", "test@example.com"),
        check=True,
    )
    subprocess.run(
        ("git", "-C", str(repository), "config", "user.name", "Test"),
        check=True,
    )
    (repository / "package.json").write_text(
        json.dumps({"dependencies": {"only": "^1"}}),
        encoding="utf-8",
    )
    (repository / "npm-shrinkwrap.json").write_text(
        json.dumps({"lockfileVersion": 3, "packages": {}}),
        encoding="utf-8",
    )
    (repository / "package-lock.json").write_text(
        json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {"node_modules/only": {"version": "1.2.3"}},
            }
        ),
        encoding="utf-8",
    )
    subprocess.run(("git", "-C", str(repository), "add", "."), check=True)
    subprocess.run(
        ("git", "-C", str(repository), "commit", "-q", "-m", "fixture"),
        check=True,
    )
    commit = subprocess.run(
        ("git", "-C", str(repository), "rev-parse", "HEAD"),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    snapshot = read_dependency_snapshot(repository, commit)

    assert snapshot.lockfile == "npm-shrinkwrap.json"
    assert snapshot.dependencies[0].locked_version is None


def test_pnpm_5_and_9_root_importer_resolution() -> None:
    manifest = {
        "dependencies": {"prod": "^1.0.0"},
        "devDependencies": {"dev": "~2.0.0", "mismatch": "^3.0.0"},
    }
    v5 = b"""
lockfileVersion: 5.4
importers:
  .:
    specifiers:
      prod: ^1.0.0
      dev: ~2.0.0
      mismatch: ^4.0.0
    dependencies:
      prod: 1.2.3_peer@4.0.0
    devDependencies:
      dev: 2.0.1
      mismatch: 3.0.1
packages: {}
"""
    observed_v5 = locked_direct_versions(
        manifest=manifest,
        lockfile="pnpm-lock.yaml",
        lock_bytes=v5,
    )
    assert [item.locked_version for item in observed_v5] == [
        "1.2.3",
        "2.0.1",
        None,
    ]

    v9 = b"""
lockfileVersion: '9.0'
importers:
  .:
    dependencies:
      prod:
        specifier: ^1.0.0
        version: 1.3.0(peer@4.0.0)
    devDependencies:
      dev:
        specifier: ~2.0.0
        version: 2.0.2
      mismatch:
        specifier: ^4.0.0
        version: 3.0.2
packages: {}
"""
    observed_v9 = locked_direct_versions(
        manifest=manifest,
        lockfile="pnpm-lock.yaml",
        lock_bytes=v9,
    )
    assert [item.locked_version for item in observed_v9] == [
        "1.3.0",
        "2.0.2",
        None,
    ]


def test_yarn_classic_and_berry_match_exact_manifest_descriptors() -> None:
    manifest = {
        "dependencies": {"same": "^1.0.0", "other": "~2.0.0"},
    }
    classic = b"""
# yarn lockfile v1
"same@^1.0.0", "same@~1.2.0":
  version "1.3.0"

other@^2.0.0:
  version "2.1.0"
"""
    observed_classic = locked_direct_versions(
        manifest=manifest,
        lockfile="yarn.lock",
        lock_bytes=classic,
    )
    assert {item.name: item.locked_version for item in observed_classic} == {
        "same": "1.3.0",
        "other": None,
    }

    berry = b"""
__metadata:
  version: 8

"same@npm:^1.0.0, same@npm:~1.2.0":
  version: 1.4.0
  resolution: "same@npm:1.4.0"

"other@npm:~2.0.0":
  version: 2.0.3
"""
    observed_berry = locked_direct_versions(
        manifest=manifest,
        lockfile="yarn.lock",
        lock_bytes=berry,
    )
    assert {item.name: item.locked_version for item in observed_berry} == {
        "same": "1.4.0",
        "other": "2.0.3",
    }


def _write_registry_fixture(
    root: Path,
    *,
    package: str,
    payload: Mapping[str, object],
) -> Path:
    response_root = root / "responses"
    response_root.mkdir(parents=True)
    body = json.dumps(payload, separators=(",", ":")).encode()
    relative = "responses/value.bin"
    (root / relative).write_bytes(body)
    row = {
        "package": package,
        "request_url": f"https://registry.npmjs.org/{package}",
        "response_url": f"https://registry.npmjs.org/{package}",
        "status": 200,
        "queried_at": "2026-07-29T00:00:00.000000Z",
        "attempts": (
            {
                "attempt": 1,
                "queried_at": "2026-07-29T00:00:00.000000Z",
                "status": 200,
            },
        ),
        "path": relative,
        "byte_count": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    manifest = {
        "schema_version": "barcarolle_dependency_lag_registry_manifest_v1",
        "registry": "https://registry.npmjs.org/",
        "request_accept": "application/json",
        "package_count": 1,
        "package_digest": canonical_digest((package,)),
        "response_count": 1,
        "response_bytes": len(body),
        "responses": (row,),
    }
    manifest["registry_manifest_digest"] = canonical_digest(manifest)
    path = root / "manifest.json"
    path.write_text(canonical_json(manifest) + "\n", encoding="utf-8")
    return path


def test_packument_projection_uses_only_versions_and_cutoff(
    tmp_path: Path,
) -> None:
    manifest_path = _write_registry_fixture(
        tmp_path,
        package="sample",
        payload={
            "name": "sample",
            "dist-tags": {"latest": "99.0.0"},
            "modified": "2099-01-01T00:00:00Z",
            "versions": {
                "1.0.0": {},
                "1.1.0": {},
                "2.0.0-alpha": {},
                "2.0.0": {},
            },
            "time": {
                "created": "2018-01-01T00:00:00Z",
                "modified": "2099-01-01T00:00:00Z",
                "1.0.0": "2020-01-01T00:00:00Z",
                "1.1.0": "2021-01-01T00:00:00Z",
                "2.0.0-alpha": "2021-06-01T00:00:00Z",
                "2.0.0": "2022-01-01T00:00:00Z",
            },
        },
    )
    _, registry = load_registry_manifest(manifest_path)
    snapshot = DependencySnapshot(
        commit_id="a" * 40,
        lockfile="package-lock.json",
        dependencies=(DirectDependency("sample", "production", "^1", "1.0.0"),),
    )

    at_cutoff, resolved = dependency_state(
        snapshot,
        datetime(2021, 1, 1, tzinfo=UTC),
        registry,
    )

    assert resolved == 1
    assert at_cutoff is not None
    assert at_cutoff.counts[1] == 0
    assert at_cutoff.counts[2] == 1  # 1.0.0 is minor-lagged behind 1.1.0.


def test_packument_reload_rejects_raw_byte_change(tmp_path: Path) -> None:
    manifest_path = _write_registry_fixture(
        tmp_path,
        package="sample",
        payload={"name": "sample", "versions": {}, "time": {}},
    )
    (tmp_path / "responses/value.bin").write_bytes(b"changed")

    with pytest.raises(ValueError, match="byte count|SHA"):
        load_registry_manifest(manifest_path)


def test_exact_state_distance_and_missing_marker() -> None:
    left = StateVector((1, 0, 0, 0, 0, 0, 0, 0, 0, 0), 1)
    right = StateVector((0, 1, 0, 0, 0, 0, 0, 0, 0, 0), 1)
    mixed = StateVector((1, 1, 0, 0, 0, 0, 0, 0, 0, 0), 2)

    assert state_distance(left, left) == 0
    assert state_distance(left, right) == 1
    assert state_distance(mixed, left) == Fraction(1, 2)
    assert state_distance(None, left) == 1


def test_selection_uses_exact_distance_then_frozen_hash_tie_break() -> None:
    origin = StateVector((1, 0, 0, 0, 0, 0, 0, 0, 0, 0), 1)
    near = StateVector((2, 0, 0, 0, 0, 0, 0, 0, 0, 0), 2)
    far = StateVector((0, 1, 0, 0, 0, 0, 0, 0, 0, 0), 1)
    task_ids = tuple(f"task-{index}" for index in range(12))
    states = {task_id: far for task_id in task_ids}
    states["task-11"] = near

    selection = select_nearest_regime(
        study_id="study",
        repository_id="repo",
        origin_id="origin",
        history_task_ids=task_ids,
        task_states=states,
        origin_state=origin,
        budget=10,
    )
    expected_ties = sorted(
        task_ids[:-1],
        key=lambda task_id: hashlib.sha256(
            f"study\0repo\0origin\0{task_id}".encode()
        ).hexdigest(),
    )

    assert selection.selected_task_ids[0] == "task-11"
    assert selection.selected_task_ids[1:] == tuple(expected_ties[:9])


def test_binary_brier_is_scalar_not_two_class_sum() -> None:
    assert binary_brier((0, 1), Fraction(1, 4)) == pytest.approx(0.3125)


def test_scoring_label_is_root_only_and_reads_both_sides() -> None:
    assert patch_touches_root_dependency("diff --git a/package.json b/package.json\n")
    assert patch_touches_root_dependency("diff --git a/old-name b/yarn.lock\n")
    assert not patch_touches_root_dependency(
        "diff --git a/packages/a/package.json b/packages/a/package.json\n"
    )


def test_temporal_null_is_deterministic_and_uses_nonzero_offsets() -> None:
    offsets = {
        "a": {1: -0.1, 2: 0.2},
        "b": {1: -0.2, 2: 0.3},
    }
    first = temporal_null_summary(
        offsets,
        repositories=("a", "b"),
        true_contrast=-0.05,
        seed=20260729,
    )
    second = temporal_null_summary(
        offsets,
        repositories=("a", "b"),
        true_contrast=-0.05,
        seed=20260729,
    )

    assert first == second
    assert first["draw_count"] == 20000
    assert 0.0 <= first["as_good_or_better_rate"] <= 1.0


@pytest.mark.parametrize(
    ("locked", "latest", "expected"),
    (
        ((1, 2, 3), (1, 2, 3), "current"),
        ((1, 2, 2), (1, 2, 3), "patch_lag"),
        ((1, 1, 9), (1, 2, 0), "minor_lag"),
        ((1, 9, 9), (2, 0, 0), "major_lag"),
        ((2, 0, 0), (1, 9, 9), "unknown"),
    ),
)
def test_lag_classification(
    locked: tuple[int, int, int],
    latest: tuple[int, int, int],
    expected: str,
) -> None:
    assert classify_lag(locked, latest) == expected
