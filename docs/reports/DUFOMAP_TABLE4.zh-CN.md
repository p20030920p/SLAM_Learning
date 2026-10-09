# DUFOMap 表 IV 消融复现

[English](DUFOMAP_TABLE4.md) | 中文

2026-10-09（莫斯科）实际执行。使用作者原始 C++ 二进制和 00 公开帧段的全部 141 帧，仅修改作者 TOML 中的 `resolution`、`inflate_hits_dist`（d_s）、`inflate_unknown`（d_p）。完整设置复用经过 SHA-256 核对的原始成功结果，五组均重新运行作者 PCL 导出（0.05 m）和作者 Python 评分。

| 设置 | 本机 SA % | 论文 SA % | 本机 DA % | 论文 DA % | 本机 AA % | 论文 AA % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 无 d_s、d_p；v=0.1 m | 14.8856 | 14.89 | 99.9917 | 99.99 | 38.5802 | 38.58 |
| 仅 d_s=0.2 m；v=0.1 m | 30.2853 | 30.29 | 99.9865 | 99.99 | 55.0284 | 55.03 |
| 仅 d_p=1；v=0.1 m | 91.8936 | 91.89 | 98.9727 | 98.97 | 95.3675 | 95.37 |
| d_s=0.2 m、d_p=1；v=0.2 m | 92.9696 | 92.97 | 98.2424 | 98.24 | 95.5696 | 95.57 |
| 完整设置；v=0.1 m | 97.9635 | 97.96 | 98.7196 | 98.72 | 98.3408 | 98.34 |

论文值来自 [DUFOMap §V-D、表 IV](https://arxiv.org/html/2403.01449v1#S5.T4)。本机 15 个指标保留两位小数后均一致；最大绝对差为 0.0047 个百分点，处于论文显示精度内。

![原始评价的五组消融结果](../../results/figures/dufomap-table4.png)

[可导出 PDF](../../results/figures/dufomap-table4.pdf) · [图表来源与匹配检查](../../results/figures/dufomap-table4.json)。柱高取自原始评分日志，未重新实现评价公式。

这验证了该帧段上误差补偿的消融趋势。它不能证明在线定位改善、不同位姿来源下仍保持相同分数，或在新传感器上达到同样效果。论文其他实验仍需另行复现。

证据：[原始评分日志](../../results/runs/dufomap-table4-ablation-01/scores/run.log)、[指标与逐项差值](../../results/runs/dufomap-table4-ablation-01/metrics.json)、[完成记录](../../results/runs/dufomap-table4-ablation-01/outcomes.json)。输入逐文件哈希、参数副本、配置 diff、命令与输出哈希保存在同名本地运行目录；源码保持干净。

本轮 CPU 配额为 200%、RAM/swap 限额为 4G/6G，与其他任务同时运行，不用于复现论文耗时或性能排序。

Windows PowerShell 重做，运行名必须新建：

```powershell
wsl -d Ubuntu-22.04 -- python3 /mnt/d/workspace/be2/SLAM_Author_Originals/src/scripts/run_dufo_ablation.py --runtime /home/qzl/projects/SLAM_Author_Originals --name dufomap-table4-manual-01
```

已在这台电脑完成数据准备时，上述脚本直接使用 `data/00-pristine`。它会验证 141 帧和原始完整设置结果，独立保存新输出，拒绝覆盖旧运行目录。
