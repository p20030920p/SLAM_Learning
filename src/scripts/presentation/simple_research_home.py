"""A short bilingual homepage: three hypotheses, direct experiment links, data only."""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUITE = "results/reference/direction-20261016-v2"
MARKER = "<!-- SIMPLE_HYPOTHESES_V2 -->"


def table(head, rows):
    return (
        "\n".join(
            [
                "| " + " | ".join(head) + " |",
                "| " + " | ".join(["---"] * len(head)) + " |",
                *["| " + " | ".join(map(str, row)) + " |" for row in rows],
            ]
        )
        + "\n\n"
    )


def num(value, scale=1):
    return "N/A" if value is None else f"{value * scale:.2f}"


def pct(value):
    return num(value, 100) + ("%" if value is not None else "")


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def hypotheses(zh):
    def label(cn, en):
        return cn if zh else en

    rows = [
        [
            "H1 / Q1",
            label(
                "动态清图在保留静态结构的同时减少残影，并降低独立定位误差。",
                "Dynamic cleaning removes traces while retaining static structure and reduces held-out localization error.",
            ),
            "Raw / SRRG",
            label("DA、SA、Eₘ、XY RMSE", "DA, SA, Eₘ, XY RMSE"),
        ],
        [
            "H2 / Q2",
            label(
                "FAST-LIO去畸变能降低运动造成的地图误差，并提高独立定位精度。",
                "FAST-LIO deskew reduces motion-induced map error and improves held-out localization accuracy.",
            ),
            label("点补偿关 / 开", "Point compensation off / on"),
            label("Eₘ、Cₘ、XYZ RMSE", "Eₘ, Cₘ, XYZ RMSE"),
        ],
        [
            "H3 / Q3",
            label(
                "长廊中增加雷达可见的非对称静态参照，能降低沿廊定位误差。",
                "Adding LiDAR-visible asymmetric static references reduces along-corridor localization error.",
            ),
            label("原长廊 / 加参照长廊", "Original / landmark corridor"),
            label("Eₘ、SA、沿廊 RMSE", "Eₘ, SA, along RMSE"),
        ],
    ]
    body = (
        '<a id="mapping-hypothesis-tests"></a>\n\n## '
        + label("假设", "Hypothesis")
        + "\n\n"
        + MARKER
        + "\n\n"
    )
    body += table(
        [
            label("问题", "Question"),
            label("一句话假设", "Hypothesis"),
            label("对照方法", "Controls"),
            label("指标", "Metrics"),
        ],
        rows,
    )
    body += label(
        "目标：先检查地图是否改善，再检验同一定位器在独立B中的误差是否下降。\n\n",
        "Goal: first measure map improvement, then test whether the same localizer has lower error on independent B.\n\n",
    )
    body += label(
        "镜面识别与真实反射仍是Q3中待验证的部分，实物证据保留在首页开头。\n\n",
        "Mirror identification and physical reflections remain open within Q3; physical evidence stays at the top.\n\n",
    )
    body += '<a id="hypothesis-math"></a>\n\n### ' + label("数学表达", "Mathematical form") + "\n\n"
    body += (
        label(
            r"A用于建图，B是另一次采集；冻结A的地图后，用相同定位器处理B。$`j`$是对照方法，$`Z`$是扫描，$`T`$是传感器位姿，$`p^{\ast}`$是位置真值：",
            r"A builds the map; B is a separate acquisition. Freeze A's map and run the same localizer on B. $`j`$ indexes the control, $`Z`$ denotes scans, $`T`$ is the sensor pose and $`p^{\ast}`$ is true position:",
        )
        + "\n\n"
    )
    # GitHub math fences keep Markdown from consuming TeX escapes and symbols.
    # Separate blocks also avoid an aligned environment spanning HTML paragraphs.
    body += r"""```math
M_j = \mathcal{B}_j\bigl(Z^A,\hat{T}_j^A\bigr)
```

```math
\hat{T}_{j,t}^B = \mathcal{L}\bigl(Z_{\leq t}^B,M_j\bigr)
```

```math
E_L(j) = \sqrt{\frac{1}{N}\sum_t\left\lVert\hat{p}_{j,t}^B-p_t^{B,\ast}\right\rVert^2}
```

```math
\Delta E_L = E_L(\mathrm{baseline})-E_L(\mathrm{method})
```

"""
    body += (
        label(
            r"$`\Delta E_L\gt 0`$表示定位改善；地图误差$`E_M`$下降但$`\Delta E_L\leq 0`$时，只支持建图改善。下式是要检验的预测：",
            r"$`\Delta E_L\gt 0`$ means improved localization; lower map error $`E_M`$ with $`\Delta E_L\leq 0`$ supports only map improvement. Test these predictions:",
        )
        + "\n\n"
    )
    body += r"""**H1**

```math
\mathrm{DA}_{\mathrm{SRRG}}\gt\mathrm{DA}_{\mathrm{Raw}},\qquad \mathrm{SA}_{\mathrm{SRRG}}\geq\mathrm{SA}_{\mathrm{Raw}}-\varepsilon
```

```math
E_M(\mathrm{SRRG})\lt E_M(\mathrm{Raw}),\qquad\Delta E_L\gt 0
```

**H2**

```math
p_i^{\mathrm{end}}=T(t_{\mathrm{end}})^{-1}T(t_i)p_i
```

```math
E_M(\mathrm{on})\lt E_M(\mathrm{off}),\qquad\Delta E_L\gt 0
```

**H3**

```math
E_{\parallel}=\sqrt{\frac{1}{N}\sum_t\left[u^{\mathsf{T}}\left(\hat{p}_t-p_t^{\ast}\right)\right]^2}
```

```math
E_{\parallel}(\mathrm{landmark})\lt E_{\parallel}(\mathrm{original})
```

"""
    body += (
        label(
            r"$`\varepsilon=1`$个百分点为本轮静态损失容差；$`u`$为走廊方向。SRRG本轮是端到端对照，包含位姿优化与地图维护；给定相同位姿的纯删除消融仍待做。真值仅用于评分。",
            r"$`\varepsilon=1`$ percentage point is the static-loss tolerance; $`u`$ is the corridor direction. This SRRG comparison includes pose optimization and maintenance; deletion alone at fixed poses remains untested. Truth is used only for scoring.",
        )
        + "\n\n"
    )
    body += '<a id="hypothesis-pseudocode"></a>\n\n### ' + label("伪代码", "Pseudocode") + "\n\n"
    body += """```text
for scene in [static, dynamic, motion, corridor, corridor_landmarks]:
    controls = methods_for(scene)
    A, maps = record_A_and_build_maps(scene, controls)
    map_metrics = score_and_freeze(maps)
    B = record_new_localization_session(scene)
    poses = same_localizer_for_all_maps(B, maps)
    report(map_metrics, score_on_common_times(poses, B.truth))
    save_native_recordings_and_input_hashes()
compare_corridor_variants_on_common_elapsed_times()
```

"""
    body += (
        label(
            "H3分别采集原长廊与加参照场景的A/B，保持路线、速度、初始偏移和定位参数相同。\n\n[实验与新录像](#practice-index)",
            "For H3, acquire A/B in each corridor variant with the same route, speed, initial offset and localization settings.\n\n[Experiments and new recordings](#practice-index)",
        )
        + "\n\n"
    )
    return body


def metric_table(zh):
    def label(cn, en):
        return cn if zh else en

    return table(
        [label("指标", "Metric"), label("一句话说明", "Definition")],
        [
            [
                "DA ↑ / SA ↑",
                label(
                    "仅评清图A：动态删除比例／静态保留比例；无动态时只列SA。二维按观测支持、三维按点评分。",
                    "Cleaning A only: dynamic removal / static retention; omit DA without dynamics. Units are observed support in 2D and points in 3D.",
                ),
            ],
            [
                "Eₘ ↓",
                label(
                    "去畸变A：地图点到静态参考几何的距离RMSE，cm。",
                    "Deskew A: map-point distance RMSE to static reference geometry, cm.",
                ),
            ],
            [
                label("XY / XYZ RMSE ↓", "XY / XYZ RMSE ↓"),
                label(
                    "冻结地图后的定位B：二维／三维位置误差，cm。",
                    "Localization B on frozen maps: 2D / 3D position error, cm.",
                ),
            ],
            [
                label("沿廊 RMSE ↓", "Along RMSE ↓"),
                label(
                    "H3受限观测阶段：沿走廊方向的位置误差，cm。", "H3 during limited observations: position error along the corridor, cm."
                ),
            ],
            [
                label("角度RMSE ↓", "Angular RMSE ↓"),
                label("仅在评价姿态时报告偏航或三维旋转误差，度；A里程计误差单独标注。", "Yaw or 3D rotation error when pose orientation is evaluated, degrees; A odometry is labelled separately."),
            ],
        ],
    )


def metrics(previous, zh):
    title = "指标" if zh else "Metrics"
    evidence = "实验证据" if zh else "Evidence"
    body = "## " + title + "\n\n" + metric_table(zh) + "### " + evidence + "\n\n"
    # Retain only tables; include method/data identity inside each table.
    for method in ["DUFOMap", "BeautyMap", "IR-MCL"]:
        part = re.search(r"^#### " + re.escape(method) + r"\n(.*?)(?=^#### |\Z)", previous, re.M | re.S)
        if part:
            found = re.search(r"(?m)^\|.*(?:\n\|.*)+", part.group(1))
            if found:
                rows = found.group().splitlines()
                rows[0] = rows[0].replace("| ", "| " + method + " · ", 1)
                body += "\n".join(rows) + "\n\n"
        else:
            # Idempotent after headings/prose were removed.
            found = re.search(r"(?m)^\| " + re.escape(method) + r" · .*(?:\n\|.*)+", previous)
            if found:
                body += found.group() + "\n\n"
    body = body.replace("DUFOMap · 指标", "DUFOMap · KITTI-00 · 指标").replace(
        "DUFOMap · Metric", "DUFOMap · KITTI-00 · Metric"
    )
    body = body.replace("BeautyMap · 指标", "BeautyMap · KITTI-02 · 指标").replace(
        "BeautyMap · Metric", "BeautyMap · KITTI-02 · Metric"
    )
    # Show only task-specific evidence; retain complete scoring in source records.
    body = "\n".join(
        line for line in body.splitlines()
        if not re.match(r"^\| (?:AA|HA|Location <|Yaw <|位置 <|偏航 <|位置小于|偏航小于)", line)
    ) + "\n\n"
    return body


def related(previous, doc, zh):
    def href(path):
        return os.path.relpath(ROOT / path, doc.parent).replace("\\", "/")

    text = previous
    for method in ["dufomap", "beautymap", "ir-mcl"]:
        preview = href(f"docs/media/related-pointcloud/20261016/{method}.gif")
        full = href(f"results/reference/desktop-live-{method}/execution.mp4")
        caption = "点云实录节选" if zh else "Point-cloud capture excerpt"
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if f'id="related-{method}"' in line:
                cells = line.split(" | ")
                cells[1] = (
                    f'<a href="{full}"><img src="{preview}" width="280" loading="lazy" alt="{method} · {caption}"></a><br>[{caption}]({full})'
                )
                lines[i] = " | ".join(cells)
        text = "\n".join(lines) + "\n"
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if 'id="related-adam-mcl"' in line:
            cells = line.split(" | ")
            folder = "results/reference/desktop-adam-mcl"
            caption = "二维粒子结果回放" if zh else "2D particle-result replay"
            cells[1] = (
                f'<a href="{href(folder + "/result.mp4")}"><img src="{href(folder + "/result.gif")}" width="280" loading="lazy" alt="AdaM-MCL · {caption}"></a><br>{caption}'
            )
            lines[i] = " | ".join(cells)
    text = "\n".join(lines) + "\n"
    text = text.replace("| 原库复现GIF |", "| 原库复现GIF／原文点云图 |").replace(
        "Author-repository reproduction GIF", "Native GIF / original point-cloud figure"
    )
    text = text.replace("| Reproduction GIF |", "| Native GIF / original point-cloud figure |")
    base = href("docs/assets/related/20261016-pointcloud") + "/"
    text = re.sub(
        r'<img src="[^"]*fastlio2-fig1.png"[^>]*>',
        f'<img src="{base}fastlio2-fig12.png" width="280" alt="FAST-LIO2 original Fig. 12: point-cloud map">',
        text,
    )
    text = re.sub(
        r'<img src="[^"]*srrg-fig1.png"[^>]*>',
        f'<img src="{base}srrg-fig7.png" width="280" alt="SRRG original Fig. 7: point-cloud map">',
        text,
    )
    text = re.sub(
        r"!\[SRRG [^\]]*\]\([^)]*srrg-fig1.png\)",
        f"![SRRG · original point-cloud Fig. 7]({base}srrg-fig7.png)",
        text,
    )
    text = re.sub(
        r"!\[FAST-LIO2 [^\]]*\]\([^)]*fastlio2-fig1.png\)",
        f"![FAST-LIO2 · original point-cloud Fig. 12]({base}fastlio2-fig12.png)",
        text,
    )
    text = text.replace("图1，第2页", "图7，第6页").replace("Fig. 1, page 2", "Fig. 7, page 6")
    text = text.replace("图1，第4页", "图12，第16页").replace("Fig. 1, page 4", "Fig. 12, page 16")
    text = text.replace("#srrg-2d", "#experiment-h1").replace(
        "#direction-experiments-20261016", "#experiment-h2"
    )
    return text


def practice(doc, zh, previous):
    from compact_practice import analysis_slot
    from publish_home_experiments import quality, pct as old_pct

    def label(cn, en):
        return cn if zh else en

    def href(path):
        return os.path.relpath(ROOT / path, doc.parent).replace("\\", "/")

    def ref(path, name):
        return f"[{name}]({href(path)})"

    lines = [
        "## " + label("实践", "Practice"),
        "",
        "<!-- HOME_EXPERIMENTS_V2 -->",
        MARKER,
        "",
        '<a id="practice-index"></a>',
        "",
        "### " + label("目录", "Contents"),
        "",
    ]
    toc = [
        [
            "0",
            label("实验设置", "Setup"),
            "[URDF](#robot-urdf) · [" + label("指标", "Metrics") + "](#practice-metrics)",
            "[↗](#practice-setup)",
        ],
        [
            "1",
            "H1 · " + label("动态清图", "Dynamic cleaning"),
            "["
            + label("静态A", "Static A")
            + "](#h1-static-a) / [B](#h1-static-b) · ["
            + label("动态A", "Dynamic A")
            + "](#h1-dynamic-a) / [B](#h1-dynamic-b)",
            "[↗](#experiment-h1)",
        ],
        [
            "2",
            "H2 · FAST-LIO",
            "[A](#h2-a) · ["
            + label("静止", "Stationary")
            + "](#h2-stationary) / ["
            + label("慢转", "Slow turn")
            + "](#h2-slow) / ["
            + label("快转", "Fast turn")
            + "](#h2-fast) / ["
            + label("平移", "Translation")
            + "](#h2-translation) · [B](#h2-b)",
            "[↗](#experiment-h2)",
        ],
        [
            "3",
            "H3 · " + label("长廊参照", "Corridor references"),
            "["
            + label("原场景A", "Original A")
            + "](#h3-original-a) / [B](#h3-original-b) · ["
            + label("加参照A", "Landmark A")
            + "](#h3-landmark-a) / [B](#h3-landmark-b) · ["
            + label("配对指标", "Paired scores")
            + "](#h3-scores)",
            "[↗](#experiment-h3)",
        ],
        [
            "4",
            label("三维原测试", "Existing 3D tests"),
            "["
            + label("静态", "Static")
            + "](#scene-static-3d) · ["
            + label("动态", "Dynamic")
            + "](#scene-dynamic-3d) · ["
            + label("长廊", "Corridor")
            + "](#scene-corridor-3d) · ["
            + label("结构变化", "Changed world")
            + "](#scene-change-3d)",
            "[↗](#baseline-3d)",
        ],
        [
            "5",
            label("补充实验", "Supplementary experiments"),
            "[SRRG](#supp-srrg) · ["
            + label("点云回放", "Cloud replay")
            + "](#map-review-3d) · [NDT/GICP](#supp-registrations) · ["
            + label("采集", "Acquisition")
            + "](#supp-acquisition) · ["
            + label("失败记录", "Failed runs")
            + "](#srrg-diagnostics)",
            "[↗](#practice-appendix)",
        ],
    ]
    lines += [
        table(
            [
                label("序号", "No."),
                label("实验", "Experiment"),
                label("下属实验（直接点击）", "Subexperiments (direct links)"),
            ],
            [[row[0], row[3].replace("↗", row[1]), row[2]] for row in toc],
        ),
        '<a id="practice-setup"></a>',
        "",
        "### " + label("实验设置", "Setup"),
        "",
        table(
            [label("项目", "Item"), label("设置", "Setting")],
            [
                [label("平台", "Platform"), "Windows / WSL2 · ROS 2 Jazzy · Gazebo Harmonic · RViz2"],
                [
                    label("机器人", "Robot"),
                    label(
                        "Sim2Real全向轮底盘；URDF截图见下。", "Sim2Real omni chassis; rendered URDF below."
                    ),
                ],
                [
                    label("二维设备", "2D devices"),
                    label("720束二维激光雷达＋轮式里程计。", "720-beam 2D LiDAR + wheel odometry."),
                ],
                [
                    label("三维设备", "3D devices"),
                    label(
                        "16×720三维激光雷达；FAST-LIO组另加200 Hz IMU。",
                        "16×720 3D LiDAR; FAST-LIO arm adds a 200 Hz IMU.",
                    ),
                ],
            ],
        ),
        '<a id="robot-urdf"></a>',
        "",
        f'<img src="{href("docs/media/robot/20261016/urdf.png")}" width="560" alt="Actual robot URDF rendered in RViz">',
        "",
        '<a id="practice-metrics"></a>',
        "",
        "### " + label("指标说明", "Metric definitions"),
        "",
        "["
        + label("简短定义见指标表", "Short definitions in Metrics")
        + "](#"
        + ("指标" if zh else "metrics")
        + ")",
        "",
        label(
            "A按任务评价清图或几何；B评价冻结地图后的定位。B使用共同10 Hz时间点，预热5秒，输出滞后≤0.15秒；样本数与缺失情况见记录。每组1轮，未测完整导航到达效果。",
            "A measures cleaning or geometry for the task; B measures localization on frozen maps. B uses common 10 Hz times after 5 s warmup, with pose age ≤0.15 s; counts and missing outputs remain in records. One run per arm; complete navigation outcomes were not measured.",
        ),
        "",
    ]

    def heading(anchor, text, level=4):
        lines.extend([f'<a id="{anchor}"></a>', "", "#" * level + " " + text, ""])

    def media(folder, items):
        cells = []
        for file, title in items:
            path = folder + "/" + file
            if (ROOT / (path + ".gif")).exists():
                cells.append(
                    f'<a href="{href(path + ".mp4")}"><img src="{href(path + ".gif")}" width="340" loading="lazy" alt="{title}"></a>'
                )
        if cells:
            lines.extend([table([title for _, title in items], [cells])])

    def blank(key):
        lines.extend(
            [analysis_slot(previous, key, zh), "[↑ " + label("目录", "Contents") + "](#practice-index)", ""]
        )

    def map_a(scene, anchor, title):
        heading(anchor, title)
        folder = SUITE + "/2d-A-" + scene
        if not (ROOT / folder / "record.json").exists():
            lines.extend([label("重新录制中。", "New recording in progress."), ""])
            return
        data = read(folder + "/record.json")["methods"]
        dynamic = scene == "dynamic"
        rows = [[name] + ([pct(data[key]["dynamic_removal"])] if dynamic else []) + [pct(data[key]["static_retention"])]
                for key, name in [("raw", "Raw"), ("srrg", "SRRG")]]
        lines.extend(
            [
                table([label("方法", "Method")] + (["DA ↑"] if dynamic else []) + ["SA ↑"], rows),
                ref(folder + "/record.json", label("记录", "Record")),
                "",
            ]
        )
        media(folder, [("execution", "A · Raw / SRRG")])
        blank(anchor)

    def loc_b(scene, anchor, title, corridor=False):
        heading(anchor, title)
        folder = SUITE + "/2d-" + scene
        if not (ROOT / folder / "time-grid-score.json").exists():
            lines.extend([label("重新录制中。", "New recording in progress."), ""])
            return
        data = read(folder + "/time-grid-score.json")["methods"]
        prefix = "degraded_" if corridor else ""
        rows = []
        for key, name in [("raw", "Raw"), ("srrg", "SRRG")]:
            m = data[prefix + key]
            v = m["common"]
            rows.append(
                [
                    name,
                    num(v["rmse_m"], 100),
                    num(v["yaw_rmse_deg"]),
                ]
            )
        lines.extend(
            [
                table(
                    [
                        label("地图", "Map"),
                        "XY RMSE / cm",
                        "yaw / °",
                    ],
                    rows,
                ),
                ref(folder + "/time-grid-score.json", label("评分", "Scores")),
                "",
            ]
        )
        media(
            folder, [("executions/" + prefix + key, name) for key, name in [("raw", "Raw"), ("srrg", "SRRG")]]
        )
        blank(anchor)

    heading(
        "experiment-h1", "H1 · " + label("动态清图 → 独立定位", "Dynamic cleaning → held-out localization"), 3
    )
    lines += [
        table(
            [label("场景", "Scene"), label("只改变", "Change"), label("固定", "Keep fixed")],
            [
                [
                    label("静态对照 / 运动障碍物", "Static control / moving obstacles"),
                    "Raw / SRRG",
                    label(
                        "同次A扫描、同一B扫描、AMCL参数与初始偏移",
                        "Shared A scans, shared B scans, AMCL settings and initial offset",
                    ),
                ]
            ],
        )
    ]
    for scene in ["static", "dynamic"]:
        title = label("静态", "Static") if scene == "static" else label("动态", "Dynamic")
        map_a(scene, "h1-" + scene + "-a", title + " · A")
        loc_b(scene, "h1-" + scene + "-b", title + " · B")

    heading("experiment-h2", "H2 · FAST-LIO " + label("运动畸变", "motion distortion"), 3)
    lines += [
        table(
            [label("场景", "Scene"), label("只改变", "Change"), label("固定", "Keep fixed")],
            [
                [
                    label(
                        "现有静态场景；静止→慢转→快转→平移",
                        "Existing static scene; stationary → slow/fast turns → translation",
                    ),
                    label("FAST-LIO点补偿关 / 开", "FAST-LIO point compensation off / on"),
                    label(
                        "相同扫描、逐点时间、IMU、状态预测；B使用相同GICP",
                        "Same scans, point timing, IMU and state prediction; identical GICP for B",
                    ),
                ]
            ],
        ),
        label(
            "三帧真实扫描各取120°扇区组成0.2秒扫描；这是受控分组采样，不是商用雷达扫描模式。",
            "Three measured 120° sectors form a 0.2 s scan; this is controlled grouped sampling.",
        ),
        "",
    ]
    heading("h2-a", "A · " + label("建图与运动阶段", "Mapping and motion phases"))
    folder = SUITE + "/fastlio-maps"
    if (ROOT / folder / "score.json").exists():
        data = read(folder + "/score.json")["methods"]
        rows = []
        for key, name in [("no_deskew", label("关", "Off")), ("deskew", label("开", "On"))]:
            m = data[key]
            rows.append([name, num(m["surface_rmse_m"], 100)])
        lines += [
            table([label("点补偿", "Point compensation"), "Eₘ / cm ↓"], rows),
            ref(folder + "/score.json", label("评分", "Scores")),
            "",
        ]
    media(SUITE + "/fastlio-motion", [("execution", "A · FAST-LIO on / off")])
    for anchor, phase, title, interval in [
        ("stationary", "stationary", label("静止", "Stationary"), "0–7 s"),
        ("slow", "slow_turn", label("慢转", "Slow turn"), "7–15 s"),
        ("fast", "fast_turn", label("快转", "Fast turn"), "15–31 s"),
        ("translation", "translation", label("平移", "Translation"), "31–39 s"),
    ]:
        heading("h2-" + anchor, title, 5)
        if (ROOT / folder / "score.json").exists():
            rows = []
            for key, name in [("no_deskew", label("关", "Off")), ("deskew", label("开", "On"))]:
                m = data[key]["phases"][phase]
                rows.append(
                    [name, interval, num(m["xyz_rmse_m"], 100), num(m["rotation_rmse_deg"])]
                )
            lines += [
                table(
                    [
                        label("点补偿", "Point compensation"),
                        label("阶段时间", "Phase time"),
                        label("A里程计XYZ RMSE / cm", "A odometry XYZ RMSE / cm"),
                        label("旋转 / °", "Rotation / °"),
                    ],
                    rows,
                )
            ]
    blank("h2-a")
    heading("h2-b", "B · " + label("冻结地图后GICP定位", "GICP on frozen maps"))
    folder = SUITE + "/fastlio-B"
    if (ROOT / folder / "score-3d.json").exists():
        data = read(folder + "/score-3d.json")
        rows = []
        for key, name in [("no_deskew", label("关", "Off")), ("deskew", label("开", "On"))]:
            m = data[key]
            rows.append(
                [
                    name,
                    num(m["xyz_rmse_m"], 100),
                    num(m["rotation_rmse_deg"]),
                ]
            )
        lines += [
            table(
                [
                    label("A点补偿", "A compensation"),
                    "XYZ RMSE / cm",
                    label("旋转 / °", "Rotation / °"),
                ],
                rows,
            ),
            ref(folder + "/score-3d.json", label("评分", "Scores")),
            "",
        ]
    media(folder, [("executions/no_deskew", "Off map"), ("executions/deskew", "On map")])
    blank("h2-b")

    heading("experiment-h3", "H3 · " + label("长廊静态参照", "Corridor static references"), 3)
    lines += [
        table(
            [label("场景", "Scene"), label("只改变", "Change"), label("固定", "Keep fixed")],
            [
                [
                    label("原长廊 / 加参照长廊", "Original / landmark corridor"),
                    label(
                        "侧壁两处非对称0.24×0.24×0.9 m实体",
                        "Two asymmetric physical side blocks, 0.24×0.24×0.9 m",
                    ),
                    label(
                        "SRRG、AMCL、路线、初始偏移；A/B前50秒为72束、240°、3.5 m，随后恢复",
                        "SRRG, AMCL, route and initial offset; A/B use 72 beams, 240°, 3.5 m for 50 s, then restore full scans",
                    ),
                ]
            ],
        )
    ]
    for scene, short, title in [
        ("corridor", "original", label("原长廊", "Original corridor")),
        ("landmark-corridor", "landmark", label("加参照长廊", "Landmark corridor")),
    ]:
        map_a(scene, "h3-" + short + "-a", title + " · A")
        loc_b(scene, "h3-" + short + "-b", title + " · B", corridor=True)
    heading("h3-scores", label("前50秒配对指标", "Paired scores in the first 50 s"))
    path = SUITE + "/corridor-comparison.json"
    if (ROOT / path).exists():
        data = read(path)
        rows = []
        for key, title in [
            ("original-degraded_srrg", label("原长廊", "Original")),
            ("landmark-degraded_srrg", label("加参照", "Landmarks")),
        ]:
            m = data["methods"][key]["limited"]
            rows.append([title, num(m["along_rmse_m"], 100), num(m["across_rmse_m"], 100), m["samples"]])
        lines += [
            table(
                [
                    label("SRRG地图", "SRRG map"),
                    label("沿廊RMSE / cm", "Along RMSE / cm"),
                    label("横向RMSE / cm", "Across RMSE / cm"),
                    "N",
                ],
                rows,
            ),
            ref(path, label("共同时间评分", "Common-time scores")),
            "",
        ]
    blank("h3-scores")

    heading("baseline-3d", label("三维原测试", "Existing 3D tests"), 3)
    lines += [
        label(
            "保留原Raw／DUFOMap／BeautyMap及GICP结果；各表的评分窗口见记录。",
            "Original Raw/DUFOMap/BeautyMap and GICP results are retained; see records for scoring windows.",
        ),
        "",
    ]
    for scene, title in [
        ("static", label("静态", "Static")),
        ("dynamic", label("动态", "Dynamic")),
        ("corridor", label("长廊", "Corridor")),
        ("change", label("结构变化", "Changed world")),
    ]:
        heading("scene-" + scene + "-3d", title + " · 3D")
        folder = "results/reference/robot-3d-" + ("large-change" if scene == "change" else scene)
        data = read(folder + "/record.json")["metrics_3d"]
        map_metrics = quality("large-change" if scene == "change" else scene, "3d")
        rows, mapping_rows = [], []
        for key, name in [("raw", "Raw"), ("dufomap", "DUFOMap"), ("beautymap", "BeautyMap")]:
            m = data[key]
            mapping_rows.append([name] + ([old_pct(map_metrics[key]["dynamic_removal"])] if scene == "dynamic" else []) + [old_pct(map_metrics[key]["static_retention"])])
            rows.append(
                [
                    name,
                    num(m["xyz_rmse_m"], 100),
                    num(m["rotation_rmse_deg"]),
                ]
            )
        lines += [
            "**" + label("A · 地图清理", "A · Map cleaning") + "**\n",
            table([label("地图", "Map")] + (["DA ↑"] if scene == "dynamic" else []) + ["SA ↑"], mapping_rows),
            "**" + label("B · 冻结地图后定位", "B · Localization on frozen maps") + "**\n",
            "<!-- HOME_EXPERIMENT_TABLE -->",
            table(
                [
                    label("地图", "Map"),
                    "XYZ RMSE / cm",
                    label("旋转 RMSE / °", "Rotation RMSE / °"),
                ],
                rows,
            ).rstrip(),
            "<!-- /HOME_EXPERIMENT_TABLE -->",
            "",
            ref(folder + "/record.json", label("记录", "Record")),
            "",
        ]
        if scene == "corridor":
            lines += [label(
                "本组有效定位输出区间不同；RMSE只覆盖有输出的时段，不能据此排名稳定性。缺失输出详情见记录。",
                "Valid localization intervals differ in this group; RMSE covers available outputs only and cannot rank stability. See records for missing outputs.",
            ), ""]
        media(
            folder,
            [
                ("executions/" + key, name)
                for key, name in [("raw", "Raw"), ("dufomap", "DUFOMap"), ("beautymap", "BeautyMap")]
            ],
        )
        blank("scene-" + scene + "-3d")

    heading("practice-appendix", label("补充实验", "Supplementary experiments"), 3)
    heading("supp-srrg", "SRRG · " + label("持久结构变化", "Persistent change"))
    folder = "results/reference/srrg-2d-large-change"
    data = read(folder + "/record.json")["map_quality"]
    lines += [
        table(
            [
                label("方法", "Method"),
                "SA",
                label("新增结构覆盖", "New structure coverage"),
                label("独立B", "Separate B"),
            ],
            [
                [
                    name,
                    pct(data[key]["static_retention"]),
                    pct(data[key].get("new_structure_retention")),
                    label("未测", "Not tested"),
                ]
                for key, name in [("raw", "Raw"), ("srrg", "SRRG")]
            ],
        ),
        ref(folder + "/record.json", label("记录", "Record")),
        "",
    ]
    media(folder, [("execution", "SRRG changed-world A")])
    blank("srrg-large-change-2d")
    heading("map-review-3d", label("保存点云回放", "Saved point-cloud replay"))
    media(
        "results/reference/robot-3d-map-review-v2",
        [("execution", label("已保存结果，无新推理", "Saved results; no new inference"))],
    )
    heading("supp-registrations", "Raw · NDT / GICP")
    rows = []
    for key, name in [
        ("robot-ndt-static-initial", "NDT initial"),
        ("robot-ndt-static", "NDT"),
        ("robot-gicp-static", "GICP"),
    ]:
        folder = "results/reference/" + key
        m = read(folder + "/record.json")["metrics"]["cases"]["ndt" if "ndt" in key else "gicp"]
        rows.append(
            [
                name,
                num(m["position_rmse_m"], 100),
                num(m["yaw_rmse_deg"]),
                ref(folder + "/record.json", label("记录", "Record")),
            ]
        )
    lines += [table([label("方法", "Method"), "XY RMSE / cm", "yaw / °", label("证据", "Evidence")], rows)]
    heading("supp-acquisition", label("补充采集与定位", "Additional acquisition and localization"))
    rows = []
    for key, title in [
        ("static", label("静态", "Static")),
        ("dynamic", label("动态", "Dynamic")),
        ("large-change", label("结构变化", "Changed world")),
    ]:
        folder = "results/reference/robot-supp-" + key
        m = read(folder + "/record.json")["metrics"]
        rows.append(
            [
                title,
                "AMCL" if key == "large-change" else "slam_toolbox",
                str(m["mapping_frames"]) if key != "large-change" else "—",
                ref(folder + "/record.json", label("记录", "Record")),
                ref(folder + "/execution.mp4", "MP4"),
            ]
        )
    lines += [
        table(
            [
                label("场景", "Scene"),
                label("方法", "Method"),
                label("扫描帧数", "Scan frames"),
                label("记录", "Record"),
                label("录制", "Recording"),
            ],
            rows,
        )
    ]
    heading("srrg-diagnostics", label("SRRG失败记录", "SRRG failed runs"))
    rows = []
    for key, title in [
        ("srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d", "Eigen ABI"),
        ("srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3", "stdout"),
        ("srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d", "g2o"),
    ]:
        folder = "results/reference/" + key
        rows.append(
            [
                title,
                read(folder + "/record.json")["status"],
                ref(folder + "/record.json", label("记录", "Record")),
                ref(folder + "/execution.mp4", "MP4"),
            ]
        )
    lines += [
        table(
            [
                label("环节", "Stage"),
                label("状态", "Status"),
                label("记录", "Record"),
                label("录制", "Recording"),
            ],
            rows,
        ),
        "[↑ " + label("目录", "Contents") + "](#practice-index)",
        "",
    ]
    return "\n".join(lines) + "\n"


def publish_document(doc, zh):
    if "<!-- OWN_HYPOTHESES_20261016 -->" in doc.read_text(encoding="utf-8"):
        from own_research_home import publish_document as publish_own_document
        return publish_own_document(doc, zh)
    from publish_home_experiments import sections, apply_home_layout

    text = doc.read_text(encoding="utf-8")
    prefix, blocks = sections(text)
    prefix = re.sub(
        r" · \[(?:Hypothesis test experiment|Hardware experiment|假设检验实验|实机实验)\]\([^)]*\)",
        "",
        prefix,
    )
    names = {
        "hyp": "假设" if zh else "Hypothesis",
        "metrics": "指标" if zh else "Metrics",
        "practice": "实践" if zh else "Practice",
    }
    related_title = "相关工作" if zh else "Related works"
    blocks[related_title] = related(blocks[related_title], doc, zh)
    blocks[names["hyp"]] = hypotheses(zh)
    blocks[names["metrics"]] = metrics(blocks[names["metrics"]], zh)
    blocks[names["practice"]] = practice(doc, zh, blocks[names["practice"]])
    for key in ["Hypothesis test experiment", "假设检验实验", "Hardware experiment", "实机实验"]:
        blocks.pop(key, None)
    result = apply_home_layout(prefix + "".join(blocks.values()), zh)
    doc.write_text(result, encoding="utf-8", newline="\n")


def publish():
    if "<!-- OWN_HYPOTHESES_20261016 -->" in (ROOT / "README.md").read_text(encoding="utf-8"):
        from own_research_home import publish as publish_own
        return publish_own()
    for doc, zh in [(ROOT / "README.md", False), (ROOT / "docs/HOME.zh-CN.md", True)]:
        publish_document(doc, zh)
    for zh, name in [(False, "MAPPING-FOCUS.md"), (True, "MAPPING-FOCUS.zh-CN.md")]:
        home = "../HOME.zh-CN.md" if zh else "../../README.md"
        design = table(
            [
                "实验" if zh else "Experiment",
                "场景" if zh else "Scene",
                "A建图对照" if zh else "A mapping controls",
                "独立B定位" if zh else "Separate B localization",
            ],
            [
                ["H1", "静态＋动态" if zh else "Static + dynamic", "Raw / SRRG", "AMCL"],
                [
                    "H2",
                    "静态场景：静止、慢转、快转、平移"
                    if zh
                    else "Static scene: stationary, slow/fast turns, translation",
                    "FAST-LIO点补偿关 / 开" if zh else "FAST-LIO compensation off / on",
                    "GICP",
                ],
                [
                    "H3",
                    "原长廊 / 加非对称参照" if zh else "Original / landmark corridor",
                    "SRRG（Raw同时保留）" if zh else "SRRG (retain Raw control)",
                    "AMCL",
                ],
            ],
        )
        protocol = hypotheses(zh).replace("](#practice-index)", "](" + home + "#practice-index)")
        protocol += "### " + ("实验设计" if zh else "Experiment design") + "\n\n" + design
        protocol += (
            "每个场景重新采集A/B；同一场景各方法共享输入和参数，仅改变表中的对照因素。原三维Raw／DUFOMap／BeautyMap测试保留。\n\n"
            if zh
            else "Reacquire A/B for each scene; within each scene share inputs and settings and change only the listed control. Existing 3D Raw/DUFOMap/BeautyMap tests are retained.\n\n"
        )
        protocol += "```powershell\n./demo/record-hypotheses.ps1 -Suite results/reference/direction-YYYYMMDD-new\n```\n"
        (ROOT / "docs/testing" / name).write_text(
            protocol,
            encoding="utf-8",
            newline="\n",
        )
    for zh, name in [(False, "MINIMAL.md"), (True, "MINIMAL.zh-CN.md")]:
        home = "HOME.zh-CN.md" if zh else "../README.md"
        rows = [
            [
                "H1",
                f"[{'动态清图：静态、动态A/B' if zh else 'Dynamic cleaning: static/dynamic A/B'}]({home}#experiment-h1)",
            ],
            [
                "H2",
                f"[{'FAST-LIO：运动阶段、建图A、定位B' if zh else 'FAST-LIO: motion phases, mapping A, localization B'}]({home}#experiment-h2)",
            ],
            [
                "H3",
                f"[{'长廊：原场景、加参照场景A/B' if zh else 'Corridor: original/landmark A/B'}]({home}#experiment-h3)",
            ],
            ["3D", f"[{'原三维测试' if zh else 'Existing 3D tests'}]({home}#baseline-3d)"],
            [
                "+",
                f"[{'补充实验及下属实验' if zh else 'Supplementary experiments and subexperiments'}]({home}#practice-appendix)",
            ],
        ]
        body = f"[{'完整实验目录' if zh else 'Full experiment contents'}]({home}#practice-index) · [MP4](../demo/gallery.html)\n\n"
        body += table(["实验" if zh else "Experiment", "入口" if zh else "Go"], rows)
        (ROOT / "docs" / name).write_text(body.rstrip() + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    publish()
