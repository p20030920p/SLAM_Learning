# HOV-SG 20-frame map and original scoring

English | [中文](HOVSG_HOME_RESULTS.zh-CN.md)

The extra room0 home configuration completed feature mapping and original semantic evaluation. Default 200-frame sampling and the full benchmark remain incomplete.

## 1. Results

| Item | Value |
| --- | --- |
| Input | 2,000 native 1200×680 RGB-D pairs; `skip_frames=100`, 20 selected |
| SAM | Batch 16, disclosed resource variant |
| Saved map | 156 segments; 399,663 global points |
| Features | `[156,1024]` and `[399663,1024]`, finite and aligned |
| mIoU / F-mIoU | 34.7500 / 62.8725% |
| mAcc / pAcc | 43.7114 / 72.1861% |

[Metrics](../evidence/runs/hovsg-room0-home-evaluation-author-palette-01/metrics.json) · [Original log](../evidence/runs/hovsg-room0-home-evaluation-author-palette-01/evaluation/run.log) · [Audit](../evidence/runs/hovsg-room0-home-evaluation-author-palette-01/evaluation-audit/validation.json). JSON values are 0..1; the table multiplies by 100. No saved confusion matrix exists, so no independent matrix recalculation is claimed.

## 2. Evaluation retry

Our wrapper selected a palette missing class 0. The retry points to the author's complete palette and verifies/reuses the saved map; source, predictions and scoring formulas remain unchanged. The earlier failure is preserved and is not an algorithm-accuracy failure.

Mapping took 425.62 s and evaluation 82.48 s under shared load; neither is a paper-speed result. Checks bind 166 unique artifacts; large PLY/PT files remain local. `full_feats.pt` is about 1.64 GB.

## 3. Limits

The default 200-frame run first hit OOM, then retry 03 timed out at 7,200 s without a final map. New default 06/follower 08 wait with disclosed limits; queued status is not completion. Reduced sampling changes observations and fusion size together.

The author scores 5NN labels at GT mesh vertices. The logged 3,814,588 interpolation positions are not the excluded-class scoring denominator. These scores do not establish identity, hierarchy, queries, navigation or superiority over CG's different support. [Scope](SCOPE.md).

## 4. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```text
/home/qzl/projects/SLAM_Author_Originals/runs/public-semantic-benchmark-06-room0-hov-home-features/artifacts/replica/
```

```bash
cat "$RUNTIME/runs/public-semantic-benchmark-06-room0-hov-home/validation.json"
cat "$RUNTIME/runs/hovsg-room0-home-evaluation-author-palette-01/outcomes.json"
cat "$RUNTIME/runs/hovsg-room0-home-evaluation-author-palette-01/metrics.json"
```
