"""Publish all native SRRG outcomes with short tables and navigable scenes."""

import html
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[4]
SCENES = [
    ("static", "纯静态", "Pure static"),
    ("dynamic", "运动障碍物", "Moving obstacles"),
    ("large-change", "持久结构变化", "Persistent change"),
    ("corridor", "走廊退化", "Corridor degradation"),
]


def effect(v, zh=True):
    da = "N/A" if v["dynamic_removal"] is None else f"{v['dynamic_removal']*100:.2f}%"
    return (
        f"动态残影删除 {da}；静态覆盖保留 {v['static_retention']*100:.2f}%"
        if zh
        else f"Ghost removal {da}; static coverage {v['static_retention']*100:.2f}%"
    )


def relative(p, doc):
    return os.path.relpath(p, doc.parent).replace("\\", "/")


def markdown(doc, zh, records):
    def link(p):
        return relative(p, doc)

    lines = [
        "<!-- SRRG_PRACTICE -->",
        '<a id="srrg-2d"></a>',
        "",
        "### 原生二维建图 · srrg_mapper2d" if zh else "### Native 2D mapping · srrg_mapper2d",
        "",
        "[↑ 实践目录](#practice-index)" if zh else "[↑ Practice index](#practice-index)",
        "",
        (
            "本组实际使用二维雷达和轮式里程计，无三维雷达、无真值配准。调用作者完整Mapper2D配准与位姿图；主组按作者默认关闭图合并，局部投影融合开启。图合并开启的数值失败单独保留。"
            if zh
            else "Actual 2D lidar and wheel odometry, with no 3D lidar or truth registration. Native author Mapper2D registration and pose graph; the main group uses the author default with graph merging off and local projective merging on. The numerical failure with graph merging on is retained separately."
        ),
        "",
        (
            "指标：10cm唯一观测支持、15cm覆盖容差；只对后来实测射线确认为空的历史动态位置计算删除率，排除当前动态物体。原始图按各帧当时估计累计，SRRG还进行图优化，属于端到端维护对照。百分数不可与三维精确点保留率直接排名。"
            if zh
            else "Metrics use unique 10cm observed support and 15cm coverage tolerance. Ghost removal scores only historical dynamic positions later verified free by actual rays, excluding current objects. Raw accumulation uses each frame’s then-current estimate; SRRG also optimizes the graph. This is an end-to-end comparison, distinct from exact 3D point retention."
        ),
        "",
    ]
    for scene, title, en in SCENES:
        p, r = records[scene]
        lines += [
            f'<a id="srrg-{scene}-2d"></a>',
            "",
            f"#### {title if zh else en} · 2D",
            "",
            "| 方法 | 地图类型 | 指标效果 |" if zh else "| Method | Map type | Metric / effect |",
            "| --- | --- | --- |",
        ]
        for key, label in [("raw", "Raw"), ("srrg", "srrg_mapper2d")]:
            lines.append(
                f"| {label} | {'原生二维点图' if zh else 'Native 2D point map'} | {effect(r['map_quality'][key],zh)} |"
            )
        lines += [
            "",
            f"{'建图轨迹XY RMSE（非固定地图定位B）' if zh else 'Mapping trajectory XY RMSE (not held-out localization B)'}: {r['audit']['mapping_pose_xy_rmse_m']*100:.2f} cm.",
            "",
        ]
        if r.get("multi_session_prior"):
            lines += [
                (
                    "实际加载静态A旧图，已知会话起点，调用作者多会话入口更新。该短路线不能覆盖论文的长期多会话结论。"
                    if zh
                    else "Loads the static-A author map and calls the native multi-session update with a known start. This short route does not reproduce the paper’s long-term evaluation."
                ),
                "",
            ]
            value = r["map_quality"]["srrg"].get("new_structure_retention")
            if value is not None:
                lines += [
                    (
                        f"当前可见新增结构覆盖保留 {value*100:.2f}%（{r['audit']['new_structure_cells']}个观测格）；本场景只增加结构，没有旧结构被搬走，动态删除率为N/A。"
                        if zh
                        else f"Retention of observed added structures: {value*100:.2f}% ({r['audit']['new_structure_cells']} support cells). This scene adds structures without removing old ones; dynamic removal is N/A."
                    ),
                    "",
                ]
        if scene == "corridor":
            lines += [
                (
                    "前50个录制仿真秒限制72束／3.5m；保留720角度格，其余无效，随后恢复。"
                    if zh
                    else "The first 50 recording simulation seconds retain 72 rays within 3.5m in the original 720 angular bins; other bins are invalid, then full observations return."
                ),
                "",
            ]
        events = r["audit"]["events"]
        if events:
            lines += [
                "| 事件 | 仿真秒 | 视频定位（约） |"
                if zh
                else "| Event | Simulation seconds | Video time (approx.) |",
                "| --- | --- | --- |",
            ]
            for event in events:
                labels = {
                    "native_mapper_reset": "建图跟踪重置",
                    "pose_error_warning": "定位偏差持续超过20cm",
                    "map_geometry_warning": "地图几何预警",
                    "observation_change": "观测恢复" if event["criterion"] == "full" else "观测受限",
                }
                at = event.get("approx_mp4_s")
                jump = (
                    f"[{at:.1f}s]({link(p/'execution.mp4')}#t={at:.1f})"
                    if at is not None
                    else f"录制仿真偏移 {event['recording_sim_elapsed_s']:.1f}s"
                )
                lines.append(
                    f"| {labels[event['kind']] if zh else event['kind']} | {event['stamp_s']:.1f} | {jump} |"
                )
            lines += [""]
        else:
            lines += [
                (
                    "本轮未记录作者跟踪器重置或持续20cm定位预警；不能据此保证所有地图几何无误。"
                    if zh
                    else "No native tracker reset or sustained 20cm pose warning was logged; this does not guarantee perfect map geometry."
                ),
                "",
            ]
        lines += [
            f"![SRRG {en} actual native mapping]({link(p/'execution.gif')})",
            "",
            f"[MP4]({link(p/'execution.mp4')}) · [record]({link(p/'record.json')})",
            "",
        ]
    lines += [
        '<a id="srrg-diagnostics"></a>',
        "",
        "#### 保留的失败诊断" if zh else "#### Retained failure diagnostics",
        "",
        "| 视频 | 结果 |" if zh else "| Video | Outcome |",
        "| --- | --- |",
    ]
    for p in sorted((ROOT / "results/reference").glob("srrg-diagnostic-*")):
        name = p.name
        reason = (
            "图合并开启：最后成功输出仿真66.0s／录制55.4s，随后g2o数值分解失败并崩溃；不是动态清理率为零。"
            if "030729" in name
            else "联调失败：Eigen ABI不一致（首次运动）"
            if "025711" in name
            else "联调失败：作者stdout诊断污染传输；已隔离"
        )
        lines.append(
            f"| [GIF]({link(p/'execution.gif')}) · [MP4]({link(p/'execution.mp4')}) · [record]({link(p/'record.json')}) | {reason} |"
        )
    lines += [
        "",
        f"[{'原文数据与适用性' if zh else 'Paper datasets and scope'}]({link(ROOT/'docs/papers/srrg_mapper2d.zh-CN.md')}) · [{'指标与退化时间说明' if zh else 'Metrics and degradation timestamps'}]({link(ROOT/'docs/testing/MAP-METRICS.zh-CN.md')})",
        "<!-- /SRRG_PRACTICE -->",
        "",
    ]
    return "\n".join(lines)


def main():
    records = {
        scene: (
            ROOT / f"results/reference/srrg-2d-{scene}",
            json.loads((ROOT / f"results/reference/srrg-2d-{scene}/record.json").read_text()),
        )
        for scene, _, _ in SCENES
    }
    for doc, zh in [(ROOT / "README.md", False), (ROOT / "docs/HOME.zh-CN.md", True)]:
        text = doc.read_text(encoding="utf-8")
        if "<!-- HOME_EXPERIMENTS_V2 -->" in text:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
            from publish_home_experiments import refresh_document

            refresh_document(doc, zh)
            continue
        if "| srrg_mapper2d |" not in text:
            pos = text.index("\n", text.index("| AdaM-MCL |"))
            text = (
                text[:pos]
                + (
                    "\n| srrg_mapper2d | 原生二维点图（Gazebo） | 动态残影删除42.31% / 静态覆盖保留99.51% |"
                    if zh
                    else "\n| srrg_mapper2d | Native 2D point map (Gazebo) | Ghost removal 42.31% / static coverage 99.51% |"
                )
                + text[pos:]
            )
        text = re.sub(r"<!-- SRRG_PRACTICE -->.*?<!-- /SRRG_PRACTICE -->\n*", "", text, flags=re.S)
        text = text.replace("### 2D · AMCL", markdown(doc, zh, records) + "\n### 2D · AMCL", 1)
        related = (
            "### srrg_mapper2d · 原生二维动态残影维护\n\n"
            if zh
            else "### srrg_mapper2d · native 2D dynamic-map maintenance\n\n"
        )
        related += "[IROS 2018 论文](https://iris.uniroma1.it/handle/11573/1340118) · [作者建图库](https://gitlab.com/srrg-software/srrg_mapper2d) · [ROS入口](https://gitlab.com/srrg-software/srrg_mapper2d_ros) · [merger2d.cpp](https://gitlab.com/srrg-software/srrg_scan_matcher/-/blob/master/src/merger2d.cpp)。\n\n"
        related += (
            "原文针对连续二维点云的长期动态环境建图，使用 LCAS–STRANDS 与 MIT Stata Center；动态处理嵌在多帧配准／合并和图维护中。已编译并完成本机同四场景录制。"
            if zh
            else "The paper evaluates long-term dynamic 2D mapping on LCAS–STRANDS and MIT Stata Center, integrating dynamic handling into scan alignment, merging and graph maintenance. The author libraries have now been compiled and tested in all four local scenes."
        )
        related += (
            "\n\n[2D 实践：视频与指标](#srrg-2d) · [失败诊断](#srrg-diagnostics) · [原文适用条件]("
            + relative(ROOT / "docs/papers/srrg_mapper2d.zh-CN.md", doc)
            + ")\n\n"
        )
        text = re.sub(r"<!-- SRRG_RELATED -->.*?<!-- /SRRG_RELATED -->\n*", "", text, flags=re.S)
        needle = "## " + ("假设" if zh else "Hypothesis") + "\n"
        text = text.replace(
            needle, "<!-- SRRG_RELATED -->\n" + related + "<!-- /SRRG_RELATED -->\n\n" + needle, 1
        )
        for scene, _, _ in SCENES:
            old = "change" if scene == "large-change" else scene
            needle = f"| [查看录像](#scene-{old}-2d)" if zh else f"| [View recordings](#scene-{old}-2d)"
            if needle in text:
                text = text.replace(
                    needle,
                    f"| [SRRG建图](#srrg-{scene}-2d) / [旧投影定位](#scene-{old}-2d)"
                    if zh
                    else f"| [SRRG mapping](#srrg-{scene}-2d) / [Legacy localization](#scene-{old}-2d)",
                    1,
                )
        doc.write_text(text, encoding="utf-8")
    slots = ROOT / "docs/figures/slots.json"
    data = json.loads(slots.read_text())
    data["slots"] = [s for s in data["slots"] if not s["id"].startswith("srrg-")]
    for scene, title, en in SCENES:
        rel = f"results/reference/srrg-2d-{scene}"
        data["slots"].append(
            {
                "id": f"srrg-{scene}-2d",
                "status": "published",
                "path": rel + "/execution.gif",
                "caption": {"zh": title + " · 原生二维SRRG建图", "en": en + " · native SRRG 2D mapping"},
                "source_records": [rel + "/record.json"],
                "source_artifact": "execution.gif",
            }
        )
    slots.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # One compact, self-contained gallery also mirrored to the requested drive.
    rows = [
        '<!doctype html><meta charset="utf-8"><title>SRRG 二维建图</title><style>body{font:18px system-ui;max-width:1100px;margin:30px auto;color:#193b55}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:9px}video{width:100%}a{color:#175bc4}</style>',
        "<h1>原生二维建图 · SRRG</h1><p>动态残影删除／静态覆盖保留；原始图灰色、作者维护图蓝色。旧三维清理图投影结果保留在原目录。</p><table><tr><th>场景</th><th>跳转</th></tr>",
    ]
    for scene, title, _ in SCENES:
        rows.append(f'<tr><td>{title}</td><td><a href="#{scene}">视频与指标</a></td></tr>')
    rows.append("</table>")
    destination = Path(r"F:\be2演讲\本轮成片\mapping-2d")
    destination.mkdir(parents=True, exist_ok=True)
    for scene, title, _ in SCENES:
        folder, r = records[scene]
        rows += [
            f'<h2 id="{scene}">{title} · 2D</h2><table><tr><th>方法</th><th>地图类型</th><th>指标效果</th></tr>'
        ]
        for key, label in [("raw", "Raw"), ("srrg", "srrg_mapper2d")]:
            rows.append(
                f'<tr><td>{label}</td><td>原生二维点图</td><td>{effect(r["map_quality"][key])}</td></tr>'
            )
        rows.append(
            f'</table><p>建图轨迹XY RMSE {r["audit"]["mapping_pose_xy_rmse_m"]*100:.2f}cm；定位B尚未测试。</p>'
        )
        rows.append(
            f'<video controls preload="none" src="../results/reference/srrg-2d-{scene}/execution.mp4"></video>'
        )
        if r["audit"]["events"]:
            rows.append("<table><tr><th>事件</th><th>仿真秒</th><th>视频定位（约）</th></tr>")
            for event in r["audit"]["events"]:
                labels = {
                    "native_mapper_reset": "建图跟踪重置",
                    "pose_error_warning": "持续位置偏差超过20cm",
                    "map_geometry_warning": "地图几何预警",
                    "observation_change": "观测恢复" if event["criterion"] == "full" else "观测受限",
                }
                at = event.get("approx_mp4_s")
                jump = (
                    f'<a href="../results/reference/srrg-2d-{scene}/execution.mp4#t={at:.1f}">{at:.1f}s</a>'
                    if at is not None
                    else "见终端仿真时间"
                )
                rows.append(
                    f'<tr><td>{labels[event["kind"]]}</td><td>{event["stamp_s"]:.1f}</td><td>{jump}</td></tr>'
                )
            rows.append("</table>")
        shutil.copytree(folder, destination / scene, dirs_exist_ok=True)
    rows.append('<h2 id="diagnostics">保留的失败与额外对照</h2>')
    extras = list(sorted((ROOT / "results/reference").glob("srrg-diagnostic-*"))) + [
        ROOT / "results/reference/srrg-2d-static-graph-merge-on"
    ]
    for folder in extras:
        description = (
            "图合并开启：最后成功66.0s后数值崩溃"
            if "030729" in folder.name
            else "静态：图合并开启额外对照"
            if "graph-merge-on" in folder.name
            else "联调失败（已修复，保留原片）"
        )
        rows.append(
            f'<p>{html.escape(description)}</p><video controls preload="none" src="../results/reference/{folder.name}/execution.mp4"></video>'
        )
        shutil.copytree(folder, destination / "diagnostics" / folder.name, dirs_exist_ok=True)
    result = "\n".join(rows)
    (ROOT / "demo/srrg-2d.html").write_text(result, encoding="utf-8")
    for scene, _, _ in SCENES:
        result = result.replace(f"../results/reference/srrg-2d-{scene}/", scene + "/")
    for folder in extras:
        result = result.replace(f"../results/reference/{folder.name}/", "diagnostics/" + folder.name + "/")
    (destination / "index.html").write_text(result, encoding="utf-8")
    for gallery in (ROOT / "demo/gallery.html",):
        text = gallery.read_text(encoding="utf-8")
        if "srrg-2d.html" not in text:
            text = text.replace(
                "<body>", '<body><p><a href="srrg-2d.html">新增：SRRG 原生二维建图（四场景与指标）</a></p>', 1
            )
        gallery.write_text(text, encoding="utf-8")
    native_index = destination.parent / "native-ui/index.html"
    if native_index.exists():
        text = native_index.read_text(encoding="utf-8")
        if "../mapping-2d/index.html" not in text:
            text = text.replace(
                "<body>",
                '<body><p><a href="../mapping-2d/index.html">新增：SRRG原生二维建图、地图指标与失败诊断</a></p>',
                1,
            )
            native_index.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
