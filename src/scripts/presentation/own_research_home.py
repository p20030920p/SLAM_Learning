"""Separate paper-method practice from project-written hypothesis experiments."""

import json
import os
import re

from publish_home_experiments import apply_home_layout, sections
from simple_research_home import ROOT, metrics, num, pct, practice as paper_practice, related, table

MARKER = "<!-- OWN_HYPOTHESES_20261016 -->"
SUITE = "results/reference/own-hypotheses-20261016"


def definitions(zh):
    def s(cn, en):
        return cn if zh else en
    text = '<a id="mapping-hypothesis-tests"></a>\n\n## ' + s("假设", "Hypothesis") + "\n\n<!-- SIMPLE_HYPOTHESES_V2 -->\n" + MARKER + "\n\n"
    text += table([s("问题", "Question"), s("一句话假设", "Hypothesis"), s("对照方法", "Controls"), s("指标", "Metrics")], [
        ["H1 / Q1", s("重复命中＋自由射线确认能减少动态残影，并改善独立定位。", "Repeated hits plus free-ray confirmation reduce dynamic traces and improve held-out localization."), s("自写累积图 / 自写时序清图", "Own accumulation / own temporal cleaning"), "DA、SA、Eₘ、XY RMSE"],
        ["H2 / Q2", s("用轮式里程计补偿点的采样时间差，能降低地图和独立定位误差。", "Wheel-odometry compensation for point timestamps reduces map and held-out localization error."), s("自写补偿关 / 开", "Own compensation off / on"), "Eₘ、SA、XY RMSE"],
        ["H3 / Q3", s("检测几何退化并按弱方向的约束贡献保留可靠静态结构，能减少沿廊定位误差。", "Detecting geometric degeneracy and retaining reliable static structures that constrain the weak direction reduces along-corridor error."), s("自写统一阈值 / 自写退化感知清图", "Own uniform threshold / own degeneracy-aware cleaning"), "SA、Eₘ、along RMSE"],
    ])
    text += s("三项干预均由本库实现；AMCL只作为统一的下游评分定位器。镜面识别仍待实物验证。", "All three interventions are implemented in this repository; AMCL is the common downstream localizer. Mirror identification still needs physical validation.") + "\n\n"
    text += '<a id="hypothesis-math"></a>\n\n### ' + s("数学表达", "Mathematical form") + "\n\n"
    text += s("A建图、B独立采集；冻结地图后，各对照使用相同B扫描、里程计和AMCL参数。", "A builds the maps; B is a separate acquisition. Freeze the maps and share B scans, odometry and AMCL settings across controls.") + "\n\n"
    text += r"""```math
M_j=\mathcal{B}_j(Z^A,\hat T_{\rm odom}^A),\qquad \hat T_{j,t}^B=\mathcal{L}_{\rm AMCL}(Z_{\leq t}^B,M_j)
```

```math
E_L(j)=\sqrt{\frac{1}{N}\sum_t\lVert\hat p_{j,t}^B-p_t^{B,\ast}\rVert^2},\qquad \Delta E_L=E_L(\mathrm{baseline})-E_L(\mathrm{method})
```

**H1**

```math
H_c=\sum_b\mathbf{1}[\text{hit in time bin }b],\quad F_c=\sum_b\mathbf{1}[\text{free ray through }c],\quad K_c=\mathbf{1}[H_c\geq3\ \land\ H_c\geq1.5F_c]
```

```math
\mathrm{DA}_{\rm temporal}\gt\mathrm{DA}_{\rm raw},\quad\mathrm{SA}_{\rm temporal}\geq\mathrm{SA}_{\rm raw}-\varepsilon,\quad E_M(\mathrm{temporal})\lt E_M(\mathrm{raw}),\quad\Delta E_L\gt0
```

**H2**

```math
\tilde p_i=\hat T_{\rm odom}(t_e)^{-1}\hat T_{\rm odom}(t_i)p_i,\qquad E_M(\mathrm{on})\lt E_M(\mathrm{off}),\quad\Delta E_L\gt0
```

**H3**

"""
    text += s("解决方案：从已观测结构的局部法线估计约束较弱的方向；对该方向有约束贡献、至少两次命中且没有自由射线反证的结构，降低删除阈值。下面n为局部法线，G为平移约束的近似矩阵，v为最弱方向。", "Proposed solution: estimate the weak direction from observed local surface normals, then lower the deletion threshold for structures that constrain that direction, have repeated hits and have no contradicting free rays. Here n is a local normal, G approximates translational constraints and v is the weakest direction.") + "\n\n"
    text += r"""
```math
G=\sum_{c\in C}n_cn_c^{\mathsf T},\quad v_{\min}=\mathrm{eigvec}_{\min}(G),\quad R_c=\mathbf{1}[H_c\geq2,\ F_c=0,\ |n_c^{\mathsf T}v_{\min}|\gt0.7]
```

```math
D=\mathbf{1}[\lambda_{\min}(G)\lt0.25\lambda_{\max}(G)],\qquad K_c^{\rm protected}=\mathbf{1}[(H_c\geq5\land H_c\geq1.5F_c)\lor(D=1\land R_c=1)]
```

```math
E_{\parallel}=\sqrt{\frac1N\sum_t[u^{\mathsf T}(\hat p_t-p_t^\ast)]^2},\qquad E_{\parallel}(\mathrm{protected})\lt E_{\parallel}(\mathrm{strict})
```

"""
    text += s("时间箱0.5秒；自由射线在回波前15 cm停止；静态损失容差ε＝1个百分点。H3保持走廊、路线、传感器和定位器相同，仅切换清图规则。它保护已有观测提供的约束；完全缺少沿廊信息时仍需额外观测，不能凭空恢复位置。真值仅用于评分。", "Time bins: 0.5 s; free rays stop 15 cm before each return; static-loss tolerance ε = 1 percentage point. H3 keeps the corridor, route, sensors and localizer fixed and changes only the cleaning rule. It protects observed constraints; a corridor with no along-axis information still needs additional observations. Truth is used only for scoring.") + "\n\n"
    text += '<a id="hypothesis-pseudocode"></a>\n\n### ' + s("伪代码", "Pseudocode") + "\n\n"
    text += """```text
for scene in [static, dynamic, motion, corridor]:
    A = acquire_scans_and_wheel_odometry(scene)
    for control in controls_for(scene):
        if H2: compensate_sector_points_by_interpolated_odometry()
        update_hit_and_free_evidence_in_distinct_time_bins()
        if H1: retain_temporally_supported_cells()
        if H3: protect_supported_normals_along_the_weak_direction()
        freeze_map(control)
    B = acquire_a_separate_session(scene)
    run_the_same_AMCL_on_all_frozen_maps(B)
    score_map_and_localization_on_common_times_using_truth_only_here()
```

"""
    return text + "[" + s("实现、实验与录像", "Implementation, experiments and recordings") + "](#hypothesis-test-index)\n\n"


def practice(doc, zh, previous):
    def s(cn, en):
        return cn if zh else en
    def href(path):
        return os.path.relpath(ROOT / path, doc.parent).replace("\\", "/")
    original = paper_practice(doc, zh, previous)
    setup = original[original.index('<a id="practice-setup">'):original.index('<a id="experiment-h1">')]
    sr = original[original.index('<a id="experiment-h1">'):original.index('<a id="experiment-h2">')]
    fast = original[original.index('<a id="experiment-h2">'):original.index('<a id="experiment-h3">')]
    corridor = ('<a id="practice-srrg-corridor"></a>\n\n### P1.3 · SRRG · ' + s("长廊", "Corridor") + "\n\n"
        + original[original.index('<a id="h3-original-a">'):original.index('<a id="h3-landmark-a">')])
    rest = original[original.index('<a id="baseline-3d">'):]
    for record_name in ("robot-ndt-static-initial", "robot-ndt-static", "robot-gicp-static"):
        folder = "results/reference/" + record_name
        record_link = f'[{s("记录", "Record")}]({href(folder + "/record.json")})'
        rest = rest.replace(record_link, record_link + f' · [MP4]({href(folder + "/execution.mp4")})')
    sr = re.sub(r"### H1 · .*", "### P1 · SRRG · " + s("静态与动态", "Static and dynamic"), sr)
    fast = re.sub(r"### H2 · .*", "### P2 · FAST-LIO · " + s("运动畸变", "Motion distortion"), fast)
    corridor = re.sub(r"### H3 · .*", "### P1.3 · SRRG · " + s("长廊场景对照", "Corridor controls"), corridor)
    sr = sr.replace('id="experiment-h1"', 'id="practice-srrg"')
    fast = fast.replace('id="experiment-h2"', 'id="practice-fastlio"')
    corridor = corridor.replace('id="experiment-h3"', 'id="practice-srrg-corridor"')
    def expand_single_video(block):
        return "\n".join(line.replace('width="340"', 'width="840"') if line.count("<img") == 1 else line for line in block.split("\n"))
    sr, corridor, fast = map(expand_single_video, (sr, corridor, fast))
    index = [
        ["P0", s("实验设置与设备", "Setup and devices"), "[↗](#practice-setup)"],
        ["P1.1", "SRRG · " + s("静态", "Static"), "[A](#h1-static-a) / [B](#h1-static-b)"],
        ["P1.2", "SRRG · " + s("动态", "Dynamic"), "[A](#h1-dynamic-a) / [B](#h1-dynamic-b)"],
        ["P1.3", "SRRG · " + s("原长廊", "Original corridor"), "[A](#h3-original-a) / [B](#h3-original-b)"],
        ["P1.4", "SRRG · " + s("结构变化", "Persistent change"), "[A](#supp-srrg)"],
        ["P2.1", "FAST-LIO · " + s("建图与运动阶段", "Mapping and motion phases"), "[A](#h2-a) / [" + s("静止", "Stationary") + "](#h2-stationary) / [" + s("慢转", "Slow turn") + "](#h2-slow) / [" + s("快转", "Fast turn") + "](#h2-fast) / [" + s("平移", "Translation") + "](#h2-translation)"],
        ["P2.2", "FAST-LIO · " + s("冻结地图定位", "Frozen-map localization"), "[B](#h2-b)"],
    ]
    index.append(["P3.0", "DUFOMap / BeautyMap · KITTI-00", "[" + s("清图实践", "Map-cleaning practice") + "](#practice-kitti)"])
    for number, scene, cn, en in [(1, "static", "静态", "Static"), (2, "dynamic", "动态", "Dynamic"), (3, "corridor", "长廊", "Corridor"), (4, "change", "结构变化", "Changed world")]:
        index.append([f"P3.{number}", "DUFOMap / BeautyMap · 3D · " + s(cn, en), f"[A/B](#scene-{scene}-3d)"])
    index += [["P4", "IR-MCL · Bonn", "[↗](#practice-irmcl)"], ["P5", "AdaM-MCL", "[↗](#practice-adam)"],
        ["P6.1", "NDT / GICP", "[↗](#supp-registrations)"], ["P6.2", "slam_toolbox / AMCL", "[↗](#supp-acquisition)"],
        ["P6.3", s("保存点云回放", "Saved-cloud replay"), "[↗](#map-review-3d)"], ["P6.4", s("失败诊断", "Failure diagnostics"), "[↗](#srrg-diagnostics)"]]
    text = "## " + s("实践", "Practice") + "\n\n"
    text += s("这里实践Related works中的方法。A＝建图，B＝冻结地图后的另一次定位；点击目录中的A/B直接进入对应录像与指标。", "This section practices methods in Related works. A = mapping; B = a separate localization session on frozen maps. Click A/B in the contents to reach its recordings and metrics.") + "\n\n<a id=\"practice-index\"></a>\n\n### " + s("实验目录", "Experiment contents") + "\n\n"
    index = [[cell.replace("[↗]", "[" + s("进入实验", "Open experiment") + "]") for cell in row] for row in index]
    text += table([s("编号", "No."), s("方法／下属实验", "Method / subexperiment"), s("直达", "Go directly")], index)
    kitti = '<a id="practice-kitti"></a>\n\n### P3.0 · DUFOMap / BeautyMap · KITTI-00\n\n'
    kitti_rows = []
    for method, title in [("dufomap", "DUFOMap"), ("beautymap", "BeautyMap")]:
        folder = "results/reference/desktop-live-" + method
        data = json.loads((ROOT / folder / "record.json").read_text())["metrics"]
        preview = f'<a href="{href(folder + "/execution.mp4")}"><img src="{href("docs/media/related-pointcloud/20261016/" + method + ".gif")}" width="340" alt="{title}"></a>'
        kitti_rows.append([title, "141", num(data["DA"]) + "%", num(data["SA"]) + "%", preview, f'[{s("记录", "Record")}]({href(folder + "/record.json")})'])
    kitti += table([s("方法", "Method"), s("帧数", "Scans"), "DA", "SA", s("点云实录节选（点击看完整录像）", "Point-cloud excerpt (click for full recording)"), s("记录", "Record")], kitti_rows)
    text += setup + sr + corridor + fast + kitti + rest
    for anchor, name, folder, video, preview, score_text in [
        ("practice-irmcl", "IR-MCL", "results/reference/desktop-live-ir-mcl", "execution", "docs/media/related-pointcloud/20261016/ir-mcl.gif", "XY RMSE 5.31 cm / yaw 1.07°"),
        ("practice-adam", "AdaM-MCL", "results/reference/desktop-adam-mcl", "result", "results/reference/desktop-adam-mcl/result.gif", s("RMSE 32.23格；持续收敛0/10；保存结果回放", "RMSE 32.23 cells; sustained convergence 0/10; saved-result replay")),
    ]:
        text += f'<a id="{anchor}"></a>\n\n### {name}\n\n'
        text += table([s("录像", "Recording"), s("指标", "Metrics"), s("记录", "Record")], [[f'<a href="{href(folder + "/" + video + ".mp4")}"><img src="{href(preview)}" width="340" alt="{name}"></a>', score_text, f'[{s("记录", "Record")}]({href(folder + "/record.json")})']])
        text += "**" + s("分析：", "Analysis:") + "**\n\n[↑ " + s("目录", "Contents") + "](#practice-index)\n\n"
    return text


def hypothesis_tests(doc, zh):
    def s(cn, en):
        return cn if zh else en
    def href(path):
        return os.path.relpath(ROOT / path, doc.parent).replace("\\", "/")
    def link(path, caption):
        return f"[{caption}]({href(path)})"
    def media(path, label, width=420):
        return f'<a href="{href(path + ".mp4")}"><img src="{href(path + ".gif")}" width="{width}" loading="lazy" alt="{label}"></a>'
    text = '<a id="hypothesis-test"></a>\n\n## Hypothesis test\n\n<a id="hypothesis-test-index"></a>\n\n'
    text += s("自写方法的实验。每个场景重新采集A/B；同一场景各对照共享输入。每组1轮，固定参数，不根据真值调参。", "Experiments for project-written methods. Reacquire A/B per scene and share inputs across its controls. One trial per control, fixed parameters, no truth-based tuning.") + "\n\n"
    index = []
    for scene, name in [("static", s("H1 静态保留", "H1 Static retention")), ("dynamic", s("H1 动态清理", "H1 Dynamic cleaning")), ("motion", s("H2 里程计去畸变", "H2 Odometry deskew")), ("corridor", s("H3 退化约束保护", "H3 Weak-axis protection"))]:
        index.append([name, f"[A](#own-{scene}-a)", f"[B](#own-{scene}-b)"])
    text += table([s("实验", "Experiment"), s("建图与指标", "Mapping and scores"), s("独立定位与指标", "Held-out localization and scores")], index)
    text += s("设备同Practice的全向轮机器人；算法仅使用二维雷达和轮式里程计。H2将三个真实时刻的扇区组合为滚动扫描，保留各点原采样时刻；未使用FAST-LIO。H3保持同一走廊，只切换地图保留规则。", "Use the same omni robot as Practice; algorithms use only 2D LiDAR and wheel odometry. H2 combines sectors from three actual scan times, preserving each point timestamp, without FAST-LIO. H3 keeps the same corridor and changes only map retention.") + "\n\n"
    text += link("src/slam_learning/runtime/own_mapping.py", s("自写算法", "Own algorithms")) + " · " + link("demo/record-own-hypotheses.ps1", s("一键录制", "Record all")) + "\n\n"
    text += s("H2录像阶段：静止0–7秒、慢转7–15秒、快转15–31秒、平移31–39秒。", "H2 recording phases: stationary 0–7 s, slow turn 7–15 s, fast turns 15–31 s, translation 31–39 s.") + "\n\n"
    for scene, name in [("static", "H1 · " + s("静态保留", "Static retention")), ("dynamic", "H1 · " + s("动态清理", "Dynamic cleaning")), ("motion", "H2 · " + s("里程计去畸变", "Odometry deskew")), ("corridor", "H3 · " + s("退化约束保护", "Weak-axis protection"))]:
        a, b = f"{SUITE}/{scene}-A", f"{SUITE}/{scene}-B"
        ar = json.loads((ROOT / a / "record.json").read_text())
        br = json.loads((ROOT / b / "time-grid-score.json").read_text())
        text += f'<a id="own-{scene}-a"></a>\n\n### {name} · A\n\n'
        controls = ("off", "deskew") if scene == "motion" else (("strict", "protected") if scene == "corridor" else ("raw", "temporal"))
        text += table([s("对照", "Control"), "DA", "SA", "Eₘ / cm"], [[method, pct(ar["methods"][method]["dynamic_removal"]), pct(ar["methods"][method]["static_retention"]), num(ar["methods"][method]["map_rmse_m"], 100)] for method in controls])
        if scene == "corridor":
            extra = ar["methods"]["protected"]["points"] - ar["methods"]["strict"]["points"]
            same_map = (ROOT / a / "maps/strict/map.pgm").read_bytes() == (ROOT / a / "maps/protected/map.pgm").read_bytes()
            text += table([s("保护规则额外保留的栅格数", "Additional cells retained by protection"), s("冻结地图字节相同", "Frozen maps are byte-identical")], [[extra, s("是", "Yes") if same_map else s("否", "No")]])
            if same_map:
                text += s("本轮保护规则未改变最终地图；B中的随机误差差别不能视为地图干预带来的改善。", "The protection rule did not change the final map in this trial; random differences in B cannot establish improvement from the map intervention.") + "\n\n"
        text += table([s("建图录像：灰色为基线，蓝色为自写干预", "Mapping: grey baseline, blue own intervention")], [[media(a + "/execution", name + " A", 840)]])
        text += link(a + "/record.json", s("记录", "Record")) + "\n\n**" + s("分析：", "Analysis:") + "**\n<!-- OWN_ANALYSIS:" + scene + "-a -->\n\n<!-- /OWN_ANALYSIS:" + scene + "-a -->\n\n"
        text += f'<a id="own-{scene}-b"></a>\n\n### {name} · B\n\n'
        if scene == "corridor":
            text += s("沿廊RMSE在前50秒受限扫描阶段评分；XY RMSE使用整个共同评分区间。", "Along-corridor RMSE uses the first 50 s of limited observations; XY RMSE uses the full common evaluation interval.") + "\n\n"
        selected = {key: m for key, m in br["methods"].items() if (key.startswith("degraded_") if scene == "corridor" else True)}
        text += table([s("地图／AMCL", "Map / AMCL"), "XY RMSE / cm", "along RMSE / cm", "P95 / cm", "N", s("更新覆盖", "Fresh coverage")], [[key, num((m.get("common") or {}).get("rmse_m"), 100), num((m.get("limited") or {}).get("along_x_rmse_m"), 100) if scene == "corridor" else "—", num((m.get("common") or {}).get("p95_m"), 100), (m.get("common") or {}).get("samples", 0), pct(m["fresh_update_grid_coverage"])] for key, m in selected.items()])
        text += table(list(selected), [[media(b + "/executions/" + key, key + " B") for key in selected]])
        text += link(b + "/time-grid-score.json", s("共同时间点评分", "Common-time scores")) + " · " + link(b + "/record.json", s("记录", "Record")) + "\n\n**" + s("分析：", "Analysis:") + "**\n<!-- OWN_ANALYSIS:" + scene + "-b -->\n\n<!-- /OWN_ANALYSIS:" + scene + "-b -->\n\n[↑ " + s("目录", "Contents") + "](#hypothesis-test-index)\n\n"
    text += s("Eₘ为地图点到已观测静态支持的距离RMSE。定位预热5秒后在共同10 Hz时间点评分，最新输出最多滞后0.15秒；更新覆盖不是失锁率。地图改善但定位未改善时，只支持建图结论。", "Eₘ is map-point distance RMSE to observed static support. Localization uses common 10 Hz times after 5 s warmup, with output age at most 0.15 s; fresh coverage is not tracking-loss rate. Map improvement without localization improvement supports only the mapping claim.") + "\n\n"
    return text


def publish_document(doc, zh):
    text = doc.read_text(encoding="utf-8")
    prefix, blocks = sections(text)
    previous = blocks["实践" if zh else "Practice"]
    rebuilt = {}
    for key, value in blocks.items():
        if key in ("Branches", "分支", "Hypothesis test", "假设检验实验"):
            continue
        if key in ("Hypothesis", "假设"):
            value = definitions(zh)
        elif key in ("Practice", "实践"):
            value = practice(doc, zh, previous)
        elif key in ("Related works", "相关工作"):
            value = related(value, doc, zh)
            value = re.sub(r"\[[^\]]+\]\(#experiment-h2\)", "[FAST-LIO Practice](#practice-fastlio)", value)
            value = value.replace("#experiment-h1", "#practice-srrg").replace("#experiment-h3", "#practice-srrg-corridor")
        elif key in ("Metrics", "指标"):
            value = metrics(value, zh)
        rebuilt[key] = value
    result = apply_home_layout(prefix + "".join(rebuilt.values()) + hypothesis_tests(doc, zh), zh)
    result = re.sub(r" · \[(?:Branches|分支)\]\([^)]*\)", "", result)
    result = result.replace("[Practice](#practice)", "[Practice](#practice-index) · [Hypothesis test](#hypothesis-test-index)")
    result = result.replace("[实践](#实践)", "[实践](#practice-index) · [Hypothesis test](#hypothesis-test-index)")
    for key, body in re.findall(r"<!-- OWN_ANALYSIS:([^ ]+) -->(.*?)<!-- /OWN_ANALYSIS:[^ ]+ -->", text, re.S):
        result = re.sub(fr"(<!-- OWN_ANALYSIS:{re.escape(key)} -->).*?(<!-- /OWN_ANALYSIS:{re.escape(key)} -->)", lambda m: m[1] + body + m[2], result, flags=re.S)
    doc.write_text(result, encoding="utf-8", newline="\n")


def publish():
    for path, zh in [("README.md", False), ("docs/HOME.zh-CN.md", True)]:
        publish_document(ROOT / path, zh)
    for zh, name in [(False, "MAPPING-FOCUS.md"), (True, "MAPPING-FOCUS.zh-CN.md")]:
        home = "../HOME.zh-CN.md" if zh else "../../README.md"
        text = definitions(zh).replace("](#hypothesis-test-index)", "](" + home + "#hypothesis-test-index)")
        (ROOT / "docs/testing" / name).write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
    for zh, name in [(False, "MINIMAL.md"), (True, "MINIMAL.zh-CN.md")]:
        home = "HOME.zh-CN.md" if zh else "../README.md"
        text = table(["Section", "Go"], [["Practice", f"[{'论文方法实践' if zh else 'Paper-method practice'}]({home}#practice-index)"], ["Hypothesis test", f"[{'自写方法实验' if zh else 'Own-method experiments'}]({home}#hypothesis-test-index)"]])
        (ROOT / "docs" / name).write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    publish()
