# Repository working agreement

- Keep `main` clean. Use an isolated worktree: branch → draft PR → commit-bound audit and CI → explicit owner approval → merge. Never push directly to main or enable auto-merge. Later changes require a new review.
- Preserve evidence, failures, annotation versions, hashes and scores. Version later re-scoring as post-hoc.
- Identity-budget v2 confirmation requires human review of raw views, identities, boundaries, queries, parts and exclusions before sealing or frontend execution.
- Owner amendment, 2026-10-08: manual review was waived for branch exploration. Use the separate AI-only protocol and explicit `--exploratory` flag. Never claim human review or confirmation. The original human gate and main approval rule remain.
- Support/candidate caps are offline readouts; never modify maps or equate candidate caps with matched memory/point budgets.
- H1 stays a candidate. Report negative findings; never choose scenes, labels, thresholds or seeds after inspecting mapper outputs.
- Preserve other windows' worktrees, environments, caches and jobs, including `reproduce/author-originals`, personal guides and local backups. Check resources before heavy work; defer while occupied.
- Keep English/Chinese claims consistent. Bind media to sources; distinguish full execution, actual 3D viewing and saved-map replay. Inspect every PDF page.
- Main acceptance requires code/design review, human labels, all cells/failures, recomputable metrics, tests/CI, bilingual consistency and media provenance. Pending items keep the PR a draft.

用户批准实验计划不等于批准合并；须明确批准已审核的具体提交。

## 中文

- 保持 main 干净：独立工作区／分支 → 草稿 PR → 绑定提交的审核与 CI → 用户明确批准 → 合并。禁止直推 main 或自动合并；后续修改重新审核。
- 保留证据、失败、标注版本、哈希和分数；后续重评分标记为事后分析。
- 确认性实验须先人工复核原视图、身份、边界、查询、部件与排除项，再封存及执行前端。
- 用户于 2026-10-08 仅豁免分支探索的人审：使用独立 AI-only 协议及 --exploratory，不声称人审或确认；确认性门槛与 main 审批仍有效。
- 支持门槛／候选上限只作离线读出，不改地图；相同候选上限不等于相同点数或内存。
- H1 保持候选；报告反证，不在看过结果后挑场景、标签、阈值或种子。
- 保留其他窗口的工作区、环境、缓存、任务、个人指南和本地备份；重任务前查资源，忙时推迟。
- 中英文结论一致；媒体绑定来源，区分完整执行、实际三维查看与保存地图回放；PDF 逐页检查。
- main 验收须有代码／设计审核、人审标注、全部单元／失败、可重算指标、测试／CI、双语检查与媒体来源；未齐全的 PR 保持草稿。

批准实验计划不等于批准合并，须明确批准审核过的具体提交。
