# Reproduction Setup

English | [中文](REPRODUCE.zh-CN.md)

Run from the repository root. CPU and CUDA environments are separate; prepare each method's data and weights before execution.

```bash
uv sync --project src --frozen --python 3.10 --extra methods --extra dev
uv run --project src slam-study fetch
uv run --project src slam-study run --method dufomap
uv run --project src slam-study run --method beautymap
```

```bash
bash src/scripts/setup/setup_semantic.sh
.venv-semantic/bin/python src/scripts/methods/run_conceptgraphs.py
```

HOV-SG is in progress; its environment and diagnostic entry remain available.

```bash
bash src/scripts/setup/setup_hovsg.sh
.venv-hovsg/bin/python src/scripts/methods/run_hovsg.py
```

## Checks

```bash
uv run --project src pytest -q src/tests
uv run --project src python src/scripts/evidence/verify_evidence.py
uv run --project src python src/scripts/evidence/check_docs.py
uv run --project src slam-study doctor
```

LiDAR `--frames 10` is a smoke check without paper scores. Every invocation creates a new run directory; successful execution is separate from paper agreement. Large maps remain local.

[Docs](../README.md) · [Results](../../results/REPORT.md) · [Structure](STRUCTURE.md)
