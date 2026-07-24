"""Append-only Result Store contracts and joins."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterator, Mapping, Sequence, TextIO
import json
import os

try:
    import fcntl
except ImportError:  # pragma: no cover - scoreable execution is POSIX-only today
    fcntl = None  # type: ignore[assignment]

from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    CheckOutcomeValue,
    EvaluationCellSet,
    InvalidOwner,
    MatrixScoreableState,
    ResultCacheIdentity,
    ResultCellRef,
    ResultMatrix,
    ResultRecord,
    ResultImportReceipt,
    ResultSourceManifest,
    ResultScoreableState,
    RuntimeConfig,
    TaskCheckRef,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    cache_identity_agent_mismatches,
    cache_identity_task_check_mismatches,
    canonical_digest,
    canonical_json,
    format_utc_timestamp,
    load_jsonl_records,
    make_result_cache_identity,
    make_result_cache_key,
    make_result_evidence_digest,
    make_result_execution_digest,
    make_result_id,
    parse_utc_timestamp,
    record_with_digest,
    result_cell_record_mismatches,
    validate_agent,
    validate_check,
    validate_evaluation_cell_set,
    validate_result,
    validate_result_cache_identity,
    validate_result_matrix,
    validate_runtime_config,
    validate_task,
    validate_workspace_config,
    validate_workspace_run,
    utc_now_timestamp,
    write_jsonl_records,
)


RESULT_SOURCE_MANIFEST_SCHEMA_VERSION = "barcarolle_result_source_manifest_v1"


def _normalized_cost_rates(
    pricing_version: object,
    cost_rates: object,
) -> dict[str, float]:
    if not isinstance(pricing_version, str) or not pricing_version:
        raise ValueError("pricing_version is required")
    if not isinstance(cost_rates, Mapping):
        raise ValueError("cost_rates must be a mapping")
    normalized: dict[str, float] = {}
    for key, rate in cost_rates.items():
        if not isinstance(key, str):
            raise ValueError("cost rate keys must be strings")
        if isinstance(rate, bool) or not isinstance(rate, int | float):
            raise ValueError(
                f"cost rate for {key} must be a finite and nonnegative number"
            )
        try:
            numeric_rate = float(rate)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(
                f"cost rate for {key} must be a finite and nonnegative number"
            ) from exc
        if not isfinite(numeric_rate) or numeric_rate < 0.0:
            raise ValueError(
                f"cost rate for {key} must be a finite and nonnegative number"
            )
        normalized[key] = abs(numeric_rate)
    return {key: normalized[key] for key in sorted(normalized)}


@dataclass(frozen=True)
class ScoringConfig:
    pricing_version: str
    cost_rates: Mapping[str, float]

    def __post_init__(self) -> None:
        normalized = _normalized_cost_rates(self.pricing_version, self.cost_rates)
        object.__setattr__(self, "cost_rates", MappingProxyType(normalized))

    @property
    def scoring_config_digest(self) -> str:
        return canonical_digest(
            {
                "pricing_version": self.pricing_version,
                "cost_rates": self.cost_rates,
            }
        )


@dataclass(frozen=True)
class ResultStore:
    path: Path


@dataclass(frozen=True)
class ResultSourceBundle:
    manifest: ResultSourceManifest
    results: tuple[ResultRecord, ...]
    result_records_path: Path


class ResultStoreSession:
    """One locked, indexed append session for a Runner operation."""

    def __init__(
        self,
        store: ResultStore,
        handle: TextIO,
        results: Sequence[ResultRecord],
        *,
        created: bool,
    ) -> None:
        self.store = store
        self._handle = handle
        self._results = list(results)
        self._result_by_id: dict[str, ResultRecord] = {}
        for result in results:
            self._result_by_id.setdefault(result.result_id, result)
        self._created = created

    @property
    def results(self) -> tuple[ResultRecord, ...]:
        return tuple(self._results)

    def append(self, result: ResultRecord) -> ResultRecord:
        return self.append_many((result,))[0]

    def append_many(self, results: Sequence[ResultRecord]) -> tuple[ResultRecord, ...]:
        accepted: list[ResultRecord] = []
        new_results: list[ResultRecord] = []
        pending_by_id: dict[str, ResultRecord] = {}
        for result in results:
            errors = _result_record_errors(result)
            if errors:
                raise ValueError(f"result record is invalid: {', '.join(errors)}")
            stored = self._result_by_id.get(result.result_id) or pending_by_id.get(
                result.result_id
            )
            if stored is not None:
                if stored.result_digest != result.result_digest:
                    raise ValueError("result_id already exists with a different digest")
                accepted.append(stored)
                continue
            pending_by_id[result.result_id] = result
            new_results.append(result)
            accepted.append(result)
        if new_results:
            payload = "".join(f"{canonical_json(result)}\n" for result in new_results)
            self._handle.write(payload)
            self._handle.flush()
            os.fsync(self._handle.fileno())
            if self._created:
                _fsync_directory(self.store.path.parent)
                self._created = False
            self._results.extend(new_results)
            self._result_by_id.update(
                (result.result_id, result) for result in new_results
            )
        return tuple(accepted)


@dataclass(frozen=True)
class ResultQuery:
    task_ids: tuple[str, ...] = ()
    check_ids: tuple[str, ...] = ()
    agent_ids: tuple[str, ...] = ()
    result_ids: tuple[str, ...] = ()
    cache_identity_digests: tuple[str, ...] = ()
    scoring_config_digests: tuple[str, ...] = ()
    result_available_after: str | None = None
    result_available_before: str | None = None


@dataclass(frozen=True)
class ResultCacheConfig:
    reuse_benchmark_invalid: bool = False

    def __post_init__(self) -> None:
        if type(self.reuse_benchmark_invalid) is not bool:
            raise ValueError("reuse_benchmark_invalid must be a bool")


@dataclass(frozen=True)
class ResultJoinConfig:
    missing_cell_policy: str = "mark_missing"
    agent_invalid_policy: str = "count_as_failure"
    benchmark_invalid_policy: str = "exclude_task_check"
    abstention_policy: str = "abstain_on_missing"

    def __post_init__(self) -> None:
        supported = {
            "missing_cell_policy": {"error", "mark_missing"},
            "agent_invalid_policy": {"count_as_failure", "exclude"},
            "benchmark_invalid_policy": {"exclude_task_check"},
            "abstention_policy": {"abstain_on_missing"},
        }
        for field_name, allowed_values in supported.items():
            value = getattr(self, field_name)
            if value not in allowed_values:
                allowed = ", ".join(sorted(allowed_values))
                raise ValueError(f"{field_name} must be one of: {allowed}")

    @property
    def join_policy_digest(self) -> str:
        return canonical_digest(
            {
                "missing_cell_policy": self.missing_cell_policy,
                "agent_invalid_policy": self.agent_invalid_policy,
                "benchmark_invalid_policy": self.benchmark_invalid_policy,
                "abstention_policy": self.abstention_policy,
            }
        )

    @property
    def denominator_policy_digest(self) -> str:
        return canonical_digest(
            {
                "agent_invalid_policy": self.agent_invalid_policy,
                "benchmark_invalid_policy": self.benchmark_invalid_policy,
            }
        )


def build_result_record(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_run: WorkspaceRunRecord,
    cache_identity: ResultCacheIdentity,
    scoring_config: ScoringConfig,
) -> ResultRecord:
    _validate_task_check_agent_records(task, check, agent)
    workspace_run_validation = validate_workspace_run(workspace_run)
    if not workspace_run_validation.ok:
        raise ValueError(
            f"workspace_run is invalid: {', '.join(workspace_run_validation.errors)}"
        )
    _validate_task_check_agent_linkage(task, check, agent, workspace_run)
    _validate_cache_identity_inputs(task, check, agent, cache_identity)
    scoreable_state, outcome, invalid_owner = _normalize_result_state(workspace_run)
    result_available_at = _latest_timestamp_utc(_now(), workspace_run.finished_at)
    result = ResultRecord(
        result_id="",
        result_digest="",
        cache_identity=cache_identity,
        agent_id=agent.agent_id,
        task_id=task.task_id,
        check_id=check.check_id,
        terminal_status=workspace_run.terminal_status,
        scoreable_state=scoreable_state,
        outcome=outcome,
        invalid_owner=invalid_owner,
        failure_label=workspace_run.failure_label,
        cost=compute_cost(workspace_run.usage, scoring_config),
        scoring_config_digest=scoring_config.scoring_config_digest,
        pricing_version=scoring_config.pricing_version,
        usage=workspace_run.usage,
        latency=_latency_from_workspace_run(workspace_run),
        diff_digest=workspace_run.diff_digest,
        verifier_metadata_digest=_verifier_metadata_digest(workspace_run),
        started_at=workspace_run.started_at,
        finished_at=workspace_run.finished_at,
        evidence_source_kind="barcarolle_managed",
        evidence_source_manifest_digest=None,
        evidence_imported_at=None,
        source_result_available_at=result_available_at,
        availability_policy="managed_observation_v1",
        result_available_at=result_available_at,
    )
    result = replace(result, result_id=compute_result_id(result))
    result = record_with_digest(result)
    result_validation = validate_result(result)
    if not result_validation.ok:
        raise ValueError(
            f"result record is invalid: {', '.join(result_validation.errors)}"
        )
    return result


def compute_result_cache_identity(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
) -> ResultCacheIdentity:
    _validate_task_check_agent_records(task, check, agent)
    _validate_cache_identity_configs(workspace_config, runtime_config)
    _validate_task_check_linkage(task, check)
    identity = make_result_cache_identity(
        task,
        check,
        agent,
        workspace_config,
        runtime_config,
    )
    validation = validate_result_cache_identity(identity)
    if not validation.ok:
        raise ValueError(
            f"result cache identity is invalid: {', '.join(validation.errors)}"
        )
    return identity


def compute_result_cache_key(identity: ResultCacheIdentity) -> str:
    return make_result_cache_key(identity)


def store_result(result: ResultRecord, store: ResultStore) -> ResultRecord:
    return store_results((result,), store)[0]


def store_results(
    results: Sequence[ResultRecord], store: ResultStore
) -> tuple[ResultRecord, ...]:
    if not results:
        return ()
    with open_result_store_session(store) as session:
        return session.append_many(results)


def load_result_source_bundle(manifest_path: Path) -> ResultSourceBundle:
    manifest_file = manifest_path.resolve()
    if manifest_file.name != "result-source-manifest.jsonl":
        raise ValueError(
            "Result source manifest must be named result-source-manifest.jsonl"
        )
    try:
        manifests = tuple(load_jsonl_records(manifest_file, ResultSourceManifest))
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError("Result source manifest is unavailable or invalid") from exc
    if len(manifests) != 1:
        raise ValueError("Result source manifest must contain exactly one record")
    manifest = manifests[0]
    errors = _result_source_manifest_errors(manifest)
    if errors:
        raise ValueError("Result source manifest is invalid: " + "; ".join(errors))
    result_path = _result_source_ref_path(
        manifest_file.parent,
        manifest.result_records_ref,
    )
    try:
        results = tuple(load_jsonl_records(result_path, ResultRecord))
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError("source Result records are unavailable or invalid") from exc
    ensure_unique_result_ids(results)
    if canonical_digest(results) != manifest.result_records_digest:
        raise ValueError("source Result records digest does not match manifest")
    return ResultSourceBundle(manifest, results, result_path)


def load_result_import_receipt(path: Path) -> ResultImportReceipt | None:
    if not path.exists():
        return None
    try:
        receipts = tuple(load_jsonl_records(path, ResultImportReceipt))
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError("Result import receipt is unavailable or invalid") from exc
    if len(receipts) != 1:
        raise ValueError("Result import receipt must contain exactly one record")
    receipt = receipts[0]
    errors = _result_import_receipt_errors(receipt)
    if errors:
        raise ValueError("Result import receipt is invalid: " + "; ".join(errors))
    return receipt


def write_result_import_receipt(
    receipt: ResultImportReceipt,
    path: Path,
) -> ResultImportReceipt:
    errors = _result_import_receipt_errors(receipt)
    if errors:
        raise ValueError("Result import receipt is invalid: " + "; ".join(errors))
    existing = load_result_import_receipt(path)
    if existing is not None:
        if existing != receipt:
            raise ValueError(
                "Result import receipt path already contains other evidence"
            )
        return existing
    write_jsonl_records(path, (receipt,))
    return receipt


def _result_source_manifest_errors(
    manifest: ResultSourceManifest,
) -> tuple[str, ...]:
    errors: list[str] = []
    if manifest.schema_version != RESULT_SOURCE_MANIFEST_SCHEMA_VERSION:
        errors.append("schema_version is not supported")
    if not manifest.producer_id:
        errors.append("producer_id is required")
    if not manifest.authority_digest:
        errors.append("authority_digest is required")
    if manifest.availability_semantics not in {
        "import_time_floor_v1",
        "producer_attested_historical_v1",
    }:
        errors.append("availability_semantics is not supported")
    try:
        created_at = _canonical_timestamp(manifest.created_at)
    except (TypeError, ValueError):
        errors.append("created_at is invalid")
    else:
        if created_at != manifest.created_at:
            errors.append("created_at is not canonical UTC")
    if manifest.manifest_digest != canonical_digest(manifest, exclude_self_digest=True):
        errors.append("manifest_digest does not match canonical content")
    return tuple(errors)


def _result_import_receipt_errors(
    receipt: ResultImportReceipt,
) -> tuple[str, ...]:
    errors: list[str] = []
    required_strings = (
        "receipt_id",
        "source_manifest_digest",
        "source_result_records_digest",
        "target_task_pool_id",
        "target_task_pool_digest",
        "accepted_authority_digest",
        "workspace_config_digest",
        "runtime_config_digest",
    )
    for field_name in required_strings:
        value = getattr(receipt, field_name)
        if not isinstance(value, str) or not value:
            errors.append(f"{field_name} is required")
    if receipt.availability_policy not in {
        "import_time_floor_v1",
        "producer_attested_historical_v1",
    }:
        errors.append("availability_policy is not supported")
    try:
        imported_at = _canonical_timestamp(receipt.imported_at)
    except (TypeError, ValueError):
        errors.append("imported_at is invalid")
    else:
        if imported_at != receipt.imported_at:
            errors.append("imported_at is not canonical UTC")
    agent_digests = receipt.agent_record_digests
    if (
        not agent_digests
        or any(not isinstance(value, str) or not value for value in agent_digests)
        or len(agent_digests) != len(set(agent_digests))
    ):
        errors.append("agent_record_digests must be a nonempty unique tuple")
    for index, decision in enumerate(receipt.decisions):
        if not decision.source_result_id or not decision.source_result_digest:
            errors.append(f"decision {index} source Result binding is required")
        if decision.status in {"admitted", "idempotent"}:
            if (
                not decision.local_result_id
                or not decision.local_result_digest
                or decision.rejection_reasons
            ):
                errors.append(
                    f"decision {index} accepted state is internally inconsistent"
                )
        elif decision.status == "rejected":
            if (
                decision.local_result_id is not None
                or decision.local_result_digest is not None
                or not decision.rejection_reasons
                or any(
                    not isinstance(reason, str) or not reason
                    for reason in decision.rejection_reasons
                )
            ):
                errors.append(
                    f"decision {index} rejected state is internally inconsistent"
                )
        else:
            errors.append(f"decision {index} status is not normalized")
    expected_receipt_id = "result_import_" + canonical_digest(
        {
            "source_manifest_digest": receipt.source_manifest_digest,
            "target_task_pool_digest": receipt.target_task_pool_digest,
            "imported_at": receipt.imported_at,
            "availability_policy": receipt.availability_policy,
        }
    )
    if receipt.receipt_id != expected_receipt_id:
        errors.append("receipt_id does not match import identity")
    try:
        expected_digest = canonical_digest(receipt, exclude_self_digest=True)
    except (OverflowError, TypeError, ValueError):
        errors.append("receipt is not strict canonical JSON")
    else:
        if receipt.receipt_digest != expected_digest:
            errors.append("receipt_digest does not match")
    return tuple(errors)


def _result_source_ref_path(root: Path, ref: str) -> Path:
    if not isinstance(ref, str) or not ref:
        raise ValueError("result_records_ref is invalid")
    path = Path(ref)
    if path.is_absolute() or path.name != "results.jsonl":
        raise ValueError("result_records_ref must be relative and named results.jsonl")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("result_records_ref escapes Result source root")
    return resolved


def normalize_external_result(
    result: ResultRecord,
    *,
    source_manifest_digest: str,
    imported_at: str,
    availability_policy: str,
) -> ResultRecord:
    if not source_manifest_digest:
        raise ValueError("source_manifest_digest must not be empty")
    if availability_policy not in {
        "import_time_floor_v1",
        "producer_attested_historical_v1",
    }:
        raise ValueError("external Result availability policy is not supported")
    imported = _canonical_timestamp(imported_at)
    source_available = _canonical_timestamp(result.source_result_available_at)
    effective_available = (
        _latest_timestamp_utc(source_available, imported)
        if availability_policy == "import_time_floor_v1"
        else source_available
    )
    normalized = replace(
        result,
        result_id="",
        result_digest="",
        evidence_source_kind="external_attested",
        evidence_source_manifest_digest=source_manifest_digest,
        evidence_imported_at=imported,
        source_result_available_at=source_available,
        availability_policy=availability_policy,
        result_available_at=effective_available,
    )
    normalized = replace(normalized, result_id=compute_result_id(normalized))
    normalized = record_with_digest(normalized)
    validation = validate_result(normalized)
    if not validation.ok:
        raise ValueError(
            "normalized external Result is invalid: " + ", ".join(validation.errors)
        )
    return normalized


def ambiguous_result_execution_keys(
    results: Sequence[ResultRecord],
) -> frozenset[tuple[str, str, str, ResultCacheIdentity]]:
    executions: dict[
        tuple[str, str, str, ResultCacheIdentity],
        set[str],
    ] = {}
    for result in results:
        if not validate_result(result).ok:
            continue
        key = (
            result.agent_id,
            result.task_id,
            result.check_id,
            result.cache_identity,
        )
        executions.setdefault(key, set()).add(result_execution_digest(result))
    return frozenset(key for key, digests in executions.items() if len(digests) > 1)


def ensure_unambiguous_result_executions(
    results: Sequence[ResultRecord],
) -> None:
    conflicts = ambiguous_result_execution_keys(results)
    if not conflicts:
        return
    identity_digests = sorted(key[3].identity_digest for key in conflicts)
    raise ValueError(
        "conflicting Result executions share cache identities: "
        + ", ".join(identity_digests)
    )


def canonical_result_execution_view(
    results: Sequence[ResultRecord],
) -> ResultRecord:
    """Choose one stable Result view for a known-identical paid execution."""
    if not results:
        raise ValueError("at least one Result execution view is required")
    return min(results, key=lambda result: result.result_id)


def ensure_unique_result_ids(results: Sequence[ResultRecord]) -> None:
    """Reject a Result collection whose identities are not one-to-one."""
    result_ids = tuple(result.result_id for result in results)
    if len(result_ids) != len(set(result_ids)):
        raise ValueError("Result collection contains duplicate result IDs")


@contextmanager
def open_result_store_session(
    store: ResultStore,
) -> Iterator[ResultStoreSession]:
    store.path.parent.mkdir(parents=True, exist_ok=True)
    created = not store.path.exists()
    handle = store.path.open("a+", encoding="utf-8", newline="")
    try:
        _lock_store_file(handle, exclusive=True)
        results = _load_results_unlocked(store)
        handle.seek(0, os.SEEK_END)
        yield ResultStoreSession(store, handle, results, created=created)
    finally:
        _unlock_store_file(handle)
        handle.close()


def load_results(store: ResultStore, query: ResultQuery) -> Sequence[ResultRecord]:
    available_after, available_before = _query_time_bounds(query)
    if not store.path.exists():
        return ()
    with store.path.open("rb") as lock_handle:
        _lock_store_file(lock_handle, exclusive=False)
        try:
            results = _load_results_unlocked(store)
        finally:
            _unlock_store_file(lock_handle)
    return _filter_results(
        results,
        query,
        available_after=available_after,
        available_before=available_before,
    )


def recover_result_store_tail(store: ResultStore) -> str:
    """Explicitly repair one interrupted, unterminated final JSONL line.

    A parseable final JSON value is completed with a newline and left for normal
    schema validation. An unparseable byte tail is truncated to the last durable
    newline. Complete lines are never removed.
    """
    if not store.path.exists():
        return "not_needed"
    with store.path.open("r+b") as handle:
        _lock_store_file(handle, exclusive=True)
        try:
            data = handle.read()
            if not data or data.endswith(b"\n"):
                return "not_needed"
            tail_start = data.rfind(b"\n") + 1
            tail = data[tail_start:]
            try:
                json.loads(tail.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                handle.seek(tail_start)
                handle.truncate()
                action = "truncated"
            else:
                handle.seek(0, os.SEEK_END)
                handle.write(b"\n")
                action = "completed"
            handle.flush()
            os.fsync(handle.fileno())
            return action
        finally:
            _unlock_store_file(handle)


def _load_results_unlocked(store: ResultStore) -> tuple[ResultRecord, ...]:
    if not store.path.exists():
        return ()
    with store.path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        if size:
            handle.seek(-1, os.SEEK_END)
            if handle.read(1) != b"\n":
                raise ValueError(
                    f"{store.path}: unterminated final line; "
                    "run recover_result_store_tail explicitly"
                )
    results = tuple(load_jsonl_records(store.path, ResultRecord))
    for line_number, result in enumerate(results, start=1):
        errors = _result_record_errors(result)
        if errors:
            raise ValueError(
                f"{store.path}: line {line_number}: invalid Result record: "
                + ", ".join(errors)
            )
    _require_unique_result_ids(store.path, results)
    return results


def _require_unique_result_ids(
    path: Path,
    results: Sequence[ResultRecord],
) -> None:
    seen: dict[str, ResultRecord] = {}
    for line_number, result in enumerate(results, start=1):
        existing = seen.get(result.result_id)
        if existing is not None:
            digest_detail = (
                " with a different digest"
                if existing.result_digest != result.result_digest
                else ""
            )
            raise ValueError(
                f"{path}: line {line_number}: duplicate result_id "
                f"{result.result_id}{digest_detail}"
            )
        seen[result.result_id] = result


def _filter_results(
    results: Sequence[ResultRecord],
    query: ResultQuery,
    *,
    available_after: datetime | None,
    available_before: datetime | None,
) -> tuple[ResultRecord, ...]:

    return tuple(
        result
        for result in results
        if _matches_query(
            result,
            query,
            available_after=available_after,
            available_before=available_before,
        )
    )


def _query_time_bounds(query: ResultQuery) -> tuple[datetime | None, datetime | None]:
    _validate_query_filters(query)
    available_after = _query_timestamp(
        "result_available_after",
        query.result_available_after,
    )
    available_before = _query_timestamp(
        "result_available_before",
        query.result_available_before,
    )
    if (
        available_after is not None
        and available_before is not None
        and available_after > available_before
    ):
        raise ValueError(
            "result_available_after must not be after result_available_before"
        )
    return available_after, available_before


def _validate_query_filters(query: ResultQuery) -> None:
    for field_name in (
        "task_ids",
        "check_ids",
        "agent_ids",
        "result_ids",
        "cache_identity_digests",
        "scoring_config_digests",
    ):
        values = getattr(query, field_name)
        if type(values) is not tuple or any(
            not isinstance(value, str) or not value for value in values
        ):
            raise ValueError(f"{field_name} must be a tuple of non-empty strings")


def _query_timestamp(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be null or a non-empty timestamp string")
    return parse_utc_timestamp(value)


def _session_results(
    store: ResultStore, session: ResultStoreSession | None
) -> tuple[ResultRecord, ...]:
    if session is None:
        return tuple(load_results(store, ResultQuery()))
    _ensure_session_store(store, session)
    return session.results


def _ensure_session_store(store: ResultStore, session: ResultStoreSession) -> None:
    if session.store.path.resolve() != store.path.resolve():
        raise ValueError("ResultStoreSession does not match ResultStore")


def find_missing_results(
    task_check_refs: Sequence[TaskCheckRef],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    store: ResultStore,
    cache_config: ResultCacheConfig,
    *,
    session: ResultStoreSession | None = None,
) -> Sequence[ResultCellRef]:
    return tuple(
        cell
        for cell in resolve_result_cells(
            task_check_refs,
            tasks,
            checks,
            agents,
            workspace_config,
            runtime_config,
            store,
            cache_config,
            session=session,
        )
        if cell.cell_state == "missing"
    )


def resolve_result_cells(
    task_check_refs: Sequence[TaskCheckRef],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    store: ResultStore,
    cache_config: ResultCacheConfig,
    scoring_config: ScoringConfig | None = None,
    *,
    session: ResultStoreSession | None = None,
) -> Sequence[ResultCellRef]:
    """Resolve each requested Agent/Task/Check cell against exact cached identity.

    Multiple pricing views of one execution are interchangeable for execution
    reuse. Distinct executions under one exact identity are an evidence
    conflict and must be resolved explicitly rather than by append order.
    """
    ref_keys = tuple((ref.task_id, ref.check_id) for ref in task_check_refs)
    if len(set(ref_keys)) != len(ref_keys):
        raise ValueError("duplicate Task/Check refs are not allowed")
    agent_ids = tuple(agent.agent_id for agent in agents)
    if len(set(agent_ids)) != len(agent_ids):
        raise ValueError("duplicate Agent IDs are not allowed")
    task_by_id = {task.task_id: task for task in tasks}
    stored_results = _session_results(store, session)
    reusable_results = _index_reusable_results(
        stored_results,
        cache_config,
        scoring_config.scoring_config_digest if scoring_config is not None else None,
    )
    cells: list[ResultCellRef] = []
    for ref in task_check_refs:
        task = _task_for_ref(ref, task_by_id)
        check = _check_for_ref(ref, task, checks)
        for agent in agents:
            identity = compute_result_cache_identity(
                task, check, agent, workspace_config, runtime_config
            )
            reusable = reusable_results.get(
                (agent.agent_id, task.task_id, check.check_id, identity)
            )
            cells.append(_resolved_result_cell(agent, task, check, identity, reusable))
    return tuple(cells)


def reprice_cached_results(
    task_check_refs: Sequence[TaskCheckRef],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    store: ResultStore,
    cache_config: ResultCacheConfig,
    scoring_config: ScoringConfig,
    *,
    session: ResultStoreSession | None = None,
) -> Sequence[ResultRecord]:
    """Append the current pricing view for reusable paid executions.

    Execution reuse is still decided solely by exact ``ResultCacheIdentity``.
    If that execution has no Result under the requested pricing, retained usage
    and outcome evidence are repriced without invoking an Agent or Check.
    """
    if session is None:
        with open_result_store_session(store) as owned_session:
            return reprice_cached_results(
                task_check_refs,
                tasks,
                checks,
                agents,
                workspace_config,
                runtime_config,
                store,
                cache_config,
                scoring_config,
                session=owned_session,
            )
    _ensure_session_store(store, session)
    current_cells = resolve_result_cells(
        task_check_refs,
        tasks,
        checks,
        agents,
        workspace_config,
        runtime_config,
        store,
        cache_config,
        scoring_config,
        session=session,
    )
    current_keys = {
        (cell.agent_id, cell.task_id, cell.check_id)
        for cell in current_cells
        if cell.cell_state == "result"
    }
    if all(cell.cell_state == "result" for cell in current_cells):
        return ()

    execution_cells = resolve_result_cells(
        task_check_refs,
        tasks,
        checks,
        agents,
        workspace_config,
        runtime_config,
        store,
        cache_config,
        session=session,
    )
    source_bindings = {
        (cell.result_id, cell.result_digest)
        for cell in execution_cells
        if cell.result_id is not None and cell.result_digest is not None
    }
    if not source_bindings:
        return ()
    source_results = {
        (result.result_id, result.result_digest): result
        for result in session.results
        if (result.result_id, result.result_digest) in source_bindings
    }
    repriced: list[ResultRecord] = []
    for cell in execution_cells:
        cell_key = (cell.agent_id, cell.task_id, cell.check_id)
        if (
            cell_key in current_keys
            or cell.result_id is None
            or cell.result_digest is None
        ):
            continue
        source = source_results.get((cell.result_id, cell.result_digest))
        if source is None:
            raise ValueError(
                f"cached result binding is missing for result_id {cell.result_id}"
            )
        repriced.append(_reprice_result(source, scoring_config))
    return session.append_many(repriced)


def build_result_matrix(
    evaluation_cells: EvaluationCellSet,
    task_check_refs: Sequence[TaskCheckRef],
    tasks: Sequence[TaskRecord],
    checks: Mapping[str, CheckRecord],
    agents: Sequence[AgentRecord],
    results: Sequence[ResultRecord],
    matrix_role: str,
    join_config: ResultJoinConfig,
) -> ResultMatrix:
    cell_validation = validate_evaluation_cell_set(evaluation_cells)
    if not cell_validation.ok:
        raise ValueError(
            f"evaluation cell set is invalid: {', '.join(cell_validation.errors)}"
        )
    expected_refs = _matrix_refs(evaluation_cells, matrix_role)
    requested_refs = tuple(task_check_refs)
    if requested_refs != expected_refs:
        raise ValueError(
            "task_check_refs must exactly match the evaluation subset for matrix_role"
        )
    task_by_id = {task.task_id: task for task in tasks}
    for ref in requested_refs:
        task = _task_for_ref(ref, task_by_id)
        _check_for_ref(ref, task, checks)
    result_by_binding = _results_by_binding(results)
    required_cells = _required_cells_by_key(
        evaluation_cells.cells, requested_refs, agents
    )
    resolved_results = {
        cell_key: result
        for cell_key, required in required_cells.items()
        if (result := _result_for_required_cell(required, result_by_binding))
        is not None
    }
    task_exclusions = _task_check_exclusions(
        required_cells, resolved_results, join_config
    )
    has_agent_specific_exclusion = _has_agent_specific_exclusion(
        resolved_results,
        task_exclusions,
        join_config,
    )
    matrix_cells: list[ResultCellRef] = []
    for agent in agents:
        for ref in requested_refs:
            required = required_cells.get((agent.agent_id, ref.task_id, ref.check_id))
            if required is None:
                raise ValueError(
                    "evaluation_cells must include every matrix Agent/Task/Check cell"
                )
            result = resolved_results.get(
                (required.agent_id, required.task_id, required.check_id)
            )
            exclusion_reason = task_exclusions.get((ref.task_id, ref.check_id))
            matrix_cells.append(
                _matrix_cell(required, result, join_config, exclusion_reason)
            )
    abstention_reason = _abstention_reason(
        matrix_cells,
        join_config,
        has_agent_specific_exclusion=has_agent_specific_exclusion,
    )
    matrix = ResultMatrix(
        matrix_id=f"matrix_{canonical_digest((evaluation_cells.cell_set_id, matrix_role, join_config.join_policy_digest, tuple(task_check_refs)))}",
        matrix_role=matrix_role,
        origin_id=evaluation_cells.origin_id,
        selection_id=evaluation_cells.selection_id,
        agent_ids=tuple(agent.agent_id for agent in agents),
        task_check_refs=requested_refs,
        cells=tuple(matrix_cells),
        join_policy_digest=join_config.join_policy_digest,
        denominator_policy_digest=join_config.denominator_policy_digest,
        abstention_reason=abstention_reason,
        scoreable_state="abstained"
        if abstention_reason
        else _matrix_scoreable_state(matrix_cells),
        matrix_digest="",
    )
    matrix = record_with_digest(matrix)
    matrix_validation = validate_result_matrix(matrix)
    if not matrix_validation.ok:
        raise ValueError(
            f"result matrix is invalid: {', '.join(matrix_validation.errors)}"
        )
    return matrix


def _validate_task_check_agent_linkage(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_run: WorkspaceRunRecord,
) -> None:
    _validate_task_check_linkage(task, check)
    if (
        workspace_run.task_id != task.task_id
        or workspace_run.check_id != check.check_id
    ):
        raise ValueError("workspace_run task/check does not match result inputs")
    if workspace_run.agent_id != agent.agent_id:
        raise ValueError("workspace_run agent does not match result inputs")


def _validate_task_check_agent_records(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
) -> None:
    for record_name, validation in (
        ("task", validate_task(task)),
        ("check", validate_check(check)),
        ("agent", validate_agent(agent)),
    ):
        if not validation.ok:
            raise ValueError(
                f"{record_name} is invalid: {', '.join(validation.errors)}"
            )


def _validate_task_check_linkage(task: TaskRecord, check: CheckRecord) -> None:
    if check.task_id != task.task_id or check.check_id not in task.check_ids:
        raise ValueError("check must be linked to task")


def _validate_cache_identity_configs(
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
) -> None:
    for config_name, validation in (
        ("workspace_config", validate_workspace_config(workspace_config)),
        ("runtime_config", validate_runtime_config(runtime_config)),
    ):
        if not validation.ok:
            raise ValueError(
                f"{config_name} is invalid: {', '.join(validation.errors)}"
            )


def _validate_cache_identity_inputs(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    identity: ResultCacheIdentity,
) -> None:
    validation = validate_result_cache_identity(identity)
    if not validation.ok:
        raise ValueError(f"cache identity is invalid: {', '.join(validation.errors)}")
    mismatched = (
        *cache_identity_task_check_mismatches(identity, task, check),
        *cache_identity_agent_mismatches(identity, agent),
    )
    if mismatched:
        raise ValueError(
            f"cache identity does not match result inputs: {', '.join(mismatched)}"
        )


def _normalize_result_state(
    workspace_run: WorkspaceRunRecord,
) -> tuple[ResultScoreableState, CheckOutcomeValue, InvalidOwner | None]:
    if (
        workspace_run.terminal_status == "passed"
        and workspace_run.check_outcome == "pass"
    ):
        return ("scoreable", "pass", None)
    if workspace_run.terminal_status == "failed":
        return ("scoreable", "fail", None)
    invalid_owner = workspace_run.invalid_owner
    if workspace_run.terminal_status in {"error", "timeout"}:
        invalid_owner = invalid_owner or "agent"
    if invalid_owner == "agent":
        return ("agent_invalid", "invalid", "agent")
    return ("benchmark_invalid", "invalid", invalid_owner or "benchmark")


def validate_scoring_config(scoring_config: ScoringConfig) -> None:
    """Reject scoring inputs that cannot produce a durable Result."""
    _normalized_cost_rates(
        scoring_config.pricing_version,
        scoring_config.cost_rates,
    )


def compute_cost(
    usage: Mapping[str, Any], scoring_config: ScoringConfig
) -> Mapping[str, Any]:
    """Price recorded usage without affecting the paid execution identity."""
    validate_scoring_config(scoring_config)
    missing_keys = [key for key in scoring_config.cost_rates if key not in usage]
    costs: dict[str, Any] = {}
    total = 0.0
    for key, rate in scoring_config.cost_rates.items():
        if key not in usage:
            continue
        value = usage[key]
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(
                f"usage and cost rate for {key} must be finite and nonnegative numbers"
            )
        try:
            numeric_value = float(value)
            numeric_rate = float(rate)
            amount = numeric_value * numeric_rate
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(
                f"usage and cost rate for {key} must be finite and nonnegative numbers"
            ) from exc
        if not all(
            isfinite(number) and number >= 0.0
            for number in (numeric_value, numeric_rate, amount)
        ):
            raise ValueError(
                f"usage and cost rate for {key} must be finite and nonnegative numbers"
            )
        costs[f"{key}_cost"] = amount
        total += amount
    costs["total_cost"] = (
        total if usage and scoring_config.cost_rates and not missing_keys else None
    )
    return costs


def _latency_from_workspace_run(workspace_run: WorkspaceRunRecord) -> Mapping[str, Any]:
    return dict(workspace_run.latency)


def _latest_timestamp_utc(*values: str) -> str:
    latest = max(parse_utc_timestamp(value) for value in values)
    return format_utc_timestamp(latest)


def _canonical_timestamp(value: str) -> str:
    return format_utc_timestamp(parse_utc_timestamp(value))


def _verifier_metadata_digest(workspace_run: WorkspaceRunRecord) -> str:
    return canonical_digest(
        {
            "workspace_run_id": workspace_run.workspace_run_id,
            "solver_workspace_digest": workspace_run.solver_workspace_digest,
            "verifier_workspace_digest": workspace_run.verifier_workspace_digest,
            "replay_status": workspace_run.replay_status,
            "check_outcome": workspace_run.check_outcome,
        }
    )


def result_execution_digest(result: ResultRecord) -> str:
    """Digest one paid execution independently of its pricing views."""
    return make_result_execution_digest(result)


def compute_result_id(result: ResultRecord) -> str:
    """Return the canonical ID for one Result execution, price, and evidence view."""
    return make_result_id(result)


def _result_record_errors(result: ResultRecord) -> tuple[str, ...]:
    return validate_result(result).errors


def result_evidence_digest(result: ResultRecord) -> str:
    return make_result_evidence_digest(result)


def _reprice_result(
    result: ResultRecord, scoring_config: ScoringConfig
) -> ResultRecord:
    repriced = replace(
        result,
        result_id="",
        result_digest="",
        cost=compute_cost(result.usage, scoring_config),
        scoring_config_digest=scoring_config.scoring_config_digest,
        pricing_version=scoring_config.pricing_version,
    )
    repriced = replace(repriced, result_id=compute_result_id(repriced))
    repriced = record_with_digest(repriced)
    validation = validate_result(repriced)
    if not validation.ok:
        raise ValueError(
            f"repriced result record is invalid: {', '.join(validation.errors)}"
        )
    return repriced


def _matches_query(
    result: ResultRecord,
    query: ResultQuery,
    *,
    available_after: datetime | None,
    available_before: datetime | None,
) -> bool:
    if query.task_ids and result.task_id not in query.task_ids:
        return False
    if query.check_ids and result.check_id not in query.check_ids:
        return False
    if query.agent_ids and result.agent_id not in query.agent_ids:
        return False
    if query.result_ids and result.result_id not in query.result_ids:
        return False
    if (
        query.cache_identity_digests
        and result.cache_identity.identity_digest not in query.cache_identity_digests
    ):
        return False
    if (
        query.scoring_config_digests
        and result.scoring_config_digest not in query.scoring_config_digests
    ):
        return False
    if available_after is not None or available_before is not None:
        result_available_at = parse_utc_timestamp(result.result_available_at)
        if available_after is not None and result_available_at < available_after:
            return False
        if available_before is not None and result_available_at > available_before:
            return False
    return True


def _index_reusable_results(
    results: Sequence[ResultRecord],
    cache_config: ResultCacheConfig,
    scoring_config_digest: str | None = None,
) -> Mapping[tuple[str, str, str, ResultCacheIdentity], ResultRecord]:
    conflicts = ambiguous_result_execution_keys(results)
    if conflicts:
        raise ValueError(
            "conflicting reusable Result executions share one cache identity: "
            + ", ".join(sorted(key[3].identity_digest for key in conflicts))
        )
    reusable: dict[tuple[str, str, str, ResultCacheIdentity], ResultRecord] = {}
    for result in results:
        if (
            scoring_config_digest is not None
            and result.scoring_config_digest != scoring_config_digest
        ):
            continue
        if not validate_result(result).ok:
            continue
        if (
            result.scoreable_state == "benchmark_invalid"
            and not cache_config.reuse_benchmark_invalid
        ):
            continue
        key = (result.agent_id, result.task_id, result.check_id, result.cache_identity)
        existing = reusable.get(key)
        if existing is None:
            reusable[key] = result
            continue
        if result_execution_digest(existing) != result_execution_digest(result):
            raise ValueError(
                "conflicting reusable Result executions share one cache identity: "
                f"{result.cache_identity.identity_digest}"
            )
        reusable[key] = canonical_result_execution_view((existing, result))
    return reusable


def _resolved_result_cell(
    agent: AgentRecord,
    task: TaskRecord,
    check: CheckRecord,
    identity: ResultCacheIdentity,
    result: ResultRecord | None,
) -> ResultCellRef:
    if result is None:
        return ResultCellRef(
            agent_id=agent.agent_id,
            task_id=task.task_id,
            check_id=check.check_id,
            required_identity_digest=identity.identity_digest,
            result_id=None,
            result_digest=None,
            cell_state="missing",
            exclusion_reason=None,
            outcome=None,
        )
    return ResultCellRef(
        agent_id=agent.agent_id,
        task_id=task.task_id,
        check_id=check.check_id,
        required_identity_digest=identity.identity_digest,
        result_id=result.result_id,
        result_digest=result.result_digest,
        cell_state="result",
        exclusion_reason=None,
        outcome=result.outcome,
    )


def _task_for_ref(ref: TaskCheckRef, tasks: Mapping[str, TaskRecord]) -> TaskRecord:
    task = tasks.get(ref.task_id)
    if task is None:
        raise ValueError(f"task is missing for ref {ref.task_id}")
    return task


def _check_for_ref(
    ref: TaskCheckRef, task: TaskRecord, checks: Mapping[str, CheckRecord]
) -> CheckRecord:
    check = checks.get(ref.check_id)
    if check is None:
        raise ValueError(f"check is missing for ref {ref.check_id}")
    if check.task_id != task.task_id or check.check_id not in task.check_ids:
        raise ValueError("check must be linked to task")
    return check


def _matrix_refs(
    evaluation_cells: EvaluationCellSet, matrix_role: str
) -> tuple[TaskCheckRef, ...]:
    if matrix_role == "selected":
        return evaluation_cells.selected_task_check_refs
    if matrix_role == "future_holdout":
        return evaluation_cells.future_task_check_refs
    raise ValueError("matrix_role is not normalized")


def _results_by_binding(
    results: Sequence[ResultRecord],
) -> Mapping[tuple[str, str], ResultRecord]:
    by_binding: dict[tuple[str, str], ResultRecord] = {}
    for result in results:
        validation = validate_result(result)
        if not validation.ok:
            continue
        by_binding.setdefault((result.result_id, result.result_digest), result)
    return by_binding


def _result_for_required_cell(
    required: ResultCellRef,
    results: Mapping[tuple[str, str], ResultRecord],
) -> ResultRecord | None:
    if required.result_id is None or required.result_digest is None:
        return None
    result = results.get((required.result_id, required.result_digest))
    if result is None:
        return None
    if result_cell_record_mismatches(required, result):
        return None
    return result


def _required_cells_by_key(
    cells: Sequence[ResultCellRef],
    refs: Sequence[TaskCheckRef],
    agents: Sequence[AgentRecord],
) -> Mapping[tuple[str, str, str], ResultCellRef]:
    allowed_refs = {(ref.task_id, ref.check_id) for ref in refs}
    allowed_agents = {agent.agent_id for agent in agents}
    by_key: dict[tuple[str, str, str], ResultCellRef] = {}
    for cell in cells:
        if (
            cell.agent_id in allowed_agents
            and (cell.task_id, cell.check_id) in allowed_refs
        ):
            by_key[(cell.agent_id, cell.task_id, cell.check_id)] = cell
    return by_key


def _task_check_exclusions(
    required_cells: Mapping[tuple[str, str, str], ResultCellRef],
    result_by_cell: Mapping[tuple[str, str, str], ResultRecord],
    join_config: ResultJoinConfig,
) -> Mapping[tuple[str, str], str]:
    if join_config.benchmark_invalid_policy != "exclude_task_check":
        return {}
    exclusions: dict[tuple[str, str], str] = {}
    for required in required_cells.values():
        result = result_by_cell.get(
            (required.agent_id, required.task_id, required.check_id)
        )
        if result is None or result.invalid_owner != "benchmark":
            continue
        reason = result.failure_label or "benchmark_invalid"
        exclusions[(required.task_id, required.check_id)] = (
            f"task_check_infrastructure_failure:{reason}:{result.result_digest}"
        )
    return exclusions


def _matrix_cell(
    required: ResultCellRef,
    result: ResultRecord | None,
    join_config: ResultJoinConfig,
    task_exclusion_reason: str | None,
) -> ResultCellRef:
    if task_exclusion_reason is not None:
        return ResultCellRef(
            agent_id=required.agent_id,
            task_id=required.task_id,
            check_id=required.check_id,
            required_identity_digest=required.required_identity_digest,
            result_id=result.result_id if result is not None else None,
            result_digest=result.result_digest if result is not None else None,
            cell_state="excluded",
            exclusion_reason=task_exclusion_reason,
            outcome=result.outcome if result is not None else None,
        )
    if result is None:
        if join_config.missing_cell_policy == "error":
            raise ValueError("missing required result cell")
        return ResultCellRef(
            agent_id=required.agent_id,
            task_id=required.task_id,
            check_id=required.check_id,
            required_identity_digest=required.required_identity_digest,
            result_id=None,
            result_digest=None,
            cell_state="missing",
            exclusion_reason=None,
            outcome=None,
        )
    if (
        result.invalid_owner == "agent"
        and join_config.agent_invalid_policy == "exclude"
    ):
        return ResultCellRef(
            agent_id=required.agent_id,
            task_id=required.task_id,
            check_id=required.check_id,
            required_identity_digest=required.required_identity_digest,
            result_id=result.result_id,
            result_digest=result.result_digest,
            cell_state="excluded",
            exclusion_reason=result.failure_label or "agent_invalid",
            outcome=result.outcome,
        )
    return ResultCellRef(
        agent_id=required.agent_id,
        task_id=required.task_id,
        check_id=required.check_id,
        required_identity_digest=required.required_identity_digest,
        result_id=result.result_id,
        result_digest=result.result_digest,
        cell_state="result",
        exclusion_reason=None,
        outcome=result.outcome,
    )


def result_matrix_evidence_errors(
    matrix: ResultMatrix,
    results: Sequence[ResultRecord],
) -> tuple[str, ...]:
    """Check that Matrix policy fields are derivable from their exact Results."""
    results_by_cell, binding_errors = _matrix_results_by_cell(matrix, results)
    return (*binding_errors, *_matrix_policy_evidence_errors(matrix, results_by_cell))


def _matrix_results_by_cell(
    matrix: ResultMatrix,
    results: Sequence[ResultRecord],
) -> tuple[Mapping[tuple[str, str, str], ResultRecord], tuple[str, ...]]:
    results_by_binding = _results_by_binding(results)
    results_by_cell: dict[tuple[str, str, str], ResultRecord] = {}
    errors: list[str] = []
    for cell in matrix.cells:
        if cell.result_id is None and cell.result_digest is None:
            continue
        if cell.result_id is None or cell.result_digest is None:
            errors.append(f"matrix {matrix.matrix_id} has an incomplete Result binding")
            continue
        result = results_by_binding.get((cell.result_id, cell.result_digest))
        if result is None:
            errors.append(
                f"matrix {matrix.matrix_id} references missing Result {cell.result_id}"
            )
            continue
        mismatches = result_cell_record_mismatches(cell, result)
        if mismatches:
            errors.append(
                f"matrix {matrix.matrix_id} cell does not match Result "
                f"{cell.result_id}: {', '.join(mismatches)}"
            )
            continue
        results_by_cell[(cell.agent_id, cell.task_id, cell.check_id)] = result
    return results_by_cell, tuple(errors)


def _matrix_policy_evidence_errors(
    matrix: ResultMatrix,
    results_by_cell: Mapping[tuple[str, str, str], ResultRecord],
) -> tuple[str, ...]:
    cells_by_key = {
        (cell.agent_id, cell.task_id, cell.check_id): cell for cell in matrix.cells
    }
    default_config = ResultJoinConfig()
    task_exclusions = _task_check_exclusions(
        cells_by_key,
        results_by_cell,
        default_config,
    )
    supported_configs = (
        default_config,
        ResultJoinConfig(agent_invalid_policy="exclude"),
        ResultJoinConfig(missing_cell_policy="error"),
        ResultJoinConfig(
            missing_cell_policy="error",
            agent_invalid_policy="exclude",
        ),
    )
    for config in supported_configs:
        if (
            matrix.join_policy_digest != config.join_policy_digest
            or matrix.denominator_policy_digest != config.denominator_policy_digest
        ):
            continue
        expected_cells: list[ResultCellRef] = []
        try:
            for cell in matrix.cells:
                key = (cell.agent_id, cell.task_id, cell.check_id)
                result = results_by_cell.get(key)
                task_exclusion = task_exclusions.get((cell.task_id, cell.check_id))
                expected_cells.append(
                    _matrix_cell(cell, result, config, task_exclusion)
                )
        except ValueError:
            continue
        expected = tuple(expected_cells)
        expected_abstention = _abstention_reason(
            expected,
            config,
            has_agent_specific_exclusion=_has_agent_specific_exclusion(
                results_by_cell,
                task_exclusions,
                config,
            ),
        )
        expected_scoreable_state = (
            "abstained"
            if expected_abstention is not None
            else _matrix_scoreable_state(expected)
        )
        if (
            matrix.cells == expected
            and matrix.abstention_reason == expected_abstention
            and matrix.scoreable_state == expected_scoreable_state
        ):
            return ()
    return (
        f"matrix {matrix.matrix_id} does not follow Result evidence under its "
        "declared Result join policy",
    )


def _has_agent_specific_exclusion(
    results_by_cell: Mapping[tuple[str, str, str], ResultRecord],
    task_exclusions: Mapping[tuple[str, str], str],
    join_config: ResultJoinConfig,
) -> bool:
    return join_config.agent_invalid_policy == "exclude" and any(
        result.invalid_owner == "agent"
        and (result.task_id, result.check_id) not in task_exclusions
        for result in results_by_cell.values()
    )


def _abstention_reason(
    cells: Sequence[ResultCellRef],
    join_config: ResultJoinConfig,
    *,
    has_agent_specific_exclusion: bool,
) -> str | None:
    if join_config.abstention_policy == "abstain_on_missing" and any(
        cell.cell_state == "missing" for cell in cells
    ):
        return "missing_required_results"
    if has_agent_specific_exclusion:
        return "agent_specific_invalid_exclusion"
    return None


def _lock_store_file(handle: Any, *, exclusive: bool) -> None:
    if fcntl is None:
        raise RuntimeError("Result Store file locking requires POSIX fcntl")
    operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    fcntl.flock(handle.fileno(), operation)


def _unlock_store_file(handle: Any) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _fsync_directory(path: Path) -> None:
    directory_fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _matrix_scoreable_state(
    cells: Sequence[ResultCellRef],
) -> MatrixScoreableState:
    if any(cell.cell_state == "missing" for cell in cells):
        return "incomplete"
    if any(cell.cell_state == "excluded" for cell in cells):
        return "complete_with_exclusions"
    return "complete"


def _now() -> str:
    return utc_now_timestamp()
