# Click R0 Release Hygiene

Date: 2026-05-10

## Scope

R0 turns the current Click smoke slice into an auditable mini release without claiming final benchmark authority. Existing `public/statement.md` files are preserved for compatibility. ACUT-visible inputs now use `public/acut_statement.md`; source URLs, target SHAs, compare links, and reference patch material are preserved separately under `audit/provenance.md`.

Release digest: `711cf19bd1235489683f0d58dde12db99ea25158d89581db75a0b75736910898`
Task count: `14`

| Task | Split | Oracle Grade | ACUT Statement | Audit Provenance |
| --- | --- | --- | --- | --- |
| `click__rbench__001` | `rbench` | `B` | `experiments/core_narrative/tasks/click/rbench/click__rbench__001/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rbench/click__rbench__001/audit/provenance.md` |
| `click__rbench__002` | `rbench` | `B` | `experiments/core_narrative/tasks/click/rbench/click__rbench__002/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rbench/click__rbench__002/audit/provenance.md` |
| `click__rbench__003` | `rbench` | `B` | `experiments/core_narrative/tasks/click/rbench/click__rbench__003/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rbench/click__rbench__003/audit/provenance.md` |
| `click__rbench__004` | `rbench` | `B` | `experiments/core_narrative/tasks/click/rbench/click__rbench__004/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rbench/click__rbench__004/audit/provenance.md` |
| `click__rbench__005` | `rbench` | `B` | `experiments/core_narrative/tasks/click/rbench/click__rbench__005/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rbench/click__rbench__005/audit/provenance.md` |
| `click__rbench__006` | `rbench` | `B` | `experiments/core_narrative/tasks/click/rbench/click__rbench__006/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rbench/click__rbench__006/audit/provenance.md` |
| `click__rbench__007` | `rbench` | `B` | `experiments/core_narrative/tasks/click/rbench/click__rbench__007/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rbench/click__rbench__007/audit/provenance.md` |
| `click__rbench__008` | `rbench` | `B` | `experiments/core_narrative/tasks/click/rbench/click__rbench__008/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rbench/click__rbench__008/audit/provenance.md` |
| `click__rwork__001` | `rwork` | `B` | `experiments/core_narrative/tasks/click/rwork/click__rwork__001/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rwork/click__rwork__001/audit/provenance.md` |
| `click__rwork__002` | `rwork` | `B` | `experiments/core_narrative/tasks/click/rwork/click__rwork__002/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rwork/click__rwork__002/audit/provenance.md` |
| `click__rwork__003` | `rwork` | `B` | `experiments/core_narrative/tasks/click/rwork/click__rwork__003/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rwork/click__rwork__003/audit/provenance.md` |
| `click__rwork__004` | `rwork` | `B` | `experiments/core_narrative/tasks/click/rwork/click__rwork__004/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rwork/click__rwork__004/audit/provenance.md` |
| `click__rwork__005` | `rwork` | `B` | `experiments/core_narrative/tasks/click/rwork/click__rwork__005/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rwork/click__rwork__005/audit/provenance.md` |
| `click__rwork__006` | `rwork` | `B` | `experiments/core_narrative/tasks/click/rwork/click__rwork__006/public/acut_statement.md` | `experiments/core_narrative/tasks/click/rwork/click__rwork__006/audit/provenance.md` |

## Leakage Reduction

The ACUT-visible task path now omits target commit URLs, target SHAs, compare links, and reference patch material. Those fields remain in `audit/provenance.md` and release metadata so reviewers can reproduce the package and audit lineage without exposing answer-adjacent anchors to ACUT runs.

## Remaining Provisional

This release still uses smoke-slice task membership and focused verifier grades. It does not assert final benchmark authority, predictive validity, license, admission, or authorization.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/click_r0_release_hygiene.py \
  --output experiments/core_narrative/releases/click_r0_20260510/release_metadata.json \
  --report experiments/core_narrative/reports/2026-05-10_click_r0_release_hygiene.md
```
