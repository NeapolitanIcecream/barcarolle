# Phase 1 Attrs Source Repair Candidate Packets

Packet count: 3.

What happened: sanitized packets were built for the three attrs source-review tasks.

## attrs__v2__218

Repo: attrs.
Implementation paths: src/attr/_make.py, src/attr/converters.py.
Test paths: tests/test_annotations.py.
Technical profile: py39_pytest_lt5_pythonpath / technical_certified.
Implementation diff digest: sha256:32cf78237a4a...
Test diff digest: sha256:2751359d117c...
Current blocker: technical certification passed, but source_context_quality=commit_message_only_context is not release eligible without public-context repair or reviewed statement repair.

## attrs__v2__231

Repo: attrs.
Implementation paths: src/attr/_make.py.
Test paths: tests/test_annotations.py, tests/test_dunders.py, tests/test_funcs.py.
Technical profile: py39_pytest_lt5_pythonpath / technical_certified.
Implementation diff digest: sha256:57d3a98888a4...
Test diff digest: sha256:1100fbd4ba6f...
Current blocker: technical certification passed, but source_context_quality=commit_message_only_context is not release eligible without public-context repair or reviewed statement repair.

## attrs__v2__237

Repo: attrs.
Implementation paths: src/attr/_make.py.
Test paths: tests/test_annotations.py.
Technical profile: py39_pytest_lt5_pythonpath / technical_certified.
Implementation diff digest: sha256:01ee59636d0f...
Test diff digest: sha256:824693d8169d...
Current blocker: technical certification passed, but source_context_quality=commit_message_only_context is not release eligible without public-context repair or reviewed statement repair.

Why it matters: the packets contain provenance, paths, certification status, and digests without committing raw target diffs or hidden oracle material.

Whether attrs now reaches 30 release-eligible tasks: not yet; packets only prepare the review path.
