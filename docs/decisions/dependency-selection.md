# Dependency Selection

## Status

Proposed on 2026-04-20.

## Context

This project aims to build a repository-specific code agent evaluation / admission platform. The research inputs in `docs/draft/abstract.md` and `docs/research/*.md` consistently point to the same system requirements:

- replayable task construction from repository history, issues, PRs, tests, and norms
- environment replay and executable verification
- strong execution isolation
- evaluation of agent configurations, not just models
- context selection and process-level diagnostics
- benchmark freshness, traceability, and trustworthiness

That pushes the stack toward boring, inspectable, widely used infrastructure rather than bespoke subsystems. Where a layer is still too research-sensitive to lock down early, this document explicitly defers selection.

## Decision Summary

Recommended initial stack:

- Repository ingestion and host integration: Git CLI as the default primitive, GitHub Apps + Octokit for GitHub-hosted repositories, `tree-sitter` for multi-language structural parsing.
- Isolation and replay: Docker / OCI containers as the baseline execution format, with gVisor as the default hardening layer for shared runners.
- Workflow orchestration: Temporal.
- Data modeling and storage: PostgreSQL as system of record; SQLAlchemy 2.x + Alembic on the Python side; `pgvector` only as an extension, not as a separate vector database.
- Backend API and workers: Python, with FastAPI + Pydantic v2.
- Frontend: Next.js + React + TanStack Query.
- Observability and evaluation telemetry: OpenTelemetry, Prometheus, Grafana.

Explicitly deferred for now:

- agent framework lock-in
- separate vector database
- Kafka-class event streaming
- Firecracker-first execution
- self-hosted object storage product choice

## Why Existing Dependencies Over Custom Builds

- Rebuilding repository access, workflow durability, API serialization, SQL mapping, telemetry, and browser UI primitives would consume time without improving benchmark trustworthiness.
- The project's novelty is task generation, replay fidelity, context/evaluation methodology, and admission policy. Those are the layers that should remain custom.
- Mature infra dependencies already encode failure handling, migrations, metrics, auth, retries, dashboarding, and ecosystem integration that this project will need anyway.

## Recommendations By Capability Domain

### 1. Repository Fetching, History Analysis, and Host Integration

#### Recommended

- Git CLI
- GitHub Apps + GitHub GraphQL/REST APIs via Octokit
- `tree-sitter`

#### Facts

- GitHub Docs position [GitHub Apps](https://docs.github.com/en/apps/using-github-apps/about-using-github-apps) as first-party integrations and document both [app webhooks](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/using-webhooks-with-github-apps) and the [GraphQL API](https://docs.github.com/graphql/overview/about-the-graphql-api).
- [Octokit](https://github.com/octokit/octokit.js) is GitHub's official SDK family for GitHub API integrations, and the upstream repository maintains an auditable [release history](https://github.com/octokit/octokit.js/releases).
- [`tree-sitter`](https://github.com/tree-sitter/tree-sitter) is maintained upstream as an incremental parsing system, and its official repository has an auditable [release history](https://github.com/tree-sitter/tree-sitter/releases).

#### Inference

- Use the Git CLI for cloning, checkout, blame, diff, merge-base, and archive operations because Git itself is the compatibility target.
- Use GitHub Apps + Octokit rather than custom webhook/auth plumbing when repositories live on GitHub; it reduces integration risk and gives first-party support for app installation tokens, webhooks, and GraphQL.
- Use `tree-sitter` for language-agnostic structural parsing and localization features; it is a better default than building custom parsers or depending only on regex/AST libraries tied to one language.

#### Rejected / not preferred

- Pure custom Git protocol handling: unnecessary and brittle.
- Host-specific SDK sprawl at phase 1: GitHub is enough for the first platform slice; keep a provider abstraction for GitLab/Bitbucket later.

### 2. Replayable Environments and Execution Isolation

#### Recommended

- Docker / OCI images for reproducible environments
- gVisor as the default extra isolation layer for shared execution

#### Defer

- Firecracker-first execution

#### Facts

- [Docker Docs](https://docs.docker.com/engine/docker-overview/) describe Docker's image/container/registry/API workflow, and the upstream [Moby repository](https://github.com/moby/moby) keeps an auditable [release history](https://github.com/moby/moby/releases).
- [gVisor](https://github.com/google/gvisor) is maintained upstream as an application kernel for containers, with an auditable [release history](https://github.com/google/gvisor/releases).
- [Firecracker](https://github.com/firecracker-microvm/firecracker) describes itself as purpose-built for secure, multi-tenant, minimal-overhead execution, and the official repository exposes an auditable [release history](https://github.com/firecracker-microvm/firecracker/releases).

#### Inference

- Docker/OCI should be the baseline because most real repositories, CI pipelines, and benchmark artifacts already map naturally to container images.
- gVisor is the right initial hardening layer because it materially improves isolation without forcing the operational leap to full microVM scheduling on day 1.
- Firecracker is attractive for hostile multi-tenant runners, but making it the initial default would front-load platform complexity before the replay/evaluation methodology is proven.

#### Rejected / not preferred

- Raw process sandboxing as the primary strategy: too weak for untrusted repository code.
- Firecracker-first rollout: operationally heavier than needed for initial benchmark construction.

### 3. Workflow Orchestration and Long-Running Evaluation Control

#### Recommended

- Temporal

#### Facts

- [Temporal docs](https://docs.temporal.io/) and the official [server repository](https://github.com/temporalio/temporal) describe Temporal as a durable execution platform for resilient workflows; the server repo also has an auditable [release history](https://github.com/temporalio/temporal/releases).
- The official [Temporal Python SDK repository](https://github.com/temporalio/sdk-python) documents workflows, activities, testing, replay, and workflow sandboxing, and it exposes an auditable [release history](https://github.com/temporalio/sdk-python/releases).

#### Inference

- Temporal is a strong fit because repository evaluation involves long-running, retry-heavy, stateful pipelines: task construction, environment build, agent execution, grading, artifact collection, and replays.
- Durable workflow history is particularly valuable for benchmark auditability, reruns, and partial failure recovery.

#### Rejected / not preferred

- Celery/Redis-only orchestration: good for background jobs, weak for durable multi-step workflow history and replay semantics.
- Airflow-first: stronger for batch DAG scheduling than for event-driven, stateful benchmark execution with fine-grained retries.

### 4. Data Modeling, Metadata Storage, and Search

#### Recommended

- PostgreSQL
- SQLAlchemy 2.x + Alembic
- `pgvector` as an extension only when embeddings are actually needed

#### Facts

- [PostgreSQL's official site](https://www.postgresql.org/about/) states that the project has nearly 40 years of active development, and the official [documentation](https://www.postgresql.org/docs/) plus [news/release feed](https://www.postgresql.org/about/news/) show ongoing supported releases.
- [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) and [Alembic](https://github.com/sqlalchemy/alembic) are maintained as the upstream ORM and migration projects, each with an auditable [SQLAlchemy release history](https://github.com/sqlalchemy/sqlalchemy/releases) and [Alembic release history](https://github.com/sqlalchemy/alembic/releases).
- [`pgvector`](https://github.com/pgvector/pgvector) is distributed as a Postgres extension for vector similarity search inside PostgreSQL, and the upstream repository has an auditable [release history](https://github.com/pgvector/pgvector/releases).

#### Inference

- PostgreSQL should be the system of record because the core workload is relational: repositories, snapshots, tasks, runs, patches, scores, traces, permissions, and artifacts metadata.
- JSONB, full-text search, advisory locks, and extensions let Postgres cover early-stage needs without introducing multiple data systems.
- `pgvector` is useful for optional retrieval experiments, but should remain an extension, not a reason to adopt a separate vector database early.

#### Rejected / not preferred

- MongoDB-first: a poor fit for strongly relational benchmark lineage and scoring data.
- Separate vector DB at phase 1: premature split-brain storage.

### 5. Backend API and Worker Runtime

#### Recommended

- Python
- FastAPI
- Pydantic v2
- `pydantic-settings`

#### Facts

- [FastAPI](https://github.com/fastapi/fastapi) describes itself upstream as a modern, high-performance web framework and maintains an auditable [release history](https://github.com/fastapi/fastapi/releases).
- [Pydantic](https://github.com/pydantic/pydantic) and [`pydantic-settings`](https://github.com/pydantic/pydantic-settings) are maintained in the official Pydantic organization, and both projects expose auditable [Pydantic releases](https://github.com/pydantic/pydantic/releases) and [`pydantic-settings` releases](https://github.com/pydantic/pydantic-settings/releases).

#### Inference

- Python is the best default backend/runtime choice for this project because the evaluation and research ecosystem around repository benchmarking, sandbox tooling, and experiment code is still strongest there.
- FastAPI + Pydantic gives typed request/response models, OpenAPI, validation, and a mature async story without inventing an API layer.
- This stack also aligns cleanly with Temporal's Python SDK for orchestration workers.

#### Rejected / not preferred

- Flask/Django as the initial API layer: both are viable, but FastAPI is a better fit for typed service APIs and worker-heavy internal platforms.
- TypeScript-only backend as the primary runtime: possible, but weaker for the research/evaluation-heavy first phase.

### 6. Frontend and Operator Console

#### Recommended

- React
- Next.js
- TanStack Query

#### Facts

- [React's upstream repository](https://github.com/facebook/react) describes it as "The library for web and native user interfaces" and maintains an auditable [release history](https://github.com/facebook/react/releases).
- [Next.js docs](https://nextjs.org/docs) describe Next.js as a React framework for building full-stack web applications.
- [TanStack Query](https://github.com/tanstack/query) describes itself upstream as an async state-management and server-state library, and the official repository maintains an auditable [release history](https://github.com/tanstack/query/releases).

#### Inference

- The operator console will need run inspection, diff views, workflow history, and evaluative dashboards. React/Next.js remains the safest mainstream choice for this class of product UI.
- TanStack Query is preferable to ad hoc fetch state because the UI will naturally become server-state-heavy.

#### Rejected / not preferred

- Building the UI as custom server-rendered HTML: too limiting for run inspection workflows.
- Early adoption of niche frontend meta-frameworks: unnecessary ecosystem risk.

### 7. Metrics, Traces, Logs, and Evaluation Diagnostics

#### Recommended

- OpenTelemetry
- Prometheus
- Grafana

#### Facts

- The official [OpenTelemetry specification repository](https://github.com/open-telemetry/opentelemetry-specification) defines the cross-language requirements for telemetry implementations.
- [Prometheus](https://github.com/prometheus/prometheus) is maintained upstream with an auditable [release history](https://github.com/prometheus/prometheus/releases).
- [Grafana docs](https://grafana.com/docs/) position Grafana as the visualization layer across metrics, logs, and traces.

#### Inference

- OpenTelemetry should be the instrumentation boundary because this system needs traceable runs across API, workflow workers, sandbox runners, and evaluation stages.
- Prometheus + Grafana is a mainstream default for platform metrics and operational dashboards.
- Agent-run and benchmark-specific analytics should still be persisted in project tables; observability tools complement that data, not replace it.

#### Rejected / not preferred

- Custom tracing schema without OpenTelemetry: would make integration and tooling worse for no upside.

### 8. Artifact Storage

#### Recommended

- Depend on an S3-compatible object storage interface, not a specific self-hosted product yet.

#### Facts

- The [Temporal Python SDK repository](https://github.com/temporalio/sdk-python) documents external payload storage and built-in external storage drivers in its usage guide.
- The official [`minio/minio` repository](https://github.com/minio/minio) is marked archived and read-only by the owner.

#### Inference

- Store logs, patches, terminal transcripts, container build artifacts, and replay bundles behind an S3-compatible abstraction.
- Avoid standardizing on MinIO as the default self-hosted choice until the community/maintenance picture is clearer; managed S3 or another actively maintained S3-compatible option is safer.

#### Rejected / not preferred

- MinIO as the default recommendation in this document.

### 9. Layers To Avoid Locking Down Too Early

#### Do not finalize yet

- agent framework
- model gateway/provider SDK choice
- dedicated vector database
- streaming bus

#### Why

- Research notes argue that the evaluation object is the whole agent configuration. Locking the platform too tightly to one agent framework too early would bias the benchmark platform toward the thing it is supposed to evaluate.
- A thin adapter boundary is preferable: the platform should execute and score multiple agent configurations, not embed one canonical agent shell in its core.

## Risks and Open Validation Items

- Firecracker may become necessary if the threat model shifts from trusted internal benchmarking to hostile multi-tenant execution.
- GitHub-specific integration should not leak into the core task model; preserve a host abstraction from the beginning.
- `pgvector` should only be enabled after retrieval experiments show value; many context selection pipelines can start with lexical, structural, and metadata retrieval.
- Temporal adds operational weight; if the first deployed scope is very small, a temporary lighter job runner may look attractive, but that would likely be a migration cost rather than a true simplification.
- Benchmark artifacts can become large quickly; validate storage retention and lifecycle policy before scaling historical replay.

## Implementation Notes

- Prefer a Python service boundary for task generation, grading, and workflow workers.
- Keep execution runners isolated behind a service boundary so Docker/gVisor/Firecracker can evolve without changing the rest of the platform.
- Use PostgreSQL as the canonical source for benchmark lineage and authority decisions.
- Treat object storage, host integration, and agent execution as pluggable adapters.

## Sources

Primary sources used for activity/mainstream verification. Release/activity pages were checked on 2026-04-20:

- GitHub Apps docs: <https://docs.github.com/en/apps/using-github-apps/about-using-github-apps>
- GitHub GraphQL docs: <https://docs.github.com/graphql/overview/about-the-graphql-api>
- GitHub webhooks for apps: <https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/using-webhooks-with-github-apps>
- Octokit: <https://github.com/octokit/octokit.js>
- Docker overview: <https://docs.docker.com/engine/docker-overview/>
- Moby: <https://github.com/moby/moby>
- gVisor: <https://github.com/google/gvisor>
- Firecracker: <https://github.com/firecracker-microvm/firecracker>
- Temporal docs: <https://docs.temporal.io/>
- Temporal server: <https://github.com/temporalio/temporal>
- Temporal Python SDK: <https://github.com/temporalio/sdk-python>
- PostgreSQL about: <https://www.postgresql.org/about/>
- PostgreSQL docs: <https://www.postgresql.org/docs/>
- PostgreSQL releases/news: <https://www.postgresql.org/about/news/>
- SQLAlchemy: <https://github.com/sqlalchemy/sqlalchemy>
- Alembic: <https://github.com/sqlalchemy/alembic>
- pgvector: <https://github.com/pgvector/pgvector>
- FastAPI: <https://github.com/fastapi/fastapi>
- Pydantic: <https://github.com/pydantic/pydantic>
- pydantic-settings: <https://github.com/pydantic/pydantic-settings>
- React: <https://github.com/facebook/react>
- Next.js docs: <https://nextjs.org/docs>
- Next.js community page: <https://nextjs.org/docs/community>
- TanStack Query: <https://github.com/tanstack/query>
- tree-sitter: <https://github.com/tree-sitter/tree-sitter>
- OpenTelemetry specification: <https://github.com/open-telemetry/opentelemetry-specification>
- Prometheus: <https://github.com/prometheus/prometheus>
- Grafana docs: <https://grafana.com/docs/>
- MinIO repository status: <https://github.com/minio/minio>
