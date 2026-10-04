#!/usr/bin/env python3
"""The two figures the D line promised, from the numbers stage 2 measured.

`reproductions/01_robust_localization_slam_dynamic/README.md` lists the
direction's hard outputs as

    1. a table: F1 ranking vs registration-failure ranking, with Spearman rho
    2. a scatter: static-point removal rate vs localization failure rate

The table lives in that README and in 01-02's findings. This script draws the
figure, from `results/registration_utility.json` and the per-map scores in
`results/registration_maps/`, so it can be regenerated whenever the numbers move.

Usage:
    work/make_h1prime_figure.py [--out results/h1prime.png]
"""

from __future__ import annotations

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/h1prime.png")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    results = os.path.normpath(os.path.join(here, "..", "results"))
    with open(os.path.join(results, "registration_utility.json"), encoding="utf-8") as fh:
        util = json.load(fh)

    maps_dir = os.path.join(results, "registration_maps")
    quality = {}
    for f in sorted(os.listdir(maps_dir)):
        if f.startswith("score_") and f.endswith(".json"):
            with open(os.path.join(maps_dir, f), encoding="utf-8") as fh:
                s = json.load(fh)["official"]
            quality[f[len("score_"):-len(".json")]] = (s["SA"], s["AA"])

    maps = [m for m in util["maps"] if m in quality]
    levels = sorted(util["maps"][maps[0]].keys())

    # the as-submitted SA/AA, straight from each method folder's own score json
    submitted = {"uncleaned": {"SA": 100.0, "AA": 0.0}}
    repro = os.path.normpath(os.path.join(here, "..", ".."))
    for name, (folder, rel) in {
            "erasor_port": ("03_erasor", "results/erasor_benchmark_port.json"),
            "removert_official": ("04_removert", "results/score_official_scanside.json"),
            "removert_port": ("04_removert", "results/score_benchmark_port.json"),
            "dufomap": ("05_dufomap", "results/dufomap_score_paper_default_dp1.json"),
            "beautymap": ("06_beautymap", "results/beautymap_score.json")}.items():
        path = os.path.join(repro, folder, rel)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                payload = json.load(fh)
            s_ = payload.get("official") or payload.get("python")
            if s_:
                submitted[name] = {"SA": s_["SA"], "AA": s_["AA"]}

    def _rank(x):
        """Tie-averaged ranks - the standard Spearman convention, and the one
        reproduce.py uses. Sequential ranks would disagree here: dufomap and
        removert_port tie at 11.3 % failure, and breaking that tie by list order
        moves rho from 0.38 to 0.49."""
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    def _rho(a, b):
        ra, rb = _rank(a), _rank(b)
        n = len(a)
        ma, mb = sum(ra) / n, sum(rb) / n
        num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
        da = sum((ra[i] - ma) ** 2 for i in range(n)) ** 0.5
        db = sum((rb[i] - mb) ** 2 for i in range(n)) ** 0.5
        return num / (da * db) if da and db else 0.0

    _lv = levels[-2] if len(levels) >= 2 else levels[-1]
    _util = [100.0 - util["maps"][m][_lv]["failure_rate_pct"] for m in maps]
    rho_norm = _rho([quality[m][1] for m in maps], _util)
    rho_submitted = (_rho([submitted[m]["AA"] for m in maps], _util)
                     if all(m in submitted for m in maps) else None)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))

    # ---- panel 1: removal rate vs failure rate (hard output #2) -----------
    # The x axis is the *as-submitted* SA - the number the benchmark tables
    # print - because that is where "how much did this method delete" actually
    # varies (0.4 % for Removert, 33 % for ERASOR). On the resolution-normalised
    # maps every method sits at 81-86 % removed, which is a property of the
    # normalisation, not of the method.
    ax = axes[0]
    lv = levels[-2] if len(levels) >= 2 else levels[-1]
    lv_meta = util["protocol"]["perturbation_levels"][int(lv[1:])]
    offs = {"erasor_port": (-58, 6), "uncleaned": (8, 4), "beautymap": (8, 4),
            "removert_port": (8, -12), "dufomap": (8, 4), "removert_official": (8, -12)}
    for m in maps:
        sa = submitted.get(m, {}).get("SA", quality[m][0])
        fail = util["maps"][m][lv]["failure_rate_pct"]
        ax.scatter(100 - sa, fail, s=70)
        ax.annotate(m, (100 - sa, fail), textcoords="offset points",
                    xytext=offs.get(m, (8, 4)), fontsize=9)
    ax.set_xlabel("static points removed  [%]   (100 - SA, maps as submitted)")
    ax.set_ylabel(f"registration failure rate [%]  ({lv}: {lv_meta['m']} m, {lv_meta['deg']} deg)")
    ax.set_title("Does deleting more static points cost localizability?")
    ax.text(0.98, 0.04,
            f"rho(as-submitted AA, utility) = "
            f"{rho_submitted if rho_submitted is not None else float('nan'):.2f}",
            transform=ax.transAxes, ha="right", fontsize=9,
            bbox=dict(boxstyle="round", fc="white", ec="0.7"))
    ax.grid(alpha=0.3)

    # ---- panel 2: failure vs perturbation, one line per map ---------------
    ax = axes[1]
    for m in maps:
        ys = [util["maps"][m][l]["failure_rate_pct"] for l in levels]
        xs = [util["protocol"]["perturbation_levels"][int(l[1:])]["m"] for l in levels]
        ax.plot(xs, ys, marker="o", label=m)
    ax.set_xlabel("initial-guess translation error [m]")
    ax.set_ylabel("registration failure rate [%]")
    ax.set_title("Failure vs how wrong the initial guess is")
    ax.text(0.02, 0.94, f"rho(normalised AA, utility) = {rho_norm:.2f} at {lv}",
            transform=ax.transAxes, fontsize=9,
            bbox=dict(boxstyle="round", fc="white", ec="0.7"))
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    fig.suptitle("H1': map-quality ranking vs downstream localizability "
                 "(KITTI 00, 141 frames, self-registration)", fontsize=11)
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    fig.savefig(args.out, dpi=140)
    print(f"wrote {args.out}")
    print(f"  panel 1 level: {lv}; maps: {', '.join(maps)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
