# Codex CLI Transport Hardening Review

You are the focused no-model/static reviewer for the Barcarolle core narrative
experiment Codex CLI transport-hardening delivery.

Reviewer repository:
`/Users/chenmohan/gits/barcarolle-wt-codex-cli-transport-hardening-reviewer`

Delivered worker worktree under review:
`/Users/chenmohan/gits/barcarolle-wt-codex-cli-transport-hardening`

Worker commit under review: `fa80a57`

## Coordination Contract

Read first:

1. `.codex-workflows/core-narrative-experiment/coordinator.md`
2. `/Users/chenmohan/gits/barcarolle-wt-codex-cli-transport-hardening/.codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening/process.md`
3. `.codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening-reviewer/process.md`
4. `.codex-workflows/core-narrative-experiment/workers/pilot-006-reviewer/process.md`
5. `.codex-workflows/core-narrative-experiment/workers/pilot-007-reviewer/process.md`

Do not inspect any `cli.log` file in any worktree or artifact tree. Do not start
any ACUT attempt, live BARCAROLLE model call, retry, second attempt, additional
specialist ACUT run, broad execution, further pilot attempt, cost-ledger append,
or large model-call batch.

Never record credential values, bearer tokens, resolved secrets, hostnames, IP
addresses, or full base URL values.

## Review Scope

Review only the worker delivery in
`/Users/chenmohan/gits/barcarolle-wt-codex-cli-transport-hardening`:

- `experiments/core_narrative/tools/codex_cli_patch_command.py`
- `experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/test_acut_patch_adapter.py`
- `experiments/core_narrative/reports/codex_cli_transport_hardening.md`
- `.codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening/**`

Write only these files in this reviewer repository:

- `.codex-workflows/core-narrative-experiment/reviews/codex-cli-transport-hardening-review.md`
- `.codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening-reviewer/process.md`

## What To Check

1. The worker stayed no-model/static: no ACUT attempt, live BARCAROLLE model
   call, main cost-ledger append, retry, second attempt, additional specialist
   run, broad execution, further pilot attempt, or large batch.
2. The classifier correctly identifies the reviewed redacted Responses
   streaming disconnect shape without recording message bodies, credential
   values, bearer tokens, full URLs, hostnames, or IP addresses.
3. Generic nonzero exits, timeouts, unsafe patch rejection, exit-0 empty diff,
   and successful verifier-eligible patch behavior remain distinct.
4. Adapter metadata propagation preserves raw adapter status and ledger event
   semantics, budget accounting, verifier policy, retry policy, and one-primary
   attempt policy.
5. The report honestly records that no safe non-streaming Codex CLI transport
   switch was established by no-model local discovery.
6. Tests and static checks are adequate for the risk and can be reproduced
   without contacting BARCAROLLE.
7. Scoped artifacts contain no secrets, bearer-token-shaped strings, full URLs,
   hostnames, or IP-shaped values. Exclude every `cli.log` path from scans and
   do not inspect it.

You may run no-model tests and static checks only.

## Output

Write
`.codex-workflows/core-narrative-experiment/reviews/codex-cli-transport-hardening-review.md`:

```markdown
# Codex CLI Transport Hardening Review

status: no_issues | issues_found | blocked

## Summary
...

## Findings
...

## Evidence
...

## Required Closure
...
```

Update
`.codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening-reviewer/process.md`
with `status: no_issues`, `status: issues_found`, or `status: blocked`, a
short summary, checks run, and handoff. If you find no issues, say explicitly
that the coordinator may integrate the transport-hardening delivery and review
artifact before deciding any later bounded execution hypothesis.
