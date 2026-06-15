# Boltons capacity current inventory

Generated at: `2026-06-15T05:08:30+00:00`. Paid cells run: `0`.

## Summary

| Metric | Value |
| --- | --- |
| Deduped candidate anchors | 433 |
| Current release-eligible/certified tasks | 35 |
| Kilo low-cost tasks with outcome rows | 30 |
| Kilo low-cost scoreable tasks | 28 |
| Complete four-Agent outcome tasks | 30 |
| Phase 2b usable selected-window tasks | 10 train / 6 dev / 10 future |

The current committed inventory has many candidate anchors but a much thinner scoreable layer. Across candidate-like committed sources I found `433` deduped boltons anchors. The current release/selectable layer is `35` tasks, and the current Kilo low-cost outcome layer has `30` tasks with rows, `28` of them scoreable.

## Why Phase 2b Had One Window

Phase 2b could use one 10/6/10 train/dev/future split. The other available time-ordered splits had only four dev tasks and failed headroom: one dev slice was above the preferred range at `0.75`, and one was saturated at `1.0` after excluding an unscoreable row. The bridge and unused rows did not create another credible dev/future window.

## Time And Coverage

Selector-table task roles: `{'holdout': 10, 'selection': 20, 'smoke': 1, 'unused': 4}`.

Selector-table time buckets for all 35 release tasks: `{'legacy_2018_or_earlier': 10, 'middle_2019_2022': 13, 'recent_2023_or_later': 12}`. Selection+Holdout only: `{'legacy_2018_or_earlier': 10, 'middle_2019_2022': 13, 'recent_2023_or_later': 7}`. The older predictive-validity inventory records bucket counts `{'legacy_2018_or_earlier': 24, 'middle_2019_2022': 8, 'recent_2023_or_later': 3}`; this audit keeps both source-specific views rather than forcing them to agree.

Module coverage from the 35 selector-table tasks: `{'cacheutils': 3, 'dictutils': 2, 'fileutils+jsonutils': 1, 'funcutils': 4, 'ioutils': 1, 'iterutils': 8, 'listutils': 1, 'mathutils': 1, 'setutils': 2, 'socketutils': 1, 'strutils': 1, 'tbutils': 6, 'timeutils': 3, 'urlutils': 1}`.

## Gap Definition

Raw candidates are mined task anchors. Certified candidates have local certification and hidden oracle material. Scoreable paid outcomes are Agent result rows. Phase 2b windows additionally need time order, train/dev/future counts, and baseline headroom. The large drop is therefore expected: `433` raw-ish anchors -> `35` release tasks -> `30` Kilo outcome tasks -> one usable 10/6/10 window.
