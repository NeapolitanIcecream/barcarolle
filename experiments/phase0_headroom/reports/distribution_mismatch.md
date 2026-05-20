# Phase 0 Distribution Mismatch

Primary target: `toolz`. Generic comparator: archived Click R0 metadata.

- Target anchors: `50`.
- Early window count: `25`.
- Late window count: `25`.
- Cutoff used for early/late split: `2016-12-09T14:43:06-06:00`.
- Target top module: `functoolz` at `34.6%` of module touches.
- Generic Click top module: `core` at `41.2%` of module touches.
- Mismatch rows with absolute gap >= 0.15: `12`.

The strongest Phase 0 mismatch is that `toolz` history is concentrated in functional-utility modules and includes maintenance/refactor/introspection work, while the archived Click comparator is a curated behavior-verifier mix centered on command-line option, prompt, and testing behavior. This is enough to treat a generic Click-like task mix as a weak estimator for `toolz` future work at this scope.

Missing-data labels are explicit in the target profile. Issue and PR body text was not fetched in this deterministic pass.
