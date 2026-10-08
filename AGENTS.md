# Repository working agreement

This repository is a laboratory application with auditable research evidence.

- Keep `main` clean. Work in an isolated worktree and a topic branch. Never commit or push directly to `main`, enable auto-merge, or merge without the human owner's explicit approval of the reviewed revision.
- Use branch → pull request → commit-bound review report and passing CI → explicit human approval → merge. Any change after review invalidates that review; audit the new revision again.
- Preserve previous evidence, failed attempts, annotation versions, source hashes and scores. Label later re-scoring as post-hoc analysis.
- For identity-budget v2, do not seal annotations or start the room2 frontend until the owner has reviewed the raw RGB-D views, identities, boundaries, queries, parts and exclusions. AI-generated labels are drafts, never human review.
- Candidate caps and support thresholds are offline readouts. They must not change the underlying map. Do not describe equal candidate caps as matched memory or point budgets.
- H1 remains a candidate hypothesis. Report negative controls and negative findings. Do not choose scenes, targets, thresholds or seeds after inspecting mapper results.
- Do not modify another window's worktree, environment, cache or running jobs. In particular preserve `reproduce/author-originals`, the personal guide and the local-only backup. Check resources before heavy work; defer GPU work while occupied.
- Keep English and Chinese documentation consistent. Bind published media to actual source records. Distinguish full execution recording, real 3D viewing and saved-map replay; inspect every PDF page.
- A ready-to-merge audit must cover code, design, human labels, all cells and failures, recalculable metrics, tests/CI, bilingual claims and media provenance. Pending items mean the PR stays a draft.

用户批准本计划不等于批准合并。只有用户明确批准已审核的具体提交，才能合并至主分支。
