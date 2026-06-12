# Presentation Feedback 2026-06-11

Status: working notes for the next presentation and project-story revision.

This note records feedback from the latest internal presentation. Use it as a
checklist when revising slides, choosing the next demo, or reframing the
near-term project plan.

Local source note: the user's original wording is preserved in
[`local-artifacts/presentation-feedback-2026-06-11-raw-user-notes.md`](local-artifacts/presentation-feedback-2026-06-11-raw-user-notes.md).
That file is intentionally ignored by Git and should be used only for local
cross-checking.

## Summary

Reviewers generally accepted the project direction, but the story still needs
sharper product framing. The next version should:

- include Agent selection as a major use case, not only Agent tuning;
- avoid making project value depend on whether SKVM or DSPy is already valued
  internally;
- either find a concrete business sponsor or produce a strong prototype result;
- use more Chinese and fewer technical terms so non-specialist reviewers can
  follow the argument.

## 1. Add The Agent Selection Story

Current slides mainly emphasize Agent tuning. Reviewers said Agent selection is
also a practical and potentially broader use case.

The challenge is that Agent selection is very general. A broad "many teams need
to choose Agents" story may sound useful but not investable, because it lacks a
specific internal buyer. The next story needs to make Agent selection concrete
without turning the project into a vague platform claim.

Working direction:

- keep the main system claim as target-repo predictive Agent evaluation;
- present tuning and selection as two major use cases;
- frame selection as a deployment decision, such as which Agent configuration
  can enter a repository, whether a current Agent should be replaced, and what
  risk remains before rollout;
- avoid making Agent selection the only story unless a concrete internal user
  is found.

Open questions:

- Should the landing scenario be "Agent Selection and Tuning" instead of only
  "Agent Tuning"?
- Can we identify a concrete internal team that already needs repository-level
  Agent admission or replacement decisions?
- What end-to-end metric would make the selection story credible: selection
  accuracy, future holdout pass-rate lift, regression-risk reduction, cost per
  accepted Agent, or avoided bad rollout?

## 2. Do Not Over-Bind Value To SKVM Or DSPy

Reviewers noted that internal consensus on SKVM and DSPy is not settled. If the
project value is phrased as "making SKVM or DSPy better," reviewers may ask why
that matters if those systems themselves are not yet a priority.

There are two possible paths.

### Path A: Find A Business Sponsor

Find a concrete internal business or engineering team that needs Agent
evaluation, selection, tuning, or admission for a specific repository or
workflow. That team can provide the buyer-side reason to invest.

Support work we can prepare:

- write an internal community post explaining target-repo predictive Agent
  evaluation in plain language;
- ask for teams that are already trying to choose, tune, or govern Coding
  Agents;
- collect concrete user stories and decision points;
- identify one or two candidate repositories for a joint pilot.

This path depends on internal user discovery and may be slow.

### Path B: Build A Strong Prototype Result

If a concrete sponsor is not available soon, build a prototype around a real
Coding Agent setting and produce a visible performance result.

Possible demo objects:

- SKVM;
- DSPy;
- Hermes Agent;
- another internal Coding Agent that is easier to run and compare.

The result should show a clear before/after or A/B effect. If the number is
strong enough, the project can be framed as a new Agent optimization/evaluation
layer even before the exact business landing path is fully settled.

Candidate metrics:

- future holdout pass-rate improvement;
- percentage-point lift after one or more tuning rounds;
- regression-rate reduction;
- cost per validated improvement;
- correct selection of the better Agent configuration;
- reduction in misleading tuning or selection decisions.

Open questions:

- Which real Agent is easiest to run end to end in the next prototype?
- Is "SkVM++" a useful internal framing, or should it remain only a working
  analogy?
- What result would be large enough for reviewers to treat the prototype as a
  new capability rather than a support tool?

## 3. Reduce Terminology And Use More Chinese

Reviewers said the slides still carry too much terminology. The next deck should
prefer plain Chinese and sacrifice some technical precision when needed.

Guidelines:

- use Chinese slide titles by default;
- keep English terms only when they are necessary or widely recognized;
- define every retained term the first time it appears;
- avoid long chains of terms such as selector, release, oracle, rolling-origin,
  stratified, calibration, and adapter;
- replace internal phrasing with plain user-facing wording.

Preferred wording examples:

- "选哪些任务更能代表未来工作" instead of "task selection policy";
- "未来任务预测误差" instead of only "future holdout MAE";
- "隐藏验证测试" instead of only "hidden oracle";
- "历史滚动验证" instead of only "rolling-origin";
- "强简单对照" instead of only "strong baseline";
- "目标仓库" and "真实工作" should stay visible throughout the deck.

The deck should answer five reader questions in this order:

1. Who has the problem?
2. Why do current benchmarks or generators not solve it?
3. What does the system do?
4. Why should it work?
5. What measurable result will prove value?

## Working Implications For The Next Deck

The project should still be framed as a target-repo predictive Agent evaluation
system. The slide story should change in three ways:

- the landing scenario should include both Agent selection and Agent tuning;
- SKVM, DSPy, and similar systems should be examples or demo targets, not the
  foundation of the value claim;
- the language should be rewritten for reviewers who do not follow benchmark or
  Agent-tuning research closely.

The next work should decide whether to prioritize:

- a business-sponsor discovery plan;
- a prototype A/B result around a real Agent;
- or both in parallel, with the prototype used to make sponsor discovery easier.
