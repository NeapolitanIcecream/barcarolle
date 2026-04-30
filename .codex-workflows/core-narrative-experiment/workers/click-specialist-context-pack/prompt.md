# Click Specialist Context Pack Worker

You are a focused implementation worker for the Barcarolle core narrative
experiment.

Repository and workflow context:

- Coordinator repo: `/Users/chenmohan/gits/barcarolle`
- Your worktree: `/Users/chenmohan/gits/barcarolle-wt-click-specialist-context-pack`
- Your branch: `codex/core-exp-click-specialist-context-pack`
- Coordinator file: `.codex-workflows/core-narrative-experiment/coordinator.md`
- Your process file: `.codex-workflows/core-narrative-experiment/workers/click-specialist-context-pack/process.md`

Hard constraints:

- Do not inspect any `cli.log` file.
- Do not start broad ACUT execution.
- Do not start any ACUT attempt, retry, second attempt, specialist ACUT run,
  additional pilot attempt, or large model-call batch.
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
- Prefer no-model smoke. Use at most one or two minimal live injection/health
  smokes only if no-model evidence cannot prove context injection. A live smoke
  is not an ACUT attempt and must not produce patch-generation, verifier, retry,
  second-attempt, specialist-run, broad-execution, or batch artifacts.

Goal:

Generate and wire a reviewed-ready, task-agnostic Click specialist context pack
so the 2x2 ACUT design has a real specialist treatment before any specialist
ACUT execution.

The active 2x2 ACUTs remain:

- `frontier-generic-swe`
- `frontier-click-specialist`
- `cheap-generic-swe`
- `cheap-click-specialist`

The specialist treatment must not change model tier, harness, task budget, turn
cap, test cap, retry policy, or task slice. Within each model tier, only the
generic-vs-Click-specialist policy/context changes.

Allowed source material for the Click specialist context pack:

- Locked local Click checkout:
  `experiments/core_narrative/external_repos/click`
- Public, committed source/docs/tests/examples in that locked checkout.
- Current active ACUT manifests and run manifest for declared policy IDs and
  artifact references.

Forbidden source material:

- RBench/RWork gold patches.
- Hidden verifier tests or hidden benchmark artifacts.
- Hidden human hints.
- ACUT outputs, failed/generated patches, pilot outputs, or post-hoc tuning from
  the observed attempts.
- Git history mining unless explicitly declared, deterministic, task-agnostic,
  and justified. Prefer no history mining.
- Network-fetched docs or task-specific private artifacts.

Required deliverables:

1. A reproducible context pack under
   `experiments/core_narrative/context_packs/click_specialist/` with:
   - repo map;
   - docs map;
   - symbol index;
   - convention playbook;
   - deterministic retrieval policy;
   - manifest recording generator command, locked Click commit, source
     allowlist, leakage guards, artifact hashes, and task-agnostic generation
     timing.
2. Tooling or command-path changes that make context injection explicit and
   testable for the reviewed Codex CLI inner patch command path. Specialist
   ACUTs must include the context pack in the prompt/context; generic ACUTs must
   not include it.
3. A no-model smoke that proves:
   - `frontier-click-specialist` and `cheap-click-specialist` prompts/context
     include the context pack marker, pack ID/hash, and meaningful section IDs;
   - `frontier-generic-swe` and `cheap-generic-swe` prompts/context do not
     include the Click specialist context pack;
   - prompt/context evidence stores hashes, section IDs, char counts, and
     booleans, not full secrets or full endpoint values;
   - no ACUT attempt, retry, second attempt, specialist live run, broad
     execution, or large batch was started.
4. A concise report at
   `experiments/core_narrative/reports/click_specialist_context_pack.md`.
5. Machine-readable no-model smoke artifacts under:
   - `experiments/core_narrative/results/raw/click_specialist_context_pack*/**`
   - `experiments/core_narrative/results/normalized/click_specialist_context_pack*.json`

Suggested implementation path:

1. Inspect the existing active ACUT manifests and
   `experiments/core_narrative/tools/codex_cli_patch_command.py` prompt
   construction.
2. Add a deterministic generator such as
   `experiments/core_narrative/tools/build_click_specialist_context_pack.py`.
3. Add a small loader/injection path used by `codex_cli_patch_command.py`, or a
   shared helper if that fits the existing style better.
4. Reference the context pack from the two Click-specialist ACUT manifests, and
   keep the two generic ACUTs free of that reference.
5. Add a dry-run/no-model evidence mode or reuse the existing dry-run path so
   reviewers can see the pack is injected without making a BARCAROLLE call.

Required checks:

- Python syntax check for any changed Python tools.
- YAML/JSON parse checks for new/updated configs and artifacts.
- A reproducibility check that re-running the generator does not change the
  context pack unless source inputs change.
- A no-model injection smoke for both specialist ACUTs and both generic ACUTs.
- A scoped no-secret scan over changed reports, raw artifacts, normalized
  artifacts, generated context pack, and your process file.
- A leakage guard check showing the context pack does not include gold patches,
  hidden verifier files, ACUT outputs, post-hoc pilot artifacts, full URLs,
  credential values, bearer tokens, hostnames, or IP addresses.
- `git diff --check`.

Process requirements:

- Update your `process.md` before meaningful work and before handoff.
- If blocked, set `status: blocked` and write the exact blocker and whether
  user input is required.
- If delivered, set `status: delivered`, list changed and inspected files,
  checks run, whether any live BARCAROLLE model call occurred, any ledger event
  appended, and the reviewer handoff.
- Commit only your owned changes on branch
  `codex/core-exp-click-specialist-context-pack`.

Do not integrate into the coordinator branch. A focused reviewer must inspect
your delivery before any specialist execution or broader ACUT execution
decision.
