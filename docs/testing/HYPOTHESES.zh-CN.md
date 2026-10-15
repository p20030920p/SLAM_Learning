# 从失效录像提出假设，再做简单实验

本页为此前**定位层探索**：地图冻结。当前研究已收窄到[地图层问题与M1–M5](MAPPING-FOCUS.zh-CN.md)，本页Depth实验不能作为时序深度建图门控的验证。

此前地图清理没有稳定降低定位误差，原走廊的三维GICP还出现发散与输出中断。这提示需要研究“什么时候还能信任匹配、缺少什么观测、怎样找回位置并确认恢复”，而不只是继续删地图点。[此前证据与原因分析](MAP-2D-3D.zh-CN.md)。

下面是本项目自写的小原型，用来检验方向，不是新增论文方法的复现。正式重测前保存[统一高度基准后的协议与源代码哈希](../../results/analysis/hypotheses/calibrated-protocol.json)；[首轮原型协议](../../results/analysis/hypotheses/protocol.json)及全部失败／无效结果也保留。

## 先核验坐标基准，再判断方法

首轮自写原型固定z=0。静态三维组的XY误差约0.14cm，但XYZ约9.41cm，几乎全部来自约9.41cm的固定Z偏差。这是原型的参考高度设置错误，不能解释为三维观测或论文清理器无效；同次原生GICP约1.09cm，也没有这个固定z设置。[首轮三维静态记录](../../results/reference/probe-3d-static/record.json)。

实际URDF中三维雷达相对车体的安装高度是0.30m。用建图A已有的传感器位姿和真实外参，计算`T_world_body = T_world_lidar × inverse(T_body_lidar)`，再取车体Z的中位数，四份A均得到约0.09414m。修正后的内部XYZ地图减去这个参考高度，发布位姿时使用同一个A标定高度；原始世界地图与原生参照保持各自坐标一致。定位B不读取真值，也没有把B误差拟合回轨迹。

下面主表展示统一基准后的完整重测。每组保存A位姿矩阵、URDF外参、标定输入和发布日志，可重新检查高度来源。首轮十组作为排查证据保留，不能与重测中的小差异拼成排名。

## H1：先阻止不可靠匹配拖走位姿

假设：动态点和新增障碍只占部分观测时，稳健残差可抑制错误匹配；平行墙导致某个方向缺少约束时，应减少该方向的激光修正，保留轮式里程计预测。可观测性与多源约束的研究动机可参考[RELEAD](https://arxiv.org/abs/2402.18934)，本原型不实现其ESIKF或图优化。

对照是Plain与Guard：两者都使用同一份雷达点图、同一帧点云和轮式里程计预测。Guard增加Huber残差、较小的对应距离、弱特征值方向抑制与里程计正则。这是一个组合保护方案，不能把收益归因到其中某一个零件。若初值沿完全无约束的走廊方向偏了1m，保留里程计只能保留这个偏差，不能凭空恢复绝对位置。

## H2：用二维雷达＋深度相机补上高度线索

假设：二维雷达看不到的高处边缘、悬挂物或立体轮廓，可能给深度相机提供额外的位置约束。若相机看到的仍是相同的平行墙，增加点数不等于增加信息；视场、量程、时间配对和静态结构可见性都是前提。

Guard与Depth只有额外深度约束这一项差别，使用独立的深度地图A和同一帧B深度返回；每个传感器的残差组分别归一化，避免用大量像素数量压过雷达。深度帧与雷达最多相差0.12s，并用轮式里程计补偿到雷达时刻。过期或没有有效返回时不强行融合，保留使用比例。

深度来自真正的Gazebo `depth_camera`，配置参考[官方深度相机示例](https://github.com/gazebosim/gz-sim/blob/gz-sim8/examples/worlds/depth_camera_sensor.sdf)：320×240，水平80°，0.25–4m，10Hz请求频率。二维B机器人URDF中移除了三维雷达，不能把三维雷达点裁成“深度相机”。本轮未加入真实相机的噪声、反光、透明物体或标定误差模型。

保留原走廊，另加一个明确分开的高度可行性对照：在原走廊加入两块高处几何。地面路线、初值和退化规则不变，A与B都有这两个物体。它检验“有额外高度信息时是否有机会改善”，不能被当作原走廊成绩或一般室内环境的证明。

## H3：从局部匹配转向候选搜索，再确认恢复

假设：局部优化卡在错误位置时，在初始信念附近搜索多个x/y/yaw候选，比一直从同一个错误初值迭代更有机会恢复。候选不仅要匹配得好，还要与其他空间上不同的候选拉开分数差，并在下一次搜索中与里程计运动保持一致。[Cartographer官方算法说明](https://google-cartographer-ros.readthedocs.io/en/latest/algo_walkthrough.html)介绍了候选搜索与局部精配准的组合；本原型使用简单网格搜索，不实现它的分支定界或完整后端。

比较Guard与LiDAR Search，以及Depth与Depth + Search。搜索范围为当前信念附近±2m、±30°；间隔至少3s。匹配分数达到0.65、不同位置候选差至少0.025，且连续两次的地图／里程计对齐相差小于0.25m、8°后才接受。启动未确认、匹配残差偏大、有效对应不足或信息矩阵降秩时才搜索。接受事件是算法决定，是否真正恢复必须另由独立真值的持续误差标准判断。

## 实验边界与测试方式

- 原有四场景保留：纯静态、运动障碍物、持久结构变化、原走廊退化；第五个高度对照单独标注。前三类90仿真秒，两个走廊120秒；雷达在准备期及录屏起始后50仿真秒受限，随后恢复，深度相机仍保持4m量程。
- 每场景分别录制二维雷达＋深度、16线三维雷达＋深度。五个原型共享完全相同的帧ID、点数组和轮式里程计；另保留同源输入的原生AMCL／GICP参照。原生节点独立消费消息，不能将它们与原型的差异全部解释为新想法的效果。
- 五个原型都估计地面机器人的x/y/yaw，z固定为A标定高度、roll和pitch固定为0；三维组确实使用XYZ表面残差，但不是完整六自由度SLAM。原生GICP仍发布其完整位姿。三维表同时保留XYZ／旋转评分，这一运动先验本身也是与原生算法的差别。固定高度与姿态只适合本轮平坦地面条件。
- 原生二维AMCL使用同源点云的5cm栅格投影及一格膨胀，原型直接匹配二维雷达点图；因此两者差值还包含地图表示与观测模型的影响。小原型之间的配对更适合判断H1–H3。
- 所有定位器只估计位姿；自动巡航由同一轮式里程计路线控制，定位输出没有参与导航闭环。
- 建图A使用给定位姿；定位B不读取真值。持久变化复用静态A，地图冻结。H1检验拒绝不一致观测，不执行新墙确认或地图更新。
- 建图A同时保留三维雷达参照，并用其给定位姿与外参审计车体高度；二维原型匹配的是独立二维雷达点图与深度点图。这里验证的是二维雷达＋深度的定位输入可行性，尚未验证仅靠廉价传感器自主完成建图与高度估计。
- 二维报XY RMSE，三维报XYZ RMSE，不做轨迹空间拟合。每次发布输出与0.05s内的独立Gazebo真值配对；首次评分是已经计算出的位姿，不额外虚构未发布初始信念。缺失输出不补零，并单独统计输出覆盖。
- 观察者启动边界漏收的原型消息可从实际发布日志重新与真值配对，原始观察者CSV另存，修复记录明确列出；算法自身未发布的时段始终不填补。原生AMCL的保留初始位姿按其真实Transient Local QoS接收，重复消息去重。
- 沿用恢复标准：观测恢复后XY<0.1m、|yaw|<5°连续5s且至少8次更新。这里只测试初始信念偏移的纠正，没有实际搬动机器人；不是任意全局绑架恢复。
- 这是理想仿真的单轮可行性实验。毫米或厘米级数值不能直接承诺实体效果，微小差别不构成方法排名。
- 定位器在录屏准备阶段已经运行；若确认发生在录屏开始前，视频呈现其后续跟踪差异，完整起始误差和接受时刻以CSV、误差曲线和候选日志为准。

## 简单实验结果

正式批次完成后，下面按二维、三维分开展示全部场景；每段先列三列表格，再放真实Gazebo＋RViz＋终端录像。[全部实验视频目录](../../demo/hypotheses.html)。

<!-- PROBE_RESULTS -->

<a id="hypothesis-experiment-index"></a>

| 场景 | 2D＋深度 | 3D＋深度 |
| --- | --- | --- |
| 纯静态 | [查看实验](#probe-calibrated-2d-static) | [查看实验](#probe-calibrated-3d-static) |
| 运动障碍物 | [查看实验](#probe-calibrated-2d-dynamic) | [查看实验](#probe-calibrated-3d-dynamic) |
| 持久结构变化 | [查看实验](#probe-calibrated-2d-large-change) | [查看实验](#probe-calibrated-3d-large-change) |
| 原走廊退化 | [查看实验](#probe-calibrated-2d-corridor) | [查看实验](#probe-calibrated-3d-corridor) |
| 高处标志 · 派生对照 | [查看实验](#probe-calibrated-2d-height-corridor) | [查看实验](#probe-calibrated-3d-height-corridor) |

[粗到细补充实验](#probe-refinement-index)

[结果解释与后续方向](#hypothesis-findings)

本轮固定同源Raw图，五个原型严格共享已配对输入。红Plain、黄Guard、橙Depth、紫雷达搜索、绿深度＋搜索、蓝原生AMCL／GICP。二维报XY，三维报XYZ；单轮结果不构成稳定排名。

### 2D · 真实窗口实验

<a id="probe-calibrated-2d-static"></a>

#### 纯静态 · 2D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + AMCL | 同源二维栅格投影图 | XY RMSE 6.82 cm |
| Plain ICP | 二维雷达点图 | XY RMSE 0.15 cm |
| H1 · Guard | 二维雷达点图 | XY RMSE 0.15 cm；接近Plain |
| H2 · Guard＋Depth | 二维雷达点图＋深度点图 | XY RMSE 0.21 cm；较Guard高0.06 cm |
| H3 · 雷达搜索 | 二维雷达点图 | XY RMSE 0.15 cm；接近Guard |
| H3 · 深度＋搜索 | 二维雷达点图＋深度点图 | XY RMSE 0.21 cm；接近Depth |

五原型各264帧；有效深度219/264帧；原生参照287次输出。车体高度由建图A标定。

原生参照最后一次有效输出在仿真73.2s，原型记录至99.4s；无输出时段未填补，其RMSE只覆盖已有输出。

![纯静态 · 2D · 真实窗口](../../results/reference/probe-calibrated-2d-static/execution.gif)

[MP4](../../results/reference/probe-calibrated-2d-static/execution.mp4) · [record](../../results/reference/probe-calibrated-2d-static/record.json) · [CSV](../../results/reference/probe-calibrated-2d-static/recover-samples.csv)

<a id="probe-calibrated-2d-dynamic"></a>

#### 运动障碍物 · 2D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + AMCL | 同源二维栅格投影图 | XY RMSE 7.08 cm |
| Plain ICP | 二维雷达点图 | XY RMSE 0.37 cm |
| H1 · Guard | 二维雷达点图 | XY RMSE 0.19 cm；较Plain低0.18 cm |
| H2 · Guard＋Depth | 二维雷达点图＋深度点图 | XY RMSE 0.18 cm；接近Guard |
| H3 · 雷达搜索 | 二维雷达点图 | XY RMSE 0.19 cm；接近Guard |
| H3 · 深度＋搜索 | 二维雷达点图＋深度点图 | XY RMSE 0.18 cm；接近Depth |

五原型各265帧；有效深度181/265帧；原生参照292次输出。车体高度由建图A标定。

原生参照最后一次有效输出在仿真72.3s，原型记录至99.7s；无输出时段未填补，其RMSE只覆盖已有输出。

![运动障碍物 · 2D · 真实窗口](../../results/reference/probe-calibrated-2d-dynamic/execution.gif)

[MP4](../../results/reference/probe-calibrated-2d-dynamic/execution.mp4) · [record](../../results/reference/probe-calibrated-2d-dynamic/record.json) · [CSV](../../results/reference/probe-calibrated-2d-dynamic/recover-samples.csv)

<a id="probe-calibrated-2d-large-change"></a>

#### 持久结构变化 · 2D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + AMCL | 同源二维栅格投影图 | XY RMSE 6.28 cm |
| Plain ICP | 二维雷达点图 | XY RMSE 7.98 cm |
| H1 · Guard | 二维雷达点图 | XY RMSE 0.49 cm；较Plain低7.49 cm |
| H2 · Guard＋Depth | 二维雷达点图＋深度点图 | XY RMSE 0.49 cm；接近Guard |
| H3 · 雷达搜索 | 二维雷达点图 | XY RMSE 0.49 cm；接近Guard |
| H3 · 深度＋搜索 | 二维雷达点图＋深度点图 | XY RMSE 0.49 cm；接近Depth |

五原型各263帧；有效深度187/263帧；原生参照288次输出。车体高度由建图A标定。

原生参照最后一次有效输出在仿真71.3s，原型记录至99.3s；无输出时段未填补，其RMSE只覆盖已有输出。

旧图保持冻结；此处检验不一致观测的处理，没有执行地图更新。

![持久结构变化 · 2D · 真实窗口](../../results/reference/probe-calibrated-2d-large-change/execution.gif)

[MP4](../../results/reference/probe-calibrated-2d-large-change/execution.mp4) · [record](../../results/reference/probe-calibrated-2d-large-change/record.json) · [CSV](../../results/reference/probe-calibrated-2d-large-change/recover-samples.csv)

<a id="probe-calibrated-2d-corridor"></a>

#### 原走廊退化 · 2D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + AMCL | 同源二维栅格投影图 | XY RMSE 100.61 cm；恢复后45.7 s持续收敛 |
| Plain ICP | 二维雷达点图 | XY RMSE 1037.69 cm；未持续收敛 |
| H1 · Guard | 二维雷达点图 | XY RMSE 100.48 cm；较Plain低937.21 cm；未持续收敛 |
| H2 · Guard＋Depth | 二维雷达点图＋深度点图 | XY RMSE 100.54 cm；较Guard高0.06 cm；未持续收敛 |
| H3 · 雷达搜索 | 二维雷达点图 | XY RMSE 70.40 cm；较Guard低30.08 cm；恢复后5.8 s持续收敛 |
| H3 · 深度＋搜索 | 二维雷达点图＋深度点图 | XY RMSE 70.44 cm；较Depth低30.11 cm；恢复后5.8 s持续收敛 |

五原型各338帧；有效深度195/338帧；原生参照600次输出。车体高度由建图A标定。

![原走廊退化 · 2D · 真实窗口](../../results/reference/probe-calibrated-2d-corridor/execution.gif)

[MP4](../../results/reference/probe-calibrated-2d-corridor/execution.mp4) · [record](../../results/reference/probe-calibrated-2d-corridor/record.json) · [CSV](../../results/reference/probe-calibrated-2d-corridor/recover-samples.csv)

<a id="probe-calibrated-2d-height-corridor"></a>

#### 高处标志 · 派生对照 · 2D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + AMCL | 同源二维栅格投影图 | XY RMSE 67.00 cm；恢复后11.7 s持续收敛 |
| Plain ICP | 二维雷达点图 | XY RMSE 285.54 cm；未持续收敛 |
| H1 · Guard | 二维雷达点图 | XY RMSE 101.15 cm；较Plain低184.39 cm；未持续收敛 |
| H2 · Guard＋Depth | 二维雷达点图＋深度点图 | XY RMSE 100.77 cm；较Guard低0.38 cm；未持续收敛 |
| H3 · 雷达搜索 | 二维雷达点图 | XY RMSE 70.93 cm；较Guard低30.22 cm；恢复后5.0 s持续收敛 |
| H3 · 深度＋搜索 | 二维雷达点图＋深度点图 | XY RMSE 21.15 cm；较Depth低79.61 cm；恢复后0.2 s持续收敛 |

五原型各345帧；有效深度239/345帧；原生参照620次输出。车体高度由建图A标定。

此场景额外加入两块高处几何，作为结构互补的可行性对照；与原走廊分别报告。

![高处标志 · 派生对照 · 2D · 真实窗口](../../results/reference/probe-calibrated-2d-height-corridor/execution.gif)

[MP4](../../results/reference/probe-calibrated-2d-height-corridor/execution.mp4) · [record](../../results/reference/probe-calibrated-2d-height-corridor/record.json) · [CSV](../../results/reference/probe-calibrated-2d-height-corridor/recover-samples.csv)

### 3D · 真实窗口实验

<a id="probe-calibrated-3d-static"></a>

#### 纯静态 · 3D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + GICP | 三维雷达点图 | XYZ RMSE 1.08 cm |
| Plain ICP | 三维雷达点图 | XYZ RMSE 0.12 cm |
| H1 · Guard | 三维雷达点图 | XYZ RMSE 0.12 cm；接近Plain |
| H2 · Guard＋Depth | 三维雷达点图＋深度点图 | XYZ RMSE 0.21 cm；较Guard高0.09 cm |
| H3 · 雷达搜索 | 三维雷达点图 | XYZ RMSE 0.12 cm；接近Guard |
| H3 · 深度＋搜索 | 三维雷达点图＋深度点图 | XYZ RMSE 0.21 cm；接近Depth |

五原型各266帧；有效深度184/266帧；原生参照994次输出。车体高度由建图A标定。

![纯静态 · 3D · 真实窗口](../../results/reference/probe-calibrated-3d-static/execution.gif)

[MP4](../../results/reference/probe-calibrated-3d-static/execution.mp4) · [record](../../results/reference/probe-calibrated-3d-static/record.json) · [CSV](../../results/reference/probe-calibrated-3d-static/recover-samples.csv)

<a id="probe-calibrated-3d-dynamic"></a>

#### 运动障碍物 · 3D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + GICP | 三维雷达点图 | XYZ RMSE 1.39 cm |
| Plain ICP | 三维雷达点图 | XYZ RMSE 0.17 cm |
| H1 · Guard | 三维雷达点图 | XYZ RMSE 0.13 cm；较Plain低0.04 cm |
| H2 · Guard＋Depth | 三维雷达点图＋深度点图 | XYZ RMSE 0.13 cm；接近Guard |
| H3 · 雷达搜索 | 三维雷达点图 | XYZ RMSE 0.13 cm；接近Guard |
| H3 · 深度＋搜索 | 三维雷达点图＋深度点图 | XYZ RMSE 0.13 cm；接近Depth |

五原型各258帧；有效深度154/258帧；原生参照951次输出。车体高度由建图A标定。

![运动障碍物 · 3D · 真实窗口](../../results/reference/probe-calibrated-3d-dynamic/execution.gif)

[MP4](../../results/reference/probe-calibrated-3d-dynamic/execution.mp4) · [record](../../results/reference/probe-calibrated-3d-dynamic/record.json) · [CSV](../../results/reference/probe-calibrated-3d-dynamic/recover-samples.csv)

<a id="probe-calibrated-3d-large-change"></a>

#### 持久结构变化 · 3D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + GICP | 三维雷达点图 | XYZ RMSE 1.25 cm |
| Plain ICP | 三维雷达点图 | XYZ RMSE 3.69 cm |
| H1 · Guard | 三维雷达点图 | XYZ RMSE 0.24 cm；较Plain低3.45 cm |
| H2 · Guard＋Depth | 三维雷达点图＋深度点图 | XYZ RMSE 0.35 cm；较Guard高0.11 cm |
| H3 · 雷达搜索 | 三维雷达点图 | XYZ RMSE 0.24 cm；接近Guard |
| H3 · 深度＋搜索 | 三维雷达点图＋深度点图 | XYZ RMSE 0.35 cm；接近Depth |

五原型各264帧；有效深度163/264帧；原生参照950次输出。车体高度由建图A标定。

旧图保持冻结；此处检验不一致观测的处理，没有执行地图更新。

![持久结构变化 · 3D · 真实窗口](../../results/reference/probe-calibrated-3d-large-change/execution.gif)

[MP4](../../results/reference/probe-calibrated-3d-large-change/execution.mp4) · [record](../../results/reference/probe-calibrated-3d-large-change/record.json) · [CSV](../../results/reference/probe-calibrated-3d-large-change/recover-samples.csv)

<a id="probe-calibrated-3d-corridor"></a>

#### 原走廊退化 · 3D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + GICP | 三维雷达点图 | XYZ RMSE 397.82 cm；未持续收敛 |
| Plain ICP | 三维雷达点图 | XYZ RMSE 733.38 cm；未持续收敛 |
| H1 · Guard | 三维雷达点图 | XYZ RMSE 100.49 cm；较Plain低632.88 cm；未持续收敛 |
| H2 · Guard＋Depth | 三维雷达点图＋深度点图 | XYZ RMSE 100.62 cm；较Guard高0.12 cm；未持续收敛 |
| H3 · 雷达搜索 | 三维雷达点图 | XYZ RMSE 56.77 cm；较Guard低43.72 cm；恢复后6.2 s持续收敛 |
| H3 · 深度＋搜索 | 三维雷达点图＋深度点图 | XYZ RMSE 57.56 cm；较Depth低43.06 cm；恢复后6.6 s持续收敛 |

五原型各247帧；有效深度122/247帧；原生参照712次输出。车体高度由建图A标定。

原生参照最后一次有效输出在仿真75.6s，原型记录至132.8s；无输出时段未填补，其RMSE只覆盖已有输出。

![原走廊退化 · 3D · 真实窗口](../../results/reference/probe-calibrated-3d-corridor/execution.gif)

[MP4](../../results/reference/probe-calibrated-3d-corridor/execution.mp4) · [record](../../results/reference/probe-calibrated-3d-corridor/record.json) · [CSV](../../results/reference/probe-calibrated-3d-corridor/recover-samples.csv)

<a id="probe-calibrated-3d-height-corridor"></a>

#### 高处标志 · 派生对照 · 3D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + GICP | 三维雷达点图 | XYZ RMSE 512.79 cm；未持续收敛 |
| Plain ICP | 三维雷达点图 | XYZ RMSE 46.60 cm；恢复后8.7 s持续收敛 |
| H1 · Guard | 三维雷达点图 | XYZ RMSE 100.36 cm；较Plain高53.76 cm；未持续收敛 |
| H2 · Guard＋Depth | 三维雷达点图＋深度点图 | XYZ RMSE 100.38 cm；较Guard高0.02 cm；未持续收敛 |
| H3 · 雷达搜索 | 三维雷达点图 | XYZ RMSE 47.70 cm；较Guard低52.66 cm；恢复后8.7 s持续收敛 |
| H3 · 深度＋搜索 | 三维雷达点图＋深度点图 | XYZ RMSE 50.79 cm；较Depth低49.59 cm；恢复后12.8 s持续收敛 |

五原型各203帧；有效深度124/203帧；原生参照716次输出。车体高度由建图A标定。

原生参照最后一次有效输出在仿真75.1s，原型记录至132.5s；无输出时段未填补，其RMSE只覆盖已有输出。

此场景额外加入两块高处几何，作为结构互补的可行性对照；与原走廊分别报告。

![高处标志 · 派生对照 · 3D · 真实窗口](../../results/reference/probe-calibrated-3d-height-corridor/execution.gif)

[MP4](../../results/reference/probe-calibrated-3d-height-corridor/execution.mp4) · [record](../../results/reference/probe-calibrated-3d-height-corridor/record.json) · [CSV](../../results/reference/probe-calibrated-3d-height-corridor/recover-samples.csv)

<a id="probe-refinement-index"></a>

### 补充假设：粗到细搜索与恢复确认

首轮高处对照出现约20cm平台误差。补充试验将候选平移网格从0.4m细化到0.1m，并把更多已检查位置纳入分数差检验；H1／H2、分数门槛和连续确认规则保持一致。使用上方同一B包的雷达、深度、里程计数组重新推理，下面的视频是保存输出的结果回放。

| 场景 | 2D重算 | 3D重算 |
| --- | --- | --- |
| 原走廊退化 | [2D](#probe-calibrated-refinement-2d-corridor) | [3D](#probe-calibrated-refinement-3d-corridor) |
| 高处标志 · 派生对照 | [2D](#probe-calibrated-refinement-2d-height-corridor) | [3D](#probe-calibrated-refinement-3d-height-corridor) |

<a id="probe-calibrated-refinement-2d-corridor"></a>

#### 2D · 原走廊退化 · 同输入细化

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| 粗搜索·雷达 | 雷达点图 | XY RMSE 70.40 cm；首次输出后61.1s持续收敛 |
| 粗搜索·深度＋雷达 | 雷达点图＋深度点图 | XY RMSE 70.44 cm；首次输出后61.1s持续收敛 |
| 细化·雷达 | 雷达点图 | XY RMSE 70.40 cm；首次输出后61.1s持续收敛 |
| 细化·深度＋雷达 | 雷达点图＋深度点图 | XY RMSE 70.44 cm；首次输出后61.1s持续收敛 |

![原走廊退化 · 2D · 离线重算结果回放](../../results/reference/probe-calibrated-refinement-2d-corridor/result.gif)

[结果回放MP4](../../results/reference/probe-calibrated-refinement-2d-corridor/result.mp4) · [record](../../results/reference/probe-calibrated-refinement-2d-corridor/record.json)

<a id="probe-calibrated-refinement-2d-height-corridor"></a>

#### 2D · 高处标志 · 派生对照 · 同输入细化

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| 粗搜索·雷达 | 雷达点图 | XY RMSE 70.93 cm；首次输出后60.7s持续收敛 |
| 粗搜索·深度＋雷达 | 雷达点图＋深度点图 | XY RMSE 21.15 cm；首次输出后55.9s持续收敛 |
| 细化·雷达 | 雷达点图 | XY RMSE 70.93 cm；首次输出后60.7s持续收敛 |
| 细化·深度＋雷达 | 雷达点图＋深度点图 | XY RMSE 16.20 cm；首次输出后3.3s持续收敛 |

![高处标志 · 派生对照 · 2D · 离线重算结果回放](../../results/reference/probe-calibrated-refinement-2d-height-corridor/result.gif)

[结果回放MP4](../../results/reference/probe-calibrated-refinement-2d-height-corridor/result.mp4) · [record](../../results/reference/probe-calibrated-refinement-2d-height-corridor/record.json)

<a id="probe-calibrated-refinement-3d-corridor"></a>

#### 3D · 原走廊退化 · 同输入细化

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| 粗搜索·雷达 | 雷达点图 | XYZ RMSE 56.77 cm；首次输出后63.7s持续收敛 |
| 粗搜索·深度＋雷达 | 雷达点图＋深度点图 | XYZ RMSE 57.56 cm；首次输出后64.1s持续收敛 |
| 细化·雷达 | 雷达点图 | XYZ RMSE 56.77 cm；首次输出后63.7s持续收敛 |
| 细化·深度＋雷达 | 雷达点图＋深度点图 | XYZ RMSE 56.84 cm；首次输出后63.7s持续收敛 |

![原走廊退化 · 3D · 离线重算结果回放](../../results/reference/probe-calibrated-refinement-3d-corridor/result.gif)

[结果回放MP4](../../results/reference/probe-calibrated-refinement-3d-corridor/result.mp4) · [record](../../results/reference/probe-calibrated-refinement-3d-corridor/record.json)

<a id="probe-calibrated-refinement-3d-height-corridor"></a>

#### 3D · 高处标志 · 派生对照 · 同输入细化

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| 粗搜索·雷达 | 雷达点图 | XYZ RMSE 47.70 cm；首次输出后66.1s持续收敛 |
| 粗搜索·深度＋雷达 | 雷达点图＋深度点图 | XYZ RMSE 50.79 cm；首次输出后70.2s持续收敛 |
| 细化·雷达 | 雷达点图 | XYZ RMSE 47.70 cm；首次输出后66.1s持续收敛 |
| 细化·深度＋雷达 | 雷达点图＋深度点图 | XYZ RMSE 47.71 cm；首次输出后66.1s持续收敛 |

![高处标志 · 派生对照 · 3D · 离线重算结果回放](../../results/reference/probe-calibrated-refinement-3d-height-corridor/result.gif)

[结果回放MP4](../../results/reference/probe-calibrated-refinement-3d-height-corridor/result.mp4) · [record](../../results/reference/probe-calibrated-refinement-3d-height-corridor/record.json)

<!-- PROBE_RESULTS_END -->

<a id="hypothesis-findings"></a>

## 结果解释：哪些问题被缓解，哪些仍然开放

**H1适合处理部分观测与地图不一致，但存在保护过度。** 持久变化的二维Plain→Guard为7.98→0.49cm，三维为3.69→0.24cm；静态组没有可见收益，动态组差异较小。三维高处走廊中，Guard反而从Plain的46.60变成100.36cm：Plain在视野恢复后8.7s持续收敛，Guard没有。恢复后的实际匹配日志中，Plain为rank=3，Guard/Depth在错误位置仍为rank=2，较小对应门槛和弱方向抑制的组合使它们保留原始偏差。这支持“保底与恢复分工”，不能宣称稳健化必然提高精度，也不能从组合实验断定某一个组件单独导致结果。

**H2的条件是增加能够区分位置的结构。** 原走廊受限阶段，在独立真值处检查，二维151帧、三维76帧的雷达与雷达＋深度都没有达到本协议的满秩阈值。深度看见的主要仍是平行墙；增加XYZ点不产生稳定的沿廊绝对约束。高度对照中，二维深度确实采到2159个高处几何点，而二维雷达为0；但157帧中联合信息仅4帧过满秩阈值，单纯Depth仍保留约1m偏差。此处有弱的可区分信息，局部更新门槛却可能抑制它，需要位置候选机制才能利用。[二维原走廊检查](../../results/analysis/hypotheses/calibrated-2d-corridor-observability.json)、[二维高度检查](../../results/analysis/hypotheses/calibrated-2d-height-corridor-observability.json)。局部满秩也不等于全局位置唯一。

**H3在信息返回后有用，确认规则仍会接受有偏位置。** 原走廊中，雷达搜索在完整视野恢复后二维5.8s、三维6.2s持续收敛；加入深度分别为5.8s、6.6s，没有额外收益。在二维高度对照的仿真8.5s，粗深度搜索分数0.969、分数差0.041，两次确认后仍有20.2cm误差。0.4m网格与弱方向投影会留下半格偏差。相同B数组、相同确认门槛下，0.1m细化及更完整候选检查得到误差0.43cm的候选；持续收敛提前到首次输出后3.3s，完整RMSE为16.20cm，仍包含前几秒的约1m初值误差。首5s之后的XY RMSE为0.60cm。这是条件性正结果，不能推广为任何走廊都能恢复。

**三维高度对照仍有负结果。** 同输入细化没有在视野恢复前收敛；深度细化的XYZ RMSE由50.79降到47.71cm，恢复后延迟由12.8降到8.7s。受限阶段19次搜索只有2次通过几何门槛，发生在11.8s和57.5s，之后一次均无有效深度，确认次数重置。其间可用深度或几何区分度也常不足。这里的限制包括可见性、候选评分与跨帧确认，不是看到高处物体就一定有效；本轮没有为得到正结果而降低0.025分数差门槛。[三维高度检查](../../results/analysis/hypotheses/calibrated-3d-height-corridor-observability.json)。

**工程因素也必须与方法适用性分开。** 首轮XYZ的约9.4cm固定误差来自原型高度基准，校准后静态三维Plain约0.12cm；这不涉及此前论文清理器的适用性。其次，三维高度试验受限段只有45个已处理输入帧，二维有157帧；三维搜索日志出现3.0–4.5s的单次处理耗时。各组内部五原型严格同帧，但不同维度的处理节奏、深度可用率不同，不能据RMSE直接判断二维优于三维。RMSE按已有输出样本等权计算，不是时间积分。原生GICP在两个三维走廊分别于75.6s、75.1s后停止有效发布，而原型仍继续；其RMSE只覆盖已有输出，视频最后一帧的位置不能当成继续定位。

**下一步优先组合已得到支持的部分。** 以Guard维持局部跟踪，以二维雷达＋深度的可区分几何支持有界候选细化，再用独立持续误差标准评估恢复；不把“接受候选”直接当作“已经恢复”。后续尚未实验的方向是：按弱方向信息分配传感器权重、跨多帧累积候选证据、将慢搜索与持续跟踪解耦，以及主动运动去观察端墙或拐角。持久结构变化中的新旧地图分层确认也仍未实现。本轮地图冻结，H1的定位收益不表示完成了在线地图更新。仅廉价传感器自主建图、真实噪声/标定误差、独立多次重复与真实绑架应在后续分别检验。

[统一重测汇总](../../results/analysis/hypotheses/calibrated-summary.json) · [二维高度误差曲线](../../results/analysis/hypotheses/calibrated-2d-height-corridor-errors.png) · [三维高度误差曲线](../../results/analysis/hypotheses/calibrated-3d-height-corridor-errors.png) · [原型坐标错误、旧细化负结果录像](../../demo/hypotheses-diagnostics.html) · [开发／录屏／启动失败的独立档案](../../results/analysis/hypotheses/diagnostics.json)。早期未校准细化曾让二维高度RMSE由21.21变为70.76cm，三维由约22.62变为65.47cm；这些结果保留在诊断页，不能与新重测混用。
