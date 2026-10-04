#!/usr/bin/env python3
"""Automated reproduction driver for this directory.

One command runs every reproduction that can run on this machine, records the
metrics it produced, checks them against the recorded baselines, refreshes the
progress block in the READMEs, and writes `status.json`.

    python3 reproductions/run_all.py              # run + backtest + refresh README
    python3 reproductions/run_all.py --no-backtest
    python3 reproductions/run_all.py --check      # do not run, only re-render status
    python3 reproductions/run_all.py --only 02-01

A reproduction is a folder `reproductions/<direction>/<NN_name>/` containing:

    README.md        the plan; its `| 复现状态 | ... |` line is the static status
    reproduce.py     optional; exposes require(ctx) and run(ctx)
    baselines.json   optional; the metrics a known-good run produced

`reproduce.py` contract
-----------------------
    require(ctx) -> None | str
        None when the reproduction can run. A string explaining what is missing
        (data not downloaded, repo not cloned, GPU absent) when it cannot.

    run(ctx) -> dict
        {"metrics": {...},
         "checks":    [{"name":..., "ok":bool, "detail":str}],   # invariants
         "findings":  [{"name":..., "detail":str}],              # measurements
         "artifacts": [relative paths]}

    `checks` gate the run: a failing check means the reproduction is broken.
    `findings` never gate anything — they are results about the data that belong
    in the record (for example "geometry alone cannot separate moved from
    unchanged on this pair").

`ctx` carries: direction, folder, id, path, data_root, code_root, results_dir,
work_dir, repo_root.

Nothing here needs network access unless a reproduction asks for it; the driver
never downloads on its own.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
STATUS_PATH = os.path.join(HERE, "status.json")

PROGRESS_START = "<!-- PROGRESS:START -->"
PROGRESS_END = "<!-- PROGRESS:END -->"

# The two directions, in folder order.
DIRECTIONS = {
    "01_robust_localization_slam_dynamic": "D1",
    "02_semantic_mapping_visual_anchoring_navigation": "D2",
}

STATUS_ICON = {
    "green": "🟢",
    "yellow": "🟡",
    "blocked": "⛔",
    "planned": "⬜",
    "failed": "❌",
}


# --------------------------------------------------------------------------- #
# discovery
# --------------------------------------------------------------------------- #
def discover():
    """Every reproduction folder, in numbered order."""
    found = []
    for direction in sorted(DIRECTIONS):
        dpath = os.path.join(HERE, direction)
        if not os.path.isdir(dpath):
            continue
        for name in sorted(os.listdir(dpath)):
            fpath = os.path.join(dpath, name)
            if not os.path.isdir(fpath) or not re.match(r"^\d\d_", name):
                continue
            num = f"{direction[:2]}-{name[:2]}"
            found.append({
                "id": num,
                "direction": direction,
                "direction_code": DIRECTIONS[direction],
                "folder": name,
                "path": fpath,
            })
    return found


def read_plan(folder):
    """Paper name, venue, static status and the task-book anchor from README.md."""
    readme = os.path.join(folder, "README.md")
    info = {"title": "", "venue": "", "static_status": "", "heading": ""}
    if not os.path.exists(readme):
        return info
    text = open(readme, encoding="utf-8").read()
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        info["heading"] = m.group(1).strip()
    for key, field in (("论文", "title"), ("Venue", "venue"), ("复现状态", "static_status")):
        m = re.search(rf"^\|\s*{key}\s*\|\s*(.+?)\s*\|\s*$", text, re.M)
        if m:
            info[field] = m.group(1).strip()
    return info


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# running
# --------------------------------------------------------------------------- #
def run_one(entry, backtest=True):
    ctx = {
        "id": entry["id"],
        "direction": entry["direction"],
        "folder": entry["folder"],
        "path": entry["path"],
        "data_root": os.path.join(entry["path"], "data", "raw"),
        "code_root": os.path.join(entry["path"], "code"),
        "results_dir": os.path.join(entry["path"], "results"),
        "work_dir": os.path.join(entry["path"], "work"),
        "repo_root": REPO_ROOT,
    }
    result = dict(entry)
    result.update(read_plan(entry["path"]))
    result["ran"] = False
    result["metrics"] = {}
    result["checks"] = []
    result["findings"] = []
    result["artifacts"] = []

    repro = os.path.join(entry["path"], "reproduce.py")
    if not os.path.exists(repro):
        result["level"] = "planned"
        result["note"] = "no reproduce.py yet — see README.md for the plan"
        return result

    try:
        mod = load_module(repro, f"repro_{entry['id'].replace('-', '_')}")
    except Exception as exc:  # a broken reproduction must not stop the others
        result["level"] = "failed"
        result["note"] = f"cannot load reproduce.py: {exc}"
        return result

    if hasattr(mod, "require"):
        try:
            missing = mod.require(ctx)
        except Exception as exc:
            result["level"] = "failed"
            result["note"] = f"require() raised: {exc}"
            return result
        if missing:
            result["level"] = "blocked"
            result["note"] = str(missing)
            return result

    try:
        out = mod.run(ctx) or {}
    except Exception as exc:
        result["level"] = "failed"
        result["note"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()[-1500:]
        return result

    result["ran"] = True
    result["metrics"] = out.get("metrics", {})
    result["checks"] = out.get("checks", [])
    result["findings"] = out.get("findings", [])
    result["artifacts"] = out.get("artifacts", [])
    result["note"] = out.get("note", "")

    failed_checks = [c for c in result["checks"] if not c.get("ok", False)]
    if failed_checks:
        result["level"] = "failed"
        result["note"] = result["note"] or f"{len(failed_checks)} check(s) failed"

    if backtest:
        result["backtest"] = backtest_one(entry["path"], result["metrics"])
        if result.get("level") != "failed" and result["backtest"]["status"] == "regressed":
            result["level"] = "failed"
            result["note"] = "backtest regressed"
    if not result.get("level") or result["level"] not in ("failed",):
        result["level"] = "green" if result["metrics"] else "yellow"
    return result


# --------------------------------------------------------------------------- #
# backtest: compare this run's metrics against the recorded baseline
# --------------------------------------------------------------------------- #
def backtest_one(folder, metrics):
    path = os.path.join(folder, "baselines.json")
    if not os.path.exists(path):
        return {"status": "no-baseline", "diffs": []}
    baseline = json.load(open(path, encoding="utf-8"))
    expected = baseline.get("metrics", {})
    rel_tol = baseline.get("rel_tolerance", 0.02)
    abs_tol = baseline.get("abs_tolerance", 1e-9)

    diffs = []
    for key, want in expected.items():
        got = metrics.get(key)
        if got is None:
            diffs.append({"metric": key, "expected": want, "got": None,
                          "ok": False, "why": "missing from this run"})
            continue
        if isinstance(want, (int, float)) and isinstance(got, (int, float)):
            ok = abs(got - want) <= max(abs_tol, rel_tol * abs(want))
        else:
            ok = got == want
        diffs.append({"metric": key, "expected": want, "got": got, "ok": ok,
                      "why": "" if ok else "outside tolerance"})
    extra = sorted(set(metrics) - set(expected))
    return {
        "status": "ok" if all(d["ok"] for d in diffs) else "regressed",
        "diffs": diffs,
        "new_metrics_not_in_baseline": extra,
        "baseline_recorded": baseline.get("recorded", ""),
    }


# --------------------------------------------------------------------------- #
# progress block
# --------------------------------------------------------------------------- #
def render_progress(results):
    green = sum(1 for r in results if r["level"] == "green")
    ran = sum(1 for r in results if r["ran"])
    automated = sum(1 for r in results
                    if os.path.exists(os.path.join(r["path"], "reproduce.py")))
    total = len(results)
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")

    lines = [
        PROGRESS_START,
        "",
        f"**进度 Progress** — {green}/{total} 跑通 · {ran} 本次实际运行 · "
        f"{automated}/{total} 已自动化 · 更新于 {stamp}",
        "",
        "| # | 方向 | 复现对象 | 状态 | 本次运行 | 回测 | 关键指标 / 阻塞原因 |",
        "| :-- | :-- | :-- | :-- | :-- | :-- | :-- |",
    ]
    for r in sorted(results, key=lambda x: x["id"]):
        icon = STATUS_ICON.get(r["level"], "⬜")
        ran = "✅" if r["ran"] else "—"
        bt = r.get("backtest", {}).get("status", "—")
        bt_icon = {"ok": "✅ 通过", "regressed": "❌ 回退", "no-baseline": "—"}.get(bt, bt)
        if r["metrics"]:
            bits = []
            for k in ("objects_total", "unchanged", "moved", "absent_unlabelled"):
                if k in r["metrics"]:
                    bits.append(f"{k}={r['metrics'][k]}")
            detail = ", ".join(bits) if bits else f"{len(r['metrics'])} metrics"
        else:
            detail = r.get("note", "") or r.get("static_status", "")
        detail = detail.replace("|", "/")
        if len(detail) > 110:
            detail = detail[:107] + "…"
        title = r["heading"] or r["folder"]
        title = re.sub(r"^\d\d-\d\d\s*·\s*", "", title)
        lines.append(f"| {r['id']} | {r['direction_code']} | {title} | {icon} "
                     f"{r['level']} | {ran} | {bt_icon} | {detail} |")
    lines += [
        "",
        "> 本表由 `python3 reproductions/run_all.py` 自动生成，块内内容请勿手改。",
        "> 新增复现：建好文件夹与 `README.md`，再放一个实现 `require(ctx)` / `run(ctx)` 的 "
        "`reproduce.py`，重跑本命令即可。",
        "",
        PROGRESS_END,
    ]
    return "\n".join(lines)


def update_readme(path, block):
    if not os.path.exists(path):
        return False
    text = open(path, encoding="utf-8").read()
    if PROGRESS_START in text and PROGRESS_END in text:
        new = re.sub(
            re.escape(PROGRESS_START) + r".*?" + re.escape(PROGRESS_END),
            block.replace("\\", "\\\\"), text, flags=re.S)
    else:
        new = text.rstrip() + "\n\n" + block + "\n"
    if new != text:
        open(path, "w", encoding="utf-8").write(new)
        return True
    return False


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="run just this id, e.g. 02-01")
    ap.add_argument("--no-backtest", action="store_true", help="skip baseline comparison")
    ap.add_argument("--check", action="store_true",
                    help="do not run anything; re-render status and READMEs only")
    ap.add_argument("--no-readme", action="store_true", help="do not touch the READMEs")
    args = ap.parse_args()

    all_entries = discover()
    entries = all_entries
    if args.only:
        entries = [e for e in entries if e["id"] == args.only]
        if not entries:
            raise SystemExit(f"no reproduction with id {args.only}")

    print(f"discovered {len(all_entries)} reproduction folders under {HERE}"
          + (f"; running only {args.only}" if args.only else "") + "\n")
    results = []
    for e in entries:
        if args.check:
            r = dict(e)
            r.update(read_plan(e["path"]))
            r.update({"ran": False, "metrics": {}, "checks": [], "findings": [],
                      "artifacts": [], "level": "planned", "note": ""})
            prev = None
            if os.path.exists(STATUS_PATH):
                try:
                    prev = next((x for x in json.load(open(STATUS_PATH, encoding="utf-8"))["reproductions"]
                                 if x["id"] == e["id"]), None)
                except Exception:
                    prev = None
            if prev:
                r.update({k: prev[k] for k in
                          ("level", "metrics", "checks", "findings", "note",
                           "ran", "backtest")
                          if k in prev})
            results.append(r)
            continue

        print(f"[{e['id']}] {e['folder']}")
        r = run_one(e, backtest=not args.no_backtest)
        results.append(r)
        icon = STATUS_ICON.get(r["level"], "?")
        print(f"    {icon} {r['level']}"
              f"{' — ' + r['note'] if r.get('note') else ''}")
        for c in r["checks"]:
            print(f"      {'PASS' if c.get('ok') else 'FAIL'}  {c.get('name')}"
                  f"{' — ' + c.get('detail', '') if c.get('detail') else ''}")
        for f in r.get("findings", []):
            print(f"      FIND  {f.get('name')}"
                  f"{' — ' + f.get('detail', '') if f.get('detail') else ''}")
        bt = r.get("backtest")
        if bt and bt["status"] != "no-baseline":
            print(f"      backtest: {bt['status']}"
                  + (f" ({sum(1 for d in bt['diffs'] if not d['ok'])} diff)"
                     if bt["status"] != "ok" else ""))
        print()

    def _rel(path):
        try:
            return os.path.relpath(path, REPO_ROOT)
        except ValueError:
            return path

    for r in results:
        r["path"] = _rel(r["path"])

    status = {
        "generated": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "root": "reproductions",
        "summary": {
            "total": len(results),
            "green": sum(1 for r in results if r["level"] == "green"),
            "failed": sum(1 for r in results if r["level"] == "failed"),
            "blocked": sum(1 for r in results if r["level"] == "blocked"),
            "planned": sum(1 for r in results if r["level"] == "planned"),
            "ran_this_pass": sum(1 for r in results if r["ran"]),
        },
        "reproductions": results,
    }
    with open(STATUS_PATH, "w", encoding="utf-8") as fh:
        json.dump(status, fh, indent=2, ensure_ascii=False)

    if not args.no_readme:
        block = render_progress(results)
        changed = []
        for rel in ("reproductions/README.md", "README.md", "README.zh-CN.md"):
            if update_readme(os.path.join(REPO_ROOT, rel), block):
                changed.append(rel)
        print("README progress block updated in: " + (", ".join(changed) or "nothing changed"))

    s = status["summary"]
    print(f"\nsummary: {s['green']}/{s['total']} green · {s['ran_this_pass']} ran · "
          f"{s['blocked']} blocked · {s['planned']} planned · {s['failed']} failed")
    print(f"status written to {STATUS_PATH}")
    return 1 if s["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
