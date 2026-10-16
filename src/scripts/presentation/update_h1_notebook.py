"""Sync shared H1/H2 explanations without changing code, figures or results."""

import hashlib
import json
from pathlib import Path
import shutil

import nbformat
from nbformat.sign import NotebookNotary

from hypothesis_notation import math_sections, pseudocode, raw_baselines, srrg_comparison

ROOT = Path(__file__).resolve().parents[3]
NAME = "新假设_H1-H2_数学原理与可视化.ipynb"


def publish():
    destination = Path("F:/be2演讲/ipynb") / NAME
    original = destination.read_bytes()
    notebook = nbformat.reads(original.decode("utf-8"), as_version=4)
    assert len(notebook.cells) == 9
    # Only explanatory Markdown changes; retain all code, images and actual results.
    preserved = {i: notebook.cells[i].copy() for i in (1, 3, 4, 6, 7)}
    fingerprint = hashlib.sha256(original).hexdigest()[:12]
    backup = ROOT / ".cache/hypothesis-exposition-before" / fingerprint
    backup.mkdir(parents=True, exist_ok=True)
    if not (backup / NAME).exists():
        (backup / NAME).write_bytes(original)

    parts = math_sections(True)
    notebook.cells[0].source = (
        "# 新的 Hypothesis：数学原理与可视化\n\n"
        "[H1 自写对齐与清理](#h1) · [H2 运动补偿](#h2) · [与SRRG思路对比](#hypothesis-srrg-comparison)\n\n"
        "代码默认折叠，图已执行保存；两张图是构造的原理示意。实际验证另列，SRRG部分仅比较思路，不比较指标效果。\n\n"
        + parts["common"] + "\n\n### Raw基线说明\n\n" + raw_baselines(True)
    )
    notebook.cells[2].source = (
        '<a id="h1"></a>\n## H1｜自写对齐与动态清理\n\n' + parts["h1"]
        + '\n\n<a id="hypothesis-srrg-comparison"></a>\n### 创新点与SRRG思路对比\n\n'
        + srrg_comparison(True)
    )
    notebook.cells[5].source = '<a id="h2"></a>\n## H2｜统一点的采样参考时刻\n\n' + parts["h2"]
    notebook.cells[8].source = "### 实验伪代码\n\n```text\n" + pseudocode() + "```"

    for index, before in preserved.items():
        assert notebook.cells[index] == before
    nbformat.validate(notebook)
    assert not any(output.output_type == "error" for cell in notebook.cells
                   if cell.cell_type == "code" for output in cell.outputs)
    nbformat.write(notebook, destination)
    destination.write_bytes(destination.read_bytes().replace(b"\r\n", b"\n"))
    NotebookNotary().sign(notebook)
    target = ROOT / "notebooks/presentation" / NAME
    shutil.copyfile(destination, target)
    print(json.dumps({"notebook": str(destination), "H1_and_H2_math_synced": True,
                      "code_figures_and_results_preserved": True,
                      "F_and_repository_identical": target.read_bytes() == destination.read_bytes()}, ensure_ascii=False))


if __name__ == "__main__":
    publish()
