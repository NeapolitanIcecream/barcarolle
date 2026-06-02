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

## Step 1 - Reader Argument Map

Created:

```text
docs/research/barcarolle-project-showcase-deck-zh/project-argument-map-v1.zh.md
```

Acceptance evidence:

- The map is organized by audience, reader questions, condition, consequence, response, main claim, reasons, evidence, warrants, objections, responses, and future work.
- It frames the core problem as target-repository prediction for a named ACUT, not as a deck or packet problem.
- It positions related work as adjacent contributions rather than failed competitors.
- It covers the benchmark-compiler method, algorithm evolution environment, current effects, unproven limits, Agent License, and Agent Tuning.
- It preserves the current evidence boundary: predictive validity and tuning-loop improvement remain unproven.

## Step 2 - Related-Work Positioning

Created:

```text
docs/research/barcarolle-project-showcase-deck-zh/related-work-positioning-v1.zh.md
```

Acceptance evidence:

- The note positions SWE-bench, SWE-bench Verified, SWE-bench-Live, SWE-smith, and R2E-Gym by contribution and remaining Barcarolle layer.
- It describes related work as adjacent and useful rather than failed or replaceable.
- It defines Barcarolle's distinct layer as repo-specific benchmark release compilation for a target repository and named ACUT boundary.
- It uses only source-approved claims already present in the main proposal report; no public browsing or new citations were added.

## Step 3 - New Deck Outline

Created:

```text
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v1.zh.md
```

Acceptance evidence:

- The outline uses the 15-slide project-showcase architecture: problem, stakes, related work, Barcarolle's layer, north star, method, ACUT boundary, selection problem, algorithm environment, current effects, limits, future validation, Agent License, and Agent Tuning.
- Each slide records visible title, main message, visual object, essential evidence or example, and content to omit.
- Related work appears in the main story rather than in an appendix.
- Agent License and Agent Tuning appear as future productization paths with current non-proof boundaries preserved.
- Required forbidden-language, overclaim, local-path, and scoped whitespace checks passed for the outline.

## Step 4 - New Chinese PPTX

Created:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v1.zh.pptx
```

Presentation workspace:

```text
outputs/019e8612-2054-7261-838f-a9823b236589/presentations/barcarolle-project-showcase-deck-zh/
```

Acceptance evidence:

- Used the Presentations artifact-tool workflow with `create` task mode and primary `engineering-platform` deck profile.
- Created `profile-plan.txt` in the thread-scoped presentation workspace.
- Generated 15 editable artifact-tool slides using text, shapes, lines, matrices, workflows, and evidence callouts; no decorative generated images or imagegen assets were used.
- Rendered all slides to PNG, generated layout JSON, and generated a contact sheet through `build_artifact_deck.mjs`.
- Final build manifest reported `slideCount: 15` and non-empty output (`73293` bytes in the workspace build).
- Visual iteration fixed right-edge clipping on slides 2, 3, and 15 and an overfull boundary node on slide 8.
- `check_layout_quality.mjs --warn-only` reported `0` errors and `7` tight-text warnings; rendered warning areas were manually checked and did not show clipping or label collision.
- The final PPTX follows the project-showcase architecture and preserves the current non-proof boundaries for predictive validity and tuning-loop improvement.
