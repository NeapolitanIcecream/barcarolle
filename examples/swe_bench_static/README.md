# Static SWE-bench Adapter

This adapter imports one repository slice from an exact SWE-bench dataset
revision. It is a concrete classic-source adapter, not a Generator registry.
Its output is the ordinary prepared-candidate package consumed by Task Pool
certification.

The three explicit phases are:

1. `freeze_source.py` filters one repository, verifies the dataset bytes, and
   resolves each verifier image to an OCI manifest digest without pulling the
   image.
2. `prepare_package.py` writes the strict candidate/material package, observed
   frame, source protocol, hidden check material, and reference-patch
   path-overlap dependency evidence.
3. `certify_pool.py` verifies local repository and image bindings, requires a
   fresh base-fail/reference-pass pair for every candidate, and publishes the
   immutable Task Pool.

The committed SymPy source manifest is
`sources/sympy-verified-91aa3ed.json`. Large datasets, repositories, images,
raw checks, and published artifacts belong below ignored `outputs/`; the
manifest retains only the small source and image identities needed to replay
their selection.

Run `--help` on each script for its explicit inputs. The adapter deliberately
does not download a dataset, choose a repository, install a harness, clone a
target repository, or infer credentials. Those acquisition steps are campaign
authority, not stable adapter behavior.

Current claim boundary:

- certification proves the imported checks distinguish the frozen base and
  trusted reference patch under the pinned verifier;
- patch-path overlap supplies a conservative dependency component, not proof
  that disjoint patches are independent;
- a retrospective SWE-bench Task Pool does not establish prospective source
  coverage or historical Selector evidence.
