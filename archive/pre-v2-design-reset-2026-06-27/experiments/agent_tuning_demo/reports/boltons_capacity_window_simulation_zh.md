# Boltons rolling-origin window capacity simulation

Generated at: `2026-06-15T05:08:30+00:00`. Paid cells run: `0`.

## Summary

| Metric | Value |
| --- | --- |
| Conservative projected release pool | 57 |
| Projected time buckets | {'legacy_2018_or_earlier': 25, 'middle_2019_2022': 20, 'recent_2023_or_later': 12} |
| Count-only windows meeting min counts | 2 |
| Evidence-backed Phase2b-style windows | 1 |
| Two-window dev-only cost estimate | $1.7949 |
| Two-window if both futures run | $3.3904 |

The conservative projected pool is `57` release tasks: `35` current plus `22` incremental v2 release-eligible rows. This is enough for count-only time-ordered partitions, but not enough for a persuasive evidence-backed multi-window Agent Tuning Demo.

## Result

Current evidence supports one Phase 2b-style window: `boltons_time_ordered_w1_train2015_2018_dev2019_2020_future2022_2023`. It has current Kilo low-cost dev/future headroom, but the actual Phase 2b dev gate was negative (`4/6 -> 4/6`, paired net wins `0`).

The two projected windows in the JSON meet minimum counts only by using newly certified tasks whose Kilo baseline headroom is unknown. They are therefore not equivalent to two prepared rolling-origin windows.

## Cost

Using Phase 2b observed Agent-cell cost (`$0.049859` per cell), a single 6-dev/8-future minimum window is about `$1.6952` if future runs. Two such windows would be about `$3.3904` if both dev gates pass. These estimates exclude proposer LLM calls and do not authorize any paid work.
