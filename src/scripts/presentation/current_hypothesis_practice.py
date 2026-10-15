"""Compact map-quality to localization evidence for the new hypothesis batch."""
from __future__ import annotations

import json

SUITE = "results/reference/map-hypotheses-20261015"


def fold_history(block, zh):
    marker = "<!-- EARLIER_LOCALIZATION_ONLY -->"
    if marker in block:
        return block
    title = "假设检验实验" if zh else "Hypothesis test experiment"
    before, body = block.split("## " + title + "\n", 1)
    current_link = ("[新一轮建图质量 → 独立定位实验](#current-map-hypotheses)" if zh
                    else "[New map-quality → held-out localization tests](#current-map-hypotheses)")
    summary = "历史定位层实验：Guard／Depth／Search" if zh else "Historical localization-only tests: Guard / Depth / Search"
    return (before + "## " + title + "\n\n" + current_link + "\n\n<details>\n<summary>" + summary
            + "</summary>\n\n" + marker + "\n" + body.strip() + "\n\n</details>\n\n")


def render(doc, zh, previous, *, root, link, analysis_slot):
    summary = json.loads((root / SUITE / "summary.json").read_text(encoding="utf-8"))
    host = json.loads((root / SUITE / "host.json").read_text(encoding="utf-8"))

    def label(cn, en):
        return cn if zh else en

    def number(value, scale=1):
        return "N/A" if value is None else f"{value * scale:.2f}"

    def pct(value):
        return "N/A" if value is None else f"{value * 100:.2f}%"

    def ref(path, title):
        return f"[{title}]({link(doc, SUITE + '/' + path)})"

    def table(headers, rows):
        return "\n".join(["| " + " | ".join(headers) + " |",
                          "| " + " | ".join(["---"] * len(headers)) + " |",
                          *["| " + " | ".join(map(str, row)) + " |" for row in rows], ""])

    def clip(path, title, stem="execution"):
        return ('<a href="' + link(doc, SUITE + '/' + path + '/' + stem + '.mp4') + '"><img src="'
                + link(doc, SUITE + '/' + path + '/' + stem + '.gif') + '" width="230" loading="lazy" alt="'
                + title + '"></a><br>' + ref(path + '/' + stem + '.mp4', title))

    def pose_table(values):
        rows = []
        for method, name in (("raw", "Raw"), ("dufomap", "DUFOMap"), ("beautymap", "BeautyMap")):
            value = values[method]
            rows.append([name, number(value["common_xyz_rmse_m"], 100),
                         number(value["common_rotation_rmse_deg"]), number(value["common_xyz_p95_m"], 100),
                         pct(value["output_coverage"]), pct(value["success_fraction_all_grid"]),
                         number(value.get("paired_rmse_gain_m"), 100)])
        return table([label("地图", "Map"), "XYZ RMSE / cm", label("旋转 RMSE / °", "Rotation RMSE / °"),
                      "P95 / cm", label("输出覆盖", "Output coverage"), label("达标时段", "Within thresholds"),
                      label("较Raw改善 / cm", "Gain vs Raw / cm")], rows)

    lines = [
        '<a id="current-map-hypotheses"></a>', "",
        "### " + label("新假设实验：建图质量 → 独立定位", "New hypothesis tests: map quality → held-out localization"), "",
        label("目录：", "Index: ") + " · ".join(
            f"[{cn if zh else en}](#current-hypothesis-{key})"
            for key, cn, en in (("static", "静态", "Static"), ("dynamic", "动态", "Dynamic"),
                                ("corridor", "长廊", "Corridor"))), "",
        table([label("项目", "Item"), label("设置", "Setup")], [
            [label("任务", "Task"), label("新采集A → 同源60帧 → Raw / DUFOMap / BeautyMap → 冻结图 → 新采集B + 固定GICP",
                                          "Fresh A → same 60 scans → Raw / DUFOMap / BeautyMap → frozen maps → fresh B + fixed GICP")],
            [label("设备", "Sensors"), label("沿用上方全向底盘与720×16三维LiDAR；B使用点云和轮式里程计；真值仅评分",
                                            "Omni base and 720×16 3D LiDAR above; B uses clouds and wheel odometry; truth for evaluation only")],
            [label("运行机", "Run host"), host["cpu"]["Name"].strip() + f"; {host['ram_bytes'] / 2**30:.2f} GiB; "
             + host["renderer"].split("OpenGL renderer string: ")[-1]],
            [label("时长／次数", "Duration / trials"), label("A各90仿真秒；B静态／动态90秒，长廊120秒；每场景1轮",
                                                        "A: 90 simulation s each; B: static/dynamic 90 s, corridor 120 s; one run per scene")],
            [label("检验范围", "Test scope"), label("M1地图联合评分；M4独立定位配对；M5长廊约束边界。污染剂量关系与几何保护消融仍待测",
                                                   "M1 joint map scores; M4 paired localization; M5 corridor boundary. Pollution dose response and geometry-selection ablation remain pending")],
        ]),
        ref("protocol.json", label("固定实验设置", "Frozen protocol")) + " · " + ref("summary.json", label("原始数值", "Scores"))
        + " · " + ref("host.json", label("运行机记录", "Host record")), "",
        table([label("指标", "Metric"), label("解释", "Definition")], [
            [label("表面 RMSE ↓", "Surface RMSE ↓"), label("地图点到渲染静态三角面的距离均方根；cm；去地面／自体，5cm体素等权",
                                                          "RMS map-to-rendered-static-mesh distance, cm; ground/self excluded; one point per 5cm voxel")],
            [label("P@5cm／C@5cm ↑", "P@5cm / C@5cm ↑"), label("5cm内正确表面比例／A已观测静态参考覆盖；C不表示全环境完整率",
                                                               "Surface precision / A-observed static-reference coverage at 5cm; coverage is not whole-world completeness")],
            ["DA / SA ↑", label("带标签源点的动态删除／静态保留；静态场景DA为N/A，SA使用几何确认静态点",
                                 "Dynamic removal / static retention on source points; static scenes use geometry-confirmed static points and DA=N/A")],
            [label("定位 RMSE／P95 ↓", "Pose RMSE / P95 ↓"), label("录制时段10Hz网格，仅在三图共同有效时配对；最新输出≤0.15s；不拟合轨迹",
                                                                  "10Hz recording-time grid; paired where all maps have valid causal outputs aged ≤0.15s; no trajectory fitting")],
            [label("输出覆盖／达标时段 ↑", "Output coverage / within thresholds ↑"), label("全时段有效输出比例／位置<10cm且旋转<5°的比例；缺失算未达标",
                                                                                       "Valid-output fraction / fraction with position<10cm and rotation<5°; missing outputs are unsuccessful")],
            [label("改善量 ↑", "Gain ↑"), label("Raw RMSE − 方法RMSE；正值为改善，负值为变差", "Raw RMSE minus method RMSE; positive improves, negative worsens")],
        ]), "",
    ]
    for scene, cn, en in (("static", "静态场景", "Static scene"), ("dynamic", "动态场景", "Dynamic scene"),
                          ("corridor", "长廊退化", "Corridor degradation")):
        data = summary["scenes"][scene]
        quality = data["map_quality"]["methods"]
        lines += [f'<a id="current-hypothesis-{scene}"></a>', "", "#### " + (cn if zh else en), "",
                  "**" + label("A · 建图指标", "A · Map scores") + "**", "",
                  table([label("方法", "Method"), label("表面 RMSE / cm", "Surface RMSE / cm"), "P@5cm", "C@5cm", "DA", "SA"],
                        [[name, number(quality[key]["surface_rmse_m"], 100), pct(quality[key]["surface_precision_5cm"]),
                          pct(quality[key]["observed_static_coverage_5cm"]), pct(quality[key]["dynamic_removal"]),
                          pct(quality[key]["static_retention"])]
                         for key, name in (("raw", "Raw"), ("dufomap", "DUFOMap"), ("beautymap", "BeautyMap"))]),
                  ref(scene + "/map-quality/record.json", label("地图评分记录", "Map-score record")), "",
                  "**" + label("B · 独立定位", "B · Held-out localization") + "**", "",
                  pose_table(data["methods"]),
                  label("共同评分时点：", "Common scoring timestamps: ") + str(data["common_grid_samples"])
                  + " / " + str(data["grid_samples"]) + " · "
                  + ref(scene + "/localization-3d/record.json", label("定位记录", "Localization record")), ""]
        if scene == "corridor":
            lines += [label("长廊：前50秒限制为3.5m／240°／72水平采样，随后恢复完整观测；完整观测组自始运行。两组均有1m初始X偏差。",
                            "Corridor: 3.5m / 240° / 72 horizontal bins for the first 50s, then restored; full-input arms run from the start. Both start with a 1m X offset."), ""]
            if quality["raw"]["map_sha256"] == quality["dufomap"]["map_sha256"]:
                lines += [label("本轮长廊Raw／DUFOMap点云哈希一致；定位结果来自各自节点。",
                                "Corridor Raw/DUFOMap cloud hashes are identical in this run; pose streams come from separate nodes."), ""]
            for key, title_cn, title_en in (("limited", "受限阶段", "Limited phase"),
                                            ("restored", "恢复观测后", "After observation restoration"),
                                            ("full_observations", "从开始使用完整观测", "Full observations from start")):
                phase = data[key]
                lines += ["**" + (title_cn if zh else title_en) + "** · "
                          + label("共同评分时点 ", "Common timestamps ") + str(phase["common_grid_samples"]), "",
                          pose_table(phase["methods"])]
        lines += ["<details>", "<summary>" + label("新录制：采集／处理／定位", "New recordings: acquisition / processing / localization") + "</summary>", "",
                  clip(scene + "/mapping-a", label("A采集现场", "Mapping-A acquisition")), "",
                  clip(scene + "/map-processing", label("三方法实际处理终端", "Actual three-method processing terminal"), "full-session"), ""]
        for method, name in (("raw", "Raw"), ("dufomap", "DUFOMap"), ("beautymap", "BeautyMap")):
            lines += [clip(scene + "/localization-3d/executions", name + " · " + label("独立B现场", "held-out B live"), method), ""]
        lines += ["</details>", "", analysis_slot(previous, "current-hypothesis-" + scene, zh)]
    return "\n".join(lines)
