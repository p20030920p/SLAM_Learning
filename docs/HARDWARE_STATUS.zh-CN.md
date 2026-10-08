# 本机实物验证状态：2026-10-08

本机工作目录 `D:\workspace\be2\Personal-Learning-Physical`，分支 `Personal-Learning-Physical`。已有静止定位基线和主分支 DUFOMap 实物接口执行成绩；尚无移动／回环／地图算法正式质量验收成绩。最新诊断见 [第二轮报告](DIAGNOSTICS_ROUND2.zh-CN.md)。

## 已通过

- 实际设备枚举：RealSense D435（不是已证实的 D435i）、USB 3.2；L2 版本查询返回 YS-L2，硬件 2.2.1.1、固件 2.8.8.1。
- CH343 实体串口访问：绕开实体与虚拟 COM3 同名问题，无需删除虚拟串口或修改网卡配置。
- 四路相机采集：640×480、30 fps。最新 60 秒深度 1788 帧、左 IR 1787、右 IR 1787、RGB 1787，约 29.98 fps，各路无序号缺失或时间倒退。
- 原始相机录制回放 v2：SDK 单路回调覆盖 SQLite 全部图像消息，原 60 秒深度 1790、两路 IR 各 1791、RGB 1787；所有实时采集帧号都被保留，原始记录另含启动帧。此前帧数匹配只指同步帧组检查。文件为 SDK 2.58.4 的 `.db3`。
- 最新 60 秒 L2 点云与 IMU：12,932 线包、15,000 IMU 包、3,525,525 有效点；主机约 215.53 线包/s、250.00 IMU 包/s；CRC 错误、序号缺失、重复、时间倒退均为 0。
- 串口接收整改：从同线程解码／画图改成独立线程收字节，并请求 1 MiB 驱动接收缓冲。整改前 30 秒并发测试有 14 次 CRC 拒绝；整改后本次 60 秒为 0。这是一次观测到的改善，尚不是长时间可靠性保证。
- 独立解码核对：固定官方 SDK2 提交 `0e3c51f512e6b8ff60b8c32f160b412cb48445c2`，原生库能经 Linux 伪终端读取已保存 UART；官方内联 XYZ 与 Python 对应包最大分量差约 4.53 μm。该差值是实现一致性，不能当实际测距精度。
- 软件核查：Python 编译、依赖一致性、CRC 错误包拒绝与跨读取块重同步检查通过。
- RTAB-Map Stereo 静止基线：约 58 秒，576/576 状态和位姿；lost=0；最大偏离 0.286 mm、转角 0.093°。通过本次静止目标；不能当移动定位精度。详见 [报告与视频](BASELINE_RESULTS.zh-CN.md)。
- L2 SDK 主机时间路径：保留原接收节奏回放，1000 IMU 的 SDK／主机跨度都约 3.995100 秒。此路径使用主机解析时间，不提供硬件同步。
- 结束前新做 5 秒双设备收流复核：相机约 29.98 fps；L2 1076 线包、1249 IMU 包；无 CRC／帧号或包序号缺失，原始相机回放计数匹配，见 `evidence/final-receipt.json`。
- 扩展解码数值对照：SDK 同样 float 角度累加控制下，20 包严格 0.1 mm 门槛通过，最大差 0.000954 mm；整段原生 SDK 得到 3,525,525 点，点数一致。
- 主分支 DUFOMap 原适配器用 40 份实际 L2 观测运行成功，输出 541,723 个有限 XYZ 点；只有接口检查通过，SA／DA 没有标注依据，仍为空。
- 相机短暂 emitter 关闭对照后已恢复原值 1，SDK 恢复检查 true。
- 本轮结束前 5 秒仍收到两设备：L2 CRC／序号缺失为 0，相机原始记录经 v2 全量核验。深度启动间隔约 285 ms 保留记录，首次交付后 2 秒的四路约 29.98 fps；不是新增静止精度结果。旧回放漏读 1 帧的失败保留，见第二轮报告。

## 尚未通过或不具备条件

1. **L2 时间尺度。** 60 秒主机时间对应约 30 秒原始设备时间；线包／IMU 拟合比例分别约 1.9986621／1.9986627。原生 SDK 保留同样的原始值。尚未确认时间字段／逐点 time／固件版本的正确处理方法，未修改固件、设备时钟或原始时间。Point-LIO 与跨设备融合暂不验收。
2. **相机 IMU。** SDK 只有 Stereo Module 和 RGB Camera，没有运动传感器。可用 RGB-D／Stereo；视觉惯性模式不能以这台相机单独完成。
3. **相机摆位。** 用户确认固定后的中央深度约 0.154 m，深度全画面有效比例约 20.0%。近前景和明亮反射占据大量视野，需移开近物，将目标置于约 1–3 m再做受控测距与定位；当前低有效率不直接判为驱动坏或硬件坏。
4. **IMU 噪声和参考。** 固定会话前 10 秒估计陀螺仪均值，后 50 秒独立检查：均值约 `[0.00062, 0.00015, 0.00680]`，各轴标准差约 `[0.1205, 0.3485, 0.0640]`，减去前 10 秒均值后的模长 p95 约 0.6343，均保留 SDK 原数值约定。加速度平均向量模长约 9.4007。均值接近零但波动较大；单位、轴、振动、重力标定未完成，未将这些数据当位置真值。
5. **L2 ICP 静止精度失败。** 50 线原生 SDK 对照仍偏离 20.00 cm／13.40°；独立 KISS-ICP 偏离 41.54 cm／179.71°、展开 yaw 约 12.27°/s 持续转动。保留失败视频／配置，排查场景几何、扫描覆盖与配准；还不能归因于硬件故障。ORB-SLAM3、Point-LIO 与主分支其余三个核心尚未完成本次实物运行；设备收流不算定位准确。
6. **参考轨迹和标定。** 没有独立真值、尺量目标和相机—雷达外参；ATE／RPE 尚不具备计算条件。
7. **解码对照的适用范围。** 原 20 包 XYZ 最大差 0.1274 mm 的失败保留；同一门槛的 float 角度控制已解释数值差异。原生 SDK 点云上的定位仍失败，不能把实现一致性推广为实物测距或定位精度保证。

官方 Unitree Point-LIO 的 [L2 配置](https://github.com/unitreerobotics/point_lio_unilidar/blob/main/config/unilidar_l2.yaml)使用 `imu_time_inte: 0.004`；本机实测主机接收约 250 Hz 与该配置周期相符。该对应关系不能消除原始设备时间尺度异常，也不能证明同步已完成。

## 本机证据

- `evidence/static-camera-capture.json`：最新相机型号、内外参、帧统计和原始文件 SHA-256。
- `evidence/static-camera-playback.json`：最新原始录制完整回放核对。
- `evidence/static-l2-capture.json`：最新雷达版本、接收质量、时间比例、UART SHA-256。
- `evidence/static-audit.json`：固定会话的独立离线审核与 IMU 分段检查。
- `evidence/sdk-decoder-crosscheck.json`、`evidence/official-sdk-replay.json`：官方实现对照范围。
- `evidence/concurrent-link.json`：接收整改前的并发结果；保留失败，不覆盖为成功。
- `data/static-20261008-221334/`：本机原始录制和视频，Git 忽略。
- `evidence/rtabmap-stereo-static.json`、`rtabmap-icp-50line-static.json`：首轮算法实测；全量配置另存相应 YAML。
- `evidence/observer-v1-rejection.json`：首次视觉测试脚本的接收缺陷和作废说明，修复后已重跑。
- `evidence/sdk-paced-system-clock.json`、`imu-frequency-resampled.json`、`l2-standby-diagnostic.json`、`l2-restored-capture.json`：时间、频谱与已恢复收流的诊断证据。

分支已从空白初始化；主分支未修改、未合并。以后以 main 为基底筛选移植硬件模块和轻量证据，详细步骤见 `MAIN_INTEGRATION.zh-CN.md`。
