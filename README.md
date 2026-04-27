# Barcarolle

Barcarolle is a repository-specific "Agent License" and evaluation system design. It turns one repository's history, tasks, tests, operating rules, and explicit risk appetite into replayable benchmark evidence for a specific agent configuration, then uses that evidence to support repository-scoped admission decisions.

The documents under `docs/architecture`, `docs/analysis`, and `docs/decisions` are the source of truth for the complete system design. Concepts present in those documents are part of the intended product semantics unless a later design change explicitly says otherwise.

Primary use cases:

- Agent-configuration and agent-framework developers use Barcarolle as a repository-specific evaluation environment for comparing complete agent configurations.
- Repository owners, platform teams, research groups, companies, or open-source communities use Barcarolle to quantify whether a new agent configuration works well in a shared repository and how it compares with alternatives under the same repository-specific conditions.

Primary operating assumption: trusted internal collaboration. Repository owners and tested-agent owners are expected to have aligned incentives and no intent to cheat the benchmark. Barcarolle is not an adversarial certification system. It is also not a runtime enforcement plane: a Barcarolle License is an evidence-backed repository admission record, including the `G5` fully trusted YOLO tier, not a guardrail mechanism that constrains agent actions at runtime. Repository or organization risk profiles are policy appetite inputs for calibration and authorization; they do not become runtime guards or calibration truth labels.
