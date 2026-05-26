# Phase 1 Reference-Pass Failure Inventory

Plain-language summary: this inventory counts every candidate whose first failing local certification gate was `reference_pass`. It records only sanitized command metadata and hashes, not raw stdout or stderr.

## Counts By Repo

| repo | reference_pass failures |
| --- | ---: |
| attrs | 54 |
| boltons | 22 |

## Top Repeated Failure Signatures

| signature | count |
| --- | ---: |
| `1|0c281d21831a|e3b0c44298fc` | 1 |
| `1|7158f8f8bbc6|e3b0c44298fc` | 1 |
| `1|1e59aebbb45c|e3b0c44298fc` | 1 |
| `1|2e699eddc5b8|e3b0c44298fc` | 1 |
| `1|3ce07c2a21f0|e3b0c44298fc` | 1 |
| `1|4d7959937585|e3b0c44298fc` | 1 |
| `1|b772089a017b|e3b0c44298fc` | 1 |
| `4|ce72dd5edb78|e3b0c44298fc` | 1 |
| `2|68e1467ca44d|b7f5c3bc1fad` | 1 |
| `2|8a1611cd8ffb|0f87eeb6f521` | 1 |
| `2|49e354419427|402f4e58cebf` | 1 |
| `2|b2b19e0f9113|63db1ba5bdc5` | 1 |

## Prioritized Replay Sample

| repo | task | priority | year | reason |
| --- | --- | --- | ---: | --- |
| attrs | `attrs__supply_expansion_20260526__030` | high | 2015 | no_op_failed_as_expected_but_reference_failed,simple_one_code_one_test_change,old_commit_environment_drift_risk |
| attrs | `attrs__supply_expansion_20260526__037` | high | 2015 | no_op_failed_as_expected_but_reference_failed,simple_one_code_one_test_change,old_commit_environment_drift_risk |
| attrs | `attrs__supply_expansion_20260526__039` | high | 2016 | no_op_failed_as_expected_but_reference_failed,old_commit_environment_drift_risk |
| attrs | `attrs__supply_expansion_20260526__042` | high | 2016 | no_op_failed_as_expected_but_reference_failed,old_commit_environment_drift_risk |
| attrs | `attrs__supply_expansion_20260526__043` | high | 2016 | no_op_failed_as_expected_but_reference_failed,old_commit_environment_drift_risk |
| attrs | `attrs__supply_expansion_20260526__044` | high | 2016 | no_op_failed_as_expected_but_reference_failed,old_commit_environment_drift_risk |
| boltons | `boltons__supply_expansion_20260526__086` | high | 2017 | no_op_failed_as_expected_but_reference_failed,simple_one_code_one_test_change,old_commit_environment_drift_risk |
| boltons | `boltons__supply_expansion_20260526__090` | high | 2018 | no_op_failed_as_expected_but_reference_failed,simple_one_code_one_test_change |
| boltons | `boltons__supply_expansion_20260526__091` | high | 2018 | no_op_failed_as_expected_but_reference_failed,simple_one_code_one_test_change |
| boltons | `boltons__supply_expansion_20260526__096` | high | 2018 | no_op_failed_as_expected_but_reference_failed,simple_one_code_one_test_change |
| boltons | `boltons__supply_expansion_20260526__097` | high | 2018 | no_op_failed_as_expected_but_reference_failed,simple_one_code_one_test_change |
| boltons | `boltons__supply_expansion_20260526__098` | high | 2018 | no_op_failed_as_expected_but_reference_failed,simple_one_code_one_test_change |

## Grouped Counts

- repo_id: `attrs`=54, `boltons`=22
- year: `2015`=2, `2016`=11, `2017`=19, `2018`=18, `2019`=26
- module_or_package: `__init__,_make`=1, `__init__,_make,exceptions`=1, `_compat`=3, `_compat,_make`=2, `_funcs`=7, `_funcs,_make`=1, `_make`=31, `_make,exceptions`=1, `_make,validators`=2, `dictutils`=7, `exceptions,validators`=1, `funcutils`=2
- test_files: `tests/__init__.py,tests/test_funcs.py`=3, `tests/test_annotations.py,tests/test_dark_magic.py,tests/test_make.py`=2, `tests/test_dark_magic.py`=5, `tests/test_dark_magic.py,tests/test_dunders.py`=1, `tests/test_dark_magic.py,tests/test_dunders.py,tests/test_filters.py,tests/test_funcs.py,tests/test_make.py,tests/utils.py`=1, `tests/test_dark_magic.py,tests/test_make.py`=2, `tests/test_dark_magic.py,tests/test_make.py,tests/typing_example.py`=1, `tests/test_dark_magic.py,tests/test_make.py,tests/utils.py`=1, `tests/test_dark_magic.py,tests/test_validators.py,tests/utils.py`=1, `tests/test_dictutils.py`=7, `tests/test_dunders.py`=6, `tests/test_dunders.py,tests/typing_example.py`=1
- change_size_bucket: `l_201_plus`=3, `m_81_200`=22, `s_21_80`=39, `xs_0_20`=12
- candidate_filter_status: `accepted`=60, `manual_review_required`=16
- source_context_status: `diff_assisted_statement_needed`=12, `non_leaky_problem_context`=64
- reference_run_1_returncode: `1`=23, `2`=51, `4`=2
- reference_run_2_returncode: `1`=23, `2`=51, `4`=2
- stderr_tail_hash: `037845dc91f4`=1, `03a1d65f630f`=1, `06dc345dd930`=1, `0c281d21831a`=1, `0fa307b1f5be`=1, `1000cf106d00`=1, `1296613e8d0f`=1, `13b545da7255`=1, `156d5dbbcbf0`=1, `1e59aebbb45c`=1, `1e9eb1cff33d`=1, `21bedc920d04`=1
- stdout_tail_hash: `0c140a7842fa`=1, `0dab9f49da35`=1, `0f87eeb6f521`=1, `159a802df7e1`=1, `1e6c8bc81219`=1, `2172a8227ab9`=1, `2bdedc337219`=1, `2d2c99381343`=1, `2e6ff23cd2da`=1, `2e9467441902`=1, `34cf064bbe71`=1, `359e2d46a842`=1
- duration_bucket: `1s_to_5s`=2, `lt_1s`=74
