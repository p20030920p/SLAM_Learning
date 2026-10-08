# Author-method reproduction

This independent, orphan branch runs the official DUFOMap, BeautyMap, ConceptGraphs and HOV-SG repositories. Pinned Git submodules preserve author sources. Execution uses a separate Linux-native WSL workspace on this computer.

**Status: original LiDAR entries and author evaluation have run on the public 00 teaser. Semantic pipelines are in progress. Full-paper reproduction is not complete.**

[中文入口](README.zh-CN.md) · [Results and limitations](docs/STATUS.zh-CN.md) · [Windows/WSL commands](docs/RUNBOOK.zh-CN.md) · [Coverage and upstream comparison](docs/SCOPE.zh-CN.md) · [Execution evidence](evidence/README.md)

Upstream URLs and exact commits are in [the source manifest](config/upstreams.json) and [.gitmodules](.gitmodules). No algorithm-source changes are applied to these canonical repositories. Compiler/dependency compatibility changes, configuration copies and optional API-provider substitutions must be recorded separately. Existing main-branch wrapper results are not imported as new execution evidence.
