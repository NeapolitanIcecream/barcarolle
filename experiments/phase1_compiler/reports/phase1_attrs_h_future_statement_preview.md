# Phase 1 Attrs H_future Statement Preview

Generated: `2026-05-25T01:34:18Z`.

These previews do not change previous paid outcomes and are not a rerun.
Any future paid validation using improved statements requires a new frozen release or preregistration.

## Summary

- Preview statements: `4`.
- Scoreable results represented here: `0`.
- Statements cut mid-code or mid-sentence: `0`.

## Previews

### attrs__hist__012

- Source ref: `issue:680`.
- Problem summary: Using slots class overrides custom `__setattr__` in 20.1.0
- Short public excerpt: A public report says a slotted attrs class with a custom __setattr__ worked in 19.3.0, but 20.1.0 replaced that custom behavior with the default slotted behavior.
- Editable implementation scope: `['src/attr/_make.py']`.
- Known non-editable test paths: `['tests/test_setattr.py']`.
- Verifier command metadata: `uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_setattr.py`.
- Statement quality flags: `{'body_summary_hit_old_cap': True, 'risk_reasons': ['body_summary_hit_old_240_char_cap', 'statement_ends_mid_code_fence', 'statement_probably_truncated'], 'statement_probably_truncated': True, 'statement_quality_gate': 'material_risk'}`.

Preview statement:

```text
Repair attrs behavior described by sanitized public context `issue:680`.
Problem summary: Using slots class overrides custom `__setattr__` in 20.1.0.
Problem details excerpt: A public report says a slotted attrs class with a custom __setattr__ worked in 19.3.0, but 20.1.0 replaced that custom behavior with the default slotted behavior.
Editable implementation scope: src/attr/_make.py.
Known non-editable test paths: tests/test_setattr.py.
Verifier command metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_setattr.py
Preserve existing public behavior and do not edit tests, generated metadata, or files outside the editable implementation scope.
```

### attrs__hist__013

- Source ref: `pr:687`.
- Problem summary: NG: make frozen classes comfortably subclassable
- Short public excerpt: A PR-context report says on_setattr=validate gets in the way for frozen define classes and for subclassing frozen classes in the next-gen API.
- Editable implementation scope: `['src/attr/_next_gen.py']`.
- Known non-editable test paths: `['tests/test_next_gen.py']`.
- Verifier command metadata: `uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_next_gen.py`.
- Statement quality flags: `{'body_summary_hit_old_cap': True, 'risk_reasons': ['body_summary_hit_old_240_char_cap', 'statement_probably_truncated', 'pr_context_source'], 'statement_probably_truncated': True, 'statement_quality_gate': 'material_risk'}`.

Preview statement:

```text
Repair attrs behavior described by sanitized public context `pr:687`.
Problem summary: NG: make frozen classes comfortably subclassable.
Problem details excerpt: A PR-context report says on_setattr=validate gets in the way for frozen define classes and for subclassing frozen classes in the next-gen API.
Editable implementation scope: src/attr/_next_gen.py.
Known non-editable test paths: tests/test_next_gen.py.
Verifier command metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_next_gen.py
Preserve existing public behavior and do not edit tests, generated metadata, or files outside the editable implementation scope.
```

### attrs__hist__023

- Source ref: `issue:593`.
- Problem summary: Deferred type annotations are evaluated in the wrong execution context
- Short public excerpt: A public issue reproduces get_type_hints(C.__init__) for an attrs class using a deferred List[int] annotation and expects annotations to resolve in the correct context.
- Editable implementation scope: `['src/attr/_make.py']`.
- Known non-editable test paths: `['tests/test_annotations.py']`.
- Verifier command metadata: `uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_annotations.py`.
- Statement quality flags: `{'body_summary_hit_old_cap': True, 'risk_reasons': ['body_summary_hit_old_240_char_cap', 'statement_ends_mid_code_fence', 'statement_probably_truncated'], 'statement_probably_truncated': True, 'statement_quality_gate': 'material_risk'}`.

Preview statement:

```text
Repair attrs behavior described by sanitized public context `issue:593`.
Problem summary: Deferred type annotations are evaluated in the wrong execution context.
Problem details excerpt: A public issue reproduces get_type_hints(C.__init__) for an attrs class using a deferred List[int] annotation and expects annotations to resolve in the correct context.
Editable implementation scope: src/attr/_make.py.
Known non-editable test paths: tests/test_annotations.py.
Verifier command metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_annotations.py
Preserve existing public behavior and do not edit tests, generated metadata, or files outside the editable implementation scope.
```

### attrs__hist__027

- Source ref: `issue:766`.
- Problem summary: Field hooks are too clunky with Python 3.10 / string annotations
- Short public excerpt: A public issue says Python 3.10 string annotations made field hooks clunky and needed a public helper path for resolving string annotations on attrs fields.
- Editable implementation scope: `['src/attr/__init__.pyi', 'src/attr/_funcs.py']`.
- Known non-editable test paths: `['tests/test_hooks.py']`.
- Verifier command metadata: `uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_hooks.py`.
- Statement quality flags: `{'body_summary_hit_old_cap': True, 'risk_reasons': ['body_summary_hit_old_240_char_cap', 'statement_probably_truncated', 'resolve_types_attribs_api_behavior_under_specified'], 'statement_probably_truncated': True, 'statement_quality_gate': 'material_risk'}`.

Preview statement:

```text
Repair attrs behavior described by sanitized public context `issue:766`.
Problem summary: Field hooks are too clunky with Python 3.10 / string annotations.
Problem details excerpt: A public issue says Python 3.10 string annotations made field hooks clunky and needed a public helper path for resolving string annotations on attrs fields.
Editable implementation scope: src/attr/__init__.pyi, src/attr/_funcs.py.
Known non-editable test paths: tests/test_hooks.py.
Verifier command metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_hooks.py
Preserve existing public behavior and do not edit tests, generated metadata, or files outside the editable implementation scope.
```
