# Historical protocol and BeautyMap Table III

English | [中文](KITTI_PAPER_PROTOCOL.zh-CN.md)

Historical DynamicMap_Benchmark commit `161b555017608277d21230cd0be0e80589ee8576` follows the author's [version clarification](https://github.com/KTH-RPL/DynamicMap_Benchmark/discussions/8). BeautyMap's exact paper commit remains unidentified.

## 1. Matched Table III

Historical extraction keeps unfiltered scans and labels; original C++ GT and PCL export use 0.05 m. KITTI-02 frames 860–950 provide 91 scans; z=0.5 m and range=40 m follow the README.

| XY m | Measured SA / DA / HA % | Paper SA / DA / HA % |
| ---: | --- | --- |
| 0.5 | 83.9165 / 84.1405 / 84.0284 | 83.92 / 84.14 / 84.03 |
| 1.0 | 83.3978 / 82.4092 / 82.9006 | 83.40 / 82.41 / 82.90 |
| 2.0 | 74.9226 / 88.8251 / 81.2837 | 74.92 / 88.83 / 81.28 |

All nine entries match paper rounding; maximum difference 0.0049 percentage points. The historical scorer outputs AA, not HA. After verifying original exports, the current author's HA scorer runs separately without changing maps. [Log](../../results/runs/beautymap-table3-historical-01/scores/run.log) · [Metrics](../../results/runs/beautymap-table3-historical-01/metrics.json).

## 2. Remaining version gap

Historical 00 restores all 141 point counts but no byte-identical files. Pose/convention differences and 00/01 paper-score gaps remain. Current 50 m, historical and released inputs cannot be pooled. [Historical results](../../results/runs/kitti-historical-protocol-01/metrics.json) · [Validation](../../results/runs/kitti-historical-results-validation-01/validation.json).

Matching 02 does not identify every unreported parameter or historical dependency. Coarser-grid tradeoffs are existing paper behavior, not H1 effectiveness. Use new run names; original checkouts remain fixed and task timing is not a paper-speed measure.

## 3. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```bash
RUNTIME=/home/qzl/projects/SLAM_Author_Originals
DOCS=/mnt/d/workspace/be2/SLAM_Author_Originals
"$RUNTIME/envs/lidar/bin/python" "$DOCS/src/scripts/run_kitti_paper_protocol.py" \
  --runtime "$RUNTIME" --name kitti-historical-manual-01
python3 "$DOCS/src/scripts/verify_beautymap_table3.py" --runtime "$RUNTIME" \
  --historical-run "$RUNTIME/runs/kitti-historical-manual-01" \
  --name beautymap-table3-manual-01
```
