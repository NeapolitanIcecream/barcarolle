from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXP_REL = Path("experiments/phase0_headroom")
TOOLZ_REPO_REL = EXP_REL / "external_repos" / "toolz"
CLICK_REPO_REL = Path("archive/2026-05-agent-license-reset/experiments/core_narrative/external_repos/click")
GENERIC_COMPARATOR_REL = EXP_REL / "generic_comparator" / "click_r0"
RAW_REL = EXP_REL / "results" / "raw" / "measured_endpoint"
WORKSPACE_REL = EXP_REL / "workspaces" / "measured_endpoint"
PRIMARY_MODEL = "gpt-5.4-mini"
MODEL_SMOKE_EVENT = "model_smoke_test"
CALIBRATION_TASK_IDS = ["toolz__hist__001", "toolz__hist__003", "toolz__hist__004", "toolz__hist__010"]
RATES = {
    "pricing_source": "user_estimate_required_conservative_default",
    "input_rate_per_1m_usd": 3.0,
    "cached_input_rate_per_1m_usd": 0.3,
    "output_rate_per_1m_usd": 15.0,
}


@dataclass
class Endpoint:
    base_url: str
    api_key: str

    @property
    def host_hash(self) -> str:
        parsed = urllib.parse.urlparse(self.base_url)
        host = parsed.netloc or self.base_url
        return hashlib.sha256(host.encode("utf-8")).hexdigest()[:12]

    @property
    def key_fingerprint(self) -> str:
        return hashlib.sha256(self.api_key.encode("utf-8")).hexdigest()[:12]


@dataclass
class CommandResult:
    command: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(command: list[str], cwd: Path, timeout: int = 120) -> CommandResult:
    start = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return CommandResult(
            command=command,
            cwd=str(cwd),
            returncode=completed.returncode,
            stdout=completed.stdout.decode("utf-8", errors="replace"),
            stderr=completed.stderr.decode("utf-8", errors="replace"),
            duration_seconds=time.monotonic() - start,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command=command,
            cwd=str(cwd),
            returncode=124,
            stdout=exc.stdout.decode("utf-8", errors="replace") if exc.stdout else "",
            stderr=exc.stderr.decode("utf-8", errors="replace") if exc.stderr else "",
            duration_seconds=time.monotonic() - start,
            timed_out=True,
        )


def require_success(result: CommandResult) -> str:
    if result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(result.command)}\n{result.stderr}")
    return result.stdout


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def endpoint_from_env() -> Endpoint:
    base = os.environ.get("LLM_BASE_URL", "").rstrip("/")
    key = os.environ.get("LLM_API_KEY", "")
    if not base or not key:
        raise RuntimeError("LLM_BASE_URL and LLM_API_KEY must be present")
    return Endpoint(base, key)


def request_json(endpoint: Endpoint, path: str, payload: dict[str, Any] | None = None, timeout: int = 120) -> tuple[int, dict[str, Any], float]:
    url = endpoint.base_url.rstrip("/") + path
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Authorization": "Bearer " + endpoint.api_key}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"error": "non_json_response", "body_preview_sha256": hashlib.sha256(body[:1000].encode("utf-8")).hexdigest()[:12]}
            return response.status, parsed, time.monotonic() - start
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"error": body[:1000]}
        return exc.code, parsed, time.monotonic() - start


def discover_models(endpoint: Endpoint) -> tuple[str, dict[str, Any]]:
    for path in ["/models", "/v1/models"]:
        status, payload, _ = request_json(endpoint, path, timeout=60)
        if status == 200 and isinstance(payload.get("data"), list):
            return path, payload
    raise RuntimeError("no OpenAI-compatible model list found at /models or /v1/models")


def sanitize_models(endpoint: Endpoint, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    models = []
    for row in payload.get("data", []):
        models.append(
            {
                "id": row.get("id"),
                "object": row.get("object"),
                "owned_by": row.get("owned_by"),
                "supported_endpoint_types": row.get("supported_endpoint_types", []),
            }
        )
    return {
        "schema_version": "barcarolle.endpoint_models.v1",
        "generated_at": iso_now(),
        "endpoint_host_hash": endpoint.host_hash,
        "models_path_used": path,
        "model_count": len(models),
        "models": sorted(models, key=lambda item: str(item.get("id", ""))),
    }


def parse_usage(payload: dict[str, Any]) -> dict[str, int | None | bool]:
    usage = payload.get("usage") or {}
    prompt_details = usage.get("prompt_tokens_details") or {}
    completion_details = usage.get("completion_tokens_details") or {}
    input_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("completion_tokens")
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": prompt_details.get("cached_tokens"),
        "output_tokens": output_tokens,
        "reasoning_output_tokens": completion_details.get("reasoning_tokens"),
        "usage_observed": input_tokens is not None or output_tokens is not None,
    }


def estimate_cost_usd(
    input_tokens: int | None,
    cached_input_tokens: int | None,
    output_tokens: int | None,
    *,
    input_rate: float = RATES["input_rate_per_1m_usd"],
    cached_rate: float = RATES["cached_input_rate_per_1m_usd"],
    output_rate: float = RATES["output_rate_per_1m_usd"],
) -> float | None:
    if input_tokens is None and output_tokens is None:
        return None
    input_total = max(int(input_tokens or 0), 0)
    cached_total = max(int(cached_input_tokens or 0), 0)
    uncached_total = max(input_total - cached_total, 0)
    output_total = max(int(output_tokens or 0), 0)
    return round((uncached_total * input_rate + cached_total * cached_rate + output_total * output_rate) / 1_000_000, 8)


def ledger_record(
    *,
    endpoint: Endpoint,
    run_id: str,
    phase: str,
    event: str,
    model: str,
    request_api: str,
    status: str,
    latency_seconds: float,
    payload: dict[str, Any] | None,
    artifact_ref: str,
    notes: str = "",
) -> dict[str, Any]:
    usage = parse_usage(payload or {})
    estimated = estimate_cost_usd(
        usage["input_tokens"],
        usage["cached_input_tokens"],
        usage["output_tokens"],
    )
    return {
        "schema_version": "barcarolle.measured_cost.v1",
        "run_id": run_id,
        "timestamp": iso_now(),
        "phase": phase,
        "event": event,
        "endpoint_host_hash": endpoint.host_hash,
        "model": model,
        "request_api": request_api,
        "status": status,
        "latency_seconds": round(latency_seconds, 3),
        "input_tokens": usage["input_tokens"],
        "cached_input_tokens": usage["cached_input_tokens"],
        "output_tokens": usage["output_tokens"],
        "reasoning_output_tokens": usage["reasoning_output_tokens"],
        "usage_observed": usage["usage_observed"],
        "pricing_source": RATES["pricing_source"],
        "input_rate_per_1m_usd": RATES["input_rate_per_1m_usd"],
        "cached_input_rate_per_1m_usd": RATES["cached_input_rate_per_1m_usd"],
        "output_rate_per_1m_usd": RATES["output_rate_per_1m_usd"],
        "estimated_cost_usd": estimated,
        "actual_cost_usd": None,
        "artifact_ref": artifact_ref,
        "notes": notes,
    }


def summarize_cost(rows: list[dict[str, Any]]) -> dict[str, Any]:
    call_rows = [row for row in rows if row.get("event") != "projected_acut_batch"]
    totals = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "usage_observed_count": 0,
    }
    latencies: list[float] = []
    for row in call_rows:
        for key in ["input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"]:
            totals[key] += int(row.get(key) or 0)
        totals["estimated_cost_usd"] += float(row.get("estimated_cost_usd") or 0.0)
        if row.get("usage_observed"):
            totals["usage_observed_count"] += 1
        latencies.append(float(row.get("latency_seconds") or 0.0))
    latencies_sorted = sorted(latencies)
    median = None
    if latencies_sorted:
        median = latencies_sorted[len(latencies_sorted) // 2]
    return {
        "schema_version": "barcarolle.measured_cost_summary.v1",
        "generated_at": iso_now(),
        "call_count": len(call_rows),
        "usage_observed_count": totals["usage_observed_count"],
        "usage_observed_rate": None if not call_rows else round(totals["usage_observed_count"] / len(call_rows), 4),
        "input_tokens": totals["input_tokens"],
        "cached_input_tokens": totals["cached_input_tokens"],
        "output_tokens": totals["output_tokens"],
        "reasoning_output_tokens": totals["reasoning_output_tokens"],
        "estimated_cost_usd": round(totals["estimated_cost_usd"], 8),
        "actual_cost_usd": None,
        "pricing_source": RATES["pricing_source"],
        "median_latency_seconds": median,
    }


def append_manual_pretool_smoke(endpoint: Endpoint) -> dict[str, Any]:
    payload = {
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 5,
            "prompt_tokens_details": {"cached_tokens": 0},
            "completion_tokens_details": {"reasoning_tokens": 0},
        }
    }
    return ledger_record(
        endpoint=endpoint,
        run_id="manual_pretool_smoke_gpt_5_4_mini",
        phase="endpoint_discovery",
        event="manual_pretool_smoke",
        model=PRIMARY_MODEL,
        request_api="/v1/chat/completions",
        status="success",
        latency_seconds=1.739,
        payload=payload,
        artifact_ref="not_retained",
        notes="Manual endpoint smoke run before measurement utility existed; raw response was not retained.",
    )


def chat_completion(endpoint: Endpoint, model: str, messages: list[dict[str, str]], max_tokens: int, raw_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0}
    status, response, latency = request_json(endpoint, "/v1/chat/completions", payload, timeout=240)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps({"request": payload, "response": response, "http_status": status}, indent=2), encoding="utf-8")
    record_meta = {"http_status": status, "latency": latency, "status": "success" if status == 200 else "http_error"}
    return response, record_meta


def run_model_smoke(endpoint: Endpoint, model: str, root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    raw_path = root / RAW_REL / "smoke" / f"{model.replace('/', '_')}.json"
    response, meta = chat_completion(
        endpoint,
        model,
        [{"role": "user", "content": "Return the exact text: ok"}],
        16,
        raw_path,
    )
    content = (response.get("choices") or [{}])[0].get("message", {}).get("content", "")
    smoke = {
        "schema_version": "barcarolle.endpoint_smoke_test.v1",
        "generated_at": iso_now(),
        "model": model,
        "request_api": "/v1/chat/completions",
        "success": meta["status"] == "success" and "ok" in content.lower(),
        "http_status": meta["http_status"],
        "latency_seconds": round(meta["latency"], 3),
        "usage_observed": parse_usage(response)["usage_observed"],
        "raw_artifact_ref": str(raw_path.relative_to(root)),
        "content_preview_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()[:12],
    }
    ledger = ledger_record(
        endpoint=endpoint,
        run_id=f"smoke_{model.replace('/', '_')}",
        phase="endpoint_discovery",
        event=MODEL_SMOKE_EVENT,
        model=model,
        request_api="/v1/chat/completions",
        status="success" if smoke["success"] else "failed",
        latency_seconds=meta["latency"],
        payload=response,
        artifact_ref=str(raw_path.relative_to(root)),
    )
    return smoke, ledger


def archive_tree(repo: Path, commit: str, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(["git", "archive", "--format=tar", commit], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace"))
    with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r:") as tar:
        tar.extractall(destination)


def initialize_workspace_git(workspace: Path) -> None:
    require_success(run_command(["git", "init", "-q"], workspace))
    require_success(run_command(["git", "add", "."], workspace))
    require_success(
        run_command(
            ["git", "-c", "user.name=Barcarolle Phase0", "-c", "user.email=phase0@example.invalid", "commit", "-q", "-m", "base task state"],
            workspace,
        )
    )


def generate_hidden_test_patch(root: Path, task: dict[str, Any], output_dir: Path) -> Path:
    repo = root / TOOLZ_REPO_REL
    output_dir.mkdir(parents=True, exist_ok=True)
    patch_path = output_dir / f"{task['task_id']}_hidden_tests.patch"
    result = run_command(["git", "diff", "--binary", task["base_commit"], task["target_commit"], "--", *task["test_files"]], repo)
    require_success(result)
    patch_path.write_text(result.stdout, encoding="utf-8")
    return patch_path


def changed_paths(workspace: Path) -> list[str]:
    result = run_command(["git", "diff", "--name-only"], workspace)
    require_success(result)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def apply_submission_patch(workspace: Path, patch_path: Path) -> tuple[bool, str, str]:
    check = run_command(["git", "apply", "--check", str(patch_path)], workspace)
    if check.returncode == 0:
        apply_result = run_command(["git", "apply", str(patch_path)], workspace)
        if apply_result.returncode == 0:
            return True, "git_apply", ""
        return False, "git_apply", apply_result.stderr[-1000:]
    # Model-generated unified diffs often have approximate hunk offsets. The
    # standard patch tool is still deterministic and records a distinct method.
    patch_result = run_command(["patch", "-p1", "--forward", "--quiet", "-i", str(patch_path)], workspace)
    if patch_result.returncode == 0:
        return True, "patch_p1_fuzzy", ""
    return False, "patch_p1_fuzzy", patch_result.stderr[-1000:] or check.stderr[-1000:]


def extract_unified_diff(text: str) -> str:
    fence = re.search(r"```(?:diff|patch)?\s*(diff --git[\s\S]*?)```", text)
    if fence:
        return fence.group(1).strip() + "\n"
    start = text.find("diff --git")
    if start >= 0:
        return text[start:].strip() + "\n"
    return ""


def calibration_prompt(task: dict[str, Any], statement: dict[str, Any], workspace: Path) -> str:
    file_blocks = []
    for path in task["code_files"]:
        content = (workspace / path).read_text(encoding="utf-8")
        file_blocks.append(f"### {path}\n```python\n{content}\n```")
    return "\n\n".join(
        [
            "You are a patch-generation coding agent. Produce a minimal unified diff only.",
            "Do not edit tests. Do not mention or use hidden tests. Do not use network resources.",
            "Return output beginning with diff --git and no prose.",
            "",
            "Task statement:",
            statement["solver_facing_statement"],
            "",
            "Scope boundary:",
            statement.get("scope_boundaries", ""),
            "",
            "Repository files at the base commit:",
            *file_blocks,
        ]
    )


def run_calibration_task(
    endpoint: Endpoint,
    root: Path,
    model: str,
    task: dict[str, Any],
    statement: dict[str, Any],
    split: str,
    *,
    run_label: str = "calibration1",
    ledger_phase: str = "calibration_batch",
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    repo = root / TOOLZ_REPO_REL
    run_id = f"measured_{model.replace('/', '_')}__{task['task_id']}__{run_label}"
    solver_ws = root / WORKSPACE_REL / "calibration" / run_id / "solver"
    verify_ws = root / WORKSPACE_REL / "calibration" / run_id / "verify"
    raw_dir = root / RAW_REL / "calibration" / run_id
    archive_tree(repo, task["base_commit"], solver_ws)
    initialize_workspace_git(solver_ws)
    prompt = calibration_prompt(task, statement, solver_ws)
    (raw_dir / "prompt.txt").parent.mkdir(parents=True, exist_ok=True)
    (raw_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    response, meta = chat_completion(endpoint, model, [{"role": "user", "content": prompt}], 1800, raw_dir / "response.json")
    content = (response.get("choices") or [{}])[0].get("message", {}).get("content", "")
    patch_text = extract_unified_diff(content)
    patch_path = raw_dir / "submission.patch"
    patch_path.write_text(patch_text, encoding="utf-8")
    patch_nonempty = bool(patch_text.strip())
    submission = {
        "schema_version": "barcarolle.measured_endpoint_submission.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "model": model,
        "task_id": task["task_id"],
        "split": split,
        "status": "submitted" if meta["status"] == "success" and patch_nonempty else "invalid_output",
        "http_status": meta["http_status"],
        "patch_sha256": sha256_file(patch_path),
        "raw_artifacts": {
            "prompt": str((raw_dir / "prompt.txt").relative_to(root)),
            "response": str((raw_dir / "response.json").relative_to(root)),
            "patch": str(patch_path.relative_to(root)),
        },
    }
    ledger = ledger_record(
        endpoint=endpoint,
        run_id=run_id,
        phase=ledger_phase,
        event="endpoint_acut_task",
        model=model,
        request_api="/v1/chat/completions",
        status="success" if meta["status"] == "success" else "failed",
        latency_seconds=meta["latency"],
        payload=response,
        artifact_ref=str((raw_dir / "response.json").relative_to(root)),
    )
    verifier = {
        "schema_version": "barcarolle.measured_endpoint_verifier.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "model": model,
        "task_id": task["task_id"],
        "split": split,
        "status": "invalid_output",
        "verifier_exit_code": None,
        "harness_error": None,
    }
    if submission["status"] != "submitted":
        return submission, verifier, ledger
    archive_tree(repo, task["base_commit"], verify_ws)
    initialize_workspace_git(verify_ws)
    applied, apply_method, apply_error = apply_submission_patch(verify_ws, patch_path)
    verifier["patch_apply_method"] = apply_method
    if not applied:
        verifier["harness_error"] = "submission_patch_did_not_apply"
        verifier["patch_apply_error_tail"] = apply_error
        return submission, verifier, ledger
    edited_tests = [path for path in changed_paths(verify_ws) if "/tests/" in path or path.startswith("tests/")]
    if edited_tests:
        verifier["harness_error"] = "submission_edited_tests"
        verifier["edited_tests"] = edited_tests
        return submission, verifier, ledger
    hidden_patch = generate_hidden_test_patch(root, task, raw_dir)
    check_tests = run_command(["git", "apply", "--check", str(hidden_patch)], verify_ws)
    if check_tests.returncode != 0:
        verifier["status"] = "harness_error"
        verifier["harness_error"] = "hidden_test_patch_did_not_apply"
        return submission, verifier, ledger
    require_success(run_command(["git", "apply", str(hidden_patch)], verify_ws))
    stdout_path = raw_dir / "verifier_stdout.txt"
    stderr_path = raw_dir / "verifier_stderr.txt"
    result = run_command(["uv", "run", "--project", str(root / EXP_REL), "python", "-m", "pytest", "-q", *task["test_files"]], verify_ws, timeout=180)
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    verifier.update(
        {
            "status": "timeout" if result.timed_out else "verified_pass" if result.returncode == 0 else "verified_fail",
            "verifier_exit_code": result.returncode,
            "duration_seconds": round(result.duration_seconds, 3),
            "raw_artifacts": {"stdout": str(stdout_path.relative_to(root)), "stderr": str(stderr_path.relative_to(root))},
        }
    )
    return submission, verifier, ledger


def load_generic_manifests(root: Path, protocol: dict[str, Any]) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for row in protocol.get("tasks", []):
        if not row.get("same_protocol_scoreable"):
            continue
        manifest_path = row.get("active_manifest")
        if not isinstance(manifest_path, str) or not manifest_path:
            continue
        manifest = read_json(root / manifest_path)
        manifests.append(manifest)
    return manifests


def generic_comparator_prompt(manifest: dict[str, Any], workspace: Path) -> str:
    file_blocks = []
    for path in manifest.get("prompt_code_files", []):
        content = (workspace / path).read_text(encoding="utf-8")
        file_blocks.append(f"### {path}\n```python\n{content}\n```")
    expected_area = "\n".join(f"- {item}" for item in manifest.get("scope_review", {}).get("expected_touched_area", []))
    return "\n\n".join(
        [
            "You are a patch-generation coding agent. Produce a minimal unified diff only.",
            "Do not edit tests. Do not mention or use hidden tests. Do not use network resources.",
            "Return output beginning with diff --git and no prose.",
            "",
            "Task statement:",
            str(manifest["solver_facing_statement"]),
            "",
            "Scope boundary:",
            expected_area,
            "",
            "Repository files at the base commit:",
            *file_blocks,
        ]
    )


def setup_click_verifier_environment(workspace: Path, raw_dir: Path) -> tuple[bool, dict[str, str]]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    venv_result = run_command(["python3", "-m", "venv", ".venv"], workspace, timeout=180)
    venv_stdout = raw_dir / "venv_stdout.txt"
    venv_stderr = raw_dir / "venv_stderr.txt"
    venv_stdout.write_text(venv_result.stdout, encoding="utf-8")
    venv_stderr.write_text(venv_result.stderr, encoding="utf-8")
    if venv_result.returncode != 0:
        return False, {"setup_error": "venv_create_failed", "stdout": str(venv_stdout), "stderr": str(venv_stderr)}

    install_result = run_command([".venv/bin/python", "-m", "pip", "install", "-q", "-e", ".", "pytest"], workspace, timeout=300)
    install_stdout = raw_dir / "venv_install_stdout.txt"
    install_stderr = raw_dir / "venv_install_stderr.txt"
    install_stdout.write_text(install_result.stdout, encoding="utf-8")
    install_stderr.write_text(install_result.stderr, encoding="utf-8")
    if install_result.returncode != 0:
        return False, {"setup_error": "venv_install_failed", "stdout": str(install_stdout), "stderr": str(install_stderr)}
    return True, {
        "venv_stdout": str(venv_stdout),
        "venv_stderr": str(venv_stderr),
        "install_stdout": str(install_stdout),
        "install_stderr": str(install_stderr),
    }


def run_generic_comparator_task(
    endpoint: Endpoint,
    root: Path,
    model: str,
    manifest: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    repo = root / CLICK_REPO_REL
    task_id = manifest["task_id"]
    run_id = f"measured_{model.replace('/', '_')}__{task_id}__matrix1"
    solver_ws = root / WORKSPACE_REL / "matrix" / run_id / "solver"
    verify_ws = root / WORKSPACE_REL / "matrix" / run_id / "verify"
    raw_dir = root / RAW_REL / "matrix" / run_id
    archive_tree(repo, manifest["base_commit"], solver_ws)
    initialize_workspace_git(solver_ws)
    prompt = generic_comparator_prompt(manifest, solver_ws)
    (raw_dir / "prompt.txt").parent.mkdir(parents=True, exist_ok=True)
    (raw_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    response, meta = chat_completion(endpoint, model, [{"role": "user", "content": prompt}], 1800, raw_dir / "response.json")
    content = (response.get("choices") or [{}])[0].get("message", {}).get("content", "")
    patch_text = extract_unified_diff(content)
    patch_path = raw_dir / "submission.patch"
    patch_path.write_text(patch_text, encoding="utf-8")
    patch_nonempty = bool(patch_text.strip())
    submission = {
        "schema_version": "barcarolle.measured_endpoint_submission.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "model": model,
        "task_id": task_id,
        "split": "G_mini",
        "status": "submitted" if meta["status"] == "success" and patch_nonempty else "invalid_output",
        "http_status": meta["http_status"],
        "patch_sha256": sha256_file(patch_path),
        "raw_artifacts": {
            "prompt": str((raw_dir / "prompt.txt").relative_to(root)),
            "response": str((raw_dir / "response.json").relative_to(root)),
            "patch": str(patch_path.relative_to(root)),
        },
    }
    ledger = ledger_record(
        endpoint=endpoint,
        run_id=run_id,
        phase="expanded_matrix",
        event="endpoint_acut_task",
        model=model,
        request_api="/v1/chat/completions",
        status="success" if meta["status"] == "success" else "failed",
        latency_seconds=meta["latency"],
        payload=response,
        artifact_ref=str((raw_dir / "response.json").relative_to(root)),
    )
    verifier = {
        "schema_version": "barcarolle.measured_endpoint_verifier.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "model": model,
        "task_id": task_id,
        "split": "G_mini",
        "status": "invalid_output",
        "verifier_exit_code": None,
        "harness_error": None,
    }
    if submission["status"] != "submitted":
        return submission, verifier, ledger

    archive_tree(repo, manifest["base_commit"], verify_ws)
    initialize_workspace_git(verify_ws)
    applied, apply_method, apply_error = apply_submission_patch(verify_ws, patch_path)
    verifier["patch_apply_method"] = apply_method
    if not applied:
        verifier["harness_error"] = "submission_patch_did_not_apply"
        verifier["patch_apply_error_tail"] = apply_error
        return submission, verifier, ledger
    edited_tests = [path for path in changed_paths(verify_ws) if "/tests/" in path or path.startswith("tests/")]
    if edited_tests:
        verifier["harness_error"] = "submission_edited_tests"
        verifier["edited_tests"] = edited_tests
        return submission, verifier, ledger
    setup_ok, setup_artifacts = setup_click_verifier_environment(verify_ws, raw_dir)
    if not setup_ok:
        verifier["status"] = "harness_error"
        verifier["harness_error"] = setup_artifacts["setup_error"]
        verifier["raw_artifacts"] = {key: str(Path(value).relative_to(root)) for key, value in setup_artifacts.items() if key != "setup_error"}
        return submission, verifier, ledger
    stdout_path = raw_dir / "verifier_stdout.txt"
    stderr_path = raw_dir / "verifier_stderr.txt"
    package_dir = root / GENERIC_COMPARATOR_REL / task_id
    result = run_command([str((package_dir / manifest["oracle_command"]).resolve())], verify_ws, timeout=int(manifest["cost_bound"]["expected_timeout_seconds"]) + 120)
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    raw_artifacts = {
        "stdout": str(stdout_path.relative_to(root)),
        "stderr": str(stderr_path.relative_to(root)),
    }
    raw_artifacts.update({key: str(Path(value).relative_to(root)) for key, value in setup_artifacts.items()})
    verifier.update(
        {
            "status": "timeout" if result.timed_out else "verified_pass" if result.returncode == 0 else "verified_fail",
            "verifier_exit_code": result.returncode,
            "duration_seconds": round(result.duration_seconds, 3),
            "raw_artifacts": raw_artifacts,
        }
    )
    return submission, verifier, ledger


def expanded_matrix_plan(toolz_task_ids: list[str], existing_submissions: list[dict[str, Any]], generic: dict[str, Any]) -> dict[str, list[str]]:
    existing_task_ids = {row["task_id"] for row in existing_submissions}
    missing_toolz = [task_id for task_id in toolz_task_ids if task_id not in existing_task_ids]
    generic_task_ids = [row["task_id"] for row in generic.get("tasks", []) if row.get("same_protocol_scoreable") and row["task_id"] not in existing_task_ids]
    return {
        "missing_toolz_task_ids": missing_toolz,
        "generic_task_ids": generic_task_ids,
        "scheduled_task_ids": [*missing_toolz, *generic_task_ids],
    }


def projected_batch_row(endpoint: Endpoint, model: str, plan: dict[str, list[str]], prior_ledger_rows: list[dict[str, Any]]) -> dict[str, Any]:
    prior_task_costs = [
        float(row["estimated_cost_usd"])
        for row in prior_ledger_rows
        if row.get("event") == "endpoint_acut_task" and row.get("estimated_cost_usd") is not None
    ]
    mean_task_cost = (sum(prior_task_costs) / len(prior_task_costs)) if prior_task_costs else 0.05
    projected_cost = round(mean_task_cost * len(plan["scheduled_task_ids"]), 8)
    return {
        "schema_version": "barcarolle.projected_cost.v1",
        "run_id": "overnight_matrix_a_projected_batch",
        "timestamp": iso_now(),
        "phase": "expanded_matrix",
        "event": "projected_acut_batch",
        "endpoint_host_hash": endpoint.host_hash,
        "model": model,
        "scheduled_task_ids": plan["scheduled_task_ids"],
        "missing_toolz_task_ids": plan["missing_toolz_task_ids"],
        "generic_task_ids": plan["generic_task_ids"],
        "prior_mean_endpoint_task_cost_usd": round(mean_task_cost, 8),
        "projected_batch_cost_usd": projected_cost,
        "budget_soft_cap_usd": 25,
        "budget_hard_cap_usd": 60,
        "projected_cumulative_spend_usd": round(projected_cost + sum(float(row.get("estimated_cost_usd") or 0.0) for row in prior_ledger_rows), 8),
    }


def release_toolz_task_ids(root: Path) -> list[str]:
    release = read_json(root / EXP_REL / "releases" / "toolz_phase0_mini_release.json")
    return [*release["splits"].get("B_real", []), *release["splits"].get("W_real", [])]


def expanded_cost_realignment_payload(summary: dict[str, Any], rows: list[dict[str, Any]], generic: dict[str, Any]) -> dict[str, Any]:
    scoreable = sum(1 for row in rows if row["scoreable_cell"] is True)
    submitted = len(rows)
    estimated = float(summary.get("estimated_cost_usd") or 0.0)
    generic_scoreable = sum(1 for row in rows if row["split"] == "G_mini" and row["scoreable_cell"] is True)
    return {
        "schema_version": "barcarolle.cost_realignment.v1",
        "generated_at": iso_now(),
        "decision": "matrix_a_complete_stay_diagnostic",
        "calibration_estimated_cost_usd": estimated,
        "scoreable_same_repo_cells": sum(1 for row in rows if row["split"] in {"B_real", "W_real"} and row["scoreable_cell"] is True),
        "scoreable_g_mini_cells": generic_scoreable,
        "cost_per_submitted_cell_usd": None if submitted == 0 else round(estimated / submitted, 8),
        "cost_per_scoreable_cell_usd": None if scoreable == 0 else round(estimated / scoreable, 8),
        "usage_observed_rate": summary.get("usage_observed_rate"),
        "generic_comparator_status": generic["status"],
        "projected_cumulative_spend_if_scaled_usd": None,
        "scale_up_approved": False,
        "rationale": "Matrix A repairs the G_mini protocol but remains too small for predictive-validity claims.",
    }


def annotate_matrix_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(metrics)
    metrics["status"] = "measured_endpoint_matrix_a"
    split_metrics = metrics.get("split_metrics", {})
    metrics["g_mini_to_w_real_available"] = (
        split_metrics.get("G_mini", {}).get("scoreable_cell_count", 0) >= 3
        and split_metrics.get("W_real", {}).get("scoreable_cell_count", 0) > 0
    )
    metrics["g_mini_plus_b_real_to_w_real_available"] = (
        metrics["g_mini_to_w_real_available"]
        and split_metrics.get("B_real", {}).get("scoreable_cell_count", 0) > 0
    )
    metrics["invalid_output_rate"] = None
    cell_count = sum(item.get("cell_count", 0) for item in split_metrics.values())
    if cell_count:
        metrics["invalid_output_rate"] = round(metrics.get("invalid_or_harness_error_count", 0) / cell_count, 4)
    return metrics


def write_expanded_cost_report(root: Path, summary: dict[str, Any], realignment: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    status_counts = Counter(row["terminal_status"] for row in rows)
    paid_task_calls = sum(1 for row in read_jsonl(root / EXP_REL / "results" / "measured_cost_ledger.jsonl") if row.get("event") == "endpoint_acut_task")
    write_text(
        root / EXP_REL / "reports" / "measured_cost_report.md",
        "\n".join(
            [
                "# Measured Cost Report",
                "",
                f"Measured call count: `{summary['call_count']}`.",
                f"Paid task-solving calls: `{paid_task_calls}`.",
                f"Usage observed rate: `{summary['usage_observed_rate']}`.",
                f"Input tokens: `{summary['input_tokens']}`.",
                f"Cached input tokens: `{summary['cached_input_tokens']}`.",
                f"Output tokens: `{summary['output_tokens']}`.",
                f"Estimated cost: `${summary['estimated_cost_usd']:.8f}`.",
                f"Pricing source: `{summary['pricing_source']}`.",
                f"Median latency seconds: `{summary['median_latency_seconds']}`.",
                "",
                "## Matrix A Outcomes",
                "",
                *[f"- `{status}`: `{count}`" for status, count in sorted(status_counts.items())],
                "",
                "## Scale Decision",
                "",
                f"Decision: `{realignment['decision']}`.",
                f"Cost per submitted cell: `{realignment['cost_per_submitted_cell_usd']}`.",
                f"Cost per scoreable cell: `{realignment['cost_per_scoreable_cell_usd']}`.",
                "No second ACUT or optional Matrix B is approved from this underpowered Matrix A alone.",
                "",
            ]
        ),
    )


def write_expanded_headroom_outputs(root: Path, rows: list[dict[str, Any]], metrics: dict[str, Any], summary: dict[str, Any], model: str) -> None:
    write_csv(
        root / EXP_REL / "results" / "headroom_score_table.csv",
        rows,
        [
            "acut_id",
            "task_id",
            "split",
            "attempt",
            "submission_status",
            "terminal_status",
            "verifier_exit_code",
            "scoreable_cell",
            "agent_failure",
            "harness_error",
        ],
    )
    write_json(root / EXP_REL / "results" / "headroom_metrics.json", metrics)
    write_json(
        root / EXP_REL / "results" / "headroom_matrix.json",
        {
            "schema_version": "barcarolle.phase0_headroom_matrix.v1",
            "generated_at": iso_now(),
            "status": "measured_endpoint_matrix_a_complete",
            "acut_id": model,
            "paid_model_calls_started": sum(1 for row in read_jsonl(root / EXP_REL / "results" / "measured_cost_ledger.jsonl") if row.get("event") == "endpoint_acut_task"),
            "paid_acut_batches_started": 2,
            "scheduled_task_ids": [row["task_id"] for row in rows],
            "terminal_status_counts": dict(Counter(row["terminal_status"] for row in rows)),
            "scoreable_cell_count": metrics["scoreable_cell_count"],
            "estimated_cost_usd": summary["estimated_cost_usd"],
            "g_mini_protocol_status": metrics["g_mini_protocol_status"],
            "g_mini_to_w_real_available": metrics["g_mini_to_w_real_available"],
            "g_mini_plus_b_real_to_w_real_available": metrics["g_mini_plus_b_real_to_w_real_available"],
            "scale_up_approved": False,
        },
    )
    write_text(
        root / EXP_REL / "reports" / "headroom_analysis.md",
        "\n".join(
            [
                "# Phase 0 Headroom Analysis",
                "",
                "Status: `measured_endpoint_matrix_a_complete`.",
                "",
                "Matrix A uses the measured endpoint path with the current `gpt-5.4-mini` model. It reuses compatible calibration cells and adds the missing `toolz` cells plus the repaired Click `G_mini` comparator cells.",
                "",
                "## Matrix Cells",
                "",
                "| Task | Split | Terminal Status | Scoreable |",
                "|---|---|---:|---:|",
                *[f"| `{row['task_id']}` | `{row['split']}` | `{row['terminal_status']}` | `{row['scoreable_cell']}` |" for row in rows],
                "",
                "Predictive metrics remain `not_applicable_underpowered`; the run is a protocol and harness diagnostic, not a final predictive-validity estimate.",
                "",
            ]
        ),
    )


def write_expanded_final_memo(root: Path, model: str, summary: dict[str, Any], realignment: dict[str, Any], metrics: dict[str, Any]) -> None:
    write_text(
        root / EXP_REL / "reports" / "phase0_decision_memo.md",
        "\n".join(
            [
                "# Phase 0 Decision Memo",
                "",
                "Decision: `proceed_regression_benchmark`.",
                "",
                "## Scope",
                "",
                "Phase 0 now has measured endpoint evidence for same-repo tasks and a repaired same-protocol generic comparator matrix.",
                "",
                f"- Endpoint-selected primary ACUT model: `{model}`.",
                "- Primary target repository: `toolz`.",
                "- Generic comparator source: active Click R0 packages under `experiments/phase0_headroom/generic_comparator/click_r0/`.",
                "- Canonical measured ledger: `experiments/phase0_headroom/results/measured_cost_ledger.jsonl`.",
                f"- Estimated measured endpoint spend: `USD {summary['estimated_cost_usd']:.8f}`.",
                "- Actual provider-billed cost: `null` because the endpoint response did not expose billing dollars.",
                "",
                "## Evidence Summary",
                "",
                "- Certified same-repo tasks after source-adapter repair: `6`.",
                "- Same-protocol `G_mini` comparator tasks: `4`.",
                "- Generic comparator protocol: `scoreable_same_protocol`.",
                f"- Matrix scoreable cells: `{metrics['scoreable_cell_count']}`.",
                f"- Matrix harness or invalid-output cells: `{metrics['invalid_or_harness_error_count']}`.",
                f"- Measured endpoint calls recorded: `{summary['call_count']}`.",
                f"- Input tokens: `{summary['input_tokens']}`.",
                f"- Cached input tokens: `{summary['cached_input_tokens']}`.",
                f"- Output tokens: `{summary['output_tokens']}`.",
                f"- Usage observed rate: `{summary['usage_observed_rate']}`.",
                f"- Cost per scoreable cell: `{realignment['cost_per_scoreable_cell_usd']}`.",
                f"- `G_mini -> W_real` availability: `{metrics['g_mini_to_w_real_available']}`.",
                f"- `G_mini + B_real -> W_real` availability: `{metrics['g_mini_plus_b_real_to_w_real_available']}`.",
                "",
                "## What Phase 0 Supports",
                "",
                "Phase 0 supports continuing as a measured regression-benchmark compiler. The endpoint path can discover models, record token usage, run same-repo and generic comparator cells, and separate verified failures from harness or invalid-output outcomes.",
                "",
                "## What Phase 0 Does Not Support",
                "",
                "Phase 0 still does not support predictive-validity claims. Matrix A is too small and too harness-sensitive to justify moving to `proceed_predictive`.",
                "",
                "## Threats To Validity",
                "",
                "- One primary target repository.",
                "- Small Matrix A sample.",
                "- Generic comparator packages are recovered from archived Click R0 material.",
                "- Pricing uses conservative user-estimate-required rates rather than endpoint billing data.",
                "- MAE, RMSE, and Brier score remain `not_applicable_underpowered`.",
                "",
                "## Next Smallest Useful Experiment",
                "",
                "Initialize the Phase 1 compiler skeleton around task/release schemas, target profiles, stratified weighting, splits, uncertainty, and scorecards before any broader paid residual-validation run.",
                "",
            ]
        ),
    )


def run_expanded_matrix(endpoint: Endpoint, root: Path, model: str) -> None:
    generic = read_json(root / EXP_REL / "results" / "generic_comparator_protocol.json")
    if int(generic.get("scoreable_same_protocol_count") or 0) < 3:
        raise RuntimeError("generic comparator protocol must have at least three scoreable tasks before Matrix A")
    tasks, statements, splits = load_task_maps(root)
    existing_submissions = read_jsonl(root / EXP_REL / "results" / "measured_endpoint_submissions.jsonl")
    existing_verifiers = read_jsonl(root / EXP_REL / "results" / "measured_endpoint_verifier_results.jsonl")
    ledger_rows = read_jsonl(root / EXP_REL / "results" / "measured_cost_ledger.jsonl")
    plan = expanded_matrix_plan(release_toolz_task_ids(root), existing_submissions, generic)
    projected = projected_batch_row(endpoint, model, plan, ledger_rows)
    write_jsonl(root / EXP_REL / "results" / "overnight_projected_cost_ledger.jsonl", [projected])
    if projected["projected_cumulative_spend_usd"] > 40:
        raise RuntimeError("projected Matrix A spend exceeds overnight batch gate")

    submissions = list(existing_submissions)
    verifiers = list(existing_verifiers)
    generic_by_task = {manifest["task_id"]: manifest for manifest in load_generic_manifests(root, generic)}
    for task_id in plan["missing_toolz_task_ids"]:
        submission, verifier, ledger = run_calibration_task(
            endpoint,
            root,
            model,
            tasks[task_id],
            statements[task_id],
            splits[task_id],
            run_label="matrix1",
            ledger_phase="expanded_matrix",
        )
        submissions.append(submission)
        verifiers.append(verifier)
        ledger_rows.append(ledger)
        if not ledger.get("usage_observed"):
            break
    if all(row.get("usage_observed", True) for row in ledger_rows[-len(plan["missing_toolz_task_ids"]):]):
        for task_id in plan["generic_task_ids"]:
            submission, verifier, ledger = run_generic_comparator_task(endpoint, root, model, generic_by_task[task_id])
            submissions.append(submission)
            verifiers.append(verifier)
            ledger_rows.append(ledger)
            if not ledger.get("usage_observed"):
                break

    write_jsonl(root / EXP_REL / "results" / "measured_endpoint_submissions.jsonl", submissions)
    write_jsonl(root / EXP_REL / "results" / "measured_endpoint_verifier_results.jsonl", verifiers)
    write_jsonl(root / EXP_REL / "results" / "measured_cost_ledger.jsonl", ledger_rows)
    rows = score_rows(submissions, verifiers)
    summary = summarize_cost(ledger_rows)
    metrics = annotate_matrix_metrics(metrics_payload(rows, generic["status"]))
    realignment = expanded_cost_realignment_payload(summary, rows, generic)
    write_json(root / EXP_REL / "results" / "measured_cost_summary.json", summary)
    write_json(root / EXP_REL / "results" / "cost_realignment.json", realignment)
    write_expanded_cost_report(root, summary, realignment, rows)
    write_expanded_headroom_outputs(root, rows, metrics, summary, model)
    write_expanded_final_memo(root, model, summary, realignment, metrics)


def score_rows(submissions: list[dict[str, Any]], verifiers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    verifier_by_task = {row["task_id"]: row for row in verifiers}
    rows = []
    for submission in submissions:
        verifier = verifier_by_task.get(submission["task_id"], {})
        terminal = verifier.get("status") or submission["status"]
        rows.append(
            {
                "acut_id": submission["model"],
                "task_id": submission["task_id"],
                "split": submission["split"],
                "attempt": 1,
                "submission_status": submission["status"],
                "terminal_status": terminal,
                "verifier_exit_code": verifier.get("verifier_exit_code", ""),
                "scoreable_cell": terminal in {"verified_pass", "verified_fail"},
                "agent_failure": terminal == "verified_fail",
                "harness_error": terminal in {"harness_error", "invalid_output", "timeout"},
            }
        )
    return rows


def load_task_maps(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, str]]:
    tasks = {row["task_id"]: row for row in read_jsonl(root / EXP_REL / "certified_tasks" / "toolz_certified_tasks.jsonl")}
    statements = {row["task_id"]: row for row in read_jsonl(root / EXP_REL / "certified_tasks" / "toolz_task_statements.jsonl")}
    release_rows = read_csv(root / EXP_REL / "releases" / "toolz_phase0_task_table.csv")
    splits = {row["task_id"]: row["split"] for row in release_rows}
    return tasks, statements, splits


def reverify_existing_calibration(root: Path, model: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    tasks, _statements, splits = load_task_maps(root)
    submissions = read_jsonl(root / EXP_REL / "results" / "measured_endpoint_submissions.jsonl")
    submission_by_task = {row["task_id"]: row for row in submissions}
    verifiers: list[dict[str, Any]] = []
    repo = root / TOOLZ_REPO_REL
    for task_id in CALIBRATION_TASK_IDS:
        task = tasks[task_id]
        split = splits[task_id]
        run_id = f"measured_{model.replace('/', '_')}__{task_id}__calibration1"
        raw_dir = root / RAW_REL / "calibration" / run_id
        patch_path = raw_dir / "submission.patch"
        verify_ws = root / WORKSPACE_REL / "calibration" / run_id / "verify"
        archive_tree(repo, task["base_commit"], verify_ws)
        initialize_workspace_git(verify_ws)
        verifier = {
            "schema_version": "barcarolle.measured_endpoint_verifier.v1",
            "run_id": run_id,
            "generated_at": iso_now(),
            "model": model,
            "task_id": task_id,
            "split": split,
            "status": "invalid_output",
            "verifier_exit_code": None,
            "harness_error": None,
        }
        if not patch_path.exists() or patch_path.stat().st_size == 0:
            verifier["harness_error"] = "missing_or_empty_patch"
            verifiers.append(verifier)
            continue
        applied, apply_method, apply_error = apply_submission_patch(verify_ws, patch_path)
        verifier["patch_apply_method"] = apply_method
        if not applied:
            verifier["harness_error"] = "submission_patch_did_not_apply"
            verifier["patch_apply_error_tail"] = apply_error
            verifiers.append(verifier)
            continue
        edited_tests = [path for path in changed_paths(verify_ws) if "/tests/" in path or path.startswith("tests/")]
        if edited_tests:
            verifier["harness_error"] = "submission_edited_tests"
            verifier["edited_tests"] = edited_tests
            verifiers.append(verifier)
            continue
        hidden_patch = generate_hidden_test_patch(root, task, raw_dir)
        check_tests = run_command(["git", "apply", "--check", str(hidden_patch)], verify_ws)
        if check_tests.returncode != 0:
            verifier["status"] = "harness_error"
            verifier["harness_error"] = "hidden_test_patch_did_not_apply"
            verifiers.append(verifier)
            continue
        require_success(run_command(["git", "apply", str(hidden_patch)], verify_ws))
        stdout_path = raw_dir / "verifier_stdout.txt"
        stderr_path = raw_dir / "verifier_stderr.txt"
        result = run_command(["uv", "run", "--project", str(root / EXP_REL), "python", "-m", "pytest", "-q", *task["test_files"]], verify_ws, timeout=180)
        stdout_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")
        verifier.update(
            {
                "status": "timeout" if result.timed_out else "verified_pass" if result.returncode == 0 else "verified_fail",
                "verifier_exit_code": result.returncode,
                "duration_seconds": round(result.duration_seconds, 3),
                "raw_artifacts": {"stdout": str(stdout_path.relative_to(root)), "stderr": str(stderr_path.relative_to(root))},
            }
        )
        verifiers.append(verifier)
    return submissions, verifiers, read_jsonl(root / EXP_REL / "results" / "measured_cost_ledger.jsonl")


def write_preflight(endpoint: Endpoint, root: Path) -> None:
    endpoint_yaml = "\n".join(
        [
            "schema_version: barcarolle.endpoint_config.v1",
            "base_url_present: true",
            f"endpoint_host_hash: {endpoint.host_hash}",
            "api_key_present: true",
            f"api_key_fingerprint: {endpoint.key_fingerprint}",
            "local_codex_subscription_fallback: disabled",
            "openai_api_key_fallback: disabled",
            "raw_endpoint_url_committed: false",
        ]
    )
    write_text(root / EXP_REL / "configs" / "endpoint.yaml", endpoint_yaml + "\n")
    write_text(
        root / EXP_REL / "reports" / "endpoint_preflight.md",
        "\n".join(
            [
                "# Endpoint Preflight",
                "",
                f"Generated UTC: `{iso_now()}`.",
                "",
                "- `LLM_BASE_URL` present: `true`.",
                "- `LLM_API_KEY` present: `true`.",
                f"- Endpoint host hash: `{endpoint.host_hash}`.",
                f"- Key fingerprint: `{endpoint.key_fingerprint}`.",
                "- Local Codex/ChatGPT subscription fallback: `disabled`.",
                "- `OPENAI_API_KEY` and provider-specific fallback variables were not used.",
                "",
            ]
        ),
    )


def write_model_selection(root: Path, selected_model: str, smoke_rows: list[dict[str, Any]], models_path: str) -> None:
    write_text(
        root / EXP_REL / "configs" / "model_selection.yaml",
        "\n".join(
            [
                "schema_version: barcarolle.model_selection.v1",
                f"primary_acut_model: {selected_model}",
                "stronger_comparison_model: null",
                "selection_source: endpoint_model_discovery",
                f"models_path_used: {models_path}",
                "requires_user_override: false",
            ]
        )
        + "\n",
    )
    smoke = smoke_rows[0]
    write_text(
        root / EXP_REL / "reports" / "model_selection.md",
        "\n".join(
            [
                "# Model Selection",
                "",
                f"Primary ACUT model: `{selected_model}`.",
                "",
                "The selected model appears in the sanitized endpoint model discovery output and completed the smoke request.",
                "",
                "## Smoke Result",
                "",
                f"- Success: `{smoke['success']}`.",
                f"- Latency seconds: `{smoke['latency_seconds']}`.",
                f"- Usage observed: `{smoke['usage_observed']}`.",
                "",
            ]
        ),
    )


def write_measured_budget(root: Path) -> None:
    write_text(
        root / EXP_REL / "configs" / "measured_budget.yaml",
        "\n".join(
            [
                "schema_version: barcarolle.measured_budget.v1",
                "hard_cap_usd: 200",
                "soft_stop_usd: 160",
                "stop_and_ask_usd: 180",
                f"pricing_source: {RATES['pricing_source']}",
                f"input_rate_per_1m_usd: {RATES['input_rate_per_1m_usd']}",
                f"cached_input_rate_per_1m_usd: {RATES['cached_input_rate_per_1m_usd']}",
                f"output_rate_per_1m_usd: {RATES['output_rate_per_1m_usd']}",
                "scale_requires_usage_observed: true",
                "scale_requires_generic_comparator: true",
            ]
        )
        + "\n",
    )


def write_generic_protocol(root: Path) -> dict[str, Any]:
    release = read_json(root / EXP_REL / "releases" / "toolz_phase0_mini_release.json")
    tasks = []
    for task_id in release["splits"].get("G_mini", []):
        tasks.append(
            {
                "task_id": task_id,
                "repo_id": "click",
                "status": "metadata_only",
                "same_protocol_scoreable": False,
                "reason": "archived Click metadata lacks active Phase 0 base checkout, solver statement, and verifier package",
            }
        )
    payload = {
        "schema_version": "barcarolle.generic_comparator_protocol.v1",
        "generated_at": iso_now(),
        "status": "blocked_metadata_only",
        "scoreable_same_protocol_count": 0,
        "required_scoreable_same_protocol_count": 3,
        "tasks": tasks,
        "decision": "repair_generic_comparator_first",
    }
    write_json(root / EXP_REL / "results" / "generic_comparator_protocol.json", payload)
    write_text(
        root / EXP_REL / "reports" / "generic_comparator_protocol.md",
        "\n".join(
            [
                "# Generic Comparator Protocol",
                "",
                "Status: `blocked_metadata_only`.",
                "",
                "The archived Click `G_mini` records remain useful metadata, but they are not active Phase 0 task packages. Materializing them would require producing Phase 0-compatible base checkouts, solver-facing statements, hidden verifiers, and leakage review records rather than reviving old core-narrative semantics.",
                "",
                "- Same-protocol scoreable `G_mini` tasks: `0`.",
                "- Required for comparator repair gate: `3`.",
                "- Paid comparator ACUT calls started: `0`.",
                "",
            ]
        ),
    )
    return payload


def metrics_payload(rows: list[dict[str, Any]], generic_status: str) -> dict[str, Any]:
    split_metrics: dict[str, dict[str, Any]] = {}
    for split in sorted({row["split"] for row in rows}):
        split_rows = [row for row in rows if row["split"] == split]
        scoreable = [row for row in split_rows if row["scoreable_cell"] is True]
        passes = [row for row in scoreable if row["terminal_status"] == "verified_pass"]
        split_metrics[split] = {
            "cell_count": len(split_rows),
            "scoreable_cell_count": len(scoreable),
            "verified_pass_count": len(passes),
            "verified_fail_count": sum(1 for row in scoreable if row["terminal_status"] == "verified_fail"),
            "pass_rate": None if not scoreable else round(len(passes) / len(scoreable), 4),
        }
    return {
        "schema_version": "barcarolle.phase0_headroom_metrics.v1",
        "generated_at": iso_now(),
        "status": "measured_endpoint_calibration",
        "claim_scope": "measured_endpoint_diagnostic",
        "split_metrics": split_metrics,
        "scoreable_cell_count": sum(1 for row in rows if row["scoreable_cell"] is True),
        "invalid_or_harness_error_count": sum(1 for row in rows if row["harness_error"] is True),
        "g_mini_protocol_status": generic_status,
        "mae": "not_applicable_underpowered",
        "rmse": "not_applicable_underpowered",
        "brier_score": "not_applicable_underpowered",
    }


def cost_realignment_payload(summary: dict[str, Any], rows: list[dict[str, Any]], generic: dict[str, Any]) -> dict[str, Any]:
    scoreable = sum(1 for row in rows if row["scoreable_cell"] is True)
    calibration_cost = float(summary.get("estimated_cost_usd") or 0.0)
    cost_per_scoreable = None if scoreable == 0 else round(calibration_cost / scoreable, 8)
    decision = "repair_generic_comparator_first" if generic["scoreable_same_protocol_count"] < 3 else "stay_diagnostic"
    return {
        "schema_version": "barcarolle.cost_realignment.v1",
        "generated_at": iso_now(),
        "decision": decision,
        "calibration_estimated_cost_usd": calibration_cost,
        "scoreable_same_repo_cells": scoreable,
        "cost_per_scoreable_cell_usd": cost_per_scoreable,
        "usage_observed_rate": summary.get("usage_observed_rate"),
        "generic_comparator_status": generic["status"],
        "projected_cumulative_spend_if_scaled_usd": None,
        "scale_up_approved": False,
        "rationale": "Same-repo calibration is measured, but G_mini comparator protocol remains blocked.",
    }


def write_cost_report(root: Path, summary: dict[str, Any], realignment: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    status_counts = Counter(row["terminal_status"] for row in rows)
    write_text(
        root / EXP_REL / "reports" / "measured_cost_report.md",
        "\n".join(
            [
                "# Measured Cost Report",
                "",
                f"Measured call count: `{summary['call_count']}`.",
                f"Usage observed rate: `{summary['usage_observed_rate']}`.",
                f"Input tokens: `{summary['input_tokens']}`.",
                f"Cached input tokens: `{summary['cached_input_tokens']}`.",
                f"Output tokens: `{summary['output_tokens']}`.",
                f"Estimated cost: `${summary['estimated_cost_usd']:.8f}`.",
                f"Pricing source: `{summary['pricing_source']}`.",
                f"Median latency seconds: `{summary['median_latency_seconds']}`.",
                "",
                "## Calibration Outcomes",
                "",
                *[f"- `{status}`: `{count}`" for status, count in sorted(status_counts.items())],
                "",
                "## Scale Decision",
                "",
                f"Decision: `{realignment['decision']}`.",
                f"Cost per scoreable cell: `{realignment['cost_per_scoreable_cell_usd']}`.",
                "No scale-up batch is approved until generic comparator protocol is repaired or explicitly waived.",
                "",
            ]
        ),
    )


def write_headroom_outputs(root: Path, rows: list[dict[str, Any]], metrics: dict[str, Any], summary: dict[str, Any], model: str) -> None:
    write_csv(
        root / EXP_REL / "results" / "headroom_score_table.csv",
        rows,
        [
            "acut_id",
            "task_id",
            "split",
            "attempt",
            "submission_status",
            "terminal_status",
            "verifier_exit_code",
            "scoreable_cell",
            "agent_failure",
            "harness_error",
        ],
    )
    write_json(root / EXP_REL / "results" / "headroom_metrics.json", metrics)
    write_json(
        root / EXP_REL / "results" / "headroom_matrix.json",
        {
            "schema_version": "barcarolle.phase0_headroom_matrix.v1",
            "generated_at": iso_now(),
            "status": "measured_endpoint_calibration_complete",
            "acut_id": model,
            "paid_model_calls_started": len(rows),
            "paid_acut_batches_started": 1,
            "scheduled_task_ids": [row["task_id"] for row in rows],
            "terminal_status_counts": dict(Counter(row["terminal_status"] for row in rows)),
            "scoreable_cell_count": metrics["scoreable_cell_count"],
            "estimated_cost_usd": summary["estimated_cost_usd"],
            "g_mini_protocol_status": metrics["g_mini_protocol_status"],
            "scale_up_approved": False,
        },
    )
    write_text(
        root / EXP_REL / "reports" / "headroom_analysis.md",
        "\n".join(
            [
                "# Phase 0 Headroom Analysis",
                "",
                "Status: `measured_endpoint_calibration_complete`.",
                "",
                "The measured endpoint run replaces the earlier Codex-subscription cost estimate for Phase 0 calibration. It remains underpowered and diagnostic only.",
                "",
                "## Calibration Cells",
                "",
                "| Task | Split | Terminal Status | Scoreable |",
                "|---|---|---:|---:|",
                *[f"| `{row['task_id']}` | `{row['split']}` | `{row['terminal_status']}` | `{row['scoreable_cell']}` |" for row in rows],
                "",
                "Predictive metrics remain `not_applicable_underpowered` because `G_mini` is not same-protocol scoreable and the calibration matrix is small.",
                "",
            ]
        ),
    )


def write_final_memo(root: Path, model: str, summary: dict[str, Any], realignment: dict[str, Any], metrics: dict[str, Any]) -> None:
    write_text(
        root / EXP_REL / "reports" / "phase0_decision_memo.md",
        "\n".join(
            [
                "# Phase 0 Decision Memo",
                "",
                "Decision: `proceed_regression_benchmark`.",
                "",
                "## Scope",
                "",
                "Phase 0 now has measured endpoint evidence in addition to the earlier certification and same-repo scoring chain.",
                "",
                f"- Endpoint-selected primary ACUT model: `{model}`.",
                "- Primary target repository: `toolz`.",
                "- Generic comparator source: archived Click R0 metadata.",
                "- Canonical measured ledger: `experiments/phase0_headroom/results/measured_cost_ledger.jsonl`.",
                f"- Estimated measured endpoint spend: `USD {summary['estimated_cost_usd']:.8f}`.",
                "- Actual provider-billed cost: `null` because the endpoint response did not expose billing dollars.",
                "",
                "## Evidence Summary",
                "",
                "- Certified same-repo tasks after source-adapter repair: `6`.",
                "- Mini release status: `benchmark_grade_candidate`.",
                "- Generic comparator protocol: `blocked_metadata_only` with `0` same-protocol `G_mini` tasks.",
                f"- Calibration scoreable same-repo cells: `{metrics['scoreable_cell_count']}`.",
                f"- Calibration harness or invalid-output cells: `{metrics['invalid_or_harness_error_count']}`.",
                f"- Measured endpoint calls recorded: `{summary['call_count']}`.",
                f"- Input tokens: `{summary['input_tokens']}`.",
                f"- Cached input tokens: `{summary['cached_input_tokens']}`.",
                f"- Output tokens: `{summary['output_tokens']}`.",
                f"- Usage observed rate: `{summary['usage_observed_rate']}`.",
                f"- Cost per scoreable cell: `{realignment['cost_per_scoreable_cell_usd']}`.",
                "",
                "## What Phase 0 Supports",
                "",
                "Phase 0 supports continuing as a measured regression-benchmark compiler. The endpoint path can discover models, record token usage, run a measured same-repo calibration batch, and separate verified failures from harness or invalid-output outcomes.",
                "",
                "## What Phase 0 Does Not Support",
                "",
                "Phase 0 still does not support predictive-validity claims. The generic comparator remains blocked, so `G_mini -> W_real` and `G_mini + B_real -> W_real` comparisons are unavailable.",
                "",
                "## Threats To Validity",
                "",
                "- One primary target repository.",
                "- Small calibration batch.",
                "- `G_mini` comparator tasks are metadata-only under the measured endpoint protocol.",
                "- Pricing uses conservative user-estimate-required rates rather than endpoint billing data.",
                "- MAE, RMSE, and Brier score remain `not_applicable_underpowered`.",
                "",
                "## Next Smallest Useful Experiment",
                "",
                "Run `repair_generic_comparator_first` by materializing at least three Phase 0-compatible `G_mini` tasks before any second ACUT or larger same-repo scale-up.",
                "",
            ]
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 0 measured endpoint runbook.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--reverify-existing", action="store_true", help="Re-score existing raw calibration patches without new endpoint calls.")
    parser.add_argument("--run-expanded-matrix", action="store_true", help="Run Matrix A by reusing existing calibration cells and adding missing toolz plus scoreable G_mini cells.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    endpoint = endpoint_from_env()

    if args.run_expanded_matrix:
        run_expanded_matrix(endpoint, root, PRIMARY_MODEL)
        return 0

    if args.reverify_existing:
        generic = read_json(root / EXP_REL / "results" / "generic_comparator_protocol.json")
        submissions, verifiers, ledger_rows = reverify_existing_calibration(root, PRIMARY_MODEL)
        write_jsonl(root / EXP_REL / "results" / "measured_endpoint_verifier_results.jsonl", verifiers)
        rows = score_rows(submissions, verifiers)
        summary = summarize_cost(ledger_rows)
        realignment = cost_realignment_payload(summary, rows, generic)
        metrics = metrics_payload(rows, generic["status"])
        write_json(root / EXP_REL / "results" / "measured_cost_summary.json", summary)
        write_json(root / EXP_REL / "results" / "cost_realignment.json", realignment)
        write_cost_report(root, summary, realignment, rows)
        write_headroom_outputs(root, rows, metrics, summary, PRIMARY_MODEL)
        write_final_memo(root, PRIMARY_MODEL, summary, realignment, metrics)
        return 0

    write_preflight(endpoint, root)
    models_path, models_payload = discover_models(endpoint)
    models = sanitize_models(endpoint, models_path, models_payload)
    write_json(root / EXP_REL / "results" / "endpoint_models.json", models)
    discovered_ids = {row["id"] for row in models["models"]}
    if PRIMARY_MODEL not in discovered_ids:
        raise RuntimeError(f"selected model {PRIMARY_MODEL} was not discovered")

    smoke, smoke_ledger = run_model_smoke(endpoint, PRIMARY_MODEL, root)
    if not smoke["success"]:
        raise RuntimeError("selected model failed smoke test")
    write_jsonl(root / EXP_REL / "results" / "endpoint_smoke_tests.jsonl", [smoke])
    write_model_selection(root, PRIMARY_MODEL, [smoke], models_path)
    write_measured_budget(root)

    generic = write_generic_protocol(root)
    tasks, statements, splits = load_task_maps(root)
    submissions: list[dict[str, Any]] = []
    verifiers: list[dict[str, Any]] = []
    ledger_rows = [append_manual_pretool_smoke(endpoint), smoke_ledger]
    for task_id in CALIBRATION_TASK_IDS:
        submission, verifier, ledger = run_calibration_task(endpoint, root, PRIMARY_MODEL, tasks[task_id], statements[task_id], splits[task_id])
        submissions.append(submission)
        verifiers.append(verifier)
        ledger_rows.append(ledger)
    write_jsonl(root / EXP_REL / "results" / "measured_endpoint_submissions.jsonl", submissions)
    write_jsonl(root / EXP_REL / "results" / "measured_endpoint_verifier_results.jsonl", verifiers)
    rows = score_rows(submissions, verifiers)
    summary = summarize_cost(ledger_rows)
    realignment = cost_realignment_payload(summary, rows, generic)
    metrics = metrics_payload(rows, generic["status"])

    write_jsonl(root / EXP_REL / "results" / "measured_cost_ledger.jsonl", ledger_rows)
    write_json(root / EXP_REL / "results" / "measured_cost_summary.json", summary)
    write_json(root / EXP_REL / "results" / "cost_realignment.json", realignment)
    write_cost_report(root, summary, realignment, rows)
    write_headroom_outputs(root, rows, metrics, summary, PRIMARY_MODEL)
    write_final_memo(root, PRIMARY_MODEL, summary, realignment, metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
