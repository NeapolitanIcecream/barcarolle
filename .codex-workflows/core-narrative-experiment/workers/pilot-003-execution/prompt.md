# Pilot 003 Bounded 2x2 Execution Attempt

You are the third bounded execution worker for the Barcarolle core narrative
experiment.

Worktree:

`/Users/chenmohan/gits/barcarolle-wt-pilot-003-execution`

Branch:

`codex/core-exp-pilot-003-execution`

## Coordinator Authorization

The coordinator recorded explicit execution start for exactly one primary
attempt:

- run_id: `pilot_003__cheap-generic-swe__click__rbench__003__attempt1`
- ACUT: `cheap-generic-swe`
- task: `click__rbench__003`
- split: `rbench`
- attempt: `1`
- model route: `openai/gpt-5.4-mini`
- projected cost: USD `3.00`
- projected cumulative cost: USD `9.0008`

No other model-call attempts are authorized. This is not a retry of
`pilot_001` or `pilot_002`. Broad ACUT execution, large batches, specialist
ACUT runs, retries, and second attempts are not authorized.

## Hard Constraints

- Do not inspect any `cli.log` file.
- Use only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` for live LLM
  access. Do not record their values, bearer tokens, resolved secrets,
  hostnames, IP addresses, or full base URL values anywhere.
- Run the live patch-generation attempt only through
  `experiments/core_narrative/tools/acut_patch_adapter.py` with the reviewed
  custom `experiments/core_narrative/tools/barcarolle_patch_command.py` after
  `--`.
- Do not use bare `codex exec` as the ACUT patch-generation command.
- If either required env var is missing, if
  `experiments/core_narrative/results/cost_ledger.jsonl` is missing or
  unwritable, or if any budget gate blocks, set `status: blocked` in
  `process.md` and do not run the live command.
- Keep all writes inside the owned paths listed in `process.md`.

## Inputs

- Coordinator: `.codex-workflows/core-narrative-experiment/coordinator.md`
- Run manifest: `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- LLM access contract: `experiments/core_narrative/configs/llm_access.yaml`
- Task manifest: `experiments/core_narrative/tasks/click/rbench/click__rbench__003/task.yaml`
- ACUT manifest: `experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml`
- Source repo cache: `experiments/core_narrative/external_repos/click`

## Required Execution Shape

Use these paths:

```bash
RUN_ID="pilot_003__cheap-generic-swe__click__rbench__003__attempt1"
WORKSPACE="experiments/core_narrative/workspaces/${RUN_ID}"
TASK="experiments/core_narrative/tasks/click/rbench/click__rbench__003/task.yaml"
ACUT="experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml"
ARTIFACT_DIR="experiments/core_narrative/results/raw/${RUN_ID}"
NORMALIZED="experiments/core_narrative/results/normalized/${RUN_ID}.json"
LEDGER="experiments/core_narrative/results/cost_ledger.jsonl"
```

1. Update `process.md` before meaningful phases.
2. Confirm required env var presence without printing or recording values.
3. Confirm the ACUT manifest uses model route `openai/gpt-5.4-mini`.
4. Confirm the cost ledger exists, parses as JSONL, is writable, and that the
   projected cumulative estimated cost stays below the USD `240` soft stop and
   USD `300` hard cap.
5. If the worktree-local source cache is missing, restore it from the sibling
   local checkout at
   `/Users/chenmohan/gits/barcarolle/experiments/core_narrative/external_repos/click`.
   Do not fetch from the network unless you first mark `process.md` blocked and
   explain why the local cache cannot be used.
6. Prepare a fresh workspace:

```bash
python3 experiments/core_narrative/tools/prepare_workspace.py \
  --task "$TASK" \
  --source-repo experiments/core_narrative/external_repos/click \
  --workspace "$WORKSPACE" \
  --force \
  --output "$ARTIFACT_DIR/prepare_workspace.json"
```

7. Run a no-model dry run of the patch command to estimate prompt size. Store
   the summary under the raw artifact directory. Estimate input tokens from
   prompt characters (`ceil(char_count / 4)`) and use a conservative output
   budget of `64000` tokens unless you record a tighter value before the live
   call.
8. Run exactly one live adapter attempt:

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
  --coordinator-decision-ref ".codex-workflows/core-narrative-experiment/coordinator.md#pilot-003-decision" \
  --timeout-seconds 1200 \
  -- \
  python3 /Users/chenmohan/gits/barcarolle-wt-pilot-003-execution/experiments/core_narrative/tools/barcarolle_patch_command.py \
    --acut /Users/chenmohan/gits/barcarolle-wt-pilot-003-execution/experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml \
    --summary-output /Users/chenmohan/gits/barcarolle-wt-pilot-003-execution/experiments/core_narrative/results/raw/pilot_003__cheap-generic-swe__click__rbench__003__attempt1/patch_command_summary.json
```

9. If the adapter produces an applied patch, run the task verifier once on the
   patched workspace using `apply_and_verify.py --skip-apply` and write the
   normalized result to `$NORMALIZED`. If the adapter fails before a patch is
   available, preserve the adapter artifacts and write the failure clearly in
   `process.md`; do not retry.
10. Parse JSON/JSONL artifacts enough to confirm they are valid and that the
    cost ledger appended a record for this run id.
11. Run a scoped scan of the new owned artifacts for credential-looking
    values, bearer tokens, resolved required env values, full URLs, hostnames,
    and IP addresses without printing any secret values.
12. Commit only owned paths.

## Process Handoff

When complete, set `status: delivered` in `process.md` even if the ACUT failed
to solve the task; a completed one-attempt result is still a delivered attempt.
Use `status: blocked` only for environment, ledger, budget, or infrastructure
conditions that prevented the authorized attempt from running. Include:

- whether the adapter command ran;
- whether a live model call was attempted;
- ledger append status and cumulative estimated cost if available;
- artifact paths;
- verifier status if run;
- confirmation that no `cli.log` was inspected;
- confirmation that no broad execution, retries, second attempts, specialist
  ACUT runs, or large batches happened.
