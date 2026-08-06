# External benchmark inventory

This study tests whether pinned public benchmark sources add usable
repository-local rolling-Origin supply. It does not combine repositories into
one Task Pool, certify imported Tasks, open Agent outcomes, or develop a
Generator.

`inventory-plan.json` freezes the sources and four capacity protocols before
the row-level audit. `inventory.py` projects only repository, instance,
base-commit, Task-time, and language columns from exact remote Parquet
revisions. Raw Tasks, patches, repositories, and result files are not committed.
Each completed five-column projection is cached under ignored `outputs/` with
its source identity and digest, so a later remote failure resumes instead of
rescanning completed sources.

For the most robust replay, first download these exact files below an ignored
directory. `curl` supports retries and resumption:

```bash
mkdir -p outputs/research/2026-07-28-external-benchmark-inventory/sources

curl -fL --retry 5 --retry-all-errors -C - \
  -o outputs/research/2026-07-28-external-benchmark-inventory/sources/swe_bench_verified_reference.parquet \
  https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified/resolve/91aa3ed51b709be6457e12d00300a6a596d4c6a3/data/test-00000-of-00001.parquet

curl -fL --retry 5 --retry-all-errors -C - \
  -o outputs/research/2026-07-28-external-benchmark-inventory/sources/swe_bench_full_test.parquet \
  https://huggingface.co/datasets/SWE-bench/SWE-bench/resolve/7074ef12ea2a6f70a228943c1336553333c22786/data/test-00000-of-00001.parquet

curl -fL --retry 5 --retry-all-errors -C - \
  -o outputs/research/2026-07-28-external-benchmark-inventory/sources/swe_polybench_full.parquet \
  https://huggingface.co/datasets/AmazonScience/SWE-PolyBench/resolve/de2980959852c0d1bc532841f8e74cc5b30f24ed/default/test/0000.parquet

curl -fL --retry 5 --retry-all-errors -C - \
  -o outputs/research/2026-07-28-external-benchmark-inventory/sources/swe_rebench_v2.parquet \
  https://huggingface.co/datasets/nebius/SWE-rebench-V2/resolve/475dd5e8703bb5fb22dd3c60b5d038b019eba1e0/data/train-00000-of-00001.parquet
```

Then run:

```bash
PYTHONPATH=src:. uv run --isolated --python 3.11 --with duckdb \
  python examples/external_benchmark_inventory/inventory.py \
  --source-dir outputs/research/2026-07-28-external-benchmark-inventory/sources \
  --output /tmp/barcarolle-external-benchmark-inventory.json
```

Every local source is size- and SHA-256-verified against the frozen plan before
projection. The committed result still retains only sanitized aggregate
metadata. A later import must separately build and certify repository-local
prepared candidate packages.

SWE-bench Verified is scanned only as the existing reference. The executable
candidates are SWE-bench Full, SWE-PolyBench, and SWE-rebench V2. Multi-SWE-bench
and the sparse/live SWE-bench variants remain descriptor-only until their
official packaging and result evidence can support the same checks without
turning a headline total into synthetic capacity evidence.
