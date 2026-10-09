"""Build bilingual reading reports from verified evidence and Markdown editions.

Run in the separate reports environment; the CPU/method dependency lock is unchanged.
PDF rendering and human layout review are required before publication.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import urljoin

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_portable(path: Path) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("schema_version") != 1 or record.get("status") != "executed":
        raise ValueError(f"Completed evidence required: {path}")
    for name, artifact in record["artifacts"].items():
        target = (path.parent / name).resolve()
        if not target.is_relative_to(path.parent.resolve()):
            raise ValueError("Artifact escapes its record directory")
        if artifact["availability"] == "portable" and (
            not target.is_file() or digest(target) != artifact["sha256"]
        ):
            raise ValueError(f"Unverified portable input: {target}")
    return record


def inline(text: str, source: Path, root: Path, base_url: str) -> str:
    # Convert authored Markdown to ReportLab markup, retaining clickable source links.
    tokens = []

    def link(match):
        label, target = match.groups()
        if not re.match(r"https?://", target):
            target = urljoin(base_url, (source.parent / target).resolve().relative_to(root).as_posix())
        tokens.append(f'<a href="{escape(target, quote=True)}" color="#147D85">{escape(label)}</a>')
        return f"SLAMLINKTOKEN{len(tokens)-1}END"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
    text = escape(text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<font color='#394E58'>\1</font>", text)
    # Mechanism equations are explicitly written in readable notation, not raw LaTeX.
    text = text.replace(r"$\sigma_p^2+\sigma_s^2/N$", "sigma_p^2 + sigma_s^2 / N")
    text = text.replace(r"$(\sigma_p^2+\sigma_s^2)/N$", "(sigma_p^2 + sigma_s^2) / N")
    for i, token in enumerate(tokens):
        text = text.replace(f"SLAMLINKTOKEN{i}END", token)
    text = text.replace("$N$", "N")
    # English editions still include a Chinese edition link; avoid missing glyphs.
    return re.sub(r"[\u3400-\u9fff]+", r"<font name='StudyCJK'>\g<0></font>", text)


def build(source: Path, target: Path, root: Path, language: str, base_url: str, image_max_height=225,
          body_leading=15.6, keep_tables_together=False) -> int:
    chinese = language == "zh-CN"
    face = "StudyCJK" if chinese else "Helvetica"
    body = ParagraphStyle("body", fontName=face, fontSize=10.2, leading=body_leading,
                          textColor=colors.HexColor("#263D47"), spaceAfter=8,
                          wordWrap="CJK" if chinese else None, splitLongWords=True)
    styles = {
        "body": body,
        "title": ParagraphStyle("title", parent=body, fontSize=22, leading=29,
                                textColor=colors.HexColor("#173D48"), spaceAfter=12),
        "heading": ParagraphStyle("heading", parent=body, fontSize=13.2, leading=19,
                                  textColor=colors.HexColor("#147D85"), spaceBefore=12,
                                  spaceAfter=7, keepWithNext=True),
        "small": ParagraphStyle("small", parent=body, fontSize=8.4, leading=12, spaceAfter=5),
        "cell": ParagraphStyle("cell", parent=body, fontSize=8.4, leading=12, spaceAfter=0),
        "code": ParagraphStyle("code", parent=body, fontName="Courier", fontSize=8.3,
                               leading=12, backColor=colors.HexColor("#F0F5F6"),
                               borderPadding=8, spaceBefore=5, spaceAfter=10),
    }
    story = [Paragraph("SLAM LEARNING  /  REPRODUCTION STUDY  /  08 OCT 2026", styles["small"]),
             HRFlowable(width="100%", thickness=2, color=colors.HexColor("#147D85")), Spacer(1, 12)]
    lines = source.read_text(encoding="utf-8").splitlines()
    cursor = 0
    while cursor < len(lines):
        line = lines[cursor].strip()
        cursor += 1
        if not line or line.startswith("<!--"):
            continue
        if line.startswith("# "):
            story.append(Paragraph(inline(line[2:], source, root, base_url), styles["title"]))
        elif line.startswith("## "):
            story.append(Paragraph(inline(line[3:], source, root, base_url), styles["heading"]))
        elif line.startswith("!["):
            match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", line)
            if not match:
                raise ValueError(f"Unsupported image markup: {line}")
            image = (source.parent / match[2]).resolve()
            if not image.is_relative_to(root):
                raise ValueError("Image escapes repository")
            from PIL import Image as PILImage
            with PILImage.open(image) as native:
                width, height = native.size
            display_width = min(A4[0]-92, width)
            display_height = display_width * height / width
            if display_height > image_max_height:
                display_width *= image_max_height/display_height
                display_height = image_max_height
            story.append(KeepTogether([Image(str(image), display_width, display_height, hAlign="LEFT"),
                                      Spacer(1, 5), Paragraph(escape(match[1]), styles["small"])]))
        elif line.startswith("```"):
            code = []
            while cursor < len(lines) and not lines[cursor].strip().startswith("```"):
                code.append(lines[cursor])
                cursor += 1
            cursor += 1
            story.append(Paragraph("<br/>".join(escape(x) for x in code), styles["code"]))
        elif line.startswith("|"):
            rows = [line]
            while cursor < len(lines) and lines[cursor].strip().startswith("|"):
                rows.append(lines[cursor].strip())
                cursor += 1
            cells = [row.strip("|").split("|") for row in rows]
            cells = [row for row in cells if not all(re.fullmatch(r"\s*:?-+:?\s*", col) for col in row)]
            widths = [A4[0]-92] * 1
            count = len(cells[0])
            if count == 3:
                widths = [(A4[0]-92)*v for v in (.22, .39, .39)]
            elif count == 2:
                widths = [(A4[0]-92)*v for v in (.43, .57)]
            else:
                widths = [(A4[0]-92)/count]*count
            data = [[Paragraph(inline(col.strip(), source, root, base_url), styles["cell"])
                     for col in row] for row in cells]
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEDEF")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8F8")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), .7, colors.HexColor("#147D85")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            story.extend([KeepTogether([table]) if keep_tables_together else table, Spacer(1, 10)])
        elif line.startswith("$$"):
            story.append(Paragraph("Residual mechanism: r(i,t) = J_pose(i,t) delta_pose(t) + "
                                   "J_object(i,t) delta_object(i) + epsilon(i,t)", styles["code"]))
        else:
            text = [line]
            while cursor < len(lines) and lines[cursor].strip() and not re.match(
                r"^(#|\||```|!\[|\$\$|\d+\. |[-*] )", lines[cursor].strip()
            ):
                text.append(lines[cursor].strip())
                cursor += 1
            content = " ".join(text)
            if re.match(r"^\d+\. |^[-*] ", content):
                content = re.sub(r"^[-*] ", "• ", content)
            story.append(Paragraph(inline(content, source, root, base_url), body))

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#C8D8DC"))
        canvas.line(46, 39, A4[0]-46, 39)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#526A73"))
        canvas.drawString(46, 26, f"SLAM Learning | {target.stem} | measured scope + disclosed limits")
        canvas.drawRightString(A4[0]-46, 26, str(document.page))
        canvas.restoreState()

    document = SimpleDocTemplate(str(target), pagesize=A4, leftMargin=46, rightMargin=46,
                                 topMargin=42, bottomMargin=52, title=lines[0].lstrip("# "),
                                 author="SLAM Learning study", pageCompression=1)
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    pdf = PdfReader(target)
    if not pdf.pages or any(len(page.extract_text().strip()) < 30 for page in pdf.pages):
        raise ValueError(f"Empty/unreadable PDF page: {target}")
    return len(pdf.pages)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://github.com/p20030920p/SLAM_Learning/blob/main/")
    parser.add_argument("--publish", action="store_true", help="Copy generated PDFs to output/pdf; evidence remains immutable")
    parser.add_argument("--cjk-font", type=Path, help="Optional licensed TrueType/TTC font, embedded as a subset")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    suite_path = root / "configs/paper_suite.json"
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    inputs = [(method["id"], method["cards"]) for method in suite["methods"]]
    inputs += [("study", {"en": "docs/STUDY.md", "zh": "docs/STUDY.zh-CN.md"}),
               ("real-world", {"en": "docs/REAL_WORLD.md", "zh": "docs/REAL_WORLD.zh-CN.md"})]
    records = [root / method[key] for method in suite["methods"] for key in ("record", "media_record")]
    for path in records:
        verify_portable(path)
    if args.cjk_font:
        pdfmetrics.registerFont(TTFont("StudyCJK", str(args.cjk_font), subfontIndex=0))
        font_info = {"name": "embedded TrueType subset", "sha256": digest(args.cjk_font)}
    else:
        font = UnicodeCIDFont("STSong-Light")
        font.fontName = "StudyCJK"
        pdfmetrics.registerFont(font)
        font_info = {"name": "STSong-Light built-in CID fallback"}
    pdfmetrics.registerFontFamily("StudyCJK", normal="StudyCJK", bold="StudyCJK",
                                  italic="StudyCJK", boldItalic="StudyCJK")
    output = root / "results/runs" / f"paper-pdfs-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    artifacts, sources, pages = {}, {}, {}

    def bind(path):
        name = path.relative_to(output).as_posix()
        artifacts[name] = {"sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"}

    for path in [suite_path, *records]:
        copy = output / "inputs" / path.relative_to(root)
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copy)
        bind(copy)
        sources[path.relative_to(root).as_posix()] = digest(path)
    for name, cards in inputs:
        for lang, card in cards.items():
            language = "en" if lang == "en" else "zh-CN"
            source = root / card
            copy = output / "inputs" / card
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, copy)
            bind(copy)
            sources[card] = digest(source)
            target = output / f"{name}.{language}.pdf"
            pages[target.name] = build(source, target, root, language, args.base_url)
            bind(target)
    for method in suite["methods"]:
        poster = root / f"docs/media/{method['id']}/poster.png"
        media = json.loads((root / method["media_record"]).read_text(encoding="utf-8"))
        if digest(poster) != media["artifacts"]["poster.png"]["sha256"]:
            raise ValueError("Report image differs from measured media")
        copy = output / "inputs" / poster.relative_to(root)
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(poster, copy)
        bind(copy)
        sources[poster.relative_to(root).as_posix()] = digest(poster)
    record = {"schema_version": 1, "kind": "bilingual_paper_reports", "status": "executed",
              "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "repository_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
              "repository_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)),
              "generator_sha256": digest(Path(__file__)),
              "environment": {"python": platform.python_version(),
                              "packages": {name: importlib.metadata.version(name) for name in ("reportlab", "pypdf", "pillow")}},
              "cjk_font": font_info,
              "input_sha256": sources, "page_counts": pages,
              "scope": "Reading reports, not new experiment measurements. Page rendering/visual QA is a separate publication gate.",
              "artifacts": artifacts}
    (output / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    if args.publish:
        destination = root / "output/pdf"
        destination.mkdir(parents=True, exist_ok=True)
        for name in pages:
            shutil.copy2(output / name, destination / name)
    print(json.dumps({"record": str(output / "record.json"), "pages": pages}, ensure_ascii=False))


if __name__ == "__main__":
    main()
