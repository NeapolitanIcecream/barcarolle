# Barcarolle Phase 1 Task Generator Design External Review Bundle

This is a sanitized evidence package for an external GPT-5.5-Pro review.

Please answer in Chinese, while keeping important technical terms in English
where that is clearer.

## Review Goal

We need a hard technical review of Barcarolle's current Task Generator / Task
Source Adapter design.

The central question:

```text
Is our current task supply pipeline too weak, and what should we use next:
an external upstream task generator such as SWE-Bench++ or SWE-smith, a stronger
internal repo-history generator, or a hybrid design?
```

We do not need encouragement. We need a concrete recommendation that can guide
the next local-only runbook and the next implementation.

## Required External Research

Before answering, please research or recall the current state of at least these
systems and cite sources if web access is available:

```text
SWE-Bench++
SWE-smith
SWE-bench-Live
SWE-Gym
R2E-Gym
SWE-bench / SWE-bench Verified / SWE-bench Pro where relevant
```

The review should not merely summarize them. Use them to decide what Barcarolle
should adopt, adapt, avoid, or implement internally.

## Project Framing

Barcarolle is not meant to be another general-purpose SWE task generator.
Barcarolle is a target-repository benchmark compiler:

```text
candidate task sources + certification + target profile + assembly/weighting
  -> small calibrated repo-specific benchmark release
  -> predicts held-out future work for a target repo and agent family
```

Task generation is Layer 1 supply infrastructure. Stronger upstream generators
make Barcarolle better, but the core research claim is benchmark compilation
and predictive validity, not raw task production.

This distinction matters. If you recommend building a stronger generator, frame
it as supply infrastructure and define how to evaluate it by:

```text
raw anchor yield
candidate yield
environment reconstruction rate
oracle extraction rate
source-context quality
statement quality
certification yield
cost
auditability
```

## Current Situation

Our current generator is intentionally thin. It is mostly a repo-history source
adapter:

```text
git history mining
  -> commits that change implementation files and test files
  -> path/subject/size filters
  -> public PR title/body or commit-message context
  -> template solver-facing statement
  -> local certification gates
```

It does not currently have a full SWE-Bench++-style environment synthesis and
oracle extraction pipeline. It does not have a strong endpoint-compliant LLM
statement generation/review loop in the latest supply expansion. It also does
not yet use multiple independent task sources as required by the research plan.

Recent evidence:

```text
Two-repo supply expansion:
  attrs total eligible after expansion:   20
  boltons total eligible after expansion: 27
  target: at least 30 per repo

Reference-pass failure audit:
  no sampled local validation-code bug found
  many failures were old-environment problems

Historical environment synthesis:
  sampled known failures: 36
  recovered reference_pass: 8
  confirmed recovered eligible:
    attrs:   +2 -> projected total 22
    boltons: +4 -> projected total 31
  conclusion: attrs/boltons still not enough

Third-repo local gate using existing artifacts:
  toolz:    16 candidates, 6 certified
  humanize: 16 candidates, 12 certified
  neither reached the 30-certified-task gate
```

Important interpretation:

```text
The toolz/humanize result should not be read as "these repos have no supply."
It only says the existing local artifacts are too narrow. The Task Generator
may simply not have done enough work.
```

## Constraints

Please respect these constraints in your recommendation:

- Do not redesign Barcarolle as an ACUT agent harness.
- Do not make task generation the core research claim.
- Do not use hidden oracle material, raw ACUT transcripts, raw prompts, or raw
  completions for task selection or statement writing.
- If paid LLM calls are proposed, they must be through `LLM_BASE_URL` and
  `LLM_API_KEY`; do not rely on local ChatGPT/Codex subscription auth for
  scoreable experiment work.
- Prefer mature modern stacks over bespoke infrastructure when they improve
  auditability and reproducibility.
- Keep raw workspaces, raw logs, target clones, and caches out of committed
  artifacts.

## Key Files To Read First

Start with:

```text
TASK_GENERATOR_PROBLEM_BRIEF.md
background/research-proposal-0519.md
background/research-plan-0526.md
background/system-design.md
reports/phase1_two_repo_supply_expansion_decision.md
reports/phase1_reference_pass_failure_audit_decision.md
reports/phase1_historical_environment_synthesis_decision.md
reports/phase1_third_repo_environment_gate_screen.md
code/repo_history_pilot.py
code/phase1_two_repo_certified_supply_expansion.py
code/phase1_historical_environment_synthesis_gate.py
```

Then inspect candidate artifacts if needed:

```text
candidate_artifacts/toolz_*
candidate_artifacts/humanize_*
candidate_artifacts/attrs_supply_expansion_20260526_*
candidate_artifacts/boltons_supply_expansion_20260526_*
```

## Questions For Review

Please answer these questions directly.

1. Diagnosis:
   Is the current Task Generator / source adapter likely too weak? If yes,
   what exactly is weak: candidate mining, source-context retrieval, statement
   writing, environment reconstruction, oracle extraction, certification, repo
   choice, or compute budget?

2. Evidence interpretation:
   The latest runbook completed quickly and only screened existing toolz and
   humanize artifacts. What can and cannot be concluded from that result?

3. External option analysis:
   Compare SWE-Bench++, SWE-smith, SWE-bench-Live, SWE-Gym, R2E-Gym, and any
   other relevant systems as upstream sources for Barcarolle. Which are usable
   now, which are research references only, and which would be too costly or
   misaligned?

4. Build vs adopt vs hybrid:
   Recommend one of:
   - adopt an external generator/source as default;
   - build a stronger internal generator;
   - use a hybrid design.

   Give the reason, risks, cost, and implementation path.

5. Internal design if needed:
   If you recommend building or extending our generator, propose a concrete
   architecture. Include:
   - candidate source types;
   - history/PR/issue mining;
   - environment synthesis;
   - oracle extraction;
   - solver-facing statement generation;
   - leakage and ambiguity review;
   - certification gates;
   - artifact schema;
   - how to avoid overfitting to the current repos.

6. External integration design:
   If you recommend external sources, describe the adapter schema, trust
   boundary, required QA gates, deduplication policy, and how Barcarolle should
   mix external and internal task pools.

7. Next local-only runbook:
   Design the next runbook. It should compare Task Generator options before
   paid ACUT calls. Include metrics, thresholds, sample sizes, stop/go rules,
   and expected outputs.

8. Modern stack:
   Recommend libraries/tools for mining, environment synthesis, task metadata,
   optimization, storage, and review workflows. Say where bespoke code is still
   justified.

9. Final recommendation:
   What should we do next week? Be concrete. Include a prioritized 3-step plan.

## Output Format Requested

Please structure your answer as:

```text
1. Executive answer
2. What the current evidence really proves
3. Diagnosis of current generator weakness
4. External generator/source comparison table
5. Recommended architecture
6. Next local-only runbook
7. Stop/go thresholds before paid validation
8. Risks and mitigations
9. Three-step implementation plan
```

Separate high-confidence claims from speculative claims. If you recommend an
algorithm or architecture, give pseudocode or a concrete implementation outline.

## Bundle Map

```text
background/          project framing and research plans
runbooks/            runbooks that produced current task-supply evidence
code/                current task mining, certification, and env replay tools
configs/             repo list and environment replay configs
inputs/              compact input summaries
reports/             human-readable results
results/             machine-readable results
candidate_artifacts/ selected current candidate/task artifacts
TASK_GENERATOR_PROBLEM_BRIEF.md
MANIFEST.sha256
```

No raw ACUT transcripts, raw prompts, raw completions, solver workspaces,
verifier workspaces, hidden oracle files, secrets, or raw local target clones
are intended to be included. Some copied runbooks may mention the original
local repository root as execution context; treat those paths as non-secret
local provenance, not as required paths on your machine.
