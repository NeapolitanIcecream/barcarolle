# Repository-Local Rich-W20 Blocked Status

Generated: 2026-05-15T03:48:22Z

Superseded: 2026-05-15T04:03:46Z. The Barcarolle transport remains blocked, but the same frozen `gpt-5.4-mini` route passed a minimal probe through the user's authenticated default Codex provider. Primary runs after that point use `--codex-provider-mode default`.

## Status

The reduced Rich-W20 protocol is preregistered and the live budget preflight passed, but full primary is not authorized.

The blocking condition is the live LLM route probe: the frozen cheap primary route `gpt-5.4-mini` is not serving Responses requests. Starting full primary would convert the experiment into infrastructure failures rather than ACUT behavior.

## What Ran

- Readiness and protocol checks passed for the reduced Rich-W20 design.
- The live budget preflight passed with projected cumulative estimated cost USD 204.217436, below the USD 240 soft stop and USD 300 hard cap.
- A small live primary attempt was started, then paused after route failures were identified.
- Before pause, 60 public normalized results and 64 private raw run directories had been written. These are excluded from primary scoring and require rerun after the route probe passes.

## Blocker

The required route probe for `gpt-5.4-mini` returned `no_available_distributor_channel`. Checked provider-prefixed alternates were not acceptable substitutes because they returned provider-policy rejection. No response text, credentials, endpoint value, raw commits, raw subjects, or reference patch bodies are recorded in this public report.

## Frozen Scan Acceptance

For this experiment, frozen scan acceptance means the pre-primary public artifacts prove:

- ACUT manifests and task identities are frozen before primary.
- Route policy and denominators are fixed before primary.
- Public artifacts do not expose raw commits, raw subjects, or reference patch bodies.
- Runner and budget gates pass.
- A live route probe for the frozen primary model passes.

The current result does not satisfy the final condition, so the experiment cannot formally start.

## Unblock

Restore or approve a serving live route for the frozen cheap primary model, regenerate the route probe with `status: passed`, then start the primary runner with 4 workers.
