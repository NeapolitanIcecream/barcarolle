# Phase 0 Headroom Matrix Decision

Decision: `repair_generic_comparator_protocol`.

## Entry Conditions

Phase 0 met entry conditions: `True`.

## Scoreable Cells

- Scoreable same-repo cells: `6`.
- Agent failures: `4`.
- Harness or invalid-output failures: `0`.
- `G_mini` same-protocol scoreable: `False`.

## Budget

Estimated budget recorded for this matrix: `$60.00`. The batch started `6` paid Codex CLI task attempts under one ACUT configuration; exact CLI cost was not observable, so the conservative projected maximum remains the recorded estimate.

## Supported Claim

The run supports only an underpowered same-repo scoreability diagnostic. It does not support predictive validity, repository-general conclusions, or a final benchmark claim.

## Limitations

- The sample has six same-repo tasks and one ACUT.
- Four tasks are clustered around one `compose` issue thread.
- `G_mini` archived Click tasks were not same-protocol scoreable in this Phase 0 harness.

## Next Smallest Useful Action

Repair or materialize the generic comparator protocol before spending on a second ACUT. A second ACUT would be useful only after comparator scoreability is fixed; keep any follow-up projected cost at or below USD 60 unless explicitly approved.
