# Post-Pilot-008 Transport/Harness Options

status: no_model_options_recorded_option_c_spike_completed
recorded_at: 2026-05-06T21:55:01+08:00
updated: 2026-05-06T23:51:30+08:00
option_c_spike: `experiments/core_narrative/reports/post_pilot_008_option_c_no_model_spike.md`
related_decision: `.codex-workflows/core-narrative-experiment/decisions/post-pilot-008-transport-gate.md`

## Purpose

Record no-model options after pilots 006/007/008 showed a treatment-independent and model-tier-independent pre-verifier failure on the current Codex CLI Responses streaming patch-generation path.

This note does not authorize a live BARCAROLLE model call. It is the static planning artifact required before the coordinator can decide whether any future one-run probe is worth proposing.

## Admission Rubric For Any Option

An option can be considered for a future live call only if no-model review first shows all of the following:

1. It is materially different from the current failing Codex CLI Responses streaming path.
2. It preserves the outer `acut_patch_adapter.py` responsibilities: budget gate, cost ledger append, redaction, result normalization, verifier gating, and one-primary-attempt policy.
3. It can produce a verifier-ready workspace patch or an explicit `infra_failed` result without weakening the 2x2 ACUT control contract.
4. It records no credential values, bearer tokens, resolved secrets, full base URLs, hostnames, or IP addresses.
5. It can be dry-run or mock-tested without a live BARCAROLLE model call before any proposed live probe.

## Options

### Option A — Continue Current Codex CLI Responses Streaming Path

Status: rejected for further live attempts.

Reason: pilots 006/007/008 already exercised the current path across cheap specialist, cheap generic, and frontier generic cells. Another same-path run would spend budget without a new capability or transport hypothesis.

### Option B — Bounded Output/Context Profile On Codex CLI Path

Status: possible no-model spike only.

Hypothesis: a materially smaller output/context envelope could avoid the observed streaming disconnect while preserving patch-generation semantics.

No-model evidence needed before any live call:

- command construction proves lower output/turn/context limits are actually enforced;
- dry-run artifact shows the exact prompt/context profile and preserves generic-vs-specialist context controls;
- adapter tests show unchanged handling for timeout, nonzero exit, empty patch, unsafe patch, and verifier-ready patch outcomes.

Risk: this may still be the same Responses streaming path. It is admissible only if the bounded profile is documented as materially different and reviewed before a live probe.

### Option C — Alternate Non-Streaming Patch-Generation Transport

Status: preferred no-model design direction; initial no-model spike completed at `experiments/core_narrative/reports/post_pilot_008_option_c_no_model_spike.md`. Not live-authorized.

Hypothesis: replace only the inner patch-generation command with a BARCAROLLE-env-only non-streaming request path while keeping the outer adapter unchanged. The repo already has this direct command (`experiments/core_narrative/tools/barcarolle_patch_command.py`), and the spike adds executable mock/dry-run/adapter-wrap specs for it.

No-model evidence needed before any live call:

- mock transport proves request/response shaping without network;
- code path consumes only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` by environment-variable name;
- redaction tests cover credentials, authorization headers, full URLs, hostnames, IP-like strings, stdout/stderr tails, and saved artifacts;
- result normalization remains compatible with existing raw/normalized schema and verifier gating;
- command template can target the same ACUT/task inputs without leaking gold patches or task-specific specialist context.

Risk: direct transport code may duplicate Codex CLI behavior and needs focused review to avoid silently changing the evaluated ACUT envelope. Existing pilots 001/002/003 also show that the direct command path previously failed live before verifier with redacted `gaierror`; any future probe must explain why it is not just a repeat of that direct-path failure family as well as not a repeat of pilots 006/007/008.

### Option D — Patch-Only Artifact Contract With Mockable Agent Boundary

Status: possible no-model design direction.

Hypothesis: define a stricter inner-agent contract that returns a patch artifact through a mockable boundary, reducing dependence on CLI streaming behavior.

No-model evidence needed before any live call:

- mock agent can return success, empty patch, unsafe patch, timeout, and nonzero/transport failure fixtures;
- adapter can distinguish verifier-ready patch from no-patch infra failure;
- actual future model call would still be a single named ACUT patch-generation attempt with ledger and redaction gates.

Risk: if the contract abstracts away too much native CLI behavior, it may weaken the ACUT/native-runtime interpretation. Review must explicitly preserve the intended subject.

### Option E — Pause Live Execution And Report No Scoreable Result

Status: always safe.

Hypothesis: the current evidence is enough to report an infrastructure/transport blocker and stop budget spend until a stronger transport implementation exists.

No-model evidence needed: none beyond the current decision record, manifest gate, and coordinator cleanup.

Risk: produces no ACUT ranking signal, but avoids misleading capability conclusions and unnecessary spend.

## Recommended Next No-Model Step

Review the completed Option C no-model spike first. If it passes review, the next coordinator decision is still either pause/report no scoreable result, or prepare a separate no-secret operational-readiness record for exactly one future direct-transport probe. That record must satisfy the post-pilot-008 gate and explain why the proposal is not another direct-command `gaierror` repeat or Codex CLI Responses streaming repeat. No live BARCAROLLE model call is authorized by this options note.
