"""Concise current experiment definitions, measurements, media and blank analysis."""

import json

SUITE = "results/reference/direction-20261016"


def read(root, path):
    return json.loads((root / path).read_text(encoding="utf-8"))


def number(value, scale=1):
    return "N/A" if value is None else f"{value * scale:.2f}"


def percent(value):
    return "N/A" if value is None else f"{value * 100:.2f}%"


def table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(map(str, row)) + " |" for row in rows],
        ]
    )


def render_2d(doc, zh, previous, scene, *, root, link, analysis_slot):
    key, cn, en = scene
    anchor = "change" if key == "large-change" else key
    folder = SUITE + "/2d-" + key
    lines = [
        f'<a id="scene-{anchor}-2d"></a>',
        "",
        "#### " + ("原生二维地图 + AMCL · Raw / SRRG" if zh else "Native 2D maps + AMCL · Raw / SRRG"),
        "",
    ]
    if not (root / folder / "time-grid-score.json").is_file():
        return "\n".join(
            lines
            + [
                (
                    "独立B待测；本栏不再展示DUFOMap／BeautyMap二维投影。"
                    if zh
                    else "Separate B pending; projected DUFOMap/BeautyMap arms are removed."
                ),
                "",
                analysis_slot(previous, f"scene-{anchor}-2d", zh),
            ]
        )
    record = read(root, folder + "/time-grid-score.json")
    rows = []
    for method, label in [("raw", "Raw"), ("srrg", "SRRG")]:
        name = ("degraded_" if key == "corridor" else "") + method
        m = record["methods"][name]
        v = m["common"]
        rows.append(
            [
                label,
                number(v["rmse_m"], 100),
                number(v["yaw_rmse_deg"]),
                number(v["p95_m"], 100),
                percent(v["over_25cm_fraction"]),
                percent(m["fresh_update_grid_coverage"]),
                v["samples"],
            ]
        )
    lines += [
        table(
            [
                "Map",
                "XY RMSE / cm",
                "yaw RMSE / °",
                "P95 / cm",
                "P(e>25cm)",
                ("新鲜更新覆盖" if zh else "Fresh-update coverage"),
                "N",
            ],
            rows,
        ),
        "",
        f"[{'评分' if zh else 'Scores'}]({link(doc, folder + '/time-grid-score.json')}) · [{'记录' if zh else 'Record'}]({link(doc, folder + '/record.json')})",
        "",
    ]
    for method, label in [("raw", "Raw"), ("srrg", "SRRG")]:
        name = ("degraded_" if key == "corridor" else "") + method
        gif = link(doc, folder + f"/executions/{name}.gif")
        mp4 = link(doc, folder + f"/executions/{name}.mp4")
        lines += [
            f"**{label}**",
            f'<a href="{mp4}"><img src="{gif}" width="480" loading="lazy" alt="{label} native AMCL recording"></a>',
            "",
        ]
    return "\n".join(lines + [analysis_slot(previous, f"scene-{anchor}-2d", zh)])


def render(doc, zh, previous, *, root, link, analysis_slot):
    if not (root / SUITE / "2d-dynamic/time-grid-score.json").exists():
        return ""

    def label(cn, en):
        return cn if zh else en

    def href(path):
        return link(doc, SUITE + "/" + path)

    def media(path, title, width=640):
        return f'**{title}**\n\n<a href="{href(path + ".mp4")}"><img src="{href(path + ".gif")}" width="{width}" loading="lazy" alt="{title}"></a>\n'

    lines = [
        '<a id="direction-experiments-20261016"></a>',
        "",
        "### " + label("当前三个开放问题：H1／H2／H3", "Current three questions: H1/H2/H3"),
        "",
        "[E1 · H1](#direction-e1) · [E2 · H2](#direction-e2) · [E3a · H3](#direction-e3a) · [E3b · H3](#direction-e3b)",
        "",
        table(
            [label("实验设置", "Setup"), label("实际内容", "Actual configuration")],
            [
                [
                    label("场景／机器人", "Scene / robot"),
                    label(
                        "原静态、动态、长廊；Sim2Real三轮全向底盘；全部为仿真",
                        "Original static, dynamic and corridor worlds; Sim2Real omni chassis; simulation",
                    ),
                ],
                [
                    "E1",
                    label(
                        "2D原生雷达720束＋轮式里程计；A冻结图，独立B用相同AMCL；3D原Raw／DUFOMap／BeautyMap和GICP不变",
                        "2D native 720-beam LiDAR + wheel odometry; frozen A, separate B with fixed AMCL; existing 3D arms unchanged",
                    ),
                ],
                [
                    "E2",
                    label(
                        "独立IMU变体200Hz；三帧各取120°实测扇区，扫描跨度约0.2s；FAST-LIO2点补偿开／关",
                        "Isolated 200Hz IMU variant; three measured 120° sectors, ~0.2s span; FAST-LIO2 point compensation on/off",
                    ),
                ],
                [
                    "E3a",
                    label(
                        "同一真实仿真扫描的固定缺测扇区回放；只检查未知／自由空间语义",
                        "Fixed-sector dropout replay of a real simulated scan; unknown/free semantics only",
                    ),
                ],
                [
                    "E3b",
                    label(
                        "原长廊 vs 新增两处0.24×0.24×0.9m非对称侧向几何标志，分别录A／B",
                        "Original vs two asymmetric 0.24×0.24×0.9m side landmarks, separately record A/B",
                    ),
                ],
            ],
        ),
        "",
        label(
            "定位表按共同10Hz真值网格重新计算误差，前5s预热，位姿年龄≤0.15s。新鲜更新覆盖受AMCL运动触发发布影响，不能直接当成失跟率。少量单轮结果用于探索。",
            "Pose errors are recomputed at common 10Hz truth timestamps after 5s, pose age≤0.15s. Fresh-update coverage depends on AMCL motion-triggered publishing and is not tracking-loss rate. Single runs are exploratory.",
        ),
        "",
        '<a id="direction-e1"></a>',
        "",
        "#### E1 · H1 · "
        + label("动态残影 → 地图 → 独立定位", "Dynamic traces → map → held-out localization"),
        "",
    ]
    rows = []
    for scene, cn, en in [
        ("static", "静态", "Static"),
        ("dynamic", "动态", "Dynamic"),
        ("corridor", "长廊", "Corridor"),
    ]:
        a = read(root, SUITE + "/2d-A-" + scene + "/record.json")
        b = read(root, SUITE + "/2d-" + scene + "/time-grid-score.json")
        for method, name in [("raw", "Raw"), ("srrg", "SRRG")]:
            m = a["methods"][method]
            v = b["methods"][("degraded_" if scene == "corridor" else "") + method]["common"]
            rows.append(
                [
                    cn if zh else en,
                    name,
                    percent(m["dynamic_removal"]),
                    percent(m["static_retention"]),
                    number(m["observed_static_support_distance_rmse_m"], 100),
                    number(v["rmse_m"], 100),
                ]
            )
    lines += [
        table(
            [
                label("场景", "Scene"),
                "Map",
                "DA",
                "SA",
                label("地图支持距离RMSE / cm", "Map support-distance RMSE / cm"),
                "B XY RMSE / cm",
            ],
            rows,
        ),
        "",
        label(
            "地图支持距离：10cm体素点到已观测静态支持的最近距离，不是精确表面误差；SA为15cm容差的静态覆盖。下方二维栏给出各方法新录像。A使用实际对应的历史采集，B为本轮新运行。",
            "Map support distance: 10cm-voxel nearest observed static support, not exact surface error; SA uses 15cm coverage tolerance. Native 2D panels below contain new recordings. A is the actual earlier acquisition paired with new B.",
        ),
        "",
    ]
    for scene, cn, en in [
        ("static", "静态A", "Static A"),
        ("dynamic", "动态A", "Dynamic A"),
        ("corridor", "长廊A", "Corridor A"),
    ]:
        lines += [
            f"[{cn if zh else en}]({href('2d-A-' + scene + '/record.json')}) · [GIF]({href('2d-A-' + scene + '/execution.gif')})"
        ]
    lines += [
        "",
        "<details>",
        "<summary>" + label("E1 · 三场景独立B新录像", "E1 · new held-out B recordings") + "</summary>",
        "",
    ]
    for scene, cn, en in [
        ("static", "静态", "Static"),
        ("dynamic", "动态", "Dynamic"),
        ("corridor", "长廊", "Corridor"),
    ]:
        for method in ["raw", "srrg"]:
            name = ("degraded_" if scene == "corridor" else "") + method
            lines += [media("2d-" + scene + "/executions/" + name, (cn if zh else en) + " · " + method, 480)]
    lines += ["</details>", ""]
    lines += [
        "",
        analysis_slot(previous, "direction-h1", zh),
        '<a id="direction-e2"></a>',
        "",
        "#### E2 · H2 · FAST-LIO2 · " + label("运动畸变", "Motion distortion"),
        "",
    ]
    score_file = root / SUITE / "fastlio-maps/score.json"
    if score_file.exists():
        s = read(root, SUITE + "/fastlio-maps/score.json")
        rows = []
        for method, title in [
            ("deskew", label("点补偿开启", "Point compensation on")),
            ("no_deskew", label("仅点补偿关闭", "Point compensation off")),
        ]:
            m = s["methods"][method]
            rows.append(
                [
                    title,
                    number(m["surface_rmse_m"], 100),
                    number(m["surface_p95_m"], 100),
                    percent(m["observed_static_coverage_5cm"]),
                    number(m["xyz_rmse_m"], 100),
                    m["native_pose_samples"],
                ]
            )
        lines += [
            table(
                [
                    label("方法", "Method"),
                    "Map RMSE / cm",
                    "Map P95 / cm",
                    label("5cm静态覆盖", "5cm static coverage"),
                    label("自身里程计XYZ RMSE / cm", "Own odometry XYZ RMSE / cm"),
                    "N",
                ],
                rows,
            ),
            "",
            label(
                "地图为共同时间的原生注册扫描累计，含地面与漂移点，不是ikd-Tree原生导出。只用一次初始位姿对齐。先过滤无效回波，并在3s静止稳定后送入IMU与扫描；静止、慢转、快转和平移分阶段记录。",
                "Maps accumulate common-time native registered scans, including ground and drifted points; not native ikd-Tree exports. One initial-pose alignment only. Invalid returns are filtered; IMU/scans start after 3s settling. Stationary, slow-turn, fast-turn and translation phases are recorded separately.",
            ),
            "",
            media(
                "fastlio-motion/execution",
                label(
                    "FAST-LIO2 同输入双组 · 绿色开启补偿／橙色关闭",
                    "FAST-LIO2 paired native execution · green on / orange off",
                ),
            ),
            f"[{label('地图与里程计评分', 'Map / odometry scores')}]({href('fastlio-maps/score.json')})",
            "",
        ]
        phase_rows = []
        for phase, cn, en in [
            ("stationary", "静止", "Stationary"),
            ("slow_turn", "慢转", "Slow turn"),
            ("fast_turn", "快转", "Fast turn"),
            ("translation", "平移", "Translation"),
        ]:
            on = s["methods"]["deskew"]["phases"][phase]
            off = s["methods"]["no_deskew"]["phases"][phase]
            phase_rows.append(
                [
                    cn if zh else en,
                    number(on["xyz_rmse_m"], 100),
                    number(off["xyz_rmse_m"], 100),
                    number(on["rotation_rmse_deg"]),
                    number(off["rotation_rmse_deg"]),
                ]
            )
        lines += [
            table(
                [
                    label("阶段", "Phase"),
                    "On XYZ / cm",
                    "Off XYZ / cm",
                    "On rotation / °",
                    "Off rotation / °",
                ],
                phase_rows,
            ),
            "",
        ]
    b_path = root / SUITE / "fastlio-B/record.json"
    if b_path.exists():
        b = read(root, SUITE + "/fastlio-B/record.json")
        rows = []
        s3 = read(root, SUITE + "/fastlio-B/score-3d.json")
        for method in ["deskew", "no_deskew"]:
            m = s3[method]
            rows.append(
                [
                    method,
                    number(m["xyz_rmse_m"], 100),
                    number(m["rotation_rmse_deg"]),
                    number(m["xyz_p95_m"], 100),
                    percent(m["fresh_update_grid_coverage"]),
                    m["samples"],
                ]
            )
        lines += [
            table(
                [
                    label("冻结地图", "Frozen map"),
                    "B XYZ RMSE / cm",
                    "Rotation / °",
                    "P95 / cm",
                    label("新鲜更新覆盖", "Fresh-update coverage"),
                    "N",
                ],
                rows,
            ),
            "",
        ]
        for method in ["deskew", "no_deskew"]:
            lines += [media("fastlio-B/executions/" + method, "B · " + method, 480)]
    else:
        lines += [
            label(
                "独立冻结地图B：执行／打包中；自身里程计不能替代此项。",
                "Held-out B on frozen maps: running/packaging; own odometry does not substitute.",
            ),
            "",
        ]
    lines += [
        analysis_slot(previous, "direction-h2", zh),
        '<a id="direction-e3a"></a>',
        "",
        "#### E3a · H3 · " + label("镜面缺测边界检查", "Mirror missing-return boundary check"),
        "",
    ]
    r = read(root, SUITE + "/mirror-control/record.json")
    rows = [
        [
            n,
            v["wrongly_cleared_boundary_cells"],
            v["reference_boundary_cells"],
            percent(v["boundary_retention"]),
        ]
        for n, v in r["metrics"].items()
    ]
    lines += [
        table(
            [
                label("更新规则", "Update rule"),
                label("误清空边界格", "Wrongly cleared cells"),
                label("参考边界格", "Reference cells"),
                label("边界保留", "Boundary retention"),
            ],
            rows,
        ),
        "",
        f'<a href="{href("mirror-control/record.json")}"><img src="{href("mirror-control/control-replay.gif")}" width="640" loading="lazy" alt="E3a controlled scan replay"></a>',
        "",
        label(
            "这是固定姿态、受控缺测的数据回放，不是镜面物理实录，不验证镜面识别或定位收益。",
            "Fixed-pose controlled-dropout data replay, not physical mirror footage; no mirror-detection or localization-benefit claim.",
        ),
        "",
        analysis_slot(previous, "direction-h3-mirror", zh),
        '<a id="direction-e3b"></a>',
        "",
        "#### E3b · H3 · " + label("长廊几何干预", "Corridor geometry intervention"),
        "",
    ]
    comparison = root / SUITE / "corridor-comparison.json"
    if comparison.exists():
        c = read(root, SUITE + "/corridor-comparison.json")
        rows = []
        for scene, title in [
            ("original", label("原长廊", "Original")),
            ("landmark", label("加非对称地标", "Landmarks")),
        ]:
            for method in ["degraded_raw", "degraded_srrg"]:
                m = c["methods"][scene + "-" + method]
                v = m["limited"]
                rows.append(
                    [
                        title,
                        method,
                        number(v["along_rmse_m"], 100),
                        number(v["across_rmse_m"], 100),
                        v["samples"],
                        percent(m["fresh_coverage"]),
                    ]
                )
        lines += [
            table(
                [
                    label("场景", "Scene"),
                    "Map",
                    label("前50s沿廊RMSE / cm", "First-50s along RMSE / cm"),
                    label("横向RMSE / cm", "Across RMSE / cm"),
                    "N",
                    label("新鲜更新覆盖", "Fresh-update coverage"),
                ],
                rows,
            ),
            "",
            media(
                "corridor-landmark-mapping/execution",
                label("派生长廊A · 新录制", "Derived corridor A · new recording"),
            ),
        ]
        for m in ["degraded_raw", "degraded_srrg"]:
            lines += [media("2d-landmark-corridor/executions/" + m, "B · " + m, 480)]
        lines += [
            f"[{label('四组共同时间评分', 'Four-way common-time scores')}]({href('corridor-comparison.json')})",
            "",
        ]
    lines += [analysis_slot(previous, "direction-h3-corridor", zh), ""]
    return "\n".join(lines)
