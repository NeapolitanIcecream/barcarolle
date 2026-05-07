# Patch Command Contract Worker

Historical note: this original worker prompt predates the active 2x2 pilot
revision. It is superseded by `revision-prompt-1.md` and
`revision-prompt-2.md`; ACUT manifest references below are historical context
only and must not be used as current execution templates, current smoke
evidence, default core IDs, or new-execution ACUT references.

You are a focused implementation worker for the Barcarolle core narrative experiment.

Repository and workflow context:

- Main coordinator repo: `/Users/chenmohan/gits/barcarolle`
- Your worktree: `/Users/chenmohan/gits/barcarolle-wt-patch-command-contract`
- Your branch: `codex/core-exp-patch-command-contract`
- Coordinator file: `.codex-workflows/core-narrative-experiment/coordinator.md`
- Your process file: `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`
- Current blocker: `patch_generation_command_gap`

Hard constraints:

- Do not inspect any `cli.log` file.
- Do not start broad ACUT execution.
- Do not start live ACUT model calls or live patch-generation attempts.
- Do not record credential values, bearer tokens, resolved secrets, or full base URL values anywhere.
- Do not modify `docs/experiments/core-narrative-experiment-plan.md`; the main worktree has unrelated user changes there.
- The live patch-generation command must use only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` for LLM access.
- The command path must be usable behind `experiments/core_narrative/tools/acut_patch_adapter.py`, so the adapter remains the budget gate, redaction gate, and cost ledger wrapper.

Goal:

Close the concrete patch-generation command gap without making a live model call. Implement a reviewed-ready command path that can later be passed after `--` to `acut_patch_adapter.py` for a single ACUT/task attempt.

Expected implementation:

1. Add a concrete command, preferably `experiments/core_narrative/tools/barcarolle_patch_command.py`.
2. The command should be dependency-light and use Python stdlib where practical.
3. It must read LLM credentials/endpoints only from `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`.
4. It must never accept credential values, bearer tokens, or full base URL values as CLI arguments.
5. It must not print or persist credential values or the resolved base URL.
6. It should support no-model smoke modes, for example a dry-run or mock-response path, so behavior can be tested without hitting a live endpoint.
7. It should prepare a concise prompt from the prepared workspace task package (`.core_narrative/task.json` and statement), ACUT manifest, and allowed visible context.
8. For live mode, it should call the configured LLM endpoint through the allowed env vars and apply a returned unified diff or structured patch in the workspace.
9. For smoke mode, prove:
   - missing env blocks before any network/model action;
   - unsafe CLI args are rejected;
   - no-model/mock response does not require a live endpoint;
   - no resolved secrets/full URLs are written into artifacts;
   - the command can be wrapped by `acut_patch_adapter.py --dry-run` and/or a no-model adapter probe without ledger or redaction regressions.

Recommended owned paths:

- `experiments/core_narrative/tools/barcarolle_patch_command.py`
- `experiments/core_narrative/reports/patch_command_contract.md`
- `experiments/core_narrative/results/normalized/patch_command_contract*.json`
- `experiments/core_narrative/results/raw/patch_command_contract*/**`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`

You may inspect relevant existing tools and config files under `experiments/core_narrative/**`, especially:

- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/_llm_budget.py`
- `experiments/core_narrative/tools/_common.py`
- `experiments/core_narrative/tools/prepare_workspace.py`
- `experiments/core_narrative/configs/acuts/lower-budget-fast-path.yaml`
- `experiments/core_narrative/tasks/click/rbench/click__rbench__001/task.yaml`

Process requirements:

- Update your `process.md` before meaningful work.
- Keep `process.md` concise and current.
- If you find this cannot be closed without user input, set `status: blocked` and write the exact needed input.
- If delivered, set `status: delivered`, list changed/inspected files, checks run, whether any live model call occurred, and the exact command template the coordinator can review next.
- Commit only your owned changes on branch `codex/core-exp-patch-command-contract`.

Do not integrate into the coordinator branch. A reviewer will inspect your delivery first.
