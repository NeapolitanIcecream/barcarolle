# Core Narrative Experiment Plan

## 1. Goal

This plan is for a fast experimental validation of Barcarolle's core narrative:

> A high score on a general coding-agent benchmark is not sufficient evidence that an agent configuration will work well in a specific repository. A repository-specific benchmark should better predict actual work quality in that repository.

The intended effect is an NFL-style ranking reversal:

- configuration A scores higher than B on a general benchmark;
- A scores lower than B on a repository-specific benchmark;
- A also performs worse than B on held-out repository work.

This is an experiment-first plan. It intentionally uses protocolized Codex-assisted artifact construction plus minimal runner/verifier glue before building the full Barcarolle platform.

## 2. Operating Mode

Use a workflow similar to `codex-design-review-loop`:

- The main Codex agent is the coordinator.
- The coordinator creates a workflow directory under `.codex-workflows/core-narrative-experiment/`.
- Subtasks run as separate non-interactive Codex CLI instances inside `tmux`.
- Each sub-agent owns explicit files or directories.
- Each sub-agent updates only its `process.md` and assigned artifact paths.
- The coordinator reads `coordinator.md` and worker `process.md` files, not CLI logs.
- CLI logs are redirected to files for debugging only.
- Reviewers inspect delivered artifacts after workers mark `status: delivered`.

If the Codex app heartbeat automation is available, create a heartbeat that wakes the coordinator every 10 minutes. On each heartbeat, the coordinator performs one bounded coordination step and returns without active polling.

## 3. Non-Goals

Do not implement the full Barcarolle product during this experiment.

Out of scope for this phase:

- License issuance and consumer conformance.
- Full `G0` through `G5` authorization semantics.
- Operator console.
- Multi-repository federation.
- Full automatic policy calibration.
- Golden/Judge governance beyond simple review support.
- Production Temporal workflows.
- Full invariant catalog.

The experiment may add small scripts and schemas when needed to make the artifacts runnable and auditable.

## 4. Experimental Design

### 4.1 Three Measurements

Each tested agent configuration, or ACUT, gets three scores:

| Score | Meaning | Source |
| --- | --- | --- |
| `G_score` | General benchmark performance | Frozen external/general benchmark slice or accepted public score with basis clearly marked |
| `R_score` | Repository-specific benchmark performance | Protocolized benchmark artifacts built for selected target repository |
| `W_score` | Held-out actual repository work performance | Disjoint held-out tasks from the same repository, evaluated by verifier plus review rubric |

The core claim is supported when `R_score` predicts `W_score` better than `G_score`, especially when at least one clear ranking reversal appears.

### 4.2 Target Repository Selection

Start with one repository. Add a second only after the first repository has a working task pack and runner smoke test.

Selection criteria:

- Deterministic test suite that can run locally.
- Enough historical issue, PR, or commit tasks to mine 20 to 40 benchmark tasks plus 10 to 20 held-out work tasks.
- Build time is acceptable for repeated runs.
- Repository does not depend heavily on external services.
- The language and tooling are familiar enough for Codex agents to build verifiers quickly.
- The license permits local evaluation use.

Avoid using this Barcarolle repository as the target repository because it currently has design documents but not enough executable code and tests for the experiment.

### 4.3 Task Splits

For each target repository:

- `RBench`: 20 to 40 repository-specific benchmark tasks.
- `RWork`: 10 to 20 held-out repository work tasks.

`RBench` and `RWork` must use disjoint source anchors. Prefer a temporal split:

- `RBench`: historical tasks before cutoff `T`.
- `RWork`: later historical tasks after cutoff `T`, or current maintainer-style tasks if available.

If a temporal split is impossible, use a source-anchor split and record the limitation.

### 4.4 ACUT Matrix

Use 4 to 8 agent configurations. The set should deliberately include likely ranking reversals:

- General-benchmark-optimized configuration.
- Repository-context-heavy configuration.
- Minimal-context baseline.
- Higher-budget configuration.
- Lower-budget configuration.
- Different model/provider if feasible.
- Same model with different repository retrieval strategy.

Each ACUT must be frozen in a YAML manifest:

- model and provider;
- prompt or policy digest;
- tool permissions;
- retrieval/context strategy;
- runtime budget;
- network policy;
- execution mode;
- adapter or harness basis;
- date and operator.

### 4.5 General Benchmark Basis

The final experiment should run the selected ACUTs on a frozen general benchmark slice if feasible. If cost or setup prevents that, public leaderboard scores may be used only as a pre-screening signal and must be marked as weaker evidence.

The coordinator must record:

- benchmark name;
- version or snapshot date;
- task subset;
- scoring method;
- whether the score was directly run or externally sourced;
- any mismatch between the general benchmark ACUT and the repository experiment ACUT.

### 4.6 LLM Access and Budget Contract

ACUT execution must use the experiment-specific LLM access environment variables:

- `BARCAROLLE_LLM_API_KEY`
- `BARCAROLLE_LLM_BASE_URL`

Do not write API keys, bearer tokens, provider secrets, or resolved credential values into Git, `process.md`, run results, CLI logs, or reports. Workers may mention the environment variable names only. If either variable is missing, ACUT execution workers must mark themselves `blocked` before making any model call.

The total LLM spend cap for this experiment is **USD $300**. This is a hard cap. The coordinator should target a weaker but usable signal rather than a full matrix.

Budget policy:

- Treat `$240` as the soft stop where the coordinator must decide whether remaining runs are worth the remaining budget.
- Treat `$300` as the hard stop. No new ACUT patch-generation run may start once the ledger reaches or is projected to exceed `$300`.
- Prefer directly-run, budget-constrained evidence over broad but unaffordable coverage.
- If actual provider billing is not returned by the API or runner, estimate cost conservatively using SOTA pricing. For OpenAI `gpt-5.5`, use `$5 / 1M input tokens` and `$30 / 1M output tokens`; for Anthropic Opus-class pricing, use `$5 / 1M input tokens` and `$25 / 1M output tokens`; for unknown SOTA-compatible endpoints, default to the higher OpenAI estimate.
- Record both actual usage, when available, and conservative estimated usage.

Budget-constrained execution profile:

- Keep all seven ACUT manifests as design artifacts.
- Run only a core subset unless the coordinator explicitly records spare budget:
  - `general-benchmark-optimized`
  - `repo-context-heavy`
  - `retrieval-sparse-symbolic`
  - `lower-budget-fast-path`
- Defer `higher-budget-repo-depth`, `retrieval-history-augmented`, and `minimal-context-baseline` unless the core subset finishes below the soft stop.
- Downsample the first executable experiment to:
  - 6 locked general-benchmark tasks for `G_score`;
  - 8 accepted `RBench` tasks for `R_score`;
  - 6 accepted `RWork` tasks for `W_score`.
- This yields about 80 primary ACUT patch-generation runs for the four-ACUT core subset, before smoke tests and targeted reruns.
- Run at most one primary attempt per ACUT/task. Use reruns only for claimed ranking reversals, infrastructure ambiguity, or patch-application ambiguity, and only while under the soft stop.

Required budget artifacts:

- `experiments/core_narrative/configs/llm_access.yaml` records only environment variable names, provider/base-url label, redaction policy, and budget caps.
- `experiments/core_narrative/results/cost_ledger.jsonl` records every ACUT model call or patch-generation attempt with ACUT ID, task ID, split, input tokens, output tokens, estimated cost, actual cost when available, and cumulative estimated cost.
- Summary reports must state that the experiment is budget-constrained and intentionally weaker than the original full matrix.

## 5. Artifact Layout

Recommended committed layout:

```text
docs/experiments/core-narrative-experiment-plan.md
experiments/core_narrative/
  README.md
  configs/
    acuts/
      <acut_id>.yaml
    general_benchmark.yaml
    llm_access.yaml
    target_repositories.yaml
  schemas/
    acut.schema.json
    task.schema.json
    run_result.schema.json
  tools/
    prepare_workspace.py
    run_task.py
    apply_and_verify.py
    summarize_results.py
  tasks/
    <repo_slug>/
      rbench/
        <task_id>/
          task.yaml
          public/
            statement.md
          verifier/
            run.sh
          private/
            reference.patch
            expected.json
          admission.md
      rwork/
        <task_id>/
          ...
  results/
    cost_ledger.jsonl
    raw/
    normalized/
    figures/
  reports/
    core_narrative_report.md
```

Recommended uncommitted or externally stored layout:

```text
experiments/core_narrative/workspaces/
experiments/core_narrative/external_repos/
experiments/core_narrative/cache/
experiments/core_narrative/large_artifacts/
```

`task.yaml` and `private/` artifacts are coordinator-side benchmark artifacts, not ACUT inputs. They may be committed after the experiment for audit, but during evaluation the ACUT process must not run from the Barcarolle repo root and must not have access to these files. ACUT workspaces receive only the base repository checkout, public task statement, allowed context, and run instructions.

### 5.1 Git-Managed Versus External Artifacts

Use Git for small, reviewable, reproducible experiment state:

- experiment code under `experiments/core_narrative/tools/**`;
- schemas under `experiments/core_narrative/schemas/**`;
- ACUT manifests and benchmark-basis manifests;
- task manifests, public task statements, admission notes, leakage notes, and small verifier scripts;
- normalized JSON/CSV results when file size stays reviewable;
- report drafts, figures, process files, review notes, and decision logs;
- workflow prompts and handoff files under `.codex-workflows/core-narrative-experiment/**`, except CLI logs.

Do not put large or volatile artifacts directly in Git:

- ACUT workspaces;
- cloned target repositories;
- package, build, and model caches;
- full stdout/stderr logs from large runs;
- container images and dependency caches;
- large raw artifacts;
- private reference patches before the coordinator has decided they are safe to archive.

For the first experiment, prefer plain Git plus manifest files. Do not add DVC, Git LFS, or object-storage plumbing unless raw artifact size or reproducibility pressure makes plain manifests inadequate.

Recommended `.gitignore` entries for the experiment:

```gitignore
experiments/core_narrative/workspaces/
experiments/core_narrative/external_repos/
experiments/core_narrative/cache/
experiments/core_narrative/large_artifacts/
experiments/core_narrative/results/raw/*/logs/
.codex-workflows/core-narrative-experiment/**/cli.log
```

If a raw artifact is too large for Git, store it externally and commit a small manifest with:

- artifact kind;
- producer worker;
- local or object-store URI;
- digest;
- size;
- generation command;
- related ACUT, task, and run IDs.

### 5.2 Branch and Worktree Policy

The coordinator should start from a dedicated branch:

```bash
git checkout -b codex/core-narrative-experiment
```

Use separate Git worktrees for workers that write code, generate many artifacts, or run commands with side effects. Recommended worktree workers:

- `schema-toolsmith`;
- `task-builder-<repo>`;
- `verifier-auditor-<repo>`;
- `leakage-auditor-<repo>` when it edits task metadata;
- `execution-shard-<n>`;
- `analysis`.

Lightweight planning workers such as `repo-scout`, `acut-matrix`, and `general-benchmark` may share the coordinator worktree if their owned paths are strictly disjoint. Use a worktree anyway if they start running repository probes or producing generated files.

Suggested setup:

```bash
git worktree add ../barcarolle-wt-schema \
  -b codex/core-exp-schema-toolsmith

git worktree add ../barcarolle-wt-task-builder \
  -b codex/core-exp-task-builder

git worktree add ../barcarolle-wt-analysis \
  -b codex/core-exp-analysis
```

Each worker prompt and `run.sh` should record both:

- `COORDINATOR_REPO=/Users/chenmohan/gits/barcarolle`
- `WORKER_REPO=/Users/chenmohan/gits/barcarolle-wt-<worker>` when a worktree is used

The Codex CLI `-C` argument must point at `WORKER_REPO`, not the coordinator worktree, for worktree-backed workers.

During status coordination, read only the worker's `process.md` plus Git metadata from that worker branch. During artifact review, inspect the delivered files normally, then merge or cherry-pick the branch after review. Do not let multiple workers commit to the same branch unless they own disjoint result shards and the coordinator has explicitly recorded that choice.

## 6. Minimal Task Schema

Each task should have a `task.yaml` with at least:

```yaml
task_id: repo_slug__family__number
repo_slug: example_repo
split: rbench
source:
  kind: pull_request
  public_url: null
  anchor_id: redacted_or_internal
  base_commit: "<sha>"
  target_commit: "<sha>"
task_family: bugfix
task_statement_path: public/statement.md
allowed_context:
  include_git_history_before_base: false
  include_issue_text: true
  include_pr_text: false
  include_reference_patch: false
disallowed_context:
  - target_commit
  - future_git_history
  - merged_pr_solution
verifier:
  command: verifier/run.sh
  timeout_seconds: 600
expected:
  no_op_fails: true
  reference_passes: true
leakage:
  reviewed: true
  notes: ""
admission:
  status: accepted
  reviewer: codex-or-human
  rationale: ""
```

`target_commit` is allowed in `task.yaml` only because `task.yaml` is private to the benchmark coordinator. It must not be copied into the ACUT-visible task package.

## 7. Minimal Run Result Schema

Each ACUT task attempt should produce a normalized JSON result:

```json
{
  "run_id": "string",
  "acut_id": "string",
  "task_id": "string",
  "split": "rbench",
  "attempt": 1,
  "started_at": "ISO-8601",
  "finished_at": "ISO-8601",
  "status": "passed|failed|infra_failed|timeout|invalid_submission",
  "patch_path": "string",
  "verification": {
    "exit_code": 0,
    "stdout_artifact": "string",
    "stderr_artifact": "string",
    "duration_seconds": 0
  },
  "review": {
    "mergeability_grade": null,
    "wrong_module": false,
    "rule_violation": false,
    "notes": ""
  }
}
```

## 8. Worker Model

### 8.1 Shared Worker Contract

Every worker prompt must include:

- The coordinator repo path: `/Users/chenmohan/gits/barcarolle`.
- The worker repo path. This may be the coordinator worktree for lightweight workers, or a dedicated Git worktree for code, task, verifier, execution, and analysis workers.
- The worker branch name when a dedicated worktree is used.
- The workflow path: `.codex-workflows/core-narrative-experiment/`.
- The worker's owned paths.
- A warning that other workers may be editing the repository.
- A rule not to revert unrelated changes.
- A rule to update `process.md` at start, after major phases, and before exit.
- A rule to mark `status: delivered` only when artifacts are complete and self-checked.
- A rule to mark `status: blocked` with exact blocker details when blocked.

Minimum `process.md` shape:

```markdown
# Process

status: working
updated: 2026-04-27T00:00:00+08:00

## Summary
...

## Owned Paths
...

## Files Changed Or Inspected
...

## Current Blockers
...

## Git State
branch: ...
worktree: ...

## Handoff
...
```

### 8.2 Suggested Workers

Run these workers in waves.

| Worker | Can Start | Owns | Delivers |
| --- | --- | --- | --- |
| `repo-scout` | Wave 0 | `experiments/core_narrative/configs/target_repositories.yaml`, scouting notes | Shortlist and final target repo recommendation |
| `schema-toolsmith` | Wave 0 | `experiments/core_narrative/schemas/**`, `experiments/core_narrative/tools/**` | Minimal schemas and runner/verifier scripts |
| `acut-matrix` | Wave 0 | `experiments/core_narrative/configs/acuts/**` | 4 to 8 frozen ACUT manifests |
| `general-benchmark` | Wave 0 | `experiments/core_narrative/configs/general_benchmark.yaml`, notes | General benchmark basis and run plan |
| `task-builder-<repo>` | Wave 1 | `experiments/core_narrative/tasks/<repo_slug>/**` | RBench/RWork task packages |
| `verifier-auditor-<repo>` | Wave 1 | verifier review notes, fixes inside assigned task dirs | No-op/reference verification audit |
| `leakage-auditor-<repo>` | Wave 1 | admission/leakage notes inside assigned task dirs | Leakage review and task exclusions |
| `execution-shard-<n>` | Wave 2 | `experiments/core_narrative/results/raw/<shard_id>/**` | Raw ACUT x task run results |
| `analysis` | Wave 3 | `experiments/core_narrative/results/normalized/**`, `figures/**`, report draft | Score matrix, correlations, reversal cases |
| `experiment-reviewer` | Wave 3 | review files only | Methodology and artifact review |

## 9. Coordinator Runbook

### 9.1 Bootstrap

The coordinator should create:

```text
.codex-workflows/core-narrative-experiment/
  coordinator.md
  shared/
    experiment-brief.md
    worker-contract.md
  workers/
    repo-scout/
      prompt.md
      process.md
      run.sh
    schema-toolsmith/
      prompt.md
      process.md
      run.sh
    ...
```

`coordinator.md` should track:

- current phase;
- active tmux sessions;
- worker status table;
- worker branch and worktree table;
- blocker table;
- decisions made;
- next heartbeat action.

Before starting worker worktrees, the coordinator should record the base commit:

```bash
git rev-parse HEAD
```

Create or reuse one branch per worktree-backed worker. Example:

```bash
git worktree add ../barcarolle-wt-schema \
  -b codex/core-exp-schema-toolsmith
```

### 9.2 Codex CLI Invocation

Use this shape for each worker by default, replacing `WORKER_REPO` with the worker's assigned repo or worktree path:

```bash
codex exec \
  -C WORKER_REPO \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  - < .codex-workflows/core-narrative-experiment/workers/<worker>/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/<worker>/cli.log \
  2>&1
```

If the user explicitly approves YOLO-mode subprocesses for this experiment, use this shape instead:

```bash
codex exec \
  -C WORKER_REPO \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < .codex-workflows/core-narrative-experiment/workers/<worker>/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/<worker>/cli.log \
  2>&1
```

Start a worker:

```bash
tmux new-session -d -s bcx-<worker> \
  '.codex-workflows/core-narrative-experiment/workers/<worker>/run.sh'
```

Before starting, check for existing session names:

```bash
tmux list-sessions -F '#S'
```

### 9.3 Heartbeat Step

On each heartbeat, the coordinator should:

1. Read `.codex-workflows/core-narrative-experiment/coordinator.md`.
2. Read worker `process.md` files only.
3. Update the worker status table.
4. Start newly unblocked workers.
5. If a worker delivered an artifact that needs review, start the matching reviewer.
6. If a reviewer reports issues, write feedback into the owning worker directory and start a revision worker.
7. If all acceptance gates pass, close the workflow and notify the user.

Do not tail or inspect `cli.log` unless the user asks for debugging.

## 10. Phase Plan

### Phase 0: Experiment Bootstrap

Deliverables:

- Workflow folder.
- Shared experiment brief.
- Worker prompts.
- Main experiment branch.
- Dedicated worker worktrees for code, task, verifier, execution, and analysis workers.
- Initial committed experiment directories.

Acceptance gate:

- Coordinator can list all workers and owned paths.
- Coordinator can list worker branches and worktrees.
- No two workers have overlapping write ownership except through explicit review feedback files.
- `.gitignore` excludes workspaces, caches, cloned repositories, large artifacts, and CLI logs.

### Phase 1: Repository, ACUT, and General Benchmark Selection

Parallel workers:

- `repo-scout`
- `acut-matrix`
- `general-benchmark`
- `schema-toolsmith`

Deliverables:

- One primary target repository selected.
- ACUT matrix frozen.
- General benchmark basis frozen or fallback evidence basis recorded.
- LLM access contract recorded with `BARCAROLLE_LLM_API_KEY`, `BARCAROLLE_LLM_BASE_URL`, and the $300 hard cap.
- Minimal schemas and scripts drafted.

Acceptance gate:

- Target repository can be cloned and tested locally.
- ACUT manifests are complete enough to reproduce runs.
- General benchmark basis is explicit enough to avoid post-hoc cherry-picking.
- ACUT execution is blocked unless both LLM access environment variables are present and cost ledgering is implemented.

### Phase 2: Task Pack Construction

Parallel workers:

- `task-builder-<repo>`
- `verifier-auditor-<repo>`
- `leakage-auditor-<repo>`

Deliverables:

- 20 to 40 accepted `RBench` tasks.
- 10 to 20 accepted `RWork` tasks.
- For each task, no-op fails and reference patch passes.
- Leakage notes and admission status.

Acceptance gate:

- At least 20 `RBench` tasks and 10 `RWork` tasks pass audit.
- Any task with future patch leakage, unreplayable environment, or ambiguous verifier is excluded.
- ACUT workspaces cannot see `private/` artifacts.

### Phase 3: Runner Smoke Test

Run a small matrix:

- 2 ACUTs.
- 3 `RBench` tasks.
- 2 `RWork` tasks.

Deliverables:

- Raw run results.
- Normalized result JSON.
- Verification logs.
- Smoke-test summary.

Acceptance gate:

- Clean-room apply-and-verify works from a fresh checkout.
- Failure classes distinguish agent failure from infra failure.
- Results can be summarized without manual spreadsheet editing.
- Smoke runs write cost records to `experiments/core_narrative/results/cost_ledger.jsonl`.
- The coordinator records a measured or conservative estimated cost per ACUT/task before approving full execution.

### Phase 4: Full Experiment Run

Use the budget-constrained execution profile by default:

- 4 core ACUTs;
- 6 `G_score` tasks;
- 8 `RBench` tasks;
- 6 `RWork` tasks;
- 1 primary attempt per ACUT/task.

Parallelize cautiously by shard:

- shard by ACUT;
- or shard by task family;
- or shard by `RBench` and `RWork` split.

Deliverables:

- Complete raw result set for all ACUT x task attempts.
- General benchmark result basis.
- Repeat runs for close or surprising ranking-reversal candidates.

Acceptance gate:

- At least 80 percent of budget-constrained planned runs finish with scoreable outcomes.
- Infra failures are either rerun or excluded with explicit reason.
- Each claimed reversal has at least one repeated-run sanity check.
- LLM spend remains under the $300 hard cap.
- New ACUT patch-generation runs stop at the $240 soft stop unless the coordinator records why the remaining runs are necessary.

### Phase 5: Analysis and Report

Deliverables:

- `G_score`, `R_score`, and `W_score` table by ACUT.
- Rank correlation comparison.
- Bootstrap confidence intervals where sample size allows.
- Ranking reversal examples.
- Failure case studies with patches and verifier evidence.
- Threats to validity.
- Recommendation for whether to invest in productizing task generation and runner components.

Acceptance gate:

- The report can support or reject the core narrative without relying on hidden manual judgment.
- Any use of public leaderboard scores is clearly separated from directly-run scores.
- Limitations are explicit.

## 11. Analysis Rules

### 11.0 Default Score Definitions

Use these defaults unless the coordinator records a pre-result change:

- `G_score`: normalized pass rate on the selected general benchmark slice. If the basis is an external leaderboard value, mark it as `external_basis` and do not mix it with directly-run scores in the same statistical claim.
- `R_score`: scoreable pass rate on accepted `RBench` tasks. Exclude infra failures only when the exclusion reason is recorded and the task is rerun or marked unscoreable for all ACUTs.
- `W_score`: held-out repository work score. Prefer `0.7 * verifier_success_rate + 0.3 * blinded_mergeability_grade`, where mergeability grade is normalized from a 0 to 3 rubric. If blinded review is unavailable, report verifier success and review grade separately instead of inventing a blended score.

The reviewer rubric for `W_score` should grade only the submitted patch and public task context, not the ACUT identity:

- `0`: wrong or unusable.
- `1`: partially relevant but not mergeable.
- `2`: likely mergeable after modest maintainer edits.
- `3`: mergeable or very close to mergeable.

### 11.1 Primary Evidence

The strongest evidence is:

- Directly run `G_score` for the same ACUTs.
- Directly run `R_score` for the same ACUTs.
- Held-out `W_score` from disjoint repository work tasks.

Weaker evidence:

- Public leaderboard score for a similar but not identical ACUT.
- Human-only review without executable verifier.
- RBench and RWork tasks drawn from overlapping source anchors.

### 11.2 Reversal Criteria

A headline reversal should meet all of these:

- ACUT A beats B on `G_score` by a meaningful margin.
- ACUT B beats A on `R_score` by a meaningful margin.
- ACUT B beats A on `W_score` by a meaningful margin.
- The result survives at least one rerun or manual audit of the affected tasks.
- The explanation is grounded in repository-specific behavior, not just random failure.

Suggested initial thresholds:

- `G_score(A) - G_score(B) >= 0.10`
- `R_score(B) - R_score(A) >= 0.10`
- `W_score(B) - W_score(A) >= 0.10`

Adjust thresholds only before seeing final results, and record the reason.

### 11.3 Correlation Checks

Compute:

- Spearman correlation between `G_score` and `W_score`.
- Spearman correlation between `R_score` and `W_score`.
- Kendall rank agreement if ACUT count is small.
- Bootstrap confidence intervals across tasks when possible.

Do not overclaim statistical certainty with a small ACUT count. The first goal is a credible signal and concrete failure cases, not a publication-grade causal estimate.

## 12. Leakage and Validity Controls

Required controls:

- ACUT workspaces are checked out at base commit only.
- Future git history is not available to ACUTs.
- Target commit SHA and reference patch are hidden.
- Merged PR links and solution-bearing discussion are excluded from task statements.
- Network is disabled for ACUT runs when feasible.
- No worker that inspected private task artifacts should run as the evaluated ACUT for that task.
- All generated tasks carry admission notes.
- No-op and reference-patch validation are recorded.
- LLM credentials are supplied only through `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`.
- LLM credentials and raw authorization headers are redacted from all saved prompts, traces, logs, and run artifacts.
- ACUT execution workers must stop before making a model call if the cumulative projected LLM spend would exceed $300.

Threats to validity to report:

- Small number of repositories.
- Codex-assisted task construction bias.
- General benchmark score mismatch if public scores are used.
- Historical task replay may differ from real maintainer workflow.
- Verifiers may be weaker than maintainer judgment.
- ACUTs may have hidden training exposure to public repository history.
- The first executable run is budget-constrained to $300, so task and ACUT coverage is intentionally weak and should be treated as signal-finding rather than final evidence.

## 13. Prompt Templates

### 13.1 Coordinator Prompt

```text
You are the coordinator for the Barcarolle core narrative experiment.

Repo: /Users/chenmohan/gits/barcarolle
Plan: docs/experiments/core-narrative-experiment-plan.md
Workflow root: .codex-workflows/core-narrative-experiment

Execute the plan using tmux-managed Codex CLI workers. Do not read worker CLI logs unless debugging is explicitly requested. Coordinate only through coordinator.md and worker process.md files. Create disjoint worker ownership. Keep the experiment focused on validating the core narrative, not building the full Barcarolle platform.

First action:
1. Create or confirm the main experiment branch.
2. Create the workflow root and shared files.
3. Create dedicated worktrees for worktree-backed workers.
4. Create Wave 0 worker prompts for repo-scout, schema-toolsmith, acut-matrix, and general-benchmark.
5. Start Wave 0 workers in tmux.
6. Update coordinator.md with session names, branch/worktree paths, and next heartbeat action.
```

### 13.2 Worker Prompt Prefix

```text
You are a Codex CLI worker in the Barcarolle core narrative experiment.

Coordinator repo: /Users/chenmohan/gits/barcarolle
Worker repo: WORKER_REPO
Worker branch: WORKER_BRANCH
Plan: docs/experiments/core-narrative-experiment-plan.md
Workflow root: .codex-workflows/core-narrative-experiment

You are not alone in the codebase. Other workers may be editing different files and branches. Do not revert changes you did not make. Only edit your owned paths in your assigned worker repo. Update your process.md at start, after meaningful phases, and before exit. Include branch and worktree state in process.md. Mark status: delivered only when your assigned artifacts are complete and self-checked. If blocked, mark status: blocked and explain the exact blocker.
```

### 13.3 Reviewer Prompt Prefix

```text
You are a reviewer for one delivered workstream in the Barcarolle core narrative experiment.

Do not edit production artifacts. Inspect the delivered files and the worker process.md. Write your review into your assigned review file. Focus on experimental validity, reproducibility, leakage risk, broken artifact contracts, and missing handoff information. Do not object that the experiment is not the full Barcarolle platform; that is intentional.
```

## 14. Decision Points

After Phase 2, decide whether the repository is viable:

- Continue if there are at least 20 accepted `RBench` tasks and 10 accepted `RWork` tasks.
- Switch repositories if too many tasks are unreplayable or leaky.
- Add a second repository only if the first one works.

After Phase 3, decide whether the runner is viable:

- Continue if clean-room verification is reliable.
- Fix minimal tooling if results cannot be normalized.
- Stop platform work if smoke runs are dominated by infra failure.

After Phase 5, decide what to build next:

- If the narrative is supported, productize task generation, canonical verification, and ACUT snapshotting first.
- If signal is mixed, expand repositories and task families before building policy layers.
- If signal is absent, revisit the repository-specific task construction method before investing in authorization semantics.

## 15. Final Deliverables

The experiment is complete when these exist:

- Frozen ACUT manifests.
- Frozen general benchmark basis.
- LLM access manifest with credential environment variable names and budget policy.
- Frozen repository-specific `RBench` task pack.
- Frozen held-out `RWork` task pack.
- Raw and normalized run results.
- Cost ledger proving the run stayed within the $300 LLM cap.
- Git branches or commits for experiment code, schemas, manifests, and reports.
- External artifact manifests for any raw data too large or sensitive for Git.
- Analysis table with `G_score`, `R_score`, and `W_score`.
- Reversal case studies or a clear statement that no reversal was found.
- Threats-to-validity section.
- Recommendation for the next Barcarolle implementation slice.
