# Local Algorithm Bakeoff Decision

Status: `complete`.
Final decision: `not_ready_keep_stratified_mainline`.
Best local candidate: `temporal_recent_baseline`.
Mainline recommendation: `keep_repo_stratified_as_mainline`.
Smallest blocker: `eligible certified task supply below 20-30 per target repo and no stable 15%+ local MAE improvement over stratified baseline`.

## Boundary Checks

- New paid ACUT calls made: `False`.
- New paid LLM calls made: `False`.
- Raw artifacts committed: `False`.
- Follow-up runbook written by worker: `False`.

## Research Questions

| RQ | Answer |
| --- | --- |
| RQ1 | Yes. The committed weighted pilot metrics reproduce exactly from the committed score table and release candidates. |
| RQ2 | Yes. The old metadata objective is `confirmed` underidentified; near-optimal metadata splits have materially different observed gaps. |
| RQ3 | No stable promotion signal. Block-randomized stratified candidates were evaluated locally, but seed/window evidence is too sparse to beat the simple stratified baseline conservatively. |
| RQ4 | Capped shrinkage weights did not add a reliable local signal after blocking; sparse support led to uniform fallback or reference-only weighting. |
| RQ5 | No. Local supply and retrospective evidence are insufficient for another paid replication; retain the simple stratified mainline for now. |

The decision does not claim predictive validity or paid replication completion.
