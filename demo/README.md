# 当前实验入口

本轮以H1动态清图、H2运动畸变、H3长廊参照组织，均重新采集建图A与独立定位B。

```powershell
./demo/record-hypotheses.ps1 -Suite results/reference/direction-YYYYMMDD-new
```

输出目录须为新目录；脚本顺序录制5场A与5场B，并保存GIF、MP4、指标和输入哈希。[数学表达与伪代码](../docs/HOME.zh-CN.md#hypothesis-math)。

二维建图使用原生二维雷达与轮式里程计，对比Raw累计图和作者SRRG维护图；固定地图B使用AMCL。二维入口不再执行DUFOMap／BeautyMap投影。三维原有Raw／DUFOMap／BeautyMap与GICP保持原配置。

```powershell
./demo/srrg.ps1 -Scene dynamic -Duration 65
./demo/record-methods.ps1 -Scene dynamic -Dimension 2D -Duration 65
./demo/srrg.ps1 -Scene corridor -Landmarks -Duration 65
./demo/record-methods.ps1 -Scene landmark-degradation -Dimension 2D -Duration 72
```

Fast-LIO使用独立IMU与扫描时序变体，不改变原三维测试：先按[编译脚本](../src/scripts/presentation/build_fastlio_study.sh)准备官方ROS2分支；再运行`presentation.ps1 -Flow mapping-fastlio-static -Auto -Record -Duration 45`，用[评分脚本](../src/scripts/presentation/score_fastlio_study.py)冻结地图，最后运行`record-methods.ps1 -Dimension 3D -FastLioMaps -Scene static -Duration 60`。每次必须等上一场完成；输出与配置写入`results/runs/presentation`。

[当前录像目录](gallery.html)按H1／H2／H3排列；[完整协议](../docs/testing/MAPPING-FOCUS.zh-CN.md)与[首页指标](../docs/HOME.zh-CN.md#practice-index)对应。镜面保留为实物开放问题。

`mapping-demo.ps1 -Dimension 2D`也会进入Raw／SRRG原生二维分支；`-Dimension 3D -Method all|raw|dufomap|beautymap`继续使用原三维入口。

三维原基线录制：`record-methods.ps1 -Scene static|dynamic|degradation -Dimension 3D`；旧参数与原始结果保持不变。[较早录像档案](archive-20261014.html)。
