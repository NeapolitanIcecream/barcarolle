# Phase 1 Reference-Pass Root Cause Taxonomy

Plain-language summary: this classifies reference-pass failures with the evidence available from the replay sample, patch checks, and repeated signatures. Unknowns stay unknown instead of being overclaimed.

## Root Cause Counts

| label | count |
| --- | ---: |
| dependency_version_drift | 1 |
| pytest_collection_or_config_error | 5 |
| python_version_drift | 6 |
| unclassified_reference_fail | 64 |

## Supply Impact

- candidates_still_blocked: 76
- candidates_needing_environment_synthesis_repair: 12
- candidates_eligible_after_validation_code_fix: 0
- candidates_needing_remine_or_exclusion: 0
