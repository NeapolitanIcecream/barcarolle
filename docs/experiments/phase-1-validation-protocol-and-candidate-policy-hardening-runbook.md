# Phase 1 Validation Protocol And Candidate Policy Hardening Runbook

Status: no-paid protocol hardening runbook, 2026-06-01.

## Goal

Turn the M3 evidence package into explicit validation and candidate-policy
rules before any paid-validation discussion.

This runbook should produce the M4 hardening package:

- study-mode and claim-boundary decision;
- candidate-policy pseudocode and fallback governance;
- baseline registry;
- adapter estimand and reporting rule;
- invalid-cell, non-scoreable, and catastrophic-miss rules;
- joint success gate;
- quantitative support thresholds;
- release artifact schema;
- validation-design figure spec;
- power and budget note;
- updated roadmap, evidence matrix, and process handoff.

M4 is complete when these rules are explicit enough for M5 to revise the
proposal report and for a future user decision to decide whether any paid
validation is worth discussing. M4 completion does not mean the current
candidate is paid-ready.

## Boundary

M4 is no-paid protocol work.

Allowed:

- read committed reports, sanitized JSON results, proposal docs, and local
  planning files already referenced by M2/M3;
- add narrow structured configs, scripts, tests, reports, and JSON artifacts
  for M4 protocol hardening;
- compute simple derived tables from existing committed/sanitized artifacts;
- write a validation-design figure spec for later rendering by M5;
- update `PROCESS.md`, the roadmap, and the evidence/TODO matrix with M4
  handoff state.

Not allowed:

- paid ACUT cells;
- paid LLM calls;
- external reviewer calls;
- public citation browsing;
- changing ACUT score tables;
- changing selected task IDs or split labels to improve results;
- rewriting the proposal report into reviewer-ready prose;
- drafting M5 or M6 runbooks;
- setting user-owned resource decisions, staffing assumptions, approval format,
  or a conditional paid budget ceiling;
- claiming predictive validity;
- authorizing paid validation.

If a rule would make the current M3 candidate fail a future gate, record that
plainly. Do not weaken the rule to make the current candidate pass.

## Research Interpretation To Preserve

M3 established useful traction, not predictive validity.

The current aggregate edge is small:

```text
candidate MAE = 0.209
best simple baseline MAE = 0.2149
candidate delta = -0.0059
```

The 1000-seed random baseline is encouraging, but adapter, repo, and window
diagnostics remain fragile. The current candidate is also composite:

```text
candidate object = coverage_constrained_unweighted_v1_with_labeled_fallbacks
overall fallback share = 6/18
boltons fallback share = 6/6
```

M4 must convert those facts into rules and claim boundaries. It must not
convert them into a validation claim.

## Inputs

Read these first:

- `AGENTS.md`
- `PROCESS.md`
- `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`
- `docs/research/phase-1-proposal-evidence-todo-matrix.md`
- `docs/research/phase-1-proposal-p0-placeholder-triage.md`
- `docs/research/phase-1-proposal-evidence-package.md`
- `docs/research/phase-1-proposal-claim-boundary.md`
- `docs/research/phase-1-proposal-report-v1.md`
- `docs/experiments/phase-1-validation-protocol-and-candidate-policy-hardening-runbook.md`

Primary M3 artifacts:

- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_decision.md`
- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_decision.json`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_coverage_ablation.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_source_supply_status.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_report_evidence_index.md`
- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_random_baseline_distribution.json`
- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_baseline_envelope.json`
- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_coverage_ablation.json`
- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_fallback_share.json`

Existing protocol artifacts to harden:

- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md`
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md`
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_success_criteria.md`
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md`
- `experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_policy_spec.json`
- `experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_validation_protocol.json`
- `experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_success_criteria.json`
- `experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_selection_manifest.json`
- `experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.json`

Useful external-plan inputs already present locally:

- `/Users/chenmohan/Downloads/barcarolle-research-0519.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0526.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0530.md`

Use local plan files only as planning input. Do not make local-only plan files
the final reviewer-facing evidence source.

## Expected Outputs

Create these M4 outputs unless a stop condition prevents them:

```text
docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md

experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_preflight.json
experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_claim_modes.json
experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_candidate_policy.json
experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_baseline_registry.json
experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_adapter_estimand.json
experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_success_gate.json
experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_support_thresholds.json
experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_release_schema.json
experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_power_budget_note.json
experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_decision.json

experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_process.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_claim_modes.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_candidate_policy.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_baseline_registry.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_adapter_estimand.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_support_thresholds.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_release_schema.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_power_budget_note.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md
```

Add a narrow tool/config/test only if it materially improves auditability:

```text
experiments/phase1_compiler/configs/phase1_validation_protocol_candidate_policy_hardening.yaml
experiments/phase1_compiler/tools/phase1_validation_protocol_candidate_policy_hardening.py
experiments/phase1_compiler/tests/test_phase1_validation_protocol_candidate_policy_hardening.py
```

If you add a tool, keep it deterministic and limited to:

- loading existing M2/M3 JSON artifacts;
- rendering structured M4 JSON/Markdown;
- checking that required decisions exist;
- checking that prohibited claims are absent.

Do not use a tool to invent new evidence or tune thresholds to the current
candidate.

## Worker Prompt

Use this prompt for the execution worker:

```text
You are executing docs/experiments/phase-1-validation-protocol-and-candidate-policy-hardening-runbook.md.

Read AGENTS.md and PROCESS.md first. Then read the runbook and follow it
step-by-step with step-level acceptance and scoped commits.

This is M4 no-paid protocol hardening. Do not run paid ACUT cells, paid LLM
calls, external reviewer calls, or public citation browsing. Do not change
score tables, selected task IDs, or split labels. Do not rewrite the proposal
report into reviewer-ready prose. Do not draft M5 or M6 runbooks.

Your job is to turn the completed M3 evidence package into explicit validation
rules and candidate-policy governance: study-mode claim boundaries, candidate
pseudocode, fallback threshold/reporting rule, adapter estimand, baseline
registry, invalid-cell and catastrophic-miss rules, joint success gate, support
thresholds, release artifact schema, validation-design figure spec, and
power/budget note.

If the hardened rules show that the current M3 candidate is not paid-ready,
record that plainly. Paid validation remains unauthorized unless the user later
authorizes it after M4 and M6 decisions.
```

## Step 0: Preflight And Scope Lock

1. Confirm the M3 stop label is `proposal_evidence_package_complete`.
2. Confirm M4 has no permission for paid calls, external review, public
   citation browsing, score-table edits, selected-task edits, or split edits.
3. Confirm whether a narrow rendering/validation tool is needed.
4. Record the exact input artifact paths and current Git commit.
5. Write the preflight JSON and process report.

Acceptance evidence:

- `phase1_validation_protocol_candidate_policy_hardening_preflight.json`
  records all inputs and boundary flags;
- `phase1_validation_protocol_candidate_policy_hardening_process.md` records
  the artifact plan and whether a tool will be used;
- paid/external/browser permissions are all false.

Suggested commit:

```text
Record M4 protocol hardening preflight
```

Stop if:

- M3 decision artifacts are missing;
- the worker cannot tell whether it is allowed to run paid or external calls;
- input artifact provenance is too inconsistent to decide validation rules.

## Step 1: Study Modes And Claim Boundary

Write the study-mode rule table.

At minimum, distinguish:

- `true_future_holdout`: future outcome-unseen validation; can support a
  predictive-validity claim only if all gates pass;
- `preregistered_rolling_origin`: can support a predictive-validity claim only
  if cutoffs, candidate policy, baselines, seeds, invalid-cell rules, adapter
  estimand, support thresholds, and success gates are frozen before outcomes
  are joined;
- `pseudo_future_replay`: can support traction and debugging only;
- current M3 retrospective evidence: traction only.

For each mode, specify:

- what can be claimed;
- what cannot be claimed;
- what must be frozen before outcomes are visible;
- what artifact proves the freeze;
- whether paid validation can be discussed after M4.

Acceptance evidence:

- claim-mode JSON and report exist;
- pseudo-future replay is explicitly barred from proving predictive validity;
- current M3 evidence is labeled traction only;
- the north-star predictive-validity claim remains future work.

Suggested commit:

```text
Define M4 validation claim modes
```

## Step 2: Candidate Policy And Fallback Governance

Produce candidate-policy pseudocode for:

```text
coverage_constrained_unweighted_v1_with_labeled_fallbacks
```

The pseudocode must show:

- allowed inputs;
- forbidden outcome inputs;
- per-repo budget;
- feature coverage objective;
- tie-break rule;
- supported-feature check;
- labeled fallback route;
- how fallback slots are marked;
- how source-quality overlays are applied;
- what counts as a policy violation.

Then decide fallback governance:

- numeric fallback-share threshold, or a written reason why no defensible
  numeric threshold can be set yet;
- whether threshold is overall, per repo, per feature, or all of those;
- include/exclude fallback-repo reporting rule;
- repair-or-narrowing rule if a repo has excessive fallback;
- whether the current M3 candidate passes the proposed fallback rule.

Use M3 facts:

```text
overall fallback share = 6/18
boltons fallback share = 6/6
fallback-repos-only diagnostic is worse than temporal by MAE 0.0139
```

Do not choose a threshold merely because it lets the current candidate pass.

Acceptance evidence:

- candidate-policy JSON/report include pseudocode and governance;
- current candidate readiness under the fallback rule is explicit;
- boltons fallback is treated as claim-changing unless the rule gives a
  defensible contrary reason;
- selected task IDs are not changed.

Suggested commit:

```text
Harden candidate policy and fallback governance
```

## Step 3: Baseline Registry

Create the baseline registry for future validation.

Mandatory baseline families:

- `temporal_recent_baseline`;
- `repo_unweighted_same_budget`;
- `repo_stratified_by_target_profile`;
- `many_seed_random_same_budget`.

For each baseline, specify:

- purpose;
- allowed inputs;
- forbidden inputs;
- budget matching rule;
- seed or deterministic tie-break rule;
- reporting metric;
- required slice reporting;
- failure modes.

Decide whether to add:

- a simple coverage-only baseline;
- a stricter temporal baseline variant;
- an external/general benchmark comparator.

If any optional baseline is not feasible inside short-term scope, record it as
deferred rather than expanding the project.

Acceptance evidence:

- baseline-registry JSON/report exist;
- temporal recent remains a serious comparator;
- random is many-seed, not five-seed;
- external/general comparators are not adopted without clean supply,
  licensing, and certification rules.

Suggested commit:

```text
Define future validation baseline registry
```

## Step 4: Adapter Estimand And Reporting Rule

Decide the estimand.

At minimum, answer:

- Is the primary claim per adapter, per named ACUT configuration, or a
  preregistered equal-mixture diagnostic?
- Can a pooled metric ever satisfy the primary success gate?
- What happens if Codex fails and Kilo passes, or vice versa?
- What adapter non-inferiority or claim-narrowing rule applies?
- What table must be primary in M5?

Preserve the existing boundary:

```text
Codex and Kilo are ACUT configuration evidence. Do not describe their
difference as model-only superiority unless adapter and harness differences
have explicitly been ruled out.
```

Acceptance evidence:

- adapter-estimand JSON/report exist;
- adapter-level reporting is primary;
- pooled improvement cannot rescue adapter-level failure unless the claim is
  explicitly narrowed to a preregistered mixture;
- current M3 Codex/Kilo split is interpreted under the rule.

Suggested commit:

```text
Define adapter estimand and reporting rule
```

## Step 5: Invalid Cells, Non-Scoreable Cells, And Catastrophic Misses

Define:

- what counts as invalid;
- what counts as non-scoreable;
- what counts as a policy violation;
- how each status enters primary metrics;
- required sensitivity analysis;
- maximum tolerated invalid/non-scoreable share, or explicit reason why a
  numeric cap is deferred;
- catastrophic-miss threshold and pass/fail rule.

M3 used a catastrophic gap threshold of `0.15`. Reuse it only if still
defensible after reading the current artifacts; otherwise record the new rule
and why it is better.

Acceptance evidence:

- invalid-cell and catastrophic-miss rules are included in the success-gate
  report and structured JSON;
- the rule prevents invalid-cell handling from changing a future claim after
  outcomes are known;
- policy violations allowed for primary claims are explicitly set.

Suggested commit:

```text
Define invalid-cell and catastrophic-miss rules
```

## Step 6: Joint Success Gate

Replace loose "margin or majority" logic with a joint gate.

The gate must cover:

- candidate beats the best eligible simple baseline by a meaningful MAE margin;
- candidate does not materially worsen catastrophic-miss rate;
- adapter rule passes or claim is narrowed before reporting;
- repo/window improvements are not concentrated in one favorable slice;
- fallback rule passes or claim is narrowed;
- invalid/non-scoreable sensitivity does not reverse the conclusion;
- candidate policy compliance passes;
- source-quality and endpoint/accounting checks pass;
- enough support exists for the intended claim.

Explicitly apply the proposed gate to current M3 evidence as a diagnostic:

- Does M3 pass the future gate?
- If not, which gate components fail or remain unresolved?
- What can still be used as proposal traction?

Acceptance evidence:

- success-gate JSON/report exist;
- M3 current-evidence pass/fail/diagnostic status is explicit;
- paid validation remains unauthorized even if a future gate is now defined;
- the gate cannot be satisfied by pooled improvement alone.

Suggested commit:

```text
Define joint validation success gate
```

## Step 7: Quantitative Support Thresholds

Set or explicitly defer quantitative support requirements for:

- minimum repos;
- minimum future tasks per repo;
- minimum adapters or named ACUT configurations;
- minimum future windows or rolling-origin cutoffs;
- maximum fallback share;
- maximum invalid/non-scoreable share;
- minimum independent source reservoirs if source mix affects the claim;
- required source-quality/certification fields.

Use M3 and the existing pilot as constraints, but do not tune thresholds to
make current evidence look stronger.

If a threshold requires user budget decisions, write it as a scenario or open
decision rather than a fixed ask.

Acceptance evidence:

- support-threshold JSON/report exist;
- thresholds say which future claims they support or block;
- user-owned budget/staffing numbers are not invented;
- insufficient support blocks primary predictive-validity claims.

Suggested commit:

```text
Define support thresholds for future validation
```

## Step 8: Release Artifact Schema

Define the minimal auditable benchmark release schema.

Include fields for:

- release ID and freeze commit;
- target repo, base commit, task ID, task source, source reservoir, source
  license status, and provenance digest;
- task statement path and solver-visible context path;
- oracle source, oracle path, hidden verifier path or digest, and oracle-source
  type;
- environment setup, dependency lock, and certification status;
- leakage checks and source-quality gates;
- candidate-policy ID, selected/not-selected status, fallback label, and
  fallback reason;
- split label, time cutoff, feature values, and tie-break value;
- ACUT adapter ID, endpoint compliance status, cost/latency accounting, and
  terminal status;
- score row digest and sanitized artifact manifest;
- raw artifact storage policy and ignored-path confirmation.

Tie each field to a claim function:

- reproducibility;
- source quality;
- outcome blindness;
- hidden-oracle protection;
- adapter accounting;
- future validation support;
- artifact hygiene.

Acceptance evidence:

- release-schema JSON/report exist;
- external candidates are untrusted until locally certified;
- generated/synthetic oracles are labeled separately from real changed tests;
- raw prompts, transcripts, workspaces, diffs, and hidden verifier material are
  not committed.

Suggested commit:

```text
Define benchmark release artifact schema
```

## Step 9: Validation-Design Figure Spec

Write a figure spec that M5 can render later.

The spec should show:

```text
task supply -> certification -> frozen candidate policy -> benchmark release
-> future ACUT run -> score join -> baseline comparison -> claim gate
```

Include the key freeze points:

- task supply/cutoffs;
- feature extraction;
- candidate policy;
- baselines and seeds;
- adapter estimand;
- invalid-cell rules;
- support thresholds;
- success gate.

Acceptance evidence:

- the summary document includes a figure spec;
- the spec distinguishes true-future/rolling-origin validation from
  pseudo-future replay;
- the spec is not a polished reviewer-facing figure unless the worker can do
  that without expanding scope.

Suggested commit:

```text
Add validation design figure spec
```

## Step 10: Power And Budget Note

Write a no-paid power/budget note.

The note should answer:

- what effect size future validation would need to detect to be persuasive;
- why the M3 edge is below or above the proposed future margin;
- how many cells a future run would roughly imply under simple scenarios;
- what prior pilot cost can and cannot imply;
- what remains user-owned, such as staffing, duration, and budget ceiling;
- why this note does not authorize paid validation.

Use the prior three-repo paid pilot cost only as historical context if useful:

```text
120 completed cells, cost $51.267333
```

Do not set a budget ceiling. That is a user decision before M6 or any
budget-bearing paid-validation discussion.

Acceptance evidence:

- power/budget JSON/report exist;
- detectable-effect or scenario reasoning is explicit;
- current M3 evidence is compared against the proposed future margin;
- no paid validation is authorized.

Suggested commit:

```text
Write no-paid power and budget note
```

## Step 11: Summary Document And Supporting Docs

Write:

```text
docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md
```

The summary should be proposal-facing but not the final proposal report. It
should contain:

- one-page M4 decision summary;
- study-mode claim table;
- candidate-policy and fallback decision;
- baseline registry summary;
- adapter estimand;
- joint gate;
- support thresholds;
- release schema pointer;
- figure spec pointer;
- power/budget note;
- readiness classification.

Update:

- `docs/research/phase-1-proposal-evidence-todo-matrix.md`
- `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`
- `PROCESS.md`

Do not rewrite `docs/research/phase-1-proposal-report-v1.md` into final prose.
If you add a short pointer there, keep it minimal and leave reviewer-ready
integration to M5.

Acceptance evidence:

- M4 outputs are discoverable from the roadmap and evidence matrix;
- `PROCESS.md` records the new handoff without copying evidence;
- M5 can start from the summary document without rereading every M4 artifact.

Suggested commit:

```text
Summarize M4 protocol hardening outputs
```

## Step 12: Verification And Closeout

Run the checks that match the files changed.

Required:

```text
python3 -m json.tool experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_preflight.json
python3 -m json.tool experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_decision.json
rg -n "proves predictive validity|established predictive validity|authorizes paid|paid validation authorized|validated predictive benchmark compiler|model-only superiority" docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_*.md
git diff --check
```

If a tool/test was added, also run:

```text
uv run pytest experiments/phase1_compiler/tests/test_phase1_validation_protocol_candidate_policy_hardening.py -q
```

The prohibited-claim grep should return no matches. If it returns matches
because the text is explicitly listing prohibited claims, rewrite the check or
the text so the closeout can clearly distinguish quoted prohibitions from
claims.

Closeout decision report must state:

- stop label;
- whether all M4-owned placeholders are filled, partially filled, or blocked;
- whether the current M3 candidate passes the hardened no-paid readiness gate;
- whether paid validation is authorized;
- whether predictive validity is established;
- whether user decisions are needed before M5;
- whether user decisions are needed before M6 or budget-bearing discussion;
- next recommended action category.

Suggested stop labels:

- `validation_protocol_candidate_policy_hardened`
- `validation_protocol_hardened_candidate_not_paid_ready`
- `blocked_fallback_policy_unresolved`
- `blocked_adapter_estimand_unresolved`
- `blocked_joint_gate_unresolved`
- `blocked_support_thresholds_unresolved`
- `blocked_release_schema_unresolved`
- `blocked_power_budget_note_unresolved`
- `blocked_claim_boundary_conflict`

Completing M4 with a "candidate not paid-ready" conclusion is a valid
successful closeout if the protocol rules are clear.

Suggested commit:

```text
Close M4 validation protocol hardening
```

## Completion Criteria

M4 is complete when:

- all M4-owned P0 placeholders are filled, explicitly narrowed, or blocked;
- the study-mode claim boundary prevents pseudo-future evidence from proving
  predictive validity;
- candidate-policy pseudocode and fallback governance are explicit;
- adapter-stratified reporting and estimand rules are explicit;
- future baselines and joint gate are explicit;
- invalid/non-scoreable/catastrophic-miss rules are explicit;
- source-support and release-schema requirements are explicit;
- the power/budget note exists without setting user-owned budget decisions;
- roadmap, evidence matrix, and `PROCESS.md` are synchronized;
- verification passes;
- closeout report records whether M5 can proceed.

## Expected Interpretation

Do not expect M4 to make the current evidence look stronger. The useful outcome
is a clean rule set:

```text
Here is what would count as future predictive-validity evidence.
Here is where current evidence falls short.
Here is what the proposal may safely claim now.
Here is what M5 must write plainly for reviewers.
```

That is enough progress for the proposal path even if the current candidate is
classified as not paid-ready.
