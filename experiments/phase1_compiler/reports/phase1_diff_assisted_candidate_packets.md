# Phase 1 Diff-Assisted Candidate Packets

Generated: `2026-05-25T02:52:58Z`.

## Summary

- Candidate packets: `22`.
- Repos: `{'attrs': 18, 'boltons': 4}`.
- Old 240-character cap flags treated as recoverable renderer defects: `19`.
- Raw target diffs committed: `false`.
- Hidden verifier material included: `false`.
- Historical paid outcomes included: `false`.

## Packets

### boltons__clean_ext__001

- Repo: `boltons`.
- Source: `issue:231` (`issue`).
- Public title: iterutils.chunked and chunked_iter raise TypeError for bytes objects
- Editable paths: `boltons/iterutils.py`.
- Non-editable tests: `tests/test_iterutils.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 10 added line(s), 0 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_ends_mid_code_fence', 'statement_probably_truncated']`.

### boltons__clean_ext__008

- Repo: `boltons`.
- Source: `issue:240` (`issue`).
- Public title: Why IndexedSet not update the index of items?
- Editable paths: `boltons/setutils.py`.
- Non-editable tests: `tests/test_setutils.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 28 added line(s), 1 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_probably_truncated']`.

### boltons__clean_ext__010

- Repo: `boltons`.
- Source: `issue:252` (`issue`).
- Public title: setutils.IndexedSet has symmetric difference()
- Editable paths: `boltons/setutils.py`.
- Non-editable tests: `tests/test_setutils.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 12 added line(s), 1 removed line(s).
- Old quality gate: `pass`; risks: `['body_summary_hit_old_240_char_cap']`.

### boltons__clean_ext__017

- Repo: `boltons`.
- Source: `issue:319` (`issue`).
- Public title: boltons.timeutils when start with 12 month and step=(1, 0, 0), result is wrong. because date.month start with 1, not 0
- Editable paths: `boltons/timeutils.py`.
- Non-editable tests: `tests/test_timeutils.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 20 added line(s), 4 removed line(s).
- Old quality gate: `pass`; risks: `[]`.

### attrs__hist__001

- Repo: `attrs`.
- Source: `issue:611` (`issue`).
- Public title: frozen=True incompatible with cache_hash=True as of 19.1.0
- Editable paths: `src/attr/_make.py`.
- Non-editable tests: `tests/test_make.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 23 added line(s), 3 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_probably_truncated']`.

### attrs__hist__003

- Repo: `attrs`.
- Source: `pr:506` (`pull_request`).
- Public title: added first doc stub
- Editable paths: `src/attr/_make.py`.
- Non-editable tests: `tests/test_make.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 40 added line(s), 0 removed line(s).
- Old quality gate: `fail`; risks: `['empty_or_nearly_empty_body_summary', 'pr_context_source', 'pr_context_without_linked_issue', 'statement_missing_public_problem_summary']`.

### attrs__hist__004

- Repo: `attrs`.
- Source: `issue:626` (`issue`).
- Public title: ``__ne__`` dunders changing?
- Editable paths: `src/attr/_make.py`.
- Non-editable tests: `tests/test_make.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 37 added line(s), 16 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_ends_mid_code_fence', 'statement_probably_truncated']`.

### attrs__hist__008

- Repo: `attrs`.
- Source: `pr:669` (`pull_request`).
- Public title: Add attr.field
- Editable paths: `src/attr/__init__.py, src/attr/__init__.pyi, src/attr/_next_gen.py`.
- Non-editable tests: `tests/test_next_gen.py, tests/typing_example.py`.
- Diff summary: 3 implementation file(s) and 2 test file(s) changed; 128 added line(s), 9 removed line(s).
- Old quality gate: `manual_review_required`; risks: `['pr_context_source', 'pr_context_without_linked_issue']`.

### attrs__hist__009

- Repo: `attrs`.
- Source: `issue:670` (`issue`).
- Public title: @attr.define fails to auto-detect __eq__
- Editable paths: `src/attr/_next_gen.py`.
- Non-editable tests: `tests/test_next_gen.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 16 added line(s), 1 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_ends_mid_code_fence', 'statement_probably_truncated']`.

### attrs__hist__010

- Repo: `attrs`.
- Source: `issue:673` (`issue`).
- Public title: Hybrid behavior doesn't work when maybe_cls=None and no annotations
- Editable paths: `src/attr/_next_gen.py`.
- Non-editable tests: `tests/test_next_gen.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 42 added line(s), 8 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_ends_mid_code_fence', 'statement_probably_truncated']`.

### attrs__hist__012

- Repo: `attrs`.
- Source: `issue:680` (`issue`).
- Public title: Using slots class overrides custom `__setattr__` in 20.1.0
- Editable paths: `src/attr/_make.py`.
- Non-editable tests: `tests/test_setattr.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 120 added line(s), 25 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_ends_mid_code_fence', 'statement_probably_truncated']`.

### attrs__hist__013

- Repo: `attrs`.
- Source: `pr:687` (`pull_request`).
- Public title: NG: make frozen classes comfortably subclassable
- Editable paths: `src/attr/_next_gen.py`.
- Non-editable tests: `tests/test_next_gen.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 100 added line(s), 7 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'pr_context_source', 'statement_probably_truncated']`.

### attrs__hist__023

- Repo: `attrs`.
- Source: `issue:593` (`issue`).
- Public title: Deferred type annotations are evaluated in the wrong execution context
- Editable paths: `src/attr/_make.py`.
- Non-editable tests: `tests/test_annotations.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 70 added line(s), 43 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_ends_mid_code_fence', 'statement_probably_truncated']`.

### attrs__hist__027

- Repo: `attrs`.
- Source: `issue:766` (`issue`).
- Public title: Field hooks are too clunky with Python 3.10 / string annotations
- Editable paths: `src/attr/__init__.pyi, src/attr/_funcs.py`.
- Non-editable tests: `tests/test_hooks.py`.
- Diff summary: 2 implementation file(s) and 1 test file(s) changed; 14 added line(s), 4 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'resolve_types_attribs_api_behavior_under_specified', 'statement_probably_truncated']`.

### attrs__hist__032

- Repo: `attrs`.
- Source: `issue:826` (`issue`).
- Public title: Performance degradation after creating many classes with the same name
- Editable paths: `src/attr/_make.py`.
- Non-editable tests: `tests/test_dunders.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 49 added line(s), 36 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_probably_truncated']`.

### attrs__hist__033

- Repo: `attrs`.
- Source: `issue:813` (`issue`).
- Public title: Python 3.10 deprecation in tests due to distutils
- Editable paths: `src/attr/converters.py, src/attr/converters.pyi`.
- Non-editable tests: `tests/test_converters.py, tests/typing_example.py`.
- Diff summary: 2 implementation file(s) and 2 test file(s) changed; 108 added line(s), 7 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_ends_mid_code_fence', 'statement_probably_truncated']`.

### attrs__hist__035

- Repo: `attrs`.
- Source: `issue:821` (`issue`).
- Public title: Using field transformer breaks integration with hypothesis
- Editable paths: `src/attr/_make.py`.
- Non-editable tests: `tests/test_hooks.py`.
- Diff summary: 1 implementation file(s) and 1 test file(s) changed; 25 added line(s), 6 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_probably_truncated']`.

### attrs__hist__036

- Repo: `attrs`.
- Source: `pr:848` (`pull_request`).
- Public title: Make `from attr import *` work again on recent python versions.
- Editable paths: `src/attr/__init__.py`.
- Non-editable tests: `tests/attr_import_star.py, tests/test_import.py`.
- Diff summary: 1 implementation file(s) and 2 test file(s) changed; 18 added line(s), 2 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'pr_context_source', 'pr_context_without_linked_issue', 'statement_probably_truncated']`.

### attrs__hist__039

- Repo: `attrs`.
- Source: `issue:875` (`issue`).
- Public title: matches_re() should accept re.Pattern in addition to str
- Editable paths: `src/attr/validators.py, src/attr/validators.pyi`.
- Non-editable tests: `tests/test_validators.py, tests/typing_example.py`.
- Diff summary: 2 implementation file(s) and 2 test file(s) changed; 63 added line(s), 23 removed line(s).
- Old quality gate: `pass`; risks: `['body_summary_hit_old_240_char_cap']`.

### attrs__hist__041

- Repo: `attrs`.
- Source: `issue:646` (`issue`).
- Public title: `asdict` fails for attributes of type Mapping with keys of type `Tuple`
- Editable paths: `src/attr/__init__.pyi, src/attr/_funcs.py`.
- Non-editable tests: `tests/test_funcs.py, tests/typing_example.py`.
- Diff summary: 2 implementation file(s) and 2 test file(s) changed; 91 added line(s), 30 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_probably_truncated']`.

### attrs__hist__045

- Repo: `attrs`.
- Source: `pr:916` (`pull_request`).
- Public title: Added attrs.validators.min_len()
- Editable paths: `src/attr/validators.py, src/attr/validators.pyi`.
- Non-editable tests: `tests/test_validators.py`.
- Diff summary: 2 implementation file(s) and 1 test file(s) changed; 122 added line(s), 0 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'pr_context_source', 'pr_context_without_linked_issue', 'statement_probably_truncated']`.

### attrs__hist__047

- Repo: `attrs`.
- Source: `issue:924` (`issue`).
- Public title: Passing multiple Validators to the `member_validator` param of the `deep_iterable` validator
- Editable paths: `src/attr/validators.py, src/attr/validators.pyi`.
- Non-editable tests: `tests/test_validators.py`.
- Diff summary: 2 implementation file(s) and 1 test file(s) changed; 71 added line(s), 13 removed line(s).
- Old quality gate: `fail`; risks: `['body_summary_hit_old_240_char_cap', 'statement_probably_truncated']`.
