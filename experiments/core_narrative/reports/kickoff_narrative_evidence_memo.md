# Kickoff Narrative Evidence Memo

status: no_scoreable_acut_result_yet
updated: 2026-05-06T23:53:50+08:00
related_gate: `.codex-workflows/core-narrative-experiment/decisions/post-pilot-008-transport-gate.md`
related_option_c_spike: `experiments/core_narrative/reports/post_pilot_008_option_c_no_model_spike.md`

## One-Sentence Honest Status

Barcarolle has a concrete, ledgered NFL-style ranking-reversal evaluation design,
but pilots 001-008 have produced **zero scoreable ACUT capability results** because
both tried patch-generation transports failed before verifier.

## The Ranking-Reversal Story We Can Still Tell

The Agent-license hypothesis is not “the biggest model always wins.” It is closer
to an NFL power-ranking problem:

- a frontier generic SWE agent can look like the best overall team;
- a cheaper or same-tier repository-specialist agent can be a better matchup on a
  specific “field,” such as Click maintenance tasks;
- the ranking can reverse when the schedule changes from generic benchmark tasks
  to repository-specific RBench/RWork tasks;
- a credible license should therefore report matchup-conditioned evidence, not a
  single global model rank.

This repo makes that story concrete with a 2x2 ACUT design:

| Axis | Cells |
| --- | --- |
| Model tier | frontier (`openai/gpt-5.5`) vs cheap (`openai/gpt-5.4-mini`) |
| Context policy | generic SWE vs Click-specialist task-agnostic context |
| Task schedule | `G_score`, `RBench`, `RWork` pilot slices |
| Attempt policy | one primary attempt per ACUT/task; no retries unless separately authorized |

## What The Evidence Currently Supports

Supported claims:

1. The benchmark/evaluation scaffolding is concrete enough to generate ACUTs,
   task packs, manifests, budget gates, cost ledger records, raw artifacts, and
   normalized result records.
2. Budget discipline is active: current ledger cumulative estimated cost is USD
   `31.0008` across 11 records, below the USD `240` soft stop and USD `300` hard
   cap.
3. No pilot has reached verifier with a non-empty, safe patch artifact, so there
   is no `G_score`, `R_score`, `W_score`, or ranking-reversal measurement yet.
4. The current Codex CLI Responses streaming path is not worth another live
   repeat: pilots 006/007/008 failed before verifier across treatment and
   model-tier axes.
5. The earlier direct command path is also not cleared for another live repeat:
   pilots 001/002/003 failed before verifier with redacted `gaierror` outcomes.
6. The next safe work is review of the no-model Option C spike or a pause/report,
   not broad execution.

Unsupported claims:

- that the Click-specialist ACUT beats or loses to the generic ACUT;
- that frontier beats cheap, or cheap beats frontier, on any task slice;
- that the Agent-license ranking reversal is empirically demonstrated;
- that any ACUT has a negative capability result.

## Pilot Outcome Table

| Pilot group | Transport/path | Cells exercised | Result class | Scoreable? | Useful conclusion |
| --- | --- | --- | --- | --- | --- |
| 001-003 | direct `barcarolle_patch_command.py` | cheap generic, RBench tasks | `command_failed` before verifier; redacted `gaierror` | no | direct path needs operational-readiness evidence before another live probe |
| 004-005 | Codex CLI/harness transition and Click-specialist recovery | cheap Click-specialist | pre-verifier no-patch failures | no | harness/empty-patch handling needed hardening and review |
| 006-008 | Codex CLI Responses streaming path | cheap specialist, cheap generic, frontier generic | `command_failed` / `codex_exec_failed`, including `responses_streaming_disconnect` | no | same path failure is treatment-independent and model-tier-independent within observed cells |

## Kickoff Slide Skeleton

1. **Problem:** Global agent rankings hide matchup risk. A license should say what
   an agent is good for, not just how strong it is overall.
2. **Analogy:** NFL-style rankings reverse by opponent and schedule; a team can be
   top-ranked overall and still be the wrong matchup.
3. **Barcarolle design:** 2x2 ACUT matrix over tier and repository-specialist
   context, evaluated across generic and repo-specific task schedules.
4. **Current evidence:** The scaffolding is real and ledgered; eight pilots and two
   route checks consumed USD `31.0008`, but no pilot reached verifier.
5. **Integrity claim:** We are explicitly not calling infra failures capability
   results. The gate prevents wasting budget on repeated pre-verifier paths.
6. **Next experiment:** Review the Option C no-model direct-transport spike, then
   either pause/report no scoreable result or record a separate operational
   readiness decision for exactly one future direct-transport probe.
7. **Success criterion:** A future kickoff-quality result requires at least one
   verifier-ready patch per compared cell on the same task schedule, then a table
   showing whether ordering changes between `G_score` and `R/W` slices.

## Minimum Result Needed For The Actual Ranking-Reversal Claim

A credible first empirical story needs all of the following:

- at least one scoreable task schedule with the same tasks run for the compared
  ACUT cells;
- non-empty, safe patch artifacts that reach verifier;
- normalized result records with comparable score fields;
- no retries or hidden context advantages outside the ACUT contract;
- a report that separates global-tier effects from repository-specialist context
  effects.

Until then, the kickoff narrative should be framed as a rigorous evaluation
program with an honest infrastructure blocker, not as a demonstrated ranking
reversal.
