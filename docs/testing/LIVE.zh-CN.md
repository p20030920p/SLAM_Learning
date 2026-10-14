# 本机现场仿真与评分

2026-10-14：实际 Windows Gazebo、RViz2、Windows Terminal 窗口；程序重新执行，窗口通过 Windows Graphics Capture 录制。三轮全向底盘来自 Sim2Real-AlgoBench，原生二维激光保留，增加独立三维激光版本。世界与驱动脚本是本地场景适配，不能称为上游论文数据。

## 现场与回放

| 场景 | 独立建图 A 现场 | 定位 B 现场 | B 结果回放 | 评分证据 |
| --- | --- | --- | --- | --- |
| 纯静态 | [MP4](../../results/reference/robot-static-mapping/execution.mp4) | [MP4](../../results/reference/robot-static/execution.mp4) | [MP4](../../results/reference/robot-static/result.mp4) | [记录](../../results/reference/robot-static/record.json) |
| 三个运动障碍物 | [MP4](../../results/reference/robot-dynamic-mapping/execution.mp4) | [MP4](../../results/reference/robot-dynamic/execution.mp4) | [MP4](../../results/reference/robot-dynamic/result.mp4) | [记录](../../results/reference/robot-dynamic/record.json) |
| 持久结构变化 | 复用静态 A | [MP4](../../results/reference/robot-large-change/execution.mp4) | [MP4](../../results/reference/robot-large-change/result.mp4) | [记录](../../results/reference/robot-large-change/record.json) |
| 走廊退化 | [MP4](../../results/reference/robot-corridor-mapping/execution.mp4) | [MP4](../../results/reference/robot-degradation/execution.mp4) | [MP4](../../results/reference/robot-degradation/result.mp4) | [记录](../../results/reference/robot-degradation/record.json) |

左为 Gazebo 自身实时渲染，右为真正的 RViz，下面是实际终端输出。视频组合三个窗口的同期采集，不包含其他桌面窗口。Gazebo 的实时因子以画面中实际值为准，不能把 15 fps 的录屏帧率当成算法吞吐。GIF 以 5 fps 采样完整 MP4 时间区间，无加速；各包的 `timing.json` 保存时长、帧数，视频全部解码检查通过。

结果回放独立标为 `MEASURED RESULT REPLAY`：读取本轮保存的原生 AMCL 更新，以 8 fps 的仿真时间展示最近一次更新。绿色是真值、蓝色是估计，下面为该方法原生更新的误差。回放不执行新的定位推理。现场视频按墙钟、回放按仿真时间，因此时长不必相同。

## 建图与算法边界

原生 `slam_toolbox` 在线生成二维地图；独立三维点云保存为建图 A。A 每仿真秒选取一帧，再均匀选择最多 60 帧，以给定的 Gazebo 传感器位姿执行原始点云堆叠、原生 DUFOMap 与原生 BeautyMap。三种输出使用共同的自由射线、0.12—1.20 m 高度带、0.05 m 栅格与一格占据膨胀，转为固定二维 AMCL 地图。自由空间来自实际扫描，未用世界模型补地图。

DUFOMap 参数为 0.1 m / d_s=0.2 / d_p=1。BeautyMap 为 range=8 m / XY=0.5 m / Z=0.2 m，使用公开作者代码；小室内地图触发了查询矩阵越界，适配仅将工作 XY 索引平移到空边界内，原始世界点保持不变，补丁、原生日志与输出保留点身份检查均记录。它属于明确披露的平台适配，不是未修改原协议的论文指标复现。地图清理点数也不能直接算静态误删率或动态移除率，本轮没有经过验证的逐点静动态真值标签。

B 使用独立的新仿真和轮速轨迹。每个方法是同一原生 Nav2 AMCL，只更换地图；动态 B 另外同时运行静态 A 地图的控制组。全部接收同一个 `/scan` 与轮速 TF；走廊另有三组接收 `/scan_degraded`。Gazebo 真值仅流入评分与显示，不给 AMCL 或巡航控制器。AMCL 使用 OmniMotionModel、500—2000 粒子、最多 60 束、相同观测与运动参数，TF 广播关闭，避免多组定位互相覆盖。RViz 中的地图与机器人 TF 对应 Raw，终端与结果回放展示所有组。

当前是二维 SLAM／定位＋给定位姿的三维点云建图，尚未完成三维 SLAM 或逐点运动畸变评测。不同配置的三维原生 SLAM与真实机器人仍按[分层测试协议](PROTOCOL.zh-CN.md)推进。

## 误差如何测算

原生 AMCL 更新保存在每个包的 `<case>-samples.csv`。独立 Gazebo `Pose_V` 选定 `omni_car`，使用消息顶层仿真时间戳；每个 AMCL 更新关联最近真值，允许时间差不超过 0.05 个仿真秒，不作 SE(2) 对齐。CSV 保留估计、真值、时间差及误差，`truth.jsonl` 保留独立真值流。

\[
e_i=\sqrt{(\hat{x}_i-x_i)^2+(\hat{y}_i-y_i)^2},\qquad
\mathrm{RMSE}_{xy}=\sqrt{\frac{1}{N}\sum_{i=1}^{N}e_i^2}.
\]

偏航差先用 `atan2(sin(差), cos(差))` 包裹到 ±π，再对角度差平方取均值开根号。首页用完整评分窗，含初始化；`metrics.json` 另报从该方法首条评分记录起 5 个仿真秒后的 RMSE、样本数及位置 P95。视频从传感器与所有定位器就绪后开始，评分流包含此前的初始更新。每次验证都会重算 CSV 几何误差与指标，并与独立真值文件核对；改变数值后仅重新写哈希不能绕过检查。

每个场景当前一次运行，同场景各方法同时接收相同输入。跨场景的路线、初值与地图不同，不能直接据此作算法普遍排名。旧主页 5.59 / 6.29 等数字来自另一机器人配置与另一组历史回放，其 21 份实际 AMCL 评分 CSV 及复算记录已保留在[历史误差审计](../../results/localization/static-dynamic/scored/audit.json)，不与本轮录像配对。

**平面位置 RMSE（cm）：包含初始化的全部原生更新，每条件一次运行。**

| 条件 | Raw + AMCL | DUFOMap + AMCL | BeautyMap + AMCL | 每组更新数 |
| --- | ---: | ---: | ---: | ---: |
| 纯静态 | 7.08 | 7.08 | 6.55 | 290 |
| 运动障碍物／动态 A 地图 | 7.31 | 7.10 | 7.28 | 291 |
| 运动障碍物／静态 A 控制 | 6.30 | 6.30 | 6.89 | 291 |
| 持久变化／旧静态 A 地图 | 6.25 | 6.25 | 6.16 | 290 |
| 走廊／完整扫描控制 | 62.64 | 62.64 | 62.64 | 478 |
| 走廊／受限→恢复 | 73.63 | 73.63 | 73.63 | 478 |

主页按方法分别展示 GIF；[录像索引](../../demo/recording-index.json)将本机文件名对应到上述各行。

## 走廊退化与恢复

走廊为两面 20 m 平行墙与端墙，地图 A 与测试 B 几何一致；初始估计 X 偏移 1.0 m、Y 偏移 0.15 m、偏航偏移 0.12 rad。其他场景初值 X 偏移 0.25 m，故走廊的全窗 RMSE不能直接与其他场景横比。

完整组始终使用 720 束、360°、12 m 扫描；压力组从相同扫描公开派生 72 束、240°、3.5 m 观测，50 个仿真秒后恢复原始观测，不添加人工测量噪声。三维激光配置保持完整。这是几何与束数／视角／距离的联合压力测试，尚未逐因素归因。

机器人恢复后继续运动，六组均保留 478 条有效原生更新，末条达到仿真 103.5 s；恢复发生在 58.6 s。压力组恢复前 RMSE 1.002 m，恢复后整个窗口 0.278 m（包含过渡过程），最后误差约 5.94 cm。持续收敛判据为位置误差 <0.1 m、绝对偏航差 <5°，覆盖 5 个仿真秒且至少八次更新；压力组约 11.3 s 达到该判据，完整组在事件前已收敛。

三种地图的占据图在这个走廊一致，因而得到相同结果。它不支持三种方法优劣排名，而提示恢复边界应考察观测约束和滤波更新触发。实际扫描的[法向覆盖诊断](../../results/reference/robot-degradation/geometry-audit.json)中，法向 Gram 矩阵小／大特征值比的中位数为完整 0.1042、受限 0.00024、恢复后 0.1048。这个局部扫描诊断不是完整 SLAM Hessian，也不是校准后的恢复概率。

首轮走廊巡航提前结束，AMCL 因运动阈值停止新位姿更新，恢复阶段没有原生评分样本；该片段保留在本机诊断目录，没有用来判断恢复失败。现在检查拒绝把缺失恢复后样本判成成功或失败。持久变化片段在本路线没有诱发失效，不能称为自恢复成功。

## 一键演示与实体测试

本机脚本：`F:\be2演讲\实机脚本`。双击静态、动态、走廊退化或持久变化 BAT。键盘在弹出的专用终端：`i/k` 前后、`j/l` 转向、`u/o` 横移、空格停止、`q` 正常结束。重录入口会自动驾驶并保存现场 MP4、ROS bag、真值与评分日志，完整媒体镜像保留在 `F:\be2演讲\屏幕实录\20261014-native-ui`。见[脚本说明](../../demo/README.md)。

| 实体场景 | 传感器层 | 指标／视频 | 状态 |
| --- | --- | --- | --- |
| 静态 | 二维／独立三维 | — | 待测 |
| 动态遮挡 | 二维／独立三维 | — | 待测 |
| 几何退化 | 二维／独立三维 | — | 待测 |
| 持久变化 | 二维／独立三维 | — | 待测 |

## 渲染与真值修复

本机 NVIDIA 4070 SUPER 在 WSLg 中需要显式 `GALLIUM_DRIVER=d3d12`，否则自动选择 llvmpipe。当前日志确认 D3D12 NVIDIA 加速，Gazebo 原生 GUI 能渲染。[相关上游问题](https://github.com/gazebosim/gz-sim/issues/2670)。RViz 地图 GLSL 的两个采样器在本机链接失败，通过独立 ament 资源覆盖给采样器设置不同 binding，保留系统安装；补丁代码随脚本记录。旧的“本机 GUI 无法渲染”判断已经被实际录屏推翻。

ROS-Gazebo 的 `Pose_V→TFMessage` 转换会丢掉用于本次评分的模型名／顶层时间戳，因此使用原生 Gazebo transport C++ 订阅。评分校验进一步检查模型身份、时间单调、匹配时间差、原生更新覆盖及持续收敛，避免画面正常而指标失真。
