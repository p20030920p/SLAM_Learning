> 历史记录（2026-10-08/09）。其中的设备状态和运行方式以当时为准；当前操作见[相机指南](../CAMERA_GUIDE.zh-CN.md)与[雷达指南](../LIDAR_GUIDE.zh-CN.md)。保留失败及复现命令。

# 2026-10-08：实际数据上的首轮定位基线

**后续更新：** [第二轮诊断](DIAGNOSTICS_ROUND2.zh-CN.md)已完成角度 float 对照、整段官方原生解码、KISS-ICP 静止基线及主分支 DUFOMap 接口实测。本文件保留首轮结果。

设备接收已经确认，定位按算法单独验收。相机实际型号是 **D435，没有 IMU**；L2 通过 USB 转串口收流。此次使用用户确认固定后的 60 秒会话，跳过约前 2 秒，得到约 58 秒有效算法输入。没有尺量距离、独立位姿真值或运动会话；不报告 ATE／RPE、移动测距精度或回环成功。

## 实测与预期

| 实际运行 | 静止时正常预期 | 本次结果 | 判断 |
| --- | --- | --- | --- |
| RTAB-Map Stereo F2M，左右 IR，约 10 Hz | 轨迹停留在起点附近、稀疏局部地图稳定；项目目标最大偏离 <5 cm、转角 <2°，状态和位姿覆盖 ≥99%，不丢失 | 57.54 秒，576/576 状态和位姿；lost=0；最大偏离 **0.286 mm**、最大转角 **0.093°**；计算 p95 **41.45 ms**，软件回调延迟 p95 **196.68 ms** | **本次静止门槛通过**；不是运动定位精度，更不是毫米级测量精度 |
| RTAB-Map ICP F2M，L2 18 线聚合，约 12 Hz | 同样应保持静止；点云与地图不能持续转动、错位 | 2.42 秒短测，18/30 输出；计算 p95 **105.73 ms** 大于约 83.53 ms 输入周期；最大偏离 **11.41 cm**、转角 **5.55°** | **失败**；默认 18 线软件聚合不等于完整周向扫描 |
| RTAB-Map ICP F2M，L2 50 线聚合，约 4.31 Hz | 增大几何覆盖后仍须满足静止门槛，不以状态灯判断正确 | 57.76 秒，250/250 状态和位姿；lost=0；计算 p95 **167.98 ms** 小于约 231.99 ms 周期；最大偏离 **19.05 cm**、转角 **16.11°** | **静止精度失败，吞吐通过**；不能拿它给主分支提供已验证的运动位姿 |

平移数字定义为 `max ||p_i - p_first_registered||`，转角为相对第一份有效注册位姿的四元数角距。每次初始化的第一份高协方差位姿单独计数、不加入稳定性统计；后续状态丢失及输出缺口另计。5 cm／2°是项目工程目标，不是厂家规格。没有强行把固定会话的位姿设为零再宣称算法通过。

视觉输入有过曝、近物和 IR 投射光斑，左右图像大部分立体对应被算法拒绝，但仍有中位 94 个内点。静止时投射纹理也能稳定，**移动相机后未必是可重复的场景特征**，因此必须补移动测试。建议对移动视觉基线增加 emitter 开／关的独立对照，记录并恢复原设置。

L2 两次 ICP 的体素、法向、对应距离等配置保持一致；50 线聚合依据实测 215.53 线/s 和约 229 ms 下电机周期选择，约覆盖一个周期。此调整修复了吞吐不足，却没有修复静止漂移。尚未证明失败原因；需要无遮挡、具有多个方向墙面和箱子的场景复测，并核查扫描覆盖、近物、自身遮挡、几何退化及配准配置。不能据此直接判定雷达损坏，也不能把持续输出 TRACKING 当作正常精度。

## 看视频时应如何判断

- [双目完整输出回放](../../data/rtabmap-stereo-static-02/preview.mp4)：上方为真实左右 IR；下方为算法状态、内点、耗时和轨迹。轨迹应贴近原点。右下是**最终稀疏局部地图的参考投影**，不是逐时刻地图，也不是稠密房间。
- [L2 ICP 失败输出回放](../../data/rtabmap-icp-static-50/preview-v2.mp4)：上方为实际原始点云投影，下方是估计位姿轨迹与依位姿累积的近期点云。绿色圆圈表示 5 cm 目标；固定设备的轨迹离开原点、地图错位，说明失败，即使状态仍为 TRACKING。

这些视频明确标注 **SAVED ALGORITHM OUTPUT REPLAY**，来自真实算法输出；没有运行回环节点。视频、原始数据和室内画面只留本机 `data/`，不加入提交。

## L2 时间与 IMU 的新增核查

原始 UART 时钟仍约是主机时间的一半，未改设备时钟或固件。官方 SDK2 的 `use_system_timestamp=true` 可使用主机解析时刻：按原 `receive.csv` 节奏回放时，1000 个 IMU 样本的 SDK 时间跨度 **3.9951005 s**、独立主机跨度 **3.9951003 s**，一致。若不按原节奏而快速灌入，时间会压缩为解析耗时，因此不能把非实时回放的主机时间当采集时间。

此选项是可用的软件时间路径，**没有修复原始设备时钟，也没有提供相机—雷达硬件同步**。ICP 此次使用已记录的主机接收时间，不使用 IMU、不去畸变；原设备时刻和逐点 dt 另存。移动时不能把全部时间字段乘 2，也不能把主机解析时间命名为采样真值。Point-LIO 仍待逐点时间、IMU 单位／轴／偏置、刚性外参验收。

静止 IMU 的 wx/wy 频谱峰约 **4.36 Hz**，接近包内下电机周期换算的 **4.3615 Hz**，并有约 8.72 Hz 分量。这支持振动排查方向，但不证明因果。短暂 standby 诊断中，停机后连 IMU 包也停止，不能完成“仅停转保留 IMU”的对照。发送 start 后 IMU 先恢复，12 秒内未见点云；之后独立 10 秒接收检查确认点云恢复、CRC 和序号缺失均为 0。原诊断的 `restore_unverified` 保留，未伪改为成功；脚本恢复检查窗口现延长至 45 秒。

## 可复现入口

Windows 导出真实录制：

```powershell
.venv\Scripts\python.exe scripts\export_stereo.py data\static-20261008-221334\camera\raw.db3 --output data\stereo-new
.venv\Scripts\python.exe scripts\export_l2_clouds.py data\static-20261008-221334\l2 --lines 50 --output data\l2-clouds-new
```

WSL Ubuntu 22.04 中，已安装 ROS2 Humble / RTAB-Map **0.23.7**；无须重新安装或修改主分支环境：

```bash
source /opt/ros/humble/setup.bash
cd /mnt/d/workspace/be2/Personal-Learning-Physical
python3 scripts/run_odometry_baseline.py data/stereo-new --output data/stereo-run-new
python3 scripts/run_odometry_baseline.py data/l2-clouds-new --mode lidar --output data/icp-run-new
python3 scripts/render_odometry_video.py data/stereo-new data/stereo-run-new
python3 scripts/render_odometry_video.py data/l2-clouds-new data/icp-run-new
```

所有输出目录要求是新的。ROS_DOMAIN_ID 默认 83、仅本机通信；顺序运行，避免与同域节点混用。每次保留请求参数、节点全量参数、节点日志、逐帧状态和位姿。相机标定来自录制中的 SDK 左右外参，baseline=0.050043 m；右相机投影矩阵 `P[3]=-fx×baseline`。本次追踪的是左相机 optical 坐标系，没有虚构底盘外参。

检查脚本 v1 曾提前结束位姿接收，得到 576 状态但仅 485 位姿，并错误放行。该次结果已作废，见 `evidence/observer-v1-rejection.json`。v2 独立接收、结束时等待两路输出并检查时间戳覆盖，重跑收齐 576/576。所有首次结果仍在本机。主机同时有其他任务运行，软件延迟是当次负载下的观测；未证明 30 Hz 相机全速或真实采集到输出的端到端性能。

轻量证据：`evidence/rtabmap-stereo-static.json`、`rtabmap-stereo-parameters.yaml`、`rtabmap-icp-18line-short.json`、`rtabmap-icp-50line-static.json`、`rtabmap-icp-parameters.yaml`、`sdk-paced-system-clock.json`、`imu-frequency-resampled.json`。几何原始 UART SHA-256 与录制 SHA-256 记录于结果中。

补充核查：跨 60 秒均匀抽取 20 个线包，Python 与官方 SDK 的点数、强度、ring 全部一致，逐点 dt 最大差约 7.3 ns；XYZ 最大分量差 **0.1274 mm**。新加的 **0.1 mm 严格实现一致性门槛未通过**，原结果保存在 `evidence/sdk-geometry-20packets.json`，未通过放宽门槛改写成成功。Python 使用双精度角度索引、SDK 使用逐步 float 累加；首轮当时尚未完成因果验证。后续同一门槛的 float 角度对照将最大差降至 **0.000954 mm**，见第二轮报告；实现差值不是实际测距误差。扩展检查也限定了早先单包 4.53 μm 对照的适用范围。

结束前另录 5 秒双设备收流，见 `evidence/final-receipt.json`：相机四路约 29.98 fps、无帧号缺失；L2 1076 线包、1249 IMU 包，CRC、序号缺失、时间倒退均为 0。相机原始录制再次全量回放并匹配计数。此短段只验收仍能接收，不用于静止精度。

下一阶段：相机移开约 15 cm 的近物，朝向 1–3 m 纹理场景；L2 底座固定且周围无遮挡，视野包含墙角和箱子。先重做受控静止／测距，再由用户按指引完成 2 m 平移、90°转动、5–10 m 回路。运动前端通过后，按 `MAIN_INTEGRATION.zh-CN.md` 扩展主分支实物测试；第二轮 DUFOMap 已有接口执行成绩，其余核心和正式实物指标仍待测试。本任务没有合并。

接口依据：[RTAB-Map odometry 官方说明](https://github.com/introlab/rtabmap_ros/tree/ros2/rtabmap_odom)、[Unitree SDK2 固定版本](https://github.com/unitreerobotics/unilidar_sdk2/tree/0e3c51f512e6b8ff60b8c32f160b412cb48445c2)。实际可复现参数以本机已安装版本的保存文件为准。
