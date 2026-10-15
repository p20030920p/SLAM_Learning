"""Render scene-first practice tables and preserve user-written analysis."""

from __future__ import annotations

import csv
import re


def analysis_slot(previous, key, zh):
    start = f"<!-- PRACTICE_ANALYSIS:{key} -->"
    end = f"<!-- /PRACTICE_ANALYSIS:{key} -->"
    match = re.search(re.escape(start) + r"(.*?)" + re.escape(end), previous, re.S)
    content = match.group(1).strip() if match else ""
    return "\n".join(["**分析：**" if zh else "**Analysis:**", start, content, end, ""])


def render_practice(doc, zh, previous, *, root, scenes, packages, read, quality, media, link, pct):
    from current_hypothesis_practice import SUITE, render as render_current

    current = (root / SUITE / "summary.json").is_file()
    def label(cn, en):
        return cn if zh else en

    def record_link(folder, title=None):
        return f"[{title or label('记录', 'Record')}]({link(doc, folder + '/record.json')})"

    def table(headers, rows):
        return "\n".join(
            [
                "<!-- HOME_EXPERIMENT_TABLE -->",
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
                *["| " + " | ".join(map(str, row)) + " |" for row in rows],
                "<!-- /HOME_EXPERIMENT_TABLE -->",
                "",
            ]
        )

    def clips(items):
        lines = ["<details>", "<summary>" + label("视频", "Videos") + "</summary>", ""]
        for title, gif, replay in items:
            lines += [f"**{title}**", "", media(doc, gif, title, zh, replay, width=200), ""]
        return "\n".join(lines + ["</details>", ""])

    def top():
        return "[↑ " + label("实践目录", "Practice index") + "](#practice-index)\n"

    def num(value, scale=1):
        return "—" if value is None else f"{value * scale:.2f}"

    def native(scene):
        key, cn, en = scene
        folder = f"results/reference/srrg-2d-{key}"
        data = read(folder + "/record.json")
        headings = [
            label("方法", "Method"),
            "DA",
            "SA",
            label("建图轨迹 XY RMSE / cm", "Mapping XY RMSE / cm"),
        ]
        rows = []
        if key == "large-change":
            headings.append(label("新增结构覆盖", "New-structure coverage"))
        for method, name in [("raw", "Raw"), ("srrg", "SRRG")]:
            value = data["map_quality"][method]
            row = [
                name,
                pct(value["dynamic_removal"]),
                pct(value["static_retention"]),
                num(data["audit"].get("mapping_pose_xy_rmse_m"), 100) if method == "srrg" else "—",
            ]
            if key == "large-change":
                row.append(pct(value.get("new_structure_retention")))
            rows.append(row)
        return "\n".join(
            [
                f'<a id="srrg-{key}-2d"></a>',
                "",
                "#### " + label("原生二维建图 · Raw / SRRG", "Native 2D mapping · Raw / SRRG"),
                "",
                table(headings, rows),
                record_link(folder) + " · " + label("独立定位 B：待测", "Held-out localization B: pending"),
                "",
                clips([("Raw / SRRG", folder + "/execution.gif", None)]),
                analysis_slot(previous, f"srrg-{key}-2d", zh),
            ]
        )

    def localization(scene, dimension):
        key, cn, en = scene
        folder = "results/reference/" + packages[dimension][scenes.index(scene)]
        data = read(folder + "/record.json")
        map_metrics = quality(key, dimension)
        anchor = "change" if key == "large-change" else key
        spatial = "XY" if dimension == "2d" else "XYZ"
        angle = (
            label("yaw RMSE / °", "yaw RMSE / °")
            if dimension == "2d"
            else label("旋转 RMSE / °", "Rotation RMSE / °")
        )
        rows, videos, ranges = [], [], []
        for method, name in [("raw", "Raw"), ("dufomap", "DUFOMap"), ("beautymap", "BeautyMap")]:
            case = ("degraded_" if dimension == "2d" and key == "corridor" else "") + method
            value = data["metrics"]["cases"][case] if dimension == "2d" else data["metrics_3d"][case]
            rows.append(
                [
                    name,
                    pct(map_metrics[method]["dynamic_removal"]),
                    pct(map_metrics[method]["static_retention"]),
                    num(value.get("position_rmse_m" if dimension == "2d" else "xyz_rmse_m"), 100),
                    num(value.get("yaw_rmse_deg" if dimension == "2d" else "rotation_rmse_deg")),
                    num(value.get("position_p95_m" if dimension == "2d" else "xyz_p95_m"), 100),
                    value["samples"],
                ]
            )
            videos.append(
                (
                    name,
                    folder + f"/executions/{case}.gif",
                    folder + f"/methods/{case}/result.gif" if dimension == "2d" else None,
                )
            )
            if key == "corridor" and dimension == "3d":
                with (root / folder / f"{case}-poses3d.csv").open(encoding="utf-8", newline="") as stream:
                    stamps = [float(row["stamp_s"]) for row in csv.DictReader(stream)]
                ranges.append([name, f"{min(stamps):.1f}–{max(stamps):.1f}"])
        audit = (
            "results/analysis/map-quality/projected-dynamic.json"
            if key == "dynamic" and dimension == "2d"
            else "results/reference/robot-3d-map-audit/record.json"
            if key == "dynamic"
            else f"results/analysis/map-quality/{'corridor' if key == 'corridor' else 'static'}.json"
        )
        lines = [
            f'<a id="scene-{anchor}-{dimension}"></a>',
            "",
            "#### "
            + label(
                "二维投影地图 + AMCL" if dimension == "2d" else "三维地图 + GICP",
                "Projected 2D maps + AMCL" if dimension == "2d" else "3D maps + GICP",
            ),
            "",
            table([label("地图", "Map"), "DA", "SA", f"{spatial} RMSE / cm", angle, "P95 / cm", "N"], rows),
            record_link(folder) + f" · [{label('地图评分', 'Map scores')}]({link(doc, audit)})",
            "",
        ]
        if key == "large-change":
            lines += [
                label(
                    "设置：冻结静态 A 旧图，B 中不更新地图；DA／SA 为旧图 A 数值。",
                    "Setup: static-A map frozen during B; DA/SA describe the old map A.",
                ),
                "",
            ]
        if ranges:
            lines += [
                table(
                    [
                        label("地图", "Map"),
                        label("有效位姿时间范围 / 仿真秒", "Valid pose interval / simulation s"),
                    ],
                    ranges,
                )
            ]
        lines += [clips(videos), analysis_slot(previous, f"scene-{anchor}-{dimension}", zh)]
        return "\n".join(lines)

    lines = [
        "## " + label("实践", "Practice"),
        "",
        "<!-- HOME_EXPERIMENTS_V2 -->",
        "",
        '<a id="practice-index"></a>',
        "",
        "### " + label("小目录", "Index"),
        "",
        "["
        + label("实验设置", "Setup")
        + "](#practice-setup) · ["
        + label("指标说明", "Metrics")
        + "](#practice-metrics)",
        "",
        "| "
        + label("场景", "Scene")
        + " | "
        + label("二维建图", "2D mapping")
        + " | "
        + label("二维定位", "2D localization")
        + " | "
        + label("三维定位", "3D localization")
        + " |",
        "| --- | --- | --- | --- |",
    ]
    if current:
        index_start = next(i for i, line in enumerate(lines) if line.startswith("| "))
        lines[index_start:index_start] = [
            "[" + label("新假设实验", "New hypothesis tests") + "](#current-map-hypotheses) · "
            + " · ".join(f"[{cn if zh else en}](#current-hypothesis-{key})"
                         for key, cn, en in (("static", "静态", "Static"), ("dynamic", "动态", "Dynamic"),
                                            ("corridor", "长廊", "Corridor"))),
            "", "<details>", "<summary>" + label("此前基线目录", "Earlier baseline index") + "</summary>", "",
        ]
    for key in ["static", "dynamic", "corridor"]:
        scene = next(scene for scene in scenes if scene[0] == key)
        lines.append(
            f"| [{scene[1] if zh else scene[2]}](#practice-{key}) | [Raw / SRRG](#srrg-{key}-2d) | [AMCL](#scene-{key}-2d) | [GICP](#scene-{key}-3d) |"
        )
    if current:
        lines += ["", "</details>", ""]
    lines += [
        "",
        "["
        + label("补充实验", "Supplementary experiments")
        + "](#practice-appendix) · ["
        + label("假设实验", "Hypothesis experiments")
        + "](#hypothesis-experiments) · ["
        + label("视频目录", "Video gallery")
        + f"]({link(doc, 'demo/gallery.html')})",
        "",
        "<!-- HOME_SIMULATION -->",
        '<a id="practice-setup"></a>',
        '<a id="simulation-sensors-and-chassis"></a>',
        '<a id="仿真雷达与小车结构参数"></a>' if zh else "",
        "",
        "### " + label("实验设置", "Experiment setup"),
        "",
    ]
    setting_rows = [
        (
            "平台",
            "Platform",
            "ROS 2 Jazzy + Gazebo Harmonic；当前结果均为仿真",
            "ROS 2 Jazzy + Gazebo Harmonic; simulation results",
        ),
        (
            "机器人",
            "Robot",
            "Sim2Real-AlgoBench 三轮全向底盘；轮间隔120°，轮半径0.06364 m",
            "Sim2Real-AlgoBench three-wheel omni base; 120° spacing, wheel radius 0.06364 m",
        ),
        (
            "二维设备",
            "2D sensors",
            "仿真二维 LiDAR + 轮式里程计；720束、360°、10 Hz、0.08–12 m",
            "Simulated 2D LiDAR + wheel odometry; 720 rays, 360°, 10 Hz, 0.08–12 m",
        ),
        (
            "三维设备",
            "3D sensors",
            "独立仿真三维 LiDAR；720×16束、360°×30°、10 Hz、0.08–12 m",
            "Independent simulated 3D LiDAR; 720×16 rays, 360°×30°, 10 Hz, 0.08–12 m",
        ),
        (
            "其他设备",
            "Other sensors",
            "RGB 640×480 / 15 Hz；深度320×240 / 10 Hz / 0.25–4 m，仅历史深度假设组使用",
            "RGB 640×480 / 15 Hz; depth 320×240 / 10 Hz / 0.25–4 m, used only in historical depth-hypothesis trials",
        ),
        (
            "物理硬件",
            "Physical hardware",
            "已有实体底盘、Unitree L2、RealSense D435；本节SLAM结果为仿真；新假设组另列运行机" if current else "已有实体底盘、Unitree L2、RealSense D435；本节SLAM结果为仿真，运行机配置待补充",
            "Physical chassis, Unitree L2 and RealSense D435 available; SLAM results here are simulated; new tests list the run host" if current else "Physical chassis, Unitree L2 and RealSense D435 available; this section's SLAM results are simulated; run-host specifications pending",
        ),
        (
            "场景",
            "Scenes",
            "静态房间、运动箱体、平行长廊；持久结构变化放入补充实验",
            "Static room, moving boxes, parallel corridor; persistent change is supplementary",
        ),
        (
            "长廊设置",
            "Corridor protocol",
            "历史记录包含72束 / 3.5 m受限扫描，录制后50仿真秒恢复；定位初值有偏移，三维另限240°视场",
            "Historical runs restrict scans to 72 rays / 3.5 m for 50 recording simulation seconds; localization starts offset, with 240° FOV in 3D",
        ),
        (
            "二维建图任务",
            "2D mapping task",
            "Raw累计图 vs SRRG维护图；作者节点自估位姿、已知起点；主组关闭图合并，独立定位B待测",
            "Raw accumulation vs SRRG maintenance; estimated mapping poses, known start, graph merging off; independent localization B pending",
        ),
        (
            "地图与定位任务",
            "Map/localization task",
            "给定位姿建图A → Raw / DUFOMap / BeautyMap → 冻结地图 → 独立B；二维固定AMCL，三维固定GICP",
            "Supplied-pose mapping A → Raw / DUFOMap / BeautyMap → frozen map → independent B; fixed AMCL in 2D and GICP in 3D",
        ),
        (
            "地图表示",
            "Map representation",
            "二维投影0.05 m格、Z=0.12–1.20 m、一格膨胀；三维保留完整点云；SRRG为原生二维",
            "2D projection: 0.05 m cells, Z=0.12–1.20 m, one-cell dilation; full 3D clouds; SRRG is native 2D",
        ),
        (
            "定位评分",
            "Pose scoring",
            "真值仅评分，同步≤0.05仿真秒；原始流保留初始化，新假设表按共同录制时段评分；不拟合轨迹、不补零" if current else "真值仅评分；同步≤0.05仿真秒，包含初始化，不拟合轨迹；缺失输出不补零",
            "Truth for evaluation only, ≤0.05 simulation-s sync; original streams retain initialization, new tables use the shared recording interval; no fitted alignment or zero fill" if current else "Truth for evaluation only; ≤0.05 simulation-s synchronization, initialization included, no trajectory fitting or zero-filled missing outputs",
        ),
    ]
    lines += ["| " + label("项目", "Item") + " | " + label("设置", "Setting") + " |", "| --- | --- |"]
    lines += [
        f"| {cn if zh else en} | {value_cn if zh else value_en} |"
        for cn, en, value_cn, value_en in setting_rows
    ]
    lines += [
        "",
        f"[{label('机器人URDF', 'Robot URDF')}]({link(doc, 'config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf')}) · [{label('场景文件', 'World files')}]({link(doc, 'config/presentation/worlds')}) · [{label('传感器分组', 'Sensor profiles')}]({link(doc, 'src/scripts/presentation/probe_sensors.py')}) · [{label('实物器材记录', 'Physical-device record')}]({link(doc, 'docs/media/hardware/record.json')})",
        "",
        "<!-- /HOME_SIMULATION -->",
        "",
        '<a id="practice-metrics"></a>',
        "",
        "### " + label("指标说明", "Metric definitions"),
        "",
    ]
    definitions = [
        (
            "DA ↑",
            "动态删除比例；无动态分母为 N/A",
            "Dynamic-removal fraction; N/A when no dynamic denominator exists",
        ),
        (
            "SA ↑",
            "静态保留／覆盖比例；三类表的样本定义见下行",
            "Static retention / coverage; sample units differ as below",
        ),
        (
            "DA / SA 口径",
            "SRRG：10 cm去重支持格、15 cm覆盖容差；二维投影：5 cm动静专属格；三维：带标签源点",
            "SRRG: 10 cm support cells, 15 cm coverage tolerance; projected 2D: exclusive 5 cm cells; 3D: labelled source points",
        ),
        (
            "RMSE ↓",
            "位置误差均方根，cm；建图轨迹与独立定位分列，二维XY、三维XYZ",
            "Position root-mean-square error, cm; mapping and held-out localization separated; XY in 2D, XYZ in 3D",
        ),
        (
            "角度 RMSE ↓",
            "二维偏航角 / 三维完整旋转误差的均方根，°",
            "Yaw error in 2D / full rotation error in 3D, RMS in degrees",
        ),
        (
            "P95 ↓ / N",
            "位置误差95分位数 / 有效评分位姿数量；仅统计实际有效输出",
            "95th percentile of position error / scored pose count; valid outputs only",
        ),
        (
            "新增结构覆盖 ↑",
            "被维护图覆盖的新增静态支持格比例",
            "Fraction of new static-support cells covered by the maintained map",
        ),
        (
            "几何误差 / 完整率 / F-score",
            "新假设组测表面误差与已观测静态覆盖；全环境完整率／F-score待测；DA／SA不替代几何指标" if current else "待测；本节DA／SA不替代这些指标",
            "New tests measure surface error and observed-static coverage; whole-world completeness/F-score pending; DA/SA are separate" if current else "Not measured; DA/SA do not substitute for these metrics",
        ),
        ("— / N/A", "未评分或未记录 / 不适用", "Not scored or recorded / not applicable"),
    ]
    lines += ["| " + label("指标", "Metric") + " | " + label("含义", "Definition") + " |", "| --- | --- |"]
    lines += [f"| {name} | {cn if zh else en} |" for name, cn, en in definitions]
    lines += [
        "",
        "["
        + label("完整计算定义", "Full calculation definitions")
        + "](#"
        + ("指标" if zh else "metrics")
        + ")",
        "",
    ]
    if current:
        lines += [render_current(doc, zh, previous, root=root, link=link, analysis_slot=analysis_slot),
                  "<details>", "<summary>" + label("此前基线与补充实验", "Earlier baselines and supplementary experiments")
                  + "</summary>", ""]
    for i, key in enumerate(["static", "dynamic", "corridor"], 1):
        scene = next(scene for scene in scenes if scene[0] == key)
        lines += [f'<a id="practice-{key}"></a>', "", f"### {i} · {scene[1] if zh else scene[2]}", ""]
        if key == "static":
            lines += [
                '<a id="srrg-2d"></a>',
                '<a id="2d--amcl"></a>',
                '<a id="2d-localization-recordings"></a>',
                '<a id="3d--gicp"></a>',
                '<a id="3d-map-cleaning-and-localization-recordings"></a>',
                '<a id="二维定位录制"></a>' if zh else "",
                '<a id="三维地图清理与定位录制"></a>' if zh else "",
                "",
            ]
        lines += [native(scene), localization(scene, "2d"), localization(scene, "3d"), top(), ""]
    lines += [
        '<a id="practice-appendix"></a>',
        "",
        "### " + label("补充实验", "Supplementary experiments"),
        "",
        "<details>",
        "<summary>" + label("持久结构变化", "Persistent change") + "</summary>",
        "",
    ]
    change = next(scene for scene in scenes if scene[0] == "large-change")
    lines += [
        native(change),
        localization(change, "2d"),
        localization(change, "3d"),
        "</details>",
        "",
        '<a id="map-review-3d"></a>',
        "<details>",
        "<summary>" + label("三维清理图回放", "Saved 3D map review") + "</summary>",
        "",
        label(
            "视频类型：已保存地图回放，无新推理；数值沿用动态场景三维表。",
            "Video: saved-map replay, no new inference; scores are those in the dynamic 3D table.",
        ),
        "",
        '<a href="'
        + link(doc, "results/reference/robot-3d-map-review-v2/execution.mp4")
        + '"><img src="'
        + link(doc, "results/reference/robot-3d-map-review-v2/execution.gif")
        + '" width="200" loading="lazy" alt="Saved 3D map review"></a><br>['
        + label("已保存地图回放（无新推理）", "Saved map replay (no new inference)")
        + "]("
        + link(doc, "results/reference/robot-3d-map-review-v2/execution.mp4")
        + ")",
        "</details>",
        "",
        '<a id="earlier-raw-map-3d-static-trials"></a>',
        '<a id="此前raw单地图三维静态试验"></a>' if zh else "",
        "<details>",
        "<summary>" + label("早期Raw地图 · NDT / GICP", "Earlier Raw-map trials · NDT / GICP") + "</summary>",
        "",
    ]
    old_rows, old_videos = [], []
    for method, folder_name, name in [
        ("ndt", "robot-ndt-static-initial", "NDT · " + label("首轮", "initial")),
        ("ndt", "robot-ndt-static", "NDT"),
        ("gicp", "robot-gicp-static", "GICP"),
    ]:
        folder = "results/reference/" + folder_name
        data = read(folder + "/record.json")["metrics"]["cases"][method]
        old_rows.append(
            [
                name,
                num(data["position_rmse_m"], 100),
                num(data["yaw_rmse_deg"]),
                data["samples"],
                record_link(folder),
            ]
        )
        if folder_name != "robot-ndt-static-initial":
            old_videos.append((name, folder + "/execution.gif", folder + "/result.gif"))
    lines += [
        table(
            [label("方法", "Method"), "XY RMSE / cm", "yaw RMSE / °", "N", label("记录", "Record")], old_rows
        ),
        clips(old_videos),
        analysis_slot(previous, "earlier-raw-map-3d-static-trials", zh),
        "</details>",
        "",
        '<a id="supplementary-live-scene-recordings"></a>',
        '<a id="补充场景实时录制"></a>' if zh else "",
        "<details>",
        "<summary>" + label("补充采集与定位", "Additional acquisition and localization") + "</summary>",
        "",
    ]
    supp_rows, supp_videos = [], []
    for scene in scenes[:3]:
        key, cn, en = scene
        folder = f"results/reference/robot-supp-{key}"
        data = read(folder + "/record.json")["metrics"]
        mapping = key != "large-change"
        supp_rows.append(
            [
                cn if zh else en,
                "slam_toolbox" if mapping else "AMCL",
                str(data["mapping_frames"]) if mapping else "—",
                str(data["observed_map"]["known_cells"]) if mapping else "—",
                "—" if mapping else num(data["cases"]["raw"]["position_rmse_m"], 100),
                record_link(folder),
            ]
        )
        supp_videos.append((cn if zh else en, folder + "/execution.gif", None))
    lines += [
        label(
            "帧数＝已保存扫描数量；已知格＝非未知栅格数。",
            "Frames = saved scans; known cells = non-unknown grid cells.",
        ),
        "",
        table(
            [
                label("场景", "Scene"),
                label("方法", "Method"),
                label("帧数", "Frames"),
                label("已知格", "Known cells"),
                "XY RMSE / cm",
                label("记录", "Record"),
            ],
            supp_rows,
        ),
        clips(supp_videos),
        analysis_slot(previous, "supplementary-live-scene-recordings", zh),
        "</details>",
        "",
        '<a id="srrg-diagnostics"></a>',
        "<details>",
        "<summary>" + label("SRRG失败记录", "SRRG failed runs") + "</summary>",
        "",
    ]
    diagnostic_folders = [
        ("srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d", "Eigen ABI"),
        ("srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3", "stdout transport"),
        ("srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d", "g2o / graph merge"),
    ]
    diagnostic_rows = []
    for folder_name, stage in diagnostic_folders:
        folder = "results/reference/" + folder_name
        diagnostic_rows.append(
            [
                stage,
                read(folder + "/record.json")["status"],
                record_link(folder),
                f"[GIF]({link(doc, folder + '/execution.gif')}) · [MP4]({link(doc, folder + '/execution.mp4')})",
            ]
        )
    lines += [
        "<!-- HOME_SRRG_DIAGNOSTICS -->",
        table(
            [
                label("环节", "Stage"),
                label("状态", "Status"),
                label("记录", "Record"),
                label("视频", "Video"),
            ],
            diagnostic_rows,
        ),
        "<!-- /HOME_SRRG_DIAGNOSTICS -->",
        analysis_slot(previous, "srrg-diagnostics", zh),
        "</details>",
        "",
        top(),
        "",
    ]
    if current:
        lines += ["</details>", ""]
    return "\n".join(lines)
