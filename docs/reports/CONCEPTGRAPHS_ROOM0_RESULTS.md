# ConceptGraphs room0 semantic evaluation

English | [中文](CONCEPTGRAPHS_ROOM0_RESULTS.zh-CN.md)

The original SAM frontend, object map, RGB PointFusion and semantic evaluator completed. This is one scene with the disclosed SAM batch-16 variant, not the eight-scene benchmark.

## 1. Measured results

| Author metric | % |
| --- | ---: |
| mIoU | 21.3460 |
| mRecall | 38.3156 |
| mPrecision | 29.3624 |
| Original mF1 | 25.2661 |
| Frequency-weighted IoU | 50.1379 |

[Original CSV](../../results/runs/conceptgraphs-room0-evaluation-cuda-05/results/none_overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub/replica_ex6_results.csv). Its `all` row includes only room0.

## 2. Denominators and audit

The 2,000-frame source uses stride 5: 400 native 1200×680 observations. SAM batch 144→16 retains the 12×12 prompt grid; comparison of 26 shared frames does not prove complete numerical equivalence. There are 77 object records, not 77 verified physical instances.

GT has 1,556,890 points and 102 label dimensions. RGB PointFusion has 7,754,935 points; the scored matrix contains 23 classes and 4,085,377 reconstructed points after exclusions. Scene-GT vocabulary and 1NN transfer measure semantic classification on this support, not open-world retrieval or geometric accuracy.

Float64 matrix recalculation differs from the author CSV by at most 1.96e-7 percentage points, below 1e-5 tolerance. The original mF1 denominator is `max(1,p+r)`; standard macro-F1 25.8221% is a separate audit supplement. [Audit](../../results/runs/conceptgraphs-room0-evaluation-cuda-05/evaluation-audit/validation.json).

## 3. Observations and limits

![Class IoU and support](../../results/runs/conceptgraphs-room0-class-analysis-01/room0-class-metrics.png)

Blinds/sofa IoU is 94.77/74.78%; rug/table have no predictions despite 18.34/6.36% GT support. Ten of 23 classes have zero IoU. This does not isolate masks, naming, association, interpolation or pose as the cause. [Class table](../../results/runs/conceptgraphs-room0-class-analysis-01/room0-class-metrics.csv).

The 690.65-second evaluation includes paging and a task-specific RAM-limit change; it is not a paper speed comparison. Original and monitor snapshots are separately preserved. No delayed correction, identity recovery, stale-coordinate or H1 test was run. [Protocol boundaries](SCOPE.md).

## 4. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```powershell
wsl -d Ubuntu-22.04 -u qzl
```

```bash
export DOCS=/mnt/d/workspace/be2/SLAM_Author_Originals
export RUNTIME=/home/qzl/projects/SLAM_Author_Originals
cat "$RUNTIME/runs/conceptgraphs-room0-evaluation-cuda-05/metrics.json"
"$RUNTIME/envs/conceptgraphs/bin/python" "$DOCS/src/scripts/audit_cg_semantic_results.py" \
  --run-root "$RUNTIME/runs/conceptgraphs-room0-evaluation-cuda-05" \
  --output "$RUNTIME/local/cg-room0-audit-manual-01.json"
```
