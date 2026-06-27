# Boltons capacity final recommendation

Generated at: `2026-06-15T05:08:30+00:00`. Paid cells run: `0`.

## Decision

| Metric | Value |
| --- | --- |
| Terminal state | return_to_target_repo_selection |
| Current boltons release tasks | 35 |
| Conservative projected boltons release tasks | 57 |
| Incremental dry-run release conversion | 22/58 (0.3793) |
| Evidence-backed rolling-origin windows | 1 |
| Best fallback | python-attrs/attrs |

Recommendation: return to target-repository selection / target-prep rather than continuing boltons expansion for the next stronger rolling-origin Agent Tuning Demo.

Boltons can plausibly grow from `35` current release tasks to `57` after bounded expansion. That is useful supply, but it remains below the conservative `>=60` continuation gate and still leaves only one current evidence-backed Phase 2b-style window. The optimistic `64` count depends on source-context repair, which is the dominant bottleneck rather than a solved deterministic path.

## Cost If Continuing Anyway

A single minimum 6-dev/8-future window would cost about `$1.6952` in Agent cells if future runs. Two minimum windows would cost about `$3.3904` if both dev gates pass. These estimates exclude proposer calls and do not authorize paid work.

## Next No-Paid Move

Prepare `python-attrs/attrs` as the fallback target. Minimal repairs: attrs target profile, repo-generic package map/fallback statement handling, a frozen 31-task manifest, verifier environment pinning, and a no-paid replay plus split/freeze dry run. Keep `click` as a supply-ready backup.

## What Not To Do

Do not run another boltons paid tuning pilot under the stronger rolling-origin claim. Use boltons only for a weaker single-window story if the user explicitly accepts that claim boundary.
