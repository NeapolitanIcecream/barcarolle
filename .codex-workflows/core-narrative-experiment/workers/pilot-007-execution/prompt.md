# Pilot 007 Bounded Recovery Execution Attempt

You are the seventh bounded execution worker for the Barcarolle core narrative
experiment.

Worktree:

`/Users/chenmohan/gits/barcarolle-wt-pilot-007-execution`

Branch:

`codex/core-exp-pilot-007-execution`

## Coordinator Authorization

Before making any live BARCAROLLE model call, confirm that the coordinator has
recorded explicit execution start for exactly one bounded recovery candidate:

- run_id: `pilot_007__cheap-generic-swe__click__rbench__001__attempt1`
- ACUT: `cheap-generic-swe`
- task: `click__rbench__001`
- split: `rbench`
- attempt: `1`
- model route: `openai/gpt-5.4-mini`
- projected cost: USD `3.00`
- projected cumulative cost: USD `21.0008`
- harness: reviewed Codex CLI inner patch command via `acut_patch_adapter.py`
- specialist context pack: excluded for generic ACUT
- empty-patch gate: reviewed and integrated
- failure-capture gate: reviewed and integrated
- nonzero-exit normalization gate: reviewed and integrated

No other model-call attempts are authorized. This is a single recovery
candidate for the prior non-scorable pilot 001 generic attempt after reviewed
route, Codex CLI harness, failure-capture, and nonzero-exit normalization
repairs. It is not broad ACUT execution and does not authorize any retry,
second attempt, additional specialist ACUT run, further pilot attempt, or large
batch.

## Hard Constraints

- Do not inspect any `cli.log` file.
- Use only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` for live LLM
  access. Do not record their values, bearer tokens, resolved secrets,
  hostnames, IP addresses, or full base URL values anywhere.
- Run the live patch-generation attempt only through
  `experiments/core_narrative/tools/acut_patch_adapter.py` with the reviewed
  `experiments/core_narrative/tools/codex_cli_patch_command.py` after `--`.
- Do not use `barcarolle_patch_command.py` for this attempt.
- Do not use bare `codex exec` outside the reviewed adapter command path.
- If either required env var is missing, if
  `experiments/core_narrative/results/cost_ledger.jsonl` is missing or
  unwritable, if the reviewed empty-patch gate is absent, if the reviewed
  failure-capture gate is absent, if the reviewed nonzero-exit normalization
  gate is absent, or if any budget gate blocks, set `status: blocked` in
  `process.md` and do not run the live command.
- Keep all writes inside the owned paths listed in `process.md`.

## Inputs

- Coordinator: `.codex-workflows/core-narrative-experiment/coordinator.md`
- Run manifest: `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- LLM access contract: `experiments/core_narrative/configs/llm_access.yaml`
- Task manifest: `experiments/core_narrative/tasks/click/rbench/click__rbench__001/task.yaml`
- ACUT manifest: `experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml`
- Source repo cache: `experiments/core_narrative/external_repos/click`

## Required Execution Shape

Use these paths:

```bash
RUN_ID="pilot_007__cheap-generic-swe__click__rbench__001__attempt1"
WORKSPACE="experiments/core_narrative/workspaces/${RUN_ID}"
TASK="experiments/core_narrative/tasks/click/rbench/click__rbench__001/task.yaml"
ACUT="experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml"
ARTIFACT_DIR="experiments/core_narrative/results/raw/${RUN_ID}"
NORMALIZED="experiments/core_narrative/results/normalized/${RUN_ID}.json"
LEDGER="experiments/core_narrative/results/cost_ledger.jsonl"
```

1. Update `process.md` before meaningful phases.
2. Confirm required env var presence without printing or recording values.
3. Confirm the coordinator records explicit execution start for this exact run
   id and that the ACUT manifest uses model route `openai/gpt-5.4-mini`.
4. Confirm the generic ACUT does not enable the Click specialist context pack.
5. Confirm the reviewed empty-patch gate is present: an exit-0 empty patch is
   `no_patch_generated` / normalized `infra_failed`, and unsafe patch rejection
   remains distinct without `no_patch_generated` metadata.
6. Confirm the reviewed failure-capture gate is present: nonzero exits,
   timeouts, unsafe patch content, and exit-zero no-workspace-patch outcomes
   write structured redacted failure metadata without credential values, bearer
   tokens, full URLs, hostnames, or IP address-shaped values.
7. Confirm the reviewed nonzero-exit normalization gate is present:
   non-timeout nonzero inner-command failures with no verifier-ready patch
   write normalized `infra_failed` while raw adapter status and ledger event
   remain `command_failed`.
8. Confirm the cost ledger exists, parses as JSONL, is writable, and that the
   projected cumulative estimated cost stays below the USD `240` soft stop and
   USD `300` hard cap.
9. If the worktree-local source cache is missing, restore it from the sibling
   local checkout at
   `/Users/chenmohan/gits/barcarolle/experiments/core_narrative/external_repos/click`.
   Do not fetch from the network unless you first mark `process.md` blocked and
   explain why the local cache cannot be used.
10. Prepare a fresh workspace:

```bash
python3 experiments/core_narrative/tools/prepare_workspace.py \
  --task "$TASK" \
  --source-repo experiments/core_narrative/external_repos/click \
  --workspace "$WORKSPACE" \
  --force \
  --output "$ARTIFACT_DIR/prepare_workspace.json"
```

11. Run a no-model dry run of the reviewed Codex CLI patch command to estimate
    prompt size and confirm generic context behavior. Store the summary under
    the raw artifact directory. Estimate input tokens from prompt characters
    (`ceil(char_count / 4)`) and use a conservative output budget of `64000`
    tokens unless you record a tighter value before the live call.

```bash
python3 experiments/core_narrative/tools/codex_cli_patch_command.py \
  --workspace "$WORKSPACE" \
  --acut "$ACUT" \
  --artifact-dir "$ARTIFACT_DIR/inner_dry_run" \
  --summary-output "$ARTIFACT_DIR/codex_cli_patch_command_dry_run.json" \
  --dry-run
```

12. Confirm the dry-run summary records no model call and does not inject the
    Click specialist context pack for this generic ACUT.
13. Run exactly one live adapter attempt:

```bash
python3 experiments/core_narrative/tools/acut_patch_adapter.py \
  --workspace "$WORKSPACE" \
  --task "$TASK" \
  --acut "$ACUT" \
  --attempt 1 \
  --run-id "$RUN_ID" \
  --artifact-dir "$ARTIFACT_DIR" \
  --output "$ARTIFACT_DIR/adapter_result.json" \
  --normalized-output "$NORMALIZED" \
  --llm-ledger "$LEDGER" \
  --projected-cost-usd 3.00 \
  --input-tokens "<estimated-input-tokens>" \
  --output-tokens "<estimated-or-budgeted-output-tokens>" \
  --coordinator-decision-ref ".codex-workflows/core-narrative-experiment/coordinator.md#pilot-007-decision" \
  --timeout-seconds 1200 \
  -- \
  python3 /Users/chenmohan/gits/barcarolle-wt-pilot-007-execution/experiments/core_narrative/tools/codex_cli_patch_command.py \
    --acut /Users/chenmohan/gits/barcarolle-wt-pilot-007-execution/experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml \
    --artifact-dir /Users/chenmohan/gits/barcarolle-wt-pilot-007-execution/experiments/core_narrative/results/raw/pilot_007__cheap-generic-swe__click__rbench__001__attempt1/inner \
    --summary-output /Users/chenmohan/gits/barcarolle-wt-pilot-007-execution/experiments/core_narrative/results/raw/pilot_007__cheap-generic-swe__click__rbench__001__attempt1/codex_cli_patch_command.json \
    --codex-timeout-seconds 900
```

14. If the adapter produces an applied patch, run the task verifier once on the
    patched workspace using `apply_and_verify.py --skip-apply` and write the
    normalized result to `$NORMALIZED`. If the adapter fails before a patch is
    available, preserve the adapter artifacts and normalized failure output; do
    not retry.
15. Parse JSON/JSONL artifacts enough to confirm they are valid and that the
    cost ledger appended a record for this run id if the live model-call gate
    was reached.
16. Run a scoped scan of the new owned artifacts for credential-looking values,
    bearer tokens, resolved required env values, full URLs, hostnames, and IP
    addresses without printing any secret values.
17. Commit only owned paths.

## Process Handoff

When complete, set `status: delivered` in `process.md` even if the ACUT failed
to solve the task; a completed one-attempt result is still a delivered attempt.
Use `status: blocked` only for environment, ledger, budget, reviewed-command,
reviewed-gate, or infrastructure conditions that prevented the authorized
attempt from running. Include:

- whether the adapter command ran;
- whether a live model call was attempted;
- whether the Codex CLI specialist context pack was excluded for the generic
  ACUT;
- whether structured `failure_capture` metadata was present if the inner Codex
  CLI command failed;
- ledger append status and cumulative estimated cost if available;
- artifact paths;
- verifier status if run;
- confirmation that no `cli.log` was inspected;
- confirmation that no broad execution, retries beyond this single recovery
  candidate, second attempts, additional specialist ACUT runs, further pilot
  attempts, or large batches happened.
