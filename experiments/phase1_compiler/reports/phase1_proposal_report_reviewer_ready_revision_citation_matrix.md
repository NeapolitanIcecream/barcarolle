# Phase 1 Proposal Report Reviewer-Ready Revision Citation Matrix

Status: M5 citation matrix, 2026-06-01.

Public browsing was used only for reviewer-facing related-work and benchmark-validity citation verification. No paid ACUT cells, paid LLM calls, or external reviewer calls were made.

## Citation Matrix

| Label | Public source | Date | Supports in v2 | Must not be used for | V2 location |
| --- | --- | --- | --- | --- | --- |
| `SWE-bench-2024` | [SWE-bench ICLR 2024 paper](https://juanmirod.github.io/public/papers/swe-bench_2310.06770v3.pdf) | ICLR 2024 | SWE-bench evaluates repository-level issue resolution by giving models a codebase and issue and scoring generated patches with repository tests; it uses real GitHub issues/PRs and execution-based filtering. | A claim that SWE-bench predicts any given target repository's future work distribution or replaces repo-specific validation. | Sections 2 and 3 |
| `SWE-bench-Verified-2024` | [OpenAI, Introducing SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) | 2024-08-13; page updated 2025-02-24 | SWE-bench Verified is a human-validated quality-improved subset intended to remove infeasible or underspecified tasks and improve evaluation reliability. | A claim that human validation fully solves contamination, oracle quality, or target-repo predictive validity. | Section 2 and Appendix B |
| `SWE-bench-Verified-2026` | [OpenAI, Why SWE-bench Verified no longer measures frontier coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) | 2026-02-23 | Public benchmark scores can become less informative when task tests are flawed or benchmark material is contaminated; evaluator-side quality and contamination audits matter. | A claim that all SWE-bench-family results are invalid or that Barcarolle's current evidence avoids every contamination risk. | Sections 2, 6, and 7 |
| `SWE-bench-Live-2025` | [SWE-bench-Live project page](https://swe-bench-live.github.io/) | 2025; monthly-update project page | Live benchmark maintenance addresses freshness and contamination by adding newly verified task instances and maintaining frozen comparison splits. | A claim that live updates alone produce target-repo predictive validity or replace a frozen repo-specific release protocol. | Section 2 |
| `SWE-smith-2025` | [SWE-smith project page](https://swesmith.com/) | 2025-04-30 | SWE-smith is a scalable task-instance generation system for software engineering agents, with large generated supply across GitHub repositories. | A claim that Barcarolle is itself a task generator, or that generated tasks can enter a Barcarolle release without local certification. | Sections 2, 3, and 7 |
| `R2E-Gym-2025` | [R2E-Gym official repository](https://github.com/R2E-Gym/R2E-Gym) | COLM 2025 / arXiv 2025 | R2E-Gym focuses on procedurally curated executable environments and hybrid verifiers for training and scaling software-engineering agents. | A claim that Barcarolle should become an agent-training gym, ACUT harness, or verifier-scaling framework. | Sections 2 and 3 |
| `Validity-Challenges-2022` | [Validity Challenges in Machine Learning Benchmarks](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2022/EECS-2022-180.html) | 2022 | Benchmark validity concerns whether benchmark findings generalize to new settings; benchmark score gains can diverge from real deployment reliability. | A claim that Barcarolle has already established construct or predictive validity. | Sections 1, 2, and 6 |

## Source-Use Rules For V2

- Use public sources only for the external related-work and benchmark-validity framing.
- Use committed Barcarolle reports for Phase 1 evidence, M3 numbers, M4 gates, artifact hygiene, source repair, adapter handling, and current claim boundaries.
- Do not cite local planning files as reviewer-facing literature support.
- Do not cite public benchmark projects as proof that Barcarolle's current candidate has predictive validity.
- Do not use `SWE-bench-Verified-2026` to overstate contamination as universal. Use it as evidence that public SWE benchmark quality and contamination require active governance.

## Citation Coverage Summary

The matrix covers the M5 minimum related-work requirements:

| Requirement | Covered by |
| --- | --- |
| SWE-bench-family or SWE-bench | `SWE-bench-2024` |
| SWE-bench Verified or quality-improved variant | `SWE-bench-Verified-2024`; `SWE-bench-Verified-2026` |
| SWE-bench Live or contamination-aware benchmark maintenance | `SWE-bench-Live-2025`; `SWE-bench-Verified-2026` |
| SWE-smith or generated task systems | `SWE-smith-2025` |
| R2E-Gym or agent-training/evaluation environments | `R2E-Gym-2025` |
| Benchmark evaluation validity, predictive validity, or construct validity | `Validity-Challenges-2022` |
