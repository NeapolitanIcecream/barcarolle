# Core Narrative Experiment

This directory contains the small, auditable experiment scaffold for validating the Barcarolle core narrative:

> General coding-agent benchmark rank is not enough evidence for repository-specific work quality.

The experiment follows `docs/experiments/core-narrative-experiment-plan.md`. It intentionally starts with protocolized artifact construction, minimal schemas, and runner/verifier glue before any platform productization.

## Current Phase

Phase 0 bootstrap is in progress. Wave 0 workers are responsible for:

- selecting a primary target repository;
- drafting the minimal schemas and tools;
- freezing the ACUT matrix;
- recording the general benchmark basis;
- enforcing the LLM access and budget contract before any ACUT execution.

Large or volatile artifacts stay out of Git. See `.gitignore` for the local workspace, clone, cache, and log paths.

## Execution Budget

ACUT execution is budget-constrained by default. LLM access must use only the environment variables named in `configs/llm_access.yaml`; credential values must never be written to repository artifacts. Cost records are appended to `results/cost_ledger.jsonl`. Broad execution remains blocked until the ledger gate is implemented and reviewed.
