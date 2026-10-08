# 官方解码、第二条雷达定位基线与主分支接口实测

继续使用用户确认传感器固定的原始 60 秒录制；后续短暂场景检查不作为静止真值。两台设备收流已确认，**定位尚不能整体验收通过**。实际相机为 D435、没有 IMU。主分支未修改、未合并。

## 实际结果与正常预期

静止定位的项目目标为最大平移偏离 5 cm、相对转角 2°，不是厂家规格。无独立位姿参考，以下不是 ATE 或测距精度。

| 实际运行 | 本次结果 | 视频正常预期与判断 |
| --- | --- | --- |
| RTAB-Map Stereo，上轮有效结果 | 576/576 输出，lost=0；最大 **0.286 mm / 0.093°**；计算 p95 41.45 ms | 轨迹靠近起点、稀疏局部地图稳定。本段静止通过，仍须运动验证 |
| RTAB-Map ICP，**官方原生 XYZ**，50 线聚合 | 248/250 输出，lost=0；最大 **20.00 cm / 13.40°**；计算 p95 193.27 ms，输入周期约 231.99 ms | 固定时轨迹与地图应稳定。本次明显错位；TRACKING 不等于正确 |
| KISS-ICP **1.3.0**，同一官方点云 | 250/250 有限位姿；最大 **41.54 cm / 179.71°**；计算中位 42.22 ms、p95 111.13 ms | 固定时不应持续转图、轨迹绕行。本次失败；API 未提供 lost 状态，不能填 lost=0 |
| 主分支 DUFOMap **1.1.1** 原适配器 | 40 次约 1 Hz 观测，545,371 输入点→541,723 有限输出点；原生执行约 0.835 s | 输入／输出应坐标一致；本次外观接近。只证明接口能执行，没有动态清除质量成绩 |

KISS 的 179.71°为标准旋转角距，范围为 0–180°；展开 yaw 后实际持续旋转约两圈，拟合 **12.27°/s**、RMSE 1.35°。处理速度足够快，位置仍错误。耗时是当前有其他任务负载时的离线观测，不是实时硬件延迟或空载性能。

- [双目静止输出视频](../data/rtabmap-stereo-static-02/preview.mp4)：左右 IR、状态、轨迹；右下为最终稀疏局部地图参考，没有回环节点。
- [KISS-ICP 失败视频](../data/kiss-official-static-50-01/preview.mp4)：原始点云、估计轨迹与依估计位姿累积的近期地图同屏，绿色圆为 5 cm 目标。标注为保存输出回放、质量未验证。
- [配准诊断图](../data/l2-registration-control-02/diagnostic.png)：展开 yaw、平移、参考扫描距离和局部法向分布。
- [DUFOMap 输入／输出图](../data/main-dufomap-hardware-smoke-01/comparison.png)：共享坐标范围、按高度着色；固定会话没有受控动态事件。

## 解码差异的因果对照

此前 20 个跨会话抽样包的 0.1 mm 实现一致性检查失败，XYZ 最大分量差 0.1274 mm；原证据 `sdk-geometry-20packets.json` 保留。

本轮只把 Python 角度初始化与逐点累加改为 SDK 相同的 float32 顺序，其余计算仍为原双精度。相同 20 包、相同门槛全部通过，最大差降至 **0.000954 mm**，点数、强度、ring 相同。这解释了主要数值差异；没有放宽门槛，也不意味着硬件具有微米测距精度。默认 Python 解码保持原样，旧结果可追溯。

随后将整段 **12,932 个 CRC 合格线包**交给官方原生 `parseFromPacketToPointCloud`，得到 **3,525,525 点**，与 Python 点数完全一致。保持 50 线分组、主机接收时刻和 RTAB-Map 参数重跑，仍漂移约 20 cm／13.4°。不能把约 0.127 mm 的数值差当作厘米级漂移的主要解释。

SDK 固定提交 `0e3c51f512e6b8ff60b8c32f160b412cb48445c2`；UART SHA-256 `c79cc1fd24c7e01566416a2867f603229e9a948c32ad26304da3188b817c1749`。`clouds.json` 保存解码器二进制哈希及计数。后续输入校验加固另做全量输出字节一致性检查，见 `native-decoder-hardening-control.json`。

## 目前能确认的配准问题

KISS 在本分支独立 `.cache/kiss-venv` 中运行，冻结依赖为 `requirements-kiss-wsl.txt`。范围 0.2–20 m、体素 0.08 m、初始自适应阈值 0.3 m、两线程；没有使用 IMU 或去畸变。未用尚未验收的设备时间补偿运动。输出初始化标记不是算法估计协方差。

另抽取 27 份扫描，与第一份有效扫描比较：固定位置直接叠加时，最近邻距离中位数在各样本间的中位值约 **5.62 cm**；施加 KISS 位姿后约 **34.76 cm**。这是单向原始点云对照，不是 KISS 内部残差或 ATE；支持“本次估计在错误对齐”，并非仅指标表达异常。

局部平面筛选后，约 58.6%的支持法向接近 Z 轴，也存在其他方向结构。该分布与扫描纹理值得排查，**不足以证明唯一原因是几何退化或雷达损坏**。下一次改变可控场景、保持参数复测，不反复调到某一段变绿。

L2 原始设备时间仍约以主机一半速度增长。SDK 主机时间路径不提供硬件同步。Point-LIO／双设备融合仍须先验时间、IMU 单位／轴／振动与刚性外参。

## 主分支实际执行范围

`run_main_dufomap.py` 从固定提交 `354b02d69ccc90304174f6d36010d25043d739ca` 用 `git show` 读取四个必要文件，存入运行目录并记录各 blob SHA-256。调用真实 `dufomap_run` 与原参数，没有改写原 KITTI 评测入口。

40 份不同观测跨约 39 秒，XYZ binary PCD、单位米、VIEWPOINT 单位姿态。`T_world_sensor=I` 来自用户确认固定的明确假设，没有使用失败的雷达轨迹，也没有当作定位成绩。只读取现有 DUFOMap 环境；主分支代码、原数据集和原结果未覆盖。脚本现要求显式 `--fixed-sensor-session`，避免误把移动记录当固定。加上该输入约束后复跑约 0.760 s，输出 PCD SHA-256 与首次完全一致，见 `main-dufomap-fixed-session-recheck.json`。

输出／输入点数比 **99.33%只是描述性计数，不是 SA**。无点级静／动态标注和事件时间，SA／DA 为空。BeautyMap、ConceptGraphs、HOV-SG 的本次实物适配和正式指标仍待做。预期画面、事件、指标分母和合入流程见 [主分支计划](MAIN_INTEGRATION.zh-CN.md)。

## 相机设置与下一步

短暂关闭 IR emitter 时 SDK 读回 0，退出后已恢复原值 **1**，恢复检查 true，原激光功率 150。短检查仍有近前景和过亮屏幕，未重新确认静止，其深度波动不能当静止噪声。

结束前另做 5 秒双设备收流：L2 1076 线包、1249 IMU 包，CRC／序号缺失均为 0。相机四路均收到，深度启动有约 285 ms 间隔，整段平均 28.41 fps；从首次交付后 2 秒起四路恢复约 29.98 fps、无序号缺失。保留完整启动统计，不把短检查称为新的静止验收。

这次旧回放检查漏读 1 帧深度，原失败保存在 `round2-camera-playback-v1-incomplete.json`。只读 SQLite 显示原文件有深度 138、RGB 138、两路 IR 各 142 帧。改为预先暂停、配置非实时、打开全部录制传感器后用单路回调读取：全部图像消息与 SQLite 数量一致、每个实时采集帧号都保留。IR 多出的 4 帧是未进入同步帧组的启动帧；此前的同步帧组检查不能等同于逐条原始记录审核。

新检查也回归了原 60 秒文件：原始深度 1790、两路 IR 各 1791、RGB 1787，全部 SDK 回调与 SQLite 匹配；实时采集深度 1788／IR 1787／RGB 1787 的每个帧号均存在。原文件哈希不变，定位实验已跳过约前 2 秒、输入未改。证据为 `round2-camera-raw-playback-v2.json`、`static-camera-raw-playback-v2.json`、`round2-receipt.json`。实现采用官方 [传感器回调接口](https://github.com/realsenseai/librealsense/blob/master/examples/sensor-control/api_how_to.h)，没有重新打开物理相机做离线回放。

将相机移开近物，朝向约 1–3 m 有纹理墙角／家具；L2 底座稳定、周围无遮挡，能看到多个方向平面。先固定 60 秒验深度 ROI、尺量测距与定位，再做 2 m 慢平移、90°转动和 5–10 m 小闭环。视觉移动另做 emitter 开／关对照，不能把投射光斑当已验证的自然运动特征。

本分支是 orphan 历史；将来从 main 创建集成分支，筛选移植模块、跑原测试和实物验收、审阅 PR 后由用户决定。**本次没有 merge、没有 push。**

## 重现新增实验

WSL Ubuntu 22.04，在本分支目录中运行；输出须用新目录：

```bash
g++ -O2 -std=c++17 scripts/decode_sdk_lines.cpp \
  -I.cache/unilidar_sdk2/unitree_lidar_sdk/include -o .cache/decode_sdk_lines_checked
python3 scripts/export_l2_clouds.py data/static-20261008-221334/l2 \
  --lines 50 --sdk-decoder .cache/decode_sdk_lines_checked --output data/l2-official-new
source /opt/ros/humble/setup.bash
python3 scripts/run_odometry_baseline.py data/l2-official-new --mode lidar --output data/rtab-icp-new

# 新机器用独立环境安装冻结依赖，不覆盖主分支环境。
python3 -m venv .cache/kiss-venv-new
.cache/kiss-venv-new/bin/python -m pip install -r requirements-kiss-wsl.txt
.cache/kiss-venv-new/bin/python scripts/run_kiss_baseline.py data/l2-official-new --output data/kiss-new
python3 scripts/render_odometry_video.py data/l2-official-new data/kiss-new
OPENBLAS_NUM_THREADS=2 python3 scripts/audit_l2_registration.py data/l2-official-new data/kiss-new --output data/geometry-new

# 本机现有 DUFOMap 环境；实物输出全部在本分支。
/home/qzl/projects/SLAM_Learning/.venv/bin/python scripts/run_main_dufomap.py data/l2-official-new \
  --main-repo /mnt/d/workspace/be2/SLAM_Learning --fixed-sensor-session --output data/dufomap-new
python3 scripts/render_dufomap_smoke.py data/dufomap-new
```

绘图使用 WSL 系统 Python 的 NumPy、SciPy、Matplotlib、OpenCV 与 ffmpeg；KISS 在自己的环境运行。轻量证据位于 `evidence/`：`sdk-float-angle-control.json`、`rtabmap-icp-official-static.json`、`kiss-icp-official-static.json`、`l2-registration-control.json`、`main-dufomap-hardware-smoke.json`、`camera-emitter-off-capture.json`。视频、图、PCD、原始录制留本机 `data/`，不提交。

接口依据：[固定 Unitree SDK2](https://github.com/unitreerobotics/unilidar_sdk2/tree/0e3c51f512e6b8ff60b8c32f160b412cb48445c2)、[KISS-ICP 官方仓库](https://github.com/PRBonn/kiss-icp)。实际版本与参数以保存证据为准。
