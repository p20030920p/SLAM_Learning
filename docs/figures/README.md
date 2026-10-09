# Figures, GIFs and videos

English | [中文](README.zh-CN.md)

This is the single media index. Selected homepage positions carry captions and commented image lines; all reserved assets are indexed here, and no missing image is rendered. `slots.json` distinguishes existing exploratory/diagnostic figures from future author comparisons and confirmatory results.

## Published figures

| Asset | Stage | Caption |
| --- | --- | --- |
| [replication-hero](replication_hero.gif) | R0/R2 | DUFOMap, BeautyMap and GT on the same selected teaser entries; fixed view, raw / removed / retained. Offline final maps, not online updates. |
| [replication-frame](replication_frame.png) | R0/R2 | One named frame, same world bounds and point identities across every method and GT. |
| [metric-correspondence](metric_correspondence.png) | R1 | Same-instance DUFOMap: direct identities, nearest neighbors of the same kept points and native export; 141 frames, zero injected error. |
| [pose-margin](../../results/reference/pose-stress/sensitivity.png) | R0 diagnostic | Real teaser, six direct-label sensitivity cells; no paper-table or semantic-navigation comparison. |
| [mechanism-ambiguity](../../results/reference/mechanism/mechanism.png) | exploratory E1 | Oracle identity/visibility, minority versus majority movers; include the median failure. |
| [evidence-calibration](../../results/reference/evidence-stress/calibration.png) | exploratory E0 | Gaussian shared bias with known scales; false deletion, Brier and changed-object recall together. |

## Reserved slots

| File | Stage | What must be shown |
| --- | --- | --- |
| `docs/figures/paper_gap.png` | R1 | Measured versus paper values, with AA and HA separated and evaluator differences annotated. |
| `docs/figures/bottleneck_diagram.svg` | B0 | Pose, correspondence, evidence and provisional updates; empirical observations separated from conjectured feedback. |
| `docs/figures/pose_drift.gif` | E0 | Exact, independent-noise and correlated-drift conditions at matched marginal error; fixed frontend and view. |
| `docs/figures/semantic_update.mp4` | R3 then E2 | First an author semantic-map baseline, then delayed correction and object queries with validity/coverage shown. |
| `docs/figures/risk_coverage.png` | E2 after H0 | Held-out risk–coverage and risk–latency curves; validation-only tuning and uncertainty intervals. |
| `docs/figures/failure_gallery.gif` | R2/E1/E2 | Unchanged, moved, removed, occluded and no-stable-anchor cases; no curated success-only sequence. |

## Render from scored evidence

1. Complete the relevant stage in [PLAN](../research/PLAN.md), then save run/frame IDs and the dataset manifest. The two offline author maps already exist locally; their final map cannot be presented as an online per-frame decision.
2. Produce point outcomes using the **declared evaluator**. For map NN use the same 5 cm rule; for segment labels use exact point identity. GT labels enter the evaluator/renderer, not the method. A different API needs a separately named figure and table.
3. Fix world bounds, camera, frame list and display sample once in [rendering.json](../../configs/rendering.json). All methods and GT use them. Point thinning is for display only; metrics use the full declared evaluation population. Frame numbers from the selected teaser are not evidence of uninterrupted KITTI sampling.
4. Render raw / removed / retained panels, add run IDs and the **scope** of any displayed number, and save [media_record.template.json](media_record.template.json) with actual hashes and generator command. Blue misses and red false removals must remain visible.
5. Publish PNG/SVG or a compact GIF preview plus an MP4 link. GitHub homepages should use the GIF/PNG preview, not depend on an HTML video element. The suggested 8 MiB GIF budget is our presentation target, not a platform limit.

## Publication

The map replay and API diagnostic have tested renderers; the remaining reserved assets are not generated yet. Do not create an empty image or label a planned generator as tested. Once an actual renderer exists, record its command/version and bind the output hash to a media-producing run record; `check_docs.py` checks published assets against those hashes.

Place the generated file at the reserved path, update the source evidence and status in [slots.json](slots.json), and replace the corresponding homepage comment with a live image. Apply the same asset to both language editions; translate captions. If localized overlays are needed, generate them from the same input/config, not two independent selections.

```bash
uv run python scripts/evidence/check_docs.py
uv run python scripts/evidence/verify_evidence.py
```

Do not retouch masks or change metric numbers in an editor. Publish failure cases too. Raw scans, model weights and dataset files stay outside this directory. PNG/SVG figures should have readable labels and a solid background for both GitHub themes.

## Four-paper recordings

[Paper index](../papers/README.md) links each native result to its MP4, GIF, poster and bilingual PDF. These 12 media assets are hash-bound in `slots.json`. [Recording commands](../guides/RECORDING.md) disclose final-map replay and coordinate checks. Physical capture is reserved as `docs/figures/physical_capture.mp4` until data collection.

Twelve bilingual PDFs are hash-bound to [generation evidence](../../results/reference/paper-pdfs/record.json), with separate [32-page layout review](../../results/reference/paper-report-review/qa.json). The index now contains 38 published assets and 7 reserved slots.

## Paired exploration and full sessions

Six measured PNGs add paired outcomes/errors, dynamic removal, restricted query projections and two raw-frame annotation overlays. [Paired report](../research/PAIRED_RESULTS.md) explains the different losses and candidate status. Two new bilingual PDFs have [generation](../../results/reference/paired-study-pdfs/record.json) and [11-page visual review](../../results/reference/paired-report-review/qa.json) evidence. Together there are 14 PDFs; previous 12 baseline reports retain their original snapshots. Four full execution MP4s stay local; [index and recording convention](../guides/RECORDING.md#complete-local-execution-recordings).
