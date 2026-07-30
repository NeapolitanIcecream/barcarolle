# SWE-bench Full Suitability and ALG-016U Transfer

This direct experiment normalizes the pinned 2,294-Task SWE-bench Full test
split against eleven exact official checked result blobs. It evaluates the
source before conditionally transferring one unchanged algorithm.

The frozen plan digest is
`1c37db6ebd2b65a4acdb81c4e75aec1fcab54a7db31e84558c7435d5dadc4b32`.
It was committed before the result blobs were downloaded or normalized for
this experiment.

The source gate rejected algorithm execution: resolution, oracle headroom, and
nontrivial Full-history prediction passed, but the H5 joint-future-block-order
null returned `p=0.126437`, above the frozen `0.05` threshold. ALG-016U was
therefore not executed. This is a source-gate result, not an ALG-016U score.

Raw official results and complete run artifacts remain ignored. The committed
[`evidence/summary.json`](evidence/summary.json) binds two byte-identical runs.
An independent implementation reproduced the normalizer, all 609 Origins,
controls, random calibration, temporal null, and exact budget-ten oracle.

## Reproduce

Use the exact dependency versions frozen in the plan:

```bash
uv run python examples/swe_bench_full_transfer/study.py fetch

uv run --with numpy==2.5.1 --with scipy==1.16.3 --with pyarrow==25.0.0 \
  python examples/swe_bench_full_transfer/study.py audit \
  --output outputs/research/2026-07-30-swe-bench-full-transfer/suitability-result-a.json

uv run --with numpy==2.5.1 --with scipy==1.16.3 --with pyarrow==25.0.0 \
  python examples/swe_bench_full_transfer/study.py audit \
  --output outputs/research/2026-07-30-swe-bench-full-transfer/suitability-result-b.json

uv run python examples/swe_bench_full_transfer/study.py summary \
  --audit outputs/research/2026-07-30-swe-bench-full-transfer/suitability-result-a.json \
  --audit-reproduction outputs/research/2026-07-30-swe-bench-full-transfer/suitability-result-b.json \
  --output examples/swe_bench_full_transfer/evidence/summary.json

uv run python examples/swe_bench_full_transfer/study.py verify \
  --audit outputs/research/2026-07-30-swe-bench-full-transfer/suitability-result-a.json \
  --summary examples/swe_bench_full_transfer/evidence/summary.json
```

`transfer` refuses to run unless the bound suitability artifact authorizes it.
Do not weaken the gate or add another algorithm after reading this result.

## Claim Boundary

SWE-bench Full was already outcome-open during the external-source audit. Its
Task time is a source-time counterfactual, its Agent Results lack native
availability time, and it shares the SWE-bench repository family with
Verified. The result can guide development-source choice; it cannot establish
independent confirmation, prospective validity, workload relevance, or a
production Selector.

The six exact Verified source/Check-specific result blobs were not read.
However, three Full submissions use the same Agent identities and cover all
500 Verified instance IDs. Those three identities are no longer eligible for
an unseen-Agent claim. The append-only
[`evidence-boundary-amendment-1.json`](evidence-boundary-amendment-1.json)
records the correction without changing the frozen plan or rerunning the gate.
