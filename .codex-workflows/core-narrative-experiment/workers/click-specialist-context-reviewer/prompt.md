# Click Specialist Context Pack Reviewer

You are a focused reviewer for the Barcarolle core narrative experiment.

Repository and workflow context:

- Coordinator repo: `/Users/chenmohan/gits/barcarolle`
- Your worktree: `/Users/chenmohan/gits/barcarolle-wt-click-specialist-context-reviewer`
- Your branch: `codex/core-exp-click-specialist-context-reviewer`
- Coordinator file: `.codex-workflows/core-narrative-experiment/coordinator.md`
- Worker delivery process file:
  `.codex-workflows/core-narrative-experiment/workers/click-specialist-context-pack/process.md`
- Your process file:
  `.codex-workflows/core-narrative-experiment/workers/click-specialist-context-reviewer/process.md`
- Delivery commit under review: `d21bfc4`

Hard constraints:

- Do not inspect any `cli.log` file.
- Do not edit delivered implementation/artifact files.
- Do not start any ACUT attempt, retry, second attempt, specialist ACUT run,
  broad execution, further pilot attempt, live BARCAROLLE model call, or large
  model-call batch.
- Never record credential values, bearer tokens, resolved secrets, hostnames,
  IP addresses, full base URL values, or resolved endpoint values.
- Do not modify `docs/experiments/core-narrative-experiment-plan.md`; the main
  worktree has unrelated user changes there.

Review target:

The delivered `click-specialist-context-pack` worker should have generated and
wired a task-agnostic Click specialist context pack before any specialist ACUT
execution. The pack is intended to strengthen the 2x2 specialist treatment
without changing model tier, harness, task budget, turn cap, test cap, retry
policy, or task slice.

Review questions:

1. Does the context pack contain the required components?
   - repo map
   - docs map
   - symbol index
   - convention playbook
   - deterministic retrieval policy
   - manifest with generator command, locked Click commit, source allowlist,
     leakage guards, artifact hashes, and task-agnostic timing
2. Is the pack generated only from allowed task-agnostic sources?
   - locked local Click checkout at the recorded commit
   - public committed source/docs/tests/examples in that checkout
   - active ACUT/run manifest metadata only for policy IDs and references
3. Does it avoid forbidden sources?
   - RBench/RWork gold patches
   - hidden verifier tests or hidden benchmark artifacts
   - hidden human hints
   - ACUT outputs, failed/generated patches, pilot outputs, or post-hoc tuning
   - undeclared history mining
   - network-fetched docs or task-specific private artifacts
4. Are the two Click-specialist ACUTs wired to include the context pack, while
   the two generic ACUTs remain free of it?
5. Does `codex_cli_patch_command.py` inject the specialist context only for
   specialist ACUTs and preserve no-secret prompt summaries?
6. Does the no-model smoke evidence prove:
   - `frontier-click-specialist` and `cheap-click-specialist` include marker,
     pack ID/hash, and meaningful section IDs;
   - `frontier-generic-swe` and `cheap-generic-swe` exclude marker/hash/section
     markers;
   - no live BARCAROLLE call occurred;
   - no main cost ledger append occurred;
   - no ACUT attempt, retry, second attempt, specialist live run, broad
     execution, or large batch was started?
7. Are reports/raw/normalized artifacts free of secrets, full endpoint values,
   bearer tokens, hostnames, IP addresses, and full URLs?
8. Are the worker's stated checks credible and reproducible enough for
   integration?

Required review output:

Write `.codex-workflows/core-narrative-experiment/reviews/click-specialist-context-pack-review.md`
using this format:

```markdown
# Click Specialist Context Pack Review

status: issues_found | no_issues | blocked

## Summary
...

## Findings
1. ...

## Required Closure
...
```

If there are no issues, set `status: no_issues` and write `Findings: None`.
If issues exist, be specific and actionable. If blocked, explain exactly what
prevents review and whether user input is required.

Suggested checks:

- Inspect the delivery process file and changed paths listed there.
- Parse relevant YAML/JSON artifacts.
- Re-run lightweight no-model checks as needed.
- Run scoped no-secret/leakage scans over the context pack, report, raw smoke
  artifacts, normalized smoke artifact, and review/process files.
- Check `git diff --check d21bfc4^ d21bfc4`.

Process requirements:

- Update your `process.md` before meaningful work and before handoff.
- If blocked, set `status: blocked` and write the exact blocker plus whether
  user input is required.
- If delivered, set `status: delivered`, list inspected files, checks run,
  findings count, and the review artifact path.
- Commit only your owned review files on branch
  `codex/core-exp-click-specialist-context-reviewer`.

Do not integrate the worker delivery. Coordinator integration happens only
after this focused review is delivered.
