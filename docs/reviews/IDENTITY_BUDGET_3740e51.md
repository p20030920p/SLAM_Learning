# Identity-budget v2 implementation review

[中文](IDENTITY_BUDGET_3740e51.zh-CN.md)

Reviewed code revision: **3740e51a9a561e18ec53c9eb950d50bfb68ac044**. This is an implementation-stage review, not a release approval or a native experimental result. Subsequent code changes require a new review. Report/document additions are not self-certified by this earlier revision binding.

[Draft PR #5](https://github.com/p20030920p/SLAM_Learning/pull/5) remains separate from main. [CI at the reviewed revision](https://github.com/p20030920p/SLAM_Learning/actions/runs/37829481276) passed. Main was verified clean at 354b02d69ccc90304174f6d36010d25043d739ca. No merge is authorized.

| Review area | Finding | Status |
| --- | --- | --- |
| Code contracts | Complete states retain contributors/support/geometry/features; offline scans do not mutate state. Fixed controls preserve original members/support/semantic features. | CPU checks pass; native validation pending |
| Design | Fixed room2, 16 mapping frames, 4 held-out prefix references, 4 corrected arms, 28 cells, 12 readouts per stage. Primary stage8; stages12/16 persistence. | Declared before frontend |
| Labels | Five AI-drawn physical IDs across 20 polygons; raw review RGB hashes verified. Raw RGB/depth/overlays supplied. | AI-only; no human validation |
| Owner amendment | Owner declined further manual review and authorized branch-only continuation. Original confirmation gate preserved; separate explicit exploratory mode introduced. | Recorded; not permission to merge |
| Tests | 60 CPU tests passed locally; Ruff passed. Category queries accept any annotated same-class ID; unknown candidates are not automatic false positives. | Passed |
| Previous evidence | Existing 35-cell primary and 6-cell post-hoc evidence verification passed. Old labels, scores and recordings were not replaced. | Preserved |
| Execution | Pipeline002 retains clean revision/source hashes and waits for another window's jobs. Pipeline001 failed before models because Linux Git could not resolve a Windows worktree path; failure retained and compatibility repaired. | Native suite pending |
| Native parity | Own-policy zero correction, native/oracle zero equivalence, original-batch parity and per-cell fixed-member gates are enforced at runtime. | Not executed yet |
| Budgets | Candidate upper limits match; actual candidates/points/snapshot bytes/correction compute are reported separately. Snapshot bytes are not runtime memory. | Correct scope |
| Decision | ≥10pp mean advantage, ≥2/3 positive seeds, two finite caps at one RMS/support/endpoint, with no duplicate/mixing increase; simple-control ties narrow/stop H1. | Implemented, no result yet |
| Bilingual docs | Protocol, owner amendment, counts, decision and evidence limits agree in English/Chinese; repository link/media checks passed. | Passed |
| Media | Recorder and saved-state-to-RViz preparation are wired into the bounded pipeline. Browser security policy prevented local-file UI inspection; review form interaction is unverified. | Full experiment videos/GIF pending |
| Release | No human confirmation, no native results, no completed media audit, no merge approval. | Not ready for main |

The zero-error vase failure in room1 cannot establish historical association loss: the body-only polygon and a possible plant/vase assembly have different part definitions. Unrecovered fragments and a poor class query are not sufficient evidence of a wrong physical identity. No room1 label repair or re-score is silently substituted for the original results. The new room2 reference set avoids a plant/vase assembly and keeps physical-instance recovery separate from class-query retrieval. These choices precede room2 model outputs; they still require caution because labels are AI-only.

The native worker preserves the v1 default entry. V2 adds explicit protocol/annotation paths and a separately gated entry. Complete stage16 snapshots precede final filtering; the finalized snapshot remains separate for author-batch parity. Correction timing excludes snapshot storage I/O and includes full prefix regeneration. This cost can be much greater than a deployable online coordinate update, so a candidate-cap comparison cannot justify a bounded-memory claim.

The implementation audit found no remaining blocker to a guarded exploratory run. It does not establish native correctness: parity failures, contributor changes, accepted-mask differences, missing cells, changed raw sources or mismatched metric code stop execution/analysis. Resource waiting is bounded, and no process or environment in the other window is changed. A later audited result package must include all failures, all 28 cells, recomputation, full local recordings and per-page PDF inspection. H1 remains a candidate.
