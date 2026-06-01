# Barcarolle Approval Packet Executive Summary V1

Status: decision-facing summary, 2026-06-01.

## Decision Requested

Approve Barcarolle as a repo-specific benchmark-compiler project. Approval
would authorize work on benchmark-selection algorithms, task certification,
versioned releases, validation protocols, reporting, and tuning-facing
interfaces under a strict claim boundary: current evidence supplies traction
and a credible validation path, but it does not establish formal predictive
validity.

## Why This Matters

Teams deploy coding agents into their own repositories, where future issues,
APIs, tests, dependencies, review norms, and failure modes can differ from the
public benchmark distribution. A benchmark can be executable and fair while
still being weak evidence for whether a named agent configuration will work on
future tasks in the repository that matters.

## What Barcarolle Is

Barcarolle sits at the benchmark-construction layer. It selects, certifies,
splits, weights or leaves unweighted, refreshes, and interprets repo-specific
benchmark releases. The ACUT keeps control of its own harness: file search,
editing strategy, prompts, tools, model choice, retry policy, runtime budget,
and trace internals.

## Current Evidence

Current evidence is strong enough for project approval, not for a completed
validity claim.

- Naive weighting failed materially, with weighted gaps of `0.3148` for attrs
  and `0.7481` for boltons versus simple same-budget baselines of `0.25` and
  `0.125`.
- Benchmark-side execution is feasible: the three-repo pilot completed
  `120/120` exploratory cells with scoreability `1.0`.
- Source-quality repair is tractable: click source context was repaired for
  `30/30` frozen tasks.
- The current candidate shows directional traction: aggregate MAE `0.209`
  versus best simple aggregate baseline `0.2149`, and it beats or ties `93.4%`
  of 1000 same-budget random selections.

## What Remains Unproven

Predictive validity remains unproven. The best-simple-baseline edge is only
`0.0059` MAE, adapter and repository slices are fragile, and `6/18` selected
slots use fallback, including `6/6` boltons slots. Barcarolle also has not
proven that its feedback improves an agent tuning loop. Those are validation
targets for the approved project, not current claims.

## Approved-Project Work

The approved project would build improved selection rules, certification gates,
release manifests, baseline suites, future or preregistered rolling-origin
validation protocols, adapter-stratified scorecards, uncertainty and fallback
reports, and optimizer-readable tuning and regression interfaces. The output is
a versioned benchmark release and evidence model, not a replacement ACUT
harness, generic task factory, or public leaderboard.

## Budget And Validation Gates

Evaluation spending should begin only after the benchmark release,
task-selection rule, baseline suite, score-join procedure, named ACUT
configurations, invalid-cell rules, and success criteria are frozen. Paid
evaluation is a gated project resource, not open-ended exploration.

User-owned values remain open:

- `[NEEDS USER DECISION: project staffing]`
- `[NEEDS USER DECISION: project duration]`
- `[NEEDS USER DECISION: gated ACUT evaluation budget ceiling]`
- `[NEEDS USER DECISION: approval path or approving owner]`

## Expected Decision Outcome

Approve the project under the stated claim boundary, fill the user-owned
resource placeholders before reviewer circulation, and use V5 as the
source-of-truth long-form report behind this approval packet.
