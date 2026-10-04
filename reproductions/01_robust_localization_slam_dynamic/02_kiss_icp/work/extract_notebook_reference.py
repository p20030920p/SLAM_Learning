#!/usr/bin/env python3
"""Extract the authors' own KITTI results from their executed notebook.

`PRBonn/kiss-icp` ships the KITTI experiment as `eval/kitti.ipynb`, and the
authors publish the *executed* notebook (with outputs) from their own fork:

    https://github.com/nachovizzo/kiss-icp/blob/main/evaluation/kitti.ipynb

That notebook is the original repository's own result: the per-sequence metrics
of sequences 00-10 and their mean. It is a much sharper comparison target than
the paper's single aggregate (0.50 %), because it tells us where a difference
comes from when there is one.

This script downloads that notebook, pulls the numbers out of its outputs, and
writes them next to this file as `kiss_icp_notebook_reference.json`. Run it again
to refresh; the notebook itself is not committed (it is someone else's artifact,
and 1.9 MB).

Usage:
    python3 extract_notebook_reference.py [--out kiss_icp_notebook_reference.json]
"""
import argparse
import json
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://raw.githubusercontent.com/nachovizzo/kiss-icp/main/evaluation/kitti.ipynb"

METRICS = {
    "translation_error_pct": r"Average Translation Error\s+([0-9.]+)",
    "rotational_error_deg_per_m": r"Average Rotational Error\s+([0-9.]+)",
    "ate_m": r"Trajectory Error \(ATE\)\s+([0-9.]+)",
    "are_rad": r"Rotational Error \(ARE\)\s+([0-9.]+)",
}


def strip(text):
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(HERE, "kiss_icp_notebook_reference.json"))
    args = ap.parse_args()

    print(f"fetching {URL}")
    with urllib.request.urlopen(URL, timeout=120) as resp:
        nb = json.load(resp)

    rows = []
    summary = {}
    for cell in nb["cells"]:
        for out in cell.get("outputs", []):
            data = out.get("data", {})
            for key in ("text/plain", "text/html"):
                if key not in data:
                    continue
                text = strip("".join(data[key]) if isinstance(data[key], list) else data[key])
                if "Average Translation Error" not in text:
                    continue
                row = {}
                for name, pattern in METRICS.items():
                    m = re.search(pattern, text)
                    if m:
                        row[name] = float(m.group(1))
                if row and (not rows or rows[-1] != row):
                    rows.append(row)
            md = data.get("text/markdown")
            if md:
                text = "".join(md) if isinstance(md, list) else md
                for name, pattern in METRICS.items():
                    m = re.search(pattern, text)
                    if m:
                        summary[name] = float(m.group(1))

    if len(rows) != 11:
        raise SystemExit(f"expected 11 per-sequence tables, found {len(rows)}")

    payload = {
        "source": URL,
        "source_repo": "https://github.com/PRBonn/kiss-icp (eval/kitti.ipynb, executed copy)",
        "what": "the authors' own KITTI 00-10 metrics, read out of the notebook outputs",
        "sequences": {f"{i:02d}": rows[i] for i in range(11)},
        "mean_printed_in_notebook": summary,
        "mean_of_per_sequence": {
            name: round(sum(r[name] for r in rows) / len(rows), 4)
            for name in METRICS if all(name in r for r in rows)},
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    print(f"wrote {args.out}")
    for seq, row in payload["sequences"].items():
        print(f"  seq {seq}: {row.get('translation_error_pct')} %  "
              f"{row.get('rotational_error_deg_per_m')} deg/m  ATE {row.get('ate_m')} m")
    print(f"  mean of the 11: {payload['mean_of_per_sequence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
