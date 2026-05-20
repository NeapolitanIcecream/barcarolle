# Phase 0 Decision Memo

Decision: `repair_source_adapter`.

## Scope

- Smoke/generic comparator: archived Click R0 metadata.
- Primary target repo: `toolz`.
- Paid LLM API spend: `USD 0.00`.
- Ledger path: `experiments/phase0_headroom/results/cost_ledger.jsonl`.

## Evidence

- Distribution mismatch rows with absolute gap >= 0.15: `12`.
- Certification attempted tasks: `16`.
- Certified benchmark-grade tasks: `0`.
- Near-certified diagnostic tasks: `6`.
- Mini release status: `diagnostic_only`.
- Headroom matrix: `blocked_underpowered`; no ACUT runs started.

## Interpretation

The target-profile and supply layers are viable enough to keep the restart alive: `toolz` yields many code-plus-test anchors and several candidates can be mechanically replayed through no-op/reference gates. The certification layer is the blocker. Deterministic commit-subject tasks do not provide sufficient non-leaky, scope-reviewed problem statements, so they cannot be counted as benchmark-grade tasks.

## Threats To Validity

- One primary target repository only.
- Generic comparator is archived Click metadata, not a fresh public benchmark sample.
- Issue and PR body text were not fetched, so ambiguity and leakage reviews are intentionally weak.
- No ACUT task-solving runs were performed.

## Next Smallest Useful Experiment

Build a source adapter that fetches PR or issue text and produces non-leaky candidate statements for the existing oracle-valid `toolz` anchors. Re-run certification until at least 6 tasks are certified, then run one cheap ACUT across 4 `B_real`, 4 `W_real`, and 4 `G_mini` tasks under the same ledger gate.
