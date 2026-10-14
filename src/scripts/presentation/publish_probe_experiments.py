"""Publish the complete calibrated matrix with compact bilingual navigation."""
import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.provenance import digest
from slam_learning.runtime.runner import verify_record
from render_probe_gallery import effect, extras, render, render_diagnostics

ROOT = Path(__file__).resolve().parents[3]
SCENES = [("static", "Pure static", "纯静态"), ("dynamic", "Moving obstacles", "运动障碍物"),
          ("large-change", "Persistent change", "持久结构变化"), ("corridor", "Original corridor degradation", "原走廊退化"),
          ("height-corridor", "Height landmarks · derived control", "高处标志 · 派生对照")]
METHODS = [("native", "Raw + native localizer", "Raw＋原生定位器"), ("plain", "Plain ICP", "Plain ICP"),
           ("guard", "H1 · Guard", "H1 · Guard"), ("depth", "H2 · Guard + Depth", "H2 · Guard＋Depth"),
           ("search", "H3 · LiDAR Search", "H3 · 雷达搜索"), ("recover", "H3 · Depth + Search", "H3 · 深度＋搜索")]


def link(document, path):
    return os.path.relpath(path, document.parent).replace("\\", "/")


def metric(record, name):
    if record["hypothesis_probes"]["dimension"] == "3d":
        return record["metrics_3d"][name]["xyz_rmse_m"] * 100
    return record["metrics"]["cases"][name]["position_rmse_m"] * 100


def english_effect(record, name):
    result = f"{'XYZ' if record['hypothesis_probes']['dimension'] == '3d' else 'XY'} RMSE {metric(record, name):.2f} cm"
    parent = {"guard": "plain", "depth": "guard", "search": "guard", "recover": "depth"}.get(name)
    if parent:
        delta = metric(record, name) - metric(record, parent)
        result += f"; close to {parent}" if abs(delta) < .01 else f"; {abs(delta):.2f} cm {'below' if delta < 0 else 'above'} {parent}"
    restored = record.get("restoration", {}).get(name)
    if restored:
        if restored["converged"]:
            result += f"; sustained recovery {restored['sustained_convergence_delay_s']:.1f}s after restoration"
        elif restored["converged"] is None:
            result += "; insufficient post-restore updates"
        else:
            result += "; no sustained recovery"
    return result


def markdown(document, chinese, records, refinements):
    lines = ['<a id="hypothesis-experiment-index"></a>', "",
             "| 场景 | 2D＋深度 | 3D＋深度 |" if chinese else "| Scene | 2D + depth | 3D + depth |", "| --- | --- | --- |"]
    for scene, en, zh in SCENES:
        view = "查看实验" if chinese else "View experiment"
        lines.append(f"| {zh if chinese else en} | [{view}](#probe-calibrated-2d-{scene}) | [{view}](#probe-calibrated-3d-{scene}) |")
    lines.extend(["", "[粗到细补充实验](#probe-refinement-index)" if chinese else "[Coarse-to-fine follow-up](#probe-refinement-index)", "",
                  "[结果解释与后续方向](#hypothesis-findings)" if chinese else "[Interpretation and next directions](#hypothesis-findings)", "",
                  "本轮固定同源Raw图，五个原型严格共享已配对输入。红Plain、黄Guard、橙Depth、紫雷达搜索、绿深度＋搜索、蓝原生AMCL／GICP。二维报XY，三维报XYZ；单轮结果不构成稳定排名。" if chinese else
                  "This matrix fixes the raw source maps and shares identical paired inputs across five prototypes. Red: Plain; yellow: Guard; orange: Depth; purple: lidar search; green: depth + search; blue: native AMCL/GICP. Report XY for 2D and XYZ for 3D; these single trials do not establish a ranking.", ""])
    for dimension in ("2d", "3d"):
        lines.extend([f"### {dimension.upper()} · {'真实窗口实验' if chinese else 'native-window experiments'}", ""])
        for scene, en, zh in SCENES:
            path, record = records[dimension, scene]
            lines.extend([f'<a id="probe-calibrated-{dimension}-{scene}"></a>', "",
                          f"#### {zh if chinese else en} · {dimension.upper()}", "",
                          "[↑ 返回目录](#hypothesis-experiment-index)" if chinese else "[↑ Back to index](#hypothesis-experiment-index)", "",
                          "| 方法 | 地图／观测 | 指标效果 |" if chinese else "| Method | Map / observations | Metric / effect |", "| --- | --- | --- |"])
            for name, label_en, label_zh in METHODS:
                label = label_zh if chinese else label_en
                if name == "native":
                    label = "Raw + " + ("AMCL" if dimension == "2d" else "GICP")
                if chinese:
                    map_type = "二维雷达点图" if dimension == "2d" else "三维雷达点图"
                    if name in ("depth", "recover"):
                        map_type += "＋深度点图"
                    if name == "native" and dimension == "2d":
                        map_type = "同源二维栅格投影图"
                    result = effect(record, name)
                else:
                    map_type = f"{dimension.upper()} lidar point map" + (" + depth map" if name in ("depth", "recover") else "")
                    if name == "native" and dimension == "2d":
                        map_type = "Same-source 2D grid projection"
                    result = english_effect(record, name)
                lines.append(f"| {label} | {map_type} | {result} |")
            frames = json.loads((path.parent / "probe-B-inputs.json").read_text())["frames"]
            used = sum(frame["depth_points"] >= 12 for frame in frames)
            native = record["metrics"]["cases"]["native"]["samples"]
            with (path.parent / "native-samples.csv").open() as stream:
                native_end = float(list(csv.DictReader(stream))[-1]["stamp_s"])
            lines.extend(["", f"五原型各{len(frames)}帧；有效深度{used}/{len(frames)}帧；原生参照{native}次输出。车体高度由建图A标定。" if chinese else
                          f"Each prototype: {len(frames)} frames; usable depth: {used}/{len(frames)}; native anchor: {native} outputs. Body height is calibrated from mapping A.", ""])
            if native_end < frames[-1]["stamp_s"] - 5:
                lines.extend([f"原生参照最后一次有效输出在仿真{native_end:.1f}s，原型记录至{frames[-1]['stamp_s']:.1f}s；无输出时段未填补，其RMSE只覆盖已有输出。" if chinese else
                              f"The native anchor last published at simulation {native_end:.1f}s; prototypes extend to {frames[-1]['stamp_s']:.1f}s. Missing outputs are not filled; native RMSE covers its available outputs only.", ""])
            if scene == "large-change":
                lines.extend(["旧图保持冻结；此处检验不一致观测的处理，没有执行地图更新。" if chinese else "The old map remains frozen; this tests inconsistent-observation handling without map updates.", ""])
            if scene == "height-corridor":
                lines.extend(["此场景额外加入两块高处几何，作为结构互补的可行性对照；与原走廊分别报告。" if chinese else "Two high blocks are added in this feasibility control; report it separately from the original corridor.", ""])
            movie = path.parent / "execution.mp4"
            lines.extend([f"![{zh if chinese else en} · {dimension.upper()} · {'真实窗口' if chinese else 'native windows'}]({link(document, path.parent / 'execution.gif')})", "",
                          f"[MP4]({link(document, movie)}) · [record]({link(document, path)}) · [CSV]({link(document, path.parent / 'recover-samples.csv')})", ""])
    lines.extend(['<a id="probe-refinement-index"></a>', "", "### 补充假设：粗到细搜索与恢复确认" if chinese else "### Follow-up hypothesis: coarse-to-fine search and recovery confirmation", "",
                  "首轮高处对照出现约20cm平台误差。补充试验将候选平移网格从0.4m细化到0.1m，并把更多已检查位置纳入分数差检验；H1／H2、分数门槛和连续确认规则保持一致。使用上方同一B包的雷达、深度、里程计数组重新推理，下面的视频是保存输出的结果回放。" if chinese else
                  "An approximately 20cm plateau in the initial height control motivated a 0.1m refinement of the 0.4m candidate grid and checks against more evaluated alternatives. H1/H2, score thresholds and consecutive confirmation stay fixed. New inference uses exactly the retained B arrays above; these videos replay its saved results.", ""])
    lines.extend(["| 场景 | 2D重算 | 3D重算 |" if chinese else "| Scene | 2D inference | 3D inference |", "| --- | --- | --- |"])
    for scene in ("corridor", "height-corridor"):
        title = next(zh if chinese else en for key, en, zh in SCENES if key == scene)
        lines.append(f"| {title} | [2D](#probe-calibrated-refinement-2d-{scene}) | [3D](#probe-calibrated-refinement-3d-{scene}) |")
    lines.append("")
    for dimension in ("2d", "3d"):
        for scene in ("corridor", "height-corridor"):
            path, record = refinements[dimension, scene]
            title = next(zh if chinese else en for key, en, zh in SCENES if key == scene)
            lines.extend([f'<a id="probe-calibrated-refinement-{dimension}-{scene}"></a>', "", f"#### {dimension.upper()} · {title} · {'同输入细化' if chinese else 'same-input refinement'}", "",
                          "[↑ 返回目录](#hypothesis-experiment-index)" if chinese else "[↑ Back to index](#hypothesis-experiment-index)", "",
                          "| 方法 | 地图／观测 | 指标效果 |" if chinese else "| Method | Map / observations | Metric / effect |", "| --- | --- | --- |"])
            for name, zh, en in (("coarse_lidar", "粗搜索·雷达", "Coarse · lidar"), ("coarse_depth", "粗搜索·深度＋雷达", "Coarse · depth + lidar"),
                                  ("fine_lidar", "细化·雷达", "Fine · lidar"), ("fine_depth", "细化·深度＋雷达", "Fine · depth + lidar")):
                value = record["metrics_3d"][name]["xyz_rmse_m"] if dimension == "3d" else record["metrics"][name]["position_rmse_m"]
                delay = record["initial_sustained_delay_s"][name]
                timing = (f"首次输出后{delay:.1f}s持续收敛" if chinese else f"sustained convergence {delay:.1f}s from first output") if delay is not None else ("未持续收敛" if chinese else "no sustained convergence")
                map_type = ("雷达点图＋深度点图" if chinese else "Lidar + depth point maps") if "depth" in name else ("雷达点图" if chinese else "Lidar point map")
                lines.append(f"| {zh if chinese else en} | {map_type} | {'XYZ' if dimension == '3d' else 'XY'} RMSE {value * 100:.2f} cm；{timing} |")
            lines.extend(["", f"![{title} · {dimension.upper()} · {'离线重算结果回放' if chinese else 'offline-inference result replay'}]({link(document, path.parent / 'result.gif')})", "",
                          f"[{'结果回放MP4' if chinese else 'Result replay MP4'}]({link(document, path.parent / 'result.mp4')}) · [record]({link(document, path)})", ""])
    return "\n".join(lines)


def put_block(path, marker, content):
    text = path.read_text(encoding="utf-8")
    end = marker.replace(" -->", "_END -->")
    before, remainder = text.split(marker, 1)
    after = remainder.split(end, 1)[1] if end in remainder else ""
    path.write_text(before + marker + "\n\n" + content + "\n" + end + after, encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path)
    args = parser.parse_args()
    batch = json.loads(args.batch.read_text(encoding="utf-8-sig"))
    if batch["status"] != "completed" or len(batch["runs"]) != 10:
        raise ValueError("The complete calibrated matrix is required")
    records = {}
    for run in batch["runs"]:
        source = Path(run["path"]) / "evidence"
        record = json.loads((source / "record.json").read_text())
        if "ground_z_m" not in record["hypothesis_probes"]:
            raise ValueError("An uncalibrated diagnostic was supplied as a primary result")
        scene = json.loads((source / "runtime.json").read_text())["scene"]
        dimension = record["hypothesis_probes"]["dimension"]
        target = ROOT / f"results/reference/probe-calibrated-{dimension}-{scene}"
        if target.exists():
            if digest(target / "record.json") != digest(source / "record.json"):
                raise ValueError("Refusing to overwrite a different archived trial")
        else:
            shutil.copytree(source, target)
        if verify_record(target / "record.json"):
            raise ValueError(f"Invalid published native record: {target}")
        records[dimension, scene] = target / "record.json", record
    refinements = {}
    for dimension in ("2d", "3d"):
        for scene in ("corridor", "height-corridor"):
            path = ROOT / f"results/reference/probe-calibrated-refinement-{dimension}-{scene}/record.json"
            if verify_record(path):
                raise ValueError(f"Invalid refinement: {path}")
            refinements[dimension, scene] = path, json.loads(path.read_text())
    for relative, chinese, marker in (("README.md", False, "<!-- PROBE_APPENDIX_RESULTS -->"),
                                     ("docs/HOME.zh-CN.md", True, "<!-- PROBE_APPENDIX_RESULTS -->"),
                                     ("docs/testing/HYPOTHESES.md", False, "<!-- PROBE_RESULTS -->"),
                                     ("docs/testing/HYPOTHESES.zh-CN.md", True, "<!-- PROBE_RESULTS -->")):
        path = ROOT / relative
        put_block(path, marker, markdown(path, chinese, records, refinements))
    render_diagnostics(ROOT / "results/reference", ROOT / "demo/hypotheses-diagnostics.html", "hypotheses.html")
    supplements, mappings = extras(ROOT / "results/reference")
    render(records, ROOT / "demo/hypotheses.html", supplements, mappings)
    slots_path = ROOT / "docs/figures/slots.json"
    slots = json.loads(slots_path.read_text(encoding="utf-8"))
    identifiers = {slot["id"] for slot in slots["slots"]}
    for path in sorted((ROOT / "results/reference").glob("probe-*/record.json")):
        record = json.loads(path.read_text())
        media = "result.gif" if record["kind"] == "offline_hypothesis_refinement" else "execution.gif"
        identifier = path.parent.name
        if identifier not in identifiers and (path.parent / media).is_file():
            slots["slots"].append({"id": identifier, "status": "published", "path": (path.parent / media).relative_to(ROOT).as_posix(),
                                   "caption": {"en": identifier + (": saved-output replay after offline inference" if media == "result.gif" else ": actual native windows"),
                                               "zh": identifier + ("：离线重算后的保存输出回放" if media == "result.gif" else "：真实窗口录制")},
                                   "source_records": [path.relative_to(ROOT).as_posix()]})
    slots_path.write_text(json.dumps(slots, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Published {len(records)} native conditions and {len(refinements)} paired refinement replays")


if __name__ == "__main__":
    main()
