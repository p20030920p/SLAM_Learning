# 历史协议与 BeautyMap 表 III

2026-10-09，已重跑作者注明的 DynamicMap_Benchmark 历史版 `161b555017608277d21230cd0be0e80589ee8576`。版本依据是 [作者说明](https://github.com/KTH-RPL/DynamicMap_Benchmark/discussions/8)：DUFOMap 使用该提交和 [Zenodo v1](https://zenodo.org/records/8160051)；BeautyMap 的具体论文提交在该说明中仍未给出。

## 已达到：02 网格消融匹配论文

历史提取器不做新版 50 m 过滤，保留原始标签；原始 C++ `extract_gtcloud` 生成二元 GT，再运行未修改的 BeautyMap 和历史 PCL 导出器，阈值 0.05 m。XY 为 0.5/1/2 m，z=0.5 m、范围 40 m；使用本轮官方源的 02 原始帧 860–950（91 帧）。

| XY 网格 m | 实测 SA % | 实测 DA % | 实测 HA % | 论文 SA / DA / HA % |
|---:|---:|---:|---:|---|
| 0.5 | 83.9165 | 84.1405 | 84.0284 | 83.92 / 84.14 / 84.03 |
| 1.0 | 83.3978 | 82.4092 | 82.9006 | 83.40 / 82.41 / 82.90 |
| 2.0 | 74.9226 | 88.8251 | 81.2837 | 74.92 / 88.83 / 81.28 |

**SA/DA/HA 共 9 项均与 [论文表 III](https://arxiv.org/html/2405.07283v1#S4.T3)的两位小数一致**，最大绝对差 0.0049 个百分点。更粗网格在该场景提高 DA、降低 SA；这是论文已有的参数取舍，不能作为 H1 的新效果。

历史评分器只输出 SA/DA/AA，AA 与 HA 不同。为核对表 III 的 HA，在重新检查历史 GT／三个导出标签的哈希后，另运行作者当前 `evaluate_all.py`（原公式，只设三项 README 配置），得到上表。没有把旧日志的 AA 列误作 HA，也未重跑或更改地图。[HA 原始日志](../evidence/runs/beautymap-table3-historical-01/scores/run.log)、[九项核对与日志哈希](../evidence/runs/beautymap-table3-historical-01/metrics.json)。

论文未单列 z 分辨率，本轮选择作者 README 的 0.5 m；数值匹配不等于证明所有未报告设置、历史依赖和位姿版本完全相同。运行时间、01 模块消融、其余论文实验尚未由此完成。

## 尚未解决：00/01 的输入版本

历史原流程还完成 00/01/02 的 DUFOMap，以及 01 默认 BeautyMap。旧评分器原始 SA/DA/AA：

| 数据 | 方法 | SA % | DA % | AA % |
|---|---|---:|---:|---:|
| 00 | DUFOMap | 98.6217 | 98.7362 | 98.6790 |
| 01 | DUFOMap | 98.8671 | 93.9496 | 96.3770 |
| 01 | BeautyMap | 98.7710 | 92.0418 | 95.3471 |
| 02 | DUFOMap | 68.7417 | 89.0077 | 78.2211 |

以上与既有发布包结果及新版 50 m 结果分开报告。历史重建的 00 有 141/141 帧与发布包点数相同，但 0/141 文件逐字节相同；这没有消除已发现的位姿／约定差异。00、01、02 GT 分别为 17,362,230 / 11,771,122 / 11,522,438 点。[历史预处理验证](../evidence/runs/kitti-historical-protocol-01/validation.json)、[七份最终地图的独立哈希／有限数值检查](../evidence/runs/kitti-historical-results-validation-01/validation.json)、[全部七组原始分数](../evidence/runs/kitti-historical-protocol-01/metrics.json)、[历史／当前源码哈希](../evidence/runs/kitti-historical-protocol-01/source-version.json)。01/02 无发布包可比较，首轮验证中的比较计数 0 仅表示未检查；独立验证将这两项明确记为 null。

历史和当前版的位姿解析及 PCL 最近邻判定仅有注释／用法文字差异；当前评分新增 HA，SA/DA/AA 公式保留。预处理版本确实不同，故先前新版 02 分数未匹配不能被解释为算法失效。00/01 未匹配的具体原因仍未确定，不能从结果强行归因于某个定位误差。

## 本机重做

在 Windows PowerShell 输入 `wsl -d Ubuntu-22.04`，再执行：

```bash
RUNTIME=/home/qzl/projects/SLAM_Author_Originals
DOCS=/mnt/d/workspace/be2/SLAM_Author_Originals
"$RUNTIME/envs/lidar/bin/python" "$DOCS/scripts/run_kitti_paper_protocol.py" \
  --runtime "$RUNTIME" --name kitti-historical-manual-01
python3 "$DOCS/scripts/verify_beautymap_table3.py" --runtime "$RUNTIME" \
  --historical-run "$RUNTIME/runs/kitti-historical-manual-01" \
  --name beautymap-table3-manual-01
```

运行名必须新建；正在运行队列时不要重复启动。历史仓库位于 `protocol-sources/dynamicmap-dufo-paper`，不切换五个现有作者 checkout。仅配置原始提取器的路径、序列和输出目录，保留 diff；源码和原始 GT／导出／评分逻辑不改。每个子任务 2 GiB RAM / 6 GiB swap、CPU 100%，本轮不做论文速度比较。
