# 摔落后检查、弱光对照与双设备并行测试（2026-10-09）

**相机基础功能初检通过，尚不能证明摔落后测距精度完全无损；L2 已恢复有效点云和 IMU。** 已完成四路原始回放、双目几何抽查、投射器开—关—开，以及两组双设备同时运行和 RViz 录像。所有原始数据、室内画面留在本机 `data/`；[数字证据](../evidence/postfall-dual-lowlight-20261009.json)随分支保存。

本轮照明条件来自操作者“关灯”的说明，画面仍有屏幕/键盘等光源，没有照度计。摔落后没有新的“已固定”确认，也没有尺量距离、共同标定或刚性安装验证；因此下面的位姿范围不是静止误差、ATE/RPE 或融合精度。

## 1. 相机检查到了什么

实际设备仍为 **D435、USB 3.2、无 IMU**，固件 5.17.0.10。未更新固件、写入新标定或执行自校准。

| 检查 | 实测 | 判读与剩余限制 |
| --- | --- | --- |
| RGB、深度、左右 IR | 六份原始录像均经 SDK 逐传感器回放，数量与 SQLite 原始图像记录一致；所有现场采集帧均能找回 | 四路、原始记录及回放链路可用 |
| 稳态收流 | 三段 25 秒对照去除前 2 秒后，四路约 29.98 Hz，最大传感器间隔约 34–38 ms，无序号缺失或倒退 | 达到本项目稳态 29–31 fps、无 >100 ms 停顿的初检目标 |
| 启动过程 | 初探深度最大间隔 322 ms；B 段 282 ms；C 段深度/IR 最大约 1.288 s，均在前 2 秒内，随后恢复 | 保留启动停顿，不把整段平均帧率写成稳定 30 Hz；仍需后续重复冷启动检查 |
| 双目几何 | 12 对 IR、4,835 个通用几何 RANSAC 内点；垂直偏差中位数 0.171 px、p95 0.489 px；左右配对时间差为 0 | 低于本项目筛查参考 p95 <1 px，暂未发现明显垂直失准；重复散斑、局部饱和、匹配选择和近似平面场景限制结论 |
| 存储标定 | 与摔落前内参/外参完全一致 | 仅说明存储值未变，不能证明镜头和基线物理位置未变 |
| RGB 暗与 IR 饱和 | 初探样本 RGB 灰度均值 18.6/255；左右 IR >250 的像素约 17.3%/19.8% | 关灯后 RGB 暗、噪声大符合预期；近处 IR 过曝和深度黑洞仍需调整距离/曝光后复查 |
| 绝对测距、坏点、整幅空间精度 | 无独立参考，未完成 | 不能宣称“相机所有功能和精度都正常” |

抽查命令先在 **Windows PowerShell** 执行，一次一行：

```powershell
Set-Location -LiteralPath D:\workspace\be2\Personal-Learning-Physical
.venv\Scripts\python.exe scripts\verify_camera_recording.py data\postfall-dark-probe-20261009-022442\camera\raw.db3 --output data\postfall-dark-probe-20261009-022442\camera\playback-recheck.json
.venv\Scripts\python.exe scripts\export_stereo.py data\postfall-dark-probe-20261009-022442\camera\raw.db3 --stride 15 --output data\postfall-stereo-recheck
.venv\Scripts\python.exe scripts\audit_camera_health.py data\postfall-dark-probe-20261009-022442\camera --stereo data\postfall-stereo-recheck --reference-capture data\static-20261008-221334\camera\capture.json --output data\postfall-health-recheck
```

输出目录需用新名字，避免覆盖证据。`stereo-matches.png` 画绿色水平参考线和真实匹配连线；大量持续倾斜的连线、p95 明显增大值得复查，但低纹理时“匹配不足”不直接等于损坏。该脚本用 SIFT 双向比值匹配，再估计不强制水平的基础矩阵；没有预先按垂直误差筛掉不合格点。

## 2. 弱光投射器开—关—开，L2 始终开启

三段各 25 秒，投射器临时设定后恢复原值 1；激光功率没有改动。全画面有效比例和中心 80×80 ROI 读数只描述当前场景，没有距离真值。

| 段 | 相机投射器 | 深度有效像素中位比例 | 中心深度中位读数 | 中心中位读数的时间标准差 | L2 线包/IMU 每秒 |
| --- | --- | --- | --- | --- | --- |
| A | 开 | 47.55% | 0.301 m | 1.09 mm | 215.44 / 249.93 |
| B | 关 | 25.99% | 0.301 m | 5.48 mm | 215.43 / 250.01 |
| C | 再开 | 47.38% | 0.302 m | 1.02 mm | 215.43 / 249.98 |

**预期画面：** 开时 IR 上有散斑，弱纹理物体较容易获得深度；关时散斑消失、深度黑洞增多；再开后恢复。本轮表现符合该预期。RGB 本身不会因 IR 投射器开启就变成明亮彩色图像；玻璃、亮屏、过近或反光区域的黑洞也不自动算损坏。主动双目依赖投射纹理的原理可查 [RealSense 官方投射器说明](https://dev.realsenseai.com/docs/projectors/)。

L2 三段均收到约 150 万个有效点，CRC 错误、序号缺失和倒退均为 0。官方 SDK 原生解码 A 段 5,386 线包、1,496,926 点，与本地解析一致；跳过启动后导出 99 份 50 线组点云。投射器变化时点云收流仍正常，但没有 L2 关闭对照、受控反射目标和运动参考，**不能据此证明两设备完全没有光学干扰**。

本机重录示例（同时采两台，输出自动加时间戳）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\capture_pair.ps1 -Seconds 25 -Session lowlight-on-a -Emitter on
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\capture_pair.ps1 -Seconds 25 -Session lowlight-off-b -Emitter off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\capture_pair.ps1 -Seconds 25 -Session lowlight-on-c -Emitter on
```

## 3. 只有两台同时开启才能检查的项目

**已做：并行占用硬件、同时收流、算法共存、分别录像、同一 Windows 主机接收时间关联。** 相机 domain 83/端口 17635，雷达 domain 84/端口 17636；四份 H.264 RViz 录像均通过编码/帧数检查，已抽查真实画面。两个定位域各有自己的原点，不能把 `/odom` 当作同一个坐标系。

| 并行组（各 40 秒） | 实际 ROS 输入 | 位姿输出与状态 | 相对首有效位姿最大范围，非真值误差 |
| --- | --- | --- | --- |
| RGB-D + L2 ICP | 8.11 / 4.32 Hz | 有效覆盖 97.51% / 98.26%；两者 LOST 0 | 7.80 mm、1.50° / 45.71 cm、12.85° |
| IR stereo + L2 KISS | 8.17 / 4.31 Hz | stereo 有效覆盖 98.14%、LOST 0；KISS 输出覆盖 100%，没有可验证的 LOST/有效跟踪状态 | 0.99 mm、0.18° / 36.60 cm、179.86° |

两组主机报告的采集窗口分别重叠约 36.76 秒和 36.78 秒。两次都是独立采集，不是相同原始输入的公平算法排名。严格覆盖 99% 目标仍未达到；KISS 输出 100% 不代表正确。雷达两段分别有 1/2 次 CRC 拒绝和 1/2 个点包序号缺失，点包缺失率约 0.012%/0.023%，小于项目初期 0.1% 参考，但不写成“零错误”。

**如何看视频：**

| 内容 | 应看到什么，怎样算正常 | 本轮画面 |
| --- | --- | --- |
| 相机 RGB-D | RGB/深度更新、`TRACKING` 状态，姿态变化时点云按估计位姿摆放；若确实固定，轨迹应聚在原点 | 暗 RGB 和深度可见，持续输出；点云按 RGB 着色所以也偏暗，当前近景在 5 m 视图中显得小 |
| 相机 IR stereo | 左右 IR 提供特征与视差，轨迹/状态实时更新；没有 IMU 辅助 | 已输出较小位姿范围。勾选 `Left IR/Right IR` 可看到实际算法图像；默认 RGB 窗格不是双目算法输入 |
| L2 ICP | 墙面/地面点云刷新，约 4.3 组/s；固定时墙面不应随轨迹持续游走 | 有点云，但位姿范围很大。即使绿色 `TRACKING` 也不能判定位精度合格 |
| L2 KISS | 显示 `POSE OUTPUT; QUALITY UNVERIFIED`；固定时不能出现旋转的墙面/大幅轨迹 | 出现近 180° 估计转动，继续保留为算法风险，不能用作融合或主分支地图真值 |

弱光下为了看清几何，可以把 RViz `Current cloud → Color Transformer` 从 `RGB8` 切为 `FlatColor` 或 `AxisColor`，并滚轮拉近；这是显示着色，不能当成算法改善。默认录像保持真实 RGB 着色。

本机视频路径如下，GitHub 不包含室内录像：

```text
D:\workspace\be2\Personal-Learning-Physical\data\live-camera-20261009-023303-779\rviz-live.mp4   RGB-D
D:\workspace\be2\Personal-Learning-Physical\data\live-lidar-20261009-023307-581\rviz-live.mp4    ICP
D:\workspace\be2\Personal-Learning-Physical\data\live-camera-20261009-023416-505\rviz-live.mp4   IR stereo
D:\workspace\be2\Personal-Learning-Physical\data\live-lidar-20261009-023420-197\rviz-live.mp4    KISS
```

要复现并同时实时看效果，开两个 **Windows PowerShell** 窗口。第一窗：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm stereo -SessionType preview -Seconds 60 -Record -Video
```

第一窗出现 RViz 后，在第二窗执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar -Algorithm kiss -SessionType preview -Seconds 60 -Record -Video
```

这样也避免两个视频录制器同时选择同一个尚未分配的虚拟显示。需要另一组时，等两窗完全结束，再分别改 `rgbd` 和 `icp`。无人值守可以各加 `-NoGui`，仍录独立 RViz 视频。同一传感器不要同时开两次。

接收时间关联示例：

```powershell
Set-Location -LiteralPath D:\workspace\be2\Personal-Learning-Physical
.venv\Scripts\python.exe scripts\audit_pair.py data\dark-on-qpc-a-20261009-023004 --output data\pair-time-recheck
```

三段共同稳态区间各约 22.3 秒，深度帧匹配最近 L2 **线包接收时刻**的绝对差 p95 约 2.20–2.22 ms。按 50 线组末端接收时间匹配时，p95 约 110 ms。后者与每组约 0.23 秒的跨度相关，说明最近一条线很近不等于整个点云同步。

新版原始采集记录 Windows Python 3.12 的 `perf_counter`/`QueryPerformanceCounter`，分辨率记录为 100 ns；这只是时钟分辨率，不是传感器时间精度。第一份使用较粗 `GetTickCount64` 的试录保留在本机，新审核会拒绝将其混入精细关联。跨进程计时依据 [Python 3.12 官方说明](https://docs.python.org/3.12/library/time.html#time.perf_counter)；没有拿 Windows/WSL 两套时钟直接相减。

## 4. 下一步及预期目标

1. **相机冷启动与测距复验。** 后续条件允许时重复启动、改用不饱和的哑光平面/多距离独立尺量。稳态目标仍为 29–31 fps、无 >100 ms 停顿；双目筛查 p95 <1 px 仅作异常排查；测距偏差目标 <max(3 cm, 距离×2%)。本轮没有尺量，继续记为未完成。
2. **雷达定位问题先独立解决。** 用确认固定、不同方向墙面的同一份原始数据，比较 18/50 线聚合、ICP/KISS 及参考点云配准残差。预期固定轨迹聚集、墙面不游走；初期目标 <5 cm、<2°。当前几十厘米/近 180° 的范围不能接受为可靠定位来源，但本轮没有固定真值，不据此直接诊断雷达硬件坏了。
3. **跨设备先验证时间、IMU、外参和刚性安装。** 解释 L2 主机/设备时间比例约 2，核实 IMU 单位/轴/偏置；硬件共同事件/参考方法支持后再谈同步残差。两台固定在同一刚性支架、标定外参、检查共同场景重投影后，才接 LIO 或视觉—雷达融合。预期融合后墙面重合、移动时无双层重影，弱光下视觉退化时轨迹仍连续；目前这些功能未实现。
4. **再推进主分支。** 现有 ConceptGraphs/HOV-SG 8/8 原生输入检查、DUFOMap/BeautyMap 接口结果保留。新的移动地图需要已验收位姿、参考数据与任务标签；不把本轮 L2 漂移轨迹或未经确认的单位位姿当真值。语义地图应看到跨帧一致的物体实例及可追踪标签，动态地图评估需要 SA/DA 等标签，当前均未验收。
5. **分支整理。** 仅提交采集计时/投射器支持、两份可复用审核工具和指南/数字证据。原始媒体与临时调度脚本保持忽略；主分支不修改、不合并。将来通过门槛后按[主分支适配指南](MAIN_INTEGRATION.zh-CN.md)做选择性合入和回归。
