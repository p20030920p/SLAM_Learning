# 定位自恢复接续状态

2026-10-14，目标库 `D:\workspace\be2\slam_learning_updated`。大方向保持动态环境中的鲁棒定位与 SLAM；自恢复是其中的开放问题。见[研究设计](DESIGN.zh-CN.md)、[本机测试与评分](../testing/LIVE.zh-CN.md)及[汇报稿](TALK.zh-CN.md)。

## 已交付本机现场录制

| 类别 | 现场与回放 | 实际结论 |
| --- | --- | --- |
| 静态 | [记录](../../results/reference/robot-static/record.json) | 三组同一二维 AMCL，Raw／DUFOMap RMSE 7.08 cm，BeautyMap 6.55 cm；含初始化 |
| 动态 | [记录](../../results/reference/robot-dynamic/record.json) | 三个运动箱体、六组同时定位；动态地图和静态地图控制组共享同一输入 |
| 持久变化 | [记录](../../results/reference/robot-large-change/record.json) | 沿用静态地图，本路线未诱发失效，不能当作恢复成功 |
| 走廊退化 | [记录](../../results/reference/robot-degradation/record.json) | 1 m 初值偏移；72束／240°／3.5m 观测在50个仿真秒后恢复；继续运动，约11.3 s持续收敛 |

每类有真正的 Gazebo＋RViz＋终端 MP4/GIF、另一个明确标记的测量结果回放、真值、逐更新评分 CSV、地图和哈希记录。静态／动态／走廊独立建图 A 的现场录像也保留。三维点云运动与给定位姿建图已完成；这些定位器是二维 AMCL，三维 SLAM与逐点运动畸变评测仍待开展。实体机器人按用户决定全部标明待测。

走廊首轮巡航提前结束，静止后 AMCL没有继续产生位姿更新，恢复后缺评分样本；该诊断没有用于判定失败。修正为恢复后继续运动，新录制六组各478条有效更新；验证拒绝缺少恢复后覆盖的结论。完整观测组在恢复事件前已收敛，受限组恢复前约1m误差，恢复后末帧约5.94cm。三种走廊占据图相同，本轮不支持方法排名。

## 原库重新执行与指标

| 方法 | 本机新执行 | 范围 |
| --- | --- | --- |
| DUFOMap | [记录](../../results/reference/desktop-dufomap/record.json) | 141帧 KITTI-00，实际 Windows终端＋本次最终地图回放；独立评分器，无新PCL核验 |
| BeautyMap | [记录](../../results/reference/desktop-beautymap/record.json) | 141帧 KITTI-00；与历史 KITTI-02 论文表复现分开 |
| IR-MCL | [记录](../../results/reference/desktop-ir-mcl/record.json) | 1543帧处理、1354评分，本轮5.36cm／1.06°；随机运动模型会使重复结果略变 |
| AdaM-MCL | [记录](../../results/reference/desktop-adam-mcl/record.json) | 已有2432步权重，自建128格地图，一次123更新的新推理；RMSE32.23格，不能比论文米制值 |

旧 AdaM 导出器误将原生距离再次取平方根，5.49格 RMSE与6.78格平均末帧误差撤回。[十次历史日志勘误](../../results/reference/adam-mcl/ERRATUM.md)：每次运行 RMSE均值34.82格，平均末帧47.71格，正确距离和包裹角度下仍为全局／绑架持续收敛0/10。旧记录字节保留，公开解释以勘误为准。

## 本机入口

`F:\be2演讲\实机脚本` 保存每条流程的BAT、键盘演示、自动重录、地图构建与正常停止入口；[说明](../../demo/README.md)。完整现场录像镜像在 `F:\be2演讲\屏幕实录\20261014-native-ui`；本轮现场／结果成对观看入口位于 `F:\be2演讲\本轮成片\native-ui\index.html`。

WSLg显式选择D3D12 NVIDIA之后原生 Gazebo GUI渲染正常；RViz采样器通过独立资源覆盖修正。旧“本机无法渲染 GUI”判断不再成立。其他会话的离屏录制与诊断文件仍保留，本轮主页只引用这里的真实窗口采集。

## 尚未完成的研究工作

逐因素退化实验、多个种子与独立环境重复；从动态失效开始而非仅初值偏移的恢复；固定传感器几何退化与观测策略对照；完整三维SLAM、LILocBench方法预测评估与实体机器人测试。按[测试协议](../testing/PROTOCOL.zh-CN.md)继续，不能把这次演示当作新恢复策略已经有效的证明。