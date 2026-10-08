"""Create bilingual exploratory analyses and plots only from a complete recalculated suite."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from slam_learning.identity_budget import ARMS, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads((args.analysis / "readouts.json").read_text())
    decision = json.loads((args.analysis / "decision.json").read_text())
    inputs = json.loads((args.analysis / "inputs.json").read_text())
    if len(rows) != 1008 or inputs["mapping_cells"] != 28 or decision["H1_validated"] is not False:
        raise ValueError("Complete recomputed 28-cell suite required; H1 must remain unverified")
    args.output.mkdir(parents=True, exist_ok=False)
    primary = [r for r in rows if r["observation"] == 8 and r["rms_m"] > 0]
    caps, colors = [25, 50, 100, None], ["#007c91", "#d58219", "#5e8d34", "#8857a5"]
    for endpoint, label in (("mean_coverage", "Partial-surface coverage"), ("instance_recovery", "Instance recovery"),
                            ("category_query_hit", "Annotated category-query hit"),
                            ("actual_candidates", "Actual candidate count"), ("actual_points", "Actual point count")):
        fig, axes = plt.subplots(3, 2, figsize=(10, 8), sharex=True, constrained_layout=True)
        for row_index, support in enumerate([1, 2, 3]):
            for column, rms in enumerate([.10, .30]):
                ax = axes[row_index, column]
                for arm, color in zip(ARMS, colors):
                    values = [[r[endpoint] for r in primary if r["arm"] == arm and r["rms_m"] == rms
                               and r["min_support"] == support and r["candidate_cap"] == cap] for cap in caps]
                    if any(len(v) != 3 for v in values):
                        raise ValueError("Missing paired seed readouts")
                    array = np.array(values)
                    ax.plot(range(4), array.mean(axis=1), "o-", color=color, label=arm, linewidth=1.6, markersize=4)
                    ax.fill_between(range(4), array.min(axis=1), array.max(axis=1), color=color, alpha=.12)
                ax.set_title(f"{rms * 100:.0f}cm RMS; support >= {support}", fontsize=10)
                ax.grid(alpha=.2)
                ax.set_xticks(range(4), ["25", "50", "100", "All"])
                if endpoint in ("mean_coverage", "instance_recovery", "category_query_hit"):
                    ax.set_ylim(0, 1.02)
                if row_index == 2:
                    ax.set_xlabel("Candidate upper limit")
                if column == 0:
                    ax.set_ylabel(label)
        axes[0, 0].legend(fontsize=7, loc="best")
        fig.suptitle(f"room2 AI-only exploratory | immediately after correction\n{label}; mean and min-max of 3 seeds", fontsize=12)
        fig.savefig(args.output / f"{endpoint}.png", dpi=180)
        plt.close(fig)
    summary = []
    for rms in [.10, .30]:
        for arm in ARMS:
            subset = [r for r in primary if r["rms_m"] == rms and r["arm"] == arm and
                      r["min_support"] == 3 and r["candidate_cap"] == 25]
            summary.append({"arm": arm, "rms_cm": int(rms * 100), **{k: float(np.mean([r[k] for r in subset]))
                for k in ("instance_recovery", "category_query_hit", "actual_candidates", "actual_points",
                          "correction_compute_seconds", "annotated_duplicate_excess", "annotated_mixed_objects")}})
    for language in ("en", "zh-CN"):
        chinese = language == "zh-CN"
        title = "room2 对象身份与候选预算：探索结果" if chinese else "room2 identity and candidate budgets: exploratory results"
        warning = ("AI-only 标注，未人工复核；仅探索筛查。H1 未验证。主评价为第 8 次修正后，第 12／16 次仅用于持续性分析。"
                   if chinese else "AI-only labels without human review; exploratory screening only. H1 is unverified. Observation8 is primary; observations12/16 are persistence analyses.")
        lines = [f"# {title}", "", warning, "", f"Decision / 决策：`{decision['status']}`", "",
                 "| Arm | RMS cm | Recovery | Query hit | Candidates | Points | Correction s | Duplicates | Mixed |",
                 "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for r in summary:
            lines.append(f"| {r['arm']} | {r['rms_cm']} | {r['instance_recovery']:.3f} | {r['category_query_hit']:.3f} | "
                         f"{r['actual_candidates']:.1f} | {r['actual_points']:.0f} | {r['correction_compute_seconds']:.3f} | "
                         f"{r['annotated_duplicate_excess']:.1f} | {r['annotated_mixed_objects']:.1f} |")
        lines.extend(["", "表为支持≥3、候选上限25的固定展示，完整1008行读出另存。" if chinese else
                      "The table is the fixed support>=3/cap25 presentation; all 1008 readouts are retained separately.", ""])
        for endpoint in ("mean_coverage", "instance_recovery", "category_query_hit", "actual_candidates", "actual_points"):
            lines.extend([f"![{endpoint}]({endpoint}.png)", ""])
        lines.extend(["候选上限相同，不表示总内存或点数代价相同。未标候选不能直接算假阳性。种子范围不是置信区间。"
                      if chinese else "Equal candidate caps do not match total memory or point costs. Unlabelled candidates are not automatic false positives. Seed ranges are not confidence intervals.", "",
                      "即使达到原型筛查门槛，也只允许提出下一份原型计划；AI-only 标注不能确立共性瓶颈。"
                      if chinese else "Even a passing screen only licenses a subsequent prototype plan; AI-only labels cannot establish a common bottleneck.", ""])
        (args.output / f"analysis.{language}.md").write_text("\n".join(lines), encoding="utf-8")
    record = {"kind": "bilingual_identity_budget_exploratory_analysis", "status": "visual_review_pending",
              "analysis_type": inputs["analysis_type"], "H1_validated": False,
              "inputs": {name: digest(args.analysis / name) for name in ("readouts.json", "decision.json", "inputs.json")},
              "summary": summary, "artifacts": {p.name: {"sha256": digest(p), "bytes": p.stat().st_size}
                                                  for p in args.output.iterdir() if p.is_file()}}
    (args.output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
