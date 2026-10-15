"""Render practice-only bilingual tables with clickable, animated GIF previews."""

import json
import re
import subprocess
from html import escape
from pathlib import Path

from publish_map_quality import NAMES, legacy_minimal

ROOT = Path(__file__).resolve().parents[3]

TRANSLATIONS = {
    "静态A旧图": "static A old map",
    "动态格删除": "Dynamic cell removal",
    "静态格保留": "Static cell retention",
    "动态残影删除": "Dynamic ghost removal",
    "动态点删除": "Dynamic point removal",
    "静态覆盖保留": "Static coverage retained",
    "静态点保留": "Static point retention",
    "动态删除": "Dynamic removal",
    "静态保留": "Static retention",
    "动态删／静态留：": "Dynamic removal / static retention: ",
    "实机传感器录制；清理指标不适用": "Hardware sensor capture; cleaning metrics N/A",
    "早期场景演示；未绑定地图清理评分，保留原片": "Early scene demo; no bound cleaning score; retained",
    "传感器／建图过程演示；未评分": "Sensor/mapping demonstration; unscored",
    "失败诊断：图合并数值崩溃，最后成功仿真66.0s／录制55.4s": "Failure: numerical graph-merge crash; last native sim 66.0s / recording offset 55.4s",
    "联调失败诊断；已修复，保留原片": "Integration failure diagnostic; fixed; retained",
    "定位原型；地图清理指标不适用；": "Pose prototype; map-cleaning metrics N/A; ",
    "旧z=0诊断（保留，不参与排名）；": "Earlier z=0 diagnostic (retained; not ranked); ",
    "定位RMSE（清理指标不适用／未标注）：": "Pose RMSE (cleaning N/A or unlabelled): ",
    "历史10轮定位RMSE均值": "Historical mean pose RMSE over 10 trials: ",
    "格（已勘误）；清理指标不适用": " cells (corrected); cleaning N/A",
    "定位RMSE": "Pose RMSE",
    "格；清理指标不适用": " cells; cleaning N/A",
    "；清理指标不适用": "; cleaning N/A",
    "旧图A静态": "Old-map A static",
    "；B未更新": "; B not updated",
    "未测试": "untested",
    "（": " (",
    "）": ")",
    "；": "; ",
    "／": " / ",
    "：": ": ",
    "、": ", ",
    "，": ", ",
}


def english(text):
    for source, target in TRANSLATIONS.items():
        text = text.replace(source, target)
    return text


GROUPS = [
    ("related-works", "Related works · 原库实践", "Related works · author-code practice"),
    ("srrg-2d", "原生二维建图 · SRRG", "Native 2D mapping · SRRG"),
    ("practice-2d", "二维投影地图＋AMCL", "Projected 2D maps + AMCL"),
    ("practice-3d", "三维地图＋GICP", "3D maps + GICP"),
    ("map-review", "三维地图清理效果", "3D map-cleaning results"),
    ("registration", "NDT／GICP早期实践", "Earlier NDT / GICP practice"),
    ("sensor-practice", "简单传感器实践", "Simple-sensor practice"),
    ("hypotheses-2d", "二维＋深度 · 定位假设实践", "2D + depth · localization prototypes"),
    ("hypotheses-3d", "三维＋深度 · 定位假设实践", "3D + depth · localization prototypes"),
    ("refinement", "同输入候选细化 · 结果回放", "Same-input refinement · result replay"),
    ("hardware", "实机传感器采集", "Hardware sensor captures"),
]
SCENES = {
    "static": ("纯静态", "Pure static"),
    "dynamic": ("运动障碍物", "Moving obstacles"),
    "large-change": ("持久结构变化", "Persistent structural change"),
    "corridor": ("走廊退化", "Corridor degradation"),
    "height-corridor": ("高处几何对照", "Added-height control"),
}


def group_for(path):
    if path.startswith("docs/media/hardware/"):
        return "hardware"
    name = path.split("/")[2]
    if name.startswith("desktop-"):
        return "related-works"
    if name.startswith("srrg-2d-"):
        return "srrg-2d"
    if name in NAMES:
        return "practice-3d" if name.startswith("robot-3d-") else "practice-2d"
    if name == "robot-3d-map-review-v2":
        return "map-review"
    if name in ("robot-ndt-static", "robot-gicp-static"):
        return "registration"
    if name.startswith("robot-supp-"):
        return "sensor-practice"
    if name.startswith("probe-calibrated-refinement-"):
        return "refinement"
    if name.startswith("probe-calibrated-"):
        return "hypotheses-3d" if "-3d-" in name else "hypotheses-2d"
    return "archive"


def render():
    source_rows = {}
    for line in legacy_minimal(write=False):
        parts = [p.strip() for p in line.split("|")[1:-1]]
        path = re.search(r"\]\(\.\./([^)]*)\)", parts[1]).group(1)
        source_rows[path] = (parts[0], parts[2])
    videos = set(subprocess.check_output(["git", "ls-files", "*.mp4"], cwd=ROOT, text=True).splitlines())
    # Match the actual practices displayed in the article, rather than file-name order.
    article = (ROOT / "README.md").read_text(encoding="utf-8")
    primary = list(dict.fromkeys(re.findall(r"!\[[^]]*\]\(([^)]*\.gif)\)", article)))
    primary += [p for p in source_rows if p.startswith("docs/media/hardware/") and p not in primary]
    assert set(primary) <= source_rows.keys()
    slots = json.loads((ROOT / "docs/figures/slots.json").read_text())["slots"]
    captions = {s["path"]: s["caption"] for s in slots if s.get("status") == "published"}
    records = {}
    for path in source_rows:
        if path.startswith("results/reference/"):
            name = path.split("/")[2]
            file = ROOT / "results/reference" / name / "record.json"
            if name not in records:
                records[name] = json.loads(file.read_text()) if file.exists() else {}

    for chinese in (False, True):
        home = "HOME.zh-CN.md" if chinese else "../README.md"
        rows = [
            "| 极简实践 | 跳转 |" if chinese else "| Minimal practice | Jump to |",
            "| --- | --- |",
            "| 语言／主文 | [English](MINIMAL.md) · [中文](MINIMAL.zh-CN.md) · [主README](HOME.zh-CN.md) |"
            if chinese
            else "| Language / main | [English](MINIMAL.md) · [中文](MINIMAL.zh-CN.md) · [Main README](../README.md) |",
            "| 查看 | 表内GIF直接播放；点击预览打开完整视频；DA／SA为动态删除／静态保留，单次不排名 |"
            if chinese
            else "| Viewing | GIFs play in the tables; click a preview for the full video; DA/SA = dynamic removal/static retention; single trials do not establish a ranking |",
        ]
        for anchor, zh, en in GROUPS:
            rows.append(f"| {zh if chinese else en} | [▶ {'查看' if chinese else 'View'}](#{anchor}) |")
        rows.append(
            "| 历史实践与失败诊断 | [展开查看](#archive) |"
            if chinese
            else "| Earlier practice and failures | [Expand](#archive) |"
        )
        used_videos = set()

        def make_row(path):
            gif = Path(path)
            label, effect = source_rows[path]
            if not chinese:
                label = captions.get(path, {}).get(
                    "en", gif.with_suffix("").as_posix().replace("results/reference/", "")
                )
                effect = english(effect)
            choices = [gif.with_suffix(".mp4").as_posix()]
            if gif.stem == "preview":
                choices += [(gif.parent / p).as_posix() for p in ("replay.mp4", "execution.mp4")]
            video = next((p for p in choices if p in videos), None)
            if video:
                used_videos.add(video)
            destination = "../" + (video or path)
            preview = f'<a href="{destination}"><img src="../{path}" width="280" loading="lazy" alt="{escape(label, quote=True)}"></a>'
            preview += f'<br>[{"完整视频" if chinese else "Full video"}]({destination}) · [GIF](../{path})'
            detail = ""
            if path.startswith("results/reference/"):
                name = path.split("/")[2]
                record = records[name]
                record_url = "../results/reference/" + name + "/record.json"
                if (ROOT / "results/reference" / name / "record.json").exists():
                    preview += f' · [{"记录" if chinese else "Record"}]({record_url})'
                method = next((m for m in ("raw", "dufomap", "beautymap") if m in path), None)
                if name in NAMES and method:
                    dimension = "3d" if name.startswith("robot-3d-") else "2d"
                    scene = ("static", "dynamic", "large-change", "corridor")[NAMES.index(name) % 4]
                    label = f'{SCENES[scene][0 if chinese else 1]} · {dimension.upper()} · {dict(raw="Raw",dufomap="DUFOMap",beautymap="BeautyMap")[method]}'
                    replay = "/methods/" in path
                    label += " · " + (
                        ("结果回放" if chinese else "Result replay")
                        if replay
                        else ("实录" if chinese else "Live")
                    )
                    case = ("degraded_" if name == "robot-corridor-v2" else "") + method
                    value = (
                        record["metrics_3d"][case]["xyz_rmse_m"]
                        if dimension == "3d"
                        else record["metrics"]["cases"][case]["position_rmse_m"]
                    )
                    effect += f'<br>{"XYZ" if dimension == "3d" else "XY"} RMSE {value*100:.2f} cm'
                    if name == "robot-3d-corridor":
                        effect += (
                            "；输出覆盖不同，不排名" if chinese else "; unequal output coverage; no ranking"
                        )
                    anchor = "scene-" + ("change" if scene == "large-change" else scene) + "-" + dimension
                    detail = home + "#" + anchor
                elif name.startswith("srrg-2d-") and name.removeprefix("srrg-2d-") in SCENES:
                    detail = home + "#srrg-" + name.removeprefix("srrg-2d-") + "-2d"
                    effect += "；独立定位B待测" if chinese else "; held-out localization B pending"
                elif name.startswith("probe-calibrated-"):
                    detail = home + "#" + name
                elif name in (
                    "desktop-live-dufomap",
                    "desktop-live-beautymap",
                    "desktop-live-ir-mcl",
                    "desktop-adam-mcl",
                ):
                    method_name = name.removeprefix("desktop-live-").removeprefix("desktop-")
                    method_label = {
                        "dufomap": "DUFOMap",
                        "beautymap": "BeautyMap",
                        "ir-mcl": "IR-MCL",
                        "adam-mcl": "AdaM-MCL",
                    }[method_name]
                    label = (
                        method_label
                        + " · "
                        + (
                            ("结果回放" if chinese else "Result replay")
                            if gif.stem == "result"
                            else ("原库实录" if chinese else "Author-code execution")
                        )
                    )
                    detail = home + "#" + method_name
                elif name == "robot-3d-map-review-v2":
                    label = (
                        "Raw／DUFOMap／BeautyMap · 三维清理结果"
                        if chinese
                        else "Raw / DUFOMap / BeautyMap · 3D cleaning results"
                    )
                    effect = (
                        "动态删除：0／46.59／74.36%；静态保留：100／99.998／81.15%；保存结果展示"
                        if chinese
                        else "DA: 0 / 46.59 / 74.36%; SA: 100 / 99.998 / 81.15%; saved-result review"
                    )
                    detail = home + "#map-review-3d"
            if detail:
                label = f"[{label}]({detail})"
            return f'| {label.replace("|", "／")} | {preview} | {effect} |'

        for anchor, zh, en in GROUPS:
            paths = [p for p in primary if group_for(p) == anchor]
            if not paths:
                continue
            rows += [
                "",
                f'<a id="{anchor}"></a>',
                "",
                f'| {zh if chinese else en} | {"GIF预览（点击看视频）" if chinese else "GIF preview (click for video)"} | {"指标效果" if chinese else "Metric / effect"} |',
                "| --- | --- | --- |",
            ]
            rows.extend(make_row(path) for path in paths)
        remaining = [p for p in source_rows if p not in primary]
        rows += [
            "",
            '<a id="archive"></a>',
            "",
            "<details>",
            f'<summary>{"历史实践与失败诊断" if chinese else "Earlier practice and failure diagnostics"} · {len(remaining)} GIF</summary>',
            "",
            "| 实践 | GIF预览（点击看视频） | 指标效果 |"
            if chinese
            else "| Practice | GIF preview (click for video) | Metric / effect |",
            "| --- | --- | --- |",
        ]
        rows.extend(make_row(path) for path in remaining)
        additional = sorted(videos - used_videos)
        if additional:
            rows += [
                "",
                "| 补充实践视频 | 视频 | 说明 |"
                if chinese
                else "| Additional practice videos | Video | Note |",
                "| --- | --- | --- |",
            ]
            for path in additional:
                label = path.removeprefix("results/reference/")
                note = (
                    "同实验补充片段；不新增评分"
                    if chinese
                    else "Additional clip of the same experiment; no additional score"
                )
                rows.append(
                    f'| {label} | [▶ {"完整视频" if chinese else "Full video"}](../{path}) | {note} |'
                )
        rows += ["", "</details>"]
        output = ROOT / "docs" / ("MINIMAL.zh-CN.md" if chinese else "MINIMAL.md")
        output.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        print(
            output.name,
            len(primary),
            "main practice GIFs;",
            len(remaining),
            "archived GIFs;",
            len(videos),
            "MP4s",
        )


if __name__ == "__main__":
    render()
