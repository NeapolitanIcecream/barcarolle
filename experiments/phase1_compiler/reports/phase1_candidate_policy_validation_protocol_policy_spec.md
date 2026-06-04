# Candidate Policy Spec

What happened: froze `coverage_constrained_unweighted_v1` as a deterministic, outcome-blind candidate policy.

Why it matters: future review can inspect an exact rule instead of an informal retrospective winner.

Action suggested next: run the selector, audit outcome-blindness, then use the frozen validation protocol before any future paid work.

Policy ID: `coverage_constrained_unweighted_v1`.
Budget per repo: `6`.
Seed: `2026053001`.

Forbidden inputs include terminal outcomes, pass/fail labels, adapter outcomes, score-table rows, raw ACUT transcripts, and hidden verifier output.
