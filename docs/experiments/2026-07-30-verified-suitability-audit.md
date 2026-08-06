# SWE-bench Verified Suitability Audit

Date: 2026-07-30.

Status: complete, reproduced, and independently audited. No paid call was
made, no sealed Agent outcome was opened, no Selector was tested, and no
Generator was developed.

## Decision

The already-opened SWE-bench Verified eleven-Agent H5 panel is more
informative than the current Multi-SWE panel, but it does not clear the frozen
gate for a Stage C algorithm-development boundary.

Three statements must remain separate:

1. Full repository-local history is a substantially better pass-rate
   estimator than always zero on this panel.
2. An exact future-open budget-ten subset has substantially lower MAE than
   full history, so the frame contains Selection capacity.
3. The real chronology does not have an unusually favorable phase under the
   frozen circular-shift null.

The first two statements pass. The third does not. The frozen terminal state
is therefore `capacity_without_detected_history_persistence`, and the panel
remains descriptive rather than an authorized development boundary.

This is not a claim that time or Task content contains no signal. The
circular-shift diagnostic preserves almost all response adjacency and asks
whether the observed sequence phase is unusually favorable. Its failure
cannot reject change-point, local-persistence, or Task-feature mechanisms.
Changing that meaning after seeing `p=0.912` would nevertheless move the
predeclared gate, so no rescue diagnostic is run on this panel.

## Frozen Frame

The plan is
[`suitability-audit-plan.json`](../../examples/multi_repository_study/suitability-audit-plan.json),
digest
`59525b1a8168b909a4499f4658e10f5c4208e2fc5d659785d0ee42d44f63f550`.

- source: SWE-bench Verified revision
  `91aa3ed51b709be6457e12d00300a6a596d4c6a3`;
- denominator: exactly 500 Tasks;
- panel: three previously opened public Agents plus eight previously opened
  development Agents;
- sealed panel: six holdout Agents, not read;
- frame: seven repositories, 68 end-aligned non-overlapping H5 Origins,
  minimum history 15, Selection budget ten;
- primary loss: future pass-rate MAE;
- aggregation: Agent mean inside Origin, Origin mean inside repository, then
  equal repository;
- controls: zero, one, full history, separately labeled cached-target
  climatology, 20,000 equal-budget random draws, and exact budget-ten
  hindsight;
- uncertainty: 10,000 repository-bootstrap resamples, repository omission,
  and 2,000 inclusive-zero joint-response circular shifts.

The public results are retrospective and Task time is projected from
`created_at`. Historical Result availability is not attested. The frame cannot
support a strict-prospective or workload-relevance claim.

## Results

| Diagnostic | Value |
| --- | ---: |
| Equal-repository future density / always-zero MAE | `0.359033` |
| Full-history MAE | `0.183374` |
| Full minus always zero | `-0.175659` |
| Repository-bootstrap 95% interval | `[-0.248315, -0.063516]` |
| Leave-one-repository-out directions | `7 / 7` favorable |
| Agent directions | `9 / 11` favorable |
| Equal-budget random mean MAE | `0.194647` |
| Exact budget-ten hindsight MAE | `0.074019` |
| Full-to-oracle Selection headroom | `0.109355` |
| Circular-shift null mean | `-0.233757` |
| Circular-shift one-sided probability | `0.912044` |

Full history reduces MAE by `0.175659` relative to always zero. An independent
post-result sensitivity found that the best fixed grid constant is near
`0.4`, with MAE about `0.256560`; full history remains better by about
`0.073186`. This sensitivity was not frozen and is not a decision gate. It
only prevents always zero from being mislabeled as the strongest possible
constant estimator.

Random budget-ten sampling is worse than full history by `0.011273` on
average. The exact oracle is better than full history by `0.109355`, a
`59.63%` reduction from the full-history loss. This is large representational
headroom, but the oracle uses future outcomes and is neither learnable evidence
nor an executable Selector.

The circular statistic is full-history MAE minus always-zero MAE, where lower
is more favorable. Of 2,000 null draws, 1,824 were at least as favorable as
the observed statistic, giving `(1824 + 1) / (2000 + 1) = 0.912044`.
Therefore the observed absolute phase is not unusually favorable among
within-repository circular shifts. This does not mean that full history loses
to zero; it plainly does not.

Calendar duration is heterogeneous even under the common H5 task-count frame.
Cutoff to future-block end ranges from `11.43` to `1,220.96` days, with median
`46.73` days. H5 remains a research estimator rather than one deployment
`TimeRange`.

## Independent Verification

The two complete executions are byte-identical:

- raw file SHA-256:
  `7fd0e788479212e2cff8f0c66ea00c082a157edda5942e905b9e85b9ab627410`;
- logical result digest:
  `2311d7da9a285b43dadf9382cebe281473c742ffd6aa79b0d9084cd1e4412ea4`;
- compact summary digest:
  `48032bc07d64c693a7d3247b7af4ab8a750c56df93b972ea339e04f5f0392403`.

An adversarial audit independently rebuilt the 500 Tasks, eleven opened
Agents, seven repositories, and 68 Origins. It reproduced the MAE,
bootstrap, leave-one-repository-out, and temporal-null values. A separate
binary-variable MILP reproduced all 68 response-pattern oracle solutions and
the `0.074019` macro MAE. The analytic random-subset expectation was
`0.194702`, within one reported Monte Carlo standard error of the 20,000-draw
estimate.

The committed compact evidence is
[`suitability-audit-summary.json`](../../examples/multi_repository_study/suitability-audit-summary.json).
Raw outcomes and complete result payloads remain under ignored output paths.

## Cross-Source Interpretation

| H5 diagnostic | Multi-SWE, 36 configurations | Verified, 11 Agents |
| --- | ---: | ---: |
| Repositories / Origins | `13 / 221` | `7 / 68` |
| Always-zero MAE | `0.059870` | `0.359033` |
| Full-history MAE | `0.067348` | `0.183374` |
| Exact B10 oracle MAE | `0.034709` | `0.074019` |
| Full-to-oracle headroom | `0.032639` | `0.109355` |
| Frozen temporal-null probability | `0.111444` | `0.912044` |

The comparison rejects a source-independent `Multi-SWE-like triviality`
explanation. Verified has materially more outcome variation and Selection
headroom. It does not establish candidate-independent temporal alignment under
the frozen null. Neither source currently authorizes theory-driven candidate
search as the main research route.

## Next Boundary

Stop the opened-panel suitability atlas here. Do not run the Verified
three-Agent row, SymPy, a favorable Agent subset, or another horizon on the
same 500 Tasks.

The next no-paid action is a source-specific SWE-bench Full normalization
preflight:

1. freeze the exact checked eleven-Agent allowlist, official result blob
   identities, 2,294-Task denominator, Check meaning, and normalizer before
   reading normalized outcomes;
2. freeze H5 and H10 frames, equal-repository aggregation, full, fixed
   trivial, random, and exact-oracle meanings;
3. replace the over-broad chronology gate with a named family of diagnostics.
   In particular, predeclare an adjacent-H5 joint-block permutation that
   destroys block order while preserving each block's eleven-Agent response
   vector. Keep circular phase alignment separate if retained;
4. execute once. If Full still lacks a predeclared chronology signal, stop
   public retrospective atlas work and specify the smallest workload-matched,
   native-time acquisition.

SWE-bench Full would be another opened counterfactual development source, not
independent confirmation. Stage C remains data-gated until that boundary is
frozen and cleared.

## Reproduction

The direct runner is
[`suitability_audit.py`](../../examples/multi_repository_study/suitability_audit.py).
Use:

```bash
uv run \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/multi_repository_study/suitability_audit.py run \
  --output outputs/research/2026-07-30-verified-suitability-audit/run.json
```

The runner validates the dataset SHA-256, all bound manifest digests, every
opened result Git blob SHA, and the zero-authority boundary before computing
the audit.
