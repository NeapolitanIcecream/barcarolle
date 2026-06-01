# Phase 1 Proposal Report V4 Agent-Tuning Integration Process

Status: complete, 2026-06-01.

This process report records execution evidence for
`docs/experiments/phase-1-proposal-report-v4-agent-tuning-integration-runbook.md`.

## Step 0: Preflight And Intent Check

Branch: `codex/restart-benchmark-compiler`.

HEAD at preflight:
`0300d243a84f9d8ddb2f72628b6eaef42c07fc6d`.

Date: `2026-06-01 16:31:19 CST`.

Starting worktree status:

```text
## codex/restart-benchmark-compiler...origin/codex/restart-benchmark-compiler [ahead 10]
 M PROCESS.md
 M docs/research/phase-1-proposal-roadmap-and-claim-planning.md
?? docs/experiments/phase-1-proposal-report-v4-agent-tuning-integration-runbook.md
```

The preexisting `PROCESS.md` and roadmap edits already describe the planned V4
agent-tuning integration. The untracked V4 runbook is the execution input for
this run. These starting changes are treated as user/coordinator context and
are not reverted.

Input availability: all required repository inputs, the 0519 local planning
file, and the current evidence reports named by the runbook were present at
preflight. The 0519 file was used as local source material only and must not be
cited as public literature support in V4.

Paid/external-call boundary:

- Paid ACUT solver cells run in this step: `0`.
- Paid LLM calls run in this step: `0`.
- External reviewer calls run in this step: `0`.
- Public browsing used in this step: `false`.
- Score tables, selected task IDs, split labels, source eligibility, task
  statements, hidden-oracle material, and completed experiment decisions
  changed: `false`.

Revision intent:

- `docs/research/phase-1-proposal-report-v3.md` is structurally accepted as the
  source draft and preserves the proposal report genre.
- V4 is a targeted application-path integration, not a full rewrite.
- Predictive validity remains the research north star and remains unproven.
- Agent tuning is the product pull: configuration selection, prompt/retrieval/
  skill/tool-policy tuning, regression monitoring, dev/eval/canary feedback,
  optimizer-readable scorecards, and failure taxonomies.
- Product-facing tuning outputs are deliverables, but formal evidence that
  Barcarolle improves tuning-loop outcomes remains a later validation target.
- Multi-ACUT residual predictive validity from the 0519 Phase 2 plan remains a
  later scientific extension, not the main body or proof burden of this
  proposal.

0519 context used:

- Phase 2 described residual predictive validity across paired ACUT
  configurations after accounting for general benchmark scores.
- Phase 3 described later tuning-loop validation using DSPy-style optimizer and
  SkVM-style skill-compiler comparisons.
- Product-value sections identified agent developers and repo owners as the
  readers who need repo-specific feedback for configuration selection, prompt
  and retriever changes, test-running policy, model upgrades, and regression
  monitoring.
- The milestone 5 material listed tuning interfaces such as optimizer feedback
  schemas and dev/eval/canary split management.
- The risk section warned that tuning can overfit the benchmark and should be
  guarded by dev/eval/canary/future-holdout separation, refresh, leakage
  checks, and uncertainty reporting.

Acceptance evidence: Step 0 complete. No proposal report text changed. No paid
or external calls made.

## Step 1: Map Existing V3 Tuning Content

Required search completed:

```text
rg -n "tuning|optimizer|scorecard|failure|regression|canary|dev/eval|configuration" docs/research/phase-1-proposal-report-v3.md
```

The compact section map is recorded in:
`experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_section_map.md`.

Mapping decision:

- V4 can be a targeted revision because V3 already has the right eleven-section
  proposal shape and contains hooks for configuration, tuning/evaluation
  objective, scorecards, failure labels, cost summaries, named ACUT
  configurations, and adapter-stratified reporting.
- The main additions should appear in the executive summary, problem/stakes,
  ACUT boundary, proposed design, validation guardrails, project plan, risks,
  deliverables, and appendix future-extension note.
- No V3 section requires a full rewrite.
- No new evidence requirement is introduced.
- Multi-ACUT residual predictive validity remains a later scientific extension.
- Formal agent-tuning-loop validation remains later product validation, not a
  current proof burden.

Acceptance evidence: Step 1 complete. The section map shows V4 can be a local
revision, preserves V3 structure, and introduces no new evidence claim.

## Step 2: Draft V4 From V3

Created `docs/research/phase-1-proposal-report-v4.md` from
`docs/research/phase-1-proposal-report-v3.md` and updated the title to V4.

Initial drafting baseline:

- V4 starts from V3 rather than from a new outline.
- The eleven-section proposal order is preserved.
- Numerical evidence and citation links are unchanged in the baseline copy.
- Predictive validity remains unproven in the copied claim boundary.

Acceptance evidence: V4 exists as a targeted-revision baseline. No substantive
agent-tuning edits have been applied yet.

## Step 3: Strengthen Product Pull In The Opening And Stakes

Revised the executive summary and problem/stakes section to make the practical
application path clear:

- teams need not only scores but configuration selection, prompt/retrieval/
  skill/tool-policy tuning, runtime-budget decisions, and regression monitoring;
- target-repository prediction remains the central problem;
- concrete stakes now include repo-docs retrievers, test-running policy,
  prompt/skill/retrieval changes, model or harness upgrades, and critical
  task-family regressions.

Acceptance evidence: the opening explains why Barcarolle matters beyond
evaluation reporting, still asks for project approval, and does not claim that
Barcarolle has already improved a tuning loop.

## Step 4: Integrate Tuning Interfaces Into Design And Deliverables

Revised the ACUT boundary, compiler design, project-plan work packages, and
deliverables:

- Barcarolle can emit benchmark releases, dev/eval/canary split metadata,
  scorecards, failure labels, regression signals, cost and latency summaries,
  and optimizer-readable result files.
- The ACUT harness or external optimizer still owns prompt, retrieval, skill,
  tool, public-test-policy, model, and runtime-budget changes.
- The project plan now includes tuning and regression feedback interfaces as
  schemas and templates, not as a current tuning-success claim.
- Expected deliverables now include optimizer-readable scorecard schemas,
  configuration-comparison templates, a split manager, tuning/regression report
  templates, failure taxonomy, and canary/holdout rules.

Acceptance evidence: the design section explains product-facing tuning
artifacts while preserving the ACUT boundary.

## Step 5: Add Tuning-Overfit Guardrails

Added validation and risk language explaining that tuning workflows need
dev/eval/canary or holdout separation because optimizer loops can overfit
visible benchmark dev tasks.

Mitigations now include:

- separate dev, eval, canary, and future holdout material;
- frozen evaluation releases before formal score joins;
- source and task-family slice reporting;
- private/canary protection where needed;
- release refresh governance;
- explicit separation between tuning feedback and formal predictive-validity
  claims.

Acceptance evidence: V4 makes tuning useful but guarded, and no tuning-loop
result is invented.

## Step 6: Keep Later Extensions Scoped

Added a short Appendix C future-extension note. It says a later scientific
extension can test residual predictive signal across multiple paired ACUT
configurations, and a later product-validation extension can test whether
Barcarolle feedback improves tuning-loop outcomes.

Acceptance evidence: these are explicitly later extensions and are not project
approval requirements.

## Step 7: Update Checklist And Handoff Documents

Updated:

- `docs/research/phase-1-proposal-report-reviewer-ready-checklist.md`
- `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`

The checklist now checks V4-specific readiness:

- V4 preserves V3 structure and claim boundary;
- agent tuning is integrated as the product/application path;
- tuning-loop improvement is not claimed as established;
- later residual predictive-validity and formal tuning-loop validation
  extensions are not promoted into the main project scope;
- paid evaluation remains budgeted and gated;
- artifact hygiene is unchanged.

The roadmap now records V4 as complete and identifies
`docs/research/phase-1-proposal-report-v4.md` as the active proposal report for
proposal use. `PROCESS.md` will be updated in the closeout step so it can point
at the final decision artifact.

Acceptance evidence: handoff docs point to V4, and M6 remains gated on V4
acceptance plus user/coordinator decisions.

## Step 8: Audit

Required checks:

```text
rg -n "Phase 3|Phase 2|multi-ACUT residual|tuning validation established|improves agent tuning|proves tuning|validated predictive benchmark compiler|established predictive validity" docs/research/phase-1-proposal-report-v4.md
rg -n "/Users/chenmohan/Downloads" docs/research/phase-1-proposal-report-v4.md
git diff --check
```

Recorded results:

- Prohibited-scope and prohibited-claim check: `pass_no_matches`.
- Local planning path check: `pass_no_matches`.
- `git diff --check`: `pass`.
- Eleven-section shape check: `pass`; V4 preserves sections 1 through 11 from
  V3.
- Evidence-number spot check: `pass`; V4 preserves the key values `0.3148`,
  `0.7481`, `0.25`, `0.125`, `120/120`, `30/30`, `0.209`, `0.2149`, `0.0059`,
  `93.4%`, `6/18`, and `6/6`.

Manual review answers:

- V4 makes the product value clearer than V3: `yes`.
- V4 avoids turning the proposal into a tuning-validation plan: `yes`.
- V4 preserves predictive validity as the north star: `yes`.
- V4 makes tuning outputs useful while keeping the ACUT boundary intact: `yes`.
- V4 avoids adding new evidence burdens before approval: `yes`.

Acceptance evidence: Step 8 passed with no acceptable-match exceptions.

## Step 9: Closeout

Wrote:

- `experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_integration_process.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_integration_decision.md`
- `experiments/phase1_compiler/results/phase1_proposal_report_v4_agent_tuning_integration_decision.json`

Stop label:

```text
proposal_report_v4_agent_tuning_integration_complete
```

Closeout decision:

- V4 supersedes V3 as the active proposal report for proposal use.
- V3's structure and claim boundary were preserved.
- Agent tuning was integrated as the product/application path through
  configuration selection, regression feedback, dev/eval/canary splits,
  optimizer-readable scorecards, failure taxonomy, and tuning/report templates.
- Tuning-loop improvement remains unproven.
- Later residual predictive-validity and formal tuning-loop validation work
  remain future extensions.
- M6 or another approval artifact should wait for user/coordinator acceptance
  of V4 plus decisions on artifact format, staffing/duration, budget ceiling,
  and reviewer-facing owner categories.

Acceptance evidence: runbook closeout artifacts are complete.
