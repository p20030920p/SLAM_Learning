"""Publish the mapping-layer question and source-checked simulator settings, without route details."""

from pathlib import Path
import re

from publish_direction_figures import refresh_direction

ROOT = Path(__file__).resolve().parents[3]

SETUP_EN = """## Simulation sensors and chassis

| Item | Actual configuration |
| --- | --- |
| Platform | Sim2Real omni chassis; ROS 2 Jazzy + Gazebo Harmonic; ideal simulated sensors, physical tests pending |
| Chassis | Three omni wheels, 120° spacing; wheel radius 0.06364 m; wheel-centre radius 0.1934 m; collision cylinder radius 0.20 m, height 0.14 m |
| Mass / contact | Base link 0.953513 kg; each wheel 0.20 kg; passive rollers approximated by spherical contact and directional friction, μ=0.02 / 2.0 |
| 2D lidar | Generic gpu_lidar, 720 rays, 360°, 10 Hz, 0.08–12 m; base_link offset (0.06, 0, 0.16) m |
| 3D lidar | Generic gpu_lidar, 720 azimuth × 16 elevation samples, 360° × 30° (±15°), 10 Hz, 0.08–12 m; offset (0, 0, 0.30) m |
| RGB camera | 640×480, 15 Hz, 80° horizontal FOV; offset (0.18, 0, 0.12) m |
| Depth hypothesis arm | Actual rendered depth_camera: 320×240, 10 Hz, 80° horizontal FOV, 0.25–4 m; no hardware noise model; native 2D/SRRG arms omit the 3D lidar |
| Map representation | 3D source points; legacy 2D projection: 0.05 m cells, world Z=0.12–1.20 m, one-cell occupied dilation; SRRG has its own native 2D map and scoring tolerance |

[Actual robot URDF](config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf) · [Depth/sensor-arm generation](src/scripts/presentation/probe_sensors.py) · [Map projection](src/scripts/presentation/build_maps.py). Sensor offsets are relative to base_link, not height above the floor. The 16-line simulator is not a claim of a specific commercial lidar model.

"""

SETUP_ZH = """## 仿真雷达与小车结构参数

| 项目 | 实际设置 |
| --- | --- |
| 平台 | Sim2Real全向底盘；ROS 2 Jazzy＋Gazebo Harmonic；理想仿真传感器，实体测试待做 |
| 底盘结构 | 三个全向轮，间隔120°；轮半径0.06364 m；轮心到车体中心0.1934 m；碰撞圆柱半径0.20 m、高0.14 m |
| 质量／接触 | base_link为0.953513 kg，每轮0.20 kg；滚子以球形接触和方向摩擦近似，μ=0.02／2.0 |
| 二维雷达 | 通用gpu_lidar，720束、360°、10 Hz、0.08–12 m；相对base_link安装位置(0.06, 0, 0.16) m |
| 三维雷达 | 通用gpu_lidar，水平720×垂直16束、360°×30°（±15°）、10 Hz、0.08–12 m；安装位置(0, 0, 0.30) m |
| RGB相机 | 640×480、15 Hz、水平视场80°；安装位置(0.18, 0, 0.12) m |
| 深度假设组 | 实际渲染depth_camera：320×240、10 Hz、水平80°、0.25–4 m；未加实体噪声模型；原生二维／SRRG组移除三维雷达 |
| 地图表示 | 三维源点；旧二维投影为0.05 m格、世界Z=0.12–1.20 m、一格占据膨胀；SRRG使用独立的原生二维地图及覆盖容差 |

[实际机器人URDF](../config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf) · [深度相机和传感器分组](../src/scripts/presentation/probe_sensors.py) · [地图投影](../src/scripts/presentation/build_maps.py)。安装位置相对base_link，不能当作离地高度；仿真16线雷达没有指定商用型号。

"""

HYP_EN = """The focused question has three linked tests: **joint map quality → contamination-dependent localization benefit → geometric conditions for that benefit**. M1 combines the former M1/M2; M4/M5 retain their identifiers for traceability. Projection is a representation/scoring diagnostic, not a separate M3 hypothesis.

| Hypothesis | Controlled test and current evidence |
| --- | --- |
| M1: suppress dynamic traces while limiting static-structure loss (former M1/M2 combined) | Score removal and retention jointly on the same inputs. DUFOMap: DA 46.59%, SA 99.998%; BeautyMap: DA 74.36%, SA 81.15%. Native 2D SRRG: ghost removal 42.31%, static coverage 99.51%, under its own definition. These are single-run observations, not a cross-representation ranking. |
| M4: localization benefit depends on map contamination encountered during the test | Freeze the localizer and independent test B; vary map contamination in predefined regions while controlling static support. Predict a larger paired error/failure reduction when more misleading map support is encountered. Existing dynamic GICP XYZ RMSE Raw/DUFO/Beauty=0.98/0.98/1.04 cm establishes no gain; the controlled relationship and SRRG's separate B remain untested. |
| M5: retained static geometry matters beyond aggregate removal/retention scores | Within one representation and comparable DA/SA, point and compute budgets, compare geometry-preserving retention with uniform/threshold-only retention. Predict better localization when repeatably visible, spatially distinct and complementary structures survive. This map-selection test is unrun; earlier Depth pose experiments do not validate it. |

[Exact hypotheses, controls and falsification](docs/testing/MAPPING-FOCUS.md) · [Map-quality evidence and failure timestamps](docs/testing/MAP-METRICS.zh-CN.md). A point/cell percentage difference alone does not measure lost localization benefit. Static and corridor scenes remain boundary controls; sensor additions and persistent-change updates are separate extensions.
"""

HYP_ZH = """围绕当前开放问题，依次检验**联合地图质量→污染条件下的定位收益→收益成立的几何条件**。M1合并原M1／M2；保留M4／M5编号以便对应历史记录。投影只作表示与评分诊断，不再单列M3假设。

| 假设 | 受控检验与现有证据 |
| --- | --- |
| M1：抑制动态残影，同时限制静态结构损失（合并原M1／M2） | 同输入联合评价删除与保留：DUFOMap的DA为46.59%、SA为99.998%；BeautyMap的DA为74.36%、SA为81.15%。原生二维SRRG按自身定义得到残影删除42.31%、静态覆盖99.51%。这些是单轮观察，不跨表示排名。 |
| M4：定位收益取决于测试时遇到的地图污染 | 固定定位器及独立测试B，在事先指定区域改变地图污染，并控制静态支持；假设遇到更多误导性地图支持时，清理带来的配对误差／失败改善更明显。已有动态GICP的Raw／DUFO／Beauty XYZ RMSE为0.98／0.98／1.04 cm，未建立收益；受控关系及SRRG独立定位B仍待测。 |
| M5：保留的静态几何分布，会影响全局删除／保留分数之外的定位表现 | 在同一表示及相近DA／SA、点数和计算预算下，对比几何结构保护与均匀／仅阈值保留；假设保住可重复观测、具有区分度且方向互补的结构更有利于定位。该地图选择实验未运行，旧Depth定位实验不能验证它。 |

[精确命题、对照与证伪条件](testing/MAPPING-FOCUS.zh-CN.md) · [地图指标与故障时间点](testing/MAP-METRICS.zh-CN.md)。点级与格级百分数不同，本身不能衡量定位收益损失。静态和走廊保留为边界对照；增加传感器与持久变化更新属于另行验证的扩展。
"""


def publish():
    for chinese, path in [(False, ROOT / "README.md"), (True, ROOT / "docs/HOME.zh-CN.md")]:
        text = path.read_text(encoding="utf-8")
        if "<!-- HOME_EXPERIMENTS_V2 -->" in text:
            text = refresh_direction(text, chinese)
            from publish_home_experiments import refresh_document

            heading = "假设" if chinese else "Hypothesis"
            hypothesis = HYP_ZH if chinese else HYP_EN
            text = re.sub(
                rf"(?<=## {heading}\n\n).*?(?=\n\n## )",
                lambda _: hypothesis.rstrip(), text, count=1, flags=re.S,
            )
            path.write_text(text, encoding="utf-8")
            refresh_document(path, chinese)
            continue
        text = text.split('\n\n<a id="mapping-hypothesis-tests"></a>')[0]
        text = re.sub(
            r"## (?:Simulation sensors and chassis|仿真雷达与小车结构参数)\n.*?(?=## (?:Practice|实践)\n)",
            "",
            text,
            flags=re.S,
        )
        if chinese:
            text = re.sub(
                r"^\[English\]\(../README.md\) \| 中文.*$",
                "[English](../README.md) | 中文",
                text,
                count=1,
                flags=re.M,
            )
            question = """**大方向：变化环境中的可靠建图与定位。** 原来的“退化与大变动下定位自恢复”适合作为长期方向，但同时跨越建图、配准、重定位和多传感器融合，对当前论文与实验过于开放。

**本轮小问题：在给定多帧扫描和建图位姿的条件下，如何删除动态障碍物残影，同时保留静态结构；这种地图改善在什么污染和几何条件下，能够降低独立定位的误差？** 先验证地图，再检验定位；不把“地图更干净”直接写成“保证定位准确”。[问题边界与论文依据](testing/MAPPING-FOCUS.zh-CN.md) · [原自恢复背景](self-recovery/DESIGN.zh-CN.md)。"""
            direction = "**SLAM**同时估计运动和地图。本轮控制建图位姿与定位器，把干预放在地图层；动态清理、持久变化更新、走廊几何退化分开讨论。IRMCL／AdaM-MCL属于定位参照，不作为动态建图方法。"
            narrower = "当前研究主线是**动态残影删除→静态约束保留→独立定位检验**。下图保留为此前定位自恢复方向的背景图，不代表本轮聚焦后的研究框架。[原可编辑图](assets/slam-recovery-flow.zh-CN.v2.pptx) · [图像来源](assets/direction/sources.json)。照片为已有器材，实体实验待测。"
            qhead, dhead, hhead = "开放问题", "方向分析", "假设"
            hyp = HYP_ZH
            setup = SETUP_ZH
        else:
            text = re.sub(
                r"^English \| \[中文\]\(docs/HOME.zh-CN.md\).*$",
                "English | [中文](docs/HOME.zh-CN.md)",
                text,
                count=1,
                flags=re.M,
            )
            question = """**Broad direction: reliable mapping and localization in changing environments.** Self-recovery under degradation and large change spans mapping, registration, relocalization and sensor fusion; it is too broad for the present paper set and experiments.

**Focused question: given multi-frame scans and mapping poses, how can dynamic traces be removed while retaining static structure, and under which contamination and geometry conditions does this map improvement reduce held-out localization error?** Validate the map first, then test localization; cleaning does not guarantee accurate pose. [Scope and paper basis](docs/testing/MAPPING-FOCUS.md) · [Earlier recovery background](docs/self-recovery/DESIGN.md)."""
            direction = "**SLAM** estimates motion and a map jointly. The current intervention is at the map layer, controlling mapping poses and the downstream localizer. Dynamic cleaning, persistent-change updates and corridor observability are separate mechanisms. IR-MCL/AdaM-MCL remain localization references."
            narrower = "The current chain is **dynamic trace removal → static constraint retention → held-out localization test**. The diagram below remains an earlier recovery-context illustration, rather than the current focused research framework. [Earlier editable diagram](docs/assets/slam-recovery-flow.en.v2.pptx) · [Image sources](docs/assets/direction/sources.json). Hardware photographs document existing equipment; physical experiments remain pending."
            qhead, dhead, hhead = "Open question", "Direction analysis", "Hypothesis"
            hyp = HYP_EN
            setup = SETUP_EN
        text = re.sub(
            rf"(?<=## {qhead}\n\n).*?(?=\n\n## {dhead})", lambda _: question, text, count=1, flags=re.S
        )
        start = text.index(f"## {dhead}\n\n") + len(f"## {dhead}\n\n")
        image = text.index("![", start)
        text = text[:start] + direction + "\n\n" + text[image:]
        image_end = text.index("\n\n", start + len(direction) + 2)
        para_end = text.index("\n\n|", image_end)
        text = text[:image_end] + "\n\n" + narrower + text[para_end:]
        text = re.sub(
            rf"(?<=## {hhead}\n\n).*?(?=\n\n## )", lambda _: hyp.rstrip(), text, count=1, flags=re.S
        )
        practice = "## 实践\n" if chinese else "## Practice\n"
        text = text.replace(practice, setup + practice, 1)
        text = (
            text.replace("## 开放问题：假设与简单实验", "## 历史定位探索：假设与简单实验")
            if chinese
            else text.replace(
                "## Hypotheses and small experiments",
                "## Earlier localization hypotheses and small experiments",
            )
        )
        marker = (
            "根据此前录像，先提出三个方向，再做对应实验："
            if chinese
            else "The earlier results suggest three directions to test:"
        )
        appendix_note = (
            "此附录保留此前的定位层探索；地图冻结，不能据此声称验证了动态建图。"
            if chinese
            else "This appendix preserves earlier pose-level exploration with frozen maps; it does not validate dynamic mapping."
        )
        if appendix_note not in text:
            text = text.replace(marker, appendix_note + "\n\n" + marker, 1)
        equation = "$$e_i=\\sqrt{(\\hat x_i-x_i)^2+(\\hat y_i-y_i)^2},\\quad \\mathrm{RMSE}_{xy}=\\sqrt{\\frac1N\\sum_{i=1}^N e_i^2}.$$"
        xyz = "$$e_{i,xyz}=\\sqrt{(\\hat x_i-x_i)^2+(\\hat y_i-y_i)^2+(\\hat z_i-z_i)^2},\\quad \\mathrm{RMSE}_{xyz}=100\\sqrt{\\frac1N\\sum_{i=1}^N e_{i,xyz}^2}\\;\\text{cm}.$$"
        note = (
            "三维GICP使用完整三维地图和点云，读取`*-poses3d.csv`的原生XYZ输出，按相同≤0.05s同步规则计算下式。缺失输出不补零；须同时检查有效数量、首末时间及共同覆盖。走廊三方法输出覆盖不同，不能直接用整段RMSE排名。地图动态删除／静态保留是另一组指标。"
            if chinese
            else "Native 3D GICP uses full 3D maps/clouds and XYZ outputs in `*-poses3d.csv`, with the same ≤0.05 s synchronization rule. Missing outputs are not filled with zero; report count, first/last timestamp and common coverage. Unequal corridor coverage prevents ranking whole-run RMSE. Dynamic removal/static retention are separate map metrics."
        )
        if xyz not in text:
            text = text.replace(equation, equation + "\n\n" + note + "\n\n" + xyz, 1)
        ending = (
            '\n\n<a id="mapping-hypothesis-tests"></a>\n\n## '
            + ("建图假设与逐项验证" if chinese else "Mapping hypotheses and sequential checks")
            + "\n\n"
            + hyp
        )
        text += ending
        # Update the tagline without changing old evidence or its original conditions.
        text = text.replace(
            "Robust localization and SLAM in dynamic environments · Localization self-recovery",
            "Dynamic map cleaning · Static structure retention · Downstream localization",
        )
        text = text.replace(
            "动态环境中的鲁棒定位与 SLAM · 定位系统自恢复", "动态残影清理 · 静态结构保留 · 下游定位检验"
        )
        text = text.replace(
            "[Hypothesis](#hypothesis) · [Branches]",
            "[Hypothesis](#hypothesis) · [Simulation setup](#simulation-sensors-and-chassis) · [Branches]",
        )
        text = text.replace(
            "[假设](#假设) · [分支]", "[假设](#假设) · [器材参数](#仿真雷达与小车结构参数) · [分支]"
        )
        text = text.replace("The diagram below remains", "The diagram above remains").replace(
            "下图保留为此前定位", "上图保留为此前定位"
        )
        text = refresh_direction(text, chinese)
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    publish()
