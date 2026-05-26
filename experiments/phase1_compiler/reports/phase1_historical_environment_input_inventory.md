# Phase 1 Historical Environment Input Inventory

Selected known failures: `36` of `76` reference_pass failures.

Plain-language summary: the sample includes all 12 previously replayed failures and 24 additional unclassified failures selected for unique stderr hashes, old target dates, simple test-file sets, and interpretable no-op behavior. This is enough for a bounded screen, not a full census.

## Counts

| group | count |
| --- | ---: |
| required previously replayed | 12 |
| additional unclassified | 24 |
| unique stderr hashes | 36 |

## Counts By Repo

| repo | selected |
| --- | ---: |
| attrs | 30 |
| boltons | 6 |

## Selected Tasks

| repo | task | year | previous label | stderr hash | reason |
| --- | --- | ---: | --- | --- | --- |
| attrs | `attrs__supply_expansion_20260526__030` | 2015 | dependency_version_drift | `0c281d21831a` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=dependency_version_drift |
| attrs | `attrs__supply_expansion_20260526__037` | 2015 | pytest_collection_or_config_error | `7158f8f8bbc6` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=pytest_collection_or_config_error |
| attrs | `attrs__supply_expansion_20260526__039` | 2016 | pytest_collection_or_config_error | `c01df2252c91` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=pytest_collection_or_config_error |
| attrs | `attrs__supply_expansion_20260526__042` | 2016 | pytest_collection_or_config_error | `1e59aebbb45c` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=pytest_collection_or_config_error |
| attrs | `attrs__supply_expansion_20260526__043` | 2016 | pytest_collection_or_config_error | `2e699eddc5b8` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=pytest_collection_or_config_error |
| attrs | `attrs__supply_expansion_20260526__044` | 2016 | pytest_collection_or_config_error | `3ce07c2a21f0` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=pytest_collection_or_config_error |
| boltons | `boltons__supply_expansion_20260526__086` | 2017 | python_version_drift | `13b545da7255` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=python_version_drift |
| boltons | `boltons__supply_expansion_20260526__090` | 2018 | python_version_drift | `21bedc920d04` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=python_version_drift |
| boltons | `boltons__supply_expansion_20260526__091` | 2018 | python_version_drift | `efa09bf79b94` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=python_version_drift |
| boltons | `boltons__supply_expansion_20260526__096` | 2018 | python_version_drift | `59df41d6a40c` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=python_version_drift |
| boltons | `boltons__supply_expansion_20260526__097` | 2018 | python_version_drift | `bde4e017e37e` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=python_version_drift |
| boltons | `boltons__supply_expansion_20260526__098` | 2018 | python_version_drift | `6579df98262c` | required_previously_replayed_sample,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=python_version_drift |
| attrs | `attrs__supply_expansion_20260526__045` | 2016 | unclassified_reference_fail | `4d7959937585` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__058` | 2016 | unclassified_reference_fail | `68e1467ca44d` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__059` | 2016 | unclassified_reference_fail | `8a1611cd8ffb` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__046` | 2016 | unclassified_reference_fail | `b772089a017b` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__049` | 2016 | unclassified_reference_fail | `a1c41c16c5b3` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__050` | 2016 | unclassified_reference_fail | `ce72dd5edb78` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__052` | 2016 | unclassified_reference_fail | `29cffc3eda41` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__065` | 2017 | unclassified_reference_fail | `49e354419427` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__069` | 2017 | unclassified_reference_fail | `b2b19e0f9113` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__070` | 2017 | unclassified_reference_fail | `3c0a3c3e3e1b` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__074` | 2017 | unclassified_reference_fail | `739bca84bdf3` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__076` | 2017 | unclassified_reference_fail | `1000cf106d00` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__077` | 2017 | unclassified_reference_fail | `660bdbe1cdb2` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__078` | 2017 | unclassified_reference_fail | `7056b041795b` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__080` | 2017 | unclassified_reference_fail | `fc1fce2419ce` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__085` | 2017 | unclassified_reference_fail | `0fa307b1f5be` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__087` | 2017 | unclassified_reference_fail | `9f54094ccd76` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__088` | 2017 | unclassified_reference_fail | `b7b0863ae171` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__090` | 2017 | unclassified_reference_fail | `f1f792e4d56a` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,simple_test_file_set,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__072` | 2017 | unclassified_reference_fail | `156d5dbbcbf0` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__073` | 2017 | unclassified_reference_fail | `bd295c89889d` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__075` | 2017 | unclassified_reference_fail | `597ef2a93255` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__081` | 2017 | unclassified_reference_fail | `f593041dadff` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=unclassified_reference_fail |
| attrs | `attrs__supply_expansion_20260526__082` | 2017 | unclassified_reference_fail | `4069de1344d1` | additional_unclassified_reference_pass_failure,unique_stderr_hash,old_target_date,noop_behavior_interpretable,previous_label=unclassified_reference_fail |

## Third Repo Screening Order

1. toolz
2. humanize only if toolz fails the local gate

Deferred unless needed later: rich, requests.
