"""Publish title-driven direction analysis without generated figures."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]

DIRECTION_ZH = """### 1. 题目究竟在研究什么？

**方向：动态环境中的鲁棒定位与 SLAM。** 核心问题是：**环境会变化、观测也可能不可靠时，怎样建立几何可信、保留有效静态约束的地图，并检验它能否让定位更准确、更连续？**

| 题目中的词 | 研究对象 | 怎样判断有进展 |
| --- | --- | --- |
| 动态环境 | 运动物体形成的残影，以及物体搬动等持久变化；两者需要不同的时序判断 | 区分短时运动与应当更新的真实结构，检查动态删除和静态保留 |
| 鲁棒定位 | 异常观测、地图失配或几何约束不足时，机器人位姿是否仍可信 | 同时看位置／旋转误差、P95、输出覆盖与失败；当前单轮实验不等于验证了普遍恢复能力 |
| SLAM | 位姿与地图的联合估计；位姿负责对齐观测，地图又为后续定位提供约束 | 既检查地图几何误差与覆盖，也检查独立定位；完整 SLAM 还要验证自估位姿下的闭环表现 |

SLAM 的基础是联合估计位姿与地图。[SLAM 综述](https://arxiv.org/abs/1606.05830)。本轮把建图位姿作为已知条件，先隔离地图层的作用；这项控制不代表完整 SLAM 已经解决。

### 2. 实物问题为什么与题目有关？

[图1的镜面与图2红圈中的建图不全](#physical-test-mirror)给出了具体研究入口：**“环境静止”与“观测可靠”是两个判断。** 镜面／玻璃可能带来缺失回波或反射造成的错误几何，影响地图边界和后续匹配；相关机制见[反射观测研究](https://arxiv.org/abs/2406.10494)。两张图记录了用户指出的现象，具体缺失原因仍需结合原始扫描、覆盖和轨迹做对照。

因此分开处理两条问题线：**运动物体 → 动态残影；静态镜面 → 观测缺失／反射异常。** 前者对应当前清图实验；后者是从实物提出的扩展问题。删掉错误点以后，还必须检查真实结构是否被误删、缺测区域是否仍然未知。

### 3. SLAM 的流程，以及哪些位置重要

**观测 → 预处理 → 前端位姿估计 → 后端优化 → 地图融合／维护 → 地图支持后续定位。** 这是功能流程；不同系统可以交错执行这些环节。

| 步骤 | 做什么、为什么影响题目 | 我们关注的位置 |
| --- | --- | --- |
| ① 观测 | 采集激光／图像与运动信息；运动目标、镜面、遮挡、距离与采样密度决定可用信息 | 实物镜面问题首先发生在这里；需要区分缺测与真实空闲空间 |
| ② 预处理 | 同步时间、校准外参、按传感器条件补偿运动畸变，标记不可靠观测 | 避免把时间／位姿误差误判为动态；镜面观测处理属于可扩展入口 |
| ③ 前端定位 | 运动预测、数据关联、扫描匹配，估计当前位姿 | **地图中留下什么约束**会影响这里；走廊要检查弱约束方向，而不只看点数 |
| ④ 后端优化 | 综合相邻帧、多传感器及经过验证的回环约束，修正轨迹一致性 | 位姿错会把正确扫描融合到错误位置；错误关联／回环也会反过来损坏地图 |
| ⑤ 地图融合与维护 | 按位姿整合扫描，处理动态残影、结构保留和持久变化 | **M1 的主要干预点；M5 在这里选择保留哪些静态几何** |
| ⑥ 地图使用与检验 | 地图反馈给后续跟踪／重定位；实验中冻结 A 地图，用独立 B 检验定位 | **M4 检验⑤→⑥的收益，M5检验保留下来的结构是否真正提供约束** |

关键反馈是 **位姿误差 → 对齐错误 → 地图错层／重影 → 匹配错误 → 后续位姿误差**。因此，“好地图”需要几何可信、有效结构有覆盖、重复观测一致，而且结构在定位时可见、有区分度；仅仅看起来更干净还不够。[流程依据](https://arxiv.org/abs/1606.05830)。

### 4. 我们的假设具体放在哪里？

| 假设 | 干预或检验位置 | 对照与指标 | 当前进度 |
| --- | --- | --- | --- |
| **M1：减少动态残影，同时限制静态损失** | ⑤ 地图观测筛选／清理 | 同一 A、相同建图位姿，对比 Raw／DUFOMap／BeautyMap；看表面误差、已观测静态覆盖、DA／SA | 静态、动态、长廊已有首轮联合评分；不以单项删除率判定成功 |
| **M4：地图改善在什么污染条件下转化为定位收益？** | **⑤→⑥：换地图，固定定位器和独立 B** | 比较配对 RMSE 改善、P95、旋转误差和输出覆盖；污染梯度实验还要控制静态支持 | 已有三场景地图配对定位；受控污染剂量关系待测 |
| **M5：哪些静态结构值得保留？** | **⑤ 的几何选择 → ③／⑥ 的匹配约束** | 在相近 DA／SA、点数与预算下，比较几何保护与均匀／阈值保留；检查方向、空间覆盖与定位误差 | 长廊已作边界观察；匹配预算的几何保护消融待测 |

我们的当前验证路线是 **A 采集 → 地图处理与地图质量评分（M1）→ 冻结地图 → 独立 B 定位（M4）→ 分析静态约束条件（M5）**。镜面扩展先处理①／②的观测可靠性，再进入同一套地图与定位评测；现有动态清理录像不能代替镜面验证。

[本轮实践与指标](#current-map-hypotheses) · [精确命题、对照与证伪条件](testing/MAPPING-FOCUS.zh-CN.md)"""

DIRECTION_EN = """### 1. What does the research title ask?

**Direction: robust localization and SLAM in dynamic environments.** The central question is: **when scenes change and observations can be unreliable, how can we build geometrically faithful maps that retain useful static constraints, and test whether these maps improve localization accuracy and continuity?**

| Term | Research object | Evidence of progress |
| --- | --- | --- |
| Dynamic environments | Moving-object traces and persistent changes such as relocated furniture; these require different temporal decisions | Separate transient motion from genuine structural updates; measure removal and static retention |
| Robust localization | Trustworthy poses under abnormal measurements, map mismatch or weak geometric constraints | Position/rotation error, P95, output coverage and failures together; current single runs do not establish general recovery |
| SLAM | Joint pose and map estimation: poses align observations, while the map constrains subsequent tracking | Map geometry and coverage plus held-out localization; complete SLAM also requires testing with estimated mapping poses |

Joint pose/map estimation is central to SLAM. [SLAM survey](https://arxiv.org/abs/1606.05830). Our current experiment supplies mapping poses to isolate the map intervention; that control does not establish complete autonomous SLAM.

### 2. How does the physical evidence connect to the title?

[The mirror in Figure 1 and incomplete mapping circled in Figure 2](#physical-test-mirror) provide a concrete starting point: **a stationary environment and reliable observations are separate properties.** Mirrors/glass can cause missing returns or reflected geometry, affecting map boundaries and later matching; see the [reflection study](https://arxiv.org/abs/2406.10494). The supplied images record the user's observation; isolating the cause requires raw scans, coverage and trajectory controls.

We therefore separate **moving objects → dynamic traces** from **stationary mirrors → missing/reflected observations**. The first is the current cleaning experiment; the second is an extension motivated by hardware. Removing bad points still requires checking static loss and retaining uncertainty where observations are missing.

### 3. The SLAM workflow and the important intervention points

**Observations → preprocessing → front-end pose estimation → back-end optimization → map integration/maintenance → map-supported localization.** This is a functional workflow; implementations may interleave its stages.

| Stage | Function and relevance | Our intervention |
| --- | --- | --- |
| ① Observations | Acquire scans/images and motion information; motion, mirrors, occlusion, range and sampling determine available evidence | The physical mirror issue starts here; distinguish missing observations from observed free space |
| ② Preprocessing | Synchronize timestamps, calibrate extrinsics, compensate motion when applicable and flag unreliable observations | Avoid confusing timing/pose error with object motion; reflective-observation handling is an extension |
| ③ Front end | Motion prediction, association and registration estimate the current pose | **Which map constraints survive** matters here; examine weak directions in corridors, beyond point counts |
| ④ Back end | Combine neighboring-frame, sensor and geometrically validated loop constraints to improve trajectory consistency | Wrong poses misplace otherwise correct scans; bad associations/loops can damage the map |
| ⑤ Map integration and maintenance | Fuse posed observations; handle dynamic traces, static retention and persistent changes | **M1 intervenes here; M5 selects which static geometry to retain** |
| ⑥ Map use and evaluation | Feed the map into tracking/relocalization; in our experiment freeze map A and evaluate separate B | **M4 tests the ⑤→⑥ benefit; M5 tests whether retained structure supplies useful constraints** |

The feedback is **pose error → misalignment → distorted/ghosted map → wrong matching → later pose error**. Useful maps need faithful geometry, static coverage, repeatability and structures that are visible and distinctive during localization; visual cleanliness alone is insufficient. [Workflow basis](https://arxiv.org/abs/1606.05830).

### 4. Where exactly do our hypotheses enter?

| Hypothesis | Intervention or test | Controls and metrics | Current status |
| --- | --- | --- | --- |
| **M1: reduce dynamic traces while bounding static loss** | ⑤ Observation selection/map cleaning | Same A and mapping poses; Raw/DUFOMap/BeautyMap; surface error, observed-static coverage and DA/SA | First joint scores exist for static, dynamic and corridor scenes; removal alone is insufficient |
| **M4: under which contamination conditions does map improvement benefit localization?** | **⑤→⑥: change the map, fix the localizer and held-out B** | Paired RMSE gain, P95, rotation error and coverage; controlled pollution levels must also hold static support constant | Three-scene paired localization exists; the pollution dose-response test is pending |
| **M5: which static structures should survive?** | **⑤ Geometry selection → ③/⑥ matching constraints** | Comparable DA/SA, point and compute budgets; geometry protection vs uniform/threshold retention; directional/spatial coverage and pose error | Corridor boundary observations exist; budget-matched geometry-selection ablation is pending |

The current protocol is **acquire A → process and score maps (M1) → freeze maps → localize separate B (M4) → examine static-constraint conditions (M5)**. A mirror extension would first address observation reliability at ①/②, then use the same map/pose evaluation chain; current dynamic-cleaning recordings do not validate mirror handling.

[Current experiments and metrics](#current-map-hypotheses) · [Exact hypotheses, controls and falsification](docs/testing/MAPPING-FOCUS.md)"""


def refresh_direction(text: str, chinese: bool) -> str:
    """Replace the direction body while preserving every other top-level section."""
    from publish_home_experiments import sections

    heading = "方向分析" if chinese else "Direction analysis"
    _, blocks = sections(text)
    if heading not in blocks:
        raise ValueError(f"Direction section missing: {heading}")
    old = blocks[heading]
    anchor = old[:old.index("## " + heading)]
    replacement = DIRECTION_ZH if chinese else DIRECTION_EN
    new = anchor + "## " + heading + "\n\n" + replacement.rstrip() + "\n\n"
    updated, count = re.subn(re.escape(old), lambda _: new, text, count=1)
    if count != 1:
        raise ValueError(f"Direction section boundary missing: {heading}")
    return updated


def publish() -> None:
    from publish_home_experiments import apply_home_layout

    for path, chinese in [(ROOT / "README.md", False), (ROOT / "docs/HOME.zh-CN.md", True)]:
        text = path.read_text(encoding="utf-8")
        updated = apply_home_layout(refresh_direction(text, chinese), chinese)
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    publish()
