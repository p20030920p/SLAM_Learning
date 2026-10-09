# DUFOMap Python：输出表示与评价阈值对照

[English](DUFOMAP_OUTPUT_AUDIT.md) | 中文

2026-10-09，本机完成作者原始 `main.py --voxel_map False`，并与先前经哈希复核的默认 `voxel_map=True` 结果对照。使用同一份 00 发布包的 141 帧、同一 Python 绑定 1.1.1；不改作者源码。几何、点数、有限数值及输出哈希均通过检查。

| 原始 Python 输出 | 近邻阈值 m | SA % | DA % | AA % | HA % |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原始点 | 0.05 | 99.8860 | 96.0305 | 97.9393 | 97.9203 |
| 体素 | 0.05 | 51.6256 | 98.1257 | 71.1744 | 67.6561 |
| 原始点 | 0.10 | 99.9422 | 94.5584 | 97.2131 | 97.1758 |
| 体素 | 0.10 | 98.9436 | 95.2856 | 97.0974 | 97.0802 |

两种输出分别有 17,232,009 / 1,447,194 点。两档阈值均使用原始 PCL 导出器和原 Python 评分公式；0.10 m 是补充敏感性分析，不能替换论文 0.05 m 指标。放宽阈值同时改变动态点匹配，不能只报告 SA 的上升。

这组对照说明输出表示与评价阈值强烈影响指标。不能把体素结果的低 SA 直接等同于同样比例的静态原始点被删，也不能据此支持 H1。两种输出来自两次原始入口执行，尚无重复运行方差。

还须区分 Python 与 C++ 默认：固定版 [Python 入口](https://github.com/KTH-RPL/dufomap/blob/9e239ddd5995136e14f5212f33382a6ebc59e518/main.py)硬编码 `d_p=2`、积分距离 0.2–50 m；[C++ 配置](https://github.com/KTH-RPL/dufomap/blob/9e239ddd5995136e14f5212f33382a6ebc59e518/assets/config.toml)为 `d_p=1`、无最大距离限制。两者的绑定/工具链也不同；本次没有将二者分差解释成单一变量的效果。

可复查：[原始分数](../../results/runs/dufo-python-output-audit-01/metrics.json)、[点云检查](../../results/runs/dufo-python-output-audit-01/validation.json)、[执行记录](../../results/runs/dufo-python-output-audit-01/raw-mapping/record.json)。首轮 scope 文本中的 `raw=False flag` 指命令中的 `--voxel_map False`，以实际命令数组为准。

在 Windows PowerShell 输入 `wsl -d Ubuntu-22.04`，再执行（运行名必须新建）：

```bash
RUNTIME=/home/qzl/projects/SLAM_Author_Originals
DOCS=/mnt/d/workspace/be2/SLAM_Author_Originals
"$RUNTIME/envs/lidar/bin/python" "$DOCS/src/scripts/run_dufo_python_outputs.py" \
  --runtime "$RUNTIME" --name dufo-python-output-audit-manual-01
```

脚本复核原有体素结果的 SHA-256，再重跑原始点入口及两档原始评价。每个子任务限额 2 GiB RAM / 6 GiB swap、CPU 100%，耗时不用于论文性能比较。
