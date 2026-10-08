# Minimal reproduction entry points

English | [中文](REPRODUCE.zh-CN.md)

CPU cores use Python 3.10 and locked project dependencies; CUDA cores have separate environments. Do not install the CPU lock into CUDA environments. [Paper cards](papers/README.md) and [semantic scope](SEMANTIC.md) specify settings, inputs and adapters.

```bash
uv sync --frozen --python 3.10 --extra methods --extra dev
uv run slam-study fetch
uv run slam-study run --method dufomap
uv run slam-study run --method beautymap
```

On Linux/WSL, `bash scripts/setup_linux.sh` prepares CPU native dependencies. Execute semantic methods sequentially:

```bash
bash scripts/setup_semantic.sh
.venv-semantic/bin/python scripts/run_conceptgraphs.py
bash scripts/setup_hovsg.sh
.venv-hovsg/bin/python scripts/run_hovsg.py
```

Each invocation creates a new run folder and prints record/log paths. LiDAR `--frames 10` is a smoke check without paper scores. Normal exit 0 means execution completed, not paper-table agreement; `--strict-paper` returns 2 on mismatch.

## Evaluation and integrity

```bash
uv run pytest -q
uv run ruff check src tests scripts
uv run python scripts/verify_evidence.py
uv run python scripts/verify_paired_evidence.py
uv run python scripts/check_docs.py
uv run slam-study verify results/runs/RUN_ID/record.json --full
```

Replace `RUN_ID` with the actual folder. Portable `results/reference` exports lack full maps and cannot replace native caches. CI checks code, lightweight evidence and documentation, not all CUDA paper experiments.

LiDAR map proximity is 5 cm. [Results](RESULTS.md) define SA/DA denominators and direct-label versus proximity differences. AA is geometric and HA harmonic; they are not a common ranking. BeautyMap inputs physically exclude GT intensity while retaining XYZ/VIEWPOINT. ConceptGraphs uses absolute `dataset.poses`; do not apply the first-frame transform again.

The 76 primary and 21 exploratory control cells have a separate [protocol](PAIRED_PROTOCOL.md), [evidence entry](../results/reference/paired-pose/record.json) and [rerun commands](PAIRED_RESULTS.md#reproduce-inspect-and-defend). Never overwrite v1 outputs.

Configs, source snapshots and run records pin data/weight checksums, author revisions and resource adaptations. [Sources and licenses](ATTRIBUTION.md) remain traceable. Detailed personal installation/recording/troubleshooting notes stay local. Public PDFs are record-bound generation snapshots; editing current research text does not silently rewrite them.
