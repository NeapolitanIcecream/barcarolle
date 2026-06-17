# Task Generator hypothesis registry

生成时间：`2026-06-17T14:19:35+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

| ID | Family | Hypothesis | Experiment | Decision |
| --- | --- | --- | --- | --- |
| H1_selection_demo_pipeline_shape | Selection-Demo compatibility | Use the boltons pattern: exact certified task rows first, then corrected windows from a task-time ordered manifest. | Build final Sphinx/mypy manifests and windows from exact certified rows only. | kept |
| H2_support_root_oracles | Support-root oracle extraction | Changed support files must be injected with verifier entry files so hidden oracles are self-contained. | Mypy injects changed test-data files; Sphinx records and preserves support-root oracle metadata. | kept |
| H3_repo_specific_adapters | Repo-specific oracle adapters | Mypy data-driven tests and Sphinx roots need adapters instead of a generic Python-test-only miner. | Add mypy TypeCheckSuite nodeid adapter and Sphinx support-root manifest conversion. | kept |
| H4_version_aware_profiles | Version-aware verifier profiles | Historical task time should choose bounded Python/dependency profiles. | Try date-compatible uv profiles and stop on first reference pass. | kept |
| H5_fail_to_pass_guards | Fail-to-pass/pass-to-pass guards | Exact certification must require target-pass/base-fail replay and record pass-to-pass guard feasibility. | Reference target and base-with-injected-tests subgates are mandatory; pass-to-pass guard recorded as not run when no stable adjacent guard exists. | kept |
| H6_public_statement_provenance | Public context statement provenance | Issue/PR refs are preferred, but low-confidence commit-message-only rows can be labeled when no paid LLM review is used. | Manifest exposes solver_visible_statement_provenance and source_confidence_label. | kept |
