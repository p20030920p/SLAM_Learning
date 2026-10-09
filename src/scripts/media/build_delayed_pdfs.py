"""Build two delayed-correction reports from sealed primary and post-hoc evidence."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from build_paper_pdfs import build, digest, verify_portable


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cjk-font", type=Path, required=True)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    sources = {Path(__file__), root / "src/scripts/media/build_paper_pdfs.py"}
    for name in ("delayed-pose", "delayed-support-control", "delayed-recordings"):
        evidence = root / f"results/reference/{name}/record.json"
        verify_portable(evidence)
        sources.add(evidence)
    pdfmetrics.registerFont(TTFont("StudyCJK", str(args.cjk_font), subfontIndex=0))
    pdfmetrics.registerFontFamily("StudyCJK", normal="StudyCJK", bold="StudyCJK",
                                  italic="StudyCJK", boldItalic="StudyCJK")
    output = root / "results/runs" / f"delayed-pdfs-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True, exist_ok=False)
    pages = {}
    for language in ("en", "zh-CN"):
        source = root / ("docs/research/DELAYED_RESULTS.md" if language == "en" else "docs/research/DELAYED_RESULTS.zh-CN.md")
        sources.add(source)
        sources.update((source.parent / name).resolve() for name in re.findall(
            r"!\[[^\]]*\]\(([^)]+)\)", source.read_text(encoding="utf-8")))
        target = output / f"delayed-study.{language}.pdf"
        pages[target.name] = build(source, target, root, language,
                                  "https://github.com/p20030920p/SLAM_Learning/blob/main/",
                                  image_max_height=340, body_leading=15.0 if language == "zh-CN" else 14.5,
                                  keep_tables_together=True)
        if args.publish:
            shutil.copy2(target, root / "docs/pdf" / target.name)
    for source in sources:
        dest = output / "inputs" / source.relative_to(root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    record = {"schema_version": 1, "kind": "bilingual_delayed_reports", "status": "executed", "exit_code": 0,
              "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "input_sha256": {p.relative_to(root).as_posix(): digest(p) for p in sorted(sources)},
              "page_counts": pages, "cjk_font_sha256": digest(args.cjk_font),
              "packages": {n: importlib.metadata.version(n) for n in ("reportlab", "pypdf", "pillow")},
              "scope": "Primary and exploratory evidence separated; H1 remains a candidate; rendered review required",
              "artifacts": {p.relative_to(output).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size,
                            "availability": "portable"} for p in output.rglob("*") if p.is_file()}}
    (output / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"record": str(output / "record.json"), "pages": pages}))


if __name__ == "__main__":
    main()
