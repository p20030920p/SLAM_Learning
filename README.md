# Author Reproduction

English | [中文](docs/HOME.zh-CN.md)

Official mapping code, pinned sources and recorded experiments.

## Results

| Method | Reproduction | Paper comparison |
| --- | --- | --- |
| DUFOMap | KITTI 00 | [Table IV: 15/15 accuracy values match](docs/reports/DUFOMAP_TABLE4.md) |
| BeautyMap | KITTI 02 | [Table III: 9/9 accuracy values match](docs/reports/KITTI_PAPER_PROTOCOL.md) |
| ConceptGraphs | 3 SAM-only / 2 Detect scenes | [Partial coverage](docs/reports/CONCEPTGRAPHS_SCENE_RESULTS.md) |
| HOV-SG | In progress | |

Matches refer to each paper's two-decimal accuracy values. ConceptGraphs coverage differs from its paper benchmark. [Protocols and limits](docs/reports/SCOPE.md).

## Usage

```bash
git submodule update --init --recursive
python3 src/scripts/prepare_runtime.py --runtime /path/to/new/runtime --cache src/upstream
```

Use Linux / WSL for execution. [Environment](docs/guides/ENVIRONMENT.md) · [Runbook](docs/guides/RUNBOOK.md) · [Data](docs/guides/DATA_ACCESS.md).

## Structure

```text
docs/      # guides and reports
results/   # logs, hashes and media
src/       # configs, scripts and upstream submodules
```

[Source pins](src/configs/upstreams.json) · [Evidence](results/README.md) · [Delivery](https://github.com/p20030920p/SLAM_Learning/tree/main) · [Personal study](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008)
