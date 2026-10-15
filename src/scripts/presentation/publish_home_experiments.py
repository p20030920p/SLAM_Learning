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


def apply_home_layout(text, zh):
    """Keep physical-test evidence before the question without replacing its content."""
    prefix, blocks = sections(text)
    direction = "方向分析" if zh else "Direction analysis"
    question = "开放问题" if zh else "Open question"
    physical = "Problem getting from Physical test"
    cluster = [direction, physical, question]
    keys = list(blocks)
    position = min(keys.index(key) for key in cluster if key in blocks)
    blocks.setdefault(physical, "## " + physical + "\n\n")
    order = [key for key in keys if key not in cluster]
    order[position:position] = cluster
    navigation = (
        "[方向分析](#方向分析) · [实物测试问题](#problem-getting-from-physical-test) · "
        "[开放问题](#开放问题) · [假设](#假设) · [相关工作](#相关工作) · [指标](#指标)"
        if zh
        else "[Direction](#direction-analysis) · "
        "[Physical test problems](#problem-getting-from-physical-test) · "
        "[Open question](#open-question) · [Hypothesis](#hypothesis) · "
        "[Related works](#related-works) · [Metrics](#metrics)"
    )
    prefix = re.sub(
        r"^\[(?:Open question|Direction|开放问题|方向分析)\][^\n]*$",
        lambda _: navigation, prefix, count=1, flags=re.M,
    )
    return prefix + "".join(blocks[key].rstrip() + "\n\n" for key in order).rstrip() + "\n"


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


def practice(doc, zh, previous):
    from compact_practice import render_practice

    return render_practice(
        doc, zh, previous, root=ROOT, scenes=SCENES, packages=PACKAGES,
        read=read, quality=quality, media=media, link=link, pct=pct,
    )


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
        "**当前进度：M1已有联合删除／保留的单轮观察，M4与M5的受控检验待做。** 原M1／M2已合并；M3移出科学假设，保留投影评分诊断。现有定位基线未建立清图收益，也没有验证污染条件或几何保留策略的作用；SRRG独立定位B待测。下方Guard／Depth／Search是历史冻结地图定位探索。"
        if zh
        else "**Current progress: M1 has single-run joint removal/retention observations; controlled M4/M5 tests are pending.** Former M1/M2 are combined, and M3 is retained only as a projection/scoring diagnostic. Existing localization baselines establish neither cleaning gains nor the effects of contamination conditions or geometry-preserving retention; SRRG's separate B remains pending. Guard/Depth/Search below is historical frozen-map pose exploration."
    )
    from current_hypothesis_practice import SUITE, fold_history

    has_current_batch = (ROOT / SUITE / "summary.json").is_file()
    if has_current_batch:
        progress = (
            "**新一轮已完成静态、动态、长廊的A建图→清图→独立B定位。** [实践数值与新录像](#current-map-hypotheses)同时报告地图表面误差、已观测静态覆盖和定位误差／输出覆盖。每场景1轮；M4污染剂量关系、M5匹配预算的几何保护消融及SRRG独立B仍待测。下方Guard／Depth／Search折叠为历史定位探索。"
            if zh else
            "**New A→map cleaning→held-out B runs are complete for static, dynamic and corridor scenes.** [Practice scores and new recordings](#current-map-hypotheses) report map surface error, observed-static coverage, pose error and output coverage. One run per scene; M4 pollution dose response, M5 budget-matched geometry selection and SRRG's separate B remain pending. Guard/Depth/Search is folded as historical localization exploration."
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
    if has_current_batch:
        old_title = "假设检验实验" if zh else "Hypothesis test experiment"
        replacements[old_title] = fold_history(blocks[old_title], zh)
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
    result = apply_home_layout(result, zh)
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
