# Personal study, operation and analysis index

English | [中文](README.zh-CN.md)

Use `notes/personal-study-guide-20261008` to walk through the workflow, compare author code and develop your own research argument. The reviewer entry remains [main](https://github.com/p20030920p/SLAM_Learning/tree/main). These guides are kept off main. A published branch is still publicly accessible; full recordings and raw device data remain local.

## Reading order

| Order | Guide | Purpose |
| --- | --- | --- |
| 1 | [Lab requirements and analysis outline](LAB_ANALYSIS.md) | Connect topics 1–2, evidence, an open question and a falsifiable hypothesis |
| 2 | [Start from Windows](WINDOWS_START.md) | Which application, directory, shell and command to use; where outputs go |
| 3 | [Author repositories versus this repository](UPSTREAM_COMPARISON.md) | Original repositories, pinned versions, entry points, adaptations and missing scope |
| 4 | [Manual reproduction and recording](MANUAL_RECORDING.md) | Run the native cores, inspect saved outputs in RViz, record the graphical side |
| 5 | [Home device runbook](HOME_RUNBOOK.md) | Connect D435i/L2, capture four events, check playback and identify pending adapters |

Start with the evidence boundaries, run DUFOMap once, then inspect RViz. Run methods serially, especially the SAM/CLIP workloads on the 12 GiB GPU.

## Research navigation

| Need | Entry |
| --- | --- |
| Understand each selected paper | [Four paper cards](../docs/papers/README.md) |
| Check related work, safeguards and counterexamples | [Literature](../docs/LITERATURE.md); additional papers were read, not all reproduced |
| Connect reproduction to H1 | [Independent analysis](../docs/STUDY.md) |
| Interpret the new complete author workflows | [Four public releases and hypothesis limits](AUTHOR_RESULTS_ANALYSIS.md); keep new runs distinct from older subsets |
| Compare paper and measured results | [LiDAR results](../docs/RESULTS.md), [semantic scope](../docs/SEMANTIC.md) |
| Understand the perturbation construction | [Paired protocol](../docs/PAIRED_PROTOCOL.md) |
| Inspect 76 main cells, 21 exploratory controls and simple baselines | [Paired results](../docs/PAIRED_RESULTS.md), [analysis record](../results/reference/paired-pose/record.json) |
| Trace numbers to logs and configurations | [Audit](../docs/AUDIT.md), [portable records](../results/reference); full native maps are in WSL `results/runs/` |
| Understand what the videos show | [Recording scope](../docs/RECORDING.md), [manual recording](MANUAL_RECORDING.md) |
| Extend with home hardware | [Public protocol](../docs/REAL_WORLD.md) plus [device steps](HOME_RUNBOOK.md) |
| Check attribution and AI use | [Attribution](../docs/ATTRIBUTION.md), [disclosure](../docs/DISCLOSURE.md) |

## Machine paths

| Path | Role |
| --- | --- |
| `D:\workspace\be2\SLAM_Learning` | Windows main checkout |
| `D:\workspace\be2\SLAM_Personal_Guide` | This documentation worktree |
| `D:\workspace\be2\SLAM_Author_Originals` | Independent author-originals branch with pinned sources and execution evidence |
| `/home/qzl/projects/SLAM_Author_Originals` | Separate original-workflow environments, full public data and large outputs |
| `/home/qzl/projects/SLAM_Learning` | WSL runtime checkout with environments, data and author caches |
| `D:\workspace\be2\SLAM_Recordings\2026-10-08` | Full terminal recordings; `rviz-review-v3/` contains graphical originals |
| `D:\workspace\be2\SLAM_Home` | New local hardware captures |
| `D:\workspace\be2\SLAM_Private\2026-10-08\original-docs` | Historical manuals; prefer the current guides |

`local/full-notes-20261008` preserves older local notes. This new guide branch starts from main `6deb08a` and changes documentation only. Machine availability statements were checked on 2026-10-08.

Before submission, explain one counterexample, one metric denominator, one real command/output pair and one outcome that would reject H1. Fill the personal analysis section in the [lab outline](LAB_ANALYSIS.md) before deciding what research text belongs on main.
