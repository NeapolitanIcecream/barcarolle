from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
DEFAULT_CONFIG = ROOT / "configs" / "phase1_mvp.yaml"

CLAIM_SCOPE = "phase1_mvp_compiler_infrastructure"
PREDICTIVE_LIMITATION = "insufficient_evidence_for_predictive_validation"
COMPARISON_LABEL = "same_endpoint_model_different_cli_harnesses"
TOOLZ_PROVENANCE = "source_provenance_issue_derived"
HUMANIZE_PROVENANCE = "source_provenance_commit_message_fallback"
CLICK_PROVENANCE = "generic_comparator_archived_click_r0"
RELEASE_STATUSES = {"diagnostic_only", "pilot_grade", "benchmark_grade_candidate", "validation_grade"}
REPO_ROLES = {"primary_target_repo", "second_target_repo", "generic_comparator"}
DISALLOWED_CLAIMS = ["predictive_validity_established", "pure_harness_effect", "production_benchmark_ranking"]
ALLOWED_SCOPE = [
    "multi_repo_compiler_mvp",
    "source_adapter_and_certification_infrastructure",
    "workspace_acut_import_and_score_tables",
    "readiness_and_artifact_hygiene_reports",
]
GATE_ORDER = [
    "checkout",
    "oracle_extractable",
    "no_op_fail",
    "reference_pass",
    "known_bad_fail",
    "flakiness_check",
    "ambiguity_review",
    "solution_leakage_review",
    "scope_clarity_review",
    "cost_boundedness",
    "taxonomy_labelability",
]
BASE_SCORE_TABLE_SOURCES = [
    ("toolz_score_table", "codex_kilo_workspace_followup", "repaired_toolz_click_matrix"),
    ("toolz_stability_score_table", "codex_kilo_workspace_stability", "repaired_toolz_click_stability_repeat"),
    ("humanize_score_table", "humanize_pre_phase1_workspace", "second_repo_humanize_pilot_matrix"),
]
OPTIONAL_SCORE_TABLE_SOURCES = [
    ("boltons_paid_smoke_score_table", "phase1_validation_boltons_paid_smoke", "third_repo_boltons_operational_smoke"),
    (
        "boltons_paid_extension_score_table",
        "phase1_validation_boltons_paid_extension",
        "third_repo_boltons_operational_extension",
    ),
]
REQUIRED_SCORE_COLUMNS = {
    "adapter_id",
    "acut_id",
    "harness_name",
    "model_or_agent_name",
    "task_id",
    "split",
    "attempt",
    "submission_status",
    "terminal_status",
    "scoreable_cell",
    "agent_failure",
    "harness_error",
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class TaskManifest:
    task_id: str
    repo_id: str
    split: str
    certification_status: str
    module_or_package: list[str]
    task_type_proxy: str
    weight: float = 1.0
    evidence_status: str = "certified"

    def validate(self) -> None:
        if not self.task_id:
            raise ValidationError("task_id is required")
        if not self.repo_id:
            raise ValidationError("repo_id is required")
        if self.split not in {"B_real", "W_real", "G_mini", "dev", "eval", "canary", "holdout"}:
            raise ValidationError(f"unsupported split: {self.split}")
        if self.weight <= 0:
            raise ValidationError("weight must be positive")


@dataclass(frozen=True)
class ReleaseManifest:
    schema_version: str
    release_id: str
    repo_id: str
    source_phase0_release: str
    status: str
    tasks: list[TaskManifest]
    splits: dict[str, list[str]]
    evidence_status: str

    def validate(self) -> None:
        if self.schema_version != "barcarolle.phase1.release_manifest.v1":
            raise ValidationError("unexpected release schema_version")
        if not self.tasks:
            raise ValidationError("release must contain at least one task")
        task_ids = {task.task_id for task in self.tasks}
        for task in self.tasks:
            task.validate()
        for split, ids in self.splits.items():
            missing = [task_id for task_id in ids if task_id not in task_ids]
            if missing:
                raise ValidationError(f"split {split} references missing tasks: {missing}")


@dataclass(frozen=True)
class TargetProfile:
    repo_id: str
    strata: dict[str, dict[str, float]]
    insufficient_evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CertificationReport:
    task_id: str
    gates: dict[str, str]
    status: str


@dataclass(frozen=True)
class AgentRunManifest:
    run_id: str
    acut_id: str
    model: str
    task_ids: list[str]
    measured_cost_usd: float | None


@dataclass(frozen=True)
class ScorecardCell:
    task_id: str
    split: str
    terminal_status: str
    scoreable: bool
    module_or_package: list[str]
    weight: float = 1.0
    adapter_id: str = ""
    acut_id: str = ""
    harness_name: str = ""

    @property
    def compatible(self) -> bool:
        return self.scoreable and self.terminal_status in {"verified_pass", "verified_fail"}

    @property
    def score(self) -> float:
        if self.terminal_status == "verified_pass":
            return 1.0
        if self.terminal_status == "verified_fail":
            return 0.0
        raise ValidationError(f"cell is not compatible: {self.task_id}")


@dataclass(frozen=True)
class Scorecard:
    run_id: str
    cells: list[ScorecardCell]
    source_score_table: str = ""


@dataclass(frozen=True)
class WeightedScoreSummary:
    schema_version: str
    run_id: str
    weighted_score: float | None
    evidence_status: str
    stratum_scores: dict[str, dict[str, Any]]
    insufficient_evidence: list[str]
    source_score_table: str = ""
    acut_ids: list[str] = field(default_factory=list)
    cell_count: int = 0
    compatible_cell_count: int = 0
    incompatible_cell_count: int = 0


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def intish(value: Any, default: int = 0) -> int:
    try:
        if value in {None, ""}:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value == "":
        return ""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() == "null":
        return None
    return value.strip("'\"")


def load_mvp_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    data: dict[str, Any] = {
        "source_artifacts": {},
        "repos": [],
        "comparators": [],
        "allowed_scope": [],
        "disallowed_claims": [],
    }
    section: str | None = None
    current_item: dict[str, Any] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()
        if indent == 0:
            current_item = None
            if text.endswith(":"):
                section = text[:-1]
                continue
            key, value = text.split(":", 1)
            data[key] = parse_scalar(value)
            section = None
            continue
        if section is None:
            raise ValidationError(f"unsupported config shape near: {raw}")
        if section == "source_artifacts":
            if indent != 2:
                raise ValidationError(f"unsupported config shape near: {raw}")
            key, value = text.split(":", 1)
            data[section][key] = parse_scalar(value)
        elif section in {"repos", "comparators"}:
            if indent not in {2, 4}:
                raise ValidationError(f"unsupported config shape near: {raw}")
            if text.startswith("- "):
                current_item = {}
                data[section].append(current_item)
                rest = text[2:]
                if rest:
                    key, value = rest.split(":", 1)
                    current_item[key] = parse_scalar(value)
            elif current_item is not None:
                key, value = text.split(":", 1)
                current_item[key] = parse_scalar(value)
            else:
                raise ValidationError(f"list item expected near: {raw}")
        elif section in {"allowed_scope", "disallowed_claims"}:
            if indent != 2:
                raise ValidationError(f"unsupported config shape near: {raw}")
            if not text.startswith("- "):
                raise ValidationError(f"list item expected near: {raw}")
            data[section].append(parse_scalar(text[2:]))
        else:
            raise ValidationError(f"unsupported config section: {section}")
    data["_path"] = str(path)
    validate_config(data)
    return data


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != "barcarolle.phase1_mvp_config.v1":
        raise ValidationError("unexpected config schema_version")
    if config.get("claim_scope") != CLAIM_SCOPE:
        raise ValidationError("config claim_scope must be phase1_mvp_compiler_infrastructure")
    if config.get("predictive_validity_established") is not False:
        raise ValidationError("config must keep predictive_validity_established=false")
    missing_claims = [claim for claim in DISALLOWED_CLAIMS if claim not in config.get("disallowed_claims", [])]
    if missing_claims:
        raise ValidationError(f"missing disallowed claims: {missing_claims}")
    missing_scope = [scope for scope in ALLOWED_SCOPE if scope not in config.get("allowed_scope", [])]
    if missing_scope:
        raise ValidationError(f"missing allowed scope entries: {missing_scope}")
    for repo in config.get("repos", []) + config.get("comparators", []):
        if repo.get("role") not in REPO_ROLES:
            raise ValidationError(f"invalid repo role: {repo.get('role')}")


def artifact_path(config: dict[str, Any], key: str) -> Path:
    try:
        raw = config["source_artifacts"][key]
    except KeyError as exc:
        raise ValidationError(f"config missing source artifact: {key}") from exc
    path = Path(str(raw))
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def require_artifacts(config: dict[str, Any], keys: list[str] | None = None) -> dict[str, Path]:
    wanted = keys or sorted(config.get("source_artifacts", {}))
    paths = {key: artifact_path(config, key) for key in wanted}
    missing = [f"{key}: {rel(path)}" for key, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError("missing Phase 1 source artifacts: " + "; ".join(missing))
    return paths


def score_table_sources(config: dict[str, Any]) -> list[tuple[str, str, str]]:
    sources = list(BASE_SCORE_TABLE_SOURCES)
    configured = config.get("source_artifacts", {})
    sources.extend(source for source in OPTIONAL_SCORE_TABLE_SOURCES if source[0] in configured)
    return sources


def output_root_from_args(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "output_root", ROOT)).resolve()


def results_dir(output_root: Path) -> Path:
    return output_root / "results"


def reports_dir(output_root: Path) -> Path:
    return output_root / "reports"


def normalize_modules(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, str):
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            return [part.strip(" '\"") for part in stripped.strip("[]").split(",") if part.strip()]
        return [stripped] if stripped else ["unknown"]
    return ["unknown"]


def repo_from_task_id(task_id: str) -> str:
    if "__" in task_id:
        return task_id.split("__", 1)[0]
    return "unknown"


def task_from_phase0(row: dict[str, Any], repo_id: str) -> TaskManifest:
    counts = row.get("counts_toward_benchmark_grade")
    certified = row.get("certification_status") == "certified" and counts is True
    evidence_status = "certified" if certified else "insufficient_evidence"
    return TaskManifest(
        task_id=str(row["task_id"]),
        repo_id=repo_id if row.get("split") != "G_mini" else "click",
        split=str(row["split"]),
        certification_status=str(row["certification_status"]),
        module_or_package=normalize_modules(row.get("module_or_package")),
        task_type_proxy=str(row.get("task_type_proxy") or "unknown"),
        weight=float(row.get("weight") or 1.0),
        evidence_status=evidence_status,
    )


def import_phase0_release(phase0_root: Path = PHASE0_ROOT) -> ReleaseManifest:
    source = read_json(phase0_root / "releases" / "toolz_phase0_mini_release.json")
    tasks = [task_from_phase0(row, source["repo_id"]) for row in source["tasks"]]
    release = ReleaseManifest(
        schema_version="barcarolle.phase1.release_manifest.v1",
        release_id=f"{source['release_id']}-phase1-draft",
        repo_id=source["repo_id"],
        source_phase0_release=str((phase0_root / "releases" / "toolz_phase0_mini_release.json").relative_to(REPO_ROOT)),
        status="draft_imported_from_phase0",
        tasks=tasks,
        splits={split: list(ids) for split, ids in source["splits"].items()},
        evidence_status="insufficient_evidence",
    )
    release.validate()
    return release


def load_target_profile(phase0_root: Path = PHASE0_ROOT) -> TargetProfile:
    profile = read_json(phase0_root / "target_profiles" / "toolz_target_profile.json")
    return TargetProfile(
        repo_id=profile["repo_id"],
        strata={
            "module_or_package": {key: float(value) for key, value in profile["overall_distributions"]["module_or_package"].items()},
            "task_type_proxy": {key: float(value) for key, value in profile["overall_distributions"]["task_type_proxy"].items()},
        },
        insufficient_evidence=list(profile.get("missing_data_labels", {}).keys()),
    )


def resolve_score_table_path(phase0_root: Path, score_table_path: Path | str | None = None) -> Path:
    if score_table_path is None:
        return phase0_root / "results" / "headroom_score_table.csv"
    path = Path(score_table_path)
    if path.is_absolute():
        return path
    if path.exists():
        return path
    return phase0_root / "results" / path


def scorecard_from_phase0(
    release: ReleaseManifest,
    phase0_root: Path = PHASE0_ROOT,
    score_table_path: Path | str | None = None,
    run_id: str = "phase0_headroom_matrix",
) -> Scorecard:
    resolved_score_table = resolve_score_table_path(phase0_root, score_table_path)
    rows = read_csv(resolved_score_table)
    task_by_id = {task.task_id: task for task in release.tasks}
    cells = []
    for row in rows:
        task = task_by_id.get(row["task_id"])
        if task is None:
            continue
        cells.append(
            ScorecardCell(
                task_id=row["task_id"],
                split=row["split"],
                terminal_status=row["terminal_status"],
                scoreable=row["scoreable_cell"] == "True",
                module_or_package=task.module_or_package,
                weight=task.weight,
                adapter_id=row.get("adapter_id", ""),
                acut_id=row.get("acut_id", ""),
                harness_name=row.get("harness_name", ""),
            )
        )
    return Scorecard(run_id=run_id, cells=cells, source_score_table=str(resolved_score_table))


def compute_weighted_score(scorecard: Scorecard, target_profile: TargetProfile) -> WeightedScoreSummary:
    module_weights = target_profile.strata.get("module_or_package", {})
    cells_by_module: dict[str, list[ScorecardCell]] = {}
    for cell in scorecard.cells:
        module = cell.module_or_package[0] if cell.module_or_package else "unknown"
        cells_by_module.setdefault(module, []).append(cell)

    stratum_scores: dict[str, dict[str, Any]] = {}
    insufficient: list[str] = []
    weighted_total = 0.0
    weight_total = 0.0
    for module, weight in sorted(module_weights.items()):
        cells = cells_by_module.get(module, [])
        compatible = [cell for cell in cells if cell.compatible]
        incompatible = [cell for cell in cells if not cell.compatible]
        if not compatible or incompatible:
            insufficient.append(module)
            stratum_scores[module] = {
                "target_weight": weight,
                "evidence_status": "insufficient_evidence",
                "compatible_cell_count": len(compatible),
                "incompatible_cell_count": len(incompatible),
                "score": None,
            }
            continue
        score = sum(cell.score for cell in compatible) / len(compatible)
        weighted_total += score * weight
        weight_total += weight
        stratum_scores[module] = {
            "target_weight": weight,
            "evidence_status": "compatible",
            "compatible_cell_count": len(compatible),
            "incompatible_cell_count": 0,
            "score": round(score, 6),
        }

    weighted_score = None if insufficient or weight_total == 0 else round(weighted_total / weight_total, 6)
    return WeightedScoreSummary(
        schema_version="barcarolle.phase1.weighted_score_summary.v1",
        run_id=scorecard.run_id,
        weighted_score=weighted_score,
        evidence_status="compatible" if weighted_score is not None else "insufficient_evidence",
        stratum_scores=stratum_scores,
        insufficient_evidence=insufficient,
        source_score_table=scorecard.source_score_table,
        acut_ids=sorted({cell.acut_id for cell in scorecard.cells if cell.acut_id}),
        cell_count=len(scorecard.cells),
        compatible_cell_count=sum(1 for cell in scorecard.cells if cell.compatible),
        incompatible_cell_count=sum(1 for cell in scorecard.cells if not cell.compatible),
    )


def config_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return load_mvp_config(Path(getattr(args, "config", DEFAULT_CONFIG)))


def build_inventory_payload(config: dict[str, Any]) -> dict[str, Any]:
    require_artifacts(config)
    readiness = read_json(artifact_path(config, "readiness_gate"))
    toolz_release = read_json(artifact_path(config, "toolz_release"))
    humanize_release = read_json(artifact_path(config, "humanize_release"))
    cost = read_json(artifact_path(config, "workspace_cost_reconciliation"))
    usage_call_count = sum(1 for line in artifact_path(config, "workspace_usage_ledger").read_text(encoding="utf-8").splitlines() if line.strip())

    task_counts = Counter()
    certified_counts = Counter()
    for row in toolz_release.get("tasks", []):
        repo_id = repo_from_task_id(str(row.get("task_id", "")))
        if repo_id == "click":
            continue
        task_counts[repo_id] += 1
        if row.get("certification_status") == "certified" and boolish(row.get("counts_toward_benchmark_grade")):
            certified_counts[repo_id] += 1
    for row in humanize_release.get("tasks", []):
        task_counts["humanize"] += 1
    certified_counts["humanize"] = int(humanize_release.get("certified_task_count", 0))

    score_counts: dict[str, Any] = {}
    for key, prefix, role in score_table_sources(config):
        rows = read_csv(artifact_path(config, key))
        score_counts[prefix] = {
            "source_artifact_key": key,
            "role": role,
            "row_count": len(rows),
            "scoreable_cell_count": sum(1 for row in rows if boolish(row.get("scoreable_cell"))),
            "terminal_status_counts": dict(Counter(row.get("terminal_status", "") for row in rows)),
            "repo_counts": dict(Counter(repo_from_task_id(row.get("task_id", "")) for row in rows)),
        }

    return {
        "schema_version": "barcarolle.phase1.input_inventory.v1",
        "generated_at": now_utc(),
        "claim_scope": CLAIM_SCOPE,
        "predictive_validity_established": False,
        "source_artifacts": dict(config["source_artifacts"]),
        "repo_count": len(config.get("repos", [])),
        "target_repos": config.get("repos", []),
        "generic_comparators": config.get("comparators", []),
        "task_counts_by_repo": dict(sorted(task_counts.items())),
        "certified_task_counts_by_repo": dict(sorted(certified_counts.items())),
        "score_table_counts": score_counts,
        "cost_summary_present": bool(cost.get("totals")),
        "usage_ledger_call_count": usage_call_count,
        "known_limitations": [
            PREDICTIVE_LIMITATION,
            "provider_billed_cost_unavailable",
            "future_holdout_unavailable_in_current_evidence",
            "humanize_source_context_uses_commit_message_fallback",
            "click_is_generic_comparator_only",
        ],
        "readiness_gate_status": readiness.get("status"),
        "readiness_gate_predictive_validity_established": readiness.get("predictive_validity_established"),
    }


def inventory_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Input Inventory",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Claim scope: `{payload['claim_scope']}`.",
        f"- Predictive validity established: `{str(payload['predictive_validity_established']).lower()}`.",
        f"- Target repos: `{', '.join(repo['repo_id'] for repo in payload['target_repos'])}`.",
        f"- Generic comparators: `{', '.join(repo['repo_id'] for repo in payload['generic_comparators'])}`.",
        f"- Usage ledger calls: `{payload['usage_ledger_call_count']}`.",
        "",
        "## Task Counts",
        "",
        "| Repo | Tasks | Certified tasks |",
        "| --- | ---: | ---: |",
    ]
    for repo_id, count in payload["task_counts_by_repo"].items():
        lines.append(f"| `{repo_id}` | {count} | {payload['certified_task_counts_by_repo'].get(repo_id, 0)} |")
    lines.extend(["", "## Score Tables", "", "| Result prefix | Rows | Scoreable cells |", "| --- | ---: | ---: |"])
    for prefix, summary in payload["score_table_counts"].items():
        lines.append(f"| `{prefix}` | {summary['row_count']} | {summary['scoreable_cell_count']} |")
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- `{item}`" for item in payload["known_limitations"])
    return "\n".join(lines)


def run_inventory(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_inventory_payload(config_from_args(args))
    root = output_root_from_args(args)
    write_json(results_dir(root) / "phase1_input_inventory.json", payload)
    write_text(reports_dir(root) / "phase1_input_inventory.md", inventory_report(payload))
    return payload


def task_payload(
    row: dict[str, Any],
    *,
    repo_id: str,
    role: str,
    source_provenance: str,
    source_release: str,
    certification_status: str = "certified",
    task_type_proxy: str | None = None,
) -> dict[str, Any]:
    return {
        "task_id": row["task_id"],
        "repo_id": repo_id,
        "split": row["split"],
        "role": role,
        "source_provenance": source_provenance,
        "source_release": source_release,
        "certification_status": certification_status,
        "module_or_package": normalize_modules(row.get("module_or_package")),
        "task_type_proxy": task_type_proxy or str(row.get("task_type_proxy") or "unknown"),
        "weight": float(row.get("weight") or 1.0),
        "evidence_status": "certified" if certification_status == "certified" else "comparator_metadata_only",
    }


def build_release_payload(config: dict[str, Any]) -> dict[str, Any]:
    require_artifacts(
        config,
        [
            "readiness_gate",
            "toolz_release",
            "humanize_release",
            "humanize_certified_tasks",
        ],
    )
    readiness = read_json(artifact_path(config, "readiness_gate"))
    toolz_release = read_json(artifact_path(config, "toolz_release"))
    humanize_release = read_json(artifact_path(config, "humanize_release"))
    humanize_certified = {row["task_id"]: row for row in read_jsonl(artifact_path(config, "humanize_certified_tasks"))}
    source_toolz = rel(artifact_path(config, "toolz_release"))
    source_humanize = rel(artifact_path(config, "humanize_release"))

    target_tasks = []
    comparator_tasks = []
    for row in toolz_release.get("tasks", []):
        task_id = str(row.get("task_id", ""))
        repo_id = repo_from_task_id(task_id)
        if repo_id == "click":
            comparator_tasks.append(
                task_payload(
                    row,
                    repo_id="click",
                    role="generic_comparator",
                    source_provenance=CLICK_PROVENANCE,
                    source_release=source_toolz,
                    certification_status=str(row.get("certification_status", "archived_click_release_metadata")),
                    task_type_proxy=str(row.get("task_type_proxy") or "behavior_or_maintenance"),
                )
            )
            continue
        if row.get("certification_status") == "certified" and boolish(row.get("counts_toward_benchmark_grade")):
            target_tasks.append(
                task_payload(
                    row,
                    repo_id="toolz",
                    role="primary_target_repo",
                    source_provenance=TOOLZ_PROVENANCE,
                    source_release=source_toolz,
                )
            )

    for row in humanize_release.get("tasks", []):
        cert = humanize_certified.get(row["task_id"], {})
        merged = dict(row)
        merged.setdefault("task_type_proxy", cert.get("task_type_proxy", "behavior_or_feature_or_bugfix"))
        target_tasks.append(
            task_payload(
                merged,
                repo_id="humanize",
                role="second_target_repo",
                source_provenance=HUMANIZE_PROVENANCE,
                source_release=source_humanize,
            )
        )

    splits: dict[str, Any] = {
        "target_repos": {
            "toolz": {split: [task["task_id"] for task in target_tasks if task["repo_id"] == "toolz" and task["split"] == split] for split in ["B_real", "W_real"]},
            "humanize": {split: [task["task_id"] for task in target_tasks if task["repo_id"] == "humanize" and task["split"] == split] for split in ["B_real", "W_real"]},
        },
        "generic_comparators": {
            "click": {"G_mini": [task["task_id"] for task in comparator_tasks]},
        },
    }
    repos = [
        {
            "repo_id": "toolz",
            "role": "primary_target_repo",
            "source_provenance": TOOLZ_PROVENANCE,
            "source_release": source_toolz,
            "source_release_status": toolz_release.get("release_status"),
            "legacy_benchmark_grade": boolish(toolz_release.get("benchmark_grade")),
            "certified_task_count": len([task for task in target_tasks if task["repo_id"] == "toolz"]),
        },
        {
            "repo_id": "humanize",
            "role": "second_target_repo",
            "source_provenance": HUMANIZE_PROVENANCE,
            "source_release": source_humanize,
            "source_release_status": humanize_release.get("release_status"),
            "legacy_benchmark_grade": boolish(humanize_release.get("benchmark_grade")),
            "legacy_pilot_grade": boolish(humanize_release.get("pilot_grade")),
            "certified_task_count": len([task for task in target_tasks if task["repo_id"] == "humanize"]),
        },
    ]
    payload = {
        "schema_version": "barcarolle.phase1.release.v1",
        "release_id": "phase1_mvp_multi_repo_release",
        "generated_at": now_utc(),
        "status": "pilot_grade",
        "claim_scope": CLAIM_SCOPE,
        "claims": [CLAIM_SCOPE, PREDICTIVE_LIMITATION],
        "predictive_validity_established": False,
        "readiness_gate_status": readiness.get("status"),
        "repos": repos,
        "generic_comparators": [
            {
                "repo_id": "click",
                "role": "generic_comparator",
                "source_provenance": CLICK_PROVENANCE,
                "source_release": source_toolz,
                "task_count": len(comparator_tasks),
                "tasks": comparator_tasks,
            }
        ],
        "tasks": target_tasks,
        "splits": splits,
        "source_provenance": {
            "toolz": TOOLZ_PROVENANCE,
            "humanize": HUMANIZE_PROVENANCE,
            "click": CLICK_PROVENANCE,
        },
        "certification_summary": {
            "target_task_count": len(target_tasks),
            "target_task_counts_by_repo": dict(Counter(task["repo_id"] for task in target_tasks)),
            "generic_comparator_task_count": len(comparator_tasks),
            "release_status_notes": [
                "humanize legacy benchmark_grade=true is retained only as source metadata",
                "phase1 release status remains pilot_grade and is not validation_grade",
            ],
        },
        "known_limitations": [
            PREDICTIVE_LIMITATION,
            "humanize_source_context_uses_commit_message_fallback",
            "future_holdout_unavailable_in_current_evidence",
            "click_is_generic_comparator_only",
        ],
        "allowed_scope": config["allowed_scope"],
        "disallowed_claims": config["disallowed_claims"],
    }
    validate_phase1_release_payload(payload)
    return payload


def validate_phase1_release_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "barcarolle.phase1.release.v1":
        raise ValidationError("unexpected Phase 1 release schema_version")
    if payload.get("predictive_validity_established") is not False:
        raise ValidationError("Phase 1 MVP release must keep predictive_validity_established=false")
    if payload.get("status") not in RELEASE_STATUSES:
        raise ValidationError(f"invalid release status: {payload.get('status')}")
    for repo in payload.get("repos", []) + payload.get("generic_comparators", []):
        if repo.get("role") not in REPO_ROLES:
            raise ValidationError(f"invalid repo role: {repo.get('role')}")
    claim_set = set(payload.get("claims", []))
    disallowed_claims = set(payload.get("disallowed_claims", []))
    if claim_set & disallowed_claims:
        raise ValidationError(f"disallowed claims used as active claims: {sorted(claim_set & disallowed_claims)}")


def run_build_release(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_release_payload(config_from_args(args))
    write_json(results_dir(output_root_from_args(args)) / "phase1_mvp_release.json", payload)
    return payload


def gate_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts = {gate: Counter() for gate in GATE_ORDER}
    for row in rows:
        gates = row.get("gates") if isinstance(row.get("gates"), dict) else row
        for gate in GATE_ORDER:
            value = gates.get(gate) if isinstance(gates, dict) else None
            if value:
                counts[gate][str(value)] += 1
    return {gate: dict(counter) for gate, counter in counts.items()}


def rollup_repo_certification(repo_id: str, funnel_path: Path, certified_path: Path, review_path: Path, statement_path: Path) -> dict[str, Any]:
    funnel_rows = read_csv(funnel_path)
    certified_rows = read_jsonl(certified_path)
    review_count = len(read_jsonl(review_path)) if review_path.exists() else 0
    statement_count = len(read_jsonl(statement_path)) if statement_path.exists() else 0
    status_counts = Counter(row.get("status", "unknown") for row in funnel_rows)
    first_failures = Counter(row.get("first_failing_gate") or "none" for row in funnel_rows)
    return {
        "repo_id": repo_id,
        "source_funnel": rel(funnel_path),
        "source_certified_tasks": rel(certified_path),
        "funnel_task_count": len(funnel_rows),
        "certified_jsonl_count": len(certified_rows),
        "status_counts": dict(status_counts),
        "certified_count": status_counts.get("certified", 0),
        "near_certified_count": status_counts.get("near_certified", 0),
        "rejected_count": sum(count for status, count in status_counts.items() if status not in {"certified", "near_certified"}),
        "first_failing_gate_counts": dict(first_failures),
        "gate_counts": gate_counts(certified_rows if certified_rows else funnel_rows),
        "review_record_count": review_count,
        "task_statement_count": statement_count,
    }


def build_certification_rollup_payload(config: dict[str, Any]) -> dict[str, Any]:
    require_artifacts(
        config,
        [
            "toolz_certification_funnel",
            "humanize_certification_funnel",
            "toolz_certified_tasks",
            "humanize_certified_tasks",
            "toolz_review_records",
            "humanize_review_records",
            "toolz_task_statements",
            "humanize_task_statements",
        ],
    )
    repos = [
        rollup_repo_certification(
            "toolz",
            artifact_path(config, "toolz_certification_funnel"),
            artifact_path(config, "toolz_certified_tasks"),
            artifact_path(config, "toolz_review_records"),
            artifact_path(config, "toolz_task_statements"),
        ),
        rollup_repo_certification(
            "humanize",
            artifact_path(config, "humanize_certification_funnel"),
            artifact_path(config, "humanize_certified_tasks"),
            artifact_path(config, "humanize_review_records"),
            artifact_path(config, "humanize_task_statements"),
        ),
    ]
    return {
        "schema_version": "barcarolle.phase1.certification_rollup.v1",
        "generated_at": now_utc(),
        "claim_scope": CLAIM_SCOPE,
        "predictive_validity_established": False,
        "repos": repos,
        "gate_order": GATE_ORDER,
        "source_weaknesses": [
            "humanize source context is source_provenance_commit_message_fallback",
            "provider-billed cost remains unavailable",
            "no Phase 1 future held-out validation has been run",
        ],
        "disallowed_claims": config["disallowed_claims"],
    }


def certification_rollup_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Certification Rollup",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "| Repo | Funnel tasks | Certified | Near-certified | Rejected |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for repo in payload["repos"]:
        lines.append(
            f"| `{repo['repo_id']}` | {repo['funnel_task_count']} | {repo['certified_count']} | "
            f"{repo['near_certified_count']} | {repo['rejected_count']} |"
        )
    lines.extend(["", "## Source Weaknesses", ""])
    lines.extend(f"- {item}" for item in payload["source_weaknesses"])
    return "\n".join(lines)


def run_certification_rollup(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_certification_rollup_payload(config_from_args(args))
    root = output_root_from_args(args)
    write_json(results_dir(root) / "phase1_certification_rollup.json", payload)
    write_text(reports_dir(root) / "phase1_certification_rollup.md", certification_rollup_report(payload))
    return payload


def build_split_plan_payload(config: dict[str, Any]) -> dict[str, Any]:
    release = build_release_payload(config)
    return {
        "schema_version": "barcarolle.phase1.split_plan.v1",
        "generated_at": now_utc(),
        "claim_scope": CLAIM_SCOPE,
        "predictive_validity_established": False,
        "release_id": release["release_id"],
        "historical_splits": release["splits"],
        "phase1_placeholders": {
            "dev": {"status": "unassigned_mvp_placeholder", "tasks": []},
            "eval": {"status": "unassigned_mvp_placeholder", "tasks": []},
            "canary": {"status": "unassigned_mvp_placeholder", "tasks": []},
            "future_holdout": {"status": "unavailable_in_current_evidence", "tasks": []},
        },
        "future_holdout_status": "unavailable_in_current_evidence",
        "constraints": [
            "target repo tasks must not appear in more than one target evaluation split unless labeled historical_diagnostic_reuse",
            "generic comparators cannot be canary or target-repo holdout tasks",
            "humanize commit-message fallback provenance is MVP infrastructure evidence, not validation-grade evidence",
        ],
        "disallowed_claims": config["disallowed_claims"],
    }


def split_plan_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Split Plan",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Future holdout status: `{payload['future_holdout_status']}`.",
        "- Phase 1 validation remains future work.",
        "",
        "## Historical Splits",
        "",
    ]
    for repo_id, splits in payload["historical_splits"]["target_repos"].items():
        lines.append(f"- `{repo_id}`: " + ", ".join(f"`{split}`={len(ids)}" for split, ids in splits.items()))
    for repo_id, splits in payload["historical_splits"]["generic_comparators"].items():
        lines.append(f"- `{repo_id}` comparator: " + ", ".join(f"`{split}`={len(ids)}" for split, ids in splits.items()))
    return "\n".join(lines)


def run_split_plan(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_split_plan_payload(config_from_args(args))
    root = output_root_from_args(args)
    write_json(results_dir(root) / "phase1_split_plan.json", payload)
    write_text(reports_dir(root) / "phase1_split_plan.md", split_plan_report(payload))
    return payload


def normalize_score_row(row: dict[str, str], source_key: str, prefix: str, role: str, source_path: Path) -> dict[str, Any]:
    task_id = row["task_id"]
    repo_id = repo_from_task_id(task_id)
    terminal = row["terminal_status"]
    scoreable = boolish(row.get("scoreable_cell"))
    score = None
    if scoreable and terminal == "verified_pass":
        score = 1.0
    elif scoreable and terminal == "verified_fail":
        score = 0.0
    return {
        "source_artifact_key": source_key,
        "source_score_table": rel(source_path),
        "source_result_prefix": prefix,
        "source_role": role,
        "comparison_label": COMPARISON_LABEL,
        "repo_id": repo_id,
        "task_id": task_id,
        "split": row["split"],
        "attempt": intish(row.get("attempt"), 1),
        "adapter_id": row["adapter_id"],
        "acut_id": row["acut_id"],
        "harness_name": row["harness_name"],
        "model_or_agent_name": row["model_or_agent_name"],
        "submission_status": row["submission_status"],
        "terminal_status": terminal,
        "scoreable_cell": scoreable,
        "policy_violation": terminal == "policy_violation",
        "agent_failure": boolish(row.get("agent_failure")),
        "harness_error": boolish(row.get("harness_error")),
        "score": score,
    }


def build_scorecard_payload(config: dict[str, Any]) -> dict[str, Any]:
    sources = score_table_sources(config)
    require_artifacts(config, [key for key, _, _ in sources])
    cells = []
    summaries: dict[str, Any] = {}
    for source_key, prefix, role in sources:
        source_path = artifact_path(config, source_key)
        rows = read_csv(source_path)
        if not rows:
            raise ValidationError(f"empty score table: {rel(source_path)}")
        missing = REQUIRED_SCORE_COLUMNS - set(rows[0])
        if missing:
            raise ValidationError(f"score table {rel(source_path)} missing columns: {sorted(missing)}")
        source_cells = [normalize_score_row(row, source_key, prefix, role, source_path) for row in rows]
        cells.extend(source_cells)
        summaries[prefix] = {
            "source_artifact_key": source_key,
            "source_score_table": rel(source_path),
            "role": role,
            "row_count": len(source_cells),
            "scoreable_cell_count": sum(1 for cell in source_cells if cell["scoreable_cell"]),
            "policy_violation_count": sum(1 for cell in source_cells if cell["policy_violation"]),
            "repo_counts": dict(Counter(cell["repo_id"] for cell in source_cells)),
            "harness_counts": dict(Counter(cell["harness_name"] for cell in source_cells)),
        }
    return {
        "schema_version": "barcarolle.phase1.workspace_scorecard.v1",
        "generated_at": now_utc(),
        "claim_scope": CLAIM_SCOPE,
        "comparison_label": COMPARISON_LABEL,
        "predictive_validity_established": False,
        "cells": cells,
        "summary": {
            "cell_count": len(cells),
            "scoreable_cell_count": sum(1 for cell in cells if cell["scoreable_cell"]),
            "humanize_cell_count": sum(1 for cell in cells if cell["repo_id"] == "humanize"),
            "policy_violation_count": sum(1 for cell in cells if cell["policy_violation"]),
            "by_result_prefix": summaries,
            "by_repo": dict(Counter(cell["repo_id"] for cell in cells)),
            "by_harness": dict(Counter(cell["harness_name"] for cell in cells)),
        },
        "independence_notes": [
            "repaired Toolz/Click followup and stability repeat are preserved as separate result prefixes",
            "stability repeat is diagnostic repeat evidence, not an independent future validation sample",
            "Click rows are generic comparator rows and not target-repo evaluation tasks",
            "Boltons paid smoke rows are operational workspace-ACUT scoreability evidence, not predictive-validation evidence",
        ],
        "disallowed_claims": config["disallowed_claims"],
    }


def scorecard_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Workspace Scorecard",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Comparison label: `{payload['comparison_label']}`.",
        f"- Total cells: `{payload['summary']['cell_count']}`.",
        f"- Scoreable cells: `{payload['summary']['scoreable_cell_count']}`.",
        f"- Humanize cells: `{payload['summary']['humanize_cell_count']}`.",
        "",
        "| Result prefix | Rows | Scoreable | Policy violations |",
        "| --- | ---: | ---: | ---: |",
    ]
    for prefix, summary in payload["summary"]["by_result_prefix"].items():
        lines.append(f"| `{prefix}` | {summary['row_count']} | {summary['scoreable_cell_count']} | {summary['policy_violation_count']} |")
    lines.extend(["", "## Independence Notes", ""])
    lines.extend(f"- {item}" for item in payload["independence_notes"])
    return "\n".join(lines)


def run_import_scorecards(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_scorecard_payload(config_from_args(args))
    root = output_root_from_args(args)
    write_json(results_dir(root) / "phase1_workspace_scorecard.json", payload)
    write_text(reports_dir(root) / "phase1_workspace_scorecard.md", scorecard_report(payload))
    return payload


def build_cost_summary_payload(config: dict[str, Any]) -> dict[str, Any]:
    require_artifacts(config, ["workspace_cost_reconciliation", "workspace_usage_ledger"])
    source = artifact_path(config, "workspace_cost_reconciliation")
    cost = read_json(source)
    usage_count = sum(1 for line in artifact_path(config, "workspace_usage_ledger").read_text(encoding="utf-8").splitlines() if line.strip())
    per_harness: Counter[str] = Counter()
    for summary in cost.get("summaries", []):
        for harness, value in summary.get("per_harness_observed_token_cost_usd", {}).items():
            per_harness[harness] += float(value)
    totals = cost.get("totals", {})
    return {
        "schema_version": "barcarolle.phase1.cost_summary.v1",
        "generated_at": now_utc(),
        "claim_scope": CLAIM_SCOPE,
        "predictive_validity_established": False,
        "source_cost_reconciliation": rel(source),
        "source_usage_ledger": rel(artifact_path(config, "workspace_usage_ledger")),
        "call_count": totals.get("call_count"),
        "usage_ledger_call_count": usage_count,
        "usage_observed_rate": totals.get("usage_observed_rate"),
        "provider_billed_cost_status": "unavailable" if cost.get("actual_provider_billed_cost_usd") is None else "available",
        "actual_provider_billed_cost_usd": cost.get("actual_provider_billed_cost_usd"),
        "observed_token_estimated_cost_usd": totals.get("observed_token_estimated_cost_usd"),
        "observed_or_conservative_estimated_cost_usd": totals.get("observed_or_conservative_estimated_cost_usd"),
        "conservative_estimated_cost_usd": totals.get("conservative_estimated_cost_usd"),
        "per_result_prefix_cost": cost.get("summaries", []),
        "per_harness_observed_token_cost_usd": {key: round(value, 7) for key, value in sorted(per_harness.items())},
        "pricing_source": (cost.get("summaries") or [{}])[0].get("pricing_source"),
        "pricing_config": cost.get("pricing_config"),
        "cost_metric_boundary": "cost is operational accounting evidence and is not used as a predictive-validity metric",
        "disallowed_claims": config["disallowed_claims"],
    }


def cost_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Cost Summary",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Calls: `{payload['call_count']}`.",
            f"- Usage observed rate: `{payload['usage_observed_rate']}`.",
            f"- Provider-billed cost status: `{payload['provider_billed_cost_status']}`.",
            f"- Observed-token estimate USD: `{payload['observed_token_estimated_cost_usd']}`.",
            f"- Observed-or-conservative estimate USD: `{payload['observed_or_conservative_estimated_cost_usd']}`.",
            f"- Pricing source: `{payload['pricing_source']}`.",
            "",
            "Provider-billed dollars remain unavailable; this summary uses the Phase 0 local price table estimate.",
        ]
    )


def run_cost_summary(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_cost_summary_payload(config_from_args(args))
    root = output_root_from_args(args)
    write_json(results_dir(root) / "phase1_cost_summary.json", payload)
    write_text(reports_dir(root) / "phase1_cost_summary.md", cost_report(payload))
    return payload


def pass_rate(cells: list[dict[str, Any]]) -> dict[str, Any]:
    compatible = [cell for cell in cells if cell["score"] in {0.0, 1.0}]
    passes = sum(1 for cell in compatible if cell["score"] == 1.0)
    failures = sum(1 for cell in compatible if cell["score"] == 0.0)
    return {
        "compatible_cell_count": len(compatible),
        "pass_count": passes,
        "fail_count": failures,
        "policy_violation_count": sum(1 for cell in cells if cell["policy_violation"]),
        "non_scoreable_count": sum(1 for cell in cells if cell["score"] is None),
        "observed_pass_rate": round(passes / len(compatible), 6) if compatible else None,
    }


def module_map_from_release(release: dict[str, Any]) -> dict[str, list[str]]:
    mapping = {}
    for task in release.get("tasks", []):
        mapping[task["task_id"]] = task.get("module_or_package", ["unknown"])
    for comparator in release.get("generic_comparators", []):
        for task in comparator.get("tasks", []):
            mapping[task["task_id"]] = task.get("module_or_package", ["unknown"])
    return mapping


def build_weighted_score_payload(config: dict[str, Any]) -> dict[str, Any]:
    release = build_release_payload(config)
    scorecard = build_scorecard_payload(config)
    modules = module_map_from_release(release)
    target_cells = [cell for cell in scorecard["cells"] if cell["repo_id"] in {"toolz", "humanize"}]
    for cell in target_cells:
        cell["module_or_package"] = modules.get(cell["task_id"], ["unknown"])

    repo_scores = {repo_id: pass_rate([cell for cell in target_cells if cell["repo_id"] == repo_id]) for repo_id in ["toolz", "humanize"]}
    split_scores: dict[str, Any] = {}
    for repo_id in ["toolz", "humanize"]:
        split_scores[repo_id] = {
            split: pass_rate([cell for cell in target_cells if cell["repo_id"] == repo_id and cell["split"] == split])
            for split in sorted({cell["split"] for cell in target_cells if cell["repo_id"] == repo_id})
        }
    module_scores: dict[str, Any] = {}
    for repo_id in ["toolz", "humanize"]:
        per_module: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for cell in target_cells:
            if cell["repo_id"] == repo_id:
                for module in cell.get("module_or_package", ["unknown"]):
                    per_module[module].append(cell)
        module_scores[repo_id] = {module: pass_rate(cells) for module, cells in sorted(per_module.items())}

    insufficient = [
        "future_holdout_unavailable_in_current_evidence",
        "predictive_validity_not_established",
        "humanize_source_provenance_commit_message_fallback",
        "toolz_followup_and_stability_are_not_independent_future_validation_samples",
        "generic_comparator_click_not_a_target_repo_validation_sample",
    ]
    if any(cell["policy_violation"] for cell in scorecard["cells"]):
        insufficient.append("policy_violations_present_in_imported_scorecards")
    payload = {
        "schema_version": "barcarolle.phase1.weighted_score.v1",
        "generated_at": now_utc(),
        "claim_scope": CLAIM_SCOPE,
        "predictive_validity_established": False,
        "diagnostic_scores": {
            "combined_target_observed_pass_rate": pass_rate(target_cells),
            "score_type": "diagnostic_observed_pass_rate",
            "predictive_score": None,
        },
        "stratum_scores": {
            "by_split": split_scores,
            "by_module": module_scores,
        },
        "repo_scores": repo_scores,
        "predictive_metrics": {
            "mae": "not_applicable_underpowered",
            "rmse": "not_applicable_underpowered",
            "brier": "not_applicable_underpowered",
            "negative_log_likelihood": "not_applicable_underpowered",
            "residual_improvement": "not_applicable_underpowered",
        },
        "insufficient_evidence": insufficient,
        "source_scorecard_cell_count": scorecard["summary"]["cell_count"],
        "disallowed_claims": config["disallowed_claims"],
    }
    return payload


def weighted_score_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Weighted Score",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "- Predictive validity established: `false`.",
        "- Predictive score: `null`.",
        "",
        "| Repo | Compatible cells | Passes | Failures | Observed pass rate |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for repo_id, summary in payload["repo_scores"].items():
        lines.append(
            f"| `{repo_id}` | {summary['compatible_cell_count']} | {summary['pass_count']} | "
            f"{summary['fail_count']} | {summary['observed_pass_rate']} |"
        )
    lines.extend(["", "## Insufficient Evidence", ""])
    lines.extend(f"- `{item}`" for item in payload["insufficient_evidence"])
    return "\n".join(lines)


def run_weighted_score(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_weighted_score_payload(config_from_args(args))
    root = output_root_from_args(args)
    write_json(results_dir(root) / "phase1_weighted_score.json", payload)
    write_text(reports_dir(root) / "phase1_weighted_score.md", weighted_score_report(payload))
    return payload


def wilson_interval(successes: int, n: int, z: float = 1.96) -> dict[str, float | None]:
    if n <= 0:
        return {"lower": None, "upper": None}
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) / n) + (z**2 / (4 * n**2))) / denom
    return {"lower": round(max(0.0, centre - half), 6), "upper": round(min(1.0, centre + half), 6)}


def build_uncertainty_payload(config: dict[str, Any]) -> dict[str, Any]:
    weighted = build_weighted_score_payload(config)
    observed = {}
    for repo_id, summary in weighted["repo_scores"].items():
        observed[repo_id] = {
            "method": "wilson_score_interval_95pct",
            "pass_count": summary["pass_count"],
            "compatible_cell_count": summary["compatible_cell_count"],
            "observed_pass_rate": summary["observed_pass_rate"],
            "interval": wilson_interval(summary["pass_count"], summary["compatible_cell_count"]),
        }
    return {
        "schema_version": "barcarolle.phase1.uncertainty_summary.v1",
        "generated_at": now_utc(),
        "claim_scope": CLAIM_SCOPE,
        "predictive_validity_established": False,
        "observed_score_uncertainty": observed,
        "future_holdout_prediction_interval": None,
        "future_holdout_status": "unavailable_in_current_evidence",
        "predictive_uncertainty_status": "not_estimated_without_future_holdout",
        "required_future_data_for_predictive_metrics": [
            "future held-out target-repo tasks",
            "pre-registered prediction target",
            "enough samples for MAE/RMSE/Brier/NLL estimates",
        ],
        "disallowed_claims": config["disallowed_claims"],
    }


def uncertainty_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Uncertainty Summary",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"- Future holdout status: `{payload['future_holdout_status']}`.",
        f"- Predictive uncertainty status: `{payload['predictive_uncertainty_status']}`.",
        "",
        "| Repo | Passes | Compatible cells | Observed pass rate | 95% interval |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for repo_id, summary in payload["observed_score_uncertainty"].items():
        interval = summary["interval"]
        lines.append(
            f"| `{repo_id}` | {summary['pass_count']} | {summary['compatible_cell_count']} | "
            f"{summary['observed_pass_rate']} | `{interval['lower']}`, `{interval['upper']}` |"
        )
    return "\n".join(lines)


def run_uncertainty_summary(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_uncertainty_payload(config_from_args(args))
    root = output_root_from_args(args)
    write_json(results_dir(root) / "phase1_uncertainty_summary.json", payload)
    write_text(reports_dir(root) / "phase1_uncertainty_summary.md", uncertainty_report(payload))
    return payload


def closeout_next_runbook_recommendation(
    hardening_decision: dict[str, Any] | None,
    paid_smoke_decision: dict[str, Any] | None = None,
    future_holdout_decision: dict[str, Any] | None = None,
    retrospective_decision: dict[str, Any] | None = None,
    clean_supply_breal_extension_decision: dict[str, Any] | None = None,
    clean_outcome_unseen_supply_decision: dict[str, Any] | None = None,
    second_repo_clean_supply_decision: dict[str, Any] | None = None,
    two_repo_future_holdout_decision: dict[str, Any] | None = None,
    policy_violation_repair_decision: dict[str, Any] | None = None,
) -> str:
    if policy_violation_repair_decision:
        recommendation = str(policy_violation_repair_decision.get("recommended_next_runbook") or "").strip()
        if recommendation:
            return recommendation
    if two_repo_future_holdout_decision and two_repo_future_holdout_decision.get("paid_acut_calls_made") is True:
        recommendation = str(two_repo_future_holdout_decision.get("recommended_next_runbook") or "").strip()
        if recommendation:
            return recommendation
    if second_repo_clean_supply_decision:
        recommendation = str(second_repo_clean_supply_decision.get("recommended_next_runbook") or "").strip()
        if recommendation:
            return recommendation
    if future_holdout_decision and future_holdout_decision.get("paid_acut_calls_made") is True:
        recommendation = str(future_holdout_decision.get("recommended_next_runbook") or "").strip()
        if recommendation:
            return recommendation
    if clean_outcome_unseen_supply_decision:
        recommendation = str(clean_outcome_unseen_supply_decision.get("recommended_next_runbook") or "").strip()
        if recommendation:
            return recommendation
    if clean_supply_breal_extension_decision:
        recommendation = str(clean_supply_breal_extension_decision.get("recommended_next_runbook") or "").strip()
        if recommendation:
            return recommendation
    if retrospective_decision:
        recommendation = str(retrospective_decision.get("recommended_next_runbook") or "").strip()
        if recommendation:
            return recommendation
    if future_holdout_decision:
        recommendation = str(future_holdout_decision.get("recommended_next_runbook") or "").strip()
        if recommendation:
            return recommendation
    if paid_smoke_decision:
        recommendation = str(paid_smoke_decision.get("recommended_next_runbook") or "").strip()
        if recommendation:
            return recommendation
    if hardening_decision:
        recommendation = str(hardening_decision.get("recommended_next_runbook") or "").strip()
        if recommendation:
            return recommendation
        if hardening_decision.get("primary_decision_label") == "replace_third_repo_before_paid_acut":
            return "select_replacement_third_repo_and_locally_certify_without_paid_acut"
        return "run local third-repo remine with fixed statement template, candidate filter, and environment repair before paid ACUT scale-up"
    return "write Phase 1 validation-design runbook with source-adapter hardening as a prerequisite for validation-grade claims"


def clean_future_holdout_scale_up_decision(future_holdout_decision: dict[str, Any] | None) -> dict[str, Any]:
    if not future_holdout_decision or future_holdout_decision.get("paid_acut_calls_made") is not True:
        return {
            "status": "not_applicable_before_paid_future_holdout",
            "next_path": "run_preregistered_clean_future_holdout_paid_validation",
            "predictive_validity_established": False,
        }
    predictive_validity_established = bool(future_holdout_decision.get("predictive_validity_established"))
    selected_repos = list(future_holdout_decision.get("selected_repos") or [])
    holdout_scoreable = int(future_holdout_decision.get("h_future_scoreable_cells") or 0)
    if predictive_validity_established:
        return {
            "status": "ready_for_phase1_predictive_validation_scaleup",
            "next_path": future_holdout_decision.get("recommended_next_runbook"),
            "predictive_validity_established": True,
        }
    return {
        "status": "boltons_clean_future_holdout_pilot_complete",
        "statement": (
            "Boltons clean future-holdout pilot complete. Predictive validity remains unestablished because "
            "the acceptance threshold requires at least two target repos and at least 12 holdout scoreable cells."
        ),
        "selected_repos": selected_repos,
        "h_future_scoreable_cells": holdout_scoreable,
        "next_path": future_holdout_decision.get("recommended_next_runbook"),
        "second_repo_paid_work_allowed": False,
        "predictive_validity_established": False,
    }


def build_closeout_payload(config: dict[str, Any]) -> dict[str, Any]:
    release = build_release_payload(config)
    certification = build_certification_rollup_payload(config)
    scorecard = build_scorecard_payload(config)
    cost = build_cost_summary_payload(config)
    weighted = build_weighted_score_payload(config)
    hardening_overlay_path = ROOT / "results" / "phase1_hardened_certification_overlay.json"
    hardening_decision_path = ROOT / "results" / "phase1_certification_hardening_decision.json"
    paid_smoke_decision_path = ROOT / "results" / "phase1_boltons_paid_acut_smoke_decision.json"
    future_holdout_decision_path = ROOT / "results" / "phase1_future_holdout_decision.json"
    retrospective_decision_path = ROOT / "results" / "phase1_retrospective_validation_decision.json"
    clean_supply_breal_extension_decision_path = ROOT / "results" / "phase1_clean_supply_breal_extension_decision.json"
    clean_outcome_unseen_supply_decision_path = ROOT / "results" / "phase1_clean_outcome_unseen_supply_decision.json"
    second_repo_clean_supply_decision_path = ROOT / "results" / "phase1_second_repo_clean_supply_decision.json"
    two_repo_future_holdout_preregistration_path = ROOT / "results" / "phase1_two_repo_future_holdout_preregistration.json"
    two_repo_future_holdout_decision_path = ROOT / "results" / "phase1_two_repo_future_holdout_decision.json"
    policy_violation_repair_decision_path = ROOT / "results" / "phase1_policy_violation_repair_decision.json"
    hardening_sidecar: dict[str, Any] | None = None
    paid_smoke_decision: dict[str, Any] | None = None
    future_holdout_decision: dict[str, Any] | None = None
    retrospective_decision: dict[str, Any] | None = None
    clean_supply_breal_extension_decision: dict[str, Any] | None = None
    clean_outcome_unseen_supply_decision: dict[str, Any] | None = None
    second_repo_clean_supply_decision: dict[str, Any] | None = None
    two_repo_future_holdout_decision: dict[str, Any] | None = None
    policy_violation_repair_decision: dict[str, Any] | None = None
    if hardening_overlay_path.exists() and hardening_decision_path.exists():
        hardening_overlay = read_json(hardening_overlay_path)
        hardening_decision = read_json(hardening_decision_path)
        hardening_sidecar = {
            "status": "available_as_sidecar_evidence",
            "overlay": rel(hardening_overlay_path),
            "decision": rel(hardening_decision_path),
            "primary_decision_label": hardening_decision.get("primary_decision_label"),
            "active_third_repo": (
                hardening_decision.get("active_third_repo")
                or (hardening_decision.get("third_repo_replacement") or {}).get("active_repo_id")
            ),
            "third_repo_replacement": hardening_decision.get("third_repo_replacement", {}),
            "repo_summary": hardening_overlay.get("repo_summary", {}),
        }
    if paid_smoke_decision_path.exists():
        paid_smoke_decision = read_json(paid_smoke_decision_path)
        paid_smoke_sidecar = {
            "status": "available_as_operational_smoke_evidence",
            "decision": rel(paid_smoke_decision_path),
            "primary_decision_label": paid_smoke_decision.get("primary_decision_label"),
            "result_prefixes": paid_smoke_decision.get("result_prefixes", []),
            "combined_total_cells": paid_smoke_decision.get("combined_total_cells"),
            "combined_scoreable_cells": paid_smoke_decision.get("combined_scoreable_cells"),
            "policy_violation_count": paid_smoke_decision.get("policy_violation_count"),
            "predictive_validity_established": paid_smoke_decision.get("predictive_validity_established"),
        }
    else:
        paid_smoke_sidecar = {
            "status": "not_available",
            "note": "Boltons paid ACUT smoke decision has not been generated for this MVP build.",
        }
    if future_holdout_decision_path.exists():
        future_holdout_decision = read_json(future_holdout_decision_path)
        future_holdout_sidecar = {
            "status": "available_as_future_holdout_sidecar_evidence",
            "decision": rel(future_holdout_decision_path),
            "primary_decision_label": future_holdout_decision.get("primary_decision_label"),
            "selected_repos": future_holdout_decision.get("selected_repos", []),
            "paid_acut_calls_made": future_holdout_decision.get("paid_acut_calls_made"),
            "b_eval_scoreable_cells": future_holdout_decision.get("b_eval_scoreable_cells"),
            "h_future_scoreable_cells": future_holdout_decision.get("h_future_scoreable_cells"),
            "policy_violation_count": future_holdout_decision.get("policy_violation_count"),
            "predictive_validity_established": future_holdout_decision.get("predictive_validity_established"),
        }
    else:
        future_holdout_sidecar = {
            "status": "not_available",
            "note": "Future holdout validation decision has not been generated for this MVP build.",
        }
    if retrospective_decision_path.exists():
        retrospective_decision = read_json(retrospective_decision_path)
        retrospective_sidecar = {
            "status": "available_as_retrospective_sidecar_evidence",
            "decision": rel(retrospective_decision_path),
            "primary_decision_label": retrospective_decision.get("primary_decision_label"),
            "evidence_level": retrospective_decision.get("retrospective_evidence_level"),
            "included_repos": retrospective_decision.get("included_retrospective_repos", []),
            "included_task_count": len(retrospective_decision.get("included_retrospective_task_ids", [])),
            "clean_supply_extension_ready": retrospective_decision.get("clean_supply_extension_ready"),
            "optional_paid_clean_validation_ran": retrospective_decision.get("optional_paid_clean_validation_ran"),
            "predictive_validity_established": retrospective_decision.get("predictive_validity_established"),
        }
    else:
        retrospective_sidecar = {
            "status": "not_available",
            "note": "Retrospective validation decision has not been generated for this MVP build.",
        }
    if clean_supply_breal_extension_decision_path.exists():
        clean_supply_breal_extension_decision = read_json(clean_supply_breal_extension_decision_path)
        clean_supply_breal_extension_sidecar = {
            "status": "available_as_clean_supply_extension_sidecar_evidence",
            "decision": rel(clean_supply_breal_extension_decision_path),
            "primary_decision_label": clean_supply_breal_extension_decision.get("primary_decision_label"),
            "repo_id": clean_supply_breal_extension_decision.get("repo_id"),
            "clean_supply_ready": clean_supply_breal_extension_decision.get("clean_supply_ready"),
            "newly_promoted_task_ids": clean_supply_breal_extension_decision.get("newly_promoted_task_ids", []),
            "paid_acut_calls_made": clean_supply_breal_extension_decision.get("paid_acut_calls_made"),
            "predictive_validity_established": clean_supply_breal_extension_decision.get("predictive_validity_established"),
        }
    else:
        clean_supply_breal_extension_sidecar = {
            "status": "not_available",
            "note": "Clean supply B_real extension decision has not been generated for this MVP build.",
        }
    if clean_outcome_unseen_supply_decision_path.exists():
        clean_outcome_unseen_supply_decision = read_json(clean_outcome_unseen_supply_decision_path)
        clean_outcome_unseen_supply_sidecar = {
            "status": "available_as_clean_outcome_unseen_supply_sidecar_evidence",
            "decision": rel(clean_outcome_unseen_supply_decision_path),
            "primary_decision_label": clean_outcome_unseen_supply_decision.get("primary_decision_label"),
            "clean_supply_ready": clean_outcome_unseen_supply_decision.get("clean_supply_ready"),
            "future_holdout_preregistration_status": clean_outcome_unseen_supply_decision.get(
                "future_holdout_preregistration_status"
            ),
            "future_holdout_selected_repos": clean_outcome_unseen_supply_decision.get("future_holdout_selected_repos", []),
            "newly_promoted_task_ids": clean_outcome_unseen_supply_decision.get("newly_promoted_task_ids", []),
            "paid_acut_calls_made": clean_outcome_unseen_supply_decision.get("paid_acut_calls_made"),
            "predictive_validity_established": clean_outcome_unseen_supply_decision.get("predictive_validity_established"),
        }
    else:
        clean_outcome_unseen_supply_sidecar = {
            "status": "not_available",
            "note": "Clean outcome-unseen supply mining decision has not been generated for this MVP build.",
        }
    if second_repo_clean_supply_decision_path.exists():
        second_repo_clean_supply_decision = read_json(second_repo_clean_supply_decision_path)
        second_repo_clean_supply_sidecar = {
            "status": "available_as_second_repo_clean_supply_sidecar_evidence",
            "decision": rel(second_repo_clean_supply_decision_path),
            "primary_decision_label": second_repo_clean_supply_decision.get("primary_decision_label"),
            "selected_repo_id": second_repo_clean_supply_decision.get("selected_repo_id"),
            "selected_repos": second_repo_clean_supply_decision.get("selected_repos", []),
            "clean_supply_ready": second_repo_clean_supply_decision.get("clean_supply_ready"),
            "two_repo_preregistration_status": second_repo_clean_supply_decision.get("two_repo_preregistration_status"),
            "paid_second_repo_acut_calls_made": second_repo_clean_supply_decision.get("paid_second_repo_acut_calls_made"),
            "predictive_validity_established": second_repo_clean_supply_decision.get("predictive_validity_established"),
        }
    else:
        second_repo_clean_supply_sidecar = {
            "status": "not_available",
            "note": "Second-repo clean supply decision has not been generated for this MVP build.",
        }
    if two_repo_future_holdout_preregistration_path.exists():
        two_repo_future_holdout_preregistration = read_json(two_repo_future_holdout_preregistration_path)
        two_repo_future_holdout_sidecar = {
            "status": "available_as_two_repo_future_holdout_preregistration_sidecar_evidence",
            "preregistration": rel(two_repo_future_holdout_preregistration_path),
            "preregistration_status": two_repo_future_holdout_preregistration.get("status"),
            "selected_repos": two_repo_future_holdout_preregistration.get("selected_repos", []),
            "total_h_future_scoreable_capacity_if_second_repo_scoreable": two_repo_future_holdout_preregistration.get(
                "total_h_future_scoreable_capacity_if_second_repo_scoreable"
            ),
            "paid_second_repo_acut_calls_made": two_repo_future_holdout_preregistration.get(
                "paid_second_repo_acut_calls_made"
            ),
            "predictive_validity_established": two_repo_future_holdout_preregistration.get(
                "predictive_validity_established"
            ),
        }
    else:
        two_repo_future_holdout_sidecar = {
            "status": "not_available",
            "note": "Two-repo future-holdout preregistration has not been generated for this MVP build.",
        }
    if two_repo_future_holdout_decision_path.exists():
        two_repo_future_holdout_decision = read_json(two_repo_future_holdout_decision_path)
        two_repo_future_holdout_paid_sidecar = {
            "status": "available_as_two_repo_future_holdout_paid_sidecar_evidence",
            "decision": rel(two_repo_future_holdout_decision_path),
            "primary_decision_label": two_repo_future_holdout_decision.get("primary_decision_label"),
            "selected_repos": two_repo_future_holdout_decision.get("selected_repos", []),
            "selected_repo_id": two_repo_future_holdout_decision.get("selected_repo_id"),
            "paid_acut_calls_made": two_repo_future_holdout_decision.get("paid_acut_calls_made"),
            "paid_second_repo_acut_calls_made": two_repo_future_holdout_decision.get(
                "paid_second_repo_acut_calls_made"
            ),
            "b_eval_scoreable_cells": two_repo_future_holdout_decision.get("b_eval_scoreable_cells"),
            "h_future_scoreable_cells": two_repo_future_holdout_decision.get("h_future_scoreable_cells"),
            "policy_violation_count": two_repo_future_holdout_decision.get("policy_violation_count"),
            "predictive_validity_established": two_repo_future_holdout_decision.get(
                "predictive_validity_established"
            ),
            "recommended_next_runbook": two_repo_future_holdout_decision.get("recommended_next_runbook"),
        }
    else:
        two_repo_future_holdout_paid_sidecar = {
            "status": "not_available",
            "note": "Two-repo paid future-holdout decision has not been generated for this MVP build.",
        }
    if policy_violation_repair_decision_path.exists():
        policy_violation_repair_decision = read_json(policy_violation_repair_decision_path)
        policy_violation_repair_sidecar = {
            "status": "available_as_policy_violation_repair_decision",
            "decision": rel(policy_violation_repair_decision_path),
            "terminal_state": policy_violation_repair_decision.get("terminal_state"),
            "classification_label": policy_violation_repair_decision.get("classification_label"),
            "paid_rerun_performed": policy_violation_repair_decision.get("paid_rerun_performed"),
            "policy_violation_count": policy_violation_repair_decision.get("policy_violation_count"),
            "h_future_scoreable_cells": policy_violation_repair_decision.get("h_future_scoreable_cells"),
            "predictive_validity_established": policy_violation_repair_decision.get(
                "predictive_validity_established"
            ),
            "recommended_next_runbook": policy_violation_repair_decision.get("recommended_next_runbook"),
        }
    else:
        policy_violation_repair_sidecar = {
            "status": "not_available",
            "note": "Policy-violation repair decision has not been generated for this MVP build.",
        }
    return {
        "schema_version": "barcarolle.phase1.mvp_closeout.v1",
        "generated_at": now_utc(),
        "claim_scope": CLAIM_SCOPE,
        "predictive_validity_established": False,
        "readiness_gate_consumed": "ready_for_phase1_mvp",
        "release_id": release["release_id"],
        "release_status": release["status"],
        "repos_imported": release["repos"],
        "task_counts_by_repo": release["certification_summary"]["target_task_counts_by_repo"],
        "certification_counts_by_repo": {repo["repo_id"]: repo["status_counts"] for repo in certification["repos"]},
        "scorecard_cells_by_result_prefix": {
            prefix: summary["row_count"] for prefix, summary in scorecard["summary"]["by_result_prefix"].items()
        },
        "cost_summary": {
            "call_count": cost["call_count"],
            "usage_observed_rate": cost["usage_observed_rate"],
            "provider_billed_cost_status": cost["provider_billed_cost_status"],
            "observed_or_conservative_estimated_cost_usd": cost["observed_or_conservative_estimated_cost_usd"],
        },
        "evidence_status": "mvp_compiler_artifacts_built_insufficient_for_predictive_validation",
        "allowed_claims": [CLAIM_SCOPE, PREDICTIVE_LIMITATION, COMPARISON_LABEL, TOOLZ_PROVENANCE, HUMANIZE_PROVENANCE, CLICK_PROVENANCE],
        "disallowed_claims": config["disallowed_claims"],
        "weighted_score_evidence": {
            "diagnostic_score_type": weighted["diagnostic_scores"]["score_type"],
            "predictive_score": None,
            "insufficient_evidence": weighted["insufficient_evidence"],
        },
        "hardening_sidecar_evidence": hardening_sidecar
        or {
            "status": "not_available",
            "note": "Phase 1 source-certification hardening overlay has not been generated for this MVP build.",
        },
        "paid_smoke_sidecar_evidence": paid_smoke_sidecar,
        "future_holdout_sidecar_evidence": future_holdout_sidecar,
        "retrospective_validation_sidecar_evidence": retrospective_sidecar,
        "clean_supply_breal_extension_sidecar_evidence": clean_supply_breal_extension_sidecar,
        "clean_outcome_unseen_supply_sidecar_evidence": clean_outcome_unseen_supply_sidecar,
        "second_repo_clean_supply_sidecar_evidence": second_repo_clean_supply_sidecar,
        "two_repo_future_holdout_preregistration_sidecar_evidence": two_repo_future_holdout_sidecar,
        "two_repo_future_holdout_paid_sidecar_evidence": two_repo_future_holdout_paid_sidecar,
        "policy_violation_repair_sidecar_evidence": policy_violation_repair_sidecar,
        "clean_future_holdout_scale_up_decision": clean_future_holdout_scale_up_decision(future_holdout_decision),
        "production_ranking_status": "not_produced",
        "next_runbook_recommendation": closeout_next_runbook_recommendation(
            hardening_decision if hardening_sidecar else None,
            paid_smoke_decision,
            future_holdout_decision,
            retrospective_decision,
            clean_supply_breal_extension_decision,
            clean_outcome_unseen_supply_decision,
            second_repo_clean_supply_decision,
            two_repo_future_holdout_decision,
            policy_violation_repair_decision,
        ),
    }


def closeout_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 MVP Closeout",
            "",
            f"Generated: `{payload['generated_at']}`.",
            "",
            f"- Release: `{payload['release_id']}`.",
            f"- Status: `{payload['release_status']}`.",
            "- Predictive validity established: `false`.",
            "- Production ranking: `not_produced`.",
            f"- Evidence status: `{payload['evidence_status']}`.",
            "",
            "The `ready_for_phase1_mvp` gate has been consumed into an MVP compiler artifact set. "
            "The artifact set is infrastructure evidence only; it is not a predictive-validation result.",
            "",
            f"Hardening sidecar evidence: `{payload['hardening_sidecar_evidence']['status']}`.",
            "The hardening overlay is reported as sidecar evidence and is not silently mixed into the historical MVP scorecards.",
            f"Paid smoke sidecar evidence: `{payload['paid_smoke_sidecar_evidence']['status']}`.",
            "Boltons paid-smoke rows are operational scoreability evidence only.",
            f"Future holdout sidecar evidence: `{payload['future_holdout_sidecar_evidence']['status']}`.",
            "Future-holdout evidence is reported as design, blocker, smoke, or validation sidecar evidence only.",
            (
                "Clean future-holdout scale-up decision: "
                f"{payload['clean_future_holdout_scale_up_decision'].get('statement', payload['clean_future_holdout_scale_up_decision']['status'])}"
            ),
            f"Retrospective validation sidecar evidence: `{payload['retrospective_validation_sidecar_evidence']['status']}`.",
            "Retrospective validation evidence remains outcome-seen and is not reported as clean future holdout.",
            f"Clean supply B_real extension sidecar evidence: `{payload['clean_supply_breal_extension_sidecar_evidence']['status']}`.",
            "Clean-supply extension evidence is reported as local supply readiness only, not validation evidence.",
            f"Clean outcome-unseen supply sidecar evidence: `{payload['clean_outcome_unseen_supply_sidecar_evidence']['status']}`.",
            "Clean outcome-unseen supply evidence is reported as preregistration readiness only, not paid validation evidence.",
            f"Second-repo clean supply sidecar evidence: `{payload['second_repo_clean_supply_sidecar_evidence']['status']}`.",
            "Second-repo clean supply evidence is local supply/preregistration evidence; paid validation is reported separately when available.",
            f"Two-repo future-holdout preregistration sidecar evidence: `{payload['two_repo_future_holdout_preregistration_sidecar_evidence']['status']}`.",
            "Two-repo future-holdout preregistration is the frozen design; paid execution is reported separately when available.",
            f"Two-repo future-holdout paid sidecar evidence: `{payload['two_repo_future_holdout_paid_sidecar_evidence']['status']}`.",
            (
                "Two-repo paid validation result: "
                f"`{payload['two_repo_future_holdout_paid_sidecar_evidence'].get('primary_decision_label', 'not_available')}`; "
                f"H_future scoreable cells "
                f"`{payload['two_repo_future_holdout_paid_sidecar_evidence'].get('h_future_scoreable_cells')}`; "
                f"policy violations "
                f"`{payload['two_repo_future_holdout_paid_sidecar_evidence'].get('policy_violation_count')}`."
            ),
            f"Policy-violation repair sidecar evidence: `{payload['policy_violation_repair_sidecar_evidence']['status']}`.",
            (
                "Policy-violation repair result: "
                f"`{payload['policy_violation_repair_sidecar_evidence'].get('terminal_state', 'not_available')}`; "
                f"paid rerun performed "
                f"`{str(payload['policy_violation_repair_sidecar_evidence'].get('paid_rerun_performed')).lower()}`."
            ),
            "",
            f"Next runbook recommendation: {payload['next_runbook_recommendation']}.",
        ]
    )


def run_closeout(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_closeout_payload(config_from_args(args))
    root = output_root_from_args(args)
    write_json(results_dir(root) / "phase1_mvp_closeout.json", payload)
    write_text(reports_dir(root) / "phase1_mvp_closeout.md", closeout_report(payload))
    return payload


BUILD_MVP_COMMANDS = [
    "inventory",
    "build-release",
    "certification-rollup",
    "split-plan",
    "import-scorecards",
    "cost-summary",
    "weighted-score",
    "uncertainty-summary",
    "closeout",
]


def run_build_mvp(args: argparse.Namespace) -> dict[str, Any]:
    runners = {
        "inventory": run_inventory,
        "build-release": run_build_release,
        "certification-rollup": run_certification_rollup,
        "split-plan": run_split_plan,
        "import-scorecards": run_import_scorecards,
        "cost-summary": run_cost_summary,
        "weighted-score": run_weighted_score,
        "uncertainty-summary": run_uncertainty_summary,
        "closeout": run_closeout,
    }
    produced = {}
    for command in BUILD_MVP_COMMANDS:
        produced[command] = runners[command](args)
    return {"schema_version": "barcarolle.phase1.build_mvp_result.v1", "commands": BUILD_MVP_COMMANDS, "produced": sorted(produced)}


def validate_outputs(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    expected = [
        "phase1_input_inventory.json",
        "phase1_certification_rollup.json",
        "phase1_mvp_release.json",
        "phase1_split_plan.json",
        "phase1_workspace_scorecard.json",
        "phase1_cost_summary.json",
        "phase1_weighted_score.json",
        "phase1_uncertainty_summary.json",
        "phase1_mvp_closeout.json",
    ]
    missing = [name for name in expected if not (results_dir(output_root) / name).exists()]
    if missing:
        raise FileNotFoundError(f"missing Phase 1 outputs: {missing}")
    predictive_fields = {}
    for name in expected:
        payload = read_json(results_dir(output_root) / name)
        if "predictive_validity_established" in payload:
            predictive_fields[name] = payload["predictive_validity_established"]
            if payload["predictive_validity_established"] is not False:
                raise ValidationError(f"{name} claims predictive validity")
    release = read_json(results_dir(output_root) / "phase1_mvp_release.json")
    validate_phase1_release_payload(release)
    return {
        "schema_version": "barcarolle.phase1.validation_result.v1",
        "generated_at": now_utc(),
        "status": "valid",
        "config": rel(Path(config["_path"])),
        "validated_outputs": expected,
        "predictive_validity_fields": predictive_fields,
    }


def run_validate(args: argparse.Namespace) -> dict[str, Any]:
    payload = validate_outputs(config_from_args(args), output_root_from_args(args))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def run_import_phase0(args: argparse.Namespace) -> None:
    phase0_root = Path(args.phase0_root).resolve()
    release = import_phase0_release(phase0_root)
    target_profile = load_target_profile(phase0_root)
    scorecard = scorecard_from_phase0(
        release,
        phase0_root,
        score_table_path=getattr(args, "score_table", None),
        run_id=getattr(args, "run_id", "phase0_headroom_matrix"),
    )
    weighted = compute_weighted_score(scorecard, target_profile)
    output_dir = Path(args.output_dir)
    write_json(output_dir / "toolz_phase1_draft_release.json", asdict(release))
    write_json(output_dir / "toolz_phase1_weighted_score.json", asdict(weighted))


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output-root", default=str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 benchmark compiler.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    import_parser = subcommands.add_parser("import-phase0", help="Import the current Phase 0 toolz release.")
    import_parser.add_argument("--phase0-root", default=str(PHASE0_ROOT))
    import_parser.add_argument("--output-dir", default=str(ROOT / "results"))
    import_parser.add_argument("--score-table", default=None)
    import_parser.add_argument("--run-id", default="phase0_headroom_matrix")

    for name in BUILD_MVP_COMMANDS + ["build-mvp", "validate"]:
        add_common_args(subcommands.add_parser(name))

    args = parser.parse_args()
    if args.command == "import-phase0":
        run_import_phase0(args)
    elif args.command == "inventory":
        run_inventory(args)
    elif args.command == "build-release":
        run_build_release(args)
    elif args.command == "certification-rollup":
        run_certification_rollup(args)
    elif args.command == "split-plan":
        run_split_plan(args)
    elif args.command == "import-scorecards":
        run_import_scorecards(args)
    elif args.command == "cost-summary":
        run_cost_summary(args)
    elif args.command == "weighted-score":
        run_weighted_score(args)
    elif args.command == "uncertainty-summary":
        run_uncertainty_summary(args)
    elif args.command == "closeout":
        run_closeout(args)
    elif args.command == "build-mvp":
        run_build_mvp(args)
    elif args.command == "validate":
        run_validate(args)
    else:
        raise AssertionError(args.command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
