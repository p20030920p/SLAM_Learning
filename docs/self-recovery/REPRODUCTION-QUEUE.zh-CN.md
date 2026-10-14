# 复现清单（按结构分组）

**选取原则**：不是按论文影响力排，而是按**结构**排——即"它做了什么结构性的改动、这个改动能不能在我们现有的仿真里被检验、上游代码是否真的公开可跑"。每条都给出：代码位置（已核实）、结构核心、怎么喂我们的仿真、怎么复现原库、优先级。

**状态标记**：✅ 已跑通 · 🔄 进行中 · 📋 待办 · ⛔ 无公开代码

---

## A 类｜观测模型结构：把"我有多像这个位姿"这件事换掉

| 方法 | 论文 | 代码（已核实） | 结构核心 | 我们的仿真怎么喂 | 原库复现 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- |
| **IR-MCL** | Kuang et al., RA-L 2023, DOI 10.1109/LRA.2023.3239318 | [PRBonn/ir-mcl](https://github.com/PRBonn/ir-mcl) 140★ @ `aab8c91b37` | 用**神经占据场（NOF）**隐式表示场景，体渲染**合成 2D 扫描**替代占据栅格的似然场，再嵌进 MCL | 我们的 Gazebo 竞技场可导出「激光 + 给定位姿」序列 → 按其 `train.py` 在**我们的地图上重训 NOF** → 用它跑全局定位，与 `nav2_amcl` 同场景对比 | 仓内自带 4 个预训练权重（fr079/intel/mit/ipblab）+ 10 个现成 config；公开数据集已下载校验；**C++ 扩展已编译通过**；上游还自带 `loc_demo.py` 直接出 GIF | **P0** |
| **AdaM-MCL / DSOM** | Chen et al., RA-L 2021, DOI 10.1109/LRA.2021.3061339 | [Runjian-Chen/AdaM_MCL](https://github.com/Runjian-Chen/AdaM_MCL) 12★ @ `e8aedd2bae` | 学一个**可采样的多模态条件位姿分布**（从均匀采样改为在似然高处采样），配**自适应混合 MCL** 在轨切换模式 | 同 IR-MCL：把我们的 2D 激光 + 地图喂进去，做全局定位/绑架恢复 | 仓内自带 `Dataset/` 与 `Trained_models/`；含 `Bicocca/UPO/synthetic` 三个数据集处理器 | **P0（进行中）** |

## B 类｜退化感知的配准/里程计结构：把"哪个方向不能信"显式化

| 方法 | 论文 | 代码 | 结构核心 | 可行性 |
| --- | --- | --- | --- | --- |
| X-ICP | arXiv:2211.16335 | **⛔ 无公开代码**（官方仓搜不到） | 用 scan–map 对应在主优化方向上算六轴可定位性，退化方向受控更新或冻结 | 只能作**方法层对照**，或自实现 2D 同构版（2×2 信息矩阵方向各向异性） |
| LF-GICP | arXiv:2608.19522 | 候选 [ies0411/LF_GICP](https://github.com/ies0411/LF_GICP)（0★，**未核验是否为作者**） | 指出体素 GICP 的协方差正则化**掩盖**退化；无正则化法向可定位性场 + 时间中值门控 | 先核验该仓真伪；否则按方法自实现 |
| GLIM | Koide et al.（体素 GICP / 全局一致） | [koide3/glim](https://github.com/koide3/glim) 1874★（2026-10 仍活跃） | 体素化 GICP + GPU 加速全局配准，工程成熟 | 3D，需要 3D 序列（我们只有 KITTI teaser 与固定安装的 L2） |
| KISS-ICP | RA-L 2023 | [PRBonn/kiss-icp](https://github.com/PRBonn/kiss-icp) 2346★ | 自适应对应阈值，免调参 | 3D，同上；作为强基线引用即可 |

## C 类｜鲁棒后端结构：把"错误约束"变成可关断/可剔除/可撤销

| 方法 | 代码（已核实） | 结构核心 | 怎么在我们这里做 |
| --- | --- | --- | --- |
| **GNC** | [borglab/gtsam](https://github.com/borglab/gtsam) 3749★（内含 GNC）+ [MIT-SPARK/CertifiablyRobustPerception](https://github.com/MIT-SPARK/CertifiablyRobustPerception) 124★ | Black-Rangarajan 对偶 + 渐进非凸，无需初值即可拒绝大量离群约束 | **离线 2D 位姿图**：用现有回放生成位姿图、注入假回环，比较剔除前后误差与恢复耗时 |
| **PCM / DCS / Switchable Constraints** | 同在 GTSAM / g2o 生态 | 集合级一致性（最大团）／残差闭式重加权／开关变量关断 | 同一 2D 位姿图试验台，与 GNC 并列对比 |
| interactive_slam | [koide3/interactive_slam](https://github.com/koide3/interactive_slam) 969★ | **人工/半自动**的事后修正 | 作为"自恢复"的**反面结构**对照：它靠人，我们要求无人干预 |

## D 类｜系统级恢复结构：丢失→新建→重接，或纯定位

| 方法 | 代码（已核实） | 结构核心 | 怎么在我们这里做 |
| --- | --- | --- | --- |
| ORB-SLAM3 | [UZ-SLAMLab/ORB_SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) 9142★ | 多地图 Atlas：跟踪丢失另起新图，重访再合并 | Gazebo 的 RGB-D 流可直接喂；瞬移模拟丢失，返回已建图区域看重定位 |
| Cartographer | [cartographer-project/cartographer](https://github.com/cartographer-project/cartographer) 7987★ | 纯定位模式（地图冻结） | 作"地图不变"的极端对照 |
| **slam_toolbox** | [SteveMacenski/slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) 2672★ | 在线建图/定位，ROS 2 原生 | **录制管线已在用它**做右侧实时建图 |

## E 类｜评测结构

| 资源 | 状态 | 说明 |
| --- | --- | --- |
| **LILocBench**（IROS 2025） | ✅ 评测链已跑通 | 官方示例提交得分 **23.1567**；公开真值覆盖 `static_0 / dynamics_0 / lt_changes_0 / lt_changes_dynamics_0`；**后续要用它评我们自己的结果** |
| DUFOMap / BeautyMap | ✅ 已完成 | 地图侧抑制；Evidence 表已在主页 |
| AnyLoc | 📋 待办 | [AnyLoc/AnyLoc](https://github.com/AnyLoc/AnyLoc) 644★，通用地点识别（视觉）——作跨模态对照 |

---

## 执行顺序（按"结构价值 ÷ 落地成本"排）

| 序 | 目标 | 双重验证 |
| --- | --- | --- |
| 1 | **AdaM-MCL**（A 类） | 原库数据集跑通 + 我们仿真 2D 激光跑通 |
| 2 | **IR-MCL**（A 类） | 公开数据集跑通 + **在我们的竞技场地图上重训 NOF** 再跑 |
| 3 | **四级场景梯度录制**（S1 静态 → S2 动态 → S3 大变动 → S4 退化） | 我们自己的仿真，用原型底盘 |
| 4 | **GNC / PCM / DCS**（C 类） | 离线 2D 位姿图，注入假回环 |
| 5 | **LILocBench 评我们自己的结果** | 把我们的位姿转 TUM + `description.json`，与上游示例 23.1567 对比 |
| 6 | ORB-SLAM3 / Cartographer（D 类） | Gazebo 流直接喂 |

**不做的**（写清原因）：X-ICP（无公开代码）· GLIM / KISS-ICP（3D 数据不够）· 多会话类（无移动平台与长期数据）。
