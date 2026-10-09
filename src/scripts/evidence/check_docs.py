"""Check bilingual pairs, local links and the evidence behind published media."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from slam_learning.core.provenance import digest
from slam_learning.runtime.runner import verify_record


def check(root: Path) -> list[str]:
    errors = []
    pairs = json.loads((root / "src/configs/documentation.json").read_text(encoding="utf-8"))["pairs"]
    for pair in pairs:
        for lang in ("en", "zh"):
            if not (root / pair[lang]).is_file():
                errors.append(f"Missing {lang} counterpart: {pair[lang]}")
    docs = [root / "README.md", *sorted((root / "docs").rglob("*.md")),
            *sorted((root / "results").glob("REPORT*.md"))]
    for path in docs:
        content = path.read_text(encoding="utf-8")
        content = re.sub(r"<!--.*?-->", "", content, flags=re.S)
        content = re.sub(r"```.*?```", "", content, flags=re.S)
        for target in re.findall(r"\]\(([^)]+)\)", content):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or not parsed.path:
                continue
            destination = (path.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root.resolve()) or not destination.exists():
                errors.append(f"Broken or external local link in {path.relative_to(root)}: {target}")
    slots = json.loads((root / "docs/figures/slots.json").read_text(encoding="utf-8"))["slots"]
    ids = set()
    for slot in slots:
        if slot["id"] in ids:
            errors.append(f"Duplicate media slot: {slot['id']}")
        ids.add(slot["id"])
        if slot["status"] not in ("reserved", "published") or not all(slot["caption"].get(k) for k in ("en", "zh")):
            errors.append(f"Invalid media state or bilingual caption: {slot['id']}")
        if slot["status"] == "published":
            asset = root / slot["path"]
            if not asset.is_file():
                errors.append(f"Missing published asset: {slot['path']}")
            if not slot["source_records"]:
                errors.append(f"Published result has no run evidence: {slot['id']}")
            bound = False
            for source in slot["source_records"]:
                record = root / source
                if not record.is_file():
                    errors.append(f"Missing media evidence: {source}")
                else:
                    errors.extend(f"{slot['id']}: {issue}" for issue in verify_record(record))
                    data = json.loads(record.read_text(encoding="utf-8"))
                    for name, info in data["artifacts"].items():
                        same_path = (record.parent / name).resolve() == asset.resolve()
                        declared_copy = slot.get("source_artifact") == name
                        if (same_path or declared_copy) and asset.is_file():
                            bound |= digest(asset) == info["sha256"]
            if not bound:
                errors.append(f"Published asset is not hash-bound to its source record: {slot['id']}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    errors = check(root)
    print("\n".join(errors) if errors else "Bilingual docs, local links and published media evidence verified")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
