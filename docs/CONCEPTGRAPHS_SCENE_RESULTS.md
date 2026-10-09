# ConceptGraphs scene and frontend comparisons

English | [中文](CONCEPTGRAPHS_SCENE_RESULTS.zh-CN.md)

Five original scene chains completed, with saved-matrix audits. These are native scene rows, not a partial average presented as the full benchmark.

## 1. Scores

| Scene | SAM-only mIoU / F-mIoU % | Detect mIoU / F-mIoU % |
| --- | ---: | ---: |
| room0 | 21.3460 / 50.1379 | 25.5987 / 45.6541 |
| office0 | 20.4157 / 33.0546 | 17.5151 / 30.4729 |
| office1 | 14.9755 / 14.7128 | Incomplete |

Detect raises room0 macro IoU but lowers weighted IoU; both fall on office0. Frontend and mapping settings change together, so this is not a single-component ablation or evidence of general Detect superiority. No repeatability interval is available.

## 2. Why scene and all rows differ

Scene rows select GT-present classes; `all` selects nonzero reconstructed GT support and slices both matrix axes. Office0 SAM-only changes from 20 to 19 classes and 20.4157→21.4902% mIoU. Office1 changes from 18 to 17 and 14.9755→16.3958%; its weighted IoU also changes from 14.7128→15.5714%.

Do not average single-scene `all` rows into the eight-scene result. Recalculation preserves original formulas; the four newer chains differ by less than 4.8e-7 percentage points. Earlier CSV-only provenance is not retroactively rewritten as matrix-bound execution. [CSVs, audits and figure sources](CONCEPTGRAPHS_SCENE_RESULTS.zh-CN.md).

## 3. Research implication and pending work

Freeze the frontend, scored support and vocabulary before testing H1. These classification scores do not measure identity or late-correction recovery, and native HOV-SG scores use a different protocol. [Comparison](SCOPE.md).

Interrupted queues 06/07, cancelled first-frame queue 08 and partial outputs remain preserved. Queue 09 verifies the five completed chains before the disclosed sequential-residency retry. Complete eight-scene success is required before original full evaluation. [GPU diagnosis](CG_GPU_RECOVERY.md) · [Runbook](RUNBOOK.md).

## 4. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```bash
cat "$RUNTIME/runs/public-semantic-benchmark-09/outcomes.json"
tail -c 1500 "$RUNTIME/runs/public-semantic-benchmark-09/orchestration.log"
```
