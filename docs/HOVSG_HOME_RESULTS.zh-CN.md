# HOV-SG：家用采样地图与未完成评分

2026-10-09。room0 的额外家用配置已完成原始特征地图，**语义评分尚未成功，默认采样与完整八场景 benchmark 均未完成。**

| 项目 | 已检查结果 |
|---|---|
| 输入 | 原生 2000 组 1200×680 RGB-D；`pipeline.skip_frames=100` 均匀取 20 帧 |
| SAM | `points_per_batch=16`，显式资源兼容配置 |
| 原始特征入口 | 退出 0；记录耗时 425.62 秒，非论文速度对照 |
| 保存结果 | 156 个分段点云；全局点云 399,663 点 |
| 特征形状 | 分段 `[156,1024]`；全局 `[399663,1024]`，有限数值及对应数量通过检查 |
| 语义评价 | 首次退出 1，原因是包装脚本选择的颜色文件缺少背景类 0；已修正路径，单独排队重试 |

原始[特征执行记录](../evidence/runs/public-semantic-benchmark-06-room0-hov-home-features/record.json)、[输出检查](../evidence/runs/public-semantic-benchmark-06-room0-hov-home/validation.json)与[错误诊断](../evidence/runs/public-semantic-benchmark-06-room0-hov-home/diagnostics/evaluation-palette-path.json)分别保留。已重新流式核对 166 个唯一产物的大小与 SHA-256；大体积 PLY/PT 留在本机，Git 只保存轻量证据。

原始地图在 WSL：

```text
/home/qzl/projects/SLAM_Author_Originals/runs/public-semantic-benchmark-06-room0-hov-home-features/artifacts/replica/
```

`full_feats.pt` 约 1.64 GB；分段数量和点数证明保存契约完成，不能当作语义、对象身份或层级图准确率。

## 为什么只重试评价

作者评价先生成一个含 1..101 类的颜色 JSON，随后加入背景类 0。我们的包装脚本误将生成文件传作颜色表，原始代码访问 `colors_map[0]` 因而失败。固定版作者已经提供含 -1、0 的[完整颜色表](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/hovsg/labels/class_id_colors.json)；修正包装脚本使用该路径即可，作者源码、已保存地图、类别预测和评分公式均不改。这次是我们的配置错误，不能归为方法精度失败。

`hovsg-room0-home-evaluation-author-palette-01` 已核对地图与原始提交，等待当前 Detect 前端完成后运行作者评价；为避免 GPU 竞争，只暂停本任务的队列调度器，正在执行的 Detect 子进程继续。评价结束或异常后恢复调度器。运行中的状态与日志留在本机，完成前不上传为结果。

本机只读检查：在[Windows/WSL 手册](RUNBOOK.zh-CN.md)设置 `RUNTIME` 后执行：

```bash
cat "$RUNTIME/runs/public-semantic-benchmark-06-room0-hov-home/validation.json"
cat "$RUNTIME/runs/hovsg-room0-home-evaluation-author-palette-01/outcomes.json"
```

默认 `skip_frames=10` 的 200 帧运行另有记录：前次融合 OOM，03 重试在 7200 秒上限超时，均未保存最终地图。20 帧运行成功不能证明默认配置已完成或单独归因内存下降；采样同时改变观测与融合规模。Replica 原始入口也不构建 HM3D 的多楼层图。[完成范围](SCOPE.zh-CN.md)。
