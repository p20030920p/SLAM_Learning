# 实测记录汇总

由原始记录生成。执行完成、论文表格一致和假设验证是不同状态。

| 实验 | 范围 | 执行 | 论文表格 | SA % | DA % | AA % | HA % | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DUFOMap 接口诊断 | 完整 teaser | 已执行 | 未比较 | — | — | — | — | [api-check-wsl](reference/api-check-wsl/record.json) |
| measured_diagnostic_plot | measured_diagnostic_plot | 已执行 | 未比较 | — | — | — | — | [api-diagnostic-plot](reference/api-diagnostic-plot/record.json) |
| beautymap | 完整 teaser | 已执行 | 有差异 | 96.9529 | 98.3382 | 97.6431 | 97.6407 | [beautymap](reference/beautymap/record.json) |
| beautymap | 完整 teaser | 已执行 | 有差异 | 96.9529 | 98.3382 | 97.6431 | 97.6407 | [beautymap-linux](reference/beautymap-linux/record.json) |
| beautymap | 完整 teaser | 失败 | 未比较 | — | — | — | — | [beautymap-windows-failure](reference/beautymap-windows-failure/record.json) |
| beautymap | 完整 teaser | 已执行 | 有差异 | 96.9529 | 98.3382 | 97.6431 | 97.6407 | [beautymap-wsl](reference/beautymap-wsl/record.json) |
| ConceptGraphs | Replica room0 40 次观测子集 | 已执行 | 未比较 | — | — | — | — | [conceptgraphs-wsl](reference/conceptgraphs-wsl/record.json) |
| ConceptGraphs | Replica room0 40 次观测子集 | 失败 | 未比较 | — | — | — | — | [conceptgraphs-wsl-batch144-interrupted](reference/conceptgraphs-wsl-batch144-interrupted/record.json) |
| dufomap | 完整 teaser | 已执行 | 有差异 | 97.9798 | 98.7029 | 98.3407 | 98.3400 | [dufomap](reference/dufomap/record.json) |
| dufomap | 完整 teaser | 已执行 | 有差异 | 97.9798 | 98.7029 | 98.3407 | 98.3400 | [dufomap-linux](reference/dufomap-linux/record.json) |
| dufomap | 完整 teaser | 已执行 | 有差异 | 97.9798 | 98.7029 | 98.3407 | 98.3400 | [dufomap-wsl](reference/dufomap-wsl/record.json) |
| 地图评价器对照 | 完整 teaser | 已执行 | 未比较 | — | — | — | — | [evaluation-check-wsl](reference/evaluation-check-wsl/record.json) |
| 探索性合成校准实验 | 探索性合成校准实验 | 已执行 | 未比较 | — | — | — | — | [evidence-stress](reference/evidence-stress/record.json) |
| 探索性合成机制实验 | 探索性合成机制实验 | 已执行 | 未比较 | — | — | — | — | [mechanism](reference/mechanism/record.json) |
| 真实数据位姿敏感性 | 真实数据位姿敏感性 | 已执行 | 未比较 | — | — | — | — | [pose-stress](reference/pose-stress/record.json) |
| 真实数据位姿敏感性 | 真实数据位姿敏感性 | 已执行 | 未比较 | — | — | — | — | [pose-stress-linux](reference/pose-stress-linux/record.json) |
| 作者地图离线回放 | 作者地图离线回放 | 已执行 | 未比较 | — | — | — | — | [reproduction-media-wsl](reference/reproduction-media-wsl/record.json) |

记录中的失败：

- beautymap (beautymap-windows-failure): CalledProcessError: Command '['D:\\workspace\\be2\\SLAM_Learning\\.venv310\\Scripts\\python.exe', '-m', 'slam_learning.cli', '_worker', '--root', 'D:\\workspace\\be2\\SLAM_Learning', '--method', 'beautymap', '--output', 'D:\\workspace\\be2\\SLAM_Learning\\results\\runs\\beautymap-9d32b2cc4c1c', '--frames', '0']' returned non-zero exit status 1.
- ConceptGraphs (conceptgraphs-wsl-batch144-interrupted): Command '['/home/qzl/projects/SLAM_Learning/.venv-semantic/bin/python', '/home/qzl/projects/SLAM_Learning/results/runs/conceptgraphs-855255b27df4/author-code/conceptgraph/scripts/generate_gsa_results.py', '--dataset_root', '/home/qzl/projects/SLAM_Learning/results/runs/conceptgraphs-855255b27df4/input/Replica', '--dataset_config', '/home/qzl/projects/SLAM_Learning/results/runs/conceptgraphs-855255b27df4/author-code/conceptgraph/dataset/dataconfigs/replica/replica.yaml', '--scene_id', 'room0', '--class_set', 'none', '--stride', '1']' died with <Signals.SIGTERM: 15>.

合成试验使用已知身份、可见性或噪声模型，属于探索性分析，不是完整系统复现或独立假设验证。
原始数据与大点云仅保留在本机；可发布记录包含其哈希与运行日志。
`verify --full` 需要本地点云。历史存档分数不参与本表。
