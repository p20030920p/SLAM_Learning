# Identity and candidate-budget study v2

[中文](IDENTITY_BUDGET.zh-CN.md)

**In progress · AI-only exploratory labels · H1 unverified.**

## 1. Question

After exact historical pose correction, does reassociation recover more valid targets than fixed associations at the same candidate cap? This separates association loss from coordinate error and low-support filtering. One scene cannot establish a common bottleneck across methods; equal caps do not match actual candidate counts, points or memory.

References cover partial visible surfaces, not official Replica instance GT. Physical-instance recovery and category-query hits are scored separately; a query may hit any annotated same-class instance. Unlabelled candidates are unknown, not automatic false positives. Duplicate excess counts qualifying fragments after the first per physical ID; a mixed object supports two annotated IDs. Both depend on label boundaries and visibility.

## 2. Frozen design

| Item | Setting |
| --- | --- |
| Scene and frames | room2; mapping 0, 25, …, 375; held-out references 12, 62, 112, 162 |
| Targets | [5 AI instances](../annotations/room2/targets.ai-v2.1.json); fixed before frontend outputs |
| Correction | Exact prefix poses after observation 8 (primary); observations 12/16 assess persistence |
| Conditions | World-x RMS 10/30 cm × seeds 417/518/619, plus zero per arm: 28 cells |
| Arms | native_fixed; threshold_fixed (1.0); visibility_fixed; oracle_replay |
| Offline readouts | Support ≥1/2/3 × caps 25/50/100/unlimited: 1008 rows across three stages |
| Candidate order | Label-free: support descending, points descending, contributor-derived ID ascending |

All arms share one frozen frontend. Fixed arms rebuild geometry from their own association traces, preserving members, supports and CLIP/text features; oracle reruns native association. Complete snapshots retain provenance, geometry, colors and features before readout filtering. Observation16 is also saved before final filtering; finalized output is separate. Readouts cannot modify maps. Zero-error own-policy, native/oracle and original-batch parity must pass. Correction time includes prefix reconstruction but excludes snapshot I/O; snapshot bytes are not runtime memory. These controls do not demonstrate a deployable low-memory correction method.

## 3. Run and record

The [exploratory protocol](../configs/identity_budget_v2_exploratory.json) follows the owner's 2026-10-08 waiver of manual review. Labels remain `human_reviewed: false`. The [confirmation protocol](../configs/identity_budget_v2.json) still requires a human receipt; the [raw-view review package](../annotations/review/identity-v2/index.html) and room1 evidence remain unchanged. Later re-scoring must be versioned as post-hoc.

Use the pinned Linux environment and separate absolute output paths. Prepare the fixed subset with `fetch_delayed_scene.py`; seal with `seal_delayed_annotations.py --seal --exploratory` before frontend execution. For prepared data and a seal:

```bash
python scripts/check_study_resources.py
python scripts/run_identity_pipeline.py \
  --repo "$REPO" --semantic-python "$SEMANTIC_PYTHON" \
  --protocol "$REPO/configs/identity_budget_v2_exploratory.json" \
  --annotations "$REPO/annotations/room2/targets.ai-v2.1.json" \
  --data "$DATA" --freeze "$SEAL/freeze.json" \
  --native-source "$SOURCE" --weights "$WEIGHTS" \
  --output "$OUT" --recordings "$VIDEOS" --wait-idle-seconds 10800
```

Resource-check exit 2 means defer. The pipeline waits up to three hours per phase without changing other jobs or environments. It copies the source and runs frontend → 28 cells → recalculation → bilingual plots/report → actual RViz saved-map replay. Failures need new directories; preserve old attempts. Full terminal videos, transcripts, commands and exit records stay local. RViz replay is labelled as replay. GIFs need source hashes; scientific result PDFs need page-by-page inspection. Neither is complete yet. [Recording scope](RECORDING.md).

## 4. Decision

At the same RMS, support and endpoint (recovery or category-query hit), oracle must beat every simple control by ≥10 mean percentage points at two finite caps, with ≥2/3 positive paired seeds and no seed increasing annotated duplicates or mixed objects. Passing permits only a bounded-replay prototype plan; ties mean narrow or stop H1. AI-only labels cannot confirm H1.

Work remains on `study/identity-budget-v2`. [Review rules](../AGENTS.md) require a commit-bound audit, CI and explicit owner approval before merging main. The [initial implementation audit](reviews/IDENTITY_BUDGET_3740e51.md) is historical, not a result report.
