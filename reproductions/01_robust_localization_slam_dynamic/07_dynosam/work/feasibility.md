# 01-07 DynoSAM — Feasibility assessment (read-only, no build attempted)

| Item | Value |
| :--- | :--- |
| Repo | `code/DynoSAM` @ `8c20caa1e6b08428d49e687a5f866c1a2b960f51` (2026-01-23, "Updated readme with RA-L"), depth-1 clone of `github.com/ACFR-RPG/DynoSAM`, no submodules (no `.gitmodules`) |
| Paper | T-RO 2025, arXiv:2501.11893 — OMD (S4U) camera ATE **0.11 m** (`../paper_baseline.md:31`) |
| Machine | 20-core CPU / 15 GB RAM / **no GPU** (`nvidia-smi`: not found; `nvcc`: not found; no `/usr/local/cuda*`; no `NvInfer.h` anywhere) |
| ROS | `/opt/ros/jazzy` only (`ROS_DISTRO=jazzy`); repo badge + docker target **Kilted** (`README.md:12`, `docker/Dockerfile.amd64:4`) |

```text
$ command -v nvcc || echo "nvcc: NOT FOUND"   -> nvcc: NOT FOUND
$ find / -maxdepth 6 -name "NvInfer.h"        -> (empty)
$ grep -n HAVE_CUDA /usr/include/x86_64-linux-gnu/opencv4/opencv2/cvconfig.h
  32:/* #undef HAVE_CUDA */
$ ls /usr/include/opencv4/opencv2/cudaoptflow.hpp -> No such file or directory
$ ros2 pkg prefix gtsam|config_utilities|opengv|dynamic_slam_interfaces -> "Package not found" (all four)
```

## 1. Exact build dependencies

| Dependency | Required version (repo evidence) | Local status |
| :--- | :--- | :--- |
| ROS 2 | **Kilted** (dev target); Jazzy tested on Orin — `docs/media/INSTALL.md:4-5`, `docker/Dockerfile.amd64:4` | Jazzy only ✅/⚠️ |
| GTSAM | **4.2.0** tag; `>= 4.1` min. Flags: `-DGTSAM_USE_SYSTEM_EIGEN=ON -DGTSAM_BUILD_UNSTABLE=ON -DGTSAM_POSE3_EXPMAP=ON -DGTSAM_ROT3_EXPMAP=ON -DGTSAM_TANGENT_PREINTEGRATION=OFF` — `docker/Dockerfile.amd64:104-113`, `docs/media/INSTALL.md:112` | ❌ **absent** (no lib, no `GTSAMConfig.cmake`, no pip gtsam) |
| OpenCV | **4.10.0 built from source with `-DWITH_CUDA=ON -DOPENCV_DNN_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=75`** + opencv_contrib — `docker/Dockerfile.amd64:67-93`. INSTALL.md:7 says `>= 3.4`, which is stale | ❌ 4.6.0 distro build, **CUDA off** |
| CUDA | 12.6.77 (Jetson) / 12.9 in practice — `docker/README.md:16,24` | ❌ absent |
| TensorRT / cuDNN | **10.7.0.23+cuda12.6** / 9.3.0.75 — `docker/README.md:18-19`; `find_package(TensorRT ...)` `dynosam_nn/CMakeLists.txt:34` | ❌ absent |
| Others (`dynosam_common/CMakeLists.txt:42-50`) | `opengv`(MIT-SPARK), `config_utilities`(MIT-SPARK), `PCL` (common io filters features), `TBB`, `nlohmann_json 3.11.3`, `Eigen3`, `MPI` | opengv ❌ / config_utilities ❌ / PCL ❌ / nlohmann_json ❌; TBB ✅ glog ✅ gflags ✅ |
| Also | `dynamic_slam_interfaces` (default ON, `dynosam_ros/CMakeLists.txt:15` + `dynosam_ros/package.xml:21`), pybind11 + Boost.Python + `Python3 3.10 Development` (`dynosam_nn/CMakeLists.txt:21-23`), `ament_cmake_python`, `ultralytics==8.3.0` + `numpy<2.0` (`dynosam_nn/README.md:28`) | dynamic_slam_interfaces ❌, pybind11 ❌ |

## 2. Is there ANY supported no-CUDA / no-TensorRT path?

**Runtime bypass of the detector: YES, and it is the default.** **Build bypass: NO — there is none.**

Detector bypass (no TensorRT/YOLO at runtime), quoted:
- `dynosam/src/frontend/vision/FeatureTracker.cc:63` — `if (!params_.prefer_provided_object_detection) { ... make_shared<dyno::YoloV8ObjectDetector>(...) }` → TensorRT engine is created **only** when the flag is `false`.
- `dynosam/src/frontend/vision/FeatureTracker.cc:1172-1186` — `if (params_.prefer_provided_object_detection) { if (image_container.hasObjectMask()) { ...computeObjectMaskBoundaryMask... return false; } else { LOG(FATAL) << "Params specify prefer provided object mask but input is missing!"; } }`
- Default is `true`: `dynosam/params/FrontendParams.yaml:62` `prefer_provided_object_detection: true` (header default also `true`, `TrackerParams.hpp:126`).
- ⚠️ **Doc bug**: `README.md:208-209` and `README.md:304` state the *opposite* of the code. `README.md:247`, `README.md:309` and `dynosam_nn/README.md:10` agree with the code.

Other CPU-ish switches (all real, all insufficient):
- `dynosam/params/FrontendParams.yaml:45` `feature_detector_type: "GFFT_CUDA"`; CPU alternative `GFTT`/`ORB_SLAM_ORB` with an explicit fallback — `dynosam/src/frontend/vision/FeatureDetector.cc:55-64` `LOG(WARNING) << "GFFT_CUDA selected but OPENCV CUDA not enabled. Falling back to GFTT"`.
- `dynosam/params/FrontendParams.yaml:61` `prefer_provided_optical_flow: false` → `FeatureTracker.cc:125-140` dense-flow branch when `true` (KHZ: the `false` branch, `trackDynamicKLT`, is the CUDA one).

**Why the build still cannot be bypassed (hard, unguarded):**
1. `dynosam_nn/CMakeLists.txt:3` — `project(dynosam_nn LANGUAGES C CXX CUDA)` → CMake configure fails with no `CMAKE_CUDA_COMPILER`.
2. `dynosam_nn/CMakeLists.txt:105` `src/YoloV8CudaUtils.cu` is an unconditional source; `:128-129` unconditionally link `TensorRT::TensorRT CUDA::cudart`; `:193` links `CUDA::cudart`. `DYNOSAM_NN_USE_TRT` (`:31`) only downgrades to a *warning* (`:37-49`) — nothing is actually removed. `INSTALL.md:24`: *"Backwards compatability (i.e no CUDA support) is not currently a priority."*
3. `dynosam/include/dynosam/frontend/vision/FeatureTracker.hpp:33` and `StaticFeatureTracker.hpp:32` — unconditional `#include <opencv2/cudaoptflow.hpp>` (header **not installed** here).
4. `FeatureTracker.cc:60` and `StaticFeatureTracker.cc:238` — unconditional `cv::cuda::SparsePyrLKOpticalFlow::create(...)`, **not** wrapped in `#ifdef DYNO_CUDA_OPENCV_ENABLED`. The macro exists (`dynosam_common/include/dynosam_common/Cuda.hpp:7-9`, derives from `HAVE_CUDA`) and is used for the *detector* (`FeatureDetector.cc:44,51`) but **not** for the tracker.
5. `dynosam/CMakeLists.txt:32` `find_package(dynosam_nn REQUIRED)` + `:143` links `dynosam_nn::dynosam_nn`, so the core `dynosam` library inherits the CUDA/TensorRT dependency.
6. No standalone example escapes this: `dynosam/example/dyno_sam.cc:89-90` sets **both** prefer-flags `false` (i.e. forces YOLO/TensorRT).

## 3. Input format and datasets

Input contract (`README.md:198-202`, `docs/media/DATASETS.md:47-50`): `rgb` 8-bit; `depth` **CV_64F metric**; `mask` **CV_32SC1**, 0 = static, else global track id `j`; `flow` **CV_32FC2**. RAFT pre-processing is **not** released (`README.md:204`).

Datasets are on an **open Apache directory index — no registration, no login** (verified HTTP 200 + listing):
```bash
wget -m -np -nH --cut-dirs=4 -R "index.html*" https://data.acfr.usyd.edu.au/rpg/dynosam/omd/swinging_4_unconstrained_stereo
```
| ID | Dataset | Server path (all publicly listed) |
| ---: | :--- | :--- |
| 3 | OMD — the 0.11 m target, `swinging_4_unconstrained_stereo/` — 552 frames × {`image_0/`, `depth/`, `flow/`, `semantic/`} + `pose_gt.txt`, `object_pose.txt`, `oxford.yaml` | `/rpg/dynosam/omd/` |
| 0 | KITTI tracking `0000…0006,0018,0020` | `/rpg/dynosam/kitti/` |
| 1 | Virtual KITTI 2 (raw, no pre-processing) | external (NAVER) |
| 2 | Cluster-SLAM CARLA `L1,L2,S1,S2` | `/rpg/dynosam/cluster_slam/` |
| 5 | TartanAir Shibuya (7 seqs) | `/rpg/dynosam/TartanAir_shibuya/` |
| 6 | VIODE `city_day,city_night,parking_lot` | `/rpg/dynosam/VIODE/` |

Size estimate for the S4U stereo subset (sampled `Content-Length`): rgb 1.41 + depth 0.30 + flow 9.83 + semantic 3.57 MB/frame ≈ **15.1 MB × 552 ≈ 8.3 GB**. Disk is fine (363 GB free); RAM is not the constraint.
Loader check — `OMDDataLoader` (`OMDDataProvider.cc:1382-1411`) wires exactly these folders; `OMDOldAllLoader` (`:963`) reads `/times.txt` (`:1045`), disparity→depth via `(baseline*fx)/(disp/256)` (`:989-1016`), `getOpticalFlow` (`:1019`), `getInstanceMask` (`:1029`). The published package matches. **So the data side is NOT the blocker.**

## 4. Test / CI path

- CI = documentation only: `.github/workflows/` contains a single `doxygen-gh-pages.yml`. **No build or test CI.**
- gtest exists (27 test files under `dynosam/test/`, e.g. `test_types.cc`, `test_camera.cc`, plus an internal synthetic `test/internal/simulator.cc`), run via `ros2 run dynosam_ros run_dynosam_gtest.py` (`README.md:328`, script at `dynosam_ros/scripts/run_dynosam_gtest.py`).
- **But the tests are not a CPU escape hatch**: `dynosam/CMakeLists.txt:278-317` `ament_add_gmock(${PROJECT_NAME}_test ...)` + `target_link_libraries(${PROJECT_NAME}_test ${PROJECT_NAME} ...)` — every test binary links the full `dynosam` library, hence CUDA-OpenCV + GTSAM + dynosam_nn/TensorRT. Same for `dynosam_cv/test/test_cuda_cache.cc` (`dynosam_cv/CMakeLists.txt:65-75`), which literally `#include <opencv2/core/cuda.hpp>`.
- `dynosam_test/` contains only resources/scripts — it is **not** a ROS package (no `package.xml`).

## Verdict

**NO — the repo cannot produce any result, or even configure, on this machine today.**
The `run_experiments_tro.py` entry point is additionally broken for this purpose (its `__main__` currently calls `run_viodes()`; every `prep_omd_sequence(".../swinging_4_unconstrained_stereo")` call is commented out — `run_experiments_tro.py:350-360, 574-628`), so the 0.11 m S4U command is not runnable as shipped anyway.

**Blocking dependency (single, concrete): a CUDA-enabled toolchain is a hard *configure/compile* requirement — `dynosam_nn/CMakeLists.txt:3` declares `project(dynosam_nn LANGUAGES C CXX CUDA)` and `dynosam/include/dynosam/frontend/vision/FeatureTracker.hpp:33` unconditionally includes `<opencv2/cudaoptflow.hpp>`, i.e. an OpenCV built with `WITH_CUDA=ON`. This machine has neither.** TensorRT (10.7), GTSAM 4.2.0, opengv, config_utilities, PCL and nlohmann_json are additional missing installs, but removing *all* of them still would not help while CUDA is absent.

Consequence for the task book: the *runtime* configuration needed for a CPU-style run already exists and is the default (`prefer_provided_object_detection: true` → dataset masks, no YOLO/TensorRT), so a **source patch** (guard the `cv::cuda` KLT behind `DYNO_CUDA_OPENCV_ENABLED` + a CPU `calcOpticalFlowPyrLK` fallback, drop `CUDA` from `project()` and the `.cu`/TensorRT link lines, stub the detector) is the only route — that is a code fork, not a reproduction, and would not reproduce the 0.11 m number faithfully. **Recommendation: keep 01-07 ⬜ 未开始 / 🔴 needs GPU; do not attempt.**
