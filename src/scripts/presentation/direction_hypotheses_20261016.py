"""Three hypotheses aligned to the user's three current open questions."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))
from publish_home_experiments import sections  # noqa: E402

HYP_ZH = """<a id="mapping-hypothesis-tests"></a>

## 假设

<!-- DIRECTION_HYPOTHESES_20261016 -->

三个假设逐一对应现在的三个开放问题。统一检验链是 **输入可靠性／地图处理 → 地图几何与覆盖 → 冻结地图 → 独立 B 定位**；地图更干净不自动代表定位更准。

| 对应问题 | 新假设 | 干预、对照与指标 |
| --- | --- | --- |
| 问题1 · 动态残影 | **H1：在可重复观测、位姿可信且静态约束足够的条件下，动态处理能在限制静态损失的同时减少残影；当残影进入定位匹配区域时，独立定位有机会受益。** | 2D：Raw／SRRG；3D：Raw／DUFOMap／BeautyMap不变。地图看DA、SA、几何误差与覆盖；同一B、同一AMCL／GICP看位置／旋转RMSE、P95、有效输出覆盖和失败。收益必须实测。 |
| 问题2 · 自身运动畸变 | **H2：在相同逐点时间、IMU、外参、扫描和轨迹下，FAST-LIO的点运动补偿能减少快速平移／旋转造成的几何误差；这种改善需要继续由独立定位验证。** | FAST-LIO2正常去畸变 vs 仅关闭点补偿的消融，IMU状态传播保留。分静止、慢转、快转、平移阶段；记录扫描跨度、姿态变化、地图表面误差、里程计误差和覆盖，再冻结地图测试B。 |
| 问题3 · 特殊观测与退化 | **H3：区分“观测不可靠”与“几何缺少约束”，分别采用观测有效性管理和可重复的非对称地标，比统一删点更可能保住地图的定位价值。** | **E3a镜面：**比较缺测标未知与误当自由空间，报告错误占据／错误清空／未知比例及定位；外观识别和真实反射仍需实物验证。**E3b长廊：**原场景 vs 加入雷达可见非对称几何标志的派生场景，同配置建图和定位；看沿廊误差、覆盖、失败及地标处几何覆盖。 |

**实验控制：**原生二维与三维分别报告，不能跨表示排名。SRRG使用作者估计位姿，因此其端到端结果不能单独归因于删除模块。运动物体的运动与机器人自身运动分开。长廊加地标明确改变环境；不能据此声称算法自动消除了所有退化。仅给地图加不存在的点、把缺测补成墙或向算法输入真值，不能作为成功结果。

[新实验、指标与录制](#direction-experiments-20261016) · [完整实验协议](testing/MAPPING-FOCUS.zh-CN.md) · [旧M1／M4／M5版本](testing/MAPPING-FOCUS-20261015.zh-CN.md)

"""
HYP_EN = """<a id="mapping-hypothesis-tests"></a>

## Hypothesis

<!-- DIRECTION_HYPOTHESES_20261016 -->

Each hypothesis addresses one current open question. The common chain is **input reliability/map intervention → map geometry and coverage → frozen map → held-out localization B**. Cleaner maps do not automatically imply better localization.

| Question | New hypothesis | Intervention, controls and metrics |
| --- | --- | --- |
| Q1 · Dynamic traces | **H1: with repeat observations, trustworthy poses and sufficient static constraints, dynamic processing can reduce traces while bounding static loss; held-out localization may benefit when the traces enter its matching region.** | 2D: Raw/SRRG; 3D: unchanged Raw/DUFOMap/BeautyMap. Score DA, SA, geometric error and coverage; same B and AMCL/GICP, reporting position/rotation RMSE, P95, coverage and failures. Measure the benefit. |
| Q2 · Ego-motion distortion | **H2: with identical point timing, IMU, extrinsics, scans and trajectory, FAST-LIO point compensation can reduce geometry errors during fast motion; independent localization must test the downstream benefit.** | Normal FAST-LIO2 vs point-correction-only ablation, keeping IMU state prediction. Separate stationary, slow turn, fast turn and translation phases; log scan span, angular motion, surface error, odometry error and coverage, then freeze maps for B. |
| Q3 · Abnormal observations and weak geometry | **H3: distinguishing unreliable observations from missing geometric constraints, and applying validity management or repeatable asymmetric landmarks respectively, is more likely to preserve localization value than indiscriminate point deletion.** | **E3a mirror:** unknown vs incorrectly free missing returns; false occupancy/clearing, unknown fraction and localization. Visual identification and physical reflections still need hardware validation. **E3b corridor:** original vs derived corridor with LiDAR-visible asymmetric landmarks; same mapping/localization settings, along-corridor error, coverage, failures and landmark support. |

**Controls:** score native 2D and 3D separately. SRRG estimates mapping poses, so end-to-end differences do not isolate its deletion module. Separate object motion from ego-motion. Adding corridor landmarks changes the environment and does not establish universal degeneracy recovery. Invented walls or truth supplied to the estimator cannot establish success.

[New experiments, metrics and recordings](#direction-experiments-20261016) · [Full protocol](docs/testing/MAPPING-FOCUS.md) · [Previous M1/M4/M5 version](docs/testing/MAPPING-FOCUS-20261015.md)

"""

PROTOCOL_ZH = """# 三个开放问题与配套实验

本版按当前首页的三个问题定义H1／H2／H3，取代旧M1／M4／M5作为当前实验组织。旧记录保持原样，不能改名冒充本轮新执行。

## E1 · 动态残影、静态保留与独立定位（H1）

- 场景：现有静态、运动障碍物、长廊；同一Sim2Real全向底盘。
- 二维：原生720束二维雷达＋轮式里程计，Raw累计地图与作者SRRG维护图；移除DUFOMap／BeautyMap二维投影的当前对照。A地图冻结，另起Gazebo会话B，共享扫描和相同AMCL参数。给定起点偏移，不向AMCL输入真值。
- 三维：保持现有Raw／DUFOMap／BeautyMap及GICP实验和记录不变。
- 地图：DA、SA、几何误差、已观测支持覆盖；静态无动态分母时DA=N/A。二维与三维分别评分。
- 定位：共同时间网格上的位置／角度RMSE、P95、有效覆盖、误差超阈比例；同时提供原生更新时间统计。缺失输出不得计作零误差。
- 判断：删除率提高但静态结构丢失，或者独立定位无改善，都不能宣布完整H1成立。SRRG的位姿图和融合同时变化，只能先做端到端观察；还需给定相同位姿的模块隔离实验。

## E2 · FAST-LIO运动畸变消融（H2）

- 使用同一静态场景和机器人，为独立实验变体加入200Hz Gazebo IMU，不修改旧三维测试配置；过滤无效回波，静止3s后才向FAST-LIO发送扫描和IMU。
- 原始gpu_lidar整帧为瞬时采样。适配器从连续三帧真实扫描中各取一个120°扇区，构成有真实分组采样时刻的扫描；没有从真值位姿生成或扭曲点，也不冒充商用雷达的连续扫描模式。
- 同一滚动扫描和IMU同时输入官方ROS2分支FAST-LIO2的两个实例。仅一个实例在IMU预测之后跳过点的反向补偿；保留状态传播、匹配和所有参数。保存补丁和作者版本。
- 录制前静止初始化，随后按固定控制序列静止、慢转、快转、正反平移、停止。先检查IMU数量、逐点时间、输出完整性；配置失败单列诊断，不输出伪造精度。
- 地图：累计共同时间的有限原生注册点云，使用相同5cm体素和参考静态几何（含地面）评价；不按估计世界高度裁剪漂移点。冻结的是注册扫描累计，不冒充ikd-Tree原生导出。
- 位姿：仅用已知起点作一次坐标系对齐，不作整条轨迹最优拟合；真值仅评测。里程计RMSE与冻结地图后的独立B分别报告。
- 独立B：从现有B录制的原生三维扫描中选取与A不重叠的测试会话，在两个冻结FAST-LIO地图上用同一GICP及相同初值；如B不能运行，明确标为未完成，不能以FAST-LIO自身里程计替代。

## E3a · 镜面缺测的边界检验（H3）

实物两图作为动机。先在已知几何中对指定角区删除回波，比较“无效／未知”与“错当最大量程自由射线”的地图更新。记录被清空的真实边界格、未知格和几何覆盖。该受控缺测不是真实镜面物理仿真，也不验证镜面识别器。真实反射、虚像和入射角依赖需要另行采集带原始扫描的视频／数据。

## E3b · 长廊几何干预（H3）

原长廊 vs 在侧壁附近放置两处不对称、真实可见几何标志的派生长廊；保留走行区。二维建图／定位分别重新采集A／B，参数、路线、初始偏移和限束／恢复时刻一致。报告沿廊误差、横向误差、yaw、有效覆盖和前50s限制段指标，避免恢复完整观测掩盖退化段。该对照改变环境，不验证自动识别退化或多传感器融合。

## 记录与判定

每个录像绑定运行输入、作者版本、配置、原生输出、独立真值和媒体哈希。今天的少量运行是探索性结果，不声称预注册或统计显著。后续以多个速度、污染水平、初始偏移和独立重复检验适用范围。首页只列指标解释、数值和分析空位。
"""
PROTOCOL_EN = """# Three open questions and experiments

H1/H2/H3 replace M1/M4/M5 as the current organization. Historical records retain their identity.

## E1 · Dynamic traces and held-out localization (H1)

Use the existing static, dynamic and corridor scenes and Sim2Real omni chassis. Native 2D uses 720-beam scans and wheel odometry: Raw accumulation vs author SRRG maintenance. Remove the projected DUFOMap/BeautyMap arms from current 2D tests. Freeze A, launch separate B, share scans and AMCL settings, and use the same initial offset. Truth is evaluation-only. Keep 3D Raw/DUFOMap/BeautyMap and GICP unchanged.

Report DA/SA, geometric error and observed support, then common-time pose/angular RMSE, P95, valid coverage and failures. DA is N/A without dynamics. Different representations are not ranked together. SRRG changes pose optimization and maintenance together; end-to-end observations do not isolate deletion. Cleaning without downstream improvement does not establish the entire hypothesis.

## E2 · FAST-LIO motion-distortion ablation (H2)

An isolated robot/world variant adds a 200Hz Gazebo IMU. Filter invalid returns and gate both IMU/scans until 3s of settling. Native gpu_lidar scans are instantaneous. Build a sequential scan from three successive measured 120-degree sectors with their actual packet timestamps; no truth-based warping or commercial scan-pattern claim.

Feed identical rolling scans, IMU and extrinsics to two official ROS2 FAST-LIO2 instances. A disclosed ablation skips only backward point correction after IMU state prediction; preserve matching and prediction. Bind the source commit and patch.

After stationary initialization, execute stationary, slow rotation, fast rotation, forward/reverse translation and stop phases. Check timing, IMU coverage and native outputs before scoring. Failures remain diagnostic records. Accumulate finite native registered clouds at matched times with 5cm voxels, including rendered ground and drifted points. Do not crop by estimated world height. This is frozen registered-scan accumulation, not an ikd-Tree export. Align poses only by the known start, never a best-fit trajectory alignment. Report odometry separately from held-out B: same GICP and initial pose on both frozen maps using an independent existing B scan session. Missing B is an explicit incomplete test, never substituted with odometry.

## E3a · Missing returns near a mirror (H3)

The supplied physical images motivate a controlled missing-return test: remove a fixed angular sector in a known scene and compare invalid/unknown handling with incorrectly treating it as maximum-range free rays. Score wrongly cleared real boundary cells, unknown space and geometric support. This is a missing-return control, not physical reflection simulation or a mirror detector. Real multipath, incidence-angle dependence and classification require additional hardware data.

## E3b · Corridor geometry (H3)

Compare the original corridor with a derived scene containing two asymmetric, LiDAR-visible physical side landmarks, leaving the route clear. Recollect A/B with identical parameters, route, initial offset and scan-limit/restoration timing. Score along/across-corridor error, yaw, coverage and the first 50s limited phase separately. The intervention changes the environment; it does not validate automatic degeneracy detection or fusion.

## Evidence

Bind recordings to inputs, source versions, configuration, native outputs, independent truth and media hashes. The few current runs are exploratory, not preregistered or statistically conclusive. Later vary speeds, contamination, offsets and repetitions. Homepage reporting contains metric definitions, values and blank analysis slots.
"""


def publish():
    for zh, path, body in [(True, ROOT / "docs/HOME.zh-CN.md", HYP_ZH), (False, ROOT / "README.md", HYP_EN)]:
        text = path.read_text(encoding="utf-8")
        _, blocks = sections(text)
        heading = "假设" if zh else "Hypothesis"
        text = text.replace(blocks[heading], body, 1)
        path.write_text(text, encoding="utf-8", newline="\n")
        target = ROOT / ("docs/testing/MAPPING-FOCUS.zh-CN.md" if zh else "docs/testing/MAPPING-FOCUS.md")
        archive = target.with_name("MAPPING-FOCUS-20261015" + (".zh-CN" if zh else "") + ".md")
        if not archive.exists():
            archive.write_bytes(target.read_bytes())
        target.write_text(PROTOCOL_ZH if zh else PROTOCOL_EN, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    publish()
