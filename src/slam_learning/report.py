from __future__ import annotations

import json
from pathlib import Path

from .runner import verify_record


def render_report(paths: list[Path]) -> str:
    lines = ["# Measured experiment ledger", "", "Generated from run records. Paper agreement is distinct from execution.", "",
             "| Experiment | Scope | Execution | Paper table | SA % | DA % | AA % | HA % | Evidence |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for path in sorted(paths):
        r = json.loads(path.read_text(encoding="utf-8"))
        issues = verify_record(path)
        if issues:
            raise ValueError(f"Invalid evidence {path}: {'; '.join(issues)}")
        comparison = r.get("paper_comparison")
        match = "matched" if comparison and comparison["matched"] else "mismatch" if comparison else "not evaluated"
        metrics = r.get("metrics", {})
        name = r.get("method", r["kind"].replace("_", " "))
        values = [f"{metrics[k]:.4f}" if k in metrics else "—" for k in ("SA", "DA", "AA", "HA")]
        lines.append(f"| {name} | {r.get('scope', r['kind'])} | {r['status']} | {match} | "
                     + " | ".join(values) + f" | {path.parent.name}/record.json |")
        if r.get("error"):
            lines.extend(["", f"{name}: {r['error']}", ""])
    lines += ["", "Synthetic trials are a mechanism test with oracle associations/visibility, not a paper reproduction.",
              "Large maps and source datasets are local-only; portable records contain their hashes and fresh-run logs.",
              "`verify --full` requires those maps to be present. No historical archive score contributes to this table.", ""]
    return "\n".join(lines)
