# 近期方向与结构阅读

[English](LITERATURE.md) | 中文

文献截止 2026 年 10 月 7 日。“活跃方向”表示有多项近期代表工作，不是引用量热度排名。核心工作按地图更新决策选择，不能对不同任务直接排排行榜。

## 方向 1–2 的活跃主题

| 方向 | 原始来源 | 机会与复现取舍 |
| --- | --- | --- |
| 动态场景中的相机／对象联合估计 | [DynoSAM，2025](https://arxiv.org/abs/2501.11893)、[源码](https://github.com/ACFR-RPG/DynoSAM) | 区分相机和对象运动；完整集成比更新接口实验耗时 |
| 学习几何与稠密视觉 SLAM | [MASt3R-SLAM，CVPR 2025](https://edexheim.github.io/mast3r-slam/)、[源码](https://github.com/rmurai0610/MASt3R-SLAM)；[DyPho-SLAM，2025](https://arxiv.org/html/2509.00741v1) | 几何先验／丰富地图不自动解决过期对象有效性 |
| 开放词汇三维对象与场景图 | 下列 ConceptGraphs、HOV-SG、DovSG | 连接定位与语言查询；空间对应依赖位姿／地图接口 |
| 长期时空地图 | 下列 Khronos、SuperMap、PerSeM | 已有可见性和记忆，因此创新问题需要更窄 |

[AnyLoc](https://arxiv.org/abs/2308.00688)、[Revisit Anything](https://arxiv.org/abs/2409.18049) 是相关视觉地点识别例子。召回依赖数据集与正样本定义，本库不沿用历史分数，未做新的 VPR 运行。

## 八篇核心工作

| 工作 | 论文证据 | 结构推断 | 已有保护／边界 |
| --- | --- | --- | --- |
| [DUFOMap，2024](https://arxiv.org/html/2403.01449v1) | III-A/B：观测自由空间与传感器／位姿容差；IV-C：`d_p=1` | 使用给定扫描位姿清图，容差不等于共享残差协方差 | 已考虑位姿误差并比较位姿来源，不能说它“不管噪声” |
| [BeautyMap，2024](https://arxiv.org/html/2405.07283v1) | III：二进制占据与射线修正／保护；表 I 用 HA | 配准后不一致可以来自位姿误差或环境变化 | 已保护可见性错误，承认地面层级局限 |
| [ConceptGraphs，ICRA 2024](https://arxiv.org/html/2309.16650v1) | 几何重叠与语义相似度关联对象，然后融合点和特征 | 世界坐标对齐错误可能先造成实例碎片化或合并 | 语义帮助关联，不能据此说所有语义地图假设静态世界 |
| [HOV-SG，RSS 2024](https://arxiv.org/html/2403.17846v2) | III-A：准确里程计投影／融合；IV-C：外部 LiDAR SLAM | 图和导航几何继承位姿接口质量 | 外部里程计／回环是保护，本库未实测其敏感性 |
| [Khronos，2024](https://arxiv.org/html/2402.13817v2) | IV：局部一致性；V-B：联合位姿／片段／背景优化；V-C：区分缺少证据 | 修正前的候选生成与局部一致性仍有影响 | **反例：** 已有联合优化、历史和可见性，不能归为固定姿态独立清图 |
| [DovSG，2024 预印本／2025 论文](https://arxiv.org/html/2410.11989v2) | III-D：ACE、匹配和 ICP 重定位后局部更新 | 错误重定位可能影响关联与过期体素处理 | 明确支持动态局部更新，反驳“场景图都静态” |
| [SuperMap，2026 年 8 月](https://arxiv.org/html/2608.22896v1) | III：条件于位姿；IV：深度观测状态与递归证据 | 展示的模型值得检查共享位姿协方差与校准 | 已区分可观测、不可观测、消失；未展示某公式不等于代码缺陷 |
| [PerSeM，2026 年 9 月预印本](https://arxiv.org/html/2609.19542v2) | 3.1/3.2：长期世界体素；5：漂移／相关误差 | 标签稳定不保证几何证据分配正确 | 已有记忆和修正；相关几何是作者承认的局限 |

共同接口只限于“先建立空间对应，再解释地图证据”。这些论文不是一个算法，多个工作已缓解相关问题。候选问题关注剩余共享几何不确定性与不可逆更新的置信度。首个语义子集已执行；实测共性仍需标注和位姿误差对照。

## 代码可得性与复现范围

DUFOMap、BeautyMap 有可执行作者实现与小型公开标注数据，固定提交见 [upstreams.json](../configs/upstreams.json)。ConceptGraphs 的 class-agnostic 前端已处理 40 次提供位姿的 Replica 观测，见[源码／参数](../configs/semantic.json)、[边界](SEMANTIC.zh-CN.md)。其余核心工作做了阅读，未新近复现。

[SuperMap 仓库](https://github.com/superxslam/SuperMap)在检查提交 `ec95b1d50a458645b2669836e2c431f1e957bbc6` 时，仅有 README、论文、演示，没有实现、依赖文件与可运行例程，安装文字不构成该快照下的复现配方。PerSeM 是近期预印本，不当作独立验证过的成熟基线。

先复现可检查的接口和负面对照，再进入真实语义前端；不能把合成对象位置包装成语义导航结果。[阶段安排](PLAN.zh-CN.md)。
