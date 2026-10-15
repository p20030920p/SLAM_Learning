"""Build pinned author libraries on Ubuntu20.04/Noetic; API compatibility only."""

import os
from pathlib import Path
import subprocess

ROOT = Path("/root/srrg-reproduction-ws")
REFS = {
    "srrg_cmake_modules": "9fdadb87f36ef35b74179069691e83bb4008ccfa",
    "srrg_core": "6dbb452ffc84132094cccfcac82bdd4a2c8afa2e",
    "srrg_scan_matcher": "e070f08f6663132d1de3e49869132581091972d7",
    "srrg_mapper2d": "5ea162d1d90b25f916f25240b653e97e2758210e",
    "srrg_mapper2d_ros": "9aa14795d5e61c1ab4531d5c16cfce198d1a0cfa",
}

if __name__ == "__main__":
    env = os.environ.copy()
    for key in list(env):
        if key.lower() in ("http_proxy", "https_proxy", "all_proxy"):
            env.pop(key)
    for name, ref in REFS.items():
        p = ROOT / "src" / name
        if not p.exists():
            subprocess.run(
                ["git", "clone", "https://gitlab.com/srrg-software/" + name + ".git", str(p)],
                env=env,
                check=True,
            )
        assert subprocess.check_output(["git", "-C", str(p), "rev-parse", "HEAD"], text=True).strip() == ref
    replacements = {
        "<opencv/cv.h>": "<opencv2/opencv.hpp>",
        "<opencv/highgui.h>": "<opencv2/highgui.hpp>",
        "CV_LOAD_IMAGE_ANYDEPTH": "cv::IMREAD_ANYDEPTH",
        "CV_LOAD_IMAGE_ANYCOLOR": "cv::IMREAD_ANYCOLOR",
        "CV_BGR2RGB": "cv::COLOR_BGR2RGB",
    }
    for p in (ROOT / "src/srrg_core/src").rglob("*"):
        if p.suffix not in (".h", ".cpp"):
            continue
        original = p.read_text()
        result = original
        for old, new in replacements.items():
            result = result.replace(old, new)
        if result != original:
            p.write_text(result)
    # Core and distro g2o use the baseline Eigen ABI. Upstream mapper/scan matcher
    # add -march=native, changing Eigen object layout on this AVX host. Use one
    # baseline ABI across all libraries; this changes compilation, not the method.
    for name in ("srrg_scan_matcher", "srrg_mapper2d"):
        p = ROOT / "src" / name / "CMakeLists.txt"
        original = p.read_text()
        result = original.replace("-march=native", "")
        if result != original:
            p.write_text(result)
    # Building a named library avoids unneeded OpenCV2 visual-demo executables.
    command = "source /opt/ros/noetic/setup.bash && export G2O_ROOT=/opt/ros/noetic && catkin_make srrg_mapper2d_library -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3 '-DCATKIN_WHITELIST_PACKAGES=srrg_cmake_modules;srrg_core;srrg_scan_matcher;srrg_mapper2d' -j4"
    with (ROOT / "build-reproducible.log").open("w") as log:
        subprocess.run(["bash", "-c", command], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    include = [
        ROOT / "src/srrg_mapper2d/src",
        ROOT / "src/srrg_scan_matcher/src",
        ROOT / "src/srrg_core/src",
        Path("/usr/include/eigen3"),
        Path("/usr/include/opencv4"),
        Path("/opt/ros/noetic/include"),
        Path("/usr/include/suitesparse"),
    ]
    args = [
        "g++",
        "-std=c++11",
        "-O3",
        "-DNDEBUG",
        "-g",
        "-rdynamic",
        str(Path(__file__).with_name("worker.cpp")),
        "-o",
        str(ROOT / "srrg_worker"),
    ]
    args += ["-I" + str(p) for p in include]
    args += [
        "-L" + str(ROOT / "devel/lib"),
        "-L/opt/ros/noetic/lib",
        "-Wl,-rpath," + str(ROOT / "devel/lib") + ":/opt/ros/noetic/lib",
        "-lsrrg_mapper2d_library",
        "-lsrrg_scan_matcher_library",
        "-lsrrg_messages_library",
        "-lg2o_core",
        "-lg2o_types_slam2d",
        "-lg2o_stuff",
    ]
    subprocess.run(args, check=True)
    print("Built native author Mapper2D + projective merger + graph merger")
