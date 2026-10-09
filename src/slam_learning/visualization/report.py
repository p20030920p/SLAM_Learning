from __future__ import annotations

import json
import os
from pathlib import Path

from slam_learning.runtime.runner import verify_record

METHODS = {"dufomap": "DUFOMap", "beautymap": "BeautyMap", "conceptgraphs": "ConceptGraphs", "hovsg": "HOV-SG"}


def render_report(paths: list[Path], base: Path | None = None, lang: str = "en") -> str:
    if lang not in ("en", "zh"):
        raise ValueError("Report language must be en or zh")
    zh = lang == "zh"
    selected = {}
    for path in sorted(paths):
        record = json.loads(path.read_text(encoding="utf-8"))
        method = str(record.get("method", "")).lower().replace("-", "")
        if method not in METHODS:
            continue
        issues = verify_record(path)
        if issues:
            raise ValueError(f"Invalid evidence {path}: {'; '.join(issues)}")
        stamp = record.get("started_at", "")
        if method not in selected or stamp > selected[method][0]:
            selected[method] = (stamp, path, record)
    lines = ["# 复现结果" if zh else "# Reproduction Results", "",
             "| 方法 | 数据 | 状态 | 记录 |" if zh else "| Method | Data | Status | Record |",
             "| --- | --- | --- | --- |"]
    states = {"recorded": "已记录", "executed": "已执行", "failed": "失败", "blocked": "环境阻塞",
              "smoke_passed": "冒烟通过", "running": "运行中"}
    for method, name in METHODS.items():
        if method == "hovsg" or method not in selected:
            lines.append(f"| {name} | | {'在复现中' if zh else 'In progress'} | |")
            continue
        _, path, record = selected[method]
        scope = str(record.get("scope", "")).replace("|", "/")
        state = record["status"]
        state = states.get(state, state) if zh else state
        link = os.path.relpath(path, base).replace("\\", "/") if base else path.as_posix()
        lines.append(f"| {name} | {scope} | {state} | [JSON]({link}) |")
    lines += ["", "执行完成不等于论文全量复现。各方法只与自己的原文协议对照。" if zh else
              "Execution is separate from full-paper reproduction. Compare each method with its own paper protocol.", ""]
    return "\n".join(lines)
