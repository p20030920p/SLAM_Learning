# DUFOMap output representation and scoring threshold

English | [中文](DUFOMAP_OUTPUT_AUDIT.zh-CN.md)

Same 141-scan 00 release and Python binding 1.1.1; original raw-point and voxel entries, with unchanged author source.

## 1. Results

| Output | NN threshold m | SA % | DA % | AA % | HA % |
| --- | ---: | ---: | ---: | ---: | ---: |
| Raw points | 0.05 | 99.8860 | 96.0305 | 97.9393 | 97.9203 |
| Voxels | 0.05 | 51.6256 | 98.1257 | 71.1744 | 67.6561 |
| Raw points | 0.10 | 99.9422 | 94.5584 | 97.2131 | 97.1758 |
| Voxels | 0.10 | 98.9436 | 95.2856 | 97.0974 | 97.0802 |

Raw/voxel outputs contain 17,232,009 / 1,447,194 points. The original PCL exporter and Python scorer were used. The 0.10 m sensitivity test does not replace the paper's 0.05 m result; DA changes too.

## 2. Interpretation

Low voxel SA is not the same fraction of static raw points being deleted. This comparison does not support H1 or provide repeatability variance.

Python hardcodes `d_p=2` and 0.2–50 m integration; C++ defaults to `d_p=1` without a maximum-distance limit. Their differences do not isolate output representation.

[Metrics](../../results/runs/dufo-python-output-audit-01/metrics.json) · [Validation](../../results/runs/dufo-python-output-audit-01/validation.json). The recorded command array is authoritative for `--voxel_map False`. Use a fresh run name; task limits 2 GiB RAM / 6 GiB swap and CPU 100% preclude paper-speed comparisons.

## 3. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```bash
RUNTIME=/home/qzl/projects/SLAM_Author_Originals
DOCS=/mnt/d/workspace/be2/SLAM_Author_Originals
"$RUNTIME/envs/lidar/bin/python" "$DOCS/src/scripts/run_dufo_python_outputs.py" \
  --runtime "$RUNTIME" --name dufo-python-output-audit-manual-01
```
