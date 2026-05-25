# Phase 1 Diff-Assisted Statement Regeneration Runbook

Status: corrected implementation runbook, 2026-05-25.

This runbook supersedes the previous diff-assisted statement-regeneration
runbook. The previous execution produced useful deterministic dry-run evidence,
but it did not satisfy the intended method: it did not start separate Codex CLI
generator and reviewer sessions. It used deterministic behavior overrides and
local review rules instead. That output must not be treated as evidence that
independent LLM-generated statements passed independent LLM review.

The corrected goal is narrow:

```text
Start real external Codex CLI generator and reviewer sessions, use them to
regenerate and review solver-facing statements from public context plus target
diff summaries, and only then rerun the statement-hardened screen.
```

If real Codex CLI generation/review cannot run, stop with a blocker. Do not
fall back to deterministic generation and call the task complete.

## Why This Runbook Exists

The statement-quality audit and preregistration attempt showed that the old
statement renderer was too brittle:

```text
old behavior:
  public body_summary was often hard-cut at 240 characters

observed consequence:
  code fences and reproductions were cut mid-stream
  expected behavior was sometimes omitted
  API intent could look under-specified

correct interpretation:
  old statement renderer is defective
  old candidate tasks are not automatically invalid
```

The first diff-assisted regeneration run confirmed one useful local point:
deterministic sidecar logic can make many old candidates look recoverable.
But because it did not run the generator/reviewer Codex CLI loop, it does not
answer the research question this runbook is meant to answer.

## Prior Run Result To Reinterpret

The previous run produced:

```text
candidate packets built: 22
regenerated statements reviewed: 22
review pass/reject: 19 / 3
eligible before regeneration: 4
eligible after regeneration: 19
remaining missing supply: boltons/H_future
paid LLM calls made: false
Codex CLI generator/reviewer sessions: not launched
```

Interpretation:

```text
valid as:
  deterministic dry-run and tooling prototype
  evidence that 240-character truncation was over-penalizing candidates
  evidence that the current inventory has no boltons H_future supply

not valid as:
  independent generated statement evidence
  independent leakage/sufficiency review evidence
  basis for freezing a statement-hardened release
  basis for paid validation
```

This corrected runbook should preserve those artifacts as historical dry-run
context, but must write new outputs under corrected names.

## Starting Point

Important inputs:

```text
experiments/phase1_compiler/reports/phase1_diff_assisted_statement_regeneration_process.md
experiments/phase1_compiler/reports/phase1_diff_assisted_statement_reviews.md
experiments/phase1_compiler/reports/phase1_diff_assisted_statement_screen.md
experiments/phase1_compiler/reports/phase1_diff_assisted_recovery_decision.md
experiments/phase1_compiler/results/phase1_diff_assisted_candidate_packets.json
experiments/phase1_compiler/results/phase1_statement_hardened_candidate_inventory.json
experiments/phase1_compiler/results/phase1_statement_hardened_candidate_screen.json
```

The corrected run must not overwrite the previous deterministic outputs. Use a
new result prefix:

```text
phase1_diff_assisted_codex_loop_*
```

The proposal in `barcarolle-research-0519.md`
allows compiler-side use of repository history. Therefore target diff summaries
may be used by the statement generator, as long as the final solver-visible
statement is independently reviewed for answer leakage.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing <repo>/docs/experiments/phase-1-diff-assisted-statement-regeneration-runbook.md.

Work in <repo>. Use uv for repo-local Python tooling.
Make a cohesive git commit after every completed step that changes files. Do
not batch unrelated steps into one commit. If a step has no file changes, record
that fact in the process report and do not create an empty commit. Do not push
unless the user explicitly asks.

Main goal: run a real external Codex CLI generator/reviewer loop for
diff-assisted statement regeneration. The previous deterministic dry-run did
not satisfy this requirement. This run must start separate generator and
reviewer Codex CLI sessions, coordinate them through process.md and sanitized
handoff files, and record proof that the external sessions ran.

Paid ACUT solver cells remain disabled. For this runbook only, the user has
explicitly overridden the repo-wide LLM endpoint rule for statement
generation/review: the generator and reviewer Codex CLI sessions must use the
user's local Codex Subscription, not LLM_BASE_URL / LLM_API_KEY and not any
other provider API key. The run scripts must avoid passing API endpoint
environment variables to Codex CLI. If local Codex Subscription execution or
Codex CLI availability fails, stop before generation and write a blocker.

Do not use deterministic behavior overrides as a substitute for Codex CLI
generation. Deterministic helpers may build candidate packets, validate output
schemas, run leakage checks, and screen reviewed statements. They may not
generate final statements or reviewer verdicts for this corrected run.

Do not run solver ACUT cells. Do not rerun existing scoreable cells. Do not
rerun the confirmed attrs__hist__027 policy violation. Do not rewrite historical
score tables. Regenerated statements and review verdicts are new sidecar
artifacts only.

Do not commit secrets, raw prompts, raw completions, raw Codex CLI logs, raw
ACUT transcripts, raw GitHub API responses, solver workspaces, verifier
workspaces, cloned external repositories, .venv, caches, raw patch bodies, full
public issue/PR bodies, raw target diffs, or large raw outputs. Commit only
small sanitized configs, prompt templates, candidate packets, generated
statements, statement digests, review verdicts, summaries, reports, and
process-file summaries.

The final user-facing summary should be simple Chinese. It must say whether the
real Codex CLI generator/reviewer loop ran, how many statements passed, and
whether the old candidate pool is actually recovered or still needs targeted
replacement supply.
```

## Non-Negotiable Requirements

The run is valid only if all are true:

```text
real_generator_codex_cli_session_started: true
real_reviewer_codex_cli_session_started: true
generator_reviewer_used_local_codex_subscription: true
generator_reviewer_did_not_use_llm_api_endpoint: true
generator_process_file_present: true
reviewer_process_file_present: true
generator_output_not_deterministic_override: true
reviewer_output_not_deterministic_rules_only: true
raw_cli_logs_not_committed: true
paid_acut_solver_cells_run: false
historical_paid_outcomes_used_for_generation_or_review: false
```

If any of these is false, the primary decision must be:

```text
blocked_real_codex_loop_not_completed
```

Do not report recovered candidates from deterministic fallback as a successful
run.

## Claim Boundary

Allowed claims:

```text
real_codex_generator_reviewer_loop_completed
codex_generated_statement_review_passed
codex_reviewed_statement_non_leaky
codex_reviewed_statement_sufficient
old_candidate_pool_recovered_by_real_codex_loop
partial_recovery_after_real_codex_loop
targeted_replacement_supply_needed
codex_loop_blocked_before_generation
```

Disallowed claims:

```text
predictive_validity_established
production_benchmark_ranking
old_paid_result_repaired
attrs_policy_violation_repaired
deterministic_dry_run_counts_as_codex_review
generated_statement_is_scoreable_result
hidden_oracle_informed_statement
paid_validation_completed
solver_performance_improved
```

## Subscription And Budget Rules

This runbook uses the user's local Codex Subscription for statement
generation/review. It does not use LLM_BASE_URL / LLM_API_KEY, OpenAI API keys,
OpenRouter keys, or provider-specific API endpoints for generator/reviewer
sessions. It does not allow paid ACUT solver validation.

```text
paid ACUT calls: disabled
paid solver cells: disabled
Codex Subscription generation/review: conditionally enabled
LLM API endpoint for generator/reviewer: disabled by explicit user override
model: gpt-5.5 unless repo config requires otherwise
reasoning effort: xhigh
max generator/reviewer iterations per batch: 3
max generator sessions per batch: 3
max reviewer sessions per batch: 3
```

Before starting Codex CLI:

```bash
command -v codex
command -v tmux
```

The run scripts must invoke Codex CLI with API endpoint variables removed, for
example:

```bash
env -u LLM_BASE_URL -u LLM_API_KEY -u OPENAI_API_KEY -u OPENROUTER_API_KEY \
  codex exec ...
```

Record only booleans about local subscription execution. Do not commit account
tokens, auth files, API keys, or raw CLI logs.

## Work-Review Loop Contract

Use the local Codex CLI work/review pattern. Create:

```text
.codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/
  coordinator.md
  generator/
    prompt.md
    process.md
    run_generator.sh
    output/
      generated_statements.jsonl
  reviewer/
    prompt.md
    process.md
    run_reviewer.sh
    review-to-generator.md
    output/
      statement_reviews.json
```

The workflow folder may contain raw logs, but raw logs must be ignored and not
committed. Coordination must use `process.md` and sanitized output files, not
stdout/stderr logs.

Start the generator with a real tmux session, for example:

```bash
tmux new-session -d -s phase1-diffstmt-generator \
  '.codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/generator/run_generator.sh'
```

After generator `process.md` reports `status: delivered`, start reviewer:

```bash
tmux new-session -d -s phase1-diffstmt-reviewer \
  '.codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/reviewer/run_reviewer.sh'
```

If reviewer returns `revise`, start a generator revision session. Maximum 3
generator/reviewer cycles per batch.

Required shell script shape:

```bash
env -u LLM_BASE_URL -u LLM_API_KEY -u OPENAI_API_KEY -u OPENROUTER_API_KEY \
codex exec \
  -C <repo> \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < .codex-workflows/.../generator/prompt.md \
  > .codex-workflows/.../generator/cli.log \
  2>&1
```

The run may use separate per-batch sessions instead of one large batch if that
is safer. It must still record generator/reviewer process files and session
proof.

## Generator Input Rules

Generator input may include:

```text
task_id
repo_id
task_time
source_ref
public issue/PR title
sanitized public issue/PR body excerpt
changed file list
implementation-file list
test-file names
module/package
certification gate summary
old statement-quality flags
target diff summary
target diff digest
test diff digest
small implementation diff excerpts only if needed and sanitized
test diff summary without raw assertions
scope boundaries
verifier command metadata
```

Generator input must exclude:

```text
historical paid outcomes
terminal statuses
solver transcripts
hidden verifier material
full raw public issue/PR bodies in committed artifacts
raw target diff as statement text
raw test assertions
secrets
```

Generator output must include one JSONL row per candidate:

```json
{
  "task_id": "...",
  "statement": "...",
  "statement_digest": "sha256:...",
  "generation_notes": "...",
  "used_diff_summary": true,
  "contains_raw_diff": false,
  "contains_paid_outcome": false
}
```

## Reviewer Contract

Reviewer input:

```text
same sanitized candidate packets
generated statement JSONL
review rubric
```

Reviewer must not edit generated statements. It writes review verdicts only.

Reviewer output schema:

```json
{
  "task_id": "...",
  "status": "pass | revise | reject",
  "leakage_pass": true,
  "sufficiency_pass": true,
  "faithfulness_pass": true,
  "scope_pass": true,
  "formatting_pass": true,
  "reasons": ["..."],
  "required_revision": "..."
}
```

Reviewer checks:

```text
leakage:
  no gold patch text
  no raw diff hunks
  no exact implementation recipe
  no hidden verifier content
  no raw test assertions
  no paid outcome/status
  no target commit hash

sufficiency:
  problem summary is clear
  expected public behavior is clear
  reproduction or behavior description is complete
  code fences are closed
  no mid-sentence truncation
  editable scope is implementation-only
  statement is faithful to public context and diff summary
  statement can be attempted without hidden tests

length:
  target: 1500-2500 characters
  soft max: 4000 characters
  never substring-truncate
```

## Output Layout

Use corrected names:

```text
experiments/phase1_compiler/
  configs/
    phase1_diff_assisted_codex_loop_statement_regeneration.yaml
  tools/
    phase1_diff_assisted_codex_loop_statement_regeneration.py
  tests/
    test_phase1_diff_assisted_codex_loop_statement_regeneration.py
  results/
    phase1_diff_assisted_codex_loop_preflight.json
    phase1_diff_assisted_codex_loop_candidate_packets.json
    phase1_diff_assisted_codex_loop_generation_plan.json
    phase1_diff_assisted_codex_loop_session_proof.json
    phase1_diff_assisted_codex_loop_generated_statements.jsonl
    phase1_diff_assisted_codex_loop_statement_reviews.json
    phase1_diff_assisted_codex_loop_deterministic_qa.json
    phase1_diff_assisted_codex_loop_statement_screen.json
    phase1_diff_assisted_codex_loop_recovery_decision.json
  reports/
    phase1_diff_assisted_codex_loop_process.md
    phase1_diff_assisted_codex_loop_session_proof.md
    phase1_diff_assisted_codex_loop_statement_reviews.md
    phase1_diff_assisted_codex_loop_statement_screen.md
    phase1_diff_assisted_codex_loop_recovery_decision.md
```

Do not overwrite prior deterministic dry-run outputs:

```text
phase1_diff_assisted_statement_*
```

## Step 0: Preflight And Prior Result Reinterpretation

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, git status, and
   existing unrelated paths.
2. Read prior deterministic dry-run artifacts and explicitly classify them as
   dry-run/prototype evidence, not real Codex loop evidence.
3. Check local Codex CLI and tmux availability:

```bash
command -v codex
command -v tmux
```

4. Verify the generated `run_generator.sh` and `run_reviewer.sh` scripts will
   unset API endpoint variables before invoking `codex exec`.

5. Write:

```text
experiments/phase1_compiler/configs/phase1_diff_assisted_codex_loop_statement_regeneration.yaml
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_preflight.json
experiments/phase1_compiler/reports/phase1_diff_assisted_codex_loop_process.md
```

Acceptance:

- Preflight explicitly says whether real local Codex Subscription
  generation/review can start.
- Preflight records that LLM API endpoint variables will not be used for
  generator/reviewer sessions.
- If Codex CLI, tmux, or local subscription execution is blocked, stop and
  write blocker decision.
- Prior deterministic results are not reported as successful loop output.

Commit:

```text
Record diff-assisted Codex loop preflight
```

## Step 1: Build Sanitized Candidate Packets

Actions:

1. Add or update corrected tooling:

```text
experiments/phase1_compiler/tools/phase1_diff_assisted_codex_loop_statement_regeneration.py
experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py
```

2. Build candidate packets from existing inventory and certified/source-context
   artifacts.
3. Include diff summaries and digests, not raw target diff as committed output.
4. Write:

```text
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_candidate_packets.json
```

Acceptance:

- Packets contain no paid outcomes, terminal statuses, raw test assertions, raw
  diff markers, secrets, or hidden verifier material.
- Tests verify forbidden fields are stripped.

Verification:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py
```

Commit:

```text
Build diff-assisted Codex loop candidate packets
```

## Step 2: Create Workflow Files And Prompt Templates

Actions:

1. Create `.codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/`.
2. Write sanitized prompt templates and process files:

```text
coordinator.md
generator/prompt.md
generator/process.md
generator/run_generator.sh
reviewer/prompt.md
reviewer/process.md
reviewer/run_reviewer.sh
```

3. Write a generation plan:

```text
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_generation_plan.json
```

Acceptance:

- `run_generator.sh` and `run_reviewer.sh` invoke `codex exec` through `env -u`
  for LLM/API endpoint variables.
- Prompts do not contain paid outcomes or raw diffs.
- Process files start with `status: pending`.
- Raw logs are directed to ignored `.codex-workflows/.../*.log`.

Commit:

```text
Create diff-assisted Codex generator reviewer workflow
```

## Step 3: Start And Complete Generator Session

Actions:

1. Start the generator in tmux.
2. Record session start metadata in:

```text
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_session_proof.json
```

3. Wait by checking only `generator/process.md`, not CLI logs.
4. If generator blocks or fails, write blocker and stop.
5. When delivered, copy sanitized generator output to:

```text
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_generated_statements.jsonl
```

Acceptance:

- `generator/process.md` reports `status: delivered`.
- Session proof records tmux session name, command shape, start/end timestamps,
  and output row count.
- Generated statements are not produced by deterministic local behavior
  overrides.
- Raw CLI logs are not committed.

Commit:

```text
Run real Codex statement generator session
```

## Step 4: Start And Complete Reviewer Session

Actions:

1. Start reviewer in a separate tmux session only after generator delivery.
2. Reviewer reads sanitized packets and generated statements.
3. Reviewer writes:

```text
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_statement_reviews.json
experiments/phase1_compiler/reports/phase1_diff_assisted_codex_loop_statement_reviews.md
```

4. If reviewer requests revision, start generator revision session. Record
   revision sessions in session proof. Maximum 3 cycles per batch.

Acceptance:

- `reviewer/process.md` reports `status: delivered`.
- Reviewer verdicts are generated by the real reviewer Codex CLI session.
- Every generated statement has a review verdict.
- `pass` verdicts include leakage, sufficiency, faithfulness, scope, and
  formatting checks.

Commit:

```text
Run real Codex statement reviewer session
```

## Step 5: Deterministic QA As A Guardrail Only

Actions:

1. Run deterministic QA over reviewer-approved statements.
2. Deterministic QA may reject or require revision; it may not create pass
   verdicts without reviewer pass.
3. Write:

```text
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_deterministic_qa.json
```

Acceptance:

- QA rejects raw diff markers, target commit hashes, hidden verifier text, paid
  statuses, unclosed code fences, and non-implementation editable paths.
- QA reports old 240-character truncation as recoverable only when regenerated
  statement plus reviewer verdict pass.

Commit:

```text
Run deterministic QA for Codex-reviewed statements
```

## Step 6: Rerun Statement-Hardened Screen

Actions:

1. Rerun the statement-hardened screen using only statements that have:

```text
real reviewer status: pass
deterministic QA status: pass
```

2. Do not use paid outcomes for selection.
3. Write:

```text
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_statement_screen.json
experiments/phase1_compiler/reports/phase1_diff_assisted_codex_loop_statement_screen.md
```

Acceptance:

- Screen includes before/after eligible counts.
- Screen separates real reviewer failures, deterministic QA failures, and true
  supply holes.
- If boltons/H_future remains empty because the old inventory contains no
  boltons H_future candidates, say that clearly.

Commit:

```text
Screen Codex-reviewed regenerated statements
```

## Step 7: Decide Recovery Branch

Actions:

1. Write:

```text
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_recovery_decision.json
experiments/phase1_compiler/reports/phase1_diff_assisted_codex_loop_recovery_decision.md
```

2. Choose exactly one:

```text
old_candidate_pool_recovered_retry_preregistration:
  Real Codex loop recovered enough candidates for a new preregistration.

partial_recovery_mine_targeted_replacement_supply:
  Real Codex loop recovered some candidates but left specific repo/split holes.

blocked_real_codex_loop_not_completed:
  Generator/reviewer Codex CLI sessions did not complete.

regeneration_failed_old_pool_not_recoverable:
  Real Codex loop completed but most candidates remained leaky, unfaithful, or
  insufficient.
```

3. Draft the exact next runbook:

```text
docs/experiments/phase-1-statement-hardened-preregistration-after-codex-loop-runbook.md
```

or:

```text
docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md
```

Acceptance:

- The decision cannot cite deterministic dry-run results as loop success.
- The decision states whether real generator/reviewer sessions ran.
- The decision states whether replacement supply is still needed.

Commit:

```text
Decide diff-assisted Codex loop recovery branch
```

## Step 8: Closeout

Actions:

1. Update:

```text
experiments/phase1_compiler/reports/phase1_diff_assisted_codex_loop_process.md
```

with:

```text
steps completed
commits created
tests run
LLM API calls made for generator/reviewer: false
Codex Subscription sessions used: true/false
LLM API endpoint used for generator/reviewer: false
paid ACUT calls made: false
real generator session completed: true/false
real reviewer session completed: true/false
raw artifacts committed: false
review pass/revise/reject counts
old pool recovered: true/false/partial
next runbook path
```

2. Run:

```bash
git diff --check
git status --short
```

3. Commit the closeout update if it changes files.

Acceptance:

- No paid ACUT calls were made.
- No raw prompts, completions, logs, or raw diffs were committed.
- Final process report is consistent with session proof and decision artifacts.

Commit:

```text
Record diff-assisted Codex loop closeout
```

## Verification Commands

At minimum:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py

uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_diff_assisted_statement_regeneration.py \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py \
  experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py \
  experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py \
  experiments/phase0_headroom/tools/test_workspace_acut_run.py

git diff --check
```

## Final Response Template

Use simple Chinese:

```text
这轮 runbook 完成后的结论：

1. generator/reviewer 两个 Codex CLI session 是否真的启动并完成。
2. 通过 real reviewer 和 deterministic QA 的题面有多少。
3. 旧候选池是否真正恢复，还是还需要定向补 supply。

不要说 deterministic dry-run 是 Codex loop。
不要说旧 paid 结果被修好了。
不要说 predictive validity 已经建立。
```
