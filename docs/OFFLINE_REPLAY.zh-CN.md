# 无人值守相机回放：录像、指标与送帧性能

[English](OFFLINE_REPLAY.md) | 中文

本轮不需要人员重新摆放、拿相机走动或量距离。使用已有原始录像自动执行，保留失败和所有输出；尺量、移动和回环精度仍未完成；自动过程不要求操作者配合。

## 1. 2026-10-09 本次结果

同一原始 SHA-256 `35cfdca0dc208f65a004b00fc3f8d9e7d142042099753d8a0ec2a8c4c8c9047b` 导出 500 个 SDK 对齐 RGB-D 观测，约源录像第 3–53 秒。相机由操作者声明固定，背景存在人员活动；因此不是完全静态场景。

RGB、深度保留原始约 10 ms 配对时差，ROS 离线回放将已配对的两帧统一盖彩色时间戳，采用 exact sync；这不等于硬件同步，也不同于实时入口的近似同步。

| 对照 | 实际送帧 / 时间 | 有效且非 LOST 覆盖 | 最大平移 / 转角偏离 | 严格数字门槛 |
| --- | --- | --- | --- | --- |
| Windows 盘读图，原 bytes 赋值，请求 10 Hz | 49.9 s 数据用 96.5 s 回放，包含最多 10 s 等待；未测独立送帧 Hz | 494/500 = **98.8%** | **0.894 mm / 0.159°** | 未通过覆盖门槛 |
| Windows 盘读图，原 bytes 赋值，请求 5 Hz | **5.001 Hz**，约 50.0 s | 249/250 = **99.6%** | **0.797 mm / 0.135°** | 数字在目标内 |
| Linux 同一输入副本，原 bytes 赋值，请求 10 Hz | **7.091 Hz**，送帧约 70.5 s | 499/500 = **99.8%** | **1.832 mm / 0.293°** | 稳定性数字在目标内，但送帧未达 10 Hz，末端落后约 20.6 s |
| Linux 同一输入副本，改用类型为 B 的字节数组，请求 10 Hz | **10.000 Hz**，送帧约 49.91 s，最大送帧迟到 15.3 ms | 494/500 = **98.8%** | **0.951 mm / 0.165°** | 送帧改善，但严格覆盖仍未通过 |

四段收到的状态中 LOST 均为 0。最后一段少了第 365–369 号输入的输出，另有 1 个初始高协方差位姿；没有删除有效尖峰，也没有把丢输出算作 TRACKING。原因尚未完全定位，主机其他研究任务并未隔离。每次运行分开保留，不能由单次顺序对照断言存储、负载或背景活动是唯一原因。

本次离线严格门槛是最大偏离 <5 cm、转角 <2°、LOST=0、有效且非 LOST 覆盖 ≥99%。正常运动计划中 >95% 是另一项初期可用性目标，不能混用门槛让失败变通过。即使数字通过，因动态背景存在，`clean_static_acceptance` 仍为空；没有 ATE/RPE、独立测距准确率或移动轨迹精度。

## 2. 修复了什么，怎样验证

ROS Humble 本机生成的 Image/PointCloud2 `data` setter 接收普通 `bytes` 时，会逐元素检查类型和取值；接收 `array('B', payload)` 则走它原生支持的数组路径。已更新实时桥接与离线发布器，图像编码、形状、点云字段与内容不变。

独立确定性消息检查覆盖 mono8、BGR、float32 深度和 180,000 点 XYZI 云：反序列化后的全部字段与 payload 均相同。合成微测中 RGB setter 中位时间约 55 ms→0.031 ms，float32 深度约 79 ms→0.20 ms；这只衡量本机消息赋值，不代表整个相机/算法有相同比例加速。

最初检查草稿曾把整个 CDR 封装原样比较并失败一次，保留在 `data/ros-payload-check-20261009-01`；最终逐字段和 payload 检查在 `...-02` 通过，并记录本次完整 CDR 是否也相同。

Linux 副本有 1,504 个文件，约 354 MB，逐个核验导出哈希；只复制 manifest 列出的输入，不复制历史运行结果。控制副本补丁与数字见[证据](../evidence/rgbd-rate-and-payload-20261009.json)。

改动后的 **15 秒实机 RGB-D 预览**：119 个输入、117 个原生输出，ROS 输入约 **8.19 Hz**，有效位姿覆盖 116/119 = **97.48%**，LOST=0；四路原始回放与 SQLite 帧数一致，实时使用帧均在原始文件中。保存 19.5 秒 H.264 RViz 录像，含启动时间。

新画面朝向/光照与旧固定段不同，未重新确认物理静止，记作 `preview`，不评精度；8.19 Hz 也不是保证的长期帧率或 30 Hz 算法运行。

双目 20 观测、ICP 10 观测另外做了入口回归，确认同样的数组发布仍有原生输出；短段初始化比例大，且 ICP 偏离仍超过目标，不把入口通过写成定位质量通过。

## 3. 看视频应该看到什么

本机目录 `D:\workspace\be2\Personal-Learning-Physical\data\rgbd-replay-input-20261009-01`：

- `odom-typed-10hz/preview.mp4`：约 50 s 的真实输入和离线算法输出，左上 RGB、右上对齐深度，中间跟踪/缺输出状态，下方轨迹与最终稀疏局部地图。固定相机的轨迹应接近原点，看起来像小点是正常的；毫米级差异见 `rate-comparison.png`。
- `odom-5hz/preview.mp4`：约 50 s 的低采样对照；并非把视频慢放两倍。
- 其余两段的 `preview.mp4` 保留性能控制与未通过记录。视频按原始观测时间播放，不按执行墙钟耗时播放，因此不能只看视频时长判断实时速度。
- 实机新录像为 `data/live-camera-20261009-021748-685/rviz-live.mp4`；实时 RViz 默认观察距离较大，近景点云可能很小，放大观察即可。录制视图独立于手动打开的 RViz。

视频中背景人员移动仍保留。稀疏局部地图不是 ConceptGraphs/HOV-SG 对象地图，也没有自动识别纸巾或饮料瓶。所有视频均 H.264、无音频，已用 ffprobe 核验；室内媒体仅留本机，不上传 GitHub。

## 4. 复现新的回放流程

先按 Win+X 打开 Windows PowerShell，确认 `PS ...>`，执行一整行：

```powershell
D:\workspace\be2\Personal-Learning-Physical\.venv\Scripts\python.exe D:\workspace\be2\Personal-Learning-Physical\scripts\export_rgbd.py D:\workspace\be2\Personal-Learning-Physical\data\live-camera-20261009-014327-492\raw.db3 --fixed-sensor-session --frames 500 --interval 0.1 --output D:\workspace\be2\Personal-Learning-Physical\data\manual-rate-01
```

仍在 PowerShell 进入 WSL：

```powershell
wsl -d Ubuntu-22.04
```

看到 `qzl@...$` 后依次执行，每块一条命令：

```bash
cd /mnt/d/workspace/be2/Personal-Learning-Physical
```

```bash
source /opt/ros/humble/setup.bash
```

```bash
python3 scripts/stage_rgbd.py data/manual-rate-01 --output /home/qzl/.cache/personal-learning-physical/manual-rate-01
```

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 scripts/run_odometry_baseline.py /home/qzl/.cache/personal-learning-physical/manual-rate-01 --mode rgbd --stride 1 --domain 85 --session-type stationary --output data/manual-rate-01/odom-10hz
```

```bash
python3 scripts/render_odometry_video.py /home/qzl/.cache/personal-learning-physical/manual-rate-01 data/manual-rate-01/odom-10hz
```

要测约 5 Hz，用 `--stride 2`，输出换 `odom-5hz`，再用同一渲染命令替换结果目录。各目录必须是新的；代码拒绝覆盖旧视频。`--speed` 是加速回放而不是采样率，本次保持 1，不用它假装 10 Hz 输入。

查看 `result.json` 的实际 `actual_publish_hz`、`valid_tracking_input_fraction`、`lost_status_fraction`、偏离及门槛，结合 `publish-timing.json`、`status.json`、`poses.json`。`time_estimation_s` 是原生计算时间，`latency_s` 是本机发布起点到结果回调，均不等于完整传感器端到端延迟。

## 5. 接下来的无人值守范围

先分析连续缺输出的具体时段、同步及队列日志；需要新对照时冻结同一输入和参数，只改变一个因素。主分支语义方向已完成[真实 RGB-D 加载检查](RGBD_MAIN_INPUT.zh-CN.md)，待计算资源适合时再接掩码、特征和对象地图；不挤占其他现有作业，不把语义模型未执行写成通过。L2 当前没有有效包，先保留 UART 失败证据，不盲目反复重连或改设备模式。

无独立距离和动作参考时，测距准确率、手持移动、回环、两传感器融合均保持未完成。所有改动继续只在个人分支，主分支未修改、未合并。
