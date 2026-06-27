# Goodhart's Law note for Barcarolle

Date: 2026-06-23

## Core concern

Barcarolle can easily become a Goodhart loop:

```text
benchmark compiler chooses tasks
-> Agent or tuning process optimizes against those tasks
-> future-task results guide compiler changes
-> the next compiler version chooses tasks shaped by that feedback
```

This is not a side issue. It is a central validity risk for any system that
uses benchmark performance to guide Agent selection or Agent tuning.

The benchmark is a proxy for real future repository work. Once that proxy is
used repeatedly as an optimization target, high benchmark performance can stop
meaning "better future work performance" and start meaning "better at the
compiler's current task distribution and scoring quirks".

## Two questions that must stay separate

### Benchmark predictive validity

Question:

> At time `t`, can the benchmark generated at `t` predict how the Agents
> available at `t` will perform on future repository work?

Clean protocol:

1. Freeze benchmark `B_t`.
2. Freeze the Agent set available at time `t`: `A_t^1`, `A_t^2`, ...
3. Evaluate those frozen Agents on `B_t`.
4. Later, evaluate the same frozen Agents on future tasks `F_{t+1}`.
5. Compare pass rates, rankings, MAE, regret, or another preregistered metric.

This asks whether the benchmark is a useful measurement instrument.

### Tuning utility

Question:

> If we use benchmark feedback to modify an Agent artifact, does the modified
> Agent perform better on later unseen work?

Clean protocol:

1. Freeze benchmark and feedback inputs.
2. Generate or choose a tuned artifact from those inputs only.
3. Freeze the artifact by hash.
4. Evaluate baseline and tuned Agents on a future holdout that was not visible
   to the tuner.
5. Ideally repeat on a later `F_{t+2}` if the artifact or compiler was changed
   after seeing `F_{t+1}`.

This asks whether benchmark feedback is useful for intervention. It is more
exposed to Goodhart effects than pure predictive-validity measurement.

## Key rule

A benchmark generated at time `t` should primarily be judged against Agents that
existed at time `t`, not against Agents already optimized using that benchmark.

If we evaluate an Agent after it was tuned using `B_t`, the result measures a
combined system:

```text
B_t + tuning process + tuned Agent
```

It no longer cleanly measures the predictive validity of `B_t` itself.

## Practical safeguards

- Keep true future holdouts that are not used for compiler or tuner decisions.
- Version and freeze selector/generator/compiler rules before joining outcomes.
- Treat rolling-origin results as development evidence, not unlimited final
  proof. Reusing them repeatedly turns historical future into training data.
- Report benchmark predictive validity and tuning utility as separate claims.
- For tuning, use later validation after any artifact or compiler change that
  was informed by a prior future holdout.
- Keep random, temporal, and simple stratified baselines so optimization does
  not silently chase artifacts of one compiler version.
- Track whether an Agent has been exposed to a benchmark family or tuning
  feedback derived from it.

## Current implication

Agent Selection Demo is closer to the cleaner predictive-validity question:
fixed Agents are evaluated on selected tasks and future tasks.

Agent Tuning Demo enters the Goodhart-sensitive intervention question:
benchmark feedback changes an Agent artifact, and that changed Agent is then
tested on future tasks.

Future materials should avoid claiming that a successful tuning result proves
benchmark predictive validity. At most it supports tuning utility under a
specific frozen protocol.

