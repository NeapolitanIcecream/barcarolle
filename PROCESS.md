# Barcarolle Process Notes

Last updated: 2026-06-27.

## Current Mode

The repository is in current-design mode.

Active design work must use only:

- `docs/architecture/v2-system-architecture-2026-06-25.md`
- `docs/design-inputs/learned-selector-roadmap-gpt-5-5-pro-2026-06-25.md`

Archived code, reports, runbooks, and experiments are historical reference
material. They are not active design inputs and should not be imported into the
current design without a specific review.

## Design Rules

- Design before implementation.
- Keep module boundaries direct and small.
- Keep the core vocabulary to `Task`, `Check`, `Workspace`, `Result`,
  `Selector`, `RollingOrigin`, `Task Pool`, `Benchmark Selection`, and
  `Agent Results`.
- Do not introduce a new first-class concept when one of those terms is enough.
- Every design document must include a source-alignment check against the
  architecture document.
- Module-level design should define function names, inputs, outputs, and
  effects, but not implementation bodies.
- Later module documents may refine earlier system documents. Update the
  affected documents instead of leaving contradictions.

## Paid Calls

No paid LLM or Agent calls are part of current design work.

If future work requires paid calls, use only:

```text
LLM_BASE_URL
LLM_API_KEY
```

and record a frozen protocol before running them.
