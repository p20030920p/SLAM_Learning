# 实验入口

| 栏目 | 内容 | 录像与指标 |
| --- | --- | --- |
| Practice | Related works中的论文方法实践 | [实验目录](../docs/HOME.zh-CN.md#practice-index) · [MP4](gallery.html) |
| Hypothesis test | 本库自写清图、去畸变与约束保留方法 | [实验目录](../docs/HOME.zh-CN.md#hypothesis-test-index) · [MP4](hypotheses.html) |

自写假设实验重新采集静态、动态、运动、长廊各一组A/B。A只读二维扫描、轮式里程计和固定起点；冻结地图后，各方法共享另一次B采集和AMCL参数。

```powershell
./demo/record-own-hypotheses.ps1 -Suite results/reference/own-hypotheses-YYYYMMDD-new
```

输出必须使用新目录，`-Resume`只续录未完成的场次。[自写算法](../src/slam_learning/runtime/own_mapping.py) · [数学表达与伪代码](../docs/HOME.zh-CN.md#hypothesis-math)。

论文方法实践入口：

```powershell
./demo/srrg.ps1 -Scene dynamic -Duration 65
./demo/record-methods.ps1 -Scene dynamic -Dimension 2D -Duration 65
./demo/presentation.ps1 -Flow mapping-fastlio-static -Auto -Record -Duration 45
./demo/record-methods.ps1 -Scene static -Dimension 3D -FastLioMaps -Duration 65
```

SRRG二维组使用原生二维雷达；原三维Raw／DUFOMap／BeautyMap与GICP测试保留。FAST-LIO地图评分与冻结步骤见[评分脚本](../src/scripts/presentation/score_fastlio_study.py)。每次等待上一场结束后再启动下一场。
