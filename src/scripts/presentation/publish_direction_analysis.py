"""Preserve the user-authored direction section when publishing experiments."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def refresh_direction(text: str, chinese: bool) -> str:
    heading = "方向分析" if chinese else "Direction analysis"
    if "## " + heading + "\n" not in text:
        raise ValueError("Missing direction analysis: " + heading)
    return text


def publish() -> None:
    from publish_home_experiments import apply_home_layout

    for path, zh in [(ROOT / "README.md", False), (ROOT / "docs/HOME.zh-CN.md", True)]:
        text = path.read_text(encoding="utf-8")
        updated = apply_home_layout(refresh_direction(text, zh), zh)
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    publish()
