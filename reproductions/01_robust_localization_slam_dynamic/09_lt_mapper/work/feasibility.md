# 01-09 · LT-mapper — feasibility assessment (read-only)

Date 2026-10-05 · upstream `code/lt-mapper` (depth-1 clone, HEAD `80b6756`, 2025-02-18) · env
`reproductions/.venvs/ros1noetic` (391 conda pkgs) · **nothing installed, nothing built, nothing modified outside `work/`.**
Paths below are relative to `SLAM_Learning/`.

| Question | Answer |
| :--- | :--- |
| Catkin packages in repo | **2**: `ltslam`, `removert` (dir `ltremovert`). No `ltmap`/`lt_map` package exists. |
| Needed for the change-detection result | **`removert` (ltremovert) alone.** Its build has *no* GTSAM dependency. |
| Missing build deps in env | **GTSAM** (blocks `ltslam` only) · `rviz` (launch file only, not needed via `rosrun`). |
| ParkingLot download | **Free, no registration.** `bit.ly` → 301 → Google Drive folder; anonymous listing + download both verified. |
| But ParkingLot is raw sensors | `01.zip` → `01/sensor_data/Ouster_imu.csv` ⇒ needs SC-LIO-SAM first; **not** ready-to-eat session data. |
| Local data route | **Viable.** KITTI 00 frames 4390–4530 split into two overlapping sessions; poses already share one world frame, so **no LT-SLAM / no GTSAM required**. |
| Paper headline (85.7 MB / 9.8 s) | **Not producible here at all** — the LT-map / delta-map code is not in the repo, and Tab. I/II need MulRan KAIST 04 (author-contact extended sequence). |

## 1. Package layout

```
code/lt-mapper/
├── ltslam/       package.xml:3  <name>ltslam</name>          → ltslam_ltslam
└── ltremovert/   package.xml:4  <name>removert</name>        → removert_removert   (CMakeLists.txt:2,79)
```
* Only two `package.xml`/`CMakeLists.txt` pairs exist anywhere in the tree (`find . -name package.xml` → 2 hits);
  upstream's own build line is `catkin build ltslam removert` (`README.md:52`) — note **directory `ltremovert` ≠ package `removert`**.
* Change detection lives entirely in `ltremovert`: `Removerter::run()` (`ltremovert/src/Removerter.cpp:1653-1679`) is
  Step 0 prep → Step 1 `removeHighDynamicPoints()` → Step 2 `detectLowDynamicPoints()` → Step 3 `updateCurrentMap()` + save.
* **LT-map is a comment, not code**: `Removerter.cpp:1671` is the string `// # Step 3: LT-map`. A whole-repo
  `grep -rn -i 'delta_map\|delta map\|meta_map\|meta map' --include='*.cpp' --include='*.h'` returns **0 hits**.
  ⇒ the paper's Tab. II numbers (delta map **85.7 MB vs 213.6 MB**, **9.8 s vs 87/160 s**) have no implementation here.

## 2. Build dependencies vs the existing env

| Package | CMakeLists | package.xml | in env? |
| :--- | :--- | :--- | :--- |
| `ltslam` | `ltslam/CMakeLists.txt:8-26` (tf roscpp rospy cv_bridge pcl_conversions std_msgs sensor_msgs geometry_msgs nav_msgs message_generation) + OpenMP + PCL + OpenCV + **`find_package(GTSAM REQUIRED QUIET)`:26** + links `gtsam`:78 | `ltslam/package.xml:43-44` GTSAM | ❌ **GTSAM missing** |
| `removert` | `ltremovert/CMakeLists.txt:8-27` — same list **+ `image_transport`:21**; GTSAM commented out at `:27`/`:46`, not linked at `:88-94` | `ltremovert/package.xml:45-46` image_transport; GTSAM commented `:48-49` | ✅ **all present** |

* Present and verified in `reproductions/.venvs/ros1noetic/`: `share/` has `tf roscpp rospy cv_bridge pcl_conversions
  pcl_ros std_msgs sensor_msgs geometry_msgs nav_msgs message_generation message_runtime image_transport image_geometry
  tf2_eigen`; also `bin/catkin_make`, `include/opencv4/opencv2/opencv.hpp` (OpenCV 4.9.0), PCL 1.13.1, VTK 9.2.6,
  libgomp, boost 1.82, `empy 3.3.4`.
* **MISSING #1 — GTSAM.** `ls share/gtsam` → absent; `find .venvs/ros1noetic -iname '*gtsam*'` → nothing; no
  `GTSAMConfig.cmake` under `/usr`, `/usr/local`, `/opt`; no `libgtsam*`. Exact conda names: **`ros-noetic-gtsam`**
  (robostack-staging, only 4.2.0 — linux-64 `ros-noetic-gtsam-4.2.0-hb0f4dca_21.conda`, `…-py311hb3d35ac_17.tar.bz2`)
  or **`gtsam`** (conda-forge, 4.2.0 / 4.3.0 — `linux-64/gtsam-4.2.0-py311ha967941_0.conda`).
* **MISSING #2 — `ros-noetic-rviz`** (robostack-staging). Referenced only by the launch files
  (`ltremovert/launch/run_ltmapper.launch:6`; `ltslam/launch/run.launch` has rviz commented out) — irrelevant when
  driving the node with `rosrun`, exactly the sibling pattern (`04_removert/work/run_official.sh:47`).
* README prerequisites `navigation` / `robot_localization` / `robot_state_publisher` (`README.md:32-34`) are **NOT**
  referenced by any CMakeLists/package.xml (`grep` → no hits) — safe to ignore. Source drift vs PCL 1.13 is **one line**:
  `ltremovert/src/Removerter.cpp:938` `boost::shared_ptr<…> … boost::make_shared` must become `pcl::IndicesPtr` /
  `pcl::make_shared` (identical to `04_removert/work/local_patches.patch:24-27`); ltremovert has **no** `<opencv/cv.h>`
  (`grep` → 0 hits), so the other sibling patch is not needed.

## 3. Input data per module

| Module | Required input | Produced by |
| :--- | :--- | :--- |
| `ltslam` | `<sessions_dir>/<name>/Scans/*.pcd` (`ltslam/src/Session.cpp:147`), `<name>/SCDs/*.txt` (`:184`, space-delimited matrix, `utility.cpp:227`), `<name>/singlesession_posegraph.g2o` (`:221`, `VERTEX_SE3:QUAT`/`EDGE_SE3:QUAT`) | **SC-LIO-SAM** saver tool; also in SC-A-LOAM / FAST_LIO_SLAM (`README.md:77`) |
| `removert` | `central_sess_scan_dir` + `central_sess_pose_path`, `query_sess_scan_dir` + `query_sess_pose_path` (`ltremovert/config/params_ltmapper.yaml:13-17`; `RosParamServer.cpp:36-39`) | SC-LIO-SAM saver (PCD) — **or any producer you write yourself** |

Format details that matter (`ltremovert/src/Session.cpp`):
* **Scans must be `.pcd`** — the KITTI `.bin` branch is commented out at `:277-281`, and `isScanFileKITTIFormat`
  is parsed (`RosParamServer.cpp:7`) but never used (3 grep hits total: decl/param/comment).
* **Poses: 12 numbers per line**, KITTI-odometry `[R|t]` row-major, missing row `[0,0,0,1]` appended at `:106-107`;
  directory entries come from `fs::directory_iterator` + `std::sort` (`:87-93`) and are asserted 1:1 against the pose
  lines (`:117`) ⇒ **filename sort order must equal pose line order**.
* Central session cropped to `[start_idx, end_idx)` (`params_ltmapper.yaml:38-39` → `Removerter.cpp:92`); the query
  session auto-cropped to scans within **10 m** of a central keyframe (`Session.cpp:234`, `nnDist` `:217-227`).
* **No Scan Context descriptors needed** — `ltremovert/src/` contains no `Scancontext.cpp`.

### Download status (checked with curl, 2026-10-05)

| Route | Observed |
| :--- | :--- |
| `https://bit.ly/ltmapper_parkinglot_data` | `HTTP/2 301` → `location: https://drive.google.com/drive/folders/1FNIU691AR2g04NlKBFCDL4APpxpzkfQp?usp=sharing` |
| that Drive folder, anonymous | `HTTP/2 200`, 369 228 B HTML, `<title>ParkingLot – Google Диск</title>`; listing shows `README.txt` + `01.zip`…`06.zip` (one 2 GB) |
| anonymous file fetch | `README.txt` (id `1_g6LLfwckftPPMLSS6Qi24PWf61Chu8i`) → **200, 222 B**, final URL `drive.usercontent.google.com/download`; content = `parkinglot_01..06` dated 2021-01-25/26/27 → **6 sessions over 3 days, no login** |
| big zips | `01.zip` (id `1QWXCn9LMsJeepFn3cu4_aszMjMAIOGYE`) returns Google's *"Virus scan warning"* interstitial first; with `confirm=t` the download runs at ~1.1 MB/s ⇒ **~30 min/zip, ~3 h for all 6** |
| **content of `01.zip`** | first entries are `01/`, `01/sensor_data/`, `01/sensor_data/Ouster_imu.csv` ⇒ **raw Ouster+IMU sequences**, i.e. still needs SC-LIO-SAM to become ltremovert input |
| Docker | `which docker` → **not found** on this machine. Registry API: `dongjae0107/lt-mapper` has 3 tags; `latest` = amd64, **2 208 135 954 B**, pushed 2025-01-08; `auth.docker.io/token` → 200. Image exists, unusable here (no docker). |

## 4. Can the official code run on data already on this machine?

**Yes for the change-detection half, with one prerequisite file-format step.** Already local:
`01_dynamicmap_benchmark/data/raw/00/pcd/` = **141 world-frame PCDs**, `004390.pcd`–`004530.pcd`, binary PCD v0.7
`x y z intensity` + `VIEWPOINT tx ty tz qw qx qy qz` (header verified). Trajectory **108.3 m**,
x ∈ [−15.7, 83.5], y ∈ [−0.1, 18.0] — read straight from the VIEWPOINT fields.

* `02_kiss_icp/work/make_kitti_seq.py:100-114` already inverts exactly this: `local = (p − t)·R` and writes
  `poses/00.txt` with 12 numbers per line. It writes **`.bin`** scans — ltremovert cannot read those.
  **What must be produced first:** the same inversion, but writing **sensor-frame `.pcd`** files, into two session dirs:
  ```
  work/sessions/A/Scans/000000.pcd … 000080.pcd   +  poses_A.txt   (12 numbers/line, world frame)
  work/sessions/B/Scans/000000.pcd … 000079.pcd   +  poses_B.txt
  ```
  Both pose files are already in **one common world frame** (the benchmark VIEWPOINTs), so `ltslam` — and therefore
  GTSAM — is **not needed**. That is what makes this reachable without installing anything.
* Recommended split (simulated against the real VIEWPOINTs with `Session.cpp:234`'s 10 m rule):
  central = idx `[0,81)` = `004390`–`004470`, query = idx `[61,141)` = `004451`–`004530`
  → **29 of the 80** query frames fall inside the central ROI (~30 keyframes per side). Splits `[0,71)`/`[51,141)`
  and `[0,61)`/`[41,141)` give 31 and 33 — all workable.
* **Scans must be sensor-frame, not world-frame**: `precleaningKeyframes(2.5)` (`Session.cpp:506-533`) deletes points
  with range < 2.5 m and |z| < 0.5 *in the scan frame*; world-frame clouds with identity poses would carve a 2.5 m
  ball out of the map at the world origin.
* Outputs of `removert` are the change-detection deliverables: `pd_map.pcd` / `nd_map.pcd` / `union_map_*.pcd`
  (`Removerter.cpp:1446-1477`) and `updated_map.pcd` / `updated_map_strong.pcd` (`:1517`), plus `map_static`/`map_dynamic`.
* **Honest caveats.** (a) This is one continuous pass, so the "change" is moving cars plus viewpoint/occlusion
  differences — not the paper's 3-day, 6-session ParkingLot scenario; a number from it is a *self-consistency*
  number, comparable to the sibling KITTI-00 runs, **not** to Tab. I/II. (b) The scoring harness already exists
  (`01_dynamicmap_benchmark/work/evaluate.py`, `gt_cloud.pcd` 277.8 MB) and comparable siblings are recorded —
  `04_removert/results/removert_score.json` SA/DA/AA = **99.44 / 41.53 / 64.26**, `03_erasor/results/erasor_score.json`
  = **66.71 / 98.54 / 81.07** — so a like-for-like ltremovert row is cheap to produce.

## 5. Verdict

> **Blocking dependency (env):** **GTSAM is absent from `reproductions/.venvs/ros1noetic`** — no `share/gtsam`,
> no `libgtsam*`, no `GTSAMConfig.cmake` anywhere on the machine. It blocks **`ltslam` only**
> (`ltslam/CMakeLists.txt:26`), because `removert` never links GTSAM (`ltremovert/CMakeLists.txt:27,88-94`).
>
> **Blocking dependency (paper headline):** the LT-map / delta-map module is **not in the repository** (0 grep hits for
> delta/meta map; `Removerter.cpp:1671` is a comment) and Tab. I/II additionally need MulRan **KAIST 04**, an
> "extended sequence" the MulRan site says to request by e-mail (`paper_baseline.md:82`).
> ⇒ **85.7 MB / 9.8 s cannot be reproduced from this checkout under any environment.**

**Smallest next step that unblocks a real number (zero installs):** build **only** the `removert` package, pointed at
the *package* directory rather than the checkout root, then feed it the two generated session dirs.

```bash
micromamba run -p reproductions/.venvs/ros1noetic \
  bash reproductions/tools/build_ros1_catkin.sh \
       reproductions/.ws/lt_mapper_ws ltremovert \
       reproductions/01_robust_localization_slam_dynamic/09_lt_mapper/code/lt-mapper/ltremovert
```
`SRC` **must** be `…/lt-mapper/ltremovert`: passing the checkout root symlinks both packages into `src/`, and
`catkin_make` then stops at `find_package(GTSAM REQUIRED QUIET)`. Binary lands at
`reproductions/.ws/lt_mapper_ws/devel/lib/removert/removert_removert`.

### Next steps (ordered)

1. `work/make_ltmapper_sessions.py` — adapt `02_kiss_icp/work/make_kitti_seq.py:100-114` to emit **sensor-frame PCD**
   + `poses_*.txt`; write sessions A (idx 0–80) and B (idx 61–140) under `work/sessions/`.
2. `work/local_patches.patch` — **one hunk**: `ltremovert/src/Removerter.cpp:938` → `pcl::IndicesPtr` /
   `pcl::make_shared` (copy `04_removert/work/local_patches.patch:24-27`).
3. `work/gen_params.py` — copy `04_removert/work/gen_params.py`; load `ltremovert/config/params_ltmapper.yaml`, change
   **only** the 4 paths, `save_pcd_directory`, `start_idx=0`, `end_idx=81`, identity `ExtrinsicLiDARtoPoseBase`; leave
   resolutions / thresholds / FOV verbatim.
4. `work/run_official.sh` — copy `04_removert/work/run_official.sh:29-67`: roscore → `rosparam load` →
   `rosrun removert removert_removert`; wait on `updated_map.pcd`.
5. Score with `01_dynamicmap_benchmark/work/evaluate.py` (the `map_static` map) → SA/DA/AA/HA; record
   `pd_map.pcd` / `nd_map.pcd` / `updated_map.pcd` point counts and wall-clock.
6. Only if LT-SLAM itself becomes the goal: `micromamba install ros-noetic-gtsam` (robostack-staging, 4.2.0) and rebuild
   with the checkout root — **an install, therefore out of scope for this assessment**.
