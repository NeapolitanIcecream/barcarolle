# Phase 1 Statement-Hardened Release Preview

Generated: `2026-05-25T02:04:56Z`.

These previews are solver-visible statement candidates only. They are not scoreable results.

## Summary

- Preview count: `4`.
- Scoreable result count: `0`.
- Statements cut mid-code or mid-sentence: `0`.

## Previews

### attrs__hist__008

- Repo: `attrs`.
- Source ref: `pr:669`.
- Problem summary: Add attr.field
- Short public excerpt: Almost forgot the last part of the NG API puzzle because it doesn't change substantially. Does this look OK so far?
- Editable implementation scope: `['src/attr/__init__.py', 'src/attr/__init__.pyi', 'src/attr/_next_gen.py']`.
- Known non-editable test paths: `['tests/test_next_gen.py', 'tests/typing_example.py']`.
- Statement digest: `f6da78f330e0f52d0249516a1aecf034431ec16bcd15e4845eebbd7fb782de91`.

### attrs__hist__039

- Repo: `attrs`.
- Source ref: `issue:875`.
- Problem summary: matches_re() should accept re.Pattern in addition to str
- Short public excerpt: `attr.validators.matches_re()` does not accept precompiled regular expressions, and instead requires a `str` pattern (and optional flags). this is not ideal when using existing compiled regular expressions, which already can have flags etc.
- Editable implementation scope: `['src/attr/validators.py', 'src/attr/validators.pyi']`.
- Known non-editable test paths: `['tests/test_validators.py', 'tests/typing_example.py']`.
- Statement digest: `a7a0430b3ca6f6bb0e3fbdb7b138ca2bc3410fc39a3c774051f9a26ad7f15e8d`.

### boltons__clean_ext__010

- Repo: `boltons`.
- Source ref: `issue:252`.
- Problem summary: setutils.IndexedSet has symmetric difference()
- Short public excerpt: ```python >>> set('abc') - set('bcd') {'a'} >>> IndexedSet('abc') - set('bcd') IndexedSet(['a']) >>> set('abc') - IndexedSet('bcd') IndexedSet(['d']) ``` I would expect this to be due to `__sub__ = __rsub__ = difference` in the source code.
- Editable implementation scope: `['boltons/setutils.py']`.
- Known non-editable test paths: `['tests/test_setutils.py']`.
- Statement digest: `28a57b0148475ff24d9cd4e45f88fe4203368327d3795515b160fd655efbc907`.

### boltons__clean_ext__017

- Repo: `boltons`.
- Source ref: `issue:319`.
- Problem summary: boltons.timeutils when start with 12 month and step=(1, 0, 0), result is wrong. because date.month start with 1, not 0
- Short public excerpt: start_day = date(year=2012, month=12, day=25) end_day = date(year=2023, month=1, day=1) for day in daterange(start_day, end_day, step=(1, 0, 0), inclusive=False): print(repr(day))
- Editable implementation scope: `['boltons/timeutils.py']`.
- Known non-editable test paths: `['tests/test_timeutils.py']`.
- Statement digest: `96d6f2037db2c23a03eb9d90d4d98a3b69a474df92f4c7160941a22dc4ee925a`.
