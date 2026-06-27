# Agent Tuning Phase 1 Feasibility Runbook 2026-06-14

Status: mandatory Phase 1 runbook for preparing the Agent Tuning Demo. This
runbook must complete all preparation required before Phase 2 artifact tuning.

Phase 1 is not an Agent tuning experiment. It does not run GEPA, DSPy, Phoenix,
or another optimizer as the main experiment. Its job is to answer the gating
question:

> Can tuner-produced artifacts be injected into real workspace Coding Agents,
> and can Barcarolle observe behavior changes caused by those artifacts?

If Phase 1 cannot show at least one reliable real-Agent injection path and one
observable behavior-change path, do not proceed to Phase 2 on Codex/Kilo-style
Agents. Recommend a tuner-native fallback instead.

## Current Context

Barcarolle has completed an Agent-selection demo on `mahmoud/boltons`.

The current reader-facing result is:

- mainline selector: HRD v3 `70/30`, `k=10`;
- Selection recommends `Kilo + GPT mainline`;
- Holdout and doubled-timeout top-2 repeat also show `Kilo + GPT mainline`
  ahead;
- this supports a demo-level Agent-selection story, not full predictive
  validity.

The next product direction is Agent Tuning. The desired long-term story is:

> Barcarolle turns target-repo Agent failures into tuning feedback and validates
> whether the tuned Agent actually improves on held-out target-repo tasks.

The immediate risk is that many Agent tuners cannot tune arbitrary opaque CLI
Agents. They usually tune prompts, rules, skills, policies, tool schemas, or
framework-native workflows. Phase 1 must establish which of those artifacts can
actually be injected into the Agents Barcarolle can run.

## Target Outcome

Phase 1 is complete only when it produces a clear readiness decision:

- recommended primary path for Phase 2;
- recommended fallback path if real-Agent artifact tuning is not feasible;
- recommended Agent and tuning surface;
- artifact schema and injection records;
- proof-of-injection results;
- behavior-change smoke-test results;
- tuner compatibility study;
- leakage and artifact-hygiene boundaries.

The preferred primary path is expected to be:

```text
GEPA or Phoenix-style proposer -> repo-specific SKILL.md / rules / AGENTS.md
artifact -> Codex/Kilo-style workspace Agent -> Barcarolle before/after
validation
```

But the executing Agent must verify this, not assume it.

## Non-Goals

- Do not run the full Agent Tuning Demo.
- Do not optimize with GEPA, DSPy, Phoenix, Opik, TextGrad, ProTeGi, or SKVM as
  the main experiment.
- Do not claim any tuned Agent improvement.
- Do not compare many tuned variants on Holdout.
- Do not expose Holdout hidden details to any proposer or optimizer.
- Do not claim that Barcarolle tunes full black-box Agents end to end.
- Do not claim that DSPy tunes Codex/Kilo unless a real bridge is implemented
  and verified.
- Do not turn this into a large framework integration project.

## Required Reading

Read before changing code or writing new reports:

- `AGENTS.md`
- `PROCESS.md`
- `docs/research/agent-selection-demo-branch-summary-2026-06-14.md`
- `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`
- `experiments/agent_selection_demo/tools/agent_selection_demo.py`
- `experiments/phase0_headroom/tools/workspace_acut_run.py`
- `experiments/phase0_headroom/tools/codex_workspace_adapter.py`
- `experiments/phase0_headroom/tools/kilo_workspace_adapter.py`
- `experiments/phase0_headroom/tools/llm_endpoint_proxy.py`
- `/Users/chenmohan/Downloads/barcarolle-research-0614-1.md` if present
- `/Users/chenmohan/Downloads/barcarolle-research-0614-2.md` if present

Use the two GPT-5.5-Pro reports as research guidance, not as source code.

## Directory Layout

Create the Phase 1 work under:

```text
experiments/agent_tuning_demo/
  config/
  reports/
  results/
  schemas/
  tests/
  tools/
```

Do not commit solver workspaces, verifier workspaces, raw transcripts, raw
prompts, raw completions, secrets, `.venv`, caches, or cloned external repos.

## Package 1: Context Audit

Goal: understand what can be reused from current Barcarolle Agent execution.

Tasks:

1. Inspect current Agent-selection demo tooling and phase0 workspace adapters.
2. Identify how Codex-style and Kilo-style Agents are represented.
3. Identify where task text, workspace paths, environment variables, timeouts,
   model identifiers, and cost/usage records are controlled.
4. Identify whether current runners can add files to the solver workspace before
   Agent invocation.
5. Identify trace fields that can show behavior change without committing raw
   transcripts.

Deliverables:

- `docs/research/agent-tuning-feasibility-plan-2026-06-14.md`
- `experiments/agent_tuning_demo/reports/context_audit_zh.md`
- `experiments/agent_tuning_demo/results/context_audit.json`

Acceptance:

- The report states which existing code paths are reusable.
- The report states whether new helper code is needed for artifact injection.
- The report records current paid-call boundary and hygiene rules.

Commit after this package.

## Package 2: Tuning Surface Inventory

Goal: build a concrete matrix of tunable surfaces for real Agents.

Check at least these surfaces:

- repo `AGENTS.md`;
- Codex skills;
- Kilo `AGENTS.md`;
- Kilo `.kilo/rules/*.md`;
- Kilo `.kilo/skills/*/SKILL.md`;
- harness-level prompt/context, if available;
- runtime policy, including timeout, public-test policy, retry, and self-check;
- model selection / reasoning effort, but mark it as a separate Agent-selection
  knob unless Phase 2 explicitly chooses policy optimization.

Produce a matrix with columns:

```text
agent_id
surface
artifact_type
can_inject
can_observe_loaded
can_affect_behavior
requires_adapter_change
expected_optimizer_output
risk
recommended_for_phase2
notes
```

Deliverables:

- `experiments/agent_tuning_demo/reports/tuning_surface_inventory_zh.md`
- `experiments/agent_tuning_demo/results/tuning_surface_inventory.json`

Acceptance:

- Codex and Kilo are both assessed.
- Unsupported or risky surfaces are recorded instead of silently skipped.
- The report distinguishes hard policy controls from soft instruction surfaces.

Commit after this package.

## Package 3: Artifact Schema And Injection Records

Goal: define the artifact format that Phase 2 optimizers/proposers can output.

Define a JSON schema supporting at least:

- `agents_md_appendix`;
- `skill_md`;
- `kilo_rule`;
- `policy_snippet`.

Each artifact record must include:

```text
artifact_id
artifact_type
target_agent
changed_files
hash
intended_effect
rollback_plan
optimizer_source
visible_to_optimizer
holdout_derived
```

Define an injection record with:

```text
run_id
artifact_id
artifact_hash
target_agent
surface
workspace_relative_paths
injected_at
cleanup_policy
```

Implement helper code only if existing tooling cannot materialize artifacts
safely. Keep helpers small and testable.

Deliverables:

- `experiments/agent_tuning_demo/schemas/tuning_artifact.schema.json`
- `experiments/agent_tuning_demo/schemas/artifact_injection_record.schema.json`
- `experiments/agent_tuning_demo/reports/tuning_artifact_schema_zh.md`
- optional helper under `experiments/agent_tuning_demo/tools/`

Acceptance:

- Schemas validate example artifacts.
- Artifacts can be hashed deterministically.
- Injection records are sanitized and do not contain raw prompts or secrets.

Commit after this package.

## Package 4: Proof-Of-Injection Smoke Tests

Goal: prove the Agent can actually see the injected artifact.

Prefer no-paid or minimal harmless runs. If a paid Agent call is unavoidable,
use the smallest harmless task and record cost. All paid calls must use
`LLM_BASE_URL` and `LLM_API_KEY`.

Codex checks:

1. `AGENTS.md` smoke test with a fixed phrase such as
   `BARCAROLLE_INJECTION_ACTIVE`.
2. Codex skill explicit-trigger smoke test.
3. Codex skill implicit-trigger smoke test if feasible.

Kilo checks:

1. Kilo `AGENTS.md` or rules smoke test.
2. Kilo skill explicit-trigger smoke test if feasible.
3. Kilo skill implicit-trigger smoke test if feasible.

For each smoke test record:

```text
surface
artifact_path
agent_id
run_mode
paid_call_used
loaded_observed
observation_method
notes
```

Deliverables:

- `experiments/agent_tuning_demo/reports/injection_smoke_tests_zh.md`
- `experiments/agent_tuning_demo/results/injection_smoke_tests.json`
- tests for any new helper code

Acceptance:

- At least one real Agent has a passing proof-of-injection path, or the runbook
  records a hard blocker.
- Unsupported surfaces are marked `unsupported` or `risky`, not treated as
  success.
- Raw transcripts are not committed.

Commit after this package.

## Package 5: Behavior-Change Smoke Test

Goal: prove artifact injection can change observable Agent behavior and that
Barcarolle can record the difference.

Create two controlled artifacts:

- Variant A: instruct the Agent not to run tests.
- Variant B: instruct the Agent to run a specified public test after editing.

Run both variants on the same tiny fixture task or harmless small task. Prefer a
task where public-test behavior can be observed cheaply.

Record whether these differ:

- command trace;
- file reads;
- file edits;
- diff;
- public-test execution;
- cost;
- latency;
- terminal status.

Use sanitized summaries only. Do not commit raw transcripts.

Deliverables:

- `experiments/agent_tuning_demo/reports/behavior_change_smoke_test_zh.md`
- `experiments/agent_tuning_demo/results/behavior_change_smoke_test.json`

Acceptance:

- At least one real Agent shows an observable behavior difference between
  Variant A and Variant B; or
- the report explains why real-Agent artifact injection cannot yet drive
  observable behavior and recommends the tuner-native fallback.

Commit after this package.

## Package 6: Tuner Compatibility Study

Goal: decide which optimizers can be used in Phase 2 and how.

Research and record at least:

- GEPA;
- Phoenix Prompt Learning;
- DSPy;
- Opik Agent Optimizer;
- TextGrad;
- ProTeGi;
- SKVM / SkillRT-style systems;
- SkillOpt-style systems if useful.

For each, answer:

```text
tunable_unit
requires_native_framework
can_optimize_opaque_cli_agent
can_use_barcarolle_scalar_feedback
can_use_traces_diffs_failure_labels
output_artifact
can_inject_into_codex_kilo
phase2_role
integration_risk
```

Expected framing:

- GEPA and Phoenix are likely proposers for `SKILL.md` / rules artifacts.
- DSPy is likely a tuner-native fallback, not a direct Codex/Kilo tuner.
- Opik/TextGrad/ProTeGi are likely proposer or future integration candidates.
- SKVM/SkillRT is likely future skill-runtime direction, not the first MVP
  optimizer.

Deliverables:

- `docs/research/agent-tuning-tuner-compatibility-2026-06-14.md`
- `experiments/agent_tuning_demo/results/tuner_compatibility_matrix.json`

Acceptance:

- The study directly answers whether each tuner output can be injected into
  Codex/Kilo-style Agents.
- It distinguishes "tunes deployable artifact" from "tunes full Agent".
- It gives one recommended primary optimizer/proposer and one fallback path.

Commit after this package.

## Package 7: Phase 2 Readiness Gate

Goal: produce the final Phase 1 closeout and Phase 2 recommendation.

The closeout must answer:

1. Can at least one real Agent reliably receive a tuning artifact?
2. Can Barcarolle observe artifact-driven behavior change?
3. Which Agent should Phase 2 use first?
4. Which artifact surface should Phase 2 use first?
5. Which optimizer/proposer should Phase 2 use first?
6. Which repo/task pool should Phase 2 use?
7. What is the fallback if real-Agent artifact tuning is not feasible?
8. What leakage controls are required before Phase 2 starts?
9. What is the exact claim Phase 2 may attempt?
10. What claims remain out of scope?

Recommended output states:

- `ready_for_phase2_real_agent_artifact_tuning`;
- `ready_for_phase2_with_restrictions`;
- `not_ready_use_tuner_native_fallback`;
- `blocked`.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase1_feasibility_closeout_zh.md`
- `experiments/agent_tuning_demo/results/phase1_feasibility_closeout.json`
- update `PROCESS.md` with only the current effective decision and links

Acceptance:

- The readiness state is explicit.
- The recommended Phase 2 route is specific enough for a new runbook.
- The report does not overclaim tuning effectiveness.

Commit after this package.

## Validation And Hygiene

Run at minimum:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
uv run --project experiments/phase0_headroom pytest experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_acut_run.py -q
git diff --check
```

If no `experiments/agent_tuning_demo/tests` exist because no code was added,
state that explicitly and run the applicable phase0 tests and `git diff
--check`.

Artifact hygiene checks:

```text
git ls-files experiments/agent_tuning_demo | rg '(\.venv|\.pytest_cache|\.DS_Store|raw|transcript|workspace|secret|prompt|completion)' || true
git diff --cached --name-only | rg '(\.venv|\.pytest_cache|\.DS_Store|raw|transcript|workspace|secret)' || true
```

Manually inspect any hits. Some words may appear in report names or policy
descriptions; raw artifacts must not be committed.

## Paid-Call Boundary

Default to no-paid tests and dry runs. If a paid call is necessary for a real
proof-of-injection smoke test:

- use the smallest harmless task;
- use only `LLM_BASE_URL` and `LLM_API_KEY`;
- record paid cells and estimated cost;
- keep raw transcripts/workspaces in ignored paths;
- commit only sanitized summaries.

Do not run Phase 2 tuning paid cells in this runbook.

## Final Closeout Requirements

The final response and closeout report must include:

- files changed and commits made;
- surfaces tested;
- surfaces that passed proof-of-injection;
- surfaces that were unsupported or risky;
- behavior-change evidence;
- tuner compatibility recommendation;
- Phase 2 readiness state;
- recommended Phase 2 path and fallback path;
- tests and hygiene checks;
- exact claims supported and unsupported.
