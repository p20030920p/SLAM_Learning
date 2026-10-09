"""Build only the two paired-study reports from verified published measurements."""

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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cjk-font", type=Path, required=True)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    evidence = root / "results/reference/paired-pose/record.json"
    verify_portable(evidence)
    pdfmetrics.registerFont(TTFont("StudyCJK", str(args.cjk_font), subfontIndex=0))
    pdfmetrics.registerFontFamily(
        "StudyCJK", normal="StudyCJK", bold="StudyCJK", italic="StudyCJK", boldItalic="StudyCJK"
    )
    output = root / "results/runs" / f"paired-pdfs-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True, exist_ok=False)
    sources = {evidence, Path(__file__), root / "src/scripts/media/build_paper_pdfs.py"}
    pages = {}
    for language in ("en", "zh-CN"):
        source = root / ("docs/research/PAIRED_RESULTS.md" if language == "en" else "docs/research/PAIRED_RESULTS.zh-CN.md")
        sources.add(source)
        sources.update(
            (source.parent / name).resolve()
            for name in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", source.read_text(encoding="utf-8"))
        )
        target = output / f"paired-study.{language}.pdf"
        pages[target.name] = build(
            source,
            target,
            root,
            language,
            "https://github.com/p20030920p/SLAM_Learning/blob/main/",
            image_max_height=340,
            body_leading=15.0 if language == "zh-CN" else 15.6,
        )
        if args.publish:
            shutil.copy2(target, root / "docs/pdf" / target.name)
    for source in sources:
        destination = output / "inputs" / source.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    record = {
        "schema_version": 1,
        "kind": "bilingual_paired_reports",
        "status": "executed",
        "exit_code": 0,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_sha256": {source.relative_to(root).as_posix(): digest(source) for source in sorted(sources)},
        "page_counts": pages,
        "cjk_font_sha256": digest(args.cjk_font),
        "packages": {name: importlib.metadata.version(name) for name in ("reportlab", "pypdf", "pillow")},
        "scope": "Two reading reports; candidate hypothesis remains unvalidated. All pages require separate rendered visual review.",
        "artifacts": {
            path.relative_to(output).as_posix(): {
                "sha256": digest(path),
                "bytes": path.stat().st_size,
                "availability": "portable",
            }
            for path in output.rglob("*")
            if path.is_file()
        },
    }
    (output / "record.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"record": str(output / "record.json"), "pages": pages}))


if __name__ == "__main__":
    main()
