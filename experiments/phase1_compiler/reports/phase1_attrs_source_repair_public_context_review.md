# Phase 1 Attrs Source Repair Public Context Review

Accepted public context count: 3.

What happened: each target task received a public-context verdict.

## attrs__v2__218

Verdict: accepted_public_context.
Public refs: issue:694, pr:710.
Summary: Public issue #694 reports that attrs-generated __init__ parameters lose useful typing information when a field uses a converter. Public PR #710 and the merge commit discuss inferring annotations from converter functions, including converter composition helpers such as pipe() and optional().
Leakage flags: []. Ambiguity flags: [].
Why sufficient: The public issue states the user-visible behavior and the PR discussion narrows the affected converter annotation scope.

## attrs__v2__231

Verdict: accepted_public_context.
Public refs: issue:716, pr:763.
Summary: Public issue #716 reports Python 3.10 compatibility problems caused by annotations being stored as strings. Public PR #763 records Python 3.10 support work around string annotations, ClassVar handling, and generated method annotations.
Leakage flags: []. Ambiguity flags: [].
Why sufficient: The public issue and PR body describe the Python 3.10 annotation failure mode and the affected typing scope.

## attrs__v2__237

Verdict: accepted_public_context.
Public refs: issue:781, pr:782.
Summary: Public issue #781 reports that typing_extensions.ClassVar can be treated as a normal attrs attribute under Python 3.10 annotation behavior, producing an ordering error. Public PR #782 records the corresponding ClassVar detection repair.
Leakage flags: []. Ambiguity flags: [].
Why sufficient: The public issue gives a clear user-visible failure and the public PR directly links the repair to typing_extensions.ClassVar detection.

Why it matters: at least two accepted public-context repairs are enough for attrs to reach 30 release-eligible tasks after overlay.

Whether attrs now reaches 30 release-eligible tasks: expected yes after Step 5 because all three attrs tasks have accepted public context.
