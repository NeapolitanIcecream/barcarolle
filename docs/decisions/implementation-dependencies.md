# Implementation Dependency Locking

## Status

Proposed on 2026-04-20.

## Scope and relation to prior memos

This memo completes the dependency work left open by:

- `docs/decisions/dependency-selection.md`
- `docs/decisions/module-dependencies.md`
- `docs/architecture/backend-control-plane.md`
- `docs/architecture/platform-operations.md`
- `docs/architecture/operator-console.md`

It does not revisit the already-locked baseline of Python, FastAPI, Temporal, PostgreSQL, Docker/OCI, gVisor, React, Next.js, TanStack Query, OpenTelemetry, Prometheus, and Grafana except where the expanded design now requires a named implementation dependency or concrete product choice.

The guiding rule stays the same: keep the custom surface in replay fidelity, validation, scoring, and authorization semantics; reuse mainstream infrastructure for storage adapters, deployment, secrets, telemetry plumbing, and console primitives.

## Summary table

| Area | Selected dependency set | Why it is locked now | Meaningful deferrals |
| --- | --- | --- | --- |
| Control-plane PostgreSQL access | `psycopg` 3 | SQLAlchemy was already locked; the backend now needs a concrete driver choice for API and worker processes | None |
| Blob/object access from Python | `boto3` against the S3-compatible interface | The evidence path and signed-artifact access model now need a concrete SDK boundary | Local emulators and cloud-specific wrappers |
| Control-plane cache / extra broker | No Redis-class dependency | Backend-control-plane and workflow docs already keep PostgreSQL as the query source and Temporal as the durable coordinator | Redis only if measured latency or rate-limiting pressure requires it |
| Cluster substrate and packaging | Kubernetes + Helm | Platform-operations now clearly requires queue-separated worker pools, network policy, RBAC, and isolated execution fleets | GitOps controller, ingress controller, and exact managed-cluster vendor |
| Secret authority | Vault | The operations design now requires short-lived per-run secrets, revocation, and auditable secret classes | ESO/CSI wiring and cloud-native secret-store integration |
| Concrete log and trace backends | OpenTelemetry Collector + Loki + Tempo, with Prometheus and Grafana inherited | The operations doc now defines operator-visible signals strongly enough to lock the telemetry pipeline | Long-term analytics warehouse and SIEM export |
| Console identity boundary | Keycloak over OIDC/OAuth 2.0 | The console now has clear persona and capability boundaries for internal users and automation | Public/external-user federation and Next-specific session helper |
| Console component system | Material UI | The operator console now has enough list/detail/action density to justify a concrete component library | Future brand layer beyond the first internal console |
| Console artifact/code viewer | Monaco Editor | Run detail requires rich inspection of logs, patches, diffs, and code-like evidence | AST-aware semantic diff tooling |
| Embedded console charts | Recharts | The console needs lightweight repository/run charts, while Grafana remains the deeper ops dashboard | Live streaming transport and heavier chart engines |

## Cross-cutting rules

- Do not introduce a second durable workflow or job system beside Temporal.
- Do not introduce a second query source beside PostgreSQL for canonical control-plane state.
- Prefer protocol and interface compatibility over product lock-in: S3 API, OIDC, OpenTelemetry, and Kubernetes packaging remain more important than one deployment vendor.
- Keep cluster-, secret-, and telemetry-level products swappable where the design still depends on deployment environment rather than benchmark semantics.

## 1. Backend control-plane implementation dependencies

### 1.1 PostgreSQL driver

**Selected dependency**

- `psycopg` 3 as the PostgreSQL driver for SQLAlchemy-backed API and worker processes.

**Candidate comparison**

- `psycopg` 3
- `psycopg2`
- `asyncpg`

**Selection rationale**

- `psycopg` 3 is the cleanest fit for the already-selected SQLAlchemy 2.x stack.
- It supports both modern PostgreSQL features and Python async usage without forcing the project into an `asyncpg`-only path.
- It avoids carrying legacy `psycopg2` behavior into a new codebase when the project is not constrained by older adapters.

**Alternatives not chosen**

- `psycopg2`: still viable for legacy services, but this project is new and does not benefit from staying on the older adapter family.
- `asyncpg`: fast and capable, but the benchmark platform benefits more from one mainstream SQLAlchemy-compatible driver across API and worker roles than from a separate async-specialized path.

**Deferred items**

- No second Postgres driver is approved. Revisit only if measured workload profiling proves an isolated hot path benefits materially from a different adapter.

**Primary-source anchors**

- [psycopg 3 documentation](https://www.psycopg.org/psycopg3/docs/) describes Psycopg 3 as a newly designed PostgreSQL adapter for Python and documents async support, connection pools, prepared statements, and pipeline mode.
- [`psycopg` on PyPI](https://pypi.org/project/psycopg/) showed `3.3.3` released on 2026-02-18 when verified on 2026-04-20, and marks the package as `Production/Stable`.

### 1.2 Object-storage SDK boundary

**Selected dependency**

- `boto3` as the Python SDK boundary for the S3-compatible artifact interface.

**Candidate comparison**

- `boto3`
- MinIO Python SDK
- Cloud-specific SDKs as the primary abstraction

**Selection rationale**

- The earlier memos already locked the storage interface to S3 compatibility rather than to one self-hosted product.
- `boto3` is the default mainstream SDK for that API surface and matches the design requirement for signed artifact access, object metadata, and evidence upload/download flows.
- This keeps object access aligned with the chosen interface rather than binding the platform to MinIO-specific helpers or to one cloud vendor’s non-S3 abstractions.

**Alternatives not chosen**

- MinIO SDK as the primary boundary: too coupled to one implementation when the design intentionally keeps the object-store product open.
- Cloud-specific SDKs first: they would weaken portability across managed S3 and self-hosted S3-compatible deployments.

**Deferred items**

- Local development emulator choice.
- Whether artifact bodies are served through direct signed URLs only or through a backend proxy for selected sensitive artifacts.

**Primary-source anchors**

- [Boto3 documentation](https://docs.aws.amazon.com/boto3/latest/) describes Boto3 as the AWS SDK for Python and documents both object-oriented and low-level access to services including Amazon S3.
- [`boto3` on PyPI](https://pypi.org/project/boto3/) showed `1.42.91` released on 2026-04-17 when verified on 2026-04-20, and marks the package as `Production/Stable`.

### 1.3 Cache and extra broker stance

**Selected dependency**

- No Redis-class cache, lock service, or second queueing dependency.

**Candidate comparison**

- PostgreSQL read models + Temporal only
- Add Redis for caching, idempotency, or job signaling

**Selection rationale**

- `docs/architecture/backend-control-plane.md` already states that read APIs should query PostgreSQL-backed read models and evidence manifests rather than live workflow state.
- Temporal already owns durable retries, state transitions, and cancellation.
- Adding Redis now would create another operational dependency without resolving a design gap in the control plane.

**Alternatives not chosen**

- Redis as a default cache or broker: premature before measured read latency, rate-limiting, or fan-out pressure demonstrates that PostgreSQL plus Temporal is insufficient.

**Deferred items**

- Redis may be introduced later only for narrow, explicitly non-authoritative concerns such as burst absorption or short-lived derived caches. It must never become a second source of truth for benchmark lineage or authorization state.

## 2. Platform operations dependencies

### 2.1 Cluster substrate and packaging

**Selected dependencies**

- Kubernetes as the deployment substrate.
- Helm as the packaging and release-management boundary for cluster workloads.

**Candidate comparison**

- Kubernetes + Helm
- Nomad-based deployment
- Cloud-vendor-specific schedulers as the primary platform abstraction

**Selection rationale**

- The platform-operations design now clearly requires separate worker pools, RBAC boundaries, network policy, runtime-class-aware execution, environment tiers, and independent scaling by queue role.
- Kubernetes is the most mainstream fit for those requirements and keeps the platform portable across local, staging, and production clusters.
- Helm is a practical packaging layer for the API, trusted workers, execution fleet, observability stack, and supporting services without inventing a custom deployment system.

**Alternatives not chosen**

- Nomad-first deployment: viable, but materially less common for the mix of network policy, ecosystem integrations, and operator familiarity this platform will need.
- Cloud-vendor scheduler first: too constraining while the design intentionally stays portable across self-managed and managed environments.

**Deferred items**

- GitOps controller choice between tools such as Argo CD and Flux.
- Ingress/Gateway controller choice.
- Exact managed-cluster vendor or on-prem distribution.

**Primary-source anchors**

- [Kubernetes overview](https://kubernetes.io/docs/concepts/overview/) exposes current documentation versions including `v1.35` and the platform capabilities relevant to workloads, RBAC, networking, storage, and observability.
- [Kubernetes releases](https://github.com/kubernetes/kubernetes/releases) showed active patch releases including `v1.34.7` on 2026-04-15 when verified on 2026-04-20.
- [Helm docs](https://helm.sh/docs/) describe Helm as the package manager for Kubernetes.
- [Helm releases](https://github.com/helm/helm/releases) showed `Helm v3.20.0` on the official release page when verified on 2026-04-20.

### 2.2 Secret authority

**Selected dependency**

- Vault as the secret-management authority for control-plane, build-time, and short-lived run-scoped secrets.

**Candidate comparison**

- Vault
- Direct Kubernetes Secrets and sealed-secret-style tooling only
- Cloud-native secret managers as the only abstraction

**Selection rationale**

- The operations design requires explicit secret classes, short-lived runtime injection, revocation, masking, and auditability.
- Vault fits that requirement better than static Kubernetes Secret objects because it supports identity-aware access, dynamic credentials, and revocation.
- Vault also keeps the system portable when production deployment is not locked to one cloud provider.

**Alternatives not chosen**

- Direct Kubernetes Secrets only: acceptable for low-risk configuration, but not sufficient as the main authority for short-lived or revocable runtime secrets.
- Cloud-native secret manager only: good when the deployment vendor is fixed, but premature as the sole design-level dependency while the cluster environment remains open.

**Deferred items**

- Whether Vault reaches workloads through External Secrets Operator, CSI mounts, direct API calls from trusted workers, or a hybrid pattern.
- Whether a cloud-native secret manager is used as Vault’s upstream source in a managed deployment.

**Primary-source anchors**

- [Vault documentation](https://developer.hashicorp.com/vault/docs) documents identity workflows, OIDC, workload identity federation, certificate management, and generation/revocation of on-demand credentials.
- [Vault releases](https://github.com/hashicorp/vault/releases) showed `v1.21.3` on the official release page when verified on 2026-04-20.

### 2.3 Telemetry routing, logs, and traces

**Selected dependencies**

- OpenTelemetry Collector as the telemetry routing layer.
- Grafana Loki as the concrete log backend.
- Grafana Tempo as the concrete trace backend.
- Prometheus and Grafana remain inherited from prior memos for metrics and visualization.

**Candidate comparison**

- OTel Collector versus direct exporter-to-backend wiring
- Loki versus OpenSearch/Elasticsearch-class log stacks
- Tempo versus Jaeger as the primary trace store

**Selection rationale**

- The platform now needs operator-visible queue health, workflow timing, retry classification, evidence completeness, and execution-fleet diagnostics across several trust boundaries.
- OpenTelemetry Collector is the right aggregator boundary because it keeps instrumentation vendor-neutral and lets trusted workers, API services, and execution supervisors ship logs, metrics, and traces through one managed path.
- Loki and Tempo fit the already-selected Grafana ecosystem and keep operational data aligned with the object-storage-oriented platform design.
- This is enough observability infrastructure for platform operations without introducing a separate analytics warehouse into the benchmark control plane.

**Alternatives not chosen**

- Direct exporter wiring from every service to every backend: harder to standardize, secure, and evolve.
- OpenSearch or Elasticsearch as the default log backend: stronger full-text and SIEM stories, but heavier than the benchmark platform needs for its first authoritative release.
- Jaeger as the main trace store: still valid, but Tempo aligns better with the existing Grafana-first stack and object-store posture.

**Deferred items**

- Long-term analytics warehouse for cross-run trend analysis beyond operational dashboards.
- SIEM forwarding and compliance export topology.

**Primary-source anchors**

- [OpenTelemetry Collector docs](https://opentelemetry.io/docs/collector/) describe the Collector as a vendor-agnostic implementation for receiving, processing, and exporting telemetry data.
- [OpenTelemetry Collector releases](https://github.com/open-telemetry/opentelemetry-collector/releases) showed `v0.146.0` on 2026-02-17 when verified on 2026-04-20.
- [Grafana Loki docs](https://grafana.com/docs/loki/latest/) describe Loki as open-source logging components built around a small index and compressed chunks stored in object storage.
- [Grafana Loki releases](https://github.com/grafana/loki/releases) showed active `3.6.x` releases on 2026-02-23 when verified on 2026-04-20.
- [Grafana Tempo docs](https://grafana.com/docs/tempo/latest/) describe Tempo as an open-source, high-scale distributed tracing backend that integrates with Grafana, Prometheus, Loki, and OpenTelemetry.
- [Grafana Tempo releases](https://github.com/grafana/tempo/releases) showed `v2.10.0` on 2026-01-26 when verified on 2026-04-20.

## 3. Operator console dependencies

### 3.1 Identity provider boundary

**Selected dependency**

- Keycloak as the internal identity provider and OIDC/OAuth 2.0 authority for the operator console and related automation clients.

**Candidate comparison**

- Keycloak
- Authentik
- Zitadel or similar hosted/self-hosted identity layers

**Selection rationale**

- The console architecture now has clear personas, capability classes, and repository-scoped permissions.
- That makes it reasonable to lock the IdP boundary, even though the exact Next-side session helper remains a replaceable implementation detail.
- Keycloak is mainstream, self-hostable, supports OIDC/OAuth 2.0, and leaves room for later fine-grained authorization or federation without forcing the benchmark platform into an external SaaS dependency immediately.

**Alternatives not chosen**

- Authentik: strong option, but smaller and less established for the sort of internal platform/IAM footprint this system may grow into.
- Zitadel-class products: good modern choice, but less conservative than Keycloak for a platform whose core promise is auditability and self-hostability.

**Deferred items**

- Public or external-user federation.
- The exact Next.js session wrapper or middleware package. The hard lock is standard OIDC/OAuth 2.0 against Keycloak, not one frontend helper library.

**Primary-source anchors**

- [Keycloak documentation](https://www.keycloak.org/documentation) documents securing applications and services, server administration, and authorization services.
- [Keycloak releases](https://github.com/keycloak/keycloak/releases) showed `26.6.1` on 2026-04-15 when verified on 2026-04-20.

### 3.2 Component library

**Selected dependency**

- Material UI as the operator console component library.

**Candidate comparison**

- Material UI
- Ant Design
- Headless primitives only

**Selection rationale**

- The operator console now has enough concrete list/detail pages, forms, dialogs, review queues, and state-rich action flows to justify a full component library.
- Material UI is broad enough to cover dense internal console workflows without rebuilding commodity components from scratch.
- It still allows a custom design layer later, which matters because the project may eventually want a visual identity distinct from stock Material defaults.

**Alternatives not chosen**

- Ant Design: mature, but less aligned with building a custom branded system later and less appealing if the product eventually needs a more restrained audit-console visual language.
- Headless primitives only: too much assembly work for a console that already has many standard admin interaction patterns.

**Deferred items**

- A later repository-specific design system layer that may sit on top of or gradually replace stock Material UI presentation.

**Primary-source anchors**

- [Material UI overview](https://mui.com/material-ui/getting-started/) describes Material UI as an open-source React component library with a comprehensive set of production-ready components and customization options.
- [Material UI releases](https://github.com/mui/material-ui/releases) showed `v7.3.9` on 2026-03-05 when verified on 2026-04-20.

### 3.3 Artifact and diff viewer

**Selected dependency**

- Monaco Editor for read-only evidence browsing and diff-oriented artifact inspection.

**Candidate comparison**

- Monaco Editor
- CodeMirror 6
- Plain syntax-highlighted HTML viewers

**Selection rationale**

- The run-detail screen is explicitly the deepest inspector in the product and needs to handle logs, patches, transcripts, and code-like artifacts.
- Monaco provides a mature editor and diff-viewing experience without requiring the project to build a bespoke evidence viewer.
- It is better suited than plain rendered HTML for large code-like artifacts and side-by-side inspection workflows.

**Alternatives not chosen**

- CodeMirror 6: still a good alternative, especially for lighter or more embeddable text editing, but Monaco is the stronger default when the main requirement is rich code inspection and diffing.
- Plain highlighted HTML: too weak for serious evidence review and operator triage.

**Deferred items**

- AST-aware semantic diffing or repository-language-specific review widgets.

**Primary-source anchors**

- [Monaco Editor repository](https://github.com/microsoft/monaco-editor) describes Monaco as the fully featured code editor from VS Code and as a browser-based code editor.
- The same official repository showed `v0.55.1` as the latest stable release on 2025-11-20 and ongoing `v0.56.0-dev-*` prereleases in February 2026 when verified on 2026-04-20.

### 3.4 Embedded charting

**Selected dependency**

- Recharts for embedded repository, run, and decision summary charts inside the console.

**Candidate comparison**

- Recharts
- Apache ECharts
- Nivo/visx-class chart stacks

**Selection rationale**

- The operator console needs embedded summary visuals, but the deeper operational dashboards still belong in Grafana.
- Recharts is a practical fit for the console’s lighter chart needs because it is React-native, SVG-based, and does not pull the frontend toward a heavier dashboarding engine too early.
- This keeps the application chart layer simple while preserving an upgrade path if evidence density later demands a more powerful engine.

**Alternatives not chosen**

- Apache ECharts: more powerful, but heavier than necessary for the initial repository/run summary views.
- visx or similar low-level libraries: flexible, but would force more custom chart assembly than the current console warrants.

**Deferred items**

- WebSocket or SSE transport for live chart updates. The current console design still prefers polling and cache refresh over a separate streaming state model.
- Heavier charting or analytics engines if the console grows into a full dashboard product rather than an audit-and-control surface.

**Primary-source anchors**

- [Recharts repository](https://github.com/recharts/recharts) describes Recharts as a chart library built with React and D3 and emphasizes declarative React components with native SVG support.
- The same official repository showed `v3.8.1` as the latest release on 2026-03-25 when verified on 2026-04-20.

## 4. Remaining deliberate deferrals

These choices still should not be hard-locked in this phase:

- GitOps controller selection between Argo CD and Flux.
- Exact ingress/gateway controller.
- Exact Vault-to-cluster wiring method such as ESO, CSI, or trusted-worker API mediation.
- Public or external-user identity federation beyond the internal Keycloak boundary.
- Live-stream transport for console progress beyond polling.
- Long-term analytics warehouse or SIEM export product.

Each deferral remains deployment-shaped rather than benchmark-shaped. The architecture is now specific enough to lock the core implementation dependencies above, but not specific enough to justify freezing every surrounding platform product.

## 5. Change versus earlier dependency memos

- No earlier baseline dependency is reversed.
- The previous S3-compatible storage decision is now concretized to `boto3` for Python integration.
- The previous platform-operations deferrals are narrowed by locking Kubernetes, Helm, Vault, OpenTelemetry Collector, Loki, and Tempo.
- The previous operator-console deferrals are narrowed by locking Keycloak, Material UI, Monaco Editor, and Recharts.
- Redis remains intentionally excluded because the control-plane and workflow docs do not yet justify a second coordination or caching dependency.
