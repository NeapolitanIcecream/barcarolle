# Prompt For Agent Tuning Phase 2 Agent

Please execute this runbook end to end:

```text
/Users/chenmohan/gits/barcarolle/docs/research/agent-tuning-phase2-action-preflight-and-artifact-tuning-runbook-2026-06-15.md
```

The goal is to complete Agent Tuning Demo Phase 2: first prove action-level
behavior change from a repo-local tuning artifact, then, only if that gate
passes, run a bounded artifact-tuning loop and frozen Holdout before/after
validation.

Do not treat Phase 1 request-context evidence as enough. The first hard gate is
action-level preflight: command execution, public-test marker, file read/edit,
diff, or public-test behavior must differ because of the injected artifact. If
that gate fails, do not run GEPA/Phoenix optimization; close with the fallback
recommendation required by the runbook.

Use the runbook's default path unless evidence forces a fallback:

```text
GEPA standalone / optimize_anything -> one Kilo repo AGENTS.md appendix ->
Kilo workspace Agent -> Barcarolle Selection-dev and Holdout validation
```

Keep Holdout invisible until the chosen artifact hash is frozen. Do not tune
multiple surfaces at once. Do not claim full black-box Agent tuning, model
fine-tuning, predictive validity, cross-repo generalization, or GEPA/Phoenix
superiority.

All paid LLM or Agent calls, if any, must use `LLM_BASE_URL` plus
`LLM_API_KEY`. Prefer no-paid/local checks where possible, stay within the
runbook's paid-cell caps, and commit only sanitized reports, summaries, schemas,
and manifests. Never commit raw prompts, completions, transcripts,
solver/verifier workspaces, secrets, caches, or large raw outputs.

Work autonomously through every package, make focused commits after each
package, and finish with a closeout listing terminal state, paid cells/cost,
preflight result, optimizer/proposer used, target Agent/surface, Selection-dev
and Holdout matrices, paired net wins, tests, hygiene checks, supported claims,
unsupported claims, and commits made.
