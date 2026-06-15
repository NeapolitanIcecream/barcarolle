# Agent Tuning Phase 2b claim and Phase 2a reframe

Generated at: `2026-06-15T03:19:57+00:00`.

## Phase 2a reframe

Phase 2a is recorded as an action-level injection and before/after validation pilot. It did not prove tuned improvement: Selection-dev stayed `1/4 -> 1/4`, Holdout stayed `5/6 -> 5/6`, and paired net wins were `0` on both splits.

Phase 2a also did not run a real LLM-driven tuner. It used GEPA `optimize_anything` with a custom deterministic local proposer and no reflection LM. A deterministic local template or local proposer must not be presented as a real LLM-driven artifact tuner.

## Frozen Phase 2b gates

- Use rolling-origin or time-ordered future validation.
- Use an LLM-driven artifact proposer; otherwise stop or label the run as non-LLM control.
- Require positive Selection-dev paired net wins before future validation.
- Require future non-regression at minimum; positive paired net wins are preferred.
- Track cost, latency, invalid/unscoreable cells, and failure-label shifts.

## Supported if successful

- A narrow, repo-local Kilo AGENTS.md appendix can be proposed from past boltons failures by an LLM-driven proposer.
- Under one or more frozen time-ordered windows, selected artifacts can be evaluated before/after under fixed Agent and verifier conditions.
- If future paired net wins are positive, Phase 2b supports demo-level artifact-tuning improvement for this target slice.

## Still unsupported

- statistical significance
- cross-repo generalization
- model fine-tuning
- full opaque-Agent tuning
- production-ready Agent tuning system
- public leaderboard ranking
- predictive validity beyond the frozen task windows
