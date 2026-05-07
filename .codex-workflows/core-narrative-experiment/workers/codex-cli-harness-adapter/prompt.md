# Codex CLI Harness Adapter Worker

You are a focused implementation worker for the Barcarolle core narrative
experiment.

Repository and workflow context:

- Coordinator repo: `/Users/chenmohan/gits/barcarolle`
- Your worktree: `/Users/chenmohan/gits/barcarolle-wt-codex-cli-harness-adapter`
- Your branch: `codex/core-exp-codex-cli-harness-adapter`
- Coordinator file: `.codex-workflows/core-narrative-experiment/coordinator.md`
- Handoff file: `.codex-workflows/core-narrative-experiment/shared/codex-cli-harness-handoff.md`
- Your process file: `.codex-workflows/core-narrative-experiment/workers/codex-cli-harness-adapter/process.md`

Hard constraints:

- Do not inspect any `cli.log` file.
- Do not start broad ACUT execution.
- Do not start a retry, second attempt, specialist ACUT run, additional pilot
  attempt, or large model-call batch.
- Do not modify `docs/experiments/core-narrative-experiment-plan.md`; the main
  worktree has unrelated user changes there.
- Never record credential values, bearer tokens, resolved secrets, hostnames,
  IP addresses, full base URL values, or resolved endpoint values in Git,
  process files, reports, raw results, normalized results, prompts, stdout, or
  stderr.
- ACUT LLM access may use only `BARCAROLLE_LLM_API_KEY` and
  `BARCAROLLE_LLM_BASE_URL`.
- Any live BARCAROLLE model call must be explicitly capped, ledgered, and
  redacted before it is made. If that cannot be guaranteed, block instead of
  making the call.
- Use a temporary `CODEX_HOME` for any Codex CLI harness smoke or generated
  command path. Do not write the real user Codex profile.

Goal:

Implement or spike a reviewed-ready Codex CLI inner patch-generation command
path. Replace only the hand-written inner patch-generation agent with
`codex exec`; the outer Barcarolle adapter remains responsible for task
materialization, budget gate, cost ledger, redaction, normalized result,
verifier execution, and reviewer handoff.

Required harness shape:

- Use a temporary run-local `CODEX_HOME`.
- At startup, inject a BARCAROLLE provider override with `wire_api="responses"`.
- Read the base URL from `BARCAROLLE_LLM_BASE_URL` at runtime, but never record
  the resolved value.
- Use `BARCAROLLE_LLM_API_KEY` as the provider `env_key`; never read or record
  its value except by presence check when needed.
- Use a temporary `model_catalog_json` that supports the provider-prefixed
  active ACUT model routes:
  - `openai/gpt-5.4-mini`
  - `openai/gpt-5.5`
- The temporary model catalog must allow shell/edit tools for both active model
  tiers and include non-interactive evaluation base instructions: complete the
  task using tools, do not stop at "I will modify", verify changed files before
  finishing, and keep the final answer brief.
- Treat provider catalog refresh warnings as non-fatal when the explicit model
  route and temporary model catalog are present.

Suggested implementation:

1. Add a dependency-light command such as
   `experiments/core_narrative/tools/codex_cli_patch_command.py`.
2. Keep the command usable after `--` from
   `experiments/core_narrative/tools/acut_patch_adapter.py`.
3. Support a no-model dry-run/smoke mode that validates command construction,
   temporary `CODEX_HOME`, temporary project trust config, temporary model
   catalog, prompt construction, and redaction without making a live model call.
4. Run the smallest no-secret smoke proving the outer adapter can invoke the
   Codex CLI inner command path. Prefer a no-model/dry-run smoke. If you decide
   a live BARCAROLLE smoke is strictly required, first verify and record only
   non-secret booleans for env presence and ledger writability, enforce a small
   explicit projected-cost cap, append a ledger record for the call/attempt, and
   keep all artifacts free of secrets, full endpoint values, hostnames, and IPs.
5. Write a concise report at
   `experiments/core_narrative/reports/codex_cli_harness_adapter.md`.
6. Write bounded smoke artifacts only under:
   - `experiments/core_narrative/results/raw/codex_cli_harness_adapter*/**`
   - `experiments/core_narrative/results/normalized/codex_cli_harness_adapter*.json`

Useful files to inspect:

- `.codex-workflows/core-narrative-experiment/shared/codex-cli-harness-handoff.md`
- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/barcarolle_patch_command.py`
- `experiments/core_narrative/tools/_llm_budget.py`
- `experiments/core_narrative/tools/_common.py`
- `experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml`
- `experiments/core_narrative/configs/acuts/frontier-generic-swe.yaml`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- `experiments/core_narrative/tasks/click/rbench/click__rbench__001/task.yaml`

Required checks:

- Python syntax check for any changed Python tools.
- JSON/JSONL parse checks for new smoke artifacts.
- A scoped no-secret scan over changed reports, raw artifacts, normalized
  artifacts, and your process file.
- A check that any smoke did not create a retry, second attempt, specialist
  ACUT run, broad execution artifact, or large batch artifact.

Process requirements:

- Update your `process.md` before meaningful work and before handoff.
- If blocked, set `status: blocked` and write the exact blocker and whether
  user input is required.
- If delivered, set `status: delivered`, list changed and inspected files,
  checks run, whether any live BARCAROLLE model call occurred, any ledger event
  appended, and the exact reviewed-ready command template using placeholders
  for secret or endpoint values.
- Commit only your owned changes on branch
  `codex/core-exp-codex-cli-harness-adapter`.

Do not integrate into the coordinator branch. A focused reviewer must inspect
your delivery before any further ACUT execution decision.
