# Task Generator related-work transfer matrix

生成时间：`2026-06-17T14:19:35+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

本矩阵只记录会影响本轮 Sphinx/mypy Task Generator 的机制，不把外部 benchmark 当作 Barcarolle 的项目身份。

| Source | Mechanism | Hypothesis | Experiment | Decision |
| --- | --- | --- | --- | --- |
| SWE-bench | PR/issue-linked tasks with fail-to-pass tests as primary evaluation signal. | Keep PR/issue/commit provenance fields and require target-pass/base-fail replay before manifest inclusion. | Baseline reproduction and exact certification attempts record reference_target and base_with_injected_tests subgates. | kept |
| SWE-bench Verified | Human filtering for clear statements, correct tests, and solvability. | Keep source-confidence, ambiguity, and leakage labels even when no paid LLM review is used. | Manifest rows expose statement provenance and source confidence. | kept |
| SWE-bench Live | Automated issue/PR curation, environment setup, and reproducible execution images. | Use version-aware uv profiles keyed by task time instead of one generic command. | Sphinx and mypy adapters try bounded date-compatible profiles and record profile winners. | kept |
| SWE-Bench++ | Programmatic sourcing, environment synthesis, state-differential oracle extraction, and QA. | Separate entry points from support oracle files and inject all target-commit oracle material into base. | Mypy data-file adapter and Sphinx support-root metadata are evaluated in no-paid certification. | kept |
| SWE-Bench Pro | Held-out/private partitions, human augmented specs, and contamination-resistant design. | Window manifests expose history pools and future holdouts separately, with selected IDs left empty. | Corrected windows for both repos keep future_holdout_after_origin outside selector inputs. | kept |
| SWE-smith | Synthetic tasks that break existing tests after constructing execution environments. | Synthetic reservoirs need separate source caps and predictive-value validation before release. | Not used because real-history exact certification reached the target without synthetic tasks. | deferred |
