"""Extract point-cloud previews from native captures and original PDF figures."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from package_session import gif

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal(folder, **metadata):
    artifacts = {
        p.relative_to(folder).as_posix(): {
            "sha256": sha(p),
            "bytes": p.stat().st_size,
            "availability": "portable",
        }
        for p in folder.rglob("*")
        if p.is_file() and p.name != "record.json"
    }
    (folder / "record.json").write_text(
        json.dumps(
            {"schema_version": 1, "status": "executed", "exit_code": 0, **metadata, "artifacts": artifacts},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main():
    folder = ROOT / "docs/media/related-pointcloud/20261016"
    folder.mkdir(parents=True, exist_ok=False)
    sources = {}
    for name, start in [("dufomap", 20), ("beautymap", 45), ("ir-mcl", 20)]:
        source = ROOT / f"results/reference/desktop-live-{name}/execution.mp4"
        target = folder / (name + ".mp4")
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                str(start),
                "-i",
                str(source),
                "-t",
                "12",
                "-vf",
                "crop=688:564:762:100",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                str(target),
            ],
            check=True,
        )
        timing = gif(target, target.with_suffix(".gif"))
        sources[name] = {
            "record": f"results/reference/desktop-live-{name}/record.json",
            "video": source.relative_to(ROOT).as_posix(),
            "sha256": sha(source),
            "interval_s": [start, start + 12],
            "crop_xywh": [762, 100, 688, 564],
            "timing": timing,
        }
    seal(
        folder,
        kind="cropped_native_pointcloud_previews",
        scope="12-second RViz viewport excerpts from existing actual author-code execution captures; real-time, terminal omitted, not new executions.",
        sources=sources,
    )
    robot = ROOT / "docs/media/robot/20261016"
    robot.mkdir(parents=True, exist_ok=False)
    for source, target in [
        ("screenshot.png", "urdf.png"),
        ("robot.rviz", "robot.rviz"),
        ("renderer.log", "renderer.log"),
    ]:
        shutil.copyfile(ROOT / ".cache/urdf-20261016" / source, robot / target)
    source = ROOT / "config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf"
    seal(
        robot,
        kind="native_urdf_rviz_screenshot",
        source_urdf=source.relative_to(ROOT).as_posix(),
        source_sha256=sha(source),
        scope="Actual RViz RobotModel rendering, all mesh files loaded; zero wheel angles. Red upper cylinder is the URDF's 3D lidar; black lower cylinder is its 2D lidar. No fabricated robot illustration.",
    )
    papers = ROOT / "docs/assets/related/20261016-pointcloud"
    papers.mkdir(parents=True, exist_ok=False)
    definitions = [
        ("srrg", 6, [95, 85, 895, 415], "srrg-fig7", "https://iris.uniroma1.it/handle/11573/1340118"),
        ("fastlio2", 16, [550, 498, 449, 280], "fastlio2-fig12", "https://arxiv.org/abs/2107.06829"),
    ]
    citations = {}
    for name, page, (x, y, w, h), target, url in definitions:
        source = ROOT / ".cache/papers-20261016" / (name + ".pdf")

        def wsl(p):
            return "/mnt/" + p.drive[0].lower() + "/" + p.as_posix()[3:]

        subprocess.run(
            [
                "wsl",
                "-d",
                "Ubuntu-24.04",
                "-u",
                "root",
                "--",
                "pdftoppm",
                "-f",
                str(page),
                "-l",
                str(page),
                "-scale-to",
                "1400",
                "-x",
                str(x),
                "-y",
                str(y),
                "-W",
                str(w),
                "-H",
                str(h),
                "-png",
                "-singlefile",
                wsl(source),
                wsl(papers / target),
            ],
            check=True,
        )
        citations[target] = {
            "url": url,
            "pdf_sha256": sha(source),
            "page": page,
            "crop_xywh_at_scale1400": [x, y, w, h],
            "scope": "Original paper figure excerpt; original-paper experiment not reproduced.",
        }
    seal(papers, kind="original_paper_pointcloud_figures", sources=citations)


if __name__ == "__main__":
    main()
