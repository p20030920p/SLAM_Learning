# HOV-SG：家用采样地图与原始评分

[English](HOVSG_HOME_RESULTS.md) | 中文

2026-10-09。room0 的额外家用配置已完成原始特征地图及作者语义评价：**mIoU 34.7500%、F-mIoU 62.8725%。默认采样与完整八场景 benchmark 仍未完成。**

| 项目 | 已检查结果 |
| --- | --- |
| 输入 | 原生 2000 组 1200×680 RGB-D；`pipeline.skip_frames=100` 均匀取 20 帧 |
| SAM | `points_per_batch=16`，显式资源兼容配置 |
| 原始特征入口 | 退出 0；记录耗时 425.62 秒，非论文速度对照 |
| 保存结果 | 156 个分段点云；全局点云 399,663 点 |
| 特征形状 | 分段 `[156,1024]`；全局 `[399663,1024]`，有限数值及对应数量通过检查 |
| 语义评价 | 修正包装脚本的颜色表路径后，复用地图重试退出 0；评价记录耗时 82.48 秒 |

| 作者原指标 | 原日志值，0..1 | 百分比 |
| --- | ---: | ---: |
| mIoU | 0.34749998212375693 | 34.7500 |
| F-mIoU | 0.628725319296474 | 62.8725 |
| mAcc | 0.43711407407257175 | 43.7114 |
| pAcc | 0.7218608514499825 | 72.1861 |

来源为[原始评价记录](../../results/runs/hovsg-room0-home-evaluation-author-palette-01/evaluation/record.json)、[原日志](../../results/runs/hovsg-room0-home-evaluation-author-palette-01/evaluation/run.log)和[指标 JSON](../../results/runs/hovsg-room0-home-evaluation-author-palette-01/metrics.json)。JSON 单位为 0..1，表中另乘 100 展示。

[审计](../../results/runs/hovsg-room0-home-evaluation-author-palette-01/evaluation-audit/validation.json)确认四项数字与 SHA-256 绑定的日志完全一致；作者入口没有保存混淆矩阵，本次不声称独立矩阵复算。

原始[特征执行记录](../../results/runs/public-semantic-benchmark-06-room0-hov-home-features/record.json)、[输出检查](../../results/runs/public-semantic-benchmark-06-room0-hov-home/validation.json)与[错误诊断](../../results/runs/public-semantic-benchmark-06-room0-hov-home/diagnostics/evaluation-palette-path.json)分别保留。已重新流式核对 166 个唯一产物的大小与 SHA-256；大体积 PLY/PT 留在本机，Git 只保存轻量证据。

原始地图在 WSL：

```text
/home/qzl/projects/SLAM_Author_Originals/runs/public-semantic-benchmark-06-room0-hov-home-features/artifacts/replica/
```

`full_feats.pt` 约 1.64 GB；分段数量和点数证明保存契约完成，不能当作语义、对象身份或层级图准确率。

## 1. 为什么只重试评价

作者评价先生成一个含 1..101 类的颜色 JSON，随后加入背景类 0。我们的包装脚本误将生成文件传作颜色表，原始代码访问 `colors_map[0]` 因而失败。

固定版作者已经提供含 -1、0 的[完整颜色表](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/hovsg/labels/class_id_colors.json)；修正包装脚本使用该路径即可，作者源码、已保存地图、类别预测和评分公式均不改。这次是我们的配置错误，不能归为方法精度失败。

`hovsg-room0-home-evaluation-author-palette-01` 已核对地图与原始提交，只重跑作者评价，未重新提取或修改保存的地图。为避免 GPU 竞争，运行时仅暂停本任务队列调度器，正在执行的 Detect 子进程继续；评价于莫斯科时间 03:16 完成，随后恢复调度器。

[复用检查](../../results/runs/hovsg-room0-home-evaluation-author-palette-01/reuse-validation.json)与[恢复记录](../../results/runs/hovsg-room0-home-evaluation-author-palette-01/queue-hold.json)保留。

本机只读检查：在[Windows/WSL 手册](../guides/RUNBOOK.zh-CN.md)设置 `RUNTIME` 后执行：

```bash
cat "$RUNTIME/runs/public-semantic-benchmark-06-room0-hov-home/validation.json"
cat "$RUNTIME/runs/hovsg-room0-home-evaluation-author-palette-01/outcomes.json"
cat "$RUNTIME/runs/hovsg-room0-home-evaluation-author-palette-01/metrics.json"
```

默认 `skip_frames=10` 的 200 帧运行另有记录：前次融合 OOM，03 重试在 7200 秒上限超时，均未保存最终地图。20 帧运行成功不能证明默认配置已完成或单独归因内存下降；采样同时改变观测与融合规模。Replica 原始入口也不构建 HM3D 的多楼层图。[完成范围](SCOPE.zh-CN.md)。

显存诊断时旧默认 05 的等待调度器已取消，未启动作者阶段；新默认 06 等待 CG 队列 09 结束，再串行运行；特征阶段时限延长至 21600 秒，16G RAM / 48G swap，采样和算法不变。当前只有排队状态，不能写为默认完成。

后续 `hovsg-replica-default-08` 仅在默认 room0 完成并通过校验后继续其余七场景；失败则停止。该队列不读取这份 20 帧家用图作为默认结果。

作者在原始 Replica GT 面片顶点处用预测点 5NN 多数投票评分；日志中有 3,814,588 个待插值位置，这不是全部计分有效点的分母。排除类别后的分母没有在该日志单列，不能用全顶点数反推。这个分数是家用配置的语义基线，不是开放世界查询、身份恢复、层级图或导航准确率，也不能与 CG 的原生 mIoU 直接排名。
