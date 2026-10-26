# 移动底盘在退化与大变动场景下的动态鲁棒定位笔记

整理：zfyyyyy  
更新日期：2026-10-26

[中文](#chinese-notes) · [English](#english-notes)

<a id="chinese-notes"></a>

## 中文

研究目标是在传感器观测退化、动态障碍物干扰和环境布局发生较大变化时，维持移动底盘的可靠定位。以定位为主任务，同时研究建图质量、动态障碍物处理、地图变化和多传感器融合对定位的影响。

本笔记记录研究方向、候选场景和后续待办。场景中的故障原因、方法有效性和候选基线均有待文献核对与实验验证。

### 1 研究方向

- **动态障碍物处理**：研究行人等运动物体对建图和定位的影响，以及动态障碍物去除后能否保留足够的定位参考。
- **视觉定位与语义 SLAM**：关注视觉、语义信息在动态场景中的定位作用，以及语义信息与惯性信息结合的可能性。
- **视觉惯性与多传感器融合**：关注视觉惯性里程计，以及激光雷达、深度相机、轮式里程计等信息的融合。IMU 是否纳入实际系统，需根据硬件条件确认。
- **退化识别与鲁棒定位**：研究环境或传感器退化时，如何判断定位信息是否可靠，以及如何维持连续定位。

### 2 短期目标和长期目标

#### 短期目标

在长廊场景下，使用三维激光雷达、深度相机和经过校准的轮式里程计，建立可重复运行的定位基线，并记录运动过程中的定位和点云地图表现。

| 信息源 | 短期设想 | 待确认事项 |
| --- | --- | --- |
| 激光雷达 | 三维激光雷达 | 雷达类型与型号 |
| 深度相机 | 提供图像和深度观测 | 型号、输出模式和可用数据 |
| 轮式里程计 | 使用经过校准的轮式运动信息 | 传感器形式、标定方法和误差水平 |

**设备待确认**：激光雷达类型尚未确定；轮式传感器的具体形式也需补充。各传感器的时间同步、外参和 IMU 可用性应一并记录。

#### 长期目标

逐步降低传感器配置和观测质量，研究二维激光雷达、深度相机与存在误差的轮式里程计，在弱光、不同障碍物和环境布局变化共同出现时的定位表现。

实验安排建议先分别引入单一退化因素，再研究多种因素叠加，便于判断各因素及其组合对定位的影响。

### 3 退化与大变动的具体含义

为便于设计实验，将问题分成三类：

1. **环境几何退化**：长廊、低密度且高度规律的工厂区域等。重点检查这些场景是否提供足够、可区分的定位约束。
2. **传感器观测退化**：弱光、特殊材料、轮式里程计误差等条件下，分别检查各信息源的输出质量和可用性。
3. **动态干扰与环境布局变化**：分别记录短时间运动、物体位置变化和跨天变化，避免把不同时间尺度的问题混在同一项实验中。

“大变动”需要用明确的场景变化体现，例如：

- 建图过程中有行人持续走动。
- 同一物体的位置或朝向发生变化。
- 跨天后障碍物、家具或设备的分布发生变化。

每组实验应记录变化前后的布局、变化持续时间，以及哪些区域仍可作为定位参考。

### 4 候选场景清单

下表中的现象是待检查的问题，记录项是实验设计建议。

| 编号 | 场景 | 重点检查的问题 | 建议记录的条件 |
| --- | --- | --- | --- |
| S01 | 镜子、水面、工业反光板等特殊材料 | 观测是否缺失或异常，地图与定位是否受影响 | 材料、位置、观测角度和原始数据 |
| S02 | 砖头等障碍物 | 障碍物是否被稳定观测，其尺寸和摆放是否影响结果 | 尺寸、数量、摆放方式和距离 |
| S03 | 长廊中的持续运动 | 运动后是否出现地图错位、定位漂移或跟踪失效 | 路线、速度、运动方向和沿途结构 |
| S04 | 弱光环境 | 深度相机的哪些输出或处理环节仍可用，哪些出现退化 | 光照条件、RGB 图像、深度输出和跟踪状态 |
| S05 | 较小场景中的运动 | 点云是否出现运动畸变，定位是否随运动条件变化 | 线速度、角速度、时间戳和同步状态 |
| S06 | 杂物堆叠的小场景 | 点云鬼影出现于何时，与运动或配准误差是否相关 | 杂物布局、静止与运动对照、点云和轨迹 |
| S07 | 物品摆放不整齐的大型工厂 | 特征匹配是否稳定，布局变化前后是否仍能定位 | 场景范围、物品分布、重复路线和匹配结果 |
| S08 | 低密度且高度规律的工厂区域 | 不同位置的观测能否区分，哪些运动条件下容易失效 | 结构密度、重复结构分布和行驶方向 |
| S09 | 大范围高密度场景 | 在复杂布局中能否保持定位精度和实时性 | 场景规模、障碍物密度、轨迹和处理耗时 |

材料、光照、几何结构、运动条件和布局变化应分别描述。砖头作为障碍物单独记录，其影响需结合尺寸和摆放方式判断。点云“鬼影”“地图失效”等描述也需要配套原始数据，具体成因待验证。

### 5 需要收敛的开放问题

1. 退化环境首先影响哪个环节：传感器观测、特征匹配、位姿估计，还是地图维护？这些影响如何反映到定位结果上？
2. 在长廊和规律重复的工厂区域中，哪些运动方向或轨迹更容易出现定位问题？可增加什么信息进行补充？
3. 当某个传感器的信息不可靠时，如何识别这种情况，并合理调整不同信息源的使用方式？
4. 动态障碍物去除后，是否仍保留足够的稳定结构用于定位？物体移动后留下的旧地图信息应如何处理？
5. 面对跨天和大幅布局变化，如何评价已有地图是否仍然可用，以及定位方法适应变化的能力？

后续应结合文献和复现结果，从这些问题中选出一个边界清楚、能够设计对照实验的问题，再形成可检验的假设。

### 6 文献检索与基线选择计划

原计划的阶段节点为 **11 月 8 日**，年份待确认。该节点前的目标是找到相关论文、明确开放问题并确定基线，争取完成初步复现。

文献检索围绕以下主题展开：

- 退化环境中的移动机器人定位与 SLAM。
- 动态障碍物处理和语义辅助定位。
- 视觉惯性定位与多传感器融合。
- 环境布局变化和长期定位。
- 工厂等工业场景中的定位失效与鲁棒性。

优先关注与 IEEE RAS 相关的会议或期刊论文，并补充能够清楚描述上述问题的资料。具体论文、发表渠道和基线尚待选定。

| 选型维度 | 需要核对的内容 |
| --- | --- |
| 传感器匹配 | 是否支持计划使用的雷达、相机、轮式里程计或 IMU，是否有额外硬件要求 |
| 场景匹配 | 是否研究长廊、弱光、动态障碍物、规律工厂结构或跨天变化 |
| 可复现性 | 是否提供代码、数据、依赖版本和清楚的运行流程 |
| 评价方式 | 是否分别报告定位、建图和运行效率，是否说明失败情形 |
| 实验可行性 | 能否在现有移动底盘上运行，并支持后续对照实验 |

原有选题偏好是寻找覆盖较多目标场景、具有工业难点且实验能够落地的工作。选型时同时核对研究问题是否明确、所需条件是否具备，不只统计场景数量。

### 7 后续实验记录建议

每次实验建议记录：场景与变化方式、传感器配置和标定状态、算法与版本、路线与速度、可用的参考轨迹、运行结果，以及出现异常时的日志和原始数据。

有可靠参考时，记录位置、航向或轨迹误差；同时记录定位丢失的次数与时长、恢复耗时和处理耗时。地图错位、鬼影、动态残留和结构缺失等现象单独保存，便于分析它们与定位结果的关系。具体指标、判定阈值和重复次数需在正式对照实验前确定。

下一步待办：

- [ ] 确认雷达类型、相机型号、轮式传感器形式，以及 IMU、同步和标定条件。
- [ ] 确认 11 月 8 日节点的年份和预期交付内容。
- [ ] 把“地图失效”“鬼影”“弱光下部分功能失效”等现象写成可观察、可记录的问题。
- [ ] 完成相关论文筛选，确定一个可复现、与硬件和场景匹配的基线。
- [ ] 先完成长廊基线，再逐步加入动态障碍物、传感器退化和布局变化。
- [ ] 根据文献与复现结果提出假设，并补充对照实验设计。

<a id="english-notes"></a>

## English

### Robust Localization of a Mobile Robot Base under Degradation and Major Environmental Changes

Prepared by: zfyyyyy  
Updated: 2026-10-26

The objective is to maintain reliable localization of a mobile robot base when sensor observations degrade, dynamic obstacles interfere with perception, or the environment layout changes substantially. Localization is the main task. Mapping quality, dynamic obstacle handling, map changes, and sensor fusion are studied through their effects on localization.

These notes record research directions, candidate scenarios, and next steps. Failure causes, method effectiveness, and candidate baselines require literature review and experimental validation.

### 1 Research Directions

- **Dynamic obstacle handling**: Study how moving objects, such as pedestrians, affect mapping and localization, and whether removing them preserves enough reference structure for localization.
- **Visual localization and semantic SLAM**: Examine the role of visual and semantic information in dynamic environments, including possible combinations of semantic and inertial information.
- **Visual inertial estimation and sensor fusion**: Consider visual inertial odometry and the fusion of LiDAR, depth camera, and wheel odometry information. Whether an IMU is included in the actual system depends on the available hardware.
- **Degradation detection and robust localization**: Investigate how to assess the reliability of localization information and maintain continuous localization when the environment or sensors degrade.

### 2 Short Term and Long Term Goals

#### Short Term Goal

Establish a repeatable localization baseline in a corridor using 3D LiDAR, a depth camera, and calibrated wheel odometry. Record localization behavior and point cloud map quality while the robot moves.

| Information source | Initial configuration | Details to confirm |
| --- | --- | --- |
| LiDAR | 3D LiDAR | LiDAR type and model |
| Depth camera | Image and depth observations | Model, output modes, and available data |
| Wheel odometry | Calibrated wheel motion information | Sensor type, calibration procedure, and error level |

**Hardware details to confirm**: The LiDAR type and the specific wheel sensing hardware remain to be confirmed. Record time synchronization, extrinsic calibration, and IMU availability as well.

#### Long Term Goal

Gradually reduce the sensor configuration and observation quality. Study localization with 2D LiDAR, a depth camera, and imperfect wheel odometry when low light, different obstacles, and environment layout changes occur together.

A suggested experimental sequence is to introduce individual degradation factors first and then combine them, so their individual and combined effects on localization can be assessed.

### 3 Defining Degradation and Major Changes

For experiment design, separate the problems into three categories:

1. **Geometric degradation**: Corridors and sparse factory areas with highly repetitive structure. Check whether these scenes provide sufficient and distinguishable localization constraints.
2. **Degradation of sensor observations**: Under low light, unusual materials, or wheel odometry errors, examine the output quality and availability of each information source separately.
3. **Dynamic interference and environment layout changes**: Record transient motion, object relocation, and changes across days separately, rather than combining different time scales in one experimental condition.

Define major changes through explicit scene modifications, for example:

- Pedestrians continuously moving while a map is being built.
- A change in the position or orientation of an object.
- Changes in the distribution of obstacles, furniture, or equipment across days.

For each experiment, record the layouts before and after the change, how long the change persists, and which areas remain usable as localization references.

### 4 Candidate Scenarios

The phenomena below are questions to investigate. The recording items are suggestions for experiment design.

| ID | Scenario | Main question | Suggested conditions to record |
| --- | --- | --- | --- |
| S01 | Mirrors, water surfaces, and industrial reflectors | Are observations missing or abnormal, and are mapping and localization affected? | Material, position, viewing angle, and raw data |
| S02 | Obstacles such as bricks | Are the obstacles observed consistently, and do their size and placement affect the result? | Size, count, placement, and distance |
| S03 | Sustained motion through a corridor | Does motion lead to map misalignment, localization drift, or tracking failure? | Route, speed, travel direction, and surrounding structure |
| S04 | Low light | Which depth camera outputs or processing stages remain usable, and which degrade? | Lighting conditions, RGB images, depth output, and tracking state |
| S05 | Motion in a small scene | Does the point cloud exhibit motion distortion, and does localization change with the motion conditions? | Linear and angular velocity, timestamps, and synchronization state |
| S06 | A small scene with stacked clutter | When does point cloud ghosting occur, and is it related to motion or registration errors? | Clutter layout, stationary and moving comparisons, point clouds, and trajectories |
| S07 | A large factory with irregularly arranged items | Is feature matching stable, and can the system localize before and after layout changes? | Scene extent, item distribution, repeated routes, and matching results |
| S08 | Sparse factory areas with highly repetitive structure | Can observations from different locations be distinguished, and under which motion conditions does localization fail? | Structure density, distribution of repeated structures, and travel direction |
| S09 | Large and densely occupied scenes | Can localization accuracy and real time operation be maintained in complex layouts? | Scene scale, obstacle density, trajectories, and processing time |

Describe material, lighting, geometry, motion, and layout changes separately. Record bricks as a distinct obstacle case and assess their effects according to size and placement. Descriptions such as point cloud ghosting or map failure also need supporting raw data; their causes remain to be verified.

### 5 Open Questions to Refine

1. Which stage is affected first by degradation: sensor observation, feature matching, pose estimation, or map maintenance? How does this affect the localization result?
2. In corridors and repetitive factory areas, which motion directions or trajectories are more likely to cause localization problems? What additional information could help?
3. When information from a sensor becomes unreliable, how can this be detected, and how should the use of different information sources be adjusted?
4. After dynamic obstacles are removed, does enough stable structure remain for localization? How should obsolete map information be handled after an object moves?
5. With changes across days or substantial layout changes, how should the usability of an existing map and the adaptability of a localization method be evaluated?

Use the literature and reproduction results to select a clearly bounded question that supports controlled comparisons, and then formulate a testable hypothesis.

### 6 Literature Review and Baseline Selection Plan

The original milestone is **November 8**, with the year to be confirmed. The intended deliverables by that date are relevant papers, a defined open problem, and a selected baseline, ideally with an initial reproduction.

Search around the following topics:

- Mobile robot localization and SLAM in degraded environments.
- Dynamic obstacle handling and semantic assisted localization.
- Visual inertial localization and sensor fusion.
- Environment layout changes and long term localization.
- Localization failures and robustness in industrial settings such as factories.

Prioritize relevant conference and journal papers associated with IEEE RAS, and collect sources that clearly describe these problems. Specific papers, publication venues, and the baseline remain to be selected.

| Selection criterion | What to check |
| --- | --- |
| Sensor compatibility | Support for the planned LiDAR, camera, wheel odometry, or IMU, and any additional hardware requirements |
| Scenario relevance | Coverage of corridors, low light, dynamic obstacles, repetitive factory structures, or changes across days |
| Reproducibility | Available code, data, dependency versions, and clear execution instructions |
| Evaluation | Separate reporting of localization, mapping, and computational performance, with failure cases described |
| Experimental feasibility | Ability to run on the available mobile robot base and support subsequent controlled comparisons |

The initial preference is for work that covers several target scenarios, addresses industrial difficulties, and can be tested with the available resources. Also check whether the research question is clear and the required conditions are available, rather than ranking papers only by the number of scenarios they cover.

### 7 Suggestions for Experiment Records

For each experiment, record the scene and changes, sensor configuration and calibration state, algorithm and version, route and speed, available reference trajectory, results, and the logs and raw data associated with abnormal behavior.

Where a reliable reference is available, record position, heading, or trajectory errors. Also record the number and duration of localization losses, recovery time, and processing time. Save map misalignment, ghosting, residual dynamic objects, and missing structure separately to examine their relationship to localization. Define the exact metrics, decision thresholds, and number of repetitions before formal controlled experiments.

Next steps:

- [ ] Confirm the LiDAR type, camera model, wheel sensing hardware, IMU availability, synchronization, and calibration conditions.
- [ ] Confirm the year and expected deliverables for the November 8 milestone.
- [ ] Convert descriptions such as map failure, ghosting, and partial failure in low light into observable and recordable questions.
- [ ] Review relevant papers and select a reproducible baseline compatible with the hardware and scenarios.
- [ ] Establish the corridor baseline first, then progressively add dynamic obstacles, sensor degradation, and layout changes.
- [ ] Formulate hypotheses from the literature and reproduction results, and develop controlled experiments.
