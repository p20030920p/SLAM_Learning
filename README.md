# Author-method reproduction

This independent, orphan branch runs the official DUFOMap, BeautyMap, ConceptGraphs and HOV-SG repositories. Pinned Git submodules preserve author sources. Execution uses a separate Linux-native WSL workspace on this computer.

**Status: both original LiDAR entries and author evaluation completed all four public labeled releases (1,997 scans per method). Semantic pipelines are in progress. Full-paper reproduction is not complete.**

The new [DUFOMap Table IV reproduction](docs/DUFOMAP_TABLE4.zh-CN.md) matches all five SA/DA/AA rows at the paper's two-decimal precision.

The missing original KITTI inputs (333 selected frames) are downloaded and verified. Both methods and three BeautyMap XY cell sizes have completed original scoring on 01/02. [Results and paper differences](docs/KITTI_SELECTED_RESULTS.zh-CN.md) remain separate because the current preprocessing differs from the older released benchmark.

ConceptGraphs room0 now has a validated complete frontend, original 3D map and RGB reference surface. Semantic evaluation is queued after repairing its CUDA dependency. A [60-second original viewer recording](evidence/videos/conceptgraphs-room0-original-window.mp4) shows RGB/instance colors and orbit controls.

[中文入口](README.zh-CN.md) · [Results and limitations](docs/STATUS.zh-CN.md) · [Windows/WSL commands](docs/RUNBOOK.zh-CN.md) · [Data downloads and ScanNet access](docs/DATA_ACCESS.zh-CN.md) · [Coverage and upstream comparison](docs/SCOPE.zh-CN.md) · [Execution evidence](evidence/README.md)

Upstream URLs and exact commits are in [the source manifest](config/upstreams.json) and [.gitmodules](.gitmodules). Canonical author checkouts remain unchanged. Explicit compatibility variants are separate copies with diffs, including a SAM microbatch adjustment for this 12GB GPU. Compiler/dependency changes and optional API-provider substitutions are also recorded separately. Existing main-branch wrapper results are not imported as new execution evidence.
