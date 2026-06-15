# Agent Tuning Phase 2b protocol

Generated at: `2026-06-15T03:20:45+00:00`.

Status: `frozen_before_llm_proposer_or_paid_agent_cells`.

## Frozen route

- Proposer: `GEPA-shaped reflective LLM proposer`
- Target Agent: `Kilo + GPT low-cost` (`kilo_gpt_5_4_mini`)
- Artifact surface: Kilo repo `AGENTS.md` appendix
- Window: `boltons_time_ordered_w1_train2015_2018_dev2019_2020_future2022_2023`
- Train/dev/future counts: `10` / `6` / `10`
- Future task IDs withheld: `True`

## Paid caps

- LLM proposer calls max: `8`
- Agent paid cells max: `72`
- Planned cells if future runs: `38`
- Soft cost cap: `$8.0`

## Gates

- Dev requires positive paired net wins before future validation.
- Future green requires positive aggregate paired net wins and no material regression.
- A single selected window can support only a time-ordered demo claim, not a multi-window rolling-origin claim.

## Stop conditions

- Stop before LLM proposer if LLM_BASE_URL or LLM_API_KEY is missing after sourcing ~/.zshrc.
- Stop or label as non-LLM control if no LLM proposal/reflection step runs.
- Stop before future validation if no dev candidate has positive paired net wins.
- Stop if paid-cell or cost caps would be exceeded.
- Stop if any candidate contains dev/future task IDs or future-derived content.
