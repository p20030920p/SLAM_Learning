"""Separate paper-method practice from project-written hypothesis experiments."""

import json
import os
import re

from hypothesis_notation import github_math, math_sections, pseudocode, raw_baselines, srrg_comparison
from publish_home_experiments import apply_home_layout, sections
from simple_research_home import ROOT, metrics, num, pct, practice as paper_practice, related, table

MARKER = "<!-- OWN_HYPOTHESES_20261016 -->"
SUITE = "results/reference/own-hypotheses-20261016"
H1_SUITE = "results/reference/h1-refined-20261016"
H1_FILTER_SUITE = "results/reference/h1-supported-20261016"


def definitions(zh):
    def s(cn, en):
        return cn if zh else en
    text = '<a id="mapping-hypothesis-tests"></a>\n\n## ' + s("假设", "Hypothesis") + "\n\n<!-- SIMPLE_HYPOTHESES_V2 -->\n" + MARKER + "\n\n"
    text += table([s("问题", "Question"), s("假设与具体做法", "Hypothesis and method"), s("对照方法", "Controls"), s("指标", "Metrics")], [
        ["H1 / Q1", s("轮速预测后，用至少3个时间箱支持的结构修正扫描位姿；按0.5秒时间箱统计邻域命中与空闲穿越，后者达到3箱且不少于前者1.5倍时删除占据；检验残影清除增加、静态覆盖损失≤1个百分点及独立B定位误差下降。", "Correct wheel-predicted scan poses using structure supported in at least three bins; count neighborhood hits and free crossings in 0.5 s bins, deleting occupancy when crossings reach three bins and at least 1.5 times hit support; test increased trace removal, static coverage loss ≤1 percentage point and lower independent-B localization error."), s("M₀：轮速累积图 / M₁：自写对齐＋清理", "M₀: wheel-pose accumulation / M₁: own alignment + cleaning"), s("A：DA、SA；B：XY RMSE", "A: DA, SA; B: XY RMSE")],
        ["H2 / Q2", s("用轮式里程计补偿点的采样时间差，能降低地图和独立定位误差。", "Wheel-odometry compensation for point timestamps reduces map and held-out localization error."), s("M₀：补偿关 / M₁：补偿开", "M₀: compensation off / M₁: on"), s("A：地图RMSE；B：XY RMSE", "A: map RMSE; B: XY RMSE")],
    ])
    text += s("两项干预均由本库实现；AMCL只作为统一的下游评分定位器。镜面识别仍待实物验证。", "Both interventions are implemented in this repository; AMCL is the common downstream localizer. Mirror identification still needs physical validation.") + "\n\n"
    text += '<a id="hypothesis-math"></a>\n\n### ' + s("数学表达", "Mathematical form") + "\n\n"
    parts = math_sections(zh)
    text += github_math("\n\n".join(parts.values())) + "\n\n"
    text += '<a id="hypothesis-srrg-comparison"></a>\n\n### ' + s("创新点与SRRG思路对比", "Innovation and conceptual comparison with SRRG") + "\n\n"
    text += github_math(srrg_comparison(zh)) + "\n\n"
    text += '<a id="hypothesis-pseudocode"></a>\n\n### ' + s("伪代码", "Pseudocode") + "\n\n"
    fence = chr(96) * 3
    text += fence + "text\n" + pseudocode() + fence + "\n\n"
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
        return "\n".join(line.replace('width="340"', 'width="840"') if line.count("<img") == 1 and "localization B" not in line else line for line in block.split("\n"))
    sr, corridor, fast = map(expand_single_video, (sr, corridor, fast))
    index = [
        ["P0", s("实验设置与设备", "Setup and devices"), "[↗](#practice-setup)"],
        ["P0.1", s("Raw基线定义与区别", "Raw baseline definitions"), "[↗](#raw-baseline-definitions)"],
        ["P1.1", "SRRG · " + s("静态", "Static"), "[A](#h1-static-a) / [B](#h1-static-b)"],
        ["P1.2", "SRRG · " + s("动态", "Dynamic"), "[A](#h1-dynamic-a) / [B](#h1-dynamic-b)"],
        ["P1.3", "SRRG · " + s("原长廊", "Original corridor"), "[A](#h3-original-a) / [B](#h3-original-b)"],
        ["P1.4", "SRRG · " + s("结构变化", "Persistent change"), "[A](#supp-srrg) / [B](#supp-srrg-b)"],
        ["P2.1", "FAST-LIO · " + s("建图与运动阶段", "Mapping and motion phases"), "[A](#h2-a) / [" + s("静止", "Stationary") + "](#h2-stationary) / [" + s("慢转", "Slow turn") + "](#h2-slow) / [" + s("快转", "Fast turn") + "](#h2-fast) / [" + s("平移", "Translation") + "](#h2-translation)"],
        ["P2.2", "FAST-LIO · " + s("冻结地图定位", "Frozen-map localization"), "[B](#h2-b)"],
    ]
    index.append(["P3.0", "DUFOMap / BeautyMap · KITTI-00", "[" + s("清图实践", "Map-cleaning practice") + "](#practice-kitti)"])
    for number, scene, cn, en in [(1, "static", "静态", "Static"), (2, "dynamic", "动态", "Dynamic"), (3, "corridor", "长廊", "Corridor"), (4, "change", "结构变化", "Changed world")]:
        index.append([f"P3.{number}", "DUFOMap / BeautyMap · 3D · " + s(cn, en), f"[A](#scene-{scene}-3d) / [B](#scene-{scene}-3d-b)"])
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
        kitti_rows.append([title, num(data["DA"]) + "%", num(data["SA"]) + "%", preview, f'[{s("记录", "Record")}]({href(folder + "/record.json")})'])
    kitti += s("KITTI-00，141帧；本项只评价地图清理。", "KITTI-00, 141 scans; this experiment evaluates map cleaning only.") + "\n\n"
    kitti += table([s("方法", "Method"), "DA ↑", "SA ↑", s("点云实录节选（点击看完整录像）", "Point-cloud excerpt (click for full recording)"), s("记录", "Record")], kitti_rows)
    raw = '<a id="raw-baseline-definitions"></a>\n\n### ' + s("Raw基线定义", "Raw baseline definitions") + "\n\n" + github_math(raw_baselines(zh)) + "\n\n"
    text += setup + raw + sr + corridor + fast + kitti + rest
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
    def method_label(key):
        return {
            "raw": s("M₀ · Raw：轮速位姿累积", "M₀ · Raw: wheel-pose accumulation"),
            "temporal": s("M₁ · Align+Temporal：自写对齐＋清理", "M₁ · Align+Temporal: own alignment + cleaning"),
            "off": s("M₀ · Off：不补偿", "M₀ · Off: uncompensated"),
            "deskew": s("M₁ · On：运动补偿", "M₁ · On: motion compensated"),
        }[key]
    text = '<a id="hypothesis-test"></a>\n\n## Hypothesis test\n\n<a id="hypothesis-test-index"></a>\n\n'
    text += s("自写方法实验。H1重用同一原始A重算地图，旧B用于开发消融；固定规则后，另采静态B一次、动态B三次。H2保留原单轮A/B。每轮对照共享扫描、里程计、AMCL参数与初始化。", "Experiments for project-written methods. H1 rebuilds maps from the same original A and uses old B for development ablation. After fixing the rule, acquire one fresh static B and three fresh dynamic B sessions. H2 retains its original single A/B trial. Each paired trial shares scans, odometry, AMCL parameters and initialization.") + "\n\n"
    index = []
    for scene, name in [("static", s("H1 静态保留", "H1 Static retention")), ("dynamic", s("H1 动态清理", "H1 Dynamic cleaning")), ("motion", s("H2 里程计去畸变", "H2 Odometry deskew"))]:
        index.append([name, f"[A](#own-{scene}-a)", f"[B](#own-{scene}-b)"])
    index.insert(0, [s("H1 旧B开发消融", "H1 old-B development ablation"), "—", "[↗](#h1-revision-ablation)"])
    text += table([s("实验", "Experiment"), s("建图与指标", "Mapping and scores"), s("独立定位与指标", "Held-out localization and scores")], index)
    text += s("设备同Practice的全向轮机器人；算法仅使用二维雷达和轮式里程计。H2将三个真实时刻的扇区组合为滚动扫描，保留各点原采样时刻；未使用FAST-LIO。", "Use the same omni robot as Practice; algorithms use only 2D LiDAR and wheel odometry. H2 combines sectors from three actual scan times, preserving each point timestamp, without FAST-LIO.") + "\n\n"
    text += link("src/slam_learning/runtime/own_mapping.py", s("自写清理", "Own cleaner")) + " · " + link("src/slam_learning/runtime/own_refinement.py", s("自写对齐", "Own alignment")) + " · " + link("demo/record-h1-revision.ps1", s("H1验证录制", "Record H1 confirmation")) + " · " + link(H1_SUITE + "/confirmation-protocol.json", s("采集前固定设置", "Settings fixed before acquisition")) + "\n\n"
    text += s("H2录像阶段：静止0–7秒、慢转7–15秒、快转15–31秒、平移31–39秒。", "H2 recording phases: stationary 0–7 s, slow turn 7–15 s, fast turns 15–31 s, translation 31–39 s.") + "\n\n"
    text += '<a id="h1-revision-ablation"></a>\n\n### ' + s("H1 · 旧B开发消融", "H1 · Old-B development ablation") + "\n\n"
    text += s("旧规则SA损失6.95个百分点；A轮速位姿RMSE还有7.74 cm。只清理无法修正地图位姿偏差，因此最终加入自写鲁棒二维对齐。下表重跑相同旧B，只用于开发消融，不混入最终新B评分。", "The old rule loses 6.95 percentage points of SA, while A wheel-pose RMSE is 7.74 cm. Cleaning cannot correct mapping-pose error, so the final method adds own robust 2D alignment. This table reruns the same old B for development ablation and is excluded from final fresh-B scores.") + "\n\n"
    aq = json.loads((ROOT / H1_FILTER_SUITE / "dynamic-A/record.json").read_text())["methods"]
    dq = json.loads((ROOT / H1_FILTER_SUITE / "dynamic-replay/trial-1/time-grid-score.json").read_text())["methods"]
    ablation = [("raw", "Raw"), ("legacy", s("旧逐格过滤", "Old per-cell filtering")), ("after_free", s("后续空闲确认（中间版）", "Later-free confirmation (pilot)")), ("temporal", s("近邻时序：只清理", "Neighborhood temporal: filter only"))]
    ablation_rows = [[name, pct(aq[key]["dynamic_removal"]), pct(aq[key]["static_retention"]), num(dq[key]["common"]["rmse_m"], 100)] for key, name in ablation]
    aligned_a = json.loads((ROOT / H1_SUITE / "dynamic-A/record.json").read_text())["methods"]
    aligned_b = json.loads((ROOT / H1_SUITE / "dynamic-replay/trial-1/time-grid-score.json").read_text())["methods"]
    ablation_rows += [[name, pct(aligned_a[key]["dynamic_removal"]), pct(aligned_a[key]["static_retention"]), num(aligned_b[key]["common"]["rmse_m"], 100)] for key, name in [("align_only", s("只做自写对齐", "Own alignment only")), ("temporal", s("自写对齐＋清理（最终）", "Own alignment + cleaning (final)"))]]
    text += table([s("方法", "Method"), "DA ↑", "SA ↑", "XY RMSE / cm ↓"], ablation_rows)
    text += link(H1_SUITE + "/dynamic-replay/trial-1/record.json", s("原生AMCL重跑记录", "Native AMCL rerun record")) + " · " + link(SUITE + "/dynamic-B/record.json", s("原始负结果保留", "Original negative result")) + "\n\n"
    text += s("只清理版本另采三次B：Raw 6.02 cm、只清理6.06 cm，仍未改善；该批次完整保留。下方主实验使用最终联合方法重新采集的B。", "Three fresh B sessions for filter-only yielded Raw 6.02 cm and filter-only 6.06 cm, without improvement; that full batch is retained. The main experiment below uses another fresh B batch for the final joint method.") + " " + link(H1_FILTER_SUITE + "/confirmation-score.json", s("只清理验证记录", "Filter-only confirmation")) + "\n\n"
    for scene, name in [("static", "H1 · " + s("静态保留", "Static retention")), ("dynamic", "H1 · " + s("动态清理", "Dynamic cleaning")), ("motion", "H2 · " + s("里程计去畸变", "Odometry deskew"))]:
        current_suite = SUITE if scene == "motion" else H1_SUITE
        a, b = f"{current_suite}/{scene}-A", f"{current_suite}/{scene}-B"
        ar = json.loads((ROOT / a / "record.json").read_text())
        score_path = H1_SUITE + "/confirmation-score.json" if scene == "dynamic" else b + "/time-grid-score.json"
        br = json.loads((ROOT / score_path).read_text())
        text += f'<a id="own-{scene}-a"></a>\n\n### {name} · A\n\n'
        controls = ("off", "deskew") if scene == "motion" else ("raw", "temporal")
        if scene in ("static", "dynamic"):
            headers = [s("对照", "Control")] + (["DA ↑"] if scene == "dynamic" else []) + ["SA ↑"]
            rows = [[method_label(method)] + ([pct(ar["methods"][method]["dynamic_removal"])] if scene == "dynamic" else []) + [pct(ar["methods"][method]["static_retention"])] for method in controls]
            text += table(headers, rows)
        elif scene == "motion":
            text += table([s("对照", "Control"), s("地图 RMSE / cm ↓", "Map RMSE / cm ↓")], [[method_label(method), num(ar["methods"][method]["map_rmse_m"], 100)] for method in controls])
        if scene == "motion":
            text += table([s("建图录像：灰色为基线，蓝色为自写干预", "Mapping: grey baseline, blue own intervention")], [[media(a + "/execution", name + " A", 840)]])
        else:
            text += table([s("原始A采集实录（旧算法画面）", "Original A acquisition (old algorithm view)"), s("同一A重放清图：灰Raw，蓝新版", "Same A reprocessed: grey Raw, blue revised")],
                          [[media(f"{SUITE}/{scene}-A/execution", name + " original A"), media(a + "/execution", name + " revised A input replay")]])
        text += link(a + "/record.json", s("记录", "Record")) + "\n\n**" + s("分析：", "Analysis:") + "**\n<!-- OWN_ANALYSIS:" + scene + "-a -->\n\n<!-- /OWN_ANALYSIS:" + scene + "-a -->\n\n"
        text += f'<a id="own-{scene}-b"></a>\n\n### {name} · B\n\n'
        selected = br["methods"]
        if scene == "motion":
            text += table([s("地图／AMCL", "Map / AMCL"), "XY RMSE / cm ↓"], [[method_label(key), num((m.get("common") or {}).get("rmse_m"), 100)] for key, m in selected.items()])
            text += table([method_label(key) for key in selected], [[media(b + "/executions/" + key, key + " B") for key in selected]])
        else:
            text += s("另采B，冻结地图后使用相同AMCL。", "Acquire fresh B and use the same AMCL on frozen maps.") + " "
            text += (s("下表为三次B的共同时间样本合并RMSE；GIF固定展示第1轮。", "The table pools common-time samples from all three B sessions; GIFs always show trial 1.") if scene == "dynamic" else s("本项为一次静态对照。", "One static control session.")) + "\n\n"
            text += table([s("地图／AMCL", "Map / AMCL"), "XY RMSE / cm ↓", s("定位实录（点击MP4）", "Localization recording (click MP4)")], [[method_label(key), num((m.get("common") or {}).get("rmse_m"), 100), media(b + "/executions/" + key, key + " fresh B")] for key, m in selected.items()])
            if scene == "dynamic":
                rows = []
                for trial, suffix in ((1, ""), (2, "2"), (3, "3")):
                    trial_folder = H1_SUITE + "/dynamic-B" + suffix
                    trial_score = json.loads((ROOT / trial_folder / "time-grid-score.json").read_text())["methods"]
                    rows.append([str(trial), num(trial_score["raw"]["common"]["rmse_m"], 100), num(trial_score["temporal"]["common"]["rmse_m"], 100), link(trial_folder + "/executions/raw.mp4", "Raw MP4") + " · " + link(trial_folder + "/executions/temporal.mp4", "Temporal MP4")])
                text += table([s("轮次", "Trial"), "Raw / cm", "Temporal / cm", s("完整录像", "Full recordings")], rows)
        text += link(score_path, s("共同时间点评分", "Common-time scores")) + " · " + link(b + "/record.json", s("记录", "Record")) + "\n\n**" + s("分析：", "Analysis:") + "**\n<!-- OWN_ANALYSIS:" + scene + "-b -->\n\n<!-- /OWN_ANALYSIS:" + scene + "-b -->\n\n[↑ " + s("目录", "Contents") + "](#hypothesis-test-index)\n\n"
    text += s("H1用DA/SA评清图，静态对照只看SA；H2用地图到静态支持的单向RMSE评分。定位预热5秒后使用共同10 Hz时间点，最新输出最多滞后0.15秒；样本数与输出缺失情况见原始评分记录。建图指标改善但B误差不降时，只支持建图结论。", "H1 uses DA/SA for cleaning and only SA in its static control; H2 uses one-way map-to-static-support RMSE. Localization uses common 10 Hz times after 5 s warmup, with output age at most 0.15 s; sample counts and missing outputs remain in the score records. Better mapping scores without lower B error support only the mapping claim.") + "\n\n"
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
            value = related(value, doc, zh).replace("H3", "Q3")
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
