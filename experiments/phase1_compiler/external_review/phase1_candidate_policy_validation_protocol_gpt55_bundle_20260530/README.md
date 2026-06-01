# GPT-5.5-Pro External Review Bundle

Status: prepared for external adversarial review; not submitted here.

This bundle is a compact, sanitized review package for Barcarolle Phase 1's
candidate benchmark policy and validation protocol.

Primary file to paste into GPT-5.5-Pro:

```text
PROMPT_FOR_GPT55_PRO.md
```

The prompt tells the reviewer what to inspect, what claims are allowed, and how
to use the included files. If the reviewer can browse GitHub, it should use:

```text
Repository: https://github.com/NeapolitanIcecream/barcarolle
Branch: codex/restart-benchmark-compiler
Commit: da8d9977f823952932efb67ecab5c068f1bc5531
```

Use the bundle as the authoritative starting packet. Use GitHub only to inspect
additional referenced artifacts that are not included here.

## Directory Map

```text
review_packet/
  Existing concise review packet: context, evidence index, claim boundary, and
  review questions.

core_reports/
  Human-readable reports for the candidate policy, validation protocol,
  success criteria, selection manifest, retrospective signal, source-quality
  repair, and fairness/gap diagnostics.

core_results/
  JSON artifacts matching the core reports. These are better for exact values
  and hashes.

context/
  AGENTS.md, PROCESS.md, the runbooks that produced the current state, and the
  0519 / 0526 research planning documents.

github_reference/
  Instructions for finding additional material in GitHub.
```

## Boundary

This bundle intentionally excludes raw prompts, raw completions, raw ACUT
transcripts, solver workspaces, verifier workspaces, raw diffs, raw test
patches, target repository clones, secrets, caches, and large raw outputs.

The current allowed claim is only:

```text
Barcarolle has a deterministic, outcome-blind candidate policy and frozen
validation protocol ready for adversarial review.
```

This bundle does not establish predictive validity and does not authorize new
paid ACUT runs.
