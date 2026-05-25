# Phase 1 Statement-Hardened After Canonical Repair Release Preview

Generated: `2026-05-25T08:11:58Z`.

These generated statements are solver-visible task statements. They are not scoreable results.

- Preview count: `16`.
- Scoreable result count: `0`.

## attrs__hist__001

- Canonical repo/split: `attrs/B_eval`.
- Statement digest: `sha256:72f3749b248f32afa7ab0639cb5918df46243c0727ffb5aca0e544fffca0a294`.

```text
Problem summary: The public issue reports a regression where an attrs class using frozen=True together with cache_hash=True can no longer be deep-copied. The issue notes that the combination used to work before an earlier change, and that frozen support is implemented through setattr protections while cache_hash relies on an internal cached-hash attribute.

Behavior details: Frozen classes should still protect user-visible attributes from mutation, and cache_hash should still lazily cache the computed hash. However, copying and deep-copying need a way to reconstruct the object and its internal cached-hash state without tripping the frozen setattr guard. The implementation should distinguish attrs' internal cache field handling from user mutation, and it should keep existing behavior for frozen classes without cache_hash and cache_hash classes that are not frozen.

Expected behavior: copy.deepcopy on an instance of a frozen attrs class with cache_hash=True should complete successfully. The copied instance should compare and hash consistently with the original, and future hash calls should continue to use the cache behavior intended by attrs. The fix should not make frozen classes generally mutable, should not expose the cache attribute as a normal init field, and should not weaken error behavior for attempts to set user attributes after construction.

Editable implementation paths: src/attr/_make.py. Non-editable test paths: tests/test_make.py. Do not edit tests, changelog files, docs, or unrelated attrs modules. The sanitized diff summary reports one implementation file and one test file changed, with 11 added and 3 removed implementation lines plus 11 added test lines; changelog activity is out of editable scope for this task.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_make.py. Diff digests from the packet are target sha256:73856fbb41aae0edf89b85259f9e38a0e26f693c70b3b7c8c8b09caabc526964 and test sha256:4d8e27858a995d80477f94fd1966671b16272c9d358a1e95d069cef1dc2fbf84.
```

## attrs__hist__003

- Canonical repo/split: `attrs/B_eval`.
- Statement digest: `sha256:c8d04730b328ad028598eee282911e825fc6617f782ac07d74415a896f5a72f0`.

```text
Problem summary: The public PR context is sparse and titled added first doc stub. The sanitized packet shows the behavioral work belongs in attrs' class-generation machinery, specifically src/attr/_make.py, with tests in tests/test_make.py. Treat this as a user-facing introspection improvement for generated attrs methods rather than a documentation-file edit.

Behavior details: attrs generates methods such as initializers dynamically. Those generated callables should expose a stable, useful doc stub through normal Python introspection instead of leaving the relevant generated method undocumented or opaque. The doc stub should be attached as part of method generation in _make.py and should not change runtime call behavior, constructor signatures, attribute collection, validation, conversion, equality, hashing, or slots behavior.

Expected behavior: For ordinary attrs classes created through the supported class-building APIs, the generated method targeted by this change should have a non-empty documentation string suitable for help(), inspect, and other reflection tools. The content should be generic and stable enough for generated attrs code, not derived from hidden tests or environment-specific data. Existing classes without generated methods should not be affected, and any generated source/metadata support already present in attrs should continue to work.

Editable implementation paths: src/attr/_make.py. Non-editable test paths: tests/test_make.py. Do not edit tests, changelog files, docs, benchmark files, or unrelated modules. The sanitized diff summary reports one implementation file and one test file changed, with 7 added implementation lines and 32 added test lines. Use that only as evidence that this is a small generation/introspection change backed by broader tests; do not infer or reproduce a raw patch.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_make.py. Diff digests from the packet are target sha256:38f2b08c094a4b4b137c61e1e3a71a3633449b9fb831741eeac5db4d0f5d1031 and test sha256:72103a90a3d26fc3a51d59326919291cfc6969f94a756246f68371ff345c0e4d.
```

## attrs__hist__004

- Canonical repo/split: `attrs/B_eval`.
- Statement digest: `sha256:6dc808c7d1efafc2397a84ca7321830cb67540128a34f91d1de9eb6d80e312dd`.

```text
Problem summary: The public issue reports that __ne__ dunder behavior changes during the lifetime of an attrs-created class. The repro uses attr.make_class with eq=True and observes that the class-level __ne__ value is not stable. Equality dunder generation should be deterministic once the class has been created; ordinary comparison or introspection should not rewrite the class in surprising ways.

Behavior details: attrs needs to coordinate generated __eq__ and Python's __ne__ fallback semantics carefully. If attrs generates equality, the class should expose a stable not-equal behavior that remains consistent before and after instances are created or comparisons are performed. If attrs intentionally relies on Python to derive __ne__ from __eq__, it should do so without installing a mutable or transient class attribute that later changes. Existing options for eq=False, custom equality methods, ordering, hashing, and make_class should remain compatible.

Expected behavior: A class produced with attr.make_class(..., eq=True) should have the same observable __ne__ semantics throughout its lifetime. Repeated reads of the class dunder and ordinary equality/inequality operations should not cause the class attribute to flip to a different implementation. Inequality should remain the logical inverse of equality for generated equality where Python expects that behavior, and classes with explicit user-defined dunders should not be overwritten unexpectedly.

Editable implementation paths: src/attr/_make.py. Non-editable test paths: tests/test_make.py. Do not edit tests or unrelated attrs modules. The sanitized diff summary reports one implementation file and one test file changed, with 26 added and 12 removed implementation lines plus 11 added and 4 removed test lines; use this as scope guidance only.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_make.py. Diff digests from the packet are target sha256:b90cc8186a96314603707c8b2d5b4cd87d0d41a3868e9be08f3406cb0ffecb59 and test sha256:c21319db6b70b1ee0e35ba35c14683f138d21d7e1193ba3241eae8a57ebf99dc.
```

## attrs__hist__008

- Canonical repo/split: `attrs/B_eval`.
- Statement digest: `sha256:8c2d8b532d98e9be3c6b01e90eb16f8afd8bccddb322c0f2d45a9b43709ed652`.

```text
Problem summary: The public PR asks to add attr.field as the last part of the next-generation attrs API. The sanitized packet shows runtime export work in src/attr/__init__.py and src/attr/_next_gen.py, plus typing stub work in src/attr/__init__.pyi. The feature should make the field helper available from the attr namespace for users of attr.define and related next-generation APIs.

Behavior details: attr.field should be a public helper with behavior matching the intended next-generation field declaration API. It should delegate to the existing attrs field/attribute construction machinery rather than introducing a separate incompatible implementation. It must be importable at runtime, included consistently in the public namespace, and represented in the type stub with the supported parameters and return type expected by typed users. Existing aliases and older attr.ib behavior should continue to work.

Expected behavior: Users should be able to write next-generation attrs classes using attr.define together with attr.field, and the resulting attributes should behave like normal attrs attributes with respect to defaults, validators, converters, repr, comparison, factories, metadata, and type-checking examples. from attr import field should work where the public namespace supports it. This task is about adding the public API surface and keeping it wired to existing behavior, not about changing tests, docs, or unrelated class-generation semantics.

Editable implementation paths: src/attr/__init__.py, src/attr/__init__.pyi, src/attr/_next_gen.py. Non-editable test paths: tests/test_next_gen.py and tests/typing_example.py. The sanitized diff summary reports three implementation files and two test files changed, with implementation changes in runtime and stub files; documentation and changelog paths seen in the packet are outside the editable scope here.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_next_gen.py tests/typing_example.py. Diff digests from the packet are target sha256:088fce5a8fcfb10006c642fc78658d1f70b3156bcac67045f03ddbedd6a62d2c and test sha256:9d86ca081ee03fb54f285b2c92b4a3f9116e4b48847bea01fe325f7150f77e22.
```

## attrs__hist__012

- Canonical repo/split: `attrs/H_future`.
- Statement digest: `sha256:eb3b31fd4bf8241f9088b47b989b307545e1a2ceae9b5782feacc02453246f16`.

```text
Problem summary: The public issue reports a regression in attrs 20.1.0 where a slots=True class with a custom __setattr__ loses that custom method. In earlier behavior, users could define their own __setattr__ on slotted attrs classes. The current class-generation path replaces it with attrs' default setter behavior, breaking custom assignment logic after class creation.

Behavior details: slots class creation must preserve a user-defined __setattr__ unless attrs has a documented reason to generate a different one, such as frozen behavior or an explicit on_setattr configuration that requires interception. Initialization still needs to set attributes correctly, including with slots, validators, converters, and defaults. After initialization, normal assignment should route through the user's custom __setattr__ for classes that supplied one.

Expected behavior: For attr.s(slots=True) classes defining __setattr__, the resulting class should retain and invoke that method. attrs should not silently overwrite it with the default object setter or an attrs-generated setter just because slots are enabled. The fix should also respect combinations with on_setattr and frozen behavior: generated setters should still be installed when those features require them, while purely custom setter classes keep their method. Existing non-slots classes and slots classes without custom setters should retain current behavior.

Editable implementation paths: src/attr/_make.py. Non-editable test paths: tests/test_setattr.py. Do not edit tests, tox.ini, changelog files, or unrelated modules. The sanitized diff summary reports one implementation file and one test file changed, with 30 added and 25 removed implementation lines plus 88 added test lines; treat the touched auxiliary files in the packet as non-editable for this task.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_setattr.py. Diff digests from the packet are target sha256:cd43d5c83903d7009358f813376866d0360b99ed3d1bc1e47acd5635bc186273 and test sha256:55b2a3a454489b097d5f3df49fb7a031ec71613ec978277f28ac1426ab9d46d9.
```

## attrs__hist__013

- Canonical repo/split: `attrs/H_future`.
- Statement digest: `sha256:702f3a1c5f7a6936944aa15727ab4c1fd973f0ed71f73b54386ee94cd75b4da3`.

```text
Problem summary: The public PR asks to make next-generation frozen classes comfortably subclassable. The excerpt explains that on_setattr=validate gets in the way when users pass define(frozen=True) or subclass a frozen next-generation attrs class. Frozen classes already reject assignment; layering normal assignment hooks on top can create configuration conflicts and unnecessary subclass friction.

Behavior details: In the attr.define next-generation path, frozen=True should interact cleanly with the default on_setattr behavior. Frozen classes should not receive ordinary assignment-validation hooks that are meaningless or conflicting once mutation is prohibited. Subclassing a frozen attrs class should remain possible when the subclass configuration is otherwise valid, and attrs should choose generated setters/guards according to frozen semantics rather than the default mutable-class validation pipeline.

Expected behavior: Users should be able to create frozen classes with attr.define and subclass them without running into avoidable on_setattr validation conflicts. The resulting classes must still be frozen: attempts to mutate fields after initialization should fail as before. Validators should still run where attrs normally runs them during initialization, and mutable next-generation classes should keep their existing on_setattr behavior. The change should be limited to src/attr/_next_gen.py and should not rewrite the older attr.s class-generation path.

Editable implementation paths: src/attr/_next_gen.py. Non-editable test paths: tests/test_next_gen.py. Do not edit tests, changelog files, docs, or unrelated modules. The sanitized diff summary reports one implementation file and one test file changed, with 33 added and 7 removed implementation lines plus 65 added test lines; use it only as scope and risk guidance.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_next_gen.py. Diff digests from the packet are target sha256:702844a1d6efbf1ff1b9b864df9c30d8037b89f7bf617c4f55fa4ab98998da89 and test sha256:c353be521b715932623d3f8a41ffcc3b193487e93453cb14e7e5b9d7c192fc05.
```

## attrs__hist__023

- Canonical repo/split: `attrs/H_future`.
- Statement digest: `sha256:3262b00021acd8bd07b3adcbe9de4e3fc297a763750ce60acfc831f9912d5390`.

```text
Problem summary: The public issue reports that deferred type annotations are evaluated in the wrong execution context. The example defines an attrs class with attr.ib(type="List[int]") and then calls typing.get_type_hints on the generated __init__. The expected result is that the string annotation resolves using the module context where List was imported, rather than failing or resolving in attrs' internal generation context.

Behavior details: attrs generates __init__ functions dynamically, including annotations derived from attribute type metadata. When type metadata is a string or otherwise deferred, the generated function must carry enough globals/locals context for typing.get_type_hints to evaluate those annotations as if they belonged to the user's class/module. This should work for normal attrs classes and should not leak attrs internals into the user's annotation namespace.

Expected behavior: A generated initializer for a class whose field type is the string "List[int]" should allow get_type_hints to resolve that annotation to the imported typing.List form in the user's module context, with the return annotation still representing None. The fix should preserve existing behavior for real type objects, no type metadata, forward references, default values, converters, validators, and generated signatures. Avoid hard-coding the example; implement the context handling in the class-generation path.

Editable implementation paths: src/attr/_make.py. Non-editable test paths: tests/test_annotations.py. Do not edit tests or unrelated attrs modules. The sanitized diff summary reports one implementation file and one test file changed, with 41 added and 43 removed implementation lines plus 29 added test lines, indicating a focused rework of annotation generation/context handling.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_annotations.py. Diff digests from the packet are target sha256:ecc937588e4f6a3c180d9164492730b80b1686df699b51d1ffe4a866a84d309e and test sha256:600cdf06d4c8e7bd4116e6f7878bb4263ddf59ce33b007d8a7abc2a7d7c7ea72.
```

## attrs__hist__027

- Canonical repo/split: `attrs/H_future`.
- Statement digest: `sha256:f4bedc621b7cd8d458dcd08ff6134e823d21687ba30177122bde297e433486f6`.

```text
Problem summary: The public issue says field hooks are too clunky with Python 3.10 and string annotations. The excerpt explains that tests had to be excluded because there was no good helper to transform a string annotation such as "str" into the actual str object for field-transformer style hooks. The sanitized packet points to src/attr/_funcs.py and the public typing stub as the implementation surface.

Behavior details: attrs should provide or extend a helper so code working with attrs Attribute objects can resolve string annotations in the same execution context attrs uses for classes. This is especially important for field transformers and hooks that receive attribute metadata before all user code has manually normalized annotation strings. The helper should be usable from public attrs APIs and represented in the stub, while preserving existing behavior for already-resolved types and classes without string annotations.

Expected behavior: A hook or transformer should be able to ask attrs to resolve deferred/string types for a class or supplied attribute list and then see actual type objects where resolution is possible. The implementation should respect caller-provided global and local namespaces when supported, should not crash on annotations that cannot be resolved, and should not mutate unrelated class state beyond the documented type-resolution behavior. Python 3.10 string-annotation cases should work without excluding hook tests.

Editable implementation paths: src/attr/__init__.pyi and src/attr/_funcs.py. Non-editable test paths: tests/test_hooks.py. Do not edit conftest.py, changelog files, tests, docs, or unrelated modules. The sanitized diff summary reports two implementation files and one test file changed, with 8 added and 3 removed lines in _funcs.py and one stub line added.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q tests/test_hooks.py. Diff digests from the packet are target sha256:9e8b88a4f2c8791394ecd033ba78a6fa3c3ff534847f3223850220d1c6ce202c and test sha256:0630c189835572fb005fae6d8621f4ef59c4645c26dc86f78ba62b9c6ecd2cd5.
```

## boltons__clean_ext__001

- Canonical repo/split: `boltons/B_eval`.
- Statement digest: `sha256:2f0f8f1b0cef43b0c1bf8c3445c7501353e461194389d8ee64a7f367304f189c`.

```text
Problem summary: The public issue reports that boltons.iterutils.chunked and chunked_iter handle text strings correctly but raise TypeError when given bytes. Bytes are a sequence type, but iterating them yields integers, so code that rebuilds chunks from per-item iteration can accidentally try to construct bytes from the wrong element shape. The intended behavior is for byte strings to be chunked as byte strings, analogous to the existing string behavior, without changing behavior for lists, tuples, generators, or ordinary text.

Behavior details: chunked should accept a bytes input and return chunks whose elements are bytes slices, preserving order and the requested chunk size. chunked_iter should provide the same byte-preserving behavior lazily. Incomplete final chunks should continue to be handled the same way the functions already handle other supported input types. Existing semantics for str, tuple, list, iterator inputs, fill behavior, and invalid chunk sizes should remain intact.

Expected behavior: A bytes value such as b"abc123" split with size 3 should produce two bytes chunks rather than raising TypeError or returning lists of integers. The fix should be narrow: teach the iterutils chunking path that bytes should be treated like other sliceable atomic sequence types where appropriate, while leaving non-bytes iterables on the existing path.

Editable implementation paths: boltons/iterutils.py. Non-editable test paths: tests/test_iterutils.py. Do not edit tests, benchmark harness files, generated artifacts, or unrelated boltons modules. The sanitized diff summary for this packet reports one implementation file and one test file changed, with 3 added implementation lines and 7 added test lines; use that only as sizing and location guidance, not as a patch recipe.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" python -m pytest -q tests/test_iterutils.py. Diff digests from the packet are target sha256:f364e63ca059a04ae08ea249b8128f1df04c154ec6e5984d2416a261dfefe17f and test sha256:33b05d51ac806f4fd07d3e9a947c7c6b3874b36b0773c576bcdd92928d4fc46f.
```

## boltons__clean_ext__008

- Canonical repo/split: `boltons/B_eval`.
- Statement digest: `sha256:5c41a33c6e235518e1e984ebb9f4b1865b9b93c53797096f5b398ed14a53613c`.

```text
Problem summary: The public issue asks why IndexedSet does not update item indexes after removals. The reporter was using IndexedSet to pop items from a list-like collection and then encountered index-out-of-range failures because internal item-to-position bookkeeping did not match the current ordered contents after an element had been removed.

Behavior details: IndexedSet is both a set and an ordered/indexable container. Any operation that removes an element from the middle of the collection must keep the remaining elements in their original relative order and refresh the stored indexes for elements that shift left. This applies to the removal path used by methods such as discard, remove, pop, and any shared delete helper they call. Membership and uniqueness semantics should remain set-like; the change is about keeping the index mapping consistent with the sequence view.

Expected behavior: After deleting or popping an item, later items should still be retrievable by their new integer positions, index lookups should return positions that exist in the current collection, and subsequent pops should not fail because a stale index points beyond the end. Removing a missing item should keep the existing public error/no-op behavior for the method being used. The implementation should avoid rebuilding unrelated behavior or changing ordering guarantees.

Editable implementation paths: boltons/setutils.py. Non-editable test paths: tests/test_setutils.py. Do not edit tests, docs, benchmark files, or unrelated modules. The sanitized diff summary reports one implementation file and one test file changed, with 13 added and 1 removed implementation lines plus 15 added test lines; treat this as evidence of a focused bookkeeping fix, not as an exact patch recipe.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" python -m pytest -q tests/test_setutils.py. Diff digests from the packet are target sha256:efd0f923d05d30ca443b6630e5d98306df48ce1d9f51966c9a5af47296e4e0c4 and test sha256:e0c47087ccff2d7c2e3898ac6adf20cec82ef7aa282cfaa217d834830cb40853.
```

## boltons__clean_ext__010

- Canonical repo/split: `boltons/B_eval`.
- Statement digest: `sha256:1ffae607372921f374157f78e660822928ab076cf76906179213aee8cc9120c7`.

```text
Problem summary: The public issue reports that subtraction involving IndexedSet is incorrectly symmetric when IndexedSet is on the right-hand side. In normal Python set semantics, A - B means elements from the left operand that are not in the right operand. The issue example shows IndexedSet behaving correctly as the left operand, but set minus IndexedSet returning elements from the IndexedSet side because the reverse subtraction hook is wired to the same difference implementation.

Behavior details: IndexedSet subtraction should honor operand direction. IndexedSet(...) - other should keep the existing left-side IndexedSet behavior and preserve the ordered result expected from IndexedSet. other - IndexedSet(...) should compute the difference from the other operand, not from the IndexedSet, and should not report items that only exist on the right. This matters for built-in set operands and for other compatible set-like inputs.

Expected behavior: Reverse subtraction must be asymmetric in the same way built-in set subtraction is asymmetric. If a regular set containing a, b, c is subtracted by an IndexedSet containing b, c, d, the result should represent only a from the left operand, not d from the right. The fix should be localized to the relevant operator implementation or helper in setutils and should not disturb union, intersection, symmetric difference, membership, ordering, or normal difference behavior when IndexedSet is the left operand.

Editable implementation paths: boltons/setutils.py. Non-editable test paths: tests/test_setutils.py. Do not edit tests or unrelated boltons modules. The sanitized diff summary reports one implementation file and one test file changed, with 5 added and 1 removed implementation lines plus 7 added test lines, indicating a small operator-semantics correction rather than a broad rewrite.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" python -m pytest -q tests/test_setutils.py. Diff digests from the packet are target sha256:412d8538790114b6935f96fa9daa3e5d22f3b9978c5d3f9ee7eeaee91aae6dad and test sha256:13c75601da5d015fbc67fd2518e3cd1c17281f3b25deabec8cd9fd00b4416176.
```

## boltons__hist__011

- Canonical repo/split: `boltons/B_eval`.
- Statement digest: `sha256:6c415911ffde12152fd9ddc6911f88400fb276e133cd62d4518c89b48ed07877`.

```text
Task: add iterable strip helpers to boltons.iterutils.

Problem summary: The public request asks for lstrip, rstrip, and strip operations for iterables. The goal is to bring the familiar edge-trimming behavior of string strip methods to general finite iterables, while preserving the values and order of the untrimmed middle.

Behavior details: Implement a public API in boltons/iterutils.py for helpers named lstrip, rstrip, and strip. The helpers should accept an iterable input and a trim target using the conventions established by the surrounding iterutils module. lstrip removes matching values only from the left edge and then leaves the rest of the iterable unchanged. rstrip removes matching values only from the right edge and must keep matching values that occur earlier in the middle once a later nonmatching value has appeared. strip applies both edge operations. These functions should be usable with ordinary sequences and with one-shot iterators or generators; trailing trim semantics may require buffering, but callers should not have to pre-materialize inputs. Empty inputs, inputs where every value is trimmed, inputs where no value is trimmed, and falsey non-target values should all behave predictably.

Expected behavior: The new helpers should be importable from boltons.iterutils and should fit the module's existing iterator utility style. They should produce deterministic results for finite iterables, preserve all non-edge values exactly, and avoid changing unrelated iterutils behavior.

Editable implementation paths: boltons/iterutils.py. Non-editable test paths: tests/test_iterutils.py. Do not edit tests, docs, workflow files, packaging, or unrelated modules.

Verifier metadata: canonical split B_eval is benchmark metadata only. The verifier command metadata is `uv run --project experiments/phase0_headroom --with "pytest>=8,<9" --with "setuptools<81" python -m pytest -q tests/test_iterutils.py`. Sanitized diff summary: 1 implementation file and 1 test file changed; 126 added lines and 0 removed lines, with docs also touched outside the editable scope. Target diff digest: sha256:4e860fbd156044b81e18ee77fd6ada1a3b8fa22d574e9923f6abc2cc0bf771ba. Test diff digest: sha256:1aef866d9447ac9135714d698e40fc4007cbc7ad749c96b812cee61733e71c9a.
```

## boltons__clean_ext__017

- Canonical repo/split: `boltons/H_future`.
- Statement digest: `sha256:06e5da6b0d3af52a92b0d16be43b660f4b972bb3d7bbdd05445250d1b92f8d7a`.

```text
Problem summary: The public issue reports wrong results from boltons.timeutils.daterange when iterating from a December start date with a tuple step of (1, 0, 0). The reporter points out that calendar months are one-based, so date.month ranges from 1 through 12. Month or year arithmetic that normalizes using zero-based assumptions can go wrong at the December boundary.

Behavior details: daterange must produce a monotonic sequence of dates between the requested start and end while honoring the tuple step and the inclusive flag. When the starting month is December, advancing by a tuple step that crosses year boundaries should keep the intended day and month relationship instead of drifting, wrapping incorrectly, or yielding an invalid month. The correction should be made in the date arithmetic/normalization path used by daterange, without changing unrelated time utilities.

Expected behavior: Starting at 2012-12-25 and iterating toward 2023-01-01 with the reported step should produce the expected calendar progression across years and stop according to inclusive=False. December should be treated as month 12 during normalization; any conversion to zero-based arithmetic should be explicit and converted back before constructing dates. Existing behavior for non-December starts, day-based steps, inclusive=True, and ordinary stop conditions should continue to work.

Editable implementation paths: boltons/timeutils.py. Non-editable test paths: tests/test_timeutils.py. Do not edit tests or unrelated modules. The sanitized diff summary reports one implementation file and one test file changed, with 6 added and 4 removed implementation lines plus 14 added test lines; use this only as scope evidence for a focused daterange fix.

Verifier metadata: uv run --project experiments/phase0_headroom --with "pytest>=7,<8" python -m pytest -q tests/test_timeutils.py. Diff digests from the packet are target sha256:654a2d887c174ab6b370417badc46dc89804ab09b5b8ef17ad77d4ddd17f0680 and test sha256:1bc73f35f6127e87ce27b15a262ee089ec6deece6c06d879a1eb12c2caeed28f.
```

## boltons__hist__022

- Canonical repo/split: `boltons/H_future`.
- Statement digest: `sha256:df7b0201c0ef0ec9f236f2c53bb50a475d2cf0bbf688f6e9ef2a87fd231500c3`.

```text
Task: add chunk_ranges to boltons.iterutils.

Problem summary: The public request asks for a chunk_ranges helper in iterutils. Unlike helpers that directly chunk an iterable or sequence, this helper should calculate the integer index ranges a caller can use to slice existing data into chunks. The request specifically calls out windowing and overlap support.

Behavior details: Implement chunk_ranges in boltons/iterutils.py. Given an input length and a chunk size, it should produce ordered start and stop indexes suitable for slicing, such as ranges that a caller can apply as data[start:stop]. Ranges should stay within the bounds of the input length, should not produce spurious empty chunks for normal nonempty inputs, and should handle zero-length input, exact multiples, final partial chunks, and inputs smaller than a single chunk. Overlap or windowing options should allow adjacent ranges to share elements while still making forward progress. Invalid arguments that would make range generation meaningless or non-terminating, such as nonpositive chunk sizes or overlap settings that prevent progress, should be rejected consistently with the style of nearby iterutils helpers.

Expected behavior: The helper returns or yields simple integer range pairs rather than slicing the data itself. Non-overlapping use should cover the input in chunk-sized steps with a final shorter range when needed. Overlapping use should advance by a stable step, keep every emitted range bounded, and stop cleanly at the end. The change should not alter existing chunking utilities except as needed to expose the new helper.

Editable implementation paths: boltons/iterutils.py. Non-editable test paths: tests/test_iterutils.py. Do not edit tests, docs, workflow files, packaging, or unrelated modules.

Verifier metadata: canonical split H_future is benchmark metadata only. The verifier command metadata is `uv run --project experiments/phase0_headroom --with "pytest>=8,<9" --with "setuptools<81" python -m pytest -q tests/test_iterutils.py`. Sanitized diff summary: 1 implementation file and 1 test file changed; 75 added lines and 3 removed lines, with docs also touched outside the editable scope. Target diff digest: sha256:7f40ada197955158306f1e5d0705dd1ec267bc621af17aa93a9f950fd6a47b92. Test diff digest: sha256:6033cb2c508202e37f191866c9dd03ea2006416b412b0dce097e8a9055c3eb8c.
```

## boltons__hist__023

- Canonical repo/split: `boltons/H_future`.
- Statement digest: `sha256:a70aa84eb91022b28b2b418aa3fd34671a3ada779bc0e4c633e42faf7a055a7a`.

```text
Task: make tbutils parse tracebacks that include anchor lines.

Problem summary: The public request describes traceback output where an extra anchor or marker line appears below the source-code line. Modern Python tracebacks can include caret or tilde style markers to point at the exact expression that raised an error. boltons.tbutils should continue parsing traceback frames correctly when those marker lines are present.

Behavior details: Update boltons/tbutils.py so the parsed-exception logic recognizes anchor lines as part of the displayed source context rather than as a new frame, exception message, or parse failure. The parser should still extract the filename, line number, function name, source line, exception type, and exception message from ordinary traceback text. When an anchor line follows a source line, parsing should skip or tolerate that extra line and then continue with the next traceback frame or final exception line. This should work for single-frame and multi-frame tracebacks and should not regress tracebacks that do not contain anchor markers. The change should be narrow and compatible with the existing ParsedException behavior.

Expected behavior: Tracebacks with anchor lines should produce the same logical parsed exception information as comparable tracebacks without those anchors, apart from the additional display-only marker being ignored. Anchor lines should not corrupt the stored source line, should not be appended to the exception message, and should not cause later frames to be missed.

Editable implementation paths: boltons/tbutils.py. Non-editable test paths: tests/test_tbutils_parsed_exc.py. Do not edit tests, docs, workflow files, packaging, or unrelated modules.

Verifier metadata: canonical split H_future is benchmark metadata only. The verifier command metadata is `uv run --project experiments/phase0_headroom --with "pytest>=8,<9" --with "setuptools<81" python -m pytest -q tests/test_tbutils_parsed_exc.py`. Sanitized diff summary: 1 implementation file and 1 test file changed; 34 added lines and 1 removed line. Target diff digest: sha256:ab855ebb21b34ac91683dabac03dc1ba3b3f424ca39864566fcbd01ce360651f. Test diff digest: sha256:0e18b510dd1bfb85f144052fae6ee5676e87438b02faf6bb620adf3845c0ddf4.
```

## boltons__hist__027

- Canonical repo/split: `boltons/H_future`.
- Statement digest: `sha256:aa6f2e0c3059224df7a4fdfec91446117128820f639b9a65793186756cea575a`.

```text
Task: make cacheutils mapping views return user-facing cache contents.

Problem summary: The public request says a test reproduced issue #348 and also checked .values(). cacheutils cache classes are dict subtypes, so callers reasonably expect standard mapping operations such as .items() and .values() to expose the cached keys and values, not implementation internals.

Behavior details: Update boltons/cacheutils.py so the relevant cache mapping classes present normal dict-like items and values views or iterables. Calling .items() should produce key/value pairs where the value is the same user value returned by normal lookup. Calling .values() should produce the cached user values. These operations should reflect the current cache contents after insertion, lookup, update, and eviction, and they should not expose internal linked-list nodes, wrappers, sentinels, or other bookkeeping structures. Keep the existing cache eviction and recency semantics intact. Apply the fix to the cache classes affected by the dict-subclass behavior in this module, including the least-recently-inserted and least-recently-used style caches when applicable.

Expected behavior: list(cache.items()) and list(cache.values()) should be useful in the same way they are for ordinary dictionaries, while remaining consistent with the cache's key iteration, length, containment, and __getitem__ behavior. The fix should be narrow: do not redesign cache storage, change public constructor APIs, or alter unrelated cache helpers.

Editable implementation paths: boltons/cacheutils.py. Non-editable test paths: tests/test_cacheutils.py. Do not edit tests, docs, workflow files, packaging, or .github/workflows/tests.yaml even though the sanitized source change touched workflow metadata.

Verifier metadata: canonical split H_future is benchmark metadata only. The verifier command metadata is `uv run --project experiments/phase0_headroom --with "pytest>=8,<9" --with "setuptools<81" python -m pytest -q tests/test_cacheutils.py`. Sanitized diff summary: 1 implementation file and 1 test file changed; 44 added lines and 2 removed lines, with workflow metadata also touched outside the editable scope. Target diff digest: sha256:599a0a96c332b9939ce6beb9fc7de909a20b09d27b8ef4392115310e7846db25. Test diff digest: sha256:d3dd14eff6b14b9a26790338fcf62b3e9b409c343224496992e617f6a5f503bb.
```
