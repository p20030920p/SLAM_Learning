# 本机现场仿真与评分

2026-10-14：实际 Windows Gazebo、RViz2、Windows Terminal 窗口；程序重新执行，窗口通过 Windows Graphics Capture 录制。三轮全向底盘来自 Sim2Real-AlgoBench，原生二维激光保留，增加独立三维激光版本。世界与驱动脚本是本地场景适配，不能称为上游论文数据。

## 现场与回放

### 纯静态

[Raw live RViz](../../results/reference/robot-live-static/executions/raw.mp4) · [DUFOMap live RViz](../../results/reference/robot-live-static/executions/dufomap.mp4) · [BeautyMap live RViz](../../results/reference/robot-live-static/executions/beautymap.mp4) · [record](../../results/reference/robot-live-static/record.json)

[独立建图 A](../../results/reference/robot-static-mapping/execution.mp4)

### 运动障碍物

[Raw live RViz](../../results/reference/robot-live-dynamic/executions/raw.mp4) · [DUFOMap live RViz](../../results/reference/robot-live-dynamic/executions/dufomap.mp4) · [BeautyMap live RViz](../../results/reference/robot-live-dynamic/executions/beautymap.mp4) · [record](../../results/reference/robot-live-dynamic/record.json)

[独立建图 A](../../results/reference/robot-dynamic-mapping/execution.mp4)

### 持久变化

[Raw live RViz](../../results/reference/robot-live-large-change/executions/raw.mp4) · [DUFOMap live RViz](../../results/reference/robot-live-large-change/executions/dufomap.mp4) · [BeautyMap live RViz](../../results/reference/robot-live-large-change/executions/beautymap.mp4) · [record](../../results/reference/robot-live-large-change/record.json)

[独立建图 A](../../results/reference/robot-static-mapping/execution.mp4)

### 走廊退化

[Raw live RViz](../../results/reference/robot-live-degradation/executions/degraded_raw.mp4) · [DUFOMap live RViz](../../results/reference/robot-live-degradation/executions/degraded_dufomap.mp4) · [BeautyMap live RViz](../../results/reference/robot-live-degradation/executions/degraded_beautymap.mp4) · [record](../../results/reference/robot-live-degradation/record.json)

[独立建图 A](../../results/reference/robot-corridor-mapping/execution.mp4)

左为 Gazebo 自身实时渲染，右为真正的 RViz，下面是实际终端输出。视频组合三个窗口的同期采集，不包含其他桌面窗口。Gazebo 的实时因子以画面中实际值为准，不能把 15 fps 的录屏帧率当成算法吞吐。GIF 以 5 fps 采样完整 MP4 时间区间，无加速；各包的 `timing.json` 保存时长、帧数，视频全部解码检查通过。

结果回放独立标为 `MEASURED RESULT REPLAY`：读取本轮保存的原生 AMCL 更新，以 8 fps 的仿真时间展示最近一次更新。绿色是真值、蓝色是估计，下面为该方法原生更新的误差。回放不执行新的定位推理。现场视频按墙钟、回放按仿真时间，因此时长不必相同。

## 建图与算法边界

原生 `slam_toolbox` 在线生成二维地图；独立三维点云保存为建图 A。A 每仿真秒选取一帧，再均匀选择最多 60 帧，以给定的 Gazebo 传感器位姿执行原始点云堆叠、原生 DUFOMap 与原生 BeautyMap。三种输出使用共同的自由射线、0.12—1.20 m 高度带、0.05 m 栅格与一格占据膨胀，转为固定二维 AMCL 地图。自由空间来自实际扫描，未用世界模型补地图。

DUFOMap 参数为 0.1 m / d_s=0.2 / d_p=1。BeautyMap 为 range=8 m / XY=0.5 m / Z=0.2 m，使用公开作者代码；小室内地图触发了查询矩阵越界，适配仅将工作 XY 索引平移到空边界内，原始世界点保持不变，补丁、原生日志与输出保留点身份检查均记录。它属于明确披露的平台适配，不是未修改原协议的论文指标复现。地图清理点数也不能直接算静态误删率或动态移除率，本轮没有经过验证的逐点静动态真值标签。

B 使用独立的新仿真和轮速轨迹。每个方法是同一原生 Nav2 AMCL，只更换地图；动态 B 另外同时运行静态 A 地图的控制组。全部接收同一个 `/scan` 与轮速 TF；走廊另有三组接收 `/scan_degraded`。Gazebo 真值仅流入评分与显示，不给 AMCL 或巡航控制器。AMCL 使用 OmniMotionModel、500—2000 粒子、最多 60 束、相同观测与运动参数，TF 广播关闭，避免多组定位互相覆盖。三种方法分别用独立 RViz 进程显示自己的地图、原生位姿／粒子及隔离的 TF；被动显示转发不改变 AMCL 输入。每段现场视频录制该方法的窗口。动态场景的静态地图控制组及走廊的完整扫描控制组也运行并保存原生评分。

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
| 纯静态 | 7.28 | 7.28 | 6.89 | 290 |
| 动态地图／运动障碍物 | 7.41 | 7.35 | 7.14 | 288 |
| 静态地图控制／同一动态输入 | 7.08 | 7.08 | 6.78 | 288 |
| 旧地图／持久变化 | 6.84 | 6.84 | 6.39 | 290 |
| 完整扫描控制 | 53.46 | 53.46 | 53.46 | 476 |
| 受限→恢复扫描 | 75.66 | 75.66 | 75.66 | 476 |

主页按方法分别展示 GIF；[录像索引](../../demo/recording-index.json)将本机文件名对应到上述各行。

## 走廊退化与恢复

匹配的两面 20 m 平行墙走廊。初始信念 X 偏移 1 m、Y 偏移 0.15 m、偏航偏移 0.12 rad；其他场景 X 偏移 0.25 m。完整控制组接收 720 束／360°／12 m；压力组从同一扫描派生 72 束／240°／3.5 m，持续 50 个仿真秒后恢复完整观测。独立三维激光始终完整，不输入 AMCL。

本次每组保留 476 条原生更新至仿真 103.3 s，恢复发生在 58.5 s。压力组恢复前 RMSE 为 0.975 m，恢复后整个过渡窗为 0.441 m，末帧误差 6.62 cm。恢复后约 31.3 s 开始持续收敛，随后覆盖 5 个仿真秒、至少八次更新，位置误差 <0.1 m、绝对偏航差 <5°。

三种投影后的走廊地图相同，因此结果相同。此前 478 更新／11.3 s 的运行仍[保留归档](../../results/reference/robot-degradation/record.json)，不与新现场录像配对。本次为 31.3 s，说明不能用单次运行宣称恢复稳定性；两次都不是实体绑架。本次持久变化路线也未诱发失效。

[历史法向覆盖诊断](../../results/reference/robot-degradation/geometry-audit.json)对应上一轮，而非本次新运行；局部 Gram 比不是完整 SLAM Hessian 或校准后的恢复概率。

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

## 原库实时状态显示

作者执行过程中原子写出当前状态，RViz 读取本次新状态；验证原生帧号／序号、状态哈希和执行时间窗。IR-MCL 本次出现不足一秒的 WSL 墙钟校时，故以帧序为因果依据，并给墙钟留 2 s 容差；后续录制另保存单调时钟。显示稀疏采样和观察器开销明确披露，原生推理与地图清理决策不变。

DUFOMap、BeautyMap 的最终 `cleaned.pcd` SHA256 与此前原生执行逐字节一致：[DUFOMap 前次](../../results/reference/desktop-dufomap/native-run/record.json)／[本次](../../results/reference/desktop-live-dufomap/native-run/record.json)，[BeautyMap 前次](../../results/reference/desktop-beautymap/native-run/record.json)／[本次](../../results/reference/desktop-live-beautymap/native-run/record.json)。
