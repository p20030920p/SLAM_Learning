"""Build two implementation-audit PDFs; never label them completed experiment results."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from build_paper_pdfs import build, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cjk-font", type=Path, required=True)
    parser.add_argument("--review-revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=False)
    pdfmetrics.registerFont(TTFont("StudyCJK", str(args.cjk_font)))
    pdfmetrics.registerFontFamily("StudyCJK", normal="StudyCJK", bold="StudyCJK",
                                  italic="StudyCJK", boldItalic="StudyCJK")
    pages, inputs = {}, {}
    for language in ("en", "zh-CN"):
        suffix = "" if language == "en" else ".zh-CN"
        source = root / f"docs/reviews/IDENTITY_BUDGET_{args.review_revision}{suffix}.md"
        output = args.output / f"identity-budget-implementation-review.{language}.pdf"
        pages[output.name] = build(source, output, root, language,
            "https://github.com/p20030920p/SLAM_Learning/blob/study/identity-budget-v2/",
            body_leading=15.0 if language == "zh-CN" else 14.5, keep_tables_together=False)
        inputs[source.relative_to(root).as_posix()] = digest(source)
    record = {"kind": "identity_budget_implementation_review_pdfs", "status": "render_review_pending",
              "scope": "Implementation-stage review; native experiments pending; AI-only labels; not result PDFs",
              "reviewed_code_revision": args.review_revision, "input_sha256": inputs,
              "font_sha256": digest(args.cjk_font), "builder_sha256": digest(Path(__file__)),
              "layout_builder_sha256": digest(Path(__file__).with_name("build_paper_pdfs.py")),
              "page_counts": pages, "artifacts": {p.name: {"sha256": digest(p), "bytes": p.stat().st_size}
                                                     for p in args.output.glob("*.pdf")}}
    (args.output / "generation.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(pages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
