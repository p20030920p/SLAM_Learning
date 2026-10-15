| 导航 | 入口 |
| --- | --- |
| 语言 | [English](MINIMAL.md) / [中文](MINIMAL.zh-CN.md) |
| 主文 | [English](../README.md) / [中文](HOME.zh-CN.md) |
| 查看方式 | 点击GIF／MP4；保留成功、无效和失败记录；单轮不排名 |

| 实验／设置 | 输入和地图 | 指标／范围 |
| --- | --- | --- |
| 原库清理 | KITTI等作者数据；原库参数见主文 | DUFO／Beauty点级DA／SA；不与仿真排名 |
| 原生二维SRRG | 四场景；二维雷达＋里程计，无三维雷达；已知起点 | 残影删除／静态覆盖；动态42.31%／99.51%；独立定位B待测 |
| 旧二维投影＋AMCL | 四场景；三维清理图投影，定位使用二维扫描 | 动态格DA／静态格SA；另报XY RMSE，含初始化 |
| 三维清理＋GICP | 四场景；三维扫描，给定位姿建图A；独立定位B无真值输入 | 源点DA／SA；另报XYZ RMSE，含初始化；走廊覆盖不同不排名 |
| 历史定位假设 | 五场景×2D／3D＋深度；五原型同帧；地图冻结 | 只测定位／恢复，不是动态建图；细化回放无新仿真 |
| 时长／重复 | 逐记录为准；假设普通场景90s、走廊120s；前50s限制雷达后恢复 | 仿真秒；主要场景每条件一轮，不能推出稳定排名 |
| 地图与定位区分 | DA=动态删除，SA=静态保留；无动态样本N/A | 清理率不是几何误差；更干净不保证定位更准 |
| SRRG退化检查 | 11.1s跟踪重置；11.5s持续偏差>20cm；57.6s恢复扫描 | 仿真时刻；MP4首告警约4.6s；非独立测得地图坍塌时刻 |

| 器材参数 | 实际设置 |
| --- | --- |
| 平台 | Sim2Real全向底盘；ROS 2 Jazzy＋Gazebo Harmonic；理想仿真传感器，实体测试待做 |
| 底盘结构 | 三个全向轮，间隔120°；轮半径0.06364 m；轮心到车体中心0.1934 m；碰撞圆柱半径0.20 m、高0.14 m |
| 质量／接触 | base_link为0.953513 kg，每轮0.20 kg；滚子以球形接触和方向摩擦近似，μ=0.02／2.0 |
| 二维雷达 | 通用gpu_lidar，720束、360°、10 Hz、0.08–12 m；相对base_link安装位置(0.06, 0, 0.16) m |
| 三维雷达 | 通用gpu_lidar，水平720×垂直16束、360°×30°（±15°）、10 Hz、0.08–12 m；安装位置(0, 0, 0.30) m |
| RGB相机 | 640×480、15 Hz、水平视场80°；安装位置(0.18, 0, 0.12) m |
| 深度假设组 | 实际渲染depth_camera：320×240、10 Hz、水平80°、0.25–4 m；未加实体噪声模型；原生二维／SRRG组移除三维雷达 |
| 地图表示 | 三维源点；旧二维投影为0.05 m格、世界Z=0.12–1.20 m、一格占据膨胀；SRRG使用独立的原生二维地图及覆盖容差 |

| 地图／算法参数 | 设置 |
| --- | --- |
| DUFOMap | voxel=0.10m; d_s=0.20m; d_p=1; threads=2 |
| BeautyMap (Gazebo) | XY=0.50m; Z=0.20m; range=8m; offline |
| SRRG | native local projective merge ON; graph merge OFF in four main runs; 10cm support / 15cm coverage tolerance |
| AMCL / GICP | frozen-map B; nearest truth ≤0.05 simulation seconds; no trajectory fitting |
| Native source | [URDF](../config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf) / [map processing](../src/scripts/presentation/build_maps.py) / [SRRG](papers/srrg_mapper2d.zh-CN.md) |

| 实验／地图 | GIF / MP4 | 指标效果 |
| --- | --- | --- |
| 简单实物测试 | [GIF](../docs/media/hardware/d435-input.gif) / [MP4](../docs/media/hardware/d435-input.mp4) | 实机传感器录制；清理指标不适用 |
| docs/media/hardware/d435.gif | [GIF](../docs/media/hardware/d435.gif) / [MP4](../docs/media/hardware/d435.mp4) | 实机传感器录制；清理指标不适用 |
| 简单实物测试 | [GIF](../docs/media/hardware/l2.gif) / [MP4](../docs/media/hardware/l2.mp4) | 实机传感器录制；清理指标不适用 |
| results/localization/self-recovery/S1_static.gif | [GIF](../results/localization/self-recovery/S1_static.gif) / [MP4](../results/localization/self-recovery/S1_static.mp4) | 早期场景演示；未绑定地图清理评分，保留原片 |
| results/localization/self-recovery/S2_dynamic.gif | [GIF](../results/localization/self-recovery/S2_dynamic.gif) / [MP4](../results/localization/self-recovery/S2_dynamic.mp4) | 早期场景演示；未绑定地图清理评分，保留原片 |
| results/localization/self-recovery/S3_large_change.gif | [GIF](../results/localization/self-recovery/S3_large_change.gif) / [MP4](../results/localization/self-recovery/S3_large_change.mp4) | 早期场景演示；未绑定地图清理评分，保留原片 |
| results/localization/self-recovery/S4_degradation.gif | [GIF](../results/localization/self-recovery/S4_degradation.gif) / [MP4](../results/localization/self-recovery/S4_degradation.mp4) | 早期场景演示；未绑定地图清理评分，保留原片 |
| results/localization/static-dynamic/clean-map-dynamic-test.gif | [GIF](../results/localization/static-dynamic/clean-map-dynamic-test.gif) / [MP4](../results/localization/static-dynamic/clean-map-dynamic-test.mp4) | 早期场景演示；未绑定地图清理评分，保留原片 |
| results/localization/static-dynamic/dynamic-lidar.gif | [GIF](../results/localization/static-dynamic/dynamic-lidar.gif) / [MP4](../results/localization/static-dynamic/dynamic-lidar.mp4) | 早期场景演示；未绑定地图清理评分，保留原片 |
| results/localization/static-dynamic/dynamic-rgbd.gif | [GIF](../results/localization/static-dynamic/dynamic-rgbd.gif) / [MP4](../results/localization/static-dynamic/dynamic-rgbd.mp4) | 早期场景演示；未绑定地图清理评分，保留原片 |
| results/localization/static-dynamic/static.gif | [GIF](../results/localization/static-dynamic/static.gif) / [MP4](../results/localization/static-dynamic/static.mp4) | 早期场景演示；未绑定地图清理评分，保留原片 |
| AdaM-MCL 评测会话录制 | [GIF](../results/reference/adam-mcl/media/preview.gif) | 历史10轮定位RMSE均值34.82格（已勘误）；清理指标不适用 |
| BeautyMap 已保存结果回放 | [GIF](../results/reference/beautymap/media/preview.gif) | 动态点删除 98.34%；静态点保留 96.95% |
| beautymap / media/replay/preview.gif | [GIF](../results/reference/beautymap/media/replay/preview.gif) / [MP4](../results/reference/beautymap/media/replay/replay.mp4) | 动态点删除 98.34%；静态点保留 96.95% |
| desktop-adam-mcl：现场执行 | [GIF](../results/reference/desktop-adam-mcl/execution.gif) / [MP4](../results/reference/desktop-adam-mcl/execution.mp4) | 定位RMSE 32.23格；清理指标不适用 |
| desktop-adam-mcl：本次结果回放 | [GIF](../results/reference/desktop-adam-mcl/result.gif) / [MP4](../results/reference/desktop-adam-mcl/result.mp4) | 定位RMSE 32.23格；清理指标不适用 |
| desktop-beautymap：现场执行 | [GIF](../results/reference/desktop-beautymap/execution.gif) / [MP4](../results/reference/desktop-beautymap/execution.mp4) | 传感器／建图过程演示；未评分 |
| desktop-beautymap：本次结果回放 | [GIF](../results/reference/desktop-beautymap/result.gif) / [MP4](../results/reference/desktop-beautymap/result.mp4) | 传感器／建图过程演示；未评分 |
| desktop-dufomap：现场执行 | [GIF](../results/reference/desktop-dufomap/execution.gif) / [MP4](../results/reference/desktop-dufomap/execution.mp4) | 传感器／建图过程演示；未评分 |
| desktop-dufomap：本次结果回放 | [GIF](../results/reference/desktop-dufomap/result.gif) / [MP4](../results/reference/desktop-dufomap/result.mp4) | 传感器／建图过程演示；未评分 |
| desktop-ir-mcl：现场执行 | [GIF](../results/reference/desktop-ir-mcl/execution.gif) / [MP4](../results/reference/desktop-ir-mcl/execution.mp4) | 传感器／建图过程演示；未评分 |
| desktop-ir-mcl：本次结果回放 | [GIF](../results/reference/desktop-ir-mcl/result.gif) / [MP4](../results/reference/desktop-ir-mcl/result.mp4) | 传感器／建图过程演示；未评分 |
| beautymap：原生计算与实时 RViz | [GIF](../results/reference/desktop-live-beautymap/execution.gif) / [MP4](../results/reference/desktop-live-beautymap/execution.mp4) | 动态点删除 98.34%；静态点保留 96.95% |
| dufomap：原生计算与实时 RViz | [GIF](../results/reference/desktop-live-dufomap/execution.gif) / [MP4](../results/reference/desktop-live-dufomap/execution.mp4) | 动态点删除 98.70%；静态点保留 97.98% |
| ir-mcl：原生计算与实时 RViz | [GIF](../results/reference/desktop-live-ir-mcl/execution.gif) / [MP4](../results/reference/desktop-live-ir-mcl/execution.mp4) | 定位RMSE 5.31cm / 1.07°；清理指标不适用 |
| DUFOMap 已保存结果回放 | [GIF](../results/reference/dufomap/media/preview.gif) | 动态点删除 98.70%；静态点保留 97.98% |
| dufomap / media/replay/preview.gif | [GIF](../results/reference/dufomap/media/replay/preview.gif) / [MP4](../results/reference/dufomap/media/replay/replay.mp4) | 动态点删除 98.70%；静态点保留 97.98% |
| IR-MCL 已保存定位结果回放 | [GIF](../results/reference/ir-mcl/media/preview.gif) | 定位RMSE 5.32cm / 1.07°；清理指标不适用 |
| probe-2d-corridor：真实窗口录制 | [GIF](../results/reference/probe-2d-corridor/execution.gif) / [MP4](../results/reference/probe-2d-corridor/execution.mp4) | 定位原型；地图清理指标不适用；plain 918.76cm / guard 100.53cm / depth 100.58cm / search 70.33cm / recover 70.35cm / native 66.02cm |
| probe-2d-dynamic：真实窗口录制 | [GIF](../results/reference/probe-2d-dynamic/execution.gif) / [MP4](../results/reference/probe-2d-dynamic/execution.mp4) | 定位原型；地图清理指标不适用；plain 0.37cm / guard 0.19cm / depth 0.19cm / search 0.19cm / recover 0.19cm / native 7.12cm |
| probe-2d-height-corridor：真实窗口录制 | [GIF](../results/reference/probe-2d-height-corridor/execution.gif) / [MP4](../results/reference/probe-2d-height-corridor/execution.mp4) | 定位原型；地图清理指标不适用；plain 290.69cm / guard 101.03cm / depth 100.65cm / search 71.00cm / recover 21.21cm / native 67.25cm |
| probe-2d-large-change：真实窗口录制 | [GIF](../results/reference/probe-2d-large-change/execution.gif) / [MP4](../results/reference/probe-2d-large-change/execution.mp4) | 定位原型；地图清理指标不适用；plain 8.05cm / guard 0.47cm / depth 0.48cm / search 0.47cm / recover 0.48cm / native 6.74cm |
| probe-2d-static：真实窗口录制 | [GIF](../results/reference/probe-2d-static/execution.gif) / [MP4](../results/reference/probe-2d-static/execution.mp4) | 定位原型；地图清理指标不适用；plain 0.14cm / guard 0.14cm / depth 0.22cm / search 0.14cm / recover 0.22cm / native 6.72cm |
| probe-3d-corridor：真实窗口录制 | [GIF](../results/reference/probe-3d-corridor/execution.gif) / [MP4](../results/reference/probe-3d-corridor/execution.mp4) | 定位原型；地图清理指标不适用；plain 48.45cm / guard 101.03cm / depth 101.01cm / search 58.76cm / recover 60.78cm / native 411.72cm |
| probe-3d-dynamic：真实窗口录制 | [GIF](../results/reference/probe-3d-dynamic/execution.gif) / [MP4](../results/reference/probe-3d-dynamic/execution.mp4) | 定位原型；地图清理指标不适用；plain 9.42cm / guard 9.41cm / depth 9.41cm / search 9.41cm / recover 9.41cm / native 1.36cm |
| probe-3d-height-corridor：真实窗口录制 | [GIF](../results/reference/probe-3d-height-corridor/execution.gif) / [MP4](../results/reference/probe-3d-height-corridor/execution.mp4) | 定位原型；地图清理指标不适用；plain 47.22cm / guard 101.30cm / depth 101.14cm / search 65.60cm / recover 22.62cm / native 411.42cm |
| probe-3d-large-change：真实窗口录制 | [GIF](../results/reference/probe-3d-large-change/execution.gif) / [MP4](../results/reference/probe-3d-large-change/execution.mp4) | 定位原型；地图清理指标不适用；plain 9.49cm / guard 9.42cm / depth 9.42cm / search 9.42cm / recover 9.42cm / native 1.06cm |
| probe-3d-static：真实窗口录制 | [GIF](../results/reference/probe-3d-static/execution.gif) / [MP4](../results/reference/probe-3d-static/execution.mp4) | 定位原型；地图清理指标不适用；plain 9.42cm / guard 9.41cm / depth 9.42cm / search 9.41cm / recover 9.42cm / native 1.09cm |
| probe-calibrated-2d-corridor：真实窗口录制 | [GIF](../results/reference/probe-calibrated-2d-corridor/execution.gif) / [MP4](../results/reference/probe-calibrated-2d-corridor/execution.mp4) | 定位原型；地图清理指标不适用；plain 1037.69cm / guard 100.48cm / depth 100.54cm / search 70.40cm / recover 70.44cm / native 100.61cm |
| probe-calibrated-2d-dynamic：真实窗口录制 | [GIF](../results/reference/probe-calibrated-2d-dynamic/execution.gif) / [MP4](../results/reference/probe-calibrated-2d-dynamic/execution.mp4) | 定位原型；地图清理指标不适用；plain 0.37cm / guard 0.19cm / depth 0.18cm / search 0.19cm / recover 0.18cm / native 7.08cm |
| probe-calibrated-2d-height-corridor：真实窗口录制 | [GIF](../results/reference/probe-calibrated-2d-height-corridor/execution.gif) / [MP4](../results/reference/probe-calibrated-2d-height-corridor/execution.mp4) | 定位原型；地图清理指标不适用；plain 285.54cm / guard 101.15cm / depth 100.77cm / search 70.93cm / recover 21.15cm / native 67.00cm |
| probe-calibrated-2d-large-change：真实窗口录制 | [GIF](../results/reference/probe-calibrated-2d-large-change/execution.gif) / [MP4](../results/reference/probe-calibrated-2d-large-change/execution.mp4) | 定位原型；地图清理指标不适用；plain 7.98cm / guard 0.49cm / depth 0.49cm / search 0.49cm / recover 0.49cm / native 6.28cm |
| probe-calibrated-2d-static：真实窗口录制 | [GIF](../results/reference/probe-calibrated-2d-static/execution.gif) / [MP4](../results/reference/probe-calibrated-2d-static/execution.mp4) | 定位原型；地图清理指标不适用；plain 0.15cm / guard 0.15cm / depth 0.21cm / search 0.15cm / recover 0.21cm / native 6.82cm |
| probe-calibrated-3d-corridor：真实窗口录制 | [GIF](../results/reference/probe-calibrated-3d-corridor/execution.gif) / [MP4](../results/reference/probe-calibrated-3d-corridor/execution.mp4) | 定位原型；地图清理指标不适用；plain 733.38cm / guard 100.49cm / depth 100.62cm / search 56.77cm / recover 57.56cm / native 397.82cm |
| probe-calibrated-3d-dynamic：真实窗口录制 | [GIF](../results/reference/probe-calibrated-3d-dynamic/execution.gif) / [MP4](../results/reference/probe-calibrated-3d-dynamic/execution.mp4) | 定位原型；地图清理指标不适用；plain 0.17cm / guard 0.13cm / depth 0.13cm / search 0.13cm / recover 0.13cm / native 1.39cm |
| probe-calibrated-3d-height-corridor：真实窗口录制 | [GIF](../results/reference/probe-calibrated-3d-height-corridor/execution.gif) / [MP4](../results/reference/probe-calibrated-3d-height-corridor/execution.mp4) | 定位原型；地图清理指标不适用；plain 46.60cm / guard 100.36cm / depth 100.38cm / search 47.70cm / recover 50.79cm / native 512.79cm |
| probe-calibrated-3d-large-change：真实窗口录制 | [GIF](../results/reference/probe-calibrated-3d-large-change/execution.gif) / [MP4](../results/reference/probe-calibrated-3d-large-change/execution.mp4) | 定位原型；地图清理指标不适用；plain 3.69cm / guard 0.24cm / depth 0.35cm / search 0.24cm / recover 0.35cm / native 1.25cm |
| probe-calibrated-3d-static：真实窗口录制 | [GIF](../results/reference/probe-calibrated-3d-static/execution.gif) / [MP4](../results/reference/probe-calibrated-3d-static/execution.mp4) | 定位原型；地图清理指标不适用；plain 0.12cm / guard 0.12cm / depth 0.21cm / search 0.12cm / recover 0.21cm / native 1.08cm |
| probe-calibrated-refinement-2d-corridor：离线重算后的保存输出回放 | [GIF](../results/reference/probe-calibrated-refinement-2d-corridor/result.gif) / [MP4](../results/reference/probe-calibrated-refinement-2d-corridor/result.mp4) | 传感器／建图过程演示；未评分 |
| probe-calibrated-refinement-2d-height-corridor：离线重算后的保存输出回放 | [GIF](../results/reference/probe-calibrated-refinement-2d-height-corridor/result.gif) / [MP4](../results/reference/probe-calibrated-refinement-2d-height-corridor/result.mp4) | 传感器／建图过程演示；未评分 |
| probe-calibrated-refinement-3d-corridor：离线重算后的保存输出回放 | [GIF](../results/reference/probe-calibrated-refinement-3d-corridor/result.gif) / [MP4](../results/reference/probe-calibrated-refinement-3d-corridor/result.mp4) | 传感器／建图过程演示；未评分 |
| probe-calibrated-refinement-3d-height-corridor：离线重算后的保存输出回放 | [GIF](../results/reference/probe-calibrated-refinement-3d-height-corridor/result.gif) / [MP4](../results/reference/probe-calibrated-refinement-3d-height-corridor/result.mp4) | 传感器／建图过程演示；未评分 |
| probe-mapping-corridor：真实窗口录制 | [GIF](../results/reference/probe-mapping-corridor/execution.gif) / [MP4](../results/reference/probe-mapping-corridor/execution.mp4) | 传感器／建图过程演示；未评分 |
| probe-mapping-dynamic：真实窗口录制 | [GIF](../results/reference/probe-mapping-dynamic/execution.gif) / [MP4](../results/reference/probe-mapping-dynamic/execution.mp4) | 传感器／建图过程演示；未评分 |
| probe-mapping-height-corridor：真实窗口录制 | [GIF](../results/reference/probe-mapping-height-corridor/execution.gif) / [MP4](../results/reference/probe-mapping-height-corridor/execution.mp4) | 传感器／建图过程演示；未评分 |
| probe-mapping-static：真实窗口录制 | [GIF](../results/reference/probe-mapping-static/execution.gif) / [MP4](../results/reference/probe-mapping-static/execution.mp4) | 传感器／建图过程演示；未评分 |
| probe-refinement-2d-corridor：离线重算后的保存输出回放 | [GIF](../results/reference/probe-refinement-2d-corridor/result.gif) / [MP4](../results/reference/probe-refinement-2d-corridor/result.mp4) | 传感器／建图过程演示；未评分 |
| probe-refinement-2d-height-corridor：离线重算后的保存输出回放 | [GIF](../results/reference/probe-refinement-2d-height-corridor/result.gif) / [MP4](../results/reference/probe-refinement-2d-height-corridor/result.mp4) | 传感器／建图过程演示；未评分 |
| probe-refinement-3d-corridor：离线重算后的保存输出回放 | [GIF](../results/reference/probe-refinement-3d-corridor/result.gif) / [MP4](../results/reference/probe-refinement-3d-corridor/result.mp4) | 传感器／建图过程演示；未评分 |
| probe-refinement-3d-height-corridor：离线重算后的保存输出回放 | [GIF](../results/reference/probe-refinement-3d-height-corridor/result.gif) / [MP4](../results/reference/probe-refinement-3d-height-corridor/result.mp4) | 传感器／建图过程演示；未评分 |
| robot-2d-dynamic-matched / execution.gif | [GIF](../results/reference/robot-2d-dynamic-matched/execution.gif) / [MP4](../results/reference/robot-2d-dynamic-matched/execution.mp4) | 动态删／静态留：Raw 0.00%/100.00%；DUFO 8.33%/100.00%；Beauty 33.33%/96.64% |
| robot-2d-dynamic-matched / executions/beautymap.gif | [GIF](../results/reference/robot-2d-dynamic-matched/executions/beautymap.gif) / [MP4](../results/reference/robot-2d-dynamic-matched/executions/beautymap.mp4) | 动态格删除 33.33%；静态格保留 96.64% |
| robot-2d-dynamic-matched / executions/dufomap.gif | [GIF](../results/reference/robot-2d-dynamic-matched/executions/dufomap.gif) / [MP4](../results/reference/robot-2d-dynamic-matched/executions/dufomap.mp4) | 动态格删除 8.33%；静态格保留 100.00% |
| robot-2d-dynamic-matched / executions/raw.gif | [GIF](../results/reference/robot-2d-dynamic-matched/executions/raw.gif) / [MP4](../results/reference/robot-2d-dynamic-matched/executions/raw.mp4) | 动态格删除 0.00%；静态格保留 100.00% |
| robot-2d-dynamic-matched / methods/beautymap/result.gif | [GIF](../results/reference/robot-2d-dynamic-matched/methods/beautymap/result.gif) / [MP4](../results/reference/robot-2d-dynamic-matched/methods/beautymap/result.mp4) | 动态格删除 33.33%；静态格保留 96.64% |
| robot-2d-dynamic-matched / methods/dufomap/result.gif | [GIF](../results/reference/robot-2d-dynamic-matched/methods/dufomap/result.gif) / [MP4](../results/reference/robot-2d-dynamic-matched/methods/dufomap/result.mp4) | 动态格删除 8.33%；静态格保留 100.00% |
| robot-2d-dynamic-matched / methods/raw/result.gif | [GIF](../results/reference/robot-2d-dynamic-matched/methods/raw/result.gif) / [MP4](../results/reference/robot-2d-dynamic-matched/methods/raw/result.mp4) | 动态格删除 0.00%；静态格保留 100.00% |
| robot-2d-dynamic-matched / result.gif | [GIF](../results/reference/robot-2d-dynamic-matched/result.gif) / [MP4](../results/reference/robot-2d-dynamic-matched/result.mp4) | 动态删／静态留：Raw 0.00%/100.00%；DUFO 8.33%/100.00%；Beauty 33.33%/96.64% |
| robot-3d-corridor / execution.gif | [GIF](../results/reference/robot-3d-corridor/execution.gif) / [MP4](../results/reference/robot-3d-corridor/execution.mp4) | 动态删／静态留：Raw N/A/100.00%；DUFO N/A/100.00%；Beauty N/A/99.90% |
| robot-3d-corridor / executions/beautymap.gif | [GIF](../results/reference/robot-3d-corridor/executions/beautymap.gif) / [MP4](../results/reference/robot-3d-corridor/executions/beautymap.mp4) | 动态点删除 N/A；静态点保留 99.90% |
| robot-3d-corridor / executions/dufomap.gif | [GIF](../results/reference/robot-3d-corridor/executions/dufomap.gif) / [MP4](../results/reference/robot-3d-corridor/executions/dufomap.mp4) | 动态点删除 N/A；静态点保留 100.00% |
| robot-3d-corridor / executions/raw.gif | [GIF](../results/reference/robot-3d-corridor/executions/raw.gif) / [MP4](../results/reference/robot-3d-corridor/executions/raw.mp4) | 动态点删除 N/A；静态点保留 100.00% |
| robot-3d-dynamic / execution.gif | [GIF](../results/reference/robot-3d-dynamic/execution.gif) / [MP4](../results/reference/robot-3d-dynamic/execution.mp4) | 动态删／静态留：Raw 0.00%/100.00%；DUFO 46.59%/100.00%；Beauty 74.36%/81.15% |
| robot-3d-dynamic / executions/beautymap.gif | [GIF](../results/reference/robot-3d-dynamic/executions/beautymap.gif) / [MP4](../results/reference/robot-3d-dynamic/executions/beautymap.mp4) | 动态点删除 74.36%；静态点保留 81.15% |
| robot-3d-dynamic / executions/dufomap.gif | [GIF](../results/reference/robot-3d-dynamic/executions/dufomap.gif) / [MP4](../results/reference/robot-3d-dynamic/executions/dufomap.mp4) | 动态点删除 46.59%；静态点保留 100.00% |
| robot-3d-dynamic / executions/raw.gif | [GIF](../results/reference/robot-3d-dynamic/executions/raw.gif) / [MP4](../results/reference/robot-3d-dynamic/executions/raw.mp4) | 动态点删除 0.00%；静态点保留 100.00% |
| robot-3d-dynamic-mapping / execution.gif | [GIF](../results/reference/robot-3d-dynamic-mapping/execution.gif) / [MP4](../results/reference/robot-3d-dynamic-mapping/execution.mp4) | 传感器／建图过程演示；未评分 |
| robot-3d-large-change / execution.gif | [GIF](../results/reference/robot-3d-large-change/execution.gif) / [MP4](../results/reference/robot-3d-large-change/execution.mp4) | 动态删／静态留：Raw N/A/100.00%；DUFO N/A/100.00%；Beauty N/A/83.33% |
| robot-3d-large-change / executions/beautymap.gif | [GIF](../results/reference/robot-3d-large-change/executions/beautymap.gif) / [MP4](../results/reference/robot-3d-large-change/executions/beautymap.mp4) | 动态点删除 N/A；静态点保留 83.33%（静态A旧图） |
| robot-3d-large-change / executions/dufomap.gif | [GIF](../results/reference/robot-3d-large-change/executions/dufomap.gif) / [MP4](../results/reference/robot-3d-large-change/executions/dufomap.mp4) | 动态点删除 N/A；静态点保留 100.00%（静态A旧图） |
| robot-3d-large-change / executions/raw.gif | [GIF](../results/reference/robot-3d-large-change/executions/raw.gif) / [MP4](../results/reference/robot-3d-large-change/executions/raw.mp4) | 动态点删除 N/A；静态点保留 100.00%（静态A旧图） |
| robot-3d-map-review-v2 / execution.gif | [GIF](../results/reference/robot-3d-map-review-v2/execution.gif) / [MP4](../results/reference/robot-3d-map-review-v2/execution.mp4) | 传感器／建图过程演示；未评分 |
| robot-3d-static / execution.gif | [GIF](../results/reference/robot-3d-static/execution.gif) / [MP4](../results/reference/robot-3d-static/execution.mp4) | 动态删／静态留：Raw N/A/100.00%；DUFO N/A/100.00%；Beauty N/A/83.33% |
| robot-3d-static / executions/beautymap.gif | [GIF](../results/reference/robot-3d-static/executions/beautymap.gif) / [MP4](../results/reference/robot-3d-static/executions/beautymap.mp4) | 动态点删除 N/A；静态点保留 83.33% |
| robot-3d-static / executions/dufomap.gif | [GIF](../results/reference/robot-3d-static/executions/dufomap.gif) / [MP4](../results/reference/robot-3d-static/executions/dufomap.mp4) | 动态点删除 N/A；静态点保留 100.00% |
| robot-3d-static / executions/raw.gif | [GIF](../results/reference/robot-3d-static/executions/raw.gif) / [MP4](../results/reference/robot-3d-static/executions/raw.mp4) | 动态点删除 N/A；静态点保留 100.00% |
| robot-corridor-mapping：现场执行 | [GIF](../results/reference/robot-corridor-mapping/execution.gif) / [MP4](../results/reference/robot-corridor-mapping/execution.mp4) | 传感器／建图过程演示；未评分 |
| robot-corridor-v2 / execution.gif | [GIF](../results/reference/robot-corridor-v2/execution.gif) / [MP4](../results/reference/robot-corridor-v2/execution.mp4) | 动态删／静态留：Raw N/A/100.00%；DUFO N/A/100.00%；Beauty N/A/100.00% |
| robot-corridor-v2 / executions/degraded_beautymap.gif | [GIF](../results/reference/robot-corridor-v2/executions/degraded_beautymap.gif) / [MP4](../results/reference/robot-corridor-v2/executions/degraded_beautymap.mp4) | 动态格删除 N/A；静态格保留 100.00% |
| robot-corridor-v2 / executions/degraded_dufomap.gif | [GIF](../results/reference/robot-corridor-v2/executions/degraded_dufomap.gif) / [MP4](../results/reference/robot-corridor-v2/executions/degraded_dufomap.mp4) | 动态格删除 N/A；静态格保留 100.00% |
| robot-corridor-v2 / executions/degraded_raw.gif | [GIF](../results/reference/robot-corridor-v2/executions/degraded_raw.gif) / [MP4](../results/reference/robot-corridor-v2/executions/degraded_raw.mp4) | 动态格删除 N/A；静态格保留 100.00% |
| robot-corridor-v2 / methods/degraded_beautymap/result.gif | [GIF](../results/reference/robot-corridor-v2/methods/degraded_beautymap/result.gif) / [MP4](../results/reference/robot-corridor-v2/methods/degraded_beautymap/result.mp4) | 动态格删除 N/A；静态格保留 100.00% |
| robot-corridor-v2 / methods/degraded_dufomap/result.gif | [GIF](../results/reference/robot-corridor-v2/methods/degraded_dufomap/result.gif) / [MP4](../results/reference/robot-corridor-v2/methods/degraded_dufomap/result.mp4) | 动态格删除 N/A；静态格保留 100.00% |
| robot-corridor-v2 / methods/degraded_raw/result.gif | [GIF](../results/reference/robot-corridor-v2/methods/degraded_raw/result.gif) / [MP4](../results/reference/robot-corridor-v2/methods/degraded_raw/result.mp4) | 动态格删除 N/A；静态格保留 100.00% |
| robot-corridor-v2 / result.gif | [GIF](../results/reference/robot-corridor-v2/result.gif) / [MP4](../results/reference/robot-corridor-v2/result.mp4) | 动态删／静态留：Raw N/A/100.00%；DUFO N/A/100.00%；Beauty N/A/100.00% |
| robot-corridor-v2-mapping / execution.gif | [GIF](../results/reference/robot-corridor-v2-mapping/execution.gif) / [MP4](../results/reference/robot-corridor-v2-mapping/execution.mp4) | 传感器／建图过程演示；未评分 |
| robot-degradation：现场执行 | [GIF](../results/reference/robot-degradation/execution.gif) / [MP4](../results/reference/robot-degradation/execution.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 62.64cm / dufomap 62.64cm / beautymap 62.64cm / degraded_raw 73.63cm / degraded_dufomap 73.63cm / degraded_beautymap 73.63cm |
| 走廊退化：beautymap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-degradation/methods/beautymap/result.gif) / [MP4](../results/reference/robot-degradation/methods/beautymap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 62.64cm / dufomap 62.64cm / beautymap 62.64cm / degraded_raw 73.63cm / degraded_dufomap 73.63cm / degraded_beautymap 73.63cm |
| 走廊退化：degraded_beautymap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-degradation/methods/degraded_beautymap/result.gif) / [MP4](../results/reference/robot-degradation/methods/degraded_beautymap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 62.64cm / dufomap 62.64cm / beautymap 62.64cm / degraded_raw 73.63cm / degraded_dufomap 73.63cm / degraded_beautymap 73.63cm |
| 走廊退化：degraded_dufomap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-degradation/methods/degraded_dufomap/result.gif) / [MP4](../results/reference/robot-degradation/methods/degraded_dufomap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 62.64cm / dufomap 62.64cm / beautymap 62.64cm / degraded_raw 73.63cm / degraded_dufomap 73.63cm / degraded_beautymap 73.63cm |
| 走廊退化：degraded_raw 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-degradation/methods/degraded_raw/result.gif) / [MP4](../results/reference/robot-degradation/methods/degraded_raw/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 62.64cm / dufomap 62.64cm / beautymap 62.64cm / degraded_raw 73.63cm / degraded_dufomap 73.63cm / degraded_beautymap 73.63cm |
| 走廊退化：dufomap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-degradation/methods/dufomap/result.gif) / [MP4](../results/reference/robot-degradation/methods/dufomap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 62.64cm / dufomap 62.64cm / beautymap 62.64cm / degraded_raw 73.63cm / degraded_dufomap 73.63cm / degraded_beautymap 73.63cm |
| 走廊退化：raw 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-degradation/methods/raw/result.gif) / [MP4](../results/reference/robot-degradation/methods/raw/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 62.64cm / dufomap 62.64cm / beautymap 62.64cm / degraded_raw 73.63cm / degraded_dufomap 73.63cm / degraded_beautymap 73.63cm |
| robot-degradation：本次结果回放 | [GIF](../results/reference/robot-degradation/result.gif) / [MP4](../results/reference/robot-degradation/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 62.64cm / dufomap 62.64cm / beautymap 62.64cm / degraded_raw 73.63cm / degraded_dufomap 73.63cm / degraded_beautymap 73.63cm |
| robot-dynamic：现场执行 | [GIF](../results/reference/robot-dynamic/execution.gif) / [MP4](../results/reference/robot-dynamic/execution.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.31cm / dufomap 7.10cm / beautymap 7.28cm / clean_raw 6.30cm / clean_dufomap 6.30cm / clean_beautymap 6.89cm |
| 运动障碍物：beautymap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-dynamic/methods/beautymap/result.gif) / [MP4](../results/reference/robot-dynamic/methods/beautymap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.31cm / dufomap 7.10cm / beautymap 7.28cm / clean_raw 6.30cm / clean_dufomap 6.30cm / clean_beautymap 6.89cm |
| 运动障碍物：clean_beautymap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-dynamic/methods/clean_beautymap/result.gif) / [MP4](../results/reference/robot-dynamic/methods/clean_beautymap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.31cm / dufomap 7.10cm / beautymap 7.28cm / clean_raw 6.30cm / clean_dufomap 6.30cm / clean_beautymap 6.89cm |
| 运动障碍物：clean_dufomap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-dynamic/methods/clean_dufomap/result.gif) / [MP4](../results/reference/robot-dynamic/methods/clean_dufomap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.31cm / dufomap 7.10cm / beautymap 7.28cm / clean_raw 6.30cm / clean_dufomap 6.30cm / clean_beautymap 6.89cm |
| 运动障碍物：clean_raw 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-dynamic/methods/clean_raw/result.gif) / [MP4](../results/reference/robot-dynamic/methods/clean_raw/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.31cm / dufomap 7.10cm / beautymap 7.28cm / clean_raw 6.30cm / clean_dufomap 6.30cm / clean_beautymap 6.89cm |
| 运动障碍物：dufomap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-dynamic/methods/dufomap/result.gif) / [MP4](../results/reference/robot-dynamic/methods/dufomap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.31cm / dufomap 7.10cm / beautymap 7.28cm / clean_raw 6.30cm / clean_dufomap 6.30cm / clean_beautymap 6.89cm |
| 运动障碍物：raw 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-dynamic/methods/raw/result.gif) / [MP4](../results/reference/robot-dynamic/methods/raw/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.31cm / dufomap 7.10cm / beautymap 7.28cm / clean_raw 6.30cm / clean_dufomap 6.30cm / clean_beautymap 6.89cm |
| robot-dynamic：本次结果回放 | [GIF](../results/reference/robot-dynamic/result.gif) / [MP4](../results/reference/robot-dynamic/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.31cm / dufomap 7.10cm / beautymap 7.28cm / clean_raw 6.30cm / clean_dufomap 6.30cm / clean_beautymap 6.89cm |
| robot-dynamic-mapping：现场执行 | [GIF](../results/reference/robot-dynamic-mapping/execution.gif) / [MP4](../results/reference/robot-dynamic-mapping/execution.mp4) | 传感器／建图过程演示；未评分 |
| robot-gicp-static / execution.gif | [GIF](../results/reference/robot-gicp-static/execution.gif) / [MP4](../results/reference/robot-gicp-static/execution.mp4) | 定位RMSE（清理指标不适用／未标注）：gicp 1.09cm |
| robot-gicp-static / result.gif | [GIF](../results/reference/robot-gicp-static/result.gif) / [MP4](../results/reference/robot-gicp-static/result.mp4) | 定位RMSE（清理指标不适用／未标注）：gicp 1.09cm |
| robot-large-change：现场执行 | [GIF](../results/reference/robot-large-change/execution.gif) / [MP4](../results/reference/robot-large-change/execution.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 6.25cm / dufomap 6.25cm / beautymap 6.16cm |
| 持久结构变化：beautymap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-large-change/methods/beautymap/result.gif) / [MP4](../results/reference/robot-large-change/methods/beautymap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 6.25cm / dufomap 6.25cm / beautymap 6.16cm |
| 持久结构变化：dufomap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-large-change/methods/dufomap/result.gif) / [MP4](../results/reference/robot-large-change/methods/dufomap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 6.25cm / dufomap 6.25cm / beautymap 6.16cm |
| 持久结构变化：raw 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-large-change/methods/raw/result.gif) / [MP4](../results/reference/robot-large-change/methods/raw/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 6.25cm / dufomap 6.25cm / beautymap 6.16cm |
| robot-large-change：本次结果回放 | [GIF](../results/reference/robot-large-change/result.gif) / [MP4](../results/reference/robot-large-change/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 6.25cm / dufomap 6.25cm / beautymap 6.16cm |
| robot-live-degradation / execution.gif | [GIF](../results/reference/robot-live-degradation/execution.gif) / [MP4](../results/reference/robot-live-degradation/execution.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 53.46cm / dufomap 53.46cm / beautymap 53.46cm / degraded_raw 75.66cm / degraded_dufomap 75.66cm / degraded_beautymap 75.66cm |
| 走廊退化：BeautyMap 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-degradation/executions/degraded_beautymap.gif) / [MP4](../results/reference/robot-live-degradation/executions/degraded_beautymap.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 53.46cm / dufomap 53.46cm / beautymap 53.46cm / degraded_raw 75.66cm / degraded_dufomap 75.66cm / degraded_beautymap 75.66cm |
| 走廊退化：DUFOMap 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-degradation/executions/degraded_dufomap.gif) / [MP4](../results/reference/robot-live-degradation/executions/degraded_dufomap.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 53.46cm / dufomap 53.46cm / beautymap 53.46cm / degraded_raw 75.66cm / degraded_dufomap 75.66cm / degraded_beautymap 75.66cm |
| 走廊退化：Raw 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-degradation/executions/degraded_raw.gif) / [MP4](../results/reference/robot-live-degradation/executions/degraded_raw.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 53.46cm / dufomap 53.46cm / beautymap 53.46cm / degraded_raw 75.66cm / degraded_dufomap 75.66cm / degraded_beautymap 75.66cm |
| 走廊退化：BeautyMap 本次原生更新回放 | [GIF](../results/reference/robot-live-degradation/methods/degraded_beautymap/result.gif) / [MP4](../results/reference/robot-live-degradation/methods/degraded_beautymap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 53.46cm / dufomap 53.46cm / beautymap 53.46cm / degraded_raw 75.66cm / degraded_dufomap 75.66cm / degraded_beautymap 75.66cm |
| 走廊退化：DUFOMap 本次原生更新回放 | [GIF](../results/reference/robot-live-degradation/methods/degraded_dufomap/result.gif) / [MP4](../results/reference/robot-live-degradation/methods/degraded_dufomap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 53.46cm / dufomap 53.46cm / beautymap 53.46cm / degraded_raw 75.66cm / degraded_dufomap 75.66cm / degraded_beautymap 75.66cm |
| 走廊退化：Raw 本次原生更新回放 | [GIF](../results/reference/robot-live-degradation/methods/degraded_raw/result.gif) / [MP4](../results/reference/robot-live-degradation/methods/degraded_raw/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 53.46cm / dufomap 53.46cm / beautymap 53.46cm / degraded_raw 75.66cm / degraded_dufomap 75.66cm / degraded_beautymap 75.66cm |
| robot-live-degradation / result.gif | [GIF](../results/reference/robot-live-degradation/result.gif) / [MP4](../results/reference/robot-live-degradation/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 53.46cm / dufomap 53.46cm / beautymap 53.46cm / degraded_raw 75.66cm / degraded_dufomap 75.66cm / degraded_beautymap 75.66cm |
| robot-live-dynamic / execution.gif | [GIF](../results/reference/robot-live-dynamic/execution.gif) / [MP4](../results/reference/robot-live-dynamic/execution.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.41cm / dufomap 7.35cm / beautymap 7.14cm / clean_raw 7.08cm / clean_dufomap 7.08cm / clean_beautymap 6.78cm |
| 运动障碍物：BeautyMap 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-dynamic/executions/beautymap.gif) / [MP4](../results/reference/robot-live-dynamic/executions/beautymap.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.41cm / dufomap 7.35cm / beautymap 7.14cm / clean_raw 7.08cm / clean_dufomap 7.08cm / clean_beautymap 6.78cm |
| 运动障碍物：DUFOMap 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-dynamic/executions/dufomap.gif) / [MP4](../results/reference/robot-live-dynamic/executions/dufomap.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.41cm / dufomap 7.35cm / beautymap 7.14cm / clean_raw 7.08cm / clean_dufomap 7.08cm / clean_beautymap 6.78cm |
| 运动障碍物：Raw 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-dynamic/executions/raw.gif) / [MP4](../results/reference/robot-live-dynamic/executions/raw.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.41cm / dufomap 7.35cm / beautymap 7.14cm / clean_raw 7.08cm / clean_dufomap 7.08cm / clean_beautymap 6.78cm |
| 运动障碍物：BeautyMap 本次原生更新回放 | [GIF](../results/reference/robot-live-dynamic/methods/beautymap/result.gif) / [MP4](../results/reference/robot-live-dynamic/methods/beautymap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.41cm / dufomap 7.35cm / beautymap 7.14cm / clean_raw 7.08cm / clean_dufomap 7.08cm / clean_beautymap 6.78cm |
| 运动障碍物：DUFOMap 本次原生更新回放 | [GIF](../results/reference/robot-live-dynamic/methods/dufomap/result.gif) / [MP4](../results/reference/robot-live-dynamic/methods/dufomap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.41cm / dufomap 7.35cm / beautymap 7.14cm / clean_raw 7.08cm / clean_dufomap 7.08cm / clean_beautymap 6.78cm |
| 运动障碍物：Raw 本次原生更新回放 | [GIF](../results/reference/robot-live-dynamic/methods/raw/result.gif) / [MP4](../results/reference/robot-live-dynamic/methods/raw/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.41cm / dufomap 7.35cm / beautymap 7.14cm / clean_raw 7.08cm / clean_dufomap 7.08cm / clean_beautymap 6.78cm |
| robot-live-dynamic / result.gif | [GIF](../results/reference/robot-live-dynamic/result.gif) / [MP4](../results/reference/robot-live-dynamic/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.41cm / dufomap 7.35cm / beautymap 7.14cm / clean_raw 7.08cm / clean_dufomap 7.08cm / clean_beautymap 6.78cm |
| robot-live-large-change / execution.gif | [GIF](../results/reference/robot-live-large-change/execution.gif) / [MP4](../results/reference/robot-live-large-change/execution.mp4) | 动态删／静态留：Raw N/A/100.00%；DUFO N/A/100.00%；Beauty N/A/96.51% |
| 持久结构变化：BeautyMap 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-large-change/executions/beautymap.gif) / [MP4](../results/reference/robot-live-large-change/executions/beautymap.mp4) | 动态格删除 N/A；静态格保留 96.51%（静态A旧图） |
| 持久结构变化：DUFOMap 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-large-change/executions/dufomap.gif) / [MP4](../results/reference/robot-live-large-change/executions/dufomap.mp4) | 动态格删除 N/A；静态格保留 100.00%（静态A旧图） |
| 持久结构变化：Raw 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-large-change/executions/raw.gif) / [MP4](../results/reference/robot-live-large-change/executions/raw.mp4) | 动态格删除 N/A；静态格保留 100.00%（静态A旧图） |
| 持久结构变化：BeautyMap 本次原生更新回放 | [GIF](../results/reference/robot-live-large-change/methods/beautymap/result.gif) / [MP4](../results/reference/robot-live-large-change/methods/beautymap/result.mp4) | 动态格删除 N/A；静态格保留 96.51%（静态A旧图） |
| 持久结构变化：DUFOMap 本次原生更新回放 | [GIF](../results/reference/robot-live-large-change/methods/dufomap/result.gif) / [MP4](../results/reference/robot-live-large-change/methods/dufomap/result.mp4) | 动态格删除 N/A；静态格保留 100.00%（静态A旧图） |
| 持久结构变化：Raw 本次原生更新回放 | [GIF](../results/reference/robot-live-large-change/methods/raw/result.gif) / [MP4](../results/reference/robot-live-large-change/methods/raw/result.mp4) | 动态格删除 N/A；静态格保留 100.00%（静态A旧图） |
| robot-live-large-change / result.gif | [GIF](../results/reference/robot-live-large-change/result.gif) / [MP4](../results/reference/robot-live-large-change/result.mp4) | 动态删／静态留：Raw N/A/100.00%；DUFO N/A/100.00%；Beauty N/A/96.51% |
| robot-live-static / execution.gif | [GIF](../results/reference/robot-live-static/execution.gif) / [MP4](../results/reference/robot-live-static/execution.mp4) | 动态删／静态留：Raw N/A/100.00%；DUFO N/A/100.00%；Beauty N/A/96.51% |
| 纯静态：BeautyMap 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-static/executions/beautymap.gif) / [MP4](../results/reference/robot-live-static/executions/beautymap.mp4) | 动态格删除 N/A；静态格保留 96.51% |
| 纯静态：DUFOMap 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-static/executions/dufomap.gif) / [MP4](../results/reference/robot-live-static/executions/dufomap.mp4) | 动态格删除 N/A；静态格保留 100.00% |
| 纯静态：Raw 独立 RViz 现场执行 | [GIF](../results/reference/robot-live-static/executions/raw.gif) / [MP4](../results/reference/robot-live-static/executions/raw.mp4) | 动态格删除 N/A；静态格保留 100.00% |
| 纯静态：BeautyMap 本次原生更新回放 | [GIF](../results/reference/robot-live-static/methods/beautymap/result.gif) / [MP4](../results/reference/robot-live-static/methods/beautymap/result.mp4) | 动态格删除 N/A；静态格保留 96.51% |
| 纯静态：DUFOMap 本次原生更新回放 | [GIF](../results/reference/robot-live-static/methods/dufomap/result.gif) / [MP4](../results/reference/robot-live-static/methods/dufomap/result.mp4) | 动态格删除 N/A；静态格保留 100.00% |
| 纯静态：Raw 本次原生更新回放 | [GIF](../results/reference/robot-live-static/methods/raw/result.gif) / [MP4](../results/reference/robot-live-static/methods/raw/result.mp4) | 动态格删除 N/A；静态格保留 100.00% |
| robot-live-static / result.gif | [GIF](../results/reference/robot-live-static/result.gif) / [MP4](../results/reference/robot-live-static/result.mp4) | 动态删／静态留：Raw N/A/100.00%；DUFO N/A/100.00%；Beauty N/A/96.51% |
| robot-ndt-static / execution.gif | [GIF](../results/reference/robot-ndt-static/execution.gif) / [MP4](../results/reference/robot-ndt-static/execution.mp4) | 定位RMSE（清理指标不适用／未标注）：ndt 0.93cm |
| robot-ndt-static / result.gif | [GIF](../results/reference/robot-ndt-static/result.gif) / [MP4](../results/reference/robot-ndt-static/result.mp4) | 定位RMSE（清理指标不适用／未标注）：ndt 0.93cm |
| robot-ndt-static-initial / execution.gif | [GIF](../results/reference/robot-ndt-static-initial/execution.gif) / [MP4](../results/reference/robot-ndt-static-initial/execution.mp4) | 定位RMSE（清理指标不适用／未标注）：ndt 34.43cm |
| robot-ndt-static-initial / result.gif | [GIF](../results/reference/robot-ndt-static-initial/result.gif) / [MP4](../results/reference/robot-ndt-static-initial/result.mp4) | 定位RMSE（清理指标不适用／未标注）：ndt 34.43cm |
| robot-static：现场执行 | [GIF](../results/reference/robot-static/execution.gif) / [MP4](../results/reference/robot-static/execution.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.08cm / dufomap 7.08cm / beautymap 6.55cm |
| 纯静态：beautymap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-static/methods/beautymap/result.gif) / [MP4](../results/reference/robot-static/methods/beautymap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.08cm / dufomap 7.08cm / beautymap 6.55cm |
| 纯静态：dufomap 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-static/methods/dufomap/result.gif) / [MP4](../results/reference/robot-static/methods/dufomap/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.08cm / dufomap 7.08cm / beautymap 6.55cm |
| 纯静态：raw 原生 AMCL 保存结果回放 | [GIF](../results/reference/robot-static/methods/raw/result.gif) / [MP4](../results/reference/robot-static/methods/raw/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.08cm / dufomap 7.08cm / beautymap 6.55cm |
| robot-static：本次结果回放 | [GIF](../results/reference/robot-static/result.gif) / [MP4](../results/reference/robot-static/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 7.08cm / dufomap 7.08cm / beautymap 6.55cm |
| robot-static-mapping：现场执行 | [GIF](../results/reference/robot-static-mapping/execution.gif) / [MP4](../results/reference/robot-static-mapping/execution.mp4) | 传感器／建图过程演示；未评分 |
| robot-supp-dynamic / execution.gif | [GIF](../results/reference/robot-supp-dynamic/execution.gif) / [MP4](../results/reference/robot-supp-dynamic/execution.mp4) | 传感器／建图过程演示；未评分 |
| robot-supp-large-change / execution.gif | [GIF](../results/reference/robot-supp-large-change/execution.gif) / [MP4](../results/reference/robot-supp-large-change/execution.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 6.99cm / dufomap 6.99cm / beautymap 7.04cm |
| robot-supp-large-change / result.gif | [GIF](../results/reference/robot-supp-large-change/result.gif) / [MP4](../results/reference/robot-supp-large-change/result.mp4) | 定位RMSE（清理指标不适用／未标注）：raw 6.99cm / dufomap 6.99cm / beautymap 7.04cm |
| robot-supp-static / execution.gif | [GIF](../results/reference/robot-supp-static/execution.gif) / [MP4](../results/reference/robot-supp-static/execution.mp4) | 传感器／建图过程演示；未评分 |
| 走廊退化 · 原生二维SRRG建图 | [GIF](../results/reference/srrg-2d-corridor/execution.gif) / [MP4](../results/reference/srrg-2d-corridor/execution.mp4) | 动态残影删除 N/A；静态覆盖保留 82.24% |
| 运动障碍物 · 原生二维SRRG建图 | [GIF](../results/reference/srrg-2d-dynamic/execution.gif) / [MP4](../results/reference/srrg-2d-dynamic/execution.mp4) | 动态残影删除 42.31%；静态覆盖保留 99.51% |
| 持久结构变化 · 原生二维SRRG建图 | [GIF](../results/reference/srrg-2d-large-change/execution.gif) / [MP4](../results/reference/srrg-2d-large-change/execution.mp4) | 动态残影删除 N/A；静态覆盖保留 99.71% |
| 纯静态 · 原生二维SRRG建图 | [GIF](../results/reference/srrg-2d-static/execution.gif) / [MP4](../results/reference/srrg-2d-static/execution.mp4) | 动态残影删除 N/A；静态覆盖保留 99.84% |
| srrg-2d-static-graph-merge-on / execution.gif | [GIF](../results/reference/srrg-2d-static-graph-merge-on/execution.gif) / [MP4](../results/reference/srrg-2d-static-graph-merge-on/execution.mp4) | 动态残影删除 N/A；静态覆盖保留 99.69% |
| srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d / execution.gif | [GIF](../results/reference/srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d/execution.gif) / [MP4](../results/reference/srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d/execution.mp4) | 联调失败诊断；已修复，保留原片 |
| srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3 / execution.gif | [GIF](../results/reference/srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3/execution.gif) / [MP4](../results/reference/srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3/execution.mp4) | 联调失败诊断；已修复，保留原片 |
| srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d / execution.gif | [GIF](../results/reference/srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d/execution.gif) / [MP4](../results/reference/srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d/execution.mp4) | 失败诊断：图合并数值崩溃，最后成功仿真66.0s／录制55.4s |
| results/localization/self-recovery-diagnostics/S1_static-unverified-15-26.mp4 / S1_static-unverified-15-26.mp4 | [MP4](../results/localization/self-recovery-diagnostics/S1_static-unverified-15-26.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| adam-mcl / replay.mp4 | [MP4](../results/reference/adam-mcl/media/replay/replay.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| beautymap / review.mp4 | [MP4](../results/reference/beautymap/media/rviz/review.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| dufomap / review.mp4 | [MP4](../results/reference/dufomap/media/rviz/review.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| ir-mcl / replay.mp4 | [MP4](../results/reference/ir-mcl/media/replay/replay.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| ir-mcl / full-session.mp4 | [MP4](../results/reference/ir-mcl/media/session/full-session.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-2d-corridor / recover.mp4 | [MP4](../results/reference/probe-2d-corridor/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-2d-dynamic / recover.mp4 | [MP4](../results/reference/probe-2d-dynamic/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-2d-height-corridor / recover.mp4 | [MP4](../results/reference/probe-2d-height-corridor/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-2d-large-change / recover.mp4 | [MP4](../results/reference/probe-2d-large-change/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-2d-static / recover.mp4 | [MP4](../results/reference/probe-2d-static/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-3d-corridor / recover.mp4 | [MP4](../results/reference/probe-3d-corridor/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-3d-dynamic / recover.mp4 | [MP4](../results/reference/probe-3d-dynamic/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-3d-height-corridor / recover.mp4 | [MP4](../results/reference/probe-3d-height-corridor/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-3d-large-change / recover.mp4 | [MP4](../results/reference/probe-3d-large-change/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-3d-static / recover.mp4 | [MP4](../results/reference/probe-3d-static/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-calibrated-2d-corridor / recover.mp4 | [MP4](../results/reference/probe-calibrated-2d-corridor/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-calibrated-2d-dynamic / recover.mp4 | [MP4](../results/reference/probe-calibrated-2d-dynamic/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-calibrated-2d-height-corridor / recover.mp4 | [MP4](../results/reference/probe-calibrated-2d-height-corridor/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-calibrated-2d-large-change / recover.mp4 | [MP4](../results/reference/probe-calibrated-2d-large-change/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-calibrated-2d-static / recover.mp4 | [MP4](../results/reference/probe-calibrated-2d-static/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-calibrated-3d-corridor / recover.mp4 | [MP4](../results/reference/probe-calibrated-3d-corridor/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-calibrated-3d-dynamic / recover.mp4 | [MP4](../results/reference/probe-calibrated-3d-dynamic/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-calibrated-3d-height-corridor / recover.mp4 | [MP4](../results/reference/probe-calibrated-3d-height-corridor/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-calibrated-3d-large-change / recover.mp4 | [MP4](../results/reference/probe-calibrated-3d-large-change/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
| probe-calibrated-3d-static / recover.mp4 | [MP4](../results/reference/probe-calibrated-3d-static/executions/recover.mp4) | 补充实录／回放；对应指标见同实验GIF行，不新增评分 |
