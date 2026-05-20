# Module-Level Dependency Refinement

## Status

Proposed on 2026-04-20.

## Scope and alignment

This memo refines `docs/decisions/dependency-selection.md` at the module and subsystem level. It does not overturn the prior phase unless stated explicitly. The system requirements still come from repository-specific benchmark generation, historical replay, execution isolation, evidence capture, graded scoring, and authorization decisions described in `docs/analysis/requirements.md`, `docs/architecture/system-design.md`, `docs/draft/abstract.md`, and `docs/research/*.md`.

The main rule is unchanged: keep custom logic in task mining, replay fidelity, scoring, and authorization semantics; reuse mature infrastructure for repository access, containers, workflow durability, API plumbing, storage, and observability.

## Summary table

| Module / subsystem | Recommended dependency set | Relation to prior phase | Lock state |
| --- | --- | --- | --- |
| Repository intake and GitHub integration | Git CLI, GitHub Apps, Octokit | Inherit | Locked for phase 1 |
| Signal extraction and parsing | `tree-sitter` plus custom extraction logic | Inherit | Locked for parser layer; retrieval extras deferred |
| Environment reconstruction | Docker/OCI, BuildKit | Docker/OCI inherited; BuildKit refined within same direction | Locked for baseline |
| Execution isolation | gVisor on top of OCI containers | Inherit | Locked for shared-runner baseline |
| Evaluation orchestration | Temporal server + Temporal Python SDK | Inherit | Locked for baseline |
| Artifact and evidence storage | PostgreSQL metadata, S3-compatible blob interface | Inherit | Interface locked; product choice deferred |
| Scoring and rule execution | Python-native scoring, PostgreSQL JSONB; optional `pgvector` only for retrieval experiments | Inherit | Core locked; vector use deferred |
| Authorization policy | Open Policy Agent (OPA) as policy boundary | New refinement, consistent with prior “separate policy layer” direction | Locked for policy boundary, not for full policy schema |
| Auditability and observability | OpenTelemetry, Prometheus, Grafana | Inherit | Locked for baseline; log/trace backend details deferred |
| Backend API and workers | Python, FastAPI, Pydantic v2, `pydantic-settings`, SQLAlchemy 2.x, Alembic | Inherit | Locked for baseline |
| Frontend console | React, Next.js, TanStack Query | Inherit | Locked for baseline; chart/component kit deferred |

## Cross-cutting rules

- Keep one source of truth for repository state: Git objects and PostgreSQL metadata, not parallel bespoke mirrors.
- Keep one durable workflow engine: Temporal, not a second ad hoc retry/state machine layer.
- Keep one policy boundary: scores are computed in application code, authorization is evaluated separately by policy.
- Keep one observability boundary: instrument through OpenTelemetry first, then fan out to Prometheus/Grafana-compatible backends.
- Prefer interface contracts over product lock-in where the deployment choice is still open, especially for object storage and retrieval.

## Module decisions

### 1. Repository intake and GitHub integration

**Selected dependencies**

- Git CLI for clone, fetch, checkout, diff, blame, merge-base, archive, and repository snapshot materialization.
- GitHub Apps as the GitHub-hosted integration model.
- Octokit as the GitHub API SDK boundary for app auth, installation tokens, REST, GraphQL, and webhooks.

**Relation to prior phase**

- Pure inheritance from the prior dependency memo. No directional change.

**Why this layer is locked now**

- The compatibility target is Git itself, so repository materialization should stay on Git CLI rather than a reimplementation.
- GitHub’s official docs still recommend GitHub Apps over OAuth apps for finer-grained permissions and short-lived tokens.
- Octokit remains GitHub’s official SDK family and still shows active releases; its upstream package explicitly covers API client, GitHub App, installation, and webhook use cases.

**Alternatives not chosen**

- `libgit2` / `pygit2` as the default path: useful for embeddings or in-process graph traversal later, but unnecessary for the first system slice and weaker as the fidelity target than Git itself.
- OAuth-app-first integration: broader than needed and weaker on least privilege for repository admission workflows.
- Early multi-host SDK sprawl for GitLab/Bitbucket: defer until there is a real second host requirement.

**Deferred items**

- Provider abstraction beyond GitHub. Trigger to lock: a confirmed requirement to ingest non-GitHub repositories in the same control plane.
- GraphQL schema codegen. Trigger to lock: repeated GraphQL query churn that exceeds hand-maintained client safety.

**Primary-source anchors**

- [GitHub Apps docs](https://docs.github.com/apps) state that GitHub Apps are the preferred fine-grained integration model.
- [Octokit repository](https://github.com/octokit/octokit.js) documents first-party support for GitHub App auth, webhooks, REST, and GraphQL.
- [Octokit releases](https://github.com/octokit/octokit.js/releases) show current upstream release activity, including `v5.0.5` on 2025-10-31.

### 2. Signal extraction and parsing

**Selected dependencies**

- `tree-sitter` for structural parsing across languages.
- Git CLI output plus repository-native files for temporal, ownership, and change signals.
- Custom extraction logic in project code for task anchors, repository rules, and benchmark-specific feature engineering.

**Relation to prior phase**

- Inherit the prior `tree-sitter` decision; refine it as the parser boundary for this subsystem.

**Why this layer is locked now**

- The system needs multi-language, structural, incrementally updateable parsing, but the project’s novelty is not parser construction.
- `tree-sitter` remains active and mainstream enough for this role; its official repository describes it as an incremental parsing system, and the release page shows `v0.26.3` on 2025-12-13.

**Alternatives not chosen**

- LSP servers as the baseline parser abstraction: too editor-oriented and inconsistent across languages for offline mining.
- Regex-only mining: insufficient for cross-file, symbol-aware task extraction.
- Semgrep-first or CodeQL-first mining: valuable later for targeted analyses, but too opinionated and operationally heavy as the universal extraction primitive.

**Deferred items**

- Embedding-based retrieval stacks. Trigger to lock: measured evidence that lexical plus structural localization is insufficient on the target repositories.
- Cross-repository knowledge graph tooling. Trigger to lock: a requirement to score repository relationships beyond one repository’s own history.

**Primary-source anchors**

- [`tree-sitter` repository](https://github.com/tree-sitter/tree-sitter) describes it as an incremental parsing system.
- [`tree-sitter` releases](https://github.com/tree-sitter/tree-sitter/releases) show `v0.26.3` on 2025-12-13.

### 3. Environment reconstruction

**Selected dependencies**

- Docker/OCI images as the reproducible environment format.
- BuildKit as the container build backend inside the Docker/OCI direction.

**Relation to prior phase**

- Docker/OCI was already selected. BuildKit is a module-level refinement, not a stack reversal.

**Why this layer is locked now**

- Historical replay needs a mainstream container/image workflow that maps to real repository build instructions and CI artifacts.
- Docker’s official docs still position BuildKit as the builder backend and default engine for modern Docker builds, including concurrent build graph solving and caching.

**Alternatives not chosen**

- Nix-first reconstruction: attractive for determinism, but a larger ecosystem and workflow shift than phase 1 requires.
- Raw shell-script replay without container capture: too weak for reproducibility and audit.

**Deferred items**

- Nix or another stronger reproducibility layer. Trigger to lock: repeated replay failures caused by upstream package churn that OCI pinning cannot absorb.
- Build farm specialization. Trigger to lock: demonstrated bottlenecks from image build throughput rather than benchmark methodology.

**Primary-source anchors**

- [Docker overview](https://docs.docker.com/engine/docker-overview/) describes Docker’s image and container model.
- [BuildKit docs](https://docs.docker.com/build/buildkit/) state that BuildKit is the builder backend used by Docker.
- [Docker build overview](https://docs.docker.com/build/concepts/overview/) states that `docker build` uses Buildx with the default BuildKit bundled with Docker.

### 4. Execution isolation

**Selected dependencies**

- gVisor `runsc` as the default hardening layer for shared OCI-based execution.

**Relation to prior phase**

- Pure inheritance from the prior phase.

**Why this layer is locked now**

- The benchmark executes untrusted repository code, so containers alone are not the trust boundary.
- gVisor’s own documentation still frames it as a strong isolation layer and explicitly states that containers are not, by themselves, a sandbox.
- gVisor keeps the project within the OCI toolchain rather than forcing an early move to a distinct microVM platform.

**Alternatives not chosen**

- Plain Docker namespaces/cgroups as the main boundary: too weak for hostile benchmark workloads.
- Firecracker-first rollout: stronger isolation, but operationally heavier before the replay harness is stable.

**Deferred items**

- Firecracker or Kata Containers. Trigger to lock: a deployment requirement for hostile multi-tenant runners that gVisor cannot satisfy.
- Per-language in-process sandboxes. Trigger to lock: a verified need for ultra-low-latency trusted plugins rather than full repository execution.

**Primary-source anchors**

- [gVisor repository](https://github.com/google/gvisor) states that it provides a strong isolation layer and includes an OCI runtime named `runsc`.
- The same official page explains why containers alone are not sufficient isolation for untrusted code.

### 5. Evaluation orchestration

**Selected dependencies**

- Temporal server for durable workflow execution.
- Temporal Python SDK for workflow and activity implementation in the backend/runtime language chosen previously.

**Relation to prior phase**

- Pure inheritance from the prior phase.

**Why this layer is locked now**

- Task generation, replay planning, environment build, execution, repeated trials, scoring, and retirement all need durable state, retries, and replayable history.
- Temporal’s official server release page shows active releases, including `v1.30.4` on 2026-04-10.
- The official Python SDK release page shows `1.25.0` on 2026-04-08 and now includes external-storage support relevant to large evidence payloads.

**Alternatives not chosen**

- Celery/Redis-only orchestration: acceptable for stateless jobs, weak for durable multi-step evaluation history.
- Airflow-first: stronger for scheduled DAGs than for event-driven benchmark execution with partial reruns.

**Deferred items**

- Multi-cluster Temporal or Temporal Cloud lock-in. Trigger to lock: proven control-plane scale or availability requirements.
- A separate queueing system around Temporal. Trigger to lock: concrete throughput constraints that Temporal task queues cannot handle directly.

**Primary-source anchors**

- [Temporal docs](https://docs.temporal.io/) position Temporal as the platform documentation for durable workflows.
- [Temporal server releases](https://github.com/temporalio/temporal/releases) show `v1.30.4` on 2026-04-10.
- [Temporal Python SDK releases](https://github.com/temporalio/sdk-python/releases) show `1.25.0` on 2026-04-08.

### 6. Artifact and evidence storage

**Selected dependencies**

- PostgreSQL for artifact metadata, lineage, checksums, retention state, and queryable evidence indexes.
- S3-compatible object storage as the blob interface for logs, patches, terminal transcripts, replay bundles, and build artifacts.

**Relation to prior phase**

- Pure inheritance on PostgreSQL and the S3-compatible storage direction.

**Why this layer is locked now**

- The relational lineage of repositories, tasks, runs, scorers, and policy decisions belongs in PostgreSQL.
- Large immutable blobs should remain outside the main relational store.
- This design avoids inventing a custom artifact service while still preserving migration freedom across cloud and self-hosted object stores.

**Alternatives not chosen**

- Database-only blob storage: expensive and awkward for large replay artifacts.
- Product-first lock-in to one self-hosted object store: premature before deployment mode is fixed.

**Deferred items**

- Specific object-store product and SDK. Trigger to lock: the first concrete deployment environment.
- Cold-storage tiering. Trigger to lock: evidence-retention cost or compliance pressure.

**Primary-source anchors**

- [PostgreSQL official about page](https://www.postgresql.org/about/) states that PostgreSQL has nearly 40 years of active development.
- [PostgreSQL releases/news](https://www.postgresql.org/about/news/) and the home page show supported release updates on 2026-02-26.
- [Temporal Python SDK release notes](https://github.com/temporalio/sdk-python/releases) document external storage and an Amazon S3 driver in `1.25.0`.

### 7. Scoring, rule execution, and retrieval experiments

**Selected dependencies**

- Python-native scoring code for benchmark semantics.
- PostgreSQL JSONB and relational tables for rubric inputs, intermediate verdicts, and evidence references.
- Optional `pgvector` only for later retrieval experiments, not as a mandatory system dependency.

**Relation to prior phase**

- Inherit PostgreSQL and optional `pgvector`; refine that scoring itself remains custom application logic.

**Why this layer stays mostly custom**

- The project’s core novelty is repository-specific scoring, benchmark retirement, leakage handling, and admission evidence. Those semantics should not be outsourced to a generic ML-eval framework or a generic rules engine.
- `pgvector` remains a pragmatic extension if vector retrieval becomes necessary, but the core workload is still relational and auditable.

**Alternatives not chosen**

- Separate vector database in phase 1: adds another consistency boundary without clear benchmark value.
- Generic “LLM eval platform” dependency as the primary scorer: likely to fight repository-specific oracles and replay semantics.

**Deferred items**

- `pgvector` activation itself. Trigger to lock: measured improvement from retrieval experiments on hard localization tasks.
- Learned or model-based graders. Trigger to lock: evidence that repository-native oracles plus structured review metrics are insufficient.

**Primary-source anchors**

- [PostgreSQL official site](https://www.postgresql.org/) continues active supported releases.
- [`pgvector` repository](https://github.com/pgvector/pgvector) documents vector similarity search inside Postgres and currently shows installation guidance for `v0.8.2`.

### 8. Authorization policy

**Selected dependencies**

- Open Policy Agent as the policy evaluation boundary for graded authorization decisions.

**Relation to prior phase**

- This is a new explicit dependency recommendation, but it follows the prior system-design rule that policy should remain separate from scoring and benchmarking.

**Why this layer is added now**

- Authorization is a distinct concern from benchmark scoring: scores summarize evidence, while policy decides what scope of authority to grant.
- OPA gives a mainstream, externalized policy model with decision logging and ecosystem support, which is preferable to burying permission logic in application conditionals.
- Its current official release page still shows active maintenance, including `v1.12.3` on 2026-01-14 and newer releases in April 2026.

**Alternatives not chosen**

- Hand-rolled policy logic in the API service: fastest to start, but harder to audit, test, and evolve.
- Casbin or Oso as the primary boundary: both are viable, but OPA is a better fit when policy needs to remain externally inspectable and potentially shared across services.

**Deferred items**

- Final policy schema and decision vocabulary. Trigger to lock: once the trust-tier model and repository/module scopes are stabilized.
- Whether OPA runs as a sidecar, library, or central service. Trigger to lock: first production deployment topology.

**Primary-source anchors**

- [OPA docs](https://www.openpolicyagent.org/docs) position OPA as the official policy engine documentation.
- [OPA releases](https://github.com/open-policy-agent/opa/releases) show active upstream releases, including `v1.12.3` on 2026-01-14 and newer releases in April 2026.

### 9. Auditability and observability

**Selected dependencies**

- OpenTelemetry as the instrumentation boundary.
- Prometheus for metrics collection and alert-friendly scraping.
- Grafana for dashboards and cross-signal inspection.

**Relation to prior phase**

- Pure inheritance from the prior phase.

**Why this layer is locked now**

- The system needs request traces, workflow activity timing, sandbox resource metrics, and audit-friendly dashboards.
- OpenTelemetry remains the cross-language spec boundary and avoids a custom telemetry schema.
- Prometheus and Grafana remain mainstream OSS defaults; Prometheus shows `3.11.2` on 2026-04-13, while Grafana’s official docs still present metrics, logs, and traces as first-class stack components.

**Alternatives not chosen**

- Custom trace/event schema only: too expensive and too hard to integrate with standard tooling.
- One vendor-specific all-in-one observability lock-in: unnecessary before deployment constraints are known.

**Deferred items**

- Concrete log and trace backends such as Loki or Tempo. Trigger to lock: once retention, query volume, and compliance requirements are measured.
- Long-term trajectory analytics warehouse. Trigger to lock: if operational telemetry and benchmark analytics diverge enough to justify separate storage.

**Primary-source anchors**

- [OpenTelemetry specification](https://github.com/open-telemetry/opentelemetry-specification) defines the cross-language requirements for OpenTelemetry implementations.
- [Prometheus repository](https://github.com/prometheus/prometheus) shows active releases including `3.11.2` on 2026-04-13.
- [Grafana docs](https://grafana.com/docs/) position Grafana around metrics, logs, and traces in the official stack.

### 10. Backend API and worker runtime

**Selected dependencies**

- Python as the backend and worker runtime.
- FastAPI for service APIs.
- Pydantic v2 and `pydantic-settings` for typed models and configuration.
- SQLAlchemy 2.x and Alembic for persistence and migrations.

**Relation to prior phase**

- Pure inheritance from the prior phase.

**Why this layer is locked now**

- The project still benefits from Python’s benchmark, orchestration, and research-tooling ecosystem.
- FastAPI remains a mainstream typed API stack and continues active releases, including `0.136.0` on 2026-04-16.
- Pydantic remains actively maintained, with `2.13.1` on 2026-04-15.
- SQLAlchemy and Alembic remain actively maintained and appropriate for a relational system of record.

**Alternatives not chosen**

- Django-first: broader framework than needed for API-heavy service boundaries.
- Flask-first: lighter, but would recreate patterns already standardized in FastAPI + Pydantic.
- TypeScript-only backend: possible, but misaligned with the Python-heavy evaluation and orchestration ecosystem chosen elsewhere.

**Deferred items**

- Separate auth framework choice for human-facing login flows. Trigger to lock: when the operator console moves beyond internal access.
- Async ORM alternatives. Trigger to lock: proven mismatch between SQLAlchemy ergonomics and workload shape.

**Primary-source anchors**

- [FastAPI repository](https://github.com/fastapi/fastapi) shows `0.136.0` on 2026-04-16.
- [Pydantic repository](https://github.com/pydantic/pydantic) shows `2.13.1` on 2026-04-15.
- [SQLAlchemy releases](https://github.com/sqlalchemy/sqlalchemy/releases) show current upstream activity in 2026.
- [Alembic repository](https://github.com/sqlalchemy/alembic) shows `1.18.4` on 2026-02-10.

### 11. Frontend console

**Selected dependencies**

- React for UI composition.
- Next.js for the application framework and routing/runtime boundary.
- TanStack Query for server-state fetching, caching, and invalidation.

**Relation to prior phase**

- Pure inheritance from the prior phase.

**Why this layer is locked now**

- The operator console needs rich inspection workflows, not simple static pages.
- React remains current and mainstream; the official release page shows `19.2.5` on 2026-04-08.
- Next.js still positions itself as the React framework for full-stack web applications.
- TanStack Query remains an actively updated default for server-state-heavy React applications; the official release page continues to ship updates in April 2026.

**Alternatives not chosen**

- Custom SSR pages without a client state layer: too limiting for run inspection, retries, diff views, and evidence drill-down.
- Locking a charting or design-system dependency now: premature before the concrete operator workflows and dashboard density are known.

**Deferred items**

- UI component kit and charting library. Trigger to lock: once the first evidence and benchmark dashboards are designed with real data density.
- Real-time transport choice for live run tails. Trigger to lock: once the orchestration and audit APIs expose concrete streaming requirements.

**Primary-source anchors**

- [React releases](https://github.com/facebook/react/releases) show `19.2.5` on 2026-04-08.
- [Next.js docs](https://nextjs.org/docs) describe Next.js as a React framework for full-stack web applications.
- [TanStack Query docs](https://tanstack.com/query/docs) position Query as the server-state/caching layer, and [TanStack Query releases](https://github.com/tanstack/query/releases) show active April 2026 updates.

## Deferred-dependency register

These items are intentionally not locked in this phase:

- Non-GitHub host SDKs and provider abstractions.
- Embedding/retrieval infrastructure beyond `tree-sitter` and relational metadata.
- Nix or equivalent stronger reproducibility tooling.
- Firecracker/Kata-class sandbox backends.
- Specific object-storage product and client SDK.
- Dedicated log backend and trace backend products.
- UI component kit, chart library, and live-stream transport.

Each deferral is deliberate: the project should first validate repository-specific replay and admission semantics before adding more platform surface area.

## Why avoiding duplicate wheel-building matters here

- Rebuilding Git host integration, workflow durability, container orchestration, storage primitives, or telemetry would not improve the benchmark’s trustworthiness.
- The research-backed hard problems are repository-specific task construction, historical replay fidelity, leakage control, evidence quality, and policy mapping.
- Using mature dependencies narrows the custom surface to the parts that actually differentiate the system and keeps future audits simpler.

## Change log versus prior dependency-selection memo

- No previously selected baseline dependency has been removed.
- BuildKit is now named explicitly inside the existing Docker/OCI choice for environment reconstruction.
- OPA is added as the recommended policy-engine boundary so that authorization logic stays separate from scoring.
- Several product classes remain intentionally deferred rather than prematurely standardized.
