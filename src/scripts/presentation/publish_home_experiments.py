"""Organize home-page evidence by algorithm family and experiment, preserving other sections."""

from __future__ import annotations

import json
import os
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = "<!-- HOME_EXPERIMENTS_V2 -->"
SCENES = [
    ("static", "纯静态", "Pure static"),
    ("dynamic", "运动障碍物", "Moving obstacles"),
    ("large-change", "持久结构变化", "Persistent change"),
    ("corridor", "走廊退化", "Corridor degradation"),
]
METHODS = [("raw", "Raw"), ("dufomap", "DUFOMap"), ("beautymap", "BeautyMap")]
PACKAGES = {
    "2d": ["robot-live-static", "robot-2d-dynamic-matched", "robot-live-large-change", "robot-corridor-v2"],
    "3d": ["robot-3d-static", "robot-3d-dynamic", "robot-3d-large-change", "robot-3d-corridor"],
}


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sections(text):
    matches = list(re.finditer(r"^## ([^\n]+)\n", text, re.M))
    starts = []
    for match in matches:
        anchor = re.search(r'(?:<a id="[^"]+"></a>\n\s*)+\Z', text[: match.start()])
        starts.append(anchor.start() if anchor else match.start())
    result = {}
    for i, match in enumerate(matches):
        end = starts[i + 1] if i + 1 < len(matches) else len(text)
        result[match.group(1)] = text[starts[i] : end].rstrip() + "\n\n"
    return text[: starts[0]], result


def pct(value):
    if value is None:
        return "N/A"
    percent = value * 100
    digits = 3 if 99.995 <= percent < 100 else 2
    return f"{percent:.{digits}f}".rstrip("0").rstrip(".") + "%"


def quality(scene, dimension):
    if scene == "dynamic":
        if dimension == "2d":
            return read("results/analysis/map-quality/projected-dynamic.json")["methods"]
        return read("results/reference/robot-3d-map-audit/record.json")["configurations"]["baseline"][
            "metrics"
        ]
    source = "corridor" if scene == "corridor" else "static"
    return read(f"results/analysis/map-quality/{source}.json")[dimension]


def media(doc, relative, label, zh, replay=None, width=230):
    def rel(path):
        return os.path.relpath(ROOT / path, doc.parent).replace("\\", "/")

    def preview(path, caption):
        video = Path(path).with_suffix(".mp4").as_posix()
        assert (ROOT / path).is_file() and (ROOT / video).is_file(), path
        return (
            f'<a href="{rel(video)}"><img src="{rel(path)}" width="{width}" loading="lazy" '
            f'alt="{escape(label + " · " + caption, quote=True)}"></a>'
            f'<br>[{caption}]({rel(video)})'
        )

    result = preview(relative, "现场实录" if zh else "Live execution")
    if replay:
        result += "<br>" + preview(
            replay, "结果回放（无新推理）" if zh else "Saved-result replay (no new inference)"
        )
    return result


def link(doc, path):
    return os.path.relpath(ROOT / path, doc.parent).replace("\\", "/")


def related(doc, zh, previous):
    marker = "<!-- HOME_RELATED_DETAILS -->"
    if marker in previous:
        details = previous.split(marker, 1)[1].split("<!-- /HOME_RELATED_DETAILS -->", 1)[0].strip()
    else:
        details = previous[previous.index("### DUFOMap") :].strip()
        details = re.sub(r"^!\[[^]]*\]\([^\n]+\)\n*", "", details, flags=re.M)
        details = re.sub(
            r"^\*\*(?:Live execution|Measured result replay|现场执行|结果回放)[^\n]*\*\*\n*",
            "",
            details,
            flags=re.M,
        )
    lines = [
        "## " + ("相关工作" if zh else "Related works"),
        "",
        "<!-- HOME_RELATED_TABLE -->",
        (
            "按算法类型排列；GIF可直接查看，点击可播放完整视频。适用方向列保留空白，供后续填写。各行数据协议不同，不跨数据集排名。"
            if zh
            else "Grouped by algorithm family. Click a GIF for the full video. The application-direction column is intentionally blank. Different data protocols prevent cross-row ranking."
        ),
        "",
        "| 方法／算法类型 | 原库复现GIF | 评价指标与本次范围 | 适用方向 |"
        if zh
        else "| Method / algorithm family | Reproduction GIF | Measured metrics and scope | Application direction |",
        "| --- | --- | --- | --- |",
    ]
    definitions = [
        ("dufomap", "DUFOMap", "三维地图清理" if zh else "3D map cleaning", "desktop-live-dufomap"),
        (
            "beautymap",
            "BeautyMap",
            "三维离线地图清理" if zh else "Offline 3D map cleaning",
            "desktop-live-beautymap",
        ),
        (
            "srrg_mapper2d",
            "srrg_mapper2d",
            "原生二维动态建图" if zh else "Native dynamic 2D mapping",
            "srrg-2d-dynamic",
        ),
        (
            "ir-mcl",
            "IR-MCL",
            "二维神经场定位" if zh else "2D neural-field localization",
            "desktop-live-ir-mcl",
        ),
        (
            "adam-mcl",
            "AdaM-MCL",
            "学习提议＋粒子定位" if zh else "Learned proposals + particle localization",
            "desktop-adam-mcl",
        ),
    ]
    for method, title, family, package in definitions:
        record_url = link(doc, f"results/reference/{package}/record.json")
        card = "srrg_mapper2d.zh-CN" if method == "srrg_mapper2d" else method
        name = f'<a id="related-{method}"></a>[{title}]({link(doc,"docs/papers/"+card+".md")})<br>{family}'
        gif = media(
            doc,
            f"results/reference/{package}/execution.gif",
            title,
            zh,
            f"results/reference/{package}/result.gif" if method == "adam-mcl" else None,
        )
        if method in ("dufomap", "beautymap"):
            counts = read(f"results/reference/{package}/metrics.json")["counts"]
            sa = counts["kept_static"] / (counts["kept_static"] + counts["removed_static"])
            da = counts["removed_dynamic"] / (counts["kept_dynamic"] + counts["removed_dynamic"])
            effect = f"SA {pct(sa)} / DA {pct(da)}<br>KITTI-00 · 141 " + (
                "帧；清理有效" if zh else "scans; cleaning demonstrated"
            )
        elif method == "srrg_mapper2d":
            value = read(f"results/reference/{package}/record.json")["map_quality"]["srrg"]
            effect = f"DA {pct(value['dynamic_removal'])} / SA {pct(value['static_retention'])}<br>" + (
                "Gazebo单轮动态场景；已编译作者原库，四场景见Practice；定位B待测"
                if zh
                else "Single Gazebo dynamic run; author code compiled, four scenes in Practice; held-out localization B pending"
            )
        elif method == "ir-mcl":
            value = read(f"results/reference/{package}/metrics.json")
            value = value.get("measured", value)
            effect = (
                f"RMSE {value['location_rmse_cm']:.2f} cm / {value['yaw_rmse_deg']:.2f}°<br>Bonn IPBLab Seq 1"
            )
        else:
            value = read(f"results/reference/{package}/metrics.json")
            effect = f"RMSE {value['position_rmse_cells']:.2f} " + (
                "格；自建128格地图、2432步训练；历史10轮持续收敛0/10，不能比较论文米制精度"
                if zh
                else "cells; authored 128-cell map, 2432 training steps; historical sustained convergence 0/10, no comparison to paper metre-scale accuracy"
            )
        lines.append(f"| {name} | {gif} | {effect}<br>[{'记录' if zh else 'Record'}]({record_url}) |  |")
    lines += [
        "<!-- /HOME_RELATED_TABLE -->",
        "",
        (
            "SA／DA与定位RMSE的定义见[指标](#指标)。SRRG按二维观测支持评分，DUFOMap／BeautyMap按三维点评分；IR-MCL／AdaM-MCL不清理地图。"
            if zh
            else "See [Metrics](#metrics) for SA/DA and pose-RMSE definitions. SRRG scores 2D observed support; DUFOMap/BeautyMap score 3D points. IR-MCL/AdaM-MCL do not clean maps."
        ),
        "",
        "<details>",
        "<summary>"
        + ("各论文的输入、处理流程与复现边界" if zh else "Inputs, processing and reproduction boundaries")
        + "</summary>",
        "",
        marker,
        details,
        "<!-- /HOME_RELATED_DETAILS -->",
        "",
        "</details>",
        "",
    ]
    return "\n".join(lines)


def metric_notes(dimension, zh):
    if zh:
        unit = "5cm动态／静态专属投影格" if dimension == "2d" else "已标注三维动态／静态源点"
        pose = "XY" if dimension == "2d" else "XYZ"
        coordinates = r"(\hat x-x)^2+(\hat y-y)^2" + (r"+(\hat z-z)^2" if dimension == "3d" else "")
        overlap = "；动静重叠投影格排除" if dimension == "2d" else ""
        matching = (
            "投影采用同一高度带和一格占据膨胀，按格是否仍被占据计数。"
            if dimension == "2d"
            else "源点到清理图最近点距离<2×10⁻⁵m判为保留；这是源点成员核对容差，不是几何精度。"
        )
        return (
            f"**计算方法：**DA＝已删除动态样本／动态样本总数×100%；SA＝仍保留静态样本／静态样本总数×100%。本组样本为{unit}{overlap}。无动态分母记N/A。\n\n"
            f"{matching}\n\n"
            f"定位 $\\mathrm{{RMSE}}_{{{pose}}}=100\\sqrt{{\\mathrm{{mean}}[{coordinates}]}}$ cm：原生输出与独立Gazebo真值最近时间差≤0.05仿真秒，包含初始化，不拟合轨迹，不给缺失输出补零。\n\n"
            "**指标含义：**DA越高，动态残留越少；SA越高，静态支持损失越少。RMSE越低，定位平均误差越小；清理率不能代替地图几何误差或定位收益。"
        )
    unit = (
        "unique 5cm dynamic/static-exclusive projection cells"
        if dimension == "2d"
        else "labelled dynamic/static source points in 3D"
    )
    pose = "XY" if dimension == "2d" else "XYZ"
    coordinates = r"(\hat x-x)^2+(\hat y-y)^2" + (r"+(\hat z-z)^2" if dimension == "3d" else "")
    overlap = "; overlapping projected labels are excluded" if dimension == "2d" else ""
    matching = (
        "Projection uses the shared height band and one-cell occupied dilation; score whether each cell remains occupied."
        if dimension == "2d"
        else "A source point is retained when its nearest cleaned-map point is <2×10⁻⁵m away. This checks source membership, not geometric accuracy."
    )
    return (
        f"**Calculation:** DA = removed dynamic samples / all dynamic samples × 100%; SA = retained static samples / all static samples × 100%. Samples here are {unit}{overlap}. No dynamic denominator means N/A.\n\n"
        f"{matching}\n\n"
        f"Pose $\\mathrm{{RMSE}}_{{{pose}}}=100\\sqrt{{\\mathrm{{mean}}[{coordinates}]}}$ cm pairs native updates with independent Gazebo truth within 0.05 simulation seconds. Initialization is included; no trajectory fitting or zero-filling of missing outputs.\n\n"
        "**Meaning:** Higher DA means fewer dynamic remnants; higher SA means less static-support loss. Lower RMSE means lower pose error. Cleaning rates do not replace map-geometry error or establish a localization benefit."
    )


def native_experiment(doc, scene, zh):
    key, title, en = scene
    folder = f"results/reference/srrg-2d-{key}"
    record = read(folder + "/record.json")
    lines = [
        f'<a id="srrg-{key}-2d"></a>',
        "",
        f"#### A{SCENES.index(scene)+1} · {title if zh else en} · 2D",
        "",
        "<!-- HOME_EXPERIMENT_TABLE -->",
        "| 方法 | 同输入建图GIF | 指标效果 |"
        if zh
        else "| Method | Same-input mapping GIF | Metric / effect |",
        "| --- | --- | --- |",
    ]
    for method, label in (("raw", "Raw累计图" if zh else "Raw accumulation"), ("srrg", "srrg_mapper2d")):
        value = record["map_quality"][method]
        gif = (
            media(doc, folder + "/execution.gif", "Raw / SRRG · " + en, zh)
            if method == "raw"
            else f"[{'同段视频：蓝色维护图' if zh else 'Same clip: blue maintained map'}]({link(doc,folder+'/execution.mp4')})"
        )
        effect = f"DA {pct(value['dynamic_removal'])} / SA {pct(value['static_retention'])}"
        if method == "srrg":
            effect += f"<br>{'建图轨迹XY RMSE' if zh else 'Mapping-trajectory XY RMSE'} {record['audit']['mapping_pose_xy_rmse_m']*100:.2f} cm"
        if value.get("new_structure_retention") is not None:
            effect += f"<br>{'新增结构覆盖' if zh else 'Added-structure coverage'} {pct(value['new_structure_retention'])}"
        lines.append(f"| {label} | {gif} | {effect} |")
    lines += [
        "<!-- /HOME_EXPERIMENT_TABLE -->",
        "",
        f"[{'记录与审计' if zh else 'Record and audit'}]({link(doc,folder+'/record.json')})",
        "",
    ]
    lines.append(
        "**计算方法：**先按10cm去重观测支持。DA＝后来被真实射线确认为空、且维护图中已删除的历史动态格／这些历史动态格×100%；SA＝距维护图≤15cm的静态支持格／静态支持格总数×100%。当前动态物体不计入残影分母。建图轨迹XY RMSE按作者跟踪位姿与同步真值计算，单位cm。"
        if zh
        else "**Calculation:** Deduplicate observed support at 10cm. DA = historical dynamic cells later verified free by real rays and removed from the maintained map / all such cells × 100%; SA = static-support cells within 15cm of the map / all static-support cells × 100%. Current moving objects are excluded from the ghost denominator. Mapping-trajectory XY RMSE compares native tracking poses with synchronized truth, in cm."
    )
    lines += [
        "",
        "**指标含义：**DA越高表示历史动态残影更少，SA越高表示静态覆盖保留更多；不是三维点分类率，也不是独立定位B误差。**定位B待测。**"
        if zh
        else "**Meaning:** Higher DA means fewer historical ghosts; higher SA means more static coverage retained. This differs from 3D point classification and from held-out localization-B error. **Localization B is pending.**",
    ]
    if key == "large-change":
        lines += [
            "",
            "加载静态A旧图，在已知起点调用原库多会话更新；本场景只新增结构、未移走旧结构，故DA为N/A。新增结构覆盖＝被维护图覆盖的新增支持格／全部新增支持格，分母91格；衡量观测到的新结构是否保留。"
            if zh
            else "The native multi-session update loads static map A with a known start. This scene adds structures without removing old ones, so DA=N/A. Added-structure coverage is covered new-support cells / all 91 new-support cells; it measures preservation of observed additions.",
        ]
    if key == "corridor":
        lines += [
            "",
            "前50个录制仿真秒仅保留72束／3.5m，之后恢复。**检查点：**11.1s首次跟踪重置（[MP4约4.6s]("
            + link(doc, folder + "/execution.mp4")
            + "#t=4.6)）；11.5s持续位置偏差>20cm；57.6s恢复完整观测。未独立测得地图几何坍塌起点，本次静态覆盖未改善。"
            if zh
            else "The first 50 recording simulation seconds retain 72 rays / 3.5m, then restore observations. **Inspection points:** first tracker reset at 11.1s ([MP4 ≈4.6s]("
            + link(doc, folder + "/execution.mp4")
            + "#t=4.6)); sustained >20cm pose error at 11.5s; full observations at 57.6s. No independent map-collapse onset was measured; static coverage did not improve here.",
        ]
    lines += ["", "[↑ Practice](#practice-index)", ""]
    return "\n".join(lines)


def localization_experiment(doc, scene, dimension, zh):
    key, title, en = scene
    i = SCENES.index(scene)
    package = PACKAGES[dimension][i]
    folder = f"results/reference/{package}"
    record = read(folder + "/record.json")
    metrics = quality(key, dimension)
    audit = (
        "results/analysis/map-quality/projected-dynamic.json"
        if key == "dynamic" and dimension == "2d"
        else "results/reference/robot-3d-map-audit/record.json"
        if key == "dynamic"
        else f"results/analysis/map-quality/{'corridor' if key == 'corridor' else 'static'}.json"
    )
    anchor = "change" if key == "large-change" else key
    group = "B" if dimension == "2d" else "C"
    lines = [
        f'<a id="scene-{anchor}-{dimension}"></a>',
        "",
        f"#### {group}{i+1} · {title if zh else en} · {dimension.upper()}",
        "",
        "<!-- HOME_EXPERIMENT_TABLE -->",
        "| 地图方法／固定定位器 | 复现实录与结果GIF | 指标效果 |"
        if zh
        else "| Map method / fixed localizer | Execution and result GIFs | Metric / effect |",
        "| --- | --- | --- |",
    ]
    for method, label in METHODS:
        case = ("degraded_" if dimension == "2d" and key == "corridor" else "") + method
        gif = folder + f"/executions/{case}.gif"
        replay = folder + f"/methods/{case}/result.gif" if dimension == "2d" else None
        score = (
            record["metrics_3d"][case]["xyz_rmse_m"]
            if dimension == "3d"
            else record["metrics"]["cases"][case]["position_rmse_m"]
        )
        value = metrics[method]
        effect = f"DA {pct(value['dynamic_removal'])} / SA {pct(value['static_retention'])}"
        if key == "large-change":
            effect += "（旧图A）" if zh else " (old map A)"
        effect += f"<br>{'XYZ' if dimension == '3d' else 'XY'} RMSE {score*100:.2f} cm"
        lines.append(
            f"| {label} / {'AMCL' if dimension=='2d' else 'GICP'} | {media(doc,gif,label+' · '+en,zh,replay)} | {effect} |"
        )
    lines += [
        "<!-- /HOME_EXPERIMENT_TABLE -->",
        "",
        f"[{'定位记录' if zh else 'Localization record'}]({link(doc,folder+'/record.json')}) · [{'清理评分' if zh else 'Cleaning audit'}]({link(doc,audit)})",
        "",
        metric_notes(dimension, zh),
        "",
    ]
    if key == "static":
        note = (
            "本场景没有动态污染，DA为N/A；检验清理是否误删静态支持，以及定位是否变化。"
            if zh
            else "No moving contamination is present, so DA=N/A. This control tests static-support loss and changes in localization."
        )
    elif key == "dynamic":
        note = (
            (
                "二维投影会合并高度和时间证据，删除三维点不一定删除二维占据格；本次定位差异不足以建立排名。"
                if dimension == "2d"
                else "三维地图确实删除动态点；但本次GICP误差未见收益，BeautyMap还损失部分静态支持。"
            )
            if zh
            else (
                "Projection merges height/time evidence: deleting 3D points need not clear a 2D occupied cell. These pose differences do not establish a ranking."
                if dimension == "2d"
                else "3D cleaning removes dynamic points, but no GICP gain is established; BeautyMap also loses static support."
            )
        )
    elif key == "large-change":
        note = (
            "本组B始终使用静态A旧图，没有调用在线更新。DA／SA仅评价旧图A，不能解释成变化后地图更新效果。"
            if zh
            else "B uses the frozen static-A map throughout, without online updates. DA/SA describe old map A, not post-change map-update performance."
        )
    elif dimension == "2d":
        note = (
            "三张投影地图相同；66.2s恢复完整观测，约79.5s持续收敛。13.3s表示初始信念偏移的纠正，不能区分清理效果；本组不是在线建图故障测试。"
            if zh
            else "All three projected maps are identical. Full observations return at 66.2s and sustained convergence is around 79.5s; the 13.3s delay corrects initial-belief bias and cannot distinguish cleaning. This is not an online-mapping failure test."
        )
    else:
        note = (
            "Raw／DUFOMap三维地图字节相同，原生输出仍不同；有效覆盖不一致，不能按整段RMSE排名。62.1s恢复观测，最后有效输出Raw／DUFO／Beauty约63.5／76.4／119.3s；固定地图实验没有建图损坏起点。"
            if zh
            else "Raw/DUFOMap 3D maps are byte-identical but native outputs differ. Unequal output coverage prevents whole-run RMSE ranking. Observations return at 62.1s; last valid Raw/DUFO/Beauty outputs are approximately 63.5/76.4/119.3s. Frozen-map localization supplies no map-damage onset."
        )
    lines += [note, "", "[↑ Practice](#practice-index)", ""]
    return "\n".join(lines)


def practice(doc, zh, previous):
    simulation_marker = "<!-- HOME_SIMULATION -->"
    if simulation_marker in previous:
        simulation = previous.split(simulation_marker, 1)[1].split("<!-- /HOME_SIMULATION -->", 1)[0].strip()
        diagnostics = (
            previous.split("<!-- HOME_SRRG_DIAGNOSTICS -->", 1)[1]
            .split("<!-- /HOME_SRRG_DIAGNOSTICS -->", 1)[0]
            .strip()
        )
    else:
        simulation_anchor = "仿真雷达与小车结构参数" if zh else "simulation-sensors-and-chassis"
        simulation = (
            previous.split(f'<a id="{simulation_anchor}"></a>', 1)[1]
            .split("<!-- SRRG_PRACTICE -->", 1)[0]
            .strip()
        )
        simulation = '<a id="simulation-sensors-and-chassis"></a>\n\n' + simulation
        if zh:
            simulation = f'<a id="{simulation_anchor}"></a>\n\n' + simulation
        diagnostics = (
            previous.split('<a id="srrg-diagnostics"></a>', 1)[1]
            .split("<!-- /SRRG_PRACTICE -->", 1)[0]
            .strip()
        )
        diagnostics = '<a id="srrg-diagnostics"></a>\n\n' + diagnostics
    lines = [
        "## " + ("实践" if zh else "Practice"),
        "",
        SCHEMA,
        "",
        '<a id="practice-index"></a>',
        "",
        f"[{'键盘演示' if zh else 'Keyboard demos'}]({link(doc,'demo/README.md')}) · [{'视频目录' if zh else 'Video gallery'}]({link(doc,'demo/gallery.html')}) · [Notebook]({link(doc,'notebooks/presentation/SLAM_实验逐步展示.ipynb')})",
        "",
        "按实验类型分组，同一实验的算法、GIF和指标放在同一张表中。二维与三维分开；单轮结果不建立稳定排名。"
        if zh
        else "Grouped by experiment type; each table keeps its algorithms, GIFs and metrics together. 2D and 3D remain separate; single runs do not establish stable rankings.",
        "",
        "| 场景 | A · 原生二维建图 | B · 二维投影＋AMCL | C · 三维地图＋GICP |"
        if zh
        else "| Scene | A · Native 2D mapping | B · 2D projection + AMCL | C · 3D maps + GICP |",
        "| --- | --- | --- | --- |",
    ]
    for key, title, en in SCENES:
        old = "change" if key == "large-change" else key
        lines.append(
            f"| {title if zh else en} | [SRRG](#srrg-{key}-2d) | [Raw / DUFO / Beauty](#scene-{old}-2d) | [Raw / DUFO / Beauty](#scene-{old}-3d) |"
        )
    lines += [
        "",
        "[仿真设置](#simulation-sensors-and-chassis) · [三维清理图](#map-review-3d) · [早期NDT／GICP](#earlier-raw-map-3d-static-trials) · [补充实践](#supplementary-live-scene-recordings) · [假设实验](#hypothesis-experiments)"
        if zh
        else "[Simulation](#simulation-sensors-and-chassis) · [3D map review](#map-review-3d) · [NDT / GICP](#earlier-raw-map-3d-static-trials) · [Supplementary](#supplementary-live-scene-recordings) · [Hypothesis experiments](#hypothesis-experiments)",
        "",
        simulation_marker,
        simulation,
        "<!-- /HOME_SIMULATION -->",
        "",
        '<a id="srrg-2d"></a>',
        "",
        "### A · 原生二维动态建图" if zh else "### A · Native dynamic 2D mapping",
        "",
        "二维雷达＋轮式里程计，已知起点；使用作者Mapper2D与局部投影融合，不输入真值配准。主组按作者默认关闭图合并。Raw按当时估计累计，SRRG还维护位姿图，属于端到端维护对照。"
        if zh
        else "2D lidar + wheel odometry with a known start; native Mapper2D/local projective merging, with no truth registration. Main runs use the author default with graph merging off. Raw accumulates then-current estimates; SRRG also maintains the pose graph, so this is an end-to-end comparison.",
        "",
    ]
    lines += [native_experiment(doc, scene, zh) for scene in SCENES]
    lines += [
        "<details>",
        "<summary>"
        + ("SRRG失败诊断与实现边界" if zh else "SRRG failure diagnostics and implementation limits")
        + "</summary>",
        "",
        "<!-- HOME_SRRG_DIAGNOSTICS -->",
        diagnostics,
        "<!-- /HOME_SRRG_DIAGNOSTICS -->",
        "",
        "</details>",
        "",
        '<a id="2d--amcl"></a>',
        '<a id="2d-localization-recordings"></a>',
        '<a id="二维定位录制"></a>' if zh else "",
        "",
        "### B · 二维投影地图定位" if zh else "### B · Localization with projected 2D maps",
        "",
        "三种三维地图处理结果使用共用高度带投影成5cm地图，定位器统一为AMCL。DUFOMap／BeautyMap是三维输入方法，这组保留为跨维适配对照。"
        if zh
        else "Three 3D map-processing choices share the height-band projection into 5cm maps, with AMCL fixed as the localizer. DUFOMap/BeautyMap require 3D inputs; this remains a cross-dimensional adaptation control.",
        "",
    ]
    lines += [localization_experiment(doc, scene, "2d", zh) for scene in SCENES]
    lines += [
        '<a id="3d--gicp"></a>',
        '<a id="3d-map-cleaning-and-localization-recordings"></a>',
        '<a id="三维地图清理与定位录制"></a>' if zh else "",
        "",
        "### C · 三维地图定位" if zh else "### C · Localization with 3D maps",
        "",
        "地图A使用提供的建图位姿隔离清理能力；独立定位B用实际三维扫描与同一原生GICP，不读取真值定位。"
        if zh
        else "Mapping A uses supplied poses to isolate cleaning. Independent B uses actual 3D scans and the same native GICP, without truth input to localization.",
        "",
    ]
    lines += [localization_experiment(doc, scene, "3d", zh) for scene in SCENES]
    lines += [
        '<a id="map-review-3d"></a>',
        "",
        "### D · 三维地图清理结果查看" if zh else "### D · 3D map-cleaning result review",
        "",
        "<!-- HOME_EXPERIMENT_TABLE -->",
        "| 对照 | 清理图GIF | 指标效果 |" if zh else "| Comparison | Cleaned-map GIF | Metric / effect |",
        "| --- | --- | --- |",
        "| Raw / DUFOMap / BeautyMap | "
        + media(doc, "results/reference/robot-3d-map-review-v2/execution.gif", "3D map review", zh)
        + " | DA 0 / 46.59 / 74.36%; SA 100 / 99.998 / 81.15% |",
        "<!-- /HOME_EXPERIMENT_TABLE -->",
        "",
        "**计算与含义：**沿用C2动态场景的三维源点DA／SA，分别表示动态删除和静态保留。这里录制已保存清理图，便于人工检查，不新增推理或评分。"
        if zh
        else "**Calculation and meaning:** Reuses C2's 3D source-point DA/SA: dynamic removal and static retention. This records saved map results for inspection, with no additional inference or score.",
        "",
        '<a id="earlier-raw-map-3d-static-trials"></a>',
        '<a id="此前raw单地图三维静态试验"></a>' if zh else "",
        "",
        "### E · 早期Raw三维地图静态定位" if zh else "### E · Earlier Raw-map 3D static trials",
        "",
        "<!-- HOME_EXPERIMENT_TABLE -->",
        "| 定位方法 | 实录／回放GIF | 指标效果 |"
        if zh
        else "| Localizer | Execution / replay GIF | Metric / effect |",
        "| --- | --- | --- |",
    ]
    for method in ("ndt", "gicp"):
        folder = f"results/reference/robot-{method}-static"
        value = read(folder + "/metrics.json")["cases"][method]
        lines.append(
            f"| {'NDT_OMP' if method=='ndt' else 'GICP'} | {media(doc,folder+'/execution.gif',method.upper(),zh,folder+'/result.gif')} | XY RMSE {value['position_rmse_m']*100:.2f} cm; yaw RMSE {value['yaw_rmse_deg']:.2f}°; N={value['samples']}<br>[{'记录' if zh else 'Record'}]({link(doc,folder+'/record.json')}) |"
        )
    lines += [
        "<!-- /HOME_EXPERIMENT_TABLE -->",
        "",
        "**计算与含义：**按B组XY公式计算位置RMSE；偏航差折回[-π,π]后取RMS并转成度。三维输入，但本组历史评分为XY／yaw，不是XYZ。都含初始化；N为有效原生更新数。NDT同参数首轮34.43cm也保留，波动原因未确定。"
        if zh
        else "**Calculation and meaning:** XY RMSE follows group B; yaw differences are wrapped to [-π,π], RMS-averaged and converted to degrees. Input is 3D, but these historical scores are XY/yaw, not XYZ. Initialization is included; N counts native updates. NDT's same-parameter first trial (34.43cm) is retained; its variation remains unexplained.",
        "",
        f"[{'NDT首轮记录' if zh else 'Initial NDT record'}]({link(doc,'results/reference/robot-ndt-static-initial/record.json')})",
        "",
        '<a id="supplementary-live-scene-recordings"></a>',
        '<a id="补充场景实时录制"></a>' if zh else "",
        "",
        "### F · 补充采集与定位实践" if zh else "### F · Supplementary acquisition and localization",
        "",
    ]
    for scene in SCENES[:3]:
        key, title, en = scene
        folder = f"results/reference/robot-supp-{key}"
        record = read(folder + "/record.json")
        mapping = key != "large-change"
        if mapping:
            values = record["metrics"]
            effect = (
                f"{values['mapping_frames']} "
                + ("帧已保存点云；已知栅格" if zh else "saved cloud frames; known cells ")
                + str(values["observed_map"]["known_cells"])
            )
        else:
            value = record["metrics"]["cases"]["raw"]
            effect = f"XY RMSE {value['position_rmse_m']*100:.2f} cm"
        lines += [
            f"#### F{SCENES.index(scene)+1} · {title if zh else en}",
            "",
            "<!-- HOME_EXPERIMENT_TABLE -->",
            "| 方法 | GIF | 指标效果 |" if zh else "| Method | GIF | Metric / effect |",
            "| --- | --- | --- |",
            f"| {'slam_toolbox' if mapping else 'Raw / AMCL'} | {media(doc,folder+'/execution.gif',en,zh)} | {effect} |",
            "<!-- /HOME_EXPERIMENT_TABLE -->",
            "",
            f"[{'记录' if zh else 'Record'}]({link(doc,folder+'/record.json')})",
            "",
            (
                "**计算与含义：**点云帧数为实际保存的扫描数量；已知格数为占据值非未知的栅格数量。它们记录采集量与覆盖，不代表清理准确率或地图几何误差，本组未评分这些精度指标。"
                if zh
                else "**Calculation and meaning:** Cloud-frame count is the number of saved scans; known cells count non-unknown grid entries. These describe acquisition/coverage, not cleaning accuracy or map-geometry error, which were not scored here."
            )
            if mapping
            else (
                "**计算与含义：**按B组XY RMSE公式，用原生AMCL输出与同步真值计算、包含初始化；数值越低表示定位误差越小。本组不测试地图更新。"
                if zh
                else "**Calculation and meaning:** Group B's XY RMSE compares native AMCL updates with synchronized truth, including initialization; lower means smaller pose error. Map updates are not tested."
            ),
            "",
        ]
    return "\n".join(lines)


def refresh_document(doc, zh):
    text = doc.read_text(encoding="utf-8")
    prefix, blocks = sections(text)
    hypothesis = "假设" if zh else "Hypothesis"
    related_title = "相关工作" if zh else "Related works"
    practice_title = "实践" if zh else "Practice"
    progress_start = "<!-- HOME_HYPOTHESIS_PROGRESS -->"
    hyp = re.sub(
        r"<!-- HOME_HYPOTHESIS_PROGRESS -->.*?<!-- /HOME_HYPOTHESIS_PROGRESS -->\n*",
        "",
        blocks[hypothesis],
        flags=re.S,
    )
    progress = (
        "**当前进度：处在M3之后、M4的验证准备阶段。**M1动态残影删除、M2静态保留、M3投影损失已有单轮证据；M4已有定位基线，但尚未完成污染程度递增、重复试验及SRRG独立定位B，定位收益尚未建立。M5二维雷达＋时序深度的建图门控未验证。下方Guard／Depth／Search属于冻结地图的定位探索。"
        if zh
        else "**Current progress: after M3, preparing the controlled M4 validation.** M1 removal, M2 static retention and M3 projection loss have single-run evidence. M4 has localization baselines, but contamination-dose/repeated tests and SRRG's held-out B are pending; no localization gain is established. M5 temporal-depth gating for 2D mapping remains untested. Guard/Depth/Search below are frozen-map localization exploration."
    )
    needle = "## " + hypothesis + "\n"
    hyp = hyp.replace(
        needle, needle + "\n" + progress_start + "\n" + progress + "\n<!-- /HOME_HYPOTHESIS_PROGRESS -->\n", 1
    )
    replacements = {
        hypothesis: hyp,
        related_title: related(doc, zh, blocks[related_title]),
        practice_title: practice(doc, zh, blocks[practice_title]),
    }
    order = [key for key in blocks if key != hypothesis]
    order.insert(order.index(related_title), hypothesis)
    prefix = re.sub(
        r"^.*Minimal English.*$",
        "[English](../README.md) | 中文" if zh else "English | [中文](docs/HOME.zh-CN.md)",
        prefix,
        flags=re.M,
    )
    title_label = "假设" if zh else "Hypothesis"
    target = "假设" if zh else "hypothesis"
    prefix = prefix.replace(f" · [{title_label}](#{target})", "")
    related_link = "[相关工作](#相关工作)" if zh else "[Related works](#related-works)"
    prefix = prefix.replace(related_link, f"[{title_label}](#{target}) · " + related_link)
    result = prefix + "".join(replacements.get(key, blocks[key]).rstrip() + "\n\n" for key in order)
    _, check = sections(result)
    for key in blocks:
        if key not in replacements:
            assert check[key] == blocks[key], f"Unrelated section changed: {key}"
    assert "MINIMAL" not in result
    assert result.index("## " + hypothesis) < result.index("## " + related_title)
    doc.write_text(result.rstrip() + "\n", encoding="utf-8", newline="\n")
    return result


def main():
    for doc, zh in ((ROOT / "README.md", False), (ROOT / "docs/HOME.zh-CN.md", True)):
        refresh_document(doc, zh)
        print("Organized:", doc.relative_to(ROOT))


if __name__ == "__main__":
    main()
