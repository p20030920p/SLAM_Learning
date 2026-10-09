# Minimal reproduction entry points

English | [中文](REPRODUCE.zh-CN.md)

CPU cores use Python 3.10 and locked project dependencies; CUDA cores have separate environments. Do not install the CPU lock into CUDA environments. [Paper cards](../papers/README.md) and [semantic scope](SEMANTIC.md) specify settings, inputs and adapters.

```bash
uv sync --project src --frozen --python 3.10 --extra methods --extra dev
uv run --project src slam-study fetch
uv run --project src slam-study run --method dufomap
uv run --project src slam-study run --method beautymap
```

On Linux/WSL, `bash src/scripts/setup/setup_linux.sh` prepares CPU native dependencies.

After setup, `bash src/launch/reproduce.sh --smoke` runs both LiDAR methods on ten frames; Windows has `powershell -File src/launch/reproduce.ps1 -Smoke`. The older `src/scripts/run_reproduction.sh` entry remains compatible. [Directory roles and launch scope](STRUCTURE.md).

Execute semantic methods sequentially:

```bash
bash src/scripts/setup/setup_semantic.sh
.venv-semantic/bin/python src/scripts/methods/run_conceptgraphs.py
bash src/scripts/setup/setup_hovsg.sh
.venv-hovsg/bin/python src/scripts/methods/run_hovsg.py
```

Each invocation creates a new run folder and prints record/log paths. LiDAR `--frames 10` is a smoke check without paper scores. Normal exit 0 means execution completed, not paper-table agreement; `--strict-paper` returns 2 on mismatch.

The project manifest and lock live in `src/`. Run uv from the repository root with `--project src`. CPU/method container:

```bash
docker build --file src/docker/Dockerfile --tag slam-learning .
docker run --rm slam-learning doctor
```

## Evaluation and integrity

```bash
uv run --project src pytest -q src/tests
uv run --project src ruff check --config src/pyproject.toml src/slam_learning src/scripts src/tests
uv run --project src python src/scripts/evidence/verify_evidence.py
uv run --project src python src/scripts/evidence/verify_paired_evidence.py
uv run --project src python src/scripts/evidence/verify_delayed_evidence.py
uv run --project src python src/scripts/evidence/verify_delayed_support.py
uv run --project src python src/scripts/evidence/check_docs.py
uv run --project src slam-study verify results/runs/RUN_ID/record.json --full
```

Replace `RUN_ID` with the actual folder. Portable `results/reference` exports lack full maps and cannot replace native caches. CI checks code, lightweight evidence and documentation, not all CUDA paper experiments.

LiDAR map proximity is 5 cm. [Results](../research/RESULTS.md) define SA/DA denominators and direct-label versus proximity differences. AA is geometric and HA harmonic; they are not a common ranking. BeautyMap inputs physically exclude GT intensity while retaining XYZ/VIEWPOINT. ConceptGraphs uses absolute `dataset.poses`; do not apply the first-frame transform again.

The 76 primary and 21 exploratory control cells have a separate [protocol](../research/PAIRED_PROTOCOL.md), [evidence entry](../../results/reference/paired-pose/record.json) and [rerun commands](../research/PAIRED_RESULTS.md#reproduce-inspect-and-defend). Never overwrite v1 outputs.

The new room1 study has 35 frozen delayed-correction cells and six separate post-hoc support controls. [Protocol and fresh-run sequence](../research/DELAYED_PROTOCOL.md#reproduction-status) · [Results and revised H1 decision](../research/DELAYED_RESULTS.md).

Configs, source snapshots and run records pin data/weight checksums, author revisions and resource adaptations. [Sources and licenses](ATTRIBUTION.md) remain traceable. Detailed personal installation/recording/troubleshooting notes stay local. Public PDFs are record-bound generation snapshots; editing current research text does not silently rewrite them.

## Maintenance

```text
src/slam_learning/   CLI → visualization → experiments → runtime → core
src/launch/             PowerShell/Bash reproduction entry points
src/scripts/            Preparation, analysis, viewer and export tools
src/configs/            Frozen inputs, annotations and separate environment snapshots
results/reference/  Immutable evidence and executed source snapshots
```

CPU checks only; no dataset download or GPU required:

```bash
uv sync --project src --frozen --python 3.10 --extra dev --extra audit
uv run --project src --no-sync deptry src/slam_learning --config src/pyproject.toml
uv run --project src --no-sync lint-imports --config src/pyproject.toml --no-cache
uv run --project src --no-sync vulture --config src/pyproject.toml
uv run --project src --no-sync pytest -q src/tests
```

[deptry](https://deptry.com/usage/) checks packaged dependencies. Pillow is direct; the five DEP002 exceptions cover BeautyMap's subprocess imports (`fire`, `dztimer`, `tqdm`) and optional Open3D/ipywidgets viewers. The methods extra explicitly pins Linux-only ipywidgets because Open3D 0.18 wheel metadata differs across platforms. The container checks the hashed dependency lock with `pip check`. [Import Linter](https://import-linter.readthedocs.io/en/stable/contract_types/) enforces acyclic imports, layer direction and separation from CUDA/ROS.

[Vulture](https://github.com/jendrikseipp/vulture) checks active source, scripts and tests at 100% confidence. Lower-confidence results require review: framework attributes and file-interface methods may be called externally. Frozen source snapshots and CUDA dependency lists are outside this cleanup scope.

[IWYU](https://github.com/include-what-you-use/include-what-you-use) applies to upstream C++ builds. Use matching Clang and a compilation database in a separate build, then run `iwyu_tool.py -p /path/to/build`. No IWYU result is claimed here; this checkout owns no C++ target.
