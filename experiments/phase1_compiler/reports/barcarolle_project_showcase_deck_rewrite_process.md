# Barcarolle Project Showcase Deck Rewrite Process

Date: 2026-06-02 10:04:06 CST

Runbook:

```text
docs/experiments/barcarolle-project-showcase-deck-rewrite-runbook.md
```

## Step 0 - Preflight And Supersession Boundary

Branch: `codex/restart-benchmark-compiler`

HEAD at preflight:

```text
2bad06e1fd2da1476e86a1151983bd1d59202e90
```

Pre-existing worktree status:

```text
 M PROCESS.md
 M docs/research/phase-1-proposal-roadmap-and-claim-planning.md
?? docs/experiments/barcarolle-project-showcase-deck-rewrite-runbook.md
```

Input availability:

- `AGENTS.md` present.
- `PROCESS.md` present.
- `docs/research/barcarolle-proposal-report-v5.md` present.
- `docs/research/m6-approval-packet-zh/README.md` present.
- `docs/research/m6-approval-packet-zh/terminology-glossary-v1.zh.md` present.
- `docs/research/m6-approval-packet-zh/approval-deck-outline-v1.zh.md` present.
- `docs/research/m6-approval-packet-zh/barcarolle-approval-deck-v1.zh.pptx` present.
- `experiments/phase1_compiler/reports/proposal_approval_packet_zh_supplement_decision.md` present.
- `docs/research/phase-1-proposal-evidence-package.md` present.
- `docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md` present.
- `experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md` present.
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_decision.md` present.
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md` present.

Supersession boundary:

- The existing Chinese M6 packet is an approval-packet localization.
- Its deck structure is too closely mapped from V5/M6 source order for the new project-showcase purpose.
- It includes process vocabulary and reader-irrelevant milestone structure.
- It does not fully organize the reader story around problem, method, effects, limitations, and future product paths.
- The old Chinese approval packet remains traceability material and fact/reference material; it is not the structure for the new deck.

Execution boundary:

- No paid ACUT calls made.
- No paid LLM calls made.
- No external reviewer calls made.
- No public browsing performed.
- No generated raster images or imagegen used.
- New package directory created at `docs/research/barcarolle-project-showcase-deck-zh/`.
- No reader-facing deck content drafted in Step 0.

