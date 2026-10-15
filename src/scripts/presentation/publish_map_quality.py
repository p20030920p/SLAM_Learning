"""Keep compact entry tables and a complete GIF-only index reproducible."""

import json
import re
import subprocess
from pathlib import Path
from map_quality_report import metric_text, quality

ROOT = Path(__file__).resolve().parents[3]
NAMES = [
    "robot-live-static",
    "robot-2d-dynamic-matched",
    "robot-live-large-change",
    "robot-corridor-v2",
    "robot-3d-static",
    "robot-3d-dynamic",
    "robot-3d-large-change",
    "robot-3d-corridor",
]


def replace_tables(path, chinese):
    text = path.read_text(encoding="utf-8")
    heading = "### 2D · AMCL"
    start = text.index(heading)
    end = text.index("## " + ("实测结果如何计算" if chinese else "Measured result calculation"))
    before, section, after = text[:start], text[start:end], text[end:]
    pattern = r"\| (?:方法|Method) \| (?:地图类型|Map type) \| (?:指标效果|Metric / effect) \|\n\| --- \| --- \| --- \|\n(?:\|[^\n]+\|\n){3}"
    found = list(re.finditer(pattern, section))
    assert len(found) == 8, len(found)
    for idx, m in reversed(list(enumerate(found))):
        dimension = "2d" if idx < 4 else "3d"
        name = NAMES[idx]
        lines = m.group().splitlines()
        rows = []
        pose = []
        for method, line in zip(("raw", "dufomap", "beautymap"), lines[2:]):
            parts = line.split("|")
            label, kind, effect = [v.strip() for v in parts[1:4]]
            # Re-running must preserve the independently reported pose values.
            source = json.loads((ROOT / f"results/reference/{name}/record.json").read_text())
            case = ("degraded_" if idx == 3 else "") + method
            value = (
                source["metrics_3d"][case]["xyz_rmse_m"]
                if dimension == "3d"
                else source["metrics"]["cases"][case]["position_rmse_m"]
            )
            pose.append(f"{label} {value*100:.2f}")
            rows.append(f"| {label} | {kind} | {metric_text(name,dimension,method,chinese)} |")
        result = "\n".join(lines[:2] + rows) + "\n"
        result += (
            "\n"
            + ("定位另列" if chinese else "Localization separately")
            + f" ({'XY' if dimension=='2d' else 'XYZ'} RMSE, cm): "
            + " / ".join(pose)
            + ".\n"
        )
        # Avoid duplicate separately-reported values on repeat publication.
        tail = section[m.end() :]
        tail = re.sub(r"^\n(?:定位另列|Localization separately)[^\n]+\n", "", tail, count=1)
        section = section[: m.start()] + result + tail
    text = before + section + after
    if chinese:
        text = text.replace("### 2D · AMCL", "### 2D · 原有三维清理图投影＋AMCL") if False else text
    note = (
        "**地图清理主指标：动态障碍物删除率、静态障碍物保留率，越高越好。** 旧二维投影按5cm唯一格评分；新SRRG按10cm观测支持、15cm覆盖容差评分；三维评分源点。口径不同不排名。静态／走廊无动态样本，删除率记N/A；持久变化旧图仅评分静态A，未测试B在线更新。定位RMSE另列，不能代替地图清理效果。原二维DUFOMap／BeautyMap投影保留为跨维参考；新增原生二维SRRG见下方。\n\n"
        if chinese
        else "**Map-cleaning metrics: dynamic removal and static retention; higher is better.** Legacy projections score unique 5cm cells; native SRRG uses 10cm support and 15cm coverage tolerance; 3D scores source points. These definitions differ. N/A means no dynamic samples. Persistent-change old maps score static A only; no B update was tested. Pose RMSE is reported separately. Legacy DUFOMap/BeautyMap projections remain as cross-dimensional references; native 2D SRRG is added below.\n\n"
    )
    intro_start = text.index("**" + ("地图清理主指标" if chinese else "Map-cleaning metrics:"))
    intro_end = text.index("### 2D · AMCL", intro_start)
    text = text[:intro_start] + note + text[intro_end:]
    # Each video group gets the same primary map-quality table before its clips.
    for idx, (scene, dimension) in enumerate(
        (s, d) for d in ("2d", "3d") for s in ("static", "dynamic", "change", "corridor")
    ):
        anchor = f'<a id="scene-{scene}-{dimension}"></a>'
        loc = text.index(anchor)
        nextloc = text.find("\n<a id=", loc + len(anchor))
        nextloc = nextloc if nextloc >= 0 else len(text)
        group = text[loc:nextloc]
        marker = "<!-- MAP_QUALITY_VIDEO_TABLE -->"
        if marker in group:
            group = re.sub(
                r"<!-- MAP_QUALITY_VIDEO_TABLE -->.*?<!-- /MAP_QUALITY_VIDEO_TABLE -->\n\n",
                "",
                group,
                flags=re.S,
            )
        head = "| 方法 | 地图类型 | 指标效果 |" if chinese else "| Method | Map type | Metric / effect |"
        table = [marker, head, "| --- | --- | --- |"]
        for method, label in [("raw", "Raw"), ("dufomap", "DUFOMap"), ("beautymap", "BeautyMap")]:
            table.append(
                f"| {label} | {dimension.upper()} | {metric_text(NAMES[idx],dimension,method,chinese)} |"
            )
        table.extend(["<!-- /MAP_QUALITY_VIDEO_TABLE -->", ""])
        # After heading/backlink, immediately before the first video paragraph.
        pos = group.find("\n\n", group.find("### ")) + 2
        group = group[:pos] + "\n".join(table) + "\n" + group[pos:]
        text = text[:loc] + group + text[nextloc:]
    minimal = "MINIMAL.zh-CN.md" if chinese else "docs/MINIMAL.zh-CN.md"
    if f"]({minimal})" not in text:
        needle = "## " + ("实践" if chinese else "Practice") + "\n"
        text = text.replace(needle, needle + f"\n[极简：全部 GIF 与指标]({minimal})\n", 1)
    path.write_text(text, encoding="utf-8")


def legacy_minimal():
    out = ROOT / "docs/MINIMAL.zh-CN.md"
    slots = json.loads((ROOT / "docs/figures/slots.json").read_text())["slots"]
    captions = {s["path"]: s["caption"].get("zh", s["id"]) for s in slots if s.get("status") == "published"}
    rows = ["| 内容／地图类型 | GIF（全部保留） | 指标效果 |", "| --- | --- | --- |"]
    tracked = [
        ROOT / name
        for name in subprocess.check_output(["git", "ls-files", "*.gif"], cwd=ROOT, text=True).splitlines()
    ]
    for gif in sorted(set((ROOT / "results/reference").rglob("*.gif")) | set(tracked)):
        rel = gif.relative_to(ROOT).as_posix()
        if not gif.is_relative_to(ROOT / "results/reference"):
            label = captions.get(rel, rel)
            effect = (
                "实机传感器录制；清理指标不适用"
                if rel.startswith("docs/media/hardware/")
                else "早期场景演示；未绑定地图清理评分，保留原片"
            )
            rows.append(f"| {label} | [GIF](../{rel}) | {effect} |")
            continue
        name = gif.relative_to(ROOT / "results/reference").parts[0]
        record_path = ROOT / "results/reference" / name / "record.json"
        record = json.loads(record_path.read_text()) if record_path.exists() else {}
        label = captions.get(
            rel, name + " / " + gif.relative_to(ROOT / "results/reference" / name).as_posix()
        )
        effect = "传感器／建图过程演示；未评分"
        method = next((c for c in ("beautymap", "dufomap", "raw") if c in gif.as_posix().lower()), None)
        if name in NAMES:
            dim = "3d" if name.startswith("robot-3d-") else "2d"
            if method:
                effect = metric_text(name, dim, method)
            else:
                metrics = quality(name, dim)
                parts = []
                for key, label_name in [("raw", "Raw"), ("dufomap", "DUFO"), ("beautymap", "Beauty")]:
                    v = metrics[key]
                    da = "N/A" if v["dynamic_removal"] is None else f"{v['dynamic_removal']*100:.2f}%"
                    parts.append(f"{label_name} {da}/{v['static_retention']*100:.2f}%")
                effect = "动态删／静态留：" + "；".join(parts)
        elif record.get("kind") == "srrg_native_2d_mapping":
            ms = record["map_quality"]["srrg"]
            da = ms["dynamic_removal"]
            effect = f"动态残影删除 {'N/A' if da is None else f'{da*100:.2f}%'}；静态覆盖保留 {ms['static_retention']*100:.2f}%"
        elif record.get("kind") == "srrg_native_2d_mapping_diagnostic":
            effect = (
                "失败诊断：图合并数值崩溃，最后成功仿真66.0s／录制55.4s"
                if "030729" in name
                else "联调失败诊断；已修复，保留原片"
            )
        elif record.get("hypothesis_probes"):
            effect = "定位原型；地图清理指标不适用；"
            data = record.get("metrics_3d") or record.get("metrics", {}).get("cases", {})
            effect += " / ".join(
                f"{k} {(v.get('xyz_rmse_m',v.get('position_rmse_m',0)))*100:.2f}cm"
                for k, v in data.items()
                if "xyz_rmse_m" in v or "position_rmse_m" in v
            )
            if "probe-live-" in name:
                effect = "旧z=0诊断（保留，不参与排名）；" + effect
        elif name in ("desktop-live-dufomap", "desktop-live-beautymap", "dufomap", "beautymap"):
            metrics_path = ROOT / "results/reference" / name / "metrics.json"
            if not metrics_path.exists():
                metrics_path = ROOT / "results/reference" / name / "runs" / f"{name}-wsl" / "metrics.json"
            metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}
            c = metrics.get("counts", {})
            if c:
                effect = f"动态点删除 {100*c['removed_dynamic']/(c['kept_dynamic']+c['removed_dynamic']):.2f}%；静态点保留 {100*c['kept_static']/(c['kept_static']+c['removed_static']):.2f}%"
        elif name == "adam-mcl":
            value = json.loads((ROOT / "results/reference/adam-mcl/score-erratum.json").read_text())[
                "position_rmse_cells_mean"
            ]
            effect = f"历史10轮定位RMSE均值{value:.2f}格（已勘误）；清理指标不适用"
        elif name in ("ir-mcl", "desktop-live-ir-mcl"):
            p = (
                ROOT
                / "results/reference"
                / name
                / ("runs/ir-mcl-wsl/metrics.json" if name == "ir-mcl" else "metrics.json")
            )
            data = json.loads(p.read_text())
            data = data.get("measured", data)
            effect = (
                f"定位RMSE {data['location_rmse_cm']:.2f}cm / {data['yaw_rmse_deg']:.2f}°；清理指标不适用"
            )
        elif name == "desktop-adam-mcl":
            data = json.loads((ROOT / "results/reference" / name / "metrics.json").read_text())
            effect = f"定位RMSE {data['position_rmse_cells']:.2f}格；清理指标不适用"
        elif record.get("metrics", {}).get("cases"):
            effect = "定位RMSE（清理指标不适用／未标注）：" + " / ".join(
                f"{k} {v['position_rmse_m']*100:.2f}cm"
                for k, v in record["metrics"]["cases"].items()
                if "position_rmse_m" in v
            )
        link = "../" + rel
        rows.append(f'| {label.replace("|","／")} | [GIF]({link}) | {effect} |')
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("Minimal GIF rows:", len(rows) - 2)


if __name__ == "__main__":
    import sys

    if "--minimal-only" not in sys.argv:
        replace_tables(ROOT / "README.md", False)
        replace_tables(ROOT / "docs/HOME.zh-CN.md", True)
    from publish_minimal import render

    render()
