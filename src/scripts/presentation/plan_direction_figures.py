"""Describe editable direction figures for the Scientific Illustrator COM drawer.

Only writes a native-object plan; it never rasterizes diagram text or topology.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/assets/direction/v3"
C = {
    "ink": "#172B42",
    "muted": "#52667B",
    "blue": "#206493",
    "pale": "#EFF5FA",
    "teal": "#137C76",
    "green": "#EAF6F2",
    "amber": "#9B5D18",
    "sand": "#FBF4E8",
    "line": "#D4E0E8",
    "slot": "#F5F7F9",
    "white": "#FFFFFF",
}


def text(name, value, x, y, w, h, size=15, color="ink", bold=False, **kw):
    result = dict(
        type="add_textbox",
        name=name,
        text=value,
        left=x,
        top=y,
        width=w,
        height=h,
        font_size=size,
        font_name="Microsoft YaHei",
        font_color=C.get(color, color),
        bold=bold,
        margin_left=0,
        margin_right=0,
        margin_top=0,
        margin_bottom=0,
        text_autofit="none",
        word_wrap=True,
    )
    result.update(kw)
    return result


def box(name, x, y, w, h, fill="pale", stroke="line", **kw):
    return text(name, "", x, y, w, h, fill_color=C[fill], line_color=C[stroke], line_width=1, **kw)


def conn(name, source, target, src=4, dst=2, color="blue", arrow=True, **kw):
    return dict(
        type="add_connector",
        name=name,
        source_name=source,
        target_name=target,
        source_site=src,
        target_site=dst,
        connector_type="straight",
        line_color=C[color],
        line_width=1.8,
        end_arrow="triangle" if arrow else "none",
        **kw,
    )


def workflow(zh):
    title = "SLAM 的整体流程" if zh else "The SLAM workflow"
    sub = (
        "观测 → 前端约束 → 后端优化 → 地图更新；地图继续约束下一帧定位"
        if zh
        else "Observations → front-end constraints → optimization → map update → next-frame tracking"
    )
    head = (
        ["传感器观测", "预处理", "前端：跟踪与关联", "后端：联合估计", "地图融合与更新"]
        if zh
        else ["Sensor input", "Preprocessing", "Front end", "Back end", "Map update"]
    )
    body = (
        [
            "LiDAR / 相机 / 深度\nIMU / 轮速等运动信息\n按系统配置选择",
            "时间同步与外参\n去畸变 / 有效值检查\n特征及可靠性筛选",
            "帧间 / 帧地图匹配\n运动初值与相对约束\n关键帧选择",
            "融合观测与运动约束\n优化位姿 / 偏置等\n可含地图变量",
            "用估计位姿融合观测\n静态结构与变化管理\n局部 / 全局地图",
        ]
        if zh
        else [
            "LiDAR / vision / depth\nIMU / wheel motion\nAs configured",
            "Time / extrinsics\nDeskew / validity\nFeatures / reliability",
            "Frame / map matching\nRelative motion factors\nKeyframes",
            "Fuse sensor factors\nPose / bias optimization\nMap variables if used",
            "Fuse scans with poses\nStatic / change updates\nLocal / global maps",
        ]
    )
    ops = [
        text("workflow-title", title, 32, 22, 896, 40, 29, bold=True),
        text("workflow-subtitle", sub, 32, 67, 896, 30, 15, "muted"),
    ]
    ops += [
        text(
            "map-feedback-label",
            "地图 / 局部结构为下一帧匹配提供约束"
            if zh
            else "Map / local structure constrains the next match",
            496,
            103,
            408,
            26,
            14,
            "teal",
        )
    ]
    for j, x in enumerate([32, 216, 400, 584, 768]):
        ops += [
            box(f"stage-{j+1}", x, 170, 160, 110),
            text(f"stage-{j+1}-title", head[j], x + 10, 181, 140, 27, 16 if zh else 17, "blue", True),
            text(f"stage-{j+1}-body", body[j], x + 10, 216, 140, 58, 13.3 if zh else 11.7),
        ]
    for j in range(1, 5):
        ops.append(conn(f"forward-{j}", f"stage-{j}", f"stage-{j+1}"))
    # Small native, transparent anchor shapes define an orthogonal feedback lane.
    for name, x, y in [("feedback-map-anchor", 847.5, 139.5), ("feedback-front-anchor", 479.5, 139.5)]:
        ops.append(text(name, "", x, y, 1, 1, fill_transparency=100, line_transparency=100))
    ops += [
        conn("map-feedback-rise", "stage-5", "feedback-map-anchor", 1, 3, "teal", False),
        conn("map-feedback-rail", "feedback-map-anchor", "feedback-front-anchor", 2, 4, "teal", False),
        conn("map-feedback-enter", "feedback-front-anchor", "stage-3", 3, 1, "teal"),
    ]
    ops += [
        text(
            "joint-estimation-note",
            "位姿影响地图，地图影响后续位姿。\n误差会沿这个反馈关系传播。"
            if zh
            else "Pose affects the map.\nThe map affects later pose.\nErrors can propagate between them.",
            32,
            336,
            338,
            62,
            15,
            "muted",
        )
    ]
    for name, x, value in [
        (
            "pose-output",
            400,
            "输出 ① 位姿 / 轨迹\n实时跟踪 + 后端校正"
            if zh
            else "Output 1 · Pose / path\nTracked + optimized",
        ),
        (
            "loop-validation",
            584,
            "回环检测与验证\n历史关键帧\n几何一致性约束"
            if zh
            else "Loop detection\nKeyframe retrieval\nGeometry validation",
        ),
        (
            "map-output",
            768,
            "输出 ② 环境地图\n点云 / 栅格 / 特征等" if zh else "Output 2 · Map\nPoints / grids / features",
        ),
    ]:
        ops += [
            text(
                name,
                value,
                x,
                348,
                160,
                62,
                13.1 if zh else 11.8,
                fill_color=C["green" if name != "loop-validation" else "sand"],
                line_color=C["teal" if name != "loop-validation" else "amber"],
                margin_left=8,
                margin_right=8,
                margin_top=8,
                margin_bottom=8,
            )
        ]
    ops += [
        conn("pose-output-edge", "stage-3", "pose-output", 3, 1),
        conn("validated-loop-factor", "loop-validation", "stage-4", 1, 3, "amber"),
        conn("map-output-edge", "stage-5", "map-output", 3, 1),
    ]
    scope = (
        "本轮实验：给定建图位姿 A → 清理并冻结地图 → 独立扫描 B 定位；该对照用于隔离地图因素。"
        if zh
        else "Current experiment: supplied mapping poses A → clean and freeze map → localize independent scans B."
    )
    ops += [
        box("experiment-scope-bg", 32, 452, 896, 51, "pale", "line"),
        text("experiment-scope", scope, 46, 461, 868, 34, 14, "blue"),
        text(
            "workflow-footnote",
            "通用功能流程；各 SLAM 系统的模块划分和状态变量可不同。"
            if zh
            else "Functional overview; module boundaries and estimated variables vary across SLAM systems.",
            32,
            516,
            896,
            16,
            10.5,
            "muted",
        ),
    ]
    return [dict(id="workflow", operations=ops)]


FACTORS_ZH = [
    (
        "采样与可见性",
        "例：远处细柱 / 大面积遮挡",
        "稀疏、低重叠 → 匹配与建图约束不足",
        "稀疏扫描 / 被遮挡场景",
    ),
    (
        "运动与扫描畸变",
        "例：快速转弯 / 振动 / 轮胎打滑",
        "扫描拉弯或运动先验失真 → 错误对齐",
        "转弯前后扫描 / 墙面",
    ),
    ("时间与空间标定", "例：LiDAR–IMU 时间差 / 外参偏差", "跨传感器错位 → 双墙与位姿偏差", "时间错位 / 双墙"),
    (
        "动态物体与持久变化",
        "例：行人经过 / 停车 / 桌椅搬动",
        "残影、遮挡或地图过期 → 误匹配",
        "动态残影 / 前后地图",
    ),
    (
        "材质与成像条件",
        "例：镜面 / 玻璃 / 深度相机强光",
        "虚假点、穿透或缺测 → 伪结构与空洞",
        "镜面实物 / 异常观测",
    ),
    (
        "几何与外观退化",
        "例：平行长走廊 / 白墙 / 重复门",
        "方向约束弱或易混淆 → 漂移 / 误关联",
        "走廊 / 重复结构",
    ),
    (
        "位姿漂移与错误回环",
        "例：累计偏航 / 相似走廊误闭环",
        "地图错层或拉扯 → 后续定位被误导",
        "轨迹 / 地图错层",
    ),
    (
        "地图表示与实时预算",
        "例：体素过粗 / 过度滤波 / 处理积压",
        "细节丢失、延迟 → 有效约束减少",
        "细节丢失 / 延迟对比",
    ),
]
FACTORS_EN = [
    (
        "Sampling and visibility",
        "E.g. distant poles / heavy occlusion",
        "Sparse, low-overlap support weakens matching.",
        "Sparse scan / occluded scene",
    ),
    (
        "Motion and scan distortion",
        "E.g. fast turns / vibration / wheel slip",
        "Warped scans or a biased motion prior misalign.",
        "Turning scan / warped wall",
    ),
    (
        "Timing and calibration",
        "E.g. LiDAR–IMU time / extrinsic offsets",
        "Cross-sensor misalignment creates double walls.",
        "Time offset / double wall",
    ),
    (
        "Dynamics and lasting change",
        "E.g. walking / parking / moved furniture",
        "Ghosts, occlusion or stale maps mislead matching.",
        "Ghosts / changed scene",
    ),
    (
        "Materials and imaging",
        "E.g. mirrors / glass / depth in strong light",
        "False or missing returns create wrong geometry.",
        "Mirror / anomalous returns",
    ),
    (
        "Geometry and appearance",
        "E.g. parallel corridor / blank or repeated walls",
        "Weak or ambiguous support causes drift / aliasing.",
        "Corridor / repeated structures",
    ),
    (
        "Pose drift and false loops",
        "E.g. yaw drift / similar corridors closed wrongly",
        "Misplaced or warped maps corrupt later tracking.",
        "Trajectory / misaligned map",
    ),
    (
        "Map representation and compute",
        "E.g. coarse voxels / heavy filtering / backlog",
        "Lost detail and stale updates reduce useful support.",
        "Detail loss / processing delay",
    ),
]


def factors(zh):
    regions = [
        dict(
            id="factors-header",
            operations=[
                text(
                    "factors-title",
                    "影响鲁棒定位与 SLAM 的因素和实例"
                    if zh
                    else "Factors and examples affecting robust localization and SLAM",
                    32,
                    19,
                    896,
                    38,
                    26 if zh else 24,
                    bold=True,
                ),
                text(
                    "factors-subtitle",
                    "读法：因素 → 典型实例 → 影响机制；右侧虚线框用于插入实测图。"
                    if zh
                    else "Read each entry as factor → example → mechanism. Dashed slots are reserved for your images.",
                    32,
                    63,
                    896,
                    25,
                    14,
                    "muted",
                ),
            ],
        )
    ]
    rows = FACTORS_ZH if zh else FACTORS_EN
    slots = []
    for row in range(4):
        ops = []
        for col in range(2):
            i = row * 2 + col
            title, example, mechanism, hint = rows[i]
            x, y = 32 + col * 456, 105 + row * 98
            ident = f"F{i+1:02}"
            slot_hint = (
                [
                    "稀疏 / 遮挡",
                    "转弯 / 墙面",
                    "错位 / 双墙",
                    "动态残影",
                    "镜面 / 异常点",
                    "长走廊",
                    "轨迹 / 错层",
                    "细节 / 延迟",
                ][i]
                if zh
                else hint
            )
            # Left is native text; right is one independent user-replaceable field.
            ops += [
                box(f"{ident}-row", x, y, 440, 88, "white", "line"),
                text(
                    f"{ident}-heading",
                    f"{ident}  {title}",
                    x + 10,
                    y + 7,
                    294,
                    23,
                    15 if zh else 13.8,
                    "blue",
                    True,
                ),
                text(f"{ident}-example", example, x + 10, y + 34, 294, 21, 12.8 if zh else 11.4),
                text(f"{ident}-mechanism", mechanism, x + 10, y + 58, 294, 24, 12.1 if zh else 10.7, "muted"),
                text(
                    f"{ident}-image-slot",
                    f"{ident} 配图位\n{slot_hint}" if zh else f"{ident} IMAGE SLOT\n{slot_hint}",
                    x + 314,
                    y + 8,
                    116,
                    72,
                    11.4 if zh else 10,
                    "muted",
                    alignment="center",
                    vertical_alignment="middle",
                    margin_left=5,
                    margin_right=5,
                    margin_top=5,
                    margin_bottom=5,
                    fill_color=C["slot"],
                    line_color=C["line"],
                    line_dash="dash",
                    line_width=1,
                ),
            ]
            slots.append(
                dict(
                    id=ident,
                    slide_index=2 if zh else 4,
                    shape_name=f"{ident}-image-slot",
                    left=x + 314,
                    top=y + 8,
                    width=116,
                    height=72,
                    subject=hint,
                    status="reserved_no_measurement",
                )
            )
        regions.append(dict(id=f"factor-row-{row+1}", operations=ops))
    regions.append(
        dict(
            id="factors-footer",
            operations=[
                text(
                    "factor-caveat",
                    "静态不等于可信；干净不等于约束充分；未观测不等于自由空间。各因素可同时出现。"
                    if zh
                    else "Static ≠ reliable; clean ≠ sufficiently constrained; unobserved ≠ free. Factors can co-occur.",
                    32,
                    502,
                    896,
                    26,
                    13,
                    "teal",
                )
            ],
        )
    )
    return regions, slots


def build():
    slides, slots = [], []
    for language, zh in [("zh-CN", True), ("en", False)]:
        slides.append(
            dict(
                name=f"slam-workflow-{language}",
                language=language,
                regions=workflow(zh),
                output=f"slam-workflow.{language}.png",
            )
        )
        regions, image_slots = factors(zh)
        slides.append(
            dict(
                name=f"robustness-factors-{language}",
                language=language,
                regions=regions,
                output=f"slam-robustness-factors.{language}.png",
            )
        )
        slots.extend(image_slots)
    for idx, slide in enumerate(slides, 1):
        for region in slide["regions"]:
            for op in region["operations"]:
                op["slide_index"] = idx
    plan = dict(
        schema_version=1,
        message="Joint pose-map estimation and eight failure-factor families, with user-insertable evidence slots.",
        application="Microsoft PowerPoint",
        backend="COM",
        canvas_points=[960, 540],
        audience="SLAM research discussion",
        reading_order="left-to-right workflow; row-major factor matrix",
        palette=C,
        typography="Microsoft YaHei; native text 10–29 pt",
        margin_points=32,
        connector_lanes=dict(main_y=225, feedback_y=140, secondary_y=[280, 348]),
        z_order="background, node containers, native labels, connectors; no raster content",
        raster_declarations=[],
        image_slots=slots,
        slides=slides,
        acceptance=dict(
            editability=1.0,
            clipping_safety=1.0,
            geometry_min=0.95,
            connector_clarity_min=0.95,
            deterministic_hard_failures=0,
        ),
        ambiguity="All examples are conceptual. Image slots are empty until user evidence is supplied; they do not report experimental outcomes.",
    )
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "design.json"
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    build()
