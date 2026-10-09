> 历史记录（2026-10-08/09）。其中的设备状态和运行方式以当时为准；当前操作见[相机指南](../CAMERA_GUIDE.zh-CN.md)与[雷达指南](../LIDAR_GUIDE.zh-CN.md)。保留失败及复现命令。

# 第三轮：运动预测对照与 BeautyMap 室内边界

本轮继续在 `Personal-Learning-Physical` 中工作，主分支固定为 `354b02d69ccc90304174f6d36010d25043d739ca`，未修改、未合并。新增算法实验使用原先用户确认固定的 60 秒录制；新的 4 秒检查只说明当前收流和视野，不作为新的静止真值。

## KISS-ICP：错误速度预测会放大漂移

同一份官方 SDK 点云、同样 250 次观测、范围 0.2–20 m、体素 0.08 m、阈值 0.3 m、两线程，均不使用 IMU 或去畸变。

| 输入／处理 | 最大相对平移／转角 | 正确解读 |
| --- | --- | --- |
| 真实静止录制，原 KISS 常速度外推 | 41.54 cm／179.71°，展开 yaw 约两圈 | 原基线失败，仍保留 |
| 同一真实录制，每步只将 `last_delta` 重置单位矩阵 | **13.23 cm／8.23°** | 关闭速度外推的诊断控制，仍失败；不是原样 KISS 的新通过成绩 |
| 将第一份真实点云重复输入 250 次，原常速度外推 | 约数值零／0° | 合成输入自洽检查，不能代替实物定位验收 |

第二项只取消 `last_pose @ last_delta` 中的速度外推，不重置 `last_pose`，不强迫输出为零。结果支持错误的运动预测在放大本段漂移；仍有 13 cm／8°误差，说明不能把速度预测当作全部原因。重复同一帧的检查通过，也不足以证明真实场景、扫描覆盖或标定正常。

[关闭速度外推的实际回放](../../data/kiss-zero-delta-control-01/preview.mp4)标为 **ZERO-DELTA CONTROL**。固定时正常预期仍是轨迹靠近原点、地图稳定；绿色圆为 5 cm 项目目标，本次轨迹仍越界。状态“有位姿输出”不等于配准正确。没有回环节点或外部 ATE／RPE 真值。

## BeautyMap：原主分支入口失败，局部边界对照可执行

复用 DUFOMap 已核验的同一批 40 次实测观测及其 PCD 哈希，合计 545,371 点；固定传感器单位位姿来自用户此前的物理固定确认。输入只有 XYZ、单位米和 VIEWPOINT；旧接口所需的 `gt_cloud.pcd` 只是无标签原始点云累积，**不是地面真值**。

主分支适配器和配置均通过 `git show` 读取固定提交，BeautyMap 作者提交为 `98bce4a97db96ddd0d5342e31425c7679f58ba2e`。未在主分支、作者固定缓存或环境中写入补丁。

原参数 `dis_range=40, xy_resolution=1.0, h_res=0.5` 下，局部地图只有 10×10 格，查询窗口却有 40×40 格。第一帧在 `generate_query_binary_tree` 读取 ROI 时出现 `index 15 is out of bounds ... size 10`，**原样主分支实物接口未通过**。完整失败和日志保留在 [失败记录](../../evidence/main-beautymap-original-failed.json)、[worker 日志文本](../../evidence/main-beautymap-original-worker.txt)。日志文本只移除行尾空格；本机原始 `worker.log` 的哈希另保留在失败记录中。

增加一个显式诊断选项，在每次运行的作者副本中将 XY 空白域向四周各扩 21 格，内部索引作相同整数格平移，网格变为 52×52。**没有补造点、没有改变查询参数或高度阈值**。该对照仅用于固定原点处于实测 XY 边界内的会话；它不是传感器轨迹可能超出已观测地图时的通用边界方案。

对照处理 40/40 观测、没有跳帧，输出 **532,472 个有限 XYZ 点**，worker 约 1.86 s。输入／输出点数比 **97.63%只是描述性计数，不是静态保留率 SA**。原日志给出 12,937 个候选删除索引，包含重复索引；最终点数差及输入坐标缺失数均为 **12,899**，不能称作“正确清除了 12,899 个动态点”。

[真实输入／输出／缺失坐标对比图](../../data/main-beautymap-padded-control-01/comparison.png)中，前两列按高度着色，第三列红色表示输入 XYZ 未出现在输出中。正常静态结构应保留，动态拖影应减少；本段没有受控动态事件或点级标注，红色区域可能包含误删，不能判为正确动态清除。SA／DA 继续留空。

另做一个明确标为合成的回归：100 m 平面、固定结构、前两帧存在后两帧消失的合成柱子，传感器固定在 `(50,50,1)`，40 m 查询窗口完全处于地图内部。原实现与扩域副本均输出 40,180 点，**输出文件 SHA-256 完全一致**，并都精确匹配已知静态几何、清除 40 个合成动态输入点。这证明此用例的内部行为未改变，不代替 KITTI 正式回归或实物事件验收。

## 当前设备与下一段场景

- D435 四路仍约 29.98 fps，无帧号缺失；emitter 原值仍为 1。当前中央深度约 **0.211 m**、全画面有效比例约 **24.17%**，近前景与亮屏仍占据视野。[当前实际画面](../../data/scene-check-round3-01/preview.png)。这不是尺量精度或静止噪声结果。
- L2 新录 4 秒，860 线包、997 IMU 包、256,056 有效点，CRC／序号缺失为 0。起始 817 字节在首个包头之前，属于开始接收时的部分包；原字节保留。原始设备时间比例仍约 2:1，没有进入 Point-LIO／融合验收。

需要将相机前方的黑色立柱、白布等近物移出视野，镜头朝 1–3 m 墙角／家具；L2 底座平稳、周围无遮挡。收到新的固定准备确认后，再采 60 秒静止数据，保持本轮参数复测，并做独立尺量。移动、转动和回环测试需要实际动作与起止标记，不能用合成点云或固定单位位姿替代。

## 重现与合入边界

在 WSL 的本分支目录中运行，所有输出用新路径：

```bash
OPENBLAS_NUM_THREADS=2 .cache/kiss-venv/bin/python scripts/run_kiss_baseline.py \
  data/l2-official-static-50 --prediction zero_delta_control --output data/kiss-zero-new
OPENBLAS_NUM_THREADS=2 .cache/kiss-venv/bin/python scripts/run_kiss_baseline.py \
  data/l2-official-static-50 --repeat-first-cloud-control --output data/kiss-repeat-new
python3 scripts/render_odometry_video.py data/l2-official-static-50 data/kiss-zero-new

# 不带控制选项先保留原样失败；加选项只测试本次运行的作者副本。
OPENBLAS_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv/bin/python scripts/run_main_beautymap.py \
  data/main-dufomap-hardware-smoke-01 --main-repo /mnt/d/workspace/be2/SLAM_Learning \
  --upstream /home/qzl/projects/SLAM_Learning/.cache/upstream/beautymap \
  --fixed-sensor-session --pad-small-map-control --output data/beautymap-control-new
python3 scripts/render_dufomap_smoke.py data/beautymap-control-new
OPENBLAS_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv/bin/python scripts/verify_beautymap_padding.py \
  --frozen-main data/main-beautymap-hardware-smoke-01/main-source \
  --upstream /home/qzl/projects/SLAM_Learning/.cache/upstream/beautymap --output data/padding-test-new
```

本次不把控制实验的通过项替换原失败。BeautyMap 的空域扩展需要更全面的边界条件和原 KITTI 回归后才适合考虑集成；KISS 修改也须先在独立场景和运动会话验证。ConceptGraphs／HOV-SG 的实物 RGB-D 适配、外参和正式质量指标仍待完成。后续以 main 建集成分支，筛选移植、运行原测试、审阅差异；**本轮没有 merge 或 push**。

轻量记录与补丁进入 `evidence/`；视频、PCD、原始数据和作者副本留本机 `data/`。前两轮报告：[首轮](BASELINE_RESULTS.zh-CN.md)、[第二轮](DIAGNOSTICS_ROUND2.zh-CN.md)。
