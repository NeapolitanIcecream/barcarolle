# Phase 1 Third Repo Repair Remine Decision

Decision: `replace_third_repo_before_paid_acut`.

Paid LLM calls made: `false`. Paid ACUT calls made: `false`.

## Results

- Statement-template bug fixed in code: `true`
- Stale Itsdangerous artifacts regenerated: `true`
- Regenerated artifacts contain `Repair the humanize behavior`: `false`
- Commit-message fallback benchmark-grade allowed: `false`
- Candidates after repaired filter: `6`
- Reviewed non-leaky PR-context statements: `6`
- Locally certified tasks: `4`
- Release status: `pilot_grade`
- B_real tasks: `2`
- W_real tasks: `2`
- Hardened benchmark-grade candidates: `0`

Itsdangerous reached a local pilot-grade release after adding the repo-declared
`freezegun` test extra to the repair config. It still should not proceed to a
paid third-repo ACUT smoke run because Phase 1 hardening accepted zero
benchmark-grade candidates. The remaining blockers are source-quality and oracle
alignment risks, not the old statement-template bug.

## Next Step

Run a local-only replacement-repo selection and certification runbook before any
paid ACUT smoke. Preferred candidates from `repositories.yaml` are `boltons`
first and `attrs` second.

Predictive validity remains `false`.
