from __future__ import annotations

import json
import os
from pathlib import Path

from .runner import verify_record


def render_report(paths: list[Path], base: Path | None = None, lang: str = "en") -> str:
    if lang not in ("en", "zh"):
        raise ValueError("Report language must be en or zh")
    zh = lang == "zh"
    labels = {"executed": "已执行", "failed": "失败", "blocked": "环境阻塞", "smoke_passed": "冒烟通过",
              "running": "运行中", "full_teaser": "完整 teaser", "smoke": "冒烟",
              "controlled_synthetic_mechanism_test": "探索性合成机制实验",
              "controlled_synthetic_calibration_test": "探索性合成校准实验",
              "real_data_pose_sensitivity": "真实数据位姿敏感性"}
    labels.update(map_evaluator_cross_check="地图评价器对照", author_map_replay="作者地图离线回放",
                  dufomap_api_diagnostic="DUFOMap 接口诊断",
                  semantic_frontend_baseline="语义前端基线",
                  **{"Replica room0 40-observation subset": "Replica room0 40 次观测子集"})
    lines = ["# 实测记录汇总" if zh else "# Measured experiment ledger", "",
             "由原始记录生成。执行完成、论文表格一致和假设验证是不同状态。" if zh
             else "Generated from run records. Execution, paper agreement and hypothesis validation are distinct.", "",
             "| 实验 | 范围 | 执行 | 论文表格 | SA % | DA % | AA % | HA % | 证据 |" if zh
             else "| Experiment | Scope | Execution | Paper table | SA % | DA % | AA % | HA % | Evidence |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    notes = []
    for path in sorted(paths):
        r = json.loads(path.read_text(encoding="utf-8"))
        issues = verify_record(path)
        if issues:
            raise ValueError(f"Invalid evidence {path}: {'; '.join(issues)}")
        comparison = r.get("paper_comparison")
        match = (("一致" if zh else "matched") if comparison and comparison["matched"]
                 else ("有差异" if zh else "mismatch") if comparison
                 else ("未比较" if zh else "not evaluated"))
        metrics = r.get("metrics", {})
        name = r.get("method", labels.get(r["kind"], r["kind"]) if zh else r["kind"].replace("_", " "))
        scope = r.get("scope", r["kind"])
        state = r["status"]
        if zh:
            scope, state = labels.get(scope, scope), labels.get(state, state)
        values = [f"{metrics[k]:.4f}" if k in metrics else "—" for k in ("SA", "DA", "AA", "HA")]
        link = os.path.relpath(path, base).replace("\\", "/") if base else path.as_posix()
        lines.append(f"| {name} | {scope} | {state} | {match} | "
                     + " | ".join(values) + f" | [{path.parent.name}]({link}) |")
        if r.get("error"):
            notes.append(f"- {name} ({path.parent.name}): {r['error']}")
    if notes:
        lines.extend(["", "记录中的失败：" if zh else "Recorded failures:", "", *notes])
    if zh:
        lines += ["", "合成试验使用已知身份、可见性或噪声模型，属于探索性分析，不是完整系统复现或独立假设验证。",
                  "原始数据与大点云仅保留在本机；可发布记录包含其哈希与运行日志。",
                  "`verify --full` 需要本地点云。历史存档分数不参与本表。", ""]
        return "\n".join(lines)
    lines += ["", "Synthetic trials are exploratory mechanism checks with oracle inputs, not independent hypothesis validation.",
              "Large maps and source datasets are local-only; portable records contain their hashes and fresh-run logs.",
              "`verify --full` requires those maps to be present. No historical archive score contributes to this table.", ""]
    return "\n".join(lines)
